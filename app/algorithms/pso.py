"""
Particle Swarm Optimization (PSO) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy

from app.algorithms.base import OptimizationAlgorithm

class PSO(OptimizationAlgorithm):
    """
    Particle Swarm Optimization (PSO) algoritması sınıfı.
    Parçacık Sürü Optimizasyonu kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        PSO algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.n_particles = params.get("n_particles", 30)
        self.n_iterations = params.get("n_iterations", 100)
        self.w = params.get("w", 0.7)  # Eylemsizlik ağırlığı
        self.c1 = params.get("c1", 1.5)  # Bilişsel katsayı
        self.c2 = params.get("c2", 1.5)  # Sosyal katsayı
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        PSO algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Parçacıkları başlat
        self.particles = self._initialize_particles()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PSO algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # İterasyon döngüsü
        for iteration in range(self.n_iterations):
            # Her parçacık için
            for particle in self.particles:
                # Parçacığın mevcut çözümünü değerlendir
                current_fitness = self.evaluate_fitness(particle["position"])
                
                # Parçacığın en iyi konumunu güncelle
                if current_fitness > particle["best_fitness"]:
                    particle["best_position"] = copy.deepcopy(particle["position"])
                    particle["best_fitness"] = current_fitness
                
                # Global en iyi çözümü güncelle
                if current_fitness > self.best_fitness:
                    self.best_solution = copy.deepcopy(particle["position"])
                    self.best_fitness = current_fitness
                
                # Parçacığın hızını ve konumunu güncelle
                self._update_velocity_and_position(particle)
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": self.n_iterations
        }
    
    def _initialize_particles(self) -> List[Dict[str, Any]]:
        """
        Parçacıkları başlatır.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç parçacıkları.
        """
        particles = []
        
        for _ in range(self.n_particles):
            # Rastgele bir çözüm oluştur
            position = self._create_random_solution()
            
            # Çözümün uygunluğunu değerlendir
            fitness = self.evaluate_fitness(position)
            
            # Parçacığı oluştur
            particle = {
                "position": position,
                "velocity": [],  # Başlangıçta boş hız
                "best_position": copy.deepcopy(position),
                "best_fitness": fitness
            }
            
            # Parçacığı ekle
            particles.append(particle)
            
            # Global en iyi çözümü güncelle
            if fitness > self.best_fitness:
                self.best_solution = copy.deepcopy(position)
                self.best_fitness = fitness
        
        return particles
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """
        Rastgele bir çözüm oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Rastgele çözüm.
        """
        solution = []
        
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        # Projeleri rastgele sırala
        projects = list(self.projects)
        random.shuffle(projects)
        
        for project in projects:
            # Rastgele bir sınıf ve zaman dilimi seç
            available_classrooms = list(self.classrooms)
            random.shuffle(available_classrooms)
            
            assigned = False
            
            for classroom in available_classrooms:
                if assigned:
                    break
                    
                available_timeslots = list(self.timeslots)
                random.shuffle(available_timeslots)
                
                for timeslot in available_timeslots:
                    if (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots:
                        # Sorumlu öğretim üyesi
                        responsible_id = project.get("responsible_id", None)
                        instructors = [responsible_id] if responsible_id else []
                        
                        # Rastgele 1-2 yardımcı katılımcı ekle
                        available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
                        if available_instructors:
                            # Proje tipine göre katılımcı sayısını belirle
                            if project.get("type") == "bitirme":
                                # Bitirme projesi için en az 2 hoca olmalı
                                hocas = [i for i in available_instructors if i.get("role") == "hoca"]
                                aras_gors = [i for i in available_instructors if i.get("role") == "aras_gor"]
                                
                                if len(hocas) > 0:
                                    # En az bir hoca ekle
                                    instructors.append(random.choice(hocas).get("id"))
                                    
                                    # Üçüncü kişi olarak hoca veya araş. gör. ekle
                                    if len(hocas) > 1 and random.random() > 0.5:
                                        instructors.append(random.choice(hocas).get("id"))
                                    elif aras_gors:
                                        instructors.append(random.choice(aras_gors).get("id"))
                            else:
                                # Ara proje için rastgele 2 kişi ekle
                                selected = random.sample(available_instructors, min(2, len(available_instructors)))
                                for instructor in selected:
                                    instructors.append(instructor.get("id"))
                        
                        # Atamayı ekle
                        assignment = {
                            "project_id": project.get("id"),
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id"),
                            "instructors": instructors
                        }
                        
                        solution.append(assignment)
                        assigned_projects.add(project.get("id"))
                        assigned_classrooms_timeslots.add((classroom.get("id"), timeslot.get("id")))
                        assigned = True
                        break
        
        return solution
    
    def _update_velocity_and_position(self, particle: Dict[str, Any]) -> None:
        """
        Parçacığın hızını ve konumunu günceller.
        
        Args:
            particle: Güncellenecek parçacık.
        """
        # İlk iterasyonda hız oluştur
        if not particle["velocity"]:
            particle["velocity"] = self._initialize_velocity()
        
        # Hızı güncelle
        new_velocity = []
        
        for v_op in particle["velocity"]:
            # Eylemsizlik bileşeni
            inertia = self.w * random.random()
            
            # Bilişsel bileşen (kişisel en iyi)
            cognitive = self.c1 * random.random()
            
            # Sosyal bileşen (global en iyi)
            social = self.c2 * random.random()
            
            # Yeni hız operasyonu
            if random.random() < inertia:
                new_velocity.append(v_op)
            
            # Bilişsel bileşen: Kişisel en iyiye doğru hareket
            if random.random() < cognitive:
                # Kişisel en iyiden bir operasyon seç
                if particle["best_position"]:
                    best_op = self._extract_operation(particle["best_position"])
                    if best_op:
                        new_velocity.append(best_op)
            
            # Sosyal bileşen: Global en iyiye doğru hareket
            if random.random() < social:
                # Global en iyiden bir operasyon seç
                if self.best_solution:
                    global_op = self._extract_operation(self.best_solution)
                    if global_op:
                        new_velocity.append(global_op)
        
        # Hızı sınırla
        max_velocity = 5
        if len(new_velocity) > max_velocity:
            new_velocity = random.sample(new_velocity, max_velocity)
        
        # Hızı güncelle
        particle["velocity"] = new_velocity
        
        # Konumu güncelle (operasyonları uygula)
        new_position = copy.deepcopy(particle["position"])
        
        for operation in particle["velocity"]:
            op_type = operation["type"]
            
            if op_type == "swap_classrooms":
                idx1, idx2 = operation["indices"]
                if idx1 < len(new_position) and idx2 < len(new_position):
                    new_position[idx1]["classroom_id"], new_position[idx2]["classroom_id"] = new_position[idx2]["classroom_id"], new_position[idx1]["classroom_id"]
            
            elif op_type == "swap_timeslots":
                idx1, idx2 = operation["indices"]
                if idx1 < len(new_position) and idx2 < len(new_position):
                    new_position[idx1]["timeslot_id"], new_position[idx2]["timeslot_id"] = new_position[idx2]["timeslot_id"], new_position[idx1]["timeslot_id"]
            
            elif op_type == "change_instructors":
                idx = operation["index"]
                instructors = operation["instructors"]
                if idx < len(new_position):
                    new_position[idx]["instructors"] = instructors
        
        # Çözümü düzelt (çakışmaları gider)
        new_position = self._repair_solution(new_position)
        
        # Konumu güncelle
        particle["position"] = new_position
    
    def _initialize_velocity(self) -> List[Dict[str, Any]]:
        """
        Başlangıç hızını oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç hız operasyonları.
        """
        velocity = []
        
        # Rastgele 1-3 operasyon oluştur
        n_operations = random.randint(1, 3)
        
        for _ in range(n_operations):
            # Rastgele bir operasyon tipi seç
            op_type = random.choice(["swap_classrooms", "swap_timeslots", "change_instructors"])
            
            if op_type == "swap_classrooms":
                # İki rastgele indeks seç
                idx1 = random.randint(0, max(0, len(self.projects) - 1))
                idx2 = random.randint(0, max(0, len(self.projects) - 1))
                while idx1 == idx2:
                    idx2 = random.randint(0, max(0, len(self.projects) - 1))
                
                velocity.append({
                    "type": "swap_classrooms",
                    "indices": (idx1, idx2)
                })
            
            elif op_type == "swap_timeslots":
                # İki rastgele indeks seç
                idx1 = random.randint(0, max(0, len(self.projects) - 1))
                idx2 = random.randint(0, max(0, len(self.projects) - 1))
                while idx1 == idx2:
                    idx2 = random.randint(0, max(0, len(self.projects) - 1))
                
                velocity.append({
                    "type": "swap_timeslots",
                    "indices": (idx1, idx2)
                })
            
            elif op_type == "change_instructors":
                # Rastgele bir indeks seç
                idx = random.randint(0, max(0, len(self.projects) - 1))
                
                # Rastgele katılımcılar seç
                project = random.choice(self.projects)
                responsible_id = project.get("responsible_id", None)
                instructors = [responsible_id] if responsible_id else []
                
                # Rastgele 1-2 yardımcı katılımcı ekle
                available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
                if available_instructors:
                    # Proje tipine göre katılımcı sayısını belirle
                    if project.get("type") == "bitirme":
                        # Bitirme projesi için en az 2 hoca olmalı
                        hocas = [i for i in available_instructors if i.get("role") == "hoca"]
                        aras_gors = [i for i in available_instructors if i.get("role") == "aras_gor"]
                        
                        if len(hocas) > 0:
                            # En az bir hoca ekle
                            instructors.append(random.choice(hocas).get("id"))
                            
                            # Üçüncü kişi olarak hoca veya araş. gör. ekle
                            if len(hocas) > 1 and random.random() > 0.5:
                                instructors.append(random.choice(hocas).get("id"))
                            elif aras_gors:
                                instructors.append(random.choice(aras_gors).get("id"))
                    else:
                        # Ara proje için rastgele 2 kişi ekle
                        selected = random.sample(available_instructors, min(2, len(available_instructors)))
                        for instructor in selected:
                            instructors.append(instructor.get("id"))
                
                velocity.append({
                    "type": "change_instructors",
                    "index": idx,
                    "instructors": instructors
                })
        
        return velocity
    
    def _extract_operation(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Çözümden rastgele bir operasyon çıkarır.
        
        Args:
            solution: Operasyon çıkarılacak çözüm.
            
        Returns:
            Dict[str, Any]: Çıkarılan operasyon.
        """
        if not solution:
            return None
        
        # Rastgele bir operasyon tipi seç
        op_type = random.choice(["swap_classrooms", "swap_timeslots", "change_instructors"])
        
        if op_type == "swap_classrooms" and len(solution) >= 2:
            # İki rastgele indeks seç
            idx1, idx2 = random.sample(range(len(solution)), 2)
            
            return {
                "type": "swap_classrooms",
                "indices": (idx1, idx2)
            }
        
        elif op_type == "swap_timeslots" and len(solution) >= 2:
            # İki rastgele indeks seç
            idx1, idx2 = random.sample(range(len(solution)), 2)
            
            return {
                "type": "swap_timeslots",
                "indices": (idx1, idx2)
            }
        
        elif op_type == "change_instructors" and len(solution) >= 1:
            # Rastgele bir indeks seç
            idx = random.randint(0, len(solution) - 1)
            
            # Mevcut katılımcıları al
            instructors = solution[idx].get("instructors", [])
            
            return {
                "type": "change_instructors",
                "index": idx,
                "instructors": instructors
            }
        
        return None
    
    def _repair_solution(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Çözümdeki çakışmaları giderir.
        
        Args:
            solution: Düzeltilecek çözüm.
            
        Returns:
            List[Dict[str, Any]]: Düzeltilmiş çözüm.
        """
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        # Geçerli atamaları koru
        valid_assignments = []
        
        for assignment in solution:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Çakışma kontrolü
            if project_id not in assigned_projects and (classroom_id, timeslot_id) not in assigned_classrooms_timeslots:
                valid_assignments.append(assignment)
                assigned_projects.add(project_id)
                assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
        
        return valid_assignments
    
    def evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
        """
        Verilen çözümün uygunluğunu değerlendirir.
        
        Args:
            solution: Değerlendirilecek çözüm.
            
        Returns:
            float: Uygunluk puanı.
        """
        # Çözüm geçerli mi?
        if not self._is_valid_solution(solution):
            return float('-inf')
        
        score = 0.0
        
        # Kural uygunluğu
        rule_compliance = self._calculate_rule_compliance(solution)
        score += rule_compliance * 100.0
        
        # Sınıf değişim sayısını minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        score -= instructor_changes * 10.0
        
        # Yük dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        score += load_balance * 50.0
        
        return score
    
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
    
    def _calculate_rule_compliance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Proje kurallarına uygunluğu hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            float: Kural uygunluk skoru (0-1 arası, 1 en iyi)
        """
        if not solution:
            return 0.0
        
        total_rules = 0
        satisfied_rules = 0
        
        for assignment in solution:
            project_id = assignment["project_id"]
            instructors = assignment["instructors"]
            
            # Projeyi bul
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if not project:
                continue
            
            # Kural 1: Her projede 3 katılımcı olmalı
            total_rules += 1
            if len(instructors) == 3:
                satisfied_rules += 1
            
            # Kural 2: İlk kişi projenin sorumlu hocası olmalı
            total_rules += 1
            if instructors and instructors[0] == project.get("responsible_id"):
                satisfied_rules += 1
            
            # Proje tipine göre kurallar
            if project.get("type") == "bitirme":
                # Kural 3: Bitirme projesinde en az 2 hoca olmalı
                total_rules += 1
                hoca_count = 0
                for instructor_id in instructors:
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("role") == "hoca":
                        hoca_count += 1
                
                if hoca_count >= 2:
                    satisfied_rules += 1
            
            elif project.get("type") == "ara":
                # Kural 4: Ara projede en az 1 hoca olmalı
                total_rules += 1
                has_hoca = False
                for instructor_id in instructors:
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("role") == "hoca":
                        has_hoca = True
                        break
                
                if has_hoca:
                    satisfied_rules += 1
        
        # Kural uygunluk oranını hesapla
        if total_rules > 0:
            return satisfied_rules / total_rules
        else:
            return 0.0 