"""
Genetic Algorithm (Genetik Algoritma) - Cok Kriterli Akademik Proje Sinavi/Juri Planlama

Bu modul, universite donem sonu Ara Proje ve Bitirme Projesi degerlendirme surecleri icin
ileri duzey optimizasyon teknikleri kullanan bir Sinav/Juri Planlama ve Atama Sistemidir.

Temel Ozellikler:
- Her proje icin 3 rol: Proje Sorumlusu (PS), 1. Juri (J1), 2. Juri (placeholder: [Araştırma Görevlisi])
- Back-to-back sinif ici yerlesim
- Timeslotlar arasi gap engelleme
- Is yuku uniformitesi (+/-2 bandi)
- Proje turu onceliklendirme (ARA_ONCE, BITIRME_ONCE, ESIT)
- Cok kriterli amac fonksiyonu: min Z = C1*H1(n) + C2*H2(n) + C3*H3(n)

Matematiksel Model:
- H1: Zaman/Gap Cezasi (ardisik olmayan gorevler)
- H2: Is Yuku Uniformite Cezasi (en kritik - C2 > C1 ve C2 > C3)
- H3: Sinif Degisimi Cezasi

Konfigurasyon:
- priority_mode: {ARA_ONCE, BITIRME_ONCE, ESIT}
- time_penalty_mode: {BINARY, GAP_PROPORTIONAL}
- workload_constraint_mode: {SOFT_ONLY, SOFT_AND_HARD}

GA Operatorleri:
- Selection: Tournament selection with elitism
- Crossover: Class assignment, Order (OX), J1 assignment
- Mutation: J1 swap, J1 reassign, class change, class swap, order swap
- Repair: Constraint-aware repair mechanism
"""

from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random
import copy
import time
import logging
import numpy as np

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# 2. Jüri placeholder metni - atama öncesi ayarlanır
J2_PLACEHOLDER = "[Araştırma Görevlisi]"


# ============================================================================
# CONFIGURATION ENUMS
# ============================================================================

class PriorityMode(str, Enum):
    """Proje turu onceliklendirme modu"""
    ARA_ONCE = "ARA_ONCE"           # Ara projeler once
    BITIRME_ONCE = "BITIRME_ONCE"   # Bitirme projeleri once
    ESIT = "ESIT"                   # Oncelik yok


class TimePenaltyMode(str, Enum):
    """Zaman cezasi modu"""
    BINARY = "BINARY"                       # Ardisik degilse 1 ceza
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Aradaki slot sayisi kadar ceza


class WorkloadConstraintMode(str, Enum):
    """Is yuku kisit modu"""
    SOFT_ONLY = "SOFT_ONLY"           # Sadece ceza
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Ceza + sert kisit


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class GAConfig:
    """Genetic Algorithm konfigurasyon parametreleri"""
    # GA parametreleri (Maliyeti dusurmek icin optimize edildi)
    population_size: int = 150  # Artirildi: daha fazla cesitlilik
    max_generations: int = 300  # Artirildi: daha fazla evrim sansi
    time_limit: int = 300  # Artirildi: daha fazla optimizasyon zamani (saniye)
    no_improve_limit: int = 50  # Artirildi: daha sabirli (iyilesme olmadan max nesil)
    
    # Operatorler
    crossover_rate: float = 0.85
    mutation_rate: float = 0.15
    elitism_rate: float = 0.15  # Artirildi: daha fazla elit koruma
    tournament_size: int = 5
    
    # Sinif sayisi
    class_count: int = 6  # 5, 6 veya 7 olabilir
    auto_class_count: bool = True  # True ise 5,6,7 icin en iyi sec
    
    # Onceliklendirme modu
    priority_mode: PriorityMode = PriorityMode.ESIT
    
    # Zaman cezasi modu
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    
    # Is yuku kisit modu
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4  # B_max: maksimum sapma
    
    # Agirlik katsayilari (C1, C2, C3)
    # min Z = C1*H1(n) + C2*H2(n) + C3*H3(n)
    # C2 > C1 ve C2 > C3 (is yuku en kritik kriter)
    # Real Simplex/Lexicographic/CP-SAT ile uyumlu standart degerler
    weight_h1: float = 10.0   # C1: Zaman/Gap cezasi agirligi
    weight_h2: float = 100.0  # C2: Is yuku cezasi agirligi (en onemli)
    weight_h3: float = 5.0    # C3: Sinif degisimi cezasi agirligi
    
    # Slot suresi
    slot_duration: float = 0.5  # saat (30 dakika)
    tolerance: float = 0.001
    
    # Baslangic stratejisi (Maliyeti dusurmek icin optimize edildi)
    heuristic_init_ratio: float = 0.50  # Artirildi: %50 heuristic, %50 random (daha iyi baslangic)
    
    # Hafiza (Memory) parametreleri (Maliyeti dusurmek icin optimize edildi)
    memory_size: int = 15  # Artirildi: daha fazla cozum sakla
    use_memory: bool = True  # Hafiza kullanilsin mi?
    restart_on_stagnation: bool = True  # Durgunlukta restart yapilsin mi?
    stagnation_generations: int = 30  # Artirildi: daha sabirli restart
    diversity_threshold: float = 0.1  # Populasyon cesitliligi esigi
    adaptive_rates: bool = True  # Adaptif mutation/crossover rates
    
    # Local improvement parametreleri (YENI)
    use_local_improvement: bool = True  # En iyi bireyleri iyilestir
    local_improvement_rate: float = 0.05  # En iyi %5'i iyilestir
    local_improvement_iterations: int = 10  # Her birey icin local search iterasyonu


@dataclass
class Project:
    """Proje veri yapisi"""
    id: int
    title: str
    type: str  # "interim" (Ara) veya "final" (Bitirme)
    responsible_id: int  # Proje Sorumlusu (PS)
    is_makeup: bool = False


@dataclass
class Instructor:
    """Ogretim gorevlisi veri yapisi"""
    id: int
    name: str
    type: str  # "instructor" veya "assistant"


@dataclass 
class ProjectAssignment:
    """Proje atama bilgisi"""
    project_id: int
    class_id: int
    order_in_class: int  # sinif icindeki sira (0-indexed)
    ps_id: int  # Proje Sorumlusu (sabit)
    j1_id: int  # 1. Juri (karar degiskeni)
    j2_id: int = -1  # 2. Juri (placeholder - modele girmez)
    
    def copy(self) -> 'ProjectAssignment':
        """Atamanin kopyasini olustur"""
        return ProjectAssignment(
            project_id=self.project_id,
            class_id=self.class_id,
            order_in_class=self.order_in_class,
            ps_id=self.ps_id,
            j1_id=self.j1_id,
            j2_id=self.j2_id
        )


@dataclass
class Individual:
    """GA bireyi - Tam cozum temsili"""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    fitness: float = float('-inf')
    
    def copy(self) -> 'Individual':
        """Bireyin derin kopyasi"""
        new_ind = Individual(class_count=self.class_count, fitness=self.fitness)
        new_ind.assignments = [a.copy() for a in self.assignments]
        return new_ind
    
    def get_class_projects(self, class_id: int) -> List[ProjectAssignment]:
        """Belirli siniftaki projeleri sirayla getir"""
        class_projects = [a for a in self.assignments if a.class_id == class_id]
        return sorted(class_projects, key=lambda x: x.order_in_class)
    
    def get_project_assignment(self, project_id: int) -> Optional[ProjectAssignment]:
        """Proje atamasini getir"""
        for a in self.assignments:
            if a.project_id == project_id:
                return a
        return None
    
    def get_class_order(self, class_id: int) -> List[int]:
        """Siniftaki proje ID'lerini sirayla getir"""
        class_projects = self.get_class_projects(class_id)
        return [a.project_id for a in class_projects]


# ============================================================================
# PENALTY CALCULATOR
# ============================================================================

