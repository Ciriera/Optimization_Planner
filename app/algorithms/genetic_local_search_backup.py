"""
Genetic Algorithm + Local Search hibrit algoritmasi sinifi - CP-SAT ozellikli versiyon.
"""
from typing import Dict, Any, List, Tuple
import random
import copy
import numpy as np

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class GeneticLocalSearch(OptimizationAlgorithm):
    """
    Genetic Algorithm + Local Search hibrit algoritmasi sinifi.
    Genetik algoritma ile yerel arama kombinasyonu kullanarak proje atama problemini cozer.
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
        Genetic Local Search algoritmasi baslatici - CP-SAT ozellikli versiyon.

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
        self.population_size = params.get("population_size", 50)
        self.generations = params.get("generations", 100)
        self.mutation_rate = params.get("mutation_rate", 0.1)
        self.crossover_rate = params.get("crossover_rate", 0.8)
        self.local_search_rate = params.get("local_search_rate", 0.3)  # Yerel arama orani
        self.local_search_iterations = params.get("local_search_iterations", 50)  # Yerel arama iterasyonlari

        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Genetic Local Search algoritmasini baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

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

        # Populasyonu baslat
        self.population = self._initialize_population()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genetic Local Search algoritmasini calistirir - CP-SAT ozellikli versiyon.

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
        generation = 0
        while time.time() - start_time < self.time_limit and generation < self.generations:
            # Fitness degerlerini hesapla
            self._evaluate_population()
            
            # En iyi cozumu guncelle
            self._update_best_solution()
            
            # Yeni populasyon olustur
            new_population = []
            
            # Elitizm - en iyi %10'u koru
            elite_size = int(self.population_size * 0.1)
            elite = sorted(self.population, key=lambda x: x["fitness"], reverse=True)[:elite_size]
            new_population.extend(elite)
            
            # Kalan populasyonu olustur
            while len(new_population) < self.population_size:
                # Ebeveyn secimi
                parent1 = self._tournament_selection()
                parent2 = self._tournament_selection()
                
                # Crossover
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
                
                # Mutation
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2)
                
                # Local search
                if random.random() < self.local_search_rate:
                    child1 = self._local_search(child1)
                if random.random() < self.local_search_rate:
                    child2 = self._local_search(child2)
                
                new_population.extend([child1, child2])
            
            # Populasyonu guncelle
            self.population = new_population[:self.population_size]

            # Nesil sayisini artir
            generation += 1

        # Son degerlendirme
        self._evaluate_population()
        self._update_best_solution()

        # Sonucu dondur (duplicate project_id kayitlarini temizle)
        final_schedule = self._deduplicate_assignments(self.best_solution)
        return {
            "schedule": final_schedule,
            "fitness": self.best_fitness,
            "generations": generation,
            "execution_time": time.time() - start_time
        }
    
    def _initialize_population(self) -> List[Dict[str, Any]]:
        """
        Populasyonu baslatir.
        
        Returns:
            List[Dict[str, Any]]: Baslangic populasyonu.
        """
        population = []
        
        for _ in range(self.population_size):
            # Rastgele bir cozum olustur
            solution = self._create_random_solution()
            
            individual = {
                "solution": solution,
                "fitness": 0.0
            }
            
            population.append(individual)
        
        return population
    
    def _evaluate_population(self):
        """Populasyonun fitness degerlerini hesaplar."""
        for individual in self.population:
            individual["fitness"] = self.evaluate_fitness(individual["solution"])
    
    def _update_best_solution(self):
        """En iyi cozumu gunceller."""
        for individual in self.population:
            if individual["fitness"] > self.best_fitness:
                self.best_solution = copy.deepcopy(individual["solution"])
                self.best_fitness = individual["fitness"]
    
    def _tournament_selection(self) -> Dict[str, Any]:
        """
        Turnuva secimi yapar.
        
        Returns:
            Dict[str, Any]: Secilen birey.
        """
        tournament_size = 3
        tournament = random.sample(self.population, tournament_size)
        return max(tournament, key=lambda x: x["fitness"])
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Crossover islemi yapar.
        
        Args:
            parent1: Ilk ebeveyn.
            parent2: Ikinci ebeveyn.
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: Iki cocuk.
        """
        child1_solution = []
        child2_solution = []
        
        # Her proje icin crossover
        for i, project in enumerate(self.projects):
            if random.random() < 0.5:
                # Parent1'den al
                child1_solution.append(copy.deepcopy(parent1["solution"][i]))
                child2_solution.append(copy.deepcopy(parent2["solution"][i]))
            else:
                # Parent2'den al
                child1_solution.append(copy.deepcopy(parent2["solution"][i]))
                child2_solution.append(copy.deepcopy(parent1["solution"][i]))
        
        child1 = {
            "solution": child1_solution,
            "fitness": 0.0

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
        
        child2 = {
            "solution": child2_solution,
            "fitness": 0.0
        }
        
        return child1, child2
    
    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mutation islemi yapar.
        
        Args:
            individual: Mutasyona ugrayacak birey.
            
        Returns:
            Dict[str, Any]: Mutasyona ugramis birey.
        """
        mutated_solution = copy.deepcopy(individual["solution"])
        
        # Rastgele bir atamayi degistir
        if mutated_solution:
            mutation_index = random.randint(0, len(mutated_solution) - 1)
            assignment = mutated_solution[mutation_index]
            
            # Sinif degistir
            if random.random() < 0.5:
                assignment["classroom_id"] = random.randint(1, len(self.classrooms))
            else:
                # Zaman dilimi degistir
                assignment["timeslot_id"] = random.randint(1, len(self.timeslots))
            
            # Instructor'lari degistir
            if random.random() < 0.3:
                if len(self.instructors) >= 3:
                    instructors = random.sample(self.instructors, 3)
                    assignment["instructors"] = [inst["id"] for inst in instructors]
        
        return {
            "solution": mutated_solution,
            "fitness": 0.0
        }
    
    def _local_search(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yerel arama yapar.
        
        Args:
            individual: Yerel arama yapilacak birey.
            
        Returns:
            Dict[str, Any]: Yerel arama sonucu.
        """
        current_solution = copy.deepcopy(individual["solution"])
        current_fitness = self.evaluate_fitness(current_solution)
        
        # Yerel arama iterasyonlari
        for _ in range(self.local_search_iterations):
            # Komsu cozum olustur
            neighbor_solution = self._create_neighbor(current_solution)
            neighbor_fitness = self.evaluate_fitness(neighbor_solution)
            
            # Eger komsu daha iyiyse kabul et
            if neighbor_fitness > current_fitness:
                current_solution = neighbor_solution
                current_fitness = neighbor_fitness
        
        return {
            "solution": current_solution,
            "fitness": current_fitness
        }
    
    def _create_neighbor(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Komsu cozum olusturur.
        
        Args:
            solution: Mevcut cozum.
            
        Returns:
            List[Dict[str, Any]]: Komsu cozum.
        """
        neighbor = copy.deepcopy(solution)
        
        # Rastgele bir atamayi degistir
        if neighbor:
            mutation_index = random.randint(0, len(neighbor) - 1)
            assignment = neighbor[mutation_index]
            
            # Kucuk degisiklik yap
            if random.random() < 0.5:
                # Sinif degistir
                current_classroom = assignment["classroom_id"]
                new_classroom = random.choice([c for c in range(1, len(self.classrooms) + 1) if c != current_classroom])
                assignment["classroom_id"] = new_classroom
            else:
                # Zaman dilimi degistir
                current_timeslot = assignment["timeslot_id"]
                new_timeslot = random.choice([t for t in range(1, len(self.timeslots) + 1) if t != current_timeslot])
                assignment["timeslot_id"] = new_timeslot
        
        return neighbor
    
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
        # Girdi farkli formatlarda gelebilir: dict veya list
        assignments = self._extract_assignments(solution)
        if not assignments:
            return 0.0

        # Sert kisitlar: bosluk ve gec saat kurali
        gap_penalty = self._calculate_gap_penalty(assignments)
        if gap_penalty < 0:
            return gap_penalty  # -9999

        time_penalty = self._calculate_time_slot_penalty(assignments)
        if time_penalty < 0:
            return time_penalty  # -9999

        # Temel skor bilesenleri
        score = 0.0

        # Kural uygunlugu (basit)
        rule_compliance = self._calculate_rule_compliance(assignments)  # 0..1
        score += rule_compliance * 100.0

        # Sinif degisimlerini azalt
        instructor_changes = self._count_instructor_classroom_changes(assignments)
        score -= instructor_changes * 10.0

        # Yuk dengesi 0..100
        instructor_loads = {}
        for a in assignments:
            for inst_id in a.get("instructors", []):
                instructor_loads[inst_id] = instructor_loads.get(inst_id, 0) + 1
        load_balance_score = self._calculate_load_balance(instructor_loads)
        score += load_balance_score * 0.5  # 0..50 katki

        return score

    def _extract_assignments(self, solution_like: Any) -> List[Dict[str, Any]]:
        """Cozum nesnesinden atama listesini cikarir (dict/list uyumlu)."""
        if isinstance(solution_like, list):
            return solution_like
        if isinstance(solution_like, dict):
            if "solution" in solution_like and isinstance(solution_like["solution"], list):
                return solution_like["solution"]
            if "schedule" in solution_like and isinstance(solution_like["schedule"], list):
                return solution_like["schedule"]
        return []

    def _calculate_time_slot_penalty(self, assignments: List[Dict[str, Any]]) -> float:
        """Standart baz ceza uygular (pozitif doner)."""
        return super()._calculate_time_slot_penalty(assignments)

    def _calculate_gap_penalty(self, assignments: List[Dict[str, Any]]) -> float:
        """Iki dolu slot arasinda bosluk varsa -9999 ceza."""
        used_indices = []
        for a in assignments:
            ts_id = a.get("timeslot_id")
            for idx, ts in enumerate(self.timeslots):
                if ts.get("id") == ts_id:
                    used_indices.append(idx)
                    break
        if not used_indices:
            return 0.0
        used_indices = sorted(set(used_indices))
        for i in range(1, len(used_indices)):
            if used_indices[i] - used_indices[i - 1] > 1:
                return -9999.0
        return 0.0

    def _count_instructor_classroom_changes(self, assignments: List[Dict[str, Any]]) -> int:
        """Ogretim uyesi basina sinif degisim sayisini hesaplar."""
        # Zaman sirasina gore sirala
        def ts_index(ts_id: int) -> int:
            for idx, ts in enumerate(self.timeslots):
                if ts.get("id") == ts_id:
                    return idx
            return 10**9
        sorted_assignments = sorted(assignments, key=lambda a: ts_index(a.get("timeslot_id")))

        last_room_by_instructor: Dict[int, Any] = {}
        changes = 0
        for a in sorted_assignments:
            room = a.get("classroom_id")
            for inst_id in a.get("instructors", []):
                if inst_id in last_room_by_instructor and last_room_by_instructor[inst_id] != room:
                    changes += 1
                last_room_by_instructor[inst_id] = room
        return changes

    def _calculate_rule_compliance(self, assignments: List[Dict[str, Any]]) -> float:
        """Basit kural uygunlugu: her atamada en az 1 egitmen olmali; bitirme icin >=2."""
        if not assignments:
            return 0.0
        satisfied = 0
        total = 0
        for a in assignments:
            total += 1
            proj = next((p for p in self.projects if p.get("id") == a.get("project_id")), None)
            instructors = a.get("instructors", [])
            if not proj:
                continue
            if proj.get("type") == "bitirme":
                if len(instructors) >= 2:
                    satisfied += 1
            else:
                if len(instructors) >= 1:
                    satisfied += 1
        return (satisfied / total) if total > 0 else 0.0
    
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
