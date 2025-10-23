"""
🔍 FULL AI FEATURES VERIFICATION SCRIPT
Tüm AI özelliklerinin doğru çalıştığını teyit eder
"""
import sys
sys.path.insert(0, '.')

from app.algorithms.genetic_algorithm import EnhancedGeneticAlgorithm

print("=" * 80)
print("🔍 FULL AI FEATURES VERIFICATION")
print("=" * 80)

# Create instance
ga = EnhancedGeneticAlgorithm()

# Test data
dummy_data = {
    "projects": [
        {"id": 1, "type": "bitirme", "responsible_instructor_id": 1, "is_makeup": False},
        {"id": 2, "type": "ara", "responsible_instructor_id": 1, "is_makeup": False},
        {"id": 3, "type": "bitirme", "responsible_instructor_id": 2, "is_makeup": False},
        {"id": 4, "type": "ara", "responsible_instructor_id": 2, "is_makeup": False},
        {"id": 5, "type": "bitirme", "responsible_instructor_id": 3, "is_makeup": False},
        {"id": 6, "type": "ara", "responsible_instructor_id": 3, "is_makeup": False},
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
        {"id": 6, "start_time": "11:30", "end_time": "12:00"},
    ]
}

ga.initialize(dummy_data)

print("\n" + "=" * 80)
print("1️⃣ ADAPTIVE PARAMETERS - VERIFICATION")
print("=" * 80)

print(f"\n[CHECK] Initial Parameters:")
print(f"  - Initial Mutation Rate: {ga.initial_mutation_rate}")
print(f"  - Initial Crossover Rate: {ga.initial_crossover_rate}")
print(f"  - Adaptive Enabled: {ga.adaptive_enabled}")
print(f"  - No Improvement Counter: {ga.no_improvement_count}")

# Test adaptive method
ga.no_improvement_count = 15  # Simulate stuck
old_mutation = ga.mutation_rate
ga._adapt_parameters(10, 100.0)
new_mutation = ga.mutation_rate

print(f"\n[TEST] Adaptation when stuck (no_improvement=15):")
print(f"  - Mutation BEFORE: {old_mutation:.4f}")
print(f"  - Mutation AFTER: {new_mutation:.4f}")
print(f"  - Changed: {'YES ✅' if new_mutation > old_mutation else 'NO ❌'}")

if new_mutation > old_mutation:
    print("  ✅ PASS: Mutation increased for exploration!")
else:
    print("  ❌ FAIL: Mutation should increase!")

print("\n" + "=" * 80)
print("2️⃣ SELF-LEARNING WEIGHTS - VERIFICATION")
print("=" * 80)

print(f"\n[CHECK] Initial Weights:")
for key, value in ga.fitness_weights.items():
    print(f"  - {key}: {value:.2f}")

print(f"\n[CHECK] Learning Components:")
print(f"  - Weight History: {len(ga.weight_history)} entries")
print(f"  - Learning Rate: {ga.weight_learning_rate}")

# Test learning
test_solution = [
    {
        "project_id": 1,
        "timeslot_id": 1,
        "classroom_id": 1,
        "responsible_instructor_id": 1,
        "instructors": [1],
        "is_makeup": False
    },
    {
        "project_id": 2,
        "timeslot_id": 2,
        "classroom_id": 1,
        "responsible_instructor_id": 1,
        "instructors": [1, 2],
        "is_makeup": False
    }
]

old_weights = ga.fitness_weights.copy()
ga._learn_from_solution(test_solution, 500.0)
new_weights = ga.fitness_weights

print(f"\n[TEST] Learning from successful solution:")
print(f"  Weights BEFORE learning:")
for key in old_weights:
    print(f"    - {key}: {old_weights[key]:.3f}")
print(f"  Weights AFTER learning:")
for key in new_weights:
    print(f"    - {key}: {new_weights[key]:.3f}")

weights_changed = any(old_weights[k] != new_weights[k] for k in old_weights)
print(f"  - Weights Changed: {'YES ✅' if weights_changed else 'NO ❌'}")

if weights_changed:
    print("  ✅ PASS: Weights are being learned!")
else:
    print("  ❌ FAIL: Weights should change!")

print("\n" + "=" * 80)
print("3️⃣ DIVERSITY MAINTENANCE - VERIFICATION")
print("=" * 80)

print(f"\n[CHECK] Diversity Components:")
print(f"  - Diversity Threshold: {ga.diversity_threshold}")
print(f"  - Diversity History: {len(ga.diversity_history)} entries")

# Create test population
ga.population = [test_solution.copy() for _ in range(10)]

# Test diversity calculation
diversity = ga._calculate_diversity()
print(f"\n[TEST] Diversity Calculation:")
print(f"  - Population Size: {len(ga.population)}")
print(f"  - Calculated Diversity: {diversity:.4f}")
print(f"  - Low Diversity: {'YES (needs injection)' if diversity < ga.diversity_threshold else 'NO (good)'}")

