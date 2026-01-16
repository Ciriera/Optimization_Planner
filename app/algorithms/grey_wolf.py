"""
Grey Wolf Optimizer (GWO) - ÖNCELİKSİZ
Çok Kriterli ve Çok Kısıtlı Akademik Proje Sınavı / Jüri Planlama Sistemi

==========================================================================
TEMEL ÖZELLİKLER:
==========================================================================
1. Projeler ÖNCELİKSİZ - Bitirme ve Ara projeleri KARIŞIK atanır
2. 2. Jüri = "[Araştırma Görevlisi]" placeholder (her projede)
3. Her timeslotta her öğretim görevlisi EN FAZLA 1 görev
4. Öğretim görevlisi kendi projesine jüri OLAMAZ
5. Süreklilik: Öğretim görevlileri mümkün olduğunca arka arkaya görev alır
6. İş yükü dengesi: Görevler eşit dağıtılır (±2 tolerans)
7. Back-to-back sınıf yerleşimi

==========================================================================
AMAÇ FONKSİYONU: min Z = C1·H1 + C2·H2 + C3·H3
==========================================================================
H1: Zaman/GAP cezası (öğretim görevlisi boşlukları)
H2: İş yükü dengesizlik cezası (dominant kriter)
H3: Sınıf değişimi cezası

NOT: Bu algoritma PSO ile aynı mantıkta çalışır, tek fark:
- PSO: Bitirme projeleri öncelikli
- GWO: Projeler önceliksiz (karışık sırada)
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


class GreyWolf(OptimizationAlgorithm):
    """
    Grey Wolf Optimizer - Süreklilik ve İş Yükü Odaklı
    
    PSO ile aynı mantıkta çalışır ama projeler ÖNCELİKSİZ atanır.
    """

    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        params = params or {}
        
        # GWO Parametreleri (PSO ile aynı)
        self.n_wolves = params.get("n_wolves", 40)  # Alfa, Beta, Delta + Omega kurtları
        self.n_iterations = params.get("n_iterations", 300)
        self.a_decay = params.get("a_decay", 2.0)  # a parametresi azalma oranı
        self.cognitive_weight = params.get("cognitive_weight", 2.0)
        self.social_weight = params.get("social_weight", 2.0)
        
        # Ceza Katsayıları - İŞ YÜKÜ DENGESİ EN ÖNEMLİ!
        self.C1 = params.get("time_penalty_weight", 15.0)       # GAP cezası
        self.C2 = params.get("workload_penalty_weight", 50.0)   # İş yükü DENGESİ - EN ÖNEMLİ!
        self.C3 = params.get("class_change_penalty_weight", 10.0)  # Sınıf değişimi
        
        time_mode = params.get("time_penalty_mode", "gap_proportional")
        self.time_penalty_mode = TimePenaltyMode(time_mode) if isinstance(time_mode, str) else time_mode
        
        self.workload_tolerance = params.get("workload_tolerance", 2)
        
        # Veri
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        self.sorted_timeslots = []
        self.timeslot_order = {}  # timeslot_id -> sıra numarası (süreklilik için)
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
        
        # ÖNCELİKSİZ: Tüm projeleri karışık sırada işle
        all_projects = list(self.projects)
        random.shuffle(all_projects)
        
        bitirme_count = sum(1 for p in all_projects if self._is_bitirme(p))
        ara_count = sum(1 for p in all_projects if self._is_ara(p))
        
        pass
        
        if not self.projects:
            return self._create_empty_result(time.time() - start_time, "No projects")
        
        # AŞAMA 1: Slot ataması (ÖNCELİKSİZ)
        assignments = self._create_initial_assignments(all_projects)
        
        if not assignments:
            return self._create_empty_result(time.time() - start_time, "Slot assignment failed")
        
        # AŞAMA 2: Süreklilik odaklı jüri ataması
        assignments = self._assign_juries_with_continuity(assignments)
        
        # AŞAMA 3: GWO optimizasyonu
        assignments = self._gwo_optimize(assignments)
        
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
            "algorithm": "Grey Wolf Optimizer - Çok Kriterli Optimizasyon (Önceliksiz)",
            "status": "completed",
            "metrics": {
                "H1_time_penalty": h1,
                "H2_workload_penalty": h2,
                "H3_class_change_penalty": h3,
                "continuity_score": continuity
            }
        }

    # ==========================================================================
    # AŞAMA 1: SLOT ATAMASI (ÖNCELİKSİZ)
    # ==========================================================================
    def _create_initial_assignments(self, all_projects: List[Dict]) -> List[Dict]:
        """
        CONSTRAINT-AWARE + SINIF SÜREKLİLİKLİ + RASTGELELİKLİ SLOT ATAMASI
        
        PSO'dan farkı: ÖNCELİK YOK! Tüm projeler karışık sırada atanır.
        
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
        
        # ÖNCELİKSİZ: Projeleri karıştır
        remaining_projects = list(all_projects)
        random.shuffle(remaining_projects)
        
        # Her timeslot için hangi sorumlular kullanıldı
        timeslot_used_responsibles = defaultdict(set)
        
        # Her timeslot'a atanan projeler
        timeslot_assignments = defaultdict(list)  # ts_order -> list of assignments
        
        # Her timeslot için hangi sınıflar kullanıldı
        timeslot_used_classrooms = defaultdict(set)  # ts_order -> set of classroom_ids
        
        # Öğretmenlerin tercih ettiği sınıf (son kullandıkları)
        responsible_preferred_classroom = {}  # responsible_id -> classroom_id
        
        def get_best_classroom(rid: int, ts_order: int) -> int:
            """Sorumlu için en iyi sınıfı bul"""
            used_cids = timeslot_used_classrooms[ts_order]
            
            # 1. Bu öğretmenin tercih ettiği sınıf boşsa, onu seç (sürekliliği korumak için)
            if rid and rid in responsible_preferred_classroom:
                preferred_cid = responsible_preferred_classroom[rid]
                if preferred_cid not in used_cids:
                    # Classroom index bul
                    for idx, c in enumerate(self.classrooms):
                        if self._safe_int(c.get("id")) == preferred_cid:
                            return idx
            
            # 2. Yoksa boş sınıflar arasından RASTGELE seç
            available_classrooms = []
            for idx, c in enumerate(self.classrooms):
                cid = self._safe_int(c.get("id"))
                if cid not in used_cids:
                    available_classrooms.append(idx)
            
            if available_classrooms:
                return random.choice(available_classrooms)
            
            return -1  # Hiç boş sınıf yok
        
        def try_assign_project(project: Dict, ts_order: int) -> bool:
            """Projeyi belirli timeslot'a atamayı dene"""
            rid = self._safe_int(
                project.get("responsible_id") or project.get("responsible_instructor_id")
            )
            
            # Bu timeslot'ta bu sorumlu zaten var mı?
            if rid and rid in timeslot_used_responsibles[ts_order]:
                return False
            
            # En iyi sınıfı bul
            classroom_idx = get_best_classroom(rid, ts_order)
            if classroom_idx < 0:
                return False  # Boş sınıf yok
            
            # Timeslot ve sınıf bilgisi
            timeslot = self.sorted_timeslots[ts_order]
            ts_id = self._safe_int(timeslot.get("id"))
            classroom = self.classrooms[classroom_idx]
            cid = self._safe_int(classroom.get("id"))
            
            # Proje tipi
            project_type = "bitirme" if self._is_bitirme(project) else "ara"
            
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
                # Bu öğretmenin tercih ettiği sınıfı güncelle
                responsible_preferred_classroom[rid] = cid
            
            return True
        
        # ================================================================
        # GAP'SIZ SLOT ATAMASI (ÖNCELİKSİZ)
        # 
        # TEMEL KURAL: Her timeslot TAMAMEN doldurulur, BOŞ slot olmaz!
        # 
        # Strateji:
        # - Projeleri KARIŞTIR ve sırayla yerleştir
        # - Timeslot dolana kadar devam et, sonra sonraki timeslot'a geç
        # ================================================================
        
        current_ts = 0
        
        while remaining_projects and current_ts < n_timeslots:
            # Bu timeslot dolu mu?
            if len(timeslot_assignments[current_ts]) >= n_classrooms:
                current_ts += 1
                continue
            
            assigned = False
            
            # ÖNCELİKSİZ: Sıradaki projeyi yerleştirmeye çalış
            for i, project in enumerate(remaining_projects):
                if try_assign_project(project, current_ts):
                    remaining_projects.pop(i)
                    assigned = True
                    break
            
            # Hiçbir proje atanamadıysa (tüm sorumlular çakışıyor) sonraki timeslot
            if not assigned:
                current_ts += 1
        
        # Atamaları birleştir
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
            "ts_order": slot["ts_order"],  # Süreklilik için
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
        # Timeslot bazlı schedule: instructor_id -> set of timeslot_ids
        instructor_busy = defaultdict(set)
        instructor_workload = defaultdict(int)
        instructor_slots = defaultdict(list)  # (ts_order, classroom_id) listesi
        instructor_resp_count = defaultdict(int)  # Responsible sayısı
        
        # Önce sorumluları yerleştir ve RESPONSIBLE COUNT hesapla
        for a in assignments:
            rid = a.get("responsible_id")
            ts_id = a.get("timeslot_id")
            ts_order = a.get("ts_order", 0)
            cid = a.get("classroom_id")
            
            if rid and ts_id:
                instructor_busy[rid].add(ts_id)
                instructor_workload[rid] += 1
                instructor_resp_count[rid] += 1  # Responsible count
                instructor_slots[rid].append({"ts_order": ts_order, "classroom_id": cid})
        
        # Ortalama iş yükü
        total_roles = len(assignments) * 2
        avg_workload = total_roles / len(self.instructor_ids) if self.instructor_ids else 0
        
        # Her öğretmen için HEDEF jüri sayısı hesapla
        # Hedef = Ortalama toplam - mevcut responsible sayısı
        instructor_target_jury = {}
        for iid in self.instructor_ids:
            resp_count = instructor_resp_count.get(iid, 0)
            target_jury = max(0, round(avg_workload) - resp_count)
            instructor_target_jury[iid] = target_jury
        
        # Slot sırasına göre jüri ata
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
        """
        En uygun jüriyi bul - İŞ YÜKÜ DENGESİ ÖNCELİKLİ
        
        Strateji:
        1. Responsible sayısı çok olana AZ jüri ver
        2. En az TOPLAM yüklü öğretmeni seç
        """
        instructor_resp_count = instructor_resp_count or {}
        
        # Müsait adayları bul
        available = []
        for iid in self.instructor_ids:
            if iid == responsible_id:
                continue
            if ts_id in instructor_busy.get(iid, set()):
                continue
            available.append(iid)
        
        if not available:
            return None
        
        # Mevcut workload dağılımını kontrol et
        workloads = list(instructor_workload.values()) if instructor_workload else [0]
        current_min = min(workloads) if workloads else 0
        current_max = max(workloads) if workloads else 0
        current_diff = current_max - current_min
        
        # ================================================================
        # STRATEJİ: RESPONSIBLE-AWARE WORKLOAD BALANCE + SINIF SÜREKLİLİĞİ
        # 1. Responsible sayısı çok olana az jüri ver
        # 2. Aynı sınıfta ardışık slot varsa bonus ver
        # ================================================================
        
        avg_target = round(avg_workload)  # ~8
        
        candidates_with_score = []
        for iid in available:
            current_total = instructor_workload.get(iid, 0)
            resp_count = instructor_resp_count.get(iid, 0)
            
            # Bu kişiye jüri verirsek toplam ne olur
            new_total = current_total + 1
            
            # Ortalamadan sapma
            deviation = abs(new_total - avg_target)
            
            # Responsible sayısı çok olana ağır ceza
            resp_penalty = resp_count * 10
            
            # SINIF SÜREKLİLİĞİ BONUSU (workload balance'ı bozmayacak kadar)
            continuity_bonus = 0
            slots = instructor_slots.get(iid, [])
            if slots:
                for s in slots:
                    if s["classroom_id"] == classroom_id and abs(ts_order - s["ts_order"]) == 1:
                        # Aynı sınıfta ardışık slot = bonus (ama çok büyük değil)
                        continuity_bonus = -15
                        break
            
            # Toplam öncelik skoru (düşük = iyi)
            priority_score = deviation + resp_penalty - (avg_target - new_total) * 5 + continuity_bonus
            
            candidates_with_score.append((iid, priority_score, current_total))
        
        # Önce priority_score'a, sonra current_total'a göre sırala
        candidates_with_score.sort(key=lambda x: (x[1], x[2]))
        
        if not candidates_with_score:
            return None
        
        # En iyi adaylar (en düşük priority_score)
        best_score = candidates_with_score[0][1]
        best_candidates = [c for c in candidates_with_score if c[1] <= best_score + 10]
        
        # Rastgelelik için shuffle
        random.shuffle(best_candidates)
        
        # Tek aday varsa döndür
        if len(best_candidates) == 1:
            return best_candidates[0][0]
        
        # Birden fazla varsa, SINIF SÜREKLİLİĞİ + GAP için skorla
        scored_candidates = []
        
        for iid, _, _ in best_candidates:
            # Sınıf sürekliliği ve GAP skoru hesapla
            score = 0.0
            slots = instructor_slots.get(iid, [])
            
            if slots:
                # Bu slot'a en yakın mevcut slot
                min_gap = min(abs(ts_order - s["ts_order"]) for s in slots)
                
                # AYNI SINIF + ARDIŞIK SLOT = EN İYİ (ÇARPICI BONUS)
                same_class_consecutive = False
                for s in slots:
                    if s["classroom_id"] == classroom_id and abs(ts_order - s["ts_order"]) == 1:
                        score -= 500  # 🎯 ÇARPICI BONUS - Aynı sınıf + ardışık
                        same_class_consecutive = True
                        break
                
                if not same_class_consecutive:
                    if min_gap == 1:
                        # Ardışık ama farklı sınıf = ceza (sınıf değişimi)
                        score += 50
                    elif min_gap == 2:
                        # 1 GAP = orta ceza
                        score += 100
                    else:
                        # Büyük GAP = ağır ceza
                        score += min_gap * 50
            
            # Küçük rastgele noise (sürekliliği bozmayacak kadar)
            score += random.uniform(-3, 3)
            scored_candidates.append((iid, score))
        
        # En iyi adayı seç (en düşük skor)
        scored_candidates.sort(key=lambda x: x[1])
        return scored_candidates[0][0]

    def _calculate_jury_score(self, iid: int, ts_order: int, classroom_id: int,
                               existing_slots: List[Dict], current_workload: int,
                               avg_workload: float, min_workload: int = 0, 
                               max_workload: int = 0) -> float:
        """
        Jüri skoru (düşük = iyi)
        
        ÖNCELİK SIRASI (YENİ):
        1. İŞ YÜKÜ DENGESİ = EN ÖNEMLİ (±2 uniform dağılım)
        2. AYNI SINIF + ARDIŞIK SLOT = İYİ
        3. SINIF DEĞİŞİMİ = KÖTÜ
        """
        score = 0.0
        
        # ================================================================
        # 1. İŞ YÜKÜ DENGESİ - EN ÖNEMLİ!
        # Max-Min fark ≤ 4 olmalı (±2 uniform)
        # ================================================================
        workload_after = current_workload + 1
        
        # Bu atama yapılırsa max-min fark ne olur?
        new_max = max(max_workload, workload_after)
        new_min = min_workload  # min değişmez (artış oldu)
        predicted_diff = new_max - new_min
        
        # ±2 uniform dağılım için max fark 4 olmalı - 3'te uyarı ver
        if predicted_diff > 3:
            # ÇARPICI CEZA - bu atamayı engelle!
            score += (predicted_diff - 3) * 800  # Artırıldı!
        
        # Ortalamadan sapma cezası - daha agresif
        deviation = abs(workload_after - avg_workload)
        if deviation > 2:
            score += (deviation - 2) * 200  # Artırıldı!
        elif deviation > 1:
            score += 50  # Artırıldı!
        
        # Düşük iş yükü bonus, yüksek iş yükü ceza - daha güçlü
        if current_workload < avg_workload - 1:
            score -= 250  # AZ YÜKÜ OLANA ÇARPICI BONUS!
        elif current_workload < avg_workload:
            score -= 100
        elif current_workload > avg_workload + 1:
            score += 300  # ÇOK YÜKÜ OLANA ÇARPICI CEZA!
        elif current_workload > avg_workload:
            score += 100
        
        # ================================================================
        # 2. SINIF SÜREKLİLİĞİ (ikinci öncelik)
        # ================================================================
        if existing_slots:
            # En yakın slotu bul
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
                
                if min_gap == 1:  # Ardışık slot
                    if is_same_classroom:
                        score -= 100  # Aynı sınıf + ardışık
                    else:
                        score += 30   # Farklı sınıf = ceza
                elif min_gap == 2:
                    if is_same_classroom:
                        score -= 40
                    else:
                        score += 20
                else:
                    score += min_gap * 10
            
            # Aynı sınıfta ardışık varsa bonus
            for s in existing_slots:
                if s["classroom_id"] == classroom_id:
                    diff = abs(ts_order - s["ts_order"])
                    if diff == 1:
                        score -= 80
        
        return score

    # ==========================================================================
    # AŞAMA 3: GWO OPTİMİZASYONU
    # ==========================================================================
    def _gwo_optimize(self, assignments: List[Dict]) -> List[Dict]:
        """Grey Wolf Optimizer ile jüri optimizasyonu"""
        if len(assignments) < 2:
            return assignments
        
        pass
        
        current = copy.deepcopy(assignments)
        current = self._fix_hard_constraints(current)
        current_fitness = self._calculate_fitness(current)
        
        # Alpha, Beta, Delta kurtları (en iyi 3 çözüm)
        alpha = copy.deepcopy(current)
        alpha_fitness = current_fitness
        
        beta = copy.deepcopy(current)
        beta_fitness = float('inf')
        
        delta = copy.deepcopy(current)
        delta_fitness = float('inf')
        
        # Omega kurtları (diğer çözümler)
        wolves = []
        for _ in range(self.n_wolves):
            w = self._create_wolf_variation(assignments)
            w = self._fix_hard_constraints(w)
            f = self._calculate_fitness(w)
            
            wolves.append({"pos": w, "fit": f})
            
            # Hiyerarşiyi güncelle
            if f < alpha_fitness:
                delta = copy.deepcopy(beta)
                delta_fitness = beta_fitness
                beta = copy.deepcopy(alpha)
                beta_fitness = alpha_fitness
                alpha = copy.deepcopy(w)
                alpha_fitness = f
            elif f < beta_fitness:
                delta = copy.deepcopy(beta)
                delta_fitness = beta_fitness
                beta = copy.deepcopy(w)
                beta_fitness = f
            elif f < delta_fitness:
                delta = copy.deepcopy(w)
                delta_fitness = f
        
        # İterasyonlar
        for it in range(self.n_iterations):
            # a parametresi azalır (2 -> 0)
            a = self.a_decay - (self.a_decay * it / self.n_iterations)
            
            for wolf in wolves:
                new_pos = self._update_wolf(wolf["pos"], alpha, beta, delta, a)
                new_pos = self._fix_hard_constraints(new_pos)
                new_fit = self._calculate_fitness(new_pos)
                
                wolf["pos"] = new_pos
                wolf["fit"] = new_fit
                
                # Hiyerarşiyi güncelle
                if new_fit < alpha_fitness:
                    delta = copy.deepcopy(beta)
                    delta_fitness = beta_fitness
                    beta = copy.deepcopy(alpha)
                    beta_fitness = alpha_fitness
                    alpha = copy.deepcopy(new_pos)
                    alpha_fitness = new_fit
                elif new_fit < beta_fitness:
                    delta = copy.deepcopy(beta)
                    delta_fitness = beta_fitness
                    beta = copy.deepcopy(new_pos)
                    beta_fitness = new_fit
                elif new_fit < delta_fitness:
                    delta = copy.deepcopy(new_pos)
                    delta_fitness = new_fit
            
            pass
        
        return alpha

    def _create_wolf_variation(self, base: List[Dict]) -> List[Dict]:
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

    def _update_wolf(self, current: List[Dict], alpha: List[Dict],
                     beta: List[Dict], delta: List[Dict], a: float) -> List[Dict]:
        """GWO pozisyon güncelleme - Alpha, Beta, Delta'ya göre"""
        result = copy.deepcopy(current)
        busy = self._build_busy_map(result)
        
        for i, assignment in enumerate(result):
            if i >= len(alpha) or i >= len(beta) or i >= len(delta):
                continue
            
            ts_id = assignment.get("timeslot_id")
            rid = assignment.get("responsible_id")
            current_jury = assignment.get("jury1_id")
            
            new_jury = current_jury
            
            # Alpha, Beta, Delta'dan etkilenme
            r1, r2, r3 = random.random(), random.random(), random.random()
            A1 = 2 * a * r1 - a
            A2 = 2 * a * r2 - a
            A3 = 2 * a * r3 - a
            
            # Alpha etkisi
            if abs(A1) < 1:
                alpha_jury = alpha[i].get("jury1_id")
                if alpha_jury and alpha_jury != rid and ts_id not in busy.get(alpha_jury, set()):
                    new_jury = alpha_jury
            
            # Beta etkisi
            if abs(A2) < 1 and random.random() < 0.5:
                beta_jury = beta[i].get("jury1_id")
                if beta_jury and beta_jury != rid and ts_id not in busy.get(beta_jury, set()):
                    new_jury = beta_jury
            
            # Delta etkisi
            if abs(A3) < 1 and random.random() < 0.3:
                delta_jury = delta[i].get("jury1_id")
                if delta_jury and delta_jury != rid and ts_id not in busy.get(delta_jury, set()):
                    new_jury = delta_jury
            
            # Exploration (rastgele keşif)
            if random.random() < 0.1:
                candidates = [
                    iid for iid in self.instructor_ids
                    if iid != rid and ts_id not in busy.get(iid, set())
                ]
                if candidates:
                    new_jury = random.choice(candidates)
            
            if new_jury != current_jury:
                if current_jury:
                    busy[current_jury].discard(ts_id)
                
                assignment["jury1_id"] = new_jury
                insts = [rid] if rid else []
                if new_jury:
                    insts.append(new_jury)
                    busy[new_jury].add(ts_id)
                assignment["instructors"] = insts
        
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
        # instructor_id -> set of timeslot_ids (busy)
        busy = defaultdict(set)
        
        # Önce sorumluları yerleştir
        for a in assignments:
            rid = a.get("responsible_id")
            ts_id = a.get("timeslot_id")
            if rid and ts_id:
                busy[rid].add(ts_id)
        
        # Jürileri kontrol et/düzelt
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
            
            # JURY2 always placeholder
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
        """
        Son düzeltmeler - Real Simplex uyumlu format
        
        instructors = [
            ps_id (int),
            j1_id (int),
            {
                "id": -1,
                "name": "[Araştırma Görevlisi]",
                "is_placeholder": True
            }
        ]
        """
        for a in assignments:
            a["jury2"] = JURY2_PLACEHOLDER
            
            # instructors array'ini Real Simplex formatında oluştur
            # Sadece ID'ler + placeholder object
            instructor_list = []
            
            # 1. Sorumlu (responsible) - sadece ID
            rid = a.get("responsible_id")
            if rid:
                instructor_list.append(rid)
            
            # 2. Jüri 1 - sadece ID
            j1id = a.get("jury1_id")
            if j1id:
                instructor_list.append(j1id)
            
            # 3. Jüri 2 - PLACEHOLDER object
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
            
            # instructors hem ID listesi hem de object array olabilir
            for inst in a.get("instructors", []):
                # Object ise ID'yi çıkar, değilse direkt kullan
                if isinstance(inst, dict):
                    iid = inst.get("id")
                    # Placeholder'ları atla (-1)
                    if iid == -1:
                        continue
                else:
                    iid = inst
                
                if iid:
                    tasks[iid].append({"ts_order": ts_order, "cid": cid})
                    workload[iid] += 1
        
        # H1: GAP
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
        
        # H2: Workload
        h2 = 0.0
        if workload:
            vals = list(workload.values())
            avg = sum(vals) / len(vals)
            for cnt in vals:
                dev = abs(cnt - avg)
                if dev > self.workload_tolerance:
                    h2 += (dev - self.workload_tolerance) ** 2
        
        # H3: Class change
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
                # Object ise ID'yi çıkar, değilse direkt kullan
                if isinstance(inst, dict):
                    iid = inst.get("id")
                    if iid == -1:  # Placeholder atla
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
            "algorithm": "Grey Wolf Optimizer",
            "status": "failed",
            "error": error
        }

    def evaluate_fitness(self, solution: Any) -> float:
        if isinstance(solution, list):
            return self._calculate_fitness(solution)
        return 0.0

    def repair_solution(self, solution: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """GWO için onarım mekanizması"""
        assignments = solution.get("assignments", [])
        if assignments:
            assignments = self._fix_hard_constraints(assignments)
            solution["assignments"] = assignments
            solution["schedule"] = assignments
            solution["solution"] = assignments
        return solution