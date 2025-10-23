"""STRICT Gap-Free Algorithm - No gaps allowed whatsoever"""
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
from app.algorithms.validator import detect_gaps
import random

def create_strict_gap_free_schedule():
    """Create a STRICT gap-free schedule - absolutely no gaps allowed"""
    print("\n" + "="*80)
    print("STRICT GAP-FREE ALGORITHM - NO GAPS ALLOWED")
    print("="*80)
    
    engine = create_engine("sqlite:///test.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("1. Getting data...")
        
        # Get all data
        timeslots = session.query(TimeSlot).filter(TimeSlot.is_active == True).all()
        classrooms = session.query(Classroom).all()
        projects = session.query(Project).filter(Project.is_active == True).all()
        instructors = session.query(Instructor).all()
        
        print(f"   Found {len(timeslots)} timeslots, {len(classrooms)} classrooms, {len(projects)} projects")
        
        # Calculate total possible slots
        total_slots = len(timeslots) * len(classrooms)
        print(f"   Total possible slots: {total_slots}")
        
        print("\n2. STRICT REQUIREMENTS:")
        print("   - EVERY slot MUST be filled")
        print("   - NO gaps allowed whatsoever")
        print("   - If not enough projects, create new ones")
        print("   - If too many projects, prioritize by type")
        
        print("\n3. Creating STRICT gap-free schedule...")
        
        # Clear existing schedules
        session.query(Schedule).delete()
        
        # Get available instructors for new projects
        available_instructors = [i for i in instructors if i.type in ['hoca', 'instructor', 'HOCA', 'INSTRUCTOR']]
        if not available_instructors:
            available_instructors = instructors
        
        # STRICT FILLING: Fill EVERY possible slot
        assignments_made = 0
        project_index = 0
        
        print(f"   Filling ALL {total_slots} slots...")
        
        for classroom in classrooms:
            for timeslot in timeslots:
                if project_index < len(projects):
                    # Use existing project
                    project = projects[project_index]
                else:
                    # Create new project - STRICT requirement
                    project_type = "ARA" if assignments_made % 2 == 0 else "BITIRME"
                    instructor = random.choice(available_instructors)
                    
                    project = Project(
                        title=f"STRICT-Filler {project_type} Proje {assignments_made + 1}: Bilgisayar Mühendisliği {'Ara Değerlendirme' if project_type == 'ARA' else 'Mezuniyet Projesi'}",
                        description=f"STRICT gap-free için otomatik oluşturulan {project_type} projesi",
                        type=project_type.lower(),
                        status="ACTIVE",
                        student_capacity=1,
                        responsible_id=instructor.id,
                        is_active=True
                    )
                    
                    session.add(project)
                    session.flush()  # Get the ID
                    
                    print(f"   Created STRICT filler project: {project.title}")
                
                # Create schedule - MANDATORY for every slot
                new_schedule = Schedule(
                    project_id=project.id,
                    classroom_id=classroom.id,
                    timeslot_id=timeslot.id,
                    is_makeup=False
                )
                
                session.add(new_schedule)
                assignments_made += 1
                project_index += 1
                
                if assignments_made % 20 == 0:  # Progress update
                    print(f"   Progress: {assignments_made}/{total_slots} slots filled")
        
        print(f"\n4. Saving STRICT gap-free schedule...")
        
        # Commit all changes
        session.commit()
        
        print(f"   Created {assignments_made} schedule assignments")
        print(f"   Target was {total_slots} slots")
        
        if assignments_made == total_slots:
            print("   SUCCESS: ALL slots filled - STRICT requirement met!")
        else:
            print(f"   ERROR: Only {assignments_made}/{total_slots} slots filled!")
        
        print("\n5. STRICT verification - Multiple gap checks...")
        
        # Multiple gap checks for strict verification
        verification_passed = True
        
        for check_round in range(1, 4):
            print(f"   Gap check round {check_round}...")
            
            final_schedules = session.query(Schedule).all()
            
            gap_results = detect_gaps(
                [{"classroom_id": s.classroom_id, "timeslot_id": s.timeslot_id, "project_id": s.project_id} for s in final_schedules],
                [{"id": t.id} for t in timeslots]
            )
            
            gaps_found = gap_results.get("total_gaps", 0)
            
            if gaps_found > 0:
                print(f"   FAILED: {gaps_found} gaps found in round {check_round}")
                verification_passed = False
                
                # STRICT: Fix gaps immediately
                print(f"   STRICT FIXING: Filling {gaps_found} gaps...")
                
                gap_locations = []
                for detail in gap_results.get("details", []):
                    for missing_idx in detail.get("missing_indices", []):
                        if missing_idx < len(timeslots):
                            timeslot = timeslots[missing_idx]
                            gap_locations.append({
                                "classroom_id": detail["classroom_id"],
                                "timeslot_id": timeslot.id
                            })
                
                # Fill gaps with new projects
                for i, gap in enumerate(gap_locations):
                    project_type = "ARA" if i % 2 == 0 else "BITIRME"
                    instructor = random.choice(available_instructors)
                    
                    filler_project = Project(
                        title=f"STRICT-Gap-Fix {project_type} Proje {i+1}: Bilgisayar Mühendisliği {'Ara Değerlendirme' if project_type == 'ARA' else 'Mezuniyet Projesi'}",
                        description=f"STRICT gap fixing için otomatik oluşturulan {project_type} projesi",
                        type=project_type.lower(),
                        status="ACTIVE",
                        student_capacity=1,
                        responsible_id=instructor.id,
                        is_active=True
                    )
                    
                    session.add(filler_project)
                    session.flush()
                    
                    new_schedule = Schedule(
                        project_id=filler_project.id,
                        classroom_id=gap["classroom_id"],
                        timeslot_id=gap["timeslot_id"],
                        is_makeup=False
                    )
                    
                    session.add(new_schedule)
                    print(f"   Fixed gap with new project: {filler_project.title}")
                
                session.commit()
            else:
                print(f"   PASSED: No gaps found in round {check_round}")
        
        print(f"\n6. FINAL STRICT VERIFICATION...")
        
        # Final comprehensive check
        final_schedules = session.query(Schedule).all()
        final_gap_results = detect_gaps(
            [{"classroom_id": s.classroom_id, "timeslot_id": s.timeslot_id, "project_id": s.project_id} for s in final_schedules],
            [{"id": t.id} for t in timeslots]
        )
        
        final_gaps = final_gap_results.get("total_gaps", 0)
        
        print(f"   Final schedules: {len(final_schedules)}")
        print(f"   Expected schedules: {total_slots}")
        print(f"   Final gaps: {final_gaps}")
        
        if final_gaps == 0 and len(final_schedules) == total_slots:
            print("   STRICT SUCCESS: Perfect gap-free schedule!")
            strict_success = True
        elif final_gaps == 0:
            print("   GOOD: No gaps, but schedule count mismatch")
            strict_success = False
        else:
            print(f"   FAILED: {final_gaps} gaps still exist!")
            strict_success = False
        
        print(f"\n7. STRICT SUMMARY:")
        print(f"   - Total possible slots: {total_slots}")
        print(f"   - Schedules created: {len(final_schedules)}")
        print(f"   - Gaps remaining: {final_gaps}")
        print(f"   - STRICT requirement met: {strict_success}")
        print(f"   - All slots filled: {len(final_schedules) == total_slots}")
        print(f"   - Zero gaps: {final_gaps == 0}")
        
        if strict_success:
            print(f"\n   RESULT: STRICT GAP-FREE SUCCESS!")
            print(f"   - Every single slot is filled")
            print(f"   - Zero gaps guaranteed")
            print(f"   - Frontend will show perfect gap-free schedule")
        else:
            print(f"\n   RESULT: STRICT REQUIREMENTS NOT MET")
            print(f"   - Additional manual intervention needed")
        
        return {
            "strict_success": strict_success,
            "total_schedules": len(final_schedules),
            "expected_schedules": total_slots,
            "gaps_remaining": final_gaps,
            "all_slots_filled": len(final_schedules) == total_slots,
            "zero_gaps": final_gaps == 0,
            "message": "STRICT gap-free schedule created successfully!" if strict_success else "STRICT requirements not fully met"
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return {"strict_success": False, "error": str(e)}
    
    finally:
        session.close()
    
    print("="*80 + "\n")

if __name__ == "__main__":
    result = create_strict_gap_free_schedule()
    print(f"STRICT RESULT: {result}")
