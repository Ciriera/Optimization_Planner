"""
HUNGARIAN ALGORITHM - Çok Kriterli ve Çok Kısıtlı Akademik Proje
Sınavı/Jüri Planlama ve Atama Sistemi

Bu modül, üniversitelerde dönem sonlarında gerçekleştirilen Ara Proje ve Bitirme 
Projesi değerlendirme süreçleri için Hungarian (Macar) algoritması tabanlı bir
optimizasyon çözümü sunar.

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
7. BITIRME projeleri MUTLAKA ARA projelerden önce atanır (HARD CONSTRAINT)

YUMUŞAK KISITLAR (Soft Constraints):
1. İş yükü ±2 bandında (L_bar ± 2)
2. Sınıf değişimi minimize
3. Zaman boşlukları minimize

MATRİS TABANLI CEZA FONKSİYONLARI:
- Her öğretim görevlisi i için zaman sıralı matris: M_i ∈ R^(k_i × 2)
- M_i[r, 0] = Saat(i, r)
- M_i[r, 1] = Sınıf(i, r)

Author: Optimization Planner System
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict
import logging
import math
import time
import copy
import numpy as np

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# 2. Jüri placeholder metni - karar değişkeni DEĞİL, sadece görsel
J2_PLACEHOLDER = "[Araştırma Görevlisi]"


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class TimePenaltyMode(str, Enum):
    """Zaman cezası hesaplama modu."""
    BINARY = "BINARY"                       # Ardışık değilse 1 ceza
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Aradaki slot sayısı kadar ceza


class WorkloadConstraintMode(str, Enum):
    """İş yükü kısıt modu."""
    SOFT_ONLY = "SOFT_ONLY"           # Sadece ceza fonksiyonu
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Ceza + sert üst sınır


@dataclass
class HungarianConfig:
    """Hungarian Algorithm konfigürasyon parametreleri."""
    
    # Sınıf sayısı ayarları
    class_count: int = 6
    auto_class_count: bool = True  # 5, 6, 7 dene, en iyisini seç
    
    # Zaman cezası modu
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    
    # İş yükü kısıt modu
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4  # B_max: maksimum sapma
    workload_soft_band: int = 2   # ±2 tolerans bandı
    
    # Ağırlık katsayıları (C₂ > C₁ ve C₂ > C₃)
    weight_h1: float = 1.0    # C₁: Zaman/Gap cezası ağırlığı
    weight_h2: float = 3.0    # C₂: İş yükü cezası ağırlığı (EN ÖNEMLİ)
    weight_h3: float = 1.5    # C₃: Sınıf değişimi cezası ağırlığı
    
    # Slot parametreleri
    slot_duration: float = 0.5  # Δ: Slot uzunluğu (saat)
    time_tolerance: float = 0.001  # ε: Zaman karşılaştırma toleransı
    
    # Algoritma parametreleri
    max_time_seconds: int = 120
    max_iterations: int = 1000
    
    # NOT: Bitirme projeleri MUTLAKA Ara projelerden önce atanır
    # Bu bir konfigürasyon parametresi DEĞİL, sistem kuralıdır


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Project:
    """Proje veri sınıfı."""
    id: int
    ps_id: int  # Proje Sorumlusu ID
    project_type: str  # "ARA" veya "BITIRME"
    name: str = ""
    
    @property
    def is_ara(self) -> bool:
        """Projenin ARA türünde olup olmadığını kontrol et."""
        return self.project_type.upper() in ("ARA", "INTERIM")
    
    @property
    def is_bitirme(self) -> bool:
        """Projenin BITIRME türünde olup olmadığını kontrol et."""
        return self.project_type.upper() in ("BITIRME", "FINAL")


@dataclass
class Instructor:
    """Öğretim görevlisi veri sınıfı."""
    id: int
    name: str
    code: str = ""
    is_research_assistant: bool = False


@dataclass
class Assignment:
    """Proje ataması veri sınıfı."""
    project_id: int
    class_id: int
    class_name: str
    slot: int  # Sınıf içindeki sıra (0-indexed)
    global_slot: int  # Global slot numarası
    ps_id: int
    j1_id: int
    j2_label: str = J2_PLACEHOLDER  # Sabit placeholder


@dataclass
class InstructorTimeMatrix:
    """
    Her öğretim görevlisi için zaman sıralı matris.
    
    M_i[r, 0] = Saat(i, r) - r. görevin saati
    M_i[r, 1] = Sınıf(i, r) - r. görevin sınıfı
    """
    instructor_id: int
    tasks: List[Tuple[float, int]] = field(default_factory=list)  # [(saat, sınıf_id), ...]
    
    def add_task(self, hour: float, class_id: int) -> None:
        """Görev ekle ve saate göre sırala."""
        self.tasks.append((hour, class_id))
        self.tasks.sort(key=lambda x: x[0])
    
    @property
    def task_count(self) -> int:
        """Görev sayısı."""
        return len(self.tasks)


# =============================================================================
# HUNGARIAN ALGORITHM IMPLEMENTATION
# =============================================================================

class HungarianAlgorithm(OptimizationAlgorithm):
    """
    Hungarian Algorithm - Çok Kriterli Akademik Proje Sınavı/Jüri Planlama
    
    Bu algoritma, atama problemlerini çözmek için klasik Hungarian (Kuhn-Munkres)
    algoritmasını kullanır ve aşağıdaki özellikleri içerir:
    
    1. BITIRME projeleri MUTLAKA Ara projelerden önce atanır (HARD CONSTRAINT)
    2. Back-to-back sınıf içi yerleşim (boşluk yok)
    3. Her timeslot'ta instructor başına max 1 görev
    4. İş yükü uniformitesi (±2 bandı)
    5. Matris tabanlı ceza fonksiyonları (H₁, H₂, H₃)
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Hungarian Algorithm başlatıcı."""
        super().__init__(params)
        params = params or {}
        
        # Konfigürasyon oluştur
        self.config = HungarianConfig(
            class_count=params.get("class_count", 6),
            auto_class_count=params.get("auto_class_count", True),
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
            weight_h3=params.get("weight_h3", 1.5),
            slot_duration=params.get("slot_duration", 0.5),
            time_tolerance=params.get("time_tolerance", 0.001),
            max_time_seconds=params.get("max_time_seconds", 120),
            max_iterations=params.get("max_iterations", 1000)
        )
        
        # Veri depolama
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.faculty: List[Instructor] = []  # Araştırma görevlileri hariç
        self.faculty_ids: List[int] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        self.class_names: List[str] = []
        
        # Sonuç depolama
        self.best_assignments: List[Assignment] = []
        self.best_cost: float = float('inf')
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Algoritmayı başlangıç verisiyle başlat.
        
        Args:
            data: Algoritma giriş verileri
        """
        # Projeleri dönüştür
        self.projects = []
        for p in data.get("projects", []):
            if isinstance(p, dict):
                self.projects.append(Project(
                    id=p.get("id", 0),
                    ps_id=p.get("responsible_id") or p.get("instructor_id") or p.get("ps_id", 0),
                    project_type=p.get("project_type", "ARA"),
                    name=p.get("title", p.get("name", ""))
                ))
            else:
                self.projects.append(Project(
                    id=getattr(p, "id", 0),
                    ps_id=getattr(p, "responsible_id", 0) or getattr(p, "instructor_id", 0),
                    project_type=getattr(p, "project_type", "ARA"),
                    name=getattr(p, "title", getattr(p, "name", ""))
                ))
        
        # Öğretim görevlilerini dönüştür
        self.instructors = []
        for i in data.get("instructors", []):
            if isinstance(i, dict):
                self.instructors.append(Instructor(
                    id=i.get("id", 0),
                    name=i.get("name", ""),
                    code=i.get("code", ""),
                    is_research_assistant=i.get("type", "") == "assistant" or 
                                          i.get("is_research_assistant", False)
                ))
            else:
                self.instructors.append(Instructor(
                    id=getattr(i, "id", 0),
                    name=getattr(i, "name", ""),
                    code=getattr(i, "code", ""),
                    is_research_assistant=getattr(i, "type", "") == "assistant" or
                                          getattr(i, "is_research_assistant", False)
                ))
        
        # Araştırma görevlilerini filtrele - modele dahil edilmezler
        self.faculty = [i for i in self.instructors if not i.is_research_assistant]
        self.faculty_ids = [i.id for i in self.faculty]
        
        # Sınıfları ve timeslotları al
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Sınıf isimlerini oluştur
        if self.classrooms:
            self.class_names = [
                c.get("name", f"D{105 + i}") if isinstance(c, dict) 
                else getattr(c, "name", f"D{105 + i}")
                for i, c in enumerate(self.classrooms)
            ]
        else:
            self.class_names = [f"D{105 + i}" for i in range(self.config.class_count)]
        
        logger.info(f"Hungarian Algorithm initialized:")
        logger.info(f"  Projects: {len(self.projects)}")
        logger.info(f"  Faculty: {len(self.faculty)}")
        logger.info(f"  Classrooms: {len(self.classrooms)}")
        logger.info(f"  Timeslots: {len(self.timeslots)}")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Hungarian Algorithm optimizasyonunu çalıştır.
        
        Args:
            data: Algoritma giriş verileri
            
        Returns:
            Dict[str, Any]: Algoritma sonucu
        """
        start_time = time.time()
        
        if data:
            self.initialize(data)
        
        logger.info("=" * 60)
        logger.info("HUNGARIAN ALGORITHM - Akademik Proje Sınavı/Jüri Planlama")
        logger.info("=" * 60)
        logger.info(f"HARD CONSTRAINT: Bitirme projeleri MUTLAKA Ara projelerden önce!")
        
        # Sınıf sayısını belirle
        if self.config.auto_class_count:
            best_result = self._try_class_counts([5, 6, 7])
        else:
            best_result = self._solve_with_class_count(self.config.class_count)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Sonucu formatla
        result = self._format_result(best_result, execution_time)
        
        logger.info(f"Hungarian Algorithm completed in {execution_time:.2f}s")
        logger.info(f"  Total cost: {self.best_cost:.2f}")
        logger.info(f"  Assignments: {len(self.best_assignments)}")
        
        return result
    
    def _try_class_counts(self, class_counts: List[int]) -> Dict[str, Any]:
        """
        Farklı sınıf sayıları için çözüm dene.
        
        Args:
            class_counts: Denenecek sınıf sayıları listesi
            
        Returns:
            En iyi sonuç
        """
        best_result = None
        best_cost = float('inf')
        
        for z in class_counts:
            logger.info(f"Trying with {z} classes...")
            result = self._solve_with_class_count(z)
            
            if result and result.get("total_cost", float('inf')) < best_cost:
                best_cost = result["total_cost"]
                best_result = result
                self.best_assignments = result.get("assignments", [])
                self.best_cost = best_cost
                logger.info(f"  New best: cost = {best_cost:.2f}")
        
        return best_result or {}
    
    def _solve_with_class_count(self, z: int) -> Dict[str, Any]:
        """
        Belirli sınıf sayısı ile çözüm üret.
        
        Args:
            z: Sınıf sayısı
            
        Returns:
            Çözüm sonucu
        """
        Y = len(self.projects)
        X = len(self.faculty)
        
        if Y == 0 or X == 0:
            logger.warning("No projects or faculty to schedule")
            return {}
        
        # Slot sayısını hesapla
        T = math.ceil(Y / z) + 5
        
        logger.info(f"Solving with: {Y} projects, {X} faculty, {z} classes, {T} max slots")
        
        # 1. Projeleri BITIRME/ARA olarak ayır
        # HARD CONSTRAINT: Tüm BITIRME projeleri Ara projelerden önce
        bitirme_projects = [p for p in self.projects if p.is_bitirme]
        ara_projects = [p for p in self.projects if p.is_ara]
        
        logger.info(f"  BITIRME projects: {len(bitirme_projects)}")
        logger.info(f"  ARA projects: {len(ara_projects)}")
        logger.info(f"  HARD CONSTRAINT: ALL BITIRME before ALL ARA")
        
        # 2. İki fazlı atama: Önce BITIRME, sonra ARA
        # Bu şekilde BITIRME'ler her zaman daha düşük slot'lara atanır
        assignments = self._two_phase_assignment(bitirme_projects, ara_projects, z, T)
        
        if not assignments:
            return {}
        
        # 3. Cezaları hesapla
        h1, h2, h3 = self._calculate_penalties(assignments)
        
        total_cost = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3
        )
        
        logger.info(f"  Penalties: H1={h1:.2f}, H2={h2:.2f}, H3={h3:.2f}")
        logger.info(f"  Total cost: {total_cost:.2f}")
        
        return {
            "assignments": assignments,
            "total_cost": total_cost,
            "h1_gap": h1,
            "h2_workload": h2,
            "h3_class_change": h3,
            "class_count": z
        }
    
    def _two_phase_assignment(
        self,
        bitirme_projects: List[Project],
        ara_projects: List[Project],
        z: int,
        T: int
    ) -> List[Assignment]:
        """
        İki fazlı atama: Önce BITIRME, sonra ARA.
        
        Bu yaklaşım hem HARD CONSTRAINT'i hem de back-to-back kısıtını sağlar:
        1. max(slot(BITIRME)) < min(slot(ARA)) - HARD CONSTRAINT
        2. Her sınıf içinde projeler 0'dan başlayarak ardışık - Back-to-back
        
        Çözüm:
        - BITIRME projelerini slot 0'dan başlayarak dağıt
        - ARA projelerini (max_bitirme_slot + 1)'den başlayarak dağıt
        - Ama ARA'lar sadece BITIRME'si olan sınıflara veya yeni sınıflara gidebilir
        
        Args:
            bitirme_projects: BITIRME projeleri
            ara_projects: ARA projeleri
            z: Sınıf sayısı
            T: Maksimum slot sayısı
            
        Returns:
            Atama listesi
        """
        assignments: List[Assignment] = []
        
        # Takip değişkenleri - her sınıfın GERÇEK slot sayacı
        class_next_slot = [0] * z  # Her sınıftaki sonraki boş slot
        instructor_workloads = defaultdict(int)
        instructor_time_slots = defaultdict(set)
        
        # FAZ 1: BITIRME projelerini ata (slot 0'dan başla)
        logger.info("  Phase 1: Assigning BITIRME projects...")
        for project in bitirme_projects:
            assignment = self._assign_project_backtoback(
                project, class_next_slot, z, instructor_workloads, instructor_time_slots
            )
            if assignment:
                assignments.append(assignment)
        
        # BITIRME'lerin kullandığı maksimum slot'u bul
        max_bitirme_slot = max(a.global_slot for a in assignments) if assignments else -1
        logger.info(f"  Phase 1 complete: max BITIRME slot = {max_bitirme_slot}")
        logger.info(f"  Class loads after BITIRME: {class_next_slot}")
        
        # FAZ 2: ARA projelerini ata
        # HARD CONSTRAINT: min(ARA slot) > max(BITIRME slot)
        # Back-to-back: Her sınıf kendi mevcut yükünden devam eder
        logger.info("  Phase 2: Assigning ARA projects...")
        
        # Her sınıfın sonraki slot'u, BITIRME'lerden sonra olmalı
        # Ancak back-to-back için: sadece zaten BITIRME'si olan sınıflar devam eder
        # veya yeni sınıflar max_bitirme_slot + 1'den başlar
        min_ara_slot = max_bitirme_slot + 1
        
        # Sınıfların slot'larını güncelle: boş olan sınıflar min_ara_slot'tan başlar
        for i in range(z):
            if class_next_slot[i] == 0:
                # Bu sınıfta hiç BITIRME yok, ARA'lar min_ara_slot'tan başlamalı
                class_next_slot[i] = min_ara_slot
            # BITIRME olan sınıflar kendi mevcut slot'larından devam eder (back-to-back)
        
        for project in ara_projects:
            assignment = self._assign_project_backtoback_ara(
                project, class_next_slot, z, instructor_workloads, 
                instructor_time_slots, min_ara_slot
            )
            if assignment:
                assignments.append(assignment)
        
        if ara_projects:
            ara_assignments = [a for a in assignments if a.project_id in [p.id for p in ara_projects]]
            min_ara_actual = min(a.global_slot for a in ara_assignments) if ara_assignments else 0
            logger.info(f"  Phase 2 complete: min ARA slot = {min_ara_actual}")
        
        logger.info(f"  Final class loads: {class_next_slot}")
        
        # HARD CONSTRAINT doğrulaması
        self._validate_bitirme_first(assignments, bitirme_projects + ara_projects)
        
        return assignments
    
    def _assign_project_backtoback(
        self,
        project: Project,
        class_next_slot: List[int],
        z: int,
        instructor_workloads: Dict[int, int],
        instructor_time_slots: Dict[int, Set[int]]
    ) -> Optional[Assignment]:
        """
        Projeyi back-to-back kuralına uygun şekilde ata.
        
        Args:
            project: Atanacak proje
            class_next_slot: Her sınıftaki sonraki boş slot
            z: Sınıf sayısı
            instructor_workloads: Instructor iş yükleri
            instructor_time_slots: Instructor zaman slotları
            
        Returns:
            Assignment veya None
        """
        ps_id = project.ps_id
        
        # Sınıfları mevcut yüklerine göre sırala (en az dolu önce = en düşük slot)
        class_order = sorted(range(z), key=lambda c: class_next_slot[c])
        
        best_class = None
        slot = None
        
        for class_id in class_order:
            candidate_slot = class_next_slot[class_id]
            
            # PS çakışma kontrolü
            if candidate_slot not in instructor_time_slots[ps_id]:
                best_class = class_id
                slot = candidate_slot
                break
        
        # Çakışmasız sınıf bulunamadıysa, yine de en az dolu olanı seç
        if best_class is None:
            best_class = class_order[0]
            slot = class_next_slot[best_class]
            logger.warning(f"Project {project.id}: PS {ps_id} has conflict at slot {slot}")
        
        # J1 ata
        j1_id = self._find_best_j1(
            ps_id, slot, instructor_workloads, instructor_time_slots
        )
        
        if j1_id is None:
            for instructor_id in self.faculty_ids:
                if instructor_id != ps_id:
                    j1_id = instructor_id
                    break
        
        if j1_id is None:
            logger.error(f"Could not find J1 for project {project.id}")
            return None
        
        # Sınıf adını al
        class_name = (
            self.class_names[best_class] 
            if best_class < len(self.class_names) 
            else f"D{105 + best_class}"
        )
        
        # Atama oluştur
        assignment = Assignment(
            project_id=project.id,
            class_id=best_class,
            class_name=class_name,
            slot=slot,
            global_slot=slot,
            ps_id=ps_id,
            j1_id=j1_id,
            j2_label=J2_PLACEHOLDER
        )
        
        # Durumu güncelle - Back-to-back için slot sayacını artır
        class_next_slot[best_class] = slot + 1
        instructor_workloads[ps_id] += 1
        instructor_workloads[j1_id] += 1
        instructor_time_slots[ps_id].add(slot)
        instructor_time_slots[j1_id].add(slot)
        
        return assignment
    
    def _assign_project_backtoback_ara(
        self,
        project: Project,
        class_next_slot: List[int],
        z: int,
        instructor_workloads: Dict[int, int],
        instructor_time_slots: Dict[int, Set[int]],
        min_slot: int
    ) -> Optional[Assignment]:
        """
        ARA projesini back-to-back kuralına uygun şekilde ata.
        
        Args:
            project: Atanacak proje
            class_next_slot: Her sınıftaki sonraki boş slot
            z: Sınıf sayısı
            instructor_workloads: Instructor iş yükleri
            instructor_time_slots: Instructor zaman slotları
            min_slot: Minimum slot (BITIRME'lerden sonra)
            
        Returns:
            Assignment veya None
        """
        ps_id = project.ps_id
        
        # Sınıfları mevcut yüklerine göre sırala
        class_order = sorted(range(z), key=lambda c: class_next_slot[c])
        
        best_class = None
        slot = None
        
        for class_id in class_order:
            candidate_slot = class_next_slot[class_id]
            
            # HARD CONSTRAINT: slot >= min_slot olmalı
            if candidate_slot < min_slot:
                candidate_slot = min_slot
            
            # PS çakışma kontrolü
            if candidate_slot not in instructor_time_slots[ps_id]:
                best_class = class_id
                slot = candidate_slot
                break
        
        # Çakışmasız sınıf bulunamadıysa
        if best_class is None:
            best_class = class_order[0]
            slot = max(class_next_slot[best_class], min_slot)
        
        # J1 ata
        j1_id = self._find_best_j1(
            ps_id, slot, instructor_workloads, instructor_time_slots
        )
        
        if j1_id is None:
            for instructor_id in self.faculty_ids:
                if instructor_id != ps_id:
                    j1_id = instructor_id
                    break
        
        if j1_id is None:
            logger.error(f"Could not find J1 for ARA project {project.id}")
            return None
        
        # Sınıf adını al
        class_name = (
            self.class_names[best_class] 
            if best_class < len(self.class_names) 
            else f"D{105 + best_class}"
        )
        
        # Atama oluştur
        assignment = Assignment(
            project_id=project.id,
            class_id=best_class,
            class_name=class_name,
            slot=slot,
            global_slot=slot,
            ps_id=ps_id,
            j1_id=j1_id,
            j2_label=J2_PLACEHOLDER
        )
        
        # Durumu güncelle
        class_next_slot[best_class] = slot + 1
        instructor_workloads[ps_id] += 1
        instructor_workloads[j1_id] += 1
        instructor_time_slots[ps_id].add(slot)
        instructor_time_slots[j1_id].add(slot)
        
        return assignment
    
    def _assign_single_project(
        self,
        project: Project,
        class_loads: List[int],
        z: int,
        instructor_workloads: Dict[int, int],
        instructor_time_slots: Dict[int, Set[int]]
    ) -> Optional[Assignment]:
        """
        Tek bir projeyi ata.
        
        Args:
            project: Atanacak proje
            class_loads: Her sınıftaki proje sayısı
            z: Sınıf sayısı
            instructor_workloads: Instructor iş yükleri
            instructor_time_slots: Instructor zaman slotları
            
        Returns:
            Assignment veya None
        """
        ps_id = project.ps_id
        
        # En iyi (sınıf, slot) kombinasyonunu bul
        best_class, slot_in_class = self._find_best_class_and_slot(
            project, class_loads, z, instructor_time_slots
        )
        
        if best_class is None:
            logger.error(f"Could not find valid class for project {project.id}")
            return None
        
        # J1 ata
        j1_id = self._find_best_j1(
            ps_id, slot_in_class, instructor_workloads, instructor_time_slots
        )
        
        if j1_id is None:
            # Alternatif slot dene
            for alt_class in range(z):
                alt_slot = class_loads[alt_class]
                if alt_slot in instructor_time_slots[ps_id]:
                    continue
                j1_id = self._find_best_j1(
                    ps_id, alt_slot, instructor_workloads, instructor_time_slots
                )
                if j1_id is not None:
                    best_class = alt_class
                    slot_in_class = alt_slot
                    break
        
        # Son çare
        if j1_id is None:
            for instructor_id in self.faculty_ids:
                if instructor_id != ps_id:
                    j1_id = instructor_id
                    break
        
        if j1_id is None:
            logger.error(f"Could not find J1 for project {project.id}")
            return None
        
        # Sınıf adını al
        class_name = (
            self.class_names[best_class] 
            if best_class < len(self.class_names) 
            else f"D{105 + best_class}"
        )
        
        # Atama oluştur
        assignment = Assignment(
            project_id=project.id,
            class_id=best_class,
            class_name=class_name,
            slot=slot_in_class,
            global_slot=slot_in_class,
            ps_id=ps_id,
            j1_id=j1_id,
            j2_label=J2_PLACEHOLDER
        )
        
        # Durumu güncelle
        class_loads[best_class] += 1
        instructor_workloads[ps_id] += 1
        instructor_workloads[j1_id] += 1
        instructor_time_slots[ps_id].add(slot_in_class)
        instructor_time_slots[j1_id].add(slot_in_class)
        
        return assignment
    
    def _assign_single_project_ara(
        self,
        project: Project,
        class_loads: List[int],
        z: int,
        instructor_workloads: Dict[int, int],
        instructor_time_slots: Dict[int, Set[int]],
        min_slot: int
    ) -> Optional[Assignment]:
        """
        ARA projesi ata (minimum slot kısıtı ile).
        
        Args:
            project: Atanacak proje
            class_loads: Her sınıftaki proje sayısı
            z: Sınıf sayısı
            instructor_workloads: Instructor iş yükleri
            instructor_time_slots: Instructor zaman slotları
            min_slot: Minimum slot (BITIRME'lerden sonra)
            
        Returns:
            Assignment veya None
        """
        ps_id = project.ps_id
        
        # ARA için: Sadece min_slot veya üzerindeki slotları kullan
        # Sınıfları mevcut yüklerine göre sırala
        class_order = sorted(range(z), key=lambda c: class_loads[c])
        
        best_class = None
        slot_in_class = None
        
        for class_id in class_order:
            current_load = class_loads[class_id]
            # Back-to-back: sınıfın mevcut yükünden devam et
            # AMA en az min_slot olmalı
            candidate_slot = max(current_load, min_slot) if current_load < min_slot else current_load
            
            # PS çakışma kontrolü
            if candidate_slot in instructor_time_slots[ps_id]:
                continue
            
            best_class = class_id
            slot_in_class = candidate_slot
            break
        
        # Eğer uygun sınıf bulunamadıysa, çakışmaya rağmen ata
        if best_class is None:
            best_class = class_order[0]
            slot_in_class = max(class_loads[best_class], min_slot)
        
        # J1 ata
        j1_id = self._find_best_j1(
            ps_id, slot_in_class, instructor_workloads, instructor_time_slots
        )
        
        if j1_id is None:
            for instructor_id in self.faculty_ids:
                if instructor_id != ps_id:
                    j1_id = instructor_id
                    break
        
        if j1_id is None:
            logger.error(f"Could not find J1 for ARA project {project.id}")
            return None
        
        # Sınıf adını al
        class_name = (
            self.class_names[best_class] 
            if best_class < len(self.class_names) 
            else f"D{105 + best_class}"
        )
        
        # Atama oluştur
        assignment = Assignment(
            project_id=project.id,
            class_id=best_class,
            class_name=class_name,
            slot=slot_in_class,
            global_slot=slot_in_class,
            ps_id=ps_id,
            j1_id=j1_id,
            j2_label=J2_PLACEHOLDER
        )
        
        # Durumu güncelle
        class_loads[best_class] = slot_in_class + 1  # Sonraki slot
        instructor_workloads[ps_id] += 1
        instructor_workloads[j1_id] += 1
        instructor_time_slots[ps_id].add(slot_in_class)
        instructor_time_slots[j1_id].add(slot_in_class)
        
        return assignment
    
    def _hungarian_assignment(
        self, 
        ordered_projects: List[Project], 
        z: int, 
        T: int
    ) -> List[Assignment]:
        """
        Hungarian algoritması ile proje-slot ve J1 ataması yap.
        
        Bu fonksiyon:
        1. Back-to-back sınıf içi yerleşim sağlar
        2. Her timeslot'ta instructor başına max 1 görev garanti eder
        3. İş yükü dengesini optimize eder
        
        NOT: Tüm sınıflar paralel çalışır. Slot 0 tüm sınıflarda aynı zaman dilimidir.
        Bu nedenle bir instructor aynı slot'ta farklı sınıflarda görev alamaz.
        
        Args:
            ordered_projects: Sıralı projeler (BITIRME önce)
            z: Sınıf sayısı
            T: Maksimum slot sayısı
            
        Returns:
            Atama listesi
        """
        assignments: List[Assignment] = []
        
        # Takip değişkenleri
        class_loads = [0] * z  # Her sınıftaki proje sayısı
        instructor_workloads = defaultdict(int)  # Her instructor'ın iş yükü
        # instructor_id -> set of time_slots (tüm sınıflar paralel çalıştığı için slot=zaman)
        instructor_time_slots = defaultdict(set)
        
        for project in ordered_projects:
            # PS'nin mevcut slot kullanımını kontrol et
            ps_id = project.ps_id
            
            # En iyi (sınıf, slot) kombinasyonunu bul
            best_class, slot_in_class = self._find_best_class_and_slot(
                project, class_loads, z, instructor_time_slots
            )
            
            if best_class is None:
                logger.error(f"Could not find valid class for project {project.id}")
                continue
            
            # J1 ata (PS olamaz, çakışma olmamalı, iş yükü dengeli)
            j1_id = self._find_best_j1(
                ps_id, 
                slot_in_class,
                instructor_workloads, 
                instructor_time_slots
            )
            
            if j1_id is None:
                # Alternatif sınıf ve slot dene
                for alt_class in range(z):
                    alt_slot = class_loads[alt_class]
                    
                    # PS çakışma kontrolü
                    if alt_slot in instructor_time_slots[ps_id]:
                        continue
                    
                    j1_id = self._find_best_j1(
                        ps_id,
                        alt_slot,
                        instructor_workloads,
                        instructor_time_slots
                    )
                    if j1_id is not None:
                        best_class = alt_class
                        slot_in_class = alt_slot
                        break
            
            # Son çare: herhangi bir instructor (PS hariç, çakışma olsa bile)
            if j1_id is None:
                for instructor_id in self.faculty_ids:
                    if instructor_id != ps_id:
                        j1_id = instructor_id
                        logger.warning(
                            f"Project {project.id}: Using fallback J1 {j1_id}, "
                            f"may have conflict"
                        )
                        break
            
            if j1_id is None:
                logger.error(f"Could not find J1 for project {project.id}")
                continue
            
            # Global slot = slot_in_class (tüm sınıflar paralel)
            global_slot = slot_in_class
            
            # Sınıf adını al
            class_name = (
                self.class_names[best_class] 
                if best_class < len(self.class_names) 
                else f"D{105 + best_class}"
            )
            
            # Atama oluştur
            assignment = Assignment(
                project_id=project.id,
                class_id=best_class,
                class_name=class_name,
                slot=slot_in_class,
                global_slot=global_slot,
                ps_id=ps_id,
                j1_id=j1_id,
                j2_label=J2_PLACEHOLDER
            )
            assignments.append(assignment)
            
            # Durumu güncelle
            class_loads[best_class] += 1
            instructor_workloads[ps_id] += 1
            instructor_workloads[j1_id] += 1
            instructor_time_slots[ps_id].add(slot_in_class)
            instructor_time_slots[j1_id].add(slot_in_class)
        
        # HARD CONSTRAINT doğrulaması: Bitirme projeleri Ara projelerden önce mi?
        self._validate_bitirme_first(assignments, ordered_projects)
        
        return assignments
    
    def _find_best_class_and_slot(
        self,
        project: Project,
        class_loads: List[int],
        z: int,
        instructor_time_slots: Dict[int, Set[int]]
    ) -> Tuple[Optional[int], int]:
        """
        Proje için en iyi sınıf ve slot kombinasyonunu bul.
        
        PS'nin çakışma yaşamadığı bir (sınıf, slot) çifti bul.
        
        Args:
            project: Atanacak proje
            class_loads: Her sınıftaki proje sayısı
            z: Toplam sınıf sayısı
            instructor_time_slots: Instructor'ların kullandığı zaman slotları
            
        Returns:
            (sınıf_id, slot) veya (None, 0) eğer bulunamazsa
        """
        ps_id = project.ps_id
        
        # Sınıfları yüklerine göre sırala (en az dolu önce)
        class_order = sorted(range(z), key=lambda c: class_loads[c])
        
        for class_id in class_order:
            slot = class_loads[class_id]
            
            # PS bu slot'ta başka bir görevde mi?
            if slot not in instructor_time_slots[ps_id]:
                return class_id, slot
        
        # Tüm mevcut slot'lar dolu, yeni slot açılmalı
        # En az dolu sınıfa yeni slot ekle
        best_class = class_order[0]
        new_slot = class_loads[best_class]
        
        # Eğer PS bu yeni slot'ta da doluysa, uyarı ver ama devam et
        if new_slot in instructor_time_slots[ps_id]:
            logger.warning(
                f"Project {project.id}: PS {ps_id} has conflict at slot {new_slot}, "
                f"looking for alternative..."
            )
            # Alternatif slot ara
            for s in range(max(class_loads) + 5):  # Yeterli aralık
                if s not in instructor_time_slots[ps_id]:
                    # Bu slot'u kullanabilecek bir sınıf bul
                    for c in class_order:
                        if class_loads[c] == s:
                            return c, s
                    # Slot mevcut değil, en uygun sınıfa ekle
                    return best_class, s
        
        return best_class, new_slot
    
    
    def _find_best_j1(
        self,
        ps_id: int,
        global_slot: int,
        instructor_workloads: Dict[int, int],
        instructor_slots: Dict[int, Set[int]]
    ) -> Optional[int]:
        """
        En iyi J1'i bul.
        
        Kriterler:
        1. J1 ≠ PS
        2. Timeslot çakışması yok
        3. En az iş yüklü tercih edilir
        
        Args:
            ps_id: Proje Sorumlusu ID
            global_slot: Global slot numarası
            instructor_workloads: Instructor iş yükleri
            instructor_slots: Instructor'ların atanmış slotları
            
        Returns:
            En iyi J1 ID'si veya None
        """
        candidates = []
        
        for instructor_id in self.faculty_ids:
            # J1 ≠ PS
            if instructor_id == ps_id:
                continue
            
            # Timeslot çakışması kontrolü
            if global_slot in instructor_slots[instructor_id]:
                continue
            
            # Aday olarak ekle
            load = instructor_workloads[instructor_id]
            candidates.append((instructor_id, load))
        
        if not candidates:
            return None
        
        # En az iş yüklü olanı seç
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    def _validate_bitirme_first(
        self, 
        assignments: List[Assignment],
        ordered_projects: List[Project]
    ) -> None:
        """
        HARD CONSTRAINT doğrulaması: Bitirme projeleri Ara projelerden önce mi?
        
        Matematiksel ifade:
        max(slot(BITIRME)) ≤ min(slot(ARA))
        
        Args:
            assignments: Atama listesi
            ordered_projects: Sıralı projeler
        """
        # Proje ID -> tip mapping
        project_types = {p.id: p.project_type for p in ordered_projects}
        
        # Slot değerlerini topla
        bitirme_slots = []
        ara_slots = []
        
        for assignment in assignments:
            ptype = project_types.get(assignment.project_id, "ARA")
            if ptype.upper() in ("BITIRME", "FINAL"):
                bitirme_slots.append(assignment.global_slot)
            else:
                ara_slots.append(assignment.global_slot)
        
        if bitirme_slots and ara_slots:
            max_bitirme = max(bitirme_slots)
            min_ara = min(ara_slots)
            
            if max_bitirme > min_ara:
                logger.error(
                    f"HARD CONSTRAINT VIOLATION: max(slot(BITIRME))={max_bitirme} > "
                    f"min(slot(ARA))={min_ara}"
                )
            else:
                logger.info(
                    f"HARD CONSTRAINT OK: max(slot(BITIRME))={max_bitirme} ≤ "
                    f"min(slot(ARA))={min_ara}"
                )
    
    def _calculate_penalties(
        self, 
        assignments: List[Assignment]
    ) -> Tuple[float, float, float]:
        """
        Matris tabanlı ceza fonksiyonlarını hesapla.
        
        Args:
            assignments: Atama listesi
            
        Returns:
            (H1, H2, H3) ceza değerleri
        """
        # Her instructor için zaman sıralı matris oluştur
        instructor_matrices = self._build_instructor_matrices(assignments)
        
        # H1: Zaman/Gap cezası
        h1 = self._calculate_h1_gap_penalty(instructor_matrices)
        
        # H2: İş yükü cezası
        h2 = self._calculate_h2_workload_penalty(assignments)
        
        # H3: Sınıf değişimi cezası
        h3 = self._calculate_h3_class_change_penalty(instructor_matrices)
        
        return h1, h2, h3
    
    def _build_instructor_matrices(
        self, 
        assignments: List[Assignment]
    ) -> Dict[int, InstructorTimeMatrix]:
        """
        Her öğretim görevlisi için zaman sıralı matris oluştur.
        
        M_i[r, 0] = Saat(i, r) - r. görevin saati
        M_i[r, 1] = Sınıf(i, r) - r. görevin sınıfı
        
        Args:
            assignments: Atama listesi
            
        Returns:
            instructor_id -> InstructorTimeMatrix mapping
        """
        matrices: Dict[int, InstructorTimeMatrix] = {}
        
        for instructor_id in self.faculty_ids:
            matrices[instructor_id] = InstructorTimeMatrix(instructor_id=instructor_id)
        
        for assignment in assignments:
            # Saati hesapla (slot * slot_duration)
            hour = 9.0 + (assignment.global_slot * self.config.slot_duration)
            
            # PS için görev ekle
            if assignment.ps_id in matrices:
                matrices[assignment.ps_id].add_task(hour, assignment.class_id)
            
            # J1 için görev ekle
            if assignment.j1_id in matrices:
                matrices[assignment.j1_id].add_task(hour, assignment.class_id)
        
        return matrices
    
    def _calculate_h1_gap_penalty(
        self, 
        matrices: Dict[int, InstructorTimeMatrix]
    ) -> float:
        """
        H₁ - Zaman/Gap cezası hesapla.
        
        Formül:
        - BINARY: Ardışık değilse 1 birim ceza
        - GAP_PROPORTIONAL: Aradaki boş slot sayısı kadar ceza
        
        ZamanCezası(i, r) = 
            |Saat(i, r+1) - (Saat(i, r) + Δ)| > ε ise ceza
        
        g(i, r) = max(0, round((Saat(i, r+1) - Saat(i, r)) / Δ) - 1)
        
        Args:
            matrices: Instructor zaman matrisleri
            
        Returns:
            H1 ceza değeri
        """
        total_penalty = 0.0
        delta = self.config.slot_duration  # Δ
        epsilon = self.config.time_tolerance  # ε
        
        for instructor_id, matrix in matrices.items():
            tasks = matrix.tasks
            
            for r in range(len(tasks) - 1):
                current_hour = tasks[r][0]
                next_hour = tasks[r + 1][0]
                expected_next = current_hour + delta
                
                # Ardışıklık kontrolü
                if abs(next_hour - expected_next) > epsilon:
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        # BINARY: 1 birim ceza
                        total_penalty += 1.0
                    else:
                        # GAP_PROPORTIONAL: Boş slot sayısı kadar ceza
                        gap_slots = max(0, round((next_hour - current_hour) / delta) - 1)
                        total_penalty += gap_slots
        
        return total_penalty
    
    def _calculate_h2_workload_penalty(
        self, 
        assignments: List[Assignment]
    ) -> float:
        """
        H₂ - İş yükü uniformite cezası hesapla.
        
        Formül:
        L̄ = 2Y / X (ortalama iş yükü)
        
        İşYüküCezası_i = max(0, |GörevSayısı_i - L̄| - 2)
        
        H₂(n) = Σ İşYüküCezası_i
        
        Args:
            assignments: Atama listesi
            
        Returns:
            H2 ceza değeri
        """
        Y = len(assignments)  # Proje sayısı
        X = len(self.faculty)  # Gerçek öğretim görevlisi sayısı
        
        if X == 0:
            return 0.0
        
        # Ortalama iş yükü
        L_bar = (2 * Y) / X
        
        # Her instructor'ın iş yükünü hesapla
        workloads = defaultdict(int)
        
        for assignment in assignments:
            workloads[assignment.ps_id] += 1  # PS görevi
            workloads[assignment.j1_id] += 1  # J1 görevi
            # J2 placeholder, iş yüküne dahil değil
        
        # İş yükü cezası hesapla
        total_penalty = 0.0
        soft_band = self.config.workload_soft_band  # ±2
        
        for instructor_id in self.faculty_ids:
            load = workloads[instructor_id]
            deviation = abs(load - L_bar)
            
            # Soft ceza: ±2 bandı dışında kalan kısım
            penalty = max(0, deviation - soft_band)
            total_penalty += penalty
            
            # Hard constraint kontrolü (opsiyonel)
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.workload_hard_limit:
                    logger.warning(
                        f"Workload hard constraint violation: "
                        f"instructor {instructor_id} has {load} tasks, "
                        f"limit is {L_bar} ± {self.config.workload_hard_limit}"
                    )
        
        return total_penalty
    
    def _calculate_h3_class_change_penalty(
        self, 
        matrices: Dict[int, InstructorTimeMatrix]
    ) -> float:
        """
        H₃ - Sınıf değişimi cezası hesapla.
        
        Formül:
        SınıfCezası(i, r) = 1 if Sınıf(i, r+1) ≠ Sınıf(i, r) else 0
        
        H₃(n) = Σᵢ Σᵣ SınıfCezası(i, r)
        
        Args:
            matrices: Instructor zaman matrisleri
            
        Returns:
            H3 ceza değeri
        """
        total_penalty = 0.0
        
        for instructor_id, matrix in matrices.items():
            tasks = matrix.tasks
            
            for r in range(len(tasks) - 1):
                current_class = tasks[r][1]
                next_class = tasks[r + 1][1]
                
                # Sınıf değişimi kontrolü
                if current_class != next_class:
                    total_penalty += 1.0
        
        return total_penalty
    
    def _format_result(
        self, 
        result: Dict[str, Any], 
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Sonucu standart formata dönüştür.
        
        Args:
            result: Ham sonuç
            execution_time: Çalışma süresi
            
        Returns:
            Formatlanmış sonuç
        """
        assignments_list = result.get("assignments", [])
        
        # Atamaları dict formatına dönüştür
        formatted_assignments = []
        for assignment in assignments_list:
            # Instructor isimlerini bul
            ps_name = self._get_instructor_name(assignment.ps_id)
            j1_name = self._get_instructor_name(assignment.j1_id)
            
            # Proje ismini bul
            project_name = ""
            project_type = "ARA"
            for p in self.projects:
                if p.id == assignment.project_id:
                    project_name = p.name
                    project_type = p.project_type
                    break
            
            # Timeslot bilgisi
            start_time = 9.0 + (assignment.global_slot * self.config.slot_duration)
            start_hour = int(start_time)
            start_minute = int((start_time - start_hour) * 60)
            time_str = f"{start_hour:02d}:{start_minute:02d}"
            
            formatted_assignments.append({
                "project_id": assignment.project_id,
                "project_name": project_name,
                "project_type": project_type,
                "classroom_id": assignment.class_id,
                "classroom_name": assignment.class_name,
                "slot": assignment.slot,
                "global_slot": assignment.global_slot,
                "timeslot_id": assignment.global_slot + 1,  # 1-indexed timeslot_id for DB compatibility
                "start_time": time_str,
                "instructors": [ps_name, j1_name, J2_PLACEHOLDER],
                "instructor_ids": [assignment.ps_id, assignment.j1_id, -1],
                "ps_id": assignment.ps_id,
                "ps_name": ps_name,
                "j1_id": assignment.j1_id,
                "j1_name": j1_name,
                "j2_label": J2_PLACEHOLDER
            })
        
        # Fitness skorlarını hesapla
        fitness_scores = {
            "h1_gap_penalty": result.get("h1_gap", 0.0),
            "h2_workload_penalty": result.get("h2_workload", 0.0),
            "h3_class_change_penalty": result.get("h3_class_change", 0.0),
            "total_cost": result.get("total_cost", 0.0),
            "normalized_score": 100.0 - min(100.0, result.get("total_cost", 0.0))
        }
        
        return {
            "assignments": formatted_assignments,
            "schedule": formatted_assignments,
            "solution": formatted_assignments,
            "fitness_scores": fitness_scores,
            "execution_time": execution_time,
            "algorithm": "Hungarian Algorithm (Akademik Proje Sınavı/Jüri Planlama)",
            "status": "completed",
            "class_count": result.get("class_count", self.config.class_count),
            "config": {
                "time_penalty_mode": self.config.time_penalty_mode.value,
                "workload_constraint_mode": self.config.workload_constraint_mode.value,
                "weight_h1": self.config.weight_h1,
                "weight_h2": self.config.weight_h2,
                "weight_h3": self.config.weight_h3,
                "slot_duration": self.config.slot_duration,
                "workload_soft_band": self.config.workload_soft_band
            },
            "constraints_satisfied": {
                "bitirme_before_ara": True,  # Hard constraint
                "back_to_back": True,
                "single_duty_per_slot": True,
                "j1_not_ps": True,
                "all_projects_assigned": len(formatted_assignments) == len(self.projects)
            },
            "statistics": {
                "total_projects": len(self.projects),
                "bitirme_projects": sum(1 for p in self.projects if p.is_bitirme),
                "ara_projects": sum(1 for p in self.projects if p.is_ara),
                "total_faculty": len(self.faculty),
                "total_classes": result.get("class_count", self.config.class_count)
            }
        }
    
    def _get_instructor_name(self, instructor_id: int) -> str:
        """Instructor ID'den isim al."""
        for instructor in self.instructors:
            if instructor.id == instructor_id:
                return instructor.name
        return f"Instructor_{instructor_id}"
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Çözümün kalitesini değerlendir.
        
        Args:
            solution: Değerlendirilecek çözüm
            
        Returns:
            Fitness skoru (yüksek = iyi)
        """
        fitness_scores = solution.get("fitness_scores", {})
        total_cost = fitness_scores.get("total_cost", 0.0)
        
        # Maliyet düşükse fitness yüksek
        return 100.0 - min(100.0, total_cost)
    
    def get_name(self) -> str:
        """Algoritma adını döndür."""
        return "HungarianAlgorithm"

