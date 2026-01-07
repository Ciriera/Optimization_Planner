"""
Real Simplex Priority Mode Test
"""
import sys
sys.path.insert(0, 'e:\\Optimization_Planner-main_v2\\Optimization_Planner-main')

from app.algorithms.real_simplex import RealSimplexAlgorithm
from collections import defaultdict

# Test verisi oluştur
projects = []
instructors = []
classrooms = []
timeslots = []

# 21 öğretmen
for i in range(1, 22):
    instructors.append({"id": i, "name": f"Ogretmen {i}", "type": "instructor"})

# 7 sınıf
for i in range(1, 8):
    classrooms.append({"id": i, "name": f"Sinif {i}"})

# 16 timeslot
for i in range(1, 17):
    timeslots.append({"id": i, "start_time": f"{8+i}:00", "end_time": f"{9+i}:00"})

# Projeler: 38 bitirme, 43 ara
project_id = 1

# ARA projeler
for i in range(43):
    responsible_id = (i % 21) + 1
    projects.append({
        "id": project_id,
        "type": "ara",
        "title": f"Ara Proje {i+1}",
        "responsible_id": responsible_id
    })
    project_id += 1

# Bitirme projeler
for i in range(38):
    responsible_id = (i % 21) + 1
    projects.append({
        "id": project_id,
        "type": "bitirme",
        "title": f"Bitirme Projesi {i+1}",
        "responsible_id": responsible_id
    })
    project_id += 1

data = {
    "projects": projects,
    "instructors": instructors,
    "classrooms": classrooms,
    "timeslots": timeslots
}

def test_priority_mode(priority_mode, expected_first_type):
    print("=" * 60)
    print(f"TEST: {priority_mode}")
    print("=" * 60)
    
    # Params ile priority mode ayarla
    params = {
        "project_priority": priority_mode
    }
    
    # Real Simplex çalıştır
    algo = RealSimplexAlgorithm(params=params)
    result = algo.optimize(data)
    
    print(f"Status: {result.get('status')}")
    print(f"Algorithm: {result.get('algorithm')}")
    
    assignments = result.get("assignments", [])
    print(f"Assignments count: {len(assignments)}")
    
    if assignments:
        # İlk 10 atamayı göster
        print("\nIlk 10 atama:")
        for a in assignments[:10]:
            ptype = a.get("project_type", "?")
            print(f"  Project {a.get('project_id')} ({ptype}) -> Slot {a.get('ts_order', '?')}")
        
        # Proje türü kontrolü
        ara_orders = [a.get("ts_order", 0) for a in assignments if str(a.get("project_type", "")).lower() in ("ara", "interim")]
        bitirme_orders = [a.get("ts_order", 0) for a in assignments if str(a.get("project_type", "")).lower() in ("bitirme", "final")]
        
        if ara_orders and bitirme_orders:
            print(f"\nAra slot araligi: {min(ara_orders)} - {max(ara_orders)}")
            print(f"Bitirme slot araligi: {min(bitirme_orders)} - {max(bitirme_orders)}")
            
            if priority_mode == "midterm_priority":
                if max(ara_orders) <= min(bitirme_orders):
                    print("✅ ARA onceligi SAGLANDI!")
                    return True
                else:
                    print("❌ ARA onceligi IHLAL!")
                    return False
            elif priority_mode == "final_exam_priority":
                if max(bitirme_orders) <= min(ara_orders):
                    print("✅ BITIRME onceligi SAGLANDI!")
                    return True
                else:
                    print("❌ BITIRME onceligi IHLAL!")
                    return False
            else:
                # none - öncelik kontrolü yok
                print("✅ Onceliksiz mod - OK")
                return True
    
    return False

# Test all priority modes
print("\n" + "=" * 60)
print("REAL SIMPLEX PRIORITY MODE TESTS")
print("=" * 60 + "\n")

results = {}

# Test 1: midterm_priority (ARA öncelikli)
try:
    results["midterm_priority"] = test_priority_mode("midterm_priority", "ara")
except Exception as e:
    print(f"ERROR: {e}")
    results["midterm_priority"] = False

print("\n")

# Test 2: final_exam_priority (Bitirme öncelikli)
try:
    results["final_exam_priority"] = test_priority_mode("final_exam_priority", "bitirme")
except Exception as e:
    print(f"ERROR: {e}")
    results["final_exam_priority"] = False

print("\n")

# Test 3: none (Önceliksiz)
try:
    results["none"] = test_priority_mode("none", None)
except Exception as e:
    print(f"ERROR: {e}")
    results["none"] = False

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for mode, success in results.items():
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {mode}: {status}")
