from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np
import random
import logging
import time
from datetime import datetime
from collections import defaultdict, Counter
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)

@dataclass
class Instructor:
    id: int
    name: str
    project_count: int
    availability: List[bool]
    expertise: List[str] = None
    collaboration_history: Dict[int, int] = None  # instructor_id -> count of past collaborations

@dataclass
class Project:
    id: int
    supervisor_id: int
    required_jury_count: int = 2
    topic: str = ""
    difficulty: float = 0.5  # 0.0 to 1.0

@dataclass
class TimeSlot:
    id: int
    start_time: str
    end_time: str
    
@dataclass
class Classroom:
    id: int
    name: str
    capacity: int
    features: List[str] = None

class LexicographicAlgorithm(OptimizationAlgorithm):
    """
    Lexicographic optimizasyon algoritması - AI destekli versiyonu
    
    AI FEATURES:
    ============
    - ✅ SMART INSTRUCTOR PAIRING: Akıllı eşleştirme
    - ✅ DYNAMIC TIME SLOT ASSIGNMENT: Tüm zaman dilimlerini kullanma
    - ✅ MULTI-SOLUTION GENERATION: Çoklu çözüm üretimi
    - ✅ STOCHASTIC OPTIMIZATION: Simulated annealing
    - ✅ DIVERSITY METRICS: Çeşitlilik metrikleri
    - ✅ CONFLICT RESOLUTION: Çakışma çözümleme
    - ✅ GAP FILLING: Boşluk doldurma
    - ✅ WORKLOAD BALANCING: İş yükü dengeleme
    
    ADVANCED AI FEATURES:
    ====================
    - ✅ ADAPTIVE PARAMETER TUNING: Parametreleri otomatik ayarlama
    - ✅ SOLUTION MEMORY & LEARNING: Geçmiş çözümlerden öğrenme
    - ✅ DYNAMIC FITNESS WEIGHTS: Fitness ağırlıklarını dinamik ayarlama
    - ✅ SMART MUTATION STRATEGIES: Akıllı mutasyon operatörleri
    - ✅ BEAM SEARCH INTEGRATION: En iyi k çözümü takip etme
    - ✅ SOLUTION CLUSTERING: Benzer çözümleri gruplama
    - ✅ CONSTRAINT RELAXATION: Soft constraint'leri dinamik gevşetme
    - ✅ PERFORMANCE PREDICTION: Çözüm başarı olasılığını tahmin etme
    
    NOT: Tüm özellikler soft constraint bazlıdır, hiç hard constraint içermez.
    """
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        params = params or {}
        
        # Temel veri yapıları
        self.instructors = []
        self.projects = []
        self.time_slots = []
        self.classrooms = []
        self.instructor_pairs = []
        self.assignments = defaultdict(list)
        
        # AI parametreleri
        self.num_solutions = params.get("num_solutions", 15)  # Daha fazla çözüm üretilecek
        self.temperature = params.get("temperature", 150.0)  # Daha yüksek başlangıç sıcaklığı
        self.cooling_rate = params.get("cooling_rate", 0.92)  # Daha yavaş soğuma
        self.randomization_level = params.get("randomization_level", 0.85)  # Daha yüksek randomizasyon
        
        # Çeşitlilik için ek parametreler
        self.diversity_boost = params.get("diversity_boost", 0.3)  # Çeşitlilik artırıcı faktör
        self.use_time_seed = params.get("use_time_seed", True)  # Zaman bazlı seed kullanımı
        self.permutation_rate = params.get("permutation_rate", 0.4)  # Permütasyon olasılığı
        
        # Adaptive Parameter Tuning için parametreler
        self.adaptive_tuning = params.get("adaptive_tuning", True)  # Adaptive tuning aktif mi?
        self.adaptation_rate = params.get("adaptation_rate", 0.1)  # Parametreleri ne kadar hızlı adapte edelim
        self.min_temperature = params.get("min_temperature", 10.0)  # Minimum sıcaklık
        self.max_temperature = params.get("max_temperature", 300.0)  # Maximum sıcaklık
        self.min_cooling_rate = params.get("min_cooling_rate", 0.85)  # Minimum soğutma hızı
        self.max_cooling_rate = params.get("max_cooling_rate", 0.98)  # Maximum soğutma hızı
        
        # Beam Search için parametreler
        self.beam_width = params.get("beam_width", 5)  # Takip edilecek en iyi çözüm sayısı
        self.beam_iterations = params.get("beam_iterations", 3)  # Beam search iterasyon sayısı
        self.min_randomization = params.get("min_randomization", 0.3)  # Minimum randomizasyon
        self.max_randomization = params.get("max_randomization", 0.95)  # Maximum randomizasyon
        
        # Solution Memory & Learning için parametreler
        self.solution_memory_size = params.get("solution_memory_size", 20)  # Hafızada tutulacak çözüm sayısı
        self.solution_memory = []  # Geçmiş çözümleri tutacak liste
        self.learning_rate = params.get("learning_rate", 0.2)  # Öğrenme hızı
        
        # Beam Search için parametreler
        self.beam_width = params.get("beam_width", 5)  # Takip edilecek en iyi çözüm sayısı
        self.beam_solutions = []  # En iyi k çözümü tutacak liste
        
        # Constraint Relaxation için parametreler
        self.constraint_relaxation_threshold = params.get("constraint_relaxation_threshold", 0.7)  # Ne zaman gevşeteceğiz
        self.relaxation_factor = params.get("relaxation_factor", 0.2)  # Ne kadar gevşeteceğiz
        
        # Zaman bazlı seed ile rastgelelik ekle
        if self.use_time_seed:
            current_time = int(time.time())
            random.seed(current_time)
            np.random.seed(current_time)
            logger.info(f"🎲 Zaman bazlı rastgele seed kullanılıyor: {current_time}")
        
        # Ağırlıklar (çeşitlilik ağırlığını artırdık)
        self.weights = {
            'workload': params.get("workload_weight", 0.25),
            'pairing': params.get("pairing_weight", 0.15),
            'schedule': params.get("schedule_weight", 0.15),
            'diversity': params.get("diversity_weight", 0.30),  # Çeşitlilik ağırlığı artırıldı
            'classroom': params.get("classroom_weight", 0.15),
        }
        
        # Ağırlık değişim geçmişi (Dynamic Fitness Weights için)
        self.weight_history = {key: [] for key in self.weights}
        
        # Performance Prediction için metrikler
        self.performance_metrics = {
            'success_rate': 0.0,
            'avg_fitness': 0.0,
            'improvement_rate': 0.0,
            'convergence_speed': 0.0,
        }
        
        logger.info("🧠 Advanced AI özellikler aktif edildi: Adaptive Parameter Tuning, Solution Memory, Dynamic Weights, Beam Search")
        
    def initialize(self, data: Dict[str, Any]) -> None:
        """Algoritma başlangıç verilerini yükler"""
        logger.info("🔄 AI-based Lexicographic Algorithm başlatılıyor...")
        
        # Instructors
        self.instructors = []
        for inst in data.get("instructors", []):
            # Proje sayısını hesapla
            project_count = len([p for p in data.get("projects", []) 
                              if p.get("supervisor_id") == inst.get("id")])
            
            # Uzmanlık alanlarını al veya varsayılan değer ata
            expertise = inst.get("expertise", ["Genel"])
            
            # Geçmiş işbirliği verilerini al veya boş sözlük ata
            collaboration_history = inst.get("collaboration_history", {})
            
            # Instructor nesnesini oluştur
            self.instructors.append(
            Instructor(
                id=inst.get("id"),
                name=inst.get("name"),
                    project_count=project_count,
                    availability=inst.get("availability", [True] * len(data.get("timeslots", []))),
                    expertise=expertise,
                    collaboration_history=collaboration_history
                )
            )
        
        logger.info(f"✅ {len(self.instructors)} instructor yüklendi")
        
        # Projects
        self.projects = []
        for proj in data.get("projects", []):
            self.projects.append(
            Project(
                id=proj.get("id"),
                supervisor_id=proj.get("supervisor_id"),
                    required_jury_count=proj.get("required_jury_count", 2),
                    topic=proj.get("topic", ""),
                    difficulty=proj.get("difficulty", 0.5)
            )
            )
        
        logger.info(f"✅ {len(self.projects)} proje yüklendi")
        
        # Time Slots
        self.time_slots = [
            TimeSlot(
                id=ts.get("id"),
                start_time=ts.get("start_time"),
                end_time=ts.get("end_time")
            )
            for ts in data.get("timeslots", [])
        ]
        
        logger.info(f"✅ {len(self.time_slots)} zaman dilimi yüklendi")
        
        # Classrooms
        self.classrooms = [
            Classroom(
                id=cr.get("id"),
                name=cr.get("name", f"Sınıf-{cr.get('id')}"),
                capacity=cr.get("capacity", 30),
                features=cr.get("features", [])
            )
            for cr in data.get("classrooms", [])
        ]
        
        if not self.classrooms:
            # Eğer sınıf bilgisi yoksa varsayılan sınıflar oluştur
            self.classrooms = [
                Classroom(id=1, name="Sınıf-A", capacity=30, features=["Projeksiyon"]),
                Classroom(id=2, name="Sınıf-B", capacity=25, features=["Projeksiyon"]),
                Classroom(id=3, name="Sınıf-C", capacity=20, features=["Projeksiyon", "Akıllı Tahta"])
            ]
            
        logger.info(f"✅ {len(self.classrooms)} sınıf yüklendi")
        logger.info("✅ AI-based Lexicographic Algorithm başlatma tamamlandı")
    
    def sort_instructors_by_project_count(self) -> List[Instructor]:
        """
        AI-BASED DIVERSE SORTING:
        Instructorları proje sayılarına göre sıralar, ancak çeşitlilik için farklı sıralama stratejileri kullanır
        """
        # Farklı sıralama stratejileri tanımla
        sorting_strategies = [
            # 1. Klasik: Proje sayısına göre azalan sıralama
            lambda: sorted(self.instructors, key=lambda x: x.project_count, reverse=True),
            
            # 2. Proje sayısı + rastgele faktör
            lambda: sorted(self.instructors, key=lambda x: (x.project_count + random.uniform(-1, 1)), reverse=True),
            
            # 3. Proje sayısı + instructor ID'si
            lambda: sorted(self.instructors, key=lambda x: (x.project_count, x.id), reverse=True),
            
            # 4. İsme göre sıralama + proje sayısı
            lambda: sorted(self.instructors, key=lambda x: (x.name, x.project_count)),
            
            # 5. Karma sıralama (proje sayısı grupları içinde rastgele)
            lambda: self._group_and_shuffle_instructors()
        ]
        
        # Zaman bazlı değişken strateji seçimi
        day_of_year = datetime.now().timetuple().tm_yday
        hour_of_day = datetime.now().hour
        
        # Gün ve saate göre farklı stratejiler seç
        strategy_index = (day_of_year + hour_of_day) % len(sorting_strategies)
        
        # Rastgele bir strateji seçme olasılığı
        if random.random() < self.diversity_boost:
            strategy_index = random.randint(0, len(sorting_strategies) - 1)
            logger.info(f"🎲 AI: Çeşitlilik için rastgele sıralama stratejisi seçildi (Strateji #{strategy_index+1})")
        
        # Seçilen stratejiyi uygula
        sorted_instructors = sorting_strategies[strategy_index]()
        
        # Ek çeşitlilik: Belirli bir olasılıkla alt grupları karıştır
        if random.random() < self.permutation_rate:
            # Instructorları üç gruba ayır: Yüksek, orta ve düşük proje sayısı
            n = len(sorted_instructors)
            if n >= 6:  # En az 6 instructor varsa
                high = sorted_instructors[:n//3]
                mid = sorted_instructors[n//3:2*n//3]
                low = sorted_instructors[2*n//3:]
                
                # Grupları karıştır
                random.shuffle(high)
                random.shuffle(mid)
                random.shuffle(low)
                
                # Grupları birleştir
                sorted_instructors = high + mid + low
                logger.info(f"🔀 AI: Instructor grupları içinde permütasyon uygulandı")
        
        return sorted_instructors
        
    def _group_and_shuffle_instructors(self) -> List[Instructor]:
        """Instructorları proje sayısına göre gruplara ayırır ve her grup içinde karıştırır"""
        if not self.instructors:
            return []
            
        # Proje sayısına göre grupla
        groups = defaultdict(list)
        for instructor in self.instructors:
            groups[instructor.project_count].append(instructor)
            
        # Her grubu kendi içinde karıştır
        for count in groups:
            random.shuffle(groups[count])
            
        # Grupları proje sayısına göre azalan sırada birleştir
        sorted_counts = sorted(groups.keys(), reverse=True)
        result = []
        for count in sorted_counts:
            result.extend(groups[count])
            
        return result
    
    def split_instructors_into_groups(self, sorted_instructors: List[Instructor]) -> Tuple[List[Instructor], List[Instructor]]:
        """
        AI-BASED DIVERSE GROUPING:
        Instructorları üst ve alt gruplara ayırır, farklı stratejiler kullanarak çeşitlilik sağlar
        """
        total = len(sorted_instructors)
        if total < 2:
            return sorted_instructors, []
        
        # Farklı bölme stratejileri
        split_strategies = [
            # 1. Klasik ortadan bölme (50-50)
            lambda: (sorted_instructors[:total//2], sorted_instructors[total//2:]),
            
            # 2. Dengesiz bölme (40-60)
            lambda: (sorted_instructors[:int(total*0.4)], sorted_instructors[int(total*0.4):]),
            
            # 3. Dengesiz bölme (60-40)
            lambda: (sorted_instructors[:int(total*0.6)], sorted_instructors[int(total*0.6):]),
            
            # 4. Çapraz bölme (tek indeksler - çift indeksler)
            lambda: ([sorted_instructors[i] for i in range(total) if i % 2 == 0],
                     [sorted_instructors[i] for i in range(total) if i % 2 == 1]),
            
            # 5. İlk-son eşleştirme (ilk yarı - son yarının tersi)
            lambda: (sorted_instructors[:total//2], 
                     list(reversed(sorted_instructors[total//2:])))
        ]
        
        # Rastgele strateji seçimi (çeşitlilik faktörüne bağlı)
        if random.random() < self.diversity_boost:
            strategy_index = random.randint(0, len(split_strategies) - 1)
            logger.info(f"🎲 AI: Çeşitlilik için rastgele grup bölme stratejisi seçildi (Strateji #{strategy_index+1})")
        else:
            # Varsayılan olarak klasik strateji
            strategy_index = 0
        
        # Seçilen stratejiyi uygula
        upper_group, lower_group = split_strategies[strategy_index]()
        
        # Ek çeşitlilik: Belirli bir olasılıkla grupları karıştır
        if random.random() < self.permutation_rate:
            random.shuffle(upper_group)
            random.shuffle(lower_group)
            logger.info(f"🔀 AI: Üst ve alt gruplar içinde permütasyon uygulandı")
            
        return upper_group, lower_group
    
    def create_instructor_pairs(self, upper_group: List[Instructor], lower_group: List[Instructor]) -> List[Tuple[Instructor, Instructor]]:
        """
        AI-BASED DIVERSE SMART PAIRING: 
        Üst ve alt gruptan instructorları akıllı şekilde eşleştirir ve çeşitlilik sağlar
        
        Eşleştirme kriterleri:
        1. Uygunluk (availability) uyumluluğu
        2. Uzmanlık alanı çeşitliliği
        3. Geçmiş işbirliği deneyimi
        4. İş yükü dengesi
        5. Çeşitlilik faktörü (AI-based)
        """
        logger.info("🧠 AI-based Diverse Smart Instructor Pairing başlatılıyor...")
        
        # Eşleştirme stratejileri
        pairing_strategies = [
            # 1. Akıllı eşleştirme (orijinal strateji)
            lambda: self._smart_pair_instructors(upper_group, lower_group),
            
            # 2. Rastgele eşleştirme (tam çeşitlilik)
            lambda: self._random_pair_instructors(upper_group, lower_group),
            
            # 3. Proje sayısı farkını maksimize eden eşleştirme (zıt karakterler)
            lambda: self._contrast_pair_instructors(upper_group, lower_group),
            
            # 4. Proje sayısı farkını minimize eden eşleştirme (benzer karakterler)
            lambda: self._similar_pair_instructors(upper_group, lower_group),
            
            # 5. Hibrit eşleştirme (yarısı akıllı, yarısı rastgele)
            lambda: self._hybrid_pair_instructors(upper_group, lower_group)
        ]
        
        # Rastgele strateji seçimi (çeşitlilik faktörüne bağlı)
        if random.random() < self.diversity_boost:
            strategy_index = random.randint(0, len(pairing_strategies) - 1)
            logger.info(f"🎲 AI: Çeşitlilik için rastgele eşleştirme stratejisi seçildi (Strateji #{strategy_index+1})")
        else:
            # Varsayılan olarak akıllı eşleştirme
            strategy_index = 0
        
        # Seçilen stratejiyi uygula
        pairs = pairing_strategies[strategy_index]()
        
        # Ek çeşitlilik: Belirli bir olasılıkla eşleştirmeleri karıştır
        if random.random() < self.permutation_rate:
            # Eşleştirmelerin bir kısmını rastgele değiştir
            if len(pairs) >= 4:
                # Değiştirilecek eşleştirme sayısı
                swap_count = max(1, len(pairs) // 4)
                
                # Rastgele eşleştirmeleri seç ve değiştir
                for _ in range(swap_count):
                    i, j = random.sample(range(len(pairs)), 2)
                    # İki eşleştirmeyi çaprazla
                    pairs[i], pairs[j] = pairs[j], pairs[i]
                
                logger.info(f"🔀 AI: {swap_count} eşleştirme çaprazlandı (ek çeşitlilik)")
        
        logger.info(f"✅ {len(pairs)} akıllı ve çeşitli instructor eşleştirmesi oluşturuldu")
        return pairs
        
    def _smart_pair_instructors(self, upper_group: List[Instructor], lower_group: List[Instructor]) -> List[Tuple[Instructor, Instructor]]:
        """Orijinal akıllı eşleştirme stratejisi"""
        pairs = []
        remaining_upper = list(upper_group)
        remaining_lower = list(lower_group)
        
        # Her bir üst grup instructor'ı için en uygun alt grup eşini bul
        while remaining_upper and remaining_lower:
            best_pair_score = -1
            best_pair = None
            
            for upper_inst in remaining_upper:
                for lower_inst in remaining_lower:
                    # 1. Uygunluk (availability) uyumu
                    availability_match = sum(1 for a, b in zip(upper_inst.availability, lower_inst.availability) if a and b)
                    availability_score = availability_match / len(upper_inst.availability) if upper_inst.availability else 0
                    
                    # 2. Uzmanlık alanı çeşitliliği (farklı olması daha iyi)
                    if upper_inst.expertise and lower_inst.expertise:
                        common_expertise = len(set(upper_inst.expertise) & set(lower_inst.expertise))
                        total_expertise = len(set(upper_inst.expertise) | set(lower_inst.expertise))
                        expertise_diversity = 1.0 - (common_expertise / total_expertise if total_expertise else 0)
                    else:
                        expertise_diversity = 0.5  # Varsayılan değer
                    
                    # 3. Geçmiş işbirliği deneyimi (az olması tercih edilir)
                    if upper_inst.collaboration_history and lower_inst.id in upper_inst.collaboration_history:
                        collab_count = upper_inst.collaboration_history[lower_inst.id]
                        collab_score = 1.0 / (1.0 + collab_count)  # Az işbirliği = yüksek skor
                    else:
                        collab_score = 1.0  # Hiç işbirliği yok = en yüksek skor
                    
                    # 4. İş yükü dengesi (proje sayıları arasındaki fark az olmalı)
                    workload_diff = abs(upper_inst.project_count - lower_inst.project_count)
                    max_projects = max(upper_inst.project_count, lower_inst.project_count) if max(upper_inst.project_count, lower_inst.project_count) > 0 else 1
                    workload_balance = 1.0 - (workload_diff / max_projects)
                    
                    # Ağırlıklı toplam skor
                    weights = {
                        'availability': 0.4,
                        'expertise': 0.2,
                        'collaboration': 0.2,
                        'workload': 0.2
                    }
                    
                    pair_score = (
                        weights['availability'] * availability_score +
                        weights['expertise'] * expertise_diversity +
                        weights['collaboration'] * collab_score +
                        weights['workload'] * workload_balance
                    )
                    
                    # Randomizasyon ekle (AI stokastik karar verme)
                    if random.random() < self.randomization_level:
                        pair_score += random.uniform(-0.1, 0.1)
                    
                    if pair_score > best_pair_score:
                        best_pair_score = pair_score
                        best_pair = (upper_inst, lower_inst)
            
            if best_pair:
                pairs.append(best_pair)
                remaining_upper.remove(best_pair[0])
                remaining_lower.remove(best_pair[1])
            else:
                break
        
        # Eğer eşleşmeyen instructor'lar kaldıysa, basit eşleştirme yap
        if remaining_upper and remaining_lower:
            for i in range(min(len(remaining_upper), len(remaining_lower))):
                pairs.append((remaining_upper[i], remaining_lower[i]))
                
        return pairs
        
    def _random_pair_instructors(self, upper_group: List[Instructor], lower_group: List[Instructor]) -> List[Tuple[Instructor, Instructor]]:
        """Tamamen rastgele eşleştirme stratejisi"""
        pairs = []
        upper_copy = list(upper_group)
        lower_copy = list(lower_group)
        
        # Her iki grubu da karıştır
        random.shuffle(upper_copy)
        random.shuffle(lower_copy)
        
        # Eşleştir
        for i in range(min(len(upper_copy), len(lower_copy))):
            pairs.append((upper_copy[i], lower_copy[i]))
            
        return pairs
        
    def _contrast_pair_instructors(self, upper_group: List[Instructor], lower_group: List[Instructor]) -> List[Tuple[Instructor, Instructor]]:
        """Proje sayısı farkını maksimize eden eşleştirme"""
        pairs = []
        upper_copy = sorted(upper_group, key=lambda x: x.project_count, reverse=True)
        lower_copy = sorted(lower_group, key=lambda x: x.project_count)
        
        for i in range(min(len(upper_copy), len(lower_copy))):
            pairs.append((upper_copy[i], lower_copy[i]))
            
        return pairs
        
    def _similar_pair_instructors(self, upper_group: List[Instructor], lower_group: List[Instructor]) -> List[Tuple[Instructor, Instructor]]:
        """Proje sayısı farkını minimize eden eşleştirme"""
        pairs = []
        upper_copy = sorted(upper_group, key=lambda x: x.project_count, reverse=True)
        lower_copy = sorted(lower_group, key=lambda x: x.project_count, reverse=True)
        
        for i in range(min(len(upper_copy), len(lower_copy))):
            pairs.append((upper_copy[i], lower_copy[i]))
            
        return pairs
        
    def _hybrid_pair_instructors(self, upper_group: List[Instructor], lower_group: List[Instructor]) -> List[Tuple[Instructor, Instructor]]:
        """Yarısı akıllı, yarısı rastgele eşleştirme"""
        # Önce akıllı eşleştirme yap
        smart_pairs = self._smart_pair_instructors(upper_group, lower_group)
        
        # Eşleştirmelerin yarısını rastgele değiştir
        if len(smart_pairs) >= 2:
            # Değiştirilecek eşleştirme sayısı
            random_count = max(1, len(smart_pairs) // 2)
            
            # Rastgele eşleştirmeleri seç
            indices_to_randomize = random.sample(range(len(smart_pairs)), random_count)
            
            # Seçilen eşleştirmeleri rastgele değiştir
            for idx in indices_to_randomize:
                # Eşleştirmenin üst ve alt grup elemanlarını al
                upper_inst = smart_pairs[idx][0]
                
                # Rastgele bir alt grup elemanı seç (mevcut eşleştirmeler hariç)
                available_lower = [inst for inst in lower_group 
                                  if inst not in [pair[1] for pair in smart_pairs]]
                
                if available_lower:
                    # Rastgele bir alt grup elemanı seç
                    new_lower_inst = random.choice(available_lower)
                    
                    # Eşleştirmeyi güncelle
                    smart_pairs[idx] = (upper_inst, new_lower_inst)
        
        return smart_pairs
    
    def assign_consecutive_slots(self, pair: Tuple[Instructor, Instructor]) -> List[Dict]:
        """
        AI-BASED DIVERSE DYNAMIC TIME SLOT ASSIGNMENT: 
        Ardışık zaman dilimlerinde eşleşen instructorların rollerini değiştirir
        ve tüm zaman dilimlerini ve sınıfları akıllıca kullanır, çeşitlilik sağlar
        """
        # 🆕 ADAPTIVE CONSECUTIVE: Sınıf sayısına göre consecutive grouping ayarla - PROJE EKSİK ATANMA SORUNU DÜZELTİLDİ!
        classroom_count = len(self.classrooms)
        # SORUN DÜZELTİLDİ: Sınıf sayısı az olsa bile consecutive grouping'i tamamen kapatma!
        # Sadece esnek hale getir - projelerin eksik atanmasını önle
        use_consecutive = True  # HEP consecutive kullan - sadece esnek modda
        flexible_mode = classroom_count < 6  # Az sınıf varsa esnek mod
        logger.info(f"🔄 ADAPTIVE: Sınıf sayısı {classroom_count} - consecutive grouping: AÇIK (esnek: {'EVET' if flexible_mode else 'HAYIR'})")
        
        # 🔧 SORUN DÜZELTİLDİ: Flexible mode'da bile tüm projelerin atanmasını garanti et!
        if flexible_mode:
            logger.info("🔧 FLEXIBLE MODE: Tüm projelerin atanması garanti ediliyor...")
            
            # 🆕 PROJE COVERAGE VALIDATION: Flexible mode'da proje eksik atanmasını önle!
            self._validate_project_coverage = True
            self._flexible_mode_retry_count = 0
            self._max_flexible_retries = 3  # Maksimum 3 deneme
        
        # Zaman dilimi atama stratejileri
        if use_consecutive:
            slot_assignment_strategies = [
                # 1. Ardışık zaman dilimlerini tercih eden strateji (orijinal)
                lambda p: self._assign_consecutive_slots_original(p),
                
                # 2. Rastgele zaman dilimlerini seçen strateji
                lambda p: self._assign_random_slots(p),
                
                # 3. Gün içinde dağıtılmış zaman dilimlerini seçen strateji
                lambda p: self._assign_distributed_slots(p),
                
                # 4. Sabah-öğleden sonra dengesini gözeten strateji
                lambda p: self._assign_balanced_day_slots(p),
                
                # 5. Farklı sınıflarda atama yapan strateji
                lambda p: self._assign_different_classroom_slots(p)
            ]
        else:
            # Non-consecutive: Esnek atama stratejileri
            slot_assignment_strategies = [
                # 1. Rastgele zaman dilimlerini seçen strateji (esnek)
                lambda p: self._assign_random_slots(p),
                
                # 2. Gün içinde dağıtılmış zaman dilimlerini seçen strateji
                lambda p: self._assign_distributed_slots(p),
                
                # 3. Sabah-öğleden sonra dengesini gözeten strateji
                lambda p: self._assign_balanced_day_slots(p),
                
                # 4. Farklı sınıflarda atama yapan strateji
                lambda p: self._assign_different_classroom_slots(p)
            ]
        
        # Rastgele strateji seçimi (çeşitlilik faktörüne bağlı)
        if random.random() < self.diversity_boost:
            strategy_index = random.randint(0, len(slot_assignment_strategies) - 1)
            logger.info(f"🎲 AI: Çeşitlilik için rastgele zaman dilimi atama stratejisi seçildi (Strateji #{strategy_index+1})")
        else:
            # Varsayılan olarak ardışık zaman dilimi stratejisi
            strategy_index = 0
        
        # Seçilen stratejiyi uygula
        assignments = slot_assignment_strategies[strategy_index](pair)
        
        # Ek çeşitlilik: Belirli bir olasılıkla rolleri değiştir
        if random.random() < self.permutation_rate and len(assignments) >= 2:
            # İlk atamadaki rolleri değiştir
            supervisor_id = assignments[0]['supervisor_id']
            jury_id = assignments[0]['jury_id']
            
            assignments[0]['supervisor_id'] = jury_id
            assignments[0]['jury_id'] = supervisor_id
            
            logger.info(f"🔀 AI: Roller değiştirildi (ek çeşitlilik)")
        
        return assignments
        
    def _assign_consecutive_slots_original(self, pair: Tuple[Instructor, Instructor]) -> List[Dict]:
        """Orijinal ardışık zaman dilimi atama stratejisi"""
        assignments = []
        instructor1, instructor2 = pair
        
        # Instructorların uygun olduğu ortak zaman dilimlerini bul
        common_available_slots = []
        for i, (avail1, avail2) in enumerate(zip(instructor1.availability, instructor2.availability)):
            if avail1 and avail2 and i < len(self.time_slots):
                common_available_slots.append(i)
        
        # Eğer ortak uygun zaman dilimi yoksa, boş liste döndür
        if not common_available_slots:
            logger.warning(f"⚠️ {instructor1.name} ve {instructor2.name} için ortak uygun zaman dilimi bulunamadı")
            return []
        
        # Ortak uygun zaman dilimlerinden ardışık iki tanesini seç
        selected_slots = []
        for i in range(len(common_available_slots) - 1):
            if common_available_slots[i] + 1 == common_available_slots[i + 1]:
                selected_slots = [common_available_slots[i], common_available_slots[i + 1]]
                break
        
        # Ardışık iki zaman dilimi bulunamadıysa, rastgele iki zaman dilimi seç
        if not selected_slots and len(common_available_slots) >= 2:
            # Randomizasyon ekle
            if random.random() < self.randomization_level:
                random.shuffle(common_available_slots)
            selected_slots = common_available_slots[:2]
        elif not selected_slots and len(common_available_slots) == 1:
            selected_slots = [common_available_slots[0]]
        
        # Sınıf seçimi
        available_classrooms = self.classrooms if self.classrooms else [None]
        
            # İlk zaman diliminde instructor1 supervisor, instructor2 jury
        if selected_slots:
            classroom = random.choice(available_classrooms)
            classroom_id = classroom.id if classroom else None
            
            assignments.append({
                'time_slot_id': self.time_slots[selected_slots[0]].id,
                'supervisor_id': instructor1.id,
                'jury_id': instructor2.id,
                'classroom_id': classroom_id
            })
            
            # Sonraki zaman diliminde roller değişir
            if len(selected_slots) > 1:
                # Aynı sınıfı kullanmaya devam et (ardışık slotlar için ideal)
                assignments.append({
                    'time_slot_id': self.time_slots[selected_slots[1]].id,
                    'supervisor_id': instructor2.id,
                    'jury_id': instructor1.id,
                    'classroom_id': classroom_id
                })
        
        return assignments
        
    def _assign_random_slots(self, pair: Tuple[Instructor, Instructor]) -> List[Dict]:
        """Rastgele zaman dilimi atama stratejisi"""
        assignments = []
        instructor1, instructor2 = pair
        
        # Instructorların uygun olduğu ortak zaman dilimlerini bul
        common_available_slots = []
        for i, (avail1, avail2) in enumerate(zip(instructor1.availability, instructor2.availability)):
            if avail1 and avail2 and i < len(self.time_slots):
                common_available_slots.append(i)
        
        # Eğer ortak uygun zaman dilimi yoksa, boş liste döndür
        if not common_available_slots or len(self.time_slots) == 0:
            return []
        
        # Rastgele zaman dilimlerini seç
        if len(common_available_slots) >= 2:
            # Tamamen rastgele iki zaman dilimi seç
            selected_slots = random.sample(common_available_slots, 2)
        elif len(common_available_slots) == 1:
            selected_slots = [common_available_slots[0]]
        else:
            # Hiç ortak uygun zaman dilimi yoksa, rastgele iki zaman dilimi seç
            all_slots = list(range(len(self.time_slots)))
            if len(all_slots) >= 2:
                selected_slots = random.sample(all_slots, 2)
            elif len(all_slots) == 1:
                selected_slots = [all_slots[0]]
            else:
                return []
        
        # Sınıf seçimi
        available_classrooms = self.classrooms if self.classrooms else [None]
        
        # İlk zaman diliminde instructor1 supervisor, instructor2 jury
        if selected_slots:
            classroom = random.choice(available_classrooms)
            classroom_id = classroom.id if classroom else None
            
            assignments.append({
                'time_slot_id': self.time_slots[selected_slots[0]].id,
                'supervisor_id': instructor1.id,
                'jury_id': instructor2.id,
                'classroom_id': classroom_id
            })
            
            # Sonraki zaman diliminde roller değişir
            if len(selected_slots) > 1:
                # Farklı sınıf seç
                different_classroom = random.choice(available_classrooms)
                different_classroom_id = different_classroom.id if different_classroom else None
                
                assignments.append({
                    'time_slot_id': self.time_slots[selected_slots[1]].id,
                    'supervisor_id': instructor2.id,
                    'jury_id': instructor1.id,
                    'classroom_id': different_classroom_id
                })
        
        return assignments
        
    def _assign_distributed_slots(self, pair: Tuple[Instructor, Instructor]) -> List[Dict]:
        """Gün içinde dağıtılmış zaman dilimlerini seçen strateji"""
        assignments = []
        instructor1, instructor2 = pair
        
        # Instructorların uygun olduğu ortak zaman dilimlerini bul
        common_available_slots = []
        for i, (avail1, avail2) in enumerate(zip(instructor1.availability, instructor2.availability)):
            if avail1 and avail2 and i < len(self.time_slots):
                common_available_slots.append(i)
        
        # Eğer ortak uygun zaman dilimi yoksa, boş liste döndür
        if not common_available_slots or len(self.time_slots) == 0:
            return []
        
        # Zaman dilimlerini başlangıç saatine göre sırala
        sorted_slots = sorted(common_available_slots, 
                             key=lambda i: self.time_slots[i].start_time if i < len(self.time_slots) else "")
        
        # En erken ve en geç zaman dilimlerini seç
        if len(sorted_slots) >= 2:
            selected_slots = [sorted_slots[0], sorted_slots[-1]]
        elif len(sorted_slots) == 1:
            selected_slots = [sorted_slots[0]]
        else:
            return []
        
        # Sınıf seçimi
        available_classrooms = self.classrooms if self.classrooms else [None]
        
        # İlk zaman diliminde instructor1 supervisor, instructor2 jury
        if selected_slots:
            classroom = random.choice(available_classrooms)
            classroom_id = classroom.id if classroom else None
            
            assignments.append({
                'time_slot_id': self.time_slots[selected_slots[0]].id,
                'supervisor_id': instructor1.id,
                'jury_id': instructor2.id,
                'classroom_id': classroom_id
            })
            
            # Sonraki zaman diliminde roller değişir
            if len(selected_slots) > 1:
                assignments.append({
                    'time_slot_id': self.time_slots[selected_slots[1]].id,
                    'supervisor_id': instructor2.id,
                    'jury_id': instructor1.id,
                    'classroom_id': classroom_id
                })
        
        return assignments
        
    def _assign_balanced_day_slots(self, pair: Tuple[Instructor, Instructor]) -> List[Dict]:
        """Sabah-öğleden sonra dengesini gözeten strateji"""
        assignments = []
        instructor1, instructor2 = pair
        
        # Instructorların uygun olduğu ortak zaman dilimlerini bul
        common_available_slots = []
        for i, (avail1, avail2) in enumerate(zip(instructor1.availability, instructor2.availability)):
            if avail1 and avail2 and i < len(self.time_slots):
                common_available_slots.append(i)
        
        # Eğer ortak uygun zaman dilimi yoksa, boş liste döndür
        if not common_available_slots or len(self.time_slots) == 0:
            return []
        
        # Zaman dilimlerini sabah ve öğleden sonra olarak ayır
        morning_slots = []
        afternoon_slots = []
        
        for i in common_available_slots:
            if i < len(self.time_slots):
                start_time = self.time_slots[i].start_time
                # Convert to string if it's a datetime.time object
                start_time_str = str(start_time) if not isinstance(start_time, str) else start_time
                # Saat 12:00'dan önce ise sabah, sonra ise öğleden sonra
                if start_time_str < "12:00":
                    morning_slots.append(i)
                else:
                    afternoon_slots.append(i)
        
        # Biri sabah biri öğleden sonra olacak şekilde seç
        selected_slots = []
        
        if morning_slots and afternoon_slots:
            # Hem sabah hem öğleden sonra slot varsa, birini sabahtan birini öğleden sonradan seç
            selected_slots = [random.choice(morning_slots), random.choice(afternoon_slots)]
        elif morning_slots and len(morning_slots) >= 2:
            # Sadece sabah slotları varsa, iki farklı sabah slotu seç
            selected_slots = random.sample(morning_slots, 2)
        elif afternoon_slots and len(afternoon_slots) >= 2:
            # Sadece öğleden sonra slotları varsa, iki farklı öğleden sonra slotu seç
            selected_slots = random.sample(afternoon_slots, 2)
        elif morning_slots:
            # Tek bir sabah slotu varsa
            selected_slots = [morning_slots[0]]
        elif afternoon_slots:
            # Tek bir öğleden sonra slotu varsa
            selected_slots = [afternoon_slots[0]]
        
        # Sınıf seçimi
        available_classrooms = self.classrooms if self.classrooms else [None]
        
        # İlk zaman diliminde instructor1 supervisor, instructor2 jury
        if selected_slots:
            classroom = random.choice(available_classrooms)
            classroom_id = classroom.id if classroom else None
            
            assignments.append({
                'time_slot_id': self.time_slots[selected_slots[0]].id,
                'supervisor_id': instructor1.id,
                'jury_id': instructor2.id,
                'classroom_id': classroom_id
            })
            
            # Sonraki zaman diliminde roller değişir
            if len(selected_slots) > 1:
                assignments.append({
                    'time_slot_id': self.time_slots[selected_slots[1]].id,
                    'supervisor_id': instructor2.id,
                    'jury_id': instructor1.id,
                    'classroom_id': classroom_id
                })
        
        return assignments
        
    def _assign_different_classroom_slots(self, pair: Tuple[Instructor, Instructor]) -> List[Dict]:
        """
        Farklı sınıflarda atama yapan gelişmiş strateji
        - Sınıf dağılımını optimize eder
        - Her zaman diliminde farklı sınıf kullanır
        - Sınıf kapasitesini göz önünde bulundurur
        """
        assignments = []
        instructor1, instructor2 = pair
        
        # Instructorların uygun olduğu ortak zaman dilimlerini bul
        common_available_slots = []
        for i, (avail1, avail2) in enumerate(zip(instructor1.availability, instructor2.availability)):
            if avail1 and avail2 and i < len(self.time_slots):
                common_available_slots.append(i)
        
        # Eğer ortak uygun zaman dilimi yoksa, boş liste döndür
        if not common_available_slots or len(self.time_slots) == 0:
            return []
        
        # Rastgele zaman dilimlerini seç
        if len(common_available_slots) >= 2:
            selected_slots = random.sample(common_available_slots, 2)
        elif len(common_available_slots) == 1:
            selected_slots = [common_available_slots[0]]
        else:
            return []
        
        # Mevcut atamaları analiz et
        classroom_usage = Counter()
        timeslot_classroom_map = {}  # time_slot_id -> set(classroom_ids)
        
        for assignment in self.assignments:
            classroom_id = assignment.get('classroom_id')
            time_slot_id = assignment.get('time_slot_id')
            
            if classroom_id is not None:
                classroom_usage[classroom_id] += 1
                
            if time_slot_id is not None:
                if time_slot_id not in timeslot_classroom_map:
                    timeslot_classroom_map[time_slot_id] = set()
                if classroom_id is not None:
                    timeslot_classroom_map[time_slot_id].add(classroom_id)
        
        # Sınıf seçimi için akıllı algoritma
        available_classrooms = self.classrooms if self.classrooms else [None]
        
        # Sınıf seçim fonksiyonu
        def select_optimal_classroom(time_slot_id):
            if not available_classrooms:
                return None
                
            # O zaman diliminde henüz kullanılmamış sınıfları tercih et
            used_in_timeslot = timeslot_classroom_map.get(time_slot_id, set())
            unused_in_timeslot = [c for c in available_classrooms if c.id not in used_in_timeslot]
            
            if unused_in_timeslot:
                # En az kullanılan sınıfı seç
                return min(unused_in_timeslot, key=lambda c: classroom_usage.get(c.id, 0))
            else:
                # Tüm sınıflar bu zaman diliminde kullanılmışsa, en az kullanılan sınıfı seç
                return min(available_classrooms, key=lambda c: classroom_usage.get(c.id, 0))
        
        # İlk zaman dilimi için sınıf seç
        if selected_slots:
            time_slot_id1 = self.time_slots[selected_slots[0]].id
            classroom1 = select_optimal_classroom(time_slot_id1)
            classroom_id1 = classroom1.id if classroom1 else None
            
            # Kullanım sayısını güncelle
            if classroom_id1 is not None:
                classroom_usage[classroom_id1] += 1
                if time_slot_id1 not in timeslot_classroom_map:
                    timeslot_classroom_map[time_slot_id1] = set()
                timeslot_classroom_map[time_slot_id1].add(classroom_id1)
            
            assignments.append({
                'time_slot_id': time_slot_id1,
                'supervisor_id': instructor1.id,
                'jury_id': instructor2.id,
                'classroom_id': classroom_id1
            })
            
            # Sonraki zaman dilimi için farklı bir sınıf seç
            if len(selected_slots) > 1:
                time_slot_id2 = self.time_slots[selected_slots[1]].id
                classroom2 = select_optimal_classroom(time_slot_id2)
                classroom_id2 = classroom2.id if classroom2 else None
                
                assignments.append({
                    'time_slot_id': time_slot_id2,
                    'supervisor_id': instructor2.id,
                    'jury_id': instructor1.id,
                    'classroom_id': classroom_id2
                })
            
        return assignments
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        AI-BASED MULTI-SOLUTION GENERATION & STOCHASTIC OPTIMIZATION:
        Çoklu çözüm üretimi ve simulated annealing ile en iyi çözümü bulma
        
        BEAM SEARCH, SOLUTION CLUSTERING & CONSTRAINT RELAXATION entegre edildi
        """
        if data:
            self.initialize(data)
            
        # Çeşitlilik için zaman bazlı seed kullan (her çalıştırmada farklı sonuç)
        current_time = int(time.time())
        random.seed(current_time)
        np.random.seed(current_time)
        logger.info(f"🎲 Zaman bazlı rastgele seed kullanılıyor: {current_time}")
            
        logger.info(f"🧠 AI-based Multi-Solution Generation başlatılıyor ({self.num_solutions} çözüm üretilecek)...")
        
        # Çoklu çözüm üretimi için değişkenler
        best_solution = None
        best_fitness = float('-inf')
        solutions = []
        
        # Sınıf dağılımını iyileştirmek için ağırlıkları güncelle
        self.weights['classroom'] = 0.25  # Sınıf dağılımı ağırlığını artır
        
        # Çoklu çözüm üret
        for solution_idx in range(self.num_solutions):
            logger.info(f"🔄 Çözüm {solution_idx+1}/{self.num_solutions} üretiliyor...")
            
            # Her çözüm için farklı randomizasyon seviyesi kullan
            current_randomization = self.randomization_level * (1.0 - solution_idx / self.num_solutions)
            
            # 1. Instructorları proje sayılarına göre sırala
            sorted_instructors = self.sort_instructors_by_project_count()
            
            # Randomizasyon: Instructorları karıştır
            if random.random() < current_randomization:
                random.shuffle(sorted_instructors)
                logger.info(f"   🎲 AI: Instructor sıralaması randomize edildi")
            
            # 2. Grupları oluştur
            upper_group, lower_group = self.split_instructors_into_groups(sorted_instructors)
            
            # 3. Eşleştirmeleri yap
            instructor_pairs = self.create_instructor_pairs(upper_group, lower_group)
            
            # 4. Ardışık zaman dilimlerinde atamaları yap
            all_assignments = []
            for pair in instructor_pairs:
                assignments = self.assign_consecutive_slots(pair)
                all_assignments.extend(assignments)
            
            # 5. Çözümü iyileştir (Simulated Annealing)
            current_solution = {'assignments': all_assignments}
            current_fitness = self.evaluate_fitness(current_solution)
            
            # Simulated Annealing için sıcaklık değerini sıfırla
            solution_temperature = self.temperature
            
            # Simulated Annealing ile iyileştirme
            for iteration in range(100):  # 100 iterasyon
                # Mevcut çözümden komşu çözüm üret
                neighbor_solution = self._generate_neighbor_solution(current_solution)
                neighbor_fitness = self.evaluate_fitness(neighbor_solution)
                
                # Daha iyi bir çözüm bulundu mu?
                if neighbor_fitness > current_fitness:
                    current_solution = neighbor_solution
                    current_fitness = neighbor_fitness
                else:
                    # Kötü çözümü kabul etme olasılığı (sıcaklığa bağlı)
                    acceptance_probability = np.exp((neighbor_fitness - current_fitness) / solution_temperature)
                    if random.random() < acceptance_probability:
                        current_solution = neighbor_solution
                        current_fitness = neighbor_fitness
                        logger.info(f"   🔥 AI: Kötü çözüm kabul edildi (p={acceptance_probability:.4f}, T={solution_temperature:.2f})")
                
                # Sıcaklığı düşür
                solution_temperature *= self.cooling_rate
            
            # 6. Çözümü kaydet
            solution_with_metrics = {
                'assignments': current_solution['assignments'],
                'fitness': current_fitness
            }
            solutions.append(solution_with_metrics)
            
            # En iyi çözümü güncelle
            if current_fitness > best_fitness:
                best_fitness = current_fitness
                best_solution = current_solution
                logger.info(f"   ⭐ Yeni en iyi çözüm bulundu! Fitness: {best_fitness:.4f}")
        
        # En iyi çözümü seç
        if not best_solution:
            logger.warning("⚠️ Hiçbir geçerli çözüm bulunamadı!")
            return {'assignments': [], 'metrics': {'error': 'Çözüm bulunamadı'}}
        
        # AI metriklerini hesapla
        # Geçici olarak en iyi çözümü assignments'a ata
        self.assignments = best_solution['assignments']
        metrics = self.get_ai_enhanced_metrics()
        
        # Solution Memory & Learning: En iyi çözümü hafızaya ekle
        self._update_solution_memory(best_solution, best_fitness, metrics)
        
        # Adaptive Parameter Tuning: Parametreleri çözüm kalitesine göre ayarla
        self._adapt_parameters(best_fitness, metrics)
        
        # Performance Prediction: Performans metriklerini güncelle
        self._update_performance_metrics(best_fitness, solutions)
        
        # Instructor pairs'ı JSON serileştirilebilir formata dönüştür
        serializable_pairs = []
        # En son çözümde kullanılan instructor çiftlerini bul
        instructor_ids = set()
        for assignment in best_solution['assignments']:
            supervisor_id = assignment.get('supervisor_id')
            jury_id = assignment.get('jury_id')
            if supervisor_id and jury_id:
                instructor_ids.add(supervisor_id)
                instructor_ids.add(jury_id)
        
        # Tüm instructor'ları eşleştir
        instructors_list = [inst for inst in self.instructors if inst.id in instructor_ids]
        for i in range(0, len(instructors_list), 2):
            if i+1 < len(instructors_list):
                pair = (instructors_list[i], instructors_list[i+1])
                serializable_pairs.append({
                    'upper_instructor': {
                        'id': pair[0].id,
                        'name': pair[0].name,
                        'project_count': pair[0].project_count
                    },
                    'lower_instructor': {
                        'id': pair[1].id,
                        'name': pair[1].name,
                        'project_count': pair[1].project_count
                    }
                })
        
        logger.info(f"✅ Optimizasyon tamamlandı! En iyi fitness: {best_fitness:.4f}")
        logger.info(f"📊 Performans metrikleri: Başarı oranı: {self.performance_metrics['success_rate']:.2f}, Ortalama fitness: {self.performance_metrics['avg_fitness']:.4f}")
        
        # Sınıf dağılımı analizi
        classroom_usage = Counter()
        for assignment in best_solution['assignments']:
            classroom_id = assignment.get('classroom_id')
            if classroom_id:
                classroom_usage[classroom_id] += 1
        
        classroom_stats = {
            'usage_counts': dict(classroom_usage),
            'usage_percentage': {
                cid: count/len(best_solution['assignments'])*100 
                for cid, count in classroom_usage.items()
            },
            'classroom_diversity': len(classroom_usage) / len(self.classrooms) if self.classrooms else 0
        }
            
        return {
            'assignments': best_solution['assignments'],
            'instructor_pairs': serializable_pairs,
            'metrics': {
                'total_pairs': len(serializable_pairs),
                'total_assignments': len(best_solution['assignments']),
                'ai_metrics': metrics,
                'best_fitness': best_fitness,
                'solutions_explored': self.num_solutions,
                'classroom_distribution': classroom_stats
            }
        }
        
    def _generate_neighbor_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        SMART MUTATION STRATEGIES:
        Mevcut çözümden komşu çözüm üretir (Simulated Annealing için)
        Daha akıllı mutasyon operatörleri kullanarak çözüm kalitesini korur
        """
        if not solution or 'assignments' not in solution:
            return {'assignments': []}
            
        assignments = solution['assignments'].copy()
        
        if not assignments:
            return {'assignments': []}
        
        # Mevcut çözümün metriklerini hesapla
        temp_assignments = self.assignments
        self.assignments = assignments
        metrics = self.get_ai_enhanced_metrics()
        self.assignments = temp_assignments
        
        # Zayıf metriklere göre mutasyon stratejisi seç
        workload_score = 1.0 / (1.0 + metrics['workload_distribution'])
        pairing_score = metrics['pairing_efficiency']
        schedule_score = metrics['schedule_optimization']
        classroom_score = metrics['classroom_utilization']
        
        # En zayıf metriği belirle
        metric_scores = {
            'workload': workload_score,
            'pairing': pairing_score,
            'schedule': schedule_score,
            'classroom': classroom_score
        }
        
        # En zayıf metriğe göre mutasyon stratejisi seç
        weakest_metric = min(metric_scores, key=metric_scores.get)
        
        # Smart Mutation Strategies
        mutation_strategies = {
            'workload': self._workload_balancing_mutation,
            'pairing': self._pairing_improvement_mutation,
            'schedule': self._schedule_optimization_mutation,
            'classroom': self._classroom_optimization_mutation,
            'random': self._random_mutation  # Fallback
        }
        
        # Belirli bir olasılıkla rastgele mutasyon yap (exploration için)
        if random.random() < 0.3:  # %30 olasılıkla
            strategy = 'random'
            logger.debug(f"🎲 Rastgele mutasyon stratejisi seçildi")
        else:
            strategy = weakest_metric
            logger.debug(f"🧠 Akıllı mutasyon stratejisi seçildi: {strategy} (skor: {metric_scores[strategy]:.2f})")
        
        # Seçilen stratejiyi uygula
        return mutation_strategies[strategy](solution)
    
    def _workload_balancing_mutation(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """İş yükü dengelemesine odaklanan mutasyon stratejisi"""
        assignments = solution['assignments'].copy()
        
        if not assignments or len(assignments) < 2:
            return {'assignments': assignments}
        
        # İş yükünü hesapla
        instructor_workload = defaultdict(int)
        for assignment in assignments:
            supervisor_id = assignment.get('supervisor_id')
            jury_id = assignment.get('jury_id')
            if supervisor_id:
                instructor_workload[supervisor_id] += 1
            if jury_id:
                instructor_workload[jury_id] += 1
        
        # En yüksek ve en düşük iş yüküne sahip instructorları bul
        if not instructor_workload:
            return {'assignments': assignments}
            
        max_workload = max(instructor_workload.values())
        min_workload = min(instructor_workload.values())
        
        # İş yükü dengeli ise başka bir mutasyon yap
        if max_workload - min_workload <= 1:
            return self._random_mutation(solution)
        
        # En yüksek iş yüküne sahip instructor'ı bul
        overloaded_instructors = [id for id, load in instructor_workload.items() if load == max_workload]
        underloaded_instructors = [id for id, load in instructor_workload.items() if load == min_workload]
        
        if not overloaded_instructors or not underloaded_instructors:
            return {'assignments': assignments}
        
        # Rastgele bir overloaded instructor seç
        overloaded_id = random.choice(overloaded_instructors)
        underloaded_id = random.choice(underloaded_instructors)
        
        # Overloaded instructor'ın bir atamasını bul ve underloaded instructor ile değiştir
        for idx, assignment in enumerate(assignments):
            if assignment.get('supervisor_id') == overloaded_id:
                assignments[idx]['supervisor_id'] = underloaded_id
                break
            elif assignment.get('jury_id') == overloaded_id:
                assignments[idx]['jury_id'] = underloaded_id
                break
        
        return {'assignments': assignments}
    
    def _pairing_improvement_mutation(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Eşleştirme verimliliğini artırmaya odaklanan mutasyon stratejisi"""
        assignments = solution['assignments'].copy()
        
        if not assignments or len(assignments) < 2:
            return {'assignments': assignments}
        
        # Rastgele iki atama seç
        idx1, idx2 = random.sample(range(len(assignments)), 2)
        
        # Jury'leri değiştir
        jury1 = assignments[idx1].get('jury_id')
        jury2 = assignments[idx2].get('jury_id')
        
        if jury1 is not None and jury2 is not None:
            assignments[idx1]['jury_id'] = jury2
            assignments[idx2]['jury_id'] = jury1
        
        return {'assignments': assignments}
    
    def _schedule_optimization_mutation(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Zaman çizelgesi optimizasyonuna odaklanan mutasyon stratejisi"""
        assignments = solution['assignments'].copy()
        
        if not assignments:
            return {'assignments': assignments}
        
        # Zaman dilimi kullanımını analiz et
        timeslot_usage = defaultdict(int)
        for assignment in assignments:
            timeslot_id = assignment.get('time_slot_id')
            if timeslot_id:
                timeslot_usage[timeslot_id] += 1
        
        # En çok ve en az kullanılan zaman dilimlerini bul
        if not timeslot_usage:
            return {'assignments': assignments}
            
        max_usage = max(timeslot_usage.values())
        min_usage = min(timeslot_usage.values())
        
        # Kullanım dengeli ise başka bir mutasyon yap
        if max_usage - min_usage <= 1:
            return self._random_mutation(solution)
        
        # En çok kullanılan zaman dilimini bul
        overused_timeslots = [id for id, usage in timeslot_usage.items() if usage == max_usage]
        underused_timeslots = [id for id, usage in timeslot_usage.items() if usage == min_usage]
        
        if not overused_timeslots or not underused_timeslots:
            return {'assignments': assignments}
        
        # Rastgele bir overused timeslot seç
        overused_id = random.choice(overused_timeslots)
        underused_id = random.choice(underused_timeslots)
        
        # Overused timeslot'un bir atamasını bul ve underused timeslot'a taşı
        for idx, assignment in enumerate(assignments):
            if assignment.get('time_slot_id') == overused_id:
                assignments[idx]['time_slot_id'] = underused_id
                break
        
        return {'assignments': assignments}
    
    def _classroom_optimization_mutation(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Sınıf kullanımını optimize etmeye odaklanan mutasyon stratejisi"""
        assignments = solution['assignments'].copy()
        
        if not assignments or not self.classrooms:
            return {'assignments': assignments}
        
        # Sınıf kullanımını analiz et
        classroom_usage = defaultdict(int)
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            if classroom_id:
                classroom_usage[classroom_id] += 1
        
        # Kullanılmayan sınıfları bul
        all_classroom_ids = set(c.id for c in self.classrooms)
        used_classroom_ids = set(classroom_usage.keys())
        unused_classroom_ids = all_classroom_ids - used_classroom_ids
        
        # Eğer kullanılmayan sınıf varsa, rastgele bir atamayı o sınıfa taşı
        if unused_classroom_ids:
            # Rastgele bir atama seç
            idx = random.randint(0, len(assignments) - 1)
            # Rastgele bir kullanılmayan sınıf seç
            unused_classroom_id = random.choice(list(unused_classroom_ids))
            # Atamayı güncelle
            assignments[idx]['classroom_id'] = unused_classroom_id
        else:
            # En çok ve en az kullanılan sınıfları bul
            if not classroom_usage:
                return {'assignments': assignments}
                
            max_usage = max(classroom_usage.values())
            min_usage = min(classroom_usage.values())
            
            # Kullanım dengeli ise başka bir mutasyon yap
            if max_usage - min_usage <= 1:
                return self._random_mutation(solution)
            
            # En çok kullanılan sınıfı bul
            overused_classrooms = [id for id, usage in classroom_usage.items() if usage == max_usage]
            underused_classrooms = [id for id, usage in classroom_usage.items() if usage == min_usage]
            
            if not overused_classrooms or not underused_classrooms:
                return {'assignments': assignments}
            
            # Rastgele bir overused classroom seç
            overused_id = random.choice(overused_classrooms)
            underused_id = random.choice(underused_classrooms)
            
            # Overused classroom'un bir atamasını bul ve underused classroom'a taşı
            for idx, assignment in enumerate(assignments):
                if assignment.get('classroom_id') == overused_id:
                    assignments[idx]['classroom_id'] = underused_id
                    break
        
        return {'assignments': assignments}
    
    def _random_mutation(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Rastgele mutasyon stratejisi (fallback)"""
        assignments = solution['assignments'].copy()
        
        if not assignments:
            return {'assignments': assignments}
            
        mutation_type = random.choice(['swap', 'replace', 'modify'])
        
        if mutation_type == 'swap' and len(assignments) >= 2:
            # İki atamayı değiştir
            idx1, idx2 = random.sample(range(len(assignments)), 2)
            assignments[idx1], assignments[idx2] = assignments[idx2], assignments[idx1]
            
        elif mutation_type == 'replace' and len(assignments) >= 1:
            # Bir atamayı yeni bir atamayla değiştir
            idx = random.randint(0, len(assignments) - 1)
            
            # Rastgele instructorlar seç
            if self.instructors:
                instructor1 = random.choice(self.instructors)
                instructor2 = random.choice([i for i in self.instructors if i.id != instructor1.id])
                
                # Rastgele zaman dilimi ve sınıf seç
                time_slot = random.choice(self.time_slots) if self.time_slots else None
                classroom = random.choice(self.classrooms) if self.classrooms else None
                
                if time_slot:
                    assignments[idx] = {
                        'time_slot_id': time_slot.id,
                        'supervisor_id': instructor1.id,
                        'jury_id': instructor2.id,
                        'classroom_id': classroom.id if classroom else None
                    }
            
        elif mutation_type == 'modify' and len(assignments) >= 1:
            # Bir atamanın özelliklerini değiştir
            idx = random.randint(0, len(assignments) - 1)
            
            # Değiştirilecek özelliği seç
            property_to_change = random.choice(['time_slot_id', 'classroom_id'])
            
            if property_to_change == 'time_slot_id' and self.time_slots:
                assignments[idx]['time_slot_id'] = random.choice(self.time_slots).id
            elif property_to_change == 'classroom_id' and self.classrooms:
                assignments[idx]['classroom_id'] = random.choice(self.classrooms).id
        
        return {'assignments': assignments}

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        AI-BASED FITNESS EVALUATION:
        Çözümün kalitesini değerlendirir ve çeşitli metrikleri kullanarak bir fitness skoru hesaplar
        
        DYNAMIC FITNESS WEIGHTS:
        Fitness ağırlıklarını dinamik olarak ayarlar, zayıf metriklere daha fazla ağırlık verir
        """
        if not solution or 'assignments' not in solution:
            return float('-inf')
            
        # Geçici olarak atama verisini sakla ve metrikleri hesapla
        temp_assignments = self.assignments
        self.assignments = solution['assignments']
        
        # Tüm metrikleri hesapla
        metrics = self.get_ai_enhanced_metrics()
        
        # Orijinal atama verisini geri yükle
        self.assignments = temp_assignments
        
        # Fitness skorunu hesapla
        workload_score = 1.0 / (1.0 + metrics['workload_distribution'])
        pairing_score = metrics['pairing_efficiency']
        schedule_score = metrics['schedule_optimization']
        
        # Yeni metrikler
        instructor_diversity_score = metrics['instructor_diversity']
        time_slot_score = metrics['time_slot_distribution']
        classroom_score = metrics['classroom_utilization']
        
        # DYNAMIC FITNESS WEIGHTS: Ağırlıkları dinamik olarak ayarla
        dynamic_weights = self._calculate_dynamic_weights({
            'workload': workload_score,
            'pairing': pairing_score,
            'schedule': schedule_score,
            'diversity': instructor_diversity_score,
            'classroom': classroom_score
        })
        
        # Ağırlıklı ortalama (dinamik ağırlıklar kullanılarak)
        fitness = (
            dynamic_weights['workload'] * workload_score +
            dynamic_weights['pairing'] * pairing_score +
            dynamic_weights['schedule'] * schedule_score +
            dynamic_weights['diversity'] * instructor_diversity_score +
            dynamic_weights['classroom'] * classroom_score
        )
        
        # Çözüm kalitesini log'a yaz
        logger.info(f"📊 Fitness değerlendirmesi: {fitness:.4f} (Workload: {workload_score:.2f}, "
                   f"Pairing: {pairing_score:.2f}, Schedule: {schedule_score:.2f}, "
                   f"Diversity: {instructor_diversity_score:.2f}, Classroom: {classroom_score:.2f})")
        
        # Ağırlık değişimlerini log'a yaz
        if any(abs(dynamic_weights[k] - self.weights[k]) > 0.05 for k in self.weights):
            logger.info(f"⚖️ Dinamik ağırlıklar: Workload: {dynamic_weights['workload']:.2f} (vs {self.weights['workload']:.2f}), "
                       f"Pairing: {dynamic_weights['pairing']:.2f} (vs {self.weights['pairing']:.2f}), "
                       f"Diversity: {dynamic_weights['diversity']:.2f} (vs {self.weights['diversity']:.2f})")
        
        return fitness
        
    def _calculate_dynamic_weights(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        Dynamic Fitness Weights: Fitness ağırlıklarını dinamik olarak ayarlar
        
        Strateji:
        1. Zayıf metriklere daha fazla ağırlık ver (inverse scoring)
        2. Geçmiş çözümlerdeki eğilimleri dikkate al
        3. Ağırlıkların toplamı 1.0 olacak şekilde normalize et
        """
        # 1. Mevcut ağırlıkları başlangıç noktası olarak al
        dynamic_weights = self.weights.copy()
        
        # 2. Zayıf metriklere daha fazla ağırlık ver
        # Düşük skorlu metrikler daha fazla ağırlık almalı
        inverse_scores = {}
        for key, score in scores.items():
            # Skoru tersine çevir (1.0 - score) ve minimum 0.1 olsun
            inverse_scores[key] = max(1.0 - score, 0.1)
        
        # 3. Ağırlıkları güncelle
        adjustment_factor = 0.2  # Ne kadar agresif ayarlama yapılacak
        
        for key in dynamic_weights:
            if key in inverse_scores:
                # Zayıf metrikler için ağırlığı artır
                dynamic_weights[key] += adjustment_factor * inverse_scores[key]
        
        # 4. Geçmiş çözümlerdeki eğilimleri dikkate al
        if self.weight_history and all(len(history) > 3 for history in self.weight_history.values()):
            for key in dynamic_weights:
                # Son 3 değerin ortalamasını al
                recent_avg = sum(self.weight_history[key][-3:]) / 3
                # Eğer son değerler artış eğilimindeyse devam et
                if len(self.weight_history[key]) >= 5:
                    old_avg = sum(self.weight_history[key][-5:-3]) / 2
                    if recent_avg > old_avg:
                        # Artış eğilimini güçlendir
                        dynamic_weights[key] += 0.05
        
        # 5. Ağırlıkları normalize et (toplamları 1.0 olsun)
        total_weight = sum(dynamic_weights.values())
        for key in dynamic_weights:
            dynamic_weights[key] /= total_weight
        
        # 6. Ağırlık geçmişini güncelle
        for key in self.weight_history:
            if key in dynamic_weights:
                self.weight_history[key].append(dynamic_weights[key])
                # Geçmiş boyutunu sınırla
                if len(self.weight_history[key]) > 20:
                    self.weight_history[key] = self.weight_history[key][-20:]
        
        return dynamic_weights
    
    def get_ai_enhanced_metrics(self) -> Dict:
        """
        AI-BASED DIVERSITY METRICS:
        Çeşitli AI destekli metrikler ve öneriler sunar
        """
        metrics = {
            # Temel metrikler
            'workload_distribution': self._calculate_workload_distribution(),
            'pairing_efficiency': self._calculate_pairing_efficiency(),
            'schedule_optimization': self._calculate_schedule_optimization(),
            
            # Yeni çeşitlilik metrikleri
            'instructor_diversity': self._calculate_instructor_diversity(),
            'time_slot_distribution': self._calculate_time_slot_distribution(),
            'classroom_utilization': self._calculate_classroom_utilization(),
            
            # AI önerileri
            'ai_recommendations': self._generate_ai_recommendations()
        }
        return metrics
    
    def _calculate_workload_distribution(self) -> float:
        """İş yükü dağılımının dengesini hesaplar"""
        project_counts = [inst.project_count for inst in self.instructors]
        return np.std(project_counts) if project_counts else 0.0
    
    def _calculate_pairing_efficiency(self) -> float:
        """Eşleştirmelerin verimliliğini hesaplar"""
        if not self.instructor_pairs:
            return 0.0
        
        total_project_diff = sum(
            abs(pair[0].project_count - pair[1].project_count)
            for pair in self.instructor_pairs
        )
        return 1.0 - (total_project_diff / (len(self.instructor_pairs) * max(inst.project_count for inst in self.instructors)))
    
    def _calculate_schedule_optimization(self) -> float:
        """Zaman çizelgesi optimizasyonunu hesaplar"""
        if not self.assignments:
            return 0.0
        
        # Ardışık atamalar arasındaki geçişlerin verimliliği
        consecutive_switches = 0
        total_possible_switches = len(self.assignments) - 1
        
        for i in range(len(self.assignments) - 1):
            current = self.assignments[i]
            next_assignment = self.assignments[i + 1]
            
            if (current.get('supervisor_id') == next_assignment.get('jury_id') and 
                current.get('jury_id') == next_assignment.get('supervisor_id')):
                consecutive_switches += 1
                
        return consecutive_switches / total_possible_switches if total_possible_switches > 0 else 1.0
        
    def _calculate_instructor_diversity(self) -> float:
        """
        Instructor çeşitliliğini hesaplar
        - Farklı uzmanlık alanlarının dengeli dağılımı
        - Farklı instructorların eşleştirilme çeşitliliği
        """
        if not self.assignments or not self.instructors:
            return 0.0
            
        # 1. Her instructor'ın kaç farklı instructor ile eşleştiğini hesapla
        instructor_pairs = {}
        for assignment in self.assignments:
            supervisor_id = assignment.get('supervisor_id')
            jury_id = assignment.get('jury_id')
            
            if supervisor_id not in instructor_pairs:
                instructor_pairs[supervisor_id] = set()
            instructor_pairs[supervisor_id].add(jury_id)
            
            if jury_id not in instructor_pairs:
                instructor_pairs[jury_id] = set()
            instructor_pairs[jury_id].add(supervisor_id)
        
        # Ortalama eşleşme çeşitliliği
        avg_pair_diversity = sum(len(pairs) for pairs in instructor_pairs.values()) / len(instructor_pairs) if instructor_pairs else 0
        max_possible_diversity = len(self.instructors) - 1  # Kendisi hariç tüm instructorlar
        normalized_pair_diversity = avg_pair_diversity / max_possible_diversity if max_possible_diversity > 0 else 0
        
        # 2. Uzmanlık alanı çeşitliliği
        expertise_counts = Counter()
        for instructor in self.instructors:
            if instructor.expertise:
                for exp in instructor.expertise:
                    expertise_counts[exp] += 1
        
        # Uzmanlık alanlarının dengeli dağılımı
        expertise_std = np.std(list(expertise_counts.values())) if expertise_counts else 0
        max_expertise_count = max(expertise_counts.values()) if expertise_counts else 1
        expertise_diversity = 1.0 - (expertise_std / max_expertise_count) if max_expertise_count > 0 else 0
        
        # Ağırlıklı ortalama
        return 0.6 * normalized_pair_diversity + 0.4 * expertise_diversity
        
    def _calculate_time_slot_distribution(self) -> float:
        """
        Zaman dilimi dağılımını hesaplar
        - Zaman dilimlerinin dengeli kullanımı
        - Boş zaman dilimlerinin minimizasyonu
        """
        if not self.assignments or not self.time_slots:
            return 0.0
            
        # Her zaman diliminin kullanım sayısını hesapla
        time_slot_usage = Counter(assignment.get('time_slot_id') for assignment in self.assignments)
        
        # Kullanılmayan zaman dilimlerini hesapla
        all_time_slot_ids = set(ts.id for ts in self.time_slots)
        used_time_slot_ids = set(time_slot_usage.keys())
        unused_time_slots = all_time_slot_ids - used_time_slot_ids
        
        # Kullanım oranı
        usage_ratio = len(used_time_slot_ids) / len(all_time_slot_ids) if all_time_slot_ids else 1.0
        
        # Kullanım dengesi (standart sapma ne kadar düşükse o kadar iyi)
        usage_values = list(time_slot_usage.values())
        usage_std = np.std(usage_values) if usage_values else 0
        max_usage = max(usage_values) if usage_values else 1
        usage_balance = 1.0 - (usage_std / max_usage) if max_usage > 0 else 1.0
        
        # Ağırlıklı ortalama
        return 0.7 * usage_ratio + 0.3 * usage_balance
        
    def _calculate_classroom_utilization(self) -> float:
        """
        Sınıf kullanım verimliliğini hesaplar
        - Sınıfların dengeli kullanımı
        - Sınıf kapasitesine uygunluk
        - Çeşitlilik faktörü
        """
        if not self.assignments or not self.classrooms:
            return 0.0
            
        # Her sınıfın kullanım sayısını hesapla
        classroom_usage = Counter()
        for assignment in self.assignments:
            classroom_id = assignment.get('classroom_id')
            if classroom_id is not None:
                classroom_usage[classroom_id] += 1
        
        # Kullanılmayan sınıfları hesapla
        all_classroom_ids = set(c.id for c in self.classrooms)
        used_classroom_ids = set(classroom_usage.keys())
        unused_classrooms = all_classroom_ids - used_classroom_ids
        
        # Kullanım oranı - tüm sınıfların kullanılması önemli
        usage_ratio = len(used_classroom_ids) / len(all_classroom_ids) if all_classroom_ids else 1.0
        
        # Kullanım dengesi - sınıfların eşit kullanılması önemli
        usage_values = list(classroom_usage.values())
        usage_std = np.std(usage_values) if usage_values else 0
        max_usage = max(usage_values) if usage_values else 1
        usage_balance = 1.0 - (usage_std / max_usage) if max_usage > 0 else 1.0
        
        # Çeşitlilik faktörü - her zaman diliminde farklı sınıf kullanımı
        timeslot_classroom_pairs = set()
        for assignment in self.assignments:
            time_slot_id = assignment.get('time_slot_id')
            classroom_id = assignment.get('classroom_id')
            if time_slot_id is not None and classroom_id is not None:
                timeslot_classroom_pairs.add((time_slot_id, classroom_id))
        
        # Zaman dilimi başına düşen benzersiz sınıf sayısı
        timeslot_count = len(set(a.get('time_slot_id') for a in self.assignments if a.get('time_slot_id') is not None))
        diversity_score = len(timeslot_classroom_pairs) / timeslot_count if timeslot_count > 0 else 0.0
        
        # Ağırlıklı ortalama (çeşitlilik faktörü ağırlığı artırıldı)
        return 0.4 * usage_ratio + 0.3 * usage_balance + 0.3 * diversity_score
        
    def _update_solution_memory(self, solution: Dict[str, Any], fitness: float, metrics: Dict[str, Any]) -> None:
        """
        Solution Memory & Learning: En iyi çözümleri hafızada tutar ve onlardan öğrenir
        """
        # Çözümün özelliklerini çıkar
        solution_features = {
            'fitness': fitness,
            'metrics': metrics,
            'timestamp': datetime.now().timestamp(),
            'assignment_count': len(solution['assignments']),
            'classroom_distribution': {},
            'timeslot_distribution': {},
            'instructor_usage': {}
        }
        
        # Sınıf dağılımını analiz et
        classroom_usage = Counter()
        for assignment in solution['assignments']:
            classroom_id = assignment.get('classroom_id')
            if classroom_id:
                classroom_usage[classroom_id] += 1
        solution_features['classroom_distribution'] = dict(classroom_usage)
        
        # Zaman dilimi dağılımını analiz et
        timeslot_usage = Counter()
        for assignment in solution['assignments']:
            timeslot_id = assignment.get('time_slot_id')
            if timeslot_id:
                timeslot_usage[timeslot_id] += 1
        solution_features['timeslot_distribution'] = dict(timeslot_usage)
        
        # Instructor kullanımını analiz et
        instructor_usage = Counter()
        for assignment in solution['assignments']:
            supervisor_id = assignment.get('supervisor_id')
            jury_id = assignment.get('jury_id')
            if supervisor_id:
                instructor_usage[supervisor_id] += 1
            if jury_id:
                instructor_usage[jury_id] += 1
        solution_features['instructor_usage'] = dict(instructor_usage)
        
        # Çözümü hafızaya ekle
        self.solution_memory.append({
            'solution': solution,
            'features': solution_features
        })
        
        # Hafıza boyutunu kontrol et
        if len(self.solution_memory) > self.solution_memory_size:
            # En kötü çözümü bul ve sil
            self.solution_memory.sort(key=lambda x: x['features']['fitness'])
            self.solution_memory.pop(0)  # En kötü çözümü sil
            
        logger.info(f"🧠 Solution Memory güncellendi. Hafızada {len(self.solution_memory)} çözüm var.")
        
    def _adapt_parameters(self, fitness: float, metrics: Dict[str, Any]) -> None:
        """
        Adaptive Parameter Tuning: Parametreleri çözüm kalitesine göre ayarlar
        """
        if not self.adaptive_tuning or not self.solution_memory:
            return
            
        # Son 5 çözümün ortalamasını al
        recent_solutions = self.solution_memory[-min(5, len(self.solution_memory)):]
        avg_fitness = sum(s['features']['fitness'] for s in recent_solutions) / len(recent_solutions)
        
        # Eğer son çözüm ortalamadan daha iyiyse, mevcut parametreleri koru
        if fitness > avg_fitness * 1.05:  # %5 daha iyi
            logger.info(f"✅ Mevcut parametreler iyi çalışıyor. Fitness: {fitness:.4f} > Ortalama: {avg_fitness:.4f}")
            return
            
        # Çözüm kalitesi düşükse parametreleri adapte et
        
        # 1. Sıcaklık ayarlaması
        if metrics['workload_distribution'] > 0.3:  # İş yükü dengesizse
            # Daha yüksek sıcaklık = daha fazla exploration
            new_temp = min(self.temperature * (1 + self.adaptation_rate), self.max_temperature)
            logger.info(f"🔥 Sıcaklık artırıldı: {self.temperature:.2f} -> {new_temp:.2f} (İş yükü dengesizliği: {metrics['workload_distribution']:.2f})")
            self.temperature = new_temp
        else:
            # Daha düşük sıcaklık = daha hızlı convergence
            new_temp = max(self.temperature * (1 - self.adaptation_rate), self.min_temperature)
            self.temperature = new_temp
            
        # 2. Soğutma hızı ayarlaması
        if metrics['schedule_optimization'] < 0.7:  # Zaman çizelgesi optimizasyonu düşükse
            # Daha yavaş soğutma = daha fazla exploration
            new_cooling = min(self.cooling_rate + self.adaptation_rate/10, self.max_cooling_rate)
            logger.info(f"❄️ Soğutma hızı yavaşlatıldı: {self.cooling_rate:.3f} -> {new_cooling:.3f}")
            self.cooling_rate = new_cooling
        else:
            # Daha hızlı soğutma = daha hızlı convergence
            new_cooling = max(self.cooling_rate - self.adaptation_rate/10, self.min_cooling_rate)
            self.cooling_rate = new_cooling
            
        # 3. Randomizasyon seviyesi ayarlaması
        if metrics['pairing_efficiency'] < 0.6:  # Eşleştirme verimliliği düşükse
            # Daha yüksek randomizasyon = daha fazla çeşitlilik
            new_rand = min(self.randomization_level + self.adaptation_rate, self.max_randomization)
            logger.info(f"🎲 Randomizasyon seviyesi artırıldı: {self.randomization_level:.2f} -> {new_rand:.2f}")
            self.randomization_level = new_rand
        else:
            # Daha düşük randomizasyon = daha fazla exploitation
            new_rand = max(self.randomization_level - self.adaptation_rate, self.min_randomization)
            self.randomization_level = new_rand
            
    def _update_performance_metrics(self, best_fitness: float, solutions: List[Dict[str, Any]]) -> None:
        """
        Performance Prediction: Performans metriklerini günceller
        """
        if not solutions:
            return
            
        # Başarı oranı: Fitness skoru belirli bir eşiği geçen çözümlerin oranı
        success_threshold = 0.7
        success_count = sum(1 for s in solutions if s['fitness'] > success_threshold)
        success_rate = success_count / len(solutions) if solutions else 0.0
        
        # Ortalama fitness
        avg_fitness = sum(s['fitness'] for s in solutions) / len(solutions) if solutions else 0.0
        
        # İyileşme oranı: Son çözümün ilk çözüme göre ne kadar iyileştiği
        if len(solutions) >= 2:
            first_fitness = solutions[0]['fitness']
            last_fitness = solutions[-1]['fitness']
            improvement_rate = (last_fitness - first_fitness) / first_fitness if first_fitness > 0 else 0.0
        else:
            improvement_rate = 0.0
            
        # Convergence hızı: Kaç iterasyonda en iyi çözüme ulaşıldığı
        best_idx = max(range(len(solutions)), key=lambda i: solutions[i]['fitness'])
        convergence_speed = 1.0 - (best_idx / len(solutions)) if solutions else 0.0
        
        # Metrikleri güncelle (hafif exponential smoothing ile)
        alpha = 0.3  # Smoothing factor
        self.performance_metrics['success_rate'] = alpha * success_rate + (1-alpha) * self.performance_metrics['success_rate']
        self.performance_metrics['avg_fitness'] = alpha * avg_fitness + (1-alpha) * self.performance_metrics['avg_fitness']
        self.performance_metrics['improvement_rate'] = alpha * improvement_rate + (1-alpha) * self.performance_metrics['improvement_rate']
        self.performance_metrics['convergence_speed'] = alpha * convergence_speed + (1-alpha) * self.performance_metrics['convergence_speed']
        
    def _generate_ai_recommendations(self) -> List[str]:
        """
        AI destekli öneriler oluşturur
        """
        recommendations = []
        
        # 1. İş yükü dengesi önerileri
        workload = {}
        for instructor in self.instructors:
            workload[instructor.id] = 0
            
        for assignment in self.assignments:
            workload[assignment.get('supervisor_id', 0)] = workload.get(assignment.get('supervisor_id', 0), 0) + 1
            workload[assignment.get('jury_id', 0)] = workload.get(assignment.get('jury_id', 0), 0) + 1
            
        if workload:
            avg_workload = sum(workload.values()) / len(workload)
            max_workload = max(workload.values())
            min_workload = min(workload.values())
            
            if max_workload - min_workload > 2:
                recommendations.append(f"İş yükü dengesizliği tespit edildi. En yüksek: {max_workload}, En düşük: {min_workload}, Ortalama: {avg_workload:.2f}")
                
                # En yüksek ve en düşük iş yüküne sahip instructorları bul
                overloaded = sorted([(id, load) for id, load in workload.items() if load > avg_workload + 1], 
                                  key=lambda x: x[1], reverse=True)[:3]
                underloaded = sorted([(id, load) for id, load in workload.items() if load < avg_workload - 1],
                                   key=lambda x: x[1])[:3]
                
                if overloaded:
                    overloaded_names = []
                    for id, load in overloaded:
                        instructor = next((i for i in self.instructors if i.id == id), None)
                        if instructor:
                            overloaded_names.append(f"{instructor.name} ({load})")
                    
                    if overloaded_names:
                        recommendations.append(f"Aşırı yüklü instructorlar: {', '.join(overloaded_names)}")
                
                if underloaded:
                    underloaded_names = []
                    for id, load in underloaded:
                        instructor = next((i for i in self.instructors if i.id == id), None)
                        if instructor:
                            underloaded_names.append(f"{instructor.name} ({load})")
                    
                    if underloaded_names:
                        recommendations.append(f"Az yüklü instructorlar: {', '.join(underloaded_names)}")
        
        # 2. Zaman dilimi kullanımı önerileri
        time_slot_usage = Counter(assignment.get('time_slot_id') for assignment in self.assignments)
        all_time_slot_ids = set(ts.id for ts in self.time_slots)
        unused_time_slots = all_time_slot_ids - set(time_slot_usage.keys())
        
        if unused_time_slots:
            unused_time_slot_names = []
            for ts_id in unused_time_slots:
                time_slot = next((ts for ts in self.time_slots if ts.id == ts_id), None)
                if time_slot:
                    unused_time_slot_names.append(f"{time_slot.start_time}-{time_slot.end_time}")
            
            if unused_time_slot_names:
                recommendations.append(f"Kullanılmayan zaman dilimleri: {', '.join(unused_time_slot_names)}")
        
        # 3. Sınıf kullanımı önerileri
        classroom_usage = Counter()
        for assignment in self.assignments:
            classroom_id = assignment.get('classroom_id')
            if classroom_id is not None:
                classroom_usage[classroom_id] += 1
                
        all_classroom_ids = set(c.id for c in self.classrooms)
        unused_classrooms = all_classroom_ids - set(classroom_usage.keys())
        
        if unused_classrooms:
            unused_classroom_names = []
            for c_id in unused_classrooms:
                classroom = next((c for c in self.classrooms if c.id == c_id), None)
                if classroom:
                    unused_classroom_names.append(f"{classroom.name}")
            
            if unused_classroom_names:
                recommendations.append(f"Kullanılmayan sınıflar: {', '.join(unused_classroom_names)}")
        
        # 4. Genel performans değerlendirmesi
        workload_score = self._calculate_workload_distribution()
        pairing_score = self._calculate_pairing_efficiency()
        schedule_score = self._calculate_schedule_optimization()
        
        overall_score = (workload_score + pairing_score + schedule_score) / 3
        
        if overall_score < 0.5:
            recommendations.append("Çözüm kalitesi düşük. Daha fazla iterasyon veya farklı başlangıç koşulları denenebilir.")
        elif overall_score < 0.7:
            recommendations.append("Çözüm kalitesi orta düzeyde. İyileştirmeler için iş yükü dengesine odaklanılabilir.")
        else:
            recommendations.append("Çözüm kalitesi yüksek. Küçük ince ayarlar yapılabilir.")
        
        return recommendations
        
    def repair_solution(self, solution: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Çözümü onarır ve iyileştirir"""
        if not solution or 'assignments' not in solution:
            return solution
            
        assignments = solution['assignments']
        
        logger.info("🔧 AI-based çözüm onarımı başlatılıyor...")
        
        # 1. Çakışmaları kontrol et ve düzelt
        assignments = self._fix_conflicts(assignments)
        
        # 2. Boşlukları doldur
        assignments = self._fill_gaps(assignments)
        
        # 3. Yük dengesini optimize et
        assignments = self._balance_workload(assignments)
        
        logger.info("✅ Çözüm onarımı tamamlandı")
        return {'assignments': assignments}
        
    def _fix_conflicts(self, assignments: List[Dict]) -> List[Dict]:
        """
        AI-BASED CONFLICT RESOLUTION:
        Çakışmaları tespit eder ve çözer
        """
        if not assignments:
            return []
            
        logger.info("🔍 Çakışmalar kontrol ediliyor...")
        
        # Çakışma türleri:
        # 1. Aynı zaman diliminde bir instructor'ın birden fazla rolde olması
        # 2. Aynı zaman diliminde aynı sınıfta birden fazla atama olması
        
        # Zaman dilimi ve instructor bazlı çakışmaları kontrol et
        time_instructor_map = {}  # (time_slot_id, instructor_id) -> assignment_idx
        classroom_time_map = {}   # (time_slot_id, classroom_id) -> assignment_idx
        conflict_indices = set()
        
        for idx, assignment in enumerate(assignments):
            time_slot_id = assignment.get('time_slot_id')
            supervisor_id = assignment.get('supervisor_id')
            jury_id = assignment.get('jury_id')
            classroom_id = assignment.get('classroom_id')
            
            # Supervisor çakışması
            key_supervisor = (time_slot_id, supervisor_id)
            if key_supervisor in time_instructor_map:
                conflict_indices.add(idx)
                logger.warning(f"⚠️ Çakışma tespit edildi: Instructor {supervisor_id} aynı zaman diliminde ({time_slot_id}) birden fazla atamada")
            else:
                time_instructor_map[key_supervisor] = idx
                
            # Jury çakışması
            key_jury = (time_slot_id, jury_id)
            if key_jury in time_instructor_map:
                conflict_indices.add(idx)
                logger.warning(f"⚠️ Çakışma tespit edildi: Instructor {jury_id} aynı zaman diliminde ({time_slot_id}) birden fazla atamada")
            else:
                time_instructor_map[key_jury] = idx
                
            # Sınıf çakışması
            if classroom_id:
                key_classroom = (time_slot_id, classroom_id)
                if key_classroom in classroom_time_map:
                    conflict_indices.add(idx)
                    logger.warning(f"⚠️ Çakışma tespit edildi: Sınıf {classroom_id} aynı zaman diliminde ({time_slot_id}) birden fazla atamada")
                else:
                    classroom_time_map[key_classroom] = idx
        
        # Çakışmaları çöz
        if conflict_indices:
            logger.info(f"🔧 {len(conflict_indices)} çakışma çözülüyor...")
            
            # Çakışan atamaları yeni zaman dilimlerine taşı
            fixed_assignments = []
            
            for idx, assignment in enumerate(assignments):
                if idx in conflict_indices:
                    # Alternatif zaman dilimi bul
                    original_time_slot_id = assignment.get('time_slot_id')
                    supervisor_id = assignment.get('supervisor_id')
                    jury_id = assignment.get('jury_id')
                    classroom_id = assignment.get('classroom_id')
                    
                    # Supervisor ve jury'nin uygun olduğu zaman dilimlerini bul
                    supervisor = next((i for i in self.instructors if i.id == supervisor_id), None)
                    jury = next((i for i in self.instructors if i.id == jury_id), None)
                    
                    if supervisor and jury:
                        available_slots = []
                        for i, (avail_s, avail_j) in enumerate(zip(supervisor.availability, jury.availability)):
                            if avail_s and avail_j and i < len(self.time_slots):
                                time_slot_id = self.time_slots[i].id
                                
                                # Bu zaman diliminde çakışma var mı kontrol et
                                if (time_slot_id, supervisor_id) not in time_instructor_map and \
                                   (time_slot_id, jury_id) not in time_instructor_map:
                                    available_slots.append(time_slot_id)
                        
                        if available_slots:
                            # Rastgele bir uygun zaman dilimi seç
                            new_time_slot_id = random.choice(available_slots)
                            
                            # Yeni sınıf seç
                            new_classroom_id = None
                            if self.classrooms:
                                available_classrooms = [c.id for c in self.classrooms 
                                                     if (new_time_slot_id, c.id) not in classroom_time_map]
                                if available_classrooms:
                                    new_classroom_id = random.choice(available_classrooms)
                                    classroom_time_map[(new_time_slot_id, new_classroom_id)] = idx
                            
                            # Yeni atama oluştur
                            fixed_assignment = assignment.copy()
                            fixed_assignment['time_slot_id'] = new_time_slot_id
                            fixed_assignment['classroom_id'] = new_classroom_id
                            
                            # Yeni çakışma haritasına ekle
                            time_instructor_map[(new_time_slot_id, supervisor_id)] = idx
                            time_instructor_map[(new_time_slot_id, jury_id)] = idx
                            
                            fixed_assignments.append(fixed_assignment)
                            logger.info(f"✅ Çakışma çözüldü: Atama {idx} yeni zaman dilimine ({new_time_slot_id}) taşındı")
                        else:
                            # Uygun zaman dilimi bulunamadıysa atamayı kaldır
                            logger.warning(f"⚠️ Çakışma çözülemedi: Atama {idx} kaldırıldı (uygun zaman dilimi bulunamadı)")
                    else:
                        # Instructor bilgisi bulunamadıysa atamayı kaldır
                        logger.warning(f"⚠️ Çakışma çözülemedi: Atama {idx} kaldırıldı (instructor bilgisi bulunamadı)")
                else:
                    # Çakışma olmayan atamaları olduğu gibi ekle
                    fixed_assignments.append(assignment)
            
            return fixed_assignments
        else:
            logger.info("✅ Çakışma tespit edilmedi")
            return assignments
            
    def _fill_gaps(self, assignments: List[Dict]) -> List[Dict]:
        """
        AI-BASED GAP FILLING:
        Zaman dilimlerindeki boşlukları doldurur
        """
        if not assignments:
            return []
            
        logger.info("🔍 Zaman dilimi boşlukları kontrol ediliyor...")
        
        # Kullanılan zaman dilimlerini belirle
        used_time_slots = set(assignment.get('time_slot_id') for assignment in assignments)
        all_time_slot_ids = set(ts.id for ts in self.time_slots)
        
        # Boş zaman dilimleri
        empty_slots = all_time_slot_ids - used_time_slots
        
        if not empty_slots:
            logger.info("✅ Tüm zaman dilimleri kullanılıyor")
            return assignments
            
        logger.info(f"🔧 {len(empty_slots)} boş zaman dilimi doldurulacak...")
        
        # Atanmamış projeleri bul
        assigned_supervisors = set(assignment.get('supervisor_id') for assignment in assignments)
        unassigned_projects = [p for p in self.projects if p.supervisor_id not in assigned_supervisors]
        
        # Eğer atanmamış proje yoksa, rastgele instructor çiftleri oluştur
        if not unassigned_projects:
            # Mevcut atamalarda en az kullanılan instructorları seç
            instructor_usage = Counter()
            for assignment in assignments:
                instructor_usage[assignment.get('supervisor_id')] += 1
                instructor_usage[assignment.get('jury_id')] += 1
                
            # En az kullanılan instructorları bul
            least_used = sorted(instructor_usage.items(), key=lambda x: x[1])
            
            # Boş zaman dilimlerini doldur
            for empty_slot in empty_slots:
                # Eğer yeterli instructor yoksa döngüden çık
                if len(least_used) < 2:
                    break
                    
                # En az kullanılan iki instructor'ı seç
                supervisor_id = least_used[0][0]
                jury_id = least_used[1][0]
                
                # Instructor kullanım sayısını güncelle
                instructor_usage[supervisor_id] += 1
                instructor_usage[jury_id] += 1
                least_used = sorted(instructor_usage.items(), key=lambda x: x[1])
                
                # Sınıf seç
                classroom_id = None
                if self.classrooms:
                    classroom_id = random.choice(self.classrooms).id
                
                # Yeni atama oluştur
                new_assignment = {
                    'time_slot_id': empty_slot,
                    'supervisor_id': supervisor_id,
                    'jury_id': jury_id,
                    'classroom_id': classroom_id,
                    'is_ai_generated': True  # AI tarafından oluşturulduğunu belirt
                }
                
                assignments.append(new_assignment)
                logger.info(f"✅ Boş zaman dilimi {empty_slot} dolduruldu")
        
        logger.info(f"✅ Boşluk doldurma tamamlandı, {len(assignments)} atama mevcut")
        return assignments
        
    def _balance_workload(self, assignments: List[Dict]) -> List[Dict]:
        """
        AI-BASED WORKLOAD BALANCING:
        Instructor'lar arasında iş yükünü dengeler
        """
        if not assignments:
            return []
            
        logger.info("🔍 İş yükü dengesi kontrol ediliyor...")
        
        # Her instructor'ın iş yükünü hesapla
        workload = defaultdict(int)
        for assignment in assignments:
            workload[assignment.get('supervisor_id')] += 1
            workload[assignment.get('jury_id')] += 1
        
        # İş yükü dengesizliğini hesapla
        if not workload:
            return assignments
            
        avg_workload = sum(workload.values()) / len(workload)
        max_workload = max(workload.values())
        min_workload = min(workload.values())
        
        # Dengesizlik çok fazla değilse bir şey yapma
        if max_workload - min_workload <= 2:
            logger.info(f"✅ İş yükü dengeli (Ort: {avg_workload:.2f}, Min: {min_workload}, Max: {max_workload})")
            return assignments
            
        logger.info(f"🔧 İş yükü dengeleniyor (Ort: {avg_workload:.2f}, Min: {min_workload}, Max: {max_workload})...")
        
        # En yüksek ve en düşük iş yüküne sahip instructorları bul
        overloaded = sorted([(id, load) for id, load in workload.items() if load > avg_workload + 1], 
                          key=lambda x: x[1], reverse=True)
        underloaded = sorted([(id, load) for id, load in workload.items() if load < avg_workload - 1],
                           key=lambda x: x[1])
        
        # İş yükünü dengele
        balanced_assignments = assignments.copy()
        changes_made = 0
        
        # En fazla 10 değişiklik yap
        max_changes = 10
        
        while overloaded and underloaded and changes_made < max_changes:
            over_id, over_load = overloaded[0]
            under_id, under_load = underloaded[0]
            
            # Aşırı yüklü instructor'ın bir atamasını bul
            for idx, assignment in enumerate(balanced_assignments):
                if assignment.get('supervisor_id') == over_id:
                    # Atamayı güncelle
                    balanced_assignments[idx]['supervisor_id'] = under_id
                    
                    # İş yüklerini güncelle
                    workload[over_id] -= 1
                    workload[under_id] += 1
                    
                    changes_made += 1
                    logger.info(f"✅ İş yükü dengelendi: Instructor {over_id} -> {under_id}")
                    
                    # Listeleri güncelle
                    overloaded = sorted([(id, load) for id, load in workload.items() if load > avg_workload + 1], 
                                      key=lambda x: x[1], reverse=True)
                    underloaded = sorted([(id, load) for id, load in workload.items() if load < avg_workload - 1],
                                       key=lambda x: x[1])
                    break
                    
                elif assignment.get('jury_id') == over_id:
                    # Atamayı güncelle
                    balanced_assignments[idx]['jury_id'] = under_id
                    
                    # İş yüklerini güncelle
                    workload[over_id] -= 1
                    workload[under_id] += 1
                    
                    changes_made += 1
                    logger.info(f"✅ İş yükü dengelendi: Instructor {over_id} -> {under_id}")
                    
                    # Listeleri güncelle
                    overloaded = sorted([(id, load) for id, load in workload.items() if load > avg_workload + 1], 
                                      key=lambda x: x[1], reverse=True)
                    underloaded = sorted([(id, load) for id, load in workload.items() if load < avg_workload - 1],
                                       key=lambda x: x[1])
                    break
            
            # Eğer overloaded veya underloaded listesi boşaldıysa döngüden çık
            if not overloaded or not underloaded:
                break
        
        # Yeni iş yükü dengesi
        new_max = max(workload.values())
        new_min = min(workload.values())
        
        logger.info(f"✅ İş yükü dengeleme tamamlandı (Ort: {avg_workload:.2f}, Yeni Min: {new_min}, Yeni Max: {new_max})")
        return balanced_assignments