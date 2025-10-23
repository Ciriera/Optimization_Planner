"""
Grey Wolf Optimizer (Gri Kurt Optimizasyonu) algoritmasi sinifi - CP-SAT ozellikli versiyon.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class GreyWolf(OptimizationAlgorithm):
    """
    Grey Wolf Optimizer (Gri Kurt Optimizasyonu) algoritmasi sinifi.
    Gri Kurt Optimizasyonu kullanarak proje atama problemini cozer.
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
        Grey Wolf Optimizer algoritmasi baslatici - CP-SAT ozellikli versiyon.

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
        self.n_wolves = params.get("n_wolves", 30)
        self.n_iterations = params.get("n_iterations", 100)
        self.a_decrease_factor = params.get("a_decrease_factor", 2.0)

        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Grey Wolf Optimizer algoritmasini baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

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

        # Kurtlari baslat
        self.wolves = self._initialize_wolves()

        # Alpha, Beta ve Delta kurtlari
        self.alpha = {"position": None, "fitness": float('-inf')}
        self.beta = {"position": None, "fitness": float('-inf')}
        self.delta = {"position": None, "fitness": float('-inf')}

        # Kurtlari sirala
        self._sort_wolves()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grey Wolf Optimizer algoritmasini calistirir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.

        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        import time
        start_time = time.time()

        # CP-SAT ozelligi: Baslangic cozumu olustur ve degerlendir
        initial_wolf = self._create_initial_solution()
        initial_fitness = self.evaluate_fitness({"solution": initial_wolf})

        # En iyi cozumu guncelle (CP-SAT ozelligi)
        self.best_solution = initial_wolf
        self.best_fitness = initial_fitness

        # CP-SAT ozelligi: Yerel arama ile cozumu iyilestir (zaman limiti icinde)
        iteration = 0
        while time.time() - start_time < self.time_limit and iteration < self.n_iterations:
            # a parametresini guncelle
            a = self.a_decrease_factor - iteration * (self.a_decrease_factor / self.n_iterations)
            
            # Her kurt icin
            for i in range(self.n_wolves):
                # Kurdu hareket ettir
                self._move_wolf(i, a)
                
                # Kurdun uygunlugunu yeniden degerlendir
                self.wolves[i]["fitness"] = self.evaluate_fitness(self.wolves[i]["position"])
            
            # Kurtlari sirala
            self._sort_wolves()

            iteration += 1

        # Sonucu dondur (duplicate guvenli)
        final_schedule = self._deduplicate_assignments(self.best_solution) if isinstance(self.best_solution, list) else self.best_solution
        return {
            "schedule": final_schedule,
            "fitness": self.best_fitness,
            "iterations": iteration,
            "execution_time": time.time() - start_time
        }
    
    def _initialize_wolves(self) -> List[Dict[str, Any]]:
        """
        Kurtlari baslatir.
        
        Returns:
            List[Dict[str, Any]]: Baslangic kurtlari.
        """
        wolves = []
        
        for _ in range(self.n_wolves):
            # Rastgele bir cozum olustur
            position = self._create_random_solution()
            
            # Cozumun uygunlugunu degerlendir
            fitness = self.evaluate_fitness(position)
            
            # Kurdu olustur
            wolf = {
                "position": position,
                "fitness": fitness
            }
            
            # Kurdu ekle
            wolves.append(wolf)
            
            # En iyi cozumu guncelle
            if fitness > self.best_fitness:
                self.best_solution = copy.deepcopy(position)
                self.best_fitness = fitness
        
        return wolves
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """
        Rastgele bir cozum olusturur.
        
        Returns:
            List[Dict[str, Any]]: Rastgele cozum.
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
    
    def _sort_wolves(self) -> None:
        """
        Kurtlari uygunluk degerine gore siralar ve Alpha, Beta, Delta kurtlarini gunceller.
        """
        # Kurtlari uygunluk degerine gore sirala
        sorted_wolves = sorted(self.wolves, key=lambda x: x["fitness"], reverse=True)
        
        # Alpha, Beta ve Delta kurtlarini guncelle
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
        
        # En iyi cozumu guncelle
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
        
        # Alpha, Beta ve Delta kurtlarinin cozumleri
        alpha_pos = self.alpha["position"]
        beta_pos = self.beta["position"]
        delta_pos = self.delta["position"]
        
        # Eger lider kurtlar henuz belirlenmemisse
        if alpha_pos is None or beta_pos is None or delta_pos is None:
            return
        
        # Yeni cozumu olustur
        new_position = self._generate_new_position(wolf["position"], alpha_pos, beta_pos, delta_pos, a)
        
        # Yeni cozumu kurda ata
        wolf["position"] = new_position
    
    def _generate_new_position(self, wolf_pos: List[Dict[str, Any]], alpha_pos: List[Dict[str, Any]], beta_pos: List[Dict[str, Any]], delta_pos: List[Dict[str, Any]], a: float) -> List[Dict[str, Any]]:
        """
        Alpha, Beta ve Delta kurtlarina gore yeni bir cozum olusturur.
        
        Args:
            wolf_pos: Kurt cozumu.
            alpha_pos: Alpha kurt cozumu.
            beta_pos: Beta kurt cozumu.
            delta_pos: Delta kurt cozumu.
            a: a parametresi.
            
        Returns:
            List[Dict[str, Any]]: Yeni cozum.
        """
        # Yeni cozum icin temel olarak wolf_pos'u kullan
        new_position = copy.deepcopy(wolf_pos)
        
        # Cozumleri proje ID'lerine gore sirala
        sorted_alpha_pos = sorted(alpha_pos, key=lambda x: x["project_id"]) if alpha_pos else []
        sorted_beta_pos = sorted(beta_pos, key=lambda x: x["project_id"]) if beta_pos else []
        sorted_delta_pos = sorted(delta_pos, key=lambda x: x["project_id"]) if delta_pos else []
        
        # Her atama icin
        for i, assignment in enumerate(new_position):
            # Rastgele A ve C katsayilari
            A1 = 2 * a * random.random() - a
            A2 = 2 * a * random.random() - a
            A3 = 2 * a * random.random() - a
            
            C1 = 2 * random.random()
            C2 = 2 * random.random()
            C3 = 2 * random.random()
            
            # Ayni projeye ait atamalari bul
            project_id = assignment["project_id"]
            alpha_assignment = next((a for a in sorted_alpha_pos if a.get("project_id") == project_id), None)
            beta_assignment = next((a for a in sorted_beta_pos if a.get("project_id") == project_id), None)
            delta_assignment = next((a for a in sorted_delta_pos if a.get("project_id") == project_id), None)
            
            # Eger tum lider kurtlarda bu proje icin atama varsa
            if alpha_assignment and beta_assignment and delta_assignment:
                # Sinif icin
                if abs(A1) < 1 and alpha_assignment.get("classroom_id"):
                    assignment["classroom_id"] = alpha_assignment["classroom_id"]
                elif abs(A2) < 1 and beta_assignment.get("classroom_id"):
                    assignment["classroom_id"] = beta_assignment["classroom_id"]
                elif abs(A3) < 1 and delta_assignment.get("classroom_id"):
                    assignment["classroom_id"] = delta_assignment["classroom_id"]
                
                # Zaman dilimi icin
                if abs(A1) < 1 and alpha_assignment.get("timeslot_id"):
                    assignment["timeslot_id"] = alpha_assignment["timeslot_id"]
                elif abs(A2) < 1 and beta_assignment.get("timeslot_id"):
                    assignment["timeslot_id"] = beta_assignment["timeslot_id"]
                elif abs(A3) < 1 and delta_assignment.get("timeslot_id"):
                    assignment["timeslot_id"] = delta_assignment["timeslot_id"]
                
                # Katilimcilar icin
                if abs(A1) < 1 and alpha_assignment.get("instructors"):
                    assignment["instructors"] = copy.deepcopy(alpha_assignment["instructors"])
                elif abs(A2) < 1 and beta_assignment.get("instructors"):
                    assignment["instructors"] = copy.deepcopy(beta_assignment["instructors"])
                elif abs(A3) < 1 and delta_assignment.get("instructors"):
                    assignment["instructors"] = copy.deepcopy(delta_assignment["instructors"])
            
            # Kesif: Rastgele degisiklik yap
            if abs(A1) >= 1 or abs(A2) >= 1 or abs(A3) >= 1:
                # Rastgele bir degisiklik tipi sec
                change_type = random.choice(["classroom", "timeslot", "instructors"])
                
                if change_type == "classroom":
                    # Sinifi degistir
                    available_classrooms = [c for c in self.classrooms if c.get("id") != assignment["classroom_id"]]
                    if available_classrooms:
                        assignment["classroom_id"] = random.choice(available_classrooms).get("id")
                
                elif change_type == "timeslot":
                    # Zaman dilimini degistir
                    available_timeslots = [t for t in self.timeslots if t.get("id") != assignment["timeslot_id"]]
                    if available_timeslots:
                        assignment["timeslot_id"] = random.choice(available_timeslots).get("id")
                
                elif change_type == "instructors":
                    # Projeyi bul
                    project = next((p for p in self.projects if p.get("id") == project_id), None)
                    
                    if project:
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
                            
                            # Katilimcilari guncelle
                            assignment["instructors"] = instructors
        
        # Cozumu duzelt (cakismalari gider)
        new_position = self._repair_solution(new_position)
        
        return new_position
    
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

    def _calculate_time_slot_penalty(self, solution: List[Dict[str, Any]]) -> float:
        """Standart baz ceza (pozitif) uygular ve fitness tarafindan dusulur."""
        return super()._calculate_time_slot_penalty(solution)
    
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