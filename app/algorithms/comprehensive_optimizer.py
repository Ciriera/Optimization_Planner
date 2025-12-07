"""
Kapsamlı Optimizasyon (Comprehensive Optimizer) - Akademik Proje Jüri Atama Sistemi

Bu modül, üniversite dönem sonu Ara Proje ve Bitirme Projesi değerlendirme süreçleri için
ileri düzey optimizasyon teknikleri kullanan kapsamlı bir Sınav/Jüri Planlama ve Atama Sistemidir.

Temel Özellikler:
- Her proje için 3 rol: Proje Sorumlusu (PS), 1. Jüri (J1), 2. Jüri (placeholder)
- Back-to-back sınıf içi yerleşim
- Timeslotlar arası gap engelleme
- İş yükü uniformitesi (±2 bandı)
- Proje türü önceliklendirme (ARA_ONCE, BITIRME_ONCE, ESIT)
- Instructor pairing logic ile dengeli sınıf dağılımı
- Çok kriterli amaç fonksiyonu: min Z = C1·H1 + C2·H2 + C3·H3

Matematiksel Model:
- H1: Zaman/Gap Cezası (ardışık olmayan görevler)
- H2: İş Yükü Uniformite Cezası
- H3: Sınıf Değişimi Cezası

Konfigürasyon:
- priority_mode: {ARA_ONCE, BITIRME_ONCE, ESIT}
- time_penalty_mode: {BINARY, GAP_PROPORTIONAL}
- workload_constraint_mode: {SOFT_ONLY, SOFT_AND_HARD}

Instructor Pairing Logic:
- Öğretim görevlileri PS yüküne göre azalan sıralanır
- Dengeli "çiftler" oluşturulur: combined_load ≈ ideal_pair_load
- Bu çiftler sınıf seviyesinde container olarak kullanılır
"""

from typing import Dict, Any, List, Tuple, Set, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random
import copy
import time
import logging
import math

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION ENUMS
# ============================================================================

class PriorityMode(str, Enum):
    """Proje türü önceliklendirme modu."""
    ARA_ONCE = "ARA_ONCE"           # Ara projeler önce
    BITIRME_ONCE = "BITIRME_ONCE"   # Bitirme projeleri önce
    ESIT = "ESIT"                   # Öncelik yok


class TimePenaltyMode(str, Enum):
    """Zaman cezası modu."""
    BINARY = "BINARY"                       # Ardışık değilse 1 ceza
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Aradaki slot sayısı kadar ceza


class WorkloadConstraintMode(str, Enum):
    """İş yükü kısıt modu."""
    SOFT_ONLY = "SOFT_ONLY"           # Sadece ceza
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Ceza + sert kısıt


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ComprehensiveConfig:
    """Kapsamlı Optimizasyon konfigürasyon parametreleri."""
    
    # Temel parametreler
    max_iterations: int = 1000
    time_limit: int = 180  # saniye
    no_improve_limit: int = 100  # iyileşme olmadan max iterasyon
    
    # Tabu listesi parametreleri
    tabu_tenure: int = 20  # yasak süresi
    aspiration_enabled: bool = True
    
    # Komşu üretimi parametreleri
    neighborhood_size: int = 80
    
    # Sınıf sayısı
    class_count: int = 6  # 5, 6 veya 7 olabilir
    auto_class_count: bool = True  # True ise 5,6,7 için en iyi seç
    
    # Önceliklendirme modu
    priority_mode: PriorityMode = PriorityMode.ESIT
    
    # Zaman cezası modu
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    
    # İş yükü kısıt modu
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4  # B_max: maksimum sapma
    workload_soft_band: int = 2   # ±2 tolerans bandı
    
    # Ağırlık katsayıları (C2 > C1, C2 > C3)
    weight_h1: float = 1.0   # C1: Zaman/Gap cezası ağırlığı
    weight_h2: float = 3.0   # C2: İş yükü cezası ağırlığı (EN ÖNEMLİ)
    weight_h3: float = 1.0   # C3: Sınıf değişimi cezası ağırlığı
    weight_h4: float = 2.0   # C4: Sınıf yükü dengesizliği cezası ağırlığı
    
    # Instructor pairing toleransı
    pairing_tolerance: int = 3  # δ: pair load toleransı
    
    # Slot süresi
    slot_duration: float = 0.5  # saat (30 dakika)
    tolerance: float = 0.001


@dataclass
class InstructorData:
    """Öğretim görevlisi veri yapısı."""
    id: int
    name: str
    type: str  # "instructor" veya "assistant"
    ps_load: int = 0  # Proje sorumlusu olarak yük
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, InstructorData):
            return self.id == other.id
        return False


@dataclass
class ProjectData:
    """Proje veri yapısı."""
    id: int
    title: str
    type: str  # "interim" (Ara) veya "final" (Bitirme)
    responsible_id: int  # Proje Sorumlusu (PS)
    is_makeup: bool = False
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, ProjectData):
            return self.id == other.id
        return False


@dataclass
class ProjectAssignment:
    """Proje atama bilgisi."""
    project_id: int
    class_id: int
    slot_in_class: int  # sınıf içindeki slot (0-indexed)
    ps_id: int  # Proje Sorumlusu (sabit)
    j1_id: int  # 1. Jüri (karar değişkeni)
    j2_id: int = -1  # 2. Jüri (placeholder - modele girmez)


@dataclass
class InstructorPair:
    """Öğretim görevlisi çifti."""
    instructor1_id: int
    instructor2_id: int
    combined_load: int
    assigned_class: int = -1


@dataclass
class Solution:
    """Tam çözüm temsili."""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    pairs: List[InstructorPair] = field(default_factory=list)
    
    def copy(self) -> 'Solution':
        """Çözümün derin kopyası."""
        new_sol = Solution(class_count=self.class_count)
        new_sol.assignments = [
            ProjectAssignment(
                project_id=a.project_id,
                class_id=a.class_id,
                slot_in_class=a.slot_in_class,
                ps_id=a.ps_id,
                j1_id=a.j1_id,
                j2_id=a.j2_id
            )
            for a in self.assignments
        ]
        new_sol.pairs = [
            InstructorPair(
                instructor1_id=p.instructor1_id,
                instructor2_id=p.instructor2_id,
                combined_load=p.combined_load,
                assigned_class=p.assigned_class
            )
            for p in self.pairs
        ]
        return new_sol
    
    def get_class_projects(self, class_id: int) -> List[ProjectAssignment]:
        """Belirli sınıftaki projeleri sırayla getir."""
        class_projects = [a for a in self.assignments if a.class_id == class_id]
        return sorted(class_projects, key=lambda x: x.slot_in_class)
    
    def get_project_assignment(self, project_id: int) -> Optional[ProjectAssignment]:
        """Proje atamasını getir."""
        for a in self.assignments:
            if a.project_id == project_id:
                return a
        return None
    
    def get_instructor_tasks(self, instructor_id: int) -> List[ProjectAssignment]:
        """Öğretim görevlisinin tüm görevlerini getir."""
        tasks = []
        for a in self.assignments:
            if a.ps_id == instructor_id or a.j1_id == instructor_id:
                tasks.append(a)
        return tasks


@dataclass
class TabuEntry:
    """Tabu listesi girdisi."""
    move_type: str
    project_id: int
    attribute: Any
    expiry: int


@dataclass
class ScoreBreakdown:
    """Skor detayları."""
    h1_time_gap: float = 0.0
    h2_workload: float = 0.0
    h3_class_change: float = 0.0
    h4_class_load_balance: float = 0.0
    c1_h1: float = 0.0
    c2_h2: float = 0.0
    c3_h3: float = 0.0
    c4_h4: float = 0.0
    total_z: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "h1_time_gap": self.h1_time_gap,
            "h2_workload": self.h2_workload,
            "h3_class_change": self.h3_class_change,
            "h4_class_load_balance": self.h4_class_load_balance,
            "c1_h1_weighted": self.c1_h1,
            "c2_h2_weighted": self.c2_h2,
            "c3_h3_weighted": self.c3_h3,
            "c4_h4_weighted": self.c4_h4,
            "total_z": self.total_z
        }


