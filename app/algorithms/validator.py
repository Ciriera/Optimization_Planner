"""
Central validator & repair utilities for optimizationplanner requirements.
Provides: validate_solution(), repair_solution(), and report generators.

Gereksinimlere göre güncellendi:
- 50 Ara Proje + 31 Bitirme Proje = 81 proje tam coverage
- Rol kuralları: Bitirme = 1 sorumlu + 1+ jüri, Ara = 1 sorumlu
- Aynı kişi aynı projede hem sorumlu hem jüri olamaz
- Tüm öğretim üyeleri en az 1 görev almalı, yük dengeli (±1)
- Zaman slotları: 09:00-09:30 = 1000 → 16:00-16:30 = 400
- 16:30 sonrası cezalı slotlar (-9999 ceza)
- Sınıf sayısı: 5-7 arası
- Gap: 0 (slot boşlukları olmamalı)
- Duplicate: 0 (aynı proje birden fazla atanmamalı)

YENİ ÖZELLİKLER:
- Gap-free scheduling garantisi
- Duplicate otomatik temizleme
- Coverage otomatik tamamlama
- Late slot otomatik düzeltme
- Load balance otomatik dengeleme
"""
from typing import List, Dict, Any, Tuple, Set, Callable
from collections import defaultdict, Counter
import json
import os
import csv
import statistics
from datetime import datetime

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None


