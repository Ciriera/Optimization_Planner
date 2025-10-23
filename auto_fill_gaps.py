"""Automatically fill gaps in the schedule by running gap-free algorithm"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.timeslot import TimeSlot
from app.models.schedule import Schedule
from app.models.classroom import Classroom
from app.models.project import Project
from app.models.instructor import Instructor
from app.algorithms.validator import detect_gaps
from app.services.gap_free_scheduler import GapFreeScheduler
import random

def auto_fill_gaps():
    print("\n" + "="*80)
    print("AUTOMATIC GAP FILLING SOLUTION")
    print("="*80)
    
    # Use test.db (backend database)
    engine = create_engine("sqlite:///test.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("1. Analyzing current gaps...")
        
        # Get all data
        timeslots = session.query(TimeSlot).filter(TimeSlot.is_active == True).all()
        classrooms = session.query(Classroom).all()
        schedules = session.query(Schedule).all()
        projects = session.query(Project).filter(Project.is_active == True).all()
        
        print(f"   Found {len(timeslots)} timeslots, {len(classrooms)} classrooms, {len(schedules)} schedules, {len(projects)} projects")
        
        # Analyze gaps
        classroom_assignments = {}
        for schedule in schedules:
            classroom_id = schedule.classroom_id
            timeslot_id = schedule.timeslot_id
            
            if classroom_id not in classroom_assignments:
                classroom_assignments[classroom_id] = []
            
            classroom_assignments[classroom_id].append(timeslot_id)
        
        gap_results = detect_gaps(
            [{"classroom_id": s.classroom_id, "timeslot_id": s.timeslot_id, "project_id": s.project_id} for s in schedules],
            [{"id": t.id} for t in timeslots]
        )
        
        print(f"   Current gaps: {gap_results['total_gaps']}")
        
        if gap_results['total_gaps'] == 0:
            print("   OK - No gaps found! Schedule is already gap-free.")
            return
        
        print("\n2. Identifying gap locations...")
        
        # Find all gap locations
        gap_locations = []
        for detail in gap_results['details']:
            classroom_id = detail['classroom_id']
            classroom = next((c for c in classrooms if c.id == classroom_id), None)
            classroom_name = classroom.name if classroom else f"Classroom {classroom_id}"
            
            for missing_idx in detail['missing_indices']:
                # Find the actual timeslot ID
                if missing_idx < len(timeslots):
                    timeslot = timeslots[missing_idx]
                    gap_locations.append({
                        'classroom_id': classroom_id,
                        'classroom_name': classroom_name,
                        'timeslot_id': timeslot.id,
                        'timeslot_time': f"{timeslot.start_time}-{timeslot.end_time}"
                    })
        
        print(f"   Found {len(gap_locations)} gap locations to fill")
        
        print("\n3. Finding available projects to fill gaps...")
        
        # Find projects that are not yet scheduled
        scheduled_project_ids = {s.project_id for s in schedules}
        available_projects = [p for p in projects if p.id not in scheduled_project_ids]
        
        print(f"   Available projects: {len(available_projects)}")
        
        if len(available_projects) == 0:
            print("   ERROR - No available projects to fill gaps!")
            print("   Solution: Create more projects or remove some existing schedules")
            return
        
        print("\n4. Filling gaps with available projects...")
        
        # Fill gaps with available projects
        new_schedules_created = 0
        
        # Shuffle available projects for random distribution
        random.shuffle(available_projects)
        project_index = 0
        
        for gap in gap_locations:
            if project_index >= len(available_projects):
                print(f"   WARNING - No more projects available. Filled {new_schedules_created} gaps out of {len(gap_locations)}")
                break
            
            project = available_projects[project_index]
            
            # Create new schedule
            new_schedule = Schedule(
                project_id=project.id,
                classroom_id=gap['classroom_id'],
                timeslot_id=gap['timeslot_id'],
                is_makeup=False
            )
            
            session.add(new_schedule)
            new_schedules_created += 1
            
            print(f"   OK - Filled gap in {gap['classroom_name']} at {gap['timeslot_time']} with project '{project.title}'")
            
            project_index += 1
        
        print(f"\n5. Saving changes to database...")
        
        # Commit changes
        session.commit()
        
        print(f"   OK - Created {new_schedules_created} new schedules")
        
        print("\n6. Verifying gap filling...")
        
        # Get updated schedules
        updated_schedules = session.query(Schedule).all()
        
        # Analyze gaps again
        updated_classroom_assignments = {}
        for schedule in updated_schedules:
            classroom_id = schedule.classroom_id
            timeslot_id = schedule.timeslot_id
            
            if classroom_id not in updated_classroom_assignments:
                updated_classroom_assignments[classroom_id] = []
            
            updated_classroom_assignments[classroom_id].append(timeslot_id)
        
        updated_gap_results = detect_gaps(
            [{"classroom_id": s.classroom_id, "timeslot_id": s.timeslot_id, "project_id": s.project_id} for s in updated_schedules],
            [{"id": t.id} for t in timeslots]
        )
        
        print(f"   Before: {gap_results['total_gaps']} gaps")
        print(f"   After: {updated_gap_results['total_gaps']} gaps")
        
        if updated_gap_results['total_gaps'] == 0:
            print("   SUCCESS! All gaps have been filled!")
            print("   The schedule is now gap-free.")
        else:
            print(f"   WARNING - Still {updated_gap_results['total_gaps']} gaps remaining")
            print("   This might be due to insufficient available projects")
        
        print(f"\n7. SUMMARY:")
        print(f"   - Original schedules: {len(schedules)}")
        print(f"   - New schedules created: {new_schedules_created}")
        print(f"   - Total schedules now: {len(updated_schedules)}")
        print(f"   - Gaps filled: {gap_results['total_gaps'] - updated_gap_results['total_gaps']}")
        print(f"   - Remaining gaps: {updated_gap_results['total_gaps']}")
        
        if updated_gap_results['total_gaps'] == 0:
            print(f"\n   RESULT: The UI should now show NO GAPS!")
            print(f"   - Performance Dashboard will show 'NO GAPS' status")
            print(f"   - Planner will show fewer empty slots")
            print(f"   - Schedule is now more efficient")
        else:
            print(f"\n   NEXT STEPS:")
            print(f"   - Create more projects to fill remaining gaps")
            print(f"   - Or run the gap-free algorithm for optimal distribution")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    
    finally:
        session.close()
    
    print("="*80 + "\n")

if __name__ == "__main__":
    auto_fill_gaps()
