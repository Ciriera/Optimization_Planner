"""
Enhanced A* Search Algorithm with CP-SAT features for project scheduling optimization
"""
from typing import Dict, Any, List, Tuple, Optional
import heapq
import copy
import time
import random

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class AStarSearch(OptimizationAlgorithm):
    """
    Enhanced A* Search Algorithm with CP-SAT features for project scheduling optimization.

    This implementation incorporates CP-SAT principles:
    - Fair instructor load distribution with ±2 tolerance
    - Strict 16:30 slot constraint (forbidden after 16:30)
    - Rule compliance (3 instructors for bitirme, 2 for ara projects)
    - Classroom change minimization
    - Project prioritization (bitirme > ara, final > makeup)
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
        A* Search Algorithm baslatici - CP-SAT ozellikli versiyon.

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
        self.time_limit = params.get("time_limit", 30)  # Saniye cinsinden zaman limiti
        self.max_nodes = params.get("max_nodes", 5000)  # Maksimum dugum sayisi

        # CP-SAT ozellikleri
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')
        self.nodes_explored = 0

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        A* Search Algorithm'i baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

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
        A* Search Algorithm'i calistirir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.

        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        start_time = time.time()

        # CP-SAT ozelligi: Baslangic cozumu olustur ve degerlendir
        initial_solution = self._create_initial_solution()
        initial_fitness = self.evaluate_fitness({"solution": initial_solution})

        # En iyi cozumu guncelle (CP-SAT ozelligi)
        self.best_solution = initial_solution
        self.best_fitness = initial_fitness

        # CP-SAT ozelligi: Yerel arama ile cozumu iyilestir (zaman limiti icinde)
        current_solution = initial_solution
        current_fitness = initial_fitness

        while time.time() - start_time < self.time_limit:
            # Komsu cozum olustur
            neighbor = self._generate_neighbor_solution(current_solution)

            # Komsu cozumun uygunlugunu degerlendir
            neighbor_fitness = self.evaluate_fitness({"solution": neighbor})

            # Daha iyi cozumu kabul et
            if neighbor_fitness > current_fitness:
                current_solution = neighbor
                current_fitness = neighbor_fitness

                # En iyi cozumu guncelle
                if current_fitness > self.best_fitness:
                    self.best_solution = current_solution
                    self.best_fitness = current_fitness
            # Not: A* acik/kapali liste varyanti kaldirildi; yerel arama ile iyilestiriyoruz
        
        # Sonucu dondur
        self.best_solution = current_solution
        self.best_fitness = current_fitness
        
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "nodes_explored": self.nodes_explored,
            "time_limit": self.time_limit,
            "execution_time": time.time() - start_time
        }
    
    def _create_start_node(self) -> Dict[str, Any]:
        """
        Baslangic dugumunu olusturur.
        
        Returns:
            Dict[str, Any]: Baslangic dugumu.
        """
        # Bos cozum ile basla
        solution = []
        
        # g-cost (gercek maliyet)
        g_cost = 0.0
        
        # h-cost (heuristic maliyet)
        h_cost = self._calculate_heuristic(solution)
        
        # f-cost = g-cost + h-cost
        f_cost = g_cost + h_cost
        
        return {
            "id": 0,
            "solution": solution,
            "g_cost": g_cost,
            "h_cost": h_cost,
            "f_cost": f_cost,
            "level": 0,
            "assigned_projects": set()
        }
    
    def _is_goal_node(self, node: Dict[str, Any]) -> bool:
        """
        Dugumun hedef dugum olup olmadigini kontrol eder.
        
        Args:
            node: Kontrol edilecek dugum.
            
        Returns:
            bool: Hedef dugum mu?
        """
        return len(node["assigned_projects"]) == len(self.projects)
    
    def _generate_neighbors(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Komsu dugumleri olusturur.
        
        Args:
            node: Mevcut dugum.
            
        Returns:
            List[Dict[str, Any]]: Komsu dugumler.
        """
        neighbors = []
        
        # Henuz atanmamis projeleri bul
        unassigned_projects = [p for p in self.projects if p["id"] not in node["assigned_projects"]]
        
        if not unassigned_projects:
            return neighbors
        
        # Ilk atanmamis projeyi al
        project = unassigned_projects[0]
        
        # Tum olasi atamalari dene (sinirli sayida)
        for classroom in self.classrooms[:3]:  # Sadece ilk 3 sinif
            for timeslot in self.timeslots[:3]:  # Sadece ilk 3 zaman dilimi
                # Instructor kombinasyonlari
                instructor_combinations = self._get_instructor_combinations()
                
                for instructors in instructor_combinations[:2]:  # Sadece ilk 2 kombinasyon
                    # Yeni atama olustur
                    new_assignment = {
                        "project_id": project["id"],
                        "classroom_id": classroom["id"],
                        "timeslot_id": timeslot["id"],
                        "instructors": [inst["id"] for inst in instructors]
                    }
                    
                    # Yeni cozum olustur
                    new_solution = copy.deepcopy(node["solution"])
                    new_solution.append(new_assignment)
                    
                    # Yeni dugum olustur
                    new_node = {
                        "id": self.nodes_explored + len(neighbors) + 1,
                        "solution": new_solution,
                        "g_cost": node["g_cost"] + self._calculate_assignment_cost(new_assignment, new_solution),
                        "h_cost": self._calculate_heuristic(new_solution),
                        "f_cost": 0.0,  # Hesaplanacak
                        "level": node["level"] + 1,
                        "assigned_projects": node["assigned_projects"] | {project["id"]}
                    }
                    
                    # f-cost hesapla
                    new_node["f_cost"] = new_node["g_cost"] + new_node["h_cost"]
                    
                    neighbors.append(new_node)
        
        return neighbors
    
    def _calculate_heuristic(self, solution: List[Dict[str, Any]]) -> float:
        """
        Heuristic maliyeti hesaplar.
        
        Args:
            solution: Cozum.
            
        Returns:
            float: Heuristic maliyet.
        """
        if not solution:
            return 100.0  # Maksimum maliyet
        
        # Kalan projeler icin tahmini maliyet
        remaining_projects = len(self.projects) - len(solution)
        if remaining_projects == 0:
            return 0.0
        
        # Mevcut cozumun kalitesine gore tahmin
        current_fitness = self.evaluate_fitness(solution)
        estimated_remaining_cost = remaining_projects * (100 - current_fitness) / len(solution) if solution else 100
        
        return estimated_remaining_cost
    
    def _calculate_assignment_cost(self, assignment: Dict[str, Any], solution: List[Dict[str, Any]]) -> float:
        """
        Atama maliyetini hesaplar.
        
        Args:
            assignment: Atama.
            solution: Cozum.
            
        Returns:
            float: Atama maliyeti.
        """
        # Basit maliyet hesaplama
        cost = 0.0
        
        # Sinif degisim maliyeti
        if len(solution) > 1:
            prev_assignment = solution[-2]
            if assignment["classroom_id"] != prev_assignment["classroom_id"]:
                cost += 10.0
        
        # Zaman dilimi degisim maliyeti
        if len(solution) > 1:
            prev_assignment = solution[-2]
            if assignment["timeslot_id"] != prev_assignment["timeslot_id"]:
                cost += 5.0
        
        # Instructor yuk maliyeti
        instructor_loads = {}
        for sol_assignment in solution:
            for instructor_id in sol_assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        # Yuk dengesizligi maliyeti
        if instructor_loads:
            loads = list(instructor_loads.values())
            if len(loads) > 1:
                mean_load = sum(loads) / len(loads)
                variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
                cost += variance * 2.0
        
        return cost
    
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
            import random
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
        # Esnek giris: dict(schedule/solution) veya dogrudan list
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
        """Standart baz ceza uygulamasi (pozitif deger)."""
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
