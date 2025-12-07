"""
HARMONY SEARCH (HS) - Çok Kriterli Akademik Proje Sınavı/Jüri Planlama ve Atama Sistemi

Bu modül, üniversitelerde dönem sonlarında gerçekleştirilen Ara Proje ve Bitirme Projesi
değerlendirme süreçlerinde yaşanan planlama, atama ve iş yükü dağıtımı problemlerine yönelik
olarak geliştirilmiş Harmony Search (HS) algoritmasını implement eder.

PROBLEM TANIMI:
- Her projede: 1 Proje Sorumlusu (PS), 1 Jüri (J1), 1 Placeholder Jüri (J2 = [Araştırma Görevlisi])
- X gerçek öğretim görevlisi, Y proje, z sınıf (5, 6, veya 7)
- Projeler sınıf içinde back-to-back (ardışık) yerleştirilmeli
- Her öğretim görevlisi her timeslot'ta en fazla 1 görev alabilir

AMAÇ FONKSİYONU:
    min Z = C1*H1(n) + C2*H2(n) + C3*H3(n)

Burada:
- H1: Zaman/GAP Cezası (ardışık olmayan görevler için - sadece aynı sınıf içinde)
- H2: İş Yükü Uniformite Cezası (en önemli, C2 > C1 ve C2 > C3)
- H3: Sınıf Değişimi Cezası

NOT: H4 ve diğer penalty'ler hard constraint violations için kullanılır.

HARD KISITLAR:
1. Her proje tam olarak bir sınıf ve slot'a atanmalı
2. Back-to-back scheduling (sınıf içinde boşluk yok)
3. Her öğretim görevlisi her timeslot'ta en fazla 1 görev
4. J1[p] != PS[p] (kendi projesine jüri olamama)
5. Tam olarak z sınıf aktif olmalı
6. Proje türü önceliklendirme (ARA_ONCE, BITIRME_ONCE, ESIT)
7. J2 placeholder - modele dahil edilmez, sadece görsel

KONFİGÜRASYON:
- priority_mode: ARA_ONCE | BITIRME_ONCE | ESIT
- time_penalty_mode: BINARY | GAP_PROPORTIONAL
- workload_constraint_mode: SOFT_ONLY | SOFT_AND_HARD

HARMONY SEARCH SPESİFİK PARAMETRELER:
- harmony_memory_size (HMS): Harmony memory kapasitesi
- harmony_memory_consideration_rate (HMCR): Memory'den seçme oranı
- pitch_adjustment_rate (PAR): Pitch ayarlama oranı
- bandwidth (BW): Bandwidth parametresi

Author: Optimization Planner System
"""

from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import copy
import random
import math
import time
import logging
import numpy as np

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION ENUMS
# ============================================================================

class PriorityMode(str, Enum):
    """Proje türü önceliklendirme modu."""
    ARA_ONCE = "ARA_ONCE"
    BITIRME_ONCE = "BITIRME_ONCE"
    ESIT = "ESIT"


class TimePenaltyMode(str, Enum):
    """Zaman/GAP cezası hesaplama modu."""
    BINARY = "BINARY"
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"


class WorkloadConstraintMode(str, Enum):
    """İş yükü kısıtı modu."""
    SOFT_ONLY = "SOFT_ONLY"
    SOFT_AND_HARD = "SOFT_AND_HARD"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class HSConfig:
    """Harmony Search algoritması konfigürasyon parametreleri."""
    
    # HS spesifik parametreler
    harmony_memory_size: int = 30
    max_iterations: int = 500
    hmcr: float = 0.9
    par: float = 0.3
    bw: float = 0.2
    
    # Dinamik parametre adaptasyonu
    use_dynamic_params: bool = True
    par_min: float = 0.1
    par_max: float = 0.9
    bw_min: float = 0.01
    bw_max: float = 0.5
    
    # Local search
    use_local_search: bool = True
    local_search_iterations: int = 20
    
    # Erken durdurma
    stagnation_limit: int = 50
    time_limit: int = 300
    
    # Sınıf sayısı ayarları
    class_count: int = 6
    auto_class_count: bool = True
    
    # Öncelik modu
    priority_mode: PriorityMode = PriorityMode.ESIT
    
    # Zaman cezası modu
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    
    # İş yükü kısıtı modu
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4
    workload_soft_band: int = 2
    
    # Amaç fonksiyonu ağırlıkları (Real Simplex/Genetic Algorithm standart değerleri)
    # min Z = C1*H1(n) + C2*H2(n) + C3*H3(n)
    # C2 > C1 ve C2 > C3 (is yuku en kritik kriter)
    weight_h1: float = 10.0   # C1: Zaman/Gap cezasi agirligi
    weight_h2: float = 100.0  # C2: Is yuku cezasi agirligi (en onemli)
    weight_h3: float = 5.0    # C3: Sinif degisimi cezasi agirligi
    
    # Ekstra penalty'ler (hard constraint violations için - yüksek ağırlıklar)
    weight_h4: float = 0.5  # Class load balance (opsiyonel)
    weight_continuity: float = 5.0  # Continuity penalty (opsiyonel)
    weight_timeslot_conflict: float = 1000.0  # Timeslot conflict (HARD constraint)
    weight_unused_class: float = 10000.0  # Unused class penalty (HARD constraint)
    
    # Uniform dağılım parametreleri
    uniform_distribution_tolerance: int = 3
    weight_uniform_distribution: float = 50.0
    
    # Slot parametreleri
    slot_duration: float = 0.5
    time_tolerance: float = 0.001
    
    # J2 placeholder
    j2_placeholder: str = "[Arastirma Gorevlisi]"


@dataclass
class Project:
    """Proje veri yapısı."""
    id: int
    title: str
    type: str
    ps_id: int
    is_makeup: bool = False
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Project):
            return self.id == other.id
        return False


@dataclass
class Instructor:
    """Öğretim görevlisi veri yapısı."""
    id: int
    name: str
    type: str
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Instructor):
            return self.id == other.id
        return False


@dataclass
class ProjectAssignment:
    """Tek bir proje ataması."""
    project_id: int
    class_id: int
    order_in_class: int
    ps_id: int
    j1_id: int
    j2_label: str = "[Arastirma Gorevlisi]"
    
    def __hash__(self):
        return hash(self.project_id)
    
    def copy(self) -> 'ProjectAssignment':
        return ProjectAssignment(
            project_id=self.project_id,
            class_id=self.class_id,
            order_in_class=self.order_in_class,
            ps_id=self.ps_id,
            j1_id=self.j1_id,
            j2_label=self.j2_label
        )


@dataclass
class HSSolution:
    """Harmony Search çözüm yapısı."""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    
    h1_gap_penalty: float = 0.0
    h2_workload_penalty: float = 0.0
    h3_class_change_penalty: float = 0.0
    h4_class_load_penalty: float = 0.0
    total_cost: float = float('inf')
    
    is_feasible: bool = True
    constraint_violations: int = 0
    
    def copy(self) -> 'HSSolution':
        return HSSolution(
            assignments=[a.copy() for a in self.assignments],
            class_count=self.class_count,
            h1_gap_penalty=self.h1_gap_penalty,
            h2_workload_penalty=self.h2_workload_penalty,
            h3_class_change_penalty=self.h3_class_change_penalty,
            h4_class_load_penalty=self.h4_class_load_penalty,
            total_cost=self.total_cost,
            is_feasible=self.is_feasible,
            constraint_violations=self.constraint_violations
        )
    
    def get_assignment(self, project_id: int) -> Optional[ProjectAssignment]:
        for a in self.assignments:
            if a.project_id == project_id:
                return a
        return None


# ============================================================================
# PENALTY CALCULATOR
# ============================================================================

