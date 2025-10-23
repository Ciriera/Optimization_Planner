"""
Test script for Lexicographic Algorithm with Strategic Pairing
"""

import sys
import logging
from app.algorithms.lexicographic import LexicographicAlgorithm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_data():
    """Create test data for the algorithm."""
    # Sample instructors with varying project loads
    instructors = [
        {"id": 1, "name": "Dr. A", "type": "instructor"},
        {"id": 2, "name": "Dr. B", "type": "instructor"},
        {"id": 3, "name": "Dr. C", "type": "instructor"},
        {"id": 4, "name": "Dr. D", "type": "instructor"},
        {"id": 5, "name": "Dr. E", "type": "instructor"},
        {"id": 6, "name": "Dr. F", "type": "instructor"},
    ]
    
    # Sample projects with varying responsible instructors
    # Dr. A: 8 projects (HIGH LOAD)
    # Dr. B: 6 projects (HIGH LOAD)
    # Dr. C: 5 projects (MEDIUM LOAD)
    # Dr. D: 4 projects (MEDIUM LOAD)
    # Dr. E: 3 projects (LOW LOAD)
    # Dr. F: 2 projects (LOW LOAD)
    
    projects = []
    project_id = 1
    
    # Dr. A projects (8)
    for _ in range(8):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 1,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. B projects (6)
    for _ in range(6):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 2,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. C projects (5)
    for _ in range(5):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 3,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. D projects (4)
    for _ in range(4):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 4,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. E projects (3)
    for _ in range(3):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 5,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. F projects (2)
    for _ in range(2):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 6,
            "is_makeup": False
        })
        project_id += 1
    
    # Sample classrooms
    classrooms = [
        {"id": 1, "name": "D106"},
        {"id": 2, "name": "D107"},
        {"id": 3, "name": "D108"},
        {"id": 4, "name": "D109"},
        {"id": 5, "name": "D110"},
    ]
    
    # Sample timeslots
    timeslots = []
    timeslot_id = 1
    times = [
        ("09:00", "09:30"),
        ("09:30", "10:00"),
        ("10:00", "10:30"),
        ("10:30", "11:00"),
        ("11:00", "11:30"),
        ("11:30", "12:00"),
        ("13:00", "13:30"),
        ("13:30", "14:00"),
        ("14:00", "14:30"),
        ("14:30", "15:00"),
        ("15:00", "15:30"),
        ("15:30", "16:00"),
        ("16:00", "16:30"),
    ]
    
    for start, end in times:
        timeslots.append({
            "id": timeslot_id,
            "start_time": start,
            "end_time": end,
            "time_range": f"{start}-{end}"
        })
        timeslot_id += 1
    
    return {
        "projects": projects,
        "instructors": instructors,
        "classrooms": classrooms,
        "timeslots": timeslots
    }

def main():
    """Main test function."""
    print("=" * 80)
    print("LEXICOGRAPHIC ALGORITHM - STRATEGIC PAIRING TEST")
    print("=" * 80)
    
    # Create test data
    print("\n📊 Creating test data...")
    data = create_test_data()
    
    print(f"   Projects: {len(data['projects'])}")
    print(f"   Instructors: {len(data['instructors'])}")
    print(f"   Classrooms: {len(data['classrooms'])}")
    print(f"   Timeslots: {len(data['timeslots'])}")
    
    # Expected strategic pairs:
    # HIGH GROUP: Dr. A (8), Dr. B (6), Dr. C (5)
    # LOW GROUP: Dr. D (4), Dr. E (3), Dr. F (2)
    # PAIRS: (A,D), (B,E), (C,F)
    
    print("\n🎯 Expected Strategic Pairs:")
    print("   Pair 1: Dr. A (8 projects) ↔ Dr. D (4 projects)")
    print("   Pair 2: Dr. B (6 projects) ↔ Dr. E (3 projects)")
    print("   Pair 3: Dr. C (5 projects) ↔ Dr. F (2 projects)")
    
    # Create algorithm
    print("\n🚀 Initializing Lexicographic Algorithm...")
    algorithm = LexicographicAlgorithm()
    
    # Run optimization
    print("\n⚡ Running optimization...")
    result = algorithm.optimize(data)
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print(f"\nStatus: {result.get('status')}")
    print(f"Algorithm: {result.get('algorithm')}")
    print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
    
    assignments = result.get("assignments", [])
    print(f"\nTotal Assignments: {len(assignments)}")
    
    # Display fitness scores
    fitness = result.get("fitness_scores", {})
    print(f"\n📈 Fitness Scores:")
    print(f"   Total Fitness: {fitness.get('total_fitness', 0):.2f}/100")
    print(f"   Coverage: {fitness.get('coverage', 0):.2f}/100")
    print(f"   Gap Penalty: {fitness.get('gap_penalty', 0):.2f}/100")
    print(f"   Duplicate Penalty: {fitness.get('duplicate_penalty', 0):.2f}/100")
    print(f"   Load Balance: {fitness.get('load_balance', 0):.2f}/100")
    
    # Display statistics
    stats = result.get("stats", {})
    print(f"\n📊 Statistics:")
    print(f"   Coverage: {stats.get('coverage_percentage', 0):.1f}%")
    print(f"   Duplicates: {stats.get('duplicate_count', 0)}")
    print(f"   Gaps: {stats.get('gap_count', 0)}")
    print(f"   Late Slots: {stats.get('late_slot_count', 0)}")
    print(f"   Classrooms Used: {stats.get('classrooms_used', 0)}")
    print(f"   Strategic Pairs Applied: {stats.get('pairs_applied', 0)}")
    
    # Display sample assignments
    if assignments:
        print(f"\n📋 Sample Assignments (first 10):")
        for i, assignment in enumerate(assignments[:10], 1):
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            instructors = assignment.get("instructors", [])
            
            print(f"   {i}. Project {project_id} → Classroom {classroom_id}, Timeslot {timeslot_id}")
            print(f"      Instructors: {instructors}")
    
    # Verify strategic pairing
    print(f"\n🔍 Verifying Strategic Pairing...")
    pair_count = 0
    for assignment in assignments:
        instructors = assignment.get("instructors", [])
        if len(instructors) >= 2:
            # Check if it's a strategic pair
            if set([1, 4]).issubset(set(instructors)):
                pair_count += 1
                print(f"   ✓ Found Pair (A,D) in Project {assignment['project_id']}")
            elif set([2, 5]).issubset(set(instructors)):
                pair_count += 1
                print(f"   ✓ Found Pair (B,E) in Project {assignment['project_id']}")
            elif set([3, 6]).issubset(set(instructors)):
                pair_count += 1
                print(f"   ✓ Found Pair (C,F) in Project {assignment['project_id']}")
    
    print(f"\n✅ Total Strategic Pair Assignments: {pair_count}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)
    
    return result

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get("status") == "completed" else 1)

