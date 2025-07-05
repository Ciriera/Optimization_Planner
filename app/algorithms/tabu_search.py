"""
Tabu Search (Tabu Arama) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple, Set
import random
import numpy as np
import hashlib
from collections import deque

from app.algorithms.base import OptimizationAlgorithm

class TabuSearch(OptimizationAlgorithm):
    """
    Tabu Search (Tabu Arama) algoritması sınıfı.
    Tabu Arama kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Tabu Search algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.max_iterations = params.get("max_iterations", 200)
        self.tabu_list_size = params.get("tabu_list_size", 20)
        self.neighborhood_size = params.get("neighborhood_size", 30)
        self.aspiration_value = params.get("aspiration_value", 10.0)
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Tabu Search algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Tabu listesi (FIFO queue)
        self.tabu_list = deque(maxlen=self.tabu_list_size)
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tabu Search algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Başlangıç çözümü oluştur
        current_solution = self._create_initial_solution()
        current_fitness = self.evaluate_fitness(current_solution)
        
        # En iyi çözümü başlat
        self.best_solution = current_solution
        self.best_fitness = current_fitness
        
        # İterasyon sayacı
        iterations_without_improvement = 0
        
        # Ana döngü
        for iteration in range(self.max_iterations):
            # Komşu çözümler oluştur
            neighbors = self._generate_neighbors(current_solution)
            
            # En iyi komşuyu bul
            best_neighbor = None
            best_neighbor_fitness = float('-inf')
            
            for neighbor in neighbors:
                # Çözümün hash'ini hesapla
                neighbor_hash = self._hash_solution(neighbor)
                
                # Çözümün uygunluğunu değerlendir
                neighbor_fitness = self.evaluate_fitness(neighbor)
                
                # Tabu listesinde olmayan veya aspirasyon kriterini sağlayan komşuları değerlendir
                if (neighbor_hash not in self.tabu_list or 
                    neighbor_fitness > self.best_fitness + self.aspiration_value):
                    if neighbor_fitness > best_neighbor_fitness:
                        best_neighbor = neighbor
                        best_neighbor_fitness = neighbor_fitness
            
            # Eğer komşu bulunamadıysa, yeni bir çözüm oluştur
            if best_neighbor is None:
                current_solution = self._create_initial_solution()
                current_fitness = self.evaluate_fitness(current_solution)
                continue
            
            # Mevcut çözümü güncelle
            current_solution = best_neighbor
            current_fitness = best_neighbor_fitness
            
            # Tabu listesine ekle
            self.tabu_list.append(self._hash_solution(current_solution))
            
            # En iyi çözümü güncelle
            if current_fitness > self.best_fitness:
                self.best_solution = current_solution
                self.best_fitness = current_fitness
                iterations_without_improvement = 0
            else:
                iterations_without_improvement += 1
            
            # Belirli sayıda iterasyon boyunca iyileşme olmazsa, yeni bir çözüm oluştur
            if iterations_without_improvement > 20:
                current_solution = self._create_initial_solution()
                current_fitness = self.evaluate_fitness(current_solution)
                iterations_without_improvement = 0
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": self.max_iterations
        }
    
    def _create_initial_solution(self) -> List[Dict[str, Any]]:
        """
        Başlangıç çözümü oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç çözümü.
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
    
    def _generate_neighbors(self, solution: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Mevcut çözümün komşu çözümlerini oluşturur.
        
        Args:
            solution: Mevcut çözüm.
            
        Returns:
            List[List[Dict[str, Any]]]: Komşu çözümler.
        """
        neighbors = []
        
        # Belirli sayıda komşu oluştur
        for _ in range(self.neighborhood_size):
            # Rastgele bir değişiklik yap
            change_type = random.choice(["swap_classrooms", "swap_timeslots", "swap_instructors", "reassign"])
            
            # Çözümün bir kopyasını oluştur
            neighbor = [assignment.copy() for assignment in solution]
            
            if change_type == "swap_classrooms" and len(neighbor) >= 2:
                # İki atama arasında sınıfları değiştir
                idx1, idx2 = random.sample(range(len(neighbor)), 2)
                neighbor[idx1]["classroom_id"], neighbor[idx2]["classroom_id"] = neighbor[idx2]["classroom_id"], neighbor[idx1]["classroom_id"]
            
            elif change_type == "swap_timeslots" and len(neighbor) >= 2:
                # İki atama arasında zaman dilimlerini değiştir
                idx1, idx2 = random.sample(range(len(neighbor)), 2)
                neighbor[idx1]["timeslot_id"], neighbor[idx2]["timeslot_id"] = neighbor[idx2]["timeslot_id"], neighbor[idx1]["timeslot_id"]
            
            elif change_type == "swap_instructors" and len(neighbor) >= 1:
                # Bir atamada yardımcı katılımcıları değiştir
                idx = random.randint(0, len(neighbor) - 1)
                assignment = neighbor[idx]
                
                # Projeyi bul
                project_id = assignment["project_id"]
                project = next((p for p in self.projects if p.get("id") == project_id), None)
                
                if project:
                    # Sorumlu öğretim üyesi
                    responsible_id = project.get("responsible_id")
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
                    
                    # Katılımcıları güncelle
                    assignment["instructors"] = instructors
            
            elif change_type == "reassign" and len(neighbor) >= 1:
                # Rastgele bir atamayı yeniden yap
                idx = random.randint(0, len(neighbor) - 1)
                assignment = neighbor[idx]
                
                # Projeyi bul
                project_id = assignment["project_id"]
                project = next((p for p in self.projects if p.get("id") == project_id), None)
                
                if project:
                    # Rastgele bir sınıf ve zaman dilimi seç
                    classroom = random.choice(self.classrooms)
                    timeslot = random.choice(self.timeslots)
                    
                    # Sorumlu öğretim üyesi
                    responsible_id = project.get("responsible_id")
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
                    
                    # Atamayı güncelle
                    assignment["classroom_id"] = classroom.get("id")
                    assignment["timeslot_id"] = timeslot.get("id")
                    assignment["instructors"] = instructors
            
            # Çözümü düzelt (çakışmaları gider)
            neighbor = self._repair_solution(neighbor)
            
            # Komşuyu ekle
            neighbors.append(neighbor)
        
        return neighbors
    
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
    
    def _hash_solution(self, solution: List[Dict[str, Any]]) -> str:
        """
        Çözümün benzersiz bir hash değerini hesaplar.
        
        Args:
            solution: Hash'i hesaplanacak çözüm.
            
        Returns:
            str: Çözümün hash değeri.
        """
        # Çözümü sırala (deterministik hash için)
        sorted_solution = sorted(solution, key=lambda x: (x["project_id"], x["classroom_id"], x["timeslot_id"]))
        
        # Çözümü string'e dönüştür
        solution_str = str(sorted_solution)
        
        # Hash hesapla
        return hashlib.md5(solution_str.encode()).hexdigest()
    
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