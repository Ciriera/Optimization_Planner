import random
import math
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class SimulatedAnnealingAlgorithm(BaseAlgorithm):
    def __init__(
        self,
        projects=None,
        instructors=None,
        initial_temperature=100.0,
        cooling_rate=0.01,
        iterations=1000,
        acceptance_probability=0.7
    ):
        super().__init__(projects, instructors, {
            'initial_temperature': initial_temperature,
            'cooling_rate': cooling_rate,
            'iterations': iterations,
            'acceptance_probability': acceptance_probability
        })
        
    def _initialize_solution(self) -> List[Tuple[int, int, int]]:
        """Başlangıç çözümünü oluştur"""
        solution = []
        for p_id in self.projects:
            # Sorumlu hoca (mutlaka olmalı)
            professor_ids = [i_id for i_id, i in self.instructors.items() 
                           if i["type"] == "professor"]
            if not professor_ids:  # Eğer hoca yoksa
                professor_ids = list(self.instructors.keys())
                
            responsible = random.choice(professor_ids)
            
            # 2 yardımcı öğretim elemanı
            assistants = random.sample(list(self.instructors.keys()), min(2, len(self.instructors)))
            if len(assistants) < 2:  # Eğer yeterli sayıda öğretim elemanı yoksa
                assistants.extend([random.choice(list(self.instructors.keys()))] * (2 - len(assistants)))
            
            solution.append((responsible, assistants[0], assistants[1]))
        
        return solution

    def _calculate_energy(self, solution: List[Tuple[int, int, int]]) -> float:
        """Çözümün enerji değerini hesapla (daha düşük daha iyidir)"""
        energy = 0.0
        violations = 0
        project_ids = list(self.projects.keys())
        
        # Geçiş matrisi: her öğretim elemanı için sınıf geçişleri
        transitions = {}
        
        # Her proje için kuralları kontrol et
        for i, (responsible, assistant1, assistant2) in enumerate(solution):
            project_id = project_ids[i]
            project_type = self.projects[project_id]["type"]
            
            # Öğretim elemanlarını bir arada tut
            instructors = [responsible, assistant1, assistant2]
            
            # Kural 1: Sorumlu hoca kontrolü
            if responsible not in self.instructors or self.instructors[responsible].get("type") != "professor":
                violations += 1
            
            # Kural 2: Bitirme projesi için en az 2 hoca kontrolü
            if project_type == "final":
                professor_count = sum(1 for a in instructors 
                                  if a in self.instructors and self.instructors[a].get("type") == "professor")
                if professor_count < 2:
                    violations += 1
            
            # Kural 3: Yük dengesi kontrolü
            for a in instructors:
                if a not in transitions:
                    transitions[a] = {}
                
                # Sınıf değişimlerini kaydet
                classroom = self.projects[project_id].get("classroom")
                if classroom:
                    if classroom not in transitions[a]:
                        transitions[a][classroom] = 0
                    transitions[a][classroom] += 1
        
        # Sınıf geçişlerini cezalandır (hocalar için daha fazla)
        for a, classrooms in transitions.items():
            if len(classrooms) > 1:
                penalty = 2.0 if self.instructors[a]["type"] == "professor" else 1.0
                energy += (len(classrooms) - 1) * penalty
        
        # Yük dağılımını cezalandır
        instructor_loads = {}
        for responsible, assistant1, assistant2 in solution:
            for a in [responsible, assistant1, assistant2]:
                if a not in instructor_loads:
                    instructor_loads[a] = 0
                instructor_loads[a] += 1
        
        # Yük dengesizliği cezası
        energy += np.std(list(instructor_loads.values())) * 5
        
        # Kural ihlalleri için ceza
        energy += violations * 100
        
        return energy

    def _get_neighbor_solution(self, solution: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Komşu çözüm oluştur"""
        # Çözümün kopyasını oluştur
        neighbor = solution.copy()
        
        # Rastgele bir proje seç
        project_idx = random.randrange(len(neighbor))
        
        # Rastgele bir değişiklik türü seç
        change_type = random.randrange(3)
        
        if change_type == 0:  # Sorumlu hocayı değiştir
            responsible, assistant1, assistant2 = neighbor[project_idx]
            professor_ids = [i_id for i_id, i in self.instructors.items() 
                           if i["type"] == "professor"]
            if professor_ids:
                new_responsible = random.choice(professor_ids)
                neighbor[project_idx] = (new_responsible, assistant1, assistant2)
        
        elif change_type == 1:  # İlk yardımcıyı değiştir
            responsible, assistant1, assistant2 = neighbor[project_idx]
            new_assistant = random.choice(list(self.instructors.keys()))
            neighbor[project_idx] = (responsible, new_assistant, assistant2)
        
        else:  # İkinci yardımcıyı değiştir
            responsible, assistant1, assistant2 = neighbor[project_idx]
            new_assistant = random.choice(list(self.instructors.keys()))
            neighbor[project_idx] = (responsible, assistant1, new_assistant)
        
        return neighbor

    def optimize(self) -> Dict[str, Any]:
        """Tavlama benzetimi algoritmasını çalıştır"""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        # Başlangıç çözümünü oluştur
        current_solution = self._initialize_solution()
        current_energy = self._calculate_energy(current_solution)
        
        # En iyi çözümü izle
        best_solution = current_solution
        best_energy = current_energy
        
        # Algoritma parametreleri
        temperature = self.parameters['initial_temperature']
        cooling_rate = self.parameters['cooling_rate']
        
        # Ana döngü
        for iteration in range(self.parameters['iterations']):
            # Sıcaklık çok düşükse durdur
            if temperature < 0.1:
                break
                
            # Komşu çözüm oluştur
            neighbor_solution = self._get_neighbor_solution(current_solution)
            neighbor_energy = self._calculate_energy(neighbor_solution)
            
            # Enerji değişimini hesapla
            energy_diff = neighbor_energy - current_energy
            
            # Yeni çözümü kabul et veya reddet
            if (energy_diff <= 0) or (random.random() < self.parameters['acceptance_probability'] * 
                                   math.exp(-energy_diff / temperature)):
                current_solution = neighbor_solution
                current_energy = neighbor_energy
                
                # En iyi çözümü güncelle
                if current_energy < best_energy:
                    best_solution = current_solution
                    best_energy = current_energy
            
            # Sıcaklığı güncelle
            temperature *= (1 - cooling_rate)
        
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
            "energy": best_energy
        } 