class GAPenaltyCalculator:
    """GA icin ceza fonksiyonlari hesaplayici"""
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: GAConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece ogretim gorevlilerini al (asistanlar dahil degil)
        self.faculty_instructors = {
            i.id: i for i in instructors 
            if i.type == "instructor"
        }
        
        # Ortalama is yuku hesapla: L_avg = 2Y / X
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.total_workload = 2 * num_projects  # Her proje 2 gorev: PS + J1
        self.avg_workload = self.total_workload / num_faculty if num_faculty > 0 else 0
    
    def calculate_fitness(self, individual: Individual) -> float:
        """
        Bireyin fitness degerini hesapla.
        
        Fitness = -(C1*H1 + C2*H2 + C3*H3)
        Yuksek fitness = daha iyi cozum
        
        C2 > C1 ve C2 > C3 (is yuku en kritik kriter)
        """
        penalty = self.calculate_total_penalty(individual)
        return -penalty
    
    def calculate_total_penalty(self, individual: Individual) -> float:
        """
        Toplam ceza degerini hesapla.
        
        min Z = C1*H1(n) + C2*H2(n) + C3*H3(n)
        
        H1: Zaman/Gap cezasi (matris tabanli)
        H2: Is yuku uniformite cezasi (soft band: ±2)
        H3: Sinif degisimi cezasi
        
        C2 > C1 ve C2 > C3 (is yuku en kritik kriter)
        """
        h1 = self.calculate_h1_time_penalty(individual)
        h2 = self.calculate_h2_workload_penalty(individual)
        h3 = self.calculate_h3_class_change_penalty(individual)
        
        total = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3
        )
        
        return total
    
    def calculate_h1_time_penalty(self, individual: Individual) -> float:
        """
        H1: Zaman/Gap cezasi - matris tabanli ceza hesaplama.
        
        Her ogretim gorevlisi i icin, her sinif icindeki gorevlerini analiz et.
        SADECE AYNI SINIF ICINDEKI gap'ler cezalandirilir.
        Farkli siniflar arasi gecisler normaldir (paralel siniflar).
        
        BINARY mod: Ardışık değilse 1 ceza
        GAP_PROPORTIONAL mod: gap slot sayisi kadar ceza (g(i,r))
        """
        total_penalty = 0.0
        
        # Her ogretim gorevlisi ve sinif bazinda gorevleri grupla
        instructor_class_tasks = defaultdict(lambda: defaultdict(list))
        
        for assignment in individual.assignments:
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
        
        # Her ogretim gorevlisi ve sinif icin gap kontrolu
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
    
    def calculate_h2_workload_penalty(self, individual: Individual) -> float:
        """
        H2: Is yuku uniformite cezasi.
        
        Her ogretim gorevlisinin is yuku Avg +/- 2 bandinda olmali.
        Bant disindaki her birim icin ceza.
        
        IsYukuCezasi_i = max(0, |GorevSayisi_i - L_avg| - 2)
        H2(n) = sum(IsYukuCezasi_i)
        
        Soft kisim her zaman aktif.
        Sert kisim (B_max) opsiyonel.
        """
        total_penalty = 0.0
        
        # Her ogretim gorevlisi icin gorev sayisini hesapla
        workload = self._calculate_instructor_workloads(individual)
        
        for instructor_id in self.faculty_instructors.keys():
            load = workload.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            
            # Soft ceza: +/- 2 tolerans
            penalty = max(0, deviation - 2)
            total_penalty += penalty
            
            # Sert kisit kontrolu
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.workload_hard_limit:
                    # Hard limit asilmis - ekstra ceza (ama makul seviyede)
                    extra_penalty = (deviation - self.config.workload_hard_limit) * 10
                    total_penalty += extra_penalty
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, individual: Individual) -> float:
        """
        H3: Sinif degisimi cezasi - matris tabanli.
        
        Her ogretim gorevlisi i icin, zaman sirasina gore gorevlerini analiz et.
        Her (r -> r+1) gecisinde:
        - Eger Sinif(i,r+1) ≠ Sinif(i,r) ise sınıf değişimi cezası
        
        H3(n) = Σ Σ SınıfCezası(i,r)
        SınıfCezası(i,r) = 1[Sınıf(i,r+1) ≠ Sınıf(i,r)]
        """
        total_penalty = 0.0
        
        # Her ogretim gorevlisi icin gorev matrisini olustur (saat bilgisi ile)
        instructor_tasks = self._build_instructor_task_matrix_with_time(individual)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Gorevleri zaman sirasina gore sirala (saat, sinif)
            tasks.sort(key=lambda x: (x['time'], x['class_id']))
            
            # Ardisik gorevler arasinda sinif degisimi kontrolu (r -> r+1)
            for r in range(len(tasks) - 1):
                current = tasks[r]
                next_task = tasks[r + 1]
                
                # Sinif degisimi kontrolu
                if current['class_id'] != next_task['class_id']:
                    # Sinif degisimi var - ceza
                    total_penalty += 1.0
        
        return total_penalty
    
    def calculate_h4_class_load_penalty(self, individual: Individual) -> float:
        """
        H4: Sinif is yuku dengesi cezasi.
        
        Her sinifin is yuku hedef degere yakin olmali.
        Target = 2 * num_projects / class_count
        
        AYRICa: Kullanilmayan siniflar icin COK AGIR ceza (HARD KISIT)!
        """
        total_penalty = 0.0
        
        num_projects = len(individual.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = (2 * num_projects) / individual.class_count
        
        # Sinif basina proje sayisi
        class_loads = defaultdict(int)
        for assignment in individual.assignments:
            class_loads[assignment.class_id] += 2  # Her proje 2 is yuku
        
        # Kullanilmayan siniflar icin COK AGIR ceza (HARD KISIT)
        unused_class_penalty = 0.0
        for class_id in range(individual.class_count):
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
    
    def calculate_continuity_penalty(self, individual: Individual) -> float:
        """
        Devamlililk cezasi (ek olarak).
        
        Her ogretim gorevlisi icin her siniftaki blok sayisini hesapla.
        Ideal: 1 blok (arka arkaya gorevler)
        Blocks(h,s) - 1 kadar ceza
        
        Ayrica ayni sinif icinde ardisik olmayan gorevler icin ekstra ceza.
        """
        total_penalty = 0.0
        
        for instructor_id in self.faculty_instructors.keys():
            for class_id in range(individual.class_count):
                blocks = self._count_blocks(individual, instructor_id, class_id)
                # Her ekstra blok icin ceza (ideal: 1 blok)
                penalty = max(0, blocks - 1)
                total_penalty += penalty
                
                # Eger birden fazla blok varsa, ekstra agir ceza
                if blocks > 1:
                    # Her ekstra blok icin kare ceza (cok daha agir)
                    total_penalty += (blocks - 1) * (blocks - 1) * 10  # Kare ceza
        
        # Ayni sinif icinde ardisik olmayan gorevler icin ekstra ceza
        instructor_tasks = self._build_instructor_task_matrix(individual)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Sinif bazinda grupla
            tasks_by_class = defaultdict(list)
            for task in tasks:
                tasks_by_class[task['class_id']].append(task)
            
            # Her sinif icin ardisiklik kontrolu
            for class_id, class_tasks in tasks_by_class.items():
                if len(class_tasks) <= 1:
                    continue
                
                # Sira sirasina gore sirala
                class_tasks.sort(key=lambda x: x['order'])
                
                # Ardisik olmayan gorevler icin ceza
                for i in range(len(class_tasks) - 1):
                    current_order = class_tasks[i]['order']
                    next_order = class_tasks[i + 1]['order']
                    gap = next_order - current_order - 1
                    
                    if gap > 0:
                        # Ardisik degil, ceza ver
                        # Her bos slot icin agir ceza (kare ceza)
                        total_penalty += gap * gap * 5  # Kare ceza daha agir
        
        return total_penalty
    
    def calculate_timeslot_conflict_penalty(self, individual: Individual) -> float:
        """
        Timeslot cakisma cezasi - HARD KISIT.
        
        Ayni timeslot'ta (class_id, order_in_class) ayni ogretim gorevlisi
        birden fazla gorev alamaz. Her cakisma icin cok agir ceza.
        """
        total_penalty = 0.0
        
        # Timeslot bazinda gorev sayisini hesapla
        timeslot_instructors = defaultdict(set)
        
        for assignment in individual.assignments:
            slot_key = (assignment.class_id, assignment.order_in_class)
            timeslot_instructors[slot_key].add(assignment.ps_id)
            timeslot_instructors[slot_key].add(assignment.j1_id)
        
        # Her timeslot icin, her ogretim gorevlisi sadece 1 kez olmali
        for slot_key, instructor_set in timeslot_instructors.items():
            # Eger bir ogretim gorevlisi bu slot'ta birden fazla gorev aliyorsa
            # (PS ve J1 ayni projede olabilir, ama farkli projelerde olamaz)
            # Bu kontrolu yapmak icin proje bazinda kontrol etmeliyiz
            pass
        
        # Daha detayli kontrol: Her timeslot icin proje bazinda kontrol
        timeslot_projects = defaultdict(list)
        for assignment in individual.assignments:
            slot_key = (assignment.class_id, assignment.order_in_class)
            timeslot_projects[slot_key].append(assignment)
        
        for slot_key, assignments in timeslot_projects.items():
            # Bu slot'taki tum ogretim gorevlilerini topla
            instructor_roles = defaultdict(set)  # instructor_id -> {project_id, ...}
            
            for assignment in assignments:
                instructor_roles[assignment.ps_id].add(assignment.project_id)
                instructor_roles[assignment.j1_id].add(assignment.project_id)
            
            # Her ogretim gorevlisi icin, birden fazla projede gorev aliyorsa cakisma var
            for instructor_id, project_set in instructor_roles.items():
                if len(project_set) > 1:
                    # CAKISMA! Bu hoca ayni slot'ta birden fazla projede gorev aliyor
                    total_penalty += len(project_set) - 1  # Her ekstra proje icin ceza
        
        return total_penalty
    
    def _build_instructor_task_matrix(
        self, 
        individual: Individual
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Her ogretim gorevlisi icin gorev matrisi olustur.
        
        M_i matrisi (k_i x 2):
        M_i[r,0] = Saat(i,r)
        M_i[r,1] = Sinif(i,r)
        """
        instructor_tasks = defaultdict(list)
        
        for assignment in individual.assignments:
            # PS gorevi
            instructor_tasks[assignment.ps_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'PS'
            })
            
            # J1 gorevi
            instructor_tasks[assignment.j1_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'J1'
            })
        
        return instructor_tasks
    
    def _build_instructor_task_matrix_with_time(
        self, 
        individual: Individual
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Her ogretim gorevlisi icin saat bilgili gorev matrisi olustur.
        
        M_i matrisi (k_i x 2):
        M_i[r,0] = Saat(i,r) - zaman bilgisi (saat cinsinden, orn: 9.0, 9.5, 10.0)
        M_i[r,1] = Sinif(i,r) - sinif bilgisi
        
        Saat hesaplama: Baslangic saati (9.0) + order * slot_duration
        """
        instructor_tasks = defaultdict(list)
        
        # Baslangic saati (9:00 = 9.0 saat)
        start_time = 9.0
        
        for assignment in individual.assignments:
            # Saat hesapla: baslangic + order * slot_duration
            task_time = start_time + assignment.order_in_class * self.config.slot_duration
            
            # PS gorevi
            instructor_tasks[assignment.ps_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'time': task_time,
                'role': 'PS'
            })
            
            # J1 gorevi
            instructor_tasks[assignment.j1_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'time': task_time,
                'role': 'J1'
            })
        
        return instructor_tasks
    
    def _calculate_instructor_workloads(
        self, 
        individual: Individual
    ) -> Dict[int, int]:
        """
        Her ogretim gorevlisi icin toplam is yukunu hesapla.
        
        GorevSayisi_i = sum_p(x_i,p^Sorumlu + x_i,p^Juri1)
        """
        workload = defaultdict(int)
        
        for assignment in individual.assignments:
            workload[assignment.ps_id] += 1
            workload[assignment.j1_id] += 1
        
        return workload
    
    def _count_blocks(
        self, 
        individual: Individual, 
        instructor_id: int, 
        class_id: int
    ) -> int:
        """
        Ogretim gorevlisinin belirli siniftaki blok sayisini hesapla.
        
        0->1 gecislerini say (blok sayisi)
        """
        class_projects = individual.get_class_projects(class_id)
        
        if not class_projects:
            return 0
        
        # Binary presence dizisi olustur
        presence = []
        for assignment in class_projects:
            is_present = (assignment.ps_id == instructor_id or 
                         assignment.j1_id == instructor_id)
            presence.append(1 if is_present else 0)
        
        if sum(presence) == 0:
            return 0
        
        # 0->1 gecislerini say (blok sayisi)
        blocks = 0
        for i in range(len(presence)):
            if presence[i] == 1:
                if i == 0 or presence[i-1] == 0:
                    blocks += 1
        
        return blocks


# ============================================================================
# GENETIC OPERATORS
# ============================================================================

