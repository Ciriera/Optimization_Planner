"""
Harmony Search Algorithm - ARA Proje Öncelikli
Çok Kriterli ve Çok Kısıtlı Akademik Proje Sınavı / Jüri Planlama Sistemi

==========================================================================
TEMEL ÖZELLİKLER:
==========================================================================
1. ARA Projeler SABAH saatlerine (HARD constraint) - PSO'nun tam tersi!
2. Bitirme Projeleri öğleden sonra (Ara bittikten sonra)  
3. 2. Jüri = "[Araştırma Görevlisi]" placeholder (her projede)
4. Her timeslotta her öğretim görevlisi EN FAZLA 1 görev
5. Öğretim görevlisi kendi projesine jüri OLAMAZ
6. Süreklilik: Öğretim görevlileri mümkün olduğunca arka arkaya görev alır
7. İş yükü dengesi: Görevler eşit dağıtılır (±2 tolerans)
8. Back-to-back sınıf yerleşimi

==========================================================================
AMAÇ FONKSİYONU: min Z = C1·H1 + C2·H2 + C3·H3
==========================================================================
H1: Zaman/GAP cezası (öğretim görevlisi boşlukları)
H2: İş yükü dengesizlik cezası (dominant kriter)
H3: Sınıf değişimi cezası
"""
from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional, Set
from enum import Enum
import random
import logging
import copy
import time
from collections import defaultdict
from datetime import time as dt_time

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)

# ==========================================================================
# SABITLER
# ==========================================================================
JURY2_PLACEHOLDER = "[Araştırma Görevlisi]"
HARD_CONSTRAINT_PENALTY = 1_000_000.0


class TimePenaltyMode(Enum):
    BINARY = "binary"
    GAP_PROPORTIONAL = "gap_proportional"


class WorkloadConstraintMode(Enum):
    SOFT_ONLY = "soft_only"
    SOFT_AND_HARD = "soft_and_hard"


