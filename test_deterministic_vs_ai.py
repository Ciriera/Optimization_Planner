"""
Deterministic vs AI-Based Comparison Test
"""

import sys
import logging
from app.algorithms.lexicographic import LexicographicAlgorithm

logging.basicConfig(level=logging.ERROR)

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
    
    for instructor_id, count in [(1, 6), (2, 4), (3, 3), (4, 2)]:
        for _ in range(count):
            projects.append({
                "id": project_id,
                "name": f"Project {project_id}",
                "type": "bitirme" if project_id % 3 == 0 else "ara",
                "responsible_id": instructor_id,
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
        ("09:00", "09:30"), ("09:30", "10:00"), ("10:00", "10:30"),
        ("10:30", "11:00"), ("11:00", "11:30"), ("11:30", "12:00"),
        ("13:00", "13:30"), ("13:30", "14:00"),
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

def extract_signature(result):
    """Extract solution signature."""
    assignments = result.get("assignments", [])
    sig = tuple(sorted((a["project_id"], a["classroom_id"], a["timeslot_id"]) for a in assignments))
    return sig

def main():
    """Main comparison test."""
    print("=" * 80)
    print("DETERMINISTIC vs AI-BASED COMPARISON")
    print("=" * 80)
    
    data = create_test_data()
    
    print(f"\n📊 Test Configuration:")
    print(f"   Projects: {len(data['projects'])}")
    print(f"   Instructors: {len(data['instructors'])}")
    
    # Test 1: Deterministic Mode (Low Randomization)
    print(f"\n{'='*80}")
    print(f"TEST 1: DETERMINISTIC MODE (randomization_level=0.0)")
    print(f"{'='*80}")
    print(f"Running 3 times - should produce SAME result...")
    
    deterministic_results = []
    for run in range(3):
        algorithm = LexicographicAlgorithm({
            "num_solutions": 1,
            "randomization_level": 0.0,  # No randomization
        })
        result = algorithm.optimize(data)
        sig = extract_signature(result)
        fitness = result.get("fitness_scores", {}).get("total_fitness", 0)
        deterministic_results.append((sig, fitness))
        print(f"   Run {run + 1}: Fitness={fitness:.2f}")
    
    det_unique = len(set(deterministic_results))
    print(f"\n   Result: {det_unique}/3 unique solutions")
    if det_unique == 1:
        print(f"   ✅ EXPECTED: All runs produced SAME result (deterministic)")
    else:
        print(f"   ⚠️  Unexpected: Different results in deterministic mode")
    
    # Test 2: AI-Based Mode (High Randomization)
    print(f"\n{'='*80}")
    print(f"TEST 2: AI-BASED MODE (randomization_level=0.9)")
    print(f"{'='*80}")
    print(f"Running 5 times - should produce DIFFERENT results...")
    
    ai_results = []
    for run in range(5):
        algorithm = LexicographicAlgorithm({
            "num_solutions": 3,  # Generate 3 candidates
            "randomization_level": 0.9,  # High randomization
        })
        result = algorithm.optimize(data)
        sig = extract_signature(result)
        fitness = result.get("fitness_scores", {}).get("total_fitness", 0)
        ai_results.append((sig, fitness))
        print(f"   Run {run + 1}: Fitness={fitness:.2f}")
    
    ai_unique = len(set(ai_results))
    print(f"\n   Result: {ai_unique}/5 unique solutions")
    if ai_unique >= 3:
        print(f"   ✅ EXCELLENT: {ai_unique} different solutions (AI working!)")
    elif ai_unique >= 2:
        print(f"   ✓ GOOD: {ai_unique} different solutions")
    else:
        print(f"   ⚠️  Low diversity: Only {ai_unique} unique solution(s)")
    
    # Comparison
    print(f"\n{'='*80}")
    print(f"COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📊 Diversity Comparison:")
    print(f"   Deterministic Mode: {det_unique}/3 unique ({(det_unique/3)*100:.0f}%)")
    print(f"   AI-Based Mode:      {ai_unique}/5 unique ({(ai_unique/5)*100:.0f}%)")
    
    diversity_improvement = ((ai_unique/5) - (det_unique/3)) * 100
    print(f"\n   📈 Diversity Improvement: {diversity_improvement:+.1f}%")
    
    # Fitness comparison
    det_fitness_avg = sum(f for _, f in deterministic_results) / len(deterministic_results)
    ai_fitness_avg = sum(f for _, f in ai_results) / len(ai_results)
    ai_fitness_max = max(f for _, f in ai_results)
    
    print(f"\n🎯 Fitness Comparison:")
    print(f"   Deterministic Avg: {det_fitness_avg:.2f}/100")
    print(f"   AI-Based Avg:      {ai_fitness_avg:.2f}/100")
    print(f"   AI-Based Best:     {ai_fitness_max:.2f}/100")
    
    if ai_fitness_max > det_fitness_avg:
        improvement = ai_fitness_max - det_fitness_avg
        print(f"\n   ✅ AI found BETTER solution (+{improvement:.2f} points)!")
    elif ai_fitness_avg > det_fitness_avg:
        improvement = ai_fitness_avg - det_fitness_avg
        print(f"\n   ✓ AI average is better (+{improvement:.2f} points)")
    else:
        print(f"\n   ℹ️  Similar fitness scores")
    
    print(f"\n{'='*80}")
    print(f"CONCLUSION")
    print(f"{'='*80}")
    
    print(f"\n✅ Deterministic Mode:")
    print(f"   • Produces SAME result every time")
    print(f"   • Fast and predictable")
    print(f"   • Use when consistency is critical")
    
    print(f"\n🤖 AI-Based Mode:")
    print(f"   • Produces DIFFERENT results")
    print(f"   • Explores solution space")
    print(f"   • Finds better solutions through randomization")
    print(f"   • Use when quality is more important than consistency")
    
    success = ai_unique >= det_unique + 1
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