# ============================================================================
# INSTRUCTOR PAIRING LOGIC
# ============================================================================

class InstructorPairingEngine:
    """
    Öğretim görevlisi eşleştirme motoru.
    
    CRITICAL REQUIREMENT:
    - Öğretim görevlileri PS yüküne göre azalan sıralanır
    - Dengeli "çiftler" oluşturulur
    - Bu çiftler sınıf seviyesinde container olarak kullanılır
    """
    
    def __init__(
        self,
        instructors: List[InstructorData],
        projects: List[ProjectData],
        config: ComprehensiveConfig
    ):
        self.instructors = {i.id: i for i in instructors}
        self.projects = projects
        self.config = config
        
        # Sadece instructor tipindekiler (assistant hariç)
        self.faculty_instructors = {
            i.id: i for i in instructors
            if i.type == "instructor"
        }
        
        # PS yüklerini hesapla
        self._calculate_ps_loads()
    
    def _calculate_ps_loads(self) -> None:
        """Her öğretim görevlisinin PS yükünü hesapla."""
        for instructor in self.faculty_instructors.values():
            instructor.ps_load = 0
        
        for project in self.projects:
            if project.responsible_id in self.faculty_instructors:
                self.faculty_instructors[project.responsible_id].ps_load += 1
    
    def build_balanced_pairs(self) -> List[InstructorPair]:
        """
        Dengeli öğretim görevlisi çiftleri oluştur.
        
        Algoritma:
        1. Öğretim görevlilerini PS yüküne göre azalan sırala
        2. ideal_pair_load = median veya mean hesapla
        3. Her instructor için combined_load ∈ [ideal - δ, ideal + δ] olan eş bul
        
        Returns:
            List[InstructorPair]: Oluşturulan çiftler
        """
        # PS yüküne göre azalan sırala
        sorted_instructors = sorted(
            self.faculty_instructors.values(),
            key=lambda x: x.ps_load,
            reverse=True
        )
        
        if len(sorted_instructors) < 2:
            logger.warning("Yeterli öğretim görevlisi yok!")
            return []
        
        # İdeal pair load hesapla
        total_load = sum(i.ps_load for i in sorted_instructors)
        num_pairs = max(1, len(sorted_instructors) // 2)
        ideal_pair_load = total_load / num_pairs
        
        logger.info(f"İdeal pair load: {ideal_pair_load:.2f}")
        logger.info(f"Tolerans: ±{self.config.pairing_tolerance}")
        
        pairs = []
        used = set()
        
        # Greedy pairing
        for instructor in sorted_instructors:
            if instructor.id in used:
                continue
            
            best_partner = None
            best_diff = float('inf')
            
            # Eş aday
            for candidate in sorted_instructors:
                if candidate.id == instructor.id or candidate.id in used:
                    continue
                
                combined = instructor.ps_load + candidate.ps_load
                diff = abs(combined - ideal_pair_load)
                
                # Tolerans içinde mi?
                if diff <= self.config.pairing_tolerance and diff < best_diff:
                    best_partner = candidate
                    best_diff = diff
            
            # Tolerans içinde eş bulunamadıysa, en yakın olanı al
            if best_partner is None:
                for candidate in sorted_instructors:
                    if candidate.id == instructor.id or candidate.id in used:
                        continue
                    
                    combined = instructor.ps_load + candidate.ps_load
                    diff = abs(combined - ideal_pair_load)
                    
                    if diff < best_diff:
                        best_partner = candidate
                        best_diff = diff
            
            if best_partner:
                pair = InstructorPair(
                    instructor1_id=instructor.id,
                    instructor2_id=best_partner.id,
                    combined_load=instructor.ps_load + best_partner.ps_load
                )
                pairs.append(pair)
                used.add(instructor.id)
                used.add(best_partner.id)
                
                logger.info(
                    f"Çift oluşturuldu: {instructor.name} ({instructor.ps_load}) + "
                    f"{best_partner.name} ({best_partner.ps_load}) = {pair.combined_load}"
                )
        
        # Kalan tek instructor varsa
        remaining = [i for i in sorted_instructors if i.id not in used]
        if remaining:
            for inst in remaining:
                # En düşük yüklü çifte ekle veya yeni çift oluştur
                if pairs:
                    min_pair = min(pairs, key=lambda p: p.combined_load)
                    # Üçlü grup olarak işaretle (bu durumda bir sınıfta 3 instructor olabilir)
                    logger.info(f"Kalan instructor {inst.name} en düşük yüklü çifte eklendi")
        
        return pairs
    
    def assign_pairs_to_classes(
        self,
        pairs: List[InstructorPair],
        class_count: int
    ) -> Dict[int, List[InstructorPair]]:
        """
        Çiftleri sınıflara ata.
        
        Args:
            pairs: Oluşturulan çiftler
            class_count: Sınıf sayısı
        
        Returns:
            Dict[int, List[InstructorPair]]: Sınıf -> Çift listesi
        """
        class_assignments: Dict[int, List[InstructorPair]] = {
            i: [] for i in range(class_count)
        }
        
        # Çiftleri combined_load'a göre azalan sırala
        sorted_pairs = sorted(pairs, key=lambda p: p.combined_load, reverse=True)
        
        # Round-robin atama (yük dengelemesi için)
        class_loads = [0] * class_count
        class_instructor_counts = [0] * class_count  # Her sınıftaki farklı instructor sayısı
        
        for pair in sorted_pairs:
            # En düşük yüklü sınıfı bul, ama 4+ instructor olan sınıfları tercih etme
            available_classes = [
                c for c in range(class_count)
                if class_instructor_counts[c] < 4  # 4'ten az instructor olan sınıflar
            ]
            
            if not available_classes:
                # Tüm sınıflarda 4+ instructor var, en düşük yüklü olanı seç
                min_class = min(range(class_count), key=lambda c: class_loads[c])
            else:
                # 4'ten az instructor olan sınıflar arasından en düşük yüklü olanı seç
                min_class = min(available_classes, key=lambda c: class_loads[c])
            
            pair.assigned_class = min_class
            class_assignments[min_class].append(pair)
            class_loads[min_class] += pair.combined_load
            class_instructor_counts[min_class] += 2  # Her çift 2 instructor ekler
            
            logger.info(
                f"Çift (load={pair.combined_load}) -> Sınıf {min_class} "
                f"(toplam yük: {class_loads[min_class]}, instructor sayısı: {class_instructor_counts[min_class]})"
            )
        
        return class_assignments


# ============================================================================
# PENALTY CALCULATOR
# ============================================================================

class PenaltyCalculator:
    """
    Ceza fonksiyonları hesaplayıcı.
    
    OBJECTIVE: min Z = C1·H1 + C2·H2 + C3·H3 + C4·H4
    
    - H1: Zaman/Gap Cezası
    - H2: İş Yükü Uniformite Cezası
    - H3: Sınıf Değişimi Cezası
    - H4: Sınıf Yükü Dengesizliği Cezası
    """
    
    def __init__(
        self,
        projects: List[ProjectData],
        instructors: List[InstructorData],
        config: ComprehensiveConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece instructor tipindekiler
        self.faculty_instructors = {
            i.id: i for i in instructors
            if i.type == "instructor"
        }
        
        # Ortalama iş yükü hesapla
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.total_workload = 2 * num_projects  # Her proje 2 görev: PS + J1
        self.avg_workload = self.total_workload / num_faculty if num_faculty > 0 else 0
        
        logger.info(f"Ortalama iş yükü (L_avg): {self.avg_workload:.2f}")
    
    def calculate_full_penalty(self, solution: Solution) -> ScoreBreakdown:
        """
        Tüm cezaları hesapla ve detaylı skor döndür.
        
        Returns:
            ScoreBreakdown: Detaylı skor bilgisi
        """
        h1 = self.calculate_h1_time_penalty(solution)
        h2 = self.calculate_h2_workload_penalty(solution)
        h3 = self.calculate_h3_class_change_penalty(solution)
        h4 = self.calculate_h4_class_load_penalty(solution)
        
        c1_h1 = self.config.weight_h1 * h1
        c2_h2 = self.config.weight_h2 * h2
        c3_h3 = self.config.weight_h3 * h3
        c4_h4 = self.config.weight_h4 * h4
        
        total_z = c1_h1 + c2_h2 + c3_h3 + c4_h4
        
        return ScoreBreakdown(
            h1_time_gap=h1,
            h2_workload=h2,
            h3_class_change=h3,
            h4_class_load_balance=h4,
            c1_h1=c1_h1,
            c2_h2=c2_h2,
            c3_h3=c3_h3,
            c4_h4=c4_h4,
            total_z=total_z
        )
    
    def calculate_total_penalty(self, solution: Solution) -> float:
        """Toplam ceza değerini hesapla."""
        return self.calculate_full_penalty(solution).total_z
    
    def calculate_h1_time_penalty(self, solution: Solution) -> float:
        """
        H1: Zaman/Gap cezası.
        
        Her öğretim görevlisi için:
        - Aynı sınıftaki ardışık görevler arasında boşluk varsa ceza
        
        BINARY: gap > 0 ise penalty = 1
        GAP_PROPORTIONAL: penalty = gap sayısı
        """
        total_penalty = 0.0
        
        # Her instructor için görev matrisini oluştur
        instructor_tasks = self._build_instructor_task_matrix(solution)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Görevleri sınıf ve slot'a göre sırala
            tasks.sort(key=lambda x: (x['class_id'], x['slot']))
            
            # Aynı sınıftaki ardışık görevleri kontrol et
            for r in range(len(tasks) - 1):
                current = tasks[r]
                next_task = tasks[r + 1]
                
                if current['class_id'] == next_task['class_id']:
                    # Aynı sınıf - gap kontrolü
                    gap = next_task['slot'] - current['slot'] - 1
                    
                    if gap > 0:
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1
                        else:  # GAP_PROPORTIONAL
                            total_penalty += gap
        
        return total_penalty
    
    def calculate_h2_workload_penalty(self, solution: Solution) -> float:
        """
        H2: İş yükü uniformite cezası.
        
        Her öğretim görevlisi için:
        deviation = max(0, |Load(i) - L_avg| - 2)
        H2 = sum(deviation)
        
        SOFT_AND_HARD modunda: |Load(i) - L_avg| > B_max ise büyük ceza
        """
        total_penalty = 0.0
        
        # Her instructor için görev sayısını hesapla
        workload = self._calculate_instructor_workloads(solution)
        
        for instructor_id in self.faculty_instructors.keys():
            load = workload.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            
            # ±2 tolerans bandı
            soft_penalty = max(0, deviation - self.config.workload_soft_band)
            total_penalty += soft_penalty
            
            # Sert kısıt kontrolü
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.workload_hard_limit:
                    total_penalty += 1000  # Çok büyük ceza (infeasible)
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, solution: Solution) -> float:
        """
        H3: Sınıf değişimi cezası.
        
        Her öğretim görevlisi için:
        count = görev yaptığı farklı sınıf sayısı
        penalty = max(0, count - 2)
        """
        total_penalty = 0.0
        
        # Her instructor için sınıf sayısını hesapla
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
        H4: Sınıf yükü dengesizliği cezası.
        
        KRİTİK: Tüm sınıflar kullanılmalı! Boş sınıf varsa çok yüksek ceza.
        Her sınıfın proje sayısı hedef değere yakın olmalı.
        Target = num_projects / class_count
        
        Eğer bir sınıf çok dolu (4+ instructor) ve başka sınıf boşsa çok yüksek ceza.
        """
        total_penalty = 0.0
        
        num_projects = len(solution.assignments)
        target_per_class = num_projects / solution.class_count
        
        # Her sınıfın proje sayısı
        class_project_counts = defaultdict(int)
        for assignment in solution.assignments:
            class_project_counts[assignment.class_id] += 1
        
        # Her sınıfın instructor sayısı (farklı PS sayısı)
        class_instructor_counts = defaultdict(set)
        for assignment in solution.assignments:
            class_instructor_counts[assignment.class_id].add(assignment.ps_id)
        
        # BOŞ SINIFLAR İÇİN ÇOK YÜKSEK CEZA (ZORUNLU KULLANIM)
        empty_classes = [
            c for c in range(solution.class_count)
            if class_project_counts.get(c, 0) == 0
        ]
        
        # Her boş sınıf için çok yüksek ceza
        total_penalty += len(empty_classes) * 1000  # Her boş sınıf için 1000 ceza
        
        # Sınıf yükü dengesizliği
        for class_id in range(solution.class_count):
            project_count = class_project_counts.get(class_id, 0)
            instructor_count = len(class_instructor_counts.get(class_id, set()))
            
            # Proje sayısı sapması
            project_deviation = abs(project_count - target_per_class)
            total_penalty += project_deviation
            
            # Eğer bir sınıfta 4+ farklı instructor varsa ve başka sınıf boşsa ekstra ceza
            if instructor_count >= 4:
                # Boş sınıf var mı?
                if empty_classes:
                    # Bu sınıftan bir çifti boş sınıfa taşıyabiliriz - çok yüksek ceza
                    total_penalty += (instructor_count - 2) * 50  # Her fazla instructor için 50 ceza
                else:
                    # Boş sınıf yok ama çok az dolu sınıf var mı?
                    underloaded_classes = [
                        c for c in range(solution.class_count)
                        if c != class_id and class_project_counts.get(c, 0) < target_per_class * 0.5
                    ]
                    if underloaded_classes:
                        # Bu sınıftan bir çifti taşıyabiliriz - ekstra ceza
                        total_penalty += (instructor_count - 2) * 10  # Her fazla instructor için 10 ceza
        
        return total_penalty
    
    def _build_instructor_task_matrix(
        self,
        solution: Solution
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Her instructor için görev matrisi oluştur."""
        instructor_tasks = defaultdict(list)
        
        for assignment in solution.assignments:
            # PS görevi
            instructor_tasks[assignment.ps_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'slot': assignment.slot_in_class,
                'role': 'PS'
            })
            
            # J1 görevi
            instructor_tasks[assignment.j1_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'slot': assignment.slot_in_class,
                'role': 'J1'
            })
        
        return instructor_tasks
    
    def _calculate_instructor_workloads(
        self,
        solution: Solution
    ) -> Dict[int, int]:
        """Her instructor için toplam iş yükünü hesapla."""
        workload = defaultdict(int)
        
        for assignment in solution.assignments:
            workload[assignment.ps_id] += 1
            workload[assignment.j1_id] += 1
        
        return workload
    
    def get_workload_summary(self, solution: Solution) -> Dict[int, Dict[str, Any]]:
        """Her instructor için iş yükü özeti."""
        workloads = self._calculate_instructor_workloads(solution)
        instructor_classes = defaultdict(set)
        
        for assignment in solution.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        summary = {}
        for instructor_id in self.faculty_instructors.keys():
            instructor = self.faculty_instructors[instructor_id]
            load = workloads.get(instructor_id, 0)
            classes = instructor_classes.get(instructor_id, set())
            
            summary[instructor_id] = {
                "name": instructor.name,
                "workload": load,
                "deviation": abs(load - self.avg_workload),
                "class_count": len(classes),
                "classes": list(classes)
            }
        
        return summary


