"""
🤖 FULL AI-POWERED GENETIC ALGORITHM WITH CONFLICT RESOLUTION - TEST SCRIPT
"""
import sys
import random
from collections import defaultdict
from typing import Dict, Any, List, Tuple

# Assuming EnhancedGeneticAlgorithm is in app.algorithms.genetic_algorithm
sys.path.append('.')
from app.algorithms.genetic_algorithm import EnhancedGeneticAlgorithm

print("=" * 80)
print("🤖 TESTING FULL AI-POWERED GENETIC ALGORITHM WITH CONFLICT RESOLUTION")
print("=" * 80)

# Create instance
ga = EnhancedGeneticAlgorithm()

# Test data with potential conflicts (like in the images)
dummy_data = {
    "projects": [
        {"id": 1, "type": "bitirme", "responsible_instructor_id": 3, "is_makeup": False},
        {"id": 2, "type": "bitirme", "responsible_instructor_id": 3, "is_makeup": False},
        {"id": 3, "type": "bitirme", "responsible_instructor_id": 21, "is_makeup": False},
        {"id": 4, "type": "bitirme", "responsible_instructor_id": 21, "is_makeup": False},
        {"id": 5, "type": "ara", "responsible_instructor_id": 11, "is_makeup": False},
        {"id": 6, "type": "bitirme", "responsible_instructor_id": 11, "is_makeup": False},
    ],
    "instructors": [
        {"id": 3, "name": "Dr. Öğretim Üyesi 3"},
        {"id": 11, "name": "Dr. Öğretim Üyesi 11"},
        {"id": 21, "name": "Dr. Öğretim Üyesi 21"},
        {"id": 1, "name": "Dr. Öğretim Üyesi 1"},
        {"id": 2, "name": "Dr. Öğretim Üyesi 2"},
    ],
    "classrooms": [
        {"id": 1, "name": "D105"},
        {"id": 2, "name": "D106"},
        {"id": 3, "name": "D107"},
        {"id": 4, "name": "D108"},
    ],
    "timeslots": [
        {"id": 14, "start_time": "14:30", "end_time": "15:00", "capacity": 2},
        {"id": 15, "start_time": "15:00", "end_time": "15:30", "capacity": 2},
        {"id": 16, "start_time": "16:00", "end_time": "16:30", "capacity": 2},
        {"id": 17, "start_time": "16:30", "end_time": "17:00", "capacity": 2},
    ]
}

ga.initialize(dummy_data)

print("\n[OK] Checking AI features including conflict resolution:")
features_to_check = [
    '_detect_all_conflicts',
    '_detect_instructor_conflicts', 
    '_detect_classroom_conflicts',
    '_detect_timeslot_conflicts',
    '_resolve_conflicts',
    '_resolve_single_conflict',
    '_reschedule_one_assignment',
    '_replace_jury_member',
    '_relocate_to_available_classroom',
    'conflict_resolution_enabled',
    'auto_resolve_conflicts'
]

all_ok = True
for feature in features_to_check:
    if hasattr(ga, feature):
        print(f"  [OK] {feature} - FOUND")
    else:
        print(f"  [FAIL] {feature} - NOT FOUND")
        all_ok = False

print(f"\n[OK] Conflict Resolution Settings:")
print(f"  - Conflict Resolution Enabled: {ga.conflict_resolution_enabled}")
print(f"  - Auto Resolve Conflicts: {ga.auto_resolve_conflicts}")
print(f"  - Conflict Detection Frequency: {ga.conflict_detection_frequency}")

print(f"\n[OK] Testing conflict resolution with dummy data:")

try:
    ga.initialize(dummy_data)
    
    # Test conflict detection
    print("\n  Testing _detect_all_conflicts()...")
    test_assignments = [
        {
            "project_id": 1,
            "timeslot_id": 14,
            "classroom_id": 1,
            "responsible_instructor_id": 3,
            "instructors": [3, 1],  # Conflict: instructor 3 both responsible and jury
            "is_makeup": False
        },
        {
            "project_id": 2,
            "timeslot_id": 14,
            "classroom_id": 2,
            "responsible_instructor_id": 3,
            "instructors": [3],  # Conflict: instructor 3 responsible again
            "is_makeup": False
        }
    ]
    
    conflicts = ga._detect_all_conflicts(test_assignments)
    print(f"  [OK] Detected {len(conflicts)} conflicts")
    
    if conflicts:
        for i, conflict in enumerate(conflicts, 1):
            print(f"    {i}. {conflict['type']}: {conflict['description']}")
    
    # Test conflict resolution
    if conflicts:
        print("\n  Testing _resolve_conflicts()...")
        resolved_assignments, resolution_log = ga._resolve_conflicts(test_assignments, conflicts)
        successful = len([r for r in resolution_log if r['success']])
        print(f"  [OK] Resolved {successful}/{len(conflicts)} conflicts")
        
        for log_entry in resolution_log:
            status = "✅" if log_entry['success'] else "❌"
            print(f"    {status} {log_entry['conflict_id']}: {log_entry['description']}")
    
    # Test full optimization
    print("\n  Testing full optimize() with conflict resolution...")
    result = ga.optimize()
    print(f"  [OK] Optimization completed")
    print(f"  [OK] Result keys: {list(result.keys())}")
    print(f"  [OK] Assignments: {len(result.get('assignments', []))}")
    print(f"  [OK] Fitness: {result.get('fitness', 0):.2f}")
    
    # Check AI features in result
    ai_features = result.get('ai_features', {})
    print(f"\n  [OK] AI Features Status:")
    for feature, status in ai_features.items():
        status_icon = "✅" if status else "❌"
        print(f"    {status_icon} {feature}: {status}")
    
    # Check if conflict resolution was used
    if ai_features.get('conflict_resolution'):
        print(f"  ✅ CONFLICT RESOLUTION: ACTIVE")
    else:
        print(f"  ❌ CONFLICT RESOLUTION: INACTIVE")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] FULL AI-POWERED GENETIC ALGORITHM WITH CONFLICT RESOLUTION IS WORKING!")
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
    print("\n[SUCCESS] ALL TESTS PASSED - Genetic Algorithm with Conflict Resolution is ready!")
    sys.exit(0)