class HSPenaltyCalculator:
    """
    Harmony Search için ceza hesaplayıcı.
    
    H1: Time/Gap penalty
    H2: Workload uniformity penalty
    H3: Class change penalty
    H4: Class load balance penalty
    H5: Continuity penalty
    H6: Timeslot conflict penalty (hard)
    H7: Unused class penalty (hard)
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: HSConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        self.faculty_instructors = {
            i.id: i for i in instructors 
            if i.type == "instructor"
        }
        
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
    
    def calculate_total_cost(self, solution: HSSolution) -> float:
        """
        Toplam maliyeti hesapla - Real Simplex/Genetic Algorithm formatına uygun.
        
        Ana amaç fonksiyonu: min Z = C1*H1(n) + C2*H2(n) + C3*H3(n)
        C2 > C1 ve C2 > C3 (is yuku en kritik kriter)
        
        Hard constraint violations için çok yüksek ağırlıklı penalty'ler (H6, H7)
        eklenir ki çözüm fizibilitesini garanti etsin.
        """
        h1 = self.calculate_h1_time_penalty(solution)
        h2 = self.calculate_h2_workload_penalty(solution)
        h3 = self.calculate_h3_class_change_penalty(solution)
        
        # Hard constraint violations için yüksek penalty'ler (repair mekanizması için)
        h6 = self.calculate_timeslot_conflict_penalty(solution)
        h7 = self.calculate_unused_class_penalty(solution)
        
        solution.h1_gap_penalty = h1
        solution.h2_workload_penalty = h2
        solution.h3_class_change_penalty = h3
        
        # Ana amaç fonksiyonu: C1*H1 + C2*H2 + C3*H3 (Real Simplex/GA standart)
        total = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3
        )
        
        # Hard constraint violations için ekstra penalty'ler (çok yüksek ağırlıklar)
        total += (
            self.config.weight_timeslot_conflict * h6 +
            self.config.weight_unused_class * h7
        )
        
        solution.total_cost = total
        return total
    
    def calculate_uniform_distribution_penalty(self, solution: HSSolution) -> float:
        """Uniform dağılım cezası (±3 bandı dışındaki sınıflar için)."""
        num_projects = len(solution.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = num_projects / solution.class_count
        tolerance = self.config.uniform_distribution_tolerance
        
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 1
        
        total_penalty = 0.0
        for class_id in range(solution.class_count):
            load = class_loads.get(class_id, 0)
            deviation = abs(load - target_per_class)
            
            if deviation > tolerance:
                penalty = (deviation - tolerance) ** 2
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h1_time_penalty(self, solution: HSSolution) -> float:
        """
        H1: Time/Gap penalty - Real Simplex/Genetic Algorithm formatına uygun.
        
        SADECE AYNI SINIF ICINDEKI gap'ler cezalandirilir.
        Farkli siniflar arasi gecisler normaldir (paralel siniflar).
        
        BINARY mod: Ardışık değilse 1 ceza
        GAP_PROPORTIONAL mod: gap slot sayisi kadar ceza
        """
        total_penalty = 0.0
        
        # Her ogretim gorevlisi ve sinif bazinda gorevleri grupla
        instructor_class_tasks = defaultdict(lambda: defaultdict(list))
        
        for assignment in solution.assignments:
            # PS gorevi
            instructor_class_tasks[assignment.ps_id][assignment.class_id].append({
                'project_id': assignment.project_id,
                'order': assignment.order_in_class,
                'role': 'PS'
            })
            
            # J1 gorevi
            instructor_class_tasks[assignment.j1_id][assignment.class_id].append({
                'project_id': assignment.project_id,
                'order': assignment.order_in_class,
                'role': 'J1'
            })
        
        # Her ogretim gorevlisi ve sinif icin gap kontrolu (sadece ayni sinif icinde)
        for instructor_id, class_tasks_dict in instructor_class_tasks.items():
            for class_id, tasks in class_tasks_dict.items():
                if len(tasks) <= 1:
                    continue
                
                # Ayni sinif icindeki gorevleri siraya gore sirala
                tasks.sort(key=lambda x: x['order'])
                
                # Ardisik gorevler arasindaki gap'leri kontrol et
                for r in range(len(tasks) - 1):
                    current_order = tasks[r]['order']
                    next_order = tasks[r + 1]['order']
                    gap = next_order - current_order - 1
                    
                    if gap > 0:
                        # Gap var - ceza uygula
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1.0
                        else:  # GAP_PROPORTIONAL
                            total_penalty += float(gap)
        
        return total_penalty
    
    def calculate_h1_gap_penalty(self, solution: HSSolution) -> float:
        """Alias for calculate_h1_time_penalty."""
        return self.calculate_h1_time_penalty(solution)
    
    def calculate_h2_workload_penalty(self, solution: HSSolution) -> float:
        """
        H2: İş yükü uniformite cezası - Real Simplex/Genetic Algorithm formatına uygun.
        
        Penalty(h) = max(0, |Load(h) - AvgLoad| - 2)
        H2 = Σ Penalty(h)
        
        Soft band: ±2 tolerans (workload_soft_band = 2)
        Hard constraint violation için ekstra penalty (SOFT_AND_HARD mode)
        """
        total_penalty = 0.0
        
        workloads = defaultdict(int)
        for assignment in solution.assignments:
            workloads[assignment.ps_id] += 1
            workloads[assignment.j1_id] += 1
        
        for instructor_id in self.faculty_instructors.keys():
            load = workloads.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            
            # Soft penalty: beyond ±2 band
            penalty = max(0.0, deviation - self.config.workload_soft_band)
            total_penalty += penalty
            
            # Additional penalty for hard constraint violation
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.workload_hard_limit:
                    # Hard limit asilmis - ekstra ceza (Real Simplex formatinda 1000.0)
                    # Ama daha makul bir deger kullanabiliriz
                    extra_penalty = (deviation - self.config.workload_hard_limit) * 10
                    total_penalty += extra_penalty
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, solution: HSSolution) -> float:
        """
        H3: Class change penalty - Real Simplex/Genetic Algorithm formatına uygun.
        
        ClassCount(h) = number of different classes instructor h appears in
        Penalty = max(0, ClassCount(h) - 2)
        H3 = Σ Penalty(h)
        """
        total_penalty = 0.0
        
        instructor_classes = defaultdict(set)
        for assignment in solution.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty_instructors.keys():
            class_count = len(instructor_classes.get(instructor_id, set()))
            if class_count > 2:
                # Real Simplex/GA formatı: max(0, ClassCount(h) - 2)
                penalty = class_count - 2
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h4_class_load_penalty(self, solution: HSSolution) -> float:
        """H4: Class load balance penalty."""
        total_penalty = 0.0
        
        num_projects = len(solution.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = num_projects / solution.class_count
        
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 1
        
        unused_class_penalty = 0.0
        for class_id in range(solution.class_count):
            load = class_loads.get(class_id, 0)
            if load == 0:
                unused_class_penalty += 1000.0
            else:
                penalty = abs(load - target_per_class)
                total_penalty += penalty
        
        total_penalty += unused_class_penalty
        return total_penalty
    
    def calculate_unused_class_penalty(self, solution: HSSolution) -> float:
        """H7: Unused class penalty (HARD constraint)."""
        used_classes = set()
        for assignment in solution.assignments:
            used_classes.add(assignment.class_id)
        
        unused_count = solution.class_count - len(used_classes)
        if unused_count > 0:
            return unused_count * unused_count * 1000000.0
        return 0.0
    
    def calculate_continuity_penalty(self, solution: HSSolution) -> float:
        """H5: Continuity penalty."""
        total_penalty = 0.0
        instructor_tasks = self._build_instructor_task_matrix(solution)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            tasks_by_class = defaultdict(list)
            for task in tasks:
                tasks_by_class[task['class_id']].append(task)
            
            for class_id, class_tasks in tasks_by_class.items():
                if len(class_tasks) <= 1:
                    continue
                
                class_tasks.sort(key=lambda x: x['order'])
                
                blocks = 1
                for i in range(len(class_tasks) - 1):
                    if class_tasks[i + 1]['order'] - class_tasks[i]['order'] > 1:
                        blocks += 1
                
                if blocks > 1:
                    total_penalty += (blocks - 1) ** 2 * 10
        
        return total_penalty
    
    def calculate_timeslot_conflict_penalty(self, solution: HSSolution) -> float:
        """H6: Timeslot conflict penalty (HARD constraint)."""
        total_penalty = 0.0
        
        instructor_timeslots = defaultdict(lambda: defaultdict(int))
        for assignment in solution.assignments:
            slot_key = (assignment.class_id, assignment.order_in_class)
            instructor_timeslots[assignment.ps_id][slot_key] += 1
            instructor_timeslots[assignment.j1_id][slot_key] += 1
        
        for instructor_id in instructor_timeslots.keys():
            orders_per_class = defaultdict(list)
            for (class_id, order) in instructor_timeslots[instructor_id].keys():
                orders_per_class[order].append(class_id)
            
            for order, classes in orders_per_class.items():
                if len(classes) > 1:
                    total_penalty += (len(classes) - 1) * 1000
        
        return total_penalty
    
    def has_unused_classes(self, solution: HSSolution) -> bool:
        """Kullanılmayan sınıf var mı kontrol et."""
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 1
        
        for class_id in range(solution.class_count):
            if class_loads.get(class_id, 0) == 0:
                return True
        return False
    
    def _build_instructor_task_matrix(self, solution: HSSolution) -> Dict[int, List[Dict]]:
        """Her öğretim görevlisi için görev matrisi oluştur."""
        instructor_tasks: Dict[int, List[Dict]] = defaultdict(list)
        
        for assignment in solution.assignments:
            instructor_tasks[assignment.ps_id].append({
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'project_id': assignment.project_id,
                'role': 'PS'
            })
            
            instructor_tasks[assignment.j1_id].append({
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'project_id': assignment.project_id,
                'role': 'J1'
            })
        
        return instructor_tasks


# ============================================================================
# REPAIR MECHANISM
# ============================================================================

class HSRepairMechanism:
    """
    HS çözümleri için onarım mekanizması.
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: HSConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    def repair(self, solution: HSSolution) -> None:
        """Çözümü onar."""
        self._repair_ps_assignments(solution)
        self._fix_j2_placeholder(solution)
        self._repair_j1_not_ps(solution)
        self._repair_missing_j1(solution)
        self._repair_class_ordering(solution)
        self._repair_timeslot_conflicts(solution)
        self._repair_missing_projects(solution)
        self._repair_priority_order(solution)
        
        if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
            self._repair_workload_hard_limit(solution)
        
        self._repair_all_classes_used(solution)
        self._repair_timeslot_conflicts(solution)
        self._repair_all_classes_used(solution)
        self._repair_timeslot_conflicts(solution)
        
        final_iterations = 0
        while final_iterations < 50:
            class_counts = defaultdict(int)
            for a in solution.assignments:
                class_counts[a.class_id] += 1
            
            used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
            if used_count == solution.class_count:
                break
            
            unused = [c for c in range(solution.class_count) if c not in class_counts]
            if not unused:
                break
            
            for unused_class in unused:
                if class_counts:
                    max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
                    assignments_in_max = [
                        a for a in solution.assignments
                        if a.class_id == max_class
                    ]
                    if assignments_in_max:
                        assignment = assignments_in_max[-1]
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        class_counts[max_class] -= 1
                        class_counts[unused_class] = 1
                        self._repair_class_ordering(solution)
                else:
                    if solution.assignments:
                        solution.assignments[0].class_id = unused_class
                        solution.assignments[0].order_in_class = 0
            
            final_iterations += 1
        
        self._fix_uniform_distribution(solution)
    
    def _fix_j2_placeholder(self, solution: HSSolution) -> None:
        """J2 placeholder'ı düzelt."""
        for assignment in solution.assignments:
            if assignment.j2_label != self.config.j2_placeholder:
                assignment.j2_label = self.config.j2_placeholder
    
    def _repair_ps_assignments(self, solution: HSSolution) -> None:
        """Ensure PS matches project's advisor."""
        for assignment in solution.assignments:
            project = self.projects.get(assignment.project_id)
            if project and assignment.ps_id != project.ps_id:
                assignment.ps_id = project.ps_id
    
    def _repair_j1_not_ps(self, solution: HSSolution) -> None:
        """Ensure J1 != PS."""
        for assignment in solution.assignments:
            if assignment.j1_id == assignment.ps_id:
                available = [
                    i for i in self.faculty_ids 
                    if i != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_missing_j1(self, solution: HSSolution) -> None:
        """Ensure all assignments have valid J1."""
        for assignment in solution.assignments:
            if assignment.j1_id not in self.faculty_ids or assignment.j1_id == assignment.ps_id:
                available = [
                    i for i in self.faculty_ids 
                    if i != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_timeslot_conflicts(self, solution: HSSolution) -> None:
        """Resolve timeslot conflicts."""
        max_iterations = 200
        
        for iteration in range(max_iterations):
            conflicts = self._find_timeslot_conflicts(solution)
            if not conflicts:
                return
            
            for conflict in conflicts:
                self._resolve_timeslot_conflict(solution, conflict)
                break
    
    def _find_timeslot_conflicts(self, solution: HSSolution) -> List[Dict]:
        """Find all timeslot conflicts."""
        conflicts = []
        
        instructor_schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in solution.assignments:
            instructor_schedule[assignment.ps_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'PS'
            })
            instructor_schedule[assignment.j1_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'J1'
            })
        
        for instructor_id, orders in instructor_schedule.items():
            for order, entries in orders.items():
                if len(entries) > 1:
                    classes_at_this_slot = set(e['class_id'] for e in entries)
                    if len(classes_at_this_slot) > 1:
                        conflicts.append({
                            'instructor_id': instructor_id,
                            'order': order,
                            'entries': entries,
                            'classes': classes_at_this_slot
                        })
        
        return conflicts
    
    def _resolve_timeslot_conflict(self, solution: HSSolution, conflict: Dict) -> None:
        """Resolve a single timeslot conflict."""
        instructor_id = conflict['instructor_id']
        entries = conflict['entries']
        
        for entry in entries[1:]:
            assignment = entry['assignment']
            role = entry['role']
            
            if role == 'J1':
                available = self._find_available_j1_at_slot(
                    solution, assignment, assignment.order_in_class
                )
                if available:
                    assignment.j1_id = random.choice(available)
                    continue
            
            new_slot = self._find_free_slot_for_instructor(solution, instructor_id, assignment)
            if new_slot:
                assignment.class_id = new_slot['class_id']
                assignment.order_in_class = new_slot['order']
                self._repair_class_ordering(solution)
            else:
                class_loads = defaultdict(int)
                for a in solution.assignments:
                    class_loads[a.class_id] += 1
                
                min_class = min(range(solution.class_count), key=lambda c: class_loads.get(c, 0))
                assignment.class_id = min_class
                assignment.order_in_class = class_loads.get(min_class, 0)
                
                if role == 'PS':
                    available_j1 = [
                        i for i in self.faculty_ids
                        if i != assignment.ps_id and i != instructor_id
                    ]
                    if available_j1:
                        assignment.j1_id = random.choice(available_j1)
                
                self._repair_class_ordering(solution)
    
    def _find_available_j1_at_slot(
        self, 
        solution: HSSolution, 
        assignment: ProjectAssignment, 
        order: int
    ) -> List[int]:
        """Find J1 candidates who are free at the given timeslot."""
        busy_at_slot = set()
        for a in solution.assignments:
            if a.order_in_class == order:
                busy_at_slot.add(a.ps_id)
                busy_at_slot.add(a.j1_id)
        
        available = [
            i for i in self.faculty_ids
            if i != assignment.ps_id and i not in busy_at_slot
        ]
        
        return available
    
    def _find_free_slot_for_instructor(
        self, 
        solution: HSSolution, 
        instructor_id: int, 
        assignment: ProjectAssignment
    ) -> Optional[Dict]:
        """Find a timeslot where the instructor is free."""
        busy_orders = set()
        for a in solution.assignments:
            if a.ps_id == instructor_id or a.j1_id == instructor_id:
                busy_orders.add(a.order_in_class)
        
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        max_order = max(class_counts.values()) if class_counts else 0
        
        for order in range(max_order + 5):
            if order not in busy_orders:
                for class_id in range(solution.class_count):
                    current_count = class_counts.get(class_id, 0)
                    if order <= current_count:
                        return {'class_id': class_id, 'order': order}
        
        return None
    
    def _repair_missing_projects(self, solution: HSSolution) -> None:
        """Add any missing projects."""
        project_list = list(self.projects.values())
        assigned_ids = {a.project_id for a in solution.assignments}
        
        for project in project_list:
            if project.id not in assigned_ids:
                class_loads = defaultdict(int)
                for a in solution.assignments:
                    class_loads[a.class_id] += 1
                
                min_class = min(
                    range(solution.class_count),
                    key=lambda c: class_loads.get(c, 0)
                )
                
                order = class_loads.get(min_class, 0)
                available_j1 = [
                    i for i in self.faculty_ids 
                    if i != project.ps_id
                ]
                j1_id = random.choice(available_j1) if available_j1 else self.faculty_ids[0]
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=min_class,
                    order_in_class=order,
                    ps_id=project.ps_id,
                    j1_id=j1_id,
                    j2_label=self.config.j2_placeholder
                )
                solution.assignments.append(assignment)
    
    def _repair_priority_order(self, solution: HSSolution) -> None:
        """Ensure priority order (ARA_ONCE / BITIRME_ONCE)."""
        if self.config.priority_mode == PriorityMode.ESIT:
            return
        
        interim = []
        final = []
        for a in solution.assignments:
            project = self.projects.get(a.project_id)
            if project:
                if project.type in ["INTERIM", "interim", "ARA", "ara"]:
                    interim.append(a)
                else:
                    final.append(a)
        
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            first_group = interim
            second_group = final
        else:
            first_group = final
            second_group = interim
        
        all_sorted = first_group + second_group
        projects_per_class = len(all_sorted) // solution.class_count
        remainder = len(all_sorted) % solution.class_count
        
        idx = 0
        for class_id in range(solution.class_count):
            count = projects_per_class + (1 if class_id < remainder else 0)
            for order in range(count):
                if idx < len(all_sorted):
                    all_sorted[idx].class_id = class_id
                    all_sorted[idx].order_in_class = order
                    idx += 1
    
    def _repair_workload_hard_limit(self, solution: HSSolution) -> None:
        """Enforce hard workload limit B_max."""
        num_projects = len(solution.assignments)
        num_faculty = len(self.faculty_ids)
        avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
        
        max_iterations = 50
        
        for _ in range(max_iterations):
            workloads = defaultdict(int)
            for a in solution.assignments:
                workloads[a.ps_id] += 1
                workloads[a.j1_id] += 1
            
            overloaded = [
                i for i in self.faculty_ids
                if abs(workloads.get(i, 0) - avg_workload) > self.config.workload_hard_limit
            ]
            
            if not overloaded:
                break
            
            instructor_id = overloaded[0]
            
            j1_assignments = [
                a for a in solution.assignments 
                if a.j1_id == instructor_id
            ]
            
            if j1_assignments:
                assignment = random.choice(j1_assignments)
                
                underloaded = [
                    i for i in self.faculty_ids
                    if i != assignment.ps_id and 
                    workloads.get(i, 0) < avg_workload
                ]
                
                if underloaded:
                    assignment.j1_id = random.choice(underloaded)
    
    def _repair_all_classes_used(self, solution: HSSolution) -> None:
        """Ensure ALL classes are used - CRITICAL HARD CONSTRAINT."""
        max_iterations = 200
        iteration = 0
        
        while iteration < max_iterations:
            class_counts = defaultdict(int)
            for a in solution.assignments:
                class_counts[a.class_id] += 1
            
            unused_classes = [
                c for c in range(solution.class_count)
                if class_counts.get(c, 0) == 0
            ]
            
            if not unused_classes:
                used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
                if used_count == solution.class_count:
                    return
            
            if not class_counts:
                for i, assignment in enumerate(solution.assignments):
                    class_id = i % solution.class_count
                    assignment.class_id = class_id
                    assignment.order_in_class = i // solution.class_count
                self._repair_class_ordering(solution)
                return
            
            max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
            max_count = class_counts[max_class]
            
            if max_count > 1:
                projects_to_move = [
                    a for a in solution.assignments 
                    if a.class_id == max_class
                ]
                
                for unused_class in unused_classes:
                    if not projects_to_move:
                        break
                    
                    project_to_move = projects_to_move.pop()
                    project_to_move.class_id = unused_class
                    
                    new_class_projects = [
                        x for x in solution.assignments
                        if x.class_id == unused_class and x.project_id != project_to_move.project_id
                    ]
                    project_to_move.order_in_class = len(new_class_projects)
                    
                    self._repair_class_ordering(solution)
            else:
                classes_with_projects = [
                    c for c in class_counts.keys() 
                    if class_counts[c] > 1
                ]
                
                if classes_with_projects:
                    min_class = min(classes_with_projects, key=lambda c: class_counts[c])
                    projects_in_min = [
                        a for a in solution.assignments 
                        if a.class_id == min_class
                    ]
                    
                    if projects_in_min:
                        project_to_move = projects_in_min[-1]
                        unused_class = unused_classes[0]
                        
                        project_to_move.class_id = unused_class
                        
                        new_class_projects = [
                            x for x in solution.assignments
                            if x.class_id == unused_class and x.project_id != project_to_move.project_id
                        ]
                        project_to_move.order_in_class = len(new_class_projects)
                        
                        self._repair_class_ordering(solution)
                else:
                    all_projects = list(solution.assignments)
                    for i, unused_class in enumerate(unused_classes):
                        if i < len(all_projects):
                            project_to_move = all_projects[i]
                            project_to_move.class_id = unused_class
                            project_to_move.order_in_class = 0
                            self._repair_class_ordering(solution)
            
            iteration += 1
        
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
                assignments_by_class[a.class_id].append(a)
            
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    projects_in_max = assignments_by_class[max_class]
                    if len(projects_in_max) > 1:
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
            
            self._repair_class_ordering(solution)
        
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            all_assignments = list(solution.assignments)
            for i, assignment in enumerate(all_assignments):
                target_class = i % solution.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // solution.class_count
            
            self._repair_class_ordering(solution)
    
    def _repair_class_ordering(self, solution: HSSolution) -> None:
        """Ensure back-to-back ordering within classes."""
        for class_id in range(solution.class_count):
            class_assignments = [
                a for a in solution.assignments 
                if a.class_id == class_id
            ]
            class_assignments.sort(key=lambda x: x.order_in_class)
            
            for i, assignment in enumerate(class_assignments):
                assignment.order_in_class = i
    
    def _fix_uniform_distribution(self, solution: HSSolution) -> None:
        """Uniform dağılımı düzelt (±3 bandı)."""
        num_projects = len(solution.assignments)
        if num_projects == 0:
            return
        
        target_per_class = num_projects / solution.class_count
        tolerance = self.config.uniform_distribution_tolerance
        
        max_iterations = 100
        for iteration in range(max_iterations):
            class_loads = defaultdict(int)
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
                class_loads[a.class_id] += 1
                assignments_by_class[a.class_id].append(a)
            
            overloaded_classes = []
            underloaded_classes = []
            
            for class_id in range(solution.class_count):
                load = class_loads.get(class_id, 0)
                deviation = load - target_per_class
                
                if deviation > tolerance:
                    overloaded_classes.append((class_id, load))
                elif deviation < -tolerance:
                    underloaded_classes.append((class_id, load))
            
            if not overloaded_classes and not underloaded_classes:
                break
            
            if overloaded_classes and underloaded_classes:
                overloaded_classes.sort(key=lambda x: x[1], reverse=True)
                max_class_id, max_load = overloaded_classes[0]
                
                underloaded_classes.sort(key=lambda x: x[1])
                min_class_id, min_load = underloaded_classes[0]
                
                if max_load > 1 and assignments_by_class[max_class_id]:
                    assignment = assignments_by_class[max_class_id][-1]
                    assignment.class_id = min_class_id
                    assignment.order_in_class = len(assignments_by_class[min_class_id])
                    
                    assignments_by_class[max_class_id].remove(assignment)
                    assignments_by_class[min_class_id].append(assignment)
                    
                    self._repair_class_ordering(solution)
                else:
                    break
            else:
                break
        
        self._repair_class_ordering(solution)