# ============================================================================
# NEIGHBORHOOD GENERATOR
# ============================================================================

class NeighborhoodGenerator:
    """
    Komşu çözüm üretici.
    
    Move types:
    1. j1_swap: Aynı sınıfta J1 değiştir
    2. j1_reassign: J1 yeniden ata
    3. project_move: Projeyi başka sınıfa taşı
    4. project_swap: İki projenin sınıfını değiştir
    5. order_swap: Sınıf içi sıra değiştir
    """
    
    def __init__(
        self,
        projects: List[ProjectData],
        instructors: List[InstructorData],
        config: ComprehensiveConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Sadece instructor tipindekiler
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
        Komşu çözümler üret.
        
        Returns:
            List of (neighbor_solution, move_type, project_id, attribute)
        """
        if count is None:
            count = self.config.neighborhood_size
        
        neighbors = []
        move_types = [
            'j1_swap',
            'j1_reassign',
            'project_move',
            'project_swap',
            'order_swap',
            'pair_move'  # Yeni: Bir çifti bir sınıftan diğerine taşı
        ]
        
        # Ağırlıklı seçim (j1_reassign, order_swap ve pair_move daha sık)
        weights = [1, 3, 1, 1, 2, 2]
        
        for _ in range(count):
            move_type = random.choices(move_types, weights=weights)[0]
            result = None
            
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
            elif move_type == 'pair_move':
                result = self._generate_pair_move(solution)
            
            if result is not None:
                neighbors.append(result)
        
        return neighbors
    
    def _generate_j1_swap(
        self,
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """J1 Swap: Aynı sınıftaki iki projenin J1'lerini değiştir."""
        class_id = random.randint(0, solution.class_count - 1)
        class_projects = solution.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return None
        
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        # Kendi projesine jüri olma kontrolü
        if p1.j1_id == p2.ps_id or p2.j1_id == p1.ps_id:
            return None
        
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
        """J1 Reassignment: Bir projenin J1'ini değiştir."""
        if not solution.assignments:
            return None
        
        assignment = random.choice(solution.assignments)
        project = self.projects.get(assignment.project_id)
        
        if not project:
            return None
        
        # PS hariç instructor'lardan seç
        available_j1 = [
            i_id for i_id in self.faculty_ids
            if i_id != project.responsible_id and i_id != assignment.j1_id
        ]
        
        if not available_j1:
            return None
        
        new_j1 = random.choice(available_j1)
        
        new_solution = solution.copy()
        
        for a in new_solution.assignments:
            if a.project_id == assignment.project_id:
                a.j1_id = new_j1
                break
        
        return (new_solution, 'j1_reassign', assignment.project_id, new_j1)
    
    def _generate_project_move(
        self,
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """Project Move: Bir projeyi başka sınıfa taşı."""
        if not solution.assignments:
            return None
        
        assignment = random.choice(solution.assignments)
        
        available_classes = [
            c for c in range(solution.class_count)
            if c != assignment.class_id
        ]
        
        if not available_classes:
            return None
        
        new_class = random.choice(available_classes)
        
        new_solution = solution.copy()
        old_class = assignment.class_id
        
        for a in new_solution.assignments:
            if a.project_id == assignment.project_id:
                a.class_id = new_class
                # Yeni sınıfın sonuna ekle
                new_class_projects = [
                    x for x in new_solution.assignments
                    if x.class_id == new_class and x.project_id != a.project_id
                ]
                a.slot_in_class = len(new_class_projects)
                break
        
        # Eski sınıftaki sıraları güncelle
        self._reorder_class(new_solution, old_class)
        
        return (new_solution, 'project_move', assignment.project_id, new_class)
    
    def _generate_project_swap(
        self,
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """Project Swap: Farklı sınıflardaki iki projenin sınıflarını değiştir."""
        if len(solution.assignments) < 2:
            return None
        
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
        
        new_solution = solution.copy()
        
        for a in new_solution.assignments:
            if a.project_id == p1.project_id:
                a.class_id = p2.class_id
                a.slot_in_class = p2.slot_in_class
            elif a.project_id == p2.project_id:
                a.class_id = p1.class_id
                a.slot_in_class = p1.slot_in_class
        
        return (new_solution, 'project_swap', p1.project_id, (p2.project_id, p2.class_id))
    
    def _generate_order_swap(
        self,
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """Order Swap: Aynı sınıftaki iki projenin sırasını değiştir."""
        class_id = random.randint(0, solution.class_count - 1)
        class_projects = solution.get_class_projects(class_id)
        
        if len(class_projects) < 2:
            return None
        
        idx1, idx2 = random.sample(range(len(class_projects)), 2)
        p1 = class_projects[idx1]
        p2 = class_projects[idx2]
        
        new_solution = solution.copy()
        
        for a in new_solution.assignments:
            if a.project_id == p1.project_id:
                a.slot_in_class = p2.slot_in_class
            elif a.project_id == p2.project_id:
                a.slot_in_class = p1.slot_in_class
        
        return (new_solution, 'order_swap', p1.project_id, p2.project_id)
    
    def _generate_pair_move(
        self,
        solution: Solution
    ) -> Optional[Tuple[Solution, str, int, Any]]:
        """
        Pair Move: Bir çiftin tüm projelerini bir sınıftan diğerine taşı.
        
        Bu hareket, sınıf yükü dengesizliğini düzeltmek için kullanılır.
        Öncelik: BOŞ SINIFLARI DOLDUR!
        Sonra: 4+ instructor olan sınıflardan az dolu sınıflara taşı.
        """
        if not solution.pairs:
            return None
        
        # Çok dolu sınıfları bul (4+ farklı instructor)
        class_instructor_counts = defaultdict(set)
        class_project_counts = defaultdict(int)
        
        for assignment in solution.assignments:
            class_instructor_counts[assignment.class_id].add(assignment.ps_id)
            class_project_counts[assignment.class_id] += 1
        
        # ÖNCELİK 1: BOŞ SINIFLARI BUL
        empty_classes = [
            c for c in range(solution.class_count)
            if class_project_counts.get(c, 0) == 0
        ]
        
        # ÖNCELİK 2: Çok dolu sınıflar (4+ instructor)
        overloaded_classes = [
            c for c in range(solution.class_count)
            if len(class_instructor_counts.get(c, set())) >= 4
        ]
        
        # Eğer boş sınıf varsa, mutlaka bir çifti oraya taşı
        if empty_classes:
            target_class = random.choice(empty_classes)
            
            # Kaynak sınıf: 4+ instructor olan veya en dolu olan
            if overloaded_classes:
                source_class = random.choice(overloaded_classes)
            else:
                # En dolu sınıfı seç
                source_class = max(
                    range(solution.class_count),
                    key=lambda c: class_project_counts.get(c, 0)
                )
            
            # Bu sınıftaki çiftleri bul
            source_pairs = [
                p for p in solution.pairs
                if p.assigned_class == source_class
            ]
            
            if not source_pairs:
                return None
            
            # Rastgele bir çift seç
            pair_to_move = random.choice(source_pairs)
        
        # Boş sınıf yoksa, 4+ instructor olan sınıflardan az dolu sınıflara taşı
        elif overloaded_classes:
            # Rastgele bir çok dolu sınıf seç
            source_class = random.choice(overloaded_classes)
            
            # Bu sınıftaki çiftleri bul
            source_pairs = [
                p for p in solution.pairs
                if p.assigned_class == source_class
            ]
            
            if not source_pairs:
                return None
            
            # Rastgele bir çift seç
            pair_to_move = random.choice(source_pairs)
            
            # Az dolu sınıfları bul
            target_classes = [
                c for c in range(solution.class_count)
                if c != source_class and class_project_counts.get(c, 0) < class_project_counts[source_class]
            ]
            
            if not target_classes:
                return None
            
            # En az dolu sınıfı seç
            target_class = min(target_classes, key=lambda c: class_project_counts.get(c, 0))
        
        else:
            # Boş sınıf yok ve 4+ instructor olan sınıf yok
            return None
        
        # Yeni çözüm oluştur
        new_solution = solution.copy()
        
        # Çiftin projelerini bul ve taşı
        pair_instructor_ids = {pair_to_move.instructor1_id, pair_to_move.instructor2_id}
        moved_count = 0
        
        for a in new_solution.assignments:
            if a.class_id == source_class and a.ps_id in pair_instructor_ids:
                a.class_id = target_class
                # Yeni sınıfın sonuna ekle
                target_projects = [
                    x for x in new_solution.assignments
                    if x.class_id == target_class and x.project_id != a.project_id
                ]
                a.slot_in_class = len(target_projects)
                moved_count += 1
        
        # Çiftin assigned_class'ını güncelle
        for p in new_solution.pairs:
            if (p.instructor1_id == pair_to_move.instructor1_id and
                p.instructor2_id == pair_to_move.instructor2_id):
                p.assigned_class = target_class
                break
        
        # Eski sınıftaki sıraları güncelle
        self._reorder_class(new_solution, source_class)
        
        if moved_count == 0:
            return None
        
        return (new_solution, 'pair_move', pair_to_move.instructor1_id, target_class)
    
    def _reorder_class(self, solution: Solution, class_id: int) -> None:
        """Sınıf içindeki sıraları yeniden düzelt."""
        class_projects = [a for a in solution.assignments if a.class_id == class_id]
        class_projects.sort(key=lambda x: x.slot_in_class)
        
        for i, a in enumerate(class_projects):
            for assignment in solution.assignments:
                if assignment.project_id == a.project_id:
                    assignment.slot_in_class = i
                    break


# ============================================================================
# INITIAL SOLUTION BUILDER
# ============================================================================

class InitialSolutionBuilder:
    """
    Başlangıç çözümü oluşturucu.
    
    Algoritma:
    1. Load-based instructor sorting
    2. Balanced pair construction
    3. Assign pairs to classes
    4. Inside each class: consecutive advisor placement + paired J1 assignment
    5. Priority mode enforcement
    """
    
    def __init__(
        self,
        projects: List[ProjectData],
        instructors: List[InstructorData],
        config: ComprehensiveConfig
    ):
        self.projects = projects
        self.instructors = instructors
        self.config = config
        
        self.projects_dict = {p.id: p for p in projects}
        self.instructors_dict = {i.id: i for i in instructors}
        
        # Pairing engine
        self.pairing_engine = InstructorPairingEngine(
            instructors, projects, config
        )
        
        # Faculty only
        self.faculty_instructors = {
            i.id: i for i in instructors
            if i.type == "instructor"
        }
    
    def build(self, class_count: int) -> Solution:
        """
        Başlangıç çözümü oluştur.
        
        Args:
            class_count: Sınıf sayısı
        
        Returns:
            Solution: Başlangıç çözümü
        """
        solution = Solution(class_count=class_count)
        
        # 1. Dengeli çiftler oluştur
        pairs = self.pairing_engine.build_balanced_pairs()
        solution.pairs = pairs
        
        # 2. Çiftleri sınıflara ata
        class_pairs = self.pairing_engine.assign_pairs_to_classes(
            pairs, class_count
        )
        
        # 3. Her sınıf için projeleri ata
        self._assign_projects_to_classes(solution, class_pairs)
        
        # 4. Tüm sınıfların kullanıldığından emin ol (boş sınıf varsa düzelt)
        self._ensure_all_classes_used(solution)
        
        # 5. Priority mode'u uygula
        self._enforce_priority_mode(solution)
        
        logger.info(f"Başlangıç çözümü oluşturuldu: {len(solution.assignments)} atama")
        
        return solution
    
    def _assign_projects_to_classes(
        self,
        solution: Solution,
        class_pairs: Dict[int, List[InstructorPair]]
    ) -> None:
        """
        Projeleri sınıflara ata.
        
        Pair scheduling rule:
        If pair = (A, B):
            Put all A's advisor-projects consecutively, J1 = B
            Then put all B's advisor-projects consecutively, J1 = A
        """
        # Her instructor'ın projeleri
        instructor_projects: Dict[int, List[ProjectData]] = defaultdict(list)
        for project in self.projects:
            instructor_projects[project.responsible_id].append(project)
        
        # Her sınıf için
        for class_id, pairs in class_pairs.items():
            slot_counter = 0
            
            for pair in pairs:
                inst1_id = pair.instructor1_id
                inst2_id = pair.instructor2_id
                
                # Instructor 1'in projeleri (J1 = Instructor 2)
                for project in instructor_projects.get(inst1_id, []):
                    assignment = ProjectAssignment(
                        project_id=project.id,
                        class_id=class_id,
                        slot_in_class=slot_counter,
                        ps_id=project.responsible_id,
                        j1_id=inst2_id,
                        j2_id=-1  # Placeholder
                    )
                    solution.assignments.append(assignment)
                    slot_counter += 1
                
                # Instructor 2'nin projeleri (J1 = Instructor 1)
                for project in instructor_projects.get(inst2_id, []):
                    assignment = ProjectAssignment(
                        project_id=project.id,
                        class_id=class_id,
                        slot_in_class=slot_counter,
                        ps_id=project.responsible_id,
                        j1_id=inst1_id,
                        j2_id=-1  # Placeholder
                    )
                    solution.assignments.append(assignment)
                    slot_counter += 1
        
        # Çiftlere atanmamış projeler varsa
        assigned_project_ids = {a.project_id for a in solution.assignments}
        unassigned = [p for p in self.projects if p.id not in assigned_project_ids]
        
        if unassigned:
            logger.warning(f"{len(unassigned)} proje çiftlere atanamadı, round-robin ile atanıyor")
            self._assign_unassigned_projects(solution, unassigned)
    
    def _assign_unassigned_projects(
        self,
        solution: Solution,
        unassigned: List[ProjectData]
    ) -> None:
        """Atanmamış projeleri round-robin ile ata."""
        # Sınıf yüklerini hesapla
        class_loads = defaultdict(int)
        for a in solution.assignments:
            class_loads[a.class_id] += 1
        
        for project in unassigned:
            # En düşük yüklü sınıfı bul
            min_class = min(
                range(solution.class_count),
                key=lambda c: class_loads[c]
            )
            
            # Slot numarası
            class_projects = solution.get_class_projects(min_class)
            slot = len(class_projects)
            
            # J1 seç (PS hariç, en düşük yüklü instructor)
            j1_id = self._select_j1_for_project(project, solution)
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=min_class,
                slot_in_class=slot,
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            solution.assignments.append(assignment)
            class_loads[min_class] += 1
    
    def _select_j1_for_project(
        self,
        project: ProjectData,
        solution: Solution
    ) -> int:
        """Proje için J1 seç."""
        # Mevcut iş yüklerini hesapla
        workloads = defaultdict(int)
        for a in solution.assignments:
            workloads[a.ps_id] += 1
            workloads[a.j1_id] += 1
        
        # PS dahil değil
        workloads[project.responsible_id] += 1
        
        # Faculty'lerden en düşük yüklü olanı seç
        faculty_ids = [
            i_id for i_id in self.faculty_instructors.keys()
            if i_id != project.responsible_id
        ]
        
        if faculty_ids:
            faculty_ids.sort(key=lambda x: workloads.get(x, 0))
            return faculty_ids[0]
        
        # Fallback
        all_ids = [i.id for i in self.instructors if i.id != project.responsible_id]
        return random.choice(all_ids) if all_ids else project.responsible_id
    
    def _ensure_all_classes_used(self, solution: Solution) -> None:
        """
        Tüm sınıfların kullanıldığından emin ol.
        
        Eğer boş sınıf varsa, 4+ instructor olan sınıflardan bir çifti boş sınıfa taşı.
        """
        # Kullanılan sınıfları bul
        used_classes = {a.class_id for a in solution.assignments}
        empty_classes = [
            c for c in range(solution.class_count)
            if c not in used_classes
        ]
        
        if not empty_classes:
            # Tüm sınıflar kullanılıyor
            return
        
        logger.warning(f"Boş sınıflar tespit edildi: {empty_classes}, düzeltiliyor...")
        
        # Her sınıfın instructor sayısını hesapla
        class_instructor_counts = defaultdict(set)
        for assignment in solution.assignments:
            class_instructor_counts[assignment.class_id].add(assignment.ps_id)
        
        # 4+ instructor olan sınıfları bul
        overloaded_classes = [
            c for c in used_classes
            if len(class_instructor_counts.get(c, set())) >= 4
        ]
        
        # Her boş sınıf için bir çift taşı
        for empty_class in empty_classes:
            if not overloaded_classes:
                # 4+ instructor olan sınıf yok, en dolu sınıftan taşı
                class_project_counts = defaultdict(int)
                for assignment in solution.assignments:
                    class_project_counts[assignment.class_id] += 1
                
                if class_project_counts:
                    source_class = max(class_project_counts.keys(), key=lambda c: class_project_counts[c])
                else:
                    continue
            else:
                # 4+ instructor olan sınıftan taşı
                source_class = random.choice(overloaded_classes)
            
            # Bu sınıftaki çiftleri bul
            source_pairs = [
                p for p in solution.pairs
                if p.assigned_class == source_class
            ]
            
            if not source_pairs:
                continue
            
            # Rastgele bir çift seç
            pair_to_move = random.choice(source_pairs)
            pair_instructor_ids = {pair_to_move.instructor1_id, pair_to_move.instructor2_id}
            
            # Çiftin projelerini boş sınıfa taşı
            moved_count = 0
            for a in solution.assignments:
                if a.class_id == source_class and a.ps_id in pair_instructor_ids:
                    a.class_id = empty_class
                    # Yeni sınıfın sonuna ekle
                    target_projects = [
                        x for x in solution.assignments
                        if x.class_id == empty_class and x.project_id != a.project_id
                    ]
                    a.slot_in_class = len(target_projects)
                    moved_count += 1
            
            # Çiftin assigned_class'ını güncelle
            for p in solution.pairs:
                if (p.instructor1_id == pair_to_move.instructor1_id and
                    p.instructor2_id == pair_to_move.instructor2_id):
                    p.assigned_class = empty_class
                    break
            
            # Eski sınıftaki sıraları güncelle
            self._reorder_class_slots(solution, source_class)
            
            logger.info(f"Çift Sınıf {source_class} -> Sınıf {empty_class} taşındı ({moved_count} proje)")
            
            # Güncellenmiş durumu kontrol et
            class_instructor_counts[empty_class] = pair_instructor_ids
            if source_class in overloaded_classes:
                class_instructor_counts[source_class] = {
                    a.ps_id for a in solution.assignments
                    if a.class_id == source_class
                }
                # Eğer artık 4'ten az instructor varsa listeden çıkar
                if len(class_instructor_counts[source_class]) < 4:
                    overloaded_classes.remove(source_class)
    
    def _reorder_class_slots(self, solution: Solution, class_id: int) -> None:
        """Sınıf içindeki slot sıralarını yeniden düzelt."""
        class_projects = [a for a in solution.assignments if a.class_id == class_id]
        class_projects.sort(key=lambda x: x.slot_in_class)
        
        for i, a in enumerate(class_projects):
            for assignment in solution.assignments:
                if assignment.project_id == a.project_id:
                    assignment.slot_in_class = i
                    break
    
    def _enforce_priority_mode(self, solution: Solution) -> None:
        """Priority mode'u uygula."""
        if self.config.priority_mode == PriorityMode.ESIT:
            return  # Öncelik yok
        
        # Her sınıf için
        for class_id in range(solution.class_count):
            class_projects = solution.get_class_projects(class_id)
            
            if self.config.priority_mode == PriorityMode.ARA_ONCE:
                # Ara projeler önce
                ara = [a for a in class_projects
                       if self.projects_dict[a.project_id].type in ('interim', 'ara')]
                bitirme = [a for a in class_projects
                          if self.projects_dict[a.project_id].type in ('final', 'bitirme')]
                sorted_projects = ara + bitirme
                
            elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
                # Bitirme projeleri önce
                bitirme = [a for a in class_projects
                          if self.projects_dict[a.project_id].type in ('final', 'bitirme')]
                ara = [a for a in class_projects
                       if self.projects_dict[a.project_id].type in ('interim', 'ara')]
                sorted_projects = bitirme + ara
            else:
                continue
            
            # Slot numaralarını güncelle
            for new_slot, assignment in enumerate(sorted_projects):
                for a in solution.assignments:
                    if a.project_id == assignment.project_id:
                        a.slot_in_class = new_slot
                        break


# ============================================================================
# MAIN COMPREHENSIVE OPTIMIZER
# ============================================================================

class ComprehensiveOptimizer(OptimizationAlgorithm):
    """
    Kapsamlı Optimizasyon (Comprehensive Optimizer).
    
    Tek fazlı çalışma prensibi:
    - Tüm projeler, hocalar, sınıf sayısı tek seferde modele verilir
    - Local Search (Tabu Search) iteratif olarak çalışır
    - En iyi çözüm tek seferde planner'a aktarılır
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Comprehensive Optimizer başlatıcı.
        
        Args:
            params: Algoritma parametreleri
        """
        super().__init__(params)
        params = params or {}
        
        # Konfigürasyon oluştur
        self.config = ComprehensiveConfig(
            max_iterations=params.get("max_iterations", 1000),
            time_limit=params.get("time_limit", 180),
            no_improve_limit=params.get("no_improve_limit", 100),
            tabu_tenure=params.get("tabu_tenure", 20),
            neighborhood_size=params.get("neighborhood_size", 80),
            class_count=params.get("class_count", 6),
            auto_class_count=params.get("auto_class_count", True),
            priority_mode=PriorityMode(params.get("priority_mode", "ESIT")),
            time_penalty_mode=TimePenaltyMode(
                params.get("time_penalty_mode", "GAP_PROPORTIONAL")
            ),
            workload_constraint_mode=WorkloadConstraintMode(
                params.get("workload_constraint_mode", "SOFT_ONLY")
            ),
            workload_hard_limit=params.get("workload_hard_limit", 4),
            workload_soft_band=params.get("workload_soft_band", 2),
            weight_h1=params.get("weight_h1", 1.0),
            weight_h2=params.get("weight_h2", 3.0),
            weight_h3=params.get("weight_h3", 1.0),
            weight_h4=params.get("weight_h4", 2.0),
            pairing_tolerance=params.get("pairing_tolerance", 3)
        )
        
        # Veri yapıları
        self.projects: List[ProjectData] = []
        self.instructors: List[InstructorData] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        
        # Tabu listesi
        self.tabu_list: List[TabuEntry] = []
        
        # En iyi çözüm
        self.best_solution: Optional[Solution] = None
        self.best_cost: float = float('inf')
        self.best_score_breakdown: Optional[ScoreBreakdown] = None
        
        # Yardımcı sınıflar
        self.penalty_calculator: Optional[PenaltyCalculator] = None
        self.neighborhood_generator: Optional[NeighborhoodGenerator] = None
        self.solution_builder: Optional[InitialSolutionBuilder] = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Algoritmayı başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri
        """
        self._load_data(data)
        
        # CRITICAL: Ensure class_count matches actual classrooms after _load_data
        # _load_data may have updated self.config.class_count based on available classrooms
        if self.classrooms:
            actual_class_count = len(self.classrooms)
            if self.config.class_count != actual_class_count:
                logger.info(f"Comprehensive Optimizer: class_count {self.config.class_count} -> {actual_class_count} (mevcut sınıf sayısı)")
                self.config.class_count = actual_class_count
        
        # Yardımcı sınıfları oluştur
        self.penalty_calculator = PenaltyCalculator(
            self.projects, self.instructors, self.config
        )
        self.neighborhood_generator = NeighborhoodGenerator(
            self.projects, self.instructors, self.config
        )
        self.solution_builder = InitialSolutionBuilder(
            self.projects, self.instructors, self.config
        )
        
        # CRITICAL: Log final class_count to verify
        logger.info(f"Comprehensive Optimizer initialize: Final class_count = {self.config.class_count}, classrooms = {len(self.classrooms)}")
        
        # Tabu listesini temizle
        self.tabu_list = []
        
        # En iyi çözümü sıfırla
        self.best_solution = None
        self.best_cost = float('inf')
        self.best_score_breakdown = None
    
    def _load_data(self, data: Dict[str, Any]) -> None:
        """Verileri yükle ve dönüştür."""
        # Projeleri yükle
        raw_projects = data.get("projects", [])
        self.projects = []
        
        for p in raw_projects:
            project = ProjectData(
                id=p.get("id"),
                title=p.get("title", ""),
                type=str(p.get("type", "interim")).lower(),
                responsible_id=p.get("responsible_id") or p.get("responsible_instructor_id"),
                is_makeup=p.get("is_makeup", False)
            )
            self.projects.append(project)
        
        # Öğretim görevlilerini yükle
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        
        for i in raw_instructors:
            instructor = InstructorData(
                id=i.get("id"),
                name=i.get("name", ""),
                type=i.get("type", "instructor")
            )
            self.instructors.append(instructor)
        
        # Sınıfları ve zaman dilimlerini yükle
        all_classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # CRITICAL: Sınıf sayısı kontrolü - Genetic Algorithm ve Simulated Annealing'deki gibi
        # Eğer classrooms varsa ve class_count mevcut sınıf sayısından farklıysa, mevcut sınıf sayısını kullan
        if all_classrooms:
            available_class_count = len(all_classrooms)
            # Eğer config'de class_count mevcut sınıf sayısından farklıysa, mevcut sınıf sayısını kullan
            if self.config.class_count != available_class_count:
                # Eğer auto_class_count aktifse veya default değerse, mevcut sınıf sayısını kullan
                if self.config.auto_class_count or self.config.class_count == 6:  # Default 6
                    self.config.class_count = available_class_count
                    logger.info(f"Comprehensive Optimizer: Sınıf sayısı otomatik olarak {available_class_count} olarak ayarlandı (mevcut sınıf sayısı)")
                else:
                    # Manuel ayarlanmışsa, ama mevcut sınıf sayısından fazlaysa, mevcut sınıf sayısını kullan
                    if self.config.class_count > available_class_count:
                        logger.warning(f"Comprehensive Optimizer: İstenen sınıf sayısı ({self.config.class_count}) mevcut sınıf sayısından ({available_class_count}) fazla. Tüm sınıflar kullanılacak.")
                        self.config.class_count = available_class_count
            else:
                # Zaten doğru, ama yine de log
                logger.info(f"Comprehensive Optimizer: {self.config.class_count} sınıf kullanılacak")
        
        # Sınıfları ayarla (eğer classroom_count belirtilmişse, o kadar sınıf kullan)
        classroom_count = data.get("classroom_count")
        if classroom_count and classroom_count > 0:
            if classroom_count > len(all_classrooms):
                logger.warning(
                    f"İstenen sınıf sayısı ({classroom_count}) mevcut sınıf sayısından "
                    f"({len(all_classrooms)}) fazla. Tüm sınıflar kullanılacak."
                )
                self.classrooms = all_classrooms
                self.config.class_count = len(all_classrooms)
            else:
                self.classrooms = all_classrooms[:classroom_count]
                self.config.class_count = classroom_count
                logger.info(f"Comprehensive Optimizer: {classroom_count} sınıf kullanılıyor")
        else:
            # classroom_count belirtilmemişse, config'deki class_count kadar veya tüm sınıfları kullan
            if self.config.class_count <= len(all_classrooms):
                self.classrooms = all_classrooms[:self.config.class_count]
            else:
                self.classrooms = all_classrooms
                self.config.class_count = len(all_classrooms)
                logger.info(f"Comprehensive Optimizer: Tüm {len(all_classrooms)} sınıf kullanılacak")
        
        logger.info(f"Veri yüklendi: {len(self.projects)} proje, {len(self.instructors)} instructor, {len(self.classrooms)} sınıf")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive Optimization algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu
        """
        if data:
            self.initialize(data)
        
        start_time = time.time()
        
        # Sınıf sayısı mantığı:
        # - Eğer class_count belirtilmişse (5, 6 veya 7), sadece o sayıyla çalış
        # - Eğer auto_class_count True ise ve class_count belirtilmemişse veya geçersizse, 5,6,7 için en iyisini seç
        # Kullanıcı belirli bir sınıf sayısı istiyorsa, sadece o sayıyla çalış
        if self.config.auto_class_count and self.config.class_count not in [5, 6, 7]:
            # Class count belirtilmemiş veya geçersiz, 5, 6, 7 için en iyi sonucu bul
            best_result = None
            best_overall_cost = float('inf')
            
            for class_count in [5, 6, 7]:
                logger.info(f"Sınıf sayısı {class_count} ile çalıştırılıyor...")
                self.config.class_count = class_count
                
                result = self._run_optimization()
                
                if result['cost'] < best_overall_cost:
                    best_overall_cost = result['cost']
                    best_result = result
                    logger.info(f"Yeni en iyi: class_count={class_count}, cost={result['cost']:.2f}")
            
            result = best_result
        else:
            # Belirtilen sınıf sayısıyla çalış (kullanıcı kaç sınıf istiyorsa o sayıyla)
            logger.info(f"Belirtilen sınıf sayısı {self.config.class_count} ile çalıştırılıyor...")
            result = self._run_optimization()
        
        end_time = time.time()
        
        # Çözümü output formatına dönüştür
        schedule = self._convert_solution_to_schedule(result['solution'])
        
        # İş yükü özeti
        workload_summary = self.penalty_calculator.get_workload_summary(result['solution'])
        
        return {
            "schedule": schedule,
            "assignments": schedule,
            "solution": schedule,
            "fitness": -result['cost'],
            "cost": result['cost'],
            "iterations": result['iterations'],
            "execution_time": end_time - start_time,
            "class_count": result['solution'].class_count,
            "penalty_breakdown": result['score_breakdown'].to_dict(),
            "workload_summary": workload_summary,
            "status": "completed",
            "algorithm_name": self.get_name()
        }
    
    def _run_optimization(self) -> Dict[str, Any]:
        """
        Ana optimizasyon döngüsü (Tabu Search).
        
        Returns:
            En iyi çözüm ve istatistikler
        """
        start_time = time.time()
        
        # Başlangıç çözümü oluştur
        current_solution = self.solution_builder.build(self.config.class_count)
        current_score = self.penalty_calculator.calculate_full_penalty(current_solution)
        current_cost = current_score.total_z
        
        # En iyi çözümü başlat
        self.best_solution = current_solution.copy()
        self.best_cost = current_cost
        self.best_score_breakdown = current_score
        
        # İterasyon sayaçları
        iteration = 0
        no_improve_count = 0
        
        logger.info(f"Başlangıç maliyeti: {current_cost:.2f}")
        logger.info(f"  H1 (time gap): {current_score.h1_time_gap:.2f}")
        logger.info(f"  H2 (workload): {current_score.h2_workload:.2f}")
        logger.info(f"  H3 (class change): {current_score.h3_class_change:.2f}")
        logger.info(f"  H4 (class load balance): {current_score.h4_class_load_balance:.2f}")
        
        # Ana döngü
        while (iteration < self.config.max_iterations and
               no_improve_count < self.config.no_improve_limit and
               time.time() - start_time < self.config.time_limit):
            
            # Komşu çözümler oluştur
            neighbors = self.neighborhood_generator.generate_neighbors(
                current_solution,
                self.config.neighborhood_size
            )
            
            # En iyi tabu-olmayan komşuyu bul
            best_neighbor = None
            best_neighbor_cost = float('inf')
            best_move_info = None
            
            for neighbor, move_type, project_id, attribute in neighbors:
                # Hard constraint kontrolü
                if not self._check_hard_constraints(neighbor):
                    continue
                
                neighbor_cost = self.penalty_calculator.calculate_total_penalty(neighbor)
                
                # Tabu kontrolü
                is_tabu = self._is_tabu(move_type, project_id, attribute, iteration)
                
                # Aspiration kriteri
                aspiration = (
                    self.config.aspiration_enabled and
                    neighbor_cost < self.best_cost
                )
                
                if (not is_tabu or aspiration) and neighbor_cost < best_neighbor_cost:
                    best_neighbor = neighbor
                    best_neighbor_cost = neighbor_cost
                    best_move_info = (move_type, project_id, attribute)
            
            # Komşu bulunamadıysa, yeni başlangıç çözümü (diversification)
            if best_neighbor is None:
                if no_improve_count > self.config.no_improve_limit // 2:
                    # Diversification: yeni rastgele başlangıç
                    current_solution = self._create_random_solution()
                    current_cost = self.penalty_calculator.calculate_total_penalty(current_solution)
                    logger.info(f"Diversification: Yeni rastgele çözüm, maliyet = {current_cost:.2f}")
                
                no_improve_count += 1
                iteration += 1
                continue
            
            # Mevcut çözümü güncelle
            current_solution = best_neighbor
            current_cost = best_neighbor_cost
            
            # Tabu listesine ekle
            if best_move_info:
                self._add_tabu(
                    best_move_info[0],
                    best_move_info[1],
                    best_move_info[2],
                    iteration
                )
            
            # En iyi çözümü güncelle
            if current_cost < self.best_cost:
                self.best_solution = current_solution.copy()
                self.best_cost = current_cost
                self.best_score_breakdown = self.penalty_calculator.calculate_full_penalty(
                    self.best_solution
                )
                no_improve_count = 0
                
                if iteration % 50 == 0 or current_cost < self.best_cost - 1:
                    logger.info(
                        f"İterasyon {iteration}: Yeni en iyi maliyet = {self.best_cost:.2f}"
                    )
            else:
                no_improve_count += 1
            
            # Eski tabu girdilerini temizle
            self._cleanup_tabu(iteration)
            
            iteration += 1
        
        # Final log
        logger.info(f"Comprehensive Optimization tamamlandı: {iteration} iterasyon")
        logger.info(f"En iyi maliyet: {self.best_cost:.2f}")
        logger.info(f"  H1: {self.best_score_breakdown.h1_time_gap:.2f} (weighted: {self.best_score_breakdown.c1_h1:.2f})")
        logger.info(f"  H2: {self.best_score_breakdown.h2_workload:.2f} (weighted: {self.best_score_breakdown.c2_h2:.2f})")
        logger.info(f"  H3: {self.best_score_breakdown.h3_class_change:.2f} (weighted: {self.best_score_breakdown.c3_h3:.2f})")
        logger.info(f"  H4: {self.best_score_breakdown.h4_class_load_balance:.2f} (weighted: {self.best_score_breakdown.c4_h4:.2f})")
        
        return {
            'solution': self.best_solution,
            'cost': self.best_cost,
            'iterations': iteration,
            'score_breakdown': self.best_score_breakdown
        }
    
    def _check_hard_constraints(self, solution: Solution) -> bool:
        """
        Hard constraint'leri kontrol et.
        
        Hard Constraints:
        1. Her proje tam 1 sınıf ve 1 slot'a atanmalı
        2. Instructor kendi projesine J1 olamaz
        3. Instructor aynı timeslot'ta birden fazla görev alamaz
        4. TÜM SINIFLAR KULLANILMALI (boş sınıf olmamalı)
        """
        # Proje tekrarı kontrolü
        project_ids = [a.project_id for a in solution.assignments]
        if len(project_ids) != len(set(project_ids)):
            return False
        
        # J1 = PS kontrolü
        for a in solution.assignments:
            if a.j1_id == a.ps_id:
                return False
        
        # Aynı slot'ta çakışma kontrolü
        slot_instructor_usage = defaultdict(set)
        for a in solution.assignments:
            slot_key = (a.class_id, a.slot_in_class)
            
            # PS ve J1 için kontrol
            for inst_id in [a.ps_id, a.j1_id]:
                if inst_id in slot_instructor_usage[slot_key]:
                    return False
                slot_instructor_usage[slot_key].add(inst_id)
        
        # TÜM SINIFLAR KULLANILMALI - Hard Constraint
        used_classes = {a.class_id for a in solution.assignments}
        if len(used_classes) < solution.class_count:
            # Boş sınıf var - hard constraint ihlali
            return False
        
        return True
    
    def _create_random_solution(self) -> Solution:
        """Rastgele yeni başlangıç çözümü oluştur."""
        return self.solution_builder.build(self.config.class_count)
    
    def _is_tabu(
        self,
        move_type: str,
        project_id: int,
        attribute: Any,
        current_iteration: int
    ) -> bool:
        """Hareketin tabu olup olmadığını kontrol et."""
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
        """Hareketi tabu listesine ekle."""
        entry = TabuEntry(
            move_type=move_type,
            project_id=project_id,
            attribute=attribute,
            expiry=current_iteration + self.config.tabu_tenure
        )
        self.tabu_list.append(entry)
    
    def _cleanup_tabu(self, current_iteration: int) -> None:
        """Süresi dolan tabu girdilerini temizle."""
        self.tabu_list = [
            entry for entry in self.tabu_list
            if entry.expiry > current_iteration
        ]
    
    def _convert_solution_to_schedule(
        self,
        solution: Solution
    ) -> List[Dict[str, Any]]:
        """
        Solution'ı schedule formatına dönüştür.
        
        Her atama için:
        - project_id
        - classroom_id
        - timeslot_id
        - instructors [PS, J1, J2]
        - class_id, slot
        """
        schedule = []
        
        if not solution or not solution.assignments:
            return schedule
        
        # Sınıf ve timeslot eşleştirmesi
        classroom_mapping = self._create_classroom_mapping(solution.class_count)
        timeslot_mapping = self._create_timeslot_mapping()
        
        for assignment in solution.assignments:
            # Sınıf ID'sini gerçek classroom ID'sine dönüştür
            classroom_id = classroom_mapping.get(
                assignment.class_id,
                self.classrooms[0].get("id") if self.classrooms else 1
            )
            
            # Timeslot ID'sini hesapla
            timeslot_idx = assignment.slot_in_class
            timeslot_id = timeslot_mapping.get(
                timeslot_idx,
                self.timeslots[0].get("id") if self.timeslots else 1
            )
            
            # Instructors listesi: [PS, J1, J2 placeholder]
            instructors = [assignment.ps_id, assignment.j1_id]
            
            # J2 placeholder ekle - her zaman "[Araştırma Görevlisi]" olarak
            if assignment.j2_id > 0:
                instructors.append(assignment.j2_id)
            else:
                # Placeholder olarak "[Araştırma Görevlisi]" dict formatında
                instructors.append({
                    "id": -1,
                    "name": "[Araştırma Görevlisi]",
                    "is_placeholder": True
                })
            
            # Proje bilgilerini al
            project_data = next(
                (p for p in self.projects if p.id == assignment.project_id),
                None
            )
            
            schedule_entry = {
                "project_id": assignment.project_id,
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": instructors,
                "class_order": assignment.slot_in_class,
                "class_id": assignment.class_id,
                "is_makeup": project_data.is_makeup if project_data else False
            }
            schedule.append(schedule_entry)
        
        return schedule
    
    def _create_classroom_mapping(self, class_count: int) -> Dict[int, int]:
        """Mantıksal sınıf ID'lerini gerçek classroom ID'lerine eşle."""
        mapping = {}
        for i in range(class_count):
            if i < len(self.classrooms):
                mapping[i] = self.classrooms[i].get("id", i + 1)
            else:
                mapping[i] = i + 1
        return mapping
    
    def _create_timeslot_mapping(self) -> Dict[int, int]:
        """Sıralama indeksini timeslot ID'lerine eşle."""
        mapping = {}
        for i, ts in enumerate(self.timeslots):
            mapping[i] = ts.get("id", i + 1)
        return mapping
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Çözümün fitness değerini hesapla.
        
        Args:
            solution: Değerlendirilecek çözüm
            
        Returns:
            Fitness değeri (yüksek = iyi)
        """
        if not solution:
            return float('-inf')
        
        assignments = solution.get("solution", solution.get("schedule", solution))
        
        if isinstance(assignments, Solution):
            cost = self.penalty_calculator.calculate_total_penalty(assignments)
            return -cost
        
        # Dict listesi ise Solution'a dönüştür
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
        """Schedule formatından Solution'a dönüştür."""
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
                slot_in_class=entry.get("class_order", 0),
                ps_id=instructors[0],
                j1_id=instructors[1],
                j2_id=instructors[2] if len(instructors) > 2 else -1
            )
            solution.assignments.append(assignment)
        
        return solution
    
    def get_name(self) -> str:
        """Algoritma adını döndür."""
        return "ComprehensiveOptimizer"
    
    def repair_solution(
        self,
        solution: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Çözümü onar.
        
        Args:
            solution: Onarılacak çözüm
            validation_result: Validation sonuçları
            
        Returns:
            Onarılmış çözüm
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
        
        # Classroom/timeslot çakışma kontrolü
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

def create_comprehensive_optimizer(
    params: Dict[str, Any] = None
) -> ComprehensiveOptimizer:
    """
    Comprehensive Optimizer oluştur.
    
    Args:
        params: Algoritma parametreleri
        
    Returns:
        ComprehensiveOptimizer instance
    """
    return ComprehensiveOptimizer(params)

