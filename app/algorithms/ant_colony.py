"""
Karınca Kolonisi Optimizasyonu algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np

from app.algorithms.base import OptimizationAlgorithm

class AntColony(OptimizationAlgorithm):
    """
    Karınca Kolonisi Optimizasyonu algoritması sınıfı.
    Karınca kolonisi optimizasyonu kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Karınca Kolonisi Optimizasyonu algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.n_ants = params.get("n_ants", 30)
        self.n_iterations = params.get("n_iterations", 100)
        self.alpha = params.get("alpha", 1.0)  # Feromon önem faktörü
        self.beta = params.get("beta", 2.0)  # Sezgisel bilgi önem faktörü
        self.evaporation_rate = params.get("evaporation_rate", 0.5)
        self.q0 = params.get("q0", 0.9)  # Keşif-sömürü dengesi parametresi
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Karınca Kolonisi Optimizasyonu algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Feromon matrisini başlat
        self.n_projects = len(self.projects)
        self.n_classrooms = len(self.classrooms)
        self.n_timeslots = len(self.timeslots)
        
        # Feromon matrisi: [proje][sınıf][zaman dilimi]
        self.pheromones = np.ones((self.n_projects, self.n_classrooms, self.n_timeslots))
        
        # Sezgisel bilgi matrisi: [proje][sınıf][zaman dilimi]
        self.heuristic = np.ones((self.n_projects, self.n_classrooms, self.n_timeslots))
        
        # Sezgisel bilgiyi hesapla
        self._calculate_heuristic()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Karınca Kolonisi Optimizasyonu algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # İterasyon döngüsü
        for iteration in range(self.n_iterations):
            # Tüm karıncalar için çözüm oluştur
            ant_solutions = []
            ant_fitnesses = []
            
            for ant in range(self.n_ants):
                # Karınca çözümü oluştur
                solution = self._construct_solution()
                
                # Çözümün uygunluğunu değerlendir
                fitness = self.evaluate_fitness(solution)
                
                ant_solutions.append(solution)
                ant_fitnesses.append(fitness)
                
                # En iyi çözümü güncelle
                if fitness > self.best_fitness:
                    self.best_solution = solution
                    self.best_fitness = fitness
            
            # Feromon güncellemesi
            self._update_pheromones(ant_solutions, ant_fitnesses)
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": self.n_iterations
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
    
    def _calculate_heuristic(self) -> None:
        """
        Sezgisel bilgi matrisini hesaplar.
        """
        # Örnek: Sınıf kapasitesi ve zaman dilimi uygunluğuna göre sezgisel bilgi
        for p_idx, project in enumerate(self.projects):
            for c_idx, classroom in enumerate(self.classrooms):
                for t_idx, timeslot in enumerate(self.timeslots):
                    # Sınıf kapasitesi uygunluğu
                    capacity_factor = 1.0
                    if hasattr(project, "student_count") and hasattr(classroom, "capacity"):
                        if project.student_count <= classroom.capacity:
                            capacity_factor = 2.0
                    
                    # Zaman dilimi uygunluğu
                    time_factor = 1.0
                    if hasattr(project, "preferred_time") and hasattr(timeslot, "start_time"):
                        if project.preferred_time == timeslot.start_time:
                            time_factor = 2.0
                    
                    self.heuristic[p_idx, c_idx, t_idx] = capacity_factor * time_factor
    
    def _construct_solution(self) -> List[Dict[str, Any]]:
        """
        Karınca çözümü oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Karınca çözümü.
        """
        solution = []
        
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        # Projeleri rastgele sırala
        project_indices = list(range(self.n_projects))
        random.shuffle(project_indices)
        
        for p_idx in project_indices:
            project = self.projects[p_idx]
            
            # Feromon ve sezgisel bilgiye göre sınıf ve zaman dilimi seç
            c_idx, t_idx = self._select_classroom_timeslot(p_idx, assigned_classrooms_timeslots)
            
            if c_idx is not None and t_idx is not None:
                classroom = self.classrooms[c_idx]
                timeslot = self.timeslots[t_idx]
                
                # Sorumlu öğretim üyesi
                responsible_id = project.get("responsible_id", None)
                instructors = [responsible_id] if responsible_id else []
                
                # Rastgele 1-2 yardımcı katılımcı ekle
                available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
                if available_instructors:
                    assistant_count = random.randint(1, 2)
                    assistants = random.sample(available_instructors, min(assistant_count, len(available_instructors)))
                    for assistant in assistants:
                        instructors.append(assistant.get("id"))
                
                # Atamayı ekle
                assignment = {
                    "project_id": project.get("id"),
                    "classroom_id": classroom.get("id"),
                    "timeslot_id": timeslot.get("id"),
                    "instructors": instructors
                }
                
                solution.append(assignment)
                assigned_projects.add(p_idx)
                assigned_classrooms_timeslots.add((c_idx, t_idx))
        
        return solution
    
    def _select_classroom_timeslot(self, p_idx: int, assigned_classrooms_timeslots: set) -> Tuple[int, int]:
        """
        Feromon ve sezgisel bilgiye göre sınıf ve zaman dilimi seçer.
        
        Args:
            p_idx: Proje indeksi.
            assigned_classrooms_timeslots: Atanmış (sınıf, zaman dilimi) çiftleri.
            
        Returns:
            Tuple[int, int]: Seçilen sınıf ve zaman dilimi indeksleri.
        """
        # Tüm olası sınıf-zaman dilimi çiftlerini oluştur
        candidates = []
        probabilities = []
        
        for c_idx in range(self.n_classrooms):
            for t_idx in range(self.n_timeslots):
                if (c_idx, t_idx) not in assigned_classrooms_timeslots:
                    candidates.append((c_idx, t_idx))
                    
                    # Feromon ve sezgisel bilgiye göre olasılık hesapla
                    pheromone = self.pheromones[p_idx, c_idx, t_idx]
                    heuristic = self.heuristic[p_idx, c_idx, t_idx]
                    
                    probability = (pheromone ** self.alpha) * (heuristic ** self.beta)
                    probabilities.append(probability)
        
        if not candidates:
            return None, None
        
        # Olasılıkları normalize et
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / len(candidates) for _ in candidates]
        
        # Keşif-sömürü stratejisi
        if random.random() < self.q0:
            # Sömürü: En yüksek olasılıklı seçeneği seç
            best_idx = probabilities.index(max(probabilities))
            return candidates[best_idx]
        else:
            # Keşif: Olasılıklara göre seç
            selected_idx = random.choices(range(len(candidates)), probabilities)[0]
            return candidates[selected_idx]
    
    def _update_pheromones(self, solutions: List[List[Dict[str, Any]]], fitnesses: List[float]) -> None:
        """
        Feromon matrisini günceller.
        
        Args:
            solutions: Karınca çözümleri.
            fitnesses: Çözümlerin uygunluk puanları.
        """
        # Feromon buharlaşması
        self.pheromones *= (1 - self.evaporation_rate)
        
        # Karınca çözümlerine göre feromon güncelleme
        for solution, fitness in zip(solutions, fitnesses):
            if fitness <= 0:
                continue
            
            # Fitness değerine göre feromon artışı
            delta = fitness / 100.0  # Normalizasyon faktörü
            
            for assignment in solution:
                p_idx = next((i for i, p in enumerate(self.projects) if p.get("id") == assignment["project_id"]), None)
                c_idx = next((i for i, c in enumerate(self.classrooms) if c.get("id") == assignment["classroom_id"]), None)
                t_idx = next((i for i, t in enumerate(self.timeslots) if t.get("id") == assignment["timeslot_id"]), None)
                
                if p_idx is not None and c_idx is not None and t_idx is not None:
                    self.pheromones[p_idx, c_idx, t_idx] += delta
        
        # Feromon sınırlarını kontrol et
        self.pheromones = np.clip(self.pheromones, 0.1, 10.0)
    
    def _is_valid_solution(self, solution: List[Dict[str, Any]]) -> bool:
        """
        Çözümün geçerli olup olmadığını kontrol eder.
        
        Args:
            solution: Kontrol edilecek çözüm.
            
        Returns:
            bool: Çözüm geçerliyse True, değilse False.
        """
        if not solution:
            return False
        
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        for assignment in solution:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Bir proje birden fazla kez atanmamalı
            if project_id in assigned_projects:
                return False
            
            # Bir sınıf-zaman dilimi çifti birden fazla kez atanmamalı
            if (classroom_id, timeslot_id) in assigned_classrooms_timeslots:
                return False
            
            assigned_projects.add(project_id)
            assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
        
        return True
    
    def _count_instructor_classroom_changes(self, solution: List[Dict[str, Any]]) -> int:
        """
        Öğretim üyelerinin sınıf değişim sayısını hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            int: Toplam sınıf değişim sayısı
        """
        if not solution:
            return 0
        
        # Öğretim üyesi başına sınıf değişim sayısını hesapla
        instructor_locations = {}
        changes = 0
        
        # Zaman dilimine göre sırala
        sorted_solution = sorted(solution, key=lambda x: x["timeslot_id"])
        
        for assignment in sorted_solution:
            classroom_id = assignment["classroom_id"]
            for instructor_id in assignment["instructors"]:
                if instructor_id in instructor_locations:
                    if instructor_locations[instructor_id] != classroom_id:
                        changes += 1
                        instructor_locations[instructor_id] = classroom_id
                else:
                    instructor_locations[instructor_id] = classroom_id
        
        return changes
    
    def _calculate_load_balance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Öğretim üyesi yük dengesini hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            float: Yük dengesi skoru (0-1 arası, 1 en iyi)
        """
        if not solution:
            return 0.0
        
        # Öğretim üyesi başına atama sayısını hesapla
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment["instructors"]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        # Yük dengesini hesapla (Gini katsayısı)
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
        
        # Gini katsayısı 0 (tam eşitlik) ile 1 (tam eşitsizlik) arasındadır
        # Biz dengeyi istediğimiz için 1 - gini döndürüyoruz
        return 1.0 - gini 