import random
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from app.algorithms.base import BaseAlgorithm

@dataclass
class Individual:
    """Genetik algoritma için birey sınıfı"""
    chromosome: List[int]  # Atama matrisi (düzleştirilmiş)
    fitness: float = 0.0

class GeneticAlgorithm(BaseAlgorithm):
    def __init__(
        self,
        projects=None,
        instructors=None,
        population_size=100,
        generations=50,
        mutation_rate=0.1,
        crossover_rate=0.8
    ):
        super().__init__(projects, instructors, {
            'population_size': population_size,
            'generations': generations,
            'mutation_rate': mutation_rate,
            'crossover_rate': crossover_rate
        })
        
        if self.projects and self.instructors:
            # Problem boyutlarını hesapla
            self.num_projects = len(self.projects)
            self.num_instructors = len(self.instructors)
            self.chromosome_length = self.num_projects * 3  # Her proje için 3 öğretim elemanı
            
            # Başlangıç popülasyonunu oluştur
            self.population = self._initialize_population()

    def _initialize_population(self) -> List[Individual]:
        """Rastgele başlangıç popülasyonu oluştur"""
        population = []
        for _ in range(self.parameters['population_size']):
            chromosome = []
            for p_id in self.projects:
                # Sorumlu hoca (mutlaka olmalı)
                responsible = random.choice([i_id for i_id, i in self.instructors.items() 
                                          if i["type"] == "professor"])
                chromosome.append(responsible)
                
                # 2 yardımcı öğretim elemanı
                assistants = random.sample(list(self.instructors.keys()), 2)
                chromosome.extend(assistants)
            
            population.append(Individual(chromosome=chromosome))
        
        return population

    def _calculate_fitness(self, individual: Individual) -> float:
        """Bireyin uygunluk değerini hesapla"""
        fitness = 0.0
        violations = 0
        
        # Her proje için kuralları kontrol et
        for i in range(0, len(individual.chromosome), 3):
            project_assignments = individual.chromosome[i:i+3]
            responsible = project_assignments[0]
            assistants = project_assignments[1:]
            
            # Kural 1: Sorumlu hoca kontrolü
            if self.instructors[responsible]["type"] != "professor":
                violations += 1
            
            # Kural 2: Bitirme projesi için en az 2 hoca kontrolü
            project_id = list(self.projects.keys())[i//3]
            if self.projects[project_id]["type"] == "final":
                professor_count = sum(1 for a in project_assignments 
                                   if self.instructors[a]["type"] == "professor")
                if professor_count < 2:
                    violations += 1
            
            # Kural 3: Yük dengesi kontrolü
            instructor_loads = {}
            for a in project_assignments:
                instructor_loads[a] = instructor_loads.get(a, 0) + 1
            
            # Yük dengesizliği cezası
            load_std = np.std(list(instructor_loads.values()))
            fitness -= load_std
        
        # Kural ihlalleri için ceza
        fitness -= violations * 100
        
        return fitness

    def _select_parents(self) -> Tuple[Individual, Individual]:
        """Turnuva seçimi ile ebeveynleri seç"""
        def tournament():
            candidates = random.sample(self.population, 3)
            return max(candidates, key=lambda x: x.fitness)
        
        parent1 = tournament()
        parent2 = tournament()
        return parent1, parent2

    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """İki nokta çaprazlama uygula"""
        if random.random() > self.parameters['crossover_rate']:
            return parent1, parent2
        
        point1, point2 = sorted(random.sample(range(self.chromosome_length), 2))
        
        child1_chromosome = parent1.chromosome[:point1] + \
                          parent2.chromosome[point1:point2] + \
                          parent1.chromosome[point2:]
                          
        child2_chromosome = parent2.chromosome[:point1] + \
                          parent1.chromosome[point1:point2] + \
                          parent2.chromosome[point2:]
        
        return Individual(child1_chromosome), Individual(child2_chromosome)

    def _mutate(self, individual: Individual):
        """Mutasyon uygula"""
        for i in range(len(individual.chromosome)):
            if random.random() < self.parameters['mutation_rate']:
                # Proje pozisyonuna göre mutasyon uygula
                position = i % 3
                if position == 0:  # Sorumlu hoca
                    individual.chromosome[i] = random.choice(
                        [i_id for i_id, i in self.instructors.items() 
                         if i["type"] == "professor"]
                    )
                else:  # Yardımcı öğretim elemanı
                    individual.chromosome[i] = random.choice(list(self.instructors.keys()))

    def optimize(self) -> Dict[str, Any]:
        """Genetik algoritmayı çalıştır"""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        # Initialize population if not already done
        if not hasattr(self, 'population'):
            # Problem boyutlarını hesapla
            self.num_projects = len(self.projects)
            self.num_instructors = len(self.instructors)
            self.chromosome_length = self.num_projects * 3  # Her proje için 3 öğretim elemanı
            # Başlangıç popülasyonunu oluştur
            self.population = self._initialize_population()
            
        best_individual = None
        best_fitness = float('-inf')
        
        # Her nesil için
        for generation in range(self.parameters['generations']):
            # Uygunluk değerlerini hesapla
            for individual in self.population:
                individual.fitness = self._calculate_fitness(individual)
                
                # En iyi bireyi güncelle
                if individual.fitness > best_fitness:
                    best_fitness = individual.fitness
                    best_individual = individual
            
            # Yeni nesil oluştur
            new_population = []
            while len(new_population) < self.parameters['population_size']:
                # Ebeveynleri seç
                parent1, parent2 = self._select_parents()
                
                # Çaprazlama
                child1, child2 = self._crossover(parent1, parent2)
                
                # Mutasyon
                self._mutate(child1)
                self._mutate(child2)
                
                new_population.extend([child1, child2])
            
            # Popülasyonu güncelle
            self.population = new_population[:self.parameters['population_size']]
        
        # Sonuçları hazırla
        assignments = {}
        for i in range(0, len(best_individual.chromosome), 3):
            project_id = list(self.projects.keys())[i//3]
            assignments[project_id] = {
                "responsible": best_individual.chromosome[i],
                "assistants": best_individual.chromosome[i+1:i+3]
            }
        
        return {
            "assignments": assignments,
            "fitness": best_fitness
        } 