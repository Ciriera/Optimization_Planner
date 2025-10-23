"""
Tabu Search (Tabu Arama) algoritmasi sinifi - CP-SAT ozellikli versiyon.
"""
from typing import Dict, Any, List, Tuple, Set
import random
import numpy as np
import hashlib
from collections import deque

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class TabuSearch(OptimizationAlgorithm):
    """
    Tabu Search (Tabu Arama) algoritmasi sinifi.
    Tabu Arama kullanarak proje atama problemini cozer.
    """
    
    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free icin onceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Dict[str, Any] = None):
        """
        Tabu Search algoritmasi baslatici - CP-SAT ozellikli versiyon.

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors

        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.max_iterations = params.get("max_iterations", 300)  # Increased for better exploration
        self.tabu_list_size = params.get("tabu_list_size", 25)   # Slightly larger tabu list
        self.neighborhood_size = params.get("neighborhood_size", 40)  # Larger neighborhood
        self.aspiration_value = params.get("aspiration_value", 15.0)  # Higher aspiration threshold

        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Tabu Search algoritmasini baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # CP-SAT ozelligi: instructor timeslot kullanim takibi
        self._instructor_timeslot_usage = {}
        for inst in self.instructors:
            self._instructor_timeslot_usage[inst.get("id")] = set()

        # Tabu listesi (FIFO queue)
        self.tabu_list = deque(maxlen=self.tabu_list_size)
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tabu Search algoritmasini calistirir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.

        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        import time
        start_time = time.time()

        # CP-SAT ozelligi: Baslangic cozumu olustur ve degerlendir
        current_solution = self._create_initial_solution()
        current_fitness = self.evaluate_fitness({"solution": current_solution})

        # En iyi cozumu baslat (CP-SAT ozelligi)
        self.best_solution = current_solution
        self.best_fitness = current_fitness
        
        # Iterasyon sayaci
        iterations_without_improvement = 0
        
        # CP-SAT ozelligi: Ana dongu (zaman limiti icinde)
        iteration = 0
        while time.time() - start_time < self.time_limit and iteration < self.max_iterations:
            # Komsu cozumler olustur
            neighbors = self._generate_neighbors(current_solution)
            
            # En iyi komsuyu bul
            best_neighbor = None
            best_neighbor_fitness = float('-inf')
            
            for neighbor in neighbors:
                # Cozumun hash'ini hesapla
                neighbor_hash = self._hash_solution(neighbor)
                
                # Cozumun uygunlugunu degerlendir
                neighbor_fitness = self.evaluate_fitness(neighbor)
                
                # Tabu listesinde olmayan veya aspirasyon kriterini saglayan komsulari degerlendir
                if (neighbor_hash not in self.tabu_list or 
                    neighbor_fitness > self.best_fitness + self.aspiration_value):
                    if neighbor_fitness > best_neighbor_fitness:
                        best_neighbor = neighbor
                        best_neighbor_fitness = neighbor_fitness
            
            # Eger komsu bulunamadiysa, yeni bir cozum olustur
            if best_neighbor is None:
                current_solution = self._create_initial_solution()
                current_fitness = self.evaluate_fitness(current_solution)
                continue
            
            # Mevcut cozumu guncelle
            current_solution = best_neighbor
            current_fitness = best_neighbor_fitness
            
            # Tabu listesine ekle
            self.tabu_list.append(self._hash_solution(current_solution))
            
            # En iyi cozumu guncelle
            if current_fitness > self.best_fitness:
                self.best_solution = current_solution
                self.best_fitness = current_fitness
                iterations_without_improvement = 0
            else:
                iterations_without_improvement += 1
            
            # Belirli sayida iterasyon boyunca iyilesme olmazsa, yeni bir cozum olustur
            if iterations_without_improvement > 20:
                current_solution = self._create_initial_solution()
                current_fitness = self.evaluate_fitness({"solution": current_solution})
                iterations_without_improvement = 0

            iteration += 1
        
        # Sonucu dondur
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "iterations": iteration,
            "execution_time": time.time() - start_time
        }
    
    def _create_initial_solution(self) -> List[Dict[str, Any]]:
        """
        Baslangic cozumu olusturur.
        
        Returns:
            List[Dict[str, Any]]: Baslangic cozumu.
        """
        solution = []
        
        # Proje, sinif ve zaman dilimi atamalarini takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) ciftleri
        
        # Projeleri rastgele sirala
        projects = list(self.projects)
        random.shuffle(projects)
        
        for project in projects:
            # Rastgele bir sinif ve zaman dilimi sec
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
                        # Sorumlu ogretim uyesi
                        responsible_id = project.get("responsible_id", None)
                        instructors = [responsible_id] if responsible_id else []
                        
                        # Rastgele 1-2 yardimci katilimci ekle
                        available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
                        if available_instructors:
                            # Proje tipine gore katilimci sayisini belirle
                            if project.get("type") == "bitirme":
                                # Bitirme projesi icin en az 2 hoca olmali
                                hocas = [i for i in available_instructors if i.get("type") == "instructor"]
                                aras_gors = [i for i in available_instructors if i.get("type") == "assistant"]
                                
                                if len(hocas) > 0:
                                    # En az bir hoca ekle
                                    instructors.append(random.choice(hocas).get("id"))
                                    
                                    # Ucuncu kisi olarak hoca veya aras. gor. ekle
                                    if len(hocas) > 1 and random.random() > 0.5:
                                        instructors.append(random.choice(hocas).get("id"))
                                    elif aras_gors:
                                        instructors.append(random.choice(aras_gors).get("id"))
                            else:
                                # Ara proje icin rastgele 2 kisi ekle
                                selected = random.sample(available_instructors, min(2, len(available_instructors)))
                                for instructor in selected:
                                    instructors.append(instructor.get("id"))
                        
                        # Atamayi ekle
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
        Mevcut cozumun komsu cozumlerini olusturur.
        
        Args:
            solution: Mevcut cozum.
            
        Returns:
            List[List[Dict[str, Any]]]: Komsu cozumler.
        """
        neighbors = []
        
        # Belirli sayida komsu olustur
        for _ in range(self.neighborhood_size):
            # Rastgele bir degisiklik yap
            change_type = random.choice(["swap_classrooms", "swap_timeslots", "swap_instructors", "reassign"])
            
            # Cozumun bir kopyasini olustur
            neighbor = [assignment.copy() for assignment in solution]
            
            if change_type == "swap_classrooms" and len(neighbor) >= 2:
                # Iki atama arasinda siniflari degistir
                idx1, idx2 = random.sample(range(len(neighbor)), 2)
                neighbor[idx1]["classroom_id"], neighbor[idx2]["classroom_id"] = neighbor[idx2]["classroom_id"], neighbor[idx1]["classroom_id"]
            
            elif change_type == "swap_timeslots" and len(neighbor) >= 2:
                # Iki atama arasinda zaman dilimlerini degistir
                idx1, idx2 = random.sample(range(len(neighbor)), 2)
                neighbor[idx1]["timeslot_id"], neighbor[idx2]["timeslot_id"] = neighbor[idx2]["timeslot_id"], neighbor[idx1]["timeslot_id"]
            
            elif change_type == "swap_instructors" and len(neighbor) >= 1:
                # Bir atamada yardimci katilimcilari degistir
                idx = random.randint(0, len(neighbor) - 1)
                assignment = neighbor[idx]
                
                # Projeyi bul
                project_id = assignment["project_id"]
                project = next((p for p in self.projects if p.get("id") == project_id), None)
                
                if project:
                    # Sorumlu ogretim uyesi
                    responsible_id = project.get("responsible_id")
                    instructors = [responsible_id] if responsible_id else []
                    
                    # Rastgele 1-2 yardimci katilimci ekle
                    available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
                    if available_instructors:
                        # Proje tipine gore katilimci sayisini belirle
                        if project.get("type") == "bitirme":
                            # Bitirme projesi icin en az 2 hoca olmali
                            hocas = [i for i in available_instructors if i.get("type") == "instructor"]
                            aras_gors = [i for i in available_instructors if i.get("type") == "assistant"]
                            
                            if len(hocas) > 0:
                                # En az bir hoca ekle
                                instructors.append(random.choice(hocas).get("id"))
                                
                                # Ucuncu kisi olarak hoca veya aras. gor. ekle
                                if len(hocas) > 1 and random.random() > 0.5:
                                    instructors.append(random.choice(hocas).get("id"))
                                elif aras_gors:
                                    instructors.append(random.choice(aras_gors).get("id"))
                        else:
                            # Ara proje icin rastgele 2 kisi ekle
                            selected = random.sample(available_instructors, min(2, len(available_instructors)))
                            for instructor in selected:
                                instructors.append(instructor.get("id"))
                    
                    # Katilimcilari guncelle
                    assignment["instructors"] = instructors
            
            elif change_type == "reassign" and len(neighbor) >= 1:
                # Rastgele bir atamayi yeniden yap
                idx = random.randint(0, len(neighbor) - 1)
                assignment = neighbor[idx]
                
                # Projeyi bul
                project_id = assignment["project_id"]
                project = next((p for p in self.projects if p.get("id") == project_id), None)
                
                if project:
                    # Rastgele bir sinif ve zaman dilimi sec
                    classroom = random.choice(self.classrooms)
                    timeslot = random.choice(self.timeslots)
                    
                    # Sorumlu ogretim uyesi
                    responsible_id = project.get("responsible_id")
                    instructors = [responsible_id] if responsible_id else []
                    
                    # Rastgele 1-2 yardimci katilimci ekle
                    available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
                    if available_instructors:
                        # Proje tipine gore katilimci sayisini belirle
                        if project.get("type") == "bitirme":
                            # Bitirme projesi icin en az 2 hoca olmali
                            hocas = [i for i in available_instructors if i.get("type") == "instructor"]
                            aras_gors = [i for i in available_instructors if i.get("type") == "assistant"]
                            
                            if len(hocas) > 0:
                                # En az bir hoca ekle
                                instructors.append(random.choice(hocas).get("id"))
                                
                                # Ucuncu kisi olarak hoca veya aras. gor. ekle
                                if len(hocas) > 1 and random.random() > 0.5:
                                    instructors.append(random.choice(hocas).get("id"))
                                elif aras_gors:
                                    instructors.append(random.choice(aras_gors).get("id"))
                        else:
                            # Ara proje icin rastgele 2 kisi ekle
                            selected = random.sample(available_instructors, min(2, len(available_instructors)))
                            for instructor in selected:
                                instructors.append(instructor.get("id"))
                    
                    # Atamayi guncelle
                    assignment["classroom_id"] = classroom.get("id")
                    assignment["timeslot_id"] = timeslot.get("id")
                    assignment["instructors"] = instructors
            
            # Cozumu duzelt (cakismalari gider)
            neighbor = self._repair_solution(neighbor)
            
            # Komsuyu ekle
            neighbors.append(neighbor)
        
        return neighbors
    
    def _repair_solution(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cozumdeki cakismalari giderir.
        
        Args:
            solution: Duzeltilecek cozum.
            
        Returns:
            List[Dict[str, Any]]: Duzeltilmis cozum.
        """
        # Proje, sinif ve zaman dilimi atamalarini takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) ciftleri
        
        # Gecerli atamalari koru
        valid_assignments = []
        
        for assignment in solution:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Cakisma kontrolu
            if project_id not in assigned_projects and (classroom_id, timeslot_id) not in assigned_classrooms_timeslots:
                valid_assignments.append(assignment)
                assigned_projects.add(project_id)
                assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
        
        return valid_assignments
    
    def _hash_solution(self, solution: List[Dict[str, Any]]) -> str:
        """
        Cozumun benzersiz bir hash degerini hesaplar.
        
        Args:
            solution: Hash'i hesaplanacak cozum.
            
        Returns:
            str: Cozumun hash degeri.
        """
        # Cozumu sirala (deterministik hash icin)
        sorted_solution = sorted(solution, key=lambda x: (x["project_id"], x["classroom_id"], x["timeslot_id"]))
        
        # Cozumu string'e donustur
        solution_str = str(sorted_solution)
        
        # Hash hesapla
        return hashlib.md5(solution_str.encode()).hexdigest()
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """CP-SAT ozelligi: Verilen cozumun uygunlugunu degerlendirir."""
        if not solution:
            return float('-inf')

        assignments = solution.get("solution", solution.get("schedule", solution))
        if not assignments:
            return float('-inf')

        # Cozum gecerli mi?
        if not self._is_valid_solution(assignments):
            return float('-inf')

        score = 0.0

        # Kural uygunlugu
        rule_compliance = self._calculate_rule_compliance(assignments)
        score += rule_compliance * 100.0

        # Sinif degisim sayisini minimize et
        instructor_changes = self._count_instructor_classroom_changes(assignments)
        score -= instructor_changes * 10.0

        # Yuk dengesini maksimize et
        load_balance = self._calculate_load_balance(assignments)
        score += load_balance * 50.0

        # Zaman slot cezasi - 16:30 sonrasi cok agir, 16:00–16:30 orta seviye
        time_penalty = self._calculate_time_slot_penalty(assignments)
        score -= time_penalty

        return score
    
    def _is_valid_solution(self, solution: List[Dict[str, Any]]) -> bool:
        """
        Cozumun gecerli olup olmadigini kontrol eder.
        
        Args:
            solution: Kontrol edilecek cozum.
            
        Returns:
            bool: Cozum gecerliyse True, degilse False.
        """
        if not solution:
            return False
        
        # Proje, sinif ve zaman dilimi atamalarini takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) ciftleri
        
        for assignment in solution:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Bir proje birden fazla kez atanmamali
            if project_id in assigned_projects:
                return False
            
            # Bir sinif-zaman dilimi cifti birden fazla kez atanmamali
            if (classroom_id, timeslot_id) in assigned_classrooms_timeslots:
                return False
            
            assigned_projects.add(project_id)
            assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
        
        return True
    
    def _count_instructor_classroom_changes(self, solution: List[Dict[str, Any]]) -> int:
        """
        Ogretim uyelerinin sinif degisim sayisini hesaplar.
        
        Args:
            solution: Atama plani
            
        Returns:
            int: Toplam sinif degisim sayisi
        """
        if not solution:
            return 0
        
        # Ogretim uyesi basina sinif degisim sayisini hesapla
        instructor_locations = {}
        changes = 0
        
        # Zaman dilimine gore sirala
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
        Ogretim uyesi yuk dengesini hesaplar.
        
        Args:
            solution: Atama plani
            
        Returns:
            float: Yuk dengesi skoru (0-1 arasi, 1 en iyi)
        """
        if not solution:
            return 0.0
        
        # Ogretim uyesi basina atama sayisini hesapla
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment["instructors"]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        # Yuk dengesini hesapla (Gini katsayisi)
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        
        # Gini katsayisi hesapla
        array = np.array(loads, dtype=np.float64)
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1, dtype=np.float64)
        n = float(array.shape[0])
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
        
        # Gini katsayisi 0 (tam esitlik) ile 1 (tam esitsizlik) arasindadir
        # Biz dengeyi istedigimiz icin 1 - gini donduruyoruz
        return 1.0 - gini
    
    def _calculate_rule_compliance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Proje kurallarina uygunlugu hesaplar.
        
        Args:
            solution: Atama plani
            
        Returns:
            float: Kural uygunluk skoru (0-1 arasi, 1 en iyi)
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
            
            # Kural 1: Her projede 3 katilimci olmali
            total_rules += 1
            if len(instructors) == 3:
                satisfied_rules += 1
            
            # Kural 2: Ilk kisi projenin sorumlu hocasi olmali
            total_rules += 1
            if instructors and instructors[0] == project.get("responsible_id"):
                satisfied_rules += 1
            
            # Proje tipine gore kurallar
            if project.get("type") == "bitirme":
                # Kural 3: Bitirme projesinde en az 2 hoca olmali
                total_rules += 1
                hoca_count = 0
                for instructor_id in instructors:
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("type") == "instructor":
                        hoca_count += 1
                
                if hoca_count >= 2:
                    satisfied_rules += 1
            
            elif project.get("type") == "ara":
                # Kural 4: Ara projede en az 1 hoca olmali
                total_rules += 1
                has_hoca = False
                for instructor_id in instructors:
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("type") == "instructor":
                        has_hoca = True
                        break
                
                if has_hoca:
                    satisfied_rules += 1
        
        # Kural uygunluk oranini hesapla
        if total_rules > 0:
            return satisfied_rules / total_rules
        else:
            return 0.0 