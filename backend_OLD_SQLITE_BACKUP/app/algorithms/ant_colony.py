import random
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class AntColonyAlgorithm(BaseAlgorithm):
    def __init__(
        self,
        projects=None,
        instructors=None,
        colony_size=50,
        iterations=100,
        evaporation_rate=0.1,
        pheromone_factor=1.0,
        heuristic_factor=2.0
    ):
        super().__init__(projects, instructors, {
            'colony_size': colony_size,
            'iterations': iterations,
            'evaporation_rate': evaporation_rate,
            'pheromone_factor': pheromone_factor,
            'heuristic_factor': heuristic_factor
        })

    def _initialize_pheromone(self):
        """Feromone matrisini başlat"""
        if not self.projects or not self.instructors:
            return None
            
        num_projects = len(self.projects)
        num_instructors = len(self.instructors)
        
        # 3B feromone matrisi: Her proje pozisyonu için 
        # [proje_id][pozisyon][instructor_id]
        pheromone = np.ones((num_projects, 3, num_instructors))
        
        # Hocalara sorumlu pozisyonu için daha çok feromone
        instructor_ids = list(self.instructors.keys())
        for i, instructor_id in enumerate(instructor_ids):
            if instructor_id in self.instructors and self.instructors[instructor_id].get("type") == "professor":
                for p in range(num_projects):
                    pheromone[p][0][i] = 2.0  # Sorumlu pozisyonu için
        
        return pheromone

    def _construct_solution(self, pheromone):
        """Karıncalar için çözüm oluştur"""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        num_projects = len(project_ids)
        num_instructors = len(instructor_ids)
        
        # Her proje için atama yap
        solution = []
        instructor_usage = {i: 0 for i in instructor_ids}  # İş yükü dengelemesi için
        
        for p in range(num_projects):
            project_assignments = []
            
            for position in range(3):  # Her proje için 3 pozisyon (1 sorumlu + 2 yardımcı)
                # 0. pozisyon -> sorumlu hoca, sadece profesörlerden seçim yap
                if position == 0:
                    candidates = [i for i, i_id in enumerate(instructor_ids) 
                               if self.instructors[i_id].get("type") == "professor"]
                    if not candidates:  # Eğer profesör yoksa tüm öğretim elemanlarından seç
                        candidates = list(range(num_instructors))
                else:
                    candidates = list(range(num_instructors))
                
                # Olasılık hesapla
                probabilities = []
                denom = 0.0
                
                for i in candidates:
                    # Feromone ve sezgisel bileşenleri
                    pheromone_component = pheromone[p][position][i] ** self.parameters['pheromone_factor']
                    heuristic_component = (1.0 / (instructor_usage[instructor_ids[i]] + 1)) ** self.parameters['heuristic_factor']
                    value = pheromone_component * heuristic_component
                    probabilities.append(value)
                    denom += value
                
                # Normalize
                if denom > 0:
                    probabilities = [p / denom for p in probabilities]
                else:
                    # Eşit olasılık
                    probabilities = [1.0 / len(candidates)] * len(candidates)
                
                # Rulet tekerleği seçimi
                selected_index = self._roulette_wheel_selection(candidates, probabilities)
                selected_instructor = instructor_ids[selected_index]
                
                # İş yükünü güncelle
                instructor_usage[selected_instructor] += 1
                
                project_assignments.append(selected_instructor)
            
            solution.append(tuple(project_assignments))
        
        return solution

    def _roulette_wheel_selection(self, candidates, probabilities):
        """Rulet tekerleği seçimi"""
        r = random.random()
        cumulative_prob = 0.0
        for i, p in zip(candidates, probabilities):
            cumulative_prob += p
            if r <= cumulative_prob:
                return i
        return candidates[-1]  # Herhangi bir hata durumunda son elemanı döndür

    def _calculate_fitness(self, solution):
        """Çözümün uygunluk değerini hesapla"""
        project_ids = list(self.projects.keys())
        fitness = 0.0
        violations = 0
        
        # İş yükü dağılımı
        instructor_loads = {}
        
        # Sınıf geçişleri
        classroom_transitions = {}
        
        for i, (responsible, assistant1, assistant2) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            # Sorumlu hoca kontrolü
            if self.instructors[responsible].get("type") != "professor":
                violations += 1
            
            # Bitirme projesi için en az 2 hoca kontrolü
            if project.get("type") == "final":
                instructor_types = [
                    self.instructors[responsible].get("type"),
                    self.instructors[assistant1].get("type"),
                    self.instructors[assistant2].get("type")
                ]
                professor_count = instructor_types.count("professor")
                if professor_count < 2:
                    violations += 1
            
            # İş yükü dağılımı
            for instructor in [responsible, assistant1, assistant2]:
                if instructor not in instructor_loads:
                    instructor_loads[instructor] = 0
                instructor_loads[instructor] += 1
                
                # Sınıf geçişleri
                if project.get("classroom"):
                    if instructor not in classroom_transitions:
                        classroom_transitions[instructor] = []
                    classroom_transitions[instructor].append(project.get("classroom"))
        
        # Yük dengesizliği cezası
        load_values = list(instructor_loads.values())
        if load_values:
            load_std = np.std(load_values)
            fitness -= load_std * 5
        
        # Sınıf geçişi cezası
        for instructor, classrooms in classroom_transitions.items():
            unique_classrooms = len(set(classrooms))
            transitions = unique_classrooms - 1
            if transitions > 0:
                if self.instructors[instructor].get("type") == "professor":
                    fitness -= transitions * 10  # Hocalar için daha büyük ceza
                else:
                    fitness -= transitions * 3
        
        # Kural ihlalleri cezası
        fitness -= violations * 100
        
        return fitness

    def _update_pheromone(self, pheromone, solutions, fitnesses):
        """Feromone matrisini güncelle"""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Feromonu buharlaştır
        pheromone *= (1 - self.parameters['evaporation_rate'])
        
        # Çözümlere göre feromonu güncelle
        for solution, fitness in zip(solutions, fitnesses):
            if fitness <= 0:  # Negatif fitnesslarda ölçekleme yapılmalı
                update_value = 1.0 / (1.0 - fitness)
            else:
                update_value = fitness
            
            for p, assignment in enumerate(solution):
                for pos, instructor in enumerate(assignment):
                    i = instructor_ids.index(instructor)
                    pheromone[p][pos][i] += update_value
        
        return pheromone
    
    def _calculate_fitness_with_rules(self, solution):
        """Kurallara uygun fitness hesaplama"""
        fitness = 0.0
        project_ids = list(self.projects.keys())
        
        # 1. Proje türü kuralları kontrolü (büyük bonus)
        for i, (responsible, assistant1, assistant2) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            project_type = project.get("type", "interim")
            
            professor_count = 0
            for instructor_id in [responsible, assistant1, assistant2]:
                if self.instructors[instructor_id]["type"] == "professor":
                    professor_count += 1
            
            if project_type == "final" and professor_count >= 2:
                fitness += 100  # Büyük bonus
            elif project_type == "interim" and professor_count >= 1:
                fitness += 100  # Büyük bonus
            else:
                fitness -= 200  # Büyük ceza
        
        # 2. Yük dengesizliği kontrolü
        instructor_loads = {}
        for assignment in solution:
            responsible, assistant1, assistant2 = assignment
            for instructor_id in [responsible, assistant1, assistant2]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if instructor_loads:
            loads = list(instructor_loads.values())
            max_load = max(loads)
            min_load = min(loads)
            load_balance_penalty = (max_load - min_load) * 10
            fitness -= load_balance_penalty
        
        # 3. Çakışma kontrolü (aynı kişi aynı anda birden fazla yerde)
        timeslot_usage = {}
        conflict_penalty = 0
        for i, (responsible, assistant1, assistant2) in enumerate(solution):
            for instructor_id in [responsible, assistant1, assistant2]:
                if instructor_id in timeslot_usage:
                    conflict_penalty += 50
                timeslot_usage[instructor_id] = True
        
        fitness -= conflict_penalty
        
        return fitness
    
    def _update_pheromone_elitist(self, pheromone, solutions, fitnesses, best_solution):
        """Elitist feromone güncelleme"""
        evaporation_rate = self.parameters['evaporation_rate']
        pheromone_factor = self.parameters['pheromone_factor']
        
        # Feromone buharlaşması
        pheromone *= (1 - evaporation_rate)
        
        # En iyi çözüm için feromone ekle (elitist strateji)
        if best_solution:
            project_ids = list(self.projects.keys())
            instructor_ids = list(self.instructors.keys())
            
            for i, (responsible, assistant1, assistant2) in enumerate(best_solution):
                # Her pozisyon için feromone ekle
                positions = [responsible, assistant1, assistant2]
                for pos_idx, instructor_id in enumerate(positions):
                    if instructor_id in instructor_ids:
                        instructor_idx = instructor_ids.index(instructor_id)
                        pheromone[i][pos_idx][instructor_idx] += pheromone_factor * 2.0  # Elitist bonus
        
        return pheromone

    def optimize(self) -> Dict[str, Any]:
        """Karınca kolonisi optimizasyonunu çalıştır - Kurallara uygun"""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
        
        # Her çalıştırmada farklı sonuç için random seed
        import time
        random.seed(int(time.time() * 1000) % 2**32)
        np.random.seed(int(time.time() * 1000) % 2**32)
            
        # Feromone matrisini başlat
        pheromone = self._initialize_pheromone()
        if pheromone is None:
            return {"error": "Failed to initialize pheromone matrix"}
            
        # En iyi çözümü izle
        best_solution = None
        best_fitness = float('-inf')
        
        # Ana döngü - Ant Colony prensiplerine göre
        for iteration in range(self.parameters['iterations']):
            # Her karınca için çözüm oluştur
            solutions = []
            fitnesses = []
            
            for ant in range(self.parameters['colony_size']):
                solution = self._construct_solution(pheromone)
                fitness = self._calculate_fitness_with_rules(solution)  # Kurallara uygun fitness
                solutions.append(solution)
                fitnesses.append(fitness)
                
                # En iyi çözümü güncelle
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_solution = solution
            
            # Feromonu güncelle - elitist strateji ile
            pheromone = self._update_pheromone_elitist(pheromone, solutions, fitnesses, best_solution)
        
        # Sonuçları hazırla
        project_ids = list(self.projects.keys())
        assignments = {}
        for i, (responsible, assistant1, assistant2) in enumerate(best_solution):
            project_id = project_ids[i]
            assignments[project_id] = {
                "responsible": responsible,
                "assistants": [assistant1, assistant2]
            }
        
        return {
            "assignments": assignments,
            "fitness": best_fitness,
            "iterations": self.parameters['iterations']
        } 
        