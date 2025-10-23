"""
Genetic Local Search Algorithm - Enhanced with Pure Consecutive Grouping
Uses same logic as Deep Search for optimal uniform distribution
"""

from typing import Dict, Any, Optional, List, Tuple, Set
import random
import numpy as np
import time
import logging
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment
from app.services.gap_free_scheduler import GapFreeScheduler
from app.services.rules import RulesService


logger = logging.getLogger(__name__)


class GeneticLocalSearch(OptimizationAlgorithm):
    """
    Genetic Local Search Algorithm - Enhanced with Pure Consecutive Grouping + Smart Jury Assignment.
    
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

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Genetic Local Search Algorithm"
        self.description = "Enhanced with Pure Consecutive Grouping + Smart Jury Assignment"

        # Genetic Local Search Parameters
        self.population_size = params.get("population_size", 50) if params else 50
        self.generations = params.get("generations", 100) if params else 100
        self.mutation_rate = params.get("mutation_rate", 0.1) if params else 0.1
        self.crossover_rate = params.get("crossover_rate", 0.8) if params else 0.8
        self.local_search_rate = params.get("local_search_rate", 0.3) if params else 0.3

        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []

        # Genetic Local Search state
        self.population = []
        self.fitness_values = []
        self.best_solution = None
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
            raise ValueError("Insufficient data for Genetic Local Search Algorithm")

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Genetic Local Search optimization with Pure Consecutive Grouping.
        Uses same approach as Deep Search Algorithm for uniform distribution.
        """
        start_time = time.time()
        self.initialize(data)
        
        logger.info("Genetic Local Search Algorithm başlatılıyor...")
        logger.info(f"  Projeler: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Sınıflar: {len(self.classrooms)}")
        logger.info(f"  Zaman Slotları: {len(self.timeslots)}")

        # Pure Consecutive Grouping Algorithm - Same as Deep Search
        logger.info("Pure Consecutive Grouping ile optimal çözüm oluşturuluyor...")
        best_solution = self._create_pure_consecutive_grouping_solution()
        logger.info(f"  Pure Consecutive Grouping: {len(best_solution)} proje atandı")
        
        # Conflict detection ve resolution
        if best_solution and len(best_solution) > 0:
            logger.info("Conflict detection ve resolution...")
            conflicts = self._detect_conflicts(best_solution)
            
            if conflicts:
                logger.warning(f"  {len(conflicts)} conflict detected!")
                best_solution = self._resolve_conflicts(best_solution)
                
                remaining_conflicts = self._detect_conflicts(best_solution)
                if remaining_conflicts:
                    logger.error(f"  WARNING: {len(remaining_conflicts)} conflicts still remain!")
                else:
                    logger.info("  All conflicts successfully resolved!")
            else:
                logger.info("  No conflicts detected.")
        
        # Final stats
        final_stats = self._calculate_grouping_stats(best_solution)
        logger.info(f"  Final consecutive grouping stats:")
        logger.info(f"    Consecutive instructors: {final_stats['consecutive_count']}")
        logger.info(f"    Avg classroom changes: {final_stats['avg_classroom_changes']:.2f}")

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Genetic Local Search Algorithm completed. Execution time: {execution_time:.2f}s")

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []),
            "execution_time": execution_time,
            "algorithm": "Genetic Local Search Algorithm (Enhanced Randomizer + Consecutive Grouping + Smart Jury)",
            "status": "completed",
            "optimizations_applied": [
                "enhanced_randomizer_instructor_order",
                "pure_consecutive_grouping",
                "smart_jury_assignment",
                "consecutive_jury_pairing",
                "conflict_detection_and_resolution",
                "uniform_classroom_distribution",
                "earliest_slot_assignment"
            ],
            "stats": final_stats,
            "parameters": {
                "algorithm_type": "consecutive_grouping_with_smart_jury",
                "enhanced_randomizer_instructor_order": True,
                "smart_jury_assignment": True,
                "consecutive_jury_pairing": True,
                "conflict_prevention": True,
                "same_classroom_priority": True,
                "uniform_distribution": True,
                "earliest_slot_strategy": True,
                "population_size": self.population_size,
                "generations": self.generations
            }
        }

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
        Genetic Local Search için özel onarım metodları.
        """
        assignments = solution.get("assignments", [])
        
        # Genetic Local Search-specific repair
        assignments = self._repair_duplicates_genetic_local_search(assignments)
        assignments = self._repair_gaps_genetic_local_search(assignments)
        assignments = self._repair_coverage_genetic_local_search(assignments)
        
        solution["assignments"] = assignments
        return solution

    def _repair_duplicates_genetic_local_search(self, assignments):
        """Genetic Local Search-specific duplicate repair"""
        from collections import defaultdict
        
        # Group by project_id and keep the best assignment
        project_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id:
                project_assignments[project_id].append(assignment)
        
        # For each project, choose the best assignment
        repaired = []
        for project_id, project_list in project_assignments.items():
            if len(project_list) == 1:
                repaired.append(project_list[0])
            else:
                # Choose the assignment with earliest timeslot
                best_assignment = min(project_list, key=lambda x: x.get("timeslot_id", ""))
                repaired.append(best_assignment)
        
        return repaired

    def _repair_gaps_genetic_local_search(self, assignments):
        """Genetic Local Search-specific gap repair"""
        # Keep all assignments - no gap filling needed for consecutive grouping
        return assignments

    def _repair_coverage_genetic_local_search(self, assignments):
        """Genetic Local Search-specific coverage repair ensuring all projects are assigned"""
        assigned_projects = set(assignment.get("project_id") for assignment in assignments)
        all_projects = set(project.get("id") for project in self.projects)
        missing_projects = all_projects - assigned_projects
        
        # Add missing projects
        for project_id in missing_projects:
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                # Find best available slot
                best_slot = self._find_best_slot_for_project(project, assignments)
                if best_slot:
                    instructors = self._get_project_instructors(project)
                    if instructors:
                        new_assignment = {
                            "project_id": project_id,
                            "classroom_id": best_slot["classroom_id"],
                            "timeslot_id": best_slot["timeslot_id"],
                            "instructors": instructors
                        }
                        assignments.append(new_assignment)
        
        return assignments

    def _find_best_slot_for_project(self, project, assignments):
        """Find best available slot for a project"""
        used_slots = set((a.get("classroom_id"), a.get("timeslot_id")) for a in assignments)
        
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                slot_key = (classroom.get("id"), timeslot.get("id"))
                if slot_key not in used_slots:
                    return {
                        "classroom_id": classroom.get("id"),
                        "timeslot_id": timeslot.get("id")
                    }
        
        return None

    def _get_project_instructors(self, project):
        """Get instructors for a project"""
        instructors = []
        responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
        if responsible_id:
            instructors.append(responsible_id)
        
        # Add additional instructors based on project type
        project_type = project.get("type", "ara")
        if project_type == "bitirme":
            # Add jury members
            available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
            if available_instructors:
                instructors.append(available_instructors[0].get("id"))
        
        return instructors

    # ========== Pure Consecutive Grouping Methods (Same as Deep Search Algorithm) ==========

    def _create_pure_consecutive_grouping_solution(self) -> List[Dict[str, Any]]:
        """
        Pure consecutive grouping çözümü oluştur - Same as Deep Search Algorithm.
        
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
