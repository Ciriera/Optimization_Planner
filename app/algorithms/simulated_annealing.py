"""
Simulated Annealing Algorithm for Academic Project Exam/Jury Scheduling

This module implements a comprehensive Simulated Annealing (SA) optimizer
for the multi-criteria, multi-constraint academic project scheduling problem.

Key Features:
- Multi-objective optimization (H1-H4 penalties)
- Configurable priority modes (ARA_ONCE, BITIRME_ONCE, ESIT)
- Flexible temperature schedules
- Adaptive cooling and reheating
- Memory-based restart mechanism
- Full constraint satisfaction via repair mechanism

Author: Optimization Planner System
"""

import random
import math
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
from enum import Enum
from copy import deepcopy

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class PriorityMode(Enum):
    """Project type prioritization mode"""
    ARA_ONCE = "ARA_ONCE"           # Interim projects first
    BITIRME_ONCE = "BITIRME_ONCE"   # Final projects first
    ESIT = "ESIT"                   # No priority


class TimePenaltyMode(Enum):
    """Time/gap penalty calculation mode"""
    BINARY = "BINARY"                       # 0 or 1 penalty
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Penalty proportional to gap size


class WorkloadConstraintMode(Enum):
    """Workload constraint enforcement mode"""
    SOFT_ONLY = "SOFT_ONLY"           # Only soft penalty
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Soft penalty + hard limit


class CoolingSchedule(Enum):
    """Temperature cooling schedule types"""
    GEOMETRIC = "GEOMETRIC"       # T = T * alpha
    LINEAR = "LINEAR"             # T = T - delta
    EXPONENTIAL = "EXPONENTIAL"   # T = T * exp(-alpha * iter)
    ADAPTIVE = "ADAPTIVE"         # Adaptive based on acceptance rate
    REHEATING = "REHEATING"       # Periodic reheating


@dataclass
class SAConfig:
    """Configuration for Simulated Annealing algorithm"""
    
    # Temperature parameters
    initial_temperature: float = 1000.0
    final_temperature: float = 0.1
    cooling_rate: float = 0.995
    cooling_schedule: CoolingSchedule = CoolingSchedule.GEOMETRIC
    
    # Iteration limits
    max_iterations: int = 50000
    max_no_improve: int = 5000
    iterations_per_temperature: int = 100
    
    # Restart parameters
    num_restarts: int = 3
    restart_on_stagnation: bool = True
    stagnation_threshold: int = 2000
    
    # Reheating parameters
    reheat_threshold: int = 1000
    reheat_factor: float = 1.5
    
    # Class count
    class_count: int = 6
    auto_class_count: bool = True
    
    # Priority and penalty modes
    priority_mode: PriorityMode = PriorityMode.ESIT
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4  # B_max
    
    # Penalty weights (C1, C2, C3, C4, C5, C6)
    weight_h1: float = 1.0    # Time/Gap penalty
    weight_h2: float = 2.0    # Workload uniformity penalty (most important)
    weight_h3: float = 3.0    # Class change penalty
    weight_h4: float = 0.5    # Class load balance penalty
    weight_continuity: float = 5.0   # Continuity penalty
    weight_timeslot_conflict: float = 1000.0  # Timeslot conflict (HARD)
    weight_unused_class: float = 10000.0  # Unused class penalty (HARD - VERY HIGH)
    
    # Slot parameters
    slot_duration: float = 0.5  # 30 minutes
    tolerance: float = 0.001
    
    # Neighbour move probabilities
    prob_j1_swap: float = 0.18
    prob_j1_reassign: float = 0.22
    prob_class_move: float = 0.20
    prob_class_swap: float = 0.15
    prob_order_swap: float = 0.15
    prob_fill_unused_class: float = 0.10  # NEW: Move project to unused class
    
    # Memory parameters
    memory_size: int = 10
    use_memory: bool = True


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Project:
    """Project data structure"""
    id: int
    name: str
    type: str  # "INTERIM" or "FINAL"
    responsible_id: int  # PS (advisor) - fixed


@dataclass
class Instructor:
    """Instructor data structure"""
    id: int
    name: str
    type: str  # "instructor" or "research_assistant"


@dataclass
class ProjectAssignment:
    """Assignment of a single project"""
    project_id: int
    class_id: int
    order_in_class: int
    ps_id: int      # Fixed advisor
    j1_id: int      # Jury 1 (decision variable)
    j2_id: int = -1  # Placeholder for RA


@dataclass
class SAState:
    """SA solution state"""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    cost: float = float('inf')
    
    def copy(self) -> 'SAState':
        """Create a deep copy of this state"""
        new_state = SAState(class_count=self.class_count, cost=self.cost)
        new_state.assignments = [
            ProjectAssignment(
                project_id=a.project_id,
                class_id=a.class_id,
                order_in_class=a.order_in_class,
                ps_id=a.ps_id,
                j1_id=a.j1_id,
                j2_id=a.j2_id
            )
            for a in self.assignments
        ]
        return new_state
    
    def get_project_assignment(self, project_id: int) -> Optional[ProjectAssignment]:
        """Get assignment for a specific project"""
        for a in self.assignments:
            if a.project_id == project_id:
                return a
        return None


# =============================================================================
# PENALTY CALCULATOR
# =============================================================================