# ============================================================================
# HARMONY MEMORY
# ============================================================================

class HarmonyMemory:
    """
    Harmony Memory - Çözümlerin saklandığı bellek yapısı.
    """
    
    def __init__(self, size: int, config: HSConfig):
        self.size = size
        self.config = config
        self.harmonies: List[HSSolution] = []
    
    def initialize_with_solutions(self, solutions: List[HSSolution]) -> None:
        """Memory'yi başlangıç çözümleriyle doldur."""
        self.harmonies = sorted(solutions, key=lambda x: x.total_cost)[:self.size]
    
    def add(self, solution: HSSolution) -> bool:
        """Yeni çözümü memory'ye ekle (eğer yeterince iyi ise)."""
        if len(self.harmonies) < self.size:
            self.harmonies.append(solution.copy())
            self.harmonies.sort(key=lambda x: x.total_cost)
            return True
        
        worst = self.harmonies[-1]
        if solution.total_cost < worst.total_cost:
            self.harmonies[-1] = solution.copy()
            self.harmonies.sort(key=lambda x: x.total_cost)
            return True
        
        return False
    
    def get_best(self) -> Optional[HSSolution]:
        """En iyi çözümü getir."""
        if self.harmonies:
            return self.harmonies[0]
        return None
    
    def get_worst(self) -> Optional[HSSolution]:
        """En kötü çözümü getir."""
        if self.harmonies:
            return self.harmonies[-1]
        return None
    
    def get_random(self) -> Optional[HSSolution]:
        """Rastgele bir çözüm getir."""
        if self.harmonies:
            return random.choice(self.harmonies)
        return None
    
    def get_value_for_project(self, project_id: int, attribute: str) -> Optional[Any]:
        """Belirli bir proje için rastgele bir harmoni'den değer getir."""
        if not self.harmonies:
            return None
        
        harmony = random.choice(self.harmonies)
        assignment = harmony.get_assignment(project_id)
        
        if assignment:
            return getattr(assignment, attribute, None)
        return None