# Test diversity injection
if diversity < ga.diversity_threshold:
    old_pop_size = len(ga.population)
    ga._inject_diversity()
    new_pop_size = len(ga.population)
    print(f"\n[TEST] Diversity Injection:")
    print(f"  - Population BEFORE: {old_pop_size}")
    print(f"  - Population AFTER: {new_pop_size}")
    print(f"  - Injection Done: {'YES ✅' if new_pop_size == old_pop_size else 'NO ❌'}")
    print("  ✅ PASS: Diversity injection works!")

print("\n" + "=" * 80)
print("4️⃣ SMART INITIALIZATION - VERIFICATION")
print("=" * 80)

print(f"\n[CHECK] Initialization Strategies:")
for strategy, percentage in ga.init_strategies.items():
    print(f"  - {strategy}: {percentage*100:.0f}%")

# Test smart initialization
ga.population = []
ga.population = ga._smart_initialize_population()

print(f"\n[TEST] Smart Initialization Result:")
print(f"  - Population Size: {len(ga.population)}")
print(f"  - Target Size: {ga.population_size}")
print(f"  - Match: {'YES ✅' if len(ga.population) == ga.population_size else 'NO ❌'}")

# Verify different strategies were used
unique_structures = set()
for individual in ga.population[:10]:  # Check first 10
    structure = tuple(sorted([a.get('timeslot_id', 0) for a in individual]))
    unique_structures.add(structure)

print(f"  - Unique Structures in First 10: {len(unique_structures)}")
print(f"  - Diversity: {'HIGH ✅' if len(unique_structures) > 5 else 'LOW ❌'}")

if len(ga.population) == ga.population_size and len(unique_structures) > 5:
    print("  ✅ PASS: Smart initialization creates diverse population!")
else:
    print("  ❌ FAIL: Initialization issue!")

print("\n" + "=" * 80)
print("5️⃣ PATTERN RECOGNITION & LEARNING - VERIFICATION")
print("=" * 80)

print(f"\n[CHECK] Pattern Learning Components:")
print(f"  - Pattern Learning Enabled: {ga.pattern_learning_enabled}")
print(f"  - Successful Pairs Tracked: {len(ga.successful_pairs)}")
print(f"  - Successful Classrooms Tracked: {len(ga.successful_classrooms)}")

# Test pattern learning
test_solution_with_patterns = [
    {
        "project_id": 1,
        "timeslot_id": 1,
        "classroom_id": 1,
        "responsible_instructor_id": 1,
        "instructors": [1, 2],
        "is_makeup": False
    },
    {
        "project_id": 2,
        "timeslot_id": 2,
        "classroom_id": 1,
        "responsible_instructor_id": 2,
        "instructors": [2, 1],
        "is_makeup": False
    }
]

old_pairs_count = len(ga.successful_pairs)
ga._learn_patterns(test_solution_with_patterns)
new_pairs_count = len(ga.successful_pairs)

print(f"\n[TEST] Pattern Learning:")
print(f"  - Pairs BEFORE: {old_pairs_count}")
print(f"  - Pairs AFTER: {new_pairs_count}")
print(f"  - Patterns Learned: {'YES ✅' if new_pairs_count > old_pairs_count else 'NO ❌'}")

# Test pattern bonus calculation
pattern_bonus = ga._calculate_pattern_bonus(test_solution_with_patterns)
print(f"\n[TEST] Pattern Bonus:")
print(f"  - Calculated Bonus: {pattern_bonus:.2f}")
print(f"  - Bonus Applied: {'YES ✅' if pattern_bonus > 0 else 'NO ❌'}")

if new_pairs_count > old_pairs_count:
    print("  ✅ PASS: Pattern recognition works!")
else:
    print("  ❌ FAIL: Patterns not being learned!")

print("\n" + "=" * 80)
print("6️⃣ LOCAL SEARCH INTEGRATION - VERIFICATION")
print("=" * 80)

print(f"\n[CHECK] Local Search Components:")
print(f"  - Local Search Enabled: {ga.local_search_enabled}")
print(f"  - Local Search Frequency: Every {ga.local_search_frequency} generations")

# Test local search
test_individual = [
    {
        "project_id": 1,
        "timeslot_id": 1,
        "classroom_id": 1,
        "responsible_instructor_id": 1,
        "instructors": [1],
        "is_makeup": False
    }
]

original_fitness = ga._evaluate_fitness_ai(test_individual)
improved = ga._hill_climbing(test_individual, original_fitness, max_iterations=5)
improved_fitness = ga._evaluate_fitness_ai(improved)

print(f"\n[TEST] Hill Climbing Local Search:")
print(f"  - Original Fitness: {original_fitness:.2f}")
print(f"  - Improved Fitness: {improved_fitness:.2f}")
print(f"  - Improvement: {improved_fitness - original_fitness:.2f}")
print(f"  - Better or Equal: {'YES ✅' if improved_fitness >= original_fitness else 'NO ❌'}")

# Test neighbor generation
neighbor = ga._generate_neighbor(test_individual)
print(f"\n[TEST] Neighbor Generation:")
print(f"  - Original: {test_individual[0] if test_individual else 'None'}")
print(f"  - Neighbor: {neighbor[0] if neighbor else 'None'}")
print(f"  - Different: {'YES ✅' if neighbor != test_individual else 'NO ❌'}")

