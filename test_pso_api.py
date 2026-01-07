"""
PSO Test - API üzerinden veri çek ve test et
"""
import sys
sys.path.insert(0, '.')
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 60)
print("API uzerinden veri cekiliyor...")
print("=" * 60)

# Projects
try:
    r = requests.get(f"{BASE_URL}/projects/")
    projects = r.json()
    print(f"Projects: {len(projects)}")
except Exception as e:
    print(f"Projects error: {e}")
    projects = []

# Instructors
try:
    r = requests.get(f"{BASE_URL}/instructors/")
    instructors = r.json()
    print(f"Instructors: {len(instructors)}")
except Exception as e:
    print(f"Instructors error: {e}")
    instructors = []

# Classrooms
try:
    r = requests.get(f"{BASE_URL}/classrooms/")
    classrooms = r.json()
    print(f"Classrooms: {len(classrooms)}")
except Exception as e:
    print(f"Classrooms error: {e}")
    classrooms = []

# Timeslots
try:
    r = requests.get(f"{BASE_URL}/timeslots/")
    timeslots = r.json()
    print(f"Timeslots: {len(timeslots)}")
except Exception as e:
    print(f"Timeslots error: {e}")
    timeslots = []

if not projects:
    print("Proje verisi yok!")
    sys.exit(1)

# Proje turlerini goster (case-insensitive)
bitirme_count = len([p for p in projects if str(p.get('type', '')).lower() in ['bitirme', 'final']])
ara_count = len([p for p in projects if str(p.get('type', '')).lower() in ['ara', 'interim']])
print(f"\nBitirme (FINAL): {bitirme_count}, Ara (INTERIM): {ara_count}")

# ilk 3 projeyi goster
print("\nIlk 3 proje:")
for p in projects[:3]:
    print(f"  id={p.get('id')}, type={p.get('type')}, title={p.get('title', '')[:30]}")

# Veriyi PSO formatina cevir
pso_projects = []
for p in projects:
    pso_projects.append({
        "id": p.get("id"),
        "type": p.get("type"),
        "title": p.get("title"),
        "responsible_id": p.get("responsible_instructor_id")
    })

pso_instructors = []
for i in instructors:
    pso_instructors.append({
        "id": i.get("id"),
        "name": i.get("name"),
        "type": i.get("type", "instructor")
    })

pso_classrooms = []
for c in classrooms:
    pso_classrooms.append({
        "id": c.get("id"),
        "name": c.get("name")
    })

pso_timeslots = []
for t in timeslots:
    pso_timeslots.append({
        "id": t.get("id"),
        "start_time": t.get("start_time"),
        "end_time": t.get("end_time")
    })

print()
print("=" * 60)
print("PSO calistiriliyor...")
print("=" * 60)

from app.algorithms.pso import PSO

test_data = {
    "projects": pso_projects,
    "instructors": pso_instructors,
    "classrooms": pso_classrooms,
    "timeslots": pso_timeslots
}

print(f"PSO'ya gonderilen veri:")
print(f"  projects: {len(test_data['projects'])}")
print(f"  instructors: {len(test_data['instructors'])}")
print(f"  classrooms: {len(test_data['classrooms'])}")
print(f"  timeslots: {len(test_data['timeslots'])}")

pso = PSO()
result = pso.optimize(test_data)

print()
print("=" * 60)
print("RESULT")
print("=" * 60)
print(f"Status: {result.get('status')}")
print(f"Algorithm: {result.get('algorithm')}")
print(f"Assignments count: {len(result.get('assignments', []))}")
print(f"Fitness: {result.get('fitness')}")

