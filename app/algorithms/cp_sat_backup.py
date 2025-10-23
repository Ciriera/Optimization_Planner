"""
CP-SAT (Constraint Programming - SAT) algoritmasi sinifi.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import time

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class CPSAT(OptimizationAlgorithm):
    """
    CP-SAT (Constraint Programming - SAT) algoritmasi sinifi.
    Kisit Programlama ve SAT cozucu kullanarak proje atama problemini cozer.
    
    Not: Bu sinif, gercek bir CP-SAT cozucu kullanmak yerine, CP-SAT yaklasimini simule eder.
    Gercek bir implementasyon icin Google OR-Tools gibi kutuphanelerin kullanilmasi onerilir.
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
        CP-SAT algoritmasi baslatici.

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
        self.time_limit = params.get("time_limit", 60)  # Saniye cinsinden zaman limiti
        self.best_solution = None
        self.best_fitness = float('-inf')
        # Fairness konfigurasyonu
        self.max_load_tolerance = params.get("max_load_tolerance", 2)  # ortalamanin +2 fazlasini gecmesin

    def initialize(self, data: Dict[str, Any]) -> None:
        """
        CP-SAT algoritmasini baslangic verileri ile baslatir.
        
        Args:
            data: Algoritma giris verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        # Tek-slotta ayni hocanin iki projede olmasini engellemek icin slot kullanim haritasi
        self._instructor_timeslot_usage: Dict[int, set] = {}
        for inst in self.instructors:
            self._instructor_timeslot_usage[inst.get("id")] = set()

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CP-SAT algoritmasini calistirir.
        
        Args:
            data: Algoritma giris verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Baslangic zamani
        start_time = time.time()
        
        # Baslangic cozumu olustur
        solution = self._create_initial_solution()
        
        # Cozumun uygunlugunu degerlendir
        fitness = self.evaluate_fitness(solution)
        
        # En iyi cozumu guncelle
        self.best_solution = solution
        self.best_fitness = fitness
        
        # Yerel arama ile cozumu iyilestir
        while time.time() - start_time < self.time_limit:
            # Komsu cozum olustur
            neighbor = self._generate_neighbor(solution)
            
            # Komsu cozumun uygunlugunu degerlendir
            neighbor_fitness = self.evaluate_fitness(neighbor)
            
            # Daha iyi cozumu kabul et
            if neighbor_fitness > fitness:
                solution = neighbor
                fitness = neighbor_fitness
                
                # En iyi cozumu guncelle
                if fitness > self.best_fitness:
                    self.best_solution = solution
                    self.best_fitness = fitness
        
        # Sonucu dondur
        return {
            "schedule": self.best_solution or [],
            "fitness": self.best_fitness,
            "time_limit": self.time_limit
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
        
        # Projeleri onceliklendir
        projects = self._prioritize_projects()
        
        # Her proje icin en iyi atamayi yap
        for project in projects:
            # En iyi sinif ve zaman dilimini bul
            best_assignment = self._find_best_assignment(project, assigned_classrooms_timeslots)
            
            if best_assignment:
                solution.append(best_assignment)
                assigned_projects.add(project.get("id"))
                assigned_classrooms_timeslots.add((best_assignment["classroom_id"], best_assignment["timeslot_id"]))
                # Hocanin slot kullanimini guncelle
                for inst_id in best_assignment.get("instructors", []):
                    self._instructor_timeslot_usage.setdefault(inst_id, set()).add(best_assignment["timeslot_id"]) 
        
        return solution
    
    def _prioritize_projects(self) -> List[Dict[str, Any]]:
        """
        Projeleri onceliklendirir.
        
        Returns:
            List[Dict[str, Any]]: Onceliklendirilmis projeler.
        """
        # Projeleri tipine gore onceliklendir (bitirme > ara)
        bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type") == "ara"]
        
        # Bitirme projelerini butunleme durumuna gore onceliklendir
        bitirme_final = [p for p in bitirme_projects if not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in bitirme_projects if p.get("is_makeup", False)]
        
        # Ara projeleri butunleme durumuna gore onceliklendir
        ara_final = [p for p in ara_projects if not p.get("is_makeup", False)]
        ara_makeup = [p for p in ara_projects if p.get("is_makeup", False)]
        
        # Oncelik sirasi: bitirme_final > ara_final > bitirme_makeup > ara_makeup
        return bitirme_final + ara_final + bitirme_makeup + ara_makeup
    
    def _find_best_assignment(self, project: Dict[str, Any], assigned_classrooms_timeslots: set) -> Dict[str, Any]:
        """
        Proje icin en iyi sinif ve zaman dilimi atamasini bulur.
        
        Args:
            project: Atanacak proje.
            assigned_classrooms_timeslots: Atanmis (sinif, zaman dilimi) ciftleri.
            
        Returns:
            Dict[str, Any]: En iyi atama.
        """
        best_assignment = None
        best_score = float('-inf')
        
        # Sorumlu ogretim uyesi
        responsible_id = project.get("responsible_id", None)
        
        # Tum sinif ve zaman dilimi kombinasyonlarini degerlendir
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                if (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots:
                    # Katilimcilari sec
                    instructors = self._select_instructors(project, responsible_id, timeslot.get("id"))
                    
                    if instructors:
                        # Atama skoru hesapla
                        score = self._calculate_assignment_score(project, classroom, timeslot, instructors)
                        
                        # En iyi atamayi guncelle
                        if score > best_score:
                            best_score = score
                            best_assignment = {
                                "project_id": project.get("id"),
                                "classroom_id": classroom.get("id"),
                                "timeslot_id": timeslot.get("id"),
                                "instructors": instructors
                            }
        
        return best_assignment
    
    def _select_instructors(self, project: Dict[str, Any], responsible_id: str, timeslot_id: int) -> List[str]:
        """
        Proje icin katilimcilari secer (adil dagilim ve slot uygunlugu ile).
        """
        instructors: List[int] = [responsible_id] if responsible_id else []
        project_type = project.get("type")

        # Mevcut yukler
        instructor_loads = self._calculate_instructor_loads()
        avg_load = (sum(instructor_loads.values()) / len(instructor_loads)) if instructor_loads else 0

        # Bu slotta uygun hocalar (ayni slotta iki projede olamaz)
        available_faculty = []
        for inst in self.instructors:
            if inst.get("id") == responsible_id:
                continue
            if inst.get("type") != "instructor":
                continue
            used = self._instructor_timeslot_usage.get(inst.get("id"), set())
            if timeslot_id in used:
                continue
            # Asiri yuklenmeyi engelle (ortalama + tolerans)
            if instructor_loads.get(inst.get("id"), 0) > avg_load + self.max_load_tolerance:
                continue
            available_faculty.append(inst)

        # Cesitlilik: yuku az olana oncelik ver (ve rastgele tie-break)
        random.shuffle(available_faculty)
        available_faculty.sort(key=lambda x: instructor_loads.get(x.get("id"), 0))

        if project_type == "bitirme":
            # Min 2 hoca (sorumlu + 1 hoca) olmali
            if len(available_faculty) >= 1:
                instructors.append(available_faculty[0].get("id"))
            # 3. kisi olarak ikinci bir hoca veya asistan ekle
            third_added = False
            if len(available_faculty) >= 2:
                instructors.append(available_faculty[1].get("id"))
                third_added = True
            if not third_added:
                # Asistan eklenebilir
                assistant = next((i for i in self.instructors if i.get("type") == "assistant" and i.get("id") != responsible_id), None)
                if assistant:
                    instructors.append(assistant.get("id"))
        else:
            # Ara projelerde sorumlu disinda hoca zorunlu degil. Asistan da olabilir.
            # Once hoca eklemeyi dener, yoksa asistan ekler.
            if available_faculty:
                instructors.append(available_faculty[0].get("id"))
            assistant = next((i for i in self.instructors if i.get("type") == "assistant" and i.get("id") != responsible_id), None)
            if assistant:
                instructors.append(assistant.get("id"))

        # Secilenler icin slot kullanimini guncelle (gecici)
        for inst_id in instructors:
            if inst_id is None:
                continue
            self._instructor_timeslot_usage.setdefault(inst_id, set())
        
        # Kural sayisina uyulmuyorsa bos dondur
        if not self._check_rule_compliance(project, instructors):
            return []
        return instructors

    def _calculate_instructor_loads(self) -> Dict[str, int]:
        """
        Ogretim uyelerinin mevcut yuklerini hesaplar.
        
        Returns:
            Dict[str, int]: Ogretim uyesi ID'si -> yuk sayisi.
        """
        loads: Dict[int, int] = {}
        # Mevcut en iyi cozumdeki yukleri hesapla
        if self.best_solution:
            for assignment in self.best_solution:
                for instructor_id in assignment.get("instructors", []):
                    loads[instructor_id] = loads.get(instructor_id, 0) + 1
        return loads

    def _calculate_assignment_score(self, project: Dict[str, Any], classroom: Dict[str, Any], timeslot: Dict[str, Any], instructors: List[str]) -> float:
        """
        Atama skorunu hesaplar.
        """
        score = 0.0
        
        # Kural uygunlugu
        if self._check_rule_compliance(project, instructors):
            score += 100.0
        
        # Sinif degisimlerini minimize et
        if self.best_solution:
            instructor_last_classrooms = {}
            for assignment in self.best_solution:
                for instructor_id in assignment.get("instructors", []):
                    instructor_last_classrooms[instructor_id] = assignment.get("classroom_id")
            changes = 0
            for instructor_id in instructors:
                if instructor_id in instructor_last_classrooms and instructor_last_classrooms[instructor_id] != classroom.get("id"):
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("type") == "instructor":
                        changes += 2
                    else:
                        changes += 1
            score -= changes * 10.0
        
        # Yuk dengesini maksimize et (yuk varyansini azalt)
        instructor_loads = self._calculate_instructor_loads()
        total_load = sum(instructor_loads.values()) if instructor_loads else 0
        avg_load = total_load / len(instructor_loads) if instructor_loads else 0
        load_variance = 0.0
        for instructor_id in instructors:
            load = instructor_loads.get(instructor_id, 0)
            load_variance += (load - avg_load) ** 2
        score -= load_variance * 5.0
        
        # Cesitlilik: hep ayni iki hocayi secmeyi caydir
        diversity_bonus = 0.0
        distinct = len(set(instructors))
        diversity_bonus += max(0.0, (distinct - 2) * 5.0)
        score += diversity_bonus
        
        # Zaman slot odul/ceza (16:30 sonrasi agir ceza ust katmanda hesaplanir)
        try:
            key = self._format_timeslot_key(timeslot)
            rewards = self._get_slot_rewards_map()
            score += rewards.get(key, 0.0) / 10.0
        except Exception:
            pass
        return score
    
    def _check_rule_compliance(self, project: Dict[str, Any], instructors: List[str]) -> bool:
        """
        Proje kurallarina uygunlugu kontrol eder.
        
        Args:
            project: Proje bilgisi.
            instructors: Katilimci ID'leri.
            
        Returns:
            bool: Kurallara uygunsa True, degilse False.
        """
        # Kural 1: Her projede 3 katilimci olmali
        if len(instructors) != 3:
            return False
        
        # Kural 2: Ilk kisi projenin sorumlu hocasi olmali
        if instructors[0] != project.get("responsible_id"):
            return False
        
        # Proje tipine gore kurallar
        project_type = project.get("type")
        
        if project_type == "bitirme":
            # Kural 3: Bitirme projesinde en az 2 hoca olmali
            hoca_count = 0
            for instructor_id in instructors:
                instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                if instructor and instructor.get("type") == "instructor":
                    hoca_count += 1
            
            if hoca_count < 2:
                return False
        
        elif project_type == "ara":
            # Kural 4: Ara projede en az 1 hoca olmali
            has_hoca = False
            for instructor_id in instructors:
                instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                if instructor and instructor.get("type") == "instructor":
                    has_hoca = True
                    break
            
            if not has_hoca:
                return False
        
        return True
    
    def _generate_neighbor(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mevcut cozumun komsu cozumunu olusturur.
        
        Args:
            solution: Mevcut cozum.
            
        Returns:
            List[Dict[str, Any]]: Komsu cozum.
        """
        if not solution:
            return solution
        
        # Cozumun bir kopyasini olustur
        neighbor = [assignment.copy() for assignment in solution]
        
        # Rastgele bir degisiklik yap
        change_type = random.choice(["swap_classrooms", "swap_timeslots", "swap_instructors"])
        
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
                
                # Yeni katilimcilar sec
                new_instructors = self._select_instructors(project, responsible_id, assignment["timeslot_id"])
                
                # Katilimcilari guncelle
                assignment["instructors"] = new_instructors
        
        return neighbor
    
    def evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
        """
        Verilen cozumun uygunlugunu degerlendirir.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Uygunluk puani.
        """
        # Cozum gecerli mi?
        if not self._is_valid_solution(solution):
            return float('-inf')
        
        score = 0.0
        
        # Kural uygunlugu
        rule_compliance = self._calculate_rule_compliance(solution)
        score += rule_compliance * 100.0
        
        # Sinif degisim sayisini minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        score -= instructor_changes * 10.0
        
        # Yuk dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        score += load_balance * 50.0

        # Zaman slot cezasi - 16:30 sonrasi cok agir, 16:00–16:30 orta seviye
        time_penalty = getattr(self, "_calculate_time_slot_penalty", lambda s: 0.0)(solution)
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