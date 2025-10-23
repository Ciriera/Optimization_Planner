"""
Performance metrics computation for planner outputs (algorithm-agnostic).

Conforms to the spec:
- Inputs: plan dict with classes, slots, assignments, people, expected_projects
- Outputs: normalized 0-100 metrics and weighted total, with counts and violations

This module is read-only and does not mutate plans or algorithms; it's used for evaluation only.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import math
import json
import os


DEFAULT_WEIGHTS = {
    "CoverageScore": 0.25,      # Kapsam (81 proje tam)
    "DuplicateScore": 0.20,     # Duplicate olmamalı (0)
    "GapScore": 0.15,          # Gap olmamalı (0)
    "LateSlotScore": 0.15,     # Cezalı slot kullanımı minimum
    "RoleComplianceScore": 0.10, # Rol kuralları (sorumlu+jüri)
    "LoadBalanceScore": 0.10,   # Yük dengesi (±1 tolerans)
    "ClassSwitchScore": 0.05,   # Sınıf geçişleri minimum
    "SessionCountScore": 0.00,  # Oturum sayısı (optimize edilecek)
}


@dataclass
class MetricParams:
    duplicate_K: float = 2.0
    gap_G: float = 5.0
    late_linear_L: float = 1.0
    late_fixed_penalty_per_assignment: float = 15.0
    load_std_threshold: float = 0.5  # std at/below threshold -> near 100
    load_std_span: float = 1.5       # std above threshold up to threshold+span -> goes to 0
    class_switch_target: float = 1.0 # desired avg switches per instructor (guidance)
    session_penalty_factor: float = 1.0


def _load_weights_from_config(config_path: Optional[str]) -> Dict[str, float]:
    if not config_path:
        return DEFAULT_WEIGHTS.copy()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        weights = data.get("weights", {})
        merged = DEFAULT_WEIGHTS.copy()
        for k, v in weights.items():
            if k in merged and isinstance(v, (int, float)):
                merged[k] = float(v)
        return merged
    except Exception:
        return DEFAULT_WEIGHTS.copy()


def _index_slots(plan: Dict[str, Any]) -> Tuple[Dict[Any, int], Dict[Any, Dict[str, Any]], List[Any]]:
    slots: List[Dict[str, Any]] = plan.get("slots", []) or []
    # Slots are already in chronological order per spec; build index by their order
    id_to_idx: Dict[Any, int] = {}
    id_to_slot: Dict[Any, Dict[str, Any]] = {}
    ordered_ids: List[Any] = []
    for i, s in enumerate(slots):
        sid = s.get("id", i)
        id_to_idx[sid] = i
        id_to_slot[sid] = s
        ordered_ids.append(sid)
    return id_to_idx, id_to_slot, ordered_ids


def _get_slot_reward(slot: Dict[str, Any]) -> float:
    """Slot ödülünü hesapla - erken saatler yüksek puanlı"""
    if slot is None:
        return 0.0

    # Zaman bilgisini al
    time_range = str(slot.get("time_range") or slot.get("start_time") or "")

    # Erken saatler yüksek ödül
    if "09:00" in time_range:
        return 1000.0
    elif "09:30" in time_range:
        return 950.0
    elif "10:00" in time_range:
        return 900.0
    elif "10:30" in time_range:
        return 850.0
    elif "11:00" in time_range:
        return 800.0
    elif "11:30" in time_range:
        return 750.0
    elif "13:00" in time_range:
        return 700.0
    elif "13:30" in time_range:
        return 650.0
    elif "14:00" in time_range:
        return 600.0
    elif "14:30" in time_range:
        return 550.0
    elif "15:00" in time_range:
        return 500.0
    elif "15:30" in time_range:
        return 450.0
    elif "16:00" in time_range:
        return 400.0
    elif "16:30" in time_range:
        return -9999.0  # Cezalı slot
    elif "17:00" in time_range:
        return -9999.0  # Cezalı slot
    elif "17:30" in time_range:
        return -9999.0  # Cezalı slot
    elif "18:00" in time_range:
        return -9999.0  # Cezalı slot

    # Varsayılan düşük ödül
    return 100.0


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


def _collect_expected_project_ids(plan: Dict[str, Any]) -> List[Any]:
    eps = plan.get("expected_projects", []) or []
    ids = []
    for p in eps:
        pid = p.get("id")
        if pid is not None:
            ids.append(pid)
    return ids


def _collect_expected_project_type_counts(plan: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {"ara": 0, "bitirme": 0}
    for p in plan.get("expected_projects", []) or []:
        t = str(p.get("type") or p.get("project_type") or "").lower()
        if t in counts:
            counts[t] += 1
    return counts


def _collect_people_types(plan: Dict[str, Any]) -> Dict[Any, str]:
    mapping: Dict[Any, str] = {}
    for person in plan.get("people", []) or []:
        pid = person.get("id")
        if pid is not None:
            mapping[pid] = str(person.get("type") or "").lower()
    return mapping


def _role_violations_for_assignment(ass: Dict[str, Any], people_types: Dict[Any, str]) -> int:
    """Rol kısıtlarını kontrol et - güncellenmiş kurallara göre"""
    violations = 0
    project_type = str(ass.get("project_type") or ass.get("type") or "").lower()
    roles = ass.get("roles") or []
    instructors = ass.get("instructors", [])

    # Rol bilgilerini topla
    responsibles = [r for r in roles if str(r.get("role", "")).upper() in ("SORUMLU", "RESPONSIBLE")]
    juries = [r for r in roles if str(r.get("role", "")).upper() in ("JURI", "JURY")]

    # Aynı kişi hem sorumlu hem jüri olamaz
    resp_ids = {r.get("person_id") for r in responsibles}
    jury_ids = {r.get("person_id") for r in juries}
    same_person_both_roles = resp_ids & jury_ids
    if same_person_both_roles:
        violations += 1

    # Proje türüne göre gerekli rol sayısı kontrolü
    if project_type == "bitirme":
        if len(responsibles) != 1:
            violations += 1
        if len(juries) < 1:
            violations += 1
        # Jüri sayısı için ek kontrol - çok fazla olmamalı
        if len(juries) > 3:  # Max 3 jüri
            violations += 1
    elif project_type == "ara":
        if len(responsibles) != 1:
            violations += 1
        if len(juries) != 0:
            violations += 1

    # Instructor sayısı kontrolü (rollerle tutarlı olmalı)
    expected_instructor_count = len(responsibles) + len(juries)
    if len(instructors) != expected_instructor_count:
        violations += 1

    return violations


def _compute_gap_units(assignments: List[Dict[str, Any]], id_to_idx: Dict[Any, int]) -> int:
    if not assignments or not id_to_idx:
        return 0
    # Per-classroom continuity
    by_class: Dict[Any, List[int]] = {}
    for a in assignments:
        cid = a.get("class_id") or a.get("classroom_id")
        sid = a.get("slot_id") or a.get("timeslot_id")
        if cid is None or sid not in id_to_idx:
            continue
        by_class.setdefault(cid, []).append(id_to_idx[sid])
    total = 0
    for cid, idxs in by_class.items():
        s = sorted(set(idxs))
        for prev, curr in zip(s, s[1:]):
            if curr - prev > 1:
                # Öğle arası gap'ını ignore et (timeslot index 6 ve 7 arası)
                # Eğer gap 12:00-13:00 arasındaysa ignore et
                if prev == 6 and curr == 7:  # 12:00-13:00 gap (timeslot index 6->7)
                    continue
                total += (curr - prev - 1)
    return total


def _compute_class_switch_stats(assignments: List[Dict[str, Any]], id_to_idx: Dict[Any, int], people_types: Dict[Any, str]) -> Tuple[int, int]:
    # Returns (total_switches, faculty_count)
    per_instructor = {}
    for a in assignments:
        roles = a.get("roles") or []
        # consider only HOCA in either responsible or jury
        involved = [r.get("person_id") for r in roles if people_types.get(r.get("person_id")) == "hoca"]
        sid = a.get("slot_id") or a.get("timeslot_id")
        cid = a.get("class_id") or a.get("classroom_id")
        for iid in set(involved):
            per_instructor.setdefault(iid, []).append((id_to_idx.get(sid, 10**9), cid))
    total_switches = 0
    for iid, items in per_instructor.items():
        items.sort(key=lambda x: x[0])
        prev_class = None
        for _, cls in items:
            if prev_class is None:
                prev_class = cls
            else:
                if cls != prev_class:
                    total_switches += 1
                prev_class = cls
    return total_switches, len(per_instructor)


def _compute_loads(assignments: List[Dict[str, Any]], people_types: Dict[Any, str]) -> Dict[Any, int]:
    loads: Dict[Any, int] = {}
    for a in assignments:
        roles = a.get("roles") or []
        for r in roles:
            pid = r.get("person_id")
            if people_types.get(pid) != "hoca":
                continue
            loads[pid] = loads.get(pid, 0) + 1
    return loads


def _normalize_0_100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def compute(plan: Dict[str, Any], weights: Optional[Dict[str, float]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compute performance metrics for a single plan.

    Args:
        plan: Dict with keys: classes, slots, assignments, people, expected_projects
        weights: optional per-metric weights; if None, try metrics.config.json then defaults
        params: optional MetricParams overrides as dict

    Returns: Dict with perMetric, totals, counts
    """
    cfg_path = None
    try:
        cfg_path = params.get("config_path") if isinstance(params, dict) else None
    except Exception:
        cfg_path = None
    W = _load_weights_from_config(cfg_path) if weights is None else {**DEFAULT_WEIGHTS, **weights}
    p = MetricParams(**{k: v for k, v in (params or {}).items() if k in MetricParams().__dict__}) if isinstance(params, dict) else MetricParams()

    # Indices and maps
    id_to_idx, id_to_slot, ordered_slot_ids = _index_slots(plan)
    assignments: List[Dict[str, Any]] = plan.get("assignments", []) or []
    people_types = _collect_people_types(plan)
    expected_ids = _collect_expected_project_ids(plan)
    expected_total = len(expected_ids)

    # Coverage
    scheduled_ids = []
    for a in assignments:
        pid = a.get("project_id")
        if pid is not None:
            scheduled_ids.append(pid)
    scheduled_unique = len(set(scheduled_ids))
    missing = [pid for pid in expected_ids if pid not in set(scheduled_ids)]
    coverage_pct = 100.0 * (scheduled_unique / expected_total) if expected_total > 0 else 0.0

    # Type-specific check (optional)
    exp_types = _collect_expected_project_type_counts(plan)
    type_penalty = 0.0
    if exp_types.get("ara", 0) and exp_types.get("bitirme", 0):
        # Estimate scheduled counts by project_type within assignments if present
        sched_ara = sum(1 for a in assignments if str(a.get("project_type") or "").lower() == "ara")
        sched_bit = sum(1 for a in assignments if str(a.get("project_type") or "").lower() == "bitirme")
        type_diff = abs(sched_ara - exp_types.get("ara", 0)) + abs(sched_bit - exp_types.get("bitirme", 0))
        if expected_total > 0:
            type_penalty = min(20.0, 100.0 * type_diff / expected_total)  # cap penalty
    CoverageScore = _normalize_0_100(coverage_pct - type_penalty)

    # Duplicates
    counts_by_project: Dict[Any, int] = {}
    for pid in scheduled_ids:
        counts_by_project[pid] = counts_by_project.get(pid, 0) + 1
    duplicate_extra = sum(max(0, c - 1) for c in counts_by_project.values())
    DuplicateScore = _normalize_0_100(100.0 - min(100.0, 100.0 * (duplicate_extra / max(1, expected_total)) * p.duplicate_K))

    # Gaps (global across classrooms)
    gap_units = _compute_gap_units(assignments, id_to_idx)
    total_slots = len(ordered_slot_ids)
    GapScore = _normalize_0_100(100.0 - min(100.0, 100.0 * (gap_units / max(1, total_slots)) * p.gap_G))

    # Late slots
    late_assignments = 0
    for a in assignments:
        sid = a.get("slot_id") or a.get("timeslot_id")
        slot = id_to_slot.get(sid)
        if _is_late_slot(slot):
            late_assignments += 1
    late_ratio = late_assignments / max(1, len(assignments))
    LateSlotScore = _normalize_0_100(100.0 - min(100.0, 100.0 * late_ratio * p.late_linear_L) - late_assignments * p.late_fixed_penalty_per_assignment)

    # Role compliance
    role_violations = 0
    for a in assignments:
        role_violations += _role_violations_for_assignment(a, people_types)
    RoleComplianceScore = _normalize_0_100(100.0 - role_violations * 5.0)

    # Load balance (faculty HOCA only)
    loads = _compute_loads(assignments, people_types)
    faculty_loads = [v for pid, v in loads.items() if people_types.get(pid) == "hoca"]
    if len(faculty_loads) >= 1:
        mean = sum(faculty_loads) / len(faculty_loads)
        variance = sum((x - mean) ** 2 for x in faculty_loads) / len(faculty_loads)
        std = math.sqrt(variance)
        # Normalize: std <= threshold -> near 100; std >= threshold+span -> 0
        if std <= p.load_std_threshold:
            LoadBalanceScore = 100.0
        else:
            over = min(1.0, (std - p.load_std_threshold) / max(1e-6, p.load_std_span))
            LoadBalanceScore = _normalize_0_100(100.0 * (1.0 - over))
    else:
        LoadBalanceScore = 0.0

    # Class switch (faculty HOCA only)
    total_switches, faculty_count = _compute_class_switch_stats(assignments, id_to_idx, people_types)
    avg_switch = (total_switches / faculty_count) if faculty_count > 0 else 0.0
    # Map to 0-100: zero or <= target -> 100; linear drop afterwards capped at 0
    if avg_switch <= p.class_switch_target:
        ClassSwitchScore = 100.0
    else:
        # Every switch beyond target reduces proportionally (heuristic)
        drop = min(100.0, (avg_switch - p.class_switch_target) * 25.0)
        ClassSwitchScore = _normalize_0_100(100.0 - drop)

    # Session count (optional): unique slot ids used
    used_slots = {a.get("slot_id") or a.get("timeslot_id") for a in assignments if (a.get("slot_id") or a.get("timeslot_id")) in id_to_idx}
    used_sessions = len(used_slots)
    # Heuristic ideal: pack sessions so that used_sessions ~= ceil(total_projects / max_classes)
    classes = plan.get("classes", []) or []
    max_classes = max(1, min(len(classes), 7))
    ideal_sessions = math.ceil(max(1, scheduled_unique) / max_classes)
    extra_sessions = max(0, used_sessions - ideal_sessions)
    SessionCountScore = _normalize_0_100(100.0 - min(100.0, 100.0 * (extra_sessions / max(1, used_sessions)) * p.session_penalty_factor))

    # Weighted total
    perMetric = {
        "CoverageScore": round(CoverageScore, 2),
        "DuplicateScore": round(DuplicateScore, 2),
        "GapScore": round(GapScore, 2),
        "LateSlotScore": round(LateSlotScore, 2),
        "RoleComplianceScore": round(RoleComplianceScore, 2),
        "LoadBalanceScore": round(LoadBalanceScore, 2),
        "ClassSwitchScore": round(ClassSwitchScore, 2),
        "SessionCountScore": round(SessionCountScore, 2),
    }

    total = 0.0
    wsum = 0.0
    for k, v in perMetric.items():
        w = float(W.get(k, 0.0))
        total += v * w
        wsum += w
    WeightedTotalScore = round(total / wsum, 2) if wsum > 0 else 0.0

    counts = {
        "expected_total": expected_total,
        "scheduled_total": scheduled_unique,
        "missing_count": len(missing),
        "duplicate_count": duplicate_extra,
        "gap_units": gap_units,
        "late_assignments": late_assignments,
        "role_violations_count": role_violations,
    }
    violations = {
        "duplicates": duplicate_extra,
        "gaps": gap_units,
        "late_usage": late_assignments,
        "role_violations": role_violations,
    }

    return {
        "perMetric": perMetric,
        "totals": {"WeightedTotalScore": WeightedTotalScore, "violations": violations, "weights": W},
        "counts": counts,
    }


def compute_many(plans_by_algorithm: Dict[str, Dict[str, Any]], weights: Optional[Dict[str, float]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compute metrics for multiple algorithms, returning a comparable table."""
    results: Dict[str, Any] = {"byAlgorithm": {}, "ranking": []}
    for name, plan in plans_by_algorithm.items():
        try:
            results["byAlgorithm"][name] = compute(plan, weights=weights, params=params)
        except Exception:
            results["byAlgorithm"][name] = {"error": True}
    # Build ranking by WeightedTotalScore
    items: List[Tuple[str, float]] = []
    for name, res in results["byAlgorithm"].items():
        try:
            score = float(res.get("totals", {}).get("WeightedTotalScore", 0.0))
        except Exception:
            score = 0.0
        items.append((name, score))
    items.sort(key=lambda x: x[1], reverse=True)
    results["ranking"] = [{"algorithm": n, "score": s} for n, s in items]
    return results


