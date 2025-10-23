"""
Hybrid CP-SAT + Tabu/SA + NSGA-II algoritması sınıfı.
Pratik & hızlı çözüm için CP-SAT feasibility + metaheuristic iyileştirme + çok-amaçlı optimizasyon.
"""
from typing import Dict, Any, List, Tuple, Optional
import random
import numpy as np
import time
from ortools.sat.python import cp_model
from collections import deque
import math

from app.algorithms.base import BaseAlgorithm

class HybridCPSATTabuSANsga(BaseAlgorithm):
    """
    Hybrid CP-SAT + Tabu/SA + NSGA-II algoritması sınıfı.
    Pratik & hızlı çözüm için CP-SAT feasibility + metaheuristic iyileştirme + çok-amaçlı optimizasyon.
    
    Aşamalar:
    1. CP-SAT ile feasibility çözümü
    2. Tabu Search ile yerel optimizasyon
    3. Simulated Annealing ile global optimizasyon
    4. NSGA-II ile çok-amaçlı optimizasyon
    """
    
    def __init__(self, projects=None, instructors=None, parameters=None):
        """
        Hybrid CP-SAT + Tabu/SA + NSGA-II algoritması başlatıcı.
        
        Args:
            projects: Projelerin bilgileri
            instructors: Öğretim elemanlarının bilgileri
            parameters: Algoritma parametreleri
        """
        super().__init__(projects, instructors, parameters)
        params = parameters or {}
        self.time_limit = params.get("time_limit", 180)  # 3 dakika
        self.cp_time_limit = params.get("cp_time_limit", 30)  # 30 saniye CP için
        self.tabu_iterations = params.get("tabu_iterations", 50)
        self.sa_iterations = params.get("sa_iterations", 100)
        self.nsga_generations = params.get("nsga_generations", 20)
        self.population_size = params.get("population_size", 30)
        
        self.best_solution = None
        self.best_fitness = None
        self.objective_scores = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Hybrid algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Veri hazırlığı
        self._prepare_data()
        
        # Amaç fonksiyonu skorları
        self.objective_scores = {
            "assignment_completion": 0.0,
            "load_balance": 0.0,
            "classroom_concentration": 0.0,
            "schedule_uniformity": 0.0,
            "constraint_compliance": 0.0
        }
    
    def optimize(self) -> Dict[str, Any]:
        """
        Hybrid CP-SAT + Tabu/SA + NSGA-II optimizasyonunu çalıştırır.
        
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Veri hazırlığı
        data = {
            "instructors": self.instructors,
            "projects": self.projects,
            "classrooms": getattr(self, 'classrooms', []),
            "timeslots": getattr(self, 'timeslots', [])
        }
        self.initialize(data)
        
        start_time = time.time()
        
        # Aşama 1: CP-SAT ile feasibility çözümü
        print("Aşama 1: CP-SAT feasibility çözümü...")
        feasibility_solution = self._solve_feasibility_cp_sat()
        
        if not feasibility_solution:
            print("Feasibility çözümü bulunamadı!")
            return self._create_empty_result()
        
        print(f"Feasibility çözümü bulundu: {len(feasibility_solution)} proje atandı")
        
        # Aşama 2: Tabu Search ile yerel optimizasyon
        print("Aşama 2: Tabu Search yerel optimizasyon...")
        tabu_solution = self._optimize_with_tabu_search(feasibility_solution)
        
        # Aşama 3: Simulated Annealing ile global optimizasyon
        print("Aşama 3: Simulated Annealing global optimizasyon...")
        sa_solution = self._optimize_with_simulated_annealing(tabu_solution)
        
        # Aşama 4: NSGA-II ile çok-amaçlı optimizasyon
        print("Aşama 4: NSGA-II çok-amaçlı optimizasyon...")
        final_solution = self._optimize_with_nsga_ii(sa_solution)
        
        # Final çözümü değerlendir
        self.best_solution = final_solution
        self.best_fitness = self._evaluate_solution_quality(final_solution)
        self._calculate_objective_scores(final_solution)
        
        execution_time = time.time() - start_time
        print(f"Optimizasyon tamamlandı. Süre: {execution_time:.2f} saniye")
        
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "objective_scores": self.objective_scores,
            "time_limit": self.time_limit,
            "execution_time": execution_time,
            "stages_completed": ["cp_sat", "tabu_search", "simulated_annealing", "nsga_ii"]
        }
    
    def _prepare_data(self) -> None:
        """Veri hazırlığı yapar."""
        # Hoca ve asistan ayrımı
        self.hocas = [i for i in self.instructors if i.get("role") == "hoca"]
        self.asistans = [i for i in self.instructors if i.get("role") == "aras_gor"]
        
        # Proje tiplerine göre ayrım
        self.ara_projects = [p for p in self.projects if p.get("type") == "ara"]
        self.bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        
        # Zaman dilimi sıralaması
        self.timeslots.sort(key=lambda x: x.get("start_time", ""))
    
    def _solve_feasibility_cp_sat(self) -> Optional[List[Dict[str, Any]]]:
        """CP-SAT ile feasibility problemi çözer."""
        model = cp_model.CpModel()
        
        # Karar değişkenleri
        x = {}
        for project in self.projects:
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    x[(project.get("id"), classroom.get("id"), timeslot.get("id"))] = model.NewBoolVar(
                        f"x_{project.get('id')}_{classroom.get('id')}_{timeslot.get('id')}"
                    )
        
        # Kısıtlar
        # 1. Her proje tam olarak bir kez sunulmalı
        for project in self.projects:
            model.Add(sum(x[(project.get("id"), c.get("id"), t.get("id"))] 
                      for c in self.classrooms for t in self.timeslots) == 1)
        
        # 2. Her sınıf-zaman dilimi çifti en fazla bir proje alabilir
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                model.Add(sum(x[(p.get("id"), classroom.get("id"), timeslot.get("id"))] 
                             for p in self.projects) <= 1)
        
        # 3. Ardışık zaman dilimi kısıtları
        self._add_consecutive_timeslot_constraints(model, x)
        
        # Çözücü
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.cp_time_limit
        
        # Çöz
        status = solver.Solve(model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Çözümü çıkar
            solution = []
            for project in self.projects:
                for classroom in self.classrooms:
                    for timeslot in self.timeslots:
                        if solver.Value(x[(project.get("id"), classroom.get("id"), timeslot.get("id"))]):
                            instructors = self._assign_jury_for_project(project, classroom, timeslot)
                            assignment = {
                                "project_id": project.get("id"),
                                "classroom_id": classroom.get("id"),
                                "timeslot_id": timeslot.get("id"),
                                "instructors": instructors
                            }
                            solution.append(assignment)
            return solution
        
        return None
    
    def _optimize_with_tabu_search(self, initial_solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Tabu Search ile yerel optimizasyon yapar."""
        current_solution = initial_solution.copy()
        best_solution = initial_solution.copy()
        
        current_score = self._calculate_classroom_concentration_score(current_solution)
        best_score = current_score
        
        tabu_list = deque(maxlen=20)
        
        for iteration in range(self.tabu_iterations):
            # Komşu çözümler oluştur
            neighbors = self._generate_tabu_neighbors(current_solution)
            
            best_neighbor = None
            best_neighbor_score = current_score
            
            for neighbor in neighbors:
                neighbor_score = self._calculate_classroom_concentration_score(neighbor)
                neighbor_hash = hash(str(sorted(neighbor, key=lambda x: x["project_id"])))
                
                if neighbor_hash not in tabu_list and neighbor_score > best_neighbor_score:
                    best_neighbor = neighbor
                    best_neighbor_score = neighbor_score
            
            if best_neighbor:
                current_solution = best_neighbor
                current_score = best_neighbor_score
                
                if current_score > best_score:
                    best_solution = current_solution
                    best_score = current_score
                
                # Tabu listesine ekle
                tabu_list.append(hash(str(sorted(current_solution, key=lambda x: x["project_id"]))))
            else:
                break
        
        return best_solution
    
    def _optimize_with_simulated_annealing(self, initial_solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simulated Annealing ile global optimizasyon yapar."""
        current_solution = initial_solution.copy()
        best_solution = initial_solution.copy()
        
        current_score = self._calculate_load_balance(current_solution)
        best_score = current_score
        
        temperature = 1000.0
        cooling_rate = 0.95
        min_temperature = 1.0
        
        for iteration in range(self.sa_iterations):
            # Komşu çözüm oluştur
            neighbor = self._generate_sa_neighbor(current_solution)
            neighbor_score = self._calculate_load_balance(neighbor)
            
            # Kabul kriteri
            if neighbor_score > current_score or random.random() < math.exp((neighbor_score - current_score) / temperature):
                current_solution = neighbor
                current_score = neighbor_score
                
                if current_score > best_score:
                    best_solution = current_solution
                    best_score = current_score
            
            temperature *= cooling_rate
            
            if temperature < min_temperature:
                break
        
        return best_solution
    
    def _optimize_with_nsga_ii(self, initial_solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """NSGA-II ile çok-amaçlı optimizasyon yapar."""
        # Başlangıç popülasyonu oluştur
        population = [initial_solution]
        
        # Rastgele çözümler ekle
        for _ in range(self.population_size - 1):
            random_solution = self._create_random_solution()
            if random_solution:
                population.append(random_solution)
        
        # Nesil döngüsü
        for generation in range(self.nsga_generations):
            # Popülasyonu değerlendir
            self._evaluate_population(population)
            
            # Ebeveyn seçimi
            parents = self._select_parents_nsga(population)
            
            # Yeni nesil oluştur
            offspring = self._create_offspring_nsga(parents)
            
            # Popülasyonu güncelle
            population = self._update_population_nsga(population, offspring)
        
        # En iyi çözümü seç
        self._evaluate_population(population)
        best_individual = max(population, key=lambda x: x.get("fitness", 0))
        
        return best_individual.get("solution", initial_solution)
    
    def _add_consecutive_timeslot_constraints(self, model: cp_model.CpModel, x: Dict) -> None:
        """Ardışık zaman dilimi kısıtlarını ekler."""
        sorted_timeslots = sorted(self.timeslots, key=lambda t: t.get("start_time", ""))
        
        for i in range(len(sorted_timeslots) - 1):
            current_timeslot = sorted_timeslots[i]
            next_timeslot = sorted_timeslots[i + 1]
            
            for classroom in self.classrooms:
                current_has_project = sum(x[(p.get("id"), classroom.get("id"), current_timeslot.get("id"))] 
                                        for p in self.projects)
                next_has_project = sum(x[(p.get("id"), classroom.get("id"), next_timeslot.get("id"))] 
                                      for p in self.projects)
                
                model.Add(current_has_project <= next_has_project)
    
    def _assign_jury_for_project(self, project: Dict[str, Any], classroom: Dict[str, Any], timeslot: Dict[str, Any]) -> List[str]:
        """Proje için jüri ataması yapar."""
        instructors = []
        
        # Sorumlu öğretim üyesi
        responsible_id = project.get("responsible_id")
        if responsible_id:
            instructors.append(responsible_id)
        
        # Proje tipine göre jüri seçimi
        project_type = project.get("type")
        
        if project_type == "bitirme":
            # Bitirme projesi için en az 2 hoca
            hocas = [h for h in self.hocas if h.get("id") != responsible_id]
            if len(hocas) >= 2:
                instructors.extend([h.get("id") for h in hocas[:2]])
            elif len(hocas) == 1:
                instructors.append(hocas[0].get("id"))
                if self.asistans:
                    instructors.append(random.choice(self.asistans).get("id"))
        else:
            # Ara proje için en az 1 hoca (sorumlu hoca zaten var)
            available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
            if len(available_instructors) >= 2:
                selected = random.sample(available_instructors, 2)
                instructors.extend([s.get("id") for s in selected])
        
        return instructors[:3]
    
    def _generate_tabu_neighbors(self, solution: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Tabu Search için komşu çözümler oluşturur."""
        neighbors = []
        
        # Sınıf değişimi
        for i in range(len(solution)):
            for j in range(i + 1, len(solution)):
                neighbor = solution.copy()
                neighbor[i]["classroom_id"], neighbor[j]["classroom_id"] = neighbor[j]["classroom_id"], neighbor[i]["classroom_id"]
                neighbors.append(neighbor)
        
        return neighbors[:10]
    
    def _generate_sa_neighbor(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simulated Annealing için komşu çözüm oluşturur."""
        neighbor = solution.copy()
        
        # Rastgele iki atamanın zaman dilimlerini değiştir
        if len(neighbor) >= 2:
            i, j = random.sample(range(len(neighbor)), 2)
            neighbor[i]["timeslot_id"], neighbor[j]["timeslot_id"] = neighbor[j]["timeslot_id"], neighbor[i]["timeslot_id"]
        
        return neighbor
    
    def _create_random_solution(self) -> Optional[List[Dict[str, Any]]]:
        """Rastgele çözüm oluşturur."""
        solution = []
        assigned_projects = set()
        assigned_classrooms_timeslots = set()
        
        projects = list(self.projects)
        random.shuffle(projects)
        
        for project in projects:
            available_classrooms = [c for c in self.classrooms 
                                  if (c.get("id"), t.get("id")) not in assigned_classrooms_timeslots 
                                  for t in self.timeslots]
            
            if available_classrooms:
                classroom = random.choice(available_classrooms)
                timeslot = random.choice(self.timeslots)
                
                if (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots:
                    instructors = self._assign_jury_for_project(project, classroom, timeslot)
                    assignment = {
                        "project_id": project.get("id"),
                        "classroom_id": classroom.get("id"),
                        "timeslot_id": timeslot.get("id"),
                        "instructors": instructors
                    }
                    solution.append(assignment)
                    assigned_projects.add(project.get("id"))
                    assigned_classrooms_timeslots.add((classroom.get("id"), timeslot.get("id")))
        
        return solution if len(solution) == len(self.projects) else None
    
    def _evaluate_population(self, population: List[Dict[str, Any]]) -> None:
        """Popülasyonu değerlendirir."""
        for individual in population:
            if isinstance(individual, dict) and "solution" in individual:
                solution = individual["solution"]
            else:
                solution = individual
            
            # Çoklu amaç fonksiyonları
            objectives = [
                self._calculate_classroom_concentration_score(solution),
                self._calculate_load_balance(solution),
                self._calculate_schedule_uniformity_score(solution)
            ]
            
            # Toplam fitness
            fitness = sum(objectives) / len(objectives)
            
            if isinstance(individual, dict):
                individual["objectives"] = objectives
                individual["fitness"] = fitness
            else:
                # Individual bir çözüm ise, dict'e dönüştür
                individual = {
                    "solution": solution,
                    "objectives": objectives,
                    "fitness": fitness
                }
    
    def _select_parents_nsga(self, population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """NSGA-II için ebeveyn seçimi yapar."""
        parents = []
        
        for _ in range(self.population_size):
            # Turnuva seçimi
            candidates = random.sample(population, min(3, len(population)))
            best_candidate = max(candidates, key=lambda x: x.get("fitness", 0))
            parents.append(best_candidate)
        
        return parents
    
    def _create_offspring_nsga(self, parents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """NSGA-II için yavru oluşturur."""
        offspring = []
        
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                parent1 = parents[i]
                parent2 = parents[i + 1]
                
                # Çaprazlama
                child1, child2 = self._crossover_nsga(parent1["solution"], parent2["solution"])
                
                # Mutasyon
                child1 = self._mutate_nsga(child1)
                child2 = self._mutate_nsga(child2)
                
                offspring.extend([
                    {"solution": child1, "objectives": None, "fitness": None},
                    {"solution": child2, "objectives": None, "fitness": None}
                ])
        
        return offspring
    
    def _crossover_nsga(self, solution1: List[Dict[str, Any]], solution2: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """NSGA-II için çaprazlama yapar."""
        if not solution1 or not solution2:
            return solution1, solution2
        
        crossover_point = random.randint(1, min(len(solution1), len(solution2)) - 1)
        
        child1 = solution1[:crossover_point] + solution2[crossover_point:]
        child2 = solution2[:crossover_point] + solution1[crossover_point:]
        
        # Çözümleri düzelt
        child1 = self._repair_solution(child1)
        child2 = self._repair_solution(child2)
        
        return child1, child2
    
    def _mutate_nsga(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """NSGA-II için mutasyon yapar."""
        if not solution:
            return solution
        
        mutated = solution.copy()
        
        # Rastgele bir atamayı değiştir
        mutation_idx = random.randint(0, len(mutated) - 1)
        assignment = mutated[mutation_idx]
        
        # Sınıf veya zaman dilimi değiştir
        if random.random() < 0.5:
            new_classroom = random.choice(self.classrooms)
            assignment["classroom_id"] = new_classroom.get("id")
        else:
            new_timeslot = random.choice(self.timeslots)
            assignment["timeslot_id"] = new_timeslot.get("id")
        
        return self._repair_solution(mutated)
    
    def _repair_solution(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Çözümdeki çakışmaları giderir."""
        assigned_projects = set()
        assigned_classrooms_timeslots = set()
        valid_assignments = []
        
        for assignment in solution:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            if project_id not in assigned_projects and (classroom_id, timeslot_id) not in assigned_classrooms_timeslots:
                valid_assignments.append(assignment)
                assigned_projects.add(project_id)
                assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
        
        return valid_assignments
    
    def _update_population_nsga(self, population: List[Dict[str, Any]], offspring: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """NSGA-II için popülasyonu günceller."""
        # Popülasyon ve yavruları birleştir
        combined = population + offspring
        
        # Fitness'e göre sırala
        combined.sort(key=lambda x: x.get("fitness", 0), reverse=True)
        
        # En iyi bireyleri seç
        return combined[:self.population_size]
    
    def _calculate_classroom_concentration_score(self, solution: List[Dict[str, Any]]) -> float:
        """Sınıf konsantrasyonu skorunu hesaplar."""
        instructor_classrooms = {}
        
        for assignment in solution:
            classroom_id = assignment["classroom_id"]
            for instructor_id in assignment["instructors"]:
                if instructor_id not in instructor_classrooms:
                    instructor_classrooms[instructor_id] = []
                instructor_classrooms[instructor_id].append(classroom_id)
        
        concentration_score = 0.0
        hoca_count = 0
        
        for instructor_id, classrooms in instructor_classrooms.items():
            instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
            if instructor and instructor.get("role") == "hoca":
                hoca_count += 1
                if classrooms:
                    most_common_classroom = max(set(classrooms), key=classrooms.count)
                    concentration_ratio = classrooms.count(most_common_classroom) / len(classrooms)
                    concentration_score += concentration_ratio
        
        return concentration_score / hoca_count if hoca_count > 0 else 0.0
    
    def _calculate_schedule_uniformity_score(self, solution: List[Dict[str, Any]]) -> float:
        """Takvim uniformluğu skorunu hesaplar."""
        daily_distribution = {}
        
        for assignment in solution:
            timeslot_id = assignment["timeslot_id"]
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)
            if timeslot:
                day = timeslot.get("day", "unknown")
                daily_distribution[day] = daily_distribution.get(day, 0) + 1
        
        if not daily_distribution:
            return 0.0
        
        values = list(daily_distribution.values())
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        return 1.0 / (1.0 + variance) if variance > 0 else 1.0
    
    def _evaluate_solution_quality(self, solution: List[Dict[str, Any]]) -> float:
        """Çözüm kalitesini değerlendirir."""
        if not solution:
            return 0.0
        
        weights = {
            "assignment_completion": 0.4,
            "load_balance": 0.25,
            "classroom_concentration": 0.2,
            "schedule_uniformity": 0.15
        }
        
        scores = {
            "assignment_completion": len(solution) / len(self.projects) if self.projects else 0.0,
            "load_balance": self._calculate_load_balance(solution),
            "classroom_concentration": self._calculate_classroom_concentration_score(solution),
            "schedule_uniformity": self._calculate_schedule_uniformity_score(solution)
        }
        
        return sum(weights[key] * scores[key] for key in weights)
    
    def _calculate_objective_scores(self, solution: List[Dict[str, Any]]) -> None:
        """Amaç fonksiyonu skorlarını hesaplar ve normalize eder."""
        if not solution:
            return
        
        self.objective_scores["assignment_completion"] = (len(solution) / len(self.projects)) * 100
        self.objective_scores["load_balance"] = self._calculate_load_balance(solution) * 100
        self.objective_scores["classroom_concentration"] = self._calculate_classroom_concentration_score(solution) * 100
        self.objective_scores["schedule_uniformity"] = self._calculate_schedule_uniformity_score(solution) * 100
        self.objective_scores["constraint_compliance"] = self._calculate_constraint_compliance(solution) * 100
    
    def _calculate_constraint_compliance(self, solution: List[Dict[str, Any]]) -> float:
        """Kısıt uyumluluğunu hesaplar."""
        if not solution:
            return 0.0
        
        total_constraints = 0
        satisfied_constraints = 0
        
        for assignment in solution:
            project_id = assignment["project_id"]
            instructors = assignment["instructors"]
            
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if not project:
                continue
            
            # Kısıt 1: Her projede 3 katılımcı
            total_constraints += 1
            if len(instructors) == 3:
                satisfied_constraints += 1
            
            # Kısıt 2: Sorumlu hoca ilk sırada
            total_constraints += 1
            if instructors and instructors[0] == project.get("responsible_id"):
                satisfied_constraints += 1
            
            # Kısıt 3: Proje tipine göre hoca sayısı
            project_type = project.get("type")
            if project_type == "bitirme":
                total_constraints += 1
                hoca_count = sum(1 for i in instructors 
                               if next((inst for inst in self.instructors if inst.get("id") == i), {}).get("role") == "hoca")
                if hoca_count >= 2:
                    satisfied_constraints += 1
            elif project_type == "ara":
                total_constraints += 1
                has_hoca = any(next((inst for inst in self.instructors if inst.get("id") == i), {}).get("role") == "hoca" 
                             for i in instructors)
                if has_hoca:
                    satisfied_constraints += 1
        
        return satisfied_constraints / total_constraints if total_constraints > 0 else 0.0
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Boş sonuç döndürür."""
        return {
            "schedule": [],
            "fitness": 0.0,
            "objective_scores": self.objective_scores,
            "time_limit": self.time_limit,
            "execution_time": 0.0,
            "stages_completed": []
        }
    
    def evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
        """Verilen çözümün uygunluğunu değerlendirir."""
        return self._evaluate_solution_quality(solution)
    
    def _calculate_load_balance(self, solution: List[Dict[str, Any]]) -> float:
        """Yük dengesini hesaplar."""
        if not solution:
            return 0.0
        
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment["instructors"]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        
        # Gini katsayısı hesapla
        array = np.array(loads)
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1)
        n = array.shape[0]
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
        
        return 1.0 - gini
        
    def validate_parameters(self) -> bool:
        """
        Algoritma parametrelerini doğrula.
        
        Returns:
            bool: Parametreler geçerli mi?
        """
        required_params = ["time_limit", "cp_time_limit", "tabu_iterations", "sa_iterations", "nsga_generations", "population_size"]
        
        for param in required_params:
            if param not in self.parameters:
                return False
            
            if not isinstance(self.parameters[param], (int, float)) or self.parameters[param] <= 0:
                return False
        
        return True
