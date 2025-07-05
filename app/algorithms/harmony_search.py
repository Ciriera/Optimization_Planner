"""
Harmony Search (Uyum Arama) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy

from app.algorithms.base import OptimizationAlgorithm

class HarmonySearch(OptimizationAlgorithm):
    """
    Harmony Search (Uyum Arama) algoritması sınıfı.
    Uyum Arama kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Harmony Search algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.harmony_memory_size = params.get("harmony_memory_size", 30)
        self.max_iterations = params.get("max_iterations", 100)
        self.hmcr = params.get("hmcr", 0.9)  # Harmony Memory Considering Rate
        self.par = params.get("par", 0.3)  # Pitch Adjustment Rate
        self.bw = params.get("bw", 0.2)  # Bandwidth
        self.best_solution = None
        self.best_fitness = float('-inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Harmony Search algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Harmony belleğini başlat
        self.harmony_memory = self._initialize_harmony_memory()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Harmony Search algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # İterasyon döngüsü
        for iteration in range(self.max_iterations):
            # Yeni bir harmoni oluştur
            new_harmony = self._improvise()
            
            # Yeni harmoninin uygunluğunu değerlendir
            new_fitness = self.evaluate_fitness(new_harmony)
            
            # Harmony belleğini güncelle
            self._update_harmony_memory(new_harmony, new_fitness)
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": self.max_iterations
        }
    
    def _initialize_harmony_memory(self) -> List[Dict[str, Any]]:
        """
        Harmony belleğini başlatır.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç harmony belleği.
        """
        harmony_memory = []
        
        for _ in range(self.harmony_memory_size):
            # Rastgele bir çözüm oluştur
            solution = self._create_random_solution()
            
            # Çözümün uygunluğunu değerlendir
            fitness = self.evaluate_fitness(solution)
            
            # Harmony belleğine ekle
            harmony_memory.append({
                "solution": solution,
                "fitness": fitness
            })
            
            # En iyi çözümü güncelle
            if fitness > self.best_fitness:
                self.best_solution = copy.deepcopy(solution)
                self.best_fitness = fitness
        
        # Uygunluk değerine göre sırala
        harmony_memory.sort(key=lambda x: x["fitness"], reverse=True)
        
        return harmony_memory
    
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
    
    def _improvise(self) -> List[Dict[str, Any]]:
        """
        Yeni bir harmoni (çözüm) oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Yeni harmoni.
        """
        new_harmony = []
        
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        # Her proje için atama yap
        for project in self.projects:
            # HMCR: Harmony Memory Considering Rate
            if random.random() < self.hmcr:
                # Harmony belleğinden bir çözüm seç
                selected_harmony = random.choice(self.harmony_memory)
                
                # Seçilen çözümden bu projeye ait atamayı bul
                project_assignment = next((a for a in selected_harmony["solution"] if a.get("project_id") == project.get("id")), None)
                
                if project_assignment:
                    classroom_id = project_assignment["classroom_id"]
                    timeslot_id = project_assignment["timeslot_id"]
                    instructors = project_assignment["instructors"]
                    
                    # PAR: Pitch Adjustment Rate
                    if random.random() < self.par:
                        # Sınıf veya zaman dilimini ayarla
                        if random.random() < 0.5:
                            # Sınıfı ayarla
                            available_classrooms = [c for c in self.classrooms if c.get("id") != classroom_id]
                            if available_classrooms:
                                classroom_id = random.choice(available_classrooms).get("id")
                        else:
                            # Zaman dilimini ayarla
                            available_timeslots = [t for t in self.timeslots if t.get("id") != timeslot_id]
                            if available_timeslots:
                                timeslot_id = random.choice(available_timeslots).get("id")
                    
                    # Çakışma kontrolü
                    if project.get("id") not in assigned_projects and (classroom_id, timeslot_id) not in assigned_classrooms_timeslots:
                        # Atamayı ekle
                        assignment = {
                            "project_id": project.get("id"),
                            "classroom_id": classroom_id,
                            "timeslot_id": timeslot_id,
                            "instructors": instructors
                        }
                        
                        new_harmony.append(assignment)
                        assigned_projects.add(project.get("id"))
                        assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
                        continue
            
            # Rastgele bir atama yap (HMCR başarısız olduğunda veya çakışma durumunda)
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
                        
                        new_harmony.append(assignment)
                        assigned_projects.add(project.get("id"))
                        assigned_classrooms_timeslots.add((classroom.get("id"), timeslot.get("id")))
                        assigned = True
                        break
        
        return new_harmony
    
    def _update_harmony_memory(self, new_harmony: List[Dict[str, Any]], new_fitness: float) -> None:
        """
        Harmony belleğini günceller.
        
        Args:
            new_harmony: Yeni harmoni.
            new_fitness: Yeni harmoninin uygunluk değeri.
        """
        # En kötü harmoniyi bul
        worst_idx = min(range(len(self.harmony_memory)), key=lambda i: self.harmony_memory[i]["fitness"])
        worst_fitness = self.harmony_memory[worst_idx]["fitness"]
        
        # Eğer yeni harmoni daha iyiyse, en kötü harmoniyi değiştir
        if new_fitness > worst_fitness:
            self.harmony_memory[worst_idx] = {
                "solution": copy.deepcopy(new_harmony),
                "fitness": new_fitness
            }
            
            # En iyi çözümü güncelle
            if new_fitness > self.best_fitness:
                self.best_solution = copy.deepcopy(new_harmony)
                self.best_fitness = new_fitness
            
            # Uygunluk değerine göre sırala
            self.harmony_memory.sort(key=lambda x: x["fitness"], reverse=True)
    
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