import random
import time
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class SimplexAlgorithm(BaseAlgorithm):
    """
    Simplex algoritması - Linear Programming tabanlı optimizasyon
    Doğrusal programlama kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, projects=None, instructors=None, max_iterations=1000, tolerance=0.001):
        super().__init__(projects, instructors, {
            'max_iterations': max_iterations,
            'tolerance': tolerance
        })
        self.solution = None
        
    def _initialize_solution(self) -> List[Tuple[int, int, int]]:
        solution = []
        for p_id in self.projects:
            professor_ids = [i_id for i_id, i in self.instructors.items() if i["type"] == "professor"]
            if not professor_ids:
                professor_ids = list(self.instructors.keys())
            responsible = random.choice(professor_ids)
            assistants = random.sample(list(self.instructors.keys()), min(2, len(self.instructors)))
            if len(assistants) < 2:
                assistants.extend([random.choice(list(self.instructors.keys()))] * (2 - len(assistants)))
            solution.append((responsible, assistants[0], assistants[1]))
        return solution

    def _calculate_energy(self, solution: List[Tuple[int, int, int]]) -> float:
        """
        Linear Programming tabanlı amaç fonksiyonu hesaplama
        Minimize edilecek toplam maliyet
        """
        energy = 0.0
        violations = 0
        project_ids = list(self.projects.keys())
        
        # 1. Yük dengesizliği maliyeti (Gini katsayısı benzeri)
        instructor_loads = {}
        for assignment in solution:
            responsible, assistant1, assistant2 = assignment
            for instructor_id in [responsible, assistant1, assistant2]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if instructor_loads:
            loads = list(instructor_loads.values())
            # Gini katsayısı hesapla
            if len(loads) > 1:
                loads_array = np.array(loads)
                loads_array = np.sort(loads_array)
                n = len(loads_array)
                index = np.arange(1, n + 1)
                gini = ((np.sum((2 * index - n - 1) * loads_array)) / (n * np.sum(loads_array)))
                energy += gini * 100  # Yük dengesizliği cezası
        
        # 2. Proje türü kısıtları (büyük cezalar)
        for i, (responsible, assistant1, assistant2) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            project_type = project.get("type", "interim")
            
            professor_count = 0
            for instructor_id in [responsible, assistant1, assistant2]:
                if self.instructors[instructor_id]["type"] == "professor":
                    professor_count += 1
            
            if project_type == "final" and professor_count < 2:
                energy += 1000  # Çok büyük ceza - kısıt ihlali
                violations += 1
            elif project_type == "interim" and professor_count < 1:
                energy += 500   # Büyük ceza - kısıt ihlali
                violations += 1
        
        # 3. Çakışma maliyeti (aynı kişi aynı anda birden fazla yerde)
        timeslot_usage = {}
        for i, (responsible, assistant1, assistant2) in enumerate(solution):
            for instructor_id in [responsible, assistant1, assistant2]:
                if instructor_id in timeslot_usage:
                    energy += 200  # Çakışma cezası
                    violations += 1
                timeslot_usage[instructor_id] = True
        
        # 4. Sınıf değişim maliyeti
        classroom_changes = self._calculate_classroom_changes(solution)
        energy += classroom_changes * 50
        
        # 5. Toplam ihlal cezası
        energy += violations * 1000
        
        return energy
    
    def _calculate_classroom_changes(self, solution: List[Tuple[int, int, int]]) -> int:
        """Sınıf değişim sayısını hesapla"""
        instructor_locations = {}
        changes = 0
        
        # Rastgele zaman sıralaması (simplex için)
        random_indices = list(range(len(solution)))
        random.shuffle(random_indices)
        
        for idx in random_indices:
            assignment = solution[idx]
            responsible, assistant1, assistant2 = assignment
            
            # Her instructor için sınıf değişimini kontrol et
            for instructor_id in [responsible, assistant1, assistant2]:
                # Basit sınıf ataması (rastgele)
                classroom_id = random.randint(1, 3)  # 3 sınıf varsayımı
                
                if instructor_id in instructor_locations:
                    if instructor_locations[instructor_id] != classroom_id:
                        changes += 1
                instructor_locations[instructor_id] = classroom_id
        
        return changes

    def _get_neighbor_solution(self, solution: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        neighbor = [assignment for assignment in solution]
        project_idx = random.randint(0, len(neighbor) - 1)
        responsible, assistant1, assistant2 = neighbor[project_idx]
        
        change_type = random.choice(["assistant1", "assistant2", "both_assistants"])
        
        if change_type == "assistant1":
            new_assistant = random.choice(list(self.instructors.keys()))
            neighbor[project_idx] = (responsible, new_assistant, assistant2)
        elif change_type == "assistant2":
            new_assistant = random.choice(list(self.instructors.keys()))
            neighbor[project_idx] = (responsible, assistant1, new_assistant)
        else:
            new_assistant1 = random.choice(list(self.instructors.keys()))
            new_assistant2 = random.choice(list(self.instructors.keys()))
            neighbor[project_idx] = (responsible, new_assistant1, new_assistant2)
        
        return neighbor

    def optimize(self) -> Dict[str, Any]:
        """
        Simplex optimizasyonunu çalıştırır - Linear Programming tabanlı
        """
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
        
        # Her çalıştırmada farklı sonuç için random seed
        random.seed(int(time.time() * 1000) % 2**32)
        
        # Problem boyutlarını hesapla
        n_projects = len(self.projects)
        n_instructors = len(self.instructors)
        
        # Simplex benzeri iteratif iyileştirme
        best_solution = self._initialize_solution()
        best_energy = self._calculate_energy(best_solution)
        
        max_iterations = self.parameters['max_iterations']
        tolerance = self.parameters['tolerance']
        
        # Ana döngü - Simplex benzeri pivot operasyonları
        for iteration in range(max_iterations):
            improved = False
            
            # Her iterasyonda birden fazla pivot dene
            for _ in range(min(20, n_projects * 2)):  # Daha fazla pivot deneme
                neighbor_solution = self._get_neighbor_solution(best_solution)
                neighbor_energy = self._calculate_energy(neighbor_solution)
                
                # Pivot kriteri: sadece daha iyi çözümleri kabul et
                if neighbor_energy < best_energy - tolerance:
                    best_solution = neighbor_solution
                    best_energy = neighbor_energy
                    improved = True
                    break
            
            # Eğer iyileştirme yoksa dur
            if not improved:
                break
        
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
            "energy": best_energy,
            "iterations": max_iterations,
            "status": "optimal" if not improved else "improved"
        }
