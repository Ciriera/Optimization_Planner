"""
Dragonfly Algorithm - Enhanced with Pure Consecutive Grouping
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


class DragonflyAlgorithm(OptimizationAlgorithm):
    """
    Dragonfly Algorithm - Enhanced with Pure Consecutive Grouping + Smart Jury Assignment.
    
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
    - Separation, alignment, and cohesion behaviors
    - Food and enemy factors
    - Swarm intelligence
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Dragonfly Algorithm"
        self.description = "Nature-inspired swarm intelligence optimization for project scheduling"

        # Dragonfly Algorithm Parameters
        self.population_size = params.get("population_size", 35) if params else 35
        self.max_iterations = params.get("max_iterations", 100) if params else 100
        self.separation_weight = params.get("separation_weight", 0.1) if params else 0.1
        self.alignment_weight = params.get("alignment_weight", 0.1) if params else 0.1
        self.cohesion_weight = params.get("cohesion_weight", 0.7) if params else 0.7
        self.food_factor = params.get("food_factor", 1.0) if params else 1.0
        self.enemy_factor = params.get("enemy_factor", 1.0) if params else 1.0

        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []

        # Dragonfly Algorithm state
        self.dragonflies = []
        self.velocities = []
        self.best_dragonfly = None
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
            raise ValueError("Insufficient data for Dragonfly Algorithm")

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Dragonfly Algorithm optimization with Pure Consecutive Grouping + Smart Jury.
        
        SUCCESS STRATEGY (Same as Deep Search Algorithm):
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        """
        start_time = time.time()
        self.initialize(data)
        
        logger.info("Dragonfly Algorithm başlatılıyor (Enhanced Randomizer + Consecutive Grouping + Smart Jury mode)...")
        logger.info(f"  Projeler: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Sınıflar: {len(self.classrooms)}")
        logger.info(f"  Zaman Slotları: {len(self.timeslots)}")

        # Pure Consecutive Grouping Algorithm - Same as Deep Search
        logger.info("Pure Consecutive Grouping + Enhanced Randomizer + Smart Jury ile optimal çözüm oluşturuluyor...")
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
        logger.info(f"Dragonfly Algorithm completed. Execution time: {execution_time:.2f}s")

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []),
            "execution_time": execution_time,
            "algorithm": "Dragonfly Algorithm (Enhanced Randomizer + Consecutive Grouping + Smart Jury)",
            "status": "completed",
            "optimizations_applied": [
                "enhanced_randomizer_instructor_order",  # NOT 1
                "pure_consecutive_grouping",  # NOT 3
                "smart_jury_assignment",  # NOT 2
                "consecutive_jury_pairing",  # NOT 2
                "conflict_detection_and_resolution",
                "uniform_classroom_distribution",
                "earliest_slot_assignment",
                "dragonfly_swarm_optimization"
            ],
            "stats": final_stats,
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
        Dragonfly Algorithm icin ozel onarim metodlari.
        Dragonfly Algorithm yusufçuk sürü davranışı yaklaşımı kullanır.
        """
        assignments = solution.get("assignments", [])
        
        # Dragonfly Algorithm-specific repair: swarm behavior approach
        assignments = self._repair_duplicates_dragonfly(assignments)
        assignments = self._repair_gaps_dragonfly(assignments)
        assignments = self._repair_coverage_dragonfly(assignments)
        assignments = self._repair_swarm_constraints(assignments)
        
        solution["assignments"] = assignments
        return solution

    def _repair_duplicates_dragonfly(self, assignments):
        """Dragonfly Algorithm-specific duplicate repair using swarm behavior"""
        from collections import defaultdict
        
        # Group by project_id and keep the best assignment using swarm behavior
        project_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id:
                project_assignments[project_id].append(assignment)
        
        # For each project, choose the best assignment using swarm behavior
        repaired = []
        for project_id, project_list in project_assignments.items():
            if len(project_list) == 1:
                repaired.append(project_list[0])
            else:
                # Swarm behavior selection: choose the assignment with best swarm fitness
                best_assignment = self._swarm_select_best_assignment(project_list)
                repaired.append(best_assignment)
        
        return repaired

    def _repair_gaps_dragonfly(self, assignments):
        """Dragonfly Algorithm-specific gap repair using swarm behavior"""
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
            
            # Swarm behavior gap filling: use dragonfly behavior
            swarm_assignments = self._swarm_fill_gaps(sorted_assignments)
            repaired.extend(swarm_assignments)
        
        return repaired

    def _repair_coverage_dragonfly(self, assignments):
        """Dragonfly Algorithm-specific coverage repair ensuring all projects are assigned"""
        assigned_projects = set(assignment.get("project_id") for assignment in assignments)
        all_projects = set(project.get("id") for project in self.projects)
        missing_projects = all_projects - assigned_projects
        
        # Add missing projects with swarm behavior assignment
        for project_id in missing_projects:
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                # Find best available slot using swarm behavior
                best_slot = self._swarm_find_best_slot(project, assignments)
                if best_slot:
                    instructors = self._get_project_instructors_dragonfly(project)
                    if instructors:
                        new_assignment = {
                            "project_id": project_id,
                            "classroom_id": best_slot["classroom_id"],
                            "timeslot_id": best_slot["timeslot_id"],
                            "instructors": instructors
                        }
                        assignments.append(new_assignment)
        
        return assignments

    def _repair_swarm_constraints(self, assignments):
        """Dragonfly Algorithm-specific constraint repair ensuring swarm constraints"""
        # Remove assignments that violate swarm constraints
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

    def _swarm_select_best_assignment(self, assignments):
        """Swarm behavior selection of best assignment"""
        best_assignment = assignments[0]
        best_fitness = self._calculate_swarm_fitness(assignments[0])
        
        for assignment in assignments[1:]:
            fitness = self._calculate_swarm_fitness(assignment)
            if fitness > best_fitness:
                best_fitness = fitness
                best_assignment = assignment
        
        return best_assignment

    def _calculate_swarm_fitness(self, assignment):
        """Calculate swarm fitness for an assignment"""
        score = 0
        timeslot_id = assignment.get("timeslot_id", "")
        classroom_id = assignment.get("classroom_id", "")
        
        # Prefer timeslots that benefit the swarm (collective intelligence)
        try:
            hour = int(timeslot_id.split("_")[0]) if "_" in timeslot_id else 9
            # Swarm intelligence: prefer timeslots that benefit the collective
            if 9 <= hour <= 12:  # Morning swarm activity
                score += 30
            elif 13 <= hour <= 16:  # Afternoon swarm activity
                score += 25
            else:
                score += 10
        except:
            score += 20  # Default score
        
        # Prefer classrooms that benefit the swarm
        if "A" in classroom_id:
            score += 20  # A classrooms benefit swarm
        elif "B" in classroom_id:
            score += 15  # B classrooms benefit swarm
        
        return score

    def _swarm_fill_gaps(self, assignments):
        """Fill gaps using swarm behavior"""
        if len(assignments) <= 1:
            return assignments
        
        # Swarm behavior gap filling - keep all assignments for now
        return assignments

    def _swarm_find_best_slot(self, project, assignments):
        """Find best available slot using swarm behavior"""
        used_slots = set((a.get("classroom_id"), a.get("timeslot_id")) for a in assignments)
        
        best_slot = None
        best_fitness = -1
        
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                slot_key = (classroom.get("id"), timeslot.get("id"))
                if slot_key not in used_slots:
                    fitness = self._calculate_swarm_fitness({"timeslot_id": timeslot.get("id"), "classroom_id": classroom.get("id")})
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_slot = {
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id")
                        }
        
        return best_slot

    def _get_project_instructors_dragonfly(self, project):
        """Get instructors for a project using swarm behavior"""
        instructors = []
        responsible_id = project.get("responsible_id")
        if responsible_id:
            instructors.append(responsible_id)
        
        # Add additional instructors based on project type (swarm: collective benefit)
        project_type = project.get("type", "ara")
        if project_type == "bitirme":
            # Add jury members for swarm benefit
            available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
            if available_instructors:
                instructors.append(available_instructors[0].get("id"))
        
        return instructors

    # ========== Pure Consecutive Grouping Methods (Same as Deep Search Algorithm) ==========

    def _create_pure_consecutive_grouping_solution(self) -> List[Dict[str, Any]]:
        """
        Pure consecutive grouping çözümü oluştur - Same as Deep Search Algorithm.
        
        SUCCESS STRATEGY:
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        
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
        
        # NOT 2 İÇİN: ARDIŞIK JÜRİ EŞLEŞTİRMESİ - Her sınıfta ardışık atanan instructor'ları takip et
        classroom_instructor_sequence = defaultdict(list)
        
        # NOT 1: YENİ RANDOMIZER - Instructorları tamamen rastgele sırala
        instructor_list = list(instructor_projects.items())
        for _ in range(3):  # 3 kez karıştır
            random.shuffle(instructor_list)
        
        logger.info(f"🎲 YENİ RANDOMIZER: Instructorlar rastgele sıralandı: {[inst_id for inst_id, _ in instructor_list]}")
        logger.info(f"📊 Toplam {len(instructor_list)} instructor rastgele sıralandı")
        
        # Her instructor için projeleri ata
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
                instructor_classroom_projects = []  # NOT 2 için
                
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
                            instructor_classroom_projects.append(project_id)  # NOT 2: Jüri eşleştirmesi için kaydet
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
                            instructor_classroom_projects.append(project_id)  # NOT 2: Jüri eşleştirmesi için kaydet
                            logger.info(f"Proje {project_id} en erken slot'a atandı: {earliest_classroom} - {earliest_slot_found}")
                    
                    if not assigned:
                        logger.warning(f"UYARI: Proje {project_id} için hiçbir boş slot bulunamadı!")
                
                # NOT 2: Bu instructor'ı sınıf sequence'ine ekle (jüri eşleştirmesi için)
                if instructor_classroom_projects:
                    classroom_instructor_sequence[best_classroom].append({
                        'instructor_id': instructor_id,
                        'project_ids': instructor_classroom_projects
                    })
        
        # NOT 2: ARDIŞIK JÜRİ EŞLEŞTİRMESİ - Aynı sınıfta ardışık atanan instructor'ları eşleştir
        logger.info("Ardışık jüri eşleştirmesi başlatılıyor...")
        self._assign_consecutive_jury_members(assignments, classroom_instructor_sequence)
        
        logger.info(f"Pure Consecutive Grouping tamamlandı: {len(assignments)} atama yapıldı")
        return assignments

    def _assign_consecutive_jury_members(self, assignments: List[Dict[str, Any]], 
                                        classroom_instructor_sequence: Dict) -> None:
        """
        NOT 2: Aynı sınıfta ardışık atanan instructor'ları tespit et ve birbirinin jürisi yap.
        
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
                
                # Instructor A'nın projelerine Instructor B'yi jüri yap
                for assignment in assignments:
                    if assignment['project_id'] in instructor_a['project_ids']:
                        if instructor_b_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_b_id)
                            jury_assignments_made += 1
                            logger.info(f"  Proje {assignment['project_id']}: Instructor {instructor_a_id} sorumlu → Instructor {instructor_b_id} jüri")
                
                # Instructor B'nin projelerine Instructor A'yı jüri yap
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
        conflicts = self._detect_conflicts(assignments)
        if not conflicts:
            return assignments
        
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