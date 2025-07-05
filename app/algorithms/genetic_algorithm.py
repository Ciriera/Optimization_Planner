"""
Genetik algoritma sınıfı.
"""
from typing import Dict, Any, List
import random

from app.algorithms.base import OptimizationAlgorithm

class GeneticAlgorithm(OptimizationAlgorithm):
    """
    Genetik algoritma sınıfı.
    Genetik algoritma kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Genetik algoritma başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        self.population_size = params.get("population_size", 100)
        self.generations = params.get("generations", 100)
        self.mutation_rate = params.get("mutation_rate", 0.1)
        self.crossover_rate = params.get("crossover_rate", 0.8)
        self.population = []
        self.best_solution = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Genetik algoritmayı başlangıç popülasyonu ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Başlangıç popülasyonunu oluştur
        self.population = []
        for _ in range(self.population_size):
            solution = self._create_random_solution()
            self.population.append(solution)
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genetik algoritma optimizasyonunu çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Nesiller boyunca evrim
        for generation in range(self.generations):
            # Uygunluk değerlendirmesi
            fitness_scores = []
            for solution in self.population:
                fitness = self.evaluate_fitness(solution)
                fitness_scores.append((solution, fitness))
            
            # En iyi çözümü bul
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            self.best_solution = fitness_scores[0][0]
            self.fitness_score = fitness_scores[0][1]
            
            # Yeni popülasyon oluştur
            new_population = []
            
            # Elitizm: En iyi çözümü doğrudan aktar
            new_population.append(self.best_solution)
            
            # Çaprazlama ve mutasyon
            while len(new_population) < self.population_size:
                # Seçim
                parent1 = self._selection(fitness_scores)
                parent2 = self._selection(fitness_scores)
                
                # Çaprazlama
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                
                # Mutasyon
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2)
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            self.population = new_population
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.fitness_score,
            "generation": self.generations
        }
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
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
            return 0.0
        
        # Sınıf değişim sayısını minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        score -= instructor_changes * 10
        
        # Yük dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        score += load_balance * 20
        
        return score
    
    def _create_random_solution(self) -> Dict[str, Any]:
        """
        Rastgele bir çözüm oluşturur.
        
        Returns:
            Dict[str, Any]: Rastgele çözüm.
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
    
    def _selection(self, fitness_scores: List[tuple]) -> Dict[str, Any]:
        """
        Turnuva seçimi ile bir ebeveyn seçer.
        
        Args:
            fitness_scores: Çözüm ve uygunluk puanı çiftleri.
            
        Returns:
            Dict[str, Any]: Seçilen çözüm.
        """
        # Turnuva seçimi
        tournament_size = 3
        tournament = random.sample(fitness_scores, min(tournament_size, len(fitness_scores)))
        tournament.sort(key=lambda x: x[1], reverse=True)
        return tournament[0][0]
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> tuple:
        """
        İki ebeveyn arasında çaprazlama yapar.
        
        Args:
            parent1: Birinci ebeveyn.
            parent2: İkinci ebeveyn.
            
        Returns:
            tuple: İki çocuk çözüm.
        """
        # Tek noktalı çaprazlama
        if not parent1 or not parent2:
            return parent1, parent2
        
        crossover_point = random.randint(1, min(len(parent1), len(parent2)) - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return child1, child2
    
    def _mutate(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Çözümde mutasyon yapar.
        
        Args:
            solution: Mutasyona uğrayacak çözüm.
            
        Returns:
            Dict[str, Any]: Mutasyona uğramış çözüm.
        """
        if not solution:
            return solution
        
        # Rastgele bir atamayı değiştir
        mutation_index = random.randint(0, len(solution) - 1)
        
        # Sınıf veya zaman dilimini değiştir
        if random.random() < 0.5 and self.classrooms:
            solution[mutation_index]["classroom_id"] = random.choice(self.classrooms)["id"]
        elif self.timeslots:
            solution[mutation_index]["timeslot_id"] = random.choice(self.timeslots)["id"]
        
        return solution
    
    def _is_valid_solution(self, solution: Dict[str, Any]) -> bool:
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
    
    def _count_instructor_classroom_changes(self, solution: Dict[str, Any]) -> int:
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
    
    def _calculate_load_balance(self, solution: Dict[str, Any]) -> float:
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