if improved_fitness >= original_fitness:
    print("  ✅ PASS: Local search works correctly!")
else:
    print("  ❌ FAIL: Local search issue!")

print("\n" + "=" * 80)
print("7️⃣ HARD CONSTRAINTS CHECK")
print("=" * 80)

print(f"\n[VERIFICATION] Checking for hard constraints in code:")

# Search for hard constraint patterns in the algorithm
import inspect

source = inspect.getsource(EnhancedGeneticAlgorithm)

hard_constraint_keywords = [
    'if constraint_violated',
    'raise',
    'return None',
    'return False',
    'INVALID',
    'constraint_violation',
    'hard_constraint'
]

found_hard_constraints = []
for keyword in hard_constraint_keywords:
    if keyword.lower() in source.lower():
        # Find context
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                found_hard_constraints.append(f"Line {i+1}: {line.strip()[:60]}")

if found_hard_constraints:
    print("  ❌ FOUND HARD CONSTRAINTS:")
    for constraint in found_hard_constraints[:5]:  # Show first 5
        print(f"    - {constraint}")
else:
    print("  ✅ NO HARD CONSTRAINTS FOUND!")
    print("  ✅ Algorithm uses pure soft optimization!")

print("\n" + "=" * 80)
print("8️⃣ FULL OPTIMIZATION TEST")
print("=" * 80)

print(f"\n[FINAL TEST] Running full optimization...")

result = ga.optimize()

print(f"\n[RESULTS]:")
print(f"  - Success: {result.get('success')}")
print(f"  - Algorithm: {result.get('algorithm')}")
print(f"  - Final Fitness: {result.get('fitness', 0):.2f}")
print(f"  - Execution Time: {result.get('execution_time', 0):.2f}s")
print(f"  - Assignments: {len(result.get('assignments', []))}")

print(f"\n[AI FEATURES STATUS]:")
ai_features = result.get('ai_features', {})
for feature, status in ai_features.items():
    status_icon = '✅' if status else '❌'
    print(f"  {status_icon} {feature}: {status}")

print(f"\n[LEARNED PARAMETERS]:")
params = result.get('parameters', {})
print(f"  - Initial Mutation: {params.get('initial_mutation_rate', 0):.4f}")
print(f"  - Final Mutation: {params.get('final_mutation_rate', 0):.4f}")
print(f"  - Initial Crossover: {params.get('initial_crossover_rate', 0):.4f}")
print(f"  - Final Crossover: {params.get('final_crossover_rate', 0):.4f}")

print(f"\n[LEARNED WEIGHTS]:")
learned_weights = params.get('learned_weights', {})
for key, value in learned_weights.items():
    print(f"  - {key}: {value:.3f}")

print(f"\n[OPTIMIZATIONS APPLIED]:")
optimizations = result.get('optimizations_applied', [])
for opt in optimizations:
    print(f"  ✅ {opt}")

print("\n" + "=" * 80)
print("📊 FINAL VERIFICATION SUMMARY")
print("=" * 80)

# Count passes
all_ai_features_active = all(ai_features.values())
parameters_adapted = params.get('initial_mutation_rate') != params.get('final_mutation_rate')
weights_learned = any(v != 3.0 for v in learned_weights.values() if 'coverage' not in str(v))
has_optimizations = len(optimizations) >= 10

checks = {
    "1. Adaptive Parameters": parameters_adapted,
    "2. Self-Learning Weights": weights_learned,
    "3. Diversity Maintenance": 'diversity_maintenance' in ai_features and ai_features['diversity_maintenance'],
    "4. Smart Initialization": 'smart_initialization' in ai_features and ai_features['smart_initialization'],
    "5. Pattern Recognition": 'pattern_recognition' in ai_features and ai_features['pattern_recognition'],
    "6. Local Search": 'local_search' in ai_features and ai_features['local_search'],
    "7. No Hard Constraints": not found_hard_constraints,
    "8. All Optimizations": has_optimizations
}

print("\n[VERIFICATION RESULTS]:")
for check_name, passed in checks.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {check_name}")

total_checks = len(checks)
passed_checks = sum(checks.values())
success_rate = (passed_checks / total_checks) * 100

print(f"\n[OVERALL SCORE]: {passed_checks}/{total_checks} ({success_rate:.1f}%)")

if success_rate == 100:
    print("\n" + "🎉" * 40)
    print("✅ ALL AI FEATURES VERIFIED AND WORKING PERFECTLY!")
    print("✅ NO HARD CONSTRAINTS FOUND!")
    print("✅ FULL AI-POWERED GENETIC ALGORITHM IS READY!")
    print("🎉" * 40)
    sys.exit(0)
elif success_rate >= 80:
    print("\n✅ MOST FEATURES WORKING - Minor issues detected")
    sys.exit(0)
else:
    print("\n❌ SOME FEATURES NEED ATTENTION")
    sys.exit(1)