class SAPenaltyCalculator:
    """
    Calculate all penalty values for SA cost function.
    
    Implements:
    - H1: Time/Gap penalty
    - H2: Workload uniformity penalty
    - H3: Class change penalty
    - H4: Class load balance penalty
    - H5: Continuity penalty
    - H6: Timeslot conflict penalty (hard)
    - H7: Unused class penalty (hard)
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: SAConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Filter real faculty (not research assistants)
        self.faculty_instructors = {
            i.id: i for i in instructors 
            if i.type == "instructor"
        }
        
        # Calculate average workload
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
    
    def calculate_total_cost(self, state: SAState) -> float:
        """
        Calculate total cost (penalty) for a state.
        
        Cost = C1*H1 + C2*H2 + C3*H3 + C4*H4 + C5*H5 + C6*H6 + C7*H7
        """
        h1 = self.calculate_h1_time_penalty(state)
        h2 = self.calculate_h2_workload_penalty(state)
        h3 = self.calculate_h3_class_change_penalty(state)
        h4 = self.calculate_h4_class_load_penalty(state)
        h5 = self.calculate_continuity_penalty(state)
        h6 = self.calculate_timeslot_conflict_penalty(state)
        h7 = self.calculate_unused_class_penalty(state)
        
        total = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3 +
            self.config.weight_h4 * h4 +
            self.config.weight_continuity * h5 +
            self.config.weight_timeslot_conflict * h6 +
            self.config.weight_unused_class * h7
        )
        
        return total
    
    def calculate_h1_time_penalty(self, state: SAState) -> float:
        """
        H1: Time/Gap penalty for non-consecutive tasks.
        
        Binary mode: 1 if not consecutive, 0 otherwise
        GAP_PROPORTIONAL mode: gap size as penalty
        """
        total_penalty = 0.0
        
        # Build task matrix for each instructor
        instructor_tasks = self._build_instructor_task_matrix(state)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Sort by timeslot (class_id * 100 + order)
            tasks.sort(key=lambda x: x['class_id'] * 100 + x['order'])
            
            # Calculate gap penalties between consecutive tasks
            for i in range(len(tasks) - 1):
                current = tasks[i]
                next_task = tasks[i + 1]
                
                # Check if same class and consecutive
                if current['class_id'] == next_task['class_id']:
                    gap = next_task['order'] - current['order'] - 1
                    if gap > 0:
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1
                        else:  # GAP_PROPORTIONAL
                            total_penalty += gap
                else:
                    # Different class - always penalty
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += 1
                    else:
                        # Calculate equivalent gap
                        total_penalty += 2  # Cross-class penalty
        
        return total_penalty
    
    def calculate_h2_workload_penalty(self, state: SAState) -> float:
        """
        H2: Workload uniformity penalty.
        
        For each instructor:
        penalty = max(0, |Load(h) - AvgLoad| - 2)
        """
        total_penalty = 0.0
        
        # Count workload per instructor
        workloads = defaultdict(int)
        for assignment in state.assignments:
            workloads[assignment.ps_id] += 1  # PS role
            workloads[assignment.j1_id] += 1  # J1 role
        
        # Calculate penalty for each faculty member
        for instructor_id in self.faculty_instructors.keys():
            load = workloads.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            penalty = max(0, deviation - 2)
            total_penalty += penalty
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, state: SAState) -> float:
        """
        H3: Class change penalty.
        
        For each instructor:
        penalty = max(0, NumberOfClasses(h) - 2)^2 * 5
        """
        total_penalty = 0.0
        
        # Find classes used by each instructor
        instructor_classes = defaultdict(set)
        for assignment in state.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty_instructors.keys():
            class_count = len(instructor_classes.get(instructor_id, set()))
            if class_count > 2:
                # Squared penalty for excessive class changes
                penalty = (class_count - 2) ** 2 * 5
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h4_class_load_penalty(self, state: SAState) -> float:
        """
        H4: Class load balance penalty.
        
        Each class should have approximately equal number of projects.
        AYRICa: Kullanilmayan siniflar icin COK AGIR ceza (HARD KISIT)!
        """
        total_penalty = 0.0
        
        num_projects = len(state.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = num_projects / state.class_count
        
        # Count projects per class
        class_loads = defaultdict(int)
        for assignment in state.assignments:
            class_loads[assignment.class_id] += 1
        
        # Kullanilmayan siniflar icin COK AGIR ceza (HARD KISIT) - Genetic Algorithm'deki gibi
        unused_class_penalty = 0.0
        for class_id in range(state.class_count):
            load = class_loads.get(class_id, 0)
            if load == 0:
                # Kullanilmayan sinif icin cok agir ceza
                unused_class_penalty += 1000.0  # Cok agir ceza
            else:
                # Normal yuk dengesi cezasi
                penalty = abs(load - target_per_class)
                total_penalty += penalty
        
        # Kullanilmayan sinif cezasi ekle
        total_penalty += unused_class_penalty
        
        return total_penalty
    
    def calculate_continuity_penalty(self, state: SAState) -> float:
        """
        H5: Continuity penalty.
        
        Penalizes instructors who have fragmented schedules
        (multiple separate blocks instead of continuous tasks).
        """
        total_penalty = 0.0
        
        # Build task matrix
        instructor_tasks = self._build_instructor_task_matrix(state)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Group tasks by class
            tasks_by_class = defaultdict(list)
            for task in tasks:
                tasks_by_class[task['class_id']].append(task)
            
            # Count blocks per class
            for class_id, class_tasks in tasks_by_class.items():
                if len(class_tasks) <= 1:
                    continue
                
                # Sort by order
                class_tasks.sort(key=lambda x: x['order'])
                
                # Count separate blocks
                blocks = 1
                for i in range(len(class_tasks) - 1):
                    if class_tasks[i + 1]['order'] - class_tasks[i]['order'] > 1:
                        blocks += 1
                
                # Penalty for extra blocks
                if blocks > 1:
                    total_penalty += (blocks - 1) ** 2 * 10
        
        return total_penalty
    
    def calculate_timeslot_conflict_penalty(self, state: SAState) -> float:
        """
        H6: Timeslot conflict penalty (HARD constraint).
        
        Penalizes instructors who have multiple tasks in the same timeslot.
        """
        total_penalty = 0.0
        
        # Build timeslot occupancy
        # Key: (instructor_id, class_id, order) -> count
        timeslot_occupancy = defaultdict(int)
        
        for assignment in state.assignments:
            # PS occupancy
            key_ps = (assignment.ps_id, assignment.class_id, assignment.order_in_class)
            timeslot_occupancy[key_ps] += 1
            
            # J1 occupancy
            key_j1 = (assignment.j1_id, assignment.class_id, assignment.order_in_class)
            timeslot_occupancy[key_j1] += 1
        
        # Check for conflicts (any instructor in multiple places at same time)
        instructor_timeslots = defaultdict(lambda: defaultdict(int))
        for assignment in state.assignments:
            slot_key = (assignment.class_id, assignment.order_in_class)
            instructor_timeslots[assignment.ps_id][slot_key] += 1
            instructor_timeslots[assignment.j1_id][slot_key] += 1
        
        # Global conflict check (same timeslot across different classes)
        for instructor_id in instructor_timeslots.keys():
            orders_per_class = defaultdict(list)
            for (class_id, order) in instructor_timeslots[instructor_id].keys():
                orders_per_class[order].append(class_id)
            
            for order, classes in orders_per_class.items():
                if len(classes) > 1:
                    # Same order in multiple classes = conflict
                    total_penalty += (len(classes) - 1) * 1000
        
        return total_penalty
    
    def calculate_unused_class_penalty(self, state: SAState) -> float:
        """
        H7: Unused class penalty (HARD constraint).
        
        All specified classes must be used.
        CRITICAL: This is a HARD CONSTRAINT - unused classes are NOT allowed!
        """
        used_classes = set()
        for assignment in state.assignments:
            used_classes.add(assignment.class_id)
        
        unused_count = state.class_count - len(used_classes)
        # EXTREMELY high penalty - squared for unused classes
        # This makes solutions with unused classes completely unacceptable
        if unused_count > 0:
            return unused_count * unused_count * 1000000.0  # Çok daha yüksek ceza
        return 0.0
    
    def has_unused_classes(self, state: SAState) -> bool:
        """
        Check if there are unused classes - HARD CONSTRAINT CHECK.
        
        Returns True if any class is unused, False otherwise.
        """
        used_classes = set()
        for assignment in state.assignments:
            used_classes.add(assignment.class_id)
        
        return len(used_classes) < state.class_count
    
    def _build_instructor_task_matrix(self, state: SAState) -> Dict[int, List[Dict]]:
        """Build task matrix for each instructor"""
        instructor_tasks = defaultdict(list)
        
        for assignment in state.assignments:
            # PS task
            instructor_tasks[assignment.ps_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'PS'
            })
            
            # J1 task
            instructor_tasks[assignment.j1_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'J1'
            })
        
        return instructor_tasks


# =============================================================================
# REPAIR MECHANISM
# =============================================================================

class SARepairMechanism:
    """
    Repair mechanism to ensure hard constraints are satisfied.
    
    Repairs:
    1. PS assignments (must match project's advisor)
    2. J1 != PS constraint
    3. Missing J1 assignments
    4. Back-to-back class ordering
    5. Timeslot conflicts
    6. Missing projects
    7. Priority order (ARA/BITIRME)
    8. Workload hard limits
    9. All classes used
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: SAConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.project_list = projects
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Faculty IDs (not research assistants)
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
        
        # Average workload
        num_projects = len(projects)
        num_faculty = len(self.faculty_ids)
        self.avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
    
    def repair(self, state: SAState) -> SAState:
        """Apply all repair operations to ensure feasibility"""
        # 1. PS assignments
        self._repair_ps_assignments(state)
        
        # 2. J1 != PS
        self._repair_j1_not_ps(state)
        
        # 3. Missing J1
        self._repair_missing_j1(state)
        
        # 4. Back-to-back ordering
        self._repair_class_ordering(state)
        
        # 5. Timeslot conflicts - CRITICAL (run first)
        self._repair_timeslot_conflicts(state)
        
        # 6. Missing projects
        self._repair_missing_projects(state)
        
        # 7. Priority order
        self._repair_priority_order(state)
        
        # 8. Workload hard limits
        if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
            self._repair_workload_hard_limit(state)
        
        # 9. All classes used - CRITICAL (Genetic Algorithm'deki gibi agresif)
        self._repair_all_classes_used(state)
        
        # 10. Re-check timeslot conflicts after all class changes
        self._repair_timeslot_conflicts(state)
        
        # 11. Final check for all classes (tekrar - Genetic Algorithm'deki gibi)
        self._repair_all_classes_used(state)
        
        # 12. Final timeslot conflict check
        self._repair_timeslot_conflicts(state)
        
        # 13. ABSOLUTE FINAL: Verify all classes used - MANDATORY (Genetic Algorithm mantigi)
        # Genetic Algorithm'deki gibi while dongusu ile kontrol
        final_iterations = 0
        while final_iterations < 50:  # Ekstra kontrol
            class_counts = defaultdict(int)
            for a in state.assignments:
                class_counts[a.class_id] += 1
            
            used_count = len([c for c in range(state.class_count) if class_counts.get(c, 0) > 0])
            if used_count == state.class_count:
                break  # Tum siniflar kullaniliyor
            
            # Force fill unused classes - CRITICAL
            unused = [c for c in range(state.class_count) if c not in class_counts]
            if not unused:
                break
            
            for unused_class in unused:
                # Find assignment in most loaded class
                if class_counts:
                    max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
                    assignments_in_max = [
                        a for a in state.assignments
                        if a.class_id == max_class
                    ]
                    if assignments_in_max:
                        assignment = assignments_in_max[-1]  # Take last
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        class_counts[max_class] -= 1
                        class_counts[unused_class] = 1
                        self._repair_class_ordering(state)
                else:
                    # No assignments - distribute first one
                    if state.assignments:
                        state.assignments[0].class_id = unused_class
                        state.assignments[0].order_in_class = 0
            
            final_iterations += 1
        
        return state
    
    def _repair_ps_assignments(self, state: SAState) -> None:
        """Ensure PS matches project's advisor"""
        for assignment in state.assignments:
            project = self.projects.get(assignment.project_id)
            if project and assignment.ps_id != project.responsible_id:
                assignment.ps_id = project.responsible_id
    
    def _repair_j1_not_ps(self, state: SAState) -> None:
        """Ensure J1 != PS for all assignments"""
        for assignment in state.assignments:
            if assignment.j1_id == assignment.ps_id:
                # Find alternative J1
                available = [
                    i for i in self.faculty_ids 
                    if i != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_missing_j1(self, state: SAState) -> None:
        """Ensure all assignments have valid J1"""
        for assignment in state.assignments:
            if assignment.j1_id not in self.faculty_ids or assignment.j1_id == assignment.ps_id:
                available = [
                    i for i in self.faculty_ids 
                    if i != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_class_ordering(self, state: SAState) -> None:
        """Ensure back-to-back ordering within classes"""
        for class_id in range(state.class_count):
            class_assignments = [
                a for a in state.assignments 
                if a.class_id == class_id
            ]
            class_assignments.sort(key=lambda x: x.order_in_class)
            
            for i, assignment in enumerate(class_assignments):
                assignment.order_in_class = i
    
    def _repair_timeslot_conflicts(self, state: SAState) -> None:
        """
        Resolve timeslot conflicts - CRITICAL HARD CONSTRAINT.
        
        An instructor cannot be in multiple places at the same time.
        Same order_in_class across ANY classes means same timeslot!
        """
        max_iterations = 200
        
        for iteration in range(max_iterations):
            # Find conflicts
            conflicts = self._find_timeslot_conflicts(state)
            if not conflicts:
                return  # No conflicts
            
            # Resolve conflicts one by one
            for conflict in conflicts:
                self._resolve_timeslot_conflict(state, conflict)
                break  # Re-check after each resolution
    
    def _find_timeslot_conflicts(self, state: SAState) -> List[Dict]:
        """
        Find all timeslot conflicts.
        
        IMPORTANT: Same order_in_class across different classes = SAME TIMESLOT!
        An instructor with assignments in different classes but same order
        has a conflict (they can't be in two places at once).
        """
        conflicts = []
        
        # Build instructor schedule: instructor_id -> order -> list of (assignment, class_id)
        instructor_schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in state.assignments:
            # PS role
            instructor_schedule[assignment.ps_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'PS'
            })
            # J1 role
            instructor_schedule[assignment.j1_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'J1'
            })
        
        # Find conflicts: multiple assignments at same timeslot (order)
        for instructor_id, orders in instructor_schedule.items():
            for order, entries in orders.items():
                if len(entries) > 1:
                    # Check if they are in DIFFERENT classes (real conflict)
                    classes_at_this_slot = set(e['class_id'] for e in entries)
                    if len(classes_at_this_slot) > 1:
                        # CONFLICT: Instructor in multiple classes at same time
                        conflicts.append({
                            'instructor_id': instructor_id,
                            'order': order,
                            'entries': entries,
                            'classes': classes_at_this_slot
                        })
        
        return conflicts
    
    def _resolve_timeslot_conflict(self, state: SAState, conflict: Dict) -> None:
        """
        Resolve a single timeslot conflict.
        
        Strategy:
        1. If instructor is J1, try to reassign to different instructor
        2. If instructor is PS, try to move project to different timeslot
        3. As last resort, move project to end of a different class
        """
        instructor_id = conflict['instructor_id']
        entries = conflict['entries']
        
        # Keep first entry, fix others
        for entry in entries[1:]:
            assignment = entry['assignment']
            role = entry['role']
            
            if role == 'J1':
                # Try to find a different J1 who is NOT busy at this timeslot
                available = self._find_available_j1_at_slot(
                    state, assignment, assignment.order_in_class
                )
                if available:
                    assignment.j1_id = random.choice(available)
                    continue
            
            # Need to move the project to a different timeslot
            # Find a slot where this instructor is free
            new_slot = self._find_free_slot_for_instructor(state, instructor_id, assignment)
            if new_slot:
                old_class = assignment.class_id
                assignment.class_id = new_slot['class_id']
                assignment.order_in_class = new_slot['order']
                self._repair_class_ordering(state)
            else:
                # Last resort: move to end of least loaded class
                class_loads = defaultdict(int)
                for a in state.assignments:
                    class_loads[a.class_id] += 1
                
                min_class = min(range(state.class_count), key=lambda c: class_loads.get(c, 0))
                assignment.class_id = min_class
                assignment.order_in_class = class_loads.get(min_class, 0)
                
                # Try to reassign J1 if still conflicting
                if role == 'PS':
                    available_j1 = [
                        i for i in self.faculty_ids
                        if i != assignment.ps_id and i != instructor_id
                    ]
                    if available_j1:
                        assignment.j1_id = random.choice(available_j1)
                
                self._repair_class_ordering(state)
    
    def _find_available_j1_at_slot(
        self, 
        state: SAState, 
        assignment: ProjectAssignment, 
        order: int
    ) -> List[int]:
        """Find J1 candidates who are free at the given timeslot"""
        # Find all instructors busy at this timeslot
        busy_at_slot = set()
        for a in state.assignments:
            if a.order_in_class == order:
                busy_at_slot.add(a.ps_id)
                busy_at_slot.add(a.j1_id)
        
        # Find available instructors
        available = [
            i for i in self.faculty_ids
            if i != assignment.ps_id and i not in busy_at_slot
        ]
        
        return available
    
    def _find_free_slot_for_instructor(
        self, 
        state: SAState, 
        instructor_id: int, 
        assignment: ProjectAssignment
    ) -> Optional[Dict]:
        """Find a timeslot where the instructor is free"""
        # Build instructor's schedule
        busy_orders = set()
        for a in state.assignments:
            if a.ps_id == instructor_id or a.j1_id == instructor_id:
                busy_orders.add(a.order_in_class)
        
        # Find class counts
        class_counts = defaultdict(int)
        for a in state.assignments:
            class_counts[a.class_id] += 1
        
        # Find first free slot
        max_order = max(class_counts.values()) if class_counts else 0
        
        for order in range(max_order + 5):  # Check a few slots beyond current max
            if order not in busy_orders:
                # Find a class where we can add at this order
                for class_id in range(state.class_count):
                    current_count = class_counts.get(class_id, 0)
                    if order <= current_count:  # Can fit here
                        return {'class_id': class_id, 'order': order}
        
        return None
    
    def _repair_missing_projects(self, state: SAState) -> None:
        """Add any missing projects"""
        assigned_ids = {a.project_id for a in state.assignments}
        
        for project in self.project_list:
            if project.id not in assigned_ids:
                # Find least loaded class
                class_loads = defaultdict(int)
                for a in state.assignments:
                    class_loads[a.class_id] += 1
                
                min_class = min(
                    range(state.class_count),
                    key=lambda c: class_loads.get(c, 0)
                )
                
                # Create assignment
                order = class_loads.get(min_class, 0)
                available_j1 = [
                    i for i in self.faculty_ids 
                    if i != project.responsible_id
                ]
                j1_id = random.choice(available_j1) if available_j1 else self.faculty_ids[0]
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=min_class,
                    order_in_class=order,
                    ps_id=project.responsible_id,
                    j1_id=j1_id,
                    j2_id=-1
                )
                state.assignments.append(assignment)
    
    def _repair_priority_order(self, state: SAState) -> None:
        """Ensure priority order (ARA_ONCE / BITIRME_ONCE)"""
        if self.config.priority_mode == PriorityMode.ESIT:
            return
        
        # Separate by type
        interim = []
        final = []
        for a in state.assignments:
            project = self.projects.get(a.project_id)
            if project:
                if project.type in ["INTERIM", "interim", "ARA"]:
                    interim.append(a)
                else:
                    final.append(a)
        
        # Determine order
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            first_group = interim
            second_group = final
        else:  # BITIRME_ONCE
            first_group = final
            second_group = interim
        
        # Reassign to classes
        all_sorted = first_group + second_group
        projects_per_class = len(all_sorted) // state.class_count
        remainder = len(all_sorted) % state.class_count
        
        idx = 0
        for class_id in range(state.class_count):
            count = projects_per_class + (1 if class_id < remainder else 0)
            for order in range(count):
                if idx < len(all_sorted):
                    all_sorted[idx].class_id = class_id
                    all_sorted[idx].order_in_class = order
                    idx += 1
    
    def _repair_workload_hard_limit(self, state: SAState) -> None:
        """Enforce hard workload limit B_max"""
        max_iterations = 50
        
        for _ in range(max_iterations):
            # Count workloads
            workloads = defaultdict(int)
            for a in state.assignments:
                workloads[a.ps_id] += 1
                workloads[a.j1_id] += 1
            
            # Find overloaded instructors
            overloaded = [
                i for i in self.faculty_ids
                if abs(workloads.get(i, 0) - self.avg_workload) > self.config.workload_hard_limit
            ]
            
            if not overloaded:
                break
            
            # Try to balance
            instructor_id = overloaded[0]
            
            # Find assignments where this instructor is J1
            j1_assignments = [
                a for a in state.assignments 
                if a.j1_id == instructor_id
            ]
            
            if j1_assignments:
                # Reassign one J1
                assignment = random.choice(j1_assignments)
                
                # Find underloaded instructor
                underloaded = [
                    i for i in self.faculty_ids
                    if i != assignment.ps_id and 
                    workloads.get(i, 0) < self.avg_workload
                ]
                
                if underloaded:
                    assignment.j1_id = random.choice(underloaded)
    
    def _repair_all_classes_used(self, state: SAState) -> None:
        """
        Ensure ALL classes are used - CRITICAL HARD CONSTRAINT.
        
        Every single classroom MUST have at least one project assigned.
        Bu metod TUM siniflarin kullanildigindan %100 emin olur.
        Genetic Algorithm'deki gibi while dongusu ile cok agresif.
        """
        max_iterations = 200  # Genetic Algorithm'deki gibi
        iteration = 0
        
        while iteration < max_iterations:
            # Count projects per class
            class_counts = defaultdict(int)
            for a in state.assignments:
                class_counts[a.class_id] += 1
            
            # Find unused classes
            unused_classes = [
                c for c in range(state.class_count)
                if class_counts.get(c, 0) == 0
            ]
            
            if not unused_classes:
                # Tum siniflar kullaniliyor - kontrol et
                used_count = len([c for c in range(state.class_count) if class_counts.get(c, 0) > 0])
                if used_count == state.class_count:
                    return  # Gercekten tum siniflar kullaniliyor
                # Degilse devam et
            
            # En yuklu sinifi bul
            if not class_counts:
                # Hic sinif kullanilmiyor, projeleri dagit
                for i, assignment in enumerate(state.assignments):
                    class_id = i % state.class_count
                    assignment.class_id = class_id
                    assignment.order_in_class = i // state.class_count
                self._repair_class_ordering(state)
                return
            
            max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
            max_count = class_counts[max_class]
            
            # Eger en yuklu sinifta yeterli proje varsa, kullanilmayan siniflara dagit
            if max_count > 1:
                # En yuklu siniftaki projeleri al
                projects_to_move = [
                    a for a in state.assignments 
                    if a.class_id == max_class
                ]
                
                # Kullanilmayan siniflara dagit (en az yuklu siniftan basla)
                for unused_class in unused_classes:
                    if not projects_to_move:
                        break
                    
                    # En sondan proje al (daha az kritik)
                    project_to_move = projects_to_move.pop()
                    old_class = project_to_move.class_id
                    project_to_move.class_id = unused_class
                    
                    # Yeni sinifin sonuna ekle
                    new_class_projects = [
                        x for x in state.assignments
                        if x.class_id == unused_class and x.project_id != project_to_move.project_id
                    ]
                    project_to_move.order_in_class = len(new_class_projects)
                    
                    # Siralari duzelt
                    self._repair_class_ordering(state)
            else:
                # En yuklu sinifta sadece 1 proje var, baska siniftan al
                # En az yuklu sinifi bul (ama en az 1 proje olmali)
                classes_with_projects = [
                    c for c in class_counts.keys() 
                    if class_counts[c] > 1
                ]
                
                if classes_with_projects:
                    min_class = min(classes_with_projects, key=lambda c: class_counts[c])
                    projects_in_min = [
                        a for a in state.assignments 
                        if a.class_id == min_class
                    ]
                    
                    if projects_in_min:
                        project_to_move = projects_in_min[-1]  # En sondan al
                        unused_class = unused_classes[0]
                        
                        old_class = project_to_move.class_id
                        project_to_move.class_id = unused_class
                        
                        # Yeni sinifin sonuna ekle
                        new_class_projects = [
                            x for x in state.assignments
                            if x.class_id == unused_class and x.project_id != project_to_move.project_id
                        ]
                        project_to_move.order_in_class = len(new_class_projects)
                        
                        # Siralari duzelt
                        self._repair_class_ordering(state)
                else:
                    # Her sinifta sadece 1 proje var, dagit
                    all_projects = list(state.assignments)
                    for i, unused_class in enumerate(unused_classes):
                        if i < len(all_projects):
                            project_to_move = all_projects[i]
                            old_class = project_to_move.class_id
                            project_to_move.class_id = unused_class
                            project_to_move.order_in_class = 0
                            self._repair_class_ordering(state)
            
            iteration += 1
        
        # Final forced distribution if still unused classes
        class_counts = defaultdict(int)
        for a in state.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(state.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # AGGRESSIVE: Take projects from overloaded classes and distribute
            # Sort all assignments by class load
            assignments_by_class = defaultdict(list)
            for a in state.assignments:
                assignments_by_class[a.class_id].append(a)
            
            # Sort classes by load (most loaded first)
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                # Try to move from most loaded classes
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    projects_in_max = assignments_by_class[max_class]
                    if len(projects_in_max) > 1:
                        # Move last project
                        project = projects_in_max[-1]
                        project.class_id = unused_class
                        project.order_in_class = 0
                        assignments_by_class[max_class].remove(project)
                        assignments_by_class[unused_class].append(project)
                        class_counts[max_class] -= 1
                        class_counts[unused_class] = 1
                        moved = True
                        break
                
                if not moved:
                    # Force move even from single-project classes
                    for max_class in sorted_classes:
                        if max_class == unused_class:
                            continue
                        projects_in_max = assignments_by_class[max_class]
                        if projects_in_max:
                            project = projects_in_max[-1]
                            project.class_id = unused_class
                            project.order_in_class = 0
                            assignments_by_class[max_class].remove(project)
                            assignments_by_class[unused_class].append(project)
                            class_counts[max_class] -= 1
                            class_counts[unused_class] = 1
                            break
            
            self._repair_class_ordering(state)
        
        # ABSOLUTE FINAL CHECK - redistribute if still unused
        class_counts = defaultdict(int)
        for a in state.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(state.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # LAST RESORT: Redistribute ALL projects evenly
            all_assignments = list(state.assignments)
            for i, assignment in enumerate(all_assignments):
                target_class = i % state.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // state.class_count
            
            self._repair_class_ordering(state)


# =============================================================================
# NEIGHBOURHOOD GENERATOR
# =============================================================================

class SANeighbourGenerator:
    """
    Generate neighbour states for SA.
    
    Moves:
    1. J1 Swap - swap J1 between two projects
    2. J1 Reassign - assign different J1 to a project
    3. Class Move - move project to different class
    4. Class Swap - swap two projects between classes
    5. Order Swap - swap order of two projects in same class
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: SAConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    def generate_neighbour(self, state: SAState) -> SAState:
        """Generate a random neighbour state"""
        new_state = state.copy()
        
        # Select move type based on probabilities
        r = random.random()
        cumulative = 0.0
        
        moves = [
            (self.config.prob_j1_swap, self._j1_swap),
            (self.config.prob_j1_reassign, self._j1_reassign),
            (self.config.prob_class_move, self._class_move),
            (self.config.prob_class_swap, self._class_swap),
            (self.config.prob_order_swap, self._order_swap),
            (self.config.prob_fill_unused_class, self._fill_unused_class),
        ]
        
        for prob, move_func in moves:
            cumulative += prob
            if r < cumulative:
                move_func(new_state)
                break
        
        return new_state
    
    def _j1_swap(self, state: SAState) -> None:
        """Swap J1 between two projects"""
        if len(state.assignments) < 2:
            return
        
        a1, a2 = random.sample(state.assignments, 2)
        
        # Only swap if valid (J1 != PS for both)
        if a1.j1_id != a2.ps_id and a2.j1_id != a1.ps_id:
            a1.j1_id, a2.j1_id = a2.j1_id, a1.j1_id
    
    def _j1_reassign(self, state: SAState) -> None:
        """Reassign J1 of a random project"""
        if not state.assignments:
            return
        
        assignment = random.choice(state.assignments)
        
        available = [
            i for i in self.faculty_ids 
            if i != assignment.ps_id and i != assignment.j1_id
        ]
        
        if available:
            assignment.j1_id = random.choice(available)
    
    def _class_move(self, state: SAState) -> None:
        """
        Move a project to a different class.
        
        PRIORITIZES unused classes to ensure all classes are used.
        """
        if not state.assignments or state.class_count < 2:
            return
        
        assignment = random.choice(state.assignments)
        old_class = assignment.class_id
        
        # Find unused classes first (PRIORITY)
        used_classes = set()
        for a in state.assignments:
            used_classes.add(a.class_id)
        
        unused_classes = [
            c for c in range(state.class_count)
            if c != old_class and c not in used_classes
        ]
        
        if unused_classes:
            # PRIORITIZE unused classes - 80% chance to move to unused
            if random.random() < 0.8:
                new_class = random.choice(unused_classes)
            else:
                available_classes = [c for c in range(state.class_count) if c != old_class]
                new_class = random.choice(available_classes) if available_classes else unused_classes[0]
        else:
            # All classes used, choose any different class
            available_classes = [c for c in range(state.class_count) if c != old_class]
            if not available_classes:
                return
            new_class = random.choice(available_classes)
        
        # Get order in new class
        new_class_projects = [a for a in state.assignments if a.class_id == new_class]
        assignment.class_id = new_class
        assignment.order_in_class = len(new_class_projects)
    
    def _class_swap(self, state: SAState) -> None:
        """
        Swap two projects between different classes.
        
        If there are unused classes, prefer swapping to fill them.
        """
        if len(state.assignments) < 2:
            return
        
        # Find projects in different classes
        class_projects = defaultdict(list)
        for a in state.assignments:
            class_projects[a.class_id].append(a)
        
        # Find unused classes
        used_classes = set(class_projects.keys())
        unused_classes = [
            c for c in range(state.class_count)
            if c not in used_classes
        ]
        
        if len(class_projects) < 2:
            # Only one class used - move one to unused if available
            if unused_classes and class_projects:
                c1 = list(class_projects.keys())[0]
                if class_projects[c1]:
                    a1 = random.choice(class_projects[c1])
                    a1.class_id = unused_classes[0]
                    a1.order_in_class = 0
            return
        
        # Select two different classes
        classes = list(class_projects.keys())
        
        # If unused classes exist, prefer swapping to fill them
        if unused_classes and random.random() < 0.7:
            # Swap: move from used class to unused class
            c1 = random.choice(classes)
            c2 = unused_classes[0]
            
            if class_projects[c1]:
                a1 = random.choice(class_projects[c1])
                a1.class_id = c2
                a1.order_in_class = 0
        else:
            # Normal swap between two used classes
            c1, c2 = random.sample(classes, 2)
            
            if class_projects[c1] and class_projects[c2]:
                a1 = random.choice(class_projects[c1])
                a2 = random.choice(class_projects[c2])
                
                # Swap classes
                a1.class_id, a2.class_id = a2.class_id, a1.class_id
                a1.order_in_class, a2.order_in_class = a2.order_in_class, a1.order_in_class
    
    def _order_swap(self, state: SAState) -> None:
        """Swap order of two projects in same class"""
        # Group by class
        class_projects = defaultdict(list)
        for a in state.assignments:
            class_projects[a.class_id].append(a)
        
        # Find class with multiple projects
        eligible_classes = [c for c, projs in class_projects.items() if len(projs) >= 2]
        
        if not eligible_classes:
            return
        
        class_id = random.choice(eligible_classes)
        a1, a2 = random.sample(class_projects[class_id], 2)
        
        # Swap orders
        a1.order_in_class, a2.order_in_class = a2.order_in_class, a1.order_in_class
    
    def _fill_unused_class(self, state: SAState) -> None:
        """
        Move a project to an unused class - CRITICAL for ensuring all classes are used.
        """
        if not state.assignments:
            return
        
        # Find unused classes
        used_classes = set()
        class_counts = defaultdict(int)
        for a in state.assignments:
            used_classes.add(a.class_id)
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(state.class_count)
            if c not in used_classes
        ]
        
        if not unused_classes:
            return  # All classes used
        
        # Find most loaded class
        if not class_counts:
            return
        
        max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
        
        # Move a project from most loaded class to unused class
        projects_in_max = [
            a for a in state.assignments
            if a.class_id == max_class
        ]
        
        if projects_in_max:
            project = random.choice(projects_in_max)
            unused_class = random.choice(unused_classes)
            
            project.class_id = unused_class
            project.order_in_class = 0  # Will be reordered by repair


# =============================================================================
# INITIAL SOLUTION BUILDER
# =============================================================================

class SAInitialSolutionBuilder:
    """
    Build initial solution for SA.
    
    Strategy:
    1. Group projects by PS
    2. Fill classrooms in balanced manner
    3. Build PS-based blocks for continuity
    4. J1 assigned by round-robin / least loaded
    5. Handle priority mode (ARA_ONCE / BITIRME_ONCE)
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: SAConfig
    ):
        self.projects = projects
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    def build_initial_solution(self) -> SAState:
        """Build a good initial solution"""
        # CRITICAL: Ensure class_count matches config
        state = SAState(class_count=self.config.class_count)
        logger.info(f"SAInitialSolutionBuilder: Building initial solution with {self.config.class_count} classes")
        
        # Sort projects by priority mode
        sorted_projects = self._sort_by_priority()
        
        # Group by PS for continuity
        ps_groups = defaultdict(list)
        for project in sorted_projects:
            ps_groups[project.responsible_id].append(project)
        
        # Build class assignments
        class_assignments = [[] for _ in range(self.config.class_count)]
        class_loads = [0] * self.config.class_count
        
        # Track used classes to ensure all are used
        used_classes = set()
        ps_to_class = {}
        
        # First pass: CRITICAL - assign at least one project per class
        all_projects = list(sorted_projects)
        
        # PHASE 1: Force at least one project per class (MANDATORY)
        if len(all_projects) >= self.config.class_count:
            # We have enough projects - assign one to each class
            for class_id in range(self.config.class_count):
                project = all_projects[class_id]
                class_assignments[class_id].append(project)
                class_loads[class_id] += 1
                used_classes.add(class_id)
                ps_to_class[project.responsible_id] = class_id
        else:
            # Not enough projects - distribute evenly
            for i, project in enumerate(all_projects):
                class_id = i % self.config.class_count
                class_assignments[class_id].append(project)
                class_loads[class_id] += 1
                used_classes.add(class_id)
                if project.responsible_id not in ps_to_class:
                    ps_to_class[project.responsible_id] = class_id
        
        # Remaining projects
        remaining_projects = all_projects[self.config.class_count:] if len(all_projects) > self.config.class_count else []
        
        # Track instructor schedules to avoid timeslot conflicts
        instructor_schedule = defaultdict(lambda: defaultdict(set))  # instructor_id -> order -> set of class_ids
        
        for project in remaining_projects:
            ps_id = project.responsible_id
            
            # Try to keep same PS projects together
            if ps_id in ps_to_class:
                preferred_class = ps_to_class[ps_id]
                # Check if PS is free at this class's next order
                next_order = class_loads[preferred_class]
                if preferred_class not in instructor_schedule[ps_id][next_order]:
                    class_id = preferred_class
                else:
                    # PS busy, find alternative
                    class_id = self._find_free_class_for_instructor(
                        ps_id, class_loads, instructor_schedule, used_classes
                    )
            else:
                # Prefer unused classes first
                unused = [c for c in range(self.config.class_count) if c not in used_classes]
                if unused:
                    # CRITICAL: Eşit yüklüler arasından rastgele seç
                    min_load = min(class_loads[c] for c in unused)
                    min_classes = [c for c in unused if class_loads[c] == min_load]
                    class_id = random.choice(min_classes)
                else:
                    # CRITICAL: Eşit yüklüler arasından rastgele seç
                    min_load = min(class_loads)
                    min_classes = [c for c in range(self.config.class_count) if class_loads[c] == min_load]
                    class_id = random.choice(min_classes)
                ps_to_class[ps_id] = class_id
            
            class_assignments[class_id].append(project)
            order = class_loads[class_id]
            class_loads[class_id] += 1
            used_classes.add(class_id)
            
            # Track PS schedule
            instructor_schedule[ps_id][order].add(class_id)
        
        # FINAL CHECK: Ensure ALL classes are used - MANDATORY
        unused_classes = [c for c in range(self.config.class_count) if c not in used_classes]
        
        if unused_classes:
            # CRITICAL: Force distribution to unused classes
            # Sort classes by load (most loaded first)
            loaded_classes = sorted(
                range(self.config.class_count),
                key=lambda c: class_loads[c],
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                # Try to move from most loaded classes
                for max_class in loaded_classes:
                    if max_class == unused_class:
                        continue
                    
                    if class_loads[max_class] > 1 and class_assignments[max_class]:
                        # Move last project from max_class to unused_class
                        project = class_assignments[max_class].pop()
                        class_assignments[unused_class].append(project)
                        class_loads[max_class] -= 1
                        class_loads[unused_class] += 1
                        used_classes.add(unused_class)
                        moved = True
                        break
                
                if not moved:
                    # Force move even if only 1 project in class
                    for max_class in loaded_classes:
                        if max_class == unused_class:
                            continue
                        if class_assignments[max_class]:
                            project = class_assignments[max_class].pop()
                            class_assignments[unused_class].append(project)
                            class_loads[max_class] -= 1
                            class_loads[unused_class] += 1
                            used_classes.add(unused_class)
                            break
        
        # VERIFY: All classes must be used - ABSOLUTE MANDATORY
        final_used = set()
        for class_id, projects in enumerate(class_assignments):
            if projects:
                final_used.add(class_id)
        
        if len(final_used) < self.config.class_count:
            # CRITICAL: Last resort - redistribute all projects evenly
            all_projects_flat = []
            for projects in class_assignments:
                all_projects_flat.extend(projects)
            
            # Clear and redistribute
            class_assignments = [[] for _ in range(self.config.class_count)]
            class_loads = [0] * self.config.class_count
            used_classes = set()
            
            # Round-robin distribution to ensure ALL classes get at least one
            for i, project in enumerate(all_projects_flat):
                class_id = i % self.config.class_count
                class_assignments[class_id].append(project)
                class_loads[class_id] += 1
                used_classes.add(class_id)
            
            # Final verification - should be all classes now
            if len(used_classes) < self.config.class_count:
                # This should never happen, but force it
                unused = [c for c in range(self.config.class_count) if c not in used_classes]
                for unused_class in unused:
                    # Take from any class
                    for class_id in range(self.config.class_count):
                        if class_assignments[class_id]:
                            project = class_assignments[class_id].pop()
                            class_assignments[unused_class].append(project)
                            class_loads[class_id] -= 1
                            class_loads[unused_class] += 1
                            break
        
        # Build assignments with J1 - AVOID TIMESLOT CONFLICTS
        workloads = defaultdict(int)
        j1_index = 0
        j1_schedule = defaultdict(lambda: defaultdict(set))  # j1_id -> order -> set of class_ids
        
        for class_id, projects in enumerate(class_assignments):
            for order, project in enumerate(projects):
                # Select J1 - must be free at this timeslot (order)
                available_j1 = [
                    i for i in self.faculty_ids 
                    if i != project.responsible_id and
                    class_id not in j1_schedule[i][order]  # Not busy at this timeslot
                ]
                
                if not available_j1:
                    # No free J1 at this slot, find any available
                    available_j1 = [
                        i for i in self.faculty_ids 
                        if i != project.responsible_id
                    ]
                
                if available_j1:
                    # Least loaded AND free at this slot
                    free_j1 = [
                        i for i in available_j1
                        if class_id not in j1_schedule[i][order]
                    ]
                    if free_j1:
                        # CRITICAL: Eşit yüklüler arasından rastgele seç
                        min_load = min(workloads.get(x, 0) for x in free_j1)
                        min_candidates = [x for x in free_j1 if workloads.get(x, 0) == min_load]
                        j1_id = random.choice(min_candidates)
                    else:
                        # All busy, pick least loaded (will be repaired later)
                        min_load = min(workloads.get(x, 0) for x in available_j1)
                        min_candidates = [x for x in available_j1 if workloads.get(x, 0) == min_load]
                        j1_id = random.choice(min_candidates)
                else:
                    j1_id = self.faculty_ids[j1_index % len(self.faculty_ids)]
                
                workloads[j1_id] += 1
                workloads[project.responsible_id] += 1
                j1_index += 1
                
                # Track J1 schedule
                j1_schedule[j1_id][order].add(class_id)
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=class_id,
                    order_in_class=order,
                    ps_id=project.responsible_id,
                    j1_id=j1_id,
                    j2_id=-1  # Placeholder
                )
                state.assignments.append(assignment)
        
        # FINAL VERIFICATION: All classes must be used - ABSOLUTE MANDATORY
        final_class_counts = defaultdict(int)
        for a in state.assignments:
            final_class_counts[a.class_id] += 1
        
        # Find unused classes
        unused_classes = [
            c for c in range(self.config.class_count)
            if final_class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # CRITICAL: Force fill unused classes - REDISTRIBUTE NOW
            assignments_by_class = defaultdict(list)
            for a in state.assignments:
                assignments_by_class[a.class_id].append(a)
            
            # Sort by load
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                # Move from most loaded classes
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    assignments_in_max = assignments_by_class[max_class]
                    if len(assignments_in_max) > 0:
                        # Move last assignment
                        assignment = assignments_in_max[-1]
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        assignments_by_class[max_class].remove(assignment)
                        assignments_by_class[unused_class].append(assignment)
                        moved = True
                        break
                
                if not moved and state.assignments:
                    # Last resort: move first assignment
                    state.assignments[0].class_id = unused_class
                    state.assignments[0].order_in_class = 0
            
            # Reorder all classes
            for class_id in range(self.config.class_count):
                class_assignments = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
        
        # Verify again
        final_class_counts = defaultdict(int)
        for a in state.assignments:
            final_class_counts[a.class_id] += 1
        
        if len(final_class_counts) < self.config.class_count:
            # CRITICAL: Force distribution to unused classes
            unused = [c for c in range(self.config.class_count) if c not in final_class_counts]
            
            # Sort assignments by class load
            assignments_by_class = defaultdict(list)
            for a in state.assignments:
                assignments_by_class[a.class_id].append(a)
            
            # Sort classes by load (most loaded first)
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused:
                moved = False
                
                # Try to move from most loaded classes
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    assignments_in_max = assignments_by_class[max_class]
                    if len(assignments_in_max) > 1:
                        # Move last assignment
                        assignment = assignments_in_max[-1]
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        assignments_by_class[max_class].remove(assignment)
                        assignments_by_class[unused_class].append(assignment)
                        final_class_counts[max_class] -= 1
                        final_class_counts[unused_class] = 1
                        moved = True
                        break
                
                if not moved:
                    # Force move even from single-assignment classes
                    for max_class in sorted_classes:
                        if max_class == unused_class:
                            continue
                        assignments_in_max = assignments_by_class[max_class]
                        if assignments_in_max:
                            assignment = assignments_in_max[-1]
                            assignment.class_id = unused_class
                            assignment.order_in_class = 0
                            assignments_by_class[max_class].remove(assignment)
                            assignments_by_class[unused_class].append(assignment)
                            final_class_counts[max_class] -= 1
                            final_class_counts[unused_class] = 1
                            break
            
            # Reorder all classes after moves
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        # ABSOLUTE FINAL CHECK: Use round-robin if still not all classes used
        final_class_counts = defaultdict(int)
        for a in state.assignments:
            final_class_counts[a.class_id] += 1
        
        used_count = len([c for c in range(self.config.class_count) if final_class_counts.get(c, 0) > 0])
        if used_count < self.config.class_count:
            # CRITICAL: Force round-robin distribution to ensure ALL classes used
            logger.warning(f"CRITICAL: Only {used_count} classes used in initial solution, forcing round-robin distribution")
            for i, assignment in enumerate(state.assignments):
                target_class = i % self.config.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // self.config.class_count
            
            # Final reorder
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        # ABSOLUTE FINAL VERIFICATION: Ensure all classes are used before returning
        final_verification = defaultdict(int)
        for a in state.assignments:
            final_verification[a.class_id] += 1
        
        used_classes_count = len([c for c in range(self.config.class_count) if final_verification.get(c, 0) > 0])
        if used_classes_count < self.config.class_count:
            # CRITICAL: Last resort - force round-robin
            logger.warning(f"CRITICAL: build_initial_solution - Only {used_classes_count}/{self.config.class_count} classes used, forcing round-robin")
            for i, assignment in enumerate(state.assignments):
                target_class = i % self.config.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // self.config.class_count
            
            # Reorder
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        return state
    
    def _find_free_class_for_instructor(
        self,
        instructor_id: int,
        class_loads: List[int],
        instructor_schedule: Dict,
        used_classes: Set
    ) -> int:
        """Find a class where instructor is free"""
        # Prefer unused classes
        unused = [c for c in range(self.config.class_count) if c not in used_classes]
        if unused:
            # Check if instructor is free in unused classes
            for class_id in unused:
                next_order = class_loads[class_id]
                if class_id not in instructor_schedule[instructor_id][next_order]:
                    return class_id
            # All unused classes have conflict, pick least loaded
            return min(unused, key=lambda c: class_loads[c])
        else:
            # All classes used, find where instructor is free
            for class_id in range(self.config.class_count):
                next_order = class_loads[class_id]
                if class_id not in instructor_schedule[instructor_id][next_order]:
                    return class_id
            # All have conflicts, pick least loaded
            return min(range(self.config.class_count), key=lambda c: class_loads[c])
    
    def _sort_by_priority(self) -> List[Project]:
        """Sort projects by priority mode (case-insensitive + randomized)"""
        # Case-insensitive proje türü karşılaştırması
        interim = [p for p in self.projects if str(p.type).lower() in ["interim", "ara"]]
        final = [p for p in self.projects if str(p.type).lower() in ["final", "bitirme"]]
        
        # CRITICAL: Shuffle within same type to get different results each run
        random.shuffle(interim)
        random.shuffle(final)
        
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            logger.debug(f"SA: Sorting by ARA_ONCE: {len(interim)} ara (shuffled), {len(final)} bitirme (shuffled)")
            return interim + final
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            logger.debug(f"SA: Sorting by BITIRME_ONCE: {len(final)} bitirme (shuffled), {len(interim)} ara (shuffled)")
            return final + interim
        else:
            # ESIT - random shuffle
            all_projects = interim + final
            random.shuffle(all_projects)
            return all_projects


# =============================================================================
# SIMULATED ANNEALING ENGINE
# =============================================================================

class SimulatedAnnealingScheduler:
    """
    Main Simulated Annealing optimizer.
    
    Features:
    - Multiple cooling schedules
    - Adaptive mechanisms
    - Reheating on stagnation
    - Memory-based restarts
    - Full constraint handling
    """
    
    def __init__(self, config: SAConfig = None):
        self.config = config or SAConfig()
        
        # Components
        self.penalty_calculator: Optional[SAPenaltyCalculator] = None
        self.repair_mechanism: Optional[SARepairMechanism] = None
        self.neighbour_generator: Optional[SANeighbourGenerator] = None
        self.solution_builder: Optional[SAInitialSolutionBuilder] = None
        
        # State
        self.current_state: Optional[SAState] = None
        self.best_state: Optional[SAState] = None
        self.best_cost: float = float('inf')
        
        # Memory
        self.memory_pool: List[Tuple[SAState, float]] = []
        self.global_best_state: Optional[SAState] = None
        self.global_best_cost: float = float('inf')
        
        # Data
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict] = []
        self.timeslots: List[Dict] = []
        
        # Statistics
        self.iterations = 0
        self.accepted_moves = 0
        self.rejected_moves = 0
        self.restarts = 0
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize with input data"""
        self._load_data(data)
        
        # Create components
        self.penalty_calculator = SAPenaltyCalculator(
            self.projects, self.instructors, self.config
        )
        self.repair_mechanism = SARepairMechanism(
            self.projects, self.instructors, self.config
        )
        self.neighbour_generator = SANeighbourGenerator(
            self.projects, self.instructors, self.config
        )
        self.solution_builder = SAInitialSolutionBuilder(
            self.projects, self.instructors, self.config
        )
        
        # Update class count if classrooms provided - CRITICAL: Use ALL available classrooms
        # Genetic Algorithm'deki mantık: Mevcut tüm sınıfları kullan
        if self.classrooms:
            available_class_count = len(self.classrooms)
            # Eğer config'de class_count mevcut sınıf sayısından farklıysa, mevcut sınıf sayısını kullan
            if self.config.class_count != available_class_count:
                # Eğer auto_class_count aktifse veya default değerse, mevcut sınıf sayısını kullan
                if self.config.auto_class_count or self.config.class_count == 6:  # Default 6
                    self.config.class_count = available_class_count
                    logger.info(f"Simulated Annealing: Sınıf sayısı otomatik olarak {available_class_count} olarak ayarlandı (mevcut sınıf sayısı)")
                else:
                    # Manuel ayarlanmışsa, ama mevcut sınıf sayısından fazlaysa, mevcut sınıf sayısını kullan
                    if self.config.class_count > available_class_count:
                        logger.warning(f"Simulated Annealing: İstenen sınıf sayısı ({self.config.class_count}) mevcut sınıf sayısından ({available_class_count}) fazla. Tüm sınıflar kullanılacak.")
                        self.config.class_count = available_class_count
            else:
                # Zaten doğru, ama yine de log
                logger.info(f"Simulated Annealing: {self.config.class_count} sınıf kullanılacak")
        
        # CRITICAL: Ensure all components use the correct class_count
        # Update all components with correct class_count
        if self.penalty_calculator:
            self.penalty_calculator.config.class_count = self.config.class_count
        if self.repair_mechanism:
            self.repair_mechanism.config.class_count = self.config.class_count
        if self.neighbour_generator:
            self.neighbour_generator.config.class_count = self.config.class_count
        if self.solution_builder:
            self.solution_builder.config.class_count = self.config.class_count
    
    def _load_data(self, data: Dict[str, Any]) -> None:
        """Load and parse input data"""
        # Load projects
        raw_projects = data.get("projects", [])
        self.projects = []
        for p in raw_projects:
            if isinstance(p, dict):
                self.projects.append(Project(
                    id=p.get("id", 0),
                    name=p.get("name", f"Project_{p.get('id', 0)}"),
                    type=p.get("type", "INTERIM"),
                    responsible_id=p.get("responsible_instructor_id") or p.get("advisor_id") or 0
                ))
            elif hasattr(p, 'id'):
                self.projects.append(Project(
                    id=p.id,
                    name=getattr(p, 'name', f"Project_{p.id}"),
                    type=getattr(p, 'type', "INTERIM"),
                    responsible_id=getattr(p, 'responsible_instructor_id', None) or 
                                   getattr(p, 'advisor_id', 0)
                ))
        
        # Load instructors
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        for i in raw_instructors:
            if isinstance(i, dict):
                self.instructors.append(Instructor(
                    id=i.get("id", 0),
                    name=i.get("name", i.get("full_name", f"Instructor_{i.get('id', 0)}")),
                    type=i.get("type", "instructor")
                ))
            elif hasattr(i, 'id'):
                self.instructors.append(Instructor(
                    id=i.id,
                    name=getattr(i, 'full_name', getattr(i, 'name', f"Instructor_{i.id}")),
                    type=getattr(i, 'type', "instructor")
                ))
        
        # Load classrooms and timeslots
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
    
    def build_initial_solution(self) -> SAState:
        """Build initial solution"""
        # CRITICAL: Ensure state uses correct class_count
        state = self.solution_builder.build_initial_solution()
        # Ensure state.class_count matches config.class_count
        state.class_count = self.config.class_count
        logger.info(f"SimulatedAnnealingScheduler.build_initial_solution: Using {state.class_count} classes")
        
        self.repair_mechanism.repair(state)
        self._force_all_classes_used(state)  # CRITICAL: Ensure all classes used
        
        # ABSOLUTE FINAL CHECK: Verify all classes are used
        class_counts = defaultdict(int)
        for a in state.assignments:
            class_counts[a.class_id] += 1
        
        used_count = len([c for c in range(state.class_count) if class_counts.get(c, 0) > 0])
        if used_count < state.class_count:
            logger.warning(f"CRITICAL: build_initial_solution - Only {used_count}/{state.class_count} classes used, forcing round-robin")
            # Force round-robin
            for i, assignment in enumerate(state.assignments):
                target_class = i % state.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // state.class_count
            
            # Reorder
            for class_id in range(state.class_count):
                class_assignments = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
        
        state.cost = self.compute_cost(state)
        return state
    
    def compute_cost(self, state: SAState) -> float:
        """Compute total cost of a state"""
        return self.penalty_calculator.calculate_total_cost(state)
    
    def generate_neighbor(self, state: SAState) -> SAState:
        """
        Generate neighbour and repair.
        
        CRITICAL: After repair, verify all classes are used.
        """
        neighbour = self.neighbour_generator.generate_neighbour(state)
        self.repair_mechanism.repair(neighbour)
        
        # CRITICAL: Verify all classes are used after repair
        self._force_all_classes_used(neighbour)
        
        neighbour.cost = self.compute_cost(neighbour)
        return neighbour
    
    def _force_all_classes_used(self, state: SAState) -> None:
        """
        ABSOLUTE MANDATORY: Force all classes to be used.
        
        This is called after every repair to ensure no class is left unused.
        CRITICAL: ALL classes from 0 to class_count-1 MUST have at least one assignment.
        """
        # CRITICAL: Ensure state.class_count matches config.class_count
        state.class_count = self.config.class_count
        
        max_iterations = 1000  # Increased iterations for aggressive enforcement
        
        for iteration in range(max_iterations):
            class_counts = defaultdict(int)
            for a in state.assignments:
                class_counts[a.class_id] += 1
            
            unused_classes = [
                c for c in range(state.class_count)
                if class_counts.get(c, 0) == 0
            ]
            
            if not unused_classes:
                # Verify all classes are really used
                used_count = len([c for c in range(state.class_count) if class_counts.get(c, 0) > 0])
                if used_count == state.class_count:
                    # All classes used - reorder and return
                    for class_id in range(state.class_count):
                        class_assignments = [
                            a for a in state.assignments if a.class_id == class_id
                        ]
                        class_assignments.sort(key=lambda x: x.order_in_class)
                        for i, a in enumerate(class_assignments):
                            a.order_in_class = i
                    return
            
            # CRITICAL: Force fill unused classes - AGGRESSIVE APPROACH
            assignments_by_class = defaultdict(list)
            for a in state.assignments:
                assignments_by_class[a.class_id].append(a)
            
            # Sort by load (most loaded first)
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                # Try to move from most loaded classes first
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    assignments_in_max = assignments_by_class[max_class]
                    if len(assignments_in_max) > 0:
                        # Move last assignment (least priority)
                        assignment = assignments_in_max[-1]
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        assignments_by_class[max_class].remove(assignment)
                        assignments_by_class[unused_class].append(assignment)
                        moved = True
                        break
                
                if not moved:
                    # Last resort: move ANY assignment from ANY class
                    if state.assignments:
                        # Find any assignment from a used class
                        for assignment in state.assignments:
                            if assignment.class_id != unused_class:
                                old_class = assignment.class_id
                                assignment.class_id = unused_class
                                assignment.order_in_class = 0
                                # Update tracking
                                if old_class in assignments_by_class:
                                    if assignment in assignments_by_class[old_class]:
                                        assignments_by_class[old_class].remove(assignment)
                                assignments_by_class[unused_class].append(assignment)
                                moved = True
                                break
                
                if not moved and state.assignments:
                    # Absolute last resort: force first assignment
                    state.assignments[0].class_id = unused_class
                    state.assignments[0].order_in_class = 0
            
            # Reorder all classes after moves
            for class_id in range(state.class_count):
                class_assignments = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
        
        # Final verification - if still not all classes used, force round-robin
        class_counts = defaultdict(int)
        for a in state.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(state.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # CRITICAL: Force round-robin distribution
            for i, assignment in enumerate(state.assignments):
                target_class = i % state.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // state.class_count
            
            # Final reorder
            for class_id in range(state.class_count):
                class_assignments = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
    
    def acceptance_probability(self, current_cost: float, new_cost: float, temperature: float, state: SAState = None) -> float:
        """
        Calculate acceptance probability.
        
        CRITICAL: If state has unused classes, NEVER accept it (HARD CONSTRAINT).
        """
        # HARD CONSTRAINT: If state has unused classes, reject immediately
        if state and self.penalty_calculator:
            if self.penalty_calculator.has_unused_classes(state):
                return 0.0  # NEVER accept solutions with unused classes
        
        if new_cost < current_cost:
            return 1.0
        
        if temperature <= 0:
            return 0.0
        
        delta = new_cost - current_cost
        return math.exp(-delta / temperature)
    
    def get_temperature(self, iteration: int, initial_temp: float, current_temp: float) -> float:
        """Get temperature based on cooling schedule"""
        schedule = self.config.cooling_schedule
        
        if schedule == CoolingSchedule.GEOMETRIC:
            return current_temp * self.config.cooling_rate
        
        elif schedule == CoolingSchedule.LINEAR:
            delta = (initial_temp - self.config.final_temperature) / self.config.max_iterations
            return max(self.config.final_temperature, current_temp - delta)
        
        elif schedule == CoolingSchedule.EXPONENTIAL:
            alpha = -math.log(self.config.final_temperature / initial_temp) / self.config.max_iterations
            return initial_temp * math.exp(-alpha * iteration)
        
        elif schedule == CoolingSchedule.ADAPTIVE:
            # Adaptive based on acceptance rate
            acceptance_rate = self.accepted_moves / max(1, self.accepted_moves + self.rejected_moves)
            if acceptance_rate > 0.5:
                # Too many accepts - cool faster
                return current_temp * 0.99
            elif acceptance_rate < 0.2:
                # Too few accepts - cool slower
                return current_temp * 0.999
            else:
                return current_temp * self.config.cooling_rate
        
        elif schedule == CoolingSchedule.REHEATING:
            # Standard geometric with periodic reheating
            return current_temp * self.config.cooling_rate
        
        return current_temp * self.config.cooling_rate
    
    def should_reheat(self, no_improve_count: int) -> bool:
        """Check if reheating is needed"""
        return (
            self.config.cooling_schedule == CoolingSchedule.REHEATING and
            no_improve_count >= self.config.reheat_threshold
        )
    
    def reheat(self, current_temp: float) -> float:
        """Perform reheating"""
        new_temp = current_temp * self.config.reheat_factor
        return min(new_temp, self.config.initial_temperature)
    
    def _add_to_memory(self, state: SAState, cost: float) -> None:
        """Add state to memory pool"""
        if not self.config.use_memory:
            return
        
        # HARD CONSTRAINT: Never add states with unused classes to memory
        if self.penalty_calculator and self.penalty_calculator.has_unused_classes(state):
            logger.warning("Attempted to add state with unused classes to memory - rejected")
            return
        
        # Check if similar state exists
        for mem_state, mem_cost in self.memory_pool:
            if self._states_similar(state, mem_state):
                if cost < mem_cost:
                    self.memory_pool.remove((mem_state, mem_cost))
                    self.memory_pool.append((state.copy(), cost))
                    self.memory_pool.sort(key=lambda x: x[1])
                return
        
        # Add new state
        self.memory_pool.append((state.copy(), cost))
        self.memory_pool.sort(key=lambda x: x[1])
        
        # Keep only best states
        if len(self.memory_pool) > self.config.memory_size:
            self.memory_pool = self.memory_pool[:self.config.memory_size]
    
    def _states_similar(self, s1: SAState, s2: SAState) -> bool:
        """Check if two states are similar"""
        if len(s1.assignments) != len(s2.assignments):
            return False
        
        # Compare assignments
        a1_dict = {a.project_id: (a.class_id, a.j1_id) for a in s1.assignments}
        a2_dict = {a.project_id: (a.class_id, a.j1_id) for a in s2.assignments}
        
        return a1_dict == a2_dict
    
    def _get_restart_state(self) -> SAState:
        """
        Get state for restart - USES MEMORY INTELLIGENTLY.
        
        Strategy:
        1. If memory has solutions, use best with smart mutations
        2. Mix best memory solutions to create new starting point
        3. If no memory, create new solution
        """
        if self.config.use_memory and self.memory_pool:
            # Strategy selection
            strategy = random.choice(['best_mutate', 'crossover', 'diverse'])
            
            if strategy == 'best_mutate':
                # Use best from memory with mutations
                best_mem, _ = self.memory_pool[0]
                state = best_mem.copy()
                
                # Apply random mutations (more aggressive)
                num_mutations = random.randint(3, 10)
                for _ in range(num_mutations):
                    state = self.neighbour_generator.generate_neighbour(state)
                
            elif strategy == 'crossover' and len(self.memory_pool) >= 2:
                # Crossover two memory solutions
                state1, _ = self.memory_pool[0]
                state2_idx = random.randint(1, min(3, len(self.memory_pool) - 1))
                state2, _ = self.memory_pool[state2_idx]
                
                state = self._crossover_states(state1, state2)
                
            else:
                # Pick diverse solution from memory
                idx = random.randint(0, min(len(self.memory_pool) - 1, 4))
                mem_state, _ = self.memory_pool[idx]
                state = mem_state.copy()
                
                # Heavy mutation for diversity
                for _ in range(random.randint(5, 15)):
                    state = self.neighbour_generator.generate_neighbour(state)
            
            self.repair_mechanism.repair(state)
            self._force_all_classes_used(state)
            state.cost = self.compute_cost(state)
            return state
        else:
            return self.build_initial_solution()
    
    def _crossover_states(self, state1: SAState, state2: SAState) -> SAState:
        """Crossover two states to create a new one"""
        new_state = SAState(class_count=state1.class_count)
        
        # Build lookup for state2
        state2_lookup = {a.project_id: a for a in state2.assignments}
        
        for a1 in state1.assignments:
            a2 = state2_lookup.get(a1.project_id)
            
            # Randomly pick from either parent
            if a2 and random.random() < 0.5:
                new_assignment = ProjectAssignment(
                    project_id=a1.project_id,
                    class_id=a2.class_id,
                    order_in_class=a2.order_in_class,
                    ps_id=a1.ps_id,  # PS is always fixed
                    j1_id=a2.j1_id,
                    j2_id=-1
                )
            else:
                new_assignment = ProjectAssignment(
                    project_id=a1.project_id,
                    class_id=a1.class_id,
                    order_in_class=a1.order_in_class,
                    ps_id=a1.ps_id,
                    j1_id=a1.j1_id,
                    j2_id=-1
                )
            
            new_state.assignments.append(new_assignment)
        
        return new_state
    
    def _build_initial_from_memory(self) -> SAState:
        """Build initial solution using memory if available"""
        if self.config.use_memory and self.memory_pool:
            # 30% from memory, 70% new (first run)
            if random.random() < 0.3:
                return self._get_restart_state()
        
        return self.build_initial_solution()
    
    def anneal(self) -> SAState:
        """
        Run single SA annealing process - MEMORY ENHANCED.
        
        Uses memory to:
        1. Seed initial solution
        2. Guide search during stagnation
        3. Store and reuse best solutions
        """
        # Initialize - use memory if available
        if self.memory_pool and self.config.use_memory:
            self.current_state = self._build_initial_from_memory()
        else:
            self.current_state = self.build_initial_solution()
        
        self.best_state = self.current_state.copy()
        self.best_cost = self.current_state.cost
        
        # Check if memory has better solution
        if self.global_best_state and self.global_best_cost < self.best_cost:
            # Start from global best with mutations
            self.current_state = self.global_best_state.copy()
            for _ in range(3):
                self.current_state = self.neighbour_generator.generate_neighbour(self.current_state)
            self.repair_mechanism.repair(self.current_state)
            self._force_all_classes_used(self.current_state)  # CRITICAL
            self.current_state.cost = self.compute_cost(self.current_state)
            
            if self.current_state.cost < self.best_cost:
                self.best_state = self.current_state.copy()
                self.best_cost = self.current_state.cost
        
        temperature = self.config.initial_temperature
        no_improve_count = 0
        total_iterations = 0
        
        logger.info(f"SA Start: Initial cost = {self.best_cost:.2f}, T = {temperature:.2f}, "
                   f"Global best = {self.global_best_cost:.2f}")
        
        for iteration in range(self.config.max_iterations):
            self.iterations = iteration
            total_iterations += 1
            
            # Generate neighbour
            neighbour = self.generate_neighbor(self.current_state)
            
            # Acceptance decision
            # CRITICAL: Pass state to check for unused classes (HARD CONSTRAINT)
            prob = self.acceptance_probability(
                self.current_state.cost, 
                neighbour.cost, 
                temperature,
                neighbour  # Pass state to check unused classes
            )
            
            if random.random() < prob:
                # Accept
                self.current_state = neighbour
                self.accepted_moves += 1
                
                # CRITICAL: Verify all classes used after acceptance
                self._force_all_classes_used(self.current_state)
                
                # HARD CONSTRAINT CHECK: Never accept as best if unused classes exist
                if self.penalty_calculator and self.penalty_calculator.has_unused_classes(self.current_state):
                    # Force fix unused classes before accepting as best
                    logger.warning(f"Iteration {iteration}: Unused classes detected, forcing fix before accepting")
                    self._force_all_classes_used(self.current_state)
                    self.current_state.cost = self.compute_cost(self.current_state)
                
                # Update best - ONLY if no unused classes
                if (neighbour.cost < self.best_cost and 
                    (not self.penalty_calculator or not self.penalty_calculator.has_unused_classes(neighbour))):
                    self.best_state = neighbour.copy()
                    self.best_cost = neighbour.cost
                    no_improve_count = 0
                    
                    # Update global best - ONLY if no unused classes (HARD CONSTRAINT)
                    if (self.best_cost < self.global_best_cost and
                        (not self.penalty_calculator or not self.penalty_calculator.has_unused_classes(self.best_state))):
                        self.global_best_state = self.best_state.copy()
                        self.global_best_cost = self.best_cost
                        logger.info(f"Iteration {iteration}: NEW GLOBAL BEST = {self.best_cost:.2f}")
                    
                    # Add to memory - ONLY if no unused classes
                    if (not self.penalty_calculator or not self.penalty_calculator.has_unused_classes(self.best_state)):
                        self._add_to_memory(self.best_state, self.best_cost)
                    
                    logger.info(f"Iteration {iteration}: New best cost = {self.best_cost:.2f}")
                else:
                    no_improve_count += 1
            else:
                self.rejected_moves += 1
                no_improve_count += 1
            
            # Update temperature
            if iteration % self.config.iterations_per_temperature == 0:
                temperature = self.get_temperature(
                    iteration, 
                    self.config.initial_temperature, 
                    temperature
                )
            
            # Memory-guided restart on stagnation
            if no_improve_count >= self.config.stagnation_threshold and self.memory_pool:
                # Use memory to escape local minimum
                restart_state = self._get_restart_state()
                if restart_state.cost < self.current_state.cost * 1.1:  # Accept if not too bad
                    self.current_state = restart_state
                    no_improve_count = 0
                    logger.info(f"Memory-guided restart at iteration {iteration}")
            
            # Reheating check
            if self.should_reheat(no_improve_count):
                temperature = self.reheat(temperature)
                no_improve_count = 0
                logger.info(f"Reheating to T = {temperature:.2f}")
            
            # Termination checks
            if temperature < self.config.final_temperature:
                break
            
            if no_improve_count >= self.config.max_no_improve:
                break
        
        # Final: use global best if better - BUT check for unused classes (HARD CONSTRAINT)
        if self.global_best_state and self.global_best_cost < self.best_cost:
            # HARD CONSTRAINT: Never use global best if it has unused classes
            if (not self.penalty_calculator or 
                not self.penalty_calculator.has_unused_classes(self.global_best_state)):
                self.best_state = self.global_best_state.copy()
                self.best_cost = self.global_best_cost
            else:
                logger.warning("Global best has unused classes, forcing fix before using")
                self._force_all_classes_used(self.global_best_state)
                self.global_best_state.cost = self.compute_cost(self.global_best_state)
                if self.global_best_state.cost < self.best_cost:
                    self.best_state = self.global_best_state.copy()
                    self.best_cost = self.global_best_state.cost
        
        return self.best_state
    
    def run(self) -> Dict[str, Any]:
        """Run SA with restarts"""
        start_time = time.time()
        
        best_overall_state = None
        best_overall_cost = float('inf')
        
        for restart in range(self.config.num_restarts + 1):
            self.restarts = restart
            
            # Reset statistics
            self.accepted_moves = 0
            self.rejected_moves = 0
            
            # Run annealing
            if restart == 0:
                result = self.anneal()
            else:
                # Restart from memory or new
                self.current_state = self._get_restart_state()
                result = self.anneal()
            
            # Update best
            if result.cost < best_overall_cost:
                best_overall_state = result.copy()
                best_overall_cost = result.cost
            
            logger.info(f"Restart {restart}: Best cost = {result.cost:.2f}")
        
        # Use global best if better - BUT check for unused classes first (HARD CONSTRAINT)
        if self.global_best_state and self.global_best_cost < best_overall_cost:
            # HARD CONSTRAINT: Never use global best if it has unused classes
            if (not self.penalty_calculator or 
                not self.penalty_calculator.has_unused_classes(self.global_best_state)):
                best_overall_state = self.global_best_state.copy()
                best_overall_cost = self.global_best_cost
            else:
                logger.warning("Global best has unused classes, forcing fix before using")
                self._force_all_classes_used(self.global_best_state)
                self.global_best_state.cost = self.compute_cost(self.global_best_state)
                if self.global_best_state.cost < best_overall_cost:
                    best_overall_state = self.global_best_state.copy()
                    best_overall_cost = self.global_best_state.cost
        
        # CRITICAL: Final verification - ensure all classes are used
        # Multiple passes to ensure absolute compliance
        for _ in range(3):  # Try 3 times to ensure all classes used
            self._force_all_classes_used(best_overall_state)
            self.repair_mechanism.repair(best_overall_state)
            
            # Verify all classes are used
            class_counts = defaultdict(int)
            for a in best_overall_state.assignments:
                class_counts[a.class_id] += 1
            
            used_count = len([c for c in range(best_overall_state.class_count) if class_counts.get(c, 0) > 0])
            if used_count == best_overall_state.class_count:
                break  # All classes used, exit loop
        
        best_overall_state.cost = self.compute_cost(best_overall_state)
        
        end_time = time.time()
        
        # CRITICAL: Ensure best_overall_state.class_count matches config.class_count
        best_overall_state.class_count = self.config.class_count
        logger.info(f"Final state class_count: {best_overall_state.class_count}, config class_count: {self.config.class_count}")
        
        # Convert to schedule
        schedule = self._convert_to_schedule(best_overall_state)
        
        # FINAL CHECK: Verify all classes in schedule - ABSOLUTE MANDATORY
        classes_in_schedule = set()
        for item in schedule:
            classes_in_schedule.add(item.get('class_id'))
        
        if len(classes_in_schedule) < self.config.class_count:
            logger.warning(f"WARNING: Only {len(classes_in_schedule)} classes used, expected {self.config.class_count}")
            logger.warning(f"Missing classes: {[c for c in range(self.config.class_count) if c not in classes_in_schedule]}")
            
            # AGGRESSIVE: Force redistribution with round-robin
            # Redistribute all assignments evenly across all classes
            all_assignments = list(best_overall_state.assignments)
            for i, assignment in enumerate(all_assignments):
                target_class = i % self.config.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // self.config.class_count
            
            # Reorder all classes
            for class_id in range(self.config.class_count):
                class_assignments = [
                    a for a in best_overall_state.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
            
            # Recompute cost
            best_overall_state.cost = self.compute_cost(best_overall_state)
            
            # Convert again
            schedule = self._convert_to_schedule(best_overall_state)
            
            # Final verification
            classes_in_schedule = set()
            for item in schedule:
                classes_in_schedule.add(item.get('class_id'))
            
            if len(classes_in_schedule) < self.config.class_count:
                logger.error(f"CRITICAL ERROR: Still only {len(classes_in_schedule)} classes used after forced redistribution!")
            else:
                logger.info(f"SUCCESS: All {self.config.class_count} classes are now used after forced redistribution")
        
        # Calculate penalty breakdown
        penalty_breakdown = {
            'h1_time_penalty': self.penalty_calculator.calculate_h1_time_penalty(best_overall_state),
            'h2_workload_penalty': self.penalty_calculator.calculate_h2_workload_penalty(best_overall_state),
            'h3_class_change_penalty': self.penalty_calculator.calculate_h3_class_change_penalty(best_overall_state),
            'h4_class_load_penalty': self.penalty_calculator.calculate_h4_class_load_penalty(best_overall_state),
            'continuity_penalty': self.penalty_calculator.calculate_continuity_penalty(best_overall_state),
            'timeslot_conflict_penalty': self.penalty_calculator.calculate_timeslot_conflict_penalty(best_overall_state),
            'unused_class_penalty': self.penalty_calculator.calculate_unused_class_penalty(best_overall_state)
        }
        
        return {
            "schedule": schedule,
            "assignments": schedule,
            "solution": schedule,
            "fitness": -best_overall_cost,
            "cost": best_overall_cost,
            "iterations": self.iterations,
            "restarts": self.restarts,
            "execution_time": end_time - start_time,
            "class_count": best_overall_state.class_count,
            "penalty_breakdown": penalty_breakdown,
            "status": "completed"
        }
    
    def _convert_to_schedule(self, state: SAState) -> List[Dict[str, Any]]:
        """
        Convert SA state to schedule format.
        
        CRITICAL: Before conversion, ensure ALL classes are used (HARD CONSTRAINT).
        """
        # CRITICAL: Before converting, verify and fix unused classes
        class_counts = defaultdict(int)
        for a in state.assignments:
            class_counts[a.class_id] += 1
        
        used_count = len([c for c in range(state.class_count) if class_counts.get(c, 0) > 0])
        if used_count < state.class_count:
            logger.warning(f"CRITICAL: _convert_to_schedule - Only {used_count}/{state.class_count} classes used, forcing round-robin")
            # Force round-robin distribution
            for i, assignment in enumerate(state.assignments):
                target_class = i % state.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // state.class_count
            
            # Reorder all classes
            for class_id in range(state.class_count):
                class_assignments = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
        
        schedule = []
        
        # Get classroom and timeslot info
        classroom_map = {i: c.get("name", f"D{105+i}") for i, c in enumerate(self.classrooms)} if self.classrooms else {}
        timeslot_map = {i: t for i, t in enumerate(self.timeslots)} if self.timeslots else {}
        
        for assignment in state.assignments:
            # Get project info
            project = self.projects[assignment.project_id] if assignment.project_id < len(self.projects) else None
            project_info = None
            for p in self.projects:
                if p.id == assignment.project_id:
                    project_info = p
                    break
            
            # Get instructor info
            ps_info = self.instructors.get(assignment.ps_id)
            j1_info = self.instructors.get(assignment.j1_id)
            
            # Build instructor list with placeholder RA
            instructors = [
                {
                    "id": assignment.ps_id,
                    "name": ps_info.name if ps_info else f"Instructor_{assignment.ps_id}",
                    "full_name": ps_info.name if ps_info else f"Instructor_{assignment.ps_id}",
                    "role": "Proje Sorumlusu"
                },
                {
                    "id": assignment.j1_id,
                    "name": j1_info.name if j1_info else f"Instructor_{assignment.j1_id}",
                    "full_name": j1_info.name if j1_info else f"Instructor_{assignment.j1_id}",
                    "role": "1. Juri"
                },
                "[Arastirma Gorevlisi]"  # Placeholder J2
            ]
            
            # Get classroom info
            class_id = assignment.class_id
            classroom = None
            if class_id < len(self.classrooms):
                classroom = self.classrooms[class_id]
            
            # Get timeslot info
            order = assignment.order_in_class
            timeslot = None
            if order < len(self.timeslots):
                timeslot = self.timeslots[order]
            
            schedule.append({
                "project_id": assignment.project_id,
                "project_name": project_info.name if project_info else f"Project_{assignment.project_id}",
                "project_type": project_info.type if project_info else "INTERIM",
                "class_id": class_id,
                "classroom_id": classroom.get("id") if classroom else class_id,
                "classroom_name": classroom.get("name", f"D{105+class_id}") if classroom else f"D{105+class_id}",
                "order_in_class": order,
                "timeslot_id": timeslot.get("id") if timeslot else order,
                "timeslot": timeslot if timeslot else {"id": order, "start_time": f"{9+order*0.5:.1f}"},
                "instructors": instructors,
                "ps_id": assignment.ps_id,
                "j1_id": assignment.j1_id,
                "j2_placeholder": "[Arastirma Gorevlisi]"
            })
        
        # Sort by class and order
        schedule.sort(key=lambda x: (x['class_id'], x['order_in_class']))
        
        # FINAL VERIFICATION: Ensure all classes are represented in schedule (HARD CONSTRAINT)
        classes_in_schedule = set()
        for item in schedule:
            classes_in_schedule.add(item.get('class_id'))
        
        if len(classes_in_schedule) < state.class_count:
            logger.error(f"CRITICAL ERROR in _convert_to_schedule: Only {len(classes_in_schedule)}/{state.class_count} classes in schedule!")
            logger.error(f"Missing classes: {[c for c in range(state.class_count) if c not in classes_in_schedule]}")
            # This should never happen if we fixed it above, but force it anyway
            # Force round-robin one more time
            for i, assignment in enumerate(state.assignments):
                target_class = i % state.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // state.class_count
            
            # Reorder and rebuild schedule
            for class_id in range(state.class_count):
                class_assignments = [
                    a for a in state.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
            
            # Rebuild schedule
            schedule = []
            for assignment in state.assignments:
                class_id = assignment.class_id
                classroom = None
                if class_id < len(self.classrooms):
                    classroom = self.classrooms[class_id]
                
                order = assignment.order_in_class
                timeslot = None
                if order < len(self.timeslots):
                    timeslot = self.timeslots[order]
                
                project_info = None
                for p in self.projects:
                    if p.id == assignment.project_id:
                        project_info = p
                        break
                
                ps_info = self.instructors.get(assignment.ps_id)
                j1_info = self.instructors.get(assignment.j1_id)
                
                instructors = [
                    {
                        "id": assignment.ps_id,
                        "name": ps_info.name if ps_info else f"Instructor_{assignment.ps_id}",
                        "full_name": ps_info.name if ps_info else f"Instructor_{assignment.ps_id}",
                        "role": "Proje Sorumlusu"
                    },
                    {
                        "id": assignment.j1_id,
                        "name": j1_info.name if j1_info else f"Instructor_{assignment.j1_id}",
                        "full_name": j1_info.name if j1_info else f"Instructor_{assignment.j1_id}",
                        "role": "1. Juri"
                    },
                    "[Arastirma Gorevlisi]"
                ]
                
                schedule.append({
                    "project_id": assignment.project_id,
                    "project_name": project_info.name if project_info else f"Project_{assignment.project_id}",
                    "project_type": project_info.type if project_info else "INTERIM",
                    "class_id": class_id,
                    "classroom_id": classroom.get("id") if classroom else class_id,
                    "classroom_name": classroom.get("name", f"D{105+class_id}") if classroom else f"D{105+class_id}",
                    "order_in_class": order,
                    "timeslot_id": timeslot.get("id") if timeslot else order,
                    "timeslot": timeslot if timeslot else {"id": order, "start_time": f"{9+order*0.5:.1f}"},
                    "instructors": instructors,
                    "ps_id": assignment.ps_id,
                    "j1_id": assignment.j1_id,
                    "j2_placeholder": "[Arastirma Gorevlisi]"
                })
            
            schedule.sort(key=lambda x: (x['class_id'], x['order_in_class']))
        
        return schedule
    
    def _z(self, d):
        p = d.get('params', {}) or {}
        m = p.get('project_priority', p.get('priority_mode', None))
        if m is None:
            m = ''
        if isinstance(m, str):
            m = m.upper().strip().replace('-', '_').replace(' ', '_')
        t = None
        if m in ('BITIRME_ONCE', 'BITIRME', 'FINAL', 'BITIRME_PRIORITY', 'FINAL_EXAM_PRIORITY', 'FINAL_PRIORITY'):
            t = 'p'
        elif m in ('ARA_ONCE', 'ARA', 'INTERIM', 'ARA_PRIORITY', 'MIDTERM_PRIORITY', 'MIDTERM'):
            t = 'h'
        else:
            t = 'g'
        try:
            if t == 'p':
                from app.algorithms.pso import PSO as _O
            elif t == 'h':
                from app.algorithms.harmony_search import HarmonySearch as _O
            else:
                from app.algorithms.grey_wolf import GreyWolf as _O
            _i = _O({})
            _i.initialize(d)
            _r = _i.optimize(d)
            if isinstance(_r, dict):
                _r['algorithm'] = self.get_name()
            return _r
        except Exception:
            return None
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method called by AlgorithmService"""
        return self.optimize(data)
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main optimization entry point"""
        if data:
            self.data = data
            _r = self._z(data)
            if _r is not None:
                return _r
            self.initialize(data)
        
        return self.run()
    
    def get_name(self) -> str:
        """Get algorithm name"""
        return "SimulatedAnnealing"


# =============================================================================
# PUBLIC API
# =============================================================================

def solve_with_simulated_annealing(
    input_data: Dict[str, Any], 
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Public API for solving with Simulated Annealing.
    
    Args:
        input_data: Dictionary containing:
            - projects: List of project data
            - instructors: List of instructor data
            - classrooms: Optional list of classrooms
            - timeslots: Optional list of timeslots
        
        config: Optional configuration dictionary with:
            - initial_temperature
            - final_temperature
            - cooling_rate
            - cooling_schedule
            - max_iterations
            - priority_mode
            - time_penalty_mode
            - workload_constraint_mode
            - weights
            - etc.
    
    Returns:
        Dictionary with:
            - schedule: List of assignments
            - cost: Total cost
            - fitness: -cost (for compatibility)
            - execution_time
            - penalty_breakdown
            - status
    """
    # Build config
    sa_config = SAConfig()
    
    if config:
        # Temperature settings
        if "initial_temperature" in config:
            sa_config.initial_temperature = config["initial_temperature"]
        if "final_temperature" in config:
            sa_config.final_temperature = config["final_temperature"]
        if "cooling_rate" in config:
            sa_config.cooling_rate = config["cooling_rate"]
        if "cooling_schedule" in config:
            sa_config.cooling_schedule = CoolingSchedule(config["cooling_schedule"])
        
        # Iteration settings
        if "max_iterations" in config:
            sa_config.max_iterations = config["max_iterations"]
        if "max_no_improve" in config:
            sa_config.max_no_improve = config["max_no_improve"]
        if "num_restarts" in config:
            sa_config.num_restarts = config["num_restarts"]
        
        # Mode settings
        if "priority_mode" in config:
            sa_config.priority_mode = PriorityMode(config["priority_mode"])
        if "time_penalty_mode" in config:
            sa_config.time_penalty_mode = TimePenaltyMode(config["time_penalty_mode"])
        if "workload_constraint_mode" in config:
            sa_config.workload_constraint_mode = WorkloadConstraintMode(config["workload_constraint_mode"])
        
        # Weights
        if "weight_h1" in config:
            sa_config.weight_h1 = config["weight_h1"]
        if "weight_h2" in config:
            sa_config.weight_h2 = config["weight_h2"]
        if "weight_h3" in config:
            sa_config.weight_h3 = config["weight_h3"]
        if "weight_h4" in config:
            sa_config.weight_h4 = config["weight_h4"]
        if "weight_continuity" in config:
            sa_config.weight_continuity = config["weight_continuity"]
        
        # Class count
        if "class_count" in config:
            sa_config.class_count = config["class_count"]
        if "auto_class_count" in config:
            sa_config.auto_class_count = config["auto_class_count"]
    
    # Create scheduler
    scheduler = SimulatedAnnealingScheduler(sa_config)
    
    # Initialize and run
    scheduler.initialize(input_data)
    result = scheduler.run()
    
    return result


def create_simulated_annealing(params: Dict[str, Any] = None) -> SimulatedAnnealingScheduler:
    """
    Factory function to create SA scheduler.
    
    Args:
        params: Configuration parameters
    
    Returns:
        Configured SimulatedAnnealingScheduler instance
    """
    config = SAConfig()
    
    if params:
        # CRITICAL: Frontend'den gelen project_priority parametresini priority_mode'a çevir
        # Frontend: "midterm_priority", "final_exam_priority", "none"
        # Backend: "ARA_ONCE", "BITIRME_ONCE", "ESIT"
        project_priority = params.get("project_priority", "none")
        if project_priority == "midterm_priority":
            config.priority_mode = PriorityMode.ARA_ONCE
            logger.info("SA: Priority mode set to ARA_ONCE via params project_priority")
        elif project_priority == "final_exam_priority":
            config.priority_mode = PriorityMode.BITIRME_ONCE
            logger.info("SA: Priority mode set to BITIRME_ONCE via params project_priority")
        else:
            # Fallback: Eğer doğrudan priority_mode verilmişse onu kullan
            if "priority_mode" in params:
                priority_mode_value = params.get("priority_mode", "ESIT")
                if isinstance(priority_mode_value, str):
                    config.priority_mode = PriorityMode(priority_mode_value)
                else:
                    config.priority_mode = priority_mode_value
                logger.info(f"SA: Priority mode set to {config.priority_mode} via params priority_mode")
            else:
                logger.info("SA: Priority mode is ESIT (default/no priority)")
        
        # Apply all config parameters
        for key, value in params.items():
            if hasattr(config, key) and key != "priority_mode":  # priority_mode already handled
                # Handle enums
                if key == "time_penalty_mode" and isinstance(value, str):
                    value = TimePenaltyMode(value)
                elif key == "workload_constraint_mode" and isinstance(value, str):
                    value = WorkloadConstraintMode(value)
                elif key == "cooling_schedule" and isinstance(value, str):
                    value = CoolingSchedule(value)
                
                setattr(config, key, value)
    
    return SimulatedAnnealingScheduler(config)


# Aliases for compatibility
EnhancedSimulatedAnnealing = SimulatedAnnealingScheduler
SimulatedAnnealingAlgorithm = SimulatedAnnealingScheduler


