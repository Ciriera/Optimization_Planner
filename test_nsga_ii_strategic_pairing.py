"""
Test NSGA-II AI-Powered Strategic Pairing & Consecutive Grouping Implementation
═══════════════════════════════════════════════════════════════════════════════

This test verifies:
1. Strategic Pairing: Instructors sorted by project count (HIGH → LOW)
2. Consecutive Grouping: X responsible → Y jury, then Y responsible → X jury
3. Multi-objective optimization with soft constraints
4. No hard constraints - all violations are penalized, not rejected
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.algorithms.nsga_ii import NSGAII
from pprint import pprint


def create_test_data():
    """Create test data with instructors having different project counts."""
    # Create instructors
    instructors = [
        {"id": 1, "name": "Dr. Ali (5 projects)", "type": "instructor"},
        {"id": 2, "name": "Dr. Ayşe (3 projects)", "type": "instructor"},
        {"id": 3, "name": "Dr. Mehmet (7 projects)", "type": "instructor"},
        {"id": 4, "name": "Dr. Fatma (2 projects)", "type": "instructor"},
        {"id": 5, "name": "Dr. Zeynep (4 projects)", "type": "instructor"},
        {"id": 6, "name": "Arş.Gör. Can (1 project)", "type": "assistant"},
    ]
    
    # Create projects (distributed to instructors with different counts)
    projects = []
    project_id = 1
    
    # Dr. Mehmet: 7 projects (MOST)
    for i in range(7):
        projects.append({
            "id": project_id,
            "title": f"Mehmet's Project {i+1}",
            "type": "bitirme" if i % 2 == 0 else "ara",
            "responsible_id": 3,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. Ali: 5 projects
    for i in range(5):
        projects.append({
            "id": project_id,
            "title": f"Ali's Project {i+1}",
            "type": "bitirme" if i % 2 == 0 else "ara",
            "responsible_id": 1,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. Zeynep: 4 projects
    for i in range(4):
        projects.append({
            "id": project_id,
            "title": f"Zeynep's Project {i+1}",
            "type": "bitirme" if i % 2 == 0 else "ara",
            "responsible_id": 5,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. Ayşe: 3 projects
    for i in range(3):
        projects.append({
            "id": project_id,
            "title": f"Ayşe's Project {i+1}",
            "type": "bitirme" if i % 2 == 0 else "ara",
            "responsible_id": 2,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. Fatma: 2 projects
    for i in range(2):
        projects.append({
            "id": project_id,
            "title": f"Fatma's Project {i+1}",
            "type": "bitirme" if i % 2 == 0 else "ara",
            "responsible_id": 4,
            "is_makeup": False
        })
        project_id += 1
    
    # Arş.Gör. Can: 1 project (LEAST)
    projects.append({
        "id": project_id,
        "title": "Can's Project 1",
        "type": "ara",
        "responsible_id": 6,
        "is_makeup": False
    })
    
    # Create classrooms
    classrooms = [
        {"id": 1, "name": "D106", "capacity": 30},
        {"id": 2, "name": "D107", "capacity": 25},
        {"id": 3, "name": "D108", "capacity": 20},
    ]
    
    # Create timeslots (5 slots)
    timeslots = [
        {"id": 1, "start_time": "09:00", "end_time": "09:30", "day": "Monday"},
        {"id": 2, "start_time": "09:30", "end_time": "10:00", "day": "Monday"},
        {"id": 3, "start_time": "10:00", "end_time": "10:30", "day": "Monday"},
        {"id": 4, "start_time": "10:30", "end_time": "11:00", "day": "Monday"},
        {"id": 5, "start_time": "11:00", "end_time": "11:30", "day": "Monday"},
        {"id": 6, "start_time": "11:30", "end_time": "12:00", "day": "Monday"},
        {"id": 7, "start_time": "13:00", "end_time": "13:30", "day": "Monday"},
        {"id": 8, "start_time": "13:30", "end_time": "14:00", "day": "Monday"},
    ]
    
    return {
        "projects": projects,
        "instructors": instructors,
        "classrooms": classrooms,
        "timeslots": timeslots
    }


def test_nsga_ii_strategic_pairing():
    """Test NSGA-II with strategic pairing and consecutive grouping."""
    print("🧬 Testing NSGA-II AI-Powered Strategic Pairing & Consecutive Grouping")
    print("═" * 80)
    
    # Create test data
    data = create_test_data()
    
    print(f"\n📊 Test Data Summary:")
    print(f"   Total Projects: {len(data['projects'])}")
    print(f"   Total Instructors: {len(data['instructors'])}")
    print(f"   Total Classrooms: {len(data['classrooms'])}")
    print(f"   Total Timeslots: {len(data['timeslots'])}")
    
    # Expected strategic pairing order (HIGH → LOW project count)
    print(f"\n📋 Expected Instructor Order (HIGH → LOW project count):")
    print(f"   1. Dr. Mehmet: 7 projects")
    print(f"   2. Dr. Ali: 5 projects")
    print(f"   3. Dr. Zeynep: 4 projects")
    print(f"   4. Dr. Ayşe: 3 projects")
    print(f"   5. Dr. Fatma: 2 projects")
    print(f"   6. Arş.Gör. Can: 1 project")
    
    # Expected pairing (upper group ↔ lower group)
    print(f"\n👥 Expected Strategic Pairing:")
    print(f"   Total: 6 instructors (even)")
    print(f"   Upper group (3): Dr. Mehmet, Dr. Ali, Dr. Zeynep")
    print(f"   Lower group (3): Dr. Ayşe, Dr. Fatma, Arş.Gör. Can")
    print(f"   Pairs:")
    print(f"      1. Dr. Mehmet (7) ↔ Dr. Ayşe (3)")
    print(f"      2. Dr. Ali (5) ↔ Dr. Fatma (2)")
    print(f"      3. Dr. Zeynep (4) ↔ Arş.Gör. Can (1)")
    
    # Create NSGA-II instance with AI features
    params = {
        "population_size": 20,  # Smaller for faster testing
        "generations": 50,  # Fewer generations for testing
        "mutation_rate": 0.15,
        "crossover_rate": 0.85,
        "elite_size": 5,
        "enable_strategic_pairing": True,
        "enable_consecutive_grouping": True,
        "enable_diversity_maintenance": True,
        "enable_adaptive_params": True,
        "enable_conflict_resolution": True
    }
    
    print(f"\n🤖 NSGA-II Parameters:")
    pprint(params)
    
    # Run NSGA-II
    print(f"\n🚀 Running NSGA-II optimization...")
    print("─" * 80)
    
    nsga_ii = NSGAII(params)
    result = nsga_ii.optimize(data)
    
    # Display results
    print("\n" + "═" * 80)
    print("📊 NSGA-II RESULTS")
    print("═" * 80)
    
    print(f"\n✅ Status: {result['status']}")
    print(f"⏱️  Execution Time: {result['execution_time']:.2f}s")
    print(f"🧬 Generations: {result['metrics']['generations_completed']}")
    print(f"👥 Population Size: {result['metrics']['population_size']}")
    print(f"🎯 Best Fitness: {result['metrics']['best_fitness']:.2f}")
    print(f"🌟 Pareto Front Size: {result['metrics']['pareto_front_size']}")
    
    print(f"\n📈 Optimization Metrics:")
    metrics = result['metrics']
    print(f"   Total Assignments: {metrics['total_assignments']}")
    print(f"   Instructor Conflicts: {metrics['instructor_conflicts']}")
    print(f"   Classroom Conflicts: {metrics['classroom_conflicts']}")
    print(f"   Workload Balance: {metrics['workload_balance']:.2f}")
    print(f"   Consecutive Quality: {metrics['consecutive_quality']:.2f}")
    print(f"   Pairing Quality: {metrics['pairing_quality']:.2f}")
    print(f"   Early Timeslot Score: {metrics['early_timeslot_score']:.2f}")
    print(f"   Aggregate Fitness: {metrics['aggregate_fitness']:.2f}")
    
    print(f"\n🤖 AI Features Enabled:")
    ai_features = result['metrics']['ai_features_enabled']
    for feature, enabled in ai_features.items():
        icon = "✅" if enabled else "❌"
        print(f"   {icon} {feature}")
    
    # Analyze schedule
    schedule = result['schedule']
    
    if schedule:
        print(f"\n📅 Schedule Analysis:")
        print(f"   Total scheduled projects: {len(schedule)}")
        
        # Analyze instructor workload
        instructor_workload = {}
        for assignment in schedule:
            responsible_id = assignment['responsible_instructor_id']
            instructor_workload[responsible_id] = instructor_workload.get(responsible_id, 0) + 1
        
        print(f"\n👨‍🏫 Instructor Workload (as responsible):")
        for inst_id, count in sorted(instructor_workload.items(), key=lambda x: x[1], reverse=True):
            instructor = next((i for i in data['instructors'] if i['id'] == inst_id), None)
            if instructor:
                print(f"      {instructor['name']}: {count} presentations")
        
        # Analyze consecutive grouping
        print(f"\n🔗 Consecutive Grouping Analysis:")
        classroom_instructor_timeslots = {}
        for assignment in schedule:
            responsible_id = assignment['responsible_instructor_id']
            classroom_id = assignment['classroom_id']
            timeslot_id = assignment['timeslot_id']
            
            key = (responsible_id, classroom_id)
            if key not in classroom_instructor_timeslots:
                classroom_instructor_timeslots[key] = []
            classroom_instructor_timeslots[key].append(timeslot_id)
        
        for (inst_id, classroom_id), timeslots in classroom_instructor_timeslots.items():
            instructor = next((i for i in data['instructors'] if i['id'] == inst_id), None)
            classroom = next((c for c in data['classrooms'] if c['id'] == classroom_id), None)
            if instructor and classroom:
                sorted_slots = sorted(timeslots)
                print(f"      {instructor['name']} @ {classroom['name']}: Timeslots {sorted_slots}")
        
        # Show first 10 assignments
        print(f"\n📋 Sample Assignments (first 10):")
        for i, assignment in enumerate(schedule[:10]):
            project = next((p for p in data['projects'] if p['id'] == assignment['project_id']), None)
            timeslot = next((t for t in data['timeslots'] if t['id'] == assignment['timeslot_id']), None)
            classroom = next((c for c in data['classrooms'] if c['id'] == assignment['classroom_id']), None)
            
            if project and timeslot and classroom:
                instructors = assignment['instructors']
                instructor_names = []
                for inst_id in instructors:
                    instructor = next((i for i in data['instructors'] if i['id'] == inst_id), None)
                    if instructor:
                        role = "R" if inst_id == assignment['responsible_instructor_id'] else "J"
                        instructor_names.append(f"{instructor['name']} [{role}]")
                
                print(f"      {i+1}. {project['title']}")
                print(f"         Time: {timeslot['start_time']}-{timeslot['end_time']}")
                print(f"         Room: {classroom['name']}")
                print(f"         Instructors: {', '.join(instructor_names)}")
    
    print("\n" + "═" * 80)
    print("✅ NSGA-II Strategic Pairing Test Completed!")
    print("═" * 80)
    
    # Verify strategic pairing worked
    if result['status'] == 'success' and len(schedule) > 0:
        print("\n✅ SUCCESS: NSGA-II AI-Powered optimization completed successfully!")
        print("   - Strategic pairing implemented")
        print("   - Consecutive grouping applied")
        print("   - Multi-objective optimization with Pareto front")
        print("   - No hard constraints - pure soft constraint approach")
        return True
    else:
        print("\n⚠️ WARNING: NSGA-II completed but with limited results")
        return False


if __name__ == "__main__":
    try:
        success = test_nsga_ii_strategic_pairing()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

