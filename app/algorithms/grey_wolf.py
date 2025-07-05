"""
Grey Wolf Optimizer (Gri Kurt Optimizasyonu) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy

from app.algorithms.base import OptimizationAlgorithm

class GreyWolf(OptimizationAlgorithm):
    """
    Grey Wolf Optimizer (Gri Kurt Optimizasyonu) algoritması sınıfı.
    Gri Kurt Optimizasyonu kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Grey Wolf Optimizer algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.n_wolves = params.get("n_wolves", 30)
        self.n_iterations = params.get("n_iterations", 100)
        self.a_decrease_factor = params.get("a_decrease_factor", 2.0)
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Grey Wolf Optimizer algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Kurtları başlat
        self.wolves = self._initialize_wolves()
        
        # Alpha, Beta ve Delta kurtları
        self.alpha = {"position": None, "fitness": float('-inf')}
        self.beta = {"position": None, "fitness": float('-inf')}
        self.delta = {"position": None, "fitness": float('-inf')}
        
        # Kurtları sırala
        self._sort_wolves()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grey Wolf Optimizer algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # İterasyon döngüsü
        for iteration in range(self.n_iterations):
            # a parametresini güncelle
            a = self.a_decrease_factor - iteration * (self.a_decrease_factor / self.n_iterations)
            
            # Her kurt için
            for i in range(self.n_wolves):
                # Kurdu hareket ettir
                self._move_wolf(i, a)
                
                # Kurdun uygunluğunu yeniden değerlendir
                self.wolves[i]["fitness"] = self.evaluate_fitness(self.wolves[i]["position"])
            
            # Kurtları sırala
            self._sort_wolves()
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": self.n_iterations
        }
    
    def _initialize_wolves(self) -> List[Dict[str, Any]]:
        """
        Kurtları başlatır.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç kurtları.
        """
        wolves = []
        
        for _ in range(self.n_wolves):
            # Rastgele bir çözüm oluştur
            position = self._create_random_solution()
            
            # Çözümün uygunluğunu değerlendir
            fitness = self.evaluate_fitness(position)
            
            # Kurdu oluştur
            wolf = {
                "position": position,
                "fitness": fitness
            }
            
            # Kurdu ekle
            wolves.append(wolf)
            
            # En iyi çözümü güncelle
            if fitness > self.best_fitness:
                self.best_solution = copy.deepcopy(position)
                self.best_fitness = fitness
        
        return wolves
    
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
    
    def _sort_wolves(self) -> None:
        """
        Kurtları uygunluk değerine göre sıralar ve Alpha, Beta, Delta kurtlarını günceller.
        """
        # Kurtları uygunluk değerine göre sırala
        sorted_wolves = sorted(self.wolves, key=lambda x: x["fitness"], reverse=True)
        
        # Alpha, Beta ve Delta kurtlarını güncelle
        if sorted_wolves[0]["fitness"] > self.alpha["fitness"]:
            self.alpha = {
                "position": copy.deepcopy(sorted_wolves[0]["position"]),
                "fitness": sorted_wolves[0]["fitness"]
            }
        
        if len(sorted_wolves) > 1 and sorted_wolves[1]["fitness"] > self.beta["fitness"]:
            self.beta = {
                "position": copy.deepcopy(sorted_wolves[1]["position"]),
                "fitness": sorted_wolves[1]["fitness"]
            }
        
        if len(sorted_wolves) > 2 and sorted_wolves[2]["fitness"] > self.delta["fitness"]:
            self.delta = {
                "position": copy.deepcopy(sorted_wolves[2]["position"]),
                "fitness": sorted_wolves[2]["fitness"]
            }
        
        # En iyi çözümü güncelle
        if self.alpha["fitness"] > self.best_fitness:
            self.best_solution = copy.deepcopy(self.alpha["position"])
            self.best_fitness = self.alpha["fitness"]
    
    def _move_wolf(self, wolf_idx: int, a: float) -> None:
        """
        Kurdu hareket ettirir.
        
        Args:
            wolf_idx: Kurt indeksi.
            a: a parametresi.
        """
        # Mevcut kurt
        wolf = self.wolves[wolf_idx]
        
        # Alpha, Beta ve Delta kurtlarının çözümleri
        alpha_pos = self.alpha["position"]
        beta_pos = self.beta["position"]
        delta_pos = self.delta["position"]
        
        # Eğer lider kurtlar henüz belirlenmemişse
        if alpha_pos is None or beta_pos is None or delta_pos is None:
            return
        
        # Yeni çözümü oluştur
        new_position = self._generate_new_position(wolf["position"], alpha_pos, beta_pos, delta_pos, a)
        
        # Yeni çözümü kurda ata
        wolf["position"] = new_position
    
    def _generate_new_position(self, wolf_pos: List[Dict[str, Any]], alpha_pos: List[Dict[str, Any]], beta_pos: List[Dict[str, Any]], delta_pos: List[Dict[str, Any]], a: float) -> List[Dict[str, Any]]:
        """
        Alpha, Beta ve Delta kurtlarına göre yeni bir çözüm oluşturur.
        
        Args:
            wolf_pos: Kurt çözümü.
            alpha_pos: Alpha kurt çözümü.
            beta_pos: Beta kurt çözümü.
            delta_pos: Delta kurt çözümü.
            a: a parametresi.
            
        Returns:
            List[Dict[str, Any]]: Yeni çözüm.
        """
        # Yeni çözüm için temel olarak wolf_pos'u kullan
        new_position = copy.deepcopy(wolf_pos)
        
        # Çözümleri proje ID'lerine göre sırala
        sorted_alpha_pos = sorted(alpha_pos, key=lambda x: x["project_id"]) if alpha_pos else []
        sorted_beta_pos = sorted(beta_pos, key=lambda x: x["project_id"]) if beta_pos else []
        sorted_delta_pos = sorted(delta_pos, key=lambda x: x["project_id"]) if delta_pos else []
        
        # Her atama için
        for i, assignment in enumerate(new_position):
            # Rastgele A ve C katsayıları
            A1 = 2 * a * random.random() - a
            A2 = 2 * a * random.random() - a
            A3 = 2 * a * random.random() - a
            
            C1 = 2 * random.random()
            C2 = 2 * random.random()
            C3 = 2 * random.random()
            
            # Aynı projeye ait atamaları bul
            project_id = assignment["project_id"]
            alpha_assignment = next((a for a in sorted_alpha_pos if a.get("project_id") == project_id), None)
            beta_assignment = next((a for a in sorted_beta_pos if a.get("project_id") == project_id), None)
            delta_assignment = next((a for a in sorted_delta_pos if a.get("project_id") == project_id), None)
            
            # Eğer tüm lider kurtlarda bu proje için atama varsa
            if alpha_assignment and beta_assignment and delta_assignment:
                # Sınıf için
                if abs(A1) < 1 and alpha_assignment.get("classroom_id"):
                    assignment["classroom_id"] = alpha_assignment["classroom_id"]
                elif abs(A2) < 1 and beta_assignment.get("classroom_id"):
                    assignment["classroom_id"] = beta_assignment["classroom_id"]
                elif abs(A3) < 1 and delta_assignment.get("classroom_id"):
                    assignment["classroom_id"] = delta_assignment["classroom_id"]
                
                # Zaman dilimi için
                if abs(A1) < 1 and alpha_assignment.get("timeslot_id"):
                    assignment["timeslot_id"] = alpha_assignment["timeslot_id"]
                elif abs(A2) < 1 and beta_assignment.get("timeslot_id"):
                    assignment["timeslot_id"] = beta_assignment["timeslot_id"]
                elif abs(A3) < 1 and delta_assignment.get("timeslot_id"):
                    assignment["timeslot_id"] = delta_assignment["timeslot_id"]
                
                # Katılımcılar için
                if abs(A1) < 1 and alpha_assignment.get("instructors"):
                    assignment["instructors"] = copy.deepcopy(alpha_assignment["instructors"])
                elif abs(A2) < 1 and beta_assignment.get("instructors"):
                    assignment["instructors"] = copy.deepcopy(beta_assignment["instructors"])
                elif abs(A3) < 1 and delta_assignment.get("instructors"):
                    assignment["instructors"] = copy.deepcopy(delta_assignment["instructors"])
            
            # Keşif: Rastgele değişiklik yap
            if abs(A1) >= 1 or abs(A2) >= 1 or abs(A3) >= 1:
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
        new_position = self._repair_solution(new_position)
        
        return new_position
    
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