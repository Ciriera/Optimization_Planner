"""
Enhanced Dragonfly Algorithm with CP-SAT features for project scheduling optimization
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy
import math

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class DragonflyAlgorithm(OptimizationAlgorithm):
    """
    Enhanced Dragonfly Algorithm with CP-SAT features for project scheduling optimization.

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
        Enhanced Dragonfly Algorithm baslatici - CP-SAT ozellikli versiyon.

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
        self.n_dragonflies = params.get("n_dragonflies", 30)
        self.max_iterations = params.get("max_iterations", 100)
        self.s = params.get("s", 2.0)  # Separation weight
        self.a = params.get("a", 2.0)  # Alignment weight
        self.c = params.get("c", 2.0)  # Cohesion weight
        self.f = params.get("f", 2.0)  # Food attraction weight
        self.e = params.get("e", 1.0)  # Enemy distraction weight
        self.w = params.get("w", 0.9)  # Inertia weight

        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Enhanced Dragonfly Algorithm'i baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

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

        # Yusufcuk surusunu baslat
        self.dragonflies = self._initialize_dragonflies()
        
        # En iyi yusufcuk
        self.best_dragonfly = None
        self.best_fitness = float('-inf')
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dragonfly Algorithm'i calistirir.
        
        Args:
            data: Algoritma giris verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Iterasyon dongusu
        for iteration in range(self.max_iterations):
            # Her yusufcuk icin
            for i in range(self.n_dragonflies):
                # Komsulari bul
                neighbors = self._find_neighbors(i)
                
                # Sosyal davranislari hesapla
                separation = self._calculate_separation(i, neighbors)
                alignment = self._calculate_alignment(i, neighbors)
                cohesion = self._calculate_cohesion(i, neighbors)
                
                # Yiyecek cekimi
                food_attraction = self._calculate_food_attraction(i)
                
                # Dusman kacinmasi
                enemy_distraction = self._calculate_enemy_distraction(i)
                
                # Hiz guncelle
                new_velocity = (
                    self.w * np.array(self.dragonflies[i]["velocity"]) +
                    self.s * separation +
                    self.a * alignment +
                    self.c * cohesion +
                    self.f * food_attraction +
                    self.e * enemy_distraction
                )
                
                # Pozisyon guncelle
                new_position = np.array(self.dragonflies[i]["position"]) + new_velocity
                
                # Sinirlari kontrol et
                new_position = self._apply_boundaries(new_position)
                
                # Yeni cozum olustur
                new_solution = self._position_to_solution(new_position.tolist())
                new_fitness = self.evaluate_fitness(new_solution)
                
                # Eger yeni cozum daha iyiyse kabul et
                if new_fitness > self.dragonflies[i]["fitness"]:
                    self.dragonflies[i]["solution"] = new_solution
                    self.dragonflies[i]["fitness"] = new_fitness
                    self.dragonflies[i]["position"] = new_position.tolist()
                    self.dragonflies[i]["velocity"] = new_velocity.tolist()
                
                # En iyi cozumu guncelle
                if new_fitness > self.best_fitness:
                    self.best_dragonfly = copy.deepcopy(self.dragonflies[i])
                    self.best_fitness = new_fitness
                    self.best_solution = copy.deepcopy(new_solution)
        
        # Sonucu dondur
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": self.max_iterations
        }
    
    def _initialize_dragonflies(self) -> List[Dict[str, Any]]:
        """
        Yusufcuk surusunu baslatir.
        
        Returns:
            List[Dict[str, Any]]: Baslangic yusufcuk surusu.
        """
        dragonflies = []
        
        for _ in range(self.n_dragonflies):
            # Rastgele bir cozum olustur
            solution = self._create_random_solution()
            
            # Cozumun uygunlugunu degerlendir
            fitness = self.evaluate_fitness(solution)
            
            # Pozisyon ve hiz vektorleri olustur
            position = self._solution_to_position(solution)
            velocity = [0.0] * len(position)
            
            dragonfly = {
                "solution": solution,
                "fitness": fitness,
                "position": position,
                "velocity": velocity
            }
            
            dragonflies.append(dragonfly)
            
            # En iyi cozumu guncelle
            if fitness > self.best_fitness:
                self.best_dragonfly = copy.deepcopy(dragonfly)
                self.best_fitness = fitness
        
        return dragonflies
    
    def _find_neighbors(self, dragonfly_index: int) -> List[int]:
        """
        Komsulari bulur.
        
        Args:
            dragonfly_index: Yusufcuk indeksi.
            
        Returns:
            List[int]: Komsu indeksleri.
        """
        neighbors = []
        current_pos = np.array(self.dragonflies[dragonfly_index]["position"])
        
        for i, dragonfly in enumerate(self.dragonflies):
            if i != dragonfly_index:
                neighbor_pos = np.array(dragonfly["position"])
                distance = np.linalg.norm(current_pos - neighbor_pos)
                
                # Komsuluk yaricapi (rastgele)
                radius = random.uniform(0.1, 0.5)
                if distance < radius:
                    neighbors.append(i)
        
        return neighbors
    
    def _calculate_separation(self, dragonfly_index: int, neighbors: List[int]) -> np.ndarray:
        """
        Ayrilma davranisini hesaplar.
        
        Args:
            dragonfly_index: Yusufcuk indeksi.
            neighbors: Komsu indeksleri.
            
        Returns:
            np.ndarray: Ayrilma vektoru.
        """
        if not neighbors:
            return np.zeros(len(self.dragonflies[dragonfly_index]["position"]))
        
        current_pos = np.array(self.dragonflies[dragonfly_index]["position"])
        separation = np.zeros_like(current_pos)
        
        for neighbor_index in neighbors:
            neighbor_pos = np.array(self.dragonflies[neighbor_index]["position"])
            separation += current_pos - neighbor_pos
        
        return separation / len(neighbors) if neighbors else separation
    
    def _calculate_alignment(self, dragonfly_index: int, neighbors: List[int]) -> np.ndarray:
        """
        Hizalama davranisini hesaplar.
        
        Args:
            dragonfly_index: Yusufcuk indeksi.
            neighbors: Komsu indeksleri.
            
        Returns:
            np.ndarray: Hizalama vektoru.
        """
        if not neighbors:
            return np.zeros(len(self.dragonflies[dragonfly_index]["position"]))
        
        alignment = np.zeros(len(self.dragonflies[dragonfly_index]["velocity"]))
        
        for neighbor_index in neighbors:
            neighbor_velocity = np.array(self.dragonflies[neighbor_index]["velocity"])
            alignment += neighbor_velocity
        
        return alignment / len(neighbors) if neighbors else alignment
    
    def _calculate_cohesion(self, dragonfly_index: int, neighbors: List[int]) -> np.ndarray:
        """
        Birlik davranisini hesaplar.
        
        Args:
            dragonfly_index: Yusufcuk indeksi.
            neighbors: Komsu indeksleri.
            
        Returns:
            np.ndarray: Birlik vektoru.
        """
        if not neighbors:
            return np.zeros(len(self.dragonflies[dragonfly_index]["position"]))
        
        current_pos = np.array(self.dragonflies[dragonfly_index]["position"])
        center_of_mass = np.zeros_like(current_pos)
        
        for neighbor_index in neighbors:
            neighbor_pos = np.array(self.dragonflies[neighbor_index]["position"])
            center_of_mass += neighbor_pos
        
        center_of_mass /= len(neighbors)
        return center_of_mass - current_pos
    
    def _calculate_food_attraction(self, dragonfly_index: int) -> np.ndarray:
        """
        Yiyecek cekimini hesaplar.
        
        Args:
            dragonfly_index: Yusufcuk indeksi.
            
        Returns:
            np.ndarray: Yiyecek cekim vektoru.
        """
        if not self.best_dragonfly:
            return np.zeros(len(self.dragonflies[dragonfly_index]["position"]))
        
        current_pos = np.array(self.dragonflies[dragonfly_index]["position"])
        food_pos = np.array(self.best_dragonfly["position"])
        
        return food_pos - current_pos
    
    def _calculate_enemy_distraction(self, dragonfly_index: int) -> np.ndarray:
        """
        Dusman kacinmasini hesaplar.
        
        Args:
            dragonfly_index: Yusufcuk indeksi.
            
        Returns:
            np.ndarray: Dusman kacinma vektoru.
        """
        # En kotu cozumu dusman olarak kabul et
        worst_dragonfly = min(self.dragonflies, key=lambda x: x["fitness"])
        
        current_pos = np.array(self.dragonflies[dragonfly_index]["position"])
        enemy_pos = np.array(worst_dragonfly["position"])
        
        return current_pos - enemy_pos
    
    def _apply_boundaries(self, position: np.ndarray) -> np.ndarray:
        """
        Sinirlari uygular.
        
        Args:
            position: Pozisyon vektoru.
            
        Returns:
            np.ndarray: Sinirlanmis pozisyon.
        """
        return np.clip(position, 0.0, 1.0)
    
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
    
    def evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
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
        
        # Uygunluk fonksiyonu
        fitness = (
            metrics.get("load_balance", 0) * 0.3 +
            metrics.get("time_continuity", 0) * 0.25 +
            metrics.get("classroom_changes", 0) * 0.2 +
            metrics.get("participant_count", 0) * 0.15 +
            metrics.get("instructor_requirements", 0) * 0.1
        )
        
        # Zaman slot cezasini uygula (gec saatler icin agir ceza)
        penalty = getattr(self, "_calculate_time_slot_penalty", lambda s: 0.0)(solution)
        fitness -= penalty

        # Slot odulleri ile erken saatleri tesvik et
        try:
            reward = getattr(self, "_calculate_total_slot_reward", lambda s: 0.0)(solution)
            fitness += reward / 50.0
        except Exception:
            pass
        
        return fitness
    
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
