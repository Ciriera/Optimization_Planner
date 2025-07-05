"""
Firefly (Ateşböceği) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import math
import copy

from app.algorithms.base import OptimizationAlgorithm

class Firefly(OptimizationAlgorithm):
    """
    Firefly (Ateşböceği) algoritması sınıfı.
    Ateşböceği algoritması kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Firefly algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.n_fireflies = params.get("n_fireflies", 30)
        self.n_iterations = params.get("n_iterations", 100)
        self.alpha = params.get("alpha", 0.2)  # Rastgelelik parametresi
        self.beta0 = params.get("beta0", 1.0)  # Çekicilik parametresi
        self.gamma = params.get("gamma", 1.0)  # Işık emilim katsayısı
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Firefly algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Ateşböceklerini başlat
        self.fireflies = self._initialize_fireflies()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Firefly algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # İterasyon döngüsü
        for iteration in range(self.n_iterations):
            # Her ateşböceği için
            for i in range(self.n_fireflies):
                # Diğer ateşböcekleriyle karşılaştır
                for j in range(self.n_fireflies):
                    # Eğer j ateşböceği i'den daha parlaksa (daha iyi uygunluk değerine sahipse)
                    if self.fireflies[j]["fitness"] > self.fireflies[i]["fitness"]:
                        # i ateşböceğini j'ye doğru hareket ettir
                        self._move_firefly(i, j)
                        
                        # i ateşböceğinin uygunluğunu yeniden değerlendir
                        self.fireflies[i]["fitness"] = self.evaluate_fitness(self.fireflies[i]["position"])
                        
                        # En iyi çözümü güncelle
                        if self.fireflies[i]["fitness"] > self.best_fitness:
                            self.best_solution = copy.deepcopy(self.fireflies[i]["position"])
                            self.best_fitness = self.fireflies[i]["fitness"]
            
            # Alpha parametresini azalt (soğutma)
            self.alpha *= 0.97
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": self.n_iterations
        }
    
    def _initialize_fireflies(self) -> List[Dict[str, Any]]:
        """
        Ateşböceklerini başlatır.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç ateşböcekleri.
        """
        fireflies = []
        
        for _ in range(self.n_fireflies):
            # Rastgele bir çözüm oluştur
            position = self._create_random_solution()
            
            # Çözümün uygunluğunu değerlendir
            fitness = self.evaluate_fitness(position)
            
            # Ateşböceğini oluştur
            firefly = {
                "position": position,
                "fitness": fitness
            }
            
            # Ateşböceğini ekle
            fireflies.append(firefly)
            
            # En iyi çözümü güncelle
            if fitness > self.best_fitness:
                self.best_solution = copy.deepcopy(position)
                self.best_fitness = fitness
        
        return fireflies
    
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
    
    def _move_firefly(self, i: int, j: int) -> None:
        """
        i ateşböceğini j ateşböceğine doğru hareket ettirir.
        
        Args:
            i: Hareket eden ateşböceği indeksi.
            j: Çeken ateşböceği indeksi.
        """
        # Çözümler arası mesafeyi hesapla
        distance = self._calculate_distance(self.fireflies[i]["position"], self.fireflies[j]["position"])
        
        # Çekicilik hesapla
        beta = self.beta0 * math.exp(-self.gamma * distance**2)
        
        # Yeni çözümü oluştur
        new_position = self._generate_new_position(self.fireflies[i]["position"], self.fireflies[j]["position"], beta)
        
        # Yeni çözümü ateşböceğine ata
        self.fireflies[i]["position"] = new_position
    
    def _calculate_distance(self, solution1: List[Dict[str, Any]], solution2: List[Dict[str, Any]]) -> float:
        """
        İki çözüm arasındaki mesafeyi hesaplar.
        
        Args:
            solution1: Birinci çözüm.
            solution2: İkinci çözüm.
            
        Returns:
            float: İki çözüm arasındaki mesafe.
        """
        # Basit bir mesafe metriği: Farklı atamaların oranı
        if not solution1 or not solution2:
            return 1.0
        
        # Çözümleri proje ID'lerine göre sırala
        sorted_solution1 = sorted(solution1, key=lambda x: x["project_id"])
        sorted_solution2 = sorted(solution2, key=lambda x: x["project_id"])
        
        # Minimum uzunluğu al
        min_length = min(len(sorted_solution1), len(sorted_solution2))
        
        # Farklı atamaları say
        differences = 0
        
        for i in range(min_length):
            # Sınıf ve zaman dilimi farklıysa
            if (sorted_solution1[i]["classroom_id"] != sorted_solution2[i]["classroom_id"] or
                sorted_solution1[i]["timeslot_id"] != sorted_solution2[i]["timeslot_id"]):
                differences += 1
            
            # Katılımcılar farklıysa
            if set(sorted_solution1[i]["instructors"]) != set(sorted_solution2[i]["instructors"]):
                differences += 0.5
        
        # Uzunluk farkını da hesaba kat
        differences += abs(len(sorted_solution1) - len(sorted_solution2))
        
        # Normalize et
        max_length = max(len(sorted_solution1), len(sorted_solution2))
        if max_length > 0:
            return differences / max_length
        else:
            return 1.0
    
    def _generate_new_position(self, solution1: List[Dict[str, Any]], solution2: List[Dict[str, Any]], beta: float) -> List[Dict[str, Any]]:
        """
        İki çözümden yeni bir çözüm oluşturur.
        
        Args:
            solution1: Birinci çözüm (hareket eden).
            solution2: İkinci çözüm (çeken).
            beta: Çekicilik değeri.
            
        Returns:
            List[Dict[str, Any]]: Yeni çözüm.
        """
        # Yeni çözüm için temel olarak solution1'i kullan
        new_solution = copy.deepcopy(solution1)
        
        # Çözümleri proje ID'lerine göre sırala
        sorted_solution2 = sorted(solution2, key=lambda x: x["project_id"])
        
        # Beta olasılığıyla solution2'den atamalar al
        for i, assignment in enumerate(new_solution):
            if random.random() < beta:
                # Aynı projeye ait atamayı solution2'den bul
                project_id = assignment["project_id"]
                s2_assignment = next((a for a in sorted_solution2 if a.get("project_id") == project_id), None)
                
                if s2_assignment:
                    # Beta olasılığıyla sınıfı al
                    if random.random() < beta:
                        assignment["classroom_id"] = s2_assignment["classroom_id"]
                    
                    # Beta olasılığıyla zaman dilimini al
                    if random.random() < beta:
                        assignment["timeslot_id"] = s2_assignment["timeslot_id"]
                    
                    # Beta olasılığıyla katılımcıları al
                    if random.random() < beta:
                        assignment["instructors"] = copy.deepcopy(s2_assignment["instructors"])
        
        # Alpha olasılığıyla rastgele değişiklikler yap
        for assignment in new_solution:
            if random.random() < self.alpha:
                # Rastgele bir değişiklik tipi seç
                change_type = random.choice(["classroom", "timeslot", "instructors"])
                
                if change_type == "classroom":
                    # Sınıfı değiştir
                    available_classrooms = [c for c in self.classrooms if c.get("id") != assignment["classroom_id"]]
                    if available_classrooms:
                        assignment["classroom_id"] = random.choice(available_classrooms).get("id")
                
                elif change_type == "timeslot":
                    # Zaman dilimini değiştir
                    available_timeslots = [t for t in self.timeslots if t.get("id") != assignment["timeslot_id"]]
                    if available_timeslots:
                        assignment["timeslot_id"] = random.choice(available_timeslots).get("id")
                
                elif change_type == "instructors":
                    # Projeyi bul
                    project_id = assignment["project_id"]
                    project = next((p for p in self.projects if p.get("id") == project_id), None)
                    
                    if project:
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
                            
                            # Katılımcıları güncelle
                            assignment["instructors"] = instructors
        
        # Çözümü düzelt (çakışmaları gider)
        new_solution = self._repair_solution(new_solution)
        
        return new_solution
    
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