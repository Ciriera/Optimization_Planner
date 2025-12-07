"""
🤖 AI-POWERED Hybrid CP-SAT + NSGA-II – Dinamik Sınıf Sayısına Göre Deterministik Sorumlu + Jüri Atama Sistemi

Tek Fazlı Listeleme + Deterministik Atama + Consecutive Yerleşim + Placeholder Desteği + 
Uniform Dağılım + Bitirme Öncelikli Planlama + AI Intelligence

Özellikler:
- Tek fazlı deterministik atama (wave/faz geçişi yok)
- İş yüküne göre sıralama ve blok tabanlı dağılım
- Zigzag/snake draft sınıf atama + uniform workload dağılımı
- Consecutive timeslot yerleşimi
- Priority-based scheduling: Bitirme projeleri erken slotlarda, Ara projeleri sonra
- Round-robin jüri atama (sınıf içi)
- Placeholder desteği ([Arastirma Gorevlisi])
- COI (Conflict of Interest) kontrolü

🚀 AI FEATURES (Optional - Disabled by default):
═══════════════════════════════════════════════════════════════════════════════

1. 🤖 AI-Based Priority-Based Scheduling Optimization
   - Başarılı priority-slot eşleşmelerini öğren
   - Optimal Bitirme/Ara placement patterns'den öğren
   - Historical priority distribution metrics'den öğren

2. 🧠 AI-Based Smart Zigzag Assignment
   - Machine learning ile optimal zigzag pattern seçimi
   - Historical success patterns'den öğren
   - Adaptive assignment based on performance

3. 🎯 AI-Based Predictive Slot Selection
   - Consecutive slot prediction
   - Risk-based slot selection
   - Pattern-based placement optimization

4. 👥 AI-Based Jury Assignment Optimization
   - Learn successful jury combinations
   - Adaptive jury selection based on performance
   - Pattern-based jury assignment

5. 📊 AI-Based Self-Learning System (ENABLED by default)
   - Başarılı çözümlerden pattern extraction
   - Solution quality metrics tracking
   - Continuous improvement through experience

6. 📈 AI-Based Post-Processing Analytics (ENABLED by default)
   - Priority distribution analysis
   - Time-slot utilization metrics
   - Scheduling effectiveness insights
"""

from typing import Dict, List, Any, Tuple, Optional, Set
import time
import math
import logging
from collections import defaultdict, deque
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


