"""
ANT COLONY OPTIMIZATION (ACO) - Çok Kriterli Akademik Proje Sınavı/Jüri Planlama ve Atama Sistemi

Bu modül, üniversitelerde dönem sonlarında gerçekleştirilen Ara Proje ve Bitirme Projesi
değerlendirme süreçlerinde yaşanan planlama, atama ve iş yükü dağıtımı problemlerine yönelik
olarak geliştirilmiş Ant Colony Optimization (ACO) algoritmasını implement eder.

PROBLEM TANIMI:
- Her projede: 1 Proje Sorumlusu (PS), 1 Jüri (J1), 1 Placeholder Jüri (J2 = [Araştırma Görevlisi])
- X gerçek öğretim görevlisi, Y proje, z sınıf (5, 6, veya 7)
- Projeler sınıf içinde back-to-back (ardışık) yerleştirilmeli
- Her öğretim görevlisi her timeslot'ta en fazla 1 görev alabilir

AMAÇ FONKSİYONU:
    min Z = C1*H1(n) + C2*H2(n) + C3*H3(n) + C4*H4(n)

Burada:
- H1: Zaman/GAP Cezası (ardışık olmayan görevler için)
- H2: İş Yükü Uniformite Cezası (en önemli, C2 > C1 ve C2 > C3)
- H3: Sınıf Değişimi Cezası
- H4: Sınıf Yükü Dengesi Cezası

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

ACO SPESİFİK PARAMETRELER:
- ant_count: Koloni boyutu
- alpha: Feromon etkisi
- beta: Heuristik bilgi etkisi
- evaporation_rate: Feromon buharlaşma oranı
- Q: Feromon miktarı sabiti

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
    ARA_ONCE = "ARA_ONCE"           # Tüm ARA (ara) projeleri BITIRME'den önce
    BITIRME_ONCE = "BITIRME_ONCE"   # Tüm BITIRME projeleri ARA'dan önce
    ESIT = "ESIT"                   # Öncelik kısıtı yok


class TimePenaltyMode(str, Enum):
    """Zaman/GAP cezası hesaplama modu."""
    BINARY = "BINARY"                       # Ardışık değilse 1 ceza
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Ceza = boşluk slot sayısı


class WorkloadConstraintMode(str, Enum):
    """İş yükü kısıtı modu."""
    SOFT_ONLY = "SOFT_ONLY"           # Sadece ceza (H2)
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Ceza + hard kısıt (B_max)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ACOConfig:
    """ACO algoritması konfigürasyon parametreleri."""
    
    # ACO spesifik parametreler
    ant_count: int = 50                    # Koloni boyutu
    max_iterations: int = 200              # Maksimum iterasyon sayısı
    alpha: float = 1.0                     # Feromon etkisi (α)
    beta: float = 2.0                      # Heuristik bilgi etkisi (β)
    evaporation_rate: float = 0.1          # Feromon buharlaşma oranı (ρ)
    Q: float = 100.0                       # Feromon miktarı sabiti
    initial_pheromone: float = 1.0         # Başlangıç feromon değeri
    min_pheromone: float = 0.01            # Minimum feromon değeri
    max_pheromone: float = 10.0            # Maksimum feromon değeri
    
    # Elitist ACO parametreleri
    use_elitist: bool = True               # Elitist ACO kullan
    elitist_weight: float = 2.0            # Elitist karınca ağırlığı
    
    # Local search parametreleri
    use_local_search: bool = True          # Local search uygula
    local_search_iterations: int = 10      # Local search iterasyon sayısı
    
    # Erken durdurma
    stagnation_limit: int = 30             # İyileşme olmadan durma limiti
    time_limit: int = 300                  # Maksimum süre (saniye)
    
    # Sınıf sayısı ayarları
    class_count: int = 6
    auto_class_count: bool = True          # 5, 6, 7 dene ve en iyisini seç
    
    # Öncelik modu
    priority_mode: PriorityMode = PriorityMode.ESIT
    
    # Zaman cezası modu
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    
    # İş yükü kısıtı modu
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4           # B_max (SOFT_AND_HARD modu için)
    workload_soft_band: int = 2            # ±2 tolerans
    
    # Amaç fonksiyonu ağırlıkları (SA'daki gibi - C2 > C1 ve C2 > C3 - iş yükü en önemli)
    weight_h1: float = 1.0                 # Time/GAP penalty (SA'daki gibi)
    weight_h2: float = 2.0                 # Workload uniformity penalty (most important - SA'daki gibi)
    weight_h3: float = 3.0                 # Class change penalty (SA'daki gibi)
    weight_h4: float = 0.5                # Class load balance penalty (SA'daki gibi)
    weight_continuity: float = 5.0         # Continuity penalty (H5 - SA'daki gibi)
    weight_timeslot_conflict: float = 1000.0  # Timeslot conflict (HARD - SA'daki gibi)
    weight_unused_class: float = 10000.0   # Unused class penalty (HARD - VERY HIGH - SA'daki gibi)
    
    # Uniform dağılım parametreleri (±3 bandı)
    uniform_distribution_tolerance: int = 3  # ±3 proje sayısı toleransı
    weight_uniform_distribution: float = 50.0  # Uniform dağılım cezası ağırlığı
    
    # Slot parametreleri
    slot_duration: float = 0.5             # 30 dakika
    time_tolerance: float = 0.001          # Zaman karşılaştırma toleransı
    
    # J2 placeholder
    j2_placeholder: str = "[Arastirma Gorevlisi]"


@dataclass
class Project:
    """Proje veri yapısı."""
    id: int
    title: str
    type: str  # "interim" (ARA) veya "final" (BITIRME)
    ps_id: int  # Proje Sorumlusu (PS) - sabit, değiştirilemez
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
    type: str  # "instructor" veya "assistant"
    
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
    ps_id: int      # Proje Sorumlusu (sabit)
    j1_id: int      # Jüri 1 (karar değişkeni)
    j2_label: str = "[Arastirma Gorevlisi]"  # Jüri 2 (her zaman placeholder)
    
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
class ACOSolution:
    """ACO çözüm yapısı."""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    
    # Amaç değerleri
    h1_gap_penalty: float = 0.0
    h2_workload_penalty: float = 0.0
    h3_class_change_penalty: float = 0.0
    h4_class_load_penalty: float = 0.0
    total_cost: float = float('inf')
    
    # Geçerlilik
    is_feasible: bool = True
    constraint_violations: int = 0
    
    def copy(self) -> 'ACOSolution':
        """Derin kopya oluştur."""
        new_sol = ACOSolution(
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
        return new_sol
    
    def get_assignment(self, project_id: int) -> Optional[ProjectAssignment]:
        """Belirli bir proje için atamayı getir."""
        for a in self.assignments:
            if a.project_id == project_id:
                return a
        return None


# ============================================================================
# PHEROMONE MATRIX
# ============================================================================

class PheromoneMatrix:
    """
    Feromon matrisi yönetimi.
    
    İki tip feromon matrisi:
    1. project_class_pheromone[p][c]: Proje p'nin sınıf c'ye atanması için feromon
    2. project_jury_pheromone[p][j]: Proje p'ye jüri j atanması için feromon
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor],
        config: ACOConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece öğretim görevlileri (asistanlar hariç)
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
        
        self.project_ids = [p.id for p in projects]
        
        # Feromon matrisleri
        self._init_pheromones()
    
    def _init_pheromones(self):
        """Feromon matrislerini başlat."""
        # Proje-Sınıf feromon matrisi
        self.project_class_pheromone: Dict[int, Dict[int, float]] = {}
        for p_id in self.project_ids:
            self.project_class_pheromone[p_id] = {}
            for c in range(self.config.class_count):
                # CRITICAL: Tüm sınıflar için eşit başlangıç feromon değeri
                # Bu, tüm sınıfların eşit şansı olmasını sağlar
                self.project_class_pheromone[p_id][c] = self.config.initial_pheromone
        
        # Proje-Jüri feromon matrisi
        self.project_jury_pheromone: Dict[int, Dict[int, float]] = {}
        for p_id in self.project_ids:
            self.project_jury_pheromone[p_id] = {}
            for j_id in self.faculty_ids:
                self.project_jury_pheromone[p_id][j_id] = self.config.initial_pheromone
    
    def get_class_pheromone(self, project_id: int, class_id: int) -> float:
        """Proje-sınıf feromon değerini getir."""
        return self.project_class_pheromone.get(project_id, {}).get(
            class_id, self.config.initial_pheromone
        )
    
    def get_jury_pheromone(self, project_id: int, jury_id: int) -> float:
        """Proje-jüri feromon değerini getir."""
        return self.project_jury_pheromone.get(project_id, {}).get(
            jury_id, self.config.initial_pheromone
        )
    
    def evaporate(self):
        """Feromon buharlaşması uygula."""
        rho = self.config.evaporation_rate
        
        # Proje-Sınıf feromonları
        for p_id in self.project_ids:
            for c in range(self.config.class_count):
                current = self.project_class_pheromone[p_id][c]
                new_value = (1 - rho) * current
                self.project_class_pheromone[p_id][c] = max(
                    self.config.min_pheromone, new_value
                )
        
        # Proje-Jüri feromonları
        for p_id in self.project_ids:
            for j_id in self.faculty_ids:
                current = self.project_jury_pheromone[p_id][j_id]
                new_value = (1 - rho) * current
                self.project_jury_pheromone[p_id][j_id] = max(
                    self.config.min_pheromone, new_value
                )
    
    def deposit(self, solution: ACOSolution, amount: float):
        """
        Çözüm yoluna feromon bırak.
        
        Args:
            solution: Çözüm
            amount: Bırakılacak feromon miktarı (genellikle Q / cost)
        """
        for assignment in solution.assignments:
            # Sınıf feromonunu güncelle
            p_id = assignment.project_id
            c_id = assignment.class_id
            j1_id = assignment.j1_id
            
            if p_id in self.project_class_pheromone:
                current = self.project_class_pheromone[p_id].get(c_id, 0)
                new_value = current + amount
                self.project_class_pheromone[p_id][c_id] = min(
                    self.config.max_pheromone, new_value
                )
            
            # Jüri feromonunu güncelle
            if p_id in self.project_jury_pheromone and j1_id in self.faculty_ids:
                current = self.project_jury_pheromone[p_id].get(j1_id, 0)
                new_value = current + amount
                self.project_jury_pheromone[p_id][j1_id] = min(
                    self.config.max_pheromone, new_value
                )
    
    def update_class_count(self, new_class_count: int):
        """Sınıf sayısı değiştiğinde feromon matrisini güncelle."""
        self.config.class_count = new_class_count
        
        # Yeni sınıflar için feromon ekle
        for p_id in self.project_ids:
            for c in range(new_class_count):
                if c not in self.project_class_pheromone[p_id]:
                    self.project_class_pheromone[p_id][c] = self.config.initial_pheromone


# ============================================================================
# PENALTY CALCULATOR
# ============================================================================

