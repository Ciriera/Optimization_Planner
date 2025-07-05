"""
Benzetimli Tavlama algoritması sınıfı.
"""
import random
import math
from typing import Dict, Any, List, Tuple
import numpy as np

from app.algorithms.base import OptimizationAlgorithm

class SimulatedAnnealing(OptimizationAlgorithm):
    """
    Benzetimli Tavlama algoritması sınıfı.
    Benzetimli Tavlama kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Benzetimli Tavlama algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.initial_temperature = params.get("initial_temperature", 1000.0)
        self.cooling_rate = params.get("cooling_rate", 0.95)
        self.iterations_per_temp = params.get("iterations_per_temp", 100)
        self.min_temperature = params.get("min_temperature", 1.0)
        self.temperature = self.initial_temperature
        self.current_solution = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Benzetimli Tavlama algoritmasını başlangıç çözümü ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Başlangıç çözümünü oluştur
        self.current_solution = self._create_random_solution()
        self.fitness_score = self.evaluate_fitness(self.current_solution)
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Benzetimli Tavlama optimizasyonunu çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        temperature = self.initial_temperature
        current_solution = self.current_solution
        current_fitness = self.fitness_score
        best_solution = current_solution
        best_fitness = current_fitness
        
        # Sıcaklık düşene kadar devam et
        while temperature > self.min_temperature:
            for _ in range(self.iterations_per_temp):
                # Komşu çözüm oluştur
                neighbor = self._get_neighbor_solution(current_solution)
                neighbor_fitness = self.evaluate_fitness(neighbor)
                
                # Komşu çözümü kabul et veya reddet
                if self._acceptance_probability(current_fitness, neighbor_fitness, temperature) > random.random():
                    current_solution = neighbor
                    current_fitness = neighbor_fitness
                    
                    # En iyi çözümü güncelle
                    if current_fitness > best_fitness:
                        best_solution = current_solution
                        best_fitness = current_fitness
            
            # Sıcaklığı düşür
            temperature *= self.cooling_rate
        
        # Sonucu döndür
        return {
            "schedule": best_solution,
            "fitness": best_fitness,
            "temperature": self.initial_temperature,
            "cooling_rate": self.cooling_rate
        }
    
    def evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
        """
        Verilen çözümün uygunluğunu değerlendirir.
        
        Args:
            solution: Değerlendirilecek çözüm.
            
        Returns:
            float: Uygunluk puanı.
        """
        # Basit bir fitness fonksiyonu örneği
        score = 0.0
        
        # Çözüm geçerli mi?
        if not self._is_valid_solution(solution):
            return float('-inf')
        
        # Sınıf değişim sayısını minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        score -= instructor_changes * 10
        
        # Yük dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        score += load_balance * 20
        
        return score
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """
        Rastgele bir çözüm oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Rastgele çözüm.
        """
        solution = []
        
        # Her proje için rastgele bir sınıf ve zaman dilimi ata
        for project in self.projects:
            classroom = random.choice(self.classrooms) if self.classrooms else None
            timeslot = random.choice(self.timeslots) if self.timeslots else None
            
            if classroom and timeslot:
                assignment = {
                    "project_id": project["id"],
                    "classroom_id": classroom["id"],
                    "timeslot_id": timeslot["id"],
                    "instructors": [project["responsible_id"]]
                }
                
                # Rastgele 1-2 yardımcı katılımcı ekle
                available_instructors = [i for i in self.instructors if i["id"] != project["responsible_id"]]
                if available_instructors:
                    assistant_count = random.randint(1, 2)
                    assistants = random.sample(available_instructors, min(assistant_count, len(available_instructors)))
                    for assistant in assistants:
                        assignment["instructors"].append(assistant["id"])
                
                solution.append(assignment)
        
        return solution
    
    def _get_neighbor_solution(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Komşu çözüm oluşturur.
        
        Args:
            solution: Mevcut çözüm.
            
        Returns:
            List[Dict[str, Any]]: Komşu çözüm.
        """
        # Çözümü kopyala
        neighbor = [assignment.copy() for assignment in solution]
        
        # Rastgele bir değişiklik yap
        if not neighbor:
            return neighbor
        
        change_type = random.choice(["classroom", "timeslot", "instructor"])
        assignment_index = random.randint(0, len(neighbor) - 1)
        
        if change_type == "classroom" and self.classrooms:
            # Sınıf değiştir
            new_classroom = random.choice(self.classrooms)
            neighbor[assignment_index]["classroom_id"] = new_classroom["id"]
        
        elif change_type == "timeslot" and self.timeslots:
            # Zaman dilimi değiştir
            new_timeslot = random.choice(self.timeslots)
            neighbor[assignment_index]["timeslot_id"] = new_timeslot["id"]
        
        elif change_type == "instructor" and len(self.instructors) > 1:
            # Yardımcı katılımcı değiştir
            assignment = neighbor[assignment_index]
            responsible_id = assignment["instructors"][0]  # İlk katılımcı her zaman sorumlu kişidir
            
            # Mevcut yardımcı katılımcıları kaldır
            assignment["instructors"] = [responsible_id]
            
            # Yeni yardımcı katılımcılar ekle
            available_instructors = [i for i in self.instructors if i["id"] != responsible_id]
            if available_instructors:
                assistant_count = random.randint(1, 2)
                assistants = random.sample(available_instructors, min(assistant_count, len(available_instructors)))
                for assistant in assistants:
                    assignment["instructors"].append(assistant["id"])
        
        return neighbor
    
    def _acceptance_probability(self, current_fitness: float, neighbor_fitness: float, temperature: float) -> float:
        """
        Kötü bir çözümü kabul etme olasılığını hesaplar.
        
        Args:
            current_fitness: Mevcut çözümün uygunluk puanı.
            neighbor_fitness: Komşu çözümün uygunluk puanı.
            temperature: Mevcut sıcaklık.
            
        Returns:
            float: Kabul olasılığı (0-1 arası).
        """
        # Daha iyi çözümü her zaman kabul et
        if neighbor_fitness > current_fitness:
            return 1.0
        
        # Kötü çözümü sıcaklığa bağlı olarak kabul et
        delta = neighbor_fitness - current_fitness
        return math.exp(delta / temperature)
    
    def _is_valid_solution(self, solution: List[Dict[str, Any]]) -> bool:
        """
        Çözümün geçerli olup olmadığını kontrol eder.
        
        Args:
            solution: Kontrol edilecek çözüm.
            
        Returns:
            bool: Çözüm geçerli ise True, değilse False.
        """
        # Çakışma kontrolü
        assignments = {}
        
        for assignment in solution:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Aynı sınıf ve zaman diliminde başka bir atama var mı?
            key = f"{classroom_id}_{timeslot_id}"
            if key in assignments:
                return False
            
            assignments[key] = True
        
        return True
    
    def _count_instructor_classroom_changes(self, solution: List[Dict[str, Any]]) -> int:
        """
        Öğretim üyelerinin sınıf değişim sayısını hesaplar.
        
        Args:
            solution: Değerlendirilecek çözüm.
            
        Returns:
            int: Sınıf değişim sayısı.
        """
        instructor_schedule = {}
        changes = 0
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_schedule:
                    instructor_schedule[instructor_id] = []
                
                instructor_schedule[instructor_id].append(assignment)
        
        # Her öğretim üyesi için sınıf değişim sayısını hesapla
        for instructor_id, assignments in instructor_schedule.items():
            # Zaman dilimine göre sırala
            assignments.sort(key=lambda x: x.get("timeslot_id"))
            
            # Ardışık atamalar arasında sınıf değişimi var mı?
            for i in range(1, len(assignments)):
                if assignments[i].get("classroom_id") != assignments[i-1].get("classroom_id"):
                    changes += 1
        
        return changes
    
    def _calculate_load_balance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Öğretim üyeleri arasındaki yük dengesini hesaplar.
        
        Args:
            solution: Değerlendirilecek çözüm.
            
        Returns:
            float: Yük dengesi puanı (0-1 arası).
        """
        instructor_loads = {}
        
        # Her öğretim üyesi için yük hesapla
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        # Standart sapma hesapla
        loads = list(instructor_loads.values())
        mean = sum(loads) / len(loads)
        variance = sum((load - mean) ** 2 for load in loads) / len(loads)
        std_dev = variance ** 0.5
        
        # Standart sapma ne kadar düşükse, denge o kadar iyi
        if mean == 0:
            return 1.0
        
        # Normalize edilmiş denge puanı (0-1 arası)
        balance = max(0, 1 - (std_dev / mean))
        
        return balance 