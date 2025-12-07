"""
Tabu Search (Tabu Arama) Algoritmasi - Cok Kriterli Akademik Proje Sinavi/Juri Planlama

Bu modul, universite donem sonu Ara Proje ve Bitirme Projesi degerlendirme surecleri icin
ileri duzey optimizasyon teknikleri kullanan bir Sinav/Juri Planlama ve Atama Sistemidir.

Temel Ozellikler:
- Her proje icin 3 rol: Proje Sorumlusu (PS), 1. Juri (J1), 2. Juri (placeholder)
- Back-to-back sinif ici yerlesim
- Timeslotlar arasi gap engelleme
- Is yuku uniformitesi (±2 bandi)
- Proje turu onceliklendirme (ARA_ONCE, BITIRME_ONCE, ESIT)
- Cok kriterli amac fonksiyonu: min Z = C1·H1(n) + C2·H2(n) + C3·H3(n)

Matematiksel Model:
- H1: Zaman/Gap Cezasi (ardisik olmayan gorevler)
- H2: Is Yuku Uniformite Cezasi
- H3: Sinif Degisimi Cezasi

Konfigurasyon:
- priority_mode: {ARA_ONCE, BITIRME_ONCE, ESIT}
- time_penalty_mode: {BINARY, GAP_PROPORTIONAL}
- workload_constraint_mode: {SOFT_ONLY, SOFT_AND_HARD}
"""

from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import random
import copy
import hashlib
import time
import logging
import numpy as np

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


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
class TabuConfig:
    """Tabu Search konfigurasyon parametreleri"""
    # Temel parametreler
    max_iterations: int = 500
    time_limit: int = 120  # saniye
    no_improve_limit: int = 50  # iyilesme olmadan max iterasyon
    
    # Tabu listesi parametreleri
    tabu_tenure: int = 15  # yasak suresi
    aspiration_enabled: bool = True
    
    # Komsu uretimi parametreleri
    neighborhood_size: int = 50
    
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
    
    # Agirlik katsayilari
    weight_h1: float = 1.0   # C1: Zaman/Gap cezasi agirligi
    weight_h2: float = 2.0   # C2: Is yuku cezasi agirligi (en onemli)
    weight_h3: float = 1.0   # C3: Sinif degisimi cezasi agirligi
    weight_h4: float = 0.5   # C4: Sinif yuk dengesi cezasi agirligi
    
    # Slot suresi
    slot_duration: float = 0.5  # saat (30 dakika)
    tolerance: float = 0.001


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


