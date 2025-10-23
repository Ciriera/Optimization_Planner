"""
Test AI-Based Lexicographic Algorithm - Solution Diversity Check
"""

import sys
import logging
from app.algorithms.lexicographic import LexicographicAlgorithm

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce log noise
    format='%(levelname)s: %(message)s'
)

def create_test_data():
    """Create test data."""
    instructors = [
        {"id": 1, "name": "Dr. A", "type": "instructor"},
        {"id": 2, "name": "Dr. B", "type": "instructor"},
        {"id": 3, "name": "Dr. C", "type": "instructor"},
        {"id": 4, "name": "Dr. D", "type": "instructor"},
    ]
    
    projects = []
    project_id = 1
    
    # Dr. A: 6 projects
    for _ in range(6):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 1,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. B: 4 projects
    for _ in range(4):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 2,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. C: 3 projects
    for _ in range(3):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 3,
            "is_makeup": False
        })
        project_id += 1
    
    # Dr. D: 2 projects
    for _ in range(2):
        projects.append({
            "id": project_id,
            "name": f"Project {project_id}",
            "type": "bitirme" if project_id % 3 == 0 else "ara",
            "responsible_id": 4,
            "is_makeup": False
        })
        project_id += 1
    
    classrooms = [
        {"id": 1, "name": "D106"},
        {"id": 2, "name": "D107"},
        {"id": 3, "name": "D108"},
    ]
    
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

def extract_solution_signature(result):
    """Extract a signature from solution for comparison."""
    assignments = result.get("assignments", [])
    
    # Create signature: project -> (classroom, timeslot)
    signature = {}
    for a in assignments:
        pid = a.get("project_id")
        cid = a.get("classroom_id")
        tid = a.get("timeslot_id")
        signature[pid] = (cid, tid)
    
    return signature

def main():
    """Main test function."""
    print("=" * 80)
    print("AI-BASED LEXICOGRAPHIC ALGORITHM - SOLUTION DIVERSITY TEST")
    print("=" * 80)
    
    data = create_test_data()
    
    print(f"\n📊 Test Data:")
    print(f"   Projects: {len(data['projects'])}")
    print(f"   Instructors: {len(data['instructors'])}")
    print(f"   Classrooms: {len(data['classrooms'])}")
    print(f"   Timeslots: {len(data['timeslots'])}")
    
    print(f"\n🤖 Running AI-Based Algorithm 5 times...")
    print(f"   (If all results are different, AI randomization is working!)")
    
    results = []
    signatures = []
    
    for run in range(5):
        print(f"\n   Run {run + 1}/5...")
        
        algorithm = LexicographicAlgorithm({
            "num_solutions": 5,  # Generate 5 solutions per run
            "randomization_level": 0.8,  # 80% randomization
        })
        
        result = algorithm.optimize(data)
        
        fitness = result.get("fitness_scores", {}).get("total_fitness", 0)
        assignments = result.get("assignments", [])
        stats = result.get("stats", {})
        
        signature = extract_solution_signature(result)
        signatures.append(signature)
        
        results.append({
            "run": run + 1,
            "fitness": fitness,
            "assignments": len(assignments),
            "classrooms_used": stats.get("classrooms_used", 0),
            "signature": signature
        })
        
        print(f"      ✓ Fitness: {fitness:.2f}/100")
        print(f"      ✓ Assignments: {len(assignments)}")
        print(f"      ✓ Classrooms Used: {stats.get('classrooms_used', 0)}")
    
    # Check diversity
    print(f"\n" + "=" * 80)
    print(f"DIVERSITY ANALYSIS")
    print(f"=" * 80)
    
    unique_solutions = len(set(str(sorted(sig.items())) for sig in signatures))
    
    print(f"\n📊 Results:")
    print(f"   Total Runs: 5")
    print(f"   Unique Solutions: {unique_solutions}")
    print(f"   Diversity Rate: {(unique_solutions / 5) * 100:.1f}%")
    
    if unique_solutions == 5:
        print(f"\n   ✅ EXCELLENT! All 5 runs produced DIFFERENT solutions!")
        print(f"   🎲 AI randomization is working perfectly!")
    elif unique_solutions >= 3:
        print(f"\n   ✓ GOOD! {unique_solutions}/5 runs produced unique solutions.")
        print(f"   🎲 AI randomization is working well!")
    else:
        print(f"\n   ⚠️  WARNING: Only {unique_solutions}/5 unique solutions.")
        print(f"   🎲 Randomization may need tuning.")
    
    # Compare solutions
    print(f"\n📋 Solution Comparison:")
    for i, r in enumerate(results, 1):
        print(f"   Run {i}: Fitness={r['fitness']:.2f}, Classrooms={r['classrooms_used']}")
    
    # Find best and worst
    best = max(results, key=lambda x: x["fitness"])
    worst = min(results, key=lambda x: x["fitness"])
    
    print(f"\n🏆 Best Solution:")
    print(f"   Run #{best['run']}: Fitness={best['fitness']:.2f}/100")
    
    print(f"\n📉 Worst Solution:")
    print(f"   Run #{worst['run']}: Fitness={worst['fitness']:.2f}/100")
    
    fitness_range = best['fitness'] - worst['fitness']
    print(f"\n📊 Fitness Range: {fitness_range:.2f} points")
    
    if fitness_range > 5:
        print(f"   ✓ Good diversity in fitness scores!")
    elif fitness_range > 0:
        print(f"   ✓ Some diversity in fitness scores.")
    else:
        print(f"   ℹ️  All solutions have same fitness (might be optimal).")
    
    print(f"\n" + "=" * 80)
    print(f"TEST COMPLETED")
    print(f"=" * 80)
    
    print(f"\n🎯 Summary:")
    print(f"   ✅ AI-Based algorithm is working")
    print(f"   ✅ Generates {unique_solutions}/5 unique solutions")
    print(f"   ✅ Fitness range: {fitness_range:.2f} points")
    print(f"   ✅ Best fitness: {best['fitness']:.2f}/100")
    
    return unique_solutions >= 3  # Success if at least 3 unique solutions

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

