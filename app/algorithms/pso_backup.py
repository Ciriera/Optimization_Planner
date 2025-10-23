"""
Particle Swarm Optimization (PSO) algoritmasi sinifi - CP-SAT ozellikli versiyon.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
import copy

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class PSO(OptimizationAlgorithm):
    """
    Particle Swarm Optimization (PSO) algoritmasi sinifi.
    Parcacik Suru Optimizasyonu kullanarak proje atama problemini cozer.
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
        PSO algoritmasi baslatici - CP-SAT ozellikli versiyon.

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
        self.n_particles = params.get("n_particles", 30)
        self.n_iterations = params.get("n_iterations", 100)
        self.w = params.get("w", 0.7)  # Eylemsizlik agirligi
        self.c1 = params.get("c1", 1.5)  # Bilissel katsayi
        self.c2 = params.get("c2", 1.5)  # Sosyal katsayi

        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        PSO algoritmasini baslangic verileri ile baslatir - CP-SAT ozellikli versiyon.

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

        # Parcaciklari baslat
        self.particles = self._initialize_particles()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PSO algoritmasini calistirir - CP-SAT ozellikli versiyon.

        Args:
            data: Algoritma giris verileri.

        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        import time
        start_time = time.time()

        # CP-SAT ozelligi: Baslangic cozumu olustur ve degerlendir
        initial_solution = self._create_initial_solution()
        initial_fitness = self.evaluate_fitness({"solution": initial_solution})

        # En iyi cozumu guncelle (CP-SAT ozelligi)
        self.best_solution = initial_solution
        self.best_fitness = initial_fitness

        # CP-SAT ozelligi: Yerel arama ile cozumu iyilestir (zaman limiti icinde)
        while time.time() - start_time < self.time_limit:
            # Her parcacik icin
            for particle in self.particles:
                # Parcacigin mevcut cozumunu degerlendir
                current_fitness = self.evaluate_fitness({"solution": particle["position"]})

                # Parcacigin en iyi konumunu guncelle
                if current_fitness > particle["best_fitness"]:
                    particle["best_position"] = copy.deepcopy(particle["position"])
                    particle["best_fitness"] = current_fitness

                # Global en iyi cozumu guncelle
                if current_fitness > self.best_fitness:
                    self.best_solution = copy.deepcopy(particle["position"])
                    self.best_fitness = current_fitness

                # Parcacigin hizini ve konumunu guncelle
                self._update_velocity_and_position(particle)

        # Sonucu dondur (duplicate guvenli)
        final_schedule = self._deduplicate_assignments(self.best_solution) if isinstance(self.best_solution, list) else self.best_solution
        return {
            "schedule": final_schedule,
            "fitness": self.best_fitness,
            "iterations": self.n_iterations,
            "execution_time": time.time() - start_time
        }
    
    def _initialize_particles(self) -> List[Dict[str, Any]]:
        """
        Parcaciklari baslatir.
        
        Returns:
            List[Dict[str, Any]]: Baslangic parcaciklari.
        """
        particles = []
        
        for _ in range(self.n_particles):
            # Rastgele bir cozum olustur
            position = self._create_random_solution()
            
            # Cozumun uygunlugunu degerlendir
            fitness = self.evaluate_fitness(position)
            
            # Parcacigi olustur
            particle = {
                "position": position,
                "velocity": [],  # Baslangicta bos hiz
                "best_position": copy.deepcopy(position),
                "best_fitness": fitness
            }
            
            # Parcacigi ekle
            particles.append(particle)
            
            # Global en iyi cozumu guncelle
            if fitness > self.best_fitness:
                self.best_solution = copy.deepcopy(position)
                self.best_fitness = fitness
        
        return particles
    
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
    
    def _update_velocity_and_position(self, particle: Dict[str, Any]) -> None:
        """
        Parcacigin hizini ve konumunu gunceller.
        
        Args:
            particle: Guncellenecek parcacik.
        """
        # Ilk iterasyonda hiz olustur
        if not particle["velocity"]:
            particle["velocity"] = self._initialize_velocity()
        
        # Hizi guncelle
        new_velocity = []
        
        for v_op in particle["velocity"]:
            # Eylemsizlik bileseni
            inertia = self.w * random.random()
            
            # Bilissel bilesen (kisisel en iyi)
            cognitive = self.c1 * random.random()
            
            # Sosyal bilesen (global en iyi)
            social = self.c2 * random.random()
            
            # Yeni hiz operasyonu
            if random.random() < inertia:
                new_velocity.append(v_op)
            
            # Bilissel bilesen: Kisisel en iyiye dogru hareket
            if random.random() < cognitive:
                # Kisisel en iyiden bir operasyon sec
                if particle["best_position"]:
                    best_op = self._extract_operation(particle["best_position"])
                    if best_op:
                        new_velocity.append(best_op)
            
            # Sosyal bilesen: Global en iyiye dogru hareket
            if random.random() < social:
                # Global en iyiden bir operasyon sec
                if self.best_solution:
                    global_op = self._extract_operation(self.best_solution)
                    if global_op:
                        new_velocity.append(global_op)
        
        # Hizi sinirla
        max_velocity = 5
        if len(new_velocity) > max_velocity:
            new_velocity = random.sample(new_velocity, max_velocity)
        
        # Hizi guncelle
        particle["velocity"] = new_velocity
        
        # Konumu guncelle (operasyonlari uygula)
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
        
        # Cozumu duzelt (cakismalari gider)
        new_position = self._repair_solution(new_position)
        
        # Konumu guncelle
        particle["position"] = new_position
    
    def _initialize_velocity(self) -> List[Dict[str, Any]]:
        """
        Baslangic hizini olusturur.
        
        Returns:
            List[Dict[str, Any]]: Baslangic hiz operasyonlari.
        """
        velocity = []
        
        # Rastgele 1-3 operasyon olustur
        n_operations = random.randint(1, 3)
        
        for _ in range(n_operations):
            # Rastgele bir operasyon tipi sec
            op_type = random.choice(["swap_classrooms", "swap_timeslots", "change_instructors"])
            
            if op_type == "swap_classrooms":
                # Iki rastgele indeks sec
                idx1 = random.randint(0, max(0, len(self.projects) - 1))
                idx2 = random.randint(0, max(0, len(self.projects) - 1))
                while idx1 == idx2:
                    idx2 = random.randint(0, max(0, len(self.projects) - 1))
                
                velocity.append({
                    "type": "swap_classrooms",
                    "indices": (idx1, idx2)
                })
            
            elif op_type == "swap_timeslots":
                # Iki rastgele indeks sec
                idx1 = random.randint(0, max(0, len(self.projects) - 1))
                idx2 = random.randint(0, max(0, len(self.projects) - 1))
                while idx1 == idx2:
                    idx2 = random.randint(0, max(0, len(self.projects) - 1))
                
                velocity.append({
                    "type": "swap_timeslots",
                    "indices": (idx1, idx2)
                })
            
            elif op_type == "change_instructors":
                # Rastgele bir indeks sec
                idx = random.randint(0, max(0, len(self.projects) - 1))
                
                # Rastgele katilimcilar sec
                project = random.choice(self.projects)
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
                
                velocity.append({
                    "type": "change_instructors",
                    "index": idx,
                    "instructors": instructors
                })
        
        return velocity
    
    def _extract_operation(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cozumden rastgele bir operasyon cikarir.
        
        Args:
            solution: Operasyon cikarilacak cozum.
            
        Returns:
            Dict[str, Any]: Cikarilan operasyon.
        """
        if not solution:
            return None
        
        # Rastgele bir operasyon tipi sec
        op_type = random.choice(["swap_classrooms", "swap_timeslots", "change_instructors"])
        
        if op_type == "swap_classrooms" and len(solution) >= 2:
            # Iki rastgele indeks sec
            idx1, idx2 = random.sample(range(len(solution)), 2)
            
            return {
                "type": "swap_classrooms",
                "indices": (idx1, idx2)
            }
        
        elif op_type == "swap_timeslots" and len(solution) >= 2:
            # Iki rastgele indeks sec
            idx1, idx2 = random.sample(range(len(solution)), 2)
            
            return {
                "type": "swap_timeslots",
                "indices": (idx1, idx2)
            }
        
        elif op_type == "change_instructors" and len(solution) >= 1:
            # Rastgele bir indeks sec
            idx = random.randint(0, len(solution) - 1)
            
            # Mevcut katilimcilari al
            instructors = solution[idx].get("instructors", [])
            
            return {
                "type": "change_instructors",
                "index": idx,
                "instructors": instructors
            }
        
        return None
    
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

    def _calculate_time_slot_penalty(self, solution: List[Dict[str, Any]]) -> float:
        """Standart baz ceza (pozitif) uygular ve fitness tarafindan dusulur."""
        return super()._calculate_time_slot_penalty(solution)

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

    def _calculate_time_slot_penalty(self, solution: List[Dict[str, Any]]) -> float:
        """CP-SAT ozelligi: Zaman slotu cezasi hesaplar."""
        penalty = 0.0

        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)

            if timeslot:
                time_range = timeslot.get("time_range", "")
                # 16:30 sonrasi agir ceza
                if "16:30" in time_range:
                    penalty += 100.0
                # 16:00-16:30 hafif ceza
                elif "16:00" in time_range:
                    penalty += 30.0

        return penalty 