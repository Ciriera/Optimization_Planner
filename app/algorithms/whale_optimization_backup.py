"""
Whale Optimization Algorithm (WOA) sinifi - CP-SAT ozellikli versiyon.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy
import math

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class WhaleOptimization(OptimizationAlgorithm):
    """
    Whale Optimization Algorithm (WOA) sinifi.
    Balina optimizasyon algoritmasi kullanarak proje atama problemini cozer.
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
        WOA algoritmasi baslatici - CP-SAT ozellikli versiyon.

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
        self.n_whales = params.get("n_whales", 30)
        self.max_iterations = params.get("max_iterations", 100)

        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        WOA algoritmasini baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

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

        # En iyi balina (alpha)
        self.alpha_whale = None
        self.alpha_fitness = float('-inf')

        # Balinalari baslat
        self.whales = self._initialize_whales()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WOA algoritmasini calistirir - CP-SAT ozellikli versiyon.

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
            # a parametresini guncelle (2'den 0'a dogru azalir)
            a = 2 - iteration * (2 / self.max_iterations)
            
            # Her balina icin
            for i in range(self.n_whales):
                # Rastgele sayilar
                r1 = random.random()
                r2 = random.random()
                
                # A ve C parametreleri
                A = 2 * a * r1 - a
                C = 2 * r2
                
                # p parametresi (0.5'ten kucukse bubble-net feeding, buyukse search for prey)
                p = random.random()
                
                if p < 0.5:
                    if abs(A) >= 1:
                        # Search for prey (exploration)
                        new_solution = self._search_for_prey(self.whales[i]["solution"], A, C)
                    else:
                        # Encircling prey (exploitation)
                        new_solution = self._encircle_prey(self.whales[i]["solution"], A, C)
                else:
                    # Bubble-net feeding (exploitation)
                    new_solution = self._bubble_net_feeding(self.whales[i]["solution"], a)
                
                # Yeni cozumun uygunlugunu degerlendir
                new_fitness = self.evaluate_fitness(new_solution)
                
                # Eger yeni cozum daha iyiyse kabul et
                if new_fitness > self.whales[i]["fitness"]:
                    self.whales[i]["solution"] = new_solution
                    self.whales[i]["fitness"] = new_fitness
                
                # En iyi cozumu guncelle
                if new_fitness > self.alpha_fitness:
                    self.alpha_whale = copy.deepcopy(new_solution)
                    self.alpha_fitness = new_fitness
                    self.best_solution = copy.deepcopy(new_solution)
                    self.best_fitness = new_fitness

            iteration += 1

        # Sonucu dondur
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": iteration,
            "execution_time": time.time() - start_time
        }
    
    def _initialize_whales(self) -> List[Dict[str, Any]]:
        """
        Balinalari baslatir.
        
        Returns:
            List[Dict[str, Any]]: Baslangic balinalari.
        """
        whales = []
        
        for _ in range(self.n_whales):
            # Rastgele bir cozum olustur
            solution = self._create_random_solution()
            
            # Cozumun uygunlugunu degerlendir
            fitness = self.evaluate_fitness(solution)
            
            whale = {
                "solution": solution,
                "fitness": fitness
            }
            
            whales.append(whale)
            
            # En iyi cozumu guncelle
            if fitness > self.alpha_fitness:
                self.alpha_whale = copy.deepcopy(solution)
                self.alpha_fitness = fitness
        
        return whales
    
    def _search_for_prey(self, current_solution: List[Dict[str, Any]], A: float, C: float) -> List[Dict[str, Any]]:
        """
        Av arama (exploration) davranisi.
        
        Args:
            current_solution: Mevcut cozum.
            A: A parametresi.
            C: C parametresi.
            
        Returns:
            List[Dict[str, Any]]: Yeni cozum.
        """
        new_solution = copy.deepcopy(current_solution)
        
        # Rastgele bir balina sec
        random_whale = random.choice(self.whales)
        
        # Yeni pozisyon hesapla
        for i, assignment in enumerate(new_solution):
            if i < len(random_whale["solution"]):
                random_assignment = random_whale["solution"][i]
                
                # Sinif degistir
                if random.random() < 0.5:
                    current_classroom = assignment.get("classroom_id", 1)
                    random_classroom = random_assignment.get("classroom_id", 1)
                    new_classroom = max(1, min(len(self.classrooms), 
                                             int(current_classroom + A * (random_classroom - current_classroom))))
                    assignment["classroom_id"] = new_classroom
                
                # Zaman dilimi degistir
                else:
                    current_timeslot = assignment.get("timeslot_id", 1)
                    random_timeslot = random_assignment.get("timeslot_id", 1)
                    new_timeslot = max(1, min(len(self.timeslots), 
                                            int(current_timeslot + A * (random_timeslot - current_timeslot))))
                    assignment["timeslot_id"] = new_timeslot
        
        return new_solution
    
    def _encircle_prey(self, current_solution: List[Dict[str, Any]], A: float, C: float) -> List[Dict[str, Any]]:
        """
        Avi kusatma (exploitation) davranisi.
        
        Args:
            current_solution: Mevcut cozum.
            A: A parametresi.
            C: C parametresi.
            
        Returns:
            List[Dict[str, Any]]: Yeni cozum.
        """
        new_solution = copy.deepcopy(current_solution)
        
        # En iyi balina (alpha) etrafinda hareket et
        if self.alpha_whale:
            for i, assignment in enumerate(new_solution):
                if i < len(self.alpha_whale):
                    alpha_assignment = self.alpha_whale[i]
                    
                    # Sinif degistir
                    if random.random() < 0.5:
                        current_classroom = assignment.get("classroom_id", 1)
                        alpha_classroom = alpha_assignment.get("classroom_id", 1)
                        new_classroom = max(1, min(len(self.classrooms), 
                                                 int(alpha_classroom - A * abs(C * alpha_classroom - current_classroom))))
                        assignment["classroom_id"] = new_classroom
                    
                    # Zaman dilimi degistir
                    else:
                        current_timeslot = assignment.get("timeslot_id", 1)
                        alpha_timeslot = alpha_assignment.get("timeslot_id", 1)
                        new_timeslot = max(1, min(len(self.timeslots), 
                                                int(alpha_timeslot - A * abs(C * alpha_timeslot - current_timeslot))))
                        assignment["timeslot_id"] = new_timeslot
        
        return new_solution
    
    def _bubble_net_feeding(self, current_solution: List[Dict[str, Any]], a: float) -> List[Dict[str, Any]]:
        """
        Bubble-net feeding (exploitation) davranisi.
        
        Args:
            current_solution: Mevcut cozum.
            a: a parametresi.
            
        Returns:
            List[Dict[str, Any]]: Yeni cozum.
        """
        new_solution = copy.deepcopy(current_solution)
        
        # En iyi balina (alpha) etrafinda spiral hareket
        if self.alpha_whale:
            for i, assignment in enumerate(new_solution):
                if i < len(self.alpha_whale):
                    alpha_assignment = self.alpha_whale[i]
                    
                    # Spiral parametreleri
                    b = 1  # Spiral sekli parametresi
                    l = (2 * random.random() - 1)  # [-1, 1] arasinda rastgele sayi
                    
                    # Sinif degistir
                    if random.random() < 0.5:
                        current_classroom = assignment.get("classroom_id", 1)
                        alpha_classroom = alpha_assignment.get("classroom_id", 1)
                        distance = abs(alpha_classroom - current_classroom)
                        new_classroom = max(1, min(len(self.classrooms), 
                                                 int(distance * math.exp(b * l) * math.cos(2 * math.pi * l) + alpha_classroom)))
                        assignment["classroom_id"] = new_classroom
                    
                    # Zaman dilimi degistir
                    else:
                        current_timeslot = assignment.get("timeslot_id", 1)
                        alpha_timeslot = alpha_assignment.get("timeslot_id", 1)
                        distance = abs(alpha_timeslot - current_timeslot)
                        new_timeslot = max(1, min(len(self.timeslots), 
                                                int(distance * math.exp(b * l) * math.cos(2 * math.pi * l) + alpha_timeslot)))
                        assignment["timeslot_id"] = new_timeslot
        
        return new_solution
    
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
        """
        Cozumun uygunlugunu degerlendirir.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Uygunluk degeri.
        """
        if not solution:
            return 0.0
        
        # Temel metrikleri hesapla
        metrics = self._calculate_metrics(solution)
        
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
        
        return {
            "load_balance": load_balance,
            "time_continuity": time_continuity,
            "classroom_changes": classroom_changes,
            "participant_count": participant_count,
            "instructor_requirements": instructor_requirements
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