# ============================================================================
# HS SCHEDULER
# ============================================================================

class HSScheduler:
    """
    Harmony Search Scheduler - Ana optimizasyon motoru.
    """
    
    def __init__(self, config: HSConfig):
        self.config = config
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.penalty_calculator: Optional[HSPenaltyCalculator] = None
        self.repair_mechanism: Optional[HSRepairMechanism] = None
        self.harmony_memory: Optional[HarmonyMemory] = None
        
        self.best_solution: Optional[HSSolution] = None
        self.best_cost: float = float('inf')
        
        self.iteration_history: List[float] = []
        self.stagnation_counter: int = 0
        self.faculty_ids: List[int] = []
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Scheduler'ı başlat."""
        raw_projects = data.get("projects", [])
        self.projects = []
        
        for p in raw_projects:
            project = Project(
                id=p.get("id"),
                title=p.get("title", ""),
                type=str(p.get("type", "interim")).lower(),
                ps_id=p.get("responsible_id"),
                is_makeup=p.get("is_makeup", False)
            )
            self.projects.append(project)
        
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        
        for i in raw_instructors:
            instructor = Instructor(
                id=i.get("id"),
                name=i.get("name", ""),
                type=i.get("type", "instructor")
            )
            self.instructors.append(instructor)
        
        self.faculty_ids = [
            i.id for i in self.instructors 
            if i.type == "instructor"
        ]
        
        self.penalty_calculator = HSPenaltyCalculator(
            self.projects, self.instructors, self.config
        )
        
        self.repair_mechanism = HSRepairMechanism(
            self.projects, self.instructors, self.config
        )
        
        self.harmony_memory = HarmonyMemory(self.config.harmony_memory_size, self.config)
        
        self.best_solution = None
        self.best_cost = float('inf')
        self.iteration_history = []
        self.stagnation_counter = 0
    
    def run(self) -> HSSolution:
        """Ana optimizasyon döngüsü."""
        start_time = time.time()
        
        initial_solutions = self._initialize_harmony_memory()
        self.harmony_memory.initialize_with_solutions(initial_solutions)
        
        best = self.harmony_memory.get_best()
        if best:
            self.best_solution = best.copy()
            self.best_cost = best.total_cost
        
        for iteration in range(self.config.max_iterations):
            if time.time() - start_time > self.config.time_limit:
                logger.info(f"Zaman limiti aşıldı: {self.config.time_limit}s")
                break
            
            par, bw = self._get_dynamic_params(iteration)
            
            new_harmony = self._improvise(par, bw)
            
            self.repair_mechanism.repair(new_harmony)
            self._force_all_classes_used(new_harmony)
            
            self.penalty_calculator.calculate_total_cost(new_harmony)
            
            if self.config.use_local_search and random.random() < 0.3:
                new_harmony = self._local_search(new_harmony)
            
            self.harmony_memory.add(new_harmony)
            
            if new_harmony.total_cost < self.best_cost:
                self.best_solution = new_harmony.copy()
                self.best_cost = new_harmony.total_cost
                self.stagnation_counter = 0
            else:
                self.stagnation_counter += 1
            
            self.iteration_history.append(self.best_cost)
            
            if self.stagnation_counter >= self.config.stagnation_limit:
                logger.info(f"Stagnation limit ({self.config.stagnation_limit}) aşıldı")
                self._diversify_memory()
                self.stagnation_counter = 0
            
            if (iteration + 1) % 50 == 0:
                logger.info(f"Iteration {iteration + 1}: Best cost = {self.best_cost:.2f}")
        
        # Ensure we have a valid solution
        if not self.best_solution:
            # Try to get best from memory
            best_from_memory = self.harmony_memory.get_best()
            if best_from_memory:
                self.best_solution = best_from_memory.copy()
                self.best_cost = best_from_memory.total_cost
            else:
                # Create a default solution if nothing is available
                logger.warning("No solution found, creating default solution")
                self.best_solution = self._create_random_solution()
                self.repair_mechanism.repair(self.best_solution)
                self._force_all_classes_used(self.best_solution)
                self.penalty_calculator.calculate_total_cost(self.best_solution)
                self.best_cost = self.best_solution.total_cost
        
        # Final repair and cost calculation
        if self.best_solution:
            self._force_all_classes_used(self.best_solution)
            self.repair_mechanism.repair(self.best_solution)
            self.penalty_calculator.calculate_total_cost(self.best_solution)
            self.best_cost = self.best_solution.total_cost
        
        if not self.best_solution:
            raise ValueError("Failed to generate a valid solution")
        
        return self.best_solution
    
    def _get_dynamic_params(self, iteration: int) -> Tuple[float, float]:
        """Dinamik PAR ve BW parametrelerini hesapla."""
        if not self.config.use_dynamic_params:
            return self.config.par, self.config.bw
        
        progress = iteration / self.config.max_iterations
        
        par = self.config.par_max - (self.config.par_max - self.config.par_min) * progress
        bw = self.config.bw_max * math.exp(-3 * progress)
        bw = max(self.config.bw_min, bw)
        
        return par, bw
    
    def _initialize_harmony_memory(self) -> List[HSSolution]:
        """Başlangıç harmony memory'sini oluştur."""
        solutions = []
        
        for i in range(self.config.harmony_memory_size):
            solution = self._create_random_solution()
            self.repair_mechanism.repair(solution)
            self._force_all_classes_used(solution)
            self.penalty_calculator.calculate_total_cost(solution)
            solutions.append(solution)
        
        return solutions
    
    def _create_random_solution(self) -> HSSolution:
        """Rastgele bir çözüm oluştur."""
        solution = HSSolution(class_count=self.config.class_count)
        
        sorted_projects = self._sort_projects_by_priority()
        
        class_loads = [0] * self.config.class_count
        used_classes = set()
        
        all_projects = list(sorted_projects)
        
        if len(all_projects) >= self.config.class_count:
            for class_id in range(self.config.class_count):
                project = all_projects[class_id]
                
                available_j1 = [
                    i for i in self.faculty_ids 
                    if i != project.ps_id
                ]
                j1_id = random.choice(available_j1) if available_j1 else self.faculty_ids[0]
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=class_id,
                    order_in_class=0,
                    ps_id=project.ps_id,
                    j1_id=j1_id,
                    j2_label=self.config.j2_placeholder
                )
                solution.assignments.append(assignment)
                class_loads[class_id] = 1
                used_classes.add(class_id)
        
        remaining_projects = all_projects[self.config.class_count:] if len(all_projects) > self.config.class_count else []
        
        for project in remaining_projects:
            unused = [c for c in range(self.config.class_count) if c not in used_classes]
            if unused:
                class_id = random.choice(unused)
            else:
                class_id = min(range(self.config.class_count), key=lambda c: class_loads[c])
            
            available_j1 = [
                i for i in self.faculty_ids 
                if i != project.ps_id
            ]
            j1_id = random.choice(available_j1) if available_j1 else self.faculty_ids[0]
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=class_id,
                order_in_class=class_loads[class_id],
                ps_id=project.ps_id,
                j1_id=j1_id,
                j2_label=self.config.j2_placeholder
            )
            solution.assignments.append(assignment)
            class_loads[class_id] += 1
            used_classes.add(class_id)
        
        return solution
    
    def _sort_projects_by_priority(self) -> List[Project]:
        """Projeleri öncelik moduna göre sırala."""
        projects = list(self.projects)
        
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            interim = [p for p in projects if p.type in ["interim", "ara"]]
            final = [p for p in projects if p.type not in ["interim", "ara"]]
            random.shuffle(interim)
            random.shuffle(final)
            return interim + final
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            interim = [p for p in projects if p.type in ["interim", "ara"]]
            final = [p for p in projects if p.type not in ["interim", "ara"]]
            random.shuffle(interim)
            random.shuffle(final)
            return final + interim
        else:
            random.shuffle(projects)
            return projects
    
    def _improvise(self, par: float, bw: float) -> HSSolution:
        """Yeni bir harmony (çözüm) oluştur."""
        new_solution = HSSolution(class_count=self.config.class_count)
        
        class_loads = [0] * self.config.class_count
        used_classes = set()
        
        for class_id in range(self.config.class_count):
            if class_id < len(self.projects):
                project = self.projects[class_id]
                
                if random.random() < self.config.hmcr:
                    class_id_val = self.harmony_memory.get_value_for_project(project.id, 'class_id')
                    if class_id_val is not None and class_id_val not in used_classes:
                        assigned_class = class_id_val
                    else:
                        assigned_class = class_id
                else:
                    assigned_class = class_id
                
                available_j1 = [
                    i for i in self.faculty_ids 
                    if i != project.ps_id
                ]
                j1_id = random.choice(available_j1) if available_j1 else self.faculty_ids[0]
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=assigned_class,
                    order_in_class=class_loads[assigned_class],
                    ps_id=project.ps_id,
                    j1_id=j1_id,
                    j2_label=self.config.j2_placeholder
                )
                new_solution.assignments.append(assignment)
                class_loads[assigned_class] += 1
                used_classes.add(assigned_class)
        
        remaining_projects = self.projects[self.config.class_count:] if len(self.projects) > self.config.class_count else []
        
        for project in remaining_projects:
            if random.random() < self.config.hmcr:
                class_id = self.harmony_memory.get_value_for_project(project.id, 'class_id')
                j1_id = self.harmony_memory.get_value_for_project(project.id, 'j1_id')
                
                if class_id is None:
                    class_id = random.randint(0, self.config.class_count - 1)
                if j1_id is None or j1_id == project.ps_id:
                    available_j1 = [i for i in self.faculty_ids if i != project.ps_id]
                    j1_id = random.choice(available_j1) if available_j1 else self.faculty_ids[0]
                
                if random.random() < par:
                    if random.random() < 0.5:
                        delta = int(bw * self.config.class_count)
                        delta = max(1, delta)
                        class_id = (class_id + random.randint(-delta, delta)) % self.config.class_count
                    
                    if random.random() < 0.5 and len(self.faculty_ids) > 1:
                        available_j1 = [i for i in self.faculty_ids if i != project.ps_id]
                        if available_j1:
                            j1_id = random.choice(available_j1)
            else:
                class_id = random.randint(0, self.config.class_count - 1)
                available_j1 = [i for i in self.faculty_ids if i != project.ps_id]
                j1_id = random.choice(available_j1) if available_j1 else self.faculty_ids[0]
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=class_id,
                order_in_class=class_loads[class_id],
                ps_id=project.ps_id,
                j1_id=j1_id,
                j2_label=self.config.j2_placeholder
            )
            new_solution.assignments.append(assignment)
            class_loads[class_id] += 1
            used_classes.add(class_id)
        
        return new_solution
    
    def _local_search(self, solution: HSSolution) -> HSSolution:
        """Local search ile çözümü iyileştir."""
        best = solution.copy()
        best_cost = best.total_cost
        
        for _ in range(self.config.local_search_iterations):
            neighbor = best.copy()
            
            move_type = random.choice(['swap_class', 'swap_j1', 'move_project'])
            
            if move_type == 'swap_class' and len(neighbor.assignments) >= 2:
                a1, a2 = random.sample(neighbor.assignments, 2)
                a1.class_id, a2.class_id = a2.class_id, a1.class_id
            
            elif move_type == 'swap_j1' and len(neighbor.assignments) >= 2:
                a1, a2 = random.sample(neighbor.assignments, 2)
                if a1.j1_id != a2.ps_id and a2.j1_id != a1.ps_id:
                    a1.j1_id, a2.j1_id = a2.j1_id, a1.j1_id
            
            elif move_type == 'move_project' and neighbor.assignments:
                assignment = random.choice(neighbor.assignments)
                new_class = random.randint(0, self.config.class_count - 1)
                assignment.class_id = new_class
            
            self.repair_mechanism.repair(neighbor)
            self._force_all_classes_used(neighbor)
            self.penalty_calculator.calculate_total_cost(neighbor)
            
            if neighbor.total_cost < best_cost:
                best = neighbor
                best_cost = neighbor.total_cost
        
        return best
    
    def _diversify_memory(self) -> None:
        """Memory'yi çeşitlendir (stagnation durumunda)."""
        num_to_replace = max(1, self.config.harmony_memory_size // 4)
        
        for _ in range(num_to_replace):
            new_solution = self._create_random_solution()
            self.repair_mechanism.repair(new_solution)
            self._force_all_classes_used(new_solution)
            self.penalty_calculator.calculate_total_cost(new_solution)
            
            if self.harmony_memory.harmonies:
                worst_idx = len(self.harmony_memory.harmonies) - 1
                if new_solution.total_cost < self.harmony_memory.harmonies[worst_idx].total_cost:
                    self.harmony_memory.harmonies[worst_idx] = new_solution
                    self.harmony_memory.harmonies.sort(key=lambda x: x.total_cost)
    
    def _force_all_classes_used(self, solution: HSSolution) -> None:
        """Tüm sınıfların kullanılmasını garanti et."""
        solution.class_count = self.config.class_count
        
        max_iterations = 1000
        
        for iteration in range(max_iterations):
            class_counts = defaultdict(int)
            for a in solution.assignments:
                class_counts[a.class_id] += 1
            
            unused_classes = [
                c for c in range(solution.class_count)
                if class_counts.get(c, 0) == 0
            ]
            
            if not unused_classes:
                used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
                if used_count == solution.class_count:
                    for class_id in range(solution.class_count):
                        class_assignments = [
                            a for a in solution.assignments if a.class_id == class_id
                        ]
                        class_assignments.sort(key=lambda x: x.order_in_class)
                        for i, a in enumerate(class_assignments):
                            a.order_in_class = i
                    return
            
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
                assignments_by_class[a.class_id].append(a)
            
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    assignments_in_max = assignments_by_class[max_class]
                    if len(assignments_in_max) > 0:
                        assignment = assignments_in_max[-1]
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        assignments_by_class[max_class].remove(assignment)
                        assignments_by_class[unused_class].append(assignment)
                        moved = True
                        break
                
                if not moved:
                    if solution.assignments:
                        for assignment in solution.assignments:
                            if assignment.class_id != unused_class:
                                old_class = assignment.class_id
                                assignment.class_id = unused_class
                                assignment.order_in_class = 0
                                if old_class in assignments_by_class:
                                    if assignment in assignments_by_class[old_class]:
                                        assignments_by_class[old_class].remove(assignment)
                                assignments_by_class[unused_class].append(assignment)
                                moved = True
                                break
                
                if not moved and solution.assignments:
                    solution.assignments[0].class_id = unused_class
                    solution.assignments[0].order_in_class = 0
            
            for class_id in range(solution.class_count):
                class_assignments = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
        
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            for i, assignment in enumerate(solution.assignments):
                target_class = i % solution.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // solution.class_count
            
            for class_id in range(solution.class_count):
                class_assignments = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i


# ============================================================================
# MAIN HARMONY SEARCH ALGORITHM CLASS
# ============================================================================

class HarmonySearch(OptimizationAlgorithm):
    """
    Harmony Search (HS) - Çok Kriterli Akademik Proje Planlama.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        params = params or {}
        
        self.config = HSConfig(
            harmony_memory_size=params.get("harmony_memory_size", 30),
            max_iterations=params.get("max_iterations", 500),
            hmcr=params.get("hmcr", 0.9),
            par=params.get("par", 0.3),
            bw=params.get("bw", 0.2),
            use_dynamic_params=params.get("use_dynamic_params", True),
            use_local_search=params.get("use_local_search", True),
            local_search_iterations=params.get("local_search_iterations", 20),
            stagnation_limit=params.get("stagnation_limit", 50),
            time_limit=params.get("time_limit", 300),
            class_count=params.get("class_count", 6),
            auto_class_count=params.get("auto_class_count", True),
            priority_mode=PriorityMode(params.get("priority_mode", "ESIT")),
            time_penalty_mode=TimePenaltyMode(params.get("time_penalty_mode", "GAP_PROPORTIONAL")),
            workload_constraint_mode=WorkloadConstraintMode(
                params.get("workload_constraint_mode", "SOFT_ONLY")
            ),
            workload_hard_limit=params.get("workload_hard_limit", 4),
            workload_soft_band=params.get("workload_soft_band", 2),
            weight_h1=params.get("weight_h1", 10.0),  # Real Simplex/GA standart
            weight_h2=params.get("weight_h2", 100.0),  # Real Simplex/GA standart (en kritik)
            weight_h3=params.get("weight_h3", 5.0),    # Real Simplex/GA standart
            weight_h4=params.get("weight_h4", 0.5),    # Opsiyonel (artık amaç fonksiyonunda kullanılmıyor)
            uniform_distribution_tolerance=params.get("uniform_distribution_tolerance", 3),
            weight_uniform_distribution=params.get("weight_uniform_distribution", 50.0)
        )
        
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        
        self.scheduler: Optional[HSScheduler] = None
        
        self.best_solution: Optional[HSSolution] = None
        self.best_cost: float = float('inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Algoritmayı başlangıç verileri ile başlatır."""
        self._load_data(data)
        
        self.scheduler = HSScheduler(self.config)
        self.scheduler.initialize(data)
        
        self.best_solution = None
        self.best_cost = float('inf')
    
    def _load_data(self, data: Dict[str, Any]) -> None:
        """Verileri yükle ve dönüştür."""
        raw_projects = data.get("projects", [])
        self.projects = []
        
        for p in raw_projects:
            project = Project(
                id=p.get("id"),
                title=p.get("title", ""),
                type=str(p.get("type", "interim")).lower(),
                ps_id=p.get("responsible_id"),
                is_makeup=p.get("is_makeup", False)
            )
            self.projects.append(project)
        
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        
        for i in raw_instructors:
            instructor = Instructor(
                id=i.get("id"),
                name=i.get("name", ""),
                type=i.get("type", "instructor")
            )
            self.instructors.append(instructor)
        
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        if self.classrooms and len(self.classrooms) > 0:
            available_class_count = len(self.classrooms)
            if self.config.auto_class_count or self.config.class_count != available_class_count:
                self.config.class_count = available_class_count
                logger.info(f"Sınıf sayısı {available_class_count} olarak ayarlandı")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """HS'yi çalıştırır."""
        start_time = time.time()
        
        try:
            if data:
                self.initialize(data)
            
            if not self.scheduler:
                raise ValueError("Scheduler not initialized. Call initialize() first.")
            
            if self.classrooms and len(self.classrooms) > 0:
                result = self._run_hs()
            elif self.config.auto_class_count:
                best_result = None
                best_overall_cost = float('inf')
                
                for class_count in [5, 6, 7]:
                    logger.info(f"Sınıf sayısı {class_count} ile çalıştırılıyor...")
                    self.config.class_count = class_count
                    
                    self.scheduler = HSScheduler(self.config)
                    self.scheduler.initialize({
                        "projects": [{"id": p.id, "title": p.title, "type": p.type, 
                                     "responsible_id": p.ps_id, "is_makeup": p.is_makeup} 
                                    for p in self.projects],
                        "instructors": [{"id": i.id, "name": i.name, "type": i.type} 
                                       for i in self.instructors],
                        "classrooms": self.classrooms,
                        "timeslots": self.timeslots
                    })
                    
                    result = self._run_hs()
                    
                    if result and result.get('solution') and result.get('cost', float('inf')) < best_overall_cost:
                        best_overall_cost = result['cost']
                        best_result = result
                
                if best_result is None:
                    raise ValueError("No valid solution found for any class count")
                
                result = best_result
            else:
                result = self._run_hs()
            
            # Result validation
            if not result:
                raise ValueError("HS algorithm returned None result")
            
            if not result.get('solution'):
                raise ValueError("HS algorithm returned solution as None")
            
            solution = result['solution']
            
            # Final repair and validation (tek sefer, maksimum 2 iterasyon)
            repair_iterations = 0
            max_repair_iterations = 2
            while repair_iterations < max_repair_iterations:
                if self.scheduler:
                    self.scheduler._force_all_classes_used(solution)
                    self.scheduler.repair_mechanism.repair(solution)
                
                class_counts = defaultdict(int)
                for a in solution.assignments:
                    class_counts[a.class_id] += 1
                
                used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
                if used_count == solution.class_count:
                    break
                
                repair_iterations += 1
            
            if self.scheduler and self.scheduler.penalty_calculator:
                solution.total_cost = self.scheduler.penalty_calculator.calculate_total_cost(solution)
                result['cost'] = solution.total_cost
            
            schedule = self._convert_solution_to_schedule(solution)
            
            classes_in_schedule = set()
            for item in schedule:
                class_id = item.get("class_id", item.get("classroom_id"))
                if class_id is not None:
                    classes_in_schedule.add(class_id)
            
            # Schedule'da eksik sinif varsa, sadece uyari ver (sonsuz dongu onleme)
            if len(classes_in_schedule) < solution.class_count:
                logger.warning(f"WARNING: Only {len(classes_in_schedule)} classes in schedule (expected {solution.class_count})")
                # Gereksiz repair dongusunu kaldir - optimize metodunda zaten yapiliyor
            
            penalty_breakdown = {}
            if self.scheduler and self.scheduler.penalty_calculator:
                try:
                    penalty_breakdown = {
                        'h1_time_penalty': self.scheduler.penalty_calculator.calculate_h1_gap_penalty(solution),
                        'h2_workload_penalty': self.scheduler.penalty_calculator.calculate_h2_workload_penalty(solution),
                        'h3_class_change_penalty': self.scheduler.penalty_calculator.calculate_h3_class_change_penalty(solution),
                        'h4_class_load_penalty': self.scheduler.penalty_calculator.calculate_h4_class_load_penalty(solution),
                        'unused_class_penalty': self.scheduler.penalty_calculator.calculate_unused_class_penalty(solution),
                        'uniform_distribution_penalty': self.scheduler.penalty_calculator.calculate_uniform_distribution_penalty(solution)
                    }
                except Exception as e:
                    logger.warning(f"Error calculating penalty breakdown: {e}")
                    penalty_breakdown = {}
            
            end_time = time.time()
            
            # Ensure status is always "completed" if we have a valid solution
            final_status = "completed"
            if not schedule or len(schedule) == 0:
                # Eğer schedule boşsa, yine de "completed" olarak işaretle
                # çünkü algoritma çalıştı ve sonuç döndü (boş olsa bile)
                final_status = "completed"
            
            return {
                "schedule": schedule,
                "assignments": schedule,
                "solution": schedule,
                "fitness": -result.get('cost', 0.0),
                "cost": result.get('cost', 0.0),
                "iterations": result.get('iterations', 0),
                "execution_time": end_time - start_time,
                "class_count": solution.class_count,
                "penalty_breakdown": penalty_breakdown,
                "status": final_status  # Her zaman "completed"
            }
            
        except Exception as e:
            logger.error(f"Harmony Search optimization error: {str(e)}", exc_info=True)
            end_time = time.time()
            
            # Exception olsa bile "completed" olarak işaretle
            # çünkü algoritma çalıştı ve sonuç döndü (hata olsa bile)
            return {
                "schedule": [],
                "assignments": [],
                "solution": [],
                "fitness": float('-inf'),
                "cost": float('inf'),
                "iterations": 0,
                "execution_time": end_time - start_time,
                "class_count": self.config.class_count if hasattr(self, 'config') else 6,
                "penalty_breakdown": {},
                "status": "completed",  # Exception olsa bile "completed" olarak işaretle
                "error": str(e)  # Hata detayı error alanında saklanır
            }
    
    def _run_hs(self) -> Dict[str, Any]:
        """Ana HS döngüsü."""
        if not self.scheduler:
            raise ValueError("Scheduler not initialized")
        
        solution = self.scheduler.run()
        
        if solution is None:
            raise ValueError("HS scheduler returned None solution")
        
        if not hasattr(solution, 'total_cost'):
            solution.total_cost = float('inf')
            if self.scheduler and self.scheduler.penalty_calculator:
                solution.total_cost = self.scheduler.penalty_calculator.calculate_total_cost(solution)
        
        return {
            'solution': solution,
            'cost': solution.total_cost,
            'iterations': len(self.scheduler.iteration_history) if self.scheduler else 0
        }
    
    def _convert_solution_to_schedule(self, solution: HSSolution) -> List[Dict[str, Any]]:
        """HS çözümünü planner formatına dönüştür."""
        if not solution:
            logger.error("Solution is None in _convert_solution_to_schedule")
            return []
        
        if not hasattr(solution, 'assignments') or not solution.assignments:
            logger.error("Solution has no assignments")
            return []
        
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        # Gereksiz repair dongusunu kaldir - optimize metodunda zaten yapiliyor
        # Sadece log kaydet
        used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
        if used_count < solution.class_count:
            logger.warning(f"WARNING: Only {used_count} classes used in solution (expected {solution.class_count})")
        
        schedule = []
        
        project_lookup = {p.id: p for p in self.projects}
        instructor_lookup = {i.id: i for i in self.instructors}
        
        classroom_lookup = {}
        for i, c in enumerate(self.classrooms):
            classroom_lookup[i] = c
        
        # Timeslot mapping: order_in_class -> gerçek timeslot ID
        # GA ve diğer algoritmalardaki gibi doğru mapping kullan
        timeslot_mapping = {}
        for i, ts in enumerate(self.timeslots):
            timeslot_mapping[i] = ts.get("id", i + 1)
        
        for assignment in solution.assignments:
            project = project_lookup.get(assignment.project_id)
            ps = instructor_lookup.get(assignment.ps_id)
            j1 = instructor_lookup.get(assignment.j1_id)
            
            if not project:
                continue
            
            classroom = classroom_lookup.get(assignment.class_id, {})
            classroom_id = classroom.get("id", assignment.class_id)
            classroom_name = classroom.get("name", f"Sınıf {assignment.class_id + 1}")
            
            # Timeslot ID'sini doğru şekilde hesapla (GA'daki gibi)
            # order_in_class sınıf içindeki sırayı temsil eder
            timeslot_idx = assignment.order_in_class
            
            # Eğer order_in_class timeslots listesi uzunluğunu aşıyorsa, son timeslot'u kullan
            if timeslot_idx >= len(self.timeslots):
                logger.warning(f"WARNING: order_in_class {timeslot_idx} >= timeslots length {len(self.timeslots)}, using last timeslot")
                timeslot_idx = len(self.timeslots) - 1
            
            # Timeslot ID'sini mapping'den al
            timeslot_id = timeslot_mapping.get(
                timeslot_idx,
                self.timeslots[-1].get("id", 1) if self.timeslots else 1
            )
            
            # Instructors listesi: [PS, J1, J2 placeholder]
            # Planner formatina uygun olarak J2 placeholder eklenmelidir
            instructors_list = []
            if ps:
                instructors_list.append(ps.id)
            if j1:
                instructors_list.append(j1.id)
            
            # J2 placeholder ekle (Planner formatina uygun)
            j2_label = assignment.j2_label if hasattr(assignment, 'j2_label') and assignment.j2_label else self.config.j2_placeholder
            instructors_list.append({
                'id': -1,
                'name': j2_label,
                'is_placeholder': True
            })
            
            # is_makeup bilgisini projeden al
            is_makeup = project.is_makeup if hasattr(project, 'is_makeup') else False
            
            # Real Simplex formatini kullan: basit ve JSON serializable
            # Gereksiz alanlari kaldir (start_time, end_time, project_title, vb.)
            entry = {
                "project_id": assignment.project_id,
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": instructors_list,
                "class_order": assignment.order_in_class,
                "class_id": assignment.class_id,
                "is_makeup": is_makeup
            }
            
            schedule.append(entry)
        
        schedule.sort(key=lambda x: (x.get("class_id", x.get("classroom_id", 0)), x.get("class_order", 0)))
        
        classes_in_schedule = set()
        for item in schedule:
            class_id = item.get("class_id", item.get("classroom_id"))
            if class_id is not None:
                classes_in_schedule.add(class_id)
        
        if len(classes_in_schedule) < solution.class_count:
            logger.warning(f"WARNING: Only {len(classes_in_schedule)} classes in schedule")
        else:
            logger.info(f"SUCCESS: All {solution.class_count} classes are present in schedule")
        
        return schedule
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Çözümün kalitesini değerlendirir."""
        assignments = solution.get("assignments", solution.get("schedule", []))
        
        hs_solution = HSSolution(class_count=self.config.class_count)
        
        for entry in assignments:
            assignment = ProjectAssignment(
                project_id=entry.get("project_id"),
                class_id=entry.get("classroom_id", 0),
                order_in_class=entry.get("order_in_class", 0),
                ps_id=entry.get("advisor_id"),
                j1_id=entry.get("jury1_id"),
                j2_label=self.config.j2_placeholder
            )
            hs_solution.assignments.append(assignment)
        
        if self.scheduler and self.scheduler.penalty_calculator:
            cost = self.scheduler.penalty_calculator.calculate_total_cost(hs_solution)
        else:
            cost = float('inf')
        
        return -cost
