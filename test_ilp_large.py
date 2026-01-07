"""
Large scale test for Integer Linear Programming algorithm.
Tests with 81 projects (50 ARA + 31 BITIRME) - realistic scenario.
"""

import time
from app.algorithms.integer_linear_programming import (
    IntegerLinearProgramming, 
    solve_with_ilp, 
    PULP_AVAILABLE
)

print("=" * 70)
print("INTEGER LINEAR PROGRAMMING - LARGE SCALE TEST")
print("=" * 70)
print(f"PuLP Available: {PULP_AVAILABLE}")

# Generate realistic test data - 81 projects
# 31 BITIRME + 50 ARA, 12 faculty members, 6 classrooms
num_bitirme = 31
num_ara = 50
num_faculty = 12
num_classrooms = 6

# Create faculty
instructors = [
    {'id': i + 1, 'name': f'Prof. {chr(65 + i)}', 'type': 'instructor'}
    for i in range(num_faculty)
]
# Add 4 research assistants (not part of optimization)
for i in range(4):
    instructors.append({
        'id': num_faculty + i + 1,
        'name': f'Ars. Gor. {chr(88 + i)}',  # X, Y, Z, [
        'type': 'assistant',
        'is_research_assistant': True
    })

# Create projects - distribute supervisors evenly
projects = []
project_id = 1

# BITIRME projects
for i in range(num_bitirme):
    supervisor_id = (i % num_faculty) + 1
    projects.append({
        'id': project_id,
        'responsible_id': supervisor_id,
        'type': 'BITIRME',
        'name': f'Bitirme Proje {project_id}'
    })
    project_id += 1

# ARA projects
for i in range(num_ara):
    supervisor_id = (i % num_faculty) + 1
    projects.append({
        'id': project_id,
        'responsible_id': supervisor_id,
        'type': 'ARA',
        'name': f'Ara Proje {project_id}'
    })
    project_id += 1

# Create classrooms
classrooms = [
    {'id': i + 1, 'name': f'D{105 + i}'}
    for i in range(num_classrooms)
]

test_data = {
    'projects': projects,
    'instructors': instructors,
    'classrooms': classrooms,
    'class_count': num_classrooms,
}

print("\n--- Input Data ---")
print(f"Projects: {len(projects)} ({num_bitirme} BITIRME, {num_ara} ARA)")
print(f"Faculty: {num_faculty} (+ 4 research assistants excluded)")
print(f"Classrooms: {num_classrooms}")

# Config - with warm start for faster solving
config = {
    'max_time_seconds': 60,   # 1 minute (reduced thanks to warm start)
    'priority_mode': 'BITIRME_ONCE',
    'workload_constraint_mode': 'SOFT_ONLY',
    'weight_uniformity': 100,
    'weight_continuity': 10,
    'weight_class_change': 5,
    'use_warm_start': True,   # Enable warm start
    'mip_gap': 0.02,          # Accept 2% gap from optimal
}

print("\n--- Running ILP Optimization (max 60 seconds with warm start) ---")
start_time = time.time()
result = solve_with_ilp(test_data, config)
elapsed = time.time() - start_time

print(f"\n--- Results (completed in {elapsed:.2f}s) ---")
print(f"Status: {result['status']}")
print(f"Cost: {result['cost']}")
print(f"Class Count: {result['class_count']}")
print(f"Schedule Count: {len(result['schedule'])}")

if result['schedule']:
    # Verify constraints
    print("\n--- Constraint Verification ---")
    
    # 1. All projects assigned
    scheduled_ids = {row['project_id'] for row in result['schedule']}
    expected_ids = {p['id'] for p in projects}
    missing = expected_ids - scheduled_ids
    print(f"Coverage: {len(scheduled_ids)}/{len(expected_ids)} projects")
    if missing:
        print(f"  Missing: {missing}")
    else:
        print("  [OK] All projects scheduled")
    
    # 2. BITIRME before ARA
    bitirme_slots = []
    ara_slots = []
    for row in result['schedule']:
        project = next((p for p in projects if p['id'] == row['project_id']), None)
        if project:
            if project['type'] == 'BITIRME':
                bitirme_slots.append(row['global_slot'])
            else:
                ara_slots.append(row['global_slot'])
    
    max_bitirme = max(bitirme_slots) if bitirme_slots else -1
    min_ara = min(ara_slots) if ara_slots else float('inf')
    constraint_ok = max_bitirme <= min_ara
    print(f"BITIRME max slot: {max_bitirme}, ARA min slot: {min_ara}")
    print(f"  {'[OK]' if constraint_ok else '[FAIL]'} BITIRME before ARA constraint")
    
    # 3. Workload distribution
    print("\n--- Workload Distribution ---")
    workload = {}
    for row in result['schedule']:
        ps_id = row['ps_id']
        j1_id = row['j1_id']
        workload[ps_id] = workload.get(ps_id, 0) + 1
        workload[j1_id] = workload.get(j1_id, 0) + 1
    
    loads = list(workload.values())
    avg_load = sum(loads) / len(loads) if loads else 0
    min_load = min(loads) if loads else 0
    max_load = max(loads) if loads else 0
    
    print(f"Total duties: {sum(loads)}")
    print(f"Average: {avg_load:.1f}, Min: {min_load}, Max: {max_load}")
    print(f"Range: {max_load - min_load} (target: <=4)")
    
    # Print per faculty
    for teacher_id in sorted(workload.keys()):
        load = workload[teacher_id]
        teacher = next((t for t in instructors if t['id'] == teacher_id), None)
        name = teacher['name'] if teacher else f"T{teacher_id}"
        deviation = load - avg_load
        bar = '*' * load
        print(f"  {name:12}: {load:2} duties ({deviation:+.1f}) {bar}")
    
    # 4. Projects per classroom
    print("\n--- Classroom Distribution ---")
    class_counts = {}
    for row in result['schedule']:
        cname = row['class_name']
        class_counts[cname] = class_counts.get(cname, 0) + 1
    
    for cname, count in sorted(class_counts.items()):
        print(f"  {cname}: {count} projects")
    
    # 5. Back-to-back check (gaps)
    print("\n--- Gap Analysis ---")
    gaps_found = 0
    for cname in sorted(class_counts.keys()):
        class_slots = sorted([
            row['order_in_class'] 
            for row in result['schedule'] 
            if row['class_name'] == cname
        ])
        for i in range(len(class_slots) - 1):
            if class_slots[i + 1] - class_slots[i] > 1:
                gaps_found += 1
    
    print(f"Gaps found: {gaps_found}")
    print(f"  {'[OK]' if gaps_found == 0 else '[WARN]'} Back-to-back scheduling")

else:
    print("\n[ERROR] No schedule produced!")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)