class ACOPenaltyCalculator:
    """
    ACO için ceza hesaplayıcı - SA'daki SAPenaltyCalculator'a uygun.
    
    Implements (SA'daki gibi):
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
        config: ACOConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Gerçek öğretim görevlileri (asistanlar hariç)
        self.faculty_instructors = {
            i.id: i for i in instructors 
            if i.type == "instructor"
        }
        
        # Ortalama iş yükü hesapla
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
    
    def calculate_total_cost(self, solution: ACOSolution) -> float:
        """
        Toplam maliyeti hesapla - SA'daki gibi.
        
        Cost = C1*H1 + C2*H2 + C3*H3 + C4*H4 + C5*H5 + C6*H6 + C7*H7 + Uniform_Distribution_Penalty
        """
        h1 = self.calculate_h1_time_penalty(solution)
        h2 = self.calculate_h2_workload_penalty(solution)
        h3 = self.calculate_h3_class_change_penalty(solution)
        h4 = self.calculate_h4_class_load_penalty(solution)
        h5 = self.calculate_continuity_penalty(solution)
        h6 = self.calculate_timeslot_conflict_penalty(solution)
        h7 = self.calculate_unused_class_penalty(solution)
        uniform_penalty = self.calculate_uniform_distribution_penalty(solution)
        
        # Değerleri kaydet
        solution.h1_gap_penalty = h1
        solution.h2_workload_penalty = h2
        solution.h3_class_change_penalty = h3
        solution.h4_class_load_penalty = h4
        
        total = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3 +
            self.config.weight_h4 * h4 +
            self.config.weight_continuity * h5 +
            self.config.weight_timeslot_conflict * h6 +
            self.config.weight_unused_class * h7 +
            self.config.weight_uniform_distribution * uniform_penalty
        )
        
        solution.total_cost = total
        return total
    
    def calculate_uniform_distribution_penalty(self, solution: ACOSolution) -> float:
        """
        Uniform dağılım cezası (±3 bandı dışındaki sınıflar için).
        
        CRITICAL: Her sınıftaki proje sayısı, ortalama ±3 bandı içinde olmalı.
        """
        num_projects = len(solution.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = num_projects / solution.class_count
        tolerance = self.config.uniform_distribution_tolerance
        
        # Sınıf yüklerini hesapla
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 1
        
        # ±3 bandı dışındaki sınıflar için ceza
        total_penalty = 0.0
        for class_id in range(solution.class_count):
            load = class_loads.get(class_id, 0)
            deviation = abs(load - target_per_class)
            
            if deviation > tolerance:
                # Band dışında - karesel ceza
                penalty = (deviation - tolerance) ** 2
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h1_time_penalty(self, solution: ACOSolution) -> float:
        """
        H1: Time/Gap penalty for non-consecutive tasks - SA'daki gibi.
        
        Binary mode: 1 if not consecutive, 0 otherwise
        GAP_PROPORTIONAL mode: gap size as penalty
        """
        total_penalty = 0.0
        
        # Build task matrix for each instructor - SA'daki gibi
        instructor_tasks = self._build_instructor_task_matrix(solution)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Sort by timeslot (class_id * 100 + order) - SA'daki gibi
            tasks.sort(key=lambda x: x['class_id'] * 100 + x['order'])
            
            # Calculate gap penalties between consecutive tasks - SA'daki gibi
            for i in range(len(tasks) - 1):
                current = tasks[i]
                next_task = tasks[i + 1]
                
                # Check if same class and consecutive - SA'daki gibi
                if current['class_id'] == next_task['class_id']:
                    gap = next_task['order'] - current['order'] - 1
                    if gap > 0:
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1
                        else:  # GAP_PROPORTIONAL
                            total_penalty += gap
                else:
                    # Different class - always penalty - SA'daki gibi
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += 1
                    else:
                        # Calculate equivalent gap - SA'daki gibi
                        total_penalty += 2  # Cross-class penalty
        
        return total_penalty
    
    def calculate_h1_gap_penalty(self, solution: ACOSolution) -> float:
        """Alias for calculate_h1_time_penalty for backward compatibility"""
        return self.calculate_h1_time_penalty(solution)
        """
        H1: Zaman/GAP cezası.
        
        Binary mod: Ardışık değilse 1 ceza
        GAP_PROPORTIONAL mod: Boşluk sayısı kadar ceza
        """
        total_penalty = 0.0
        
        # Her öğretim görevlisi için görev matrisini oluştur
        instructor_tasks = self._build_instructor_task_matrix(solution)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Timeslot'a göre sırala (class_id * 100 + order)
            tasks.sort(key=lambda x: x['class_id'] * 100 + x['order'])
            
            # Ardışık görevler arasındaki boşlukları hesapla
            for i in range(len(tasks) - 1):
                current = tasks[i]
                next_task = tasks[i + 1]
                
                # Aynı sınıfta mı ve ardışık mı kontrol et
                if current['class_id'] == next_task['class_id']:
                    gap = next_task['order'] - current['order'] - 1
                    if gap > 0:
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1
                        else:  # GAP_PROPORTIONAL
                            total_penalty += gap
                else:
                    # Farklı sınıf - her zaman ceza
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += 1
                    else:
                        # Çapraz sınıf cezası
                        total_penalty += 2
        
        return total_penalty
    
    def calculate_h2_workload_penalty(self, solution: ACOSolution) -> float:
        """
        H2: İş yükü uniformite cezası.
        
        Her öğretim görevlisi için:
        penalty = max(0, |Load(h) - AvgLoad| - 2)
        """
        total_penalty = 0.0
        
        # Öğretim görevlisi başına iş yükünü say
        workloads = defaultdict(int)
        for assignment in solution.assignments:
            workloads[assignment.ps_id] += 1  # PS rolü
            workloads[assignment.j1_id] += 1  # J1 rolü
        
        # Her öğretim görevlisi için ceza hesapla
        for instructor_id in self.faculty_instructors.keys():
            load = workloads.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            penalty = max(0, deviation - self.config.workload_soft_band)
            total_penalty += penalty
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, solution: ACOSolution) -> float:
        """
        H3: Class change penalty - SA'daki gibi.
        
        For each instructor:
        penalty = max(0, NumberOfClasses(h) - 2)^2 * 5
        """
        total_penalty = 0.0
        
        # Find classes used by each instructor - SA'daki gibi
        instructor_classes = defaultdict(set)
        for assignment in solution.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty_instructors.keys():
            class_count = len(instructor_classes.get(instructor_id, set()))
            if class_count > 2:
                # Squared penalty for excessive class changes - SA'daki gibi
                penalty = (class_count - 2) ** 2 * 5
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h4_class_load_penalty(self, solution: ACOSolution) -> float:
        """
        H4: Class load balance penalty - SA'daki gibi.
        
        Each class should have approximately equal number of projects.
        CRITICAL: Kullanilmayan siniflar icin COK AGIR ceza (HARD KISIT)!
        """
        total_penalty = 0.0
        
        num_projects = len(solution.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = num_projects / solution.class_count
        
        # Count projects per class - SA'daki gibi
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 1
        
        # Kullanilmayan siniflar icin COK AGIR ceza (HARD KISIT) - SA'daki gibi
        unused_class_penalty = 0.0
        for class_id in range(solution.class_count):
            load = class_loads.get(class_id, 0)
            if load == 0:
                # Kullanilmayan sinif icin cok agir ceza - SA'daki gibi
                unused_class_penalty += 1000.0  # Cok agir ceza
            else:
                # Normal yuk dengesi cezasi - SA'daki gibi
                penalty = abs(load - target_per_class)
                total_penalty += penalty
        
        # Kullanilmayan sinif cezasi ekle - SA'daki gibi
        total_penalty += unused_class_penalty
        
        return total_penalty
    
    def calculate_unused_class_penalty(self, solution: ACOSolution) -> float:
        """
        H7: Unused class penalty (HARD constraint) - SA'daki gibi.
        
        All specified classes must be used.
        CRITICAL: This is a HARD CONSTRAINT - unused classes are NOT allowed!
        """
        used_classes = set()
        for assignment in solution.assignments:
            used_classes.add(assignment.class_id)
        
        unused_count = solution.class_count - len(used_classes)
        # EXTREMELY high penalty - squared for unused classes - SA'daki gibi
        # This makes solutions with unused classes completely unacceptable
        if unused_count > 0:
            return unused_count * unused_count * 1000000.0  # SA'daki gibi çok daha yüksek ceza
        return 0.0
    
    def calculate_continuity_penalty(self, solution: ACOSolution) -> float:
        """
        H5: Continuity penalty - SA'daki gibi.
        
        Penalizes instructors who have fragmented schedules
        (multiple separate blocks instead of continuous tasks).
        """
        total_penalty = 0.0
        
        # Build task matrix - SA'daki gibi
        instructor_tasks = self._build_instructor_task_matrix(solution)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Group tasks by class - SA'daki gibi
            tasks_by_class = defaultdict(list)
            for task in tasks:
                tasks_by_class[task['class_id']].append(task)
            
            # Count blocks per class - SA'daki gibi
            for class_id, class_tasks in tasks_by_class.items():
                if len(class_tasks) <= 1:
                    continue
                
                # Sort by order - SA'daki gibi
                class_tasks.sort(key=lambda x: x['order'])
                
                # Count separate blocks - SA'daki gibi
                blocks = 1
                for i in range(len(class_tasks) - 1):
                    if class_tasks[i + 1]['order'] - class_tasks[i]['order'] > 1:
                        blocks += 1
                
                # Penalty for extra blocks - SA'daki gibi
                if blocks > 1:
                    total_penalty += (blocks - 1) ** 2 * 10
        
        return total_penalty
    
    def calculate_timeslot_conflict_penalty(self, solution: ACOSolution) -> float:
        """
        H6: Timeslot conflict penalty (HARD constraint) - SA'daki gibi.
        
        Penalizes instructors who have multiple tasks in the same timeslot.
        """
        total_penalty = 0.0
        
        # Build timeslot occupancy - SA'daki gibi
        # Key: (instructor_id, class_id, order) -> count
        timeslot_occupancy = defaultdict(int)
        
        for assignment in solution.assignments:
            # PS occupancy - SA'daki gibi
            key_ps = (assignment.ps_id, assignment.class_id, assignment.order_in_class)
            timeslot_occupancy[key_ps] += 1
            
            # J1 occupancy - SA'daki gibi
            key_j1 = (assignment.j1_id, assignment.class_id, assignment.order_in_class)
            timeslot_occupancy[key_j1] += 1
        
        # Check for conflicts (any instructor in multiple places at same time) - SA'daki gibi
        instructor_timeslots = defaultdict(lambda: defaultdict(int))
        for assignment in solution.assignments:
            slot_key = (assignment.class_id, assignment.order_in_class)
            instructor_timeslots[assignment.ps_id][slot_key] += 1
            instructor_timeslots[assignment.j1_id][slot_key] += 1
        
        # Global conflict check (same timeslot across different classes) - SA'daki gibi
        for instructor_id in instructor_timeslots.keys():
            orders_per_class = defaultdict(list)
            for (class_id, order) in instructor_timeslots[instructor_id].keys():
                orders_per_class[order].append(class_id)
            
            for order, classes in orders_per_class.items():
                if len(classes) > 1:
                    # Same order in multiple classes = conflict - SA'daki gibi
                    total_penalty += (len(classes) - 1) * 1000
        
        return total_penalty
    
    def has_unused_classes(self, solution: ACOSolution) -> bool:
        """Kullanılmayan sınıf var mı kontrol et."""
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 1
        
        for class_id in range(solution.class_count):
            if class_loads.get(class_id, 0) == 0:
                return True
        return False
    
    def _build_instructor_task_matrix(self, solution: ACOSolution) -> Dict[int, List[Dict]]:
        """
        Her öğretim görevlisi için görev matrisi oluştur.
        
        Returns:
            {instructor_id: [{class_id, order, project_id, role}, ...]}
        """
        instructor_tasks: Dict[int, List[Dict]] = defaultdict(list)
        
        for assignment in solution.assignments:
            # PS görevi
            instructor_tasks[assignment.ps_id].append({
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'project_id': assignment.project_id,
                'role': 'PS'
            })
            
            # J1 görevi
            instructor_tasks[assignment.j1_id].append({
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'project_id': assignment.project_id,
                'role': 'J1'
            })
        
        return instructor_tasks
    
    def get_heuristic_value(
        self, 
        project: Project, 
        class_id: int, 
        jury_id: int,
        current_state: Dict
    ) -> float:
        """
        Heuristik değer hesapla (η).
        
        Daha iyi seçimler için daha yüksek değer.
        """
        eta = 1.0
        
        # 1. İş yükü dengesi heuristiği
        workloads = current_state.get('workloads', defaultdict(int))
        jury_load = workloads.get(jury_id, 0)
        ps_load = workloads.get(project.ps_id, 0)
        
        # Ortalamaya yakın iş yükü tercih et
        jury_deviation = abs(jury_load - self.avg_workload)
        ps_deviation = abs(ps_load - self.avg_workload)
        
        if jury_deviation < 2:
            eta += 0.5
        elif jury_deviation > 4:
            eta -= 0.3
        
        # 2. Sınıf dengesi heuristiği
        class_loads = current_state.get('class_loads', defaultdict(int))
        class_load = class_loads.get(class_id, 0)
        target_per_class = len(self.projects) / self.config.class_count
        
        if class_load < target_per_class:
            eta += 0.3
        elif class_load > target_per_class + 2:
            eta -= 0.2
        
        # 3. Ardışıklık heuristiği
        instructor_last_class = current_state.get('instructor_last_class', {})
        ps_last = instructor_last_class.get(project.ps_id)
        jury_last = instructor_last_class.get(jury_id)
        
        if ps_last == class_id:
            eta += 0.4  # PS aynı sınıfta kalmayı tercih et
        if jury_last == class_id:
            eta += 0.4  # Jüri aynı sınıfta kalmayı tercih et
        
        return max(0.1, eta)  # Minimum değer


# ============================================================================
# REPAIR MECHANISM
# ============================================================================

class ACORepairMechanism:
    """
    ACO çözümleri için onarım mekanizması - SA'daki SARepairMechanism'a uygun.
    
    Repairs (SA'daki gibi):
    1. PS assignments (must match project's advisor)
    2. J1 != PS constraint
    3. Missing J1 assignments
    4. Back-to-back class ordering
    5. Timeslot conflicts
    6. Missing projects
    7. Priority order (ARA/BITIRME)
    8. Workload hard limits
    9. All classes used - CRITICAL (agresif)
    10. J2 placeholder garantisi
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: ACOConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece öğretim görevlileri
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    def repair(self, solution: ACOSolution) -> None:
        """
        Çözümü onar - SA'daki gibi agresif ve çok katmanlı.
        
        Sırayla (SA'daki gibi):
        1. PS assignments
        2. J2 placeholder'ı düzelt (her projede olmalı)
        3. J1 != PS
        4. Missing J1
        5. Back-to-back ordering
        6. Timeslot conflicts - CRITICAL (run first)
        7. Missing projects
        8. Priority order
        9. Workload hard limits
        10. All classes used - CRITICAL (agresif - SA'daki gibi)
        11. Re-check timeslot conflicts after all class changes
        12. Final check for all classes (tekrar - SA'daki gibi)
        13. Final timeslot conflict check
        14. ABSOLUTE FINAL: Verify all classes used - MANDATORY (SA'daki gibi)
        15. Uniform dağılımı düzelt (±3 bandı)
        """
        # 1. PS assignments - SA'daki gibi
        self._repair_ps_assignments(solution)
        
        # 2. J2 placeholder
        self._fix_j2_placeholder(solution)
        
        # 3. J1 != PS
        self._repair_j1_not_ps(solution)
        
        # 4. Missing J1
        self._repair_missing_j1(solution)
        
        # 5. Back-to-back ordering
        self._repair_class_ordering(solution)
        
        # 6. Timeslot conflicts - CRITICAL (run first) - SA'daki gibi
        self._repair_timeslot_conflicts(solution)
        
        # 7. Missing projects
        self._repair_missing_projects(solution)
        
        # 8. Priority order
        self._repair_priority_order(solution)
        
        # 9. Workload hard limits
        if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
            self._repair_workload_hard_limit(solution)
        
        # 10. All classes used - CRITICAL (SA'daki gibi agresif)
        self._repair_all_classes_used(solution)
        
        # 11. Re-check timeslot conflicts after all class changes - SA'daki gibi
        self._repair_timeslot_conflicts(solution)
        
        # 12. Final check for all classes (tekrar - SA'daki gibi)
        self._repair_all_classes_used(solution)
        
        # 13. Final timeslot conflict check - SA'daki gibi
        self._repair_timeslot_conflicts(solution)
        
        # 14. ABSOLUTE FINAL: Verify all classes used - MANDATORY (SA'daki gibi)
        # SA'daki gibi while dongusu ile kontrol
        final_iterations = 0
        while final_iterations < 50:  # Ekstra kontrol - SA'daki gibi
            class_counts = defaultdict(int)
            for a in solution.assignments:
                class_counts[a.class_id] += 1
            
            used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
            if used_count == solution.class_count:
                break  # Tum siniflar kullaniliyor
            
            # Force fill unused classes - CRITICAL - SA'daki gibi
            unused = [c for c in range(solution.class_count) if c not in class_counts]
            if not unused:
                        break
            
            for unused_class in unused:
                # Find assignment in most loaded class - SA'daki gibi
                if class_counts:
                    max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
                    assignments_in_max = [
                        a for a in solution.assignments
                        if a.class_id == max_class
                    ]
                    if assignments_in_max:
                        assignment = assignments_in_max[-1]  # Take last
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        class_counts[max_class] -= 1
                        class_counts[unused_class] = 1
                        self._repair_class_ordering(solution)
            else:
                    # No assignments - distribute first one - SA'daki gibi
                    if solution.assignments:
                        solution.assignments[0].class_id = unused_class
                        solution.assignments[0].order_in_class = 0
            
            final_iterations += 1
        
        # 15. Uniform dağılımı düzelt (±3 bandı)
        self._fix_uniform_distribution(solution)
    
    def _fix_j2_placeholder(self, solution: ACOSolution) -> None:
        """J2 placeholder'ı düzelt - her projede olmalı."""
        for assignment in solution.assignments:
            if assignment.j2_label != self.config.j2_placeholder:
                assignment.j2_label = self.config.j2_placeholder
    
    def _repair_ps_assignments(self, solution: ACOSolution) -> None:
        """Ensure PS matches project's advisor - SA'daki gibi"""
        for assignment in solution.assignments:
            project = self.projects.get(assignment.project_id)
            if project and assignment.ps_id != project.ps_id:
                assignment.ps_id = project.ps_id
    
    def _repair_j1_not_ps(self, solution: ACOSolution) -> None:
        """Ensure J1 != PS for all assignments - SA'daki gibi"""
        for assignment in solution.assignments:
            if assignment.j1_id == assignment.ps_id:
                # Find alternative J1 - SA'daki gibi
                available = [
                    i for i in self.faculty_ids 
                    if i != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_missing_j1(self, solution: ACOSolution) -> None:
        """Ensure all assignments have valid J1 - SA'daki gibi"""
        for assignment in solution.assignments:
            if assignment.j1_id not in self.faculty_ids or assignment.j1_id == assignment.ps_id:
                available = [
                    i for i in self.faculty_ids 
                    if i != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_timeslot_conflicts(self, solution: ACOSolution) -> None:
        """
        Resolve timeslot conflicts - CRITICAL HARD CONSTRAINT - SA'daki gibi.
        
        An instructor cannot be in multiple places at the same time.
        Same order_in_class across ANY classes means same timeslot!
        """
        max_iterations = 200  # SA'daki gibi
        
        for iteration in range(max_iterations):
            # Find conflicts - SA'daki gibi
            conflicts = self._find_timeslot_conflicts(solution)
            if not conflicts:
                return  # No conflicts
            
            # Resolve conflicts one by one - SA'daki gibi
            for conflict in conflicts:
                self._resolve_timeslot_conflict(solution, conflict)
                break  # Re-check after each resolution
    
    def _find_timeslot_conflicts(self, solution: ACOSolution) -> List[Dict]:
        """
        Find all timeslot conflicts - SA'daki gibi.
        
        IMPORTANT: Same order_in_class across different classes = SAME TIMESLOT!
        An instructor with assignments in different classes but same order
        has a conflict (they can't be in two places at once).
        """
        conflicts = []
        
        # Build instructor schedule: instructor_id -> order -> list of (assignment, class_id) - SA'daki gibi
        instructor_schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in solution.assignments:
            # PS role - SA'daki gibi
            instructor_schedule[assignment.ps_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'PS'
            })
            # J1 role - SA'daki gibi
            instructor_schedule[assignment.j1_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'J1'
            })
        
        # Find conflicts: multiple assignments at same timeslot (order) - SA'daki gibi
        for instructor_id, orders in instructor_schedule.items():
            for order, entries in orders.items():
                if len(entries) > 1:
                    # Check if they are in DIFFERENT classes (real conflict) - SA'daki gibi
                    classes_at_this_slot = set(e['class_id'] for e in entries)
                    if len(classes_at_this_slot) > 1:
                        # CONFLICT: Instructor in multiple classes at same time - SA'daki gibi
                        conflicts.append({
                            'instructor_id': instructor_id,
                            'order': order,
                            'entries': entries,
                            'classes': classes_at_this_slot
                        })
        
        return conflicts
    
    def _resolve_timeslot_conflict(self, solution: ACOSolution, conflict: Dict) -> None:
        """
        Resolve a single timeslot conflict - SA'daki gibi.
        
        Strategy:
        1. If instructor is J1, try to reassign to different instructor
        2. If instructor is PS, try to move project to different timeslot
        3. As last resort, move project to end of a different class
        """
        instructor_id = conflict['instructor_id']
        entries = conflict['entries']
        
        # Keep first entry, fix others - SA'daki gibi
        for entry in entries[1:]:
            assignment = entry['assignment']
            role = entry['role']
            
            if role == 'J1':
                # Try to find a different J1 who is NOT busy at this timeslot - SA'daki gibi
                available = self._find_available_j1_at_slot(
                    solution, assignment, assignment.order_in_class
                )
                if available:
                    assignment.j1_id = random.choice(available)
                    continue
            
            # Need to move the project to a different timeslot - SA'daki gibi
            # Find a slot where this instructor is free
            new_slot = self._find_free_slot_for_instructor(solution, instructor_id, assignment)
            if new_slot:
                old_class = assignment.class_id
                assignment.class_id = new_slot['class_id']
                assignment.order_in_class = new_slot['order']
                self._repair_class_ordering(solution)
            else:
                # Last resort: move to end of least loaded class - SA'daki gibi
                class_loads = defaultdict(int)
                for a in solution.assignments:
                    class_loads[a.class_id] += 1
                
                min_class = min(range(solution.class_count), key=lambda c: class_loads.get(c, 0))
                assignment.class_id = min_class
                assignment.order_in_class = class_loads.get(min_class, 0)
                
                # Try to reassign J1 if still conflicting - SA'daki gibi
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
        solution: ACOSolution, 
        assignment: ProjectAssignment, 
        order: int
    ) -> List[int]:
        """Find J1 candidates who are free at the given timeslot - SA'daki gibi"""
        # Find all instructors busy at this timeslot - SA'daki gibi
        busy_at_slot = set()
        for a in solution.assignments:
            if a.order_in_class == order:
                busy_at_slot.add(a.ps_id)
                busy_at_slot.add(a.j1_id)
        
        # Find available instructors - SA'daki gibi
        available = [
            i for i in self.faculty_ids
            if i != assignment.ps_id and i not in busy_at_slot
        ]
        
        return available
    
    def _find_free_slot_for_instructor(
        self, 
        solution: ACOSolution, 
        instructor_id: int, 
        assignment: ProjectAssignment
    ) -> Optional[Dict]:
        """Find a timeslot where the instructor is free - SA'daki gibi"""
        # Build instructor's schedule - SA'daki gibi
        busy_orders = set()
        for a in solution.assignments:
            if a.ps_id == instructor_id or a.j1_id == instructor_id:
                busy_orders.add(a.order_in_class)
        
        # Find class counts - SA'daki gibi
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        # Find first free slot - SA'daki gibi
        max_order = max(class_counts.values()) if class_counts else 0
        
        for order in range(max_order + 5):  # Check a few slots beyond current max - SA'daki gibi
            if order not in busy_orders:
                # Find a class where we can add at this order - SA'daki gibi
                for class_id in range(solution.class_count):
                    current_count = class_counts.get(class_id, 0)
                    if order <= current_count:  # Can fit here
                        return {'class_id': class_id, 'order': order}
        
        return None
    
    def _repair_missing_projects(self, solution: ACOSolution) -> None:
        """Add any missing projects - SA'daki gibi"""
        project_list = list(self.projects.values())
        assigned_ids = {a.project_id for a in solution.assignments}
        
        for project in project_list:
            if project.id not in assigned_ids:
                # Find least loaded class - SA'daki gibi
                class_loads = defaultdict(int)
                for a in solution.assignments:
                    class_loads[a.class_id] += 1
                
                min_class = min(
                    range(solution.class_count),
                    key=lambda c: class_loads.get(c, 0)
                )
                
                # Create assignment - SA'daki gibi
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
    
    def _repair_priority_order(self, solution: ACOSolution) -> None:
        """Ensure priority order (ARA_ONCE / BITIRME_ONCE) - SA'daki gibi"""
        if self.config.priority_mode == PriorityMode.ESIT:
            return
        
        # Separate by type - SA'daki gibi
        interim = []
        final = []
        for a in solution.assignments:
            project = self.projects.get(a.project_id)
            if project:
                if project.type in ["INTERIM", "interim", "ARA", "ara"]:
                    interim.append(a)
                else:
                    final.append(a)
        
        # Determine order - SA'daki gibi
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            first_group = interim
            second_group = final
        else:  # BITIRME_ONCE
            first_group = final
            second_group = interim
        
        # Reassign to classes - SA'daki gibi
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
    
    def _repair_workload_hard_limit(self, solution: ACOSolution) -> None:
        """Enforce hard workload limit B_max - SA'daki gibi"""
        # Average workload
        num_projects = len(solution.assignments)
        num_faculty = len(self.faculty_ids)
        avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
        
        max_iterations = 50  # SA'daki gibi
        
        for _ in range(max_iterations):
            # Count workloads - SA'daki gibi
            workloads = defaultdict(int)
            for a in solution.assignments:
                workloads[a.ps_id] += 1
                workloads[a.j1_id] += 1
            
            # Find overloaded instructors - SA'daki gibi
            overloaded = [
                i for i in self.faculty_ids
                if abs(workloads.get(i, 0) - avg_workload) > self.config.workload_hard_limit
            ]
            
            if not overloaded:
                                break
                            
            # Try to balance - SA'daki gibi
            instructor_id = overloaded[0]
            
            # Find assignments where this instructor is J1 - SA'daki gibi
            j1_assignments = [
                a for a in solution.assignments 
                if a.j1_id == instructor_id
            ]
            
            if j1_assignments:
                # Reassign one J1 - SA'daki gibi
                assignment = random.choice(j1_assignments)
                
                # Find underloaded instructor - SA'daki gibi
                underloaded = [
                    i for i in self.faculty_ids
                    if i != assignment.ps_id and 
                    workloads.get(i, 0) < avg_workload
                ]
                
                if underloaded:
                    assignment.j1_id = random.choice(underloaded)
    
    def _repair_all_classes_used(self, solution: ACOSolution) -> None:
        """
        Ensure ALL classes are used - CRITICAL HARD CONSTRAINT - SA'daki gibi.
        
        Every single classroom MUST have at least one project assigned.
        Bu metod TUM siniflarin kullanildigindan %100 emin olur.
        SA'daki gibi while dongusu ile cok agresif.
        """
        max_iterations = 200  # SA'daki gibi
        iteration = 0
        
        while iteration < max_iterations:
            # Count projects per class - SA'daki gibi
            class_counts = defaultdict(int)
            for a in solution.assignments:
                class_counts[a.class_id] += 1
            
            # Find unused classes - SA'daki gibi
            unused_classes = [
                c for c in range(solution.class_count)
                if class_counts.get(c, 0) == 0
            ]
            
            if not unused_classes:
                # Tum siniflar kullaniliyor - kontrol et - SA'daki gibi
                used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
                if used_count == solution.class_count:
                    return  # Gercekten tum siniflar kullaniliyor
                # Degilse devam et
            
            # En yuklu sinifi bul - SA'daki gibi
            if not class_counts:
                # Hic sinif kullanilmiyor, projeleri dagit - SA'daki gibi
                for i, assignment in enumerate(solution.assignments):
                    class_id = i % solution.class_count
                    assignment.class_id = class_id
                    assignment.order_in_class = i // solution.class_count
                self._repair_class_ordering(solution)
                return
            
            max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
            max_count = class_counts[max_class]
            
            # Eger en yuklu sinifta yeterli proje varsa, kullanilmayan siniflara dagit - SA'daki gibi
            if max_count > 1:
                # En yuklu siniftaki projeleri al - SA'daki gibi
                projects_to_move = [
                    a for a in solution.assignments 
                    if a.class_id == max_class
                ]
                
                # Kullanilmayan siniflara dagit (en az yuklu siniftan basla) - SA'daki gibi
                for unused_class in unused_classes:
                    if not projects_to_move:
                                break
                        
                    # En sondan proje al (daha az kritik) - SA'daki gibi
                    project_to_move = projects_to_move.pop()
                    project_to_move.class_id = unused_class
                    
                    # Yeni sinifin sonuna ekle - SA'daki gibi
                    new_class_projects = [
                        x for x in solution.assignments
                        if x.class_id == unused_class and x.project_id != project_to_move.project_id
                    ]
                    project_to_move.order_in_class = len(new_class_projects)
                    
                    # Siralari duzelt - SA'daki gibi
                    self._repair_class_ordering(solution)
            else:
                # En yuklu sinifta sadece 1 proje var, baska siniftan al - SA'daki gibi
                # En az yuklu sinifi bul (ama en az 1 proje olmali) - SA'daki gibi
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
                        project_to_move = projects_in_min[-1]  # En sondan al - SA'daki gibi
                        unused_class = unused_classes[0]
                        
                        project_to_move.class_id = unused_class
                        
                        # Yeni sinifin sonuna ekle - SA'daki gibi
                        new_class_projects = [
                            x for x in solution.assignments
                            if x.class_id == unused_class and x.project_id != project_to_move.project_id
                        ]
                        project_to_move.order_in_class = len(new_class_projects)
                        
                        # Siralari duzelt - SA'daki gibi
                        self._repair_class_ordering(solution)
                else:
                    # Her sinifta sadece 1 proje var, dagit - SA'daki gibi
                    all_projects = list(solution.assignments)
                    for i, unused_class in enumerate(unused_classes):
                        if i < len(all_projects):
                            project_to_move = all_projects[i]
                            project_to_move.class_id = unused_class
                            project_to_move.order_in_class = 0
                            self._repair_class_ordering(solution)
            
            iteration += 1
        
        # Final forced distribution if still unused classes - SA'daki gibi
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # AGGRESSIVE: Take projects from overloaded classes and distribute - SA'daki gibi
            # Sort all assignments by class load - SA'daki gibi
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
                assignments_by_class[a.class_id].append(a)
            
            # Sort classes by load (most loaded first) - SA'daki gibi
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                # Try to move from most loaded classes - SA'daki gibi
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    projects_in_max = assignments_by_class[max_class]
                    if len(projects_in_max) > 1:
                        # Move last project - SA'daki gibi
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
                    # Force move even from single-project classes - SA'daki gibi
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
        
        # ABSOLUTE FINAL CHECK - redistribute if still unused - SA'daki gibi
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # LAST RESORT: Redistribute ALL projects evenly - SA'daki gibi
            all_assignments = list(solution.assignments)
            for i, assignment in enumerate(all_assignments):
                target_class = i % solution.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // solution.class_count
            
            self._repair_class_ordering(solution)
    
    def _fix_unused_classes(self, solution: ACOSolution) -> None:
        """Alias for _repair_all_classes_used for backward compatibility"""
        self._repair_all_classes_used(solution)
        """
        Tüm sınıfların kullanılmasını sağla - AGGRESIF YAKLAŞIM.
        
        CRITICAL: Tüm sınıflar MUTLAKA kullanılmalı!
        Simulated Annealing'daki gibi while döngüsü ile çok agresif.
        """
        max_iterations = 200  # Simulated Annealing'daki gibi
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
                # Tüm sınıflar kullanılıyor - kontrol et
                used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
                if used_count == solution.class_count:
                    # Gerçekten tüm sınıflar kullanılıyor - sıralamayı düzelt ve çık
                    self._reorder_all_classes(solution)
                    return
                # Değilse devam et
            
            # En yüklü sınıfı bul
            if not class_counts:
                # Hiç sınıf kullanılmıyor, projeleri dağıt
                for i, assignment in enumerate(solution.assignments):
                    class_id = i % solution.class_count
                    assignment.class_id = class_id
                    assignment.order_in_class = i // solution.class_count
                self._reorder_all_classes(solution)
                return
            
            max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
            max_count = class_counts[max_class]
            
            # Eğer en yüklü sınıfta yeterli proje varsa, kullanılmayan sınıflara dağıt
            if max_count > 1:
                # En yüklü sınıftaki projeleri al
                projects_to_move = [
                    a for a in solution.assignments 
                    if a.class_id == max_class
                ]
                
                # Kullanılmayan sınıflara dağıt
                for unused_class in unused_classes:
                    if not projects_to_move:
                        break
                    
                    # En sondan proje al (daha az kritik)
                    project_to_move = projects_to_move.pop()
                    project_to_move.class_id = unused_class
                    
                    # Yeni sınıfın sonuna ekle
                    new_class_projects = [
                        x for x in solution.assignments
                        if x.class_id == unused_class and x.project_id != project_to_move.project_id
                    ]
                    project_to_move.order_in_class = len(new_class_projects)
                    
                    # Sıraları düzelt
                    self._reorder_all_classes(solution)
            else:
                # En yüklü sınıfta sadece 1 proje var, başka sınıftan al
                # En az yüklü sınıfı bul (ama en az 1 proje olmalı)
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
                        project_to_move = projects_in_min[-1]  # En sondan al
                        unused_class = unused_classes[0]
                        
                        project_to_move.class_id = unused_class
                        
                        # Yeni sınıfın sonuna ekle
                        new_class_projects = [
                            x for x in solution.assignments
                            if x.class_id == unused_class and x.project_id != project_to_move.project_id
                        ]
                        project_to_move.order_in_class = len(new_class_projects)
                        
                        # Sıraları düzelt
                        self._reorder_all_classes(solution)
                else:
                    # Her sınıfta sadece 1 proje var, dağıt
                    all_projects = list(solution.assignments)
                    for i, unused_class in enumerate(unused_classes):
                        if i < len(all_projects):
                            project_to_move = all_projects[i]
                            project_to_move.class_id = unused_class
                            project_to_move.order_in_class = 0
                            self._reorder_all_classes(solution)
            
            iteration += 1
        
        # Final forced distribution if still unused classes
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # AGGRESSIVE: Take projects from overloaded classes and distribute
            # Sort all assignments by class load
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
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
            
            self._reorder_all_classes(solution)
        
        # ABSOLUTE FINAL CHECK - redistribute if still unused
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # LAST RESORT: Redistribute ALL projects evenly
            all_assignments = list(solution.assignments)
            for i, assignment in enumerate(all_assignments):
                target_class = i % solution.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // solution.class_count
            
            self._reorder_all_classes(solution)
    
    def _repair_class_ordering(self, solution: ACOSolution) -> None:
        """Ensure back-to-back ordering within classes - SA'daki gibi"""
        for class_id in range(solution.class_count):
            class_assignments = [
                a for a in solution.assignments 
                if a.class_id == class_id
            ]
            class_assignments.sort(key=lambda x: x.order_in_class)
            
            for i, assignment in enumerate(class_assignments):
                assignment.order_in_class = i
    
    def _reorder_all_classes(self, solution: ACOSolution) -> None:
        """Alias for _repair_class_ordering for backward compatibility"""
        self._repair_class_ordering(solution)
    
    def _fix_uniform_distribution(self, solution: ACOSolution) -> None:
        """
        Uniform dağılımı düzelt (±3 bandı).
        
        CRITICAL: Her sınıftaki proje sayısı, ortalama ±3 bandı içinde olmalı.
        Maksimum yüklü sınıflardan minimum yüklü sınıflara proje taşır.
        """
        num_projects = len(solution.assignments)
        if num_projects == 0:
            return
        
        target_per_class = num_projects / solution.class_count
        tolerance = self.config.uniform_distribution_tolerance
        
        max_iterations = 100
        for iteration in range(max_iterations):
            # Sınıf yüklerini hesapla
            class_loads = defaultdict(int)
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
                class_loads[a.class_id] += 1
                assignments_by_class[a.class_id].append(a)
            
            # ±3 bandı dışındaki sınıfları bul
            overloaded_classes = []  # Bandın üstünde
            underloaded_classes = []  # Bandın altında
            
            for class_id in range(solution.class_count):
                load = class_loads.get(class_id, 0)
                deviation = load - target_per_class
                
                if deviation > tolerance:
                    overloaded_classes.append((class_id, load))
                elif deviation < -tolerance:
                    underloaded_classes.append((class_id, load))
            
            # Eğer tüm sınıflar ±3 bandı içindeyse, çık
            if not overloaded_classes and not underloaded_classes:
                break
            
            # Maksimum yüklü sınıflardan minimum yüklü sınıflara proje taşı
            if overloaded_classes and underloaded_classes:
                # En yüklü sınıfı bul
                overloaded_classes.sort(key=lambda x: x[1], reverse=True)
                max_class_id, max_load = overloaded_classes[0]
                
                # En az yüklü sınıfı bul
                underloaded_classes.sort(key=lambda x: x[1])
                min_class_id, min_load = underloaded_classes[0]
                
                # En yüklü sınıftan bir proje taşı
                if max_load > 1 and assignments_by_class[max_class_id]:
                    # Son projeyi taşı (daha az kritik)
                    assignment = assignments_by_class[max_class_id][-1]
                    old_class = assignment.class_id
                    assignment.class_id = min_class_id
                    assignment.order_in_class = len(assignments_by_class[min_class_id])
                    
                    # Güncelle
                    assignments_by_class[max_class_id].remove(assignment)
                    assignments_by_class[min_class_id].append(assignment)
                    
                    # Sıralamayı düzelt
                    self._reorder_all_classes(solution)
                else:
                    break
            else:
                # Sadece overloaded veya sadece underloaded varsa, çık
                break
        
        # Final: Tüm sınıfları yeniden sırala
        self._reorder_all_classes(solution)
    
    def _fix_back_to_back(self, solution: ACOSolution) -> None:
        """Back-to-back scheduling'i düzelt (sınıf içinde boşluk olmamalı)."""
        for class_id in range(solution.class_count):
            # Bu sınıftaki atamaları topla
            class_assignments = [
                a for a in solution.assignments if a.class_id == class_id
            ]
            
            # Sıraya göre sırala ve yeniden numaralandır
            class_assignments.sort(key=lambda x: x.order_in_class)
            for i, a in enumerate(class_assignments):
                a.order_in_class = i


# ============================================================================
# ANT CLASS
# ============================================================================

class Ant:
    """
    Tek bir karınca.
    
    Çözüm oluşturma mantığını içerir.
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: ACOConfig,
        pheromone_matrix: PheromoneMatrix,
        penalty_calculator: ACOPenaltyCalculator
    ):
        self.projects = list(projects)
        self.instructors = instructors
        self.config = config
        self.pheromone = pheromone_matrix
        self.penalty_calc = penalty_calculator
        
        # Sadece öğretim görevlileri
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
        
        self.solution: Optional[ACOSolution] = None
    
    def construct_solution(self) -> ACOSolution:
        """
        Çözüm oluştur - SA'daki build_initial_solution mantığını kullanarak.
        
        CRITICAL: Her sınıfın en az 1 proje almasını GARANTİ ET!
        SA'daki gibi agresif yaklaşım ile tüm sınıfların kullanılmasını sağla.
        
        Strateji (SA'daki gibi):
        1. Projeleri öncelik moduna göre sırala
        2. PS'lere göre grupla (continuity için)
        3. PHASE 1: İlk N projeyi (N = sınıf sayısı) her sınıfa 1'er tane yerleştir (MANDATORY)
        4. Kalan projeleri feromon + heuristik ile yerleştir (timeslot conflict'leri önleyerek)
        5. FINAL CHECK: Tüm sınıfların kullanıldığını garanti et (SA'daki gibi agresif)
        """
        solution = ACOSolution(class_count=self.config.class_count)
        
        # Projeleri öncelik moduna göre sırala - SA'daki gibi
        sorted_projects = self._sort_projects_by_priority()
        
        # Group by PS for continuity - SA'daki gibi
        ps_groups = defaultdict(list)
        for project in sorted_projects:
            ps_groups[project.ps_id].append(project)
        
        # Build class assignments - SA'daki gibi
        class_assignments = [[] for _ in range(self.config.class_count)]
        class_loads = [0] * self.config.class_count
        
        # Track used classes to ensure all are used - SA'daki gibi
        used_classes = set()
        ps_to_class = {}
        
        # PHASE 1: Force at least one project per class (MANDATORY) - SA'daki gibi
        all_projects = list(sorted_projects)
        
        if len(all_projects) >= self.config.class_count:
            # We have enough projects - assign one to each class - SA'daki gibi
            for class_id in range(self.config.class_count):
                project = all_projects[class_id]
                class_assignments[class_id].append(project)
                class_loads[class_id] += 1
                used_classes.add(class_id)
                ps_to_class[project.ps_id] = class_id
        else:
            # Not enough projects - distribute evenly - SA'daki gibi
            for i, project in enumerate(all_projects):
                class_id = i % self.config.class_count
                class_assignments[class_id].append(project)
                class_loads[class_id] += 1
                used_classes.add(class_id)
                if project.ps_id not in ps_to_class:
                    ps_to_class[project.ps_id] = class_id
        
        # Remaining projects - SA'daki gibi
        remaining_projects = all_projects[self.config.class_count:] if len(all_projects) > self.config.class_count else []
        
        # Track instructor schedules to avoid timeslot conflicts - SA'daki gibi
        instructor_schedule = defaultdict(lambda: defaultdict(set))  # instructor_id -> order -> set of class_ids
        
        # Durum takibi (ACO için)
        state = {
            'workloads': defaultdict(int),
            'class_loads': defaultdict(int),
            'instructor_last_class': {},
            'timeslot_usage': defaultdict(set),  # {(class, order): set(instructor_ids)}
            'used_classes': used_classes,
            'ps_to_class': ps_to_class
        }
        
        for project in remaining_projects:
            ps_id = project.ps_id
            
            # Try to keep same PS projects together - SA'daki gibi
            if ps_id in ps_to_class:
                preferred_class = ps_to_class[ps_id]
                # Check if PS is free at this class's next order - SA'daki gibi
                next_order = class_loads[preferred_class]
                if preferred_class not in instructor_schedule[ps_id][next_order]:
                    class_id = preferred_class
                else:
                    # PS busy, find alternative - SA'daki gibi
                    class_id = self._find_free_class_for_instructor(
                        ps_id, class_loads, instructor_schedule, used_classes
                    )
            else:
                # Prefer unused classes first - SA'daki gibi
                unused = [c for c in range(self.config.class_count) if c not in used_classes]
                if unused:
                    # ACO: Feromon + heuristik ile seç (ama unused'ları tercih et)
                    if unused:
                        # Unused sınıflar arasından feromon + heuristik ile seç
                        class_id = self._select_class_from_candidates(project, unused, state)
                    else:
                        class_id = min(range(self.config.class_count), key=lambda c: class_loads[c])
                else:
                    # All classes used, use ACO selection with uniform distribution
                    class_id = self._select_class_with_uniform_distribution(project, state)
                ps_to_class[ps_id] = class_id
            
            class_assignments[class_id].append(project)
            order = class_loads[class_id]
            class_loads[class_id] += 1
            used_classes.add(class_id)
            
            # Track PS schedule - SA'daki gibi
            instructor_schedule[ps_id][order].add(class_id)
            
            # Update state
            state['class_loads'][class_id] = class_loads[class_id]
            state['used_classes'] = used_classes
        
        # FINAL CHECK: Ensure ALL classes are used - MANDATORY - SA'daki gibi
        unused_classes = [c for c in range(self.config.class_count) if c not in used_classes]
        
        if unused_classes:
            # CRITICAL: Force distribution to unused classes - SA'daki gibi
            # Sort classes by load (most loaded first) - SA'daki gibi
            loaded_classes = sorted(
                range(self.config.class_count),
                key=lambda c: class_loads[c],
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                # Try to move from most loaded classes - SA'daki gibi
                for max_class in loaded_classes:
                    if max_class == unused_class:
                        continue
                    
                    if class_loads[max_class] > 1 and class_assignments[max_class]:
                        # Move last project from max_class to unused_class - SA'daki gibi
                        project = class_assignments[max_class].pop()
                        class_assignments[unused_class].append(project)
                        class_loads[max_class] -= 1
                        class_loads[unused_class] += 1
                        used_classes.add(unused_class)
                        moved = True
                        break
                    
                if not moved:
                    # Force move even if only 1 project in class - SA'daki gibi
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
        
        # VERIFY: All classes must be used - ABSOLUTE MANDATORY - SA'daki gibi
        final_used = set()
        for class_id, projects in enumerate(class_assignments):
            if projects:
                final_used.add(class_id)
        
        if len(final_used) < self.config.class_count:
            # CRITICAL: Last resort - redistribute all projects evenly - SA'daki gibi
            all_projects_flat = []
            for projects in class_assignments:
                all_projects_flat.extend(projects)
            
            # Clear and redistribute - SA'daki gibi
            class_assignments = [[] for _ in range(self.config.class_count)]
            class_loads = [0] * self.config.class_count
            used_classes = set()
            
            # Round-robin distribution to ensure ALL classes get at least one - SA'daki gibi
            for i, project in enumerate(all_projects_flat):
                class_id = i % self.config.class_count
                class_assignments[class_id].append(project)
                class_loads[class_id] += 1
                used_classes.add(class_id)
            
            # Final verification - should be all classes now - SA'daki gibi
            if len(used_classes) < self.config.class_count:
                # This should never happen, but force it - SA'daki gibi
                unused = [c for c in range(self.config.class_count) if c not in used_classes]
                for unused_class in unused:
                    # Take from any class - SA'daki gibi
                    for class_id in range(self.config.class_count):
                        if class_assignments[class_id]:
                            project = class_assignments[class_id].pop()
                            class_assignments[unused_class].append(project)
                            class_loads[class_id] -= 1
                            class_loads[unused_class] += 1
                            break
                        
        # Build assignments with J1 - AVOID TIMESLOT CONFLICTS - SA'daki gibi
        workloads = defaultdict(int)
        j1_index = 0
        j1_schedule = defaultdict(lambda: defaultdict(set))  # j1_id -> order -> set of class_ids
        
        for class_id, projects in enumerate(class_assignments):
            for order, project in enumerate(projects):
                # Select J1 - must be free at this timeslot (order) - SA'daki gibi
                available_j1 = [
                    i for i in self.faculty_ids 
                    if i != project.ps_id and
                    class_id not in j1_schedule[i][order]  # Not busy at this timeslot
                ]
                
                if not available_j1:
                    # No free J1 at this slot, find any available - SA'daki gibi
                    available_j1 = [
                        i for i in self.faculty_ids 
                        if i != project.ps_id
                    ]
                
                if available_j1:
                    # Least loaded AND free at this slot - SA'daki gibi
                    free_j1 = [
                        i for i in available_j1
                        if class_id not in j1_schedule[i][order]
                    ]
                    if free_j1:
                        # ACO: Feromon + heuristik ile seç
                        j1_id = self._select_jury_with_pheromone(project, class_id, order, free_j1, state)
                    else:
                        # All busy, pick least loaded (will be repaired later) - SA'daki gibi
                        j1_id = min(available_j1, key=lambda x: workloads.get(x, 0))
                else:
                    j1_id = self.faculty_ids[j1_index % len(self.faculty_ids)]
                
                workloads[j1_id] += 1
                workloads[project.ps_id] += 1
                j1_index += 1
                
                # Track J1 schedule - SA'daki gibi
                j1_schedule[j1_id][order].add(class_id)
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=class_id,
                    order_in_class=order,
                    ps_id=project.ps_id,
                    j1_id=j1_id,
                    j2_label=self.config.j2_placeholder  # CRITICAL: J2 placeholder
                )
                solution.assignments.append(assignment)
        
        # FINAL VERIFICATION: All classes must be used - ABSOLUTE MANDATORY - SA'daki gibi
        final_class_counts = defaultdict(int)
        for a in solution.assignments:
            final_class_counts[a.class_id] += 1
        
        # Find unused classes - SA'daki gibi
        unused_classes = [
            c for c in range(self.config.class_count)
            if final_class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # CRITICAL: Force fill unused classes - REDISTRIBUTE NOW - SA'daki gibi
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
                assignments_by_class[a.class_id].append(a)
            
            # Sort by load - SA'daki gibi
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused_classes:
                moved = False
                
                # Move from most loaded classes - SA'daki gibi
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    assignments_in_max = assignments_by_class[max_class]
                    if len(assignments_in_max) > 0:
                        # Move last assignment - SA'daki gibi
                        assignment = assignments_in_max[-1]
                        assignment.class_id = unused_class
                        assignment.order_in_class = 0
                        assignments_by_class[max_class].remove(assignment)
                        assignments_by_class[unused_class].append(assignment)
                        moved = True
                        break
                
                if not moved and solution.assignments:
                    # Last resort: move first assignment - SA'daki gibi
                    solution.assignments[0].class_id = unused_class
                    solution.assignments[0].order_in_class = 0
            
            # Reorder all classes - SA'daki gibi
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        # Verify again - SA'daki gibi
        final_class_counts = defaultdict(int)
        for a in solution.assignments:
            final_class_counts[a.class_id] += 1
        
        if len(final_class_counts) < self.config.class_count:
            # CRITICAL: Force distribution to unused classes - SA'daki gibi
            unused = [c for c in range(self.config.class_count) if c not in final_class_counts]
            
            # Sort assignments by class load - SA'daki gibi
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
                assignments_by_class[a.class_id].append(a)
            
            # Sort classes by load (most loaded first) - SA'daki gibi
            sorted_classes = sorted(
                assignments_by_class.keys(),
                key=lambda c: len(assignments_by_class[c]),
                reverse=True
            )
            
            for unused_class in unused:
                moved = False
                
                # Try to move from most loaded classes - SA'daki gibi
                for max_class in sorted_classes:
                    if max_class == unused_class:
                        continue
                    
                    assignments_in_max = assignments_by_class[max_class]
                    if len(assignments_in_max) > 1:
                        # Move last assignment - SA'daki gibi
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
                    # Force move even from single-assignment classes - SA'daki gibi
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
            
            # Reorder all classes after moves - SA'daki gibi
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        # ABSOLUTE FINAL CHECK: Use round-robin if still not all classes used - SA'daki gibi
        final_class_counts = defaultdict(int)
        for a in solution.assignments:
            final_class_counts[a.class_id] += 1
        
        used_count = len([c for c in range(self.config.class_count) if final_class_counts.get(c, 0) > 0])
        if used_count < self.config.class_count:
            # CRITICAL: Force round-robin distribution to ensure ALL classes used - SA'daki gibi
            logger.warning(f"CRITICAL: Only {used_count} classes used in ant solution, forcing round-robin distribution")
            for i, assignment in enumerate(solution.assignments):
                target_class = i % self.config.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // self.config.class_count
            
            # Final reorder - SA'daki gibi
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        # ABSOLUTE FINAL VERIFICATION: Ensure all classes are used before returning - SA'daki gibi
        final_verification = defaultdict(int)
        for a in solution.assignments:
            final_verification[a.class_id] += 1
        
        used_classes_count = len([c for c in range(self.config.class_count) if final_verification.get(c, 0) > 0])
        if used_classes_count < self.config.class_count:
            # CRITICAL: Last resort - force round-robin - SA'daki gibi
            logger.warning(f"CRITICAL: construct_solution - Only {used_classes_count}/{self.config.class_count} classes used, forcing round-robin")
            for i, assignment in enumerate(solution.assignments):
                target_class = i % self.config.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // self.config.class_count
            
            # Reorder - SA'daki gibi
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        # ABSOLUTE FINAL VERIFICATION: Ensure all classes are used before returning - SA'daki gibi
        final_verification = defaultdict(int)
        for a in solution.assignments:
            final_verification[a.class_id] += 1
        
        used_classes_count = len([c for c in range(self.config.class_count) if final_verification.get(c, 0) > 0])
        if used_classes_count < self.config.class_count:
            # CRITICAL: Last resort - force round-robin - SA'daki gibi
            logger.warning(f"CRITICAL: construct_solution final - Only {used_classes_count}/{self.config.class_count} classes used, forcing round-robin")
            for i, assignment in enumerate(solution.assignments):
                target_class = i % self.config.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // self.config.class_count
            
            # Reorder - SA'daki gibi
            for class_id in range(self.config.class_count):
                class_assignments_list = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments_list.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments_list):
                    a.order_in_class = i
        
        self.solution = solution
        return solution
    
    def _find_free_class_for_instructor(
        self,
        instructor_id: int,
        class_loads: List[int],
        instructor_schedule: Dict,
        used_classes: Set
    ) -> int:
        """Find a class where instructor is free - SA'daki gibi"""
        # Prefer unused classes - SA'daki gibi
        unused = [c for c in range(self.config.class_count) if c not in used_classes]
        if unused:
            # Check if instructor is free in unused classes - SA'daki gibi
            for class_id in unused:
                next_order = class_loads[class_id]
                if class_id not in instructor_schedule[instructor_id][next_order]:
                    return class_id
            # All unused classes have conflict, pick least loaded - SA'daki gibi
            return min(unused, key=lambda c: class_loads[c])
        else:
            # All classes used, find where instructor is free - SA'daki gibi
            for class_id in range(self.config.class_count):
                next_order = class_loads[class_id]
                if class_id not in instructor_schedule[instructor_id][next_order]:
                    return class_id
            # All have conflicts, pick least loaded - SA'daki gibi
            return min(range(self.config.class_count), key=lambda c: class_loads[c])
    
    def _select_class_from_candidates(self, project: Project, candidates: List[int], state: Dict) -> int:
        """Candidates listesinden feromon + heuristik ile sınıf seç"""
        probabilities = []
        class_loads = state.get('class_loads', defaultdict(int))
        
        for class_id in candidates:
            # Feromon değeri
            tau = self.pheromone.get_class_pheromone(project.id, class_id)
            
            # Heuristik değer
            eta = self._get_class_heuristic(project, class_id, state)
            
            # Unused sınıflar için çok yüksek bonus
            current_load = class_loads.get(class_id, 0)
            if current_load == 0:
                eta *= 50.0
                tau *= 10.0
            
            # Olasılık
            prob = (tau ** self.config.alpha) * (eta ** self.config.beta)
            probabilities.append(prob)
        
        # Normalize et
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / len(candidates)] * len(candidates)
        
        # Rulet tekerleği seçimi
        idx = self._roulette_wheel_selection(probabilities)
        return candidates[idx]
    
    def _select_jury_with_pheromone(
        self,
        project: Project,
        class_id: int,
        order: int,
        candidates: List[int],
        state: Dict
    ) -> int:
        """Candidates listesinden feromon + heuristik ile jüri seç"""
        probabilities = []
        
        for j_id in candidates:
            # Feromon değeri
            tau = self.pheromone.get_jury_pheromone(project.id, j_id)
            
            # Heuristik değer
            eta = self.penalty_calc.get_heuristic_value(
                project, class_id, j_id, state
            )
            
            prob = (tau ** self.config.alpha) * (eta ** self.config.beta)
            probabilities.append(prob)
        
        # Normalize et
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / len(candidates)] * len(candidates)
        
        # Seç
        idx = self._roulette_wheel_selection(probabilities)
        return candidates[idx]
    
    def _sort_projects_by_priority(self) -> List[Project]:
        """Projeleri öncelik moduna göre sırala."""
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            ara = [p for p in self.projects if p.type in ('interim', 'ara')]
            bitirme = [p for p in self.projects if p.type in ('final', 'bitirme')]
            return ara + bitirme
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            bitirme = [p for p in self.projects if p.type in ('final', 'bitirme')]
            ara = [p for p in self.projects if p.type in ('interim', 'ara')]
            return bitirme + ara
        else:  # ESIT
            projects = list(self.projects)
            random.shuffle(projects)
            return projects
    
    def _select_class(self, project: Project, state: Dict) -> int:
        """
        Proje için sınıf seç.
        
        CRITICAL: Kullanılmayan sınıfları ÇOK YÜKSEK tercih et!
        
        Olasılık: p(c) ∝ τ(p,c)^α * η(p,c)^β
        """
        probabilities = []
        class_loads = state.get('class_loads', defaultdict(int))
        
        for class_id in range(self.config.class_count):
            # Feromon değeri
            tau = self.pheromone.get_class_pheromone(project.id, class_id)
            
            # Heuristik değer
            eta = self._get_class_heuristic(project, class_id, state)
            
            # CRITICAL: Kullanılmayan sınıflar için ÇOK YÜKSEK bonus
            current_load = class_loads.get(class_id, 0)
            if current_load == 0:
                # Kullanılmayan sınıf - ÇOK YÜKSEK tercih
                eta *= 50.0  # Çok yüksek çarpan
                tau *= 10.0  # Feromon da yüksek
            
            # Olasılık
            prob = (tau ** self.config.alpha) * (eta ** self.config.beta)
            probabilities.append(prob)
        
        # Normalize et
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / self.config.class_count] * self.config.class_count
        
        # Rulet tekerleği seçimi
        return self._roulette_wheel_selection(probabilities)
    
    def _select_class_with_uniform_distribution(self, project: Project, state: Dict) -> int:
        """
        Proje için sınıf seç (uniform dağılımı koruyarak).
        
        CRITICAL: 
        1. Kullanılmayan sınıfları ÇOK YÜKSEK tercih et!
        2. ±3 bandı dışındaki sınıfları düşük tercih et!
        
        Olasılık: p(c) ∝ τ(p,c)^α * η(p,c)^β
        """
        probabilities = []
        class_loads = state.get('class_loads', defaultdict(int))
        target = len(self.projects) / self.config.class_count
        tolerance = self.config.uniform_distribution_tolerance
        
        for class_id in range(self.config.class_count):
            # Feromon değeri
            tau = self.pheromone.get_class_pheromone(project.id, class_id)
            
            # Heuristik değer
            eta = self._get_class_heuristic(project, class_id, state)
            
            # CRITICAL: Uniform dağılım bonusu/cezası
            current_load = class_loads.get(class_id, 0)
            deviation = current_load - target
            
            if current_load == 0:
                # Kullanılmayan sınıf - ÇOK YÜKSEK tercih
                eta *= 50.0
                tau *= 10.0
            elif deviation < -tolerance:
                # Minimum altında - yüksek tercih
                eta *= 5.0
            elif deviation > tolerance:
                # Maksimum üstünde - düşük tercih
                eta *= 0.1
            
            # Olasılık
            prob = (tau ** self.config.alpha) * (eta ** self.config.beta)
            probabilities.append(prob)
        
        # Normalize et
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / self.config.class_count] * self.config.class_count
        
        # Rulet tekerleği seçimi
        return self._roulette_wheel_selection(probabilities)
    
    def _select_jury(
        self, 
        project: Project, 
        class_id: int, 
        order: int,
        state: Dict
    ) -> int:
        """
        Proje için jüri seç.
        
        Kısıtlar:
        - J1 != PS
        - Timeslot'ta çakışma olmamalı
        """
        # Uygun jürileri filtrele
        available_juries = []
        timeslot_key = (class_id, order)
        used_instructors = state['timeslot_usage'].get(timeslot_key, set())
        
        for j_id in self.faculty_ids:
            # PS olamaz
            if j_id == project.ps_id:
                continue
            # Timeslot'ta zaten görevi varsa olamaz
            if j_id in used_instructors:
                continue
            available_juries.append(j_id)
        
        if not available_juries:
            # Hiç uygun jüri yoksa, en az yüklü olanı seç (PS hariç)
            workloads = state['workloads']
            candidates = [j for j in self.faculty_ids if j != project.ps_id]
            if candidates:
                return min(candidates, key=lambda j: workloads.get(j, 0))
            return self.faculty_ids[0] if self.faculty_ids else project.ps_id
        
        # Olasılık hesapla
        probabilities = []
        for j_id in available_juries:
            # Feromon değeri
            tau = self.pheromone.get_jury_pheromone(project.id, j_id)
            
            # Heuristik değer
            eta = self.penalty_calc.get_heuristic_value(
                project, class_id, j_id, state
            )
            
            prob = (tau ** self.config.alpha) * (eta ** self.config.beta)
            probabilities.append(prob)
        
        # Normalize et
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / len(available_juries)] * len(available_juries)
        
        # Seç
        idx = self._roulette_wheel_selection(probabilities)
        return available_juries[idx]
    
    def _get_class_heuristic(self, project: Project, class_id: int, state: Dict) -> float:
        """
        Sınıf seçimi için heuristik değer.
        
        CRITICAL: 
        1. Kullanılmayan sınıfları ÇOK YÜKSEK tercih et!
        2. Uniform dağılımı (±3 bandı) göz önünde bulundur!
        """
        eta = 1.0
        
        # CRITICAL: Kullanılmayan sınıfları çok yüksek tercih et
        class_loads = state['class_loads']
        current_load = class_loads.get(class_id, 0)
        target = len(self.projects) / self.config.class_count
        tolerance = self.config.uniform_distribution_tolerance
        
        if current_load == 0:
            # Kullanılmayan sınıf - ÇOK YÜKSEK tercih
            eta += 10.0  # Çok yüksek bonus
        else:
            # Uniform dağılım heuristiği (±3 bandı)
            deviation = current_load - target
            
            if deviation < -tolerance:
                # Minimum altında - yüksek tercih
                eta += 5.0  # Çok yüksek bonus
            elif deviation > tolerance:
                # Maksimum üstünde - düşük tercih
                eta *= 0.1  # Çok düşük çarpan
            else:
                # Band içinde - normal tercih
                if current_load < target:
                    eta += 0.5
                elif current_load > target:
                    eta -= 0.3
        
        # PS'nin son sınıfı
        instructor_last_class = state.get('instructor_last_class', {})
        if instructor_last_class.get(project.ps_id) == class_id:
            eta += 0.4
        
        return max(0.1, eta)
    
    def _roulette_wheel_selection(self, probabilities: List[float]) -> int:
        """Rulet tekerleği seçimi."""
        r = random.random()
        cumsum = 0.0
        for i, p in enumerate(probabilities):
            cumsum += p
            if r <= cumsum:
                return i
        return len(probabilities) - 1


