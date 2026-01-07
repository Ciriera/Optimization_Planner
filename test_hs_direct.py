"""
Harmony Search Test - Doğrudan Algoritma Testi
"""
import sys
sys.path.insert(0, 'e:\\Optimization_Planner-main_v2\\Optimization_Planner-main')

from app.algorithms.harmony_search import HarmonySearch
from collections import defaultdict

# Test verisi oluştur
projects = []
instructors = []
classrooms = []
timeslots = []

# 21 öğretmen
for i in range(1, 22):
    instructors.append({"id": i, "name": f"Ogretmen {i}"})

# 7 sınıf
for i in range(1, 8):
    classrooms.append({"id": i, "name": f"Sinif {i}"})

# 16 timeslot
for i in range(1, 17):
    timeslots.append({"id": i, "start_time": f"{8+i}:00"})

# Projeler: 38 bitirme, 43 ara (PSO testindeki gibi)
project_id = 1

# ARA projeler (öncelikli olmalı)
for i in range(43):
    responsible_id = (i % 21) + 1  # 1-21 arası döngüsel
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

print("=" * 60)
print("Harmony Search Test - ARA ONCELIKLI")
print("=" * 60)
print(f"Projects: {len(projects)}")
print(f"  Ara: {len([p for p in projects if p['type'] == 'ara'])}")
print(f"  Bitirme: {len([p for p in projects if p['type'] == 'bitirme'])}")
print(f"Instructors: {len(instructors)}")
print(f"Classrooms: {len(classrooms)}")
print(f"Timeslots: {len(timeslots)}")

# Harmony Search çalıştır
hs = HarmonySearch()
result = hs.optimize({
    "projects": projects,
    "instructors": instructors,
    "classrooms": classrooms,
    "timeslots": timeslots
})

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)

print(f"Status: {result.get('status')}")
print(f"Algorithm: {result.get('algorithm')}")

assignments = result.get("assignments", [])
print(f"Assignments count: {len(assignments)}")
print(f"Fitness: {result.get('fitness')}")

if assignments:
    print("\nIlk 10 atama:")
    for a in assignments[:10]:
        ptype = a.get("project_type", "?")
        print(f"  Project {a.get('project_id')} ({ptype}) -> Timeslot {a.get('ts_order', '?')}, Class {a.get('classroom_id')}")
    
    # ARA önceliği kontrolü
    ara_orders = [a.get("ts_order", 0) for a in assignments if a.get("project_type") == "ara"]
    bitirme_orders = [a.get("ts_order", 0) for a in assignments if a.get("project_type") == "bitirme"]
    
    if ara_orders and bitirme_orders:
        print(f"\nAra slot araligi: {min(ara_orders)} - {max(ara_orders)}")
        print(f"Bitirme slot araligi: {min(bitirme_orders)} - {max(bitirme_orders)}")
        
        if max(ara_orders) <= min(bitirme_orders):
            print("✅ Ara onceligi SAGLANDI!")
        else:
            print("⚠️ Ara onceligi kismi ihlal (overlap)")
    
    # Jury2 kontrolü
    print("\n--- JURY2 KONTROLU ---")
    jury2_check = all(a.get("jury2") for a in assignments)
    print(f"Jury2 Placeholder: {'OK' if jury2_check else 'FAIL'}")
    
    # Hard violations
    print("\n--- HARD VIOLATIONS ---")
    violations = 0
    usage = defaultdict(list)
    
    for a in assignments:
        ts_id = a.get("timeslot_id")
        rid = a.get("responsible_id")
        jid = a.get("jury1_id")
        
        if jid and jid == rid:
            violations += 1
        if jid is None:
            violations += 1
        if rid and ts_id:
            usage[(rid, ts_id)].append("r")
        if jid and ts_id:
            usage[(jid, ts_id)].append("j")
    
    for key, roles in usage.items():
        if len(roles) > 1:
            violations += len(roles) - 1
    
    print(f"Hard violations: {violations}")
    
    # Sınıf sürekliliği analizi
    print("\n--- SINIF SUREKLILIGI ANALIZI ---")
    instructor_tasks = defaultdict(list)
    for a in assignments:
        ts_order = a.get("ts_order", 0)
        cid = a.get("classroom_id")
        for inst in a.get("instructors", []):
            if isinstance(inst, dict):
                iid = inst.get("id")
                if iid == -1:
                    continue
            else:
                iid = inst
            if iid:
                instructor_tasks[iid].append({"ts_order": ts_order, "cid": cid})
    
    total_pairs = 0
    same_class_pairs = 0
    for iid, tasks in instructor_tasks.items():
        if len(tasks) < 2:
            continue
        sorted_tasks = sorted(tasks, key=lambda x: x["ts_order"])
        for i in range(len(sorted_tasks) - 1):
            if sorted_tasks[i+1]["ts_order"] - sorted_tasks[i]["ts_order"] == 1:
                total_pairs += 1
                if sorted_tasks[i]["cid"] == sorted_tasks[i+1]["cid"]:
                    same_class_pairs += 1
    
    print(f"Toplam ardisik gorev cifti: {total_pairs}")
    print(f"Ayni sinifta ardisik: {same_class_pairs}")
    if total_pairs > 0:
        print(f"Sinif surekliligi orani: {100*same_class_pairs/total_pairs:.1f}%")
    
    # Workload analizi
    print("\n--- IS YUKU DAGILIMI ---")
    workload = defaultdict(int)
    for a in assignments:
        rid = a.get("responsible_id")
        j1id = a.get("jury1_id")
        if rid:
            workload[rid] += 1
        if j1id:
            workload[j1id] += 1
    
    loads = list(workload.values())
    if loads:
        max_load = max(loads)
        min_load = min(loads)
        avg_load = sum(loads) / len(loads)
        diff = max_load - min_load
        
        print(f"Max yuk: {max_load}")
        print(f"Min yuk: {min_load}")
        print(f"Ortalama: {avg_load:.1f}")
        print(f"Max-Min fark: {diff}")
        
        if diff <= 4:
            print("✅ ±2 UNIFORM DAGILIM SAGLANDI!")
        else:
            print(f"❌ ±2 UNIFORM IHLAL! Fark {diff} > 4")

else:
    print("\nHATA NO ASSIGNMENTS!")
