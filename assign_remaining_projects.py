"""Assign remaining unassigned projects to available slots"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.timeslot import TimeSlot
from app.models.schedule import Schedule
from app.models.classroom import Classroom
from app.models.project import Project
from app.models.instructor import Instructor
import random

def assign_remaining_projects():
    print("\n" + "="*80)
    print("ASSIGNING REMAINING UNASSIGNED PROJECTS")
    print("="*80)
    
    # Use test.db (backend database)
    engine = create_engine("sqlite:///test.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("1. Analyzing current situation...")
        
        # Get all data
        timeslots = session.query(TimeSlot).filter(TimeSlot.is_active == True).all()
        classrooms = session.query(Classroom).all()
        schedules = session.query(Schedule).all()
        projects = session.query(Project).filter(Project.is_active == True).all()
        
        print(f"   Found {len(timeslots)} timeslots, {len(classrooms)} classrooms, {len(schedules)} schedules, {len(projects)} projects")
        
        # Find unassigned projects
        scheduled_project_ids = {s.project_id for s in schedules}
        unassigned_projects = [p for p in projects if p.id not in scheduled_project_ids]
        
        print(f"   Unassigned projects: {len(unassigned_projects)}")
        
        if len(unassigned_projects) == 0:
            print("   OK - All projects are already assigned!")
            return
        
        # Analyze by type
        unassigned_ara = [p for p in unassigned_projects if p.type.lower() in ['ara', 'interim']]
        unassigned_bitirme = [p for p in unassigned_projects if p.type.lower() in ['bitirme', 'final']]
        
        print(f"   Unassigned ARA: {len(unassigned_ara)}")
        print(f"   Unassigned BITIRME: {len(unassigned_bitirme)}")
        
        print("\n2. Finding available slots...")
        
        # Find all possible classroom-timeslot combinations
        all_possible_slots = []
        for classroom in classrooms:
            for timeslot in timeslots:
                all_possible_slots.append((classroom.id, timeslot.id, classroom.name, timeslot))
        
        # Find occupied slots
        occupied_slots = {(s.classroom_id, s.timeslot_id) for s in schedules}
        
        # Find available slots
        available_slots = []
        for classroom_id, timeslot_id, classroom_name, timeslot in all_possible_slots:
            if (classroom_id, timeslot_id) not in occupied_slots:
                available_slots.append((classroom_id, timeslot_id, classroom_name, timeslot))
        
        print(f"   Total possible slots: {len(all_possible_slots)}")
        print(f"   Occupied slots: {len(occupied_slots)}")
        print(f"   Available slots: {len(available_slots)}")
        
        if len(available_slots) < len(unassigned_projects):
            print(f"   WARNING - Not enough available slots!")
            print(f"   Need {len(unassigned_projects)} slots, but only {len(available_slots)} available")
            print("   Some projects cannot be assigned")
        
        print("\n3. Assigning projects to available slots...")
        
        # Shuffle for random distribution
        random.shuffle(unassigned_projects)
        random.shuffle(available_slots)
        
        assignments_made = 0
        
        for i, project in enumerate(unassigned_projects):
            if i >= len(available_slots):
                print(f"   WARNING - No more available slots for project {project.title}")
                break
            
            classroom_id, timeslot_id, classroom_name, timeslot = available_slots[i]
            
            # Create new schedule
            new_schedule = Schedule(
                project_id=project.id,
                classroom_id=classroom_id,
                timeslot_id=timeslot_id,
                is_makeup=False
            )
            
            session.add(new_schedule)
            assignments_made += 1
            
            print(f"   OK - Assigned '{project.title}' to {classroom_name} at {timeslot.start_time}-{timeslot.end_time}")
        
        print(f"\n4. Saving assignments...")
        
        # Commit changes
        session.commit()
        
        print(f"   OK - Created {assignments_made} new schedule assignments")
        
        print("\n5. Verifying assignments...")
        
        # Get updated data
        updated_schedules = session.query(Schedule).all()
        updated_scheduled_project_ids = {s.project_id for s in updated_schedules}
        
        # Find still unassigned projects
        still_unassigned = [p for p in projects if p.id not in updated_scheduled_project_ids]
        
        print(f"   Before: {len(unassigned_projects)} unassigned projects")
        print(f"   After: {len(still_unassigned)} unassigned projects")
        print(f"   Assigned: {len(unassigned_projects) - len(still_unassigned)} projects")
        
        if still_unassigned:
            print(f"\n   Still unassigned projects:")
            for p in still_unassigned:
                print(f"   - {p.title}")
        
        print("\n6. Final analysis...")
        
        # Analyze by type again
        assigned_ara = [p for p in projects if p.type.lower() in ['ara', 'interim'] and p.id in updated_scheduled_project_ids]
        assigned_bitirme = [p for p in projects if p.type.lower() in ['bitirme', 'final'] and p.id in updated_scheduled_project_ids]
        
        total_ara = len([p for p in projects if p.type.lower() in ['ara', 'interim']])
        total_bitirme = len([p for p in projects if p.type.lower() in ['bitirme', 'final']])
        
        print(f"   ARA projects: {len(assigned_ara)}/{total_ara} assigned ({len(assigned_ara)/total_ara*100:.1f}%)")
        print(f"   BITIRME projects: {len(assigned_bitirme)}/{total_bitirme} assigned ({len(assigned_bitirme)/total_bitirme*100:.1f}%)")
        
        print(f"\n7. SUMMARY:")
        print(f"   - Total projects: {len(projects)}")
        print(f"   - Assigned projects: {len(updated_scheduled_project_ids)}")
        print(f"   - Unassigned projects: {len(still_unassigned)}")
        print(f"   - Assignment rate: {len(updated_scheduled_project_ids)/len(projects)*100:.1f}%")
        
        if len(still_unassigned) == 0:
            print("   SUCCESS! All projects are now assigned!")
            print("   Frontend should now show all projects as assigned")
        else:
            print(f"   WARNING - {len(still_unassigned)} projects still need assignment")
            print("   This might be due to insufficient available timeslots")
        
        print(f"\n8. RECOMMENDATIONS:")
        if len(still_unassigned) > 0:
            print("   TO ASSIGN REMAINING PROJECTS:")
            print("   1. Create more timeslots (extend schedule hours)")
            print("   2. Add more classrooms")
            print("   3. Use weekend slots if available")
            print("   4. Increase classroom capacity")
        else:
            print("   ALL PROJECTS ASSIGNED!")
            print("   - Frontend will show complete project assignments")
            print("   - No missing projects in the UI")
            print("   - Schedule is fully optimized")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    
    finally:
        session.close()
    
    print("="*80 + "\n")

if __name__ == "__main__":
    assign_remaining_projects()