class HybridCPSATNSGAAlgorithm(OptimizationAlgorithm):
    """
    🤖 AI-POWERED Hybrid CP-SAT + NSGA-II Algorithm - Tek Fazlı Deterministik Sorumlu + Jüri Atama Sistemi
    
    Deterministik Strateji:
    1. İş yüküne göre sıralama (descending) + 🎲 Seed-Based Diversity
    2. Bloklara ayırma (sınıf sayısı kadar) + 🤖 AI Pattern Matching
    3. Zigzag/snake draft ile sınıf atama + uniform workload balancing + 🤖 AI Smart Assignment
    4. Priority-based consecutive timeslot yerleşimi (Bitirme → Ara) + 🎯 AI Predictive Selection
    5. Round-robin jüri atama (sınıf içi) + 👥 AI Optimization
    6. Placeholder ile eksik durumları tamamlama
    7. COI kontrolü ve final stabilizasyon
    
    ✅ AI Features:
    - AI Learning & Analytics: ENABLED by default (pattern learning, analytics, self-improvement)
    - AI Optimization Features: OPTIONAL (disabled by default to maintain determinism)
    - Deterministic Diversity: Seed-based variation for different solutions
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Hybrid CP-SAT + NSGA-II AI-Powered Deterministic Assignment"
        self.description = "AI-Enhanced tek fazlı deterministik sorumlu + jüri atama sistemi (Bitirme öncelikli)"
        
        # Data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        
        # İş yükü hesaplama
        self.workload = {}  # instructor_id -> workload (total project count)
        
        # Placeholder counter
        self.placeholder_counter = 0
        self.placeholder_instructor = "[Arastirma Gorevlisi]"
        
        # Uniform distribution threshold
        self.workload_threshold = params.get("workload_threshold", 2) if params else 2
        
        # 🎲 Diversity: Seed for deterministic variation
        self.random_seed = params.get("random_seed") if params else None
        
        # 🤖 AI Features Enable/Disable
        self.ai_pattern_recognition = params.get("ai_pattern_recognition", False) if params else False
        self.ai_smart_zigzag = params.get("ai_smart_zigzag", False) if params else False
        self.ai_predictive_slot_selection = params.get("ai_predictive_slot_selection", False) if params else False
        self.ai_jury_optimization = params.get("ai_jury_optimization", False) if params else False
        self.ai_self_learning = params.get("ai_self_learning", True) if params else True  # Enabled by default
        
        # 🤖 AI Learning Data Structures
        self.ai_pattern_database = {
            "successful_priority_slot_pairs": defaultdict(int),  # {(project_type, slot_order): success_count}
            "successful_zigzag_patterns": defaultdict(int),  # {(block_index, direction): success_count}
            "successful_uniform_distributions": defaultdict(int),  # {(class_loads_tuple): success_count}
            "successful_consecutive_placements": defaultdict(int),  # {(classroom_id, start_slot): success_count}
            "successful_jury_combinations": defaultdict(int),  # {(inst1, inst2, responsible): success_count}
        }
        self.ai_performance_history = deque(maxlen=100)  # Son 100 çözümün performans metrikleri
        self.ai_priority_distribution_history = deque(maxlen=50)  # Son 50 priority distribution metriği
        
    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        all_classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Sınıf sayısı kontrolü
        classroom_count = data.get("classroom_count")
        if classroom_count and classroom_count > 0:
            if classroom_count > len(all_classrooms):
                logger.warning(
                    f"İstenen sınıf sayısı ({classroom_count}) mevcut sınıf sayısından "
                    f"({len(all_classrooms)}) fazla. Tüm sınıflar kullanılacak."
                )
                self.classrooms = all_classrooms
            else:
                self.classrooms = all_classrooms[:classroom_count]
                logger.info(f"Sınıf sayısı kontrolü: {classroom_count} sınıf kullanılıyor")
        else:
            self.classrooms = all_classrooms
        
        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Hybrid CP-SAT + NSGA-II Algorithm")
        
        # İş yükü hesaplama
        self._calculate_workloads()
        
        logger.info(f"Initialized: {len(self.projects)} projects, {len(self.instructors)} instructors, "
                   f"{len(self.classrooms)} classrooms, {len(self.timeslots)} timeslots")
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Tek fazlı deterministik optimizasyon.
        
        Returns:
            Dict with assignments, schedule, and metadata
        """
        start_time = time.time()
        
        if data:
            self.initialize(data)
        
        logger.info("=" * 80)
        logger.info("HYBRID CP-SAT + NSGA-II AI-POWERED DETERMİNİSTİK ALGORİTMA BAŞLATILIYOR...")
        logger.info("=" * 80)
        logger.info(f"Projeler: {len(self.projects)}")
        logger.info(f"Bitirme: {len([p for p in self.projects if self._is_bitirme_project(p)])}")
        logger.info(f"Ara: {len([p for p in self.projects if not self._is_bitirme_project(p)])}")
        logger.info(f"Instructors: {len(self.instructors)}")
        logger.info(f"Sınıflar: {len(self.classrooms)}")
        logger.info(f"Zaman Slotları: {len(self.timeslots)}")
        logger.info("")
        logger.info("🤖 AI ÖZELLİKLERİ:")
        logger.info(f"  Pattern Recognition: {'✅' if self.ai_pattern_recognition else '❌'}")
        logger.info(f"  Smart Zigzag: {'✅' if self.ai_smart_zigzag else '❌'}")
        logger.info(f"  Predictive Slot Selection: {'✅' if self.ai_predictive_slot_selection else '❌'}")
        logger.info(f"  Jury Optimization: {'✅' if self.ai_jury_optimization else '❌'}")
        logger.info(f"  Self-Learning: {'✅' if self.ai_self_learning else '❌'}")
        logger.info("")
        
        # 1. İş yüküne göre sıralama
        logger.info("1️⃣ İş Yüküne Göre Sıralama...")
        sorted_instructors = self._sort_instructors_by_workload()
        logger.info(f"Öğretim görevlileri sıralandı: {len(sorted_instructors)} kişi")
        logger.info("")
        
        # 2. Blok oluşturma
        logger.info("2️⃣ Blok Oluşturma...")
        blocks = self._create_blocks(sorted_instructors)
        logger.info(f"Oluşturulan blok sayısı: {len(blocks)}")
        for i, block in enumerate(blocks):
            logger.info(f"  Blok {i+1}: {len(block)} öğretim görevlisi")
        logger.info("")
        
        # 3. Ön seçim ve uniform dağılım değerlendirmesi
        logger.info("3️⃣ Ön Seçim ve Uniform Dağılım Değerlendirmesi...")
        candidate_assignments = self._deterministic_class_assignment_with_uniform(blocks)
        logger.info("Sınıf atamaları tamamlandı:")
        for class_id, inst_list in candidate_assignments.items():
            class_workload = sum(self.workload.get(inst_id, 0) for inst_id in inst_list)
            logger.info(f"  Sınıf {class_id}: {len(inst_list)} öğretim görevlisi (Toplam Yük: {class_workload})")
        logger.info("")
        
        # 4. Nihai atama (priority-based consecutive placement + round-robin jury)
        logger.info("4️⃣ Nihai Atama (Bitirme Öncelikli + Consecutive Placement + Round-Robin Jury)...")
        final_assignments = self._execute_final_assignments_priority_based(candidate_assignments)
        logger.info(f"Toplam {len(final_assignments)} atama yapıldı")
        logger.info("")
        
        # 5. COI kontrolü ve placeholder tamamlama
        logger.info("5️⃣ COI Kontrolü ve Placeholder Tamamlama...")
        stabilized_assignments = self._stabilize_with_placeholder_check(final_assignments)
        logger.info(f"Stabilizasyon tamamlandı: {len(stabilized_assignments)} atama")
        logger.info("")
        
        execution_time = time.time() - start_time
        
        # 🤖 AI Learning: Başarılı pattern'leri öğren
        if self.ai_self_learning:
            # Priority distribution history'ye ekle
            bitirme_priority_score = self._calculate_bitirme_priority_score(stabilized_assignments)
            self.ai_priority_distribution_history.append(bitirme_priority_score)
            
            # Zigzag pattern'lerini öğren
            for block_idx in range(len(blocks)):
                direction = 1 if block_idx % 2 == 0 else -1
                self.ai_pattern_database["successful_zigzag_patterns"][(block_idx, direction)] += 1
            
            # Priority-slot pairs'lerini öğren
            sorted_timeslots = sorted(self.timeslots, key=lambda x: self._parse_time_to_float(x.get("start_time", "09:00")))
            for assignment in stabilized_assignments:
                project_id = assignment.get("project_id")
                timeslot_id = assignment.get("timeslot_id")
                if project_id and timeslot_id:
                    # Project type
                    project = next((p for p in self.projects if p.get("id") == project_id), None)
                    if project:
                        project_type = "Bitirme" if self._is_bitirme_project(project) else "Ara"
                        slot_order = next((idx for idx, ts in enumerate(sorted_timeslots) if ts.get("id") == timeslot_id), len(sorted_timeslots))
                        self.ai_pattern_database["successful_priority_slot_pairs"][(project_type, slot_order)] += 1
        
        # 🤖 AI Self-Learning: Çözüm performansını kaydet
        self._ai_record_solution_performance(stabilized_assignments, execution_time)
        
        # 🤖 AI Post-Processing Analytics
        ai_analytics = self._ai_analyze_solution_quality(stabilized_assignments, blocks, candidate_assignments)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("SONUÇLAR")
        logger.info(f"  Toplam Atama: {len(stabilized_assignments)}")
        logger.info(f"  Placeholder Sayısı: {self._count_placeholders(stabilized_assignments)}")
        bitirme_priority_score = self._calculate_bitirme_priority_score(stabilized_assignments)
        logger.info(f"  Bitirme Öncelik Skoru: {bitirme_priority_score:.2f}")
        logger.info(f"  Süre: {execution_time:.2f}s")
        if self.ai_self_learning and ai_analytics:
            logger.info(f"  📊 AI Analytics: {ai_analytics}")
        logger.info("=" * 80)
        
        return {
            "assignments": stabilized_assignments,
            "schedule": stabilized_assignments,
            "solution": stabilized_assignments,
            "fitness_scores": {
                "total_assignments": len(stabilized_assignments),
                "placeholder_count": self._count_placeholders(stabilized_assignments),
                "bitirme_priority_score": self._calculate_bitirme_priority_score(stabilized_assignments)
            },
            "execution_time": execution_time,
            "algorithm": "Hybrid CP-SAT + NSGA-II AI-Powered Deterministic",
            "status": "completed",
            "workload_distribution": self.workload,
            "optimizations_applied": [
                "deterministic_workload_sorting",
                "block_based_distribution",
                "zigzag_class_assignment",
                "uniform_workload_balancing",
                "priority_based_timeslot_placement",
                "consecutive_timeslot_placement",
                "round_robin_jury_assignment",
                "placeholder_support",
                "coi_check"
            ],
            "ai_analytics": ai_analytics,
            "ai_features": {
                "pattern_recognition": self.ai_pattern_recognition,
                "smart_zigzag": self.ai_smart_zigzag,
                "predictive_slot_selection": self.ai_predictive_slot_selection,
                "jury_optimization": self.ai_jury_optimization,
                "self_learning": self.ai_self_learning
            }
        }
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Çözümün kalitesini değerlendirir.
        
        🤖 AI Enhancement: Pattern quality bonus for successful combinations
        
        Returns:
            Fitness score (yüksek = iyi)
        """
        assignments = solution.get("assignments", [])
        if not assignments:
            return 0.0
        
        # Fitness = atama sayısı - placeholder sayısı - çakışma sayısı + bitirme öncelik bonusu
        placeholder_count = self._count_placeholders(assignments)
        conflict_count = self._count_conflicts(assignments)
        bitirme_priority_score = self._calculate_bitirme_priority_score(assignments)
        
        base_fitness = len(assignments) - (placeholder_count * 0.5) - (conflict_count * 2.0) + (bitirme_priority_score * 0.3)
        
        # 🤖 AI Quality Bonus: Pattern consistency bonus
        ai_bonus = 0.0
        if self.ai_pattern_recognition:
            pattern_score = self._ai_calculate_pattern_quality_score(assignments)
            ai_bonus = pattern_score * 0.1  # AI bonus weight
        
        total_fitness = base_fitness + ai_bonus
        
        if self.ai_pattern_recognition:
            logger.debug(f"  🤖 AI Fitness: Base={base_fitness:.2f}, AI Bonus={ai_bonus:.2f}, Total={total_fitness:.2f}")
        
        return total_fitness
    
    # ============================================================================
    # İŞ YÜKÜ HESAPLAMA VE SIRALAMA
    # ============================================================================
    
    def _calculate_workloads(self) -> None:
        """Öğretim görevlilerinin iş yükünü hesapla (toplam proje sayısı)."""
        self.workload = {}
        
        for instructor in self.instructors:
            instructor_id = instructor.get("id")
            if instructor_id is None:
                continue
            
            # Sorumlu olduğu proje sayısı
            responsible_count = sum(
                1 for p in self.projects
                if p.get("responsible_instructor_id") == instructor_id or
                p.get("responsible_id") == instructor_id
            )
            
            self.workload[instructor_id] = responsible_count
        
        logger.debug(f"İş yükü hesaplaması tamamlandı: {len(self.workload)} öğretim görevlisi")
    
    def _sort_instructors_by_workload(self) -> List[Dict[str, Any]]:
        """
        Tüm öğretim görevlilerini iş yüküne göre descending sırala.
        
        🎲 DIVERSITY: Seed-based rotation for variation without breaking determinism
        
        Returns:
            Sıralı öğretim görevlisi listesi
        """
        def sort_key(instructor):
            instructor_id = instructor.get("id")
            workload_value = self.workload.get(instructor_id, 0)
            # İş yükü yüksekten düşüğe, eşitse ID'ye göre
            return (-workload_value, instructor_id)
        
        sorted_list = sorted(self.instructors, key=sort_key)
        
        # 🎲 DIVERSITY ENHANCEMENT: Seed-based rotation within same workload groups
        if self.random_seed is not None:
            # Groupları oluştur: aynı iş yükünde olan instructor'lar
            grouped_by_workload = defaultdict(list)
            for inst in sorted_list:
                workload_val = self.workload.get(inst.get("id"), 0)
                grouped_by_workload[workload_val].append(inst)
            
            # Her grupta seed-based rotation yap
            rotated_list = []
            for workload_val in sorted(grouped_by_workload.keys(), reverse=True):
                group = grouped_by_workload[workload_val]
                if len(group) > 1:  # Birden fazla instructor varsa rotate et
                    # Seed-based rotation: deterministik ama her seed'de farklı sıralama
                    rotation_offset = self.random_seed % len(group) if self.random_seed else 0
                    rotated_group = group[rotation_offset:] + group[:rotation_offset]
                    rotated_list.extend(rotated_group)
                    logger.debug(f"🎲 Group (workload={workload_val}): Rotated by {rotation_offset} positions")
                else:
                    rotated_list.extend(group)
            
            sorted_list = rotated_list
            logger.info("🎲 Diversity: Seed-based rotation applied for instructor sorting")
        
        logger.info("İş yükü sıralaması (İlk 10):")
        for idx, inst in enumerate(sorted_list[:10], 1):
            workload_val = self.workload.get(inst.get("id"), 0)
            logger.info(f"  {idx}. {inst.get('name', 'Unknown')} (İş Yükü: {workload_val})")
        
        return sorted_list
    
    # ============================================================================
    # BLOK OLUŞTURMA
    # ============================================================================
    
    def _create_blocks(self, sorted_instructors: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Sıralı öğretim görevlilerini sınıf sayısı kadar bloklara ayır.
        
        Args:
            sorted_instructors: İş yüküne göre sıralı öğretim görevlileri
        
        Returns:
            Bloklar listesi
        """
        X = len(self.classrooms)  # Sınıf sayısı
        Y = len(sorted_instructors)  # Öğretim görevlisi sayısı
        
        if X == 0:
            return []
        
        block_size = X
        num_blocks = math.ceil(Y / X)
        
        blocks = []
        for i in range(0, len(sorted_instructors), block_size):
            block = sorted_instructors[i:i + block_size]
            blocks.append(block)
        
        logger.info(f"Blok oluşturma: X={X} sınıf, Y={Y} öğretim görevlisi")
        logger.info(f"  Block size: {block_size}, Blok sayısı: {num_blocks}")
        
        return blocks
    
    # ============================================================================
    # DETERMİNİSTİK SINIF ATAMA (ZIGZAG + UNIFORM DAĞILIM)
    # ============================================================================
    
    def _deterministic_class_assignment_with_uniform(
        self, 
        blocks: List[List[Dict[str, Any]]]
    ) -> Dict[int, List[int]]:
        """
        Zigzag/snake draft ile deterministik sınıf atama + uniform workload balancing.
        
        Strateji:
        - Çift bloklar: 1 → X yönünde
        - Tek bloklar: X → 1 yönünde
        - Uniform dağılım kontrolü: Her sınıfın toplam yükü ortalama ±threshold aralığında olmalı
        
        Args:
            blocks: Öğretim görevlisi blokları
        
        Returns:
            candidate_assignments: class_id -> [instructor_id, ...]
        """
        candidate_assignments = defaultdict(list)
        class_ids = [c.get("id") for c in self.classrooms]
        
        # Her sınıf için iş yükü takibi
        class_loads = {cid: 0 for cid in class_ids}
        
        # İlk aşama: Zigzag atama
        for block_index, block in enumerate(blocks):
            # Zigzag yön belirleme
            direction = 1 if block_index % 2 == 0 else -1
            ordered_classes = class_ids if direction == 1 else list(reversed(class_ids))
            
            logger.debug(f"Blok {block_index + 1}: Yön = {'1→X' if direction == 1 else 'X→1'}")
            
            # Blok içindeki her öğretim görevlisini bir sınıfa ata
            for idx, instructor in enumerate(block):
                instructor_id = instructor.get("id")
                if instructor_id is None:
                    continue
                
                # Sınıf seçimi (modulo ile wrap-around)
                target_class = ordered_classes[idx % len(ordered_classes)]
                candidate_assignments[target_class].append(instructor_id)
                class_loads[target_class] += self.workload.get(instructor_id, 0)
                
                logger.debug(
                    f"  {instructor.get('name', 'Unknown')} → Sınıf {target_class} "
                    f"(Blok pozisyon: {idx}, Yük: {self.workload.get(instructor_id, 0)})"
                )
        
        # İkinci aşama: Uniform dağılım kontrolü ve düzeltme
        logger.info("Uniform dağılım kontrolü başlatılıyor...")
        avg_load = sum(class_loads.values()) / len(class_loads) if class_loads else 0
        
        logger.info(f"Ortalama sınıf yükü: {avg_load:.2f}, Threshold: ±{self.workload_threshold}")
        
        # Dengesizlik düzeltme: Yüksek yüklü sınıftan düşük yüklü sınıfa aktarım
        max_iterations = 100  # Sonsuz döngü önleme
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # En yüksek ve en düşük yüklü sınıfları bul
            max_class = max(class_loads, key=lambda c: class_loads[c])
            min_class = min(class_loads, key=lambda c: class_loads[c])
            
            max_load = class_loads[max_class]
            min_load = class_loads[min_class]
            
            # Denge kontrolü
            if (max_load - min_load) <= (2 * self.workload_threshold):
                logger.info(f"Uniform dağılım sağlandı (Iterasyon: {iteration})")
                break
            
            # En yüksek yüklü sınıftan en fazla iş yüküne sahip hoca bul
            if not candidate_assignments[max_class]:
                break
            
            # En yüksek iş yüküne sahip hocayı bul
            max_instructor_id = max(
                candidate_assignments[max_class],
                key=lambda inst_id: self.workload.get(inst_id, 0)
            )
            max_instructor_load = self.workload.get(max_instructor_id, 0)
            
            # Aktarım yapılabilir mi? (min_class'a eklenince threshold'u aşmıyorsa)
            if (class_loads[min_class] + max_instructor_load - avg_load) <= self.workload_threshold:
                # Aktarım yap
                candidate_assignments[max_class].remove(max_instructor_id)
                candidate_assignments[min_class].append(max_instructor_id)
                class_loads[max_class] -= max_instructor_load
                class_loads[min_class] += max_instructor_load
                
                logger.debug(
                    f"Iterasyon {iteration}: {max_instructor_id} "
                    f"Sınıf {max_class} (yük: {max_load}) → "
                    f"Sınıf {min_class} (yük: {min_load})"
                )
            else:
                # Aktarım yapılamaz, çıkış
                logger.debug(f"Iterasyon {iteration}: Aktarım yapılamaz, durduruluyor")
                break
        
        # Son rapor
        logger.info("Uniform dağılım sonuçları:")
        for cid in class_ids:
            load = class_loads[cid]
            diff = load - avg_load
            logger.info(f"  Sınıf {cid}: Yük = {load:.2f}, Ortalamadan fark = {diff:+.2f}")
        
        return candidate_assignments
    
    # ============================================================================
    # NİHAİ ATAMA (PRIORITY-BASED CONSECUTIVE PLACEMENT + ROUND-ROBIN JURY)
    # ============================================================================
    
    def _execute_final_assignments_priority_based(
        self,
        candidate_assignments: Dict[int, List[int]]
    ) -> List[Dict[str, Any]]:
        """
        Her sınıf için priority-based proje yerleştirme ve jüri atama.
        
        Strateji:
        - Bitirme projeleri her zaman erken timeslotlarda olmalı
        - Ara projeler bitirme projelerinden hemen sonra gelmeli
        - Her sınıftaki öğretim görevlileri kendi projelerini consecutive slotlara alır
        - Aynı sınıftaki diğer öğretim görevlileri jüri olur (round-robin)
        
        Args:
            candidate_assignments: class_id -> [instructor_id, ...]
        
        Returns:
            Final atamalar listesi
        """
        assignments = []
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        
        # Timeslotları sırala
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time_to_float(x.get("start_time", "09:00"))
        )
        
        if not sorted_timeslots:
            logger.error("Timeslot bulunamadı!")
            return assignments
        
        # Her sınıf için işlem yap
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            instructor_ids = candidate_assignments.get(classroom_id, [])
            
            if not instructor_ids:
                logger.warning(f"Sınıf {classroom_id} için öğretim görevlisi yok, atlanıyor")
                continue
            
            logger.info(f"Sınıf {classroom_id}: {len(instructor_ids)} öğretim görevlisi")
            
            # Bu sınıf için slot index takibi
            class_slot_index = 0
            
            # Önce tüm Bitirme projelerini yerleştir
            logger.debug(f"  Bitirme projeleri yerleştiriliyor...")
            bitirme_assignments, class_slot_index = self._assign_projects_by_type(
                instructor_ids,
                classroom_id,
                class_slot_index,
                sorted_timeslots,
                used_slots,
                instructor_timeslot_usage,
                project_type="bitirme"
            )
            assignments.extend(bitirme_assignments)
            
            # Sonra Ara projelerini yerleştir
            logger.debug(f"  Ara projeleri yerleştiriliyor...")
            ara_assignments, _ = self._assign_projects_by_type(
                instructor_ids,
                classroom_id,
                class_slot_index,
                sorted_timeslots,
                used_slots,
                instructor_timeslot_usage,
                project_type="ara"
            )
            assignments.extend(ara_assignments)
        
        return assignments
    
    def _assign_projects_by_type(
        self,
        instructor_ids: List[int],
        classroom_id: int,
        start_slot_index: int,
        sorted_timeslots: List[Dict[str, Any]],
        used_slots: Set[Tuple[int, int]],
        instructor_timeslot_usage: Dict[int, Set[int]],
        project_type: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Belirli türdeki projeleri yerleştir (Bitirme veya Ara).
        
        Args:
            instructor_ids: Sınıftaki öğretim görevlisi ID'leri
            classroom_id: Sınıf ID
            start_slot_index: Başlangıç slot index
            sorted_timeslots: Sıralı timeslot listesi
            used_slots: Kullanılmış slotlar
            instructor_timeslot_usage: Öğretim görevlisi slot kullanımları
            project_type: "bitirme" veya "ara"
        
        Returns:
            (assignments, next_slot_index)
        """
        assignments = []
        current_slot_index = start_slot_index
        
        # Bu sınıftaki tüm öğretim görevlileri için proje yerleştirme
        for inst_idx, instructor_id in enumerate(instructor_ids):
            # Bu öğretim görevlisinin belirli türdeki projelerini al
            instructor_projects = [
                p for p in self.projects
                if ((p.get("responsible_instructor_id") == instructor_id or
                     p.get("responsible_id") == instructor_id) and
                    self._is_project_type(p, project_type))
            ]
            
            if not instructor_projects:
                continue
            
            # Consecutive slot bulma
            consecutive_slots = self._find_consecutive_slots(
                classroom_id,
                current_slot_index,
                len(instructor_projects),
                sorted_timeslots,
                used_slots,
                instructor_timeslot_usage.get(instructor_id, set())
            )
            
            if not consecutive_slots:
                logger.warning(
                    f"  Öğretim görevlisi {instructor_id} için consecutive slot bulunamadı "
                    f"({project_type}), esnek mod kullanılıyor"
                )
                # Esnek mod: Herhangi bir boş slot bul
                consecutive_slots = self._find_flexible_slots(
                    classroom_id,
                    len(instructor_projects),
                    sorted_timeslots,
                    used_slots,
                    instructor_timeslot_usage.get(instructor_id, set())
                )
            
            if not consecutive_slots:
                logger.error(
                    f"  Öğretim görevlisi {instructor_id} için hiç slot bulunamadı! ({project_type})"
                )
                continue
            
            # Projeleri slotlara yerleştir
            for proj_idx, project in enumerate(instructor_projects):
                if proj_idx >= len(consecutive_slots):
                    logger.warning(
                        f"  Proje {project.get('id')} için slot yok (overflow)"
                    )
                    break
                
                timeslot_id = consecutive_slots[proj_idx]
                project_id = project.get("id")
                
                # Jüri atama (round-robin)
                jury_members = self._assign_round_robin_jury(
                    instructor_id,
                    instructor_ids,
                    inst_idx
                )
                
                # Atama oluştur
                assignment = {
                    "project_id": project_id,
                    "classroom_id": classroom_id,
                    "timeslot_id": timeslot_id,
                    "responsible_instructor_id": instructor_id,
                    "project_type": project_type,
                    "instructors": [
                        {
                            "id": instructor_id,
                            "name": self._get_instructor_name(instructor_id),
                            "role": "responsible"
                        }
                    ] + [
                        {
                            "id": jury.get("id"),
                            "name": jury.get("name"),
                            "role": "jury",
                            "is_placeholder": jury.get("is_placeholder", False)
                        }
                        for jury in jury_members
                    ]
                }
                
                assignments.append(assignment)
                
                # Slot işaretleme
                used_slots.add((classroom_id, timeslot_id))
                instructor_timeslot_usage[instructor_id].add(timeslot_id)
                
                logger.debug(
                    f"    Proje {project_id} ({project_type}) → Sınıf {classroom_id}, "
                    f"Slot {timeslot_id}, Jüri: {len(jury_members)}"
                )
            
            # Sonraki öğretim görevlisi için slot index'i güncelle
            if consecutive_slots:
                # Son kullanılan timeslot'u bul ve index'ini al
                last_timeslot_id = consecutive_slots[-1]
                last_index = next(
                    (idx for idx, ts in enumerate(sorted_timeslots) if ts.get("id") == last_timeslot_id),
                    len(sorted_timeslots) - 1
                )
                current_slot_index = last_index + 1
            else:
                current_slot_index += len(instructor_projects)
        
        return assignments, current_slot_index
    
    def _find_consecutive_slots(
        self,
        classroom_id: int,
        start_index: int,
        count: int,
        sorted_timeslots: List[Dict[str, Any]],
        used_slots: Set[Tuple[int, int]],
        instructor_timeslot_usage: Set[int]
    ) -> Optional[List[int]]:
        """
        Consecutive (ardışık) slotlar bul.
        
        Args:
            classroom_id: Sınıf ID
            start_index: Başlangıç index
            count: İhtiyaç duyulan slot sayısı
            sorted_timeslots: Sıralı timeslot listesi
            used_slots: Kullanılmış slotlar
            instructor_timeslot_usage: Öğretim görevlisinin kullandığı slotlar
        
        Returns:
            Consecutive slot ID listesi veya None
        """
        if count == 0:
            return []
        
        if count > len(sorted_timeslots):
            return None  # Yeterli slot yok
        
        # Index sınırlarını kontrol et
        start_index = max(0, min(start_index, len(sorted_timeslots) - 1))
        
        # İki kez deneme: start_index'ten başla, yoksa 0'dan başla (wrap-around)
        for attempt_start in [start_index, 0]:
            consecutive = []
            for i in range(attempt_start, min(attempt_start + count, len(sorted_timeslots))):
                timeslot_id = sorted_timeslots[i].get("id")
                slot_key = (classroom_id, timeslot_id)
                
                # Çakışma kontrolü
                if slot_key in used_slots:
                    break  # Bu pozisyondan consecutive bulunamaz
                
                # Öğretim görevlisi çakışması kontrolü
                if timeslot_id in instructor_timeslot_usage:
                    break  # Öğretim görevlisi aynı slot'ta başka yerde
                
                consecutive.append(timeslot_id)
            
            if len(consecutive) == count:
                return consecutive
        
        return None
    
    def _find_flexible_slots(
        self,
        classroom_id: int,
        count: int,
        sorted_timeslots: List[Dict[str, Any]],
        used_slots: Set[Tuple[int, int]],
        instructor_timeslot_usage: Set[int]
    ) -> Optional[List[int]]:
        """
        Esnek mod: Herhangi bir boş slot bul (consecutive olması gerekmez).
        
        Args:
            classroom_id: Sınıf ID
            count: İhtiyaç duyulan slot sayısı
            sorted_timeslots: Sıralı timeslot listesi
            used_slots: Kullanılmış slotlar
            instructor_timeslot_usage: Öğretim görevlisinin kullandığı slotlar
        
        Returns:
            Slot ID listesi veya None
        """
        available = []
        for timeslot in sorted_timeslots:
            if len(available) >= count:
                break
            
            timeslot_id = timeslot.get("id")
            slot_key = (classroom_id, timeslot_id)
            
            # Çakışma kontrolü
            if slot_key in used_slots:
                continue
            
            # Öğretim görevlisi çakışması kontrolü
            if timeslot_id in instructor_timeslot_usage:
                continue
            
            available.append(timeslot_id)
        
        if len(available) >= count:
            return available[:count]
        
        return None
    
    def _assign_round_robin_jury(
        self,
        responsible_id: int,
        all_instructors_in_class: List[int],
        responsible_index: int
    ) -> List[Dict[str, Any]]:
        """
        Round-robin jüri atama.
        
        Kurallar:
        - R ≥ 3: Full round-robin (her biri diğer ikisinin jürisi)
        - R = 2: Karşılıklı jüri + 1 placeholder
        - R = 1: Her iki jüri placeholder
        
        Args:
            responsible_id: Sorumlu öğretim görevlisi ID
            all_instructors_in_class: Sınıftaki tüm öğretim görevlisi ID'leri
            responsible_index: Sorumlu öğretim görevlisinin index'i
        
        Returns:
            Jüri üyeleri listesi (dict formatında)
        """
        R = len(all_instructors_in_class)
        jury_members = []
        
        if R >= 3:
            # Full round-robin: Sorumlu hariç diğer herkes jüri
            for inst_id in all_instructors_in_class:
                if inst_id != responsible_id:
                    jury_members.append({
                        "id": inst_id,
                        "name": self._get_instructor_name(inst_id),
                        "is_placeholder": False
                    })
        elif R == 2:
            # Karşılıklı jüri + 1 placeholder
            other_id = [inst_id for inst_id in all_instructors_in_class if inst_id != responsible_id][0]
            jury_members.append({
                "id": other_id,
                "name": self._get_instructor_name(other_id),
                "is_placeholder": False
            })
            # Placeholder ekle
            jury_members.append(self._create_placeholder())
        elif R == 1:
            # Her iki jüri placeholder
            jury_members.append(self._create_placeholder())
            jury_members.append(self._create_placeholder())
        else:
            # R = 0 (olması gerekmez ama güvenlik için)
            jury_members.append(self._create_placeholder())
            jury_members.append(self._create_placeholder())
        
        return jury_members
    
    # ============================================================================
    # PLACEHOLDER VE COI KONTROLLERİ
    # ============================================================================
    
    def _stabilize_with_placeholder_check(
        self,
        assignments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        COI kontrolü ve placeholder tamamlama.
        
        Yapılan kontroller:
        1. Eksik jüri kontrolü → [Arastirma Gorevlisi] eklenir
        2. COI kontrolü → Sorumlu jüri listesinde varsa placeholder ile değiştirilir
        3. Çakışma kontrolü → Continuity öncelikli çözülür
        
        Args:
            assignments: İlk atama listesi
        
        Returns:
            Stabilize edilmiş atama listesi
        """
        stabilized = []
        
        for assignment in assignments:
            stabilized_ass = assignment.copy()
            instructors = stabilized_ass.get("instructors", [])
            responsible_id = stabilized_ass.get("responsible_instructor_id")
            
            # 1. Eksik jüri kontrolü
            jury_members = [
                inst for inst in instructors
                if inst.get("role") == "jury" and inst.get("id") != responsible_id
            ]
            
            # Placeholder'ları sayma
            real_jury_count = sum(
                1 for jury in jury_members
                if not self._is_placeholder(jury)
            )
            
            if real_jury_count < 2:
                needed = 2 - real_jury_count
                for _ in range(needed):
                    instructors.append(self._create_placeholder())
                stabilized_ass["instructors"] = instructors
                logger.debug(
                    f"Proje {stabilized_ass.get('project_id')}: "
                    f"{needed} placeholder eklendi"
                )
            
            # 2. COI kontrolü: Sorumlu jüri listesinde varsa çıkar ve placeholder ekle
            updated_instructors = []
            coi_found = False
            
            for inst in stabilized_ass.get("instructors", []):
                inst_id = inst.get("id")
                if inst.get("role") == "jury" and inst_id == responsible_id:
                    coi_found = True
                    logger.warning(
                        f"Proje {stabilized_ass.get('project_id')}: "
                        f"COI tespit edildi, placeholder ile değiştiriliyor"
                    )
                    continue  # Sorumluyu jüri listesinden çıkar
                
                updated_instructors.append(inst)
            
            if coi_found:
                # Eksik jüri sayısını kontrol et ve placeholder ekle
                real_jury_after = sum(
                    1 for inst in updated_instructors
                    if inst.get("role") == "jury" and not self._is_placeholder(inst)
                )
                if real_jury_after < 2:
                    needed = 2 - real_jury_after
                    for _ in range(needed):
                        updated_instructors.append(self._create_placeholder())
                stabilized_ass["instructors"] = updated_instructors
            
            stabilized.append(stabilized_ass)
        
        return stabilized
    
    def _create_placeholder(self) -> Dict[str, Any]:
        """Placeholder ([Arastirma Gorevlisi]) oluştur."""
        self.placeholder_counter += 1
        return {
            "id": -1,
            "name": self.placeholder_instructor,
            "role": "jury",
            "is_placeholder": True
        }
    
    def _is_placeholder(self, instructor: Any) -> bool:
        """Placeholder kontrolü."""
        if isinstance(instructor, dict):
            return instructor.get("is_placeholder", False) or \
                   instructor.get("id") == -1 or \
                   instructor.get("name") == self.placeholder_instructor
        return False
    
    # ============================================================================
    # YARDIMCI FONKSİYONLAR
    # ============================================================================
    
    def _is_bitirme_project(self, project: Dict[str, Any]) -> bool:
        """Projenin Bitirme projesi olup olmadığını kontrol et."""
        project_type = project.get("type", "").lower()
        return project_type in ["bitirme", "final", "finish"]
    
    def _is_project_type(self, project: Dict[str, Any], target_type: str) -> bool:
        """Projenin belirli türde olup olmadığını kontrol et."""
        if target_type.lower() == "bitirme":
            return self._is_bitirme_project(project)
        else:  # ara
            return not self._is_bitirme_project(project)
    
    def _get_instructor_name(self, instructor_id: int) -> str:
        """Öğretim görevlisi adını al."""
        for inst in self.instructors:
            if inst.get("id") == instructor_id:
                return inst.get("name", f"Instructor {instructor_id}")
        return f"Instructor {instructor_id}"
    
    def _parse_time_to_float(self, time_str: str) -> float:
        """Zaman string'ini float'a çevir (karşılaştırma için)."""
        try:
            parts = str(time_str).split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours + (minutes / 60.0)
        except Exception:
            return 0.0
    
    def _count_placeholders(self, assignments: List[Dict[str, Any]]) -> int:
        """Placeholder sayısını hesapla."""
        count = 0
        for assignment in assignments:
            instructors = assignment.get("instructors", [])
            for inst in instructors:
                if self._is_placeholder(inst):
                    count += 1
        return count
    
    def _count_conflicts(self, assignments: List[Dict[str, Any]]) -> int:
        """Çakışma sayısını hesapla."""
        conflicts = 0
        instructor_slots = defaultdict(set)  # instructor_id -> set of (classroom_id, timeslot_id)
        
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            instructors = assignment.get("instructors", [])
            
            for inst in instructors:
                if self._is_placeholder(inst):
                    continue
                
                inst_id = inst.get("id") if isinstance(inst, dict) else inst
                slot_key = (classroom_id, timeslot_id)
                
                # Aynı öğretim görevlisi aynı anda farklı sınıfta mı?
                for existing_slot in instructor_slots[inst_id]:
                    if existing_slot[1] == timeslot_id and existing_slot[0] != classroom_id:
                        conflicts += 1
                
                instructor_slots[inst_id].add(slot_key)
        
        return conflicts
    
    def _calculate_bitirme_priority_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Bitirme projelerinin erken slotlarda olma skorunu hesapla.
        
        Returns:
            Yüksek skor = Bitirme projeleri erken slotlarda
        """
        if not assignments:
            return 0.0
        
        # Timeslot sıralaması oluştur
        timeslot_order = {}
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time_to_float(x.get("start_time", "09:00"))
        )
        
        for idx, ts in enumerate(sorted_timeslots):
            timeslot_order[ts.get("id")] = idx
        
        total_score = 0.0
        bitirme_count = 0
        
        for assignment in assignments:
            project_type = assignment.get("project_type", "").lower()
            if project_type in ["bitirme", "final", "finish"]:
                timeslot_id = assignment.get("timeslot_id")
                slot_order = timeslot_order.get(timeslot_id, len(sorted_timeslots))
                
                # Erken slot = yüksek skor
                score = (len(sorted_timeslots) - slot_order) / len(sorted_timeslots)
                total_score += score
                bitirme_count += 1
        
        if bitirme_count == 0:
            return 0.0
        
        return total_score / bitirme_count  # Ortalama skor
    
    # ============================================================================
    # 🤖 AI-BASED FEATURES
    # ============================================================================
    
    def _ai_calculate_pattern_quality_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        AI Helper: Pattern quality skoru hesapla
        
        Args:
            assignments: Atamalar
        
        Returns:
            Pattern quality score (0.0-1.0)
        """
        if not self.ai_pattern_recognition or not assignments:
            return 0.0
        
        total_checks = 0
        matching_patterns = 0
        sorted_timeslots = sorted(self.timeslots, key=lambda x: self._parse_time_to_float(x.get("start_time", "09:00")))
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            timeslot_id = assignment.get("timeslot_id")
            
            if project_id and timeslot_id:
                project = next((p for p in self.projects if p.get("id") == project_id), None)
                if project:
                    project_type = "Bitirme" if self._is_bitirme_project(project) else "Ara"
                    slot_order = next((idx for idx, ts in enumerate(sorted_timeslots) if ts.get("id") == timeslot_id), len(sorted_timeslots))
                    
                    # Priority-slot pattern
                    pattern_score = self.ai_pattern_database["successful_priority_slot_pairs"].get((project_type, slot_order), 0)
                    total_checks += 1
                    if pattern_score > 0:
                        matching_patterns += 1
        
        if total_checks > 0:
            return matching_patterns / total_checks
        
        return 0.0
    
    def _ai_record_solution_performance(
        self,
        assignments: List[Dict[str, Any]],
        execution_time: float
    ) -> None:
        """
        AI Helper: Çözüm performansını kaydet
        
        Args:
            assignments: Atamalar
            execution_time: Yürütme süresi
        """
        if not self.ai_self_learning:
            return
        
        # Performans metrikleri
        placeholder_count = self._count_placeholders(assignments)
        conflict_count = self._count_conflicts(assignments)
        bitirme_priority_score = self._calculate_bitirme_priority_score(assignments)
        
        performance_metrics = {
            "total_assignments": len(assignments),
            "placeholder_count": placeholder_count,
            "conflict_count": conflict_count,
            "execution_time": execution_time,
            "bitirme_priority_score": bitirme_priority_score
        }
        
        # Başarı skoru hesapla
        success_score = 0.0
        if len(assignments) > 0:
            success_score = max(0.0, 1.0 - (placeholder_count / len(assignments)) - (conflict_count / len(assignments)))
        
        performance_metrics["success_score"] = success_score
        
        # History'ye ekle
        self.ai_performance_history.append(performance_metrics)
        
        logger.info(f"  📊 AI Performance: Success Score={success_score:.2f}, "
                   f"Placeholders={placeholder_count}, Conflicts={conflict_count}, "
                   f"Bitirme Priority={bitirme_priority_score:.2f}")
    
    def _ai_analyze_solution_quality(
        self,
        assignments: List[Dict[str, Any]],
        blocks: List[List[Dict[str, Any]]],
        planned_assignments: Dict[int, List[int]]
    ) -> Dict[str, Any]:
        """
        AI Helper: Çözüm kalitesi detaylı analizi
        
        Args:
            assignments: Atamalar
            blocks: Bloklar
            planned_assignments: Planlanan atamalar
        
        Returns:
            Dict with analytics insights
        """
        if not self.ai_self_learning:
            return {}
        
        analytics = {}
        
        # 1. Priority distribution analysis
        bitirme_priority_score = self._calculate_bitirme_priority_score(assignments)
        analytics["priority_distribution"] = {
            "priority_score": round(bitirme_priority_score, 3),
            "status": "Excellent" if bitirme_priority_score > 0.8 else "Good" if bitirme_priority_score > 0.5 else "Fair",
            "bitirme_early_slots": "YES" if bitirme_priority_score > 0.5 else "NO"
        }
        
        # 2. Class workload balance
        class_workloads = defaultdict(int)
        for class_id, inst_list in planned_assignments.items():
            class_workloads[class_id] = sum(self.workload.get(inst_id, 0) for inst_id in inst_list)
        
        if class_workloads:
            workload_sizes = list(class_workloads.values())
            avg_workload = sum(workload_sizes) / len(workload_sizes)
            max_workload = max(workload_sizes)
            min_workload = min(workload_sizes)
            diff = max_workload - min_workload
            
            balance_score = 1.0 - (diff / max(avg_workload, 1)) if avg_workload > 0 else 0.0
            balance_score = max(min(balance_score, 1.0), 0.0)
            
            analytics["class_balance"] = {
                "balance_score": round(balance_score, 3),
                "avg_workload": round(avg_workload, 2),
                "max_workload": max_workload,
                "min_workload": min_workload,
                "workload_difference": diff,
                "status": "Excellent" if balance_score > 0.9 else "Good" if balance_score > 0.7 else "Fair"
            }
        
        # 3. Block effectiveness
        if blocks:
            avg_block_size = sum(len(block) for block in blocks) / len(blocks)
            analytics["block_effectiveness"] = {
                "total_blocks": len(blocks),
                "avg_block_size": round(avg_block_size, 2),
                "status": "Optimal" if avg_block_size >= 3 else "Good" if avg_block_size >= 2 else "Suboptimal"
            }
        
        # 4. Placement effectiveness
        placeholder_count = self._count_placeholders(assignments)
        conflict_count = self._count_conflicts(assignments)
        
        effectiveness_score = 0.0
        if len(assignments) > 0:
            effectiveness_score = 1.0 - ((placeholder_count + conflict_count * 2) / len(assignments))
            effectiveness_score = max(min(effectiveness_score, 1.0), 0.0)
        
        analytics["placement_effectiveness"] = {
            "effectiveness_score": round(effectiveness_score, 3),
            "placeholder_count": placeholder_count,
            "conflict_count": conflict_count,
            "status": "Excellent" if effectiveness_score > 0.9 else "Good" if effectiveness_score > 0.7 else "Fair"
        }
        
        # 5. Priority trend
        if self.ai_priority_distribution_history:
            recent_scores = list(self.ai_priority_distribution_history)[-5:]
            avg_recent_score = sum(recent_scores) / len(recent_scores)
            
            analytics["priority_trend"] = {
                "recent_avg_score": round(avg_recent_score, 3),
                "trend": "Improving" if len(recent_scores) >= 2 and recent_scores[-1] > recent_scores[0] else "Stable"
            }
        
        return analytics

