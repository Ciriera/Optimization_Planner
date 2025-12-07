"""
LEXICOGRAPHIC OPTIMIZATION ALGORITHM - Çok Kriterli ve Çok Kısıtlı Akademik Proje
Sınavı/Jüri Planlama ve Atama Sistemi


AMAÇ FONKSİYONU:
    min Z = C₁·H₁(n) + C₂·H₂(n) + C₃·H₃(n)

Burada:
- H₁: Gap/Bekleme Cezası (Zaman bazlı süreklilik)
- H₂: İş Yükü Uniformite Cezası (En önemli - C₂ > C₁ ve C₂ > C₃)
- H₃: Sınıf Değişimi Cezası

SERT KISITLAR (Hard Constraints):
1. Her proje: 1 PS (Proje Sorumlusu) + 1 J1 (Jüri 1) + 1 J2 (Placeholder)
2. J2 = [Araştırma Görevlisi] → Modele dahil değil, sadece görsel
3. Back-to-back scheduling (sınıf içinde boşluk yok)
4. Her timeslot'ta instructor başına max 1 görev
5. J1 ≠ PS (Sorumlu kendi projesine jüri olamaz)
6. Tam z sınıf kullanılmalı
7. Priority mode (ARA_ONCE, BITIRME_ONCE, ESIT)

YUMUŞAK KISITLAR (Soft Constraints):
1. İş yükü ±2 bandında (L_bar ± 2)
2. Sınıf değişimi minimize
3. Zaman boşlukları minimize

KONFİGÜRASYON PARAMETRELERİ:
- priority_mode: ARA_ONCE | BITIRME_ONCE | ESIT
- time_penalty_mode: BINARY | GAP_PROPORTIONAL
- workload_constraint_mode: SOFT_ONLY | SOFT_AND_HARD

Author: Optimization Planner System
Version: 3.0.0 (Rebuilt)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict
import logging
import math
import time
import random

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class PriorityMode(Enum):
    """Project type prioritization mode."""
    ARA_ONCE = "ARA_ONCE"           # All ARA projects before BITIRME
    BITIRME_ONCE = "BITIRME_ONCE"   # All BITIRME projects before ARA
    ESIT = "ESIT"                   # No priority ordering


class TimePenaltyMode(Enum):
    """Time/gap penalty calculation mode."""
    BINARY = "BINARY"                     # 1 if not consecutive, 0 otherwise
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL" # Penalty = number of gap slots


class WorkloadConstraintMode(Enum):
    """Workload constraint mode."""
    SOFT_ONLY = "SOFT_ONLY"           # Only soft penalty, no hard limit
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Soft penalty + hard upper bound


@dataclass
class LexicographicConfig:
    """Configuration for Lexicographic optimizer."""
    
    # Priority mode
    priority_mode: str = "ESIT"
    
    # Penalty modes
    time_penalty_mode: str = "GAP_PROPORTIONAL"
    workload_constraint_mode: str = "SOFT_ONLY"
    
    # Weights for objective function (C2 > C1 and C2 > C3)
    weight_h1: float = 10.0     # C1 - for gap/continuity penalty
    weight_h2: float = 100.0    # C2 - for workload uniformity (most important)
    weight_h3: float = 5.0      # C3 - for class change penalty
    
    # Hard constraint parameters
    workload_hard_limit: int = 4  # B_max for SOFT_AND_HARD mode
    workload_soft_band: int = 2   # ±2 tolerance
    
    # Solver parameters
    max_time_seconds: int = 120
    max_iterations: int = 1000
    population_size: int = 50
    mutation_rate: float = 0.3
    crossover_rate: float = 0.8
    
    # Class count mode
    class_count_mode: str = "auto"  # "auto" or "manual"
    given_z: int = 7                # Used if class_count_mode == "manual"
    
    # Slot parameters
    slot_duration: float = 0.5      # Δ: Slot uzunluğu (saat)
    time_tolerance: float = 0.001   # ε: Zaman karşılaştırma toleransı
    
    # Note: J2 placeholder is ALWAYS "[Arastirma Gorevlisi]" (hardcoded, like CP-SAT)
    # It is NOT a config parameter - it's fixed in extract_schedule() and _convert_schedule_to_output()


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Teacher:
    """Teacher/Instructor data class."""
    id: int
    code: str
    name: str = ""
    is_research_assistant: bool = False


@dataclass
class Project:
    """Project data class."""
    id: int
    ps_id: int  # Project Supervisor ID
    project_type: str  # "ARA" or "BITIRME"
    name: str = ""
    
    @property
    def is_ara(self) -> bool:
        """Check if project is ARA type."""
        return self.project_type.upper() in ("ARA", "INTERIM")
    
    @property
    def is_bitirme(self) -> bool:
        """Check if project is BITIRME type."""
        return self.project_type.upper() in ("BITIRME", "FINAL")


@dataclass
class ScheduleRow:
    """Single row in the output schedule."""
    project_id: int
    class_id: int
    class_name: str
    order_in_class: int
    global_slot: int
    ps_id: int
    j1_id: int
    j2_label: str = "[Arastirma Gorevlisi]"  # Fixed placeholder - NOT in model - NOT in model


@dataclass
class SolutionState:
    """Holds the current solution state for lexicographic optimization."""
    
    # Assignments: project -> (class, slot, j1)
    assignments: Dict[int, Tuple[int, int, int]] = field(default_factory=dict)
    
    # Metadata
    projects: List[Project] = field(default_factory=list)
    teachers: List[Teacher] = field(default_factory=list)
    faculty_ids: List[int] = field(default_factory=list)
    num_classes: int = 0
    num_slots: int = 0
    class_names: List[str] = field(default_factory=list)
    
    # Penalty values
    h1_continuity: float = 0.0
    h2_workload: float = 0.0
    h3_class_change: float = 0.0
    total_cost: float = 0.0
    
    def copy(self) -> 'SolutionState':
        """Create a deep copy of the solution state."""
        return SolutionState(
            assignments=self.assignments.copy(),
            projects=self.projects.copy(),
            teachers=self.teachers.copy(),
            faculty_ids=self.faculty_ids.copy(),
            num_classes=self.num_classes,
            num_slots=self.num_slots,
            class_names=self.class_names.copy(),
            h1_continuity=self.h1_continuity,
            h2_workload=self.h2_workload,
            h3_class_change=self.h3_class_change,
            total_cost=self.total_cost
        )


# =============================================================================
# SOLUTION BUILDING (Greedy Heuristic)
# =============================================================================

def build_initial_solution(
    projects: List[Project],
    teachers: List[Teacher],
    config: LexicographicConfig,
    num_classes: int,
    class_names: Optional[List[str]] = None
) -> SolutionState:
    """
    Build initial solution using greedy heuristic.
    
    Args:
        projects: List of projects to schedule
        teachers: List of teachers (faculty only, no RAs)
        config: Configuration parameters
        num_classes: Number of classes (z)
        class_names: Optional class names
    
    Returns:
        SolutionState with initial assignments
    """
    state = SolutionState()
    
    # Filter out research assistants - they are NOT part of the model
    faculty = [t for t in teachers if not t.is_research_assistant]
    faculty_ids = [t.id for t in faculty]
    
    state.projects = projects
    state.teachers = faculty
    state.faculty_ids = faculty_ids
    state.num_classes = num_classes
    
    # Generate class names if not provided
    if class_names:
        state.class_names = class_names[:num_classes]
    else:
        state.class_names = [f"D{105 + i}" for i in range(num_classes)]
    
    Y = len(projects)  # Number of projects
    X = len(faculty)   # Number of real faculty members
    z = num_classes    # Number of classes
    
    # Calculate max slots per class (safe upper bound)
    T = math.ceil(Y / z) + 5  # Extra buffer for flexibility
    state.num_slots = T
    
    logger.info(f"Building initial solution: {Y} projects, {X} faculty, {z} classes, {T} max slots")
    
    # Note: J2 placeholder is ALWAYS "[Arastirma Gorevlisi]" (hardcoded in extract_schedule() and _convert_schedule_to_output())
    # It is NOT part of the model - only added in output format (like CP-SAT)
    
    # Create PS lookup
    ps_lookup = {p.id: p.ps_id for p in projects}
    
    # Order projects by priority mode
    ordered_projects = _order_projects_by_priority(projects, config)
    
    # Track state
    class_loads = [0] * z  # Projects per class
    instructor_workloads = defaultdict(int)  # Workload per instructor
    instructor_slots = defaultdict(set)  # instructor_id -> set of (class_id, slot)
    
    # Assign projects
    for idx, project in enumerate(ordered_projects):
        # First z projects: round-robin to ensure all classes are used
        if idx < z:
            best_class = idx
        else:
            # After ensuring all classes have at least 1 project, use least loaded
            best_class = min(range(z), key=lambda s: class_loads[s])
        
        slot = class_loads[best_class]
        ps_id = project.ps_id
        
        # Find best J1 (not PS, least loaded, no conflict)
        best_j1 = _find_best_j1(
            ps_id, best_class, slot,
            faculty_ids, instructor_workloads, instructor_slots
        )
        
        # If no J1 found, try alternative classes
        if best_j1 is None:
            for alt_class in range(z):
                if alt_class == best_class:
                    continue
                
                alt_slot = class_loads[alt_class]
                best_j1 = _find_best_j1(
                    ps_id, alt_class, alt_slot,
                    faculty_ids, instructor_workloads, instructor_slots
                )
                
                if best_j1 is not None:
                    best_class = alt_class
                    slot = alt_slot
                    break
        
        # Last resort: pick any instructor that's not PS
        if best_j1 is None:
            for instructor_id in faculty_ids:
                if instructor_id != ps_id:
                    best_j1 = instructor_id
                    break
        
        # Create assignment
        if best_j1 is not None:
            state.assignments[project.id] = (best_class, slot, best_j1)
            
            # Update state
            class_loads[best_class] += 1
            instructor_workloads[ps_id] += 1
            instructor_workloads[best_j1] += 1
            instructor_slots[ps_id].add((best_class, slot))
            instructor_slots[best_j1].add((best_class, slot))
    
    # Renumber slots within each class to ensure back-to-back
    _renumber_slots(state)
    
    # Ensure all classes are used
    _ensure_all_classes_used(state, z)
    
    return state


def _order_projects_by_priority(
    projects: List[Project],
    config: LexicographicConfig
) -> List[Project]:
    """Order projects based on priority mode."""
    
    priority_mode = config.priority_mode
    
    if priority_mode == "ESIT":
        return list(projects)
    
    ara_projects = [p for p in projects if p.is_ara]
    bitirme_projects = [p for p in projects if p.is_bitirme]
    
    if priority_mode == "ARA_ONCE":
        return ara_projects + bitirme_projects
    elif priority_mode == "BITIRME_ONCE":
        return bitirme_projects + ara_projects
    else:
        return list(projects)


def _find_best_j1(
    ps_id: int,
    class_id: int,
    slot: int,
    faculty_ids: List[int],
    instructor_workloads: Dict[int, int],
    instructor_slots: Dict[int, Set[Tuple[int, int]]]
) -> Optional[int]:
    """
    Find best J1 for given class and slot.
    
    Criteria:
    1. J1 ≠ PS
    2. No timeslot conflict
    3. Least loaded preferred
    """
    best_j1 = None
    best_j1_load = float('inf')
    
    for instructor_id in faculty_ids:
        # J1 ≠ PS check
        if instructor_id == ps_id:
            continue
        
        # Timeslot conflict check (J1)
        if (class_id, slot) in instructor_slots[instructor_id]:
            continue
        
        # Timeslot conflict check (PS)
        if (class_id, slot) in instructor_slots[ps_id]:
            continue
        
        # Least loaded preferred
        load = instructor_workloads[instructor_id]
        if load < best_j1_load:
            best_j1 = instructor_id
            best_j1_load = load
    
    return best_j1


def _renumber_slots(state: SolutionState) -> None:
    """Renumber slots within each class for back-to-back scheduling."""
    class_projects = defaultdict(list)
    
    for project_id, (class_id, slot, j1_id) in state.assignments.items():
        class_projects[class_id].append((project_id, slot, j1_id))
    
    for class_id, projects_list in class_projects.items():
        projects_list.sort(key=lambda x: x[1])  # Sort by slot
        for i, (project_id, _, j1_id) in enumerate(projects_list):
            state.assignments[project_id] = (class_id, i, j1_id)


def _ensure_all_classes_used(state: SolutionState, z: int) -> None:
    """Ensure all z classes are used."""
    used_classes = set(class_id for class_id, _, _ in state.assignments.values())
    unused_classes = set(range(z)) - used_classes
    
    if not unused_classes:
        return
    
    logger.warning(f"Unused classes: {unused_classes}")
    
    # Redistribute projects
    class_counts = defaultdict(int)
    for class_id, _, _ in state.assignments.values():
        class_counts[class_id] += 1
    
    assignments_by_class = defaultdict(list)
    for project_id, (class_id, slot, j1_id) in state.assignments.items():
        assignments_by_class[class_id].append((project_id, slot, j1_id))
    
    unused_list = list(unused_classes)
    unused_idx = 0
    
    sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    
    for class_id, count in sorted_classes:
        if unused_idx >= len(unused_list):
            break
        
        if count > 1:
            target_class = unused_list[unused_idx]
            project_to_move = assignments_by_class[class_id][0]
            project_id, _, j1_id = project_to_move
            state.assignments[project_id] = (target_class, 0, j1_id)
            unused_idx += 1
    
    _renumber_slots(state)
    
    # Final check: if still unused, force round-robin
    final_used = set(class_id for class_id, _, _ in state.assignments.values())
    if len(final_used) < z:
        logger.error(f"Still only {len(final_used)}/{z} classes used, forcing round-robin")
        assignments_list = list(state.assignments.items())
        for i, (project_id, (_, slot, j1_id)) in enumerate(assignments_list):
            state.assignments[project_id] = (i % z, slot, j1_id)
        _renumber_slots(state)


# =============================================================================
# PENALTY CALCULATION
# =============================================================================

def calculate_penalties(
    state: SolutionState,
    config: LexicographicConfig
) -> Tuple[float, float, float]:
    """
    Calculate all penalty functions for the solution.
    
    Returns:
        (h1, h2, h3): Penalty values
    """
    h1 = _calculate_h1_continuity(state, config)
    h2 = _calculate_h2_workload(state, config)
    h3 = _calculate_h3_class_change(state)
    
    return h1, h2, h3


def _calculate_h1_continuity(
    state: SolutionState,
    config: LexicographicConfig
) -> float:
    """
    H1: Continuity penalty.
    
    For each instructor, check consecutive tasks within each class.
    Penalty for gaps between tasks.
    """
    total_penalty = 0.0
    
    # Build instructor task matrix
    instructor_tasks = defaultdict(lambda: defaultdict(list))
    
    for project_id, (class_id, slot, j1_id) in state.assignments.items():
        project = next((p for p in state.projects if p.id == project_id), None)
        if not project:
            continue
        
        ps_id = project.ps_id
        
        # PS task
        instructor_tasks[ps_id][class_id].append(slot)
        # J1 task
        instructor_tasks[j1_id][class_id].append(slot)
    
    # Check continuity within each (instructor, class)
    for instructor_id, class_tasks in instructor_tasks.items():
        for class_id, slots in class_tasks.items():
            if len(slots) <= 1:
                continue
            
            slots.sort()
            
            for i in range(len(slots) - 1):
                gap = slots[i + 1] - slots[i] - 1
                
                if gap > 0:
                    if config.time_penalty_mode == "BINARY":
                        total_penalty += 1
                    else:  # GAP_PROPORTIONAL
                        total_penalty += gap
    
    return total_penalty


def _calculate_h2_workload(
    state: SolutionState,
    config: LexicographicConfig
) -> float:
    """
    H2: Workload uniformity penalty.
    
    Load(h) = PS duties + J1 duties
    Penalty(h) = max(0, |Load(h) - AvgLoad| - 2)
    H2 = Sum of Penalty(h)
    """
    total_penalty = 0.0
    
    # Calculate workloads
    workload = defaultdict(int)
    for project_id, (_, _, j1_id) in state.assignments.items():
        project = next((p for p in state.projects if p.id == project_id), None)
        if not project:
            continue
        
        workload[project.ps_id] += 1
        workload[j1_id] += 1
    
    # Calculate average
    Y = len(state.projects)
    X = len(state.faculty_ids)
    avg_workload = (2 * Y) / X if X > 0 else 0
    
    # Calculate penalty for each instructor
    for instructor_id in state.faculty_ids:
        load = workload.get(instructor_id, 0)
        deviation = abs(load - avg_workload)
        
        # Soft penalty: beyond +/-2 band
        penalty = max(0, deviation - config.workload_soft_band)
        total_penalty += penalty
    
    return total_penalty


def _calculate_h3_class_change(state: SolutionState) -> float:
    """
    H3: Class change penalty.
    
    For each instructor, count class changes between consecutive tasks.
    """
    total_penalty = 0.0
    
    # Build instructor task sequence
    instructor_sequences = defaultdict(list)
    
    for project_id, (class_id, slot, j1_id) in state.assignments.items():
        project = next((p for p in state.projects if p.id == project_id), None)
        if not project:
            continue
        
        ps_id = project.ps_id
        
        # Calculate global slot
        global_slot = class_id * state.num_slots + slot
        
        # PS task
        instructor_sequences[ps_id].append((global_slot, class_id))
        # J1 task
        instructor_sequences[j1_id].append((global_slot, class_id))
    
    # Check class changes
    for instructor_id, sequence in instructor_sequences.items():
        if len(sequence) <= 1:
            continue
        
        sequence.sort(key=lambda x: x[0])  # Sort by global slot
        
        for i in range(len(sequence) - 1):
            curr_class = sequence[i][1]
            next_class = sequence[i + 1][1]
            
            if curr_class != next_class:
                total_penalty += 1
    
    return total_penalty


def calculate_total_cost(
    state: SolutionState,
    config: LexicographicConfig
) -> float:
    """
    Calculate total cost: Z = C₁·H₁ + C₂·H₂ + C₃·H₃
    """
    h1, h2, h3 = calculate_penalties(state, config)
    
    total = (
        config.weight_h1 * h1 +
        config.weight_h2 * h2 +
        config.weight_h3 * h3
    )
    
    # Store in state
    state.h1_continuity = h1
    state.h2_workload = h2
    state.h3_class_change = h3
    state.total_cost = total
    
    return total


# =============================================================================
# LOCAL SEARCH OPTIMIZATION
# =============================================================================

def optimize_with_local_search(
    initial_state: SolutionState,
    config: LexicographicConfig,
    max_iterations: int = 1000
) -> SolutionState:
    """
    Optimize solution using local search.
    
    Move operators:
    1. J1 Swap: Swap J1 assignments between two projects
    2. Project Move: Move project to different class
    3. Project Swap: Swap class/slot between two projects
    """
    best_state = initial_state.copy()
    best_cost = calculate_total_cost(best_state, config)
    
    no_improvement_count = 0
    stagnation_limit = min(100, max_iterations // 10)
    
    for iteration in range(max_iterations):
        # Random move selection
        move_type = random.choice(['j1_swap', 'project_move', 'project_swap'])
        
        if move_type == 'j1_swap':
            candidate = _apply_j1_swap(best_state)
        elif move_type == 'project_move':
            candidate = _apply_project_move(best_state, config)
        else:
            candidate = _apply_project_swap(best_state)
        
        if candidate is None:
            continue
        
        # Check feasibility
        if not _is_feasible(candidate, config):
            continue
        
        # Calculate cost
        candidate_cost = calculate_total_cost(candidate, config)
        
        # Accept if improvement
        if candidate_cost < best_cost:
            best_state = candidate
            best_cost = candidate_cost
            no_improvement_count = 0
        else:
            no_improvement_count += 1
        
        # Stagnation check
        if no_improvement_count >= stagnation_limit:
            break
    
    return best_state


def _apply_j1_swap(state: SolutionState) -> Optional[SolutionState]:
    """Swap J1 assignments between two projects."""
    if len(state.assignments) < 2:
        return None
    
    candidate = state.copy()
    
    # Random two projects
    project_ids = list(candidate.assignments.keys())
    if len(project_ids) < 2:
        return None
    
    idx1, idx2 = random.sample(range(len(project_ids)), 2)
    p1_id = project_ids[idx1]
    p2_id = project_ids[idx2]
    
    # Get projects
    p1 = next((p for p in candidate.projects if p.id == p1_id), None)
    p2 = next((p for p in candidate.projects if p.id == p2_id), None)
    
    if not p1 or not p2:
        return None
    
    # Check J1 ≠ PS constraint
    class1, slot1, j1_1 = candidate.assignments[p1_id]
    class2, slot2, j1_2 = candidate.assignments[p2_id]
    
    if j1_2 != p1.ps_id and j1_1 != p2.ps_id:
        candidate.assignments[p1_id] = (class1, slot1, j1_2)
        candidate.assignments[p2_id] = (class2, slot2, j1_1)
        _renumber_slots(candidate)
        return candidate
    
    return None


def _apply_project_move(
    state: SolutionState,
    config: LexicographicConfig
) -> Optional[SolutionState]:
    """Move project to different class."""
    if len(state.assignments) == 0:
        return None
    
    candidate = state.copy()
    
    # Random project
    project_ids = list(candidate.assignments.keys())
    project_id = random.choice(project_ids)
    
    class_id, slot, j1_id = candidate.assignments[project_id]
    
    # Different class
    other_classes = [c for c in range(candidate.num_classes) if c != class_id]
    if not other_classes:
        return None
    
    new_class = random.choice(other_classes)
    
    # Move
    candidate.assignments[project_id] = (new_class, slot, j1_id)
    _renumber_slots(candidate)
    
    return candidate


def _apply_project_swap(state: SolutionState) -> Optional[SolutionState]:
    """Swap class/slot between two projects."""
    if len(state.assignments) < 2:
        return None
    
    candidate = state.copy()
    
    # Random two projects
    project_ids = list(candidate.assignments.keys())
    if len(project_ids) < 2:
        return None
    
    idx1, idx2 = random.sample(range(len(project_ids)), 2)
    p1_id = project_ids[idx1]
    p2_id = project_ids[idx2]
    
    class1, slot1, j1_1 = candidate.assignments[p1_id]
    class2, slot2, j1_2 = candidate.assignments[p2_id]
    
    # Swap
    candidate.assignments[p1_id] = (class2, slot2, j1_1)
    candidate.assignments[p2_id] = (class1, slot1, j1_2)
    
    _renumber_slots(candidate)
    
    return candidate


def _is_feasible(state: SolutionState, config: LexicographicConfig) -> bool:
    """Check if solution is feasible."""
    
    # Check J1 ≠ PS
    for project_id, (class_id, slot, j1_id) in state.assignments.items():
        project = next((p for p in state.projects if p.id == project_id), None)
        if not project:
            return False
        
        if j1_id == project.ps_id:
            return False
    
    # Check timeslot conflicts
    slot_duties = defaultdict(set)
    for project_id, (class_id, slot, j1_id) in state.assignments.items():
        project = next((p for p in state.projects if p.id == project_id), None)
        if not project:
            return False
        
        slot_key = (class_id, slot)
        
        if project.ps_id in slot_duties[slot_key]:
            return False
        if j1_id in slot_duties[slot_key]:
            return False
        
        slot_duties[slot_key].add(project.ps_id)
        slot_duties[slot_key].add(j1_id)
    
    # Check all classes used
    used_classes = set(class_id for class_id, _, _ in state.assignments.values())
    if len(used_classes) < state.num_classes:
        return False
    
    # Check workload hard constraint (if enabled)
    if config.workload_constraint_mode == "SOFT_AND_HARD":
        workload = defaultdict(int)
        for project_id, (_, _, j1_id) in state.assignments.items():
            project = next((p for p in state.projects if p.id == project_id), None)
            if project:
                workload[project.ps_id] += 1
                workload[j1_id] += 1
        
        Y = len(state.projects)
        X = len(state.faculty_ids)
        avg_workload = (2 * Y) / X if X > 0 else 0
        b_max = config.workload_hard_limit
        
        for instructor_id in state.faculty_ids:
            load = workload.get(instructor_id, 0)
            deviation = abs(load - avg_workload)
            if deviation > b_max:
                return False
    
    return True


# =============================================================================
# SOLUTION EXTRACTION
# =============================================================================

def extract_schedule(state: SolutionState) -> List[ScheduleRow]:
    """
    Extract schedule from solution state.
    
    Args:
        state: Solution state
    
    Returns:
        List of ScheduleRow objects
    """
    schedule = []
    
    projects = state.projects
    faculty_ids = state.faculty_ids
    z = state.num_classes
    class_names = state.class_names
    
    # Build PS lookup
    ps_lookup = {p.id: p.ps_id for p in projects}
    
    # Extract assignments
    for project in projects:
        if project.id not in state.assignments:
            logger.warning(f"Project {project.id} not assigned!")
            continue
        
        class_id, slot, j1_id = state.assignments[project.id]
        
        row = ScheduleRow(
            project_id=project.id,
            class_id=class_id,
            class_name=class_names[class_id] if class_id < len(class_names) else f"Class_{class_id}",
            order_in_class=slot,
            global_slot=class_id * state.num_slots + slot,
            ps_id=ps_lookup[project.id],
            j1_id=j1_id,
            j2_label="[Arastirma Gorevlisi]"  # Fixed placeholder - NOT in model
        )
        schedule.append(row)
    
    # Sort by class and order
    schedule.sort(key=lambda r: (r.class_id, r.order_in_class))
    
    return schedule


# =============================================================================
# MAIN SOLVER FUNCTION
# =============================================================================

def solve_with_lexicographic(
    input_data: Dict[str, Any],
    config: Optional[LexicographicConfig] = None
) -> Dict[str, Any]:
    """
    Main entry point for Lexicographic optimizer.
    
    Args:
        input_data: Dictionary containing:
            - projects: List of project dicts with id, ps_id, type
            - teachers: List of teacher dicts with id, code, is_research_assistant
            - classrooms: Optional list of classroom names
        config: Optional LexicographicConfig object
    
    Returns:
        Dictionary with schedule, cost, status, and metadata
    """
    if config is None:
        config = LexicographicConfig()
    
    # Parse input data
    projects = _parse_projects(input_data.get("projects", []))
    teachers = _parse_teachers(input_data.get("teachers", input_data.get("instructors", [])))
    classrooms = input_data.get("classrooms", [])
    
    # Filter out research assistants
    faculty = [t for t in teachers if not t.is_research_assistant]
    
    if not projects:
        logger.warning("No projects to schedule")
        return {
            "schedule": [],
            "cost": 0,
            "status": "NO_PROJECTS",
            "class_count": 0
        }
    
    if not faculty:
        logger.warning("No faculty members available")
        return {
            "schedule": [],
            "cost": 0,
            "status": "NO_FACULTY",
            "class_count": 0
        }
    
    # Determine class names
    class_names = None
    if classrooms:
        if isinstance(classrooms[0], dict):
            class_names = [c.get("name", f"D{105 + i}") for i, c in enumerate(classrooms)]
        else:
            class_names = [str(c) for c in classrooms]
    
    # Determine which z values to try
    if config.class_count_mode == "manual":
        z_list = [config.given_z]
    else:
        # Auto mode: try z in {5, 6, 7}
        z_list = [5, 6, 7]
    
    best_solution = None
    best_cost = None
    best_z = None
    
    for z in z_list:
        logger.info(f"Trying z = {z} classes...")
        
        # Build initial solution
        initial_state = build_initial_solution(
            projects=projects,
            teachers=faculty,
            config=config,
            num_classes=z,
            class_names=class_names
        )
        
        initial_cost = calculate_total_cost(initial_state, config)
        logger.info(f"z={z}: Initial cost = {initial_cost:.2f}")
        
        # Optimize with local search
        optimized_state = optimize_with_local_search(
            initial_state,
            config,
            max_iterations=config.max_iterations
        )
        
        final_cost = calculate_total_cost(optimized_state, config)
        logger.info(f"z={z}: Final cost = {final_cost:.2f}")
        
        if best_cost is None or final_cost < best_cost:
            best_cost = final_cost
            best_solution = optimized_state
            best_z = z
    
    if best_solution is None:
        return {
            "schedule": [],
            "cost": float("inf"),
            "status": "INFEASIBLE",
            "class_count": 0
        }
    
    # Convert to output format
    schedule_output = _convert_schedule_to_output(
        extract_schedule(best_solution),
        faculty
    )
    
    return {
        "schedule": schedule_output,
        "assignments": schedule_output,
        "solution": schedule_output,
        "cost": best_cost,
        "fitness": 100 - min(100, best_cost / 10),
        "status": "COMPLETED",
        "class_count": best_z,
        "penalty_breakdown": {
            "h1_continuity": best_solution.h1_continuity,
            "h2_workload": best_solution.h2_workload,
            "h3_class_change": best_solution.h3_class_change,
            "total": best_cost
        }
    }


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def _parse_projects(raw_projects: List[Any]) -> List[Project]:
    """Parse raw project data into Project objects."""
    projects = []
    
    for p in raw_projects:
        if isinstance(p, dict):
            project = Project(
                id=p.get("id", 0),
                ps_id=p.get("ps_id", p.get("responsible_id", p.get("supervisor_id", 0))),
                project_type=p.get("type", p.get("project_type", "ARA")).upper(),
                name=p.get("name", p.get("title", f"Project_{p.get('id', 0)}"))
            )
        elif hasattr(p, "id"):
            project = Project(
                id=p.id,
                ps_id=getattr(p, "ps_id", getattr(p, "responsible_id", getattr(p, "supervisor_id", 0))),
                project_type=getattr(p, "type", getattr(p, "project_type", "ARA")).upper(),
                name=getattr(p, "name", getattr(p, "title", f"Project_{p.id}"))
            )
        else:
            continue
        
        # Normalize project type
        if project.project_type in ("INTERIM", "ARA"):
            project.project_type = "ARA"
        elif project.project_type in ("FINAL", "BITIRME"):
            project.project_type = "BITIRME"
        
        projects.append(project)
    
    return projects


def _parse_teachers(raw_teachers: List[Any]) -> List[Teacher]:
    """Parse raw teacher data into Teacher objects."""
    teachers = []
    
    for t in raw_teachers:
        if isinstance(t, dict):
            is_ra = t.get("is_research_assistant", False)
            if not is_ra:
                # Check type field
                t_type = t.get("type", "instructor")
                is_ra = t_type in ("ra", "research_assistant", "assistant")
            
            teacher = Teacher(
                id=t.get("id", 0),
                code=t.get("code", t.get("name", f"T{t.get('id', 0)}")),
                name=t.get("name", t.get("full_name", "")),
                is_research_assistant=is_ra
            )
        elif hasattr(t, "id"):
            is_ra = getattr(t, "is_research_assistant", False)
            if not is_ra:
                t_type = getattr(t, "type", "instructor")
                is_ra = t_type in ("ra", "research_assistant", "assistant")
            
            teacher = Teacher(
                id=t.id,
                code=getattr(t, "code", getattr(t, "name", f"T{t.id}")),
                name=getattr(t, "name", getattr(t, "full_name", "")),
                is_research_assistant=is_ra
            )
        else:
            continue
        
        teachers.append(teacher)
    
    return teachers


def _convert_schedule_to_output(
    schedule: List[ScheduleRow],
    faculty: List[Teacher]
) -> List[Dict[str, Any]]:
    """Convert schedule to output format for planner."""
    
    # Build teacher lookup
    teacher_lookup = {t.id: t for t in faculty}
    
    output = []
    for row in schedule:
        ps_teacher = teacher_lookup.get(row.ps_id)
        j1_teacher = teacher_lookup.get(row.j1_id)
        
        output_row = {
            "project_id": row.project_id,
            "class_id": row.class_id,
            "class_name": row.class_name,
            "order_in_class": row.order_in_class,
            "global_slot": row.global_slot,
            "ps_id": row.ps_id,
            "j1_id": row.j1_id,
            # J2 is ALWAYS the fixed placeholder - NOT a decision variable
            "j2_label": "[Arastirma Gorevlisi]",
            "instructors": [
                {
                    "id": row.ps_id,
                    "name": ps_teacher.name if ps_teacher else f"Teacher_{row.ps_id}",
                    "role": "PS"
                },
                {
                    "id": row.j1_id,
                    "name": j1_teacher.name if j1_teacher else f"Teacher_{row.j1_id}",
                    "role": "J1"
                },
                # J2 placeholder - purely for frontend display
                "[Arastirma Gorevlisi]"
            ],
            "roles": [
                {
                    "person_id": row.ps_id,
                    "person_name": ps_teacher.name if ps_teacher else f"Teacher_{row.ps_id}",
                    "role": "SORUMLU"
                },
                {
                    "person_id": row.j1_id,
                    "person_name": j1_teacher.name if j1_teacher else f"Teacher_{row.j1_id}",
                    "role": "JURI"
                }
                # J2 placeholder is NOT a jury member - it's just a visual placeholder
                # It appears in instructors list as a string, but NOT in roles list
            ]
        }
        output.append(output_row)
    
    return output


# =============================================================================
# ALGORITHM INTERFACE (for integration with factory)
# =============================================================================

class LexicographicAlgorithm(OptimizationAlgorithm):
    """
    Lexicographic Algorithm wrapper for integration with algorithm factory.
    
    Implements the OptimizationAlgorithm interface.
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize with optional parameters.
        
        Args:
            params: Dictionary of configuration parameters
        """
        super().__init__(params)
        params = params or {}
        self.params = params
        self.config = self._build_config(self.params)
        self.data = None
        self.result = None
    
    def _build_config(self, params: Dict[str, Any]) -> LexicographicConfig:
        """Build LexicographicConfig from parameters dictionary."""
        config_params = {}
        
        # Map common parameter names
        param_mapping = {
            "priority_mode": "priority_mode",
            "time_penalty_mode": "time_penalty_mode",
            "workload_constraint_mode": "workload_constraint_mode",
            "weight_h1": "weight_h1",
            "weight_h2": "weight_h2",
            "weight_h3": "weight_h3",
            "workload_hard_limit": "workload_hard_limit",
            "workload_soft_band": "workload_soft_band",
            "max_time_seconds": "max_time_seconds",
            "max_iterations": "max_iterations",
            "population_size": "population_size",
            "mutation_rate": "mutation_rate",
            "crossover_rate": "crossover_rate",
            "class_count_mode": "class_count_mode",
            "given_z": "given_z",
            "class_count": "given_z",  # Alias
            "slot_duration": "slot_duration",
            "time_tolerance": "time_tolerance",
        }
        
        for param_key, config_key in param_mapping.items():
            if param_key in params:
                config_params[config_key] = params[param_key]
        
        return LexicographicConfig(**config_params)
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Initialize with input data.
        
        KRİTİK: J2 Placeholder Ataması
        ==============================
        Algoritma tek fazlı olduğu için, tüm projeler için J2 placeholder
        ataması ATAMA YAPILMADAN ÖNCE burada belirlenir.
        
        Her proje için:
        - 1 PS (Proje Sorumlusu) - sabit, projeden gelir
        - 1 J1 (Jüri 1) - karar değişkeni, optimizasyon ile belirlenir
        - 1 J2 (Jüri 2) - placeholder [Araştırma Görevlisi], her zaman aynı
        
        J2 placeholder:
        - Her zaman sabit: "[Arastirma Gorevlisi]"
        - Modele dahil değil (iş yükü hesaplarına girmez)
        - Ceza fonksiyonlarına dahil değil
        - Sadece görsel amaçlı (frontend'de gösterilir)
        """
        self.data = data
        
        # Extract config from data if provided
        if "config" in data:
            cfg = data["config"]
            if isinstance(cfg, dict):
                self.config = self._build_config(cfg)
            elif isinstance(cfg, LexicographicConfig):
                self.config = cfg
        
        # Update config with class_count from data if available
        if "class_count" in data and data["class_count"]:
            self.config.class_count_mode = "manual"
            self.config.given_z = data["class_count"]
        elif "classrooms" in data and data["classrooms"]:
            classroom_count = len(data["classrooms"])
            if classroom_count in [5, 6, 7]:
                self.config.class_count_mode = "manual"
                self.config.given_z = classroom_count
        
        # Note: J2 placeholder is ALWAYS "[Arastirma Gorevlisi]" (hardcoded in extract_schedule() and _convert_schedule_to_output())
        # It is NOT part of the model - only added in output format (like CP-SAT)
        # Every project will have: 1 PS + 1 J1 + 1 J2 (placeholder)
        
        logger.info(f"Lexicographic Algorithm initialized:")
        logger.info(f"  Priority Mode: {self.config.priority_mode}")
        logger.info(f"  Time Penalty Mode: {self.config.time_penalty_mode}")
        logger.info(f"  Workload Constraint Mode: {self.config.workload_constraint_mode}")
        logger.info(f"  J2 Placeholder: '[Arastirma Gorevlisi]' (fixed, NOT in model - like CP-SAT)")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run optimization and return result.
        
        Args:
            data: Optional input data (if not provided, uses self.data from initialize)
        """
        if data:
            self.initialize(data)
        
        if self.data is None:
            raise ValueError("Algorithm not initialized. Call initialize() first.")
        
        start_time = time.time()
        
        try:
            self.result = solve_with_lexicographic(self.data, self.config)
            execution_time = time.time() - start_time
            
            # Add execution time
            self.result["execution_time"] = execution_time
            self.result["algorithm"] = "Lexicographic Optimization"
            
            logger.info(f"Lexicographic Algorithm completed in {execution_time:.2f}s")
            logger.info(f"  Cost: {self.result.get('cost', 0):.2f}")
            logger.info(f"  Class Count: {self.result.get('class_count', 0)}")
            
            return self.result
        
        except Exception as e:
            logger.error(f"Lexicographic Algorithm error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "schedule": [],
                "assignments": [],
                "solution": [],
                "cost": float("inf"),
                "status": "ERROR",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "algorithm": "Lexicographic Optimization"
            }
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Evaluate fitness of a solution.
        
        Args:
            solution: Solution dictionary
        
        Returns:
            Fitness value (0-100, higher is better)
        """
        assignments = solution.get("assignments", solution.get("schedule", []))
        
        if not assignments:
            return 0.0
        
        # Create temporary state for evaluation
        projects = _parse_projects(solution.get("projects", []))
        teachers = _parse_teachers(solution.get("teachers", solution.get("instructors", [])))
        
        if not projects or not teachers:
            return 0.0
        
        # Build state from assignments
        state = SolutionState()
        state.projects = projects
        state.teachers = [t for t in teachers if not t.is_research_assistant]
        state.faculty_ids = [t.id for t in state.teachers]
        state.num_classes = solution.get("class_count", 7)
        state.num_slots = 20  # Default
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            class_id = assignment.get("class_id", 0)
            order = assignment.get("order_in_class", 0)
            j1_id = assignment.get("j1_id", assignment.get("instructors", [0, 0])[1] if len(assignment.get("instructors", [])) > 1 else 0)
            
            if project_id:
                state.assignments[project_id] = (class_id, order, j1_id)
        
        # Calculate cost
        total_cost = calculate_total_cost(state, self.config)
        
        # Fitness: 100 - normalized cost
        fitness = 100.0 - min(100.0, total_cost / 10.0)
        
        return max(0.0, fitness)
    
    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get the last optimization result."""
        return self.result
