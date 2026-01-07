"""
PSO Test Script - Süreklilik ve Jüri2 Kontrolü
"""
import logging
import sys
import os

sys.path.insert(0, os.getcwd())

from app.algorithms.pso import PSO, JURY2_PLACEHOLDER

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Test verisi
data = {
    "projects": [
        # Bitirme projeleri (5 adet)
        {"id": 1, "type": "FINAL", "responsible_id": 1},
        {"id": 2, "type": "Bitirme", "responsible_id": 2},
        {"id": 3, "type": "FINAL", "responsible_id": 3},
        {"id": 4, "type": "Bitirme", "responsible_id": 4},
        {"id": 5, "type": "FINAL", "responsible_id": 5},
        # Ara projeler (5 adet)
        {"id": 6, "type": "INTERIM", "responsible_id": 1},
        {"id": 7, "type": "Ara", "responsible_id": 2},
        {"id": 8, "type": "INTERIM", "responsible_id": 3},
        {"id": 9, "type": "Ara", "responsible_id": 4},
        {"id": 10, "type": "INTERIM", "responsible_id": 5},
    ],
    "instructors": [
        {"id": 1, "name": "Dr. A"},
        {"id": 2, "name": "Dr. B"},
        {"id": 3, "name": "Dr. C"},
        {"id": 4, "name": "Dr. D"},
        {"id": 5, "name": "Dr. E"},
        {"id": 6, "name": "Dr. F"},
        {"id": 7, "name": "Dr. G"},
    ],
    "classrooms": [
        {"id": 1, "name": "D101"},
        {"id": 2, "name": "D102"},
    ],
    "timeslots": [
        {"id": 1, "start_time": "09:00"},
        {"id": 2, "start_time": "09:30"},
        {"id": 3, "start_time": "10:00"},
        {"id": 4, "start_time": "10:30"},
        {"id": 5, "start_time": "11:00"},
        {"id": 6, "start_time": "11:30"},
    ]
}

print("=" * 70)
print("PSO TEST - Süreklilik ve Jüri2 Kontrolü")
print("=" * 70)

algo = PSO({"n_particles": 10, "n_iterations": 50})
result = algo.optimize(data)

print("\n" + "=" * 70)
print("ATAMALAR")
print("=" * 70)

assignments = result.get("assignments", [])
assignments.sort(key=lambda x: (x["slot_index"], x["classroom_id"]))

for a in assignments:
    ptype = a.get("project_type", "?").upper()[:3]
    pid = a.get("project_id")
    slot = a.get("slot_index")
    rid = a.get("responsible_id")
    j1 = a.get("jury1_id")
    j2 = a.get("jury2")
    
    j2_ok = "✓" if j2 == JURY2_PLACEHOLDER else "✗"
    
    print(f"Slot {slot}: Proje {pid} ({ptype}) | Sorumlu: {rid} | Juri1: {j1} | Juri2: {j2_ok}")

print("\n" + "=" * 70)
print("KONTROLLER")
print("=" * 70)

# Bitirme önceliği
bitirme_slots = [a["slot_index"] for a in assignments if a.get("project_type") == "bitirme"]
ara_slots = [a["slot_index"] for a in assignments if a.get("project_type") == "ara"]

if bitirme_slots and ara_slots:
    max_b = max(bitirme_slots)
    min_a = min(ara_slots)
    if max_b <= min_a:
        print(f"✓ Bitirme Önceliği: OK (max_bitirme={max_b} <= min_ara={min_a})")
    else:
        print(f"✗ Bitirme Önceliği: FAIL")

# Jury2 kontrolü
jury2_ok = all(a.get("jury2") == JURY2_PLACEHOLDER for a in assignments)
print(f"{'✓' if jury2_ok else '✗'} Jury2 Placeholder: {'ALL OK' if jury2_ok else 'MISSING'}")

# Hard violations
violations = algo._count_hard_violations(assignments)
print(f"{'✓' if violations == 0 else '✗'} Hard Violations: {violations}")

# Süreklilik
continuity = algo._calculate_continuity_score(assignments)
print(f"{'✓' if continuity > 50 else '⚠'} Süreklilik Skoru: {continuity:.1f}%")

# İş yükü
from collections import Counter
workload = Counter()
for a in assignments:
    for iid in a.get("instructors", []):
        workload[iid] += 1

print(f"\nİş Yükü Dağılımı: {dict(workload)}")
print(f"Min: {min(workload.values())}, Max: {max(workload.values())}, Avg: {sum(workload.values())/len(workload):.1f}")

print("\n" + "=" * 70)
print(f"Final Fitness: {result.get('fitness', 0):.2f}")
print("=" * 70)