# ============================================================================
# LOCAL SEARCH
# ============================================================================

class ACOLocalSearch:
    """
    ACO çözümleri için local search.
    
    Hareketler:
    - J1 swap: İki projenin jürilerini değiştir
    - Class move: Projeyi başka sınıfa taşı
    - Order swap: Aynı sınıftaki iki projenin sırasını değiştir
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: ACOConfig,
        penalty_calculator: ACOPenaltyCalculator,
        repair_mechanism: ACORepairMechanism
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        self.penalty_calc = penalty_calculator
        self.repair = repair_mechanism
        
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    def improve(self, solution: ACOSolution) -> ACOSolution:
        """
        Local search ile çözümü iyileştir.
        """
        best_solution = solution.copy()
        best_cost = self.penalty_calc.calculate_total_cost(best_solution)
        
        for _ in range(self.config.local_search_iterations):
            # Rastgele hareket seç
            move_type = random.choice(['j1_swap', 'class_move', 'order_swap'])
            
            neighbour = best_solution.copy()
            
            if move_type == 'j1_swap':
                self._apply_j1_swap(neighbour)
            elif move_type == 'class_move':
                self._apply_class_move(neighbour)
            else:
                self._apply_order_swap(neighbour)
            
            # Onar
            self.repair.repair(neighbour)
            
            # Değerlendir
            cost = self.penalty_calc.calculate_total_cost(neighbour)
            
            if cost < best_cost:
                best_solution = neighbour
                best_cost = cost
        
        return best_solution
    
    def _apply_j1_swap(self, solution: ACOSolution) -> None:
        """İki projenin jürilerini değiştir."""
        if len(solution.assignments) < 2:
            return
        
        # Rastgele iki proje seç
        a1, a2 = random.sample(solution.assignments, 2)
        
        # Jürileri değiştir (PS != J1 kontrolü ile)
        if a1.j1_id != a2.ps_id and a2.j1_id != a1.ps_id:
            a1.j1_id, a2.j1_id = a2.j1_id, a1.j1_id
    
    def _apply_class_move(self, solution: ACOSolution) -> None:
        """Projeyi başka sınıfa taşı."""
        if not solution.assignments:
            return
        
        # Rastgele bir proje seç
        assignment = random.choice(solution.assignments)
        
        # Farklı bir sınıf seç
        new_class = random.randint(0, solution.class_count - 1)
        if new_class != assignment.class_id:
            assignment.class_id = new_class
    
    def _apply_order_swap(self, solution: ACOSolution) -> None:
        """Aynı sınıftaki iki projenin sırasını değiştir."""
        # Sınıflara göre grupla
        class_assignments: Dict[int, List[ProjectAssignment]] = defaultdict(list)
        for a in solution.assignments:
            class_assignments[a.class_id].append(a)
        
        # En az 2 projesi olan bir sınıf seç
        valid_classes = [c for c, assignments in class_assignments.items() if len(assignments) >= 2]
        if not valid_classes:
            return
        
        class_id = random.choice(valid_classes)
        a1, a2 = random.sample(class_assignments[class_id], 2)
        
        # Sıraları değiştir
        a1.order_in_class, a2.order_in_class = a2.order_in_class, a1.order_in_class


# ============================================================================
# ACO SCHEDULER
# ============================================================================

class ACOScheduler:
    """
    Ana ACO zamanlayıcı.
    
    Özellikler:
    - Elitist ACO
    - Local search entegrasyonu
    - Adaptif feromon güncelleme
    - Çoklu sınıf sayısı denemesi
    """
    
    def __init__(self, config: ACOConfig = None):
        self.config = config or ACOConfig()
        
        # Bileşenler
        self.pheromone_matrix: Optional[PheromoneMatrix] = None
        self.penalty_calculator: Optional[ACOPenaltyCalculator] = None
        self.repair_mechanism: Optional[ACORepairMechanism] = None
        self.local_search: Optional[ACOLocalSearch] = None
        
        # Veri
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict] = []
        self.timeslots: List[Dict] = []
        
        # Durum
        self.best_solution: Optional[ACOSolution] = None
        self.best_cost: float = float('inf')
        self.iteration_history: List[float] = []
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Veriyi yükle ve bileşenleri başlat."""
        self._load_data(data)
        self._init_components()
    
    def _load_data(self, data: Dict[str, Any]) -> None:
        """Veriyi yükle ve dönüştür."""
        # Projeleri yükle
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
        
        # Öğretim görevlilerini yükle
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        
        for i in raw_instructors:
            instructor = Instructor(
                id=i.get("id"),
                name=i.get("name", ""),
                type=i.get("type", "instructor")
            )
            self.instructors.append(instructor)
        
        # Sınıfları ve zaman dilimlerini yükle
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Sınıf sayısını ayarla
        if self.classrooms and len(self.classrooms) > 0:
            available_class_count = len(self.classrooms)
            if self.config.auto_class_count or self.config.class_count != available_class_count:
                self.config.class_count = available_class_count
                logger.info(f"Sınıf sayısı {available_class_count} olarak ayarlandı")
    
    def _init_components(self) -> None:
        """Bileşenleri başlat."""
        self.pheromone_matrix = PheromoneMatrix(
            self.projects, self.instructors, self.config
        )
        
        self.penalty_calculator = ACOPenaltyCalculator(
            self.projects, self.instructors, self.config
        )
        
        self.repair_mechanism = ACORepairMechanism(
            self.projects, self.instructors, self.config
        )
        
        self.local_search = ACOLocalSearch(
            self.projects, self.instructors, self.config,
            self.penalty_calculator, self.repair_mechanism
        )
    
    def run(self) -> ACOSolution:
        """
        ACO algoritmasını çalıştır.
        
        Returns:
            En iyi çözüm
        """
        start_time = time.time()
        no_improve_count = 0
        
        logger.info(f"ACO başlatılıyor: {self.config.ant_count} karınca, "
                   f"{self.config.max_iterations} iterasyon, "
                   f"{self.config.class_count} sınıf")
        
        for iteration in range(self.config.max_iterations):
            # Zaman kontrolü
            if time.time() - start_time > self.config.time_limit:
                logger.info(f"Zaman limiti aşıldı, iterasyon {iteration}'de durduruluyor")
                break
            
            # Karıncaları çalıştır
            iteration_best = self._run_iteration()
            
            # En iyi çözümü güncelle - SADECE kullanılmayan sınıfı olmayan çözümler
            if (iteration_best.total_cost < self.best_cost and 
                not self.penalty_calculator.has_unused_classes(iteration_best)):
                self.best_solution = iteration_best.copy()
                self.best_cost = iteration_best.total_cost
                no_improve_count = 0
                logger.info(f"İterasyon {iteration}: Yeni en iyi maliyet = {self.best_cost:.2f}")
            else:
                no_improve_count += 1
                
                # Eğer en iyi çözümde kullanılmayan sınıf varsa, zorla düzelt
                if self.penalty_calculator.has_unused_classes(iteration_best):
                    logger.warning(f"İterasyon {iteration}: En iyi çözümde kullanılmayan sınıf var, zorla düzeltiliyor")
                    self._force_all_classes_used(iteration_best)
                    self.repair_mechanism.repair(iteration_best)
                    self.penalty_calculator.calculate_total_cost(iteration_best)
                    
                    # Tekrar kontrol et
                    if (iteration_best.total_cost < self.best_cost and 
                        not self.penalty_calculator.has_unused_classes(iteration_best)):
                        self.best_solution = iteration_best.copy()
                        self.best_cost = iteration_best.total_cost
                        no_improve_count = 0
                        logger.info(f"İterasyon {iteration}: Düzeltme sonrası yeni en iyi maliyet = {self.best_cost:.2f}")
            
            self.iteration_history.append(self.best_cost)
            
            # Erken durdurma
            if no_improve_count >= self.config.stagnation_limit:
                logger.info(f"Stagnasyon limiti aşıldı, iterasyon {iteration}'de durduruluyor")
                break
            
            # Her 10 iterasyonda bir log
            if iteration % 10 == 0:
                logger.info(f"İterasyon {iteration}: En iyi maliyet = {self.best_cost:.2f}")
        
        elapsed_time = time.time() - start_time
        
        # CRITICAL: Final verification - ensure all classes are used - SA'daki gibi
        # Multiple passes to ensure absolute compliance - SA'daki gibi
        if self.best_solution:
            for _ in range(3):  # Try 3 times to ensure all classes used - SA'daki gibi
                self._force_all_classes_used(self.best_solution)
                self.repair_mechanism.repair(self.best_solution)
                
                # Verify all classes are used - SA'daki gibi
                class_counts = defaultdict(int)
                for a in self.best_solution.assignments:
                    class_counts[a.class_id] += 1
                
                used_count = len([c for c in range(self.best_solution.class_count) if class_counts.get(c, 0) > 0])
                if used_count == self.best_solution.class_count:
                    break  # All classes used, exit loop - SA'daki gibi
            
            # Final cost calculation - SA'daki gibi
            self.penalty_calculator.calculate_total_cost(self.best_solution)
            self.best_cost = self.best_solution.total_cost
        
        # CRITICAL: Ensure best_solution.class_count matches config.class_count - SA'daki gibi
        if self.best_solution:
            self.best_solution.class_count = self.config.class_count
            logger.info(f"Final state class_count: {self.best_solution.class_count}, config class_count: {self.config.class_count}")
        
        # Final verification: Tüm sınıfların kullanıldığını doğrula - SA'daki gibi
        if self.best_solution:
            class_counts = defaultdict(int)
            for a in self.best_solution.assignments:
                class_counts[a.class_id] += 1
            
            used_classes = len([c for c in range(self.best_solution.class_count) if class_counts.get(c, 0) > 0])
            logger.info(f"Final doğrulama: {used_classes}/{self.best_solution.class_count} sınıf kullanılıyor")
            
            if used_classes < self.best_solution.class_count:
                logger.warning(f"WARNING: Only {used_classes} classes used, expected {self.best_solution.class_count}")
                logger.warning(f"Missing classes: {[c for c in range(self.best_solution.class_count) if class_counts.get(c, 0) == 0]}")
        
        logger.info(f"ACO tamamlandı: {elapsed_time:.2f}s, "
                   f"En iyi maliyet = {self.best_cost:.2f}")
        
        return self.best_solution
    
    def _run_iteration(self) -> ACOSolution:
        """
        Tek bir iterasyon çalıştır.
        
        1. Tüm karıncalar çözüm oluşturur
        2. Çözümler onarılır
        3. Local search uygulanır
        4. Feromon güncellenir
        
        Returns:
            Bu iterasyonun en iyi çözümü
        """
        solutions: List[ACOSolution] = []
        
        # Her karınca için çözüm oluştur
        for _ in range(self.config.ant_count):
            ant = Ant(
                self.projects,
                self.instructors,
                self.config,
                self.pheromone_matrix,
                self.penalty_calculator
            )
            
            solution = ant.construct_solution()
            
            # CRITICAL: ÖNCE tüm sınıfların kullanıldığını zorla (repair'den önce)
            self._force_all_classes_used(solution)
            
            # Onar (CRITICAL: Tüm sınıfların kullanılmasını garanti et)
            self.repair_mechanism.repair(solution)
            
            # CRITICAL: Repair sonrası tekrar tüm sınıfların kullanıldığını doğrula
            self._force_all_classes_used(solution)
            
            # Local search
            if self.config.use_local_search:
                solution = self.local_search.improve(solution)
                # Local search sonrası tekrar kontrol et
                self.repair_mechanism.repair(solution)
                self._force_all_classes_used(solution)
            
            # Değerlendir
            self.penalty_calculator.calculate_total_cost(solution)
            
            solutions.append(solution)
        
        # En iyi çözümü bul - SADECE kullanılmayan sınıfı olmayan çözümler arasından
        valid_solutions = [
            s for s in solutions 
            if not self.penalty_calculator.has_unused_classes(s)
        ]
        
        if valid_solutions:
            iteration_best = min(valid_solutions, key=lambda s: s.total_cost)
        else:
            # Eğer hiç geçerli çözüm yoksa, en iyisini seç ve zorla düzelt
            iteration_best = min(solutions, key=lambda s: s.total_cost)
            logger.warning("CRITICAL: Tüm çözümlerde kullanılmayan sınıf var, zorla düzeltiliyor")
            self._force_all_classes_used(iteration_best)
            self.repair_mechanism.repair(iteration_best)
            self.penalty_calculator.calculate_total_cost(iteration_best)
        
        # Final check: En iyi çözümde kullanılmayan sınıf varsa zorla düzelt
        if self.penalty_calculator.has_unused_classes(iteration_best):
            logger.warning("CRITICAL: İterasyon en iyi çözümünde kullanılmayan sınıf var, zorla düzeltiliyor")
            self._force_all_classes_used(iteration_best)
            self.repair_mechanism.repair(iteration_best)
            self._force_all_classes_used(iteration_best)  # Repair sonrası tekrar zorla
            self.penalty_calculator.calculate_total_cost(iteration_best)
        
        # ABSOLUTE FINAL CHECK: En iyi çözümde mutlaka tüm sınıflar kullanılmalı
        final_class_counts = defaultdict(int)
        for a in iteration_best.assignments:
            final_class_counts[a.class_id] += 1
        
        used_count = len([c for c in range(iteration_best.class_count) if final_class_counts.get(c, 0) > 0])
        if used_count < iteration_best.class_count:
            logger.error(f"CRITICAL ERROR: _run_iteration - Only {used_count}/{iteration_best.class_count} classes used, forcing round-robin")
            # CRITICAL: Force round-robin distribution
            for i, assignment in enumerate(iteration_best.assignments):
                target_class = i % iteration_best.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // iteration_best.class_count
            
            # Reorder
            for class_id in range(iteration_best.class_count):
                class_assignments = [
                    a for a in iteration_best.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
            
            # Repair after round-robin
            self.repair_mechanism.repair(iteration_best)
            self.penalty_calculator.calculate_total_cost(iteration_best)
        
        # Feromon güncelle
        self._update_pheromones(solutions, iteration_best)
        
        return iteration_best
    
    def _force_all_classes_used(self, solution: ACOSolution) -> None:
        """
        ABSOLUTE MANDATORY: Force all classes to be used - CRITICAL HARD CONSTRAINT.
        
        SA'daki SimulatedAnnealingScheduler._force_all_classes_used gibi
        agresif round-robin dağıtım ve yük dengeleme yapar.
        
        CRITICAL: Every single classroom MUST have at least one project assigned.
        Bu metod TUM siniflarin kullanildigindan %100 emin olur.
        
        This is called after every repair, after ant construction, after local search
        to ensure no class is left unused.
        CRITICAL: ALL classes from 0 to class_count-1 MUST have at least one assignment.
        SA'daki SimulatedAnnealingScheduler._force_all_classes_used'a birebir uygun.
        """
        # CRITICAL: Ensure solution.class_count matches config.class_count - SA'daki gibi
        solution.class_count = self.config.class_count
        
        max_iterations = 1000  # SA'daki gibi increased iterations for aggressive enforcement
        
        for iteration in range(max_iterations):
            class_counts = defaultdict(int)
            for a in solution.assignments:
                class_counts[a.class_id] += 1
            
            unused_classes = [
                c for c in range(solution.class_count)
                if class_counts.get(c, 0) == 0
            ]
            
            if not unused_classes:
                # Verify all classes are really used
                used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
                if used_count == solution.class_count:
                    # All classes used - reorder and return
                    for class_id in range(solution.class_count):
                        class_assignments = [
                            a for a in solution.assignments if a.class_id == class_id
                        ]
                        class_assignments.sort(key=lambda x: x.order_in_class)
                        for i, a in enumerate(class_assignments):
                            a.order_in_class = i
                    return
        
            # CRITICAL: Force fill unused classes - AGGRESSIVE APPROACH
            assignments_by_class = defaultdict(list)
            for a in solution.assignments:
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
                    if solution.assignments:
                        # Find any assignment from a used class
                        for assignment in solution.assignments:
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
                
                if not moved and solution.assignments:
                    # Absolute last resort: force first assignment
                    solution.assignments[0].class_id = unused_class
                    solution.assignments[0].order_in_class = 0
            
            # Reorder all classes after moves
            for class_id in range(solution.class_count):
                class_assignments = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
        
        # Final verification - if still not all classes used, force round-robin
        class_counts = defaultdict(int)
        for a in solution.assignments:
            class_counts[a.class_id] += 1
        
        unused_classes = [
            c for c in range(solution.class_count)
            if class_counts.get(c, 0) == 0
        ]
        
        if unused_classes:
            # CRITICAL: Force round-robin distribution
            for i, assignment in enumerate(solution.assignments):
                target_class = i % solution.class_count
                assignment.class_id = target_class
                assignment.order_in_class = i // solution.class_count
            
            # Final reorder
            for class_id in range(solution.class_count):
                class_assignments = [
                    a for a in solution.assignments if a.class_id == class_id
                ]
                class_assignments.sort(key=lambda x: x.order_in_class)
                for i, a in enumerate(class_assignments):
                    a.order_in_class = i
    
    def _reorder_all_classes_in_solution(self, solution: ACOSolution) -> None:
        """Tüm sınıflardaki projeleri yeniden sırala."""
        for class_id in range(solution.class_count):
            class_assignments = [
                a for a in solution.assignments if a.class_id == class_id
            ]
            class_assignments.sort(key=lambda x: x.order_in_class)
            for i, a in enumerate(class_assignments):
                a.order_in_class = i
    
    def _update_pheromones(
        self, 
        solutions: List[ACOSolution], 
        iteration_best: ACOSolution
    ) -> None:
        """
        Feromon matrisini güncelle.
        
        1. Buharlaşma
        2. Tüm karıncalar feromon bırakır
        3. Elitist: En iyi çözüm ekstra feromon bırakır
        """
        # Buharlaşma
        self.pheromone_matrix.evaporate()
        
        # Tüm çözümler feromon bırakır
        for solution in solutions:
            if solution.total_cost > 0:
                amount = self.config.Q / solution.total_cost
                self.pheromone_matrix.deposit(solution, amount)
        
        # Elitist: En iyi çözüm ekstra feromon bırakır
        if self.config.use_elitist and self.best_solution:
            if self.best_cost > 0:
                elitist_amount = (self.config.Q / self.best_cost) * self.config.elitist_weight
                self.pheromone_matrix.deposit(self.best_solution, elitist_amount)


# ============================================================================
# MAIN ACO ALGORITHM CLASS
# ============================================================================

class AntColonyOptimization(OptimizationAlgorithm):
    """
    Ant Colony Optimization (ACO) - Çok Kriterli Akademik Proje Planlama.
    
    Tek fazlı çalışma prensibi:
    - Tüm projeler, hocalar, sınıf sayısı tek seferde modele verilir
    - ACO iteratif olarak çalışır
    - En iyi çözüm tek seferde planner'a aktarılır
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        ACO başlatıcı.
        
        Args:
            params: Algoritma parametreleri
        """
        super().__init__(params)
        params = params or {}
        
        # Konfigürasyon oluştur
        self.config = ACOConfig(
            ant_count=params.get("ant_count", 50),
            max_iterations=params.get("max_iterations", 200),
            alpha=params.get("alpha", 1.0),
            beta=params.get("beta", 2.0),
            evaporation_rate=params.get("evaporation_rate", 0.1),
            Q=params.get("Q", 100.0),
            initial_pheromone=params.get("initial_pheromone", 1.0),
            use_elitist=params.get("use_elitist", True),
            elitist_weight=params.get("elitist_weight", 2.0),
            use_local_search=params.get("use_local_search", True),
            local_search_iterations=params.get("local_search_iterations", 10),
            stagnation_limit=params.get("stagnation_limit", 30),
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
            weight_h1=params.get("weight_h1", 10.0),
            weight_h2=params.get("weight_h2", 100.0),
            weight_h3=params.get("weight_h3", 5.0),
            weight_h4=params.get("weight_h4", 2.0),
            uniform_distribution_tolerance=params.get("uniform_distribution_tolerance", 3),
            weight_uniform_distribution=params.get("weight_uniform_distribution", 50.0)
        )
        
        # Veri yapıları
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        
        # Scheduler
        self.scheduler: Optional[ACOScheduler] = None
        
        # En iyi çözüm
        self.best_solution: Optional[ACOSolution] = None
        self.best_cost: float = float('inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Algoritmayı başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri
        """
        # Verileri yükle
        self._load_data(data)
        
        # Scheduler oluştur
        self.scheduler = ACOScheduler(self.config)
        self.scheduler.initialize(data)
        
        # En iyi çözümü sıfırla
        self.best_solution = None
        self.best_cost = float('inf')
    
    def _load_data(self, data: Dict[str, Any]) -> None:
        """Verileri yükle ve dönüştür."""
        # Projeleri yükle
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
        
        # Öğretim görevlilerini yükle
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        
        for i in raw_instructors:
            instructor = Instructor(
                id=i.get("id"),
                name=i.get("name", ""),
                type=i.get("type", "instructor")
            )
            self.instructors.append(instructor)
        
        # Sınıfları ve zaman dilimlerini yükle
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Sınıf sayısını ayarla
        if self.classrooms and len(self.classrooms) > 0:
            available_class_count = len(self.classrooms)
            if self.config.auto_class_count or self.config.class_count != available_class_count:
                self.config.class_count = available_class_count
                logger.info(f"Sınıf sayısı {available_class_count} olarak ayarlandı")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ACO'yu çalıştırır.
        
        Args:
            data: Algoritma giriş verileri
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu
        """
        if data:
            self.initialize(data)
        
        start_time = time.time()
        
        # Sınıf sayısı denemesi
        if self.classrooms and len(self.classrooms) > 0:
            # Mevcut sınıf sayısını kullan
            result = self._run_aco()
        elif self.config.auto_class_count:
            # 5, 6, 7 sınıf sayısı için dene
            best_result = None
            best_overall_cost = float('inf')
            
            for class_count in [5, 6, 7]:
                logger.info(f"Sınıf sayısı {class_count} ile çalıştırılıyor...")
                self.config.class_count = class_count
                
                # Scheduler'ı yeniden başlat
                self.scheduler = ACOScheduler(self.config)
                self.scheduler.initialize({
                    "projects": [{"id": p.id, "title": p.title, "type": p.type, 
                                 "responsible_id": p.ps_id, "is_makeup": p.is_makeup} 
                                for p in self.projects],
                    "instructors": [{"id": i.id, "name": i.name, "type": i.type} 
                                   for i in self.instructors],
                    "classrooms": self.classrooms,
                    "timeslots": self.timeslots
                })
                
                result = self._run_aco()
                
                if result['cost'] < best_overall_cost:
                    best_overall_cost = result['cost']
                    best_result = result
            
            result = best_result
        else:
            result = self._run_aco()
        
        end_time = time.time()
        
        # CRITICAL: Final check before conversion - ensure all classes are used - SA'daki gibi
        if result['solution']:
            # Multiple passes to ensure absolute compliance - SA'daki gibi
            for _ in range(3):  # Try 3 times to ensure all classes used
                if self.scheduler:
                    self.scheduler._force_all_classes_used(result['solution'])
                    self.scheduler.repair_mechanism.repair(result['solution'])
                
                # Verify all classes are used
                class_counts = defaultdict(int)
                for a in result['solution'].assignments:
                    class_counts[a.class_id] += 1
                
                used_count = len([c for c in range(result['solution'].class_count) if class_counts.get(c, 0) > 0])
                if used_count == result['solution'].class_count:
                    break  # All classes used, exit loop
            
            # Recalculate cost after repairs
            if self.scheduler and self.scheduler.penalty_calculator:
                result['solution'].total_cost = self.scheduler.penalty_calculator.calculate_total_cost(result['solution'])
                result['cost'] = result['solution'].total_cost
        
        # Çözümü output formatına dönüştür
        schedule = self._convert_solution_to_schedule(result['solution'])
        
        # FINAL CHECK: Verify all classes in schedule - ABSOLUTE MANDATORY - SA'daki gibi
        classes_in_schedule = set()
        for item in schedule:
            class_id = item.get("class_id", item.get("classroom_id"))
            if class_id is not None:
                classes_in_schedule.add(class_id)
        
        if len(classes_in_schedule) < result['solution'].class_count:
            logger.warning(f"WARNING: Only {len(classes_in_schedule)} classes in schedule, expected {result['solution'].class_count}")
            logger.warning(f"Missing classes: {[c for c in range(result['solution'].class_count) if c not in classes_in_schedule]}")
            
            # AGGRESSIVE: Force redistribution with round-robin - SA'daki gibi
            if self.scheduler:
                self.scheduler._force_all_classes_used(result['solution'])
                self.scheduler.repair_mechanism.repair(result['solution'])
                result['solution'].total_cost = self.scheduler.penalty_calculator.calculate_total_cost(result['solution'])
                result['cost'] = result['solution'].total_cost
                
                # Convert again
                schedule = self._convert_solution_to_schedule(result['solution'])
                
                # Final verification
                classes_in_schedule = set()
                for item in schedule:
                    class_id = item.get("class_id", item.get("classroom_id"))
                    if class_id is not None:
                        classes_in_schedule.add(class_id)
                
                if len(classes_in_schedule) < result['solution'].class_count:
                    logger.error(f"CRITICAL ERROR: Still only {len(classes_in_schedule)} classes used after forced redistribution!")
                else:
                    logger.info(f"SUCCESS: All {result['solution'].class_count} classes are now used after forced redistribution")
        
        # Calculate penalty breakdown - SA'daki gibi
        penalty_breakdown = {}
        if self.scheduler and self.scheduler.penalty_calculator:
            penalty_breakdown = {
                'h1_time_penalty': self.scheduler.penalty_calculator.calculate_h1_gap_penalty(result['solution']),
                'h2_workload_penalty': self.scheduler.penalty_calculator.calculate_h2_workload_penalty(result['solution']),
                'h3_class_change_penalty': self.scheduler.penalty_calculator.calculate_h3_class_change_penalty(result['solution']),
                'h4_class_load_penalty': self.scheduler.penalty_calculator.calculate_h4_class_load_penalty(result['solution']),
                'unused_class_penalty': self.scheduler.penalty_calculator.calculate_unused_class_penalty(result['solution']),
                'uniform_distribution_penalty': self.scheduler.penalty_calculator.calculate_uniform_distribution_penalty(result['solution'])
            }
        else:
            penalty_breakdown = {
                "h1_gap_penalty": result['solution'].h1_gap_penalty if hasattr(result['solution'], 'h1_gap_penalty') else 0,
                "h2_workload_penalty": result['solution'].h2_workload_penalty if hasattr(result['solution'], 'h2_workload_penalty') else 0,
                "h3_class_change_penalty": result['solution'].h3_class_change_penalty if hasattr(result['solution'], 'h3_class_change_penalty') else 0,
                "h4_class_load_penalty": result['solution'].h4_class_load_penalty if hasattr(result['solution'], 'h4_class_load_penalty') else 0
            }
        
        return {
            "schedule": schedule,
            "assignments": schedule,
            "solution": schedule,
            "fitness": -result['cost'],  # Fitness = -cost
            "cost": result['cost'],
            "iterations": result['iterations'],
            "execution_time": end_time - start_time,
            "class_count": result['solution'].class_count,
            "penalty_breakdown": penalty_breakdown,
            "status": "completed"
        }
    
    def _run_aco(self) -> Dict[str, Any]:
        """
        Ana ACO döngüsü.
        
        Returns:
            En iyi çözüm ve istatistikler
        """
        solution = self.scheduler.run()
        
        return {
            'solution': solution,
            'cost': solution.total_cost,
            'iterations': len(self.scheduler.iteration_history)
        }
    
    def _convert_solution_to_schedule(self, solution: ACOSolution) -> List[Dict[str, Any]]:
        """
        ACO çözümünü planner formatına dönüştür.
        
        CRITICAL: Before conversion, ensure ALL classes are used (HARD CONSTRAINT).
        SA'daki gibi agresif kontrol ve düzeltme yapılır.
        
        Args:
            solution: ACO çözümü
            
        Returns:
            Planner formatında atamalar listesi
        """
        # CRITICAL: Before converting, verify and fix unused classes - SA'daki gibi
        if solution:
            # Ensure all classes are used - SA'daki gibi
            class_counts = defaultdict(int)
            for a in solution.assignments:
                class_counts[a.class_id] += 1
            
            used_count = len([c for c in range(solution.class_count) if class_counts.get(c, 0) > 0])
            if used_count < solution.class_count:
                logger.warning(f"CRITICAL: Only {used_count} classes used before conversion, forcing all {solution.class_count} classes")
                # Force all classes used - SA'daki gibi
                if self.scheduler:
                    self.scheduler._force_all_classes_used(solution)
                    self.scheduler.repair_mechanism.repair(solution)
        
        schedule = []
        
        # Proje ve öğretim görevlisi lookup'ları
        project_lookup = {p.id: p for p in self.projects}
        instructor_lookup = {i.id: i for i in self.instructors}
        
        # Sınıf ve timeslot lookup'ları
        classroom_lookup = {}
        for i, c in enumerate(self.classrooms):
            classroom_lookup[i] = c
        
        timeslot_lookup = {}
        for i, t in enumerate(self.timeslots):
            timeslot_lookup[i] = t
        
        for assignment in solution.assignments:
            project = project_lookup.get(assignment.project_id)
            ps = instructor_lookup.get(assignment.ps_id)
            j1 = instructor_lookup.get(assignment.j1_id)
            
            if not project:
                continue
            
            # Sınıf ve timeslot bilgisi
            classroom = classroom_lookup.get(assignment.class_id, {})
            classroom_id = classroom.get("id", assignment.class_id)
            classroom_name = classroom.get("name", f"Sınıf {assignment.class_id + 1}")
            
            # Timeslot hesapla
            timeslot_idx = assignment.order_in_class
            if timeslot_idx < len(self.timeslots):
                timeslot = self.timeslots[timeslot_idx]
                timeslot_id = timeslot.get("id", timeslot_idx)
                start_time = timeslot.get("start_time", f"{9 + timeslot_idx // 2}:{(timeslot_idx % 2) * 30:02d}")
                end_time = timeslot.get("end_time", "")
            else:
                timeslot_id = timeslot_idx
                start_time = f"{9 + timeslot_idx // 2}:{(timeslot_idx % 2) * 30:02d}"
                end_time = ""
            
            # Öğretim görevlileri listesi
            instructors_list = []
            if ps:
                instructors_list.append(ps.id)
            if j1:
                instructors_list.append(j1.id)
            
            # J2 placeholder - SA'daki gibi
            j2_label = assignment.j2_label if hasattr(assignment, 'j2_label') and assignment.j2_label else self.config.j2_placeholder
            
            entry = {
                "project_id": assignment.project_id,
                "project_title": project.title,
                "project_type": project.type,
                "classroom_id": classroom_id,
                "classroom_name": classroom_name,
                "class_id": assignment.class_id,  # SA'daki gibi class_id ekle
                "timeslot_id": timeslot_id,
                "start_time": start_time,
                "end_time": end_time,
                "order_in_class": assignment.order_in_class,
                "instructors": instructors_list,
                "advisor_id": assignment.ps_id,
                "advisor_name": ps.name if ps else "",
                "jury1_id": assignment.j1_id,
                "jury1_name": j1.name if j1 else "",
                "jury2_id": -1,
                "jury2_name": j2_label
            }
            
            schedule.append(entry)
        
        # Sınıf ve sıraya göre sırala
        schedule.sort(key=lambda x: (x.get("class_id", x.get("classroom_id", 0)), x.get("order_in_class", 0)))
        
        # CRITICAL: Final verification - ensure all classes in schedule - SA'daki gibi
        classes_in_schedule = set()
        for item in schedule:
            class_id = item.get("class_id", item.get("classroom_id"))
            if class_id is not None:
                classes_in_schedule.add(class_id)
        
        if len(classes_in_schedule) < solution.class_count:
            logger.warning(f"WARNING: Only {len(classes_in_schedule)} classes in schedule, expected {solution.class_count}")
            logger.warning(f"Missing classes: {[c for c in range(solution.class_count) if c not in classes_in_schedule]}")
        else:
            logger.info(f"SUCCESS: All {solution.class_count} classes are present in schedule")
        
        return schedule
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Çözümün kalitesini değerlendirir.
        
        Args:
            solution: Değerlendirilecek çözüm
            
        Returns:
            float: Çözüm kalitesi skoru (negatif maliyet)
        """
        # Çözümü ACOSolution'a dönüştür
        assignments = solution.get("assignments", solution.get("schedule", []))
        
        aco_solution = ACOSolution(class_count=self.config.class_count)
        
        for entry in assignments:
            assignment = ProjectAssignment(
                project_id=entry.get("project_id"),
                class_id=entry.get("classroom_id", 0),
                order_in_class=entry.get("order_in_class", 0),
                ps_id=entry.get("advisor_id"),
                j1_id=entry.get("jury1_id"),
                j2_label=entry.get("jury2_name", self.config.j2_placeholder)
            )
            aco_solution.assignments.append(assignment)
        
        # Maliyeti hesapla
        if self.scheduler and self.scheduler.penalty_calculator:
            cost = self.scheduler.penalty_calculator.calculate_total_cost(aco_solution)
        else:
            # Basit hesaplama
            penalty_calc = ACOPenaltyCalculator(
                self.projects, self.instructors, self.config
            )
            cost = penalty_calc.calculate_total_cost(aco_solution)
        
        # Fitness = -cost (düşük maliyet = yüksek fitness)
        return -cost
    
    def get_name(self) -> str:
        """Algoritma adını döndürür."""
        return "AntColonyOptimization"

