"""
Test script for Integer Linear Programming algorithm.
"""

from app.algorithms.integer_linear_programming import (
    IntegerLinearProgramming, 
    solve_with_ilp, 
    PULP_AVAILABLE,
    ILPConfig
)

print("=" * 60)
print("INTEGER LINEAR PROGRAMMING TEST")
print("=" * 60)
print(f"PuLP Available: {PULP_AVAILABLE}")

# Test data - 5 projects (2 BITIRME, 3 ARA), 3 faculty, 2 classes
test_data = {
    'projects': [
        {'id': 1, 'responsible_id': 1, 'type': 'BITIRME', 'name': 'Bitirme Proje 1'},
        {'id': 2, 'responsible_id': 2, 'type': 'BITIRME', 'name': 'Bitirme Proje 2'},
        {'id': 3, 'responsible_id': 3, 'type': 'ARA', 'name': 'Ara Proje 1'},
        {'id': 4, 'responsible_id': 1, 'type': 'ARA', 'name': 'Ara Proje 2'},
        {'id': 5, 'responsible_id': 2, 'type': 'ARA', 'name': 'Ara Proje 3'},
    ],
    'instructors': [
        {'id': 1, 'name': 'Prof. Ahmet', 'type': 'instructor'},
        {'id': 2, 'name': 'Prof. Mehmet', 'type': 'instructor'},
        {'id': 3, 'name': 'Prof. Zeynep', 'type': 'instructor'},
        {'id': 4, 'name': 'Ars. Gor. Ali', 'type': 'assistant', 'is_research_assistant': True},
    ],
    'classrooms': [
        {'id': 1, 'name': 'D105'},
        {'id': 2, 'name': 'D106'},
    ],
    'class_count': 2,
}

print("\n--- Input Data ---")
print(f"Projects: {len(test_data['projects'])} (2 BITIRME, 3 ARA)")
print(f"Faculty: 3 (excluding research assistant)")
print(f"Classrooms: 2")

# Test config
config = {
    'max_time_seconds': 60,
    'priority_mode': 'BITIRME_ONCE',  # BITIRME before ARA (mandatory)
    'workload_constraint_mode': 'SOFT_ONLY',
    'use_warm_start': True,  # Re-enable warm start
}

print("\n--- Running ILP Optimization ---")
result = solve_with_ilp(test_data, config)

print("\n--- Results ---")
print(f"Status: {result['status']}")
print(f"Cost: {result['cost']}")
print(f"Fitness: {result['fitness']}")
print(f"Class Count: {result['class_count']}")
print(f"Schedule Count: {len(result['schedule'])}")

if result['schedule']:
    print("\n--- Schedule ---")
    print(f"{'Project':<12} {'Type':<10} {'Class':<10} {'Slot':<6} {'PS':<6} {'J1':<6}")
    print("-" * 56)
    
    # Group by project type for display
    schedule_sorted = sorted(
        result['schedule'], 
        key=lambda x: (x['class_id'], x['order_in_class'])
    )
    
    for row in schedule_sorted:
        project = next(
            (p for p in test_data['projects'] if p['id'] == row['project_id']), 
            None
        )
        p_type = project['type'] if project else 'UNK'
        print(
            f"P{row['project_id']:<10} {p_type:<10} {row['class_name']:<10} "
            f"{row['order_in_class']:<6} {row['ps_id']:<6} {row['j1_id']:<6}"
        )

    # Verify BITIRME before ARA constraint (per-class)
    print("\n--- Constraint Verification ---")
    from collections import defaultdict
    
    # Group by class
    class_projects = defaultdict(lambda: {'BITIRME': [], 'ARA': []})
    for row in result['schedule']:
        project = next(
            (p for p in test_data['projects'] if p['id'] == row['project_id']), 
            None
        )
        if project:
            class_id = row['class_id']
            slot_in_class = row['order_in_class']
            p_type = project['type']
            class_projects[class_id][p_type].append(slot_in_class)
    
    # Check per-class: max(BITIRME slots) < min(ARA slots) in each class
    constraint_ok = True
    for class_id in sorted(class_projects.keys()):
        bitirme_slots = class_projects[class_id]['BITIRME']
        ara_slots = class_projects[class_id]['ARA']
        if bitirme_slots and ara_slots:
            max_bitirme = max(bitirme_slots)
            min_ara = min(ara_slots)
            if max_bitirme >= min_ara:
                constraint_ok = False
                print(f"  Class {class_id}: BITIRME max={max_bitirme}, ARA min={min_ara} [FAIL]")
            else:
                print(f"  Class {class_id}: BITIRME max={max_bitirme}, ARA min={min_ara} [OK]")
    
    print(f"BITIRME before ARA (per-class): {'[OK] PASSED' if constraint_ok else '[X] FAILED'}")

    # Workload check
    print("\n--- Workload Distribution ---")
    workload = {}
    for row in result['schedule']:
        ps_id = row['ps_id']
        j1_id = row['j1_id']
        workload[ps_id] = workload.get(ps_id, 0) + 1
        workload[j1_id] = workload.get(j1_id, 0) + 1
    
    for teacher_id, load in sorted(workload.items()):
        teacher = next(
            (t for t in test_data['instructors'] if t['id'] == teacher_id), 
            None
        )
        name = teacher['name'] if teacher else f"T{teacher_id}"
        print(f"  {name}: {load} duties")

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)

