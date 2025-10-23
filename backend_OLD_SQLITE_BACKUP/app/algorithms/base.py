from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Set
import logging
from collections import defaultdict
from datetime import datetime

class BaseAlgorithm(ABC):
    """Bütün optimizasyon algoritmaları için temel sınıf."""
    
    def __init__(self, projects=None, instructors=None, parameters=None):
        """
        Args:
            projects: Projelerin bilgileri
            instructors: Öğretim elemanlarının bilgileri
            parameters: Algoritma parametreleri
        """
        self.projects = projects or {}
        self.instructors = instructors or {}
        self.parameters = parameters or {}
        self.result = None
        
    @abstractmethod
    def optimize(self) -> Dict[str, Any]:
        """
        Optimizasyon algoritmasını çalıştır.
        
        Returns:
            Dict[str, Any]: Optimizasyon sonuçları
        """
        pass
    
    def validate_parameters(self) -> bool:
        """
        Algoritma parametrelerini doğrula.
        
        Returns:
            bool: Parametreler geçerli mi?
        """
        # Alt sınıflar için varsayılan davranış
        return True
        
    def run(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Algoritmayı verilen parametrelerle çalıştır.
        
        Args:
            params: Özel parametreler
            
        Returns:
            Dict[str, Any]: Algoritma çalışma sonuçları
        """
        if params:
            self.parameters.update(params)
        
        if not self.validate_parameters():
            return {"error": "Invalid parameters", "status": "failed"}
            
        try:
            result = self.optimize()
            try:
                if isinstance(result, dict):
                    duplicate_report: Dict[str, Any] = {
                        "algorithm": self.__class__.__name__,
                        "duplicates": [],
                        "summary": {"total_duplicates": 0, "duplicated_projects": 0},
                    }

                    def _collect_and_report(list_obj: Any, label: str) -> None:
                        if isinstance(list_obj, list) and list_obj:
                            rep = self._detect_duplicates(list_obj)
                            if rep and rep.get("duplicates"):
                                duplicate_report["duplicates"].append({
                                    "list": label,
                                    "items": rep["duplicates"],
                                })
                                duplicate_report["summary"]["total_duplicates"] += rep["summary"]["total_duplicates"]
                                duplicate_report["summary"]["duplicated_projects"] += rep["summary"]["duplicated_projects"]

                    _collect_and_report(result.get("schedule"), "schedule")
                    _collect_and_report(result.get("assignments"), "assignments")
                    _collect_and_report(result.get("solution"), "solution")

                    try:
                        if duplicate_report["summary"]["total_duplicates"] > 0:
                            logging.getLogger(__name__).warning(
                                "Duplicate assignments detected | algo=%s | report=%s",
                                self.__class__.__name__,
                                duplicate_report,
                            )
                        result["duplicate_report"] = duplicate_report
                    except Exception:
                        pass

                    if isinstance(result.get("assignments"), list):
                        result["assignments"] = self._deduplicate_assignments(result.get("assignments"))
                    if isinstance(result.get("schedule"), list):
                        result["schedule"] = self._deduplicate_assignments(result.get("schedule"))
                    if isinstance(result.get("solution"), list):
                        items = result.get("solution")
                        if any(isinstance(it, dict) and ("project_id" in it) for it in items):
                            result["solution"] = self._deduplicate_assignments(items)  # type: ignore
                    self._deduplicate_result_recursively(result)

                    gap_reports: Dict[str, Dict[str, Any]] = {}
                    time_policy_reports: Dict[str, Dict[str, Any]] = {}
                    processed_lists: Dict[int, Dict[str, Any]] = {}
                    for key in ("schedule", "assignments", "solution"):
                        assignments_list = result.get(key)
                        if not self._list_contains_projects(assignments_list):
                            continue

                        before_report = self._detect_classroom_gaps(assignments_list)  # type: ignore[arg-type]

                        list_id = id(assignments_list)
                        if list_id not in processed_lists:
                            if before_report.get("total_gaps", 0) > 0:
                                self._compact_schedule_classrooms(assignments_list)  # type: ignore[arg-type]
                            # Sınıflar arası sıkıştırma
                            self._compact_schedule_globally(assignments_list)  # type: ignore[arg-type]
                            after_report = self._detect_classroom_gaps(assignments_list)  # type: ignore[arg-type]
                            processed_lists[list_id] = after_report
                        else:
                            after_report = processed_lists[list_id]

                        gap_reports[key] = {
                            "before": before_report,
                            "after": after_report,
                        }

                        # Geç saat politikası
                        time_report = self._enforce_time_policy(assignments_list)  # type: ignore[arg-type]
                        time_policy_reports[key] = time_report

                    if gap_reports:
                        result["gap_report"] = gap_reports
                        for key, report in gap_reports.items():
                            if report.get("after", {}).get("total_gaps", 0) > 0:
                                logging.getLogger(__name__).warning(
                                    "Gap-compaction incomplete | algo=%s | list=%s | remaining_gaps=%s",
                                    self.__class__.__name__,
                                    key,
                                    report.get("after", {}).get("details", []),
                                )
                    if time_policy_reports:
                        result["time_policy_report"] = time_policy_reports
            except Exception:
                pass
            self.result = result
            return {"result": result, "status": "completed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
            
    def get_result(self) -> Dict[str, Any]:
        """
        Son algoritma sonucunu döndür.
        
        Returns:
            Dict[str, Any]: Algoritma sonuçları
        """
        return self.result 

    def _format_timeslot_key(self, timeslot: Any) -> str:
        """HH:MM-HH:MM anahtarını üretir (time_range yoksa start/end'den türetir)."""
        if isinstance(timeslot, dict):
            tr = timeslot.get("time_range")
            if tr:
                return str(tr)
            start = str(timeslot.get("start_time", "")).split(".")[0]
            end = str(timeslot.get("end_time", "")).split(".")[0]
        else:
            tr = getattr(timeslot, "time_range", None)
            if tr:
                return str(tr)
            start = str(getattr(timeslot, "start_time", "")).split(".")[0]
            end = str(getattr(timeslot, "end_time", "")).split(".")[0]
        if len(start) == 5:
            start = f"{start}:00"
        if len(end) == 5:
            end = f"{end}:00"
        start_hm = ":".join(start.split(":")[:2])
        end_hm = ":".join(end.split(":")[:2])
        return f"{start_hm}-{end_hm}"

    def _get_slot_rewards_map(self) -> Dict[str, float]:
        """Varsayılan slot ödül/ceza haritası."""
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

    def _score_single_assignment(self, assignment: Dict[str, Any]) -> float:
        """Tek atama için kalite skoru (slot ödül/cezası)."""
        try:
            ts_id = assignment.get("timeslot_id")
            if ts_id is None:
                return 0.0
            rewards = self._get_slot_rewards_map()
            ts = None
            for t in getattr(self, "timeslots", []) or []:
                tid = t.get("id") if isinstance(t, dict) else getattr(t, "id", None)
                if tid == ts_id:
                    ts = t
                    break
            if not ts:
                return 0.0
            key = self._format_timeslot_key(ts).replace(" ", "")
            return float(rewards.get(key, 0.0))
        except Exception:
            return 0.0

    def _deduplicate_assignments(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aynı projeye ait (Proje Adı öncelikli; yoksa project_id) kayıtları tekilleştirir.
        """
        if not assignments:
            return assignments
        best_by_key: Dict[Any, Dict[str, Any]] = {}
        pid_to_name = self._build_project_id_to_name_map()
        for a in assignments:
            key = self._get_assignment_project_key(a, pid_to_name)
            if key is None:
                continue
            score = self._score_single_assignment(a)
            if key not in best_by_key or score > best_by_key[key]["s"]:
                best_by_key[key] = {"a": a, "s": score}
        if best_by_key:
            deduped = [v["a"] for v in best_by_key.values()]
            try:
                deduped.sort(key=lambda x: x.get("project_id"))
            except Exception:
                pass
            return deduped
        return assignments

    def _deduplicate_result_recursively(self, node: Any) -> None:
        """Sonuç yapısında project_id içeren tüm listeleri dedupla (in-place)."""
        try:
            if isinstance(node, dict):
                for k, v in list(node.items()):
                    if isinstance(v, list):
                        has_pid = any(isinstance(it, dict) and ("project_id" in it) for it in v)
                        if has_pid:
                            node[k] = self._deduplicate_assignments(v)  # type: ignore
                        else:
                            for it in v:
                                self._deduplicate_result_recursively(it)
                    elif isinstance(v, dict):
                        self._deduplicate_result_recursively(v)
            elif isinstance(node, list):
                for it in node:
                    self._deduplicate_result_recursively(it)
        except Exception:
            pass

    def _detect_duplicates(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        report: Dict[str, Any] = {"duplicates": [], "summary": {"total_duplicates": 0, "duplicated_projects": 0}}
        if not assignments:
            return report
        from collections import defaultdict
        by_project: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
        for a in assignments:
            if not isinstance(a, dict):
                continue
            key = a.get("project_id", a.get("id"))
            if key is None:
                continue
            by_project[key].append(a)
        for pid, items in by_project.items():
            if len(items) > 1:
                occ = []
                for it in items:
                    occ.append({
                        "classroom_id": it.get("classroom_id"),
                        "timeslot_id": it.get("timeslot_id"),
                    })
                report["duplicates"].append({
                    "project_id": pid,
                    "count": len(items),
                    "occurrences": occ,
                })
        report["summary"]["duplicated_projects"] = len(report["duplicates"])
        report["summary"]["total_duplicates"] = sum(max(0, d["count"] - 1) for d in report["duplicates"]) if report["duplicates"] else 0
        return report

    def _list_contains_projects(self, items: Any) -> bool:
        if not isinstance(items, list):
            return False
        for element in items:
            if isinstance(element, dict) and ("project_id" in element or "id" in element):
                return True
        return False

    def _build_timeslot_lookup(self) -> Tuple[Dict[Any, int], List[Any], Dict[Any, Any]]:
        timeslots = getattr(self, "timeslots", []) or []
        if not timeslots:
            return {}, [], {}

        def _parse_start(ts: Any) -> Tuple[int, int, int, int]:
            start = ts.get("start_time") if isinstance(ts, dict) else getattr(ts, "start_time", None)
            # Support datetime.time directly
            try:
                from datetime import time as _time
                if isinstance(start, _time):
                    return (start.hour, start.minute, start.second, 0)
            except Exception:
                pass
            # Parse strings (support microseconds)
            if isinstance(start, str):
                for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
                    try:
                        dt = datetime.strptime(start.split()[0], fmt)
                        return (dt.hour, dt.minute, dt.second, 0)
                    except ValueError:
                        continue
            # Fallback to time_range
            tr = ts.get("time_range") if isinstance(ts, dict) else getattr(ts, "time_range", None)
            if isinstance(tr, str) and "-" in tr:
                try:
                    start_part = tr.split("-")[0].strip()
                    for fmt in ("%H:%M", "%H:%M:%S"):
                        try:
                            dt = datetime.strptime(start_part, fmt)
                            return (dt.hour, dt.minute, dt.second, 0)
                        except ValueError:
                            continue
                except Exception:
                    pass
            return (24, 0, 0, 0)

        enumerated = list(enumerate(timeslots))
        enumerated.sort(key=lambda item: (_parse_start(item[1]), item[0]))

        ts_index: Dict[Any, int] = {}
        sorted_ids: List[Any] = []
        id_to_timeslot: Dict[Any, Any] = {}
        for idx, ts in enumerate(enumerated):
            _, slot = ts
            slot_id = slot.get("id") if isinstance(slot, dict) else getattr(slot, "id", idx)
            if slot_id is None:
                slot_id = idx
            ts_index[slot_id] = idx
            sorted_ids.append(slot_id)
            id_to_timeslot[slot_id] = slot
        return ts_index, sorted_ids, id_to_timeslot

    def _detect_classroom_gaps(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        ts_index, sorted_ids, id_to_ts = self._build_timeslot_lookup()
        if not assignments or not ts_index:
            return {"total_gaps": 0, "classrooms_with_gap": 0, "details": []}

        classrooms: Dict[Any, List[int]] = defaultdict(list)
        for assignment in assignments:
            if not isinstance(assignment, dict):
                continue
            classroom_id = assignment.get("classroom_id")
            ts_id = assignment.get("timeslot_id")
            if classroom_id is None or ts_id not in ts_index:
                continue
            classrooms[classroom_id].append(ts_index[ts_id])

        details = []
        total_gap_slots = 0
        for class_id, indices in classrooms.items():
            if not indices:
                continue
            indices = sorted(set(indices))
            class_gaps = []
            for prev, curr in zip(indices, indices[1:]):
                if curr - prev > 1:
                    missing = list(range(prev + 1, curr))
                    total_gap_slots += len(missing)
                    class_gaps.append({
                        "after_timeslot": id_to_ts.get(sorted_ids[prev], {}),
                        "before_timeslot": id_to_ts.get(sorted_ids[curr], {}),
                        "gap_slots": [id_to_ts.get(sorted_ids[m], {}) for m in missing],
                    })
            if class_gaps:
                details.append({
                    "classroom_id": class_id,
                    "gap_segments": class_gaps,
                })

        return {
            "total_gaps": total_gap_slots,
            "classrooms_with_gap": len(details),
            "details": details,
        }

    def _compact_schedule_classrooms(self, assignments: List[Dict[str, Any]]) -> None:
        if not assignments:
            return

        ts_index, sorted_ids, _ = self._build_timeslot_lookup()
        if not ts_index:
            return

        classrooms: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
        for assignment in assignments:
            if isinstance(assignment, dict):
                classrooms[assignment.get("classroom_id")].append(assignment)

        if not classrooms:
            return

        def _min_index(assignment_list: List[Dict[str, Any]]) -> int:
            indices = [ts_index.get(a.get("timeslot_id"), len(sorted_ids)) for a in assignment_list if isinstance(a, dict)]
            return min(indices) if indices else 0

        classroom_order = sorted(
            classrooms.items(),
            key=lambda item: (_min_index(item[1]), item[0]),
        )

        instructor_busy: Dict[Any, Set[int]] = defaultdict(set)

        for class_id, class_assignments in classroom_order:
            valid_assignments = [a for a in class_assignments if isinstance(a, dict) and a.get("timeslot_id") in ts_index]
            if not valid_assignments:
                continue

            remaining = sorted(valid_assignments, key=lambda a: ts_index.get(a.get("timeslot_id"), len(sorted_ids)))

            pointer = _min_index(remaining)

            while remaining and pointer < len(sorted_ids):
                desired_idx = pointer
                chosen_assignment: Optional[Dict[str, Any]] = None
                chosen_target_idx: Optional[int] = None

                for candidate in remaining:
                    candidate_idx = ts_index.get(candidate.get("timeslot_id"), len(sorted_ids))
                    instructors = candidate.get("instructors", []) or []
                    earliest_idx = None
                    for idx in range(desired_idx, candidate_idx + 1):
                        if all(idx not in instructor_busy[instr] for instr in instructors):
                            earliest_idx = idx
                            break
                    if earliest_idx is None:
                        continue
                    if earliest_idx == desired_idx:
                        chosen_assignment = candidate
                        chosen_target_idx = desired_idx
                        break
                    if chosen_assignment is None or (chosen_target_idx is not None and earliest_idx < chosen_target_idx):
                        chosen_assignment = candidate
                        chosen_target_idx = earliest_idx

                if chosen_assignment is None or chosen_target_idx is None:
                    pointer += 1
                    continue

                current_idx = ts_index.get(chosen_assignment.get("timeslot_id"), len(sorted_ids))
                target_idx = chosen_target_idx

                if target_idx != current_idx:
                    for instr in chosen_assignment.get("instructors", []) or []:
                        instructor_busy[instr].discard(current_idx)
                    chosen_assignment["timeslot_id"] = sorted_ids[target_idx]

                for instr in chosen_assignment.get("instructors", []) or []:
                    instructor_busy[instr].add(target_idx)

                remaining.remove(chosen_assignment)
                pointer = target_idx + 1

            for assignment in remaining:
                orig_idx = ts_index.get(assignment.get("timeslot_id"))
                if orig_idx is not None:
                    for instr in assignment.get("instructors", []) or []:
                        instructor_busy[instr].add(orig_idx)

    def _compact_schedule_globally(self, assignments: List[Dict[str, Any]]) -> None:
        if not assignments:
            return
        ts_index, sorted_ids, id_to_ts = self._build_timeslot_lookup()
        if not ts_index:
            return
        classrooms: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
        for a in assignments:
            if isinstance(a, dict):
                classrooms[a.get("classroom_id")].append(a)
        class_ids = [cid for cid in classrooms.keys() if cid is not None]
        if not class_ids:
            return
        instructor_busy: Dict[Any, Set[int]] = defaultdict(set)
        for a in assignments:
            if not isinstance(a, dict):
                continue
            idx = ts_index.get(a.get("timeslot_id"))
            if idx is None:
                continue
            for instr in a.get("instructors", []) or []:
                instructor_busy[instr].add(idx)
        def occupied(cid: Any, idx: int) -> bool:
            for a in classrooms.get(cid, []):
                if ts_index.get(a.get("timeslot_id")) == idx:
                    return True
            return False
        def pull_candidate(target_idx: int) -> Optional[Dict[str, Any]]:
            best: Optional[Dict[str, Any]] = None
            best_delta = None
            for a in assignments:
                if not isinstance(a, dict):
                    continue
                a_idx = ts_index.get(a.get("timeslot_id"))
                if a_idx is None or a_idx <= target_idx:
                    continue
                instructors = a.get("instructors", []) or []
                if all(target_idx not in instructor_busy[i] for i in instructors):
                    delta = a_idx - target_idx
                    if best is None or delta < best_delta:  # type: ignore
                        best = a
                        best_delta = delta
            return best
        def _min_idx(cid: Any) -> int:
            idxs = [ts_index.get(a.get("timeslot_id"), len(sorted_ids)) for a in classrooms.get(cid, [])]
            return min(idxs) if idxs else len(sorted_ids)
        ordered_class_ids = sorted(class_ids, key=_min_idx)
        for cid in ordered_class_ids:
            idxs = sorted({ts_index.get(a.get("timeslot_id")) for a in classrooms.get(cid, []) if ts_index.get(a.get("timeslot_id")) is not None})
            if not idxs:
                continue
            pointer = idxs[0]
            last_idx = idxs[-1]
            while pointer <= last_idx:
                if occupied(cid, pointer):
                    pointer += 1
                    continue
                candidate = pull_candidate(pointer)
                if candidate is None:
                    pointer += 1
                    continue
                old_idx = ts_index.get(candidate.get("timeslot_id"))
                for instr in candidate.get("instructors", []) or []:
                    if old_idx is not None:
                        instructor_busy[instr].discard(old_idx)
                candidate["classroom_id"] = cid
                candidate["timeslot_id"] = sorted_ids[pointer]
                classrooms[cid].append(candidate)
                for instr in candidate.get("instructors", []) or []:
                    instructor_busy[instr].add(pointer)
                pointer += 1

    def _is_late_slot(self, timeslot: Any) -> bool:
        try:
            start_str = timeslot.get("start_time", "") if isinstance(timeslot, dict) else getattr(timeslot, "start_time", "")
            if not start_str:
                return False
            parts = str(start_str).split(":")
            hour = int(parts[0]) if parts and parts[0].isdigit() else 0
            minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            return hour > 16 or (hour == 16 and minute >= 30)
        except Exception:
            return False

    def _count_late_slots(self, assignments: List[Dict[str, Any]]) -> int:
        ts_index, sorted_ids, id_to_ts = self._build_timeslot_lookup()
        if not assignments:
            return 0
        count = 0
        for a in assignments:
            if not isinstance(a, dict):
                continue
            ts = id_to_ts.get(a.get("timeslot_id"))
            if ts and self._is_late_slot(ts):
                count += 1
        return count

    def _enforce_time_policy(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        report = {"late_before": 0, "late_after": 0, "moved": 0, "unmoved": 0}
        if not assignments:
            return report
        ts_index, sorted_ids, id_to_ts = self._build_timeslot_lookup()
        if not ts_index:
            return report
        last_ok_idx = None
        for idx, ts_id in enumerate(sorted_ids):
            ts = id_to_ts.get(ts_id)
            if ts and self._is_late_slot(ts):
                last_ok_idx = idx - 1
                break
        if last_ok_idx is None:
            last_ok_idx = len(sorted_ids) - 1
        occupied: Dict[Tuple[Any, int], bool] = {}
        instructor_busy: Dict[Any, Set[int]] = defaultdict(set)
        classrooms: List[Any] = []
        # Prefer full classroom set from algorithm context to allow moving into empty rooms
        try:
            for c in getattr(self, "classrooms", []) or []:
                cid = c.get("id") if isinstance(c, dict) else getattr(c, "id", None)
                if cid is not None and cid not in classrooms:
                    classrooms.append(cid)
        except Exception:
            classrooms = []
        if not classrooms:
            for a in assignments:
                if not isinstance(a, dict):
                    continue
                cid = a.get("classroom_id")
                if cid is not None and cid not in classrooms:
                    classrooms.append(cid)
            # Build occupancy and instructor busy from all assignments
            for a in assignments:
                if not isinstance(a, dict):
                    continue
                cid = a.get("classroom_id")
                idx = ts_index.get(a.get("timeslot_id"))
                if cid is not None and idx is not None:
                    occupied[(cid, idx)] = True
                for instr in a.get("instructors", []) or []:
                    if idx is not None:
                        instructor_busy[instr].add(idx)
        late_list: List[Dict[str, Any]] = []
        for a in assignments:
            if not isinstance(a, dict):
                continue
            ts = id_to_ts.get(a.get("timeslot_id"))
            if ts and self._is_late_slot(ts):
                late_list.append(a)
        report["late_before"] = len(late_list)
        moved = 0
        for a in late_list:
            current_idx = ts_index.get(a.get("timeslot_id"), None)
            if current_idx is None:
                continue
            instructors = a.get("instructors", []) or []
            moved_here = False
            for target_idx in range(0, last_ok_idx + 1):
                for cid in sorted(classrooms):
                    if occupied.get((cid, target_idx)):
                        continue
                    if all(target_idx not in instructor_busy[instr] for instr in instructors):
                        old_idx = current_idx
                        old_cid = a.get("classroom_id")
                        if old_cid is not None and old_idx is not None:
                            occupied.pop((old_cid, old_idx), None)
                        a["classroom_id"] = cid
                        a["timeslot_id"] = sorted_ids[target_idx]
                        occupied[(cid, target_idx)] = True
                        for instr in instructors:
                            if old_idx is not None:
                                instructor_busy[instr].discard(old_idx)
                            instructor_busy[instr].add(target_idx)
                        moved += 1
                        moved_here = True
                        break
                if moved_here:
                    break
        report["moved"] = moved
        report["late_after"] = self._count_late_slots(assignments)
        report["unmoved"] = max(0, report["late_before"] - moved)
        return report

    def _normalize_text(self, text: Any) -> Any:
        try:
            s = str(text).strip().lower()
            s = " ".join(s.split())
            return s
        except Exception:
            return None

    def _build_project_id_to_name_map(self) -> Dict[Any, str]:
        mapping: Dict[Any, str] = {}
        try:
            for p in getattr(self, "projects", []) or []:
                if isinstance(p, dict):
                    pid = p.get("id")
                    name = p.get("title") or p.get("name") or p.get("project_name")
                else:
                    pid = getattr(p, "id", None)
                    name = getattr(p, "title", None) or getattr(p, "name", None) or getattr(p, "project_name", None)
                if pid is not None and name:
                    norm = self._normalize_text(name)
                    if norm:
                        mapping[pid] = norm
        except Exception:
            pass
        return mapping

    def _get_assignment_project_key(self, assignment: Any, pid_to_name: Dict[Any, str]) -> Any:
        try:
            if isinstance(assignment, dict):
                pid = assignment.get("project_id")
                name = assignment.get("project_name") or assignment.get("title") or assignment.get("name")
            else:
                pid = getattr(assignment, "project_id", None)
                name = getattr(assignment, "project_name", None) or getattr(assignment, "title", None) or getattr(assignment, "name", None)
            norm = self._normalize_text(name) if name else None
            if norm:
                return norm
            if pid in pid_to_name:
                return pid_to_name.get(pid)
            return pid
        except Exception:
            return None