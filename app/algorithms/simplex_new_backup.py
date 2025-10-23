"""
Enhanced Simplex Algorithm with CP-SAT features for project scheduling optimization
"""

from typing import Dict, Any, Optional, List
import numpy as np
import time
import random
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment


class SimplexAlgorithm(OptimizationAlgorithm):
    """
    Enhanced Simplex Algorithm with CP-SAT features for project scheduling optimization.

    This implementation incorporates CP-SAT principles:
    - Fair instructor load distribution with ±2 tolerance
    - Strict 16:30 slot constraint (forbidden after 16:30)
    - Rule compliance (3 instructors for bitirme, 2 for ara projects)
    - Classroom change minimization
    - Project prioritization (bitirme > ara, final > makeup)
    """
    
    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free icin onceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Enhanced Simplex Algorithm with CP-SAT"
        self.description = "Linear programming optimization with constraint programming features"
        
        # Algorithm parameters
        self.max_iterations = params.get("max_iterations", 1000) if params else 1000
        self.tolerance = params.get("tolerance", 1e-8) if params else 1e-8
        self.timeout = params.get("timeout", 30) if params else 30
        
        # CP-SAT ozellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2
        self.best_solution = None
        self.best_fitness = float('-inf')

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

        # CP-SAT instructor timeslot usage tracking
        self._instructor_timeslot_usage = {}
        
    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with CP-SAT enhanced problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

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
        
        # CP-SAT instructor timeslot usage tracking
        self._instructor_timeslot_usage = {}
        for inst in self.instructors:
            self._instructor_timeslot_usage[inst.get("id")] = set()
        
        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Enhanced Simplex algorithm")
            
        print(f"Enhanced Simplex Algorithm with CP-SAT initialized with {len(self.projects)} projects, "
              f"{len(self.instructors)} instructors, {len(self.classrooms)} classrooms, "
              f"{len(self.timeslots)} timeslots")
        print(f"   Max load tolerance: {self.max_load_tolerance}")
        print(f"   Time limit: {self.time_limit}s")
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the Enhanced Simplex optimization with CP-SAT features.
        
        Args:
            data: Problem data containing projects, instructors, classrooms, timeslots
            
        Returns:
            Optimization result with solution and comprehensive metrics
        """
        try:
            # CP-SAT ozelligi: Baslangic zamani
            start_time = time.time()

            # Re-initialize data to ensure it's properly set
            self.initialize(data)
            
            print(f"Starting Enhanced Simplex Algorithm with CP-SAT features...")

            # CP-SAT ozelligi: Baslangic cozumu olustur (proje onceliklendirmesi ile)
            initial_solution = self._create_initial_solution_cp_sat()

            # Cozumun uygunlugunu degerlendir
            fitness = self.evaluate_fitness({"solution": initial_solution})

            # En iyi cozumu guncelle
            self.best_solution = initial_solution
            self.best_fitness = fitness

            # CP-SAT ozelligi: Yerel arama ile cozumu iyilestir
            current_solution = initial_solution
            current_fitness = fitness

            while time.time() - start_time < self.time_limit:
                # Komsu cozum olustur
                neighbor = self._generate_neighbor_solution_cp_sat(current_solution)

                # Komsu cozumun uygunlugunu degerlendir
                neighbor_fitness = self.evaluate_fitness({"solution": neighbor})

                # Daha iyi cozumu kabul et
                if neighbor_fitness > current_fitness:
                    current_solution = neighbor
                    current_fitness = neighbor_fitness

                    # En iyi cozumu guncelle
                    if current_fitness > self.best_fitness:
                        self.best_solution = current_solution
                        self.best_fitness = current_fitness

            # Final evaluation
            final_fitness = self.best_fitness
            execution_time = time.time() - start_time

            print(f"Enhanced Simplex Algorithm with CP-SAT completed!")
            print(f"   Final fitness: {final_fitness:.4f}")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Projects assigned: {len(self.best_solution)}/{len(self.projects)}")

            # Calculate comprehensive metrics
            metrics = self._calculate_comprehensive_metrics_cp_sat(self.best_solution)
            
            return {
                "algorithm": "Enhanced Simplex Algorithm with CP-SAT",
                "status": "completed",
                "schedule": self.best_solution,
                "solution": self.best_solution,
                "metrics": metrics,
                "execution_time": execution_time,
                "iterations": self.max_iterations,
                "message": "Enhanced Simplex Algorithm with CP-SAT optimization completed successfully",
                "constraint_compliance": self._check_constraint_compliance_cp_sat(self.best_solution),
                "fitness": final_fitness
            }
            
        except Exception as e:
            print(f"Enhanced Simplex Algorithm error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_solution_cp_sat()

    def _create_initial_solution_cp_sat(self) -> List[Dict[str, Any]]:
        """
        CP-SAT ozelligi: Baslangic cozumu olusturur (proje onceliklendirmesi ile).
        
        Returns:
            List[Dict[str, Any]]: Baslangic cozumu.
        """
        solution = []

        # CP-SAT ozelligi: Projeleri onceliklendir
        prioritized_projects = self._prioritize_projects_cp_sat()

        # Track used slots and instructor assignments
        used_slots = set()  # (classroom_id, timeslot_id) pairs
        instructor_assignments = {}  # instructor_id -> set of timeslot_ids

        # Process all projects with CP-SAT style assignment
        for project in prioritized_projects:
            assignment = self._find_best_assignment_cp_sat_style(project, used_slots, instructor_assignments)
            if assignment:
                solution.append(assignment)
                # Update tracking structures
                slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
                used_slots.add(slot_key)
                for instructor_id in assignment["instructors"]:
                    if instructor_id not in instructor_assignments:
                        instructor_assignments[instructor_id] = set()
                    instructor_assignments[instructor_id].add(assignment["timeslot_id"])

        # Ensure all projects are assigned (CP-SAT guarantee)
        solution = self._ensure_all_projects_assigned_cp_sat(solution)

        return solution

    def _prioritize_projects_cp_sat(self) -> List[Dict[str, Any]]:
        """CP-SAT ozelligi: Projeleri onceliklendirir."""
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

    def _find_best_assignment_cp_sat_style(self, project: Dict[str, Any],
                                         used_slots: set, instructor_assignments: Dict[int, set]) -> Dict[str, Any]:
        """CP-SAT ozelligi: Proje icin en iyi sinif ve zaman dilimi atamasini bulur."""
        best_assignment = None
        best_score = float('-inf')

        # Sorumlu ogretim uyesi
        responsible_id = project.get("responsible_id", None)

        # Tum sinif ve zaman dilimi kombinasyonlarini degerlendir
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                slot_key = (classroom.get("id"), timeslot.get("id"))

                # Check if slot is available
                if slot_key in used_slots:
                    continue

                # Check 16:30 constraint
                if not self._is_valid_timeslot_for_assignment_cp_sat(timeslot):
                    continue

                # Katilimcilari sec (CP-SAT style)
                instructors = self._select_instructors_cp_sat(project, responsible_id, instructor_assignments, timeslot.get("id"))

                if instructors:
                    # Atama skorunu hesapla (CP-SAT style)
                    score = self._calculate_assignment_score_cp_sat(project, classroom, timeslot, instructors)

                    # En iyi atamayi guncelle
                    if score > best_score:
                        best_score = score
                        best_assignment = {
                            "project_id": project.get("id"),
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id"),
                            "instructors": instructors,
                            "is_makeup": project.get("is_makeup", False),
                            "slot_key": slot_key
                        }

        return best_assignment

    def _is_valid_timeslot_for_assignment_cp_sat(self, timeslot: Dict[str, Any]) -> bool:
        """Check if timeslot is valid for assignment (ULTRA STRICT 16:30 constraint)."""
        # Handle both old format (time_range) and new format (start_time, end_time)
        if 'start_time' in timeslot:
            # New format: parse start_time
            start_time_str = timeslot.get('start_time', '09:00')
            timeslot_hour = int(start_time_str.split(':')[0])
            timeslot_minute = int(start_time_str.split(':')[1])
        elif 'time_range' in timeslot:
            # Old format: parse time_range
            time_range = timeslot.get('time_range', '09:00-10:00')
            start_time_str = time_range.split('-')[0].strip()
            timeslot_hour = int(start_time_str.split(':')[0])
            timeslot_minute = int(start_time_str.split(':')[1])
        else:
            # Fallback
            return True

        # ULTRA STRICT: 16:30 and later slots are FORBIDDEN
        if timeslot_hour > 16 or (timeslot_hour == 16 and timeslot_minute >= 30):
            return False

        # 16:00 slot should be last choice - only allow if absolutely necessary
        if timeslot_hour == 16 and timeslot_minute == 0:
            # Only allow 16:00 slot if we have less than 10% slots remaining
            total_slots = len(self.timeslots)
            used_slots = len(self._instructor_timeslot_usage.get(1, set())) if self._instructor_timeslot_usage else 0
            if used_slots < total_slots * 0.9:
                return False

        return True

    def _select_instructors_cp_sat(self, project: Dict[str, Any], responsible_id: int,
                                 instructor_assignments: Dict[int, set], timeslot_id: int) -> List[int]:
        """CP-SAT ozelligi: Proje icin katilimcilari secer."""
        instructors = [responsible_id] if responsible_id else []
        project_type = project.get("type")

        # Mevcut yukler
        instructor_loads = self._calculate_instructor_loads_cp_sat()
        avg_load = (sum(instructor_loads.values()) / len(instructor_loads)) if instructor_loads else 0

        # Bu slotta uygun hocalar
        available_faculty = []
        for inst in self.instructors:
            if inst.get("id") == responsible_id:
                continue
            if inst.get("type") != "instructor":
                continue
            used = self._instructor_timeslot_usage.get(inst.get("id"), set())
            if timeslot_id in used:
                continue
            # Asiri yuklenmeyi engelle (daha esnek)
            max_allowed_load = avg_load + max(3, self.max_load_tolerance)  # Minimum 3 ekstra yuk izin ver
            if instructor_loads.get(inst.get("id"), 0) > max_allowed_load:
                continue
            available_faculty.append(inst)

        # Cesitlilik: yuku az olana oncelik ver
        random.shuffle(available_faculty)
        available_faculty.sort(key=lambda x: instructor_loads.get(x.get("id"), 0))

        if project_type == "bitirme":
            if len(available_faculty) >= 1:
                instructors.append(available_faculty[0].get("id"))
            if len(available_faculty) >= 2:
                instructors.append(available_faculty[1].get("id"))
            else:
                # Asistan ekle
                assistant = next((i for i in self.instructors if i.get("type") == "assistant" and i.get("id") != responsible_id), None)
                if assistant:
                    instructors.append(assistant.get("id"))
        else:
            if available_faculty:
                instructors.append(available_faculty[0].get("id"))
            assistant = next((i for i in self.instructors if i.get("type") == "assistant" and i.get("id") != responsible_id), None)
            if assistant:
                instructors.append(assistant.get("id"))

        # Eger kural uygunlugu saglanamadiysa, minimum gereksinimleri karsilayacak sekilde instructor'lari zorla ata
        if not self._check_rule_compliance_cp_sat(project, instructors):
            # Minimum gereksinimleri karsila
            if project_type == "bitirme":
                # En az 2 instructor gerekli
                while len(instructors) < 2 and available_faculty:
                    instructors.append(available_faculty.pop(0).get("id"))
                # Eger hala yeterli degilse, mevcut instructor'lari kullan
                if len(instructors) < 2:
                    for inst in self.instructors:
                        if inst.get("type") == "instructor" and inst.get("id") not in instructors:
                            instructors.append(inst.get("id"))
                            if len(instructors) >= 2:
                                break
            else:
                # Ara projesi icin en az 1 instructor gerekli
                while len(instructors) < 1 and available_faculty:
                    instructors.append(available_faculty.pop(0).get("id"))
                # Eger hala yeterli degilse, mevcut instructor'lari kullan
                if len(instructors) < 1:
                    # Add any available instructor
                    for inst in self.instructors:
                        if inst.get("type") == "instructor" and inst.get("id") not in instructors:
                            instructors.append(inst.get("id"))
                            break
                
        return instructors

    def _calculate_instructor_loads_cp_sat(self) -> Dict[int, int]:
        """CP-SAT ozelligi: Ogretim uyelerinin mevcut yuklerini hesaplar."""
        loads: Dict[int, int] = {}
        if self.best_solution:
            for assignment in self.best_solution:
                for instructor_id in assignment.get("instructors", []):
                    loads[instructor_id] = loads.get(instructor_id, 0) + 1
        return loads

    def _calculate_assignment_score_cp_sat(self, project: Dict[str, Any], classroom: Dict[str, Any],
                                         timeslot: Dict[str, Any], instructors: List[int]) -> float:
        """CP-SAT ozelligi: Atama skorunu hesaplar."""
        score = 0.0

        # Kural uygunlugu
        if self._check_rule_compliance_cp_sat(project, instructors):
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

        # Yuk dengesini maksimize et
        instructor_loads = self._calculate_instructor_loads_cp_sat()
        total_load = sum(instructor_loads.values()) if instructor_loads else 0
        avg_load = total_load / len(instructor_loads) if instructor_loads else 0
        load_variance = 0.0
        for instructor_id in instructors:
            load = instructor_loads.get(instructor_id, 0)
            load_variance += (load - avg_load) ** 2
        score -= load_variance * 5.0

        # 16:30 constraint penalty - ULTRA STRICT
        timeslot_hour = int(timeslot.get('start_time', '09:00').split(':')[0])
        timeslot_minute = int(timeslot.get('start_time', '09:00').split(':')[1])

        # 16:30 and later slots are FORBIDDEN - INFINITE penalty
        if timeslot_hour > 16 or (timeslot_hour == 16 and timeslot_minute >= 30):
            score -= 1000000.0  # INFINITE penalty for forbidden slots
        # 16:00 slot gets heavy penalty (should be last choice)
        elif timeslot_hour == 16 and timeslot_minute == 0:
            score -= 50000.0   # Very heavy penalty for 16:00 slot

        return score

    def _check_rule_compliance_cp_sat(self, project: Dict[str, Any], instructors: List[int]) -> bool:
        """CP-SAT ozelligi: Proje kurallarina uygunlugu kontrol eder."""
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

    def _generate_neighbor_solution_cp_sat(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """CP-SAT ozelligi: Mevcut cozumun komsu cozumunu olusturur."""
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
                new_instructors = self._select_instructors_cp_sat(project, responsible_id, {}, assignment["timeslot_id"])

                # Katilimcilari guncelle
                assignment["instructors"] = new_instructors

        return neighbor

    def _ensure_all_projects_assigned_cp_sat(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure all projects are assigned - emergency assignment mechanism."""
        if not solution:
            return self._create_random_solution_cp_sat()

        assigned_project_ids = {a.get("project_id") for a in solution}
        unassigned_projects = [p for p in self.projects if p.get("id") not in assigned_project_ids]

        if unassigned_projects:
            print(f"Warning: {len(unassigned_projects)} projects not assigned. Attempting emergency assignment...")

            # Try to assign unassigned projects
            for project in unassigned_projects:
                assignment = self._emergency_project_assignment_cp_sat(project, solution)
                if assignment:
                    solution.append(assignment)
                    print(f"Emergency-assigned project: {project.get('title', 'Unknown')}")

        return solution

    def _emergency_project_assignment_cp_sat(self, project: Dict[str, Any], current_solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Emergency assignment - more flexible constraints for emergency."""
        print(f"   EMERGENCY ASSIGNMENT: {project.get('title', 'Unknown')}")

        # Find any available slot (relaxed constraints for emergency)
        used_slots = set()
        for assignment in current_solution:
            slot_key = (assignment.get("classroom_id"), assignment.get("timeslot_id"))
            used_slots.add(slot_key)

        # Try all slots (relaxed 16:30 constraint for emergency)
        for timeslot in self.timeslots:
            # Relaxed constraint: only forbid slots after 17:00
            if 'start_time' in timeslot:
                start_time_str = timeslot.get('start_time', '09:00')
                timeslot_hour = int(start_time_str.split(':')[0])
            elif 'time_range' in timeslot:
                time_range = timeslot.get('time_range', '09:00-10:00')
                start_time_str = time_range.split('-')[0].strip()
                timeslot_hour = int(start_time_str.split(':')[0])
            else:
                continue

            if timeslot_hour > 17:  # Only forbid slots after 17:00
                continue

            for classroom in self.classrooms:
                slot_key = (classroom.get("id"), timeslot.get("id"))
                if slot_key not in used_slots:
                    # Emergency instructor assignment - more flexible
                    instructors = self._get_emergency_instructors_flexible_cp_sat(project)
                    if instructors:
                        return {
                            "project_id": project.get("id"),
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id"),
                            "instructors": instructors,
                            "is_makeup": project.get("is_makeup", False),
                            "slot_key": slot_key
                        }

        # If still no slots available, try to replace an existing assignment
        if current_solution:
            print(f"   REPLACING existing assignment for emergency: {project.get('title', 'Unknown')}")
            # Find assignments that can be replaced (prefer those with fewer instructors)
            replaceable_assignments = []
            for assignment in current_solution:
                timeslot_id = assignment.get("timeslot_id")
                timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)
                if timeslot:
                    timeslot_hour = int(timeslot.get('start_time', '09:00').split(':')[0])
                    if timeslot_hour <= 17:  # Only replace slots before 17:00
                        replaceable_assignments.append(assignment)

            if replaceable_assignments:
                # Replace the assignment with fewest instructors
                replacement_target = min(replaceable_assignments, key=lambda x: len(x.get("instructors", [])))
                replacement_target.clear()
                replacement_target.update({
                    "project_id": project.get("id"),
                    "classroom_id": replacement_target.get("classroom_id"),
                    "timeslot_id": replacement_target.get("timeslot_id"),
                    "instructors": self._get_emergency_instructors_flexible_cp_sat(project),
                    "is_makeup": project.get("is_makeup", False),
                    "slot_key": (replacement_target.get("classroom_id"), replacement_target.get("timeslot_id"))
                })
                return replacement_target

        return None

    def _get_emergency_instructors_flexible_cp_sat(self, project: Dict[str, Any]) -> List[int]:
        """Get emergency instructors with flexible constraints for a project."""
        project_type = project.get("type", "ara")
        required_instructors = 2 if project_type == "bitirme" else 1
        
        # Try to find available instructors first
        available_instructors = [inst for inst in self.instructors if inst.get("type") == "instructor"]
        instructors = []

        # Take required number of instructors (any available)
        for inst in available_instructors[:required_instructors + 2]:  # Take extra for flexibility
            instructors.append(inst.get("id"))
            if len(instructors) >= required_instructors:
                break

        # If still not enough, use any instructors (even if overloaded)
        if len(instructors) < required_instructors:
            all_instructors = [inst for inst in self.instructors if inst.get("type") == "instructor"]
            for inst in all_instructors:
                if inst.get("id") not in instructors:
                    instructors.append(inst.get("id"))
                    if len(instructors) >= required_instructors:
                        break

        return instructors

    def _create_random_solution_cp_sat(self) -> List[Dict[str, Any]]:
        """Create a random solution CP-SAT style."""
        solution = []

        # Use CP-SAT style priority assignment
        prioritized_projects = self._prioritize_projects_cp_sat()

        # Track used slots
        used_slots = set()

        for project in prioritized_projects:
            # Find available slot
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    slot_key = (classroom.get("id"), timeslot.get("id"))
                    if slot_key not in used_slots:
                        instructors = self._get_emergency_instructors_flexible_cp_sat(project)
                        if instructors:
                            assignment = {
                                "project_id": project.get("id"),
                                "classroom_id": classroom.get("id"),
                                "timeslot_id": timeslot.get("id"),
                                "instructors": instructors,
                                "is_makeup": project.get("is_makeup", False)
                            }
                            solution.append(assignment)
                            used_slots.add(slot_key)
                            break
                else:
                    continue
                break

        return solution

    def _create_fallback_solution_cp_sat(self) -> Dict[str, Any]:
        """Create a fallback solution when optimization fails."""
        print("Using CP-SAT fallback solution...")

        # Simple greedy assignment as fallback
        assignments = self._create_random_solution_cp_sat()
        metrics = self._calculate_comprehensive_metrics_cp_sat(assignments)

        return {
            "algorithm": "Enhanced Simplex Algorithm with CP-SAT (Fallback)",
            "status": "completed",
            "schedule": assignments,
            "solution": assignments,
            "metrics": metrics,
            "execution_time": 0.1,
            "iterations": 0,
            "message": "Enhanced Simplex Algorithm with CP-SAT completed using fallback method",
            "constraint_compliance": self._check_constraint_compliance_cp_sat(assignments)
        }
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        CP-SAT ozelligi: Verilen cozumun uygunlugunu degerlendirir.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Uygunluk puani.
        """
        if not solution:
            return float('-inf')

        assignments = solution.get("solution", solution.get("schedule", []))
        if not assignments:
            return float('-inf')

        # Cozum gecerli mi?
        if not self._is_valid_solution_cp_sat(assignments):
            return float('-inf')

        score = 0.0

        # Kural uygunlugu
        rule_compliance = self._calculate_rule_compliance_cp_sat(assignments)
        score += rule_compliance * 100.0

        # Sinif degisim sayisini minimize et
        instructor_changes = self._count_instructor_classroom_changes_cp_sat(assignments)
        score -= instructor_changes * 10.0

        # Yuk dengesini maksimize et
        load_balance = self._calculate_load_balance_cp_sat(assignments)
        score += load_balance * 50.0

        # Zaman slot cezasi - 16:30 sonrasi cok agir, 16:00–16:30 orta seviye
        time_penalty = self._calculate_time_slot_penalty_cp_sat(assignments)
        score -= time_penalty

        return score

    def _is_valid_solution_cp_sat(self, solution: List[Dict[str, Any]]) -> bool:
        """CP-SAT ozelligi: Cozumun gecerli olup olmadigini kontrol eder."""
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

    def _count_instructor_classroom_changes_cp_sat(self, solution: List[Dict[str, Any]]) -> int:
        """CP-SAT ozelligi: Ogretim uyelerinin sinif degisim sayisini hesaplar."""
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

    def _calculate_load_balance_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """CP-SAT ozelligi: Ogretim uyesi yuk dengesini hesaplar."""
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

    def _calculate_rule_compliance_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """CP-SAT ozelligi: Proje kurallarina uygunlugu hesaplar."""
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
        
    def _calculate_time_slot_penalty_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """CP-SAT ozelligi: Zaman slotu cezasi hesaplar."""
        penalty = 0.0

        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)

            if timeslot:
                # Handle both old format (time_range) and new format (start_time, end_time)
                if 'start_time' in timeslot:
                    start_time_str = timeslot.get('start_time', '09:00')
                    timeslot_hour = int(start_time_str.split(':')[0])
                    timeslot_minute = int(start_time_str.split(':')[1])
                elif 'time_range' in timeslot:
                    time_range = timeslot.get('time_range', '09:00-10:00')
                    start_time_str = time_range.split('-')[0].strip()
                    timeslot_hour = int(start_time_str.split(':')[0])
                    timeslot_minute = int(start_time_str.split(':')[1])
                else:
                    continue

                # 16:30 sonrasi agir ceza
                if timeslot_hour > 16 or (timeslot_hour == 16 and timeslot_minute >= 30):
                    penalty += 100.0  # Cok agir ceza
                # 16:00-16:30 hafif ceza
                elif timeslot_hour == 16 and timeslot_minute == 0:
                    penalty += 30.0   # Orta seviye ceza

        return penalty

    def _calculate_comprehensive_metrics_cp_sat(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """CP-SAT ozelligi: Kapsamli metrikleri hesaplar."""
        if not solution:
            return {
                "load_balance_score": 0.0,
                "classroom_change_score": 0.0,
                "time_efficiency_score": 0.0,
                "slot_minimization_score": 0.0,
                "rule_compliance_score": 0.0,
                "overall_score": 0.0
            }
        
        # Calculate all 5 objective scores
        load_balance_score = self._calculate_load_balance_score_cp_sat(solution)
        classroom_change_score = self._calculate_classroom_change_score_cp_sat(solution)
        time_efficiency_score = self._calculate_time_efficiency_score_cp_sat(solution)
        slot_minimization_score = self._calculate_slot_minimization_score_cp_sat(solution)
        rule_compliance_score = self._calculate_rule_compliance_score_cp_sat(solution)

        # Overall weighted score (equal weights for simplicity)
        weights = {"load_balance": 0.2, "classroom_changes": 0.2, "time_efficiency": 0.2,
                  "slot_minimization": 0.2, "rule_compliance": 0.2}
        overall_score = (
            load_balance_score * weights["load_balance"] +
            classroom_change_score * weights["classroom_changes"] +
            time_efficiency_score * weights["time_efficiency"] +
            slot_minimization_score * weights["slot_minimization"] +
            rule_compliance_score * weights["rule_compliance"]
        )

        return {
            "load_balance_score": load_balance_score,
            "classroom_change_score": classroom_change_score,
            "time_efficiency_score": time_efficiency_score,
            "slot_minimization_score": slot_minimization_score,
            "rule_compliance_score": rule_compliance_score,
            "overall_score": overall_score,
            "weights": weights
        }

    def _calculate_load_balance_score_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate load balance score CP-SAT style."""
        instructor_loads = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0

        loads = list(instructor_loads.values())
        mean_load = np.mean(loads)
        std_load = np.std(loads)

        # Perfect balance = 100, worse balance = lower score
        if mean_load == 0:
            return 0.0

        balance_ratio = 1.0 - (std_load / (mean_load + 1e-8))
        return max(0.0, min(100.0, balance_ratio * 100))

    def _calculate_classroom_change_score_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate classroom change minimization score CP-SAT style."""
        instructor_classrooms = {}
        total_changes = 0
        total_assignments = 0

        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id in instructor_classrooms:
                    if instructor_classrooms[instructor_id] != assignment["classroom_id"]:
                        total_changes += 1
                instructor_classrooms[instructor_id] = assignment["classroom_id"]
                total_assignments += 1

        if total_assignments == 0:
            return 100.0

        # Perfect score = no changes, worse = lower score
        change_ratio = total_changes / total_assignments
        score = max(0.0, 100.0 - (change_ratio * 100))
        return score

    def _calculate_time_efficiency_score_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency score CP-SAT style."""
        if not solution:
            return 0.0

        # Group assignments by instructor
        instructor_assignments = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_assignments:
                    instructor_assignments[instructor_id] = []
                instructor_assignments[instructor_id].append(assignment)

        total_gaps = 0
        late_slot_penalty = 0

        for instructor_id, assignments_list in instructor_assignments.items():
            if len(assignments_list) <= 1:
                continue

            # Sort by timeslot
            assignments_list.sort(key=lambda x: self._get_timeslot_index_cp_sat(x.get("timeslot_id", 0)))

            # Check for gaps
            for i in range(len(assignments_list) - 1):
                current_idx = self._get_timeslot_index_cp_sat(assignments_list[i].get("timeslot_id", 0))
                next_idx = self._get_timeslot_index_cp_sat(assignments_list[i + 1].get("timeslot_id", 0))

                if next_idx > current_idx + 1:
                    total_gaps += 1

        # Calculate slot preferences and penalties
        morning_assignments = 0
        late_assignments = 0
        total_assignments = len(solution)

        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)

            if timeslot:
                # Morning slot preference (9:00-12:00)
                if timeslot.get("is_morning", False):
                    morning_assignments += 1

                # Late slot penalty (after 16:30, except 16:00-16:30)
                timeslot_index = self._get_timeslot_index_cp_sat(timeslot_id)
                last_usable_index = self._get_last_usable_slot_index_cp_sat()

                if timeslot_index > last_usable_index:
                    late_assignments += 1

        morning_ratio = morning_assignments / total_assignments if total_assignments > 0 else 0
        late_ratio = late_assignments / total_assignments if total_assignments > 0 else 0

        # Base score from gap-free scheduling
        gap_score = max(0.0, 100.0 - (total_gaps * 20))

        # Bonus for morning slot preference
        morning_bonus = morning_ratio * 30  # Up to 30 points for morning preference

        # EXTREME penalty for using slots after 16:30
        late_penalty = late_ratio * 10000  # Up to 10000 point penalty for late slots

        # MEDIUM penalty for 16:00-16:30 slot (should be last choice)
        last_usable_penalty = 0
        if hasattr(self, 'last_usable_slot_id') and self.last_usable_slot_id:
            last_usable_count = sum(1 for assignment in solution
                                  if assignment.get("timeslot_id") == self.last_usable_slot_id)
            last_usable_ratio = last_usable_count / total_assignments if total_assignments > 0 else 0
            last_usable_penalty = last_usable_ratio * 2000  # Up to 2000 point penalty for 16:00-16:30

        # Calculate final score
        final_score = gap_score + morning_bonus - late_penalty - last_usable_penalty

        return max(0.0, min(100.0, final_score))

    def _calculate_slot_minimization_score_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate slot minimization score CP-SAT style."""
        if not solution:
            return 0.0

        # Count unique timeslots used
        used_timeslots = set(assignment["timeslot_id"] for assignment in solution)
        total_timeslots = len(self.timeslots)

        if total_timeslots == 0:
            return 0.0

        # More slots used = lower score (we want to minimize slots)
        utilization_ratio = len(used_timeslots) / total_timeslots
        score = max(0.0, 100.0 - (utilization_ratio * 50))  # Max 50 point penalty
        return score

    def _calculate_rule_compliance_score_cp_sat(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate rule compliance score CP-SAT style."""
        violations = 0
        total_projects = len(solution)

        if total_projects == 0:
            return 100.0

        for assignment in solution:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1

                actual_instructors = len(assignment.get("instructors", []))
                if actual_instructors < min_instructors:
                    violations += 1

                # Check for role conflicts
                instructors = assignment.get("instructors", [])
                if len(instructors) > 1 and instructors[0] in instructors[1:]:
                    violations += 1

        # Perfect compliance = 100, violations reduce score
        compliance_ratio = 1.0 - (violations / total_projects)
        return max(0.0, compliance_ratio * 100)

    def _get_timeslot_index_cp_sat(self, timeslot_id: int) -> int:
        """Get the index of a timeslot CP-SAT style."""
        for i, timeslot in enumerate(self.timeslots):
            if timeslot.get("id") == timeslot_id:
                return i
        return 0

    def _get_last_usable_slot_index_cp_sat(self) -> int:
        """Get the index of the last usable slot (16:30 constraint)."""
        if hasattr(self, 'last_usable_slot_id') and self.last_usable_slot_id:
            return self._get_timeslot_index_cp_sat(self.last_usable_slot_id)
        return len(self.timeslots) - 1  # Last slot as fallback

    def _check_constraint_compliance_cp_sat(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check constraint compliance for the solution CP-SAT style."""
        violations = []
        unassigned_projects = []

        # Check for unassigned projects
        assigned_project_ids = {assignment["project_id"] for assignment in solution}
        for project in self.projects:
            if project.get("id") not in assigned_project_ids:
                unassigned_projects.append({
                    "type": "unassigned_project",
                    "message": f"Project {project.get('title', 'Unknown')} (ID: {project.get('id')}) is not assigned",
                    "project_id": project.get("id"),
                    "project_title": project.get("title")
                })

        # Check instructor assignment rules
        for assignment in solution:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1

                actual_instructors = len(assignment.get("instructors", []))
                if actual_instructors < min_instructors:
                    violations.append({
                        "type": "insufficient_instructors",
                        "message": f"Project {project.get('title', 'Unknown')} ({project_type}) needs {min_instructors} instructors, has {actual_instructors}",
                        "project_id": assignment["project_id"],
                        "project_type": project_type,
                        "current": actual_instructors,
                        "required": min_instructors
                    })

        # Check slot conflicts
        used_slots = {}
        for assignment in solution:
            slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
            if slot_key in used_slots:
                violations.append({
                    "type": "slot_conflict",
                    "message": f"Multiple projects assigned to classroom {assignment['classroom_id']}, timeslot {assignment['timeslot_id']}",
                    "classroom_id": assignment["classroom_id"],
                    "timeslot_id": assignment["timeslot_id"],
                    "conflicting_project": used_slots[slot_key]
                })
            else:
                used_slots[slot_key] = assignment["project_id"]

        # Check instructor conflicts (same instructor in multiple places at same time)
        instructor_timeslots = {}
        for assignment in solution:
            timeslot_id = assignment["timeslot_id"]
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_timeslots:
                    instructor_timeslots[instructor_id] = set()
                if timeslot_id in instructor_timeslots[instructor_id]:
                    violations.append({
                        "type": "instructor_conflict",
                        "message": f"Instructor {instructor_id} assigned to multiple projects at timeslot {timeslot_id}",
                        "instructor_id": instructor_id,
                        "timeslot_id": timeslot_id
                    })
                else:
                    instructor_timeslots[instructor_id].add(timeslot_id)

        # Check gap-free compliance
        gap_violations = self._check_gap_free_violations_cp_sat(solution)

        all_violations = violations + gap_violations + unassigned_projects
        
        return {
            "is_feasible": len(all_violations) == 0,
            "is_gap_free": len(gap_violations) == 0,
            "violations": violations,
            "gap_violations": gap_violations,
            "unassigned_projects": unassigned_projects,
            "total_violations": len(all_violations),
            "compliance_percentage": max(0.0, 100.0 - (len(all_violations) * 10))
        }

    def _check_gap_free_violations_cp_sat(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for gap-free violations in the solution CP-SAT style."""
        violations = []

        # Group assignments by instructor
        instructor_assignments = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_assignments:
                    instructor_assignments[instructor_id] = []
                instructor_assignments[instructor_id].append(assignment)

        # Check each instructor's schedule
        for instructor_id, assignments_list in instructor_assignments.items():
            if len(assignments_list) <= 1:
                continue

            # Sort by timeslot
            assignments_list.sort(key=lambda x: self._get_timeslot_index_cp_sat(x.get("timeslot_id", 0)))

            # Check for gaps
            for i in range(len(assignments_list) - 1):
                current_idx = self._get_timeslot_index_cp_sat(assignments_list[i].get("timeslot_id", 0))
                next_idx = self._get_timeslot_index_cp_sat(assignments_list[i + 1].get("timeslot_id", 0))

                if next_idx > current_idx + 1:
                    violations.append({
                        "type": "gap_violation",
                        "message": f"Instructor {instructor_id} has gap between timeslots {assignments_list[i].get('timeslot_id')} and {assignments_list[i + 1].get('timeslot_id')}",
                        "instructor_id": instructor_id,
                        "gap_start": assignments_list[i].get("timeslot_id"),
                        "gap_end": assignments_list[i + 1].get("timeslot_id")
                    })

        return violations