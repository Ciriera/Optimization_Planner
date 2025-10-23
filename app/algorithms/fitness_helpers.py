"""
Ortak fitness metrik hesaplama fonksiyonlari.
Tum algoritmalar icin standart ve normalize edilmis (0-100) metrikler saglar.

Gereksinimler:
- 50 Ara + 31 Bitirme = 81 proje (Coverage = 100%)
- Duplicate = 0
- Gap = 0
- Cakisma = 0
- Cezali slot (16:30+) = 0 veya minimum
- Yuk dengesi: ±1 tolerans
- Sinif sayisi: 5-7
"""
from typing import Dict, Any, List, Tuple, Set, Optional
from collections import defaultdict, Counter
import statistics


class FitnessMetrics:
    """Standart fitness metrik hesaplayici sinif"""
    
    def __init__(self, projects: List[Dict[str, Any]], instructors: List[Dict[str, Any]],
                 classrooms: List[Dict[str, Any]], timeslots: List[Dict[str, Any]]):
        """
        Args:
            projects: Proje listesi (81 proje beklenir: 50 Ara + 31 Bitirme)
            instructors: Ogretim uyesi listesi
            classrooms: Sinif listesi (5-7 arasi kullanilmali)
            timeslots: Zaman dilimi listesi
        """
        self.projects = projects
        self.instructors = instructors
        self.classrooms = classrooms
        self.timeslots = timeslots
        
        # Cache'ler
        self._timeslot_index_map = None
        self._slot_rewards_map = None
        self._expected_project_ids = None
        
    def calculate_total_fitness(self, assignments: List[Dict[str, Any]], 
                               weights: Dict[str, float] = None) -> float:
        """
        Toplam fitness skorunu hesaplar (0-100 normalize edilmis).
        
        Args:
            assignments: Atama listesi
            weights: Metrik agirliklari (varsayilan: dengeli dagilim)
            
        Returns:
            Toplam fitness skoru (0-100)
        """
        if weights is None:
            weights = {
                "slot_reward": 0.25,      # Erken saatler tercih edilmeli
                "coverage": 0.25,         # Tum projeler atanmali (81/81)
                "gap_penalty": 0.20,      # Gap olmamali
                "duplicate_penalty": 0.15, # Duplicate olmamali
                "load_balance": 0.10,     # Yuk dengeli olmali (±1)
                "late_slot_penalty": 0.05 # 16:30+ kullanilmamali
            }
        
        # Her metrigi hesapla (0-100 normalize)
        slot_reward = self.calculate_slot_reward_score(assignments)
        coverage = self.calculate_coverage_score(assignments)
        gap_penalty = self.calculate_gap_penalty_score(assignments)
        duplicate_penalty = self.calculate_duplicate_penalty_score(assignments)
        load_balance = self.calculate_load_balance_score(assignments)
        late_slot_penalty = self.calculate_late_slot_penalty_score(assignments)
        
        # Agirlikli toplam
        fitness = (
            slot_reward * weights["slot_reward"] +
            coverage * weights["coverage"] +
            gap_penalty * weights["gap_penalty"] +
            duplicate_penalty * weights["duplicate_penalty"] +
            load_balance * weights["load_balance"] +
            late_slot_penalty * weights["late_slot_penalty"]
        )
        
        return min(100.0, max(0.0, fitness))
    
    def calculate_slot_reward_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Slot odul skoru (0-100).
        Erken saatler yuksek odul, gec saatler dusuk odul.
        
        09:00-09:30 = 1000 puan → 16:00-16:30 = 400 puan
        16:30+ = -9999 puan (CEZA)
        """
        if not assignments:
            return 0.0
        
        rewards_map = self._get_slot_rewards_map()
        total_reward = 0.0
        
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = self._get_timeslot_by_id(timeslot_id)
            if not timeslot:
                continue
            
            time_key = self._format_timeslot_key(timeslot)
            reward = rewards_map.get(time_key, 0.0)
            total_reward += reward
        
        # Normalize to 0-100
        # Max possible: len(assignments) * 1000
        # Min acceptable: len(assignments) * 400
        max_possible = len(assignments) * 1000
        min_acceptable = len(assignments) * 400
        
        if total_reward < 0:
            return 0.0  # Cezali slot kullanilmis - SISTEM KURALI: 16:30+ slot kullanma!
        
        if max_possible == min_acceptable:
            return 100.0
        
        normalized = ((total_reward - min_acceptable) / (max_possible - min_acceptable)) * 100
        return min(100.0, max(0.0, normalized))
    
    def calculate_coverage_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Kapsam skoru (0-100) - GÜNCELLENDİ.
        81 proje tam olarak atanmali (50 Ara + 31 Bitirme) - ZORUNLU KURAL!

        Returns:
            100 if coverage=100%, 0 if coverage<100% (SİSTEM KURALI: Tüm projeler atanmalı!)
        """
        expected_ids = self._get_expected_project_ids()
        scheduled_ids = {a.get("project_id") for a in assignments if a.get("project_id") is not None}

        expected_count = len(expected_ids)
        scheduled_count = len(scheduled_ids & expected_ids)

        if expected_count == 0:
            return 100.0

        coverage_ratio = scheduled_count / expected_count

        if coverage_ratio == 1.0:
            return 100.0  # Tüm projeler atandı - mükemmel
        else:
            return 0.0   # Eksik proje varsa fitness 0 - KRİTİK KURAL İHLALİ!
    
    def calculate_gap_penalty_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Gap ceza skoru (0-100) - GÜNCELLENDİ.
        Gap = 0 olmali (slotlar arasi bosluk yok) - ZORUNLU KURAL!

        Returns:
            100 if gap=0, 0 if gap>0 (SİSTEM KURALI: Gap kabul edilemez!)
        """
        gap_count = self._count_gaps(assignments)

        if gap_count == 0:
            return 100.0  # Gap-free mükemmel
        else:
            return 0.0   # Gap varsa fitness 0 - KRİTİK KURAL İHLALİ!
    
    def calculate_duplicate_penalty_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Duplicate ceza skoru (0-100) - GÜNCELLENDİ.
        Duplicate = 0 olmali (ayni proje birden fazla yerde yok) - ZORUNLU KURAL!

        Returns:
            100 if duplicate=0, 0 if duplicate>0 (SİSTEM KURALI: Duplicate kabul edilemez!)
        """
        duplicate_count = self._count_duplicates(assignments)

        if duplicate_count == 0:
            return 100.0  # Duplicate-free mükemmel
        else:
            return 0.0   # Duplicate varsa fitness 0 - KRİTİK KURAL İHLALİ!
    
    def calculate_load_balance_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Yuk dengesi skoru (0-100).
        Tum ogretim uyeleri en az 1 gorev almali.
        Yuk dagilimi ±1 tolerans icinde olmali.
        
        Returns:
            100 if perfect balance (±1), decreases with imbalance
        """
        instructor_loads = Counter()
        
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] += 1
        
        if not instructor_loads:
            return 0.0
        
        # Tum instructor'lar listesi
        all_instructor_ids = {i.get("id") for i in self.instructors if i.get("id") is not None}
        
        # Gorev almayan instructor sayisi
        unassigned_count = len(all_instructor_ids - set(instructor_loads.keys()))
        
        if unassigned_count > 0:
            # Her atanmamis instructor -15 puan
            penalty = unassigned_count * 15
            return max(0.0, 100.0 - penalty)
        
        # Yuk dagilimi kontrolu (±1 tolerans)
        loads = list(instructor_loads.values())
        mean_load = statistics.mean(loads)
        max_deviation = max(abs(load - mean_load) for load in loads)
        
        if max_deviation <= 1.0:
            return 100.0
        
        # Her 1 birimlik fazla sapma -10 puan
        penalty = (max_deviation - 1.0) * 10
        return max(0.0, 100.0 - penalty)
    
    def calculate_late_slot_penalty_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Gec slot ceza skoru (0-100).
        16:30 sonrasi slotlar kullanilmamali.
        
        Returns:
            100 if no late slots, 0 if any late slot used
        """
        late_count = self._count_late_slots(assignments)
        
        if late_count == 0:
            return 100.0
        
        # Her gec slot -50 puan (cok agir ceza)
        penalty = late_count * 50
        return max(0.0, 100.0 - penalty)
    
    def calculate_classroom_switch_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Sinif gecis skoru (0-100).
        Ogretim uyelerinin sinif degistirme sayisi minimize edilmeli.
        
        Returns:
            100 if no switches, decreases with switch count
        """
        instructor_classrooms = defaultdict(set)
        
        for assignment in assignments:
            instructor_ids = assignment.get("instructors", [])
            classroom_id = assignment.get("classroom_id")
            
            for instructor_id in instructor_ids:
                if instructor_id and classroom_id:
                    instructor_classrooms[instructor_id].add(classroom_id)
        
        # Her instructor icin gecis sayisi
        total_switches = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        
        if total_switches == 0:
            return 100.0
        
        # Her gecis -5 puan
        penalty = total_switches * 5
        return max(0.0, 100.0 - penalty)
    
    def calculate_session_minimization_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Oturum sayisi minimizasyon skoru (0-100).
        Mumkun olan en az sayida timeslot kullanilmali.
        
        Returns:
            100 if minimal sessions, decreases with session count
        """
        used_timeslots = {a.get("timeslot_id") for a in assignments if a.get("timeslot_id") is not None}
        used_count = len(used_timeslots)
        
        total_timeslots = len(self.timeslots)
        
        if total_timeslots == 0:
            return 100.0
        
        # Utilization ratio (daha az slot kullanimi daha iyi)
        utilization_ratio = used_count / total_timeslots
        
        # 100 - (utilization * 50) → %50 kullanim = 75 puan
        score = 100.0 - (utilization_ratio * 50)
        return min(100.0, max(0.0, score))
    
    def calculate_classroom_count_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Sinif sayisi skoru (0-100).
        Kullanilan sinif sayisi 5-7 arasi olmali.
        
        Returns:
            100 if 5-7 classrooms, decreases otherwise
        """
        used_classrooms = {a.get("classroom_id") for a in assignments if a.get("classroom_id") is not None}
        used_count = len(used_classrooms)
        
        if 5 <= used_count <= 7:
            return 100.0
        
        if used_count < 5:
            # Cok az sinif: her eksik icin -20 puan
            penalty = (5 - used_count) * 20
        else:
            # Cok fazla sinif: her fazla icin -15 puan
            penalty = (used_count - 7) * 15
        
        return max(0.0, 100.0 - penalty)
    
    def calculate_role_compliance_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Rol uygunluk skoru (0-100).
        - Bitirme: 1 sorumlu + 1+ juri
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri olamaz
        
        Returns:
            100 if all rules satisfied, decreases with violations
        """
        violations = 0
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            
            if not project:
                continue
            
            project_type = str(project.get("type", "")).lower()
            responsible_id = project.get("responsible_id")
            instructors = assignment.get("instructors", [])
            
            # Sorumlu ilk sirada mi?
            if responsible_id and instructors:
                if instructors[0] != responsible_id:
                    violations += 1
            
            # Sorumlu hem juri olamaz
            if responsible_id in instructors[1:]:
                violations += 1
            
            # Proje tipine gore kural
            if project_type == "bitirme":
                # 1 sorumlu + en az 1 juri
                if len(instructors) < 2:
                    violations += 1
            elif project_type == "ara":
                # Sadece 1 sorumlu
                if len(instructors) != 1:
                    violations += 1
        
        if violations == 0:
            return 100.0
        
        # Her ihlal -20 puan
        penalty = violations * 20
        return max(0.0, 100.0 - penalty)
    
    # ===== Private Helper Methods =====
    
    def _get_slot_rewards_map(self) -> Dict[str, float]:
        """Slot odul/ceza haritasi"""
        if self._slot_rewards_map is None:
            self._slot_rewards_map = {
                "09:00-09:30": 1000.0,
                "09:30-10:00": 950.0,
                "10:00-10:30": 900.0,
                "10:30-11:00": 850.0,
                "11:00-11:30": 800.0,
                "11:30-12:00": 750.0,
                "13:00-13:30": 700.0,
                "13:30-14:00": 650.0,
                "14:00-14:30": 600.0,
                "14:30-15:00": 550.0,
                "15:00-15:30": 500.0,
                "15:30-16:00": 450.0,
                "16:00-16:30": 400.0,
                "16:30-17:00": -9999.0,
                "17:00-17:30": -9999.0,
                "17:30-18:00": -9999.0,
            }
        return self._slot_rewards_map
    
    def _get_expected_project_ids(self) -> Set[Any]:
        """Beklenen proje ID'leri"""
        if self._expected_project_ids is None:
            self._expected_project_ids = {p.get("id") for p in self.projects if p.get("id") is not None}
        return self._expected_project_ids
    
    def _get_timeslot_by_id(self, timeslot_id: Any) -> Optional[Dict[str, Any]]:
        """ID'ye gore timeslot getir"""
        return next((t for t in self.timeslots if t.get("id") == timeslot_id), None)
    
    def _format_timeslot_key(self, timeslot: Dict[str, Any]) -> str:
        """Timeslot'u HH:MM-HH:MM formatina cevir"""
        time_range = timeslot.get("time_range")
        if time_range:
            return str(time_range).replace(" ", "")
        
        start_time = timeslot.get("start_time", "09:00")
        end_time = timeslot.get("end_time", "09:30")
        return f"{start_time}-{end_time}".replace(" ", "")
    
    def _count_gaps(self, assignments: List[Dict[str, Any]]) -> int:
        """Gap sayisini hesapla"""
        timeslot_index = self._build_timeslot_index()
        
        # Sinif bazli gruplama
        classrooms = defaultdict(list)
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            if classroom_id is None or timeslot_id not in timeslot_index:
                continue
            
            classrooms[classroom_id].append(timeslot_index[timeslot_id])
        
        # Her sinif icin gap sayisi
        total_gaps = 0
        for classroom_id, indices in classrooms.items():
            if not indices:
                continue
            
            indices = sorted(set(indices))
            
            for i in range(len(indices) - 1):
                gap_size = indices[i + 1] - indices[i] - 1
                if gap_size > 0:
                    total_gaps += gap_size
        
        return total_gaps
    
    def _count_duplicates(self, assignments: List[Dict[str, Any]]) -> int:
        """Duplicate sayisini hesapla"""
        project_counts = Counter(a.get("project_id") for a in assignments if a.get("project_id") is not None)
        
        # Her proje icin fazla atama sayisi
        duplicates = sum(max(0, count - 1) for count in project_counts.values())
        return duplicates
    
    def _count_late_slots(self, assignments: List[Dict[str, Any]]) -> int:
        """16:30+ slot sayisini hesapla"""
        late_count = 0
        
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = self._get_timeslot_by_id(timeslot_id)
            
            if not timeslot:
                continue
            
            if self._is_late_slot(timeslot):
                late_count += 1
        
        return late_count
    
    def _is_late_slot(self, timeslot: Dict[str, Any]) -> bool:
        """16:30 sonrasi slot mu?"""
        try:
            time_key = self._format_timeslot_key(timeslot)
            
            # 16:30, 17:00, 17:30, 18:00 kontrolu
            if any(late_time in time_key for late_time in ["16:30", "17:00", "17:30", "18:00"]):
                return True
            
            # Start time parse et
            start_time = str(timeslot.get("start_time", "09:00"))
            parts = start_time.split(":")
            hour = int(parts[0]) if parts and parts[0].isdigit() else 9
            minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            
            return hour > 16 or (hour == 16 and minute >= 30)
        except Exception:
            return False
    
    def _build_timeslot_index(self) -> Dict[Any, int]:
        """Timeslot ID -> index mapping"""
        if self._timeslot_index_map is None:
            self._timeslot_index_map = {}
            for idx, timeslot in enumerate(self.timeslots):
                timeslot_id = timeslot.get("id")
                if timeslot_id is not None:
                    self._timeslot_index_map[timeslot_id] = idx
        
        return self._timeslot_index_map


# ===== Convenience Functions =====

def create_fitness_calculator(projects: List[Dict[str, Any]], instructors: List[Dict[str, Any]],
                              classrooms: List[Dict[str, Any]], timeslots: List[Dict[str, Any]]) -> FitnessMetrics:
    """
    Fitness hesaplayici olustur.
    
    Example:
        >>> calculator = create_fitness_calculator(projects, instructors, classrooms, timeslots)
        >>> fitness = calculator.calculate_total_fitness(assignments)
    """
    return FitnessMetrics(projects, instructors, classrooms, timeslots)