class HarmonySearch(OptimizationAlgorithm):
    """
    Harmony Search Algorithm - Süreklilik ve İş Yükü Odaklı
    ARA PROJELER ÖNCELİKLİ (PSO'nun tersi)
    """

    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        params = params or {}
        
        # HS Parametreleri (PSO ile aynı mantık)
        self.n_particles = params.get("n_particles", 40)
        self.n_iterations = params.get("n_iterations", 300)
        self.inertia_weight = params.get("inertia_weight", 0.5)
        self.cognitive_weight = params.get("cognitive_weight", 2.0)
        self.social_weight = params.get("social_weight", 2.0)
        
        # Ceza Katsayıları - İŞ YÜKÜ DENGESİ EN ÖNEMLİ!
        self.C1 = params.get("time_penalty_weight", 15.0)
        self.C2 = params.get("workload_penalty_weight", 50.0)
        self.C3 = params.get("class_change_penalty_weight", 10.0)
        
        time_mode = params.get("time_penalty_mode", "gap_proportional")
        self.time_penalty_mode = TimePenaltyMode(time_mode) if isinstance(time_mode, str) else time_mode
        
        self.workload_tolerance = params.get("workload_tolerance", 2)
        
        # Veri
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        self.sorted_timeslots = []
        self.timeslot_order = {}
        self.instructor_ids = []
        self.instructor_id_set = set()

    def _safe_int(self, val) -> Optional[int]:
        if val is None:
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    def initialize(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Instructor ID'leri temizle
        self.instructor_ids = []
        self.instructor_id_set = set()
        for inst in self.instructors:
            iid = self._safe_int(inst.get("id"))
            if iid is not None and iid not in self.instructor_id_set:
                self.instructor_ids.append(iid)
                self.instructor_id_set.add(iid)
        
        # Timeslotları sırala
        self.sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time_to_minutes(x.get("start_time", "09:00"))
        )
        
        # Timeslot sıra numarası (süreklilik hesabı için)
        self.timeslot_order = {}
        for idx, ts in enumerate(self.sorted_timeslots):
            ts_id = self._safe_int(ts.get("id"))
            if ts_id is not None:
                self.timeslot_order[ts_id] = idx
        
        pass

    def _parse_time_to_minutes(self, time_str) -> int:
        if not time_str:
            return 0
        try:
            if isinstance(time_str, dt_time):
                return time_str.hour * 60 + time_str.minute
            parts = str(time_str).split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 0

    def _is_bitirme(self, project: Dict) -> bool:
        t = str(project.get("type", "")).lower()
        return t in ["bitirme", "final"]

    def _is_ara(self, project: Dict) -> bool:
        t = str(project.get("type", "")).lower()
        return t in ["ara", "interim"]

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.optimize(data)

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        self.initialize(data)
        
        pass
        
        bitirme_projects = [p for p in self.projects if self._is_bitirme(p)]
        ara_projects = [p for p in self.projects if self._is_ara(p)]
        
        pass
        
        if not self.projects:
            return self._create_empty_result(time.time() - start_time, "No projects")
        
        # AŞAMA 1: Slot ataması - ARA ÖNCELİKLİ (PSO'nun tersi!)
        assignments = self._create_initial_assignments(ara_projects, bitirme_projects)
        
        if not assignments:
            return self._create_empty_result(time.time() - start_time, "Slot assignment failed")
        
        # AŞAMA 2: Süreklilik odaklı jüri ataması
        assignments = self._assign_juries_with_continuity(assignments)
        
        # AŞAMA 3: HS optimizasyonu (PSO ile aynı mantık)
        assignments = self._hs_optimize(assignments)
        
        # AŞAMA 4: Son düzeltmeler
        assignments = self._final_fix(assignments)
        
        execution_time = time.time() - start_time
        fitness = self._calculate_fitness(assignments)
        h1, h2, h3 = self._calculate_penalties(assignments)
        continuity = self._calculate_continuity_score(assignments)
        
        self._log_final_stats(assignments, fitness, h1, h2, h3, continuity)
        
        return {
            "assignments": assignments,
            "schedule": assignments,
            "solution": assignments,
            "fitness": fitness,
            "execution_time": execution_time,
            "algorithm": "Harmony Search - Çok Kriterli Optimizasyon",
            "status": "completed",
            "metrics": {
                "H1_time_penalty": h1,
                "H2_workload_penalty": h2,
                "H3_class_change_penalty": h3,
                "continuity_score": continuity
            }
        }

    # ==========================================================================
    # AŞAMA 1: SLOT ATAMASI - ARA ÖNCELİKLİ!
    # ==========================================================================
    def _create_initial_assignments(self, ara_projects: List[Dict], 
                                     bitirme_projects: List[Dict]) -> List[Dict]:
        """
        CONSTRAINT-AWARE + SINIF SÜREKLİLİKLİ + RASTGELELİKLİ SLOT ATAMASI
        
        ÖNEMLİ: ARA PROJELER ÖNCELİKLİ (PSO'nun tersi)
        
        1. Her timeslot'ta max sınıf sayısı kadar proje atanabilir
        2. Aynı timeslot'ta aynı sorumlu iki projede olamaz
        3. Öğretmenler mümkünse aynı sınıfta kalır (süreklilik)
        4. Projeler RASTGELE sırada işlenir (her çalıştırmada farklı sonuç)
        """
        assignments = []
        n_classrooms = len(self.classrooms)
        n_timeslots = len(self.sorted_timeslots)
        
        if n_classrooms == 0 or n_timeslots == 0:
            return assignments
        
        # Projeleri sorumlu bazlı hazırla ve SHUFFLE ET!
        remaining_ara = list(ara_projects)
        remaining_bitirme = list(bitirme_projects)
        
        # RASTGELELİK: Projeleri karıştır
        random.shuffle(remaining_ara)
        random.shuffle(remaining_bitirme)
        
        # Her timeslot için hangi sorumlular kullanıldı
        timeslot_used_responsibles = defaultdict(set)
        
        # Her timeslot'a atanan projeler
        timeslot_assignments = defaultdict(list)
        
        # Her timeslot için hangi sınıflar kullanıldı
        timeslot_used_classrooms = defaultdict(set)
        
        # Öğretmenlerin tercih ettiği sınıf
        responsible_preferred_classroom = {}
        
        def get_best_classroom(rid: int, ts_order: int) -> int:
            """Sorumlu için en iyi sınıfı bul"""
            used_cids = timeslot_used_classrooms[ts_order]
            
            if rid and rid in responsible_preferred_classroom:
                preferred_cid = responsible_preferred_classroom[rid]
                if preferred_cid not in used_cids:
                    for idx, c in enumerate(self.classrooms):
                        if self._safe_int(c.get("id")) == preferred_cid:
                            return idx
            
            available_classrooms = []
            for idx, c in enumerate(self.classrooms):
                cid = self._safe_int(c.get("id"))
                if cid not in used_cids:
                    available_classrooms.append(idx)
            
            if available_classrooms:
                return random.choice(available_classrooms)
            
            return -1
        
        def try_assign_project(project: Dict, ts_order: int, project_type: str) -> bool:
            """Projeyi belirli timeslot'a atamayı dene"""
            rid = self._safe_int(
                project.get("responsible_id") or project.get("responsible_instructor_id")
            )
            
            if rid and rid in timeslot_used_responsibles[ts_order]:
                return False
            
            classroom_idx = get_best_classroom(rid, ts_order)
            if classroom_idx < 0:
                return False
            
            timeslot = self.sorted_timeslots[ts_order]
            ts_id = self._safe_int(timeslot.get("id"))
            classroom = self.classrooms[classroom_idx]
            cid = self._safe_int(classroom.get("id"))
            
            assignment = {
                "project_id": project.get("id"),
                "classroom_id": cid,
                "timeslot_id": ts_id,
                "ts_order": ts_order,
                "responsible_id": rid,
                "jury1_id": None,
                "jury2": JURY2_PLACEHOLDER,
                "instructors": [rid] if rid else [],
                "project_type": project_type
            }
            
            timeslot_assignments[ts_order].append(assignment)
            timeslot_used_classrooms[ts_order].add(cid)
            if rid:
                timeslot_used_responsibles[ts_order].add(rid)
                responsible_preferred_classroom[rid] = cid
            
            return True
        
        # ================================================================
        # GAP'SIZ SLOT ATAMASI - ARA ÖNCELİKLİ!
        # 
        # TEMEL KURAL: Her timeslot TAMAMEN doldurulur, BOŞ slot olmaz!
        # 
        # Strateji (PSO'nun tersi):
        # - Her timeslot için önce ARA projelerini yerleştir
        # - Ara kalmadıysa/atanamadıysa Bitirme ile doldur
        # ================================================================
        
        current_ts = 0
        
        while (remaining_ara or remaining_bitirme) and current_ts < n_timeslots:
            if len(timeslot_assignments[current_ts]) >= n_classrooms:
                current_ts += 1
                continue
            
            assigned = False
            
            # 1. Önce ARA projelerini yerleştirmeye çalış (PSO'nun tersi!)
            if remaining_ara:
                for i, project in enumerate(remaining_ara):
                    if try_assign_project(project, current_ts, "ara"):
                        remaining_ara.pop(i)
                        assigned = True
                        break
            
            # 2. Ara yoksa veya atanamadıysa, Bitirme dene
            if not assigned and remaining_bitirme:
                for i, project in enumerate(remaining_bitirme):
                    if try_assign_project(project, current_ts, "bitirme"):
                        remaining_bitirme.pop(i)
                        assigned = True
                        break
            
            if not assigned:
                current_ts += 1
        
        for ts_order in sorted(timeslot_assignments.keys()):
            assignments.extend(timeslot_assignments[ts_order])
        
        return assignments

    def _create_assignment(self, project: Dict, slot: Dict, project_type: str) -> Dict:
        responsible_id = self._safe_int(
            project.get("responsible_id") or project.get("responsible_instructor_id")
        )
        
        return {
            "project_id": project.get("id"),
            "classroom_id": slot["classroom_id"],
            "timeslot_id": slot["timeslot_id"],
            "ts_order": slot["ts_order"],
            "responsible_id": responsible_id,
            "jury1_id": None,
            "jury2": JURY2_PLACEHOLDER,
            "instructors": [responsible_id] if responsible_id else [],
            "project_type": project_type
        }

    # ==========================================================================
    # AŞAMA 2: SÜREKLİLİK ODAKLI JÜRI ATAMASI
    # ==========================================================================
    def _assign_juries_with_continuity(self, assignments: List[Dict]) -> List[Dict]:
        """Süreklilik odaklı jüri ataması"""
        instructor_busy = defaultdict(set)
        instructor_workload = defaultdict(int)
        instructor_slots = defaultdict(list)
        instructor_resp_count = defaultdict(int)
        
        for a in assignments:
            rid = a.get("responsible_id")
            ts_id = a.get("timeslot_id")
            ts_order = a.get("ts_order", 0)
            cid = a.get("classroom_id")
            
            if rid and ts_id:
                instructor_busy[rid].add(ts_id)
                instructor_workload[rid] += 1
                instructor_resp_count[rid] += 1
                instructor_slots[rid].append({"ts_order": ts_order, "classroom_id": cid})
        
        total_roles = len(assignments) * 2
        avg_workload = total_roles / len(self.instructor_ids) if self.instructor_ids else 0
        
        instructor_target_jury = {}
        for iid in self.instructor_ids:
            resp_count = instructor_resp_count.get(iid, 0)
            target_jury = max(0, round(avg_workload) - resp_count)
            instructor_target_jury[iid] = target_jury
        
        sorted_assignments = sorted(assignments, key=lambda x: (x.get("ts_order", 0), x.get("classroom_id", 0)))
        
        for a in sorted_assignments:
            ts_id = a.get("timeslot_id")
            ts_order = a.get("ts_order", 0)
            responsible_id = a.get("responsible_id")
            classroom_id = a.get("classroom_id")
            
            best_jury = self._find_best_jury(
                ts_id, ts_order, responsible_id, classroom_id,
                instructor_busy, instructor_slots, instructor_workload, avg_workload,
                instructor_resp_count
            )
            
            if best_jury:
                a["jury1_id"] = best_jury
                instructor_busy[best_jury].add(ts_id)
                instructor_workload[best_jury] += 1
                instructor_slots[best_jury].append({"ts_order": ts_order, "classroom_id": classroom_id})
                
                insts = [responsible_id] if responsible_id else []
                insts.append(best_jury)
                a["instructors"] = insts
        
        return assignments

    def _find_best_jury(self, ts_id: int, ts_order: int, responsible_id: Optional[int],
                        classroom_id: int, instructor_busy: Dict,
                        instructor_slots: Dict, instructor_workload: Dict,
                        avg_workload: float, instructor_resp_count: Dict = None) -> Optional[int]:
        """En uygun jüriyi bul - İŞ YÜKÜ DENGESİ ÖNCELİKLİ"""
        instructor_resp_count = instructor_resp_count or {}
        
        available = []
        for iid in self.instructor_ids:
            if iid == responsible_id:
                continue
            if ts_id in instructor_busy.get(iid, set()):
                continue
            available.append(iid)
        
        if not available:
            return None
        
        workloads = list(instructor_workload.values()) if instructor_workload else [0]
        current_min = min(workloads) if workloads else 0
        current_max = max(workloads) if workloads else 0
        current_diff = current_max - current_min
        
        avg_target = round(avg_workload)
        
        candidates_with_score = []
        for iid in available:
            current_total = instructor_workload.get(iid, 0)
            resp_count = instructor_resp_count.get(iid, 0)
            
            new_total = current_total + 1
            deviation = abs(new_total - avg_target)
            resp_penalty = resp_count * 10
            
            continuity_bonus = 0
            slots = instructor_slots.get(iid, [])
            if slots:
                for s in slots:
                    if s["classroom_id"] == classroom_id and abs(ts_order - s["ts_order"]) == 1:
                        continuity_bonus = -15
                        break
            
            priority_score = deviation + resp_penalty - (avg_target - new_total) * 5 + continuity_bonus
            
            candidates_with_score.append((iid, priority_score, current_total))
        
        candidates_with_score.sort(key=lambda x: (x[1], x[2]))
        
        if not candidates_with_score:
            return None
        
        best_score = candidates_with_score[0][1]
        best_candidates = [c for c in candidates_with_score if c[1] <= best_score + 10]
        
        random.shuffle(best_candidates)
        
        if len(best_candidates) == 1:
            return best_candidates[0][0]
        
        scored_candidates = []
        
        for iid, _, _ in best_candidates:
            score = 0.0
            slots = instructor_slots.get(iid, [])
            
            if slots:
                min_gap = min(abs(ts_order - s["ts_order"]) for s in slots)
                
                same_class_consecutive = False
                for s in slots:
                    if s["classroom_id"] == classroom_id and abs(ts_order - s["ts_order"]) == 1:
                        score -= 500
                        same_class_consecutive = True
                        break
                
                if not same_class_consecutive:
                    if min_gap == 1:
                        score += 50
                    elif min_gap == 2:
                        score += 100
                    else:
                        score += min_gap * 50
            
            score += random.uniform(-3, 3)
            scored_candidates.append((iid, score))
        
        scored_candidates.sort(key=lambda x: x[1])
        return scored_candidates[0][0]

    def _calculate_jury_score(self, iid: int, ts_order: int, classroom_id: int,
                               existing_slots: List[Dict], current_workload: int,
                               avg_workload: float, min_workload: int = 0, 
                               max_workload: int = 0) -> float:
        """Jüri skoru (düşük = iyi)"""
        score = 0.0
        
        workload_after = current_workload + 1
        new_max = max(max_workload, workload_after)
        new_min = min_workload
        predicted_diff = new_max - new_min
        
        if predicted_diff > 3:
            score += (predicted_diff - 3) * 800
        
        deviation = abs(workload_after - avg_workload)
        if deviation > 2:
            score += (deviation - 2) * 200
        elif deviation > 1:
            score += 50
        
        if current_workload < avg_workload - 1:
            score -= 250
        elif current_workload < avg_workload:
            score -= 100
        elif current_workload > avg_workload + 1:
            score += 300
        elif current_workload > avg_workload:
            score += 100
        
        if existing_slots:
            min_gap = float('inf')
            best_match = None
            
            for s in existing_slots:
                gap = abs(ts_order - s["ts_order"])
                if gap < min_gap:
                    min_gap = gap
                    best_match = s
                elif gap == min_gap and s["classroom_id"] == classroom_id:
                    best_match = s
            
            if best_match:
                is_same_classroom = (best_match["classroom_id"] == classroom_id)
                
                if min_gap == 1:
                    if is_same_classroom:
                        score -= 100
                    else:
                        score += 30
                elif min_gap == 2:
                    if is_same_classroom:
                        score -= 40
                    else:
                        score += 20
                else:
                    score += min_gap * 10
            
            for s in existing_slots:
                if s["classroom_id"] == classroom_id:
                    diff = abs(ts_order - s["ts_order"])
                    if diff == 1:
                        score -= 80
        
        return score

    # ==========================================================================
    # AŞAMA 3: HS OPTİMİZASYONU (PSO ile aynı mantık)
    # ==========================================================================
    def _hs_optimize(self, assignments: List[Dict]) -> List[Dict]:
        """Harmony Search ile jüri optimizasyonu"""
        if len(assignments) < 2:
            return assignments
        
        pass
        
        current = copy.deepcopy(assignments)
        current = self._fix_hard_constraints(current)
        current_fitness = self._calculate_fitness(current)
        
        best_global = copy.deepcopy(current)
        best_global_fitness = current_fitness
        
        particles = []
        for _ in range(self.n_particles):
            p = self._create_particle_variation(assignments)
            p = self._fix_hard_constraints(p)
            f = self._calculate_fitness(p)
            
            particles.append({
                "pos": p, "fit": f,
                "best_pos": copy.deepcopy(p), "best_fit": f
            })
            
            if f < best_global_fitness:
                best_global_fitness = f
                best_global = copy.deepcopy(p)
        
        for it in range(self.n_iterations):
            for p in particles:
                new_pos = self._update_particle(p["pos"], p["best_pos"], best_global)
                new_pos = self._fix_hard_constraints(new_pos)
                new_fit = self._calculate_fitness(new_pos)
                
                p["pos"] = new_pos
                p["fit"] = new_fit
                
                if new_fit < p["best_fit"]:
                    p["best_fit"] = new_fit
                    p["best_pos"] = copy.deepcopy(new_pos)
                
                if new_fit < best_global_fitness:
                    best_global_fitness = new_fit
                    best_global = copy.deepcopy(new_pos)
            
            pass
        
        return best_global

    def _create_particle_variation(self, base: List[Dict]) -> List[Dict]:
        """Varyasyon oluştur"""
        result = copy.deepcopy(base)
        change_count = max(1, len(result) // 4)
        
        if not result:
            return result
            
        indices = random.sample(range(len(result)), min(change_count, len(result)))
        
        for idx in indices:
            a = result[idx]
            rid = a.get("responsible_id")
            candidates = [iid for iid in self.instructor_ids if iid != rid]
            if candidates:
                a["jury1_id"] = random.choice(candidates)
        
        return result

    def _update_particle(self, current: List[Dict], personal_best: List[Dict],
                         global_best: List[Dict]) -> List[Dict]:
        """HS pozisyon güncelleme"""
        result = copy.deepcopy(current)
        busy = self._build_busy_map(result)
        
        for i, a in enumerate(result):
            if i >= len(personal_best) or i >= len(global_best):
                continue
            
            ts_id = a.get("timeslot_id")
            rid = a.get("responsible_id")
            current_jury = a.get("jury1_id")
            
            new_jury = current_jury
            r1, r2, r3 = random.random(), random.random(), random.random()
            
            if r1 < self.cognitive_weight / 4:
                pb_jury = personal_best[i].get("jury1_id")
                if pb_jury and pb_jury != rid and ts_id not in busy.get(pb_jury, set()):
                    new_jury = pb_jury
            
            if r2 < self.social_weight / 4:
                gb_jury = global_best[i].get("jury1_id")
                if gb_jury and gb_jury != rid and ts_id not in busy.get(gb_jury, set()):
                    new_jury = gb_jury
            
            if r3 < self.inertia_weight / 5:
                candidates = [
                    iid for iid in self.instructor_ids
                    if iid != rid and ts_id not in busy.get(iid, set())
                ]
                if candidates:
                    new_jury = random.choice(candidates)
            
            if new_jury != current_jury:
                if current_jury:
                    busy[current_jury].discard(ts_id)
                
                a["jury1_id"] = new_jury
                insts = [rid] if rid else []
                if new_jury:
                    insts.append(new_jury)
                    busy[new_jury].add(ts_id)
                a["instructors"] = insts
        
        return result

    def _build_busy_map(self, assignments: List[Dict]) -> Dict[int, Set[int]]:
        """instructor_id -> set of busy timeslot_ids"""
        busy = defaultdict(set)
        for a in assignments:
            ts_id = a.get("timeslot_id")
            if a.get("responsible_id") and ts_id:
                busy[a["responsible_id"]].add(ts_id)
            if a.get("jury1_id") and ts_id:
                busy[a["jury1_id"]].add(ts_id)
        return busy

    # ==========================================================================
    # AŞAMA 4: HARD CONSTRAINT DÜZELTMELERİ
    # ==========================================================================
    def _fix_hard_constraints(self, assignments: List[Dict]) -> List[Dict]:
        """Hard constraint ihlallerini düzelt"""
        busy = defaultdict(set)
        
        for a in assignments:
            rid = a.get("responsible_id")
            ts_id = a.get("timeslot_id")
            if rid and ts_id:
                busy[rid].add(ts_id)
        
        for a in assignments:
            ts_id = a.get("timeslot_id")
            rid = a.get("responsible_id")
            jid = a.get("jury1_id")
            
            need_fix = False
            
            if jid is None:
                need_fix = True
            elif jid == rid:
                need_fix = True
            elif ts_id in busy.get(jid, set()):
                need_fix = True
            
            if need_fix:
                new_jury = self._find_available_jury(ts_id, rid, busy)
                
                if new_jury:
                    a["jury1_id"] = new_jury
                    busy[new_jury].add(ts_id)
                else:
                    a["jury1_id"] = None
                
                insts = [rid] if rid else []
                if a["jury1_id"]:
                    insts.append(a["jury1_id"])
                a["instructors"] = insts
            else:
                if jid:
                    busy[jid].add(ts_id)
            
            a["jury2"] = JURY2_PLACEHOLDER
        
        return assignments

    def _find_available_jury(self, ts_id: int, responsible_id: Optional[int],
                              busy: Dict[int, Set[int]]) -> Optional[int]:
        """Müsait jüri bul"""
        candidates = []
        for iid in self.instructor_ids:
            if iid == responsible_id:
                continue
            if ts_id in busy.get(iid, set()):
                continue
            workload = len(busy.get(iid, set()))
            candidates.append((iid, workload))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def _final_fix(self, assignments: List[Dict]) -> List[Dict]:
        """Son düzeltmeler - Real Simplex uyumlu format"""
        for a in assignments:
            a["jury2"] = JURY2_PLACEHOLDER
            
            instructor_list = []
            
            rid = a.get("responsible_id")
            if rid:
                instructor_list.append(rid)
            
            j1id = a.get("jury1_id")
            if j1id:
                instructor_list.append(j1id)
            
            instructor_list.append({
                "id": -1,
                "name": JURY2_PLACEHOLDER,
                "is_placeholder": True
            })
            
            a["instructors"] = instructor_list
        
        return assignments

    # ==========================================================================
    # FITNESS VE CEZALAR
    # ==========================================================================
    def _calculate_fitness(self, assignments: List[Dict]) -> float:
        h1, h2, h3 = self._calculate_penalties(assignments)
        violations = self._count_hard_violations(assignments)
        return self.C1 * h1 + self.C2 * h2 + self.C3 * h3 + violations * HARD_CONSTRAINT_PENALTY

    def _calculate_penalties(self, assignments: List[Dict]) -> Tuple[float, float, float]:
        tasks = defaultdict(list)
        workload = defaultdict(int)
        
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
                    tasks[iid].append({"ts_order": ts_order, "cid": cid})
                    workload[iid] += 1
        
        h1 = 0.0
        for iid, tlist in tasks.items():
            if len(tlist) < 2:
                continue
            sorted_t = sorted(tlist, key=lambda x: x["ts_order"])
            for i in range(len(sorted_t) - 1):
                gap = sorted_t[i+1]["ts_order"] - sorted_t[i]["ts_order"] - 1
                if gap > 0:
                    if self.time_penalty_mode == TimePenaltyMode.BINARY:
                        h1 += 1
                    else:
                        h1 += gap
        
        h2 = 0.0
        if workload:
            vals = list(workload.values())
            avg = sum(vals) / len(vals)
            for cnt in vals:
                dev = abs(cnt - avg)
                if dev > self.workload_tolerance:
                    h2 += (dev - self.workload_tolerance) ** 2
        
        h3 = 0.0
        for iid, tlist in tasks.items():
            if len(tlist) < 2:
                continue
            sorted_t = sorted(tlist, key=lambda x: x["ts_order"])
            for i in range(len(sorted_t) - 1):
                if sorted_t[i+1]["ts_order"] - sorted_t[i]["ts_order"] <= 2:
                    if sorted_t[i]["cid"] != sorted_t[i+1]["cid"]:
                        h3 += 1
        
        return h1, h2, h3

    def _count_hard_violations(self, assignments: List[Dict]) -> int:
        count = 0
        usage = defaultdict(list)
        
        for a in assignments:
            ts_id = a.get("timeslot_id")
            rid = a.get("responsible_id")
            jid = a.get("jury1_id")
            
            if jid and jid == rid:
                count += 1
            
            if jid is None:
                count += 1
            
            if rid and ts_id:
                usage[(rid, ts_id)].append("r")
            if jid and ts_id:
                usage[(jid, ts_id)].append("j")
        
        for key, roles in usage.items():
            if len(roles) > 1:
                count += len(roles) - 1
        
        return count

    def _calculate_continuity_score(self, assignments: List[Dict]) -> float:
        tasks = defaultdict(list)
        
        for a in assignments:
            ts_order = a.get("ts_order", 0)
            for inst in a.get("instructors", []):
                if isinstance(inst, dict):
                    iid = inst.get("id")
                    if iid == -1:
                        continue
                else:
                    iid = inst
                
                if iid:
                    tasks[iid].append(ts_order)
        
        total = 0
        consecutive = 0
        
        for iid, orders in tasks.items():
            if len(orders) < 2:
                continue
            sorted_o = sorted(orders)
            for i in range(len(sorted_o) - 1):
                total += 1
                if sorted_o[i+1] - sorted_o[i] == 1:
                    consecutive += 1
        
        if total == 0:
            return 100.0
        return (consecutive / total) * 100

    def _log_final_stats(self, assignments: List[Dict], fitness: float,
                          h1: float, h2: float, h3: float, continuity: float):
        pass

    def _create_empty_result(self, exec_time: float, error: str) -> Dict[str, Any]:
        return {
            "assignments": [],
            "schedule": [],
            "solution": [],
            "fitness": 0.0,
            "execution_time": exec_time,
            "algorithm": "Harmony Search",
            "status": "failed",
            "error": error
        }

    def evaluate_fitness(self, solution: Any) -> float:
        if isinstance(solution, list):
            return self._calculate_fitness(solution)
        return 0.0
