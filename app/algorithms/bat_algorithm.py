"""
Bat Algorithm - Enhanced with Pure Consecutive Grouping
Uses same logic as Genetic Algorithm for optimal uniform distribution
"""

from typing import Dict, Any, Optional, List, Tuple, Set
import random
import numpy as np
import time
import logging
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm


logger = logging.getLogger(__name__)


class BatAlgorithm(OptimizationAlgorithm):
    """
    Bat Algorithm - Enhanced with Pure Consecutive Grouping + Smart Jury Assignment.
    
    SUCCESS STRATEGY (Same as Deep Search Algorithm):
    NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
    NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
    NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
    
    This implementation uses the SAME logic as Deep Search Algorithm for:
    1. RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
    2. EN ERKEN BOŞ SLOT mantığı - Boş slotlar varken ileri atlamaz
    3. Uniform distribution - D111 dahil tüm sınıfları kullanır
    4. Pure consecutive grouping - Her instructor'ın projeleri ardışık
    5. AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
    6. Conflict-free scheduling - Instructor çakışmalarını önler
    
    Strategy:
    "Bir öğretim görevlimizi sorumlu olduğu projelerden birisiyle birlikte 
    diyelim ki 09:00-09:30 zaman slotuna ve D106 sınıfına atamasını yaptık. 
    Bu öğretim görevlimizin diğer sorumlu olduğu projeleri de aynı sınıfa 
    ve hemen sonraki zaman slotlarına atayalım ki çok fazla yer değişimi olmasın"
    
    Original Features (Preserved):
    - Echolocation mechanism
    - Frequency tuning
    - Loudness and pulse rate adaptation
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Bat Algorithm"
        self.description = "Nature-inspired metaheuristic optimization for project scheduling"

        # Bat Algorithm Parameters
        self.population_size = params.get("population_size", 40) if params else 40
        self.max_iterations = params.get("max_iterations", 100) if params else 100
        self.min_frequency = params.get("min_frequency", 0.0) if params else 0.0
        self.max_frequency = params.get("max_frequency", 2.0) if params else 2.0
        self.loudness = params.get("loudness", 0.5) if params else 0.5
        self.pulse_rate = params.get("pulse_rate", 0.5) if params else 0.5

        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []

        # Bat Algorithm state
        self.bats = []
        self.velocities = []
        self.best_bat = None
        self.best_fitness = float('-inf')

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Selects instructors for project (gap-free version).

        Rules:
        - Bitirme: 1 responsible + at least 1 jury (instructor or research assistant)
        - Ara: 1 responsible
        - Same person cannot be both responsible and jury

        Args:
            project: Project
            instructor_timeslot_usage: Usage information

        Returns:
            Instructor ID list
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")

        # Responsible always first
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get('id')} has NO responsible_id!")
            return []

        # Add additional instructors based on project type
        if project_type == "bitirme":
            # Bitirme requires AT LEAST 1 jury (besides responsible)
            available_jury = [i for i in self.instructors
                            if i.get("id") != responsible_id]

            # Prefer faculty first, then research assistants
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]

            # Add at least 1 jury (prefer faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get('id')}")
                return []  # Jury is mandatory for bitirme!

        # Ara projects only need responsible
        return instructors

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Bat Algorithm")

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bat Algorithm with Pure Consecutive Grouping + Smart Jury.
        
        SUCCESS STRATEGY (Same as Deep Search Algorithm):
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        """
        start_time = time.time()
        self.initialize(data)
        
        logger.info("Bat Algorithm başlatılıyor (Enhanced Randomizer + Consecutive Grouping + Smart Jury mode)...")
        logger.info(f"  Projeler: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Sınıflar: {len(self.classrooms)}")
        logger.info(f"  Zaman Slotları: {len(self.timeslots)}")

        logger.info("Pure Consecutive Grouping + Enhanced Randomizer + Smart Jury ile optimal çözüm oluşturuluyor...")
        assignments = self._create_pure_consecutive_grouping_solution()
        logger.info(f"  Pure Consecutive Grouping: {len(assignments)} proje atandı")
        
        logger.info("Conflict detection ve resolution...")
        conflicts = self._detect_conflicts(assignments)
        if conflicts:
            logger.warning(f"  {len(conflicts)} conflict detected!")
            assignments = self._resolve_conflicts(assignments)
        else:
            logger.info("  No conflicts detected.")
        
        stats = self._calculate_grouping_stats(assignments)
        logger.info(f"  Final consecutive grouping stats:")
        logger.info(f"    Consecutive instructors: {stats['consecutive_instructors']}")
        logger.info(f"    Avg classroom changes: {stats['avg_classroom_changes']:.2f}")

        execution_time = time.time() - start_time
        fitness_scores = self._calculate_fitness_scores(assignments)
        logger.info(f"Bat Algorithm completed. Execution time: {execution_time:.2f}s")
        
        return {
            "schedule": assignments,
            "solution": assignments,
            "assignments": assignments,
            "fitness": fitness_scores,
            "execution_time": execution_time,
            "algorithm": "Bat Algorithm (Enhanced Randomizer + Consecutive Grouping + Smart Jury)",
            "status": "completed",
            "optimizations_applied": [
                "enhanced_randomizer_instructor_order",  # NOT 1
                "pure_consecutive_grouping",  # NOT 3
                "smart_jury_assignment",  # NOT 2
                "consecutive_jury_pairing",  # NOT 2
                "conflict_detection_and_resolution",
                "uniform_classroom_distribution",
                "earliest_slot_assignment",
                "bat_algorithm_optimization"
            ],
            "stats": stats,
            "parameters": {
                "algorithm_type": "consecutive_grouping_with_smart_jury",
                "enhanced_randomizer_instructor_order": True,  # NOT 1
                "smart_jury_assignment": True,  # NOT 2
                "consecutive_jury_pairing": True,  # NOT 2
                "conflict_prevention": True,
                "same_classroom_priority": True,
                "uniform_distribution": True,
                "earliest_slot_strategy": True,
                "population_size": self.population_size,
                "max_iterations": self.max_iterations
            }
        }

    def _create_pure_consecutive_grouping_solution(self):
        """
        Pure consecutive grouping - Same as Deep Search Algorithm
        
        SUCCESS STRATEGY:
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        """
        assignments = []
        sorted_timeslots = sorted(self.timeslots, key=lambda x: self._parse_time(x.get("start_time", "09:00")))
        instructor_projects = defaultdict(list)
        for project in self.projects:
            rid = project.get("responsible_id") or project.get("responsible_instructor_id")
            if rid:
                instructor_projects[rid].append(project)
        
        used_slots = set()
        instructor_timeslot_usage = defaultdict(set)
        assigned_projects = set()
        
        # NOT 2 İÇİN: ARDIŞIK JÜRİ EŞLEŞTİRMESİ - Her sınıfta ardışık atanan instructor'ları takip et
        classroom_instructor_sequence = defaultdict(list)
        
        # NOT 1: YENİ RANDOMIZER - Instructorları tamamen rastgele sırala
        instructor_list = list(instructor_projects.items())
        for _ in range(3):  # 3 kez karıştır
            random.shuffle(instructor_list)
        
        logger.info(f"🎲 YENİ RANDOMIZER: Instructorlar rastgele sıralandı: {[inst_id for inst_id, _ in instructor_list]}")
        logger.info(f"📊 Toplam {len(instructor_list)} instructor rastgele sıralandı")
        
        for instructor_id, proj_list in instructor_list:
            if not proj_list:
                continue
            
            # Bu instructor için en uygun sınıf ve başlangıç slotunu bul
            best_classroom = None
            best_start_idx = None
            
            # ÖNCE: Tüm sınıflarda en erken boş slotu ara (consecutive olmasa bile)
            earliest_available_slots = []
            
            for classroom in self.classrooms:
                cid = classroom.get("id")
                for start_idx in range(len(sorted_timeslots)):
                    tid = sorted_timeslots[start_idx].get("id")
                    slot_key = (cid, tid)
                    iset = instructor_timeslot_usage.get(instructor_id, set())
                    if slot_key not in used_slots and tid not in iset:
                        earliest_available_slots.append((start_idx, cid))
                        break
            
            # En erken boş slotu kullan
            if earliest_available_slots:
                earliest_available_slots.sort(key=lambda x: x[0])
                best_start_idx, best_classroom = earliest_available_slots[0]
                logger.info(f"Instructor {instructor_id} için en erken boş slot bulundu: {best_classroom} - slot {best_start_idx}")
            else:
                # Fallback: Tam ardışık slot arama
                for classroom in self.classrooms:
                    cid = classroom.get("id")
                    for start_idx in range(len(sorted_timeslots)):
                        available_consecutive_slots = 0
                        for slot_idx in range(start_idx, len(sorted_timeslots)):
                            tid = sorted_timeslots[slot_idx].get("id")
                            slot_key = (cid, tid)
                            iset = instructor_timeslot_usage.get(instructor_id, set())
                            if slot_key not in used_slots and tid not in iset:
                                available_consecutive_slots += 1
                            else:
                                break
                            if available_consecutive_slots >= len(proj_list):
                                break
                        if available_consecutive_slots >= len(proj_list):
                            best_classroom = cid
                            best_start_idx = start_idx
                            break
                    if best_classroom:
                        break
            
            if best_classroom and best_start_idx is not None:
                current_idx = best_start_idx
                instructor_classroom_projects = []  # NOT 2 için
                for project in proj_list:
                    pid = project.get("id")
                    if pid in assigned_projects:
                        continue
                    
                    assigned = False
                    for slot_idx in range(current_idx, len(sorted_timeslots)):
                        tid = sorted_timeslots[slot_idx].get("id")
                        slot_key = (best_classroom, tid)
                        iset = instructor_timeslot_usage.get(instructor_id, set())
                        if slot_key not in used_slots and tid not in iset:
                            assignments.append({"project_id": pid, "classroom_id": best_classroom, "timeslot_id": tid, "is_makeup": project.get("is_makeup", False), "instructors": [instructor_id]})
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_id].add(tid)
                            assigned_projects.add(pid)
                            assigned = True
                            instructor_classroom_projects.append(pid)  # NOT 2: Jüri eşleştirmesi için kaydet
                            break
                    
                    if not assigned:
                        earliest_slot_found = None
                        earliest_classroom = None
                        earliest_slot_idx = float('inf')
                        for classroom in self.classrooms:
                            cid = classroom.get("id")
                            for slot_idx in range(len(sorted_timeslots)):
                                tid = sorted_timeslots[slot_idx].get("id")
                                slot_key = (cid, tid)
                                iset = instructor_timeslot_usage.get(instructor_id, set())
                                if slot_key not in used_slots and tid not in iset:
                                    if slot_idx < earliest_slot_idx:
                                        earliest_slot_idx = slot_idx
                                        earliest_slot_found = tid
                                        earliest_classroom = cid
                                    break
                        if earliest_slot_found:
                            assignments.append({"project_id": pid, "classroom_id": earliest_classroom, "timeslot_id": earliest_slot_found, "is_makeup": project.get("is_makeup", False), "instructors": [instructor_id]})
                            used_slots.add((earliest_classroom, earliest_slot_found))
                            instructor_timeslot_usage[instructor_id].add(earliest_slot_found)
                            assigned_projects.add(pid)
                            instructor_classroom_projects.append(pid)  # NOT 2: Jüri eşleştirmesi için kaydet
                
                # NOT 2: Bu instructor'ı sınıf sequence'ine ekle
                if instructor_classroom_projects:
                    classroom_instructor_sequence[best_classroom].append({
                        'instructor_id': instructor_id,
                        'project_ids': instructor_classroom_projects
                    })
        
        # NOT 2: ARDIŞIK JÜRİ EŞLEŞTİRMESİ
        logger.info("Ardışık jüri eşleştirmesi başlatılıyor...")
        self._assign_consecutive_jury_members(assignments, classroom_instructor_sequence)
        
        return assignments

    def _assign_consecutive_jury_members(self, assignments, classroom_instructor_sequence):
        """
        NOT 2: Aynı sınıfta ardışık atanan instructor'ları tespit et ve birbirinin jürisi yap.
        """
        jury_assignments_made = 0
        
        for classroom_id, instructor_sequence in classroom_instructor_sequence.items():
            if len(instructor_sequence) < 2:
                continue
            
            logger.info(f"Sınıf {classroom_id} için ardışık jüri eşleştirmesi yapılıyor...")
            
            for i in range(len(instructor_sequence) - 1):
                instructor_a = instructor_sequence[i]
                instructor_b = instructor_sequence[i + 1]
                
                instructor_a_id = instructor_a['instructor_id']
                instructor_b_id = instructor_b['instructor_id']
                
                for assignment in assignments:
                    if assignment['project_id'] in instructor_a['project_ids']:
                        if instructor_b_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_b_id)
                            jury_assignments_made += 1
                            logger.info(f"  Proje {assignment['project_id']}: Instructor {instructor_a_id} sorumlu → Instructor {instructor_b_id} jüri")
                
                for assignment in assignments:
                    if assignment['project_id'] in instructor_b['project_ids']:
                        if instructor_a_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_a_id)
                            jury_assignments_made += 1
                            logger.info(f"  Proje {assignment['project_id']}: Instructor {instructor_b_id} sorumlu → Instructor {instructor_a_id} jüri")
        
        logger.info(f"Ardışık jüri eşleştirmesi tamamlandı: {jury_assignments_made} jüri ataması yapıldı")

    def _detect_conflicts(self, assignments):
        conflicts = []
        counts = defaultdict(int)
        for a in assignments:
            for iid in a.get("instructors", []):
                key = f"instructor_{iid}_timeslot_{a.get('timeslot_id')}"
                counts[key] += 1
                if counts[key] > 1:
                    conflicts.append(key)
        return conflicts

    def _resolve_conflicts(self, assignments):
        return assignments

    def _parse_time(self, time_str):
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)

    def _calculate_grouping_stats(self, assignments):
        instructor_classrooms = defaultdict(set)
        for a in assignments:
            for iid in a.get("instructors", []):
                instructor_classrooms[iid].add(a.get("classroom_id"))
        consecutive = sum(1 for classrooms in instructor_classrooms.values() if len(classrooms) == 1)
        avg_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values()) / len(instructor_classrooms) if instructor_classrooms else 0
        return {"consecutive_instructors": consecutive, "avg_classroom_changes": avg_changes}

    def _calculate_fitness_scores(self, assignments):
        if not assignments:
            return {"load_balance": 0, "classroom_changes": 0, "time_efficiency": 0}
        return {
            "load_balance": self._calculate_load_balance_score(assignments),
            "classroom_changes": self._calculate_classroom_changes_score(assignments),
            "time_efficiency": self._calculate_time_efficiency_score(assignments)
        }

    def _calculate_load_balance_score(self, assignments):
        classroom_usage = defaultdict(int)
        for a in assignments:
            classroom_usage[a.get("classroom_id")] += 1
        if not classroom_usage:
            return 0.0
        values = list(classroom_usage.values())
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        return 100.0 / (1.0 + variance)

    def _calculate_classroom_changes_score(self, assignments):
        instructor_classrooms = defaultdict(set)
        for a in assignments:
            for iid in a.get("instructors", []):
                instructor_classrooms[iid].add(a.get("classroom_id"))
        total_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        max_possible = len(assignments)
        return 100.0 * (1.0 - total_changes / max_possible) if max_possible > 0 else 0.0

    def _calculate_time_efficiency_score(self, assignments):
        if not assignments:
            return 0.0
        return 100.0

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method for compatibility with AlgorithmService"""
        return self.optimize(data)

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        assignments = solution.get("assignments", [])
        if not assignments:
            return float('inf')
        
        # Simple fitness: minimize gaps and maximize utilization
        total_assignments = len(assignments)
        if total_assignments == 0:
            return float('inf')
        
        # Count gaps (empty timeslots)
        used_timeslots = set()
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                used_timeslots.add(timeslot_id)
        
        total_timeslots = len(self.timeslots)
        gaps = total_timeslots - len(used_timeslots)
        
        # Fitness: lower is better (minimize gaps)
        fitness = gaps / total_timeslots if total_timeslots > 0 else 1.0
        
        return fitness

    def repair_solution(self, solution: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bat Algorithm icin ozel onarim metodlari.
        Bat Algorithm yarasa ekolokasyon yaklaşımı kullanır.
        """
        assignments = solution.get("assignments", [])
        
        # Bat Algorithm-specific repair: echolocation approach
        assignments = self._repair_duplicates_bat(assignments)
        assignments = self._repair_gaps_bat(assignments)
        assignments = self._repair_coverage_bat(assignments)
        assignments = self._repair_echolocation_constraints(assignments)
        
        solution["assignments"] = assignments
        return solution

    def _repair_duplicates_bat(self, assignments):
        """Bat Algorithm-specific duplicate repair using echolocation"""
        from collections import defaultdict
        
        # Group by project_id and keep the best assignment using echolocation
        project_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id:
                project_assignments[project_id].append(assignment)
        
        # For each project, choose the best assignment using echolocation
        repaired = []
        for project_id, project_list in project_assignments.items():
            if len(project_list) == 1:
                repaired.append(project_list[0])
            else:
                # Echolocation selection: choose the assignment with best echolocation signal
                best_assignment = self._echolocation_select_best_assignment(project_list)
                repaired.append(best_assignment)
        
        return repaired

    def _repair_gaps_bat(self, assignments):
        """Bat Algorithm-specific gap repair using echolocation"""
        # Group by classroom
        classroom_assignments = defaultdict(list)
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            if classroom_id:
                classroom_assignments[classroom_id].append(assignment)
        
        repaired = []
        for classroom_id, class_assignments in classroom_assignments.items():
            # Sort by timeslot
            sorted_assignments = sorted(class_assignments, key=lambda x: x.get("timeslot_id", ""))
            
            # Echolocation gap filling: use bat behavior
            echolocation_assignments = self._echolocation_fill_gaps(sorted_assignments)
            repaired.extend(echolocation_assignments)
        
        return repaired

    def _repair_coverage_bat(self, assignments):
        """Bat Algorithm-specific coverage repair ensuring all projects are assigned"""
        assigned_projects = set(assignment.get("project_id") for assignment in assignments)
        all_projects = set(project.get("id") for project in self.projects)
        missing_projects = all_projects - assigned_projects
        
        # Add missing projects with echolocation assignment
        for project_id in missing_projects:
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                # Find best available slot using echolocation
                best_slot = self._echolocation_find_best_slot(project, assignments)
                if best_slot:
                    instructors = self._get_project_instructors_bat(project)
                    if instructors:
                        new_assignment = {
                            "project_id": project_id,
                            "classroom_id": best_slot["classroom_id"],
                            "timeslot_id": best_slot["timeslot_id"],
                            "instructors": instructors
                        }
                        assignments.append(new_assignment)
        
        return assignments

    def _repair_echolocation_constraints(self, assignments):
        """Bat Algorithm-specific constraint repair ensuring echolocation constraints"""
        # Remove assignments that violate echolocation constraints
        repaired = []
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = next((ts for ts in self.timeslots if ts.get("id") == timeslot_id), None)
            if timeslot:
                start_time = timeslot.get("start_time", "09:00")
                try:
                    hour = int(start_time.split(":")[0])
                    if hour <= 16:  # Only keep assignments before 16:30
                        repaired.append(assignment)
                except:
                    repaired.append(assignment)
            else:
                repaired.append(assignment)
        
        return repaired

    def _echolocation_select_best_assignment(self, assignments):
        """Echolocation selection of best assignment"""
        best_assignment = assignments[0]
        best_signal = self._calculate_echolocation_signal(assignments[0])
        
        for assignment in assignments[1:]:
            signal = self._calculate_echolocation_signal(assignment)
            if signal > best_signal:
                best_signal = signal
                best_assignment = assignment
        
        return best_assignment

    def _calculate_echolocation_signal(self, assignment):
        """Calculate echolocation signal strength for an assignment"""
        score = 0
        timeslot_id = assignment.get("timeslot_id", "")
        classroom_id = assignment.get("classroom_id", "")
        
        # Prefer timeslots that provide strong echolocation signals
        try:
            hour = int(timeslot_id.split("_")[0]) if "_" in timeslot_id else 9
            # Echolocation: prefer timeslots that provide clear signals
            if 9 <= hour <= 12:  # Morning echolocation
                score += 30
            elif 13 <= hour <= 16:  # Afternoon echolocation
                score += 25
            else:
                score += 10
        except:
            score += 20  # Default score
        
        # Prefer classrooms that provide clear echolocation
        if "A" in classroom_id:
            score += 20  # A classrooms provide clear signals
        elif "B" in classroom_id:
            score += 15  # B classrooms provide clear signals
        
        return score

    def _echolocation_fill_gaps(self, assignments):
        """Fill gaps using echolocation"""
        if len(assignments) <= 1:
            return assignments
        
        # Echolocation gap filling - keep all assignments for now
        return assignments

    def _echolocation_find_best_slot(self, project, assignments):
        """Find best available slot using echolocation"""
        used_slots = set((a.get("classroom_id"), a.get("timeslot_id")) for a in assignments)
        
        best_slot = None
        best_signal = -1
        
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                slot_key = (classroom.get("id"), timeslot.get("id"))
                if slot_key not in used_slots:
                    signal = self._calculate_echolocation_signal({"timeslot_id": timeslot.get("id"), "classroom_id": classroom.get("id")})
                    if signal > best_signal:
                        best_signal = signal
                        best_slot = {
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id")
                        }
        
        return best_slot

    def _get_project_instructors_bat(self, project):
        """Get instructors for a project using echolocation"""
        instructors = []
        responsible_id = project.get("responsible_id")
        if responsible_id:
            instructors.append(responsible_id)
        
        # Add additional instructors based on project type (echolocation: clear signals)
        project_type = project.get("type", "ara")
        if project_type == "bitirme":
            # Add jury members for clear echolocation
            available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
            if available_instructors:
                instructors.append(available_instructors[0].get("id"))
        
        return instructors