assignments = result.get('assignments', [])
if assignments:
    # Ilk 10 atamayi goster
    print("\nIlk 10 atama:")
    for a in assignments[:10]:
        print(f"  Project {a.get('project_id')} ({a.get('project_type')}) -> Timeslot {a.get('timeslot_id')}, Class {a.get('classroom_id')}")
    
    # Bitirme/Ara dogrulama
    bitirme_slots = [a.get('timeslot_id') for a in assignments if a.get('project_type') == 'bitirme']
    ara_slots = [a.get('timeslot_id') for a in assignments if a.get('project_type') == 'ara']
    
    if bitirme_slots and ara_slots:
        print(f"\nBitirme slot araligi: {min(bitirme_slots)} - {max(bitirme_slots)}")
        print(f"Ara slot araligi: {min(ara_slots)} - {max(ara_slots)}")
        
        if max(bitirme_slots) <= min(ara_slots):
            print("OK Bitirme onceligi SAGLANDI!")
        else:
            print("HATA Bitirme onceligi IHLAL!")
    
    # JURY2 kontrolü
    print("\n--- JURY2 KONTROLU ---")
    jury2_values = [a.get('jury2') for a in assignments]
    jury2_ok = all(v == '[Araştırma Görevlisi]' for v in jury2_values)
    print(f"Jury2 Placeholder: {'OK - Tumunde atandi' if jury2_ok else 'EKSIK!'}")
    print(f"Ornek degerler: {jury2_values[:3]}")
    
    # Hard violation kontrolü
    print("\n--- HARD VIOLATIONS ---")
    violations = 0
    for a in assignments:
        if a.get('jury1_id') is None:
            violations += 1
        if a.get('jury1_id') == a.get('responsible_id'):
            violations += 1
    print(f"Hard violations: {violations}")
    
    # INSTRUCTORS FORMAT kontrolü
    print("\n--- INSTRUCTORS FORMAT ---")
    sample = assignments[0] if assignments else {}
    instructor_list = sample.get('instructors', [])
    print(f"Ilk atama instructors: {instructor_list}")
    
    # Real Simplex formatı: [id1 (int), id2 (int), {placeholder}]
    if instructor_list:
        # Check if it's the Real Simplex format (IDs + placeholder dict)
        has_integer_ids = any(isinstance(i, int) for i in instructor_list)
        has_placeholder = any(isinstance(i, dict) and i.get('is_placeholder') for i in instructor_list)
        
        if has_integer_ids and has_placeholder:
            print("Format: ID ARRAY + PLACEHOLDER (Real Simplex format - OK)")
            print(f"Placeholder mevcut: EVET")
        elif isinstance(instructor_list[0], dict):
            print("Format: FULL OBJECT ARRAY (Eski format)")
            has_placeholder = any(i.get('is_placeholder') for i in instructor_list if isinstance(i, dict))
            print(f"Placeholder mevcut: {'EVET' if has_placeholder else 'HAYIR'}")
        else:
            print("Format: BILINMEYEN")
    
    # SINIF SÜREKLİLİĞİ ANALİZİ
    print("\n--- SINIF SUREKLILIGI ANALIZI ---")
    from collections import defaultdict
    
    # Her öğretmenin ts_order ve classroom_id listesi
    instructor_tasks = defaultdict(list)
    for a in assignments:
        rid = a.get('responsible_id')
        j1id = a.get('jury1_id')
        ts_order = a.get('ts_order')
        cid = a.get('classroom_id')
        
        if rid:
            instructor_tasks[rid].append({'ts': ts_order, 'cid': cid})
        if j1id:
            instructor_tasks[j1id].append({'ts': ts_order, 'cid': cid})
    
    total_consecutive = 0
    total_same_class_consecutive = 0
    total_pairs = 0
    
    for iid, tasks in instructor_tasks.items():
        if len(tasks) < 2:
            continue
        sorted_tasks = sorted(tasks, key=lambda x: x['ts'])
        for i in range(len(sorted_tasks) - 1):
            curr = sorted_tasks[i]
            next_t = sorted_tasks[i + 1]
            if next_t['ts'] - curr['ts'] == 1:  # Ardışık
                total_consecutive += 1
                if curr['cid'] == next_t['cid']:  # Aynı sınıf
                    total_same_class_consecutive += 1
            total_pairs += 1
    
    print(f"Toplam ardisik gorev cifti: {total_consecutive}")
    print(f"Ayni sinifta ardisik: {total_same_class_consecutive}")
    if total_consecutive > 0:
        continuity_rate = (total_same_class_consecutive / total_consecutive) * 100
        print(f"Sinif surekliligi orani: {continuity_rate:.1f}%")
    
    # İŞ YÜKÜ DAĞILIMI ANALİZİ
    print("\n--- IS YUKU DAGILIMI ---")
    workload = defaultdict(int)
    for a in assignments:
        rid = a.get('responsible_id')
        j1id = a.get('jury1_id')
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

