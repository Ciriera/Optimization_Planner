"""
CP-SAT (Constraint Programming - SAT) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import time

from app.algorithms.base import OptimizationAlgorithm

class CPSAT(OptimizationAlgorithm):
    """
    CP-SAT (Constraint Programming - SAT) algoritması sınıfı.
    Kısıt Programlama ve SAT çözücü kullanarak proje atama problemini çözer.
    
    Not: Bu sınıf, gerçek bir CP-SAT çözücü kullanmak yerine, CP-SAT yaklaşımını simüle eder.
    Gerçek bir implementasyon için Google OR-Tools gibi kütüphanelerin kullanılması önerilir.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        CP-SAT algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.time_limit = params.get("time_limit", 60)  # Saniye cinsinden zaman limiti
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        CP-SAT algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CP-SAT algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Başlangıç zamanı
        start_time = time.time()
        
        # Başlangıç çözümü oluştur
        solution = self._create_initial_solution()
        
        # Çözümün uygunluğunu değerlendir
        fitness = self.evaluate_fitness(solution)
        
        # En iyi çözümü güncelle
        self.best_solution = solution
        self.best_fitness = fitness
        
        # Yerel arama ile çözümü iyileştir
        while time.time() - start_time < self.time_limit:
            # Komşu çözüm oluştur
            neighbor = self._generate_neighbor(solution)
            
            # Komşu çözümün uygunluğunu değerlendir
            neighbor_fitness = self.evaluate_fitness(neighbor)
            
            # Daha iyi çözümü kabul et
            if neighbor_fitness > fitness:
                solution = neighbor
                fitness = neighbor_fitness
                
                # En iyi çözümü güncelle
                if fitness > self.best_fitness:
                    self.best_solution = solution
                    self.best_fitness = fitness
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "time_limit": self.time_limit
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
        
        # Projeleri önceliklendir
        projects = self._prioritize_projects()
        
        # Her proje için en iyi atamayı yap
        for project in projects:
            # En iyi sınıf ve zaman dilimini bul
            best_assignment = self._find_best_assignment(project, assigned_classrooms_timeslots)
            
            if best_assignment:
                solution.append(best_assignment)
                assigned_projects.add(project.get("id"))
                assigned_classrooms_timeslots.add((best_assignment["classroom_id"], best_assignment["timeslot_id"]))
        
        return solution
    
    def _prioritize_projects(self) -> List[Dict[str, Any]]:
        """
        Projeleri önceliklendirir.
        
        Returns:
            List[Dict[str, Any]]: Önceliklendirilmiş projeler.
        """
        # Projeleri tipine göre önceliklendir (bitirme > ara)
        bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type") == "ara"]
        
        # Bitirme projelerini bütünleme durumuna göre önceliklendir
        bitirme_final = [p for p in bitirme_projects if not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in bitirme_projects if p.get("is_makeup", False)]
        
        # Ara projeleri bütünleme durumuna göre önceliklendir
        ara_final = [p for p in ara_projects if not p.get("is_makeup", False)]
        ara_makeup = [p for p in ara_projects if p.get("is_makeup", False)]
        
        # Öncelik sırası: bitirme_final > ara_final > bitirme_makeup > ara_makeup
        return bitirme_final + ara_final + bitirme_makeup + ara_makeup
    
    def _find_best_assignment(self, project: Dict[str, Any], assigned_classrooms_timeslots: set) -> Dict[str, Any]:
        """
        Proje için en iyi sınıf ve zaman dilimi atamasını bulur.
        
        Args:
            project: Atanacak proje.
            assigned_classrooms_timeslots: Atanmış (sınıf, zaman dilimi) çiftleri.
            
        Returns:
            Dict[str, Any]: En iyi atama.
        """
        best_assignment = None
        best_score = float('-inf')
        
        # Sorumlu öğretim üyesi
        responsible_id = project.get("responsible_id", None)
        
        # Tüm sınıf ve zaman dilimi kombinasyonlarını değerlendir
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                if (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots:
                    # Katılımcıları seç
                    instructors = self._select_instructors(project, responsible_id)
                    
                    if instructors:
                        # Atama skoru hesapla
                        score = self._calculate_assignment_score(project, classroom, timeslot, instructors)
                        
                        # En iyi atamayı güncelle
                        if score > best_score:
                            best_score = score
                            best_assignment = {
                                "project_id": project.get("id"),
                                "classroom_id": classroom.get("id"),
                                "timeslot_id": timeslot.get("id"),
                                "instructors": instructors
                            }
        
        return best_assignment
    
    def _select_instructors(self, project: Dict[str, Any], responsible_id: str) -> List[str]:
        """
        Proje için katılımcıları seçer.
        
        Args:
            project: Proje bilgisi.
            responsible_id: Sorumlu öğretim üyesi ID'si.
            
        Returns:
            List[str]: Seçilen katılımcı ID'leri.
        """
        instructors = [responsible_id] if responsible_id else []
        
        # Proje tipine göre katılımcı seçimi
        project_type = project.get("type")
        
        # Mevcut katılımcı yüklerini hesapla
        instructor_loads = self._calculate_instructor_loads()
        
        # Yüke göre öğretim üyelerini sırala (en az yüklü olanlar önce)
        sorted_instructors = sorted(
            [i for i in self.instructors if i.get("id") != responsible_id],
            key=lambda x: instructor_loads.get(x.get("id"), 0)
        )
        
        if project_type == "bitirme":
            # Bitirme projesi için en az 2 hoca olmalı
            hocas = [i for i in sorted_instructors if i.get("role") == "hoca"]
            aras_gors = [i for i in sorted_instructors if i.get("role") == "aras_gor"]
            
            # En az yüklü hocayı ekle
            if hocas:
                instructors.append(hocas[0].get("id"))
                
                # Üçüncü kişi olarak en az yüklü hoca veya araş. gör. ekle
                if len(hocas) > 1:
                    instructors.append(hocas[1].get("id"))
                elif aras_gors:
                    instructors.append(aras_gors[0].get("id"))
        else:
            # Ara proje için en az 1 hoca yeterli (sorumlu hoca zaten var)
            # En az yüklü 2 kişiyi ekle
            if sorted_instructors:
                instructors.append(sorted_instructors[0].get("id"))
                if len(sorted_instructors) > 1:
                    instructors.append(sorted_instructors[1].get("id"))
        
        return instructors
    
    def _calculate_instructor_loads(self) -> Dict[str, int]:
        """
        Öğretim üyelerinin mevcut yüklerini hesaplar.
        
        Returns:
            Dict[str, int]: Öğretim üyesi ID'si -> yük sayısı.
        """
        loads = {}
        
        # Mevcut en iyi çözümdeki yükleri hesapla
        if self.best_solution:
            for assignment in self.best_solution:
                for instructor_id in assignment.get("instructors", []):
                    loads[instructor_id] = loads.get(instructor_id, 0) + 1
        
        return loads
    
    def _calculate_assignment_score(self, project: Dict[str, Any], classroom: Dict[str, Any], timeslot: Dict[str, Any], instructors: List[str]) -> float:
        """
        Atama skorunu hesaplar.
        
        Args:
            project: Proje bilgisi.
            classroom: Sınıf bilgisi.
            timeslot: Zaman dilimi bilgisi.
            instructors: Katılımcı ID'leri.
            
        Returns:
            float: Atama skoru.
        """
        score = 0.0
        
        # Kural uygunluğu
        if self._check_rule_compliance(project, instructors):
            score += 100.0
        
        # Sınıf geçişlerini minimize et
        if self.best_solution:
            # Mevcut çözümdeki son atamaları bul
            instructor_last_classrooms = {}
            for assignment in self.best_solution:
                for instructor_id in assignment.get("instructors", []):
                    instructor_last_classrooms[instructor_id] = assignment.get("classroom_id")
            
            # Sınıf değişim sayısını hesapla
            changes = 0
            for instructor_id in instructors:
                if instructor_id in instructor_last_classrooms and instructor_last_classrooms[instructor_id] != classroom.get("id"):
                    # Hocalar için sınıf değişimi daha maliyetli
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("role") == "hoca":
                        changes += 2
                    else:
                        changes += 1
            
            # Değişim sayısı az olduğunda skor yüksek olsun
            score -= changes * 10.0
        
        # Yük dengesini maksimize et
        instructor_loads = self._calculate_instructor_loads()
        total_load = sum(instructor_loads.values()) if instructor_loads else 0
        avg_load = total_load / len(instructor_loads) if instructor_loads else 0
        
        # Seçilen katılımcıların yük dengesini hesapla
        load_variance = 0.0
        for instructor_id in instructors:
            load = instructor_loads.get(instructor_id, 0)
            load_variance += (load - avg_load) ** 2
        
        # Yük varyansı düşük olduğunda skor yüksek olsun
        score -= load_variance * 5.0
        
        return score
    
    def _check_rule_compliance(self, project: Dict[str, Any], instructors: List[str]) -> bool:
        """
        Proje kurallarına uygunluğu kontrol eder.
        
        Args:
            project: Proje bilgisi.
            instructors: Katılımcı ID'leri.
            
        Returns:
            bool: Kurallara uygunsa True, değilse False.
        """
        # Kural 1: Her projede 3 katılımcı olmalı
        if len(instructors) != 3:
            return False
        
        # Kural 2: İlk kişi projenin sorumlu hocası olmalı
        if instructors[0] != project.get("responsible_id"):
            return False
        
        # Proje tipine göre kurallar
        project_type = project.get("type")
        
        if project_type == "bitirme":
            # Kural 3: Bitirme projesinde en az 2 hoca olmalı
            hoca_count = 0
            for instructor_id in instructors:
                instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                if instructor and instructor.get("role") == "hoca":
                    hoca_count += 1
            
            if hoca_count < 2:
                return False
        
        elif project_type == "ara":
            # Kural 4: Ara projede en az 1 hoca olmalı
            has_hoca = False
            for instructor_id in instructors:
                instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                if instructor and instructor.get("role") == "hoca":
                    has_hoca = True
                    break
            
            if not has_hoca:
                return False
        
        return True
    
    def _generate_neighbor(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mevcut çözümün komşu çözümünü oluşturur.
        
        Args:
            solution: Mevcut çözüm.
            
        Returns:
            List[Dict[str, Any]]: Komşu çözüm.
        """
        if not solution:
            return solution
        
        # Çözümün bir kopyasını oluştur
        neighbor = [assignment.copy() for assignment in solution]
        
        # Rastgele bir değişiklik yap
        change_type = random.choice(["swap_classrooms", "swap_timeslots", "swap_instructors"])
        
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
                
                # Yeni katılımcılar seç
                new_instructors = self._select_instructors(project, responsible_id)
                
                # Katılımcıları güncelle
                assignment["instructors"] = new_instructors
        
        return neighbor
    
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