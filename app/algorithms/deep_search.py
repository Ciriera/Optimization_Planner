"""
Deep Search (Derin Arama) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple, Set
import random
import numpy as np
import time
import heapq

from app.algorithms.base import OptimizationAlgorithm

class DeepSearch(OptimizationAlgorithm):
    """
    Deep Search (Derin Arama) algoritması sınıfı.
    Derin arama stratejileri kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Deep Search algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.max_depth = params.get("max_depth", 5)  # Maksimum arama derinliği
        self.beam_width = params.get("beam_width", 10)  # Beam search genişliği
        self.time_limit = params.get("time_limit", 60)  # Saniye cinsinden zaman limiti
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Deep Search algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep Search algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Başlangıç zamanı
        start_time = time.time()
        
        # Beam search ile çözüm ara
        solution = self._beam_search()
        
        # Çözümün uygunluğunu değerlendir
        fitness = self.evaluate_fitness(solution)
        
        # En iyi çözümü güncelle
        self.best_solution = solution
        self.best_fitness = fitness
        
        # Kalan sürede iterative deepening ile çözümü iyileştir
        remaining_time = self.time_limit - (time.time() - start_time)
        if remaining_time > 0:
            improved_solution = self._iterative_deepening(solution, remaining_time)
            
            # İyileştirilmiş çözümün uygunluğunu değerlendir
            improved_fitness = self.evaluate_fitness(improved_solution)
            
            # Daha iyi çözümü kabul et
            if improved_fitness > fitness:
                self.best_solution = improved_solution
                self.best_fitness = improved_fitness
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "time_limit": self.time_limit
        }
    
    def _beam_search(self) -> List[Dict[str, Any]]:
        """
        Beam search algoritması ile çözüm arar.
        
        Returns:
            List[Dict[str, Any]]: Bulunan en iyi çözüm.
        """
        # Başlangıç çözümü (boş çözüm)
        initial_state = []
        
        # Beam (en iyi çözümleri tutan liste)
        beam = [(self.evaluate_fitness(initial_state), initial_state)]
        
        # Projeleri önceliklendir
        projects = self._prioritize_projects()
        
        # Her proje için
        for project in projects:
            # Yeni beam
            new_beam = []
            
            # Beam'deki her çözüm için
            for _, state in beam:
                # Mevcut atanmış projeler ve sınıf-zaman dilimi çiftleri
                assigned_projects = {assignment["project_id"] for assignment in state}
                assigned_classrooms_timeslots = {(assignment["classroom_id"], assignment["timeslot_id"]) for assignment in state}
                
                # Proje zaten atanmışsa, atla
                if project.get("id") in assigned_projects:
                    new_beam.append((self.evaluate_fitness(state), state))
                    continue
                
                # Olası tüm sınıf ve zaman dilimi kombinasyonlarını dene
                for classroom in self.classrooms:
                    for timeslot in self.timeslots:
                        if (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots:
                            # Sorumlu öğretim üyesi
                            responsible_id = project.get("responsible_id", None)
                            
                            # Katılımcıları seç
                            instructors = self._select_instructors(project, responsible_id, state)
                            
                            if instructors:
                                # Yeni atama
                                new_assignment = {
                                    "project_id": project.get("id"),
                                    "classroom_id": classroom.get("id"),
                                    "timeslot_id": timeslot.get("id"),
                                    "instructors": instructors
                                }
                                
                                # Yeni çözüm
                                new_state = state + [new_assignment]
                                
                                # Çözümün uygunluğunu değerlendir
                                fitness = self.evaluate_fitness(new_state)
                                
                                # Yeni beam'e ekle
                                new_beam.append((fitness, new_state))
            
            # En iyi beam_width kadar çözümü seç
            beam = heapq.nlargest(self.beam_width, new_beam, key=lambda x: x[0])
        
        # En iyi çözümü döndür
        if beam:
            return beam[0][1]
        else:
            return []
    
    def _iterative_deepening(self, solution: List[Dict[str, Any]], time_limit: float) -> List[Dict[str, Any]]:
        """
        Iterative deepening algoritması ile çözümü iyileştirir.
        
        Args:
            solution: İyileştirilecek çözüm.
            time_limit: Saniye cinsinden zaman limiti.
            
        Returns:
            List[Dict[str, Any]]: İyileştirilmiş çözüm.
        """
        # Başlangıç zamanı
        start_time = time.time()
        
        # Mevcut çözüm
        current_solution = solution
        current_fitness = self.evaluate_fitness(current_solution)
        
        # Derinlik arttırarak arama yap
        for depth in range(1, self.max_depth + 1):
            # Zaman kontrolü
            if time.time() - start_time > time_limit:
                break
            
            # Derinlik arttıkça daha fazla değişiklik yap
            improved_solution = self._depth_limited_search(current_solution, depth, time_limit - (time.time() - start_time))
            
            # İyileştirilmiş çözümün uygunluğunu değerlendir
            improved_fitness = self.evaluate_fitness(improved_solution)
            
            # Daha iyi çözümü kabul et
            if improved_fitness > current_fitness:
                current_solution = improved_solution
                current_fitness = improved_fitness
        
        return current_solution
    
    def _depth_limited_search(self, solution: List[Dict[str, Any]], depth: int, time_limit: float) -> List[Dict[str, Any]]:
        """
        Belirli bir derinliğe kadar arama yapar.
        
        Args:
            solution: Arama başlangıç çözümü.
            depth: Maksimum arama derinliği.
            time_limit: Saniye cinsinden zaman limiti.
            
        Returns:
            List[Dict[str, Any]]: Bulunan en iyi çözüm.
        """
        # Başlangıç zamanı
        start_time = time.time()
        
        # Mevcut çözüm
        current_solution = solution
        current_fitness = self.evaluate_fitness(current_solution)
        
        # Ziyaret edilen çözümler
        visited = set()
        
        # DFS ile arama yap
        def dfs(sol, d, visited_states):
            nonlocal current_solution, current_fitness, start_time
            
            # Zaman kontrolü
            if time.time() - start_time > time_limit:
                return
            
            # Çözüm hash'i
            sol_hash = self._hash_solution(sol)
            
            # Çözüm zaten ziyaret edildiyse, atla
            if sol_hash in visited_states:
                return
            
            # Çözümü ziyaret edildi olarak işaretle
            visited_states.add(sol_hash)
            
            # Çözümün uygunluğunu değerlendir
            fitness = self.evaluate_fitness(sol)
            
            # Daha iyi çözümü kabul et
            if fitness > current_fitness:
                current_solution = sol
                current_fitness = fitness
            
            # Maksimum derinliğe ulaşıldıysa, dur
            if d >= depth:
                return
            
            # Komşu çözümleri oluştur
            neighbors = self._generate_neighbors(sol)
            
            # Komşu çözümleri ziyaret et
            for neighbor in neighbors:
                dfs(neighbor, d + 1, visited_states)
        
        # DFS başlat
        dfs(current_solution, 0, visited)
        
        return current_solution
    
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
    
    def _select_instructors(self, project: Dict[str, Any], responsible_id: str, current_solution: List[Dict[str, Any]]) -> List[str]:
        """
        Proje için katılımcıları seçer.
        
        Args:
            project: Proje bilgisi.
            responsible_id: Sorumlu öğretim üyesi ID'si.
            current_solution: Mevcut çözüm.
            
        Returns:
            List[str]: Seçilen katılımcı ID'leri.
        """
        instructors = [responsible_id] if responsible_id else []
        
        # Proje tipine göre katılımcı seçimi
        project_type = project.get("type")
        
        # Mevcut katılımcı yüklerini hesapla
        instructor_loads = {}
        for assignment in current_solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
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
    
    def _generate_neighbors(self, solution: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Mevcut çözümün komşu çözümlerini oluşturur.
        
        Args:
            solution: Mevcut çözüm.
            
        Returns:
            List[List[Dict[str, Any]]]: Komşu çözümler.
        """
        neighbors = []
        
        # Çözüm boşsa, komşu yok
        if not solution:
            return neighbors
        
        # 1. Sınıf değişimi
        if len(solution) >= 2:
            # İki atama arasında sınıfları değiştir
            for i in range(len(solution)):
                for j in range(i + 1, len(solution)):
                    # Çözümün bir kopyasını oluştur
                    neighbor = [assignment.copy() for assignment in solution]
                    
                    # Sınıfları değiştir
                    neighbor[i]["classroom_id"], neighbor[j]["classroom_id"] = neighbor[j]["classroom_id"], neighbor[i]["classroom_id"]
                    
                    # Komşuyu ekle
                    neighbors.append(neighbor)
        
        # 2. Zaman dilimi değişimi
        if len(solution) >= 2:
            # İki atama arasında zaman dilimlerini değiştir
            for i in range(len(solution)):
                for j in range(i + 1, len(solution)):
                    # Çözümün bir kopyasını oluştur
                    neighbor = [assignment.copy() for assignment in solution]
                    
                    # Zaman dilimlerini değiştir
                    neighbor[i]["timeslot_id"], neighbor[j]["timeslot_id"] = neighbor[j]["timeslot_id"], neighbor[i]["timeslot_id"]
                    
                    # Komşuyu ekle
                    neighbors.append(neighbor)
        
        # 3. Katılımcı değişimi
        for i in range(len(solution)):
            # Projeyi bul
            project_id = solution[i]["project_id"]
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            
            if project:
                # Sorumlu öğretim üyesi
                responsible_id = project.get("responsible_id")
                
                # Yeni katılımcılar seç
                new_instructors = self._select_instructors(project, responsible_id, solution)
                
                # Eğer yeni katılımcılar farklıysa
                if set(new_instructors) != set(solution[i]["instructors"]):
                    # Çözümün bir kopyasını oluştur
                    neighbor = [assignment.copy() for assignment in solution]
                    
                    # Katılımcıları güncelle
                    neighbor[i]["instructors"] = new_instructors
                    
                    # Komşuyu ekle
                    neighbors.append(neighbor)
        
        return neighbors
    
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
        
        # Hash değeri
        hash_value = ""
        
        for assignment in sorted_solution:
            hash_value += f"{assignment['project_id']}:{assignment['classroom_id']}:{assignment['timeslot_id']}:"
            hash_value += ",".join(sorted(assignment["instructors"]))
            hash_value += ";"
        
        return hash_value
    
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
            return True  # Boş çözüm geçerlidir (başlangıç durumu)
        
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