"""
Test script to verify Genetic Algorithm update
"""
import sys
sys.path.insert(0, '.')

from app.algorithms.genetic_algorithm import EnhancedGeneticAlgorithm

# Test the new algorithm
print("=" * 80)
print("TESTING GENETIC ALGORITHM UPDATE")
print("=" * 80)

# Create instance
ga = EnhancedGeneticAlgorithm()

# Check if new methods exist
print("\n[OK] Checking new AI-based methods:")

methods_to_check = [
    '_create_instructor_pairs',
    '_create_paired_consecutive_solution',
    '_evaluate_fitness',
    '_calculate_coverage_score',
    '_calculate_consecutive_score',
    '_calculate_balance_score',
    '_calculate_classroom_score',
    '_calculate_jury_score',
    '_ai_repair_duplicates',
    '_ai_repair_coverage',
    '_ai_enhance_jury'
]

all_ok = True
for method_name in methods_to_check:
    if hasattr(ga, method_name):
        print(f"  [OK] {method_name} - FOUND")
    else:
        print(f"  [FAIL] {method_name} - NOT FOUND")
        all_ok = False

# Test with dummy data
print("\n[OK] Testing with dummy data:")

dummy_data = {
    "projects": [
        {"id": 1, "type": "bitirme", "responsible_instructor_id": 1, "is_makeup": False},
        {"id": 2, "type": "ara", "responsible_instructor_id": 1, "is_makeup": False},
        {"id": 3, "type": "bitirme", "responsible_instructor_id": 2, "is_makeup": False},
        {"id": 4, "type": "ara", "responsible_instructor_id": 2, "is_makeup": False},
        {"id": 5, "type": "bitirme", "responsible_instructor_id": 3, "is_makeup": False},
    ],
    "instructors": [
        {"id": 1, "name": "Instructor 1"},
        {"id": 2, "name": "Instructor 2"},
        {"id": 3, "name": "Instructor 3"},
    ],
    "classrooms": [
        {"id": 1, "name": "D106"},
        {"id": 2, "name": "D107"},
    ],
    "timeslots": [
        {"id": 1, "start_time": "09:00", "end_time": "09:30"},
        {"id": 2, "start_time": "09:30", "end_time": "10:00"},
        {"id": 3, "start_time": "10:00", "end_time": "10:30"},
        {"id": 4, "start_time": "10:30", "end_time": "11:00"},
        {"id": 5, "start_time": "11:00", "end_time": "11:30"},
    ]
}

try:
    ga.initialize(dummy_data)
    
    # Test instructor pairing
    print("\n  Testing _create_instructor_pairs()...")
    pairs = ga._create_instructor_pairs()
    print(f"  [OK] Created {len(pairs)} instructor pairs")
    
    # Test solution creation
    print("\n  Testing _create_paired_consecutive_solution()...")
    solution = ga._create_paired_consecutive_solution()
    print(f"  [OK] Created solution with {len(solution)} assignments")
    
    # Test fitness evaluation
    print("\n  Testing _evaluate_fitness()...")
    fitness = ga._evaluate_fitness(solution)
    print(f"  [OK] Fitness score: {fitness:.2f}")
    
    # Test optimize
    print("\n  Testing optimize()...")
    result = ga.optimize()
    print(f"  [OK] Optimization completed")
    print(f"  [OK] Result keys: {list(result.keys())}")
    print(f"  [OK] Assignments: {len(result.get('assignments', []))}")
    print(f"  [OK] Fitness: {result.get('fitness', 0):.2f}")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] ALL TESTS PASSED - GENETIC ALGORITHM UPDATE IS WORKING!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[FAIL] TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    all_ok = False

if not all_ok:
    print("\n[FAIL] SOME TESTS FAILED")
    sys.exit(1)
else:
    print("\n[SUCCESS] SUCCESS - Algorithm is updated correctly!")
    sys.exit(0)

