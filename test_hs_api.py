"""
Harmony Search API Test - ARA Proje Öncelikli
"""
import requests

BASE_URL = "http://localhost:8002/api"

# 1. Verileri çek
print("=" * 60)
print("API uzerinden veri cekiliyor...")
print("=" * 60)

projects = requests.get(f"{BASE_URL}/projects").json()
instructors = requests.get(f"{BASE_URL}/instructors").json()
classrooms = requests.get(f"{BASE_URL}/classrooms").json()
timeslots = requests.get(f"{BASE_URL}/time-slots").json()

print(f"Projects: {len(projects)}")
print(f"Instructors: {len(instructors)}")
print(f"Classrooms: {len(classrooms)}")
print(f"Timeslots: {len(timeslots)}")

# Proje türleri
bitirme_count = len([p for p in projects if str(p.get("type", "")).lower() in ["bitirme", "final"]])
ara_count = len([p for p in projects if str(p.get("type", "")).lower() in ["ara", "interim"]])
print(f"\nBitirme (FINAL): {bitirme_count}, Ara (INTERIM): {ara_count}")

# 2. Harmony Search çalıştır
print("\n" + "=" * 60)
print("Harmony Search calistiriliyor (ARA ONCELIKLI)...")
print("=" * 60)

payload = {
    "projects": projects,
    "instructors": instructors,
    "classrooms": classrooms,
    "timeslots": timeslots
}

response = requests.post(f"{BASE_URL}/optimize/harmony", json=payload)
result = response.json()

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
    
    # ARA önceliği kontrolü (PSO'nun tersi)
    ara_orders = [a.get("ts_order", 0) for a in assignments if a.get("project_type") == "ara"]
    bitirme_orders = [a.get("ts_order", 0) for a in assignments if a.get("project_type") == "bitirme"]
    
    if ara_orders and bitirme_orders:
        print(f"\nAra slot araligi: {min(ara_orders)} - {max(ara_orders)}")
        print(f"Bitirme slot araligi: {min(bitirme_orders)} - {max(bitirme_orders)}")
        
        if max(ara_orders) <= min(bitirme_orders):
            print("OK Ara onceligi SAGLANDI!")
        else:
            print("HATA Ara onceligi IHLAL!")
    
    # Jury2 kontrolü
    print("\n--- JURY2 KONTROLU ---")
    jury2_missing = [a for a in assignments if not a.get("jury2")]
    if len(jury2_missing) == 0:
        print("Jury2 Placeholder: OK - Tumunde atandi")
        sample = [a.get("jury2") for a in assignments[:3]]
        print(f"Ornek degerler: {sample}")
    else:
        print(f"Jury2 eksik: {len(jury2_missing)} atamada yok!")
    
    # Hard violations
    print("\n--- HARD VIOLATIONS ---")
    violations = 0
    from collections import defaultdict
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
    
    # instructors format kontrolü
    print("\n--- INSTRUCTORS FORMAT ---")
    first = assignments[0]
    print(f"Ilk atama instructors: {first.get('instructors')}")
    
    insts = first.get("instructors", [])
    if len(insts) >= 3 and isinstance(insts[-1], dict) and insts[-1].get("is_placeholder"):
        print("Format: ID ARRAY + PLACEHOLDER (Real Simplex format - OK)")
        print("Placeholder mevcut: EVET")
    else:
        print("Format kontrolü gerekli")
    
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
        
        # Responsible ve Jury ayrı ayrı
        resp_workload = defaultdict(int)
        jury_workload = defaultdict(int)
        for a in assignments:
            rid = a.get('responsible_id')
            j1id = a.get('jury1_id')
            if rid:
                resp_workload[rid] += 1
            if j1id:
                jury_workload[j1id] += 1
        
        resp_loads = list(resp_workload.values())
        jury_loads = list(jury_workload.values())
        print(f"  Resp dağılımı: min={min(resp_loads)}, max={max(resp_loads)}")
        print(f"  Jury dağılımı: min={min(jury_loads)}, max={max(jury_loads)}")
        
        if diff <= 4:
            print("✅ ±2 UNIFORM DAGILIM SAGLANDI!")
        else:
            print(f"❌ ±2 UNIFORM IHLAL! Fark {diff} > 4")

else:
    print("\nHATA NO ASSIGNMENTS!")