class GeneticOperators:
    """GA operatorleri: Selection, Crossover, Mutation"""
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: GAConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.project_list = projects
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece ogretim gorevlileri
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    # =========================================================================
    # SELECTION
    # =========================================================================
    
    def tournament_selection(
        self, 
        population: List[Individual], 
        tournament_size: int = None
    ) -> Individual:
        """
        Tournament selection.
        
        Rastgele tournament_size kadar birey sec, en iyi fitness'a sahip olani dondur.
        """
        if tournament_size is None:
            tournament_size = self.config.tournament_size
        
        tournament = random.sample(population, min(tournament_size, len(population)))
        winner = max(tournament, key=lambda x: x.fitness)
        return winner
    
    def select_parents(
        self, 
        population: List[Individual], 
        count: int
    ) -> List[Individual]:
        """count kadar ebeveyn sec"""
        parents = []
        for _ in range(count):
            parent = self.tournament_selection(population)
            parents.append(parent)
        return parents
    
    def apply_elitism(
        self, 
        population: List[Individual], 
        new_population: List[Individual]
    ) -> List[Individual]:
        """
        Elitism uygula.
        
        En iyi %elitism_rate birey direkt tasinir.
        """
        elite_count = max(1, int(len(population) * self.config.elitism_rate))
        
        # Populasyonu fitness'a gore sirala
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
        elites = [ind.copy() for ind in sorted_pop[:elite_count]]
        
        # Yeni populasyonun en kotuleri ile degistir
        new_sorted = sorted(new_population, key=lambda x: x.fitness, reverse=True)
        
        # Elitleri en iyi pozisyonlara ekle (zaten iyi ise degistirme)
        result = []
        for i, ind in enumerate(new_sorted):
            if i < len(elites) and elites[i].fitness > ind.fitness:
                result.append(elites[i])
            else:
                result.append(ind)
        
        return result
    
    # =========================================================================
    # CROSSOVER
    # =========================================================================
    
    def crossover(
        self, 
        parent1: Individual, 
        parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """
        Uc parcali crossover uygula:
        1. Class Assignment Crossover
        2. Order Crossover (OX)
        3. J1 Assignment Crossover
        
        Returns:
            Iki cocuk birey
        """
        if random.random() > self.config.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        child1 = Individual(class_count=parent1.class_count)
        child2 = Individual(class_count=parent2.class_count)
        
        # Tum proje ID'lerini al
        project_ids = list(self.projects.keys())
        
        # Crossover noktasi
        crossover_point = random.randint(1, len(project_ids) - 1)
        
        # Child 1: Ilk bolum parent1'den, ikinci bolum parent2'den
        # Child 2: Ilk bolum parent2'den, ikinci bolum parent1'den
        for i, pid in enumerate(project_ids):
            p1_assign = parent1.get_project_assignment(pid)
            p2_assign = parent2.get_project_assignment(pid)
            
            if p1_assign is None or p2_assign is None:
                continue
            
            if i < crossover_point:
                # Child1 <- Parent1, Child2 <- Parent2
                child1.assignments.append(p1_assign.copy())
                child2.assignments.append(p2_assign.copy())
            else:
                # Child1 <- Parent2, Child2 <- Parent1
                child1.assignments.append(p2_assign.copy())
                child2.assignments.append(p1_assign.copy())
        
        return child1, child2
    
    def uniform_crossover(
        self, 
        parent1: Individual, 
        parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """
        Uniform crossover.
        
        Her proje icin rastgele ebeveyn sec.
        """
        if random.random() > self.config.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        child1 = Individual(class_count=parent1.class_count)
        child2 = Individual(class_count=parent2.class_count)
        
        for pid in self.projects.keys():
            p1_assign = parent1.get_project_assignment(pid)
            p2_assign = parent2.get_project_assignment(pid)
            
            if p1_assign is None or p2_assign is None:
                continue
            
            if random.random() < 0.5:
                child1.assignments.append(p1_assign.copy())
                child2.assignments.append(p2_assign.copy())
            else:
                child1.assignments.append(p2_assign.copy())
                child2.assignments.append(p1_assign.copy())
        
        return child1, child2
    
    def order_crossover_ox(
        self, 
        parent1: Individual, 
        parent2: Individual,
        class_id: int
    ) -> Tuple[List[int], List[int]]:
        """
        Order Crossover (OX) - Sinif ici proje sirasi icin.
        
        Sira bazli permutasyon crossover.
        """
        order1 = parent1.get_class_order(class_id)
        order2 = parent2.get_class_order(class_id)
        
        if len(order1) <= 2 or len(order2) <= 2:
            return order1, order2
        
        size = len(order1)
        
        # Iki kesim noktasi sec
        start = random.randint(0, size - 2)
        end = random.randint(start + 1, size - 1)
        
        # Child 1
        child1 = [None] * size
        child1[start:end] = order1[start:end]
        
        # Kalan elemanlari order2'den siraya gore ekle
        remaining = [x for x in order2 if x not in child1]
        idx = 0
        for i in range(size):
            if child1[i] is None:
                if idx < len(remaining):
                    child1[i] = remaining[idx]
                    idx += 1
        
        # Child 2
        child2 = [None] * size
        child2[start:end] = order2[start:end]
        
        remaining = [x for x in order1 if x not in child2]
        idx = 0
        for i in range(size):
            if child2[i] is None:
                if idx < len(remaining):
                    child2[i] = remaining[idx]
                    idx += 1
        
        return child1, child2
    
    # =========================================================================
    # MUTATION
    # =========================================================================
    
    def mutate(self, individual: Individual) -> Individual:
        """
        Mutation operatorlerini uygula.
        
        Mutation tipleri (Tabu Search komsuluk hamlelerine benzer):
        - J1 swap (ayni sinif)
        - J1 reassign
        - Class change
        - Class swap
        - Order swap (sinif ici)
        """
        if random.random() > self.config.mutation_rate:
            return individual
        
        mutated = individual.copy()
        
        # Rastgele bir mutation tipi sec
        mutation_type = random.choice([
            'j1_swap',
            'j1_reassign',
            'class_change',
            'class_swap',
            'order_swap'
        ])
        
        if mutation_type == 'j1_swap':
            self._mutate_j1_swap(mutated)
        elif mutation_type == 'j1_reassign':
            self._mutate_j1_reassign(mutated)
        elif mutation_type == 'class_change':
            self._mutate_class_change(mutated)
        elif mutation_type == 'class_swap':
            self._mutate_class_swap(mutated)
        elif mutation_type == 'order_swap':
            self._mutate_order_swap(mutated)
        
        return mutated
    
    def _mutate_j1_swap(self, individual: Individual) -> None:
        """
        J1 Swap: Ayni siniftaki iki projenin J1'lerini degistir.
        """
        class_id = random.randint(0, individual.class_count - 1)
        class_projects = individual.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return
        
        # Iki proje sec
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        # Kendi projesine juri olma kontrolu
        if p1.j1_id == p2.ps_id or p2.j1_id == p1.ps_id:
            return
        
        # J1'leri swap et
        for a in individual.assignments:
            if a.project_id == p1.project_id:
                a.j1_id = p2.j1_id
            elif a.project_id == p2.project_id:
                a.j1_id = p1.j1_id
    
    def _mutate_j1_reassign(self, individual: Individual) -> None:
        """
        J1 Reassign: Bir projenin J1'ini degistir.
        """
        if not individual.assignments:
            return
        
        assignment = random.choice(individual.assignments)
        project = self.projects.get(assignment.project_id)
        
        if not project:
            return
        
        # PS haric ogretim gorevlilerinden sec
        available_j1 = [
            i_id for i_id in self.faculty_ids 
            if i_id != project.responsible_id and i_id != assignment.j1_id
        ]
        
        if not available_j1:
            return
        
        new_j1 = random.choice(available_j1)
        
        for a in individual.assignments:
            if a.project_id == assignment.project_id:
                a.j1_id = new_j1
                break
    
    def _mutate_class_change(self, individual: Individual) -> None:
        """
        Class Change: Bir projeyi baska sinifa tasi.
        """
        if not individual.assignments:
            return
        
        assignment = random.choice(individual.assignments)
        old_class = assignment.class_id
        
        # Farkli bir sinif sec
        available_classes = [
            c for c in range(individual.class_count) 
            if c != old_class
        ]
        
        if not available_classes:
            return
        
        new_class = random.choice(available_classes)
        
        # Yeni sinifin sonuna ekle
        new_class_count = sum(
            1 for a in individual.assignments 
            if a.class_id == new_class and a.project_id != assignment.project_id
        )
        
        for a in individual.assignments:
            if a.project_id == assignment.project_id:
                a.class_id = new_class
                a.order_in_class = new_class_count
                break
        
        # Eski siniftaki siralari yeniden duzelt
        self._reorder_class(individual, old_class)
    
    def _mutate_class_swap(self, individual: Individual) -> None:
        """
        Class Swap: Farkli siniflardaki iki projenin siniflarini degistir.
        """
        if len(individual.assignments) < 2:
            return
        
        # Farkli siniflarda iki proje sec
        assignments = individual.assignments.copy()
        random.shuffle(assignments)
        
        p1 = assignments[0]
        p2 = None
        
        for a in assignments[1:]:
            if a.class_id != p1.class_id:
                p2 = a
                break
        
        if p2 is None:
            return
        
        # Swap
        for a in individual.assignments:
            if a.project_id == p1.project_id:
                a.class_id = p2.class_id
                a.order_in_class = p2.order_in_class
            elif a.project_id == p2.project_id:
                a.class_id = p1.class_id
                a.order_in_class = p1.order_in_class
    
    def _mutate_order_swap(self, individual: Individual) -> None:
        """
        Order Swap: Ayni siniftaki iki projenin sirasini degistir.
        """
        class_id = random.randint(0, individual.class_count - 1)
        class_projects = individual.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return
        
        # Iki proje sec
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        # Siralari swap et
        for a in individual.assignments:
            if a.project_id == p1.project_id:
                a.order_in_class = p2.order_in_class
            elif a.project_id == p2.project_id:
                a.order_in_class = p1.order_in_class
    
    def _reorder_class(self, individual: Individual, class_id: int) -> None:
        """Sinif icindeki siralari yeniden duzelt (0'dan baslayarak ardisik)"""
        class_projects = [a for a in individual.assignments if a.class_id == class_id]
        class_projects.sort(key=lambda x: x.order_in_class)
        
        for i, a in enumerate(class_projects):
            for assignment in individual.assignments:
                if assignment.project_id == a.project_id:
                    assignment.order_in_class = i
                    break


# ============================================================================
# REPAIR MECHANISM
# ============================================================================

class GARepairMechanism:
    """GA icin onarim mekanizmasi - kisirlari zorla"""
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: GAConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.project_list = projects
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece ogretim gorevlileri
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
        
        # Ortalama is yuku
        num_projects = len(projects)
        num_faculty = len(self.faculty_ids)
        self.avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
    
    def repair(self, individual: Individual) -> Individual:
        """
        Bireyi onar - tum hard kisitlari zorla.
        
        Onarilan kisitlar:
        1. PS sabit olmali
        2. J1 != PS(p) - kendi projesine juri olamaz
        3. Her proje tam 1 J1
        4. Sinif ici bosluk yok (back-to-back)
        5. Her ogretim gorevlisi ayni anda 1 gorevden fazla alamaz
        6. Tum projeler atanmali
        7. priority_mode gereği ara/bitirme sirasi
        8. Is yuku hard limit (opsiyonel)
        """
        # 1. PS duzeltme (zaten sabit olmali)
        self._repair_ps_assignments(individual)
        
        # 2. J1 != PS kontrolu
        self._repair_j1_not_ps(individual)
        
        # 3. Eksik J1 atamalari
        self._repair_missing_j1(individual)
        
        # 4. Back-to-back (sinif ici siralama)
        self._repair_class_ordering(individual)
        
        # 5. Timeslot cakismalari
        self._repair_timeslot_conflicts(individual)
        
        # 6. Tum projelerin atanmasi
        self._repair_missing_projects(individual)
        
        # 7. Ara/Bitirme sirasi (priority_mode)
        self._repair_priority_order(individual)
        
        # 8. Is yuku hard limit
        if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
            self._repair_workload_hard_limit(individual)
        
        # 8b. Is yuku rebalancing (YENI - H2 weight=100 oldugu icin cok kritik!)
        self._rebalance_workload(individual)
        
        # 9. Tum siniflarin kullanildigindan emin ol (ONCE - diger repair'ler sinif dagilimini bozabilir)
        self._repair_all_classes_used(individual)
        
        # 10. Continuity (devamlilik) iyilestirmesi - Cok agresif
        self._repair_continuity(individual)
        
        # 11. Sinif degisikliklerini minimize et
        self._repair_minimize_class_changes(individual)
        
        # 12. Tekrar is yuku rebalancing (repair'ler sonrasi)
        self._rebalance_workload(individual)
        
        # 13. Tekrar tum siniflarin kullanildigindan emin ol (repair'ler sonrasi)
        self._repair_all_classes_used(individual)
        
        return individual
    
    def _repair_ps_assignments(self, individual: Individual) -> None:
        """PS atamalarini duzelt - projenin sorumlususu dogru olmali"""
        for assignment in individual.assignments:
            project = self.projects.get(assignment.project_id)
            if project and assignment.ps_id != project.responsible_id:
                assignment.ps_id = project.responsible_id
    
    def _repair_j1_not_ps(self, individual: Individual) -> None:
        """J1 != PS kuralini zorla"""
        for assignment in individual.assignments:
            if assignment.j1_id == assignment.ps_id:
                # Yeni J1 sec
                available = [
                    i_id for i_id in self.faculty_ids 
                    if i_id != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_missing_j1(self, individual: Individual) -> None:
        """Eksik J1 atamasini duzelt"""
        for assignment in individual.assignments:
            if assignment.j1_id <= 0 or assignment.j1_id not in self.instructors:
                available = [
                    i_id for i_id in self.faculty_ids 
                    if i_id != assignment.ps_id
                ]
                if available:
                    assignment.j1_id = random.choice(available)
    
    def _repair_class_ordering(self, individual: Individual) -> None:
        """
        Sinif ici siralama duzelt - back-to-back, bosluksuz.
        Her sinif icin projeleri 0'dan baslayarak sirala.
        """
        for class_id in range(individual.class_count):
            class_projects = [a for a in individual.assignments if a.class_id == class_id]
            class_projects.sort(key=lambda x: x.order_in_class)
            
            for i, a in enumerate(class_projects):
                for assignment in individual.assignments:
                    if assignment.project_id == a.project_id:
                        assignment.order_in_class = i
                        break
    
    def _repair_timeslot_conflicts(self, individual: Individual) -> None:
        """
        Timeslot cakismalarini duzelt - PSO yaklasimiyla.
        
        KRITIK: order_in_class = timeslot_id (TUM siniflarda!)
        Ayni order'da FARKLI siniflarda bile olsa, ayni ogretim gorevlisi
        birden fazla gorev alamaz. Bu HARD KISIT!
        
        PSO'dan alinan cozum:
        1. instructor_busy map olustur: instructor_id -> set of busy order_in_class
        2. Sorumlulari (PS) once yerlestir (sabittir, degistirilemez)
        3. J1 cakismalarini duzelt: musait J1 bul veya projeyi tasi
        """
        max_iterations = 100
        
        for iteration in range(max_iterations):
            # instructor_id -> set of order_in_class (busy slots)
            instructor_busy: Dict[int, Set[int]] = defaultdict(set)
            
            # Once sorumlulari (PS) yerlestir - bunlar degistirilemez
            for assignment in individual.assignments:
                if assignment.ps_id:
                    instructor_busy[assignment.ps_id].add(assignment.order_in_class)
            
            # Simdi J1'leri kontrol et ve cakismalari duzelt
            conflicts_fixed = 0
            
            for assignment in individual.assignments:
                j1_id = assignment.j1_id
                order = assignment.order_in_class
                ps_id = assignment.ps_id
                
                # J1 bu slot'ta zaten mesgul mu?
                if j1_id and order in instructor_busy.get(j1_id, set()):
                    # CAKISMA! J1'i degistirmemiz lazim
                    conflicts_fixed += 1
                    
                    # Musait J1 bul (bu order'da mesgul olmayan ve PS'den farkli)
                    available_j1 = []
                    for candidate_id in self.faculty_ids:
                        if candidate_id == ps_id:
                            continue  # J1 != PS
                        if order in instructor_busy.get(candidate_id, set()):
                            continue  # Bu slot'ta mesgul
                        available_j1.append(candidate_id)
                    
                    if available_j1:
                        # Is yukune gore en az yuklu olani sec
                        workloads = self._calculate_workloads(individual)
                        available_j1.sort(key=lambda x: workloads.get(x, 0))
                        new_j1 = available_j1[0]
                        assignment.j1_id = new_j1
                        instructor_busy[new_j1].add(order)
                    else:
                        # Musait J1 yok - projeyi baska slot'a tasimamiz lazim
                        moved = self._move_project_to_conflict_free_slot(individual, assignment, instructor_busy)
                        if moved:
                            # Tum busy map'i yeniden olustur (proje taşındı)
                            break
                else:
                    # J1 cakismiyor, busy map'e ekle
                    if j1_id:
                        instructor_busy[j1_id].add(order)
            
            # Cakisma kalmadiysa dur
            if conflicts_fixed == 0:
                break
        
        # Son kontrol: hala cakisma var mi?
        final_conflicts = self._count_timeslot_conflicts(individual)
        if final_conflicts > 0:
            logger.warning(f"GA Repair: {final_conflicts} timeslot conflict(s) could not be resolved after {max_iterations} iterations")
    
    def _calculate_workloads(self, individual: Individual) -> Dict[int, int]:
        """Her ogretim gorevlisinin toplam is yukunu hesapla"""
        workloads: Dict[int, int] = defaultdict(int)
        for assignment in individual.assignments:
            workloads[assignment.ps_id] += 1
            workloads[assignment.j1_id] += 1
        return workloads
    
    def _move_project_to_conflict_free_slot(
        self, 
        individual: Individual, 
        assignment: ProjectAssignment,
        instructor_busy: Dict[int, Set[int]]
    ) -> bool:
        """
        Projeyi cakisma olmayan bir slot'a tasi.
        PS ve J1'in ikisinin de musait oldugu bir slot bul.
        """
        ps_id = assignment.ps_id
        j1_id = assignment.j1_id
        old_class_id = assignment.class_id
        
        # Tum sinif ve order kombinasyonlarini dene
        for new_class_id in range(individual.class_count):
            # Bu siniftaki mevcut proje sayisi
            class_projects = [a for a in individual.assignments if a.class_id == new_class_id and a.project_id != assignment.project_id]
            new_order = len(class_projects)
            
            # PS bu slot'ta mesgul mu?
            ps_busy = new_order in instructor_busy.get(ps_id, set())
            
            if ps_busy:
                continue  # PS mesgul, bu slot kullanılamaz
            
            # J1 bu slot'ta mesgul mu?
            j1_busy = new_order in instructor_busy.get(j1_id, set())
            
            if not j1_busy:
                # Hem PS hem J1 musait - projeyi tasi!
                assignment.class_id = new_class_id
                assignment.order_in_class = new_order
                self._reorder_class(individual, old_class_id)
                self._reorder_class(individual, new_class_id)
                return True
            else:
                # PS musait ama J1 mesgul - yeni J1 bul
                available_j1 = []
                for candidate_id in self.faculty_ids:
                    if candidate_id == ps_id:
                        continue
                    if new_order in instructor_busy.get(candidate_id, set()):
                        continue
                    available_j1.append(candidate_id)
                
                if available_j1:
                    # Is yukune gore en az yuklu olani sec
                    workloads = self._calculate_workloads(individual)
                    available_j1.sort(key=lambda x: workloads.get(x, 0))
                    assignment.j1_id = available_j1[0]
                    assignment.class_id = new_class_id
                    assignment.order_in_class = new_order
                    self._reorder_class(individual, old_class_id)
                    self._reorder_class(individual, new_class_id)
                    return True
        
        return False
    
    def _count_timeslot_conflicts(self, individual: Individual) -> int:
        """Toplam timeslot cakisma sayisini say"""
        # order -> list of (instructor_id, role)
        order_instructors: Dict[int, List[Tuple[int, str]]] = defaultdict(list)
        
        for assignment in individual.assignments:
            order = assignment.order_in_class
            order_instructors[order].append((assignment.ps_id, 'PS'))
            order_instructors[order].append((assignment.j1_id, 'J1'))
        
        conflicts = 0
        for order, instructor_list in order_instructors.items():
            instructor_counts: Dict[int, int] = defaultdict(int)
            for instructor_id, role in instructor_list:
                instructor_counts[instructor_id] += 1
            
            for instructor_id, count in instructor_counts.items():
                if count > 1:
                    conflicts += count - 1
        
        return conflicts
    
    def _has_timeslot_conflict(
        self, 
        individual: Individual, 
        instructor_id: int, 
        class_id: int, 
        order: int,
        exclude_project_id: int
    ) -> bool:
        """
        Bu ogretim gorevlisi bu timeslot'ta zaten gorev aliyor mu?
        
        KRITIK: Ayni order_in_class = Ayni timeslot (TUM siniflarda!)
        Bir ogretim gorevlisi ayni order'da FARKLI siniflarda bile olsa
        birden fazla gorev alamaz - bu HARD kisit!
        """
        for assignment in individual.assignments:
            if assignment.project_id == exclude_project_id:
                continue
            
            # AYNI ORDER = AYNI TIMESLOT (tum siniflarda)
            if assignment.order_in_class == order:
                if (assignment.ps_id == instructor_id or 
                    assignment.j1_id == instructor_id):
                    return True
        return False
    
    def _move_project_to_new_slot(
        self, 
        individual: Individual, 
        project_id: int, 
        old_class_id: int, 
        old_order: int
    ) -> None:
        """Projeyi yeni bir timeslot'a tasi (cakisma yok)"""
        assignment = individual.get_project_assignment(project_id)
        if not assignment:
            return
        
        # Yeni slot bul (cakisma olmayan)
        best_slot = None
        best_penalty = float('inf')
        
        for new_class_id in range(individual.class_count):
            class_projects = [
                a for a in individual.assignments 
                if a.class_id == new_class_id and a.project_id != project_id
            ]
            new_order = len(class_projects)
            
            # Bu slot'ta cakisma var mi?
            has_conflict = (
                self._has_timeslot_conflict(
                    individual, assignment.ps_id, new_class_id, new_order, project_id
                ) or
                self._has_timeslot_conflict(
                    individual, assignment.j1_id, new_class_id, new_order, project_id
                )
            )
            
            if not has_conflict:
                # Cakisma yok, bu slot'u kullan
                assignment.class_id = new_class_id
                assignment.order_in_class = new_order
                self._reorder_class(individual, old_class_id)
                self._reorder_class(individual, new_class_id)
                return
        
        # Eger hic cakisma olmayan slot bulunamazsa, en az cakismali slot'a tasi
        # (PS cakismasi olmayan slot tercih et)
        for new_class_id in range(individual.class_count):
            class_projects = [
                a for a in individual.assignments 
                if a.class_id == new_class_id and a.project_id != project_id
            ]
            new_order = len(class_projects)
            
            # PS cakismasi yok mu?
            ps_conflict = self._has_timeslot_conflict(
                individual, assignment.ps_id, new_class_id, new_order, project_id
            )
            
            if not ps_conflict:
                # PS cakismasi yok, J1'i degistir
                assignment.class_id = new_class_id
                assignment.order_in_class = new_order
                
                # J1'i degistir
                available_j1 = [
                    i_id for i_id in self.faculty_ids 
                    if i_id != assignment.ps_id and
                    not self._has_timeslot_conflict(
                        individual, i_id, new_class_id, new_order, project_id
                    )
                ]
                
                if available_j1:
                    assignment.j1_id = random.choice(available_j1)
                
                self._reorder_class(individual, old_class_id)
                self._reorder_class(individual, new_class_id)
                return
        
        # Son care: rastgele slot'a tasi ve J1'i degistir
        new_class_id = random.randint(0, individual.class_count - 1)
        class_projects = [
            a for a in individual.assignments 
            if a.class_id == new_class_id and a.project_id != project_id
        ]
        new_order = len(class_projects)
        
        assignment.class_id = new_class_id
        assignment.order_in_class = new_order
        
        # J1'i mutlaka degistir
        available_j1 = [
            i_id for i_id in self.faculty_ids 
            if i_id != assignment.ps_id and
            not self._has_timeslot_conflict(
                individual, i_id, new_class_id, new_order, project_id
            )
        ]
        
        if available_j1:
            assignment.j1_id = random.choice(available_j1)
        
        self._reorder_class(individual, old_class_id)
        self._reorder_class(individual, new_class_id)
    
    def _repair_missing_projects(self, individual: Individual) -> None:
        """Eksik projeleri ekle"""
        assigned_ids = {a.project_id for a in individual.assignments}
        
        for project in self.project_list:
            if project.id not in assigned_ids:
                # Proje eksik, ekle
                # En az yuke sahip sinifi bul
                class_loads = defaultdict(int)
                for a in individual.assignments:
                    class_loads[a.class_id] += 1
                
                min_class = min(
                    range(individual.class_count), 
                    key=lambda c: class_loads.get(c, 0)
                )
                order = class_loads.get(min_class, 0)
                
                # J1 sec
                available_j1 = [
                    i_id for i_id in self.faculty_ids 
                    if i_id != project.responsible_id
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
                individual.assignments.append(assignment)
    
    def _repair_priority_order(self, individual: Individual) -> None:
        """
        Ara/Bitirme sirasini duzelt (priority_mode'a gore).
        
        ARA_ONCE: Tum Ara projeler Bitirme projelerden once
        BITIRME_ONCE: Tum Bitirme projeler Ara projelerden once
        ESIT: Degisiklik yapma
        """
        if self.config.priority_mode == PriorityMode.ESIT:
            return
        
        reordered_count = 0
        
        # Her sinif icin siralama kontrolu
        for class_id in range(individual.class_count):
            class_projects = individual.get_class_projects(class_id)
            
            if not class_projects:
                continue
            
            # Projeleri turlerine gore ayir (case-insensitive)
            ara_projects = []
            bitirme_projects = []
            
            for a in class_projects:
                project = self.projects.get(a.project_id)
                if project:
                    project_type = str(project.type).lower()
                    if project_type in ('interim', 'ara'):
                        ara_projects.append(a)
                    elif project_type in ('final', 'bitirme'):
                        bitirme_projects.append(a)
                    else:
                        # Diğer türler (bilinmeyen) - bitirme olarak kabul et
                        bitirme_projects.append(a)
            
            # CRITICAL: Shuffle within same type to get different results each run
            random.shuffle(ara_projects)
            random.shuffle(bitirme_projects)
            
            # Siralama
            if self.config.priority_mode == PriorityMode.ARA_ONCE:
                # Ara once, sonra Bitirme
                sorted_projects = ara_projects + bitirme_projects
            else:  # BITIRME_ONCE
                # Bitirme once, sonra Ara
                sorted_projects = bitirme_projects + ara_projects
            
            # Siralari guncelle - DÜZELTME: break kaldırıldı, her proje için güncelleme yapılıyor
            for i, a in enumerate(sorted_projects):
                for assignment in individual.assignments:
                    if assignment.project_id == a.project_id:
                        if assignment.order_in_class != i:
                            reordered_count += 1
                        assignment.order_in_class = i
                        break  # Bu break doğru - iç döngüden çık
            
    def _repair_workload_hard_limit(self, individual: Individual) -> None:
        """
        Is yuku hard limit'i zorla.
        
        |GorevSayisi_i - L_avg| <= B_max
        """
        max_iterations = 100
        iteration = 0
        
        while iteration < max_iterations:
            workloads = self._calculate_workloads(individual)
            
            # Limit asilanlari bul
            overloaded = []
            underloaded = []
            
            for instructor_id in self.faculty_ids:
                load = workloads.get(instructor_id, 0)
                deviation = load - self.avg_workload
                
                if deviation > self.config.workload_hard_limit:
                    overloaded.append((instructor_id, load))
                elif deviation < -self.config.workload_hard_limit:
                    underloaded.append((instructor_id, load))
            
            if not overloaded:
                break
            
            # Overloaded hocadan bir J1 gorevi al, underloaded'a ver
            for over_id, _ in overloaded:
                # Bu hocanin J1 oldugu bir proje bul
                for a in individual.assignments:
                    if a.j1_id == over_id:
                        # Yeni J1 sec (underloaded'dan veya normal)
                        if underloaded:
                            new_j1 = underloaded[0][0]
                        else:
                            available = [
                                i for i in self.faculty_ids 
                                if i != a.ps_id and i != over_id
                            ]
                            if not available:
                                continue
                            new_j1 = min(available, key=lambda x: workloads.get(x, 0))
                        
                        if new_j1 != a.ps_id:
                            a.j1_id = new_j1
                            break
            
            iteration += 1
    
    def _rebalance_workload(self, individual: Individual) -> None:
        """
        Is yuku dagilimini agresif sekilde optimize et.
        
        H2'nin weight'i 100 oldugu icin, is yuku dagilimi en kritik faktor.
        Bu metod, is yuku dagilimini ±2 bandina getirmeye calisir.
        """
        max_iterations = 200  # Daha fazla iterasyon - cok kritik!
        iteration = 0
        
        while iteration < max_iterations:
            workloads = self._calculate_workloads(individual)
            
            # Band disindaki hocalari bul (±2 tolerans)
            overloaded = []  # Avg + 2'den fazla
            underloaded = []  # Avg - 2'den az
            
            for instructor_id in self.faculty_ids:
                load = workloads.get(instructor_id, 0)
                deviation = load - self.avg_workload
                
                if deviation > 2:
                    overloaded.append((instructor_id, load, deviation))
                elif deviation < -2:
                    underloaded.append((instructor_id, load, deviation))
            
            # Eger band disinda kisi yoksa, islem tamam
            if not overloaded and not underloaded:
                break
            
            # Overloaded'dan underloaded'a J1 transferi yap
            improved = False
            
            # En fazla overloaded olanlardan basla
            overloaded.sort(key=lambda x: x[2], reverse=True)
            
            for over_id, over_load, over_dev in overloaded:
                # Bu hocanin J1 oldugu projeleri bul
                j1_assignments = [
                    a for a in individual.assignments
                    if a.j1_id == over_id
                ]
                
                if not j1_assignments:
                    continue
                
                # Underloaded hocalari bul (en az yuklu olanlar)
                if underloaded:
                    underloaded.sort(key=lambda x: x[2])  # En az olanlar oncelikli
                    
                    for under_id, under_load, under_dev in underloaded:
                        # Bu projeyi underloaded hocaya verebilir miyiz?
                        for assignment in j1_assignments:
                            # PS kontrolu
                            if assignment.ps_id == under_id:
                                continue
                            
                            # Timeslot cakismasi kontrolu
                            if self._has_timeslot_conflict_for_j1(
                                individual, under_id, assignment
                            ):
                                continue
                            
                            # Transfer et
                            assignment.j1_id = under_id
                            improved = True
                            
                            # Workload'leri guncelle
                            workloads[over_id] -= 1
                            workloads[under_id] = workloads.get(under_id, 0) + 1
                            
                            break
                        
                        if improved:
                            break
                else:
                    # Underloaded yok, en az yuklu normal hocaya ver
                    available = [
                        i for i in self.faculty_ids
                        if i != over_id and workloads.get(i, 0) < over_load
                    ]
                    
                    if not available:
                        continue
                    
                    # En az yuklu olan sec
                    target_id = min(available, key=lambda x: workloads.get(x, 0))
                    
                    for assignment in j1_assignments:
                        if assignment.ps_id == target_id:
                            continue
                        
                        if self._has_timeslot_conflict_for_j1(
                            individual, target_id, assignment
                        ):
                            continue
                        
                        assignment.j1_id = target_id
                        improved = True
                        break
                
                if improved:
                    break
            
            if not improved:
                break
            
            iteration += 1
    
    def _has_timeslot_conflict_for_j1(
        self,
        individual: Individual,
        j1_id: int,
        assignment: ProjectAssignment
    ) -> bool:
        """J1 atamasinda timeslot cakismasi var mi?"""
        slot_key = (assignment.class_id, assignment.order_in_class)
        
        for a in individual.assignments:
            if a.project_id == assignment.project_id:
                continue
            
            if (a.class_id, a.order_in_class) == slot_key:
                # Ayni slot'ta baska bir proje var
                if a.ps_id == j1_id or a.j1_id == j1_id:
                    return True
        
        return False
    
    def _calculate_workloads(self, individual: Individual) -> Dict[int, int]:
        """Is yuklerini hesapla"""
        workloads = defaultdict(int)
        for a in individual.assignments:
            workloads[a.ps_id] += 1
            workloads[a.j1_id] += 1
        return workloads
    
    def _reorder_class(self, individual: Individual, class_id: int) -> None:
        """Sinif icindeki siralari yeniden duzelt (0'dan baslayarak ardisik)"""
        class_projects = [a for a in individual.assignments if a.class_id == class_id]
        class_projects.sort(key=lambda x: x.order_in_class)
        
        for i, a in enumerate(class_projects):
            for assignment in individual.assignments:
                if assignment.project_id == a.project_id:
                    assignment.order_in_class = i
                    break
    
    def _repair_all_classes_used(self, individual: Individual) -> None:
        """
        Tum siniflarin kullanildigindan emin ol - Cok agresif.
        
        Eger bir sinif hic kullanilmamissa, en yuklu siniftan projeleri 
        kullanilmayan sinifa tasi. Bu HARD KISIT!
        
        Bu metod TUM siniflarin kullanildigindan %100 emin olur.
        """
        max_iterations = 200  # Daha fazla iterasyon
        iteration = 0
        
        while iteration < max_iterations:
            # Her sinifin proje sayisini hesapla
            class_counts = defaultdict(int)
            for a in individual.assignments:
                class_counts[a.class_id] += 1
            
            # Kullanilmayan siniflari bul
            unused_classes = [
                c for c in range(individual.class_count) 
                if class_counts.get(c, 0) == 0
            ]
            
            if not unused_classes:
                # Tum siniflar kullaniliyor - kontrol et
                used_count = len([c for c in range(individual.class_count) if class_counts.get(c, 0) > 0])
                if used_count == individual.class_count:
                    return  # Gercekten tum siniflar kullaniliyor
                # Degilse devam et
            
            # En yuklu sinifi bul
            if not class_counts:
                # Hic sinif kullanilmiyor, projeleri dagit
                for i, assignment in enumerate(individual.assignments):
                    class_id = i % individual.class_count
                    assignment.class_id = class_id
                    assignment.order_in_class = i // individual.class_count
                self._reorder_all_classes(individual)
                return
            
            max_class = max(class_counts.keys(), key=lambda c: class_counts[c])
            max_count = class_counts[max_class]
            
            # Eger en yuklu sinifta yeterli proje varsa, kullanilmayan siniflara dagit
            if max_count > 1:
                # En yuklu siniftaki projeleri al
                projects_to_move = [
                    a for a in individual.assignments 
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
                        x for x in individual.assignments
                        if x.class_id == unused_class and x.project_id != project_to_move.project_id
                    ]
                    project_to_move.order_in_class = len(new_class_projects)
                    
                    # Siralari duzelt
                    self._reorder_class(individual, old_class)
                    self._reorder_class(individual, unused_class)
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
                        a for a in individual.assignments 
                        if a.class_id == min_class
                    ]
                    
                    if projects_in_min:
                        project_to_move = projects_in_min[-1]  # En sondan al
                        unused_class = unused_classes[0]
                        
                        old_class = project_to_move.class_id
                        project_to_move.class_id = unused_class
                        
                        # Yeni sinifin sonuna ekle
                        new_class_projects = [
                            x for x in individual.assignments
                            if x.class_id == unused_class and x.project_id != project_to_move.project_id
                        ]
                        project_to_move.order_in_class = len(new_class_projects)
                        
                        # Siralari duzelt
                        self._reorder_class(individual, old_class)
                        self._reorder_class(individual, unused_class)
                else:
                    # Her sinifta sadece 1 proje var, dagit
                    all_projects = list(individual.assignments)
                    for i, unused_class in enumerate(unused_classes):
                        if i < len(all_projects):
                            project_to_move = all_projects[i]
                            old_class = project_to_move.class_id
                            project_to_move.class_id = unused_class
                            project_to_move.order_in_class = 0
                            self._reorder_class(individual, old_class)
                            self._reorder_class(individual, unused_class)
            
            iteration += 1
    
    def _reorder_all_classes(self, individual: Individual) -> None:
        """Tum siniflardaki siralari duzelt"""
        for class_id in range(individual.class_count):
            self._reorder_class(individual, class_id)
    
    def _repair_continuity(self, individual: Individual) -> None:
        """
        Continuity (devamlilik) iyilestirmesi - Cok agresif.
        
        Her ogretim gorevlisi icin ayni siniftaki gorevlerini arka arkaya getirmeye calis.
        Ayni zamanda sinif degisikliklerini minimize et.
        """
        max_iterations = 100
        iteration = 0
        
        while iteration < max_iterations:
            improved = False
            
            # Her ogretim gorevlisi icin
            for instructor_id in self.faculty_ids:
                # Bu hocanin tum gorevlerini bul
                instructor_assignments = []
                for a in individual.assignments:
                    if a.ps_id == instructor_id or a.j1_id == instructor_id:
                        instructor_assignments.append((a, a.class_id, a.order_in_class))
                
                if len(instructor_assignments) <= 1:
                    continue
                
                # Sinif bazinda grupla
                tasks_by_class = defaultdict(list)
                for a, class_id, order in instructor_assignments:
                    tasks_by_class[class_id].append((a, order))
                
                # Her sinif icin continuity kontrolu
                for class_id, class_tasks in tasks_by_class.items():
                    if len(class_tasks) <= 1:
                        continue
                    
                    # Sira sirasina gore sirala
                    class_tasks.sort(key=lambda x: x[1])
                    
                    # Ardisik olmayan gorevleri bul ve duzelt
                    for i in range(len(class_tasks) - 1):
                        current_order = class_tasks[i][1]
                        next_order = class_tasks[i + 1][1]
                        gap = next_order - current_order - 1
                        
                        if gap > 0:
                            # Ardisik degil, duzeltmeye calis
                            # Aradaki projeleri bul
                            gap_projects = [
                                a for a in individual.assignments
                                if a.class_id == class_id and
                                current_order < a.order_in_class < next_order
                            ]
                            
                            # Aradaki projeleri baska sinifa tasi
                            for gap_proj in gap_projects:
                                # Bu hocanin gorevi degilse tasi
                                if (gap_proj.ps_id != instructor_id and 
                                    gap_proj.j1_id != instructor_id):
                                    
                                    # En az yuklu sinifi bul (ama bu sinif degil)
                                    class_loads = defaultdict(int)
                                    for a in individual.assignments:
                                        if a.project_id != gap_proj.project_id:
                                            class_loads[a.class_id] += 1
                                    
                                    # Bu hocanin zaten gorev yaptigi siniflari tercih et
                                    preferred_classes = [c for c in tasks_by_class.keys() if c != class_id]
                                    
                                    if preferred_classes:
                                        # Hocanin zaten gorev yaptigi bir sinifa tasi
                                        target_class = min(
                                            preferred_classes,
                                            key=lambda c: class_loads.get(c, 0)
                                        )
                                    else:
                                        # Yoksa en az yuklu sinifa tasi
                                        target_class = min(
                                            range(individual.class_count),
                                            key=lambda c: class_loads.get(c, 0)
                                        )
                                    
                                    # Projeyi tasi
                                    old_class = gap_proj.class_id
                                    gap_proj.class_id = target_class
                                    gap_proj.order_in_class = class_loads.get(target_class, 0)
                                    
                                    # Siralari duzelt
                                    self._reorder_class(individual, old_class)
                                    self._reorder_class(individual, target_class)
                                    improved = True
                                    break
                            
                            if improved:
                                break
                    
                    if improved:
                        break
                
                # Sinif degisikliklerini minimize et
                if len(tasks_by_class) > 2:
                    # 2'den fazla sinif kullaniyorsa, bir sinifa topla
                    # En cok gorev yaptigi sinifi bul
                    main_class = max(tasks_by_class.keys(), key=lambda c: len(tasks_by_class[c]))
                    
                    # Diger siniflardaki gorevleri main_class'a tasi
                    for other_class, other_tasks in tasks_by_class.items():
                        if other_class == main_class:
                            continue
                        
                        for a, order in other_tasks:
                            # Projeyi main_class'a tasi
                            old_class = a.class_id
                            a.class_id = main_class
                            
                            # Yeni sinifin sonuna ekle
                            main_class_projects = [
                                x for x in individual.assignments
                                if x.class_id == main_class and x.project_id != a.project_id
                            ]
                            a.order_in_class = len(main_class_projects)
                            
                            # Siralari duzelt
                            self._reorder_class(individual, old_class)
                            self._reorder_class(individual, main_class)
                            improved = True
                
                if improved:
                    break
            
            if not improved:
                break
            
            iteration += 1
    
    def _repair_minimize_class_changes(self, individual: Individual) -> None:
        """
        Sinif degisikliklerini minimize et.
        
        Her ogretim gorevlisi icin gorevlerini minimum sayida sinifa topla.
        Ideal: 1-2 sinif.
        """
        max_iterations = 50
        iteration = 0
        
        while iteration < max_iterations:
            improved = False
            
            # Her ogretim gorevlisi icin
            for instructor_id in self.faculty_ids:
                # Bu hocanin tum gorevlerini bul
                instructor_assignments = []
                for a in individual.assignments:
                    if a.ps_id == instructor_id or a.j1_id == instructor_id:
                        instructor_assignments.append((a, a.class_id))
                
                if len(instructor_assignments) <= 1:
                    continue
                
                # Sinif bazinda grupla
                tasks_by_class = defaultdict(list)
                for a, class_id in instructor_assignments:
                    tasks_by_class[class_id].append(a)
                
                # Eger 2'den fazla sinif kullaniyorsa, bir sinifa topla
                if len(tasks_by_class) > 2:
                    # En cok gorev yaptigi sinifi bul (main class)
                    main_class = max(tasks_by_class.keys(), key=lambda c: len(tasks_by_class[c]))
                    
                    # Diger siniflardaki gorevleri main_class'a tasi
                    for other_class, other_tasks in tasks_by_class.items():
                        if other_class == main_class:
                            continue
                        
                        for a in other_tasks:
                            # Projeyi main_class'a tasi
                            old_class = a.class_id
                            a.class_id = main_class
                            
                            # Yeni sinifin sonuna ekle
                            main_class_projects = [
                                x for x in individual.assignments
                                if x.class_id == main_class and x.project_id != a.project_id
                            ]
                            a.order_in_class = len(main_class_projects)
                            
                            # Siralari duzelt
                            self._reorder_class(individual, old_class)
                            self._reorder_class(individual, main_class)
                            improved = True
                
                # Eger 2 sinif kullaniyorsa, birine toplamaya calis (ama zorunlu degil)
                elif len(tasks_by_class) == 2:
                    class1, class2 = list(tasks_by_class.keys())
                    count1 = len(tasks_by_class[class1])
                    count2 = len(tasks_by_class[class2])
                    
                    # Eger bir sinifta cok az gorev varsa, digerine tasi
                    if count1 <= 2 and count2 > count1:
                        # class1'deki gorevleri class2'ye tasi
                        for a in tasks_by_class[class1]:
                            old_class = a.class_id
                            a.class_id = class2
                            
                            class2_projects = [
                                x for x in individual.assignments
                                if x.class_id == class2 and x.project_id != a.project_id
                            ]
                            a.order_in_class = len(class2_projects)
                            
                            self._reorder_class(individual, old_class)
                            self._reorder_class(individual, class2)
                            improved = True
                    elif count2 <= 2 and count1 > count2:
                        # class2'deki gorevleri class1'e tasi
                        for a in tasks_by_class[class2]:
                            old_class = a.class_id
                            a.class_id = class1
                            
                            class1_projects = [
                                x for x in individual.assignments
                                if x.class_id == class1 and x.project_id != a.project_id
                            ]
                            a.order_in_class = len(class1_projects)
                            
                            self._reorder_class(individual, old_class)
                            self._reorder_class(individual, class1)
                            improved = True
                
                if improved:
                    break
            
            if not improved:
                break
            
            iteration += 1


# ============================================================================
# INITIALIZATION
# ============================================================================

class GAInitializer:
    """GA populasyon baslangici"""
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: GAConfig
    ):
        self.projects = projects
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece ogretim gorevlileri
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    def create_initial_population(self, size: int) -> List[Individual]:
        """
        Baslangic populasyonunu olustur.
        
        %30 heuristic, %70 random+repair (config'e gore)
        """
        population = []
        
        heuristic_count = int(size * self.config.heuristic_init_ratio)
        random_count = size - heuristic_count
        
        # Heuristic bireyler
        for _ in range(heuristic_count):
            ind = self._create_heuristic_individual()
            population.append(ind)
        
        # Random bireyler
        for _ in range(random_count):
            ind = self._create_random_individual()
            population.append(ind)
        
        return population
    
    def _create_heuristic_individual(self) -> Individual:
        """
        Heuristic birey olustur - PSO yaklasimiyla CAKISMASIZ.
        
        Strateji:
        1. PS bloklarini ayni sinifa yakın tut
        2. Ayni PS'nin projeleri art arda
        3. Sinif dengesi gozet
        4. J1 atamasi: CAKISMASIZ + is yuku dengeli (PSO'dan alinan)
        5. Ara/Bitirme moduna gore sırala
        """
        individual = Individual(class_count=self.config.class_count)
        
        # Projeleri PS'ye gore grupla
        ps_groups = defaultdict(list)
        for project in self.projects:
            ps_groups[project.responsible_id].append(project)
        
        # Onceliklendirme moduna gore sirala
        sorted_projects = self._sort_projects_by_priority()
        
        # Siniflara dagit - PS bloklarini ayni sinifta tut (continuity icin)
        class_assignments = [[] for _ in range(self.config.class_count)]
        class_loads = [0] * self.config.class_count
        
        # PS'ye gore grupla ve ayni PS'nin projelerini ayni sinifa koy
        ps_to_class = {}  # Her PS icin secilen sinif
        
        for project in sorted_projects:
            ps_id = project.responsible_id
            
            # Eger bu PS icin sinif secilmisse, ayni sinifi kullan
            if ps_id in ps_to_class:
                class_id = ps_to_class[ps_id]
            else:
                # CRITICAL: En az yuklu siniflari bul, esit yuklüler arasından rastgele sec
                min_load = min(class_loads)
                min_classes = [c for c in range(self.config.class_count) if class_loads[c] == min_load]
                class_id = random.choice(min_classes)
                ps_to_class[ps_id] = class_id
            
            class_assignments[class_id].append(project)
            class_loads[class_id] += 1
        
        # ================================================================
        # PSO YAKLAŞIMI: INSTRUCTOR BUSY MAP ILE CAKISMASIZ J1 ATAMASI
        # ================================================================
        # instructor_id -> set of busy order_in_class (timeslot)
        instructor_busy: Dict[int, Set[int]] = defaultdict(set)
        workloads: Dict[int, int] = defaultdict(int)
        
        # Ortalama is yukunu hesapla
        num_projects = len(self.projects)
        num_faculty = len(self.faculty_ids)
        avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
        
        # Önce PS'lerin mesgul oldugu slotlari belirle
        for cid, projs in enumerate(class_assignments):
            for order, project in enumerate(projs):
                ps_id = project.responsible_id
                instructor_busy[ps_id].add(order)
                workloads[ps_id] += 1
        
        # Her proje icin J1 atamasi yap (CAKISMASIZ + is yuku dengeli)
        for cid, projs in enumerate(class_assignments):
            for order, project in enumerate(projs):
                ps_id = project.responsible_id
                
                # CAKISMASIZ J1 aday listesi: PS haric + bu order'da mesgul OLMAYAN
                available_j1 = []
                for i_id in self.faculty_ids:
                    if i_id == ps_id:
                        continue  # J1 != PS
                    if order in instructor_busy.get(i_id, set()):
                        continue  # Bu timeslot'ta zaten mesgul
                    available_j1.append(i_id)
                
                if available_j1:
                    # Is yuku dagilimini optimize et: ±2 band icinde kalan ve en az yuke sahip
                    band_candidates = [
                        i_id for i_id in available_j1
                        if abs(workloads.get(i_id, 0) - avg_workload) <= 2
                    ]
                    
                    if band_candidates:
                        # Band icinde kalan en az yuklu hocaLARI bul, aralarından rastgele sec
                        min_load = min(workloads.get(x, 0) for x in band_candidates)
                        min_candidates = [x for x in band_candidates if workloads.get(x, 0) == min_load]
                        j1_id = random.choice(min_candidates)
                    else:
                        # Band icinde kalan yok, en az yuklu hocaLARI bul
                        min_load = min(workloads.get(x, 0) for x in available_j1)
                        min_candidates = [x for x in available_j1 if workloads.get(x, 0) == min_load]
                        j1_id = random.choice(min_candidates)
                else:
                    # Musait J1 yok - en az yuklu secip cakisma kabul et (sonra repair edilir)
                    fallback_j1 = [i_id for i_id in self.faculty_ids if i_id != ps_id]
                    if fallback_j1:
                        min_load = min(workloads.get(x, 0) for x in fallback_j1)
                        min_candidates = [x for x in fallback_j1 if workloads.get(x, 0) == min_load]
                        j1_id = random.choice(min_candidates)
                    else:
                        j1_id = self.faculty_ids[0] if self.faculty_ids else ps_id
                
                # J1'i busy map'e ekle
                instructor_busy[j1_id].add(order)
                workloads[j1_id] += 1
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=cid,
                    order_in_class=order,
                    ps_id=ps_id,
                    j1_id=j1_id,
                    j2_id=-1  # Placeholder
                )
                individual.assignments.append(assignment)
        
        return individual
    
    def _create_random_individual(self) -> Individual:
        """
        Random birey olustur.
        
        Rastgele sinif ve sira atamasi, J1 rastgele.
        AMA tum siniflarin kullanildigindan emin ol.
        """
        individual = Individual(class_count=self.config.class_count)
        
        # Projeleri karistir
        shuffled_projects = list(self.projects)
        random.shuffle(shuffled_projects)
        
        # Siniflara dagit - tum siniflarin kullanildigindan emin ol
        class_counts = defaultdict(int)
        used_classes = set()
        
        # Once her sinifa en az 1 proje atayarak basla
        for i, project in enumerate(shuffled_projects[:self.config.class_count]):
            class_id = i % self.config.class_count
            order = class_counts[class_id]
            class_counts[class_id] += 1
            used_classes.add(class_id)
            
            # J1 sec (is yuku dengeli - rastgele ama dengeli)
            available_j1 = [
                i_id for i_id in self.faculty_ids 
                if i_id != project.responsible_id
            ]
            
            if available_j1:
                # En az yuklu ogretim gorevlisini sec (dengeli baslangic)
                j1_id = min(available_j1, key=lambda x: workloads.get(x, 0))
            else:
                j1_id = self.faculty_ids[0]
            
            workloads[project.responsible_id] += 1
            workloads[j1_id] += 1
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=class_id,
                order_in_class=order,
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            individual.assignments.append(assignment)
        
        # Ortalama is yukunu hesapla
        num_projects = len(self.projects)
        num_faculty = len(self.faculty_ids)
        avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
        
        # Kalan projeleri dagit (en az yuklu siniflara)
        for project in shuffled_projects[self.config.class_count:]:
            # En az yuklu sinifi sec, ama once kullanilmayan siniflari tercih et
            unused_classes = [
                c for c in range(self.config.class_count) 
                if c not in used_classes
            ]
            
            if unused_classes:
                # Once kullanilmayan siniflari kullan
                class_id = min(unused_classes, key=lambda c: class_counts.get(c, 0))
                used_classes.add(class_id)
            else:
                # Tum siniflar kullanildi, en az yuklu siniflari bul, aralarından rastgele sec
                min_load = min(class_counts.get(c, 0) for c in range(self.config.class_count))
                min_classes = [c for c in range(self.config.class_count) if class_counts.get(c, 0) == min_load]
                class_id = random.choice(min_classes)
            
            order = class_counts[class_id]
            class_counts[class_id] += 1
            
            # J1 sec (is yuku dengeli - ±2 band icinde kalan)
            available_j1 = [
                i_id for i_id in self.faculty_ids 
                if i_id != project.responsible_id
            ]
            
            if available_j1:
                # Band icinde kalan ve en az yuklu olan
                band_candidates = [
                    i_id for i_id in available_j1
                    if abs(workloads.get(i_id, 0) - avg_workload) <= 2
                ]
                
                if band_candidates:
                    # CRITICAL: Eşit yüklüler arasından rastgele seç
                    min_load = min(workloads.get(x, 0) for x in band_candidates)
                    min_candidates = [x for x in band_candidates if workloads.get(x, 0) == min_load]
                    j1_id = random.choice(min_candidates)
                else:
                    min_load = min(workloads.get(x, 0) for x in available_j1)
                    min_candidates = [x for x in available_j1 if workloads.get(x, 0) == min_load]
                    j1_id = random.choice(min_candidates)
            else:
                j1_id = self.faculty_ids[0]
            
            workloads[project.responsible_id] += 1
            workloads[j1_id] += 1
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=class_id,
                order_in_class=order,
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            individual.assignments.append(assignment)
        
        return individual
    
    def _sort_projects_by_priority(self) -> List[Project]:
        """Projeleri onceliklendirme moduna gore sirala (case-insensitive + randomized)"""
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            # Ara projeler once
            ara = [p for p in self.projects if str(p.type).lower() in ('interim', 'ara')]
            bitirme = [p for p in self.projects if str(p.type).lower() in ('final', 'bitirme')]
            # CRITICAL: Shuffle within same type to get different results each run
            random.shuffle(ara)
            random.shuffle(bitirme)
            logger.debug(f"Sorting by ARA_ONCE: {len(ara)} ara (shuffled), {len(bitirme)} bitirme (shuffled)")
            return ara + bitirme
        
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            # Bitirme projeleri once
            bitirme = [p for p in self.projects if str(p.type).lower() in ('final', 'bitirme')]
            ara = [p for p in self.projects if str(p.type).lower() in ('interim', 'ara')]
            # CRITICAL: Shuffle within same type to get different results each run
            random.shuffle(bitirme)
            random.shuffle(ara)
            logger.debug(f"Sorting by BITIRME_ONCE: {len(bitirme)} bitirme (shuffled), {len(ara)} ara (shuffled)")
            return bitirme + ara
        
        else:  # ESIT
            # CRITICAL: Shuffle all projects for randomness
            shuffled = list(self.projects)
            random.shuffle(shuffled)
            return shuffled


# ============================================================================
# MAIN GENETIC ALGORITHM
# ============================================================================

class GeneticAlgorithm(OptimizationAlgorithm):
    """
    Genetic Algorithm (Genetik Algoritma) - Cok Kriterli Akademik Proje Planlama.
    
    Tek fazli calisma prensibi:
    - Tum projeler, hocalar, sinif sayisi tek seferde modele verilir
    - GA nesiller boyunca evrilir
    - En iyi cozum tek seferde planner'a aktarilir
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Genetic Algorithm baslatici.
        
        Args:
            params: Algoritma parametreleri
        """
        super().__init__(params)
        params = params or {}
        
        # CRITICAL: Frontend'den gelen project_priority parametresini priority_mode'a çevir
        # Frontend: "midterm_priority", "final_exam_priority", "none"
        # Backend: "ARA_ONCE", "BITIRME_ONCE", "ESIT"
        project_priority = params.get("project_priority", "none")
        if project_priority == "midterm_priority":
            priority_mode_value = "ARA_ONCE"
            logger.info("Priority mode set to ARA_ONCE via params project_priority")
        elif project_priority == "final_exam_priority":
            priority_mode_value = "BITIRME_ONCE"
            logger.info("Priority mode set to BITIRME_ONCE via params project_priority")
        else:
            # Fallback: Eğer doğrudan priority_mode verilmişse onu kullan
            priority_mode_value = params.get("priority_mode", "ESIT")
            if priority_mode_value != "ESIT":
                logger.info(f"Priority mode set to {priority_mode_value} via params priority_mode")
            else:
                logger.info("Priority mode is ESIT (default/no priority)")
        
        # Konfigurasyon olustur
        self.config = GAConfig(
            population_size=params.get("population_size", 150),
            max_generations=params.get("max_generations", 300),
            time_limit=params.get("time_limit", 300),
            no_improve_limit=params.get("no_improve_limit", 50),
            crossover_rate=params.get("crossover_rate", 0.85),
            mutation_rate=params.get("mutation_rate", 0.15),
            elitism_rate=params.get("elitism_rate", 0.15),
            tournament_size=params.get("tournament_size", 5),
            class_count=params.get("class_count", 6),
            auto_class_count=params.get("auto_class_count", True),
            priority_mode=PriorityMode(priority_mode_value),  # DÜZELTME: project_priority'den dönüştürülmüş değer
            time_penalty_mode=TimePenaltyMode(params.get("time_penalty_mode", "GAP_PROPORTIONAL")),
            workload_constraint_mode=WorkloadConstraintMode(
                params.get("workload_constraint_mode", "SOFT_ONLY")
            ),
            workload_hard_limit=params.get("workload_hard_limit", 4),
            weight_h1=params.get("weight_h1", 10.0),
            weight_h2=params.get("weight_h2", 100.0),
            weight_h3=params.get("weight_h3", 5.0),
            heuristic_init_ratio=params.get("heuristic_init_ratio", 0.50),
            memory_size=params.get("memory_size", 15),
            use_memory=params.get("use_memory", True),
            restart_on_stagnation=params.get("restart_on_stagnation", True),
            stagnation_generations=params.get("stagnation_generations", 30),
            diversity_threshold=params.get("diversity_threshold", 0.1),
            adaptive_rates=params.get("adaptive_rates", True),
            use_local_improvement=params.get("use_local_improvement", True),
            local_improvement_rate=params.get("local_improvement_rate", 0.05),
            local_improvement_iterations=params.get("local_improvement_iterations", 10)
        )
        
        # Veri yapilari
        self.projects: List[Project] = []
        self.projects_dict: Dict[int, Project] = {}  # Proje ID'sine gore hizli erisim
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        
        # En iyi birey
        self.best_individual: Optional[Individual] = None
        self.best_fitness: float = float('-inf')
        
        # Hafiza (Memory) - Onceki en iyi cozumler
        self.memory_pool: List[Tuple[Individual, float]] = []  # (individual, fitness) listesi
        self.global_best_individual: Optional[Individual] = None
        self.global_best_fitness: float = float('-inf')
        
        # Adaptif parametreler
        self.adaptive_mutation_rate: float = 0.15
        self.adaptive_crossover_rate: float = 0.85
        
        # Yardimci siniflar
        self.penalty_calculator: Optional[GAPenaltyCalculator] = None
        self.operators: Optional[GeneticOperators] = None
        self.repair_mechanism: Optional[GARepairMechanism] = None
        self.initializer: Optional[GAInitializer] = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Algoritmayi baslangic verileri ile baslatir.
        
        Args:
            data: Algoritma giris verileri
        """
        # Verileri yukle
        self._load_data(data)
        
        # Yardimci siniflari olustur
        self.penalty_calculator = GAPenaltyCalculator(
            self.projects, self.instructors, self.config
        )
        self.operators = GeneticOperators(
            self.projects, self.instructors, self.config
        )
        self.repair_mechanism = GARepairMechanism(
            self.projects, self.instructors, self.config
        )
        self.initializer = GAInitializer(
            self.projects, self.instructors, self.config
        )
        
        # En iyi bireyi sifirla (ama global best'i koru)
        self.best_individual = None
        self.best_fitness = float('-inf')
        
        # Adaptif parametreleri resetle
        self.adaptive_mutation_rate = self.config.mutation_rate
        self.adaptive_crossover_rate = self.config.crossover_rate
    
    def _load_data(self, data: Dict[str, Any]) -> None:
        """Verileri yukle ve donustur"""
        # Projeleri yukle
        raw_projects = data.get("projects", [])
        self.projects = []
        
        for p in raw_projects:
            project = Project(
                id=p.get("id"),
                title=p.get("title", ""),
                type=str(p.get("type", "interim")).lower(),
                responsible_id=p.get("responsible_id"),
                is_makeup=p.get("is_makeup", False)
            )
            self.projects.append(project)
        
        # Ogretim gorevlilerini yukle
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        
        for i in raw_instructors:
            instructor = Instructor(
                id=i.get("id"),
                name=i.get("name", ""),
                type=i.get("type", "instructor")
            )
            self.instructors.append(instructor)
        
        # Siniflari ve zaman dilimlerini yukle
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Eger classrooms varsa ve class_count ayarlanmamissa, otomatik olarak sinif sayisini ayarla
        if self.classrooms and len(self.classrooms) > 0:
            available_class_count = len(self.classrooms)
            # Eger config'de class_count mevcut sinif sayisindan farkliysa ve auto_class_count False ise
            # veya class_count ayarlanmamissa, mevcut sinif sayisini kullan
            if self.config.class_count != available_class_count:
                # Eger auto_class_count aktifse, mevcut sinif sayisini kullan
                if self.config.auto_class_count or self.config.class_count == 6:  # Default 6
                    self.config.class_count = available_class_count
                    logger.info(f"Sinif sayisi otomatik olarak {available_class_count} olarak ayarlandi (mevcut sinif sayisi)")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Genetic Algorithm'i calistirir.
        
        Args:
            data: Algoritma giris verileri
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu
        """
        if data:
            self.initialize(data)
        
        start_time = time.time()
        
        # Eger classrooms varsa, mevcut sinif sayisini kullan (tum siniflar kullanilsin)
        # Eger classrooms yoksa ve auto_class_count aktifse, 5, 6, 7 icin en iyi sonucu bul
        if self.classrooms and len(self.classrooms) > 0:
            # Mevcut sinif sayisini kullan (zaten _load_data'da ayarlandi)
            result = self._run_ga()
        elif self.config.auto_class_count:
            # Classrooms yok, auto_class_count ile 5, 6, 7 test et
            best_result = None
            best_overall_fitness = float('-inf')
            
            for class_count in [5, 6, 7]:
                logger.info(f"Sinif sayisi {class_count} ile calistiriliyor...")
                self.config.class_count = class_count
                
                # Yardimci siniflari guncelle
                self.penalty_calculator = GAPenaltyCalculator(
                    self.projects, self.instructors, self.config
                )
                self.operators = GeneticOperators(
                    self.projects, self.instructors, self.config
                )
                self.repair_mechanism = GARepairMechanism(
                    self.projects, self.instructors, self.config
                )
                self.initializer = GAInitializer(
                    self.projects, self.instructors, self.config
                )
                
                result = self._run_ga()
                
                if result['fitness'] > best_overall_fitness:
                    best_overall_fitness = result['fitness']
                    best_result = result
            
            result = best_result
        else:
            result = self._run_ga()
        
        end_time = time.time()
        
        # Cozumu output formatina donustur
        schedule = self._convert_individual_to_schedule(result['individual'])
        
        return {
            "schedule": schedule,
            "assignments": schedule,
            "solution": schedule,
            "fitness": result['fitness'],
            "cost": -result['fitness'],  # Maliyet = -fitness
            "generations": result['generations'],
            "execution_time": end_time - start_time,
            "class_count": result['individual'].class_count,
            "penalty_breakdown": result.get('penalty_breakdown', {}),
            "status": "completed"
        }
    
    def _run_ga(self) -> Dict[str, Any]:
        """
        Ana GA dongusu - Hafiza destekli.
        
        Returns:
            En iyi birey ve istatistikler
        """
        start_time = time.time()
        total_generations = 0
        restart_count = 0
        max_restarts = 3
        
        # Global best'i guncelle
        if self.global_best_individual is None or self.best_fitness > self.global_best_fitness:
            self.global_best_individual = self.best_individual.copy() if self.best_individual else None
            self.global_best_fitness = self.best_fitness
        
        # Baslangic populasyonunu olustur (hafizadan seed kullan)
        population = self._create_population_with_memory()
        
        # Repair ve fitness hesapla
        for ind in population:
            self.repair_mechanism.repair(ind)
            ind.fitness = self.penalty_calculator.calculate_fitness(ind)
        
        # En iyi bireyi baslat
        self.best_individual = max(population, key=lambda x: x.fitness).copy()
        self.best_fitness = self.best_individual.fitness
        
        # Global best'i guncelle
        if self.best_fitness > self.global_best_fitness:
            self.global_best_individual = self.best_individual.copy()
            self.global_best_fitness = self.best_fitness
        
        # Hafizaya ekle
        self._add_to_memory(self.best_individual, self.best_fitness)
        
        # Nesil sayaclari
        generation = 0
        no_improve_count = 0
        last_improvement_generation = 0
        
        logger.info(f"Baslangic fitness: {self.best_fitness:.2f} (Global best: {self.global_best_fitness:.2f})")
        
        # Ana dongu
        while (total_generations < self.config.max_generations and
               time.time() - start_time < self.config.time_limit):
            
            # Adaptif parametreleri guncelle
            if self.config.adaptive_rates:
                self._update_adaptive_rates(generation, no_improve_count)
            
            # Yeni nesil olustur
            new_population = []
            
            while len(new_population) < self.config.population_size:
                # Ebeveyn sec
                parent1 = self.operators.tournament_selection(population)
                parent2 = self.operators.tournament_selection(population)
                
                # Adaptif crossover rate kullan
                old_crossover_rate = self.config.crossover_rate
                if self.config.adaptive_rates:
                    self.config.crossover_rate = self.adaptive_crossover_rate
                
                # Crossover
                child1, child2 = self.operators.crossover(parent1, parent2)
                
                # Adaptif mutation rate kullan
                old_mutation_rate = self.config.mutation_rate
                if self.config.adaptive_rates:
                    self.config.mutation_rate = self.adaptive_mutation_rate
                
                # Mutation
                child1 = self.operators.mutate(child1)
                child2 = self.operators.mutate(child2)
                
                # Rate'leri geri al
                if self.config.adaptive_rates:
                    self.config.crossover_rate = old_crossover_rate
                    self.config.mutation_rate = old_mutation_rate
                
                # Repair
                self.repair_mechanism.repair(child1)
                self.repair_mechanism.repair(child2)
                
                # Fitness hesapla
                child1.fitness = self.penalty_calculator.calculate_fitness(child1)
                child2.fitness = self.penalty_calculator.calculate_fitness(child2)
                
                new_population.append(child1)
                if len(new_population) < self.config.population_size:
                    new_population.append(child2)
            
            # Elitism uygula
            population = self.operators.apply_elitism(population, new_population)
            
            # Local improvement (en iyi bireyleri iyilestir)
            if self.config.use_local_improvement:
                population = self._apply_local_improvement(population)
            
            # Workload rebalancing (her nesilde - H2 cok kritik, weight=100)
            if generation % 5 == 0:  # Her 5 nesilde bir
                population = self._apply_workload_rebalancing(population)
            
            # En iyi bireyi guncelle
            current_best = max(population, key=lambda x: x.fitness)
            
            if current_best.fitness > self.best_fitness:
                self.best_individual = current_best.copy()
                self.best_fitness = current_best.fitness
                no_improve_count = 0
                last_improvement_generation = generation
                
                # Global best'i guncelle
                if self.best_fitness > self.global_best_fitness:
                    self.global_best_individual = self.best_individual.copy()
                    self.global_best_fitness = self.best_fitness
                
                # Hafizaya ekle
                self._add_to_memory(self.best_individual, self.best_fitness)
                
                logger.info(f"Nesil {generation}: Yeni en iyi fitness = {self.best_fitness:.2f} "
                          f"(Global: {self.global_best_fitness:.2f})")
            else:
                no_improve_count += 1
            
            # Restart kontrolu
            if (self.config.restart_on_stagnation and 
                no_improve_count >= self.config.stagnation_generations and
                restart_count < max_restarts):
                
                # Populasyon cesitliligini kontrol et
                diversity = self._calculate_diversity(population)
                
                if diversity < self.config.diversity_threshold:
                    logger.info(f"Restart yapiliyor (cesitlilik dusuk: {diversity:.3f}, "
                              f"iyilesme yok: {no_improve_count} nesil)")
                    
                    # Hafizadan seed populasyon olustur
                    population = self._create_population_with_memory()
                    
                    # Repair ve fitness
                    for ind in population:
                        self.repair_mechanism.repair(ind)
                        ind.fitness = self.penalty_calculator.calculate_fitness(ind)
                    
                    # En iyi bireyi guncelle
                    current_best = max(population, key=lambda x: x.fitness)
                    if current_best.fitness > self.best_fitness:
                        self.best_individual = current_best.copy()
                        self.best_fitness = current_best.fitness
                    
                    no_improve_count = 0
                    generation = 0
                    restart_count += 1
                    
                    # Adaptif parametreleri resetle
                    if self.config.adaptive_rates:
                        self.adaptive_mutation_rate = self.config.mutation_rate * 1.5  # Artir
                        self.adaptive_crossover_rate = self.config.crossover_rate * 0.9  # Azalt
            
            generation += 1
            total_generations += 1
            
            # Max generations kontrolu
            if generation >= self.config.max_generations:
                break
            
            # No improve limit kontrolu
            if no_improve_count >= self.config.no_improve_limit:
                break
        
        # Ceza detaylarini hesapla
        penalty_breakdown = {
            'h1_time_penalty': self.penalty_calculator.calculate_h1_time_penalty(self.best_individual),
            'h2_workload_penalty': self.penalty_calculator.calculate_h2_workload_penalty(self.best_individual),
            'h3_class_change_penalty': self.penalty_calculator.calculate_h3_class_change_penalty(self.best_individual)
        }
        
        # Global best'i kullan (eger daha iyiyse)
        if self.global_best_individual and self.global_best_fitness > self.best_fitness:
            self.best_individual = self.global_best_individual.copy()
            self.best_fitness = self.global_best_fitness
            logger.info(f"Global best kullanildi: {self.best_fitness:.2f}")
        
        logger.info(f"GA tamamlandi: {total_generations} toplam nesil, "
                   f"{restart_count} restart, fitness = {self.best_fitness:.2f}")
        
        return {
            'individual': self.best_individual,
            'fitness': self.best_fitness,
            'generations': total_generations,
            'restarts': restart_count,
            'penalty_breakdown': penalty_breakdown
        }
    
    def _convert_individual_to_schedule(
        self, 
        individual: Individual
    ) -> List[Dict[str, Any]]:
        """
        Individual'i schedule formatina donustur.
        
        Her atama icin:
        - project_id
        - classroom_id
        - timeslot_id
        - instructors (PS, J1, J2=[Araştırma Görevlisi])
        
        J2 her zaman "[Araştırma Görevlisi]" placeholder olarak yazilir.
        Bu sadece frontend'de gorunecek, algoritma icinde parametrize edilmez.
        """
        schedule = []
        
        if not individual or not individual.assignments:
            return schedule
        
        # Sinif ve timeslot eslestirmesi olustur
        classroom_mapping = self._create_classroom_mapping(individual.class_count)
        timeslot_mapping = self._create_timeslot_mapping()
        
        for assignment in individual.assignments:
            # Sinif ID'sini gercek classroom ID'sine donustur
            classroom_id = classroom_mapping.get(
                assignment.class_id, 
                self.classrooms[0].get("id") if self.classrooms else 1
            )
            
            # Timeslot ID'sini hesapla (sinif icindeki siraya gore)
            timeslot_idx = assignment.order_in_class
            timeslot_id = timeslot_mapping.get(
                timeslot_idx, 
                self.timeslots[0].get("id") if self.timeslots else 1
            )
                
                # Instructors listesi: [PS, J1, J2]
            # J2 her zaman "[Araştırma Görevlisi]" placeholder olarak eklenir
            # Bu sadece frontend'de gorunecek, algoritma icinde parametrize edilmez
            instructors = [assignment.ps_id, assignment.j1_id, J2_PLACEHOLDER]
            
            schedule_entry = {
                "project_id": assignment.project_id,
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": instructors,
                "class_order": assignment.order_in_class,
                "class_id": assignment.class_id
            }
            schedule.append(schedule_entry)
        
        return schedule
    
    def _create_classroom_mapping(self, class_count: int) -> Dict[int, int]:
        """Mantiksal sinif ID'lerini gercek classroom ID'lerine esle"""
        mapping = {}
        for i in range(class_count):
            if i < len(self.classrooms):
                mapping[i] = self.classrooms[i].get("id", i + 1)
            else:
                mapping[i] = i + 1
        return mapping
    
    def _create_timeslot_mapping(self) -> Dict[int, int]:
        """Siralama indeksini timeslot ID'lerine esle"""
        mapping = {}
        for i, ts in enumerate(self.timeslots):
            mapping[i] = ts.get("id", i + 1)
        return mapping
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Cozumun fitness degerini hesapla.
        
        Args:
            solution: Degerlendirilecek cozum
            
        Returns:
            Fitness degeri (yuksek = iyi)
        """
        if not solution:
            return float('-inf')
        
        assignments = solution.get("solution", solution.get("schedule", solution))
        
        if isinstance(assignments, Individual):
            return self.penalty_calculator.calculate_fitness(assignments)
        
        # Dict listesi ise Individual'a donustur
        if isinstance(assignments, list):
            ind = self._convert_schedule_to_individual(assignments)
            if ind:
                return self.penalty_calculator.calculate_fitness(ind)
        
        return float('-inf')
    
    def _convert_schedule_to_individual(
        self, 
        schedule: List[Dict[str, Any]]
    ) -> Optional[Individual]:
        """Schedule formatindan Individual'a donustur"""
        if not schedule:
            return None
        
        individual = Individual(class_count=self.config.class_count)
        
        for entry in schedule:
            project_id = entry.get("project_id")
            instructors = entry.get("instructors", [])
            
            if not project_id or len(instructors) < 2:
                continue
            
            assignment = ProjectAssignment(
                project_id=project_id,
                class_id=entry.get("class_id", 0),
                order_in_class=entry.get("class_order", 0),
                ps_id=instructors[0] if isinstance(instructors[0], int) else 0,
                j1_id=instructors[1] if isinstance(instructors[1], int) else 0,
                j2_id=-1  # Placeholder
            )
            individual.assignments.append(assignment)
        
        return individual
    
    def _create_population_with_memory(self) -> List[Individual]:
        """
        Hafizadan seed populasyon olustur.
        
        Eger hafizada cozumler varsa, bunlari seed olarak kullan.
        Yoksa normal initialization yap.
        """
        population = []
        
        if self.config.use_memory and self.memory_pool:
            # Hafizadan en iyi cozumleri al
            memory_size = min(len(self.memory_pool), self.config.memory_size)
            memory_individuals = sorted(
                self.memory_pool, 
                key=lambda x: x[1], 
                reverse=True
            )[:memory_size]
            
            # Hafizadan seed populasyon olustur (%30 hafiza, %70 yeni)
            seed_count = int(self.config.population_size * 0.3)
            new_count = self.config.population_size - seed_count
            
            # Hafizadan seed'ler
            for i, (ind, fitness) in enumerate(memory_individuals[:seed_count]):
                # Hafizadaki cozumu mutate et (kucuk degisiklikler)
                seed = ind.copy()
                
                # Kucuk mutation uygula
                if random.random() < 0.5:
                    # J1'leri biraz degistir
                    for assignment in seed.assignments:
                        if random.random() < 0.2:  # %20 ihtimalle
                            available_j1 = [
                                i_id for i_id in self.operators.faculty_ids
                                if i_id != assignment.ps_id and i_id != assignment.j1_id
                            ]
                            if available_j1:
                                assignment.j1_id = random.choice(available_j1)
                
                population.append(seed)
            
            # Yeni bireyler ekle
            new_individuals = self.initializer.create_initial_population(new_count)
            population.extend(new_individuals)
        else:
            # Normal initialization
            population = self.initializer.create_initial_population(self.config.population_size)
        
        # Global best'i de ekle (eger varsa)
        if self.global_best_individual and len(population) > 0:
            # En kotu bireyi global best ile degistir
            worst_idx = min(range(len(population)), key=lambda i: population[i].fitness)
            population[worst_idx] = self.global_best_individual.copy()
        
        return population
    
    def _add_to_memory(self, individual: Individual, fitness: float) -> None:
        """
        Hafizaya cozum ekle.
        
        En iyi cozumleri sakla (memory_size kadar).
        """
        if not self.config.use_memory:
            return
        
        # Ayni cozum zaten hafizada mi?
        for mem_ind, mem_fitness in self.memory_pool:
            if self._individuals_equal(individual, mem_ind):
                # Zaten var, fitness'i guncelle
                if fitness > mem_fitness:
                    self.memory_pool.remove((mem_ind, mem_fitness))
                    self.memory_pool.append((individual.copy(), fitness))
                    # Sirala
                    self.memory_pool.sort(key=lambda x: x[1], reverse=True)
                return
        
        # Yeni cozum ekle
        self.memory_pool.append((individual.copy(), fitness))
        
        # Sirala ve en iyileri tut
        self.memory_pool.sort(key=lambda x: x[1], reverse=True)
        if len(self.memory_pool) > self.config.memory_size:
            self.memory_pool = self.memory_pool[:self.config.memory_size]
    
    def _individuals_equal(self, ind1: Individual, ind2: Individual) -> bool:
        """Iki bireyin esit olup olmadigini kontrol et"""
        if len(ind1.assignments) != len(ind2.assignments):
            return False
        
        # Proje bazinda kontrol
        assignments1 = {a.project_id: (a.class_id, a.order_in_class, a.j1_id) 
                        for a in ind1.assignments}
        assignments2 = {a.project_id: (a.class_id, a.order_in_class, a.j1_id) 
                        for a in ind2.assignments}
        
        return assignments1 == assignments2
    
    def _calculate_diversity(self, population: List[Individual]) -> float:
        """
        Populasyon cesitliligini hesapla.
        
        Returns:
            0.0-1.0 arasi cesitlilik skoru (1.0 = cok cesitli, 0.0 = ayni)
        """
        if len(population) <= 1:
            return 1.0
        
        # Her birey icin diger bireylerle farklilik hesapla
        total_diversity = 0.0
        comparisons = 0
        
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                diversity = self._individual_diversity(population[i], population[j])
                total_diversity += diversity
                comparisons += 1
        
        if comparisons == 0:
            return 1.0
        
        return total_diversity / comparisons
    
    def _individual_diversity(self, ind1: Individual, ind2: Individual) -> float:
        """Iki birey arasindaki cesitlilik skoru"""
        if len(ind1.assignments) != len(ind2.assignments):
            return 1.0
        
        differences = 0
        total = len(ind1.assignments)
        
        for a1 in ind1.assignments:
            a2 = ind2.get_project_assignment(a1.project_id)
            if not a2:
                differences += 1
                continue
            
            if a1.class_id != a2.class_id:
                differences += 1
            if a1.order_in_class != a2.order_in_class:
                differences += 1
            if a1.j1_id != a2.j1_id:
                differences += 1
        
        return differences / (total * 3) if total > 0 else 1.0
    
    def _apply_local_improvement(self, population: List[Individual]) -> List[Individual]:
        """
        En iyi bireyleri local search ile iyilestir.
        
        En iyi %local_improvement_rate bireyi al ve local search uygula.
        """
        if not population:
            return population
        
        # Populasyonu fitness'a gore sirala
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
        
        # Iyilestirilecek birey sayisi
        improve_count = max(1, int(len(population) * self.config.local_improvement_rate))
        
        # En iyi bireyleri iyilestir
        for i in range(improve_count):
            individual = sorted_pop[i]
            improved = self._local_search(individual)
            
            # Eger iyilestirildiyse, populasyonu guncelle
            if improved.fitness > individual.fitness:
                sorted_pop[i] = improved
        
        return sorted_pop
    
    def _local_search(self, individual: Individual) -> Individual:
        """
        Bir birey uzerinde local search yap.
        
        Kucuk degisiklikler yaparak iyilestirmeye calisir.
        """
        best = individual.copy()
        best.fitness = self.penalty_calculator.calculate_fitness(best)
        
        for _ in range(self.config.local_improvement_iterations):
            # Komsu cozum olustur
            neighbor = best.copy()
            
            # Rastgele bir mutation operatoru sec
            move_type = random.choice([
                'j1_swap',
                'j1_reassign',
                'class_change',
                'order_swap'
            ])
            
            # Mutation uygula
            if move_type == 'j1_swap':
                self._local_j1_swap(neighbor)
            elif move_type == 'j1_reassign':
                self._local_j1_reassign(neighbor)
            elif move_type == 'class_change':
                self._local_class_change(neighbor)
            elif move_type == 'order_swap':
                self._local_order_swap(neighbor)
            
            # Repair ve fitness hesapla
            self.repair_mechanism.repair(neighbor)
            neighbor.fitness = self.penalty_calculator.calculate_fitness(neighbor)
            
            # Eger daha iyiyse kabul et
            if neighbor.fitness > best.fitness:
                best = neighbor
        
        return best
    
    def _local_j1_swap(self, individual: Individual) -> None:
        """Local search: Ayni siniftaki iki projenin J1'lerini degistir"""
        if len(individual.assignments) < 2:
            return
        
        class_id = random.randint(0, individual.class_count - 1)
        class_projects = individual.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return
        
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        if p1.j1_id == p2.ps_id or p2.j1_id == p1.ps_id:
            return
        
        for a in individual.assignments:
            if a.project_id == p1.project_id:
                a.j1_id = p2.j1_id
            elif a.project_id == p2.project_id:
                a.j1_id = p1.j1_id
    
    def _local_j1_reassign(self, individual: Individual) -> None:
        """Local search: Bir projenin J1'ini degistir"""
        if not individual.assignments:
            return
        
        assignment = random.choice(individual.assignments)
        
        # Proje bilgisini bul (operators'dan dictionary erisimi)
        project = self.operators.projects.get(assignment.project_id)
        
        if not project:
            return
        
        # PS haric ogretim gorevlilerinden sec
        available_j1 = [
            i_id for i_id in self.operators.faculty_ids
            if i_id != project.responsible_id and i_id != assignment.j1_id
        ]
        
        if not available_j1:
            return
        
        assignment.j1_id = random.choice(available_j1)
    
    def _local_class_change(self, individual: Individual) -> None:
        """Local search: Bir projeyi baska sinifa tasi"""
        if not individual.assignments:
            return
        
        assignment = random.choice(individual.assignments)
        old_class = assignment.class_id
        
        available_classes = [
            c for c in range(individual.class_count)
            if c != old_class
        ]
        
        if not available_classes:
            return
        
        new_class = random.choice(available_classes)
        
        new_class_count = sum(
            1 for a in individual.assignments
            if a.class_id == new_class and a.project_id != assignment.project_id
        )
        
        assignment.class_id = new_class
        assignment.order_in_class = new_class_count
        
        self.operators._reorder_class(individual, old_class)
        self.operators._reorder_class(individual, new_class)
    
    def _local_order_swap(self, individual: Individual) -> None:
        """Local search: Ayni siniftaki iki projenin sirasini degistir"""
        class_id = random.randint(0, individual.class_count - 1)
        class_projects = individual.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return
        
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        for a in individual.assignments:
            if a.project_id == p1.project_id:
                a.order_in_class = p2.order_in_class
            elif a.project_id == p2.project_id:
                a.order_in_class = p1.order_in_class
    
    def _apply_workload_rebalancing(self, population: List[Individual]) -> List[Individual]:
        """
        Populasyondaki tum bireylere workload rebalancing uygula.
        
        H2'nin weight'i 100 oldugu icin, is yuku dagilimi cok kritik.
        Bu metod, populasyonun is yuku dagilimini optimize eder.
        """
        rebalanced_population = []
        
        for individual in population:
            # Kopya al
            rebalanced = individual.copy()
            
            # Workload rebalancing uygula
            self.repair_mechanism._rebalance_workload(rebalanced)
            
            # Fitness'i yeniden hesapla
            rebalanced.fitness = self.penalty_calculator.calculate_fitness(rebalanced)
            
            rebalanced_population.append(rebalanced)
        
        return rebalanced_population
    
    def _update_adaptive_rates(self, generation: int, no_improve_count: int) -> None:
        """
        Adaptif mutation ve crossover rate'leri guncelle.
        
        Iyilesme yoksa mutation rate'i artir, crossover rate'i azalt.
        Iyilesme varsa mutation rate'i azalt, crossover rate'i artir.
        """
        # Iyilesme yoksa cesitliligi artir
        if no_improve_count > 10:
            # Mutation rate'i artir
            self.adaptive_mutation_rate = min(
                0.5, 
                self.config.mutation_rate * (1.0 + no_improve_count * 0.05)
            )
            # Crossover rate'i azalt
            self.adaptive_crossover_rate = max(
                0.5,
                self.config.crossover_rate * (1.0 - no_improve_count * 0.02)
            )
        else:
            # Iyilesme varsa, rate'leri normale yaklastir
            self.adaptive_mutation_rate = self.config.mutation_rate
            self.adaptive_crossover_rate = self.config.crossover_rate
    
    def get_name(self) -> str:
        """Algoritma adini dondur"""
        return "GeneticAlgorithm"
    
    def repair_solution(
        self, 
        solution: Dict[str, Any], 
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cozumu onar.
        
        Args:
            solution: Onarilacak cozum
            validation_result: Validation sonuclari
            
        Returns:
            Onarilmis cozum
        """
        assignments = solution.get("assignments", solution.get("schedule", []))
        
        if not assignments:
            return solution
        
        # Individual'a donustur
        individual = self._convert_schedule_to_individual(assignments)
        
        if individual:
            # Repair uygula
            self.repair_mechanism.repair(individual)
            
            # Schedule formatina geri donustur
            repaired_schedule = self._convert_individual_to_schedule(individual)
            return {"assignments": repaired_schedule}
        
        # Fallback: basit temizlik
        seen_projects = set()
        cleaned_assignments = []
        
        for a in assignments:
            project_id = a.get("project_id")
            if project_id not in seen_projects:
                seen_projects.add(project_id)
                cleaned_assignments.append(a)
        
        # Classroom/timeslot cakisma kontrolu
        used_slots = set()
        final_assignments = []
        
        for a in cleaned_assignments:
            slot_key = (a.get("classroom_id"), a.get("timeslot_id"))
            if slot_key not in used_slots:
                used_slots.add(slot_key)
                final_assignments.append(a)
        
        return {"assignments": final_assignments}


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_genetic_algorithm(params: Dict[str, Any] = None) -> GeneticAlgorithm:
    """
    Genetic Algorithm olustur.
    
    Args:
        params: Algoritma parametreleri
        
    Returns:
        GeneticAlgorithm instance
    """
    return GeneticAlgorithm(params)


# ============================================================================
# BACKWARD COMPATIBILITY ALIAS
# ============================================================================

# Alias for backward compatibility with existing factory imports
EnhancedGeneticAlgorithm = GeneticAlgorithm

