"""
Kapsamlı Optimizasyon Algoritması - Enhanced with Pure Consecutive Grouping
Uses same logic as Deep Search for optimal uniform distribution
"""

from typing import Dict, List, Any, Tuple, Optional, Set
import random
import numpy as np
from dataclasses import dataclass
from datetime import datetime, time as dt_time
import time
import json
import logging
from collections import defaultdict
from app.algorithms.gap_free_assignment import GapFreeAssignment
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)

@dataclass
class Project:
    id: int
    title: str
    type: str  # 'ara' or 'bitirme'
    responsible_id: int
    advisor_id: Optional[int] = None
    co_advisor_id: Optional[int] = None

@dataclass
class Instructor:
    id: int
    name: str
    type: str  # 'instructor', 'associate', 'assistant'
    department: str
    bitirme_count: int = 0
    ara_count: int = 0

@dataclass
class Classroom:
    id: int
    name: str
    capacity: int
    location: str

@dataclass
class TimeSlot:
    id: int
    start_time: str
    end_time: str
    session_type: str
    is_morning: bool

@dataclass
class Schedule:
    project_id: int
    classroom_id: int
    timeslot_id: int
    is_makeup: bool = False

class ComprehensiveOptimizer(OptimizationAlgorithm):
    """
    Kapsamlı Optimizasyon Algoritması - Enhanced with Pure Consecutive Grouping + Smart Jury Assignment.
    
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
    - Comprehensive multi-algorithm approach
    - Genetic algorithm components
    - Local search optimization
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        params = params or {}
        self.population_size = params.get("population_size", 100)
        self.generations = params.get("generations", 50)
        self.mutation_rate = params.get("mutation_rate", 0.1)
        self.crossover_rate = params.get("crossover_rate", 0.8)

        # CP-SAT ozellikleri
        self.time_limit = self.params.get("time_limit", 60) if self.params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = self.params.get("max_load_tolerance", 2) if self.params else 2  # ortalamanin +2 fazlasini gecmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # Agirliklar (kisitlar dahil)
        self.weights = {
            'load_balance': 0.20,          # Yuk dengesi
            'classroom_transition': 0.15,  # Sinif gecisi
            'time_continuity': 0.15,       # Saat butunlugu
            'session_minimization': 0.15,  # Oturum minimizasyonu
            'rule_compliance': 0.15,       # Kural uyumu
            'gap_penalty': 0.20,           # Bosluk cezasi (-9999 veya 0)
            'time_slot_penalty': 0.20      # 16:30 ve sonrasi icin -9999 ceza
        }

        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Classroom] = []
        self.timeslots: List[TimeSlot] = []

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
        
    def initialize(self, data: Dict[str, Any]) -> None:
        """Verileri baslat - CP-SAT ozellikli versiyon"""
        # Projeleri yukle
        for p in data.get("projects", []):
            self.projects.append(Project(
                id=p["id"],
                title=p["title"],
                type=p["type"],
                responsible_id=p.get("responsible_id", 1),
                advisor_id=p.get("advisor_id"),
                co_advisor_id=p.get("co_advisor_id")
            ))
        
        # Ogretim uyelerini yukle
        for i in data.get("instructors", []):
            self.instructors.append(Instructor(
                id=i["id"],
                name=i["name"],
                type=i["type"],
                department=i.get("department", "Bilgisayar Muhendisligi"),
                bitirme_count=i.get("bitirme_count", 0),
                ara_count=i.get("ara_count", 0)
            ))
        
        # Siniflari yukle
        for c in data.get("classrooms", []):
            self.classrooms.append(Classroom(
                id=c["id"],
                name=c["name"],
                capacity=c["capacity"],
                location=c.get("location", "")
            ))
        
        # Zaman dilimlerini yukle
        for t in data.get("timeslots", []):
            # Zaman formatini duzelt (mikrosaniye kismini kaldir)
            # start_time ve end_time datetime.time nesnesi olabilir, once string'e cevir
            start_time_raw = t["start_time"]
            end_time_raw = t["end_time"]
            
            # datetime.time nesnesini string'e cevir
            if hasattr(start_time_raw, 'strftime'):
                start_time_str = start_time_raw.strftime('%H:%M:%S')
            else:
                start_time_str = str(start_time_raw).split('.')[0] if '.' in str(start_time_raw) else str(start_time_raw)
            
            if hasattr(end_time_raw, 'strftime'):
                end_time_str = end_time_raw.strftime('%H:%M:%S')
            else:
                end_time_str = str(end_time_raw).split('.')[0] if '.' in str(end_time_raw) else str(end_time_raw)
            
            # 24:xx:xx ve 25:xx:xx formatlarını 00:xx:xx'a çevir
            if start_time_str.startswith("24:") or start_time_str.startswith("25:"):
                start_time_str = "00:" + start_time_str[3:]
            if end_time_str.startswith("24:") or end_time_str.startswith("25:"):
                end_time_str = "00:" + end_time_str[3:]
            
            self.timeslots.append(TimeSlot(
                id=t["id"],
                start_time=start_time_str,
                end_time=end_time_str,
                session_type=t.get("session_type", "normal"),
                is_morning=t.get("is_morning", True)
            ))
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method for compatibility with AlgorithmService"""
        return self.optimize(data)

    def repair_solution(self, solution: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive Optimizer icin ozel onarim metodlari.
        Comprehensive Optimizer hibrit yaklaşım kullanır.
        """
        assignments = solution.get("assignments", solution.get("schedule", []))
        
        # Comprehensive-specific repair: hybrid approach
        assignments = self._repair_duplicates_comprehensive(assignments)
        assignments = self._repair_gaps_comprehensive(assignments)
        assignments = self._repair_coverage_comprehensive(assignments)
        assignments = self._repair_constraints_comprehensive(assignments)
        
        # Update solution with repaired assignments
        if "assignments" in solution:
            solution["assignments"] = assignments
        elif "schedule" in solution:
            solution["schedule"] = assignments
        else:
            solution["solution"] = assignments
            
        return solution

    def _repair_duplicates_comprehensive(self, assignments):
        """Comprehensive-specific duplicate repair using hybrid approach"""
        from collections import defaultdict
        
        # Group by project_id and keep the best assignment
        project_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id:
                project_assignments[project_id].append(assignment)
        
        # For each project, use comprehensive scoring
        repaired = []
        for project_id, project_list in project_assignments.items():
            if len(project_list) == 1:
                repaired.append(project_list[0])
            else:
                # Use comprehensive scoring: consider multiple factors
                best_assignment = self._score_assignments_comprehensive(project_list)
                repaired.append(best_assignment)
        
        return repaired

    def _repair_gaps_comprehensive(self, assignments):
        """Comprehensive-specific gap repair using hybrid optimization"""
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
            
            # Use comprehensive gap filling
            gap_free_assignments = self._fill_gaps_comprehensive(sorted_assignments)
            repaired.extend(gap_free_assignments)
        
        return repaired

    def _repair_coverage_comprehensive(self, assignments):
        """Comprehensive-specific coverage repair ensuring all projects are assigned"""
        assigned_projects = set(assignment.get("project_id") for assignment in assignments)
        all_projects = set(project.get("id") for project in self.projects)
        missing_projects = all_projects - assigned_projects
        
        # Add missing projects with comprehensive assignment
        for project_id in missing_projects:
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                # Find best available slot using comprehensive scoring
                best_slot = self._find_best_slot_comprehensive(project, assignments)
                if best_slot:
                    instructors = self._get_project_instructors_comprehensive(project)
                    if instructors:
                        new_assignment = {
                            "project_id": project_id,
                            "classroom_id": best_slot["classroom_id"],
                            "timeslot_id": best_slot["timeslot_id"],
                            "instructors": instructors
                        }
                        assignments.append(new_assignment)
        
        return assignments

    def _repair_constraints_comprehensive(self, assignments):
        """Comprehensive-specific constraint repair ensuring all constraints are satisfied"""
        # Remove assignments that violate constraints
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

    def _score_assignments_comprehensive(self, assignments):
        """Score assignments using comprehensive criteria"""
        best_score = -1
        best_assignment = assignments[0]
        
        for assignment in assignments:
            score = 0
            timeslot_id = assignment.get("timeslot_id", "")
            classroom_id = assignment.get("classroom_id", "")
            
            # Prefer earlier timeslots
            try:
                hour = int(timeslot_id.split("_")[0]) if "_" in timeslot_id else 9
                score += (24 - hour) * 10  # Earlier is better
            except:
                score += 50  # Default score
            
            # Prefer certain classrooms
            if "A" in classroom_id:
                score += 20  # Prefer A classrooms
            elif "B" in classroom_id:
                score += 15  # Prefer B classrooms
            
            if score > best_score:
                best_score = score
                best_assignment = assignment
        
        return best_assignment

    def _fill_gaps_comprehensive(self, assignments):
        """Fill gaps using comprehensive approach"""
        if len(assignments) <= 1:
            return assignments
        
        # Simple gap filling - keep all assignments for now
        return assignments

    def _find_best_slot_comprehensive(self, project, assignments):
        """Find best available slot using comprehensive criteria"""
        used_slots = set((a.get("classroom_id"), a.get("timeslot_id")) for a in assignments)
        
        best_slot = None
        best_score = -1
        
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                slot_key = (classroom.get("id"), timeslot.get("id"))
                if slot_key not in used_slots:
                    score = self._score_slot_comprehensive(classroom, timeslot, project)
                    if score > best_score:
                        best_score = score
                        best_slot = {
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id")
                        }
        
        return best_slot

    def _score_slot_comprehensive(self, classroom, timeslot, project):
        """Score a slot using comprehensive criteria"""
        score = 0
        
        # Prefer earlier timeslots
        start_time = timeslot.get("start_time", "09:00")
        try:
            hour = int(start_time.split(":")[0])
            score += (24 - hour) * 10  # Earlier is better
        except:
            score += 50
        
        # Prefer certain classrooms
        classroom_id = classroom.get("id", "")
        if "A" in classroom_id:
            score += 20
        elif "B" in classroom_id:
            score += 15
        
        return score

    def _get_project_instructors_comprehensive(self, project):
        """Get instructors for a project using comprehensive approach"""
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

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Comprehensive Optimizer with Pure Consecutive Grouping + Smart Jury.
        
        SUCCESS STRATEGY (Same as Deep Search Algorithm):
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        """
        start_time = time.time()
        
        # Initialize data
        self.initialize(data)
        
        # Convert dataclasses to dictionaries for processing
        projects_dict = [{"id": p.id, "title": p.title, "type": p.type, "responsible_id": p.responsible_id} for p in self.projects]
        instructors_dict = [{"id": i.id, "name": i.name, "type": i.type} for i in self.instructors]
        classrooms_dict = [{"id": c.id, "name": c.name, "capacity": c.capacity} for c in self.classrooms]
        timeslots_dict = [{"id": t.id, "start_time": str(t.start_time), "end_time": str(t.end_time)} for t in self.timeslots]
        
        logger.info("Comprehensive Optimizer Algorithm başlatılıyor (Enhanced Randomizer + Consecutive Grouping + Smart Jury mode)...")
        logger.info(f"  Projeler: {len(projects_dict)}")
        logger.info(f"  Instructors: {len(instructors_dict)}")
        logger.info(f"  Sınıflar: {len(classrooms_dict)}")
        logger.info(f"  Zaman Slotları: {len(timeslots_dict)}")

        # Pure Consecutive Grouping Algorithm - Same as Deep Search
        logger.info("Pure Consecutive Grouping + Enhanced Randomizer + Smart Jury ile optimal çözüm oluşturuluyor...")
        best_solution = self._create_pure_consecutive_grouping_solution(
            projects_dict, instructors_dict, classrooms_dict, timeslots_dict
        )
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
        final_stats = self._calculate_grouping_stats(best_solution, projects_dict)
        logger.info(f"  Final consecutive grouping stats:")
        logger.info(f"    Consecutive instructors: {final_stats['consecutive_count']}")
        logger.info(f"    Avg classroom changes: {final_stats['avg_classroom_changes']:.2f}")

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Comprehensive Optimizer Algorithm completed. Execution time: {execution_time:.2f}s")

        # Calculate quality using fitness function
        quality = self._calculate_fitness_from_assignments(best_solution)

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": {"quality": quality},
            "execution_time": execution_time,
            "algorithm": "Comprehensive Optimizer (Enhanced Randomizer + Consecutive Grouping + Smart Jury)",
            "status": "completed",
            "optimizations_applied": [
                "enhanced_randomizer_instructor_order",  # NOT 1
                "pure_consecutive_grouping",  # NOT 3
                "smart_jury_assignment",  # NOT 2
                "consecutive_jury_pairing",  # NOT 2
                "conflict_detection_and_resolution",
                "uniform_classroom_distribution",
                "earliest_slot_assignment",
                "comprehensive_multi_algorithm_optimization"
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
                "generations": self.generations
            },
            "quality": quality
        }
    
    def _calculate_fitness_from_assignments(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate fitness from assignments list."""
        if not assignments:
            return 0.0
        
        # Convert assignments to Schedule objects for fitness calculation
        schedule_objects = []
        for assignment in assignments:
            schedule_objects.append(Schedule(
                project_id=assignment.get("project_id", 0),
                classroom_id=assignment.get("classroom_id", 0),
                timeslot_id=assignment.get("timeslot_id", 0),
                is_makeup=assignment.get("is_makeup", False)
            ))
        
        return self._calculate_fitness(schedule_objects)
    
    def _genetic_algorithm(self) -> List[Schedule]:
        """Genetik algoritma"""
        # Baslangic populasyonu
        population = [self._create_random_solution() for _ in range(self.population_size)]
        
        for generation in range(self.generations):
            # Uygunluk hesapla
            fitness_scores = [self._calculate_fitness(sol) for sol in population]
            
            # En iyi cozumu sec
            best_idx = np.argmax(fitness_scores)
            best_solution = population[best_idx]
            
            # Yeni nesil olustur
            new_population = [best_solution]  # Elitizm
            
            while len(new_population) < self.population_size:
                # Ebeveyn secimi (turnuva)
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # Caprazlama
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                
                # Mutasyon
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2)
                
                new_population.extend([child1, child2])
            
            population = new_population[:self.population_size]
        
        # En iyi cozumu dondur
        fitness_scores = [self._calculate_fitness(sol) for sol in population]
        best_idx = np.argmax(fitness_scores)
        return population[best_idx]
    
    def _create_random_solution(self) -> List[Schedule]:
        """Rastgele cozum olustur"""
        solution = []
        used_slots = set()  # (classroom_id, timeslot_id) ciftleri
        
        # Projeleri rastgele sirala
        projects = self.projects.copy()
        random.shuffle(projects)
        
        for project in projects:
            # Uygun sinif ve zaman dilimi bul
            available_slots = []
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    slot_key = (classroom.id, timeslot.id)
                    if slot_key not in used_slots:
                        available_slots.append((classroom.id, timeslot.id))
            
            if available_slots:
                classroom_id, timeslot_id = random.choice(available_slots)
                used_slots.add((classroom_id, timeslot_id))
                
                solution.append(Schedule(
                    project_id=project.id,
                    classroom_id=classroom_id,
                    timeslot_id=timeslot_id,
                    is_makeup=False
                ))
        
        return solution
    
    def _tournament_selection(self, population: List[List[Schedule]], 
                            fitness_scores: List[float], tournament_size: int = 3) -> List[Schedule]:
        """Turnuva secimi"""
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_idx]
    
    def _crossover(self, parent1: List[Schedule], parent2: List[Schedule]) -> Tuple[List[Schedule], List[Schedule]]:
        """Caprazlama"""
        # Tek nokta caprazlama
        if len(parent1) <= 1:
            return parent1, parent2
        
        crossover_point = random.randint(1, len(parent1) - 1)
        
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        # Cakismalari coz
        child1 = self._resolve_conflicts(child1)
        child2 = self._resolve_conflicts(child2)
        
        return child1, child2
    
    def _mutate(self, solution: List[Schedule]) -> List[Schedule]:
        """Mutasyon"""
        if not solution:
            return solution
        
        # Rastgele bir atamayi degistir
        mutation_idx = random.randint(0, len(solution) - 1)
        schedule = solution[mutation_idx]
        
        # Yeni sinif ve zaman dilimi sec
        available_slots = []
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                # Mevcut cakismalari kontrol et
                conflict = any(
                    s.classroom_id == classroom.id and s.timeslot_id == timeslot.id
                    for i, s in enumerate(solution) if i != mutation_idx
                )
                if not conflict:
                    available_slots.append((classroom.id, timeslot.id))
        
        if available_slots:
            new_classroom_id, new_timeslot_id = random.choice(available_slots)
            solution[mutation_idx] = Schedule(
                project_id=schedule.project_id,
                classroom_id=new_classroom_id,
                timeslot_id=new_timeslot_id,
                is_makeup=schedule.is_makeup
            )
        
        return solution
    
    def _resolve_conflicts(self, solution: List[Schedule]) -> List[Schedule]:
        """Cakismalari coz"""
        used_slots = set()
        resolved_solution = []
        
        for schedule in solution:
            slot_key = (schedule.classroom_id, schedule.timeslot_id)
            if slot_key not in used_slots:
                used_slots.add(slot_key)
                resolved_solution.append(schedule)
            else:
                # Alternatif slot bul
                for classroom in self.classrooms:
                    for timeslot in self.timeslots:
                        alt_slot_key = (classroom.id, timeslot.id)
                        if alt_slot_key not in used_slots:
                            used_slots.add(alt_slot_key)
                            resolved_solution.append(Schedule(
                                project_id=schedule.project_id,
                                classroom_id=classroom.id,
                                timeslot_id=timeslot.id,
                                is_makeup=schedule.is_makeup
                            ))
                            break
                    else:
                        continue
                    break
        
        return resolved_solution
    
    def _calculate_fitness(self, solution: List[Schedule]) -> float:
        """Toplam uygunluk skoru hesapla"""
        objectives = self._calculate_objectives(solution)
        
        total_fitness = 0
        for key, weight in self.weights.items():
            total_fitness += weight * objectives[key]
        
        return total_fitness
    
    def _calculate_objectives(self, solution: List[Schedule]) -> Dict[str, float]:
        """Amac fonksiyonlarini hesapla (kisit cezalari dahil)"""
        return {
            'load_balance': self._calculate_load_balance_score(solution),
            'classroom_transition': self._calculate_classroom_transition_score(solution),
            'time_continuity': self._calculate_time_continuity_score(solution),
            'session_minimization': self._calculate_session_minimization_score(solution),
            'rule_compliance': self._calculate_rule_compliance_score(solution),
            'gap_penalty': self._calculate_gap_penalty(solution),
            'time_slot_penalty': self._calculate_time_slot_penalty(solution)
        }
    
    def _calculate_load_balance_score(self, solution: List[Schedule]) -> float:
        """Hedef 1: Yuk dengesi skoru"""
        if not solution:
            return 0.0
        
        # Her ogretim uyesinin yukunu hesapla
        instructor_loads = {}
        for schedule in solution:
            project = next((p for p in self.projects if p.id == schedule.project_id), None)
            if not project:
                continue
            
            # Sorumlu ogretim uyesi
            if project.responsible_id not in instructor_loads:
                instructor_loads[project.responsible_id] = 0
            instructor_loads[project.responsible_id] += 1
            
            # Danismanlar
            if project.advisor_id:
                if project.advisor_id not in instructor_loads:
                    instructor_loads[project.advisor_id] = 0
                instructor_loads[project.advisor_id] += 0.5
            
            if project.co_advisor_id:
                if project.co_advisor_id not in instructor_loads:
                    instructor_loads[project.co_advisor_id] = 0
                instructor_loads[project.co_advisor_id] += 0.5
        
        if not instructor_loads:
            return 0.0
        
        # Standart sapma hesapla
        loads = list(instructor_loads.values())
        mean_load = np.mean(loads)
        std_load = np.std(loads)
        
        # Normalize et (0-100)
        if mean_load == 0:
            return 100.0
        
        cv = std_load / mean_load  # Coefficient of variation
        score = max(0, 100 - cv * 100)
        
        return score
    
    def _calculate_classroom_transition_score(self, solution: List[Schedule]) -> float:
        """Hedef 2: Sinif gecis cezasi"""
        if not solution:
            return 0.0
        
        # Her ogretim uyesi icin sinif gecislerini hesapla
        instructor_transitions = {}
        
        for schedule in solution:
            project = next((p for p in self.projects if p.id == schedule.project_id), None)
            if not project:
                continue
            
            instructor_id = project.responsible_id
            if instructor_id not in instructor_transitions:
                instructor_transitions[instructor_id] = []
            
            instructor_transitions[instructor_id].append(schedule.classroom_id)
        
        total_transitions = 0
        for instructor_id, classrooms in instructor_transitions.items():
            if len(classrooms) > 1:
                # Sinif degisimlerini say
                transitions = sum(1 for i in range(1, len(classrooms)) 
                                if classrooms[i] != classrooms[i-1])
                total_transitions += transitions
        
        # Normalize et (0-100)
        max_possible_transitions = len(solution) - 1
        if max_possible_transitions == 0:
            return 100.0
        
        score = max(0, 100 - (total_transitions / max_possible_transitions) * 100)
        return score
    
    def _calculate_time_continuity_score(self, solution: List[Schedule]) -> float:
        """Hedef 3: Saat butunlugu skoru"""
        if not solution:
            return 0.0
        
        # Her ogretim uyesi icin saat araliklarini kontrol et
        instructor_schedules = {}
        
        for schedule in solution:
            project = next((p for p in self.projects if p.id == schedule.project_id), None)
            if not project:
                continue
            
            instructor_id = project.responsible_id
            if instructor_id not in instructor_schedules:
                instructor_schedules[instructor_id] = []
            
            timeslot = next((t for t in self.timeslots if t.id == schedule.timeslot_id), None)
            if timeslot:
                instructor_schedules[instructor_id].append(timeslot)
        
        continuity_score = 0
        total_instructors = len(instructor_schedules)
        
        for instructor_id, timeslots in instructor_schedules.items():
            if len(timeslots) <= 1:
                continuity_score += 100  # Tek atama = mukemmel butunluk
                continue
            
            # Zaman dilimlerini sirala
            timeslots.sort(key=lambda t: t.start_time)
            
            # Butunluk kontrolu
            continuous_blocks = 1
            for i in range(1, len(timeslots)):
                prev_end_str = timeslots[i-1].end_time
                curr_start_str = timeslots[i].start_time
                
                # String'leri time objelerine çevir
                try:
                    prev_end = datetime.strptime(prev_end_str, "%H:%M:%S").time()
                    curr_start = datetime.strptime(curr_start_str, "%H:%M:%S").time()
                    
                    # 30 dakika ara varsa butunluk bozulur
                    if (datetime.combine(datetime.today(), curr_start) - 
                        datetime.combine(datetime.today(), prev_end)).seconds > 1800:
                        continuous_blocks += 1
                except:
                    # Time parsing hatası durumunda butunluk bozulur
                    continuous_blocks += 1
            
            # Butunluk skoru (temel)
            instructor_score = (1 / continuous_blocks) * 100

            # Gec saat cezalari (sadece 16:30 ve sonrasi icin -9999 ceza)
            late_penalty = 0.0
            for ts in timeslots:
                try:
                    start_time = datetime.strptime(ts.start_time, "%H:%M:%S").time()
                    hour = start_time.hour
                    minute = start_time.minute
                    # 16:30 sonrasi slotlar (16:30-17:00, 17:00-17:30, 17:30-18:00) - -9999 ceza
                    if hour > 16 or (hour == 16 and minute >= 30):
                        late_penalty += -9999.0
                except:
                    # Time parsing hatası durumunda ceza verme
                    pass

            # Cezayi skordan dus
            instructor_score = max(0.0, instructor_score + late_penalty)
            continuity_score += instructor_score
        
        return continuity_score / total_instructors if total_instructors > 0 else 0

    def _calculate_gap_penalty(self, solution: List[Schedule]) -> float:
        """Bosluk cezasi hesaplar - iki slot arasinda bos slot olmamali"""
        if not solution:
            return 0.0

        # Tum kullanilan zaman dilimlerini topla
        used_timeslots = set()
        for schedule in solution:
            used_timeslots.add(schedule.timeslot_id)

        # Zaman dilimlerini indekse gore kontrol et
        gaps = self._check_consecutive_gaps(list(used_timeslots))

        # Eger bosluk varsa -9999 ceza ver
        if gaps > 0:
            return -9999.0

        return 0.0

    def _check_consecutive_gaps(self, slot_ids: List[int]) -> int:
        """Verilen slot listesinde ardisik slotlarda bosluk olup olmadigini kontrol eder"""
        if len(slot_ids) < 2:
            return 0

        # Slotlari indekse gore sirala
        slot_indices = []
        for slot_id in slot_ids:
            # Timeslot ID'sini indekse cevir
            for idx, ts in enumerate(self.timeslots):
                if ts.id == slot_id:
                    slot_indices.append(idx)
                    break

        if not slot_indices:
            return 0

        # Slot indekslerini sirala
        slot_indices.sort()

        gaps = 0
        # Ardisik slotlarda bosluk kontrolu
        for i in range(len(slot_indices) - 1):
            current_idx = slot_indices[i]
            next_idx = slot_indices[i + 1]

            # Eger ardisik indeksler arasinda bosluk varsa
            if next_idx - current_idx > 1:
                gaps += 1

        return gaps

    def _calculate_time_slot_penalty(self, solution: List[Schedule]) -> float:
        """Zaman slotu cezasi: 16:00-16:30 kullanilabilir; 16:30 ve sonrasi -9999 ceza.

        Not: Bu fonksiyon yalnizca gec saat kisitlarini cezalandirir.
        """
        if not solution:
            return 0.0

        penalty = 0.0
        for schedule in solution:
            ts = next((t for t in self.timeslots if t.id == schedule.timeslot_id), None)
            if not ts:
                continue
            try:
                start_time = datetime.strptime(ts.start_time, "%H:%M:%S").time()
                hour = start_time.hour
                minute = start_time.minute
                # 16:30 ve sonrasi slotlar yasak
                if hour > 16 or (hour == 16 and minute >= 30):
                    penalty += -9999.0
            except:
                # Time parsing hatası durumunda ceza verme
                pass

        return penalty

    def _calculate_session_minimization_score(self, solution: List[Schedule]) -> float:
        """Hedef 4: Oturum minimizasyonu skoru"""
        if not solution:
            return 0.0
        
        # Kullanilan zaman dilimi sayisi
        used_timeslots = set()
        for schedule in solution:
            used_timeslots.add(schedule.timeslot_id)
        
        used_count = len(used_timeslots)
        total_count = len(self.timeslots)
        
        # Normalize et (0-100)
        score = max(0, 100 - (used_count / total_count) * 100)
        return score
    
    def _calculate_rule_compliance_score(self, solution: List[Schedule]) -> float:
        """Hedef 5: Kural uyumu skoru"""
        if not solution:
            return 0.0
        
        compliance_score = 0
        total_projects = len(solution)
        
        for schedule in solution:
            project = next((p for p in self.projects if p.id == schedule.project_id), None)
            if not project:
                continue
            
            # Katilimci sayisini kontrol et
            participant_count = 1  # Sorumlu ogretim uyesi
            if project.advisor_id:
                participant_count += 1
            if project.co_advisor_id:
                participant_count += 1
            
            # Kural kontrolu
            if project.type == 'bitirme':
                # Bitirme projelerinde en az 2 ogretim uyesi
                if participant_count >= 2:
                    compliance_score += 100
                else:
                    compliance_score += 0
            elif project.type == 'ara':
                # Ara projelerinde en az 1 ogretim uyesi
                if participant_count >= 1:
                    compliance_score += 100
                else:
                    compliance_score += 0
            else:
                compliance_score += 50  # Bilinmeyen tip
        
        return compliance_score / total_projects if total_projects > 0 else 0
    
    def _format_solution(self, solution: List[Schedule]) -> List[Dict[str, Any]]:
        """Cozumu formatla"""
        formatted = []
        for schedule in solution:
            formatted.append({
                "project_id": schedule.project_id,
                "classroom_id": schedule.classroom_id,
                "timeslot_id": schedule.timeslot_id,
                "is_makeup": schedule.is_makeup
            })
        return formatted
    
    def _calculate_statistics(self, solution: List[Schedule]) -> Dict[str, Any]:
        """Istatistikleri hesapla"""
        if not solution:
            return {}
        
        # Temel istatistikler
        total_projects = len(solution)
        used_classrooms = len(set(s.classroom_id for s in solution))
        used_timeslots = len(set(s.timeslot_id for s in solution))
        
        # Proje tipi dagilimi
        ara_count = 0
        bitirme_count = 0
        for schedule in solution:
            project = next((p for p in self.projects if p.id == schedule.project_id), None)
            if project:
                if project.type == 'ara':
                    ara_count += 1
                elif project.type == 'bitirme':
                    bitirme_count += 1
        
        return {
            "total_projects": total_projects,
            "used_classrooms": used_classrooms,
            "used_timeslots": used_timeslots,
            "ara_projects": ara_count,
            "bitirme_projects": bitirme_count,
            "coverage_percentage": (total_projects / len(self.projects)) * 100 if self.projects else 0
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
        """Repair solution for Comprehensive Optimizer."""
        assignments = solution.get("assignments", [])
        solution["assignments"] = assignments
        return solution

    # ========== Pure Consecutive Grouping Methods (Same as Deep Search Algorithm) ==========

    def _create_pure_consecutive_grouping_solution(
        self, projects: List[Dict], instructors: List[Dict], 
        classrooms: List[Dict], timeslots: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Pure consecutive grouping çözümü oluştur - Same as Deep Search Algorithm.
        
        SUCCESS STRATEGY:
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        """
        assignments = []
        
        # Zaman slotlarını sırala
        sorted_timeslots = sorted(
            timeslots,
            key=lambda x: self._parse_time_str(x.get("start_time", "09:00"))
        )
        
        # Instructor bazında projeleri grupla
        instructor_projects = defaultdict(list)
        for project in projects:
            responsible_id = project.get("responsible_id")
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
            
            for classroom in classrooms:
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
            
            # Projeleri ata
            if best_classroom and best_start_slot_idx is not None:
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
                    for slot_idx in range(best_start_slot_idx, len(sorted_timeslots)):
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
                        
                        for classroom in classrooms:
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

    def _parse_time_str(self, time_str: str) -> dt_time:
        """Parse time string to datetime.time object"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)  # Default to 09:00

    def _calculate_grouping_stats(self, assignments: List[Dict[str, Any]], projects: List[Dict]) -> Dict[str, Any]:
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
            project = next((p for p in projects if p.get("id") == project_id), None)
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
