"""Analyze project assignments and identify missing/duplicate assignments"""
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

def analyze_project_assignments():
    print("\n" + "="*80)
    print("PROJECT ASSIGNMENT ANALYSIS")
    print("="*80)
    
    # Use test.db (backend database)
    engine = create_engine("sqlite:///test.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("1. Getting all data...")
        
        # Get all data
        timeslots = session.query(TimeSlot).filter(TimeSlot.is_active == True).all()
        classrooms = session.query(Classroom).all()
        schedules = session.query(Schedule).all()
        projects = session.query(Project).filter(Project.is_active == True).all()
        instructors = session.query(Instructor).all()
        
        print(f"   Found {len(timeslots)} timeslots, {len(classrooms)} classrooms, {len(schedules)} schedules, {len(projects)} projects")
        
        print("\n2. Analyzing project types...")
        
        # Analyze by project type
        ara_projects = [p for p in projects if p.type.lower() in ['ara', 'interim']]
        bitirme_projects = [p for p in projects if p.type.lower() in ['bitirme', 'final']]
        other_projects = [p for p in projects if p.type.lower() not in ['ara', 'interim', 'bitirme', 'final']]
        
        print(f"   ARA projects: {len(ara_projects)}")
        print(f"   BITIRME projects: {len(bitirme_projects)}")
        print(f"   OTHER projects: {len(other_projects)}")
        
        print("\n3. Analyzing schedule assignments...")
        
        # Get scheduled project IDs
        scheduled_project_ids = {s.project_id for s in schedules}
        
        # Find assigned vs unassigned projects
        assigned_ara = [p for p in ara_projects if p.id in scheduled_project_ids]
        unassigned_ara = [p for p in ara_projects if p.id not in scheduled_project_ids]
        
        assigned_bitirme = [p for p in bitirme_projects if p.id in scheduled_project_ids]
        unassigned_bitirme = [p for p in bitirme_projects if p.id not in scheduled_project_ids]
        
        print(f"   Assigned ARA projects: {len(assigned_ara)}/{len(ara_projects)} ({len(assigned_ara)/len(ara_projects)*100:.1f}%)")
        print(f"   Assigned BITIRME projects: {len(assigned_bitirme)}/{len(bitirme_projects)} ({len(assigned_bitirme)/len(bitirme_projects)*100:.1f}%)")
        
        if unassigned_ara:
            print(f"\n4. UNASSIGNED ARA PROJECTS ({len(unassigned_ara)}):")
            for p in unassigned_ara[:10]:  # Show first 10
                print(f"   - ID {p.id}: {p.title}")
            if len(unassigned_ara) > 10:
                print(f"   ... and {len(unassigned_ara) - 10} more")
        
        if unassigned_bitirme:
            print(f"\n5. UNASSIGNED BITIRME PROJECTS ({len(unassigned_bitirme)}):")
            for p in unassigned_bitirme[:10]:  # Show first 10
                print(f"   - ID {p.id}: {p.title}")
            if len(unassigned_bitirme) > 10:
                print(f"   ... and {len(unassigned_bitirme) - 10} more")
        
        print("\n6. Checking for duplicate assignments...")
        
        # Check for duplicate project assignments (same project in multiple schedules)
        project_assignment_counts = {}
        for schedule in schedules:
            project_id = schedule.project_id
            if project_id not in project_assignment_counts:
                project_assignment_counts[project_id] = []
            project_assignment_counts[project_id].append(schedule)
        
        duplicates = {pid: schedules_list for pid, schedules_list in project_assignment_counts.items() if len(schedules_list) > 1}
        
        if duplicates:
            print(f"   WARNING - Found {len(duplicates)} projects with multiple assignments:")
            for project_id, schedules_list in duplicates.items():
                project = next((p for p in projects if p.id == project_id), None)
                project_title = project.title if project else f"Project {project_id}"
                print(f"   - {project_title} (ID: {project_id}) assigned {len(schedules_list)} times:")
                for s in schedules_list:
                    classroom = next((c for c in classrooms if c.id == s.classroom_id), None)
                    timeslot = next((t for t in timeslots if t.id == s.timeslot_id), None)
                    classroom_name = classroom.name if classroom else f"Classroom {s.classroom_id}"
                    timeslot_time = f"{timeslot.start_time}-{timeslot.end_time}" if timeslot else f"Timeslot {s.timeslot_id}"
                    print(f"     * Schedule ID {s.id}: {classroom_name} at {timeslot_time}")
        else:
            print("   OK - No duplicate project assignments found")
        
        print("\n7. Checking for schedule conflicts...")
        
        # Check for schedule conflicts (same classroom + timeslot with different projects)
        schedule_conflicts = []
        classroom_timeslot_assignments = {}
        
        for schedule in schedules:
            key = (schedule.classroom_id, schedule.timeslot_id)
            if key not in classroom_timeslot_assignments:
                classroom_timeslot_assignments[key] = []
            classroom_timeslot_assignments[key].append(schedule)
        
        conflicts = {key: schedules_list for key, schedules_list in classroom_timeslot_assignments.items() if len(schedules_list) > 1}
        
        if conflicts:
            print(f"   WARNING - Found {len(conflicts)} schedule conflicts:")
            for (classroom_id, timeslot_id), schedules_list in conflicts.items():
                classroom = next((c for c in classrooms if c.id == classroom_id), None)
                timeslot = next((t for t in timeslots if t.id == timeslot_id), None)
                classroom_name = classroom.name if classroom else f"Classroom {classroom_id}"
                timeslot_time = f"{timeslot.start_time}-{timeslot.end_time}" if timeslot else f"Timeslot {timeslot_id}"
                print(f"   - {classroom_name} at {timeslot_time} has {len(schedules_list)} assignments:")
                for s in schedules_list:
                    project = next((p for p in projects if p.id == s.project_id), None)
                    project_title = project.title if project else f"Project {s.project_id}"
                    print(f"     * Schedule ID {s.id}: {project_title}")
        else:
            print("   OK - No schedule conflicts found")
        
        print("\n8. Summary of issues...")
        
        issues_found = []
        if unassigned_ara:
            issues_found.append(f"{len(unassigned_ara)} unassigned ARA projects")
        if unassigned_bitirme:
            issues_found.append(f"{len(unassigned_bitirme)} unassigned BITIRME projects")
        if duplicates:
            issues_found.append(f"{len(duplicates)} projects with duplicate assignments")
        if conflicts:
            issues_found.append(f"{len(conflicts)} schedule conflicts")
        
        if issues_found:
            print("   ISSUES FOUND:")
            for issue in issues_found:
                print(f"   - {issue}")
        else:
            print("   OK - No issues found")
        
        print("\n9. Frontend implications...")
        
        total_unassigned = len(unassigned_ara) + len(unassigned_bitirme)
        if total_unassigned > 0:
            print(f"   Frontend will show {total_unassigned} projects as 'not assigned'")
            print("   This is why you see missing assignments in the UI")
        
        if duplicates or conflicts:
            print("   Frontend might show inconsistent data due to duplicates/conflicts")
            print("   Some projects might appear assigned multiple times")
        
        print("\n10. Recommendations...")
        
        if unassigned_ara or unassigned_bitirme:
            print("   TO FIX MISSING ASSIGNMENTS:")
            print("   1. Create more timeslots if needed")
            print("   2. Run assignment algorithm to assign remaining projects")
            print("   3. Check if projects are properly configured")
        
        if duplicates:
            print("   TO FIX DUPLICATE ASSIGNMENTS:")
            print("   1. Remove duplicate schedule entries")
            print("   2. Check for data integrity issues")
        
        if conflicts:
            print("   TO FIX SCHEDULE CONFLICTS:")
            print("   1. Resolve overlapping assignments")
            print("   2. Reassign conflicting projects to different timeslots")
        
        print(f"\n11. FINAL STATUS:")
        print(f"   - Total projects: {len(projects)}")
        print(f"   - Assigned projects: {len(scheduled_project_ids)}")
        print(f"   - Unassigned projects: {len(projects) - len(scheduled_project_ids)}")
        print(f"   - Assignment rate: {len(scheduled_project_ids)/len(projects)*100:.1f}%")
        
        if len(scheduled_project_ids) == len(projects):
            print("   ✅ All projects are assigned!")
        else:
            print(f"   ⚠️  {len(projects) - len(scheduled_project_ids)} projects still need assignment")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()
    
    print("="*80 + "\n")

if __name__ == "__main__":
    analyze_project_assignments()
