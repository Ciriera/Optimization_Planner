"""
Bat Algorithm sinifi - CP-SAT ozellikli versiyon.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy
import math

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class BatAlgorithm(OptimizationAlgorithm):
    """
    Bat Algorithm sinifi.
    Yarasa algoritmasi kullanarak proje atama problemini cozer.
    """
    
    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free icin onceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Dict[str, Any] = None):
        """
        Bat Algorithm baslatici - CP-SAT ozellikli versiyon.

            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors

        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.n_bats = params.get("n_bats", 30)
        self.max_iterations = params.get("max_iterations", 100)
        self.f_min = params.get("f_min", 0.0)  # Minimum frekans
        self.f_max = params.get("f_max", 2.0)  # Maksimum frekans
        self.alpha = params.get("alpha", 0.9)  # Loudness decay
        self.gamma = params.get("gamma", 0.9)  # Pulse rate increase
        self.A_max = params.get("A_max", 1.0)  # Maksimum loudness
        self.r_max = params.get("r_max", 1.0)  # Maksimum pulse rate

        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Bat Algorithm'i baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # CP-SAT ozelligi: instructor timeslot kullanim takibi
        self._instructor_timeslot_usage = {}
        for inst in self.instructors:
            self._instructor_timeslot_usage[inst.get("id")] = set()

        # En iyi yarasa
        self.best_bat = None
        self.best_fitness = float('-inf')
        self.best_solution = None

        # Yarasa kolonisini baslat
        self.bats = self._initialize_bats()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bat Algorithm'i calistirir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.

        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        import time
        start_time = time.time()

        # CP-SAT ozelligi: Baslangic cozumu olustur ve degerlendir
        initial_solution = self._create_initial_solution()
        initial_fitness = self.evaluate_fitness({"solution": initial_solution})

        # En iyi cozumu guncelle (CP-SAT ozelligi)
        self.best_solution = initial_solution
        self.best_fitness = initial_fitness

        # CP-SAT ozelligi: Yerel arama ile cozumu iyilestir (zaman limiti icinde)
        iteration = 0
        while time.time() - start_time < self.time_limit and iteration < self.max_iterations:
            # Her yarasa icin
            for i in range(self.n_bats):
                # Frekans guncelle
                self.bats[i]["frequency"] = self.f_min + (self.f_max - self.f_min) * random.random()
                
                # Hiz guncelle
                if self.best_bat and self.best_bat["position"]:
                    for j in range(len(self.bats[i]["velocity"])):
                        if j < len(self.best_bat["position"]):
                            self.bats[i]["velocity"][j] += (self.bats[i]["position"][j] - self.best_bat["position"][j]) * self.bats[i]["frequency"]
                
                # Pozisyon guncelle
                for j in range(len(self.bats[i]["position"])):
                    self.bats[i]["position"][j] += self.bats[i]["velocity"][j]
                
                # Rastgele ucus (local search)
                if random.random() > self.bats[i]["pulse_rate"]:
                    # Local search yap
                    self._local_search(i)
                
                # Yeni cozum olustur
                new_solution = self._position_to_solution(self.bats[i]["position"])
                new_fitness = self.evaluate_fitness(new_solution)
                
                # Eger yeni cozum daha iyiyse ve loudness yeterliyse kabul et
                if new_fitness > self.bats[i]["fitness"] and random.random() < self.bats[i]["loudness"]:
                    self.bats[i]["position"] = self._solution_to_position(new_solution)
                    self.bats[i]["fitness"] = new_fitness
                    self.bats[i]["loudness"] *= self.alpha
                    self.bats[i]["pulse_rate"] = self.r_max * (1 - math.exp(-self.gamma * iteration))
                
                # En iyi cozumu guncelle
                if new_fitness > self.best_fitness:
                    self.best_bat = copy.deepcopy(self.bats[i])
                    self.best_fitness = new_fitness
                    self.best_solution = copy.deepcopy(new_solution)

            iteration += 1

        # Sonucu dondur (duplicate guvenli)
        final_schedule = self._deduplicate_assignments(self.best_solution) if isinstance(self.best_solution, list) else self.best_solution
        return {
            "schedule": final_schedule,
            "fitness": self.best_fitness,
            "iterations": iteration,
            "execution_time": time.time() - start_time
        }
    
    def _initialize_bats(self) -> List[Dict[str, Any]]:
        """
        Yarasa kolonisini baslatir.
        
        Returns:
            List[Dict[str, Any]]: Baslangic yarasa kolonisi.
        """
        bats = []
        
        for _ in range(self.n_bats):
            # Rastgele bir cozum olustur
            solution = self._create_random_solution()
            
            # Cozumun uygunlugunu degerlendir
            fitness = self.evaluate_fitness(solution)
            
            # Pozisyon ve hiz vektorleri olustur
            position = self._solution_to_position(solution)
            velocity = [0.0] * len(position)
            
            bat = {
                "solution": solution,
                "fitness": fitness,
                "position": position,
                "velocity": velocity,
                "frequency": self.f_min + (self.f_max - self.f_min) * random.random(),
                "loudness": self.A_max,
                "pulse_rate": self.r_max
            }
            
            # En iyi yarasayi guncelle
            if fitness > self.best_fitness:
                self.best_bat = copy.deepcopy(bat)
                self.best_fitness = fitness
                self.best_solution = copy.deepcopy(solution)
            
            bats.append(bat)
        
        return bats
    
    def _solution_to_position(self, solution: List[Dict[str, Any]]) -> List[float]:
        """
        Cozumu pozisyon vektorune donusturur.
        
        Args:
            solution: Cozum.
            
        Returns:
            List[float]: Pozisyon vektoru.
        """
        position = []
        
        for assignment in solution:
            # Sinif ID'sini normalize et
            classroom_norm = (assignment.get("classroom_id", 1) - 1) / max(1, len(self.classrooms) - 1)
            position.append(classroom_norm)
            
            # Zaman dilimi ID'sini normalize et
            timeslot_norm = (assignment.get("timeslot_id", 1) - 1) / max(1, len(self.timeslots) - 1)
            position.append(timeslot_norm)
            
            # Instructor ID'lerini normalize et
            for instructor_id in assignment.get("instructors", []):
                instructor_norm = (instructor_id - 1) / max(1, len(self.instructors) - 1)
                position.append(instructor_norm)
        
        return position
    
    def _position_to_solution(self, position: List[float]) -> List[Dict[str, Any]]:
        """
        Pozisyon vektorunu cozume donusturur.
        
        Args:
            position: Pozisyon vektoru.
            
        Returns:
            List[Dict[str, Any]]: Cozum.
        """
        solution = []
        pos_idx = 0
        
        for project in self.projects:
            # Sinif ID'sini denormalize et
            classroom_norm = max(0, min(1, position[pos_idx]))
            classroom_id = int(classroom_norm * (len(self.classrooms) - 1)) + 1
            pos_idx += 1
            
            # Zaman dilimi ID'sini denormalize et
            timeslot_norm = max(0, min(1, position[pos_idx]))
            timeslot_id = int(timeslot_norm * (len(self.timeslots) - 1)) + 1
            pos_idx += 1
            
            # Instructor ID'lerini denormalize et
            instructor_ids = []
            for _ in range(3):  # 3 instructor
                if pos_idx < len(position):
                    instructor_norm = max(0, min(1, position[pos_idx]))
                    instructor_id = int(instructor_norm * (len(self.instructors) - 1)) + 1
                    instructor_ids.append(instructor_id)
                    pos_idx += 1
                else:
                    instructor_ids.append(random.randint(1, len(self.instructors)))
            
            assignment = {
                "project_id": project["id"],
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": instructor_ids
            }
            
            solution.append(assignment)
        
        return solution
    
    def _local_search(self, bat_index: int):
        """
        Local search yapar.
        
        Args:
            bat_index: Yarasa indeksi.
        """
        # Mevcut pozisyonu al
        current_position = self.bats[bat_index]["position"]
        
        # Rastgele bir pozisyon degistir
        if current_position:
            change_index = random.randint(0, len(current_position) - 1)
            # Kucuk bir degisiklik yap
            change = (random.random() - 0.5) * 0.1
            current_position[change_index] = max(-1, min(1, current_position[change_index] + change))
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """
        Rastgele bir cozum olusturur.
        
        Returns:
            List[Dict[str, Any]]: Rastgele cozum.
        """
        solution = []
        
        for project in self.projects:
            # Rastgele sinif ve zaman dilimi sec
            classroom_id = random.randint(1, len(self.classrooms))
            timeslot_id = random.randint(1, len(self.timeslots))
            
            # Rastgele instructor'lar sec
            if len(self.instructors) >= 3:
                instructors = random.sample(self.instructors, 3)
                instructor_ids = [inst["id"] for inst in instructors]
            else:
                instructor_ids = [inst["id"] for inst in self.instructors]
                # Eksik instructor'lari tekrarla
                while len(instructor_ids) < 3:
                    instructor_ids.append(random.choice(self.instructors)["id"])
            
            assignment = {
                "project_id": project["id"],
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": instructor_ids

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
            
            solution.append(assignment)
        
        return solution
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Cozumun uygunlugunu degerlendirir.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Uygunluk degeri.
        """
        if not solution:
            return 0.0
        # Esnek giris: dict veya liste
        assignments: List[Dict[str, Any]] = []
        if isinstance(solution, dict):
            assignments = solution.get("solution") or solution.get("schedule") or []
        elif isinstance(solution, list):
            assignments = solution
        if not assignments:
            return 0.0

        score = 0.0

        # Kural uygunlugu
        rule_compliance = self._calculate_rule_compliance(assignments)
        score += rule_compliance * 100.0

        # Sinif degisim sayisini minimize et
        instructor_changes = self._count_instructor_classroom_changes(assignments)
        score -= instructor_changes * 10.0

        # Yuk dengesini maksimize et
        load_balance = self._calculate_load_balance(assignments)
        score += load_balance * 50.0

        # Zaman slot cezasi - 16:30 sonrasi cok agir, 16:00–16:30 orta seviye
        time_penalty = self._calculate_time_slot_penalty(assignments)
        score -= time_penalty

        return score

    def _calculate_time_slot_penalty(self, solution: List[Dict[str, Any]]) -> float:
        """Standart ceza politikasini uygular (pozitif deger dondurur)."""
        return super()._calculate_time_slot_penalty(solution)

    def _calculate_metrics(self, solution: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Cozum icin metrikleri hesaplar.
        
        Args:
            solution: Cozum.
            
        Returns:
            Dict[str, float]: Hesaplanan metrikler.
        """
        if not solution:
            return {}
        
        # Yuk dengesi
        instructor_loads = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        load_balance = self._calculate_load_balance(instructor_loads)
        
        # Zaman surekliligi
        time_continuity = self._calculate_time_continuity(solution)
        
        # Sinif degisimleri
        classroom_changes = self._calculate_classroom_changes(solution)
        
        # Katilimci sayisi
        participant_count = self._calculate_participant_count(solution)
        
        # Instructor gereksinimleri
        instructor_requirements = self._calculate_instructor_requirements(solution)

        # Zaman slot cezasi
        time_slot_penalty = self._calculate_time_slot_penalty(solution)

        return {
            "load_balance": load_balance,
            "time_continuity": time_continuity,
            "classroom_changes": classroom_changes,
            "participant_count": participant_count,
            "instructor_requirements": instructor_requirements,
            "time_slot_penalty": time_slot_penalty
        }
    
    def _calculate_load_balance(self, instructor_loads: Dict[int, int]) -> float:
        """Yuk dengesini hesaplar."""
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        if len(loads) <= 1:
            return 100.0
        
        # Gini katsayisi hesapla
        array = np.array(loads, dtype=np.float64)
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1, dtype=np.float64)
        n = float(array.shape[0])
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
        
        return (1.0 - gini) * 100
    
    def _calculate_time_continuity(self, solution: List[Dict[str, Any]]) -> float:
        """Zaman surekliligini hesaplar."""
        if not solution:
            return 0.0
        
        instructor_schedules = {}
        for assignment in solution:
            instructor_id = assignment.get("instructors", [{}])[0] if assignment.get("instructors") else None
            if instructor_id:
                if instructor_id not in instructor_schedules:
                    instructor_schedules[instructor_id] = []
                instructor_schedules[instructor_id].append(assignment.get("timeslot_id"))
        
        continuity_score = 0.0
        for instructor_id, timeslots in instructor_schedules.items():
            if len(timeslots) > 1:
                sorted_timeslots = sorted(timeslots)
                gaps = 0
                for i in range(1, len(sorted_timeslots)):
                    if sorted_timeslots[i] - sorted_timeslots[i-1] > 1:
                        gaps += 1
                continuity_score += max(0, 100 - gaps * 20)
            else:
                continuity_score += 100
        
        return continuity_score / len(instructor_schedules) if instructor_schedules else 0.0
    
    def _calculate_classroom_changes(self, solution: List[Dict[str, Any]]) -> float:
        """Sinif degisimlerini hesaplar."""
        if not solution:
            return 0.0
        
        instructor_classrooms = {}
        for assignment in solution:
            instructor_id = assignment.get("instructors", [{}])[0] if assignment.get("instructors") else None
            if instructor_id:
                if instructor_id not in instructor_classrooms:
                    instructor_classrooms[instructor_id] = set()
                instructor_classrooms[instructor_id].add(assignment.get("classroom_id"))
        
        total_changes = 0
        for instructor_id, classrooms in instructor_classrooms.items():
            total_changes += len(classrooms) - 1
        
        max_possible_changes = len(instructor_classrooms) * (len(self.classrooms) - 1)
        if max_possible_changes == 0:
            return 100.0
        
        return max(0, 100 - (total_changes / max_possible_changes) * 100)
    
    def _calculate_participant_count(self, solution: List[Dict[str, Any]]) -> float:
        """Katilimci sayisini hesaplar."""
        if not solution:
            return 0.0
        
        correct_count = 0
        for assignment in solution:
            instructors = assignment.get("instructors", [])
            if len(instructors) == 3:
                correct_count += 1
        
        return (correct_count / len(solution)) * 100 if solution else 0.0
    
    def _calculate_instructor_requirements(self, solution: List[Dict[str, Any]]) -> float:
        """Instructor gereksinimlerini hesaplar."""
        if not solution:
            return 0.0
        
        correct_count = 0
        for assignment in solution:
            instructors = assignment.get("instructors", [])
            if len(instructors) >= 1:  # En az 1 instructor
                correct_count += 1
        
        return (correct_count / len(solution)) * 100 if solution else 0.0
