"""
Ant Colony Optimization (ACO) Algorithm Implementation - Enhanced with Pure Consecutive Grouping
Uses same logic as Deep Search Algorithm for optimal uniform distribution
"""

from typing import Dict, Any, List
import math
import time
import logging
import random
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

logger = logging.getLogger(__name__)


class AntColonyOptimization(OptimizationAlgorithm):
    """
    Ant Colony Optimization (ACO) Algorithm - Enhanced with Pure Consecutive Grouping + Smart Jury Assignment.
    
    SUCCESS STRATEGY (Same as Deep Search Algorithm):
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
    """

    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.name = "Ant Colony Optimization Algorithm"
        self.description = "Enhanced with Pure Consecutive Grouping + Smart Jury Assignment"
        
        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        # Stage 1 cache for project placement results
        self._stage1_assignments_cache: List[Dict[str, Any]] = []

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Real Simplex Algorithm")

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Two-stage optimization: first place projects, then assign juries."""
        start_time = time.time()
        self.initialize(data)

        logger.info("Two-stage ACO optimization started: project placement -> jury assignment")
        logger.info(f"  Projeler: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Sınıflar: {len(self.classrooms)}")
        logger.info(f"  Zaman Slotları: {len(self.timeslots)}")

        stage1_assignments = self._stage1_project_placement()
        logger.info(f"Stage 1: {len(stage1_assignments)} proje atandı (Stage 1)")
        self._stage1_assignments_cache = stage1_assignments

        stage2_assignments = self._stage2_jury_assignment(stage1_assignments)
        logger.info(f"Stage 2: jury assignments completed: {len(stage2_assignments)} total atama")

        best_solution = stage2_assignments or stage1_assignments

        final_stats = self._calculate_grouping_stats(best_solution)
        logger.info(f"  Final consecutive grouping stats:")
        logger.info(f"    Consecutive instructors: {final_stats['consecutive_count']}")
        logger.info(f"    Avg classroom changes: {final_stats['avg_classroom_changes']:.2f}")

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Ant Colony Optimization Algorithm completed. Execution time: {execution_time:.2f}s")

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []),
            "execution_time": execution_time,
            "algorithm": "Ant Colony Optimization Algorithm (Two-Stage: Projects + Jurors)",
            "status": "completed",
            "optimizations_applied": [
                "two_stage_project_placement",
                "two_stage_jury_assignment",
            ],
            "stats": final_stats,
            "parameters": {
                "algorithm_type": "two_stage_staged",
                "stage1_project_placement": True,
                "stage2_jury_assignment": True
            }
        }

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method for compatibility with AlgorithmService"""
        return self.optimize(data)

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        assignments = solution.get("assignments", [])
        if not assignments:
            return float('inf')
        
        # Simple fitness: number of assignments (more is better)
        return -len(assignments)  # Negative because we minimize
    
    def _calculate_fitness_scores(self, solution: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate fitness scores for a solution."""
        if not solution:
            return {
                "load_balance": 0.0,
                "classroom_changes": 0.0,
                "time_efficiency": 0.0,
                "total": 0.0
            }
        
        load_balance = self._calculate_load_balance_score(solution)
        classroom_changes = self._calculate_classroom_changes_score(solution)
        time_efficiency = self._calculate_time_efficiency_score(solution)
        
        total = load_balance + classroom_changes + time_efficiency
        
        return {
            "load_balance": load_balance,
            "classroom_changes": classroom_changes,
            "time_efficiency": time_efficiency,
            "total": total
        }
    
    def _calculate_load_balance_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate load balance score."""
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        avg_load = sum(loads) / len(loads)
        variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
        
        return variance
    
    def _calculate_classroom_changes_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate classroom changes score."""
        instructor_classrooms = {}
        changes = 0
        
        for assignment in solution:
            classroom_id = assignment.get("classroom_id")
            for instructor_id in assignment.get("instructors", []):
                if instructor_id in instructor_classrooms:
                    if instructor_classrooms[instructor_id] != classroom_id:
                        changes += 1
                instructor_classrooms[instructor_id] = classroom_id
        
        return float(changes)
    
    def _calculate_time_efficiency_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency score."""
        instructor_timeslots = {}
        gaps = 0
        
        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_timeslots:
                    instructor_timeslots[instructor_id] = []
                instructor_timeslots[instructor_id].append(timeslot_id)
        
        for timeslots in instructor_timeslots.values():
            sorted_slots = sorted(timeslots)
            for i in range(1, len(sorted_slots)):
                if sorted_slots[i] - sorted_slots[i-1] > 1:
                    gaps += 1
        
        return float(gaps)
    
    def _calculate_grouping_stats(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consecutive grouping statistics."""
        if not assignments:
            return {
                "consecutive_count": 0,
                "total_instructors": 0,
                "avg_classroom_changes": 0.0,
                "consecutive_percentage": 0.0
            }
        
        instructor_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project and project.get("responsible_id"):
                instructor_id = project["responsible_id"]
                instructor_assignments[instructor_id].append(assignment)
        
        consecutive_count = 0
        total_classroom_changes = 0
        
        for instructor_id, instructor_assignment_list in instructor_assignments.items():
            classrooms_used = set(a.get("classroom_id") for a in instructor_assignment_list)
            classroom_changes = len(classrooms_used) - 1
            total_classroom_changes += classroom_changes
            
            timeslot_ids = sorted([a.get("timeslot_id") for a in instructor_assignment_list])
            is_consecutive = all(
                timeslot_ids[i] + 1 == timeslot_ids[i+1] 
                for i in range(len(timeslot_ids) - 1)
            ) if len(timeslot_ids) > 1 else True
            
            if is_consecutive and len(classrooms_used) == 1:
                consecutive_count += 1
        
        total_instructors = len(instructor_assignments)
        avg_classroom_changes = total_classroom_changes / total_instructors if total_instructors > 0 else 0
        
        return {
            "consecutive_count": consecutive_count,
            "total_instructors": total_instructors,
            "avg_classroom_changes": avg_classroom_changes,
            "consecutive_percentage": (consecutive_count / total_instructors * 100) if total_instructors > 0 else 0
        }

    def _create_pure_consecutive_grouping_solution(self) -> List[Dict[str, Any]]:
        """
        Pure consecutive grouping çözümü oluştur - Same as Genetic Algorithm.
        
        "Bir öğretim görevlimizi sorumlu olduğu projelerden birisiyle birlikte diyelim ki 09:00-09:30 
        zaman slotuna ve D106 sınıfına atamasını yaptık. Bu öğretim görevlimizin diğer sorumlu olduğu 
        projeleri de aynı sınıfa ve hemen sonraki zaman slotlarına atayalım ki çok fazla yer değişimi olmasın"
        """
        assignments = []
        
        # Zaman slotlarını sırala
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Instructor bazında projeleri grupla
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # Sıkı conflict prevention
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        assigned_projects = set()  # project_ids that have been assigned
        
        # ARDIŞIK JÜRİ EŞLEŞTİRMESİ İÇİN: Her sınıfta ardışık atanan instructor'ları takip et
        classroom_instructor_sequence = defaultdict(list)  # classroom_id -> [{'instructor_id': ..., 'project_ids': [...]}]
        
        # YENİ RANDOMIZER: Instructorları tamamen rastgele sırala
        # Bu sayede her seferinde farklı öğretim görevlileri farklı sınıf ve zamanlarda olur
        instructor_list = list(instructor_projects.items())
        
        # Güçlü randomizer - birden fazla karıştırma
        for _ in range(3):  # 3 kez karıştır
            random.shuffle(instructor_list)
        
        logger.info(f"🎲 YENİ RANDOMIZER: Instructorlar rastgele sıralandı: {[inst_id for inst_id, _ in instructor_list]}")
        logger.info(f"📊 Toplam {len(instructor_list)} instructor rastgele sıralandı")
        
        # Her instructor için projeleri ata (consecutive grouping korunur!)
        for instructor_id, instructor_project_list in instructor_list:
            if not instructor_project_list:
                continue
            
            logger.info(f"Instructor {instructor_id} için {len(instructor_project_list)} proje atanıyor...")
            
            # Bu instructor için en uygun sınıf ve başlangıç slotunu bul
            best_classroom = None
            best_start_slot_idx = None
            
            # ÖNCE: Tüm sınıflarda en erken boş slotu ara (consecutive olmasa bile)
            earliest_available_slots = []
            
            for classroom in self.classrooms:
                classroom_id = classroom.get("id")
                
                for start_idx in range(len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[start_idx].get("id")
                    slot_key = (classroom_id, timeslot_id)
                    
                    instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                    if not isinstance(instructor_slots, set):
                        instructor_slots = set()
                    
                    if (slot_key not in used_slots and 
                        timeslot_id not in instructor_slots):
                        earliest_available_slots.append((start_idx, classroom_id))
                        break
            
            # En erken boş slotu kullan
            if earliest_available_slots:
                earliest_available_slots.sort(key=lambda x: x[0])
                best_start_slot_idx, best_classroom = earliest_available_slots[0]
                logger.info(f"Instructor {instructor_id} için en erken boş slot bulundu: {best_classroom} - slot {best_start_slot_idx}")
            else:
                # Fallback: Tam ardışık slot arama (eski mantık)
                for classroom in self.classrooms:
                    classroom_id = classroom.get("id")
                    
                    for start_idx in range(len(sorted_timeslots)):
                        available_consecutive_slots = 0
                        
                        for slot_idx in range(start_idx, len(sorted_timeslots)):
                            timeslot_id = sorted_timeslots[slot_idx].get("id")
                            slot_key = (classroom_id, timeslot_id)
                            
                            instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                            if not isinstance(instructor_slots, set):
                                instructor_slots = set()
                            
                            if (slot_key not in used_slots and 
                                timeslot_id not in instructor_slots):
                                available_consecutive_slots += 1
                            else:
                                break
                            
                            if available_consecutive_slots >= len(instructor_project_list):
                                break
                        
                        if available_consecutive_slots >= len(instructor_project_list):
                            best_classroom = classroom_id
                            best_start_slot_idx = start_idx
                            break
                    
                    if best_classroom:
                        break
            
            # Projeleri ata
            if best_classroom and best_start_slot_idx is not None:
                current_slot_idx = best_start_slot_idx
                instructor_classroom_projects = []  # Bu instructor'ın bu sınıftaki projeleri
                
                for project in instructor_project_list:
                    project_id = project.get("id")
                    
                    # Bu proje zaten atanmış mı?
                    if project_id in assigned_projects:
                        logger.warning(f"UYARI: Proje {project_id} zaten atanmış, atlanıyor")
                        continue
                    
                    # EN ERKEN BOŞ SLOT BUL - Tüm sınıflarda ara
                    assigned = False
                    
                    # Önce mevcut sınıfta boş slot ara
                    for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                        timeslot_id = sorted_timeslots[slot_idx].get("id")
                        slot_key = (best_classroom, timeslot_id)
                        
                        instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                        if not isinstance(instructor_slots, set):
                            instructor_slots = set()
                        
                        if (slot_key not in used_slots and 
                            timeslot_id not in instructor_slots):
                            
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": best_classroom,
                                "timeslot_id": timeslot_id,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_id].add(timeslot_id)
                            assigned_projects.add(project_id)
                            assigned = True
                            instructor_classroom_projects.append(project_id)  # Jüri eşleştirmesi için kaydet
                            logger.info(f"Proje {project_id} atandı: {best_classroom} - {timeslot_id}")
                            break
                    
                    # Eğer mevcut sınıfta bulunamadıysa, tüm sınıflarda en erken boş slotu ara
                    if not assigned:
                        earliest_slot_found = None
                        earliest_classroom = None
                        earliest_slot_idx = float('inf')
                        
                        for classroom in self.classrooms:
                            classroom_id = classroom.get("id")
                            
                            for slot_idx in range(len(sorted_timeslots)):
                                timeslot_id = sorted_timeslots[slot_idx].get("id")
                                slot_key = (classroom_id, timeslot_id)
                                
                                instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                                if not isinstance(instructor_slots, set):
                                    instructor_slots = set()
                                
                                if (slot_key not in used_slots and 
                                    timeslot_id not in instructor_slots):
                                    
                                    if slot_idx < earliest_slot_idx:
                                        earliest_slot_idx = slot_idx
                                        earliest_slot_found = timeslot_id
                                        earliest_classroom = classroom_id
                                    break
                        
                        # En erken boş slotu kullan
                        if earliest_slot_found:
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": earliest_classroom,
                                "timeslot_id": earliest_slot_found,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                            used_slots.add((earliest_classroom, earliest_slot_found))
                            instructor_timeslot_usage[instructor_id].add(earliest_slot_found)
                            assigned_projects.add(project_id)
                            assigned = True
                            instructor_classroom_projects.append(project_id)  # Jüri eşleştirmesi için kaydet
                            logger.info(f"Proje {project_id} en erken slot'a atandı: {earliest_classroom} - {earliest_slot_found}")
                    
                    if not assigned:
                        logger.warning(f"UYARI: Proje {project_id} için hiçbir boş slot bulunamadı!")
                
                # Bu instructor'ı sınıf sequence'ine ekle (jüri eşleştirmesi için)
                if instructor_classroom_projects:
                    classroom_instructor_sequence[best_classroom].append({
                        'instructor_id': instructor_id,
                        'project_ids': instructor_classroom_projects
                    })
        
        # ARDIŞIK JÜRİ EŞLEŞTİRMESİ: Aynı sınıfta ardışık atanan instructor'ları eşleştir
        logger.info("Ardışık jüri eşleştirmesi başlatılıyor...")
        self._assign_consecutive_jury_members(assignments, classroom_instructor_sequence)
        
        logger.info(f"Pure Consecutive Grouping tamamlandı: {len(assignments)} atama yapıldı")
        return assignments

    def _stage1_project_placement(self) -> List[Dict[str, Any]]:
        """Stage 1: place projects across timeslots/classrooms without jury assignments.
        Heuristic: sort instructors by number of projects (desc) and place their
        projects in the earliest available (classroom, timeslot) slots.
        Additionally, prioritize projects with fewer available slots to place high-conflict items first.
        """
        assignments: List[Dict[str, Any]] = []
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            return assignments

        # Map instructor -> their projects
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)

        # Build slots timeline (earliest to latest)
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )

        # Used slots and per-instructor usage tracking
        used_slots: set = set()  # (classroom_id, timeslot_id)
        instructor_slot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        assigned_projects = set()

        # Precompute available slots count per (instructor, project)
        stage_candidates = []
        for instructor_id, projects in instructor_projects.items():
            for project in projects:
                pid = project.get("id")
                if not pid or pid in assigned_projects:
                    continue
                # count available slots for this instructor
                available = 0
                if self.classrooms and sorted_timeslots:
                    for classroom in self.classrooms:
                        cid = classroom.get("id")
                        for ts in sorted_timeslots:
                            timeslot_id = ts.get("id")
                            slot_key = (cid, timeslot_id)
                            if slot_key not in used_slots and timeslot_id not in instructor_slot_usage[instructor_id]:
                                available += 1
                stage_candidates.append((instructor_id, project, available))

        # Sort candidates by: most projects for instructor, then fewer available slots (tiebreaker)
        stage_candidates.sort(key=lambda t: (-len(instructor_projects.get(t[0], [])), t[2]))

        # Place proposals in the first available slot per candidate
        for instructor_id, project, available_slots in stage_candidates:
            pid = project.get("id")
            if not pid or pid in assigned_projects:
                continue
            placed = False
            for classroom in self.classrooms:
                cid = classroom.get("id")
                for ts in sorted_timeslots:
                    timeslot_id = ts.get("id")
                    slot_key = (cid, timeslot_id)
                    if slot_key not in used_slots and timeslot_id not in instructor_slot_usage[instructor_id]:
                        assignments.append({
                            "project_id": pid,
                            "classroom_id": cid,
                            "timeslot_id": timeslot_id,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": [instructor_id]
                        })
                        used_slots.add(slot_key)
                        instructor_slot_usage[instructor_id].add(timeslot_id)
                        assigned_projects.add(pid)
                        placed = True
                        logger.info(f"Stage1: Proje {pid} atandı: {cid} - {timeslot_id}")
                        break
                if placed:
                    break
            if not placed:
                logger.warning(f"Stage1: Proje {pid} için hiçbir boş slot bulunamadı!")
        return assignments

    def _stage2_jury_assignment(self, stage1_assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 2: assign juries based on consecutive grouping rules using stage1 results."""
        if not stage1_assignments:
            return stage1_assignments

        # Build classroom-wise sequence similar to existing logic
        classroom_instructor_sequence = defaultdict(list)
        instructor_projects_by_classroom = defaultdict(lambda: defaultdict(list))

        for assignment in stage1_assignments:
            classroom_id = assignment.get("classroom_id")
            instructor_ids = assignment.get("instructors", [])
            for instr in instructor_ids:
                instructor_projects_by_classroom[classroom_id][instr].append(assignment.get("project_id"))

        for classroom_id, instr_map in instructor_projects_by_classroom.items():
            if len(instr_map) < 2:
                continue
            entries = []
            for instr_id, proj_ids in instr_map.items():
                entries.append({
                    'instructor_id': instr_id,
                    'project_ids': proj_ids
                })
            classroom_instructor_sequence[classroom_id] = entries

        # Use existing jury assignment logic to add juries
        self._assign_consecutive_jury_members(stage1_assignments, classroom_instructor_sequence)
        return stage1_assignments

    def _assign_consecutive_jury_members(self, assignments: List[Dict[str, Any]], 
                                        classroom_instructor_sequence: Dict) -> None:
        """
        Aynı sınıfta ardışık atanan instructor'ları tespit et ve birbirinin jürisi yap.
        
        Mantık:
        - Dr. Öğretim Görevlisi 14: D106'da consecutive (09:00-09:30)
        - Dr. Öğretim Görevlisi 2: D106'da consecutive (09:30-10:00) 
        
        Sonuç:
        - Öğretim Görevlisi 14 sorumlu → Öğretim Görevlisi 2 jüri
        - Öğretim Görevlisi 2 sorumlu → Öğretim Görevlisi 14 jüri
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

    def _detect_conflicts(self, assignments: List[Dict[str, Any]]) -> List[str]:
        """Detect conflicts in assignments"""
        conflicts = []
        instructor_timeslot_counts = defaultdict(int)
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            timeslot_id = assignment.get('timeslot_id')
            
            for instructor_id in instructors_list:
                key = f"instructor_{instructor_id}_timeslot_{timeslot_id}"
                instructor_timeslot_counts[key] += 1
                
                if instructor_timeslot_counts[key] > 1:
                    conflicts.append(key)
        
        return conflicts

    def _resolve_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve conflicts by reassigning conflicting projects"""
        # Simple conflict resolution - remove conflicting assignments and reassign
        # This is a basic implementation, could be improved
        
        conflicts = self._detect_conflicts(assignments)
        if not conflicts:
            return assignments
        
        # For now, just return the original assignments
        # A more sophisticated conflict resolution could be implemented here
        logger.warning(f"Conflict resolution: {len(conflicts)} conflicts detected but not resolved")
        return assignments

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to datetime.time object"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)  # Default to 09:00