@dataclass
class Solution:
    """Tam cozum temsili"""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    
    def copy(self) -> 'Solution':
        """Cozumun derin kopyasi"""
        new_sol = Solution(class_count=self.class_count)
        new_sol.assignments = [
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
        return new_sol
    
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


@dataclass
class TabuEntry:
    """Tabu listesi girdisi"""
    move_type: str
    project_id: int
    attribute: Any  # class_id, j1_id, vb.
    expiry: int  # tabu'nun bitis iterasyonu


# ============================================================================
# PENALTY CALCULATOR
# ============================================================================

class PenaltyCalculator:
    """Ceza fonksiyonlari hesaplayici"""
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: TabuConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece ogretim gorevlilerini al (asistanlar dahil degil)
        self.faculty_instructors = {
            i.id: i for i in instructors 
            if i.type == "instructor"
        }
        
        # Ortalama is yuku hesapla
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.total_workload = 2 * num_projects  # Her proje 2 gorev: PS + J1
        self.avg_workload = self.total_workload / num_faculty if num_faculty > 0 else 0
    
    def calculate_total_penalty(self, solution: Solution) -> float:
        """
        Toplam ceza degerini hesapla.
        
        min Z = C1·H1(n) + C2·H2(n) + C3·H3(n) + C4·H4(n)
        """
        h1 = self.calculate_h1_time_penalty(solution)
        h2 = self.calculate_h2_workload_penalty(solution)
        h3 = self.calculate_h3_class_change_penalty(solution)
        h4 = self.calculate_h4_class_load_penalty(solution)
        
        total = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3 +
            self.config.weight_h4 * h4
        )
        
        return total
    
    def calculate_h1_time_penalty(self, solution: Solution) -> float:
        """
        H1: Zaman/Gap cezasi - ardisik olmayan gorevler icin ceza.
        
        Her ogretim gorevlisi icin zaman sirasina gore gorevlerini analiz et.
        Iki ardisik gorev arasinda bosluk varsa ceza uygula.
        """
        total_penalty = 0.0
        
        # Her ogretim gorevlisi icin gorev matrisini olustur
        instructor_tasks = self._build_instructor_task_matrix(solution)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Gorevleri zaman sirasina gore sirala (class_id, order)
            tasks.sort(key=lambda x: (x['class_id'], x['order']))
            
            # Ardisik gorevleri kontrol et
            for r in range(len(tasks) - 1):
                current = tasks[r]
                next_task = tasks[r + 1]
                
                # Ayni siniftaysalar ve ardisik degilseler ceza
                if current['class_id'] == next_task['class_id']:
                    gap = next_task['order'] - current['order'] - 1
                    
                    if gap > 0:
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1
                        else:  # GAP_PROPORTIONAL
                            total_penalty += gap
                else:
                    # Farkli siniflara gecis - bu da bir kesinti
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += 1
                    else:
                        total_penalty += 1  # Sinif degisimi 1 birim ceza
        
        return total_penalty
    
    def calculate_h2_workload_penalty(self, solution: Solution) -> float:
        """
        H2: Is yuku uniformite cezasi.
        
        Her ogretim gorevlisinin is yuku Avg ± 2 bandinda olmali.
        Bant disindaki her birim icin ceza.
        
        IsYukuCezasi_i = max(0, |GorevSayisi_i - L_avg| - 2)
        H2(n) = sum(IsYukuCezasi_i)
        """
        total_penalty = 0.0
        
        # Her ogretim gorevlisi icin gorev sayisini hesapla
        workload = self._calculate_instructor_workloads(solution)
        
        for instructor_id in self.faculty_instructors.keys():
            load = workload.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            
            # ±2 tolerans
            penalty = max(0, deviation - 2)
            total_penalty += penalty
            
            # Sert kisit kontrolu
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.workload_hard_limit:
                    total_penalty += 1000  # Cok buyuk ceza
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, solution: Solution) -> float:
        """
        H3: Sinif degisimi cezasi.
        
        Her ogretim gorevlisinin gorev yaptigi sinif sayisi.
        1-2 sinif idealdir, daha fazla sinif icin ceza.
        
        ClassChangeCezasi_i = max(0, ClassCount(i) - 2)
        H3(n) = sum(ClassChangeCezasi_i)
        """
        total_penalty = 0.0
        
        # Her ogretim gorevlisi icin sinif sayisini hesapla
        instructor_classes = defaultdict(set)
        
        for assignment in solution.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty_instructors.keys():
            class_count = len(instructor_classes.get(instructor_id, set()))
            penalty = max(0, class_count - 2)
            total_penalty += penalty
        
        return total_penalty
    
    def calculate_h4_class_load_penalty(self, solution: Solution) -> float:
        """
        H4: Sinif is yuku dengesi cezasi.
        
        Her sinifin is yuku hedef degere yakin olmali.
        Target = 2 * num_projects / class_count
        """
        total_penalty = 0.0
        
        num_projects = len(solution.assignments)
        target_per_class = (2 * num_projects) / solution.class_count
        
        # Sinif basina proje sayisi
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 2  # Her proje 2 is yuku
        
        for class_id in range(solution.class_count):
            load = class_loads.get(class_id, 0)
            penalty = abs(load - target_per_class)
            total_penalty += penalty
        
        return total_penalty
    
    def calculate_continuity_penalty(self, solution: Solution) -> float:
        """
        Devamlililk cezasi (ek olarak).
        
        Her ogretim gorevlisi icin her siniftaki blok sayisini hesapla.
        Ideal: 1 blok (arka arkaya gorevler)
        """
        total_penalty = 0.0
        
        for instructor_id in self.faculty_instructors.keys():
            for class_id in range(solution.class_count):
                blocks = self._count_blocks(solution, instructor_id, class_id)
                penalty = max(0, blocks - 1)
                total_penalty += penalty
        
        return total_penalty
    
    def _build_instructor_task_matrix(
        self, 
        solution: Solution
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Her ogretim gorevlisi icin gorev matrisi olustur"""
        instructor_tasks = defaultdict(list)
        
        for assignment in solution.assignments:
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
    
    def _calculate_instructor_workloads(
        self, 
        solution: Solution
    ) -> Dict[int, int]:
        """Her ogretim gorevlisi icin toplam is yukunu hesapla"""
        workload = defaultdict(int)
        
        for assignment in solution.assignments:
            workload[assignment.ps_id] += 1
            workload[assignment.j1_id] += 1
        
        return workload
    
    def _count_blocks(
        self, 
        solution: Solution, 
        instructor_id: int, 
        class_id: int
    ) -> int:
        """Ogretim gorevlisinin belirli siniftaki blok sayisini hesapla"""
        class_projects = solution.get_class_projects(class_id)
        
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
# NEIGHBORHOOD GENERATOR
# ============================================================================

class NeighborhoodGenerator:
    """Komsu cozum uretici"""
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: TabuConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece ogretim gorevlileri
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
    
    def generate_neighbors(
        self, 
        solution: Solution, 
        count: int = None
    ) -> List[Tuple[Solution, str, int, Any]]:
        """
        Komsu cozumler uret.
        
        Returns:
            List of (neighbor_solution, move_type, project_id, attribute)
        """
        if count is None:
            count = self.config.neighborhood_size
        
        neighbors = []
        move_types = [
            'j1_swap',          # Ayni sinifta J1 degistir
            'j1_reassign',      # J1 yeniden ata
            'project_move',     # Projeyi baska sinifa tasi
            'project_swap',     # Iki projenin sinifini degistir
            'order_swap'        # Sinif ici sira degistir
        ]
        
        for _ in range(count):
            move_type = random.choice(move_types)
            neighbor = None
            project_id = -1
            attribute = None
            
            if move_type == 'j1_swap':
                result = self._generate_j1_swap(solution)
            elif move_type == 'j1_reassign':
                result = self._generate_j1_reassign(solution)
            elif move_type == 'project_move':
                result = self._generate_project_move(solution)
            elif move_type == 'project_swap':
                result = self._generate_project_swap(solution)
            elif move_type == 'order_swap':
                result = self._generate_order_swap(solution)
            else:
                continue
            
            if result is not None:
                neighbors.append(result)
        
        return neighbors
    
    def _generate_j1_swap(
        self, 
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """
        Hareket Tipi 1: J1 Swap (ayni sinif icinde)
        Ayni siniftaki iki projenin J1'lerini degistir.
        """
        # Rastgele bir sinif sec
        class_id = random.randint(0, solution.class_count - 1)
        class_projects = solution.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return None
        
        # Iki proje sec
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        # J1'leri swap et (kendi projesine juri olma kuralini kontrol et)
        if p1.j1_id == p2.ps_id or p2.j1_id == p1.ps_id:
            return None
        
        # Yeni cozum olustur
        new_solution = solution.copy()
        
        for a in new_solution.assignments:
            if a.project_id == p1.project_id:
                a.j1_id = p2.j1_id
            elif a.project_id == p2.project_id:
                a.j1_id = p1.j1_id
        
        return (new_solution, 'j1_swap', p1.project_id, p2.j1_id)
    
    def _generate_j1_reassign(
        self, 
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """
        Hareket Tipi 2: J1 Reassignment
        Bir projenin J1'ini degistir.
        """
        if not solution.assignments:
            return None
        
        # Rastgele bir proje sec
        assignment = random.choice(solution.assignments)
        project = self.projects.get(assignment.project_id)
        
        if not project:
            return None
        
        # PS haric ogretim gorevlilerinden sec
        available_j1 = [
            i_id for i_id in self.faculty_ids 
            if i_id != project.responsible_id and i_id != assignment.j1_id
        ]
        
        if not available_j1:
            return None
        
        new_j1 = random.choice(available_j1)
        
        # Yeni cozum olustur
        new_solution = solution.copy()
        
        for a in new_solution.assignments:
            if a.project_id == assignment.project_id:
                old_j1 = a.j1_id
                a.j1_id = new_j1
                break
        
        return (new_solution, 'j1_reassign', assignment.project_id, new_j1)
    
    def _generate_project_move(
        self, 
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """
        Hareket Tipi 3: Proje Sinif Degisimi
        Bir projeyi baska sinifa tasi.
        """
        if not solution.assignments:
            return None
        
        # Rastgele bir proje sec
        assignment = random.choice(solution.assignments)
        
        # Farkli bir sinif sec
        available_classes = [
            c for c in range(solution.class_count) 
            if c != assignment.class_id
        ]
        
        if not available_classes:
            return None
        
        new_class = random.choice(available_classes)
        
        # Yeni cozum olustur
        new_solution = solution.copy()
        
        # Eski siniftan cikar ve yeni sinifa ekle
        for a in new_solution.assignments:
            if a.project_id == assignment.project_id:
                old_class = a.class_id
                a.class_id = new_class
                # Yeni sinifin sonuna ekle
                new_class_projects = [
                    x for x in new_solution.assignments 
                    if x.class_id == new_class and x.project_id != a.project_id
                ]
                a.order_in_class = len(new_class_projects)
                break
        
        # Eski siniftaki siralari guncelle
        self._reorder_class(new_solution, old_class)
        
        return (new_solution, 'project_move', assignment.project_id, new_class)
    
    def _generate_project_swap(
        self, 
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """
        Hareket Tipi 4: Proje Swap (iki sinif arasinda)
        Farkli siniflardaki iki projenin siniflarini degistir.
        """
        if len(solution.assignments) < 2:
            return None
        
        # Farkli siniflarda iki proje sec
        assignments = solution.assignments.copy()
        random.shuffle(assignments)
        
        p1 = assignments[0]
        p2 = None
        
        for a in assignments[1:]:
            if a.class_id != p1.class_id:
                p2 = a
                break
        
        if p2 is None:
            return None
        
        # Yeni cozum olustur
        new_solution = solution.copy()
        
        for a in new_solution.assignments:
            if a.project_id == p1.project_id:
                a.class_id = p2.class_id
                a.order_in_class = p2.order_in_class
            elif a.project_id == p2.project_id:
                a.class_id = p1.class_id
                a.order_in_class = p1.order_in_class
        
        return (new_solution, 'project_swap', p1.project_id, (p2.project_id, p2.class_id))
    
    def _generate_order_swap(
        self, 
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """
        Hareket Tipi 5: Sinif Ici Sira Degisimi
        Ayni siniftaki iki projenin sirasini degistir.
        """
        # Rastgele bir sinif sec
        class_id = random.randint(0, solution.class_count - 1)
        class_projects = solution.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return None
        
        # Iki proje sec
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        # Yeni cozum olustur
        new_solution = solution.copy()
        
        for a in new_solution.assignments:
            if a.project_id == p1.project_id:
                a.order_in_class = p2.order_in_class
            elif a.project_id == p2.project_id:
                a.order_in_class = p1.order_in_class
        
        return (new_solution, 'order_swap', p1.project_id, p2.project_id)
    
    def _reorder_class(self, solution: Solution, class_id: int) -> None:
        """Sinif icindeki siralari yeniden duzelt"""
        class_projects = [a for a in solution.assignments if a.class_id == class_id]
        class_projects.sort(key=lambda x: x.order_in_class)
        
        for i, a in enumerate(class_projects):
            for assignment in solution.assignments:
                if assignment.project_id == a.project_id:
                    assignment.order_in_class = i
                    break


# ============================================================================
# MAIN TABU SEARCH ALGORITHM
# ============================================================================

class TabuSearch(OptimizationAlgorithm):
    """
    Tabu Search (Tabu Arama) algoritmasi - Cok Kriterli Akademik Proje Planlama.
    
    Tek fazli calisma prensibi:
    - Tum projeler, hocalar, sinif sayisi tek seferde modele verilir
    - Tabu Search iteratif olarak calisir
    - En iyi cozum tek seferde planner'a aktarilir
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Tabu Search algoritmasi baslatici.
        
        Args:
            params: Algoritma parametreleri
        """
        super().__init__(params)
        params = params or {}
        
        # Konfigurasyon olustur
        self.config = TabuConfig(
            max_iterations=params.get("max_iterations", 500),
            time_limit=params.get("time_limit", 120),
            no_improve_limit=params.get("no_improve_limit", 50),
            tabu_tenure=params.get("tabu_tenure", 15),
            neighborhood_size=params.get("neighborhood_size", 50),
            class_count=params.get("class_count", 6),
            auto_class_count=params.get("auto_class_count", True),
            priority_mode=PriorityMode(params.get("priority_mode", "ESIT")),
            time_penalty_mode=TimePenaltyMode(params.get("time_penalty_mode", "GAP_PROPORTIONAL")),
            workload_constraint_mode=WorkloadConstraintMode(
                params.get("workload_constraint_mode", "SOFT_ONLY")
            ),
            weight_h1=params.get("weight_h1", 1.0),
            weight_h2=params.get("weight_h2", 2.0),
            weight_h3=params.get("weight_h3", 1.0),
            weight_h4=params.get("weight_h4", 0.5)
        )
        
        # Veri yapilari
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        
        # Tabu listesi
        self.tabu_list: List[TabuEntry] = []
        
        # En iyi cozum
        self.best_solution: Optional[Solution] = None
        self.best_cost: float = float('inf')
        
        # Yardimci siniflar
        self.penalty_calculator: Optional[PenaltyCalculator] = None
        self.neighborhood_generator: Optional[NeighborhoodGenerator] = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Algoritmay baslangic verileri ile baslatir.
        
        Args:
            data: Algoritma giris verileri
        """
        # Verileri yukle
        self._load_data(data)
        
        # CRITICAL: Ensure class_count matches actual classrooms after _load_data
        # _load_data may have updated self.config.class_count based on available classrooms
        if self.classrooms:
            actual_class_count = len(self.classrooms)
            if self.config.class_count != actual_class_count:
                logger.info(f"Tabu Search: class_count {self.config.class_count} -> {actual_class_count} (mevcut sınıf sayısı)")
                self.config.class_count = actual_class_count
        
        # Yardimci siniflari olustur
        self.penalty_calculator = PenaltyCalculator(
            self.projects, self.instructors, self.config
        )
        self.neighborhood_generator = NeighborhoodGenerator(
            self.projects, self.instructors, self.config
        )
        
        # Tabu listesini temizle
        self.tabu_list = []
        
        # En iyi cozumu sifirla
        self.best_solution = None
        self.best_cost = float('inf')
        
        # CRITICAL: Log final class_count to verify
        logger.info(f"Tabu Search initialize: Final class_count = {self.config.class_count}, classrooms = {len(self.classrooms)}")
    
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
        all_classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # CRITICAL: Sınıf sayısı kontrolü - Genetic Algorithm ve Simulated Annealing'deki gibi
        # Eğer classroom_count belirtilmişse, o kadar sınıf kullan
        classroom_count = data.get("classroom_count")
        if classroom_count and classroom_count > 0:
            if classroom_count > len(all_classrooms):
                logger.warning(
                    f"İstenen sınıf sayısı ({classroom_count}) mevcut sınıf sayısından "
                    f"({len(all_classrooms)}) fazla. Tüm sınıflar kullanılacak."
                )
                self.classrooms = all_classrooms
                self.config.class_count = len(all_classrooms)
                # Kullanıcı belirli bir sayı istedi, auto_class_count'u kapat
                self.config.auto_class_count = False
            else:
                self.classrooms = all_classrooms[:classroom_count]
                self.config.class_count = classroom_count
                # Kullanıcı belirli bir sayı istedi, auto_class_count'u kapat
                self.config.auto_class_count = False
                logger.info(f"Tabu Search: {classroom_count} sınıf kullanılıyor")
        else:
            # classroom_count belirtilmemişse, mevcut sınıflara göre ayarla
            if all_classrooms:
                available_class_count = len(all_classrooms)
                # Eğer config'de class_count mevcut sınıf sayısından farklıysa, mevcut sınıf sayısını kullan
                if self.config.class_count != available_class_count:
                    # Eğer auto_class_count aktifse veya default değerse, mevcut sınıf sayısını kullan
                    if self.config.auto_class_count or self.config.class_count == 6:  # Default 6
                        self.config.class_count = available_class_count
                        logger.info(f"Tabu Search: Sınıf sayısı otomatik olarak {available_class_count} olarak ayarlandı (mevcut sınıf sayısı)")
                else:
                    logger.info(f"Tabu Search: {self.config.class_count} sınıf kullanılacak")
            
            # Sınıfları ayarla
            if self.config.class_count <= len(all_classrooms):
                self.classrooms = all_classrooms[:self.config.class_count]
            else:
                self.classrooms = all_classrooms
                self.config.class_count = len(all_classrooms)
                logger.info(f"Tabu Search: Tüm {len(all_classrooms)} sınıf kullanılacak")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Tabu Search algoritmasini calistirir.
        
        Args:
            data: Algoritma giris verileri (optional, initialize zaten execute tarafindan cagrildi)
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu
        """
        # NOT: initialize zaten base.execute() tarafindan cagrildi, burada tekrar cagirmaya gerek yok
        # if data:
        #     self.initialize(data)
        
        start_time = time.time()
        
        # Eger auto_class_count aktifse, 5, 6, 7 icin en iyi sonucu bul
        if self.config.auto_class_count:
            best_result = None
            best_overall_cost = float('inf')
            
            for class_count in [5, 6, 7]:
                logger.info(f"Sinif sayisi {class_count} ile calistiriliyor...")
                self.config.class_count = class_count
                
                result = self._run_tabu_search()
                
                if result['cost'] < best_overall_cost:
                    best_overall_cost = result['cost']
                    best_result = result
            
            result = best_result
        else:
            result = self._run_tabu_search()
        
        end_time = time.time()
        
        # Cozumu output formatina donustur
        schedule = self._convert_solution_to_schedule(result['solution'])
        
        return {
            "schedule": schedule,
            "assignments": schedule,
            "solution": schedule,
            "fitness": -result['cost'],  # Maliyet negatif fitness
            "cost": result['cost'],
            "iterations": result['iterations'],
            "execution_time": end_time - start_time,
            "class_count": result['solution'].class_count,
            "penalty_breakdown": result.get('penalty_breakdown', {}),
            "status": "completed"
        }
    
    def _run_tabu_search(self) -> Dict[str, Any]:
        """
        Ana Tabu Search dongusu.
        
        Returns:
            En iyi cozum ve istatistikler
        """
        start_time = time.time()
        
        # Baslangic cozumu olustur
        current_solution = self._create_initial_solution()
        current_cost = self.penalty_calculator.calculate_total_penalty(current_solution)
        
        # En iyi cozumu baslat
        self.best_solution = current_solution.copy()
        self.best_cost = current_cost
        
        # Iterasyon sayaclari
        iteration = 0
        no_improve_count = 0
        
        logger.info(f"Baslangic maliyeti: {current_cost:.2f}")
        
        # Ana dongu
        while (iteration < self.config.max_iterations and
               no_improve_count < self.config.no_improve_limit and
               time.time() - start_time < self.config.time_limit):
            
            # Komsu cozumler olustur
            neighbors = self.neighborhood_generator.generate_neighbors(
                current_solution, 
                self.config.neighborhood_size
            )
            
            # En iyi tabu-olmayan komsuyu bul
            best_neighbor = None
            best_neighbor_cost = float('inf')
            best_move_info = None
            
            for neighbor, move_type, project_id, attribute in neighbors:
                neighbor_cost = self.penalty_calculator.calculate_total_penalty(neighbor)
                
                # Tabu kontrolu
                is_tabu = self._is_tabu(move_type, project_id, attribute, iteration)
                
                # Aspiration kriteri: tabu olsa bile en iyi cozumden iyiyse kabul et
                aspiration = (
                    self.config.aspiration_enabled and 
                    neighbor_cost < self.best_cost
                )
                
                if (not is_tabu or aspiration) and neighbor_cost < best_neighbor_cost:
                    best_neighbor = neighbor
                    best_neighbor_cost = neighbor_cost
                    best_move_info = (move_type, project_id, attribute)
            
            # Eger komsu bulunamadiysa, yeni baslangic cozumu
            if best_neighbor is None:
                current_solution = self._create_initial_solution()
                current_cost = self.penalty_calculator.calculate_total_penalty(current_solution)
                no_improve_count += 1
                iteration += 1
                continue
            
            # Mevcut cozumu guncelle
            current_solution = best_neighbor
            current_cost = best_neighbor_cost
            
            # Tabu listesine ekle
            if best_move_info:
                self._add_tabu(best_move_info[0], best_move_info[1], 
                             best_move_info[2], iteration)
            
            # En iyi cozumu guncelle
            if current_cost < self.best_cost:
                self.best_solution = current_solution.copy()
                self.best_cost = current_cost
                no_improve_count = 0
                logger.info(f"Iterasyon {iteration}: Yeni en iyi maliyet = {self.best_cost:.2f}")
            else:
                no_improve_count += 1
            
            # Eski tabu girdilerini temizle
            self._cleanup_tabu(iteration)
            
            iteration += 1
        
        # Ceza detaylarini hesapla
        penalty_breakdown = {
            'h1_time_penalty': self.penalty_calculator.calculate_h1_time_penalty(self.best_solution),
            'h2_workload_penalty': self.penalty_calculator.calculate_h2_workload_penalty(self.best_solution),
            'h3_class_change_penalty': self.penalty_calculator.calculate_h3_class_change_penalty(self.best_solution),
            'h4_class_load_penalty': self.penalty_calculator.calculate_h4_class_load_penalty(self.best_solution)
        }
        
        logger.info(f"Tabu Search tamamlandi: {iteration} iterasyon, "
                   f"maliyet = {self.best_cost:.2f}")
        
        return {
            'solution': self.best_solution,
            'cost': self.best_cost,
            'iterations': iteration,
            'penalty_breakdown': penalty_breakdown
        }
    
    def _create_initial_solution(self) -> Solution:
        """
        Baslangic cozumu olusturur.
        
        Heuristic yaklasim:
        1. Projeleri PS'ye gore grupla
        2. Siniflara dengeli dagit
        3. J1 atamasini yap
        """
        solution = Solution(class_count=self.config.class_count)
        
        # Proje turune gore sirala (onceliklendirme)
        sorted_projects = self._sort_projects_by_priority()
        
        # Siniflara dagit
        class_assignments = [[] for _ in range(self.config.class_count)]
        
        # Round-robin dagitim
        for i, project in enumerate(sorted_projects):
            class_id = i % self.config.class_count
            class_assignments[class_id].append(project)
        
        # Her sinif icin projeleri ata
        for class_id, projects_in_class in enumerate(class_assignments):
            for order, project in enumerate(projects_in_class):
                # J1 sec (PS haric)
                j1_id = self._select_j1_for_project(
                    project, 
                    solution, 
                    class_id
                )
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=class_id,
                    order_in_class=order,
                    ps_id=project.responsible_id,
                    j1_id=j1_id,
                    j2_id=-1  # Placeholder
                )
                solution.assignments.append(assignment)
        
        return solution
    
    def _sort_projects_by_priority(self) -> List[Project]:
        """Projeleri onceliklendirme moduna gore sirala"""
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            # Ara projeler once
            ara = [p for p in self.projects if p.type in ('interim', 'ara')]
            bitirme = [p for p in self.projects if p.type in ('final', 'bitirme')]
            return ara + bitirme
        
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            # Bitirme projeleri once
            bitirme = [p for p in self.projects if p.type in ('final', 'bitirme')]
            ara = [p for p in self.projects if p.type in ('interim', 'ara')]
            return bitirme + ara
        
        else:  # ESIT
            return list(self.projects)
    
    def _select_j1_for_project(
        self, 
        project: Project, 
        solution: Solution,
        target_class_id: int
    ) -> int:
        """
        Proje icin J1 sec.
        
        Kurallar:
        - PS projeye juri olamaz
        - Is yuku dengesi gozetilmeli
        - Ayni sinifta olmak tercih edilir
        """
        # Mevcut is yuklerini hesapla
        workloads = defaultdict(int)
        for a in solution.assignments:
            workloads[a.ps_id] += 1
            workloads[a.j1_id] += 1
        
        # PS dahil edilmez
        workloads[project.responsible_id] += 1
        
        # Ogretim gorevlilerini sirala (is yukune gore)
        faculty_ids = [
            i.id for i in self.instructors 
            if i.type == "instructor" and i.id != project.responsible_id
        ]
        
        # En az yuke sahip olan tercih edilir
        faculty_ids.sort(key=lambda x: workloads.get(x, 0))
        
        if faculty_ids:
            return faculty_ids[0]
        
        # Fallback: herhangi biri
        all_ids = [i.id for i in self.instructors if i.id != project.responsible_id]
        return random.choice(all_ids) if all_ids else project.responsible_id
    
    def _is_tabu(
        self, 
        move_type: str, 
        project_id: int, 
        attribute: Any,
        current_iteration: int
    ) -> bool:
        """Hareketin tabu olup olmadigini kontrol et"""
        for entry in self.tabu_list:
            if (entry.move_type == move_type and 
                entry.project_id == project_id and
                entry.attribute == attribute and
                entry.expiry > current_iteration):
                return True
        return False
    
    def _add_tabu(
        self, 
        move_type: str, 
        project_id: int, 
        attribute: Any,
        current_iteration: int
    ) -> None:
        """Hareketi tabu listesine ekle"""
        entry = TabuEntry(
            move_type=move_type,
            project_id=project_id,
            attribute=attribute,
            expiry=current_iteration + self.config.tabu_tenure
        )
        self.tabu_list.append(entry)
    
    def _cleanup_tabu(self, current_iteration: int) -> None:
        """Suresi dolan tabu girdilerini temizle"""
        self.tabu_list = [
            entry for entry in self.tabu_list 
            if entry.expiry > current_iteration
        ]
    
    def _convert_solution_to_schedule(
        self, 
        solution: Solution
    ) -> List[Dict[str, Any]]:
        """
        Solution'i schedule formatina donustur.
        
        Her atama icin:
        - project_id
        - classroom_id
        - timeslot_id
        - instructors (PS, J1, J2)
        """
        schedule = []
        
        if not solution or not solution.assignments:
            return schedule
        
        # Sinif ve timeslot eslestirmesi olustur
        classroom_mapping = self._create_classroom_mapping(solution.class_count)
        timeslot_mapping = self._create_timeslot_mapping()
        
        for assignment in solution.assignments:
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
            # Bu sadece frontend'de görünecek, algoritma içinde parametrize edilmez
            instructors = [assignment.ps_id, assignment.j1_id, "[Araştırma Görevlisi]"]
            
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
        
        if isinstance(assignments, Solution):
            cost = self.penalty_calculator.calculate_total_penalty(assignments)
            return -cost  # Daha dusuk maliyet = daha yuksek fitness
        
        # Dict listesi ise Solution'a donustur
        if isinstance(assignments, list):
            sol = self._convert_schedule_to_solution(assignments)
            if sol:
                cost = self.penalty_calculator.calculate_total_penalty(sol)
                return -cost
        
        return float('-inf')
    
    def _convert_schedule_to_solution(
        self, 
        schedule: List[Dict[str, Any]]
    ) -> Optional[Solution]:
        """Schedule formatindan Solution'a donustur"""
        if not schedule:
            return None
        
        solution = Solution(class_count=self.config.class_count)
        
        for entry in schedule:
            project_id = entry.get("project_id")
            instructors = entry.get("instructors", [])
            
            if not project_id or len(instructors) < 2:
                continue
            
            assignment = ProjectAssignment(
                project_id=project_id,
                class_id=entry.get("class_id", 0),
                order_in_class=entry.get("class_order", 0),
                ps_id=instructors[0],
                j1_id=instructors[1],
                j2_id=instructors[2] if len(instructors) > 2 else -1
            )
            solution.assignments.append(assignment)
        
        return solution
    
    def get_name(self) -> str:
        """Algoritma adini dondur"""
        return "TabuSearch"
    
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
        
        # Duplicate kontrol ve temizlik
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

def create_tabu_search(params: Dict[str, Any] = None) -> TabuSearch:
    """
    Tabu Search algoritmasi olustur.
    
    Args:
        params: Algoritma parametreleri
        
    Returns:
        TabuSearch instance
    """
    return TabuSearch(params)