def detect_duplicates(assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_project = defaultdict(list)
    for a in assignments:
        pid = a.get("project_id")
        if pid is None:
            continue
        by_project[pid].append(a)

    duplicates = []
    for pid, items in by_project.items():
        if len(items) > 1:
            duplicates.append({"project_id": pid, "count": len(items),
                               "occurrences": [{"classroom_id": it.get("classroom_id"), "timeslot_id": it.get("timeslot_id")} for it in items]})

    return {"duplicates": duplicates, "summary": {"total_duplicates": sum(max(0, d["count"] - 1) for d in duplicates),
                                                    "duplicated_projects": len(duplicates)}}


def detect_coverage(assignments: List[Dict[str, Any]], expected_project_ids: List[Any]) -> Dict[str, Any]:
    scheduled = {a.get("project_id") for a in assignments if a.get("project_id") is not None}
    expected = set(expected_project_ids)
    missing = list(expected - scheduled)
    extra = list(scheduled - expected)
    return {"expected_count": len(expected), "scheduled_count": len(scheduled), "missing": missing, "extra": extra}


def detect_gaps(assignments: List[Dict[str, Any]], timeslots: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Build timeslot index
    id_to_idx = {}
    for idx, ts in enumerate(timeslots):
        tid = ts.get("id")
        id_to_idx[tid] = idx

    classrooms = defaultdict(list)
    for a in assignments:
        cid = a.get("classroom_id")
        tid = a.get("timeslot_id")
        if cid is None or tid not in id_to_idx:
            continue
        classrooms[cid].append(id_to_idx[tid])

    details = []
    total_gaps = 0
    for cid, idxs in classrooms.items():
        idxs = sorted(set(idxs))
        for prev, curr in zip(idxs, idxs[1:]):
            if curr - prev > 1:
                missing = list(range(prev + 1, curr))
                total_gaps += len(missing)
                details.append({"classroom_id": cid, "gap_between": [prev, curr], "missing_indices": missing})

    return {"total_gaps": total_gaps, "details": details}


def detect_late_slots(assignments: List[Dict[str, Any]], timeslots: List[Dict[str, Any]], late_pred) -> List[Dict[str, Any]]:
    late = []
    id_to_ts = {ts.get("id"): ts for ts in timeslots}
    for a in assignments:
        ts = id_to_ts.get(a.get("timeslot_id"))
        if ts and late_pred(ts):
            late.append({"project_id": a.get("project_id"), "classroom_id": a.get("classroom_id"), "timeslot_id": a.get("timeslot_id")})
    return late


def detect_role_violations(assignments: List[Dict[str, Any]], people_types: Dict[Any, str]) -> Dict[str, Any]:
    """Rol kısıtlarını kontrol et (sorumlu/jüri kuralları)"""
    violations = []

    for a in assignments:
        project_id = a.get("project_id")
        roles = a.get("roles", [])
        instructors = a.get("instructors", [])

        # Rol bilgilerini topla
        responsibles = [r for r in roles if str(r.get("role", "")).upper() in ("SORUMLU", "RESPONSIBLE")]
        juries = [r for r in roles if str(r.get("role", "")).upper() in ("JURI", "JURY")]

        # Aynı kişi hem sorumlu hem jüri olamaz
        resp_ids = {r.get("person_id") for r in responsibles}
        jury_ids = {r.get("person_id") for r in juries}

        same_person_both_roles = resp_ids & jury_ids
        if same_person_both_roles:
            violations.append({
                "project_id": project_id,
                "type": "same_person_both_roles",
                "person_ids": list(same_person_both_roles),
                "message": f"Proje {project_id}: Aynı kişi hem sorumlu hem jüri olamaz"
            })

        # Proje türüne göre gerekli rol sayısı kontrolü
        project_type = str(a.get("project_type") or a.get("type") or "").lower()

        if project_type == "bitirme":
            if len(responsibles) != 1:
                violations.append({
                    "project_id": project_id,
                    "type": "bitirme_responsible_count",
                    "expected": 1,
                    "actual": len(responsibles),
                    "message": f"Bitirme projesi {project_id}: 1 sorumlu olmalı, {len(responsibles)} var"
                })
            if len(juries) < 1:
                violations.append({
                    "project_id": project_id,
                    "type": "bitirme_jury_count",
                    "expected": "1+",
                    "actual": len(juries),
                    "message": f"Bitirme projesi {project_id}: En az 1 jüri olmalı, {len(juries)} var"
                })
        elif project_type == "ara":
            if len(responsibles) != 1:
                violations.append({
                    "project_id": project_id,
                    "type": "ara_responsible_count",
                    "expected": 1,
                    "actual": len(responsibles),
                    "message": f"Ara projesi {project_id}: 1 sorumlu olmalı, {len(responsibles)} var"
                })
            if len(juries) != 0:
                violations.append({
                    "project_id": project_id,
                    "type": "ara_jury_count",
                    "expected": 0,
                    "actual": len(juries),
                    "message": f"Ara projesi {project_id}: Jüri olmamalı, {len(juries)} var"
                })

    return {
        "total_violations": len(violations),
        "violations": violations,
        "summary": {
            "same_person_both_roles": len([v for v in violations if v["type"] == "same_person_both_roles"]),
            "bitirme_responsible_issues": len([v for v in violations if v["type"] == "bitirme_responsible_count"]),
            "bitirme_jury_issues": len([v for v in violations if v["type"] == "bitirme_jury_count"]),
            "ara_responsible_issues": len([v for v in violations if v["type"] == "ara_responsible_count"]),
            "ara_jury_issues": len([v for v in violations if v["type"] == "ara_jury_count"])
        }
    }


def detect_load_balance_violations(assignments: List[Dict[str, Any]], instructors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Öğretim üyeleri yük dağılımını kontrol et (±1 tolerans)"""
    instructor_loads = Counter()

    for a in assignments:
        for instructor_id in a.get("instructors", []):
            instructor_loads[instructor_id] += 1

    if not instructor_loads:
        return {"total_instructors": len(instructors), "assigned_instructors": 0, "unassigned_instructors": len(instructors)}

    loads = list(instructor_loads.values())
    mean_load = statistics.mean(loads)
    std_load = statistics.stdev(loads) if len(loads) > 1 else 0

    # ±1 tolerans kontrolü
    violations = []
    for instructor_id, load in instructor_loads.items():
        deviation = abs(load - mean_load)
        if deviation > 1.0:
            violations.append({
                "instructor_id": instructor_id,
                "load": load,
                "expected_range": [max(0, int(mean_load - 1)), int(mean_load + 1)],
                "deviation": deviation
            })

    # Görev almayan öğretim üyeleri
    assigned_instructor_ids = set(instructor_loads.keys())
    all_instructor_ids = {inst.get("id") for inst in instructors if inst.get("id") is not None}
    unassigned = list(all_instructor_ids - assigned_instructor_ids)

    return {
        "total_instructors": len(instructors),
        "assigned_instructors": len(assigned_instructor_ids),
        "unassigned_instructors": len(unassigned),
        "unassigned_list": unassigned,
        "load_distribution": dict(instructor_loads),
        "mean_load": mean_load,
        "std_load": std_load,
        "balance_violations": violations,
        "max_deviation": max((abs(load - mean_load) for load in loads), default=0),
        "is_balanced": max((abs(load - mean_load) for load in loads), default=0) <= 1.0
    }


def detect_classroom_switches(assignments: List[Dict[str, Any]], instructors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Öğretim üyelerinin sınıf değiştirme sayısını hesapla"""
    instructor_classrooms = defaultdict(set)

    for a in assignments:
        instructor_ids = a.get("instructors", [])
        classroom_id = a.get("classroom_id")

        for instructor_id in instructor_ids:
            if instructor_id and classroom_id:
                instructor_classrooms[instructor_id].add(classroom_id)

    switches = {}
    total_switches = 0

    for instructor_id, classrooms in instructor_classrooms.items():
        switch_count = len(classrooms) - 1  # Her değişim için 1 ekleme
        switches[instructor_id] = {
            "classroom_count": len(classrooms),
            "switches": switch_count,
            "classrooms": list(classrooms)
        }
        total_switches += switch_count

    return {
        "per_instructor": switches,
        "total_switches": total_switches,
        "average_switches": total_switches / len(switches) if switches else 0,
        "max_switches": max((info["switches"] for info in switches.values()), default=0)
    }


def detect_session_count(assignments: List[Dict[str, Any]], timeslots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Oturum sayısını hesapla (kullanılan timeslot sayısı)"""
    used_timeslots = set()

    for a in assignments:
        timeslot_id = a.get("timeslot_id")
        if timeslot_id:
            used_timeslots.add(timeslot_id)

    total_slots = len(timeslots)
    used_slots = len(used_timeslots)

    return {
        "total_available_slots": total_slots,
        "used_slots": used_slots,
        "unused_slots": total_slots - used_slots,
        "utilization_rate": used_slots / total_slots if total_slots > 0 else 0,
        "used_timeslot_ids": sorted(list(used_timeslots))
    }


def repair_duplicates(assignments: List[Dict[str, Any]], slot_rewards_map: Dict[str, float], timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmamalı!
    
    Her algoritma kendi duplicate repair metodunu implement etmeli.
    Bu ortak repair fonksiyonu algoritmaları aynılaştırıyor.
    
    Returns:
        Değiştirilmemiş assignments (sadece uyarı verir)
    """
    print("⚠️  UYARI: repair_duplicates() fonksiyonu DEPRECATED!")
    print("⚠️  Her algoritma kendi duplicate repair metodunu kullanmalı!")
    return assignments


def repair_gaps(assignments: List[Dict[str, Any]], timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmamalı!
    
    Her algoritma kendi gap repair metodunu implement etmeli.
    Bu ortak repair fonksiyonu algoritmaları aynılaştırıyor.
    
    Returns:
        Değiştirilmemiş assignments (sadece uyarı verir)
    """
    print("⚠️  UYARI: repair_gaps() fonksiyonu DEPRECATED!")
    print("⚠️  Her algoritma kendi gap repair metodunu kullanmalı!")
    return assignments


def repair_load_balance(assignments: List[Dict[str, Any]], instructors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmamalı!
    
    Her algoritma kendi load balance repair metodunu implement etmeli.
    Bu ortak repair fonksiyonu algoritmaları aynılaştırıyor.
    
    Returns:
        Değiştirilmemiş assignments (sadece uyarı verir)
    """
    print("⚠️  UYARI: repair_load_balance() fonksiyonu DEPRECATED!")
    print("⚠️  Her algoritma kendi load balance repair metodunu kullanmalı!")
    return assignments


def emergency_assign_missing(assignments: List[Dict[str, Any]], projects: List[Dict[str, Any]],
                             instructors: List[Dict[str, Any]], classrooms: List[Dict[str, Any]],
                             timeslots: List[Dict[str, Any]], late_pred) -> List[Dict[str, Any]]:
    """
    Try to assign missing projects into free slots respecting late_pred (avoid late slots).
    This is a best-effort emergency assign that picks the first feasible slot and simple instructor selection.
    """
    assigned_pids = {a.get("project_id") for a in assignments if a.get("project_id") is not None}
    missing = [p for p in projects if p.get("id") not in assigned_pids]

    # Build occupied slots
    occupied = {(a.get("classroom_id"), a.get("timeslot_id")) for a in assignments}

    # Build instructor timeslot usage
    instr_busy = defaultdict(set)
    for a in assignments:
        ts = a.get("timeslot_id")
        for ins in a.get("instructors", []):
            instr_busy[ins].add(ts)

    id_to_instr = {ins.get("id"): ins for ins in instructors}

    for proj in missing:
        placed = False
        for ts in timeslots:
            if late_pred(ts):
                continue
            for cls in classrooms:
                key = (cls.get("id"), ts.get("id"))
                if key in occupied:
                    continue
                # Revised role selection
                resp = proj.get("responsible_id")
                ins_list: List[int] = []
                # responsible must be present and first
                if resp and ts.get("id") not in instr_busy.get(resp, set()):
                    ins_list.append(resp)
                # project type handling
                ptype = proj.get("type")
                if ptype == "bitirme":
                    # need at least one jury (not same as responsible)
                    # prefer instructors, then assistants
                    # filter available and not-responsible
                    faculty = [i for i in instructors if i.get("type") == "instructor"]
                    assistants = [i for i in instructors if i.get("type") == "assistant"]
                    candidates = faculty + assistants
                    for ins in candidates:
                        iid = ins.get("id")
                        if not iid or iid == resp:
                            continue
                        if ts.get("id") in instr_busy.get(iid, set()):
                            continue
                        ins_list.append(iid)
                        break
                else:
                    # ara: only responsible
                    pass

                # minimal check: bitirme needs responsible+jury; ara needs responsible
                if ((ptype == "bitirme" and len(ins_list) >= 2) or
                        (ptype == "ara" and len(ins_list) >= 1)):
                    assignment = {
                        "project_id": proj.get("id"),
                        "classroom_id": cls.get("id"),
                        "timeslot_id": ts.get("id"),
                        "instructors": ins_list
                    }
                    assignments.append(assignment)
                    occupied.add(key)
                    for iid in ins_list:
                        instr_busy[iid].add(ts.get("id"))
                    placed = True
                    break
            if placed:
                break

    return assignments


def repair_solution(assignments: List[Dict[str, Any]],
                   projects: List[Dict[str, Any]],
                   instructors: List[Dict[str, Any]],
                   classrooms: List[Dict[str, Any]],
                   timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmamalı!
    
    Her algoritma kendi repair metodunu implement etmeli.
    Bu ortak repair fonksiyonu algoritmaları aynılaştırıyor.
    
    Bunun yerine her algoritmanın kendi repair_solution() metodunu kullanın.
    
    Returns:
        Değiştirilmemiş assignments (sadece uyarı verir)
    """
    print("⚠️  UYARI: repair_solution() fonksiyonu DEPRECATED!")
    print("⚠️  Her algoritma kendi repair metodunu kullanmalı!")
    print("⚠️  Bu ortak repair algoritmaları aynılaştırıyor!")
    
    # Sadece uyarı ver, repair yapma
    return assignments


def remove_duplicates_from_solution(assignments: List[Dict[str, Any]], projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """DEPRECATED: Bu fonksiyon artık kullanılmamalı! Her algoritma kendi duplicate repair metodunu kullanmalı."""
    print("⚠️  UYARI: remove_duplicates_from_solution() DEPRECATED!")
    return assignments


def ensure_role_constraints(assignments: List[Dict[str, Any]],
                          projects: List[Dict[str, Any]],
                          instructors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmamalı!
    
    Her algoritma kendi role constraint repair metodunu implement etmeli.
    Bu ortak repair fonksiyonu algoritmaları aynılaştırıyor.
    
    Returns:
        Değiştirilmemiş assignments (sadece uyarı verir)
    """
    print("⚠️  UYARI: ensure_role_constraints() fonksiyonu DEPRECATED!")
    print("⚠️  Her algoritma kendi role constraint repair metodunu kullanmalı!")
    return assignments


def remove_late_slots_from_solution(assignments: List[Dict[str, Any]], timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """16:30+ slotları kaldır"""
    def is_late_slot(ts_id: str) -> bool:
        ts = next((t for t in timeslots if t.get("id") == ts_id), None)
        if not ts:
            return False

        start_time = str(ts.get("start_time", "09:00"))
        try:
            hour = int(start_time.split(":")[0])
            minute = int(start_time.split(":")[1]) if len(start_time.split(":")) > 1 else 0
            return hour > 16 or (hour == 16 and minute >= 30)
        except:
            return False

    return [a for a in assignments if not is_late_slot(a.get("timeslot_id", ""))]


def balance_instructor_load(assignments: List[Dict[str, Any]],
                          instructors: List[Dict[str, Any]],
                          projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmamalı!
    
    Her algoritma kendi load balance repair metodunu implement etmeli.
    Bu ortak repair fonksiyonu algoritmaları aynılaştırıyor.
    
    Returns:
        Değiştirilmemiş assignments (sadece uyarı verir)
    """
    print("⚠️  UYARI: balance_instructor_load() fonksiyonu DEPRECATED!")
    print("⚠️  Her algoritma kendi load balance repair metodunu kullanmalı!")
    return assignments


def repair_gaps_in_solution(assignments: List[Dict[str, Any]],
                           instructors: List[Dict[str, Any]],
                           classrooms: List[Dict[str, Any]],
                           timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmamalı!
    
    Her algoritma kendi gap repair metodunu implement etmeli.
    Bu ortak repair fonksiyonu algoritmaları aynılaştırıyor.
    
    Returns:
        Değiştirilmemiş assignments (sadece uyarı verir)
    """
    print("⚠️  UYARI: repair_gaps_in_solution() DEPRECATED!")
    print("⚠️  Her algoritma kendi gap repair metodunu kullanmalı!")
    return assignments


def _create_gap_free_blocks_for_instructor(assignments: List[Dict[str, Any]],
                                         classrooms: List[Dict[str, Any]],
                                         timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tek bir instructor için gap-free bloklar oluşturur.
    """
    if not assignments:
        return []

    # Zaman dilimlerini sırala
    timeslot_order = {ts.get("id"): i for i, ts in enumerate(timeslots)}

    # Atamaları zaman sırasına göre grupla
    assignment_blocks = []
    current_block = [assignments[0]]

    for i in range(1, len(assignments)):
        current_ts_idx = timeslot_order.get(assignments[i-1].get("timeslot_id"), 999)
        next_ts_idx = timeslot_order.get(assignments[i].get("timeslot_id"), 999)

        # Eğer ardışık zaman dilimleriyse aynı bloğa ekle
        if next_ts_idx == current_ts_idx + 1:
            current_block.append(assignments[i])
        else:
            # Yeni blok başlat
            if len(current_block) > 1:  # Sadece çoklu atamalı blokları işle
                assignment_blocks.append(current_block)
            current_block = [assignments[i]]

    # Son bloğu ekle
    if len(current_block) > 1:
        assignment_blocks.append(current_block)

    # Blokları yeniden oluştur (gap-free garanti)
    gap_free_assignments = []
    for block in assignment_blocks:
        # Blok içindeki tüm zaman dilimlerini ardışık hale getir
        first_assignment = block[0]
        last_assignment = block[-1]

        # Tüm zaman dilimlerini ara ve doldur
        first_ts_idx = timeslot_order.get(first_assignment.get("timeslot_id"), 0)
        last_ts_idx = timeslot_order.get(last_assignment.get("timeslot_id"), 0)

        all_instructors = set()
        for assignment in block:
            all_instructors.update(assignment.get("instructors", []))

        # Tüm zaman dilimleri için aynı sınıfta ve aynı instructor'larda atama oluştur
        classroom_id = first_assignment.get("classroom_id")
        project_id = first_assignment.get("project_id")  # İlk projeyi kullan

        for ts_idx in range(first_ts_idx, last_ts_idx + 1):
            if ts_idx < len(timeslots):
                timeslot = timeslots[ts_idx]
                gap_free_assignments.append({
                    "project_id": project_id,
                    "classroom_id": classroom_id,
                    "timeslot_id": timeslot.get("id"),
                    "instructors": list(all_instructors)
                })

    return gap_free_assignments


def write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_slot_rewards_map_from_algorithm(algo) -> Dict[str, float]:
    try:
        if hasattr(algo, '_get_slot_rewards_map'):
            return algo._get_slot_rewards_map()
    except Exception:
        pass
    # default
    return {
        "09:00-09:30": 1000,
        "09:30-10:00": 950,
        "10:00-10:30": 900,
        "10:30-11:00": 850,
        "11:00-11:30": 800,
        "11:30-12:00": 750,
        "13:00-13:30": 700,
        "13:30-14:00": 650,
        "14:00-14:30": 600,
        "14:30-15:00": 550,
        "15:00-15:30": 500,
        "15:30-16:00": 450,
        "16:00-16:30": 400,
        "16:30-17:00": -9999,
        "17:00-17:30": -9999,
        "17:30-18:00": -9999,
    }


def export_schedule_to_excel(assignments: List[Dict[str, Any]], projects: List[Dict[str, Any]],
                             instructors: List[Dict[str, Any]], classrooms: List[Dict[str, Any]],
                             timeslots: List[Dict[str, Any]], out_path: str) -> str:
    """
    Export schedule to Excel (or CSV fallback). Returns path written.
    """
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

    pid_to_proj = {p.get("id"): p for p in projects}
    iid_to_instr = {i.get("id"): i for i in instructors}
    cid_to_class = {c.get("id"): c for c in classrooms}
    tid_to_ts = {t.get("id"): t for t in timeslots}

    headers = ["project_id", "project_title", "project_type", "classroom_id", "classroom_name",
               "timeslot_id", "timeslot_range", "start_time", "instructors_ids", "instructors_names"]

    rows = []
    for a in assignments:
        pid = a.get("project_id")
        proj = pid_to_proj.get(pid, {})
        cid = a.get("classroom_id")
        cls = cid_to_class.get(cid, {})
        tid = a.get("timeslot_id")
        ts = tid_to_ts.get(tid, {})
        instr_ids = a.get("instructors", []) or []
        instr_names = [iid_to_instr.get(i, {}).get("name") or str(i) for i in instr_ids]

        rows.append([
            pid,
            proj.get("title") or proj.get("name") or "",
            proj.get("type") or "",
            cid,
            cls.get("name") or "",
            tid,
            ts.get("time_range") or ts.get("start_time") or "",
            ts.get("start_time") or "",
            ";".join(str(x) for x in instr_ids),
            ";".join(instr_names)
        ])

    # Try Excel
    if Workbook is not None and out_path.lower().endswith('.xlsx'):
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append(r)
        wb.save(out_path)
        return out_path

    # Fallback to CSV
    csv_path = out_path if out_path.lower().endswith('.csv') else out_path.rsplit('.', 1)[0] + '.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)

    return csv_path


def validate_solution(assignments: List[Dict[str, Any]], projects: List[Dict[str, Any]],
                     instructors: List[Dict[str, Any]], classrooms: List[Dict[str, Any]],
                     timeslots: List[Dict[str, Any]], late_pred: Callable = None) -> Dict[str, Any]:
    """
    Kapsamlı çözüm validasyonu - tüm gereksinimleri kontrol eder

    Returns:
        Tüm validasyon raporlarını içeren sözlük
    """
    if late_pred is None:
        late_pred = lambda ts: _is_late_slot(ts)

    # Veri hazırlığı
    expected_project_ids = [p.get("id") for p in projects if p.get("id") is not None]
    people_types = {person.get("id"): person.get("type") for person in instructors if person.get("id") and person.get("type")}
    slot_rewards_map = build_slot_rewards_map_from_algorithm(None)

    # Tüm kontrolleri çalıştır
    duplicate_report = detect_duplicates(assignments)
    coverage_report = detect_coverage(assignments, expected_project_ids)
    gap_report = detect_gaps(assignments, timeslots)
    late_slots_report = detect_late_slots(assignments, timeslots, late_pred)
    role_violations_report = detect_role_violations(assignments, people_types)
    load_balance_report = detect_load_balance_violations(assignments, instructors)
    classroom_switches_report = detect_classroom_switches(assignments, instructors)
    session_count_report = detect_session_count(assignments, timeslots)

    # Özet istatistikler
    ara_projects = sum(1 for p in projects if str(p.get("type", "")).lower() == "ara")
    bitirme_projects = sum(1 for p in projects if str(p.get("type", "")).lower() == "bitirme")

    summary = {
        "total_projects": len(expected_project_ids),
        "scheduled_projects": coverage_report["scheduled_count"],
        "ara_projects": ara_projects,
        "bitirme_projects": bitirme_projects,
        "total_duplicates": duplicate_report["summary"]["total_duplicates"],
        "total_gaps": gap_report["total_gaps"],
        "late_slots_count": len(late_slots_report),
        "role_violations": role_violations_report["total_violations"],
        "unassigned_instructors": load_balance_report["unassigned_instructors"],
        "is_load_balanced": load_balance_report["is_balanced"],
        "total_classroom_switches": classroom_switches_report["total_switches"],
        "session_utilization": session_count_report["utilization_rate"],
        "classroom_count": len(classrooms),
        "instructor_count": len(instructors),
        "timeslot_count": len(timeslots)
    }

    # Kabul kriterleri kontrolü
    acceptance_criteria = {
        "duplicate_ok": duplicate_report["summary"]["total_duplicates"] == 0,
        "coverage_ok": (coverage_report["scheduled_count"] >= 81 and
                       coverage_report["scheduled_count"] == len(expected_project_ids)),
        "gap_ok": gap_report["total_gaps"] == 0,
        "role_ok": role_violations_report["total_violations"] == 0,
        "late_slots_ok": len(late_slots_report) == 0,
        "load_balance_ok": load_balance_report["is_balanced"],
        "unassigned_ok": load_balance_report["unassigned_instructors"] == 0
    }

    overall_accepted = all(acceptance_criteria.values())

    return {
        "summary": summary,
        "acceptance_criteria": acceptance_criteria,
        "overall_accepted": overall_accepted,
        "duplicate_report": duplicate_report,
        "coverage_report": coverage_report,
        "gap_report": gap_report,
        "late_slots_report": late_slots_report,
        "role_violations_report": role_violations_report,
        "load_balance_report": load_balance_report,
        "classroom_switches_report": classroom_switches_report,
        "session_count_report": session_count_report,
        "validation_timestamp": json.dumps({"timestamp": str(datetime.now())}).strip('"')
    }


def _is_late_slot(slot: Dict[str, Any]) -> bool:
    """16:30 sonrası slotları tespit et"""
    if slot is None:
        return False
    if isinstance(slot.get("is_late_slot"), bool):
        return bool(slot.get("is_late_slot"))

    # Zaman parsing
    try:
        label = str(slot.get("label") or slot.get("time_range") or "")
        if any(x in label for x in ["16:30", "17:00", "17:30", "18:00"]):
            return True
        st = str(slot.get("start_time") or "")
        parts = st.split(":")
        h = int(parts[0]) if parts and parts[0].isdigit() else 0
        m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return h > 16 or (h == 16 and m >= 30)
    except Exception:
        return False


def generate_comprehensive_report(validation_result: Dict[str, Any], output_dir: str = "reports") -> Dict[str, str]:
    """
    Kapsamlı raporlama sistemi - tüm gereksinimlere uygun detaylı raporlar üret

    Args:
        validation_result: validate_solution() çıktısı
        output_dir: Raporların kaydedileceği klasör

    Returns:
        Üretilen rapor dosyalarının yolları
    """
    import os
    from datetime import datetime

    # Klasör oluştur
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_files = {}

    # 1. Validator Summary (kabul kriterleri özeti)
    summary_path = os.path.join(output_dir, f"validator_summary_{timestamp}.txt")
    write_validator_summary(summary_path, validation_result)
    report_files["validator_summary"] = summary_path

    # 2. Duplicate Report (ayrıntılı)
    duplicate_path = os.path.join(output_dir, f"duplicate_report_{timestamp}.json")
    write_json(duplicate_path, validation_result.get("duplicate_report", {}))
    report_files["duplicate_report"] = duplicate_path

    # 3. Coverage Report (kapsam detayları)
    coverage_path = os.path.join(output_dir, f"coverage_report_{timestamp}.json")
    write_json(coverage_path, validation_result.get("coverage_report", {}))
    report_files["coverage_report"] = coverage_path

    # 4. Gap Report (boşluk detayları)
    gap_path = os.path.join(output_dir, f"gap_report_{timestamp}.json")
    write_json(gap_path, validation_result.get("gap_report", {}))
    report_files["gap_report"] = gap_path

    # 5. Late Slots Report (cezalı slot kullanımı)
    late_slots_path = os.path.join(output_dir, f"late_slots_report_{timestamp}.json")
    write_json(late_slots_path, validation_result.get("late_slots_report", []))
    report_files["late_slots_report"] = late_slots_path

    # 6. Load Balance Report (yük dağılımı)
    load_balance_path = os.path.join(output_dir, f"load_balance_report_{timestamp}.json")
    write_json(load_balance_path, validation_result.get("load_balance_report", {}))
    report_files["load_balance_report"] = load_balance_path

    # 7. Role Violations Report (rol ihlalleri)
    role_violations_path = os.path.join(output_dir, f"role_violations_report_{timestamp}.json")
    write_json(role_violations_path, validation_result.get("role_violations_report", {}))
    report_files["role_violations_report"] = role_violations_path

    # 8. Classroom Switches Report (sınıf geçişleri)
    classroom_switches_path = os.path.join(output_dir, f"classroom_switches_report_{timestamp}.json")
    write_json(classroom_switches_path, validation_result.get("classroom_switches_report", {}))
    report_files["classroom_switches_report"] = classroom_switches_path

    # 9. Session Count Report (oturum sayısı)
    session_count_path = os.path.join(output_dir, f"session_count_report_{timestamp}.json")
    write_json(session_count_path, validation_result.get("session_count_report", {}))
    report_files["session_count_report"] = session_count_path

    # 10. Comprehensive Summary (tüm kriterler bir arada)
    comprehensive_path = os.path.join(output_dir, f"comprehensive_report_{timestamp}.txt")
    write_comprehensive_summary(comprehensive_path, validation_result)
    report_files["comprehensive_summary"] = comprehensive_path

    # 11. Acceptance Criteria Check (kabul kriterleri kontrolü)
    acceptance_path = os.path.join(output_dir, f"acceptance_criteria_{timestamp}.txt")
    write_acceptance_criteria(acceptance_path, validation_result)
    report_files["acceptance_criteria"] = acceptance_path

    print(f"REPORT: Kapsamlı raporlama tamamlandı! {len(report_files)} rapor üretildi:")
    for report_type, file_path in report_files.items():
        print(f"   • {report_type}: {file_path}")

    return report_files


def write_comprehensive_summary(file_path: str, validation_result: Dict[str, Any]) -> None:
    """Kapsamlı özet raporu yaz"""
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("SEARCH: KAPSAMLI OPTİMİZASYON PLANNER RAPORU\n")
        f.write("=" * 50 + "\n\n")

        summary = validation_result.get("summary", {})
        acceptance = validation_result.get("acceptance_criteria", {})

        f.write("STATS: ÖZET İSTATİSTİKLER:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Toplam Proje: {summary.get('total_projects', 0)}\n")
        f.write(f"Planlanan Proje: {summary.get('scheduled_projects', 0)}\n")
        f.write(f"Ara Proje: {summary.get('ara_projects', 0)}\n")
        f.write(f"Bitirme Proje: {summary.get('bitirme_projects', 0)}\n")
        f.write(f"Duplicate Sayısı: {summary.get('total_duplicates', 0)}\n")
        f.write(f"Gap Sayısı: {summary.get('total_gaps', 0)}\n")
        f.write(f"Cezalı Slot Sayısı: {summary.get('late_slots_count', 0)}\n")
        f.write(f"Atanmamış Öğretim Üyesi: {summary.get('unassigned_instructors', 0)}\n")
        f.write(f"Yük Dengeli: {summary.get('is_load_balanced', False)}\n")
        f.write(f"Toplam Sınıf Geçişi: {summary.get('total_classroom_switches', 0)}\n")
        f.write(f"Oturum Kullanım Oranı: {summary.get('session_utilization', 0):.2f}\n")
        f.write(f"Sınıf Sayısı: {summary.get('classroom_count', 0)}\n")
        f.write(f"Öğretim Üyesi Sayısı: {summary.get('instructor_count', 0)}\n")
        f.write(f"Timeslot Sayısı: {summary.get('timeslot_count', 0)}\n\n")

        f.write("SUCCESS: KABUL KRİTERLERİ KONTROLÜ:\n")
        f.write("-" * 35 + "\n")
        f.write(f"Duplicate OK: {'SUCCESS' if acceptance.get('duplicate_ok', False) else 'ERROR'}\n")
        f.write(f"Coverage OK: {'SUCCESS' if acceptance.get('coverage_ok', False) else 'ERROR'}\n")
        f.write(f"Gap OK: {'SUCCESS' if acceptance.get('gap_ok', False) else 'ERROR'}\n")
        f.write(f"Role OK: {'SUCCESS' if acceptance.get('role_ok', False) else 'ERROR'}\n")
        f.write(f"Late Slots OK: {'SUCCESS' if acceptance.get('late_slots_ok', False) else 'ERROR'}\n")
        f.write(f"Load Balance OK: {'SUCCESS' if acceptance.get('load_balance_ok', False) else 'ERROR'}\n")
        f.write(f"Unassigned OK: {'SUCCESS' if acceptance.get('unassigned_ok', False) else 'ERROR'}\n\n")

        overall_accepted = validation_result.get("overall_accepted", False)
        f.write(f"TARGET: GENEL SONUÇ: {'SUCCESS KABUL EDİLDİ' if overall_accepted else 'ERROR REDDEDİLDİ'}\n\n")

        # Detaylı analiz
        if not overall_accepted:
            f.write("BUILD: İYİLEŞTİRME ÖNERİLERİ:\n")
            f.write("-" * 30 + "\n")

            if not acceptance.get('duplicate_ok', False):
                f.write("• Duplicate projeler var - onarım gerekli\n")
            if not acceptance.get('coverage_ok', False):
                f.write("• Kapsam %100 değil - eksik projeler var\n")
            if not acceptance.get('gap_ok', False):
                f.write("• Gap'ler var - slot boşlukları onarılmalı\n")
            if not acceptance.get('role_ok', False):
                f.write("• Rol ihlalleri var - kurallara uyumsuzluk\n")
            if not acceptance.get('late_slots_ok', False):
                f.write("• Cezalı slot kullanımı var - 16:30 sonrası kullanılmamalı\n")
            if not acceptance.get('load_balance_ok', False):
                f.write("• Yük dengesiz - ±1 tolerans aşılmış\n")
            if not acceptance.get('unassigned_ok', False):
                f.write("• Atanmamış öğretim üyeleri var - tüm üyeler görev almalı\n")


def write_acceptance_criteria(file_path: str, validation_result: Dict[str, Any]) -> None:
    """Kabul kriterleri detay raporu"""
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("TARGET: KABUL KRİTERLERİ DETAY RAPORU\n")
        f.write("=" * 40 + "\n\n")

        acceptance = validation_result.get("acceptance_criteria", {})
        summary = validation_result.get("summary", {})

        criteria_details = [
            ("Duplicate Sayısı = 0", acceptance.get('duplicate_ok', False), summary.get('total_duplicates', 0)),
            ("Coverage = %100 (81 proje)", acceptance.get('coverage_ok', False), f"{summary.get('scheduled_projects', 0)}/{summary.get('total_projects', 0)}"),
            ("Gap Sayısı = 0", acceptance.get('gap_ok', False), summary.get('total_gaps', 0)),
            ("Rol Kurallarına Uyum", acceptance.get('role_ok', False), f"{summary.get('role_violations', 0)} ihlal"),
            ("Cezalı Slot Kullanımı = 0", acceptance.get('late_slots_ok', False), f"{summary.get('late_slots_count', 0)} slot"),
            ("Yük Dengesi (±1 tolerans)", acceptance.get('load_balance_ok', False), "Dengeli" if summary.get('is_load_balanced', False) else "Dengesiz"),
            ("Tüm Öğretim Üyeleri Görevli", acceptance.get('unassigned_ok', False), f"{summary.get('unassigned_instructors', 0)} atanmamış")
        ]

        for criterion, status, value in criteria_details:
            status_icon = "SUCCESS" if status else "ERROR"
            f.write(f"{status_icon} {criterion}: {value}\n")

        f.write(f"\nTARGET: GENEL DEĞERLENDİRME: {'SUCCESS TÜM KRİTERLER SAĞLANDI' if validation_result.get('overall_accepted', False) else 'ERROR KRİTERLER EKSİK'}\n")


def generate_reports(assignments: List[Dict[str, Any]],
                    projects: List[Dict[str, Any]],
                    instructors: List[Dict[str, Any]],
                    classrooms: List[Dict[str, Any]],
                    timeslots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tüm raporları oluşturur ve dict olarak döner.

    Returns:
        Tüm raporları içeren dict
    """
    reports = {}

    # Duplicate raporu
    reports["duplicate_report"] = detect_duplicates(assignments)

    # Coverage raporu
    expected_ids = [p.get("id") for p in projects if p.get("id")]
    reports["coverage_report"] = detect_coverage(assignments, expected_ids)

    # Gap raporu
    reports["gap_report"] = detect_gaps(assignments, timeslots)

    # Late slots raporu
    def is_late_slot(ts: Dict[str, Any]) -> bool:
        start_time = str(ts.get("start_time", "09:00"))
        try:
            hour = int(start_time.split(":")[0])
            minute = int(start_time.split(":")[1]) if len(start_time.split(":")) > 1 else 0
            return hour > 16 or (hour == 16 and minute >= 30)
        except:
            return False

    reports["late_slots_report"] = detect_late_slots(assignments, timeslots, is_late_slot)

    # Load balance raporu
    reports["load_balance_report"] = detect_load_balance_violations(assignments, instructors)

    # Acceptance criteria kontrolü
    validation_result = validate_solution(assignments, projects, instructors, classrooms, timeslots)
    reports["validation_result"] = validation_result

    return reports


def write_validator_summary(path: str, reports: Dict[str, Any]) -> None:
    """Write a compact validator_summary.txt describing acceptance criteria results."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    lines = []
    dup = reports.get('duplicate_report', {})
    cov = reports.get('coverage_report', {})
    gap = reports.get('gap_report', {})
    late = reports.get('late_slots_report', [])
    lb = reports.get('load_balance_report', {})

    lines.append(f"Duplicate_total: {dup.get('summary', {}).get('total_duplicates', 0)}")
    lines.append(f"Coverage_expected: {cov.get('expected_count', 0)}")
    lines.append(f"Coverage_scheduled: {cov.get('scheduled_count', 0)}")
    lines.append(f"Coverage_missing_count: {len(cov.get('missing', []))}")
    lines.append(f"Gap_total_slots: {gap.get('total_gaps', 0)}")
    lines.append(f"Late_slots_count: {len(late)}")
    # load balance summary
    per_instr = lb.get('per_instructor', {})
    if isinstance(per_instr, dict):
        loads = list(per_instr.values())
        if loads:
            lines.append(f"Load_min: {min(loads)}")
            lines.append(f"Load_max: {max(loads)}")
            avg = sum(loads)/len(loads)
            lines.append(f"Load_avg: {avg:.2f}")
    # details
    lines.append('')
    lines.append('Missing_projects:')
    for m in cov.get('missing', []):
        lines.append(str(m))

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))



