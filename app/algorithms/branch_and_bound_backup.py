"""
Branch and Bound algoritmasi sinifi - CP-SAT ozellikli versiyon.
"""
from typing import Dict, Any, List, Tuple, Optional
import copy
import time
import random

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class BranchAndBound(OptimizationAlgorithm):
    """
    Branch and Bound algoritmasi sinifi.
    Dal ve sinir algoritmasi kullanarak proje atama problemini cozer.
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
        Branch and Bound algoritmasi baslatici - CP-SAT ozellikli versiyon.

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

        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.time_limit = params.get("time_limit", 10)  # Saniye cinsinden zaman limiti (kisa tutuyoruz)
        self.max_nodes = params.get("max_nodes", 1000)  # Maksimum dugum sayisi

        # CP-SAT ozellikleri
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')
        self.nodes_explored = 0

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Branch and Bound algoritmasini baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

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

        # Dugum sayaci
        self.nodes_explored = 0
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Branch and Bound algoritmasini calistirir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.

        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        start_time = time.time()

        # CP-SAT ozelligi: Baslangic cozumu olustur ve degerlendir
        solution = self._create_initial_solution()
        fitness = self.evaluate_fitness({"solution": solution})

        # En iyi cozumu guncelle (CP-SAT ozelligi)
        self.best_solution = solution
        self.best_fitness = fitness

        # Sonucu dondur
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "nodes_explored": self.nodes_explored,
            "time_limit": self.time_limit,
            "execution_time": time.time() - start_time
        }
    
    def _create_greedy_solution(self) -> List[Dict[str, Any]]:
        """
        Greedy cozum olusturur.
        
        Returns:
            List[Dict[str, Any]]: Greedy cozum.
        """
        solution = []
        
        for project in self.projects:
            # En iyi atamayi bul
            best_assignment = self._find_best_assignment(project, solution)
            if best_assignment:
                solution.append(best_assignment)
        
        return solution
    
    def _find_best_assignment(self, project: Dict[str, Any], current_solution: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Proje icin en iyi atamayi bulur.
        
        Args:
            project: Atanacak proje.
            current_solution: Mevcut cozum.
            
        Returns:
            Optional[Dict[str, Any]]: En iyi atama.
        """
        best_assignment = None
        best_score = float('-inf')
        
        # Tum olasi atamalari dene (sinirli sayida)
        for classroom in self.classrooms[:3]:  # Sadece ilk 3 sinif
            for timeslot in self.timeslots[:3]:  # Sadece ilk 3 zaman dilimi
                # Instructor kombinasyonlari
                instructor_combinations = self._get_instructor_combinations()
                
                for instructors in instructor_combinations[:2]:  # Sadece ilk 2 kombinasyon
                    # Atama olustur
                    assignment = {
                        "project_id": project["id"],
                        "classroom_id": classroom["id"],
                        "timeslot_id": timeslot["id"],
                        "instructors": [inst["id"] for inst in instructors]
                    }
                    
                    # Atamanin skorunu hesapla
                    score = self._evaluate_assignment(assignment, current_solution)
                    
                    if score > best_score:
                        best_score = score
                        best_assignment = assignment
        
        return best_assignment
    
    def _get_instructor_combinations(self) -> List[List[Dict[str, Any]]]:
        """
        Instructor kombinasyonlarini olusturur.
        
        Returns:
            List[List[Dict[str, Any]]]: Instructor kombinasyonlari.
        """
        combinations = []
        
        # 3 instructor kombinasyonlari
        if len(self.instructors) >= 3:
            # Rastgele birkac kombinasyon sec
            for _ in range(min(3, len(self.instructors))):  # Maksimum 3 kombinasyon
                combination = random.sample(self.instructors, 3)
                combinations.append(combination)
        else:
            # Eksik instructor'lari tekrarla
            combination = list(self.instructors)
            while len(combination) < 3:
                combination.append(random.choice(self.instructors))
            combinations.append(combination)
        
        return combinations
    
    def _evaluate_assignment(self, assignment: Dict[str, Any], current_solution: List[Dict[str, Any]]) -> float:
        """
        Atamanin skorunu degerlendirir.
        
        Args:
            assignment: Degerlendirilecek atama.
            current_solution: Mevcut cozum.
            
        Returns:
            float: Atama skoru.
        """
        # Gecici cozum olustur
        temp_solution = current_solution + [assignment]
        
        # Skor hesapla
        return self.evaluate_fitness(temp_solution)
    
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
            }
            
            solution.append(assignment)
        
        return solution
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """CP-SAT ozelligi: Verilen cozumun uygunlugunu degerlendirir."""
        if not solution:
            return float('-inf')

        assignments = solution.get("solution", solution.get("schedule", []))
        if not assignments:
            return float('-inf')

        # Cozum gecerli mi?
        if not self._is_valid_solution(assignments):
            return float('-inf')

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
        """Standart baz ceza (pozitif) uygular ve fitness tarafindan dusulur."""
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
        
        # Basit standart sapma hesaplama
        mean_load = sum(loads) / len(loads)
        variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
        std_dev = variance ** 0.5
        
        # Standart sapma ne kadar dusukse o kadar iyi
        return max(0, 100 - std_dev * 10)
    
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
