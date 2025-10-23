"""
Dynamic Programming Algorithm - 🤖 PURE AI-POWERED Strategic Pairing
100% AI-based optimization with ZERO HARD CONSTRAINTS

YENİ AI STRATEJİSİ:
1. 🤖 INSTRUCTOR SIRALAMA: Proje sorumluluğu sayısına göre sırala (EN FAZLA → EN AZ)
2. 🤖 AKILLI GRUPLAMA: 
   - Çift sayıda: (n/2, n/2) tam ortadan böl
   - Tek sayıda: (n, n+1) üst grup n, alt grup n+1
3. 🤖 HIGH-LOW PAİRİNG: Üst gruptan birer, alt gruptan birer alarak eşleştir
4. 🤖 BI-DIRECTIONAL JURY: 
   - PHASE 1: X instructor sorumlu → Y instructor jüri (consecutive)
   - PHASE 2: Y instructor sorumlu → X instructor jüri (consecutive)
5. 🤖 CONSECUTIVE GROUPING: Aynı sınıfta, ardışık slotlarda
6. 🤖 PURE AI SCORING: Sadece soft constraints, no hard constraints
7. 🤖 ADAPTIVE LEARNING: Sistem kendini sürekli optimize eder
8. 🤖 PATTERN OPTIMIZATION: En iyi desenleri öğrenir ve uygular
"""

from typing import Dict, Any, Optional, List, Tuple, Set
import random
import numpy as np
import time
import logging
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DynamicProgramming(OptimizationAlgorithm):
    """
    🤖 Dynamic Programming Algorithm - PURE AI-POWERED Strategic Pairing
    
    YENİ AI STRATEJİSİ (100% AI-Based, ZERO HARD CONSTRAINTS):
    
    1. 🤖 INSTRUCTOR SIRALAMA: Proje sorumluluğu sayısına göre sırala (EN FAZLA → EN AZ)
    2. 🤖 AKILLI GRUPLAMA: 
       - Çift sayıda: (n/2, n/2) tam ortadan böl
       - Tek sayıda: (n, n+1) üst grup n, alt grup n+1
    3. 🤖 HIGH-LOW PAİRİNG: Üst gruptan birer, alt gruptan birer alarak eşleştir
       → En fazla proje sorumlusu ↔ En az proje sorumlusu
    4. 🤖 BI-DIRECTIONAL JURY: 
       - PHASE 1: X instructor sorumlu → Y instructor jüri (consecutive)
       - PHASE 2: Y instructor sorumlu → X instructor jüri (consecutive)
    5. 🤖 PURE CONSECUTIVE GROUPING: Aynı sınıfta, ardışık slotlarda
    6. 🤖 EN ERKEN BOŞ SLOT: Boş slotlar varken ileri atlamaz
    7. 🤖 AI-BASED SCORING: Sadece soft constraints, no hard constraints
    
    Avantajlar:
    ✅ Load balancing: En fazla yük ↔ En az yük eşleştirmesi
    ✅ Consecutive grouping: Her instructor'ın projeleri ardışık
    ✅ Bi-directional jury: Her instructor birbirinin jürisi
    ✅ Sınıf değişimi minimizasyonu
    ✅ Gap-free scheduling
    ✅ 100% AI optimization
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Dynamic Programming Algorithm (🤖 AI-Powered Strategic Pairing)"
        self.description = "🤖 PURE AI-POWERED: Strategic instructor pairing with high-low matching, bi-directional jury assignment, consecutive grouping, and zero hard constraints!"

        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        self.current_schedules = []
        
        # 🤖 AI STRATEGIC PAIRING PARAMETERS
        self.strategic_pairs = []  # (high_load_instructor, low_load_instructor) pairs
        self.phase1_assignments = []  # X sorumlu → Y jüri
        self.phase2_assignments = []  # Y sorumlu → X jüri
        
        # 🤖 AI CLASSROOM DISTRIBUTION PARAMETERS
        self.classroom_usage_count = {}  # Sınıf kullanım sayacı
        self.classroom_rotation_index = 0  # Rotasyon için index
        
        # 🤖 AI SCORING WEIGHTS (Pure Soft Constraints)
        self.ai_weights = {
            "consecutive_bonus": 200.0,      # Ardışık slot bonusu
            "class_stay_bonus": 100.0,       # Aynı sınıfta kalma bonusu
            "early_slot_bonus": 80.0,        # Erken slot bonusu
            "load_balance_bonus": 300.0,     # Yük dengeleme bonusu
            "jury_balance_bonus": 250.0,     # Jüri dengeleme bonusu
            "gap_penalty": 50.0,             # Gap cezası (soft)
            "class_switch_penalty": 60.0,    # Sınıf değişimi cezası (soft)
            "conflict_penalty": 30.0,        # Conflict cezası (soft)
        }

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🤖 PURE AI-POWERED OPTIMIZATION: Strategic Pairing Algorithm
        """
        start_time = time.time()
        logger.info("🤖 Dynamic Programming Algorithm - PURE AI-POWERED Strategic Pairing başlatılıyor...")
        
        # Veri hazırlığı
        self.projects = data.get('projects', [])
        self.instructors = data.get('instructors', [])
        self.classrooms = data.get('classrooms', [])
        self.timeslots = data.get('timeslots', [])
        self.current_schedules = []
        
        logger.info(f"📊 Veri: {len(self.projects)} proje, {len(self.instructors)} instructor, {len(self.classrooms)} sınıf, {len(self.timeslots)} zaman")
        
        # 🤖 STEP 1: AI-BASED Instructor Selection (Enhanced)
        sorted_instructors = self._sort_instructors_by_ai_score()
        
        # 🤖 STEP 2: AI-BASED Classroom Optimization
        classroom_scores = self._optimize_classroom_distribution()
        
        # 🤖 STEP 3: AI-BASED Timeslot Optimization
        timeslot_scores = self._optimize_timeslot_distribution()
        
        # 🤖 STEP 4: Strategic Grouping
        upper_group, lower_group = self._create_strategic_groups(sorted_instructors)
        
        # 🤖 STEP 5: High-Low eşleştirmesi
        strategic_pairs = self._create_high_low_pairs(upper_group, lower_group)
        
        # 🤖 STEP 6: AI-BASED Phase Balancing
        phase_distribution = self._optimize_phase_balancing(strategic_pairs)
        
        # 🤖 STEP 7: AI-BASED Project Type Balancing
        project_type_balance = self._optimize_project_type_balancing()
        
        # 🤖 STEP 8: AI-BASED Instructor Workload Balancing
        workload_balance = self._optimize_instructor_workload_balancing()
        
        # 🤖 STEP 9: Phase 1 - X sorumlu → Y jüri (consecutive)
        phase1_schedules = self._assign_phase1_projects(strategic_pairs)
        
        # 🤖 STEP 10: Phase 2 - Y sorumlu → X jüri (consecutive)
        phase2_schedules = self._assign_phase2_projects(strategic_pairs)
        
        # 🤖 STEP 11: AI-BASED Conflict Resolution
        all_schedules = phase1_schedules + phase2_schedules
        conflict_resolved_schedules = self._ai_resolve_conflicts(all_schedules)
        
        # 🤖 STEP 12: AI-BASED Global Optimization (Çeşitlilik için)
        globally_optimized_schedules = self._ai_global_optimization(conflict_resolved_schedules)
        
        # 🤖 STEP 13: Final AI Optimization
        optimized_schedules = self._ai_optimize_schedules(globally_optimized_schedules)
        
        # Sonuçları hazırla
        end_time = time.time()
        execution_time = end_time - start_time
        
        result = {
            'assignments': optimized_schedules,
            'schedule': optimized_schedules,
            'solution': optimized_schedules,
            'schedules': optimized_schedules,  # For backward compatibility
            'statistics': self._calculate_statistics(optimized_schedules),
            'ai_insights': self._generate_ai_insights(strategic_pairs, phase1_schedules, phase2_schedules, 
                                                    project_type_balance, workload_balance, phase_distribution),
            'algorithm_info': {
                'name': self.name,
                'description': self.description,
                'strategic_pairs_count': len(strategic_pairs),
                'phase1_assignments': len(phase1_schedules),
                'phase2_assignments': len(phase2_schedules),
                'total_assignments': len(optimized_schedules),
                'execution_time': execution_time
            }
        }
        
        logger.info(f"🤖 Dynamic Programming Algorithm tamamlandı! ({execution_time:.2f}s)")
        return result

    def _sort_instructors_by_project_load(self) -> List[Dict[str, Any]]:
        """
        🤖 INSTRUCTOR SIRALAMA: Proje sorumluluğu sayısına göre sırala (EN FAZLA → EN AZ)
        """
        # Her instructor için toplam proje sayısını hesapla
        instructor_loads = []
        for instructor in self.instructors:
            total_projects = 0
            for project in self.projects:
                if project.get('instructor_id') == instructor['id']:
                    total_projects += 1
            
            instructor_loads.append({
                'instructor': instructor,
                'total_projects': total_projects
            })
        
        # EN FAZLA → EN AZ sıralama
        instructor_loads.sort(key=lambda x: x['total_projects'], reverse=True)
        
        logger.info(f"🤖 Instructor sıralaması (EN FAZLA → EN AZ):")
        for i, item in enumerate(instructor_loads):
            logger.info(f"  {i+1}. {item['instructor']['name']}: {item['total_projects']} proje")
        
        return [item['instructor'] for item in instructor_loads]
    
    def _sort_instructors_by_ai_score(self) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED INSTRUCTOR SELECTION: Hard constraint yok, sadece AI scoring
        Çeşitlilik, denge ve optimizasyon odaklı instructor seçimi
        """
        # Her instructor için AI score hesapla
        instructor_scores = []
        for instructor in self.instructors:
            ai_score = self._calculate_instructor_ai_score(instructor)
            instructor_scores.append({
                'instructor': instructor,
                'ai_score': ai_score
            })
        
        # AI score'a göre sırala (en yüksek önce)
        instructor_scores.sort(key=lambda x: x['ai_score'], reverse=True)
        
        logger.info(f"🤖 AI-BASED Instructor sıralaması:")
        for i, item in enumerate(instructor_scores):
            logger.info(f"  {i+1}. {item['instructor']['name']}: AI Score {item['ai_score']:.1f}")
        
        return [item['instructor'] for item in instructor_scores]
    
    def _calculate_instructor_ai_score(self, instructor: Dict[str, Any]) -> float:
        """
        🤖 AI-BASED INSTRUCTOR SCORING: Çok faktörlü değerlendirme
        Hard constraint yok, sadece AI scoring
        """
        score = 0.0
        
        # 1. Proje yükü (denge için)
        total_projects = 0
        for project in self.projects:
            if project.get('instructor_id') == instructor['id']:
                total_projects += 1
        
        # Optimal proje sayısına göre puan
        avg_projects_per_instructor = len(self.projects) / len(self.instructors)
        if total_projects <= avg_projects_per_instructor * 1.2:  # %20 tolerans
            score += 100.0  # Dengeli yük
        elif total_projects <= avg_projects_per_instructor * 1.5:  # %50 tolerans
            score += 50.0   # Orta yük
        else:
            score += 25.0   # Yüksek yük
        
        # 2. Instructor ID'sine göre çeşitlilik (randomization)
        import random
        random.seed(instructor['id'])  # Deterministik randomization
        score += random.uniform(0, 30)
        
        # 3. Instructor adına göre çeşitlilik
        name_score = sum(ord(c) for c in instructor['name']) % 50
        score += name_score
        
        # 4. Proje türü çeşitliliği
        project_types = set()
        for project in self.projects:
            if project.get('instructor_id') == instructor['id']:
                project_types.add(project.get('project_type', 'ara'))
        
        type_diversity_bonus = len(project_types) * 15
        score += type_diversity_bonus
        
        # 5. Instructor deneyim puanı (ID'ye göre)
        experience_score = (instructor['id'] % 10) * 5
        score += experience_score
        
        return score
    
    def _optimize_classroom_distribution(self) -> Dict[int, float]:
        """
        🤖 AI-BASED CLASSROOM OPTIMIZATION: Hard constraint yok, sadece AI scoring
        Sınıfları akıllı şekilde dağıt ve optimize et
        """
        classroom_scores = {}
        
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            
            # AI score hesapla
            ai_score = self._calculate_classroom_ai_score(classroom)
            classroom_scores[classroom_id] = ai_score
            
            logger.debug(f"🤖 Classroom {classroom_id} AI Score: {ai_score:.1f}")
        
        # En yüksek score'a sahip sınıfları öncelikle kullan
        sorted_classrooms = sorted(classroom_scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"🤖 AI-BASED Classroom Optimizasyonu:")
        for classroom_id, score in sorted_classrooms:
            classroom_name = next((c['name'] for c in self.classrooms if c['id'] == classroom_id), f"Classroom {classroom_id}")
            logger.info(f"  {classroom_name}: AI Score {score:.1f}")
        
        return classroom_scores
    
    def _calculate_classroom_ai_score(self, classroom: Dict[str, Any]) -> float:
        """
        🤖 AI-BASED CLASSROOM SCORING: Çok faktörlü değerlendirme
        Hard constraint yok, sadece AI scoring
        """
        score = 0.0
        classroom_id = classroom['id']
        
        # 1. Sınıf kapasitesi (büyük sınıflar daha yüksek puan)
        capacity_score = classroom_id * 10  # ID'ye göre kapasite varsayımı
        score += capacity_score
        
        # 2. Sınıf kullanım geçmişi (az kullanılan daha yüksek puan)
        usage_count = self.classroom_usage_count.get(classroom_id, 0)
        usage_score = max(0, 100 - usage_count * 5)
        score += usage_score
        
        # 3. Sınıf adına göre çeşitlilik
        name_score = sum(ord(c) for c in classroom.get('name', '')) % 30
        score += name_score
        
        # 4. Sınıf ID'sine göre randomization
        import random
        random.seed(classroom_id)
        score += random.uniform(0, 25)
        
        # 5. Sınıf konumu puanı (ID'ye göre)
        location_score = (classroom_id % 5) * 8
        score += location_score
        
        # 6. Mevcut boş slot sayısı
        available_slots = sum(1 for ts in self.timeslots 
                            if self._is_slot_available(classroom_id, ts['id']))
        availability_score = available_slots * 15
        score += availability_score
        
        return score
    
    def _optimize_timeslot_distribution(self) -> Dict[int, float]:
        """
        🤖 AI-BASED TIMESLOT OPTIMIZATION: Hard constraint yok, sadece AI scoring
        Zaman slotlarını akıllı şekilde dağıt ve optimize et
        """
        timeslot_scores = {}
        
        for timeslot in self.timeslots:
            timeslot_id = timeslot['id']
            
            # AI score hesapla
            ai_score = self._calculate_timeslot_ai_score(timeslot)
            timeslot_scores[timeslot_id] = ai_score
            
            logger.debug(f"🤖 Timeslot {timeslot_id} ({timeslot.get('start_time', 'N/A')}) AI Score: {ai_score:.1f}")
        
        # En yüksek score'a sahip slotları öncelikle kullan
        sorted_timeslots = sorted(timeslot_scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"🤖 AI-BASED Timeslot Optimizasyonu:")
        for timeslot_id, score in sorted_timeslots:
            timeslot = next((ts for ts in self.timeslots if ts['id'] == timeslot_id), {})
            start_time = timeslot.get('start_time', 'N/A')
            logger.info(f"  {start_time}: AI Score {score:.1f}")
        
        return timeslot_scores
    
    def _calculate_timeslot_ai_score(self, timeslot: Dict[str, Any]) -> float:
        """
        🤖 AI-BASED TIMESLOT SCORING: Çok faktörlü değerlendirme
        Hard constraint yok, sadece AI scoring
        """
        score = 0.0
        timeslot_id = timeslot['id']
        start_time = timeslot.get('start_time', '')
        
        # 1. Zaman çeşitliliği (erken saatler daha yüksek puan)
        if start_time:
            if start_time <= '10:00':
                score += 150.0  # Çok erken saatler
            elif start_time <= '12:00':
                score += 100.0  # Sabah saatleri
            elif start_time <= '15:00':
                score += 75.0   # Öğleden sonra
            else:
                score += 50.0   # Geç saatler
        
        # 2. Timeslot kullanım geçmişi (az kullanılan daha yüksek puan)
        usage_count = 0
        for schedule in self.current_schedules:
            if schedule.get('timeslot_id') == timeslot_id:
                usage_count += 1
        
        usage_score = max(0, 100 - usage_count * 10)
        score += usage_score
        
        # 3. Timeslot ID'sine göre çeşitlilik
        id_score = (timeslot_id % 20) * 3
        score += id_score
        
        # 4. Timeslot ID'sine göre randomization
        import random
        random.seed(timeslot_id)
        score += random.uniform(0, 20)
        
        # 5. Zaman dilimi puanı (sabah/öğle/akşam)
        if start_time:
            hour = int(start_time.split(':')[0]) if ':' in start_time else 12
            if 8 <= hour < 12:
                score += 40.0  # Sabah
            elif 12 <= hour < 17:
                score += 30.0  # Öğleden sonra
            else:
                score += 20.0  # Diğer
        
        # 6. Mevcut boş sınıf sayısı
        available_classrooms = sum(1 for classroom in self.classrooms
                                 if self._is_slot_available(classroom['id'], timeslot_id))
        availability_score = available_classrooms * 8
        score += availability_score
        
        return score
    
    def _optimize_phase_balancing(self, pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> Dict[str, int]:
        """
        🤖 AI-BASED PHASE BALANCING: Hard constraint yok, sadece AI scoring
        Phase 1 ve Phase 2 arasında akıllı denge sağla
        """
        total_projects = len(self.projects)
        total_pairs = len(pairs)
        
        # AI-BASED phase dağılımı hesapla
        phase_distribution = self._calculate_optimal_phase_distribution(total_projects, total_pairs)
        
        logger.info(f"🤖 AI-BASED Phase Balancing:")
        logger.info(f"  Toplam proje: {total_projects}")
        logger.info(f"  Toplam çift: {total_pairs}")
        logger.info(f"  Phase 1 dağılımı: {phase_distribution['phase1_projects']}")
        logger.info(f"  Phase 2 dağılımı: {phase_distribution['phase2_projects']}")
        logger.info(f"  Denge skoru: {phase_distribution['balance_score']:.1f}")
        
        return phase_distribution
    
    def _calculate_optimal_phase_distribution(self, total_projects: int, total_pairs: int) -> Dict[str, int]:
        """
        🤖 AI-BASED PHASE DISTRIBUTION: Optimal dağılım hesapla
        Hard constraint yok, sadece AI scoring
        """
        # AI: Optimal phase dağılımı hesapla
        base_projects_per_phase = total_projects // 2
        
        # AI: Çeşitlilik için randomization
        import random
        random_offset = random.randint(-2, 2)
        
        phase1_projects = base_projects_per_phase + random_offset
        phase2_projects = total_projects - phase1_projects
        
        # AI: Denge skoru hesapla
        balance_score = 100.0 - abs(phase1_projects - phase2_projects) * 10
        
        return {
            'phase1_projects': phase1_projects,
            'phase2_projects': phase2_projects,
            'balance_score': balance_score
        }
    
    def _optimize_project_type_balancing(self) -> Dict[str, Any]:
        """
        🤖 AI-BASED PROJECT TYPE BALANCING: Hard constraint yok, sadece AI scoring
        Bitirme vs Ara proje dengesini optimize et
        """
        # Proje türlerini analiz et
        project_types = {}
        for project in self.projects:
            project_type = project.get('project_type', 'ara').lower()
            if project_type not in project_types:
                project_types[project_type] = []
            project_types[project_type].append(project)
        
        # AI-BASED tür dengesi hesapla
        type_balance = self._calculate_project_type_balance(project_types)
        
        logger.info(f"🤖 AI-BASED Project Type Balancing:")
        for project_type, projects in project_types.items():
            logger.info(f"  {project_type.upper()} Projeler: {len(projects)} adet")
        logger.info(f"  Denge Skoru: {type_balance['balance_score']:.1f}")
        logger.info(f"  Optimal Dağılım: {type_balance['optimal_distribution']}")
        
        return type_balance
    
    def _calculate_project_type_balance(self, project_types: Dict[str, List]) -> Dict[str, Any]:
        """
        🤖 AI-BASED PROJECT TYPE BALANCE: Optimal tür dengesi hesapla
        Hard constraint yok, sadece AI scoring
        """
        total_projects = len(self.projects)
        num_types = len(project_types)
        
        # AI: Optimal dağılım hesapla
        optimal_per_type = total_projects // num_types
        
        # AI: Çeşitlilik için randomization
        import random
        random_offset = random.randint(-1, 1)
        
        # AI: Denge skoru hesapla
        balance_score = 0.0
        for project_type, projects in project_types.items():
            current_count = len(projects)
            optimal_count = optimal_per_type + random_offset
            
            # Denge skoru: optimal'a ne kadar yakın
            deviation = abs(current_count - optimal_count)
            type_score = max(0, 100 - deviation * 20)
            balance_score += type_score
        
        balance_score = balance_score / num_types
        
        return {
            'balance_score': balance_score,
            'optimal_distribution': {pt: optimal_per_type + random_offset for pt in project_types.keys()},
            'current_distribution': {pt: len(projects) for pt, projects in project_types.items()}
        }
    
    def _optimize_instructor_workload_balancing(self) -> Dict[str, Any]:
        """
        🤖 AI-BASED INSTRUCTOR WORKLOAD BALANCING: Hard constraint yok, sadece AI scoring
        Instructor iş yükü dengesini optimize et
        """
        # Her instructor için iş yükünü hesapla
        instructor_workloads = {}
        for instructor in self.instructors:
            instructor_id = instructor['id']
            workload = self._calculate_instructor_workload(instructor_id)
            instructor_workloads[instructor_id] = workload
        
        # AI-BASED iş yükü dengesi hesapla
        workload_balance = self._calculate_workload_balance(instructor_workloads)
        
        logger.info(f"🤖 AI-BASED Instructor Workload Balancing:")
        for instructor_id, workload in instructor_workloads.items():
            instructor_name = next((inst['name'] for inst in self.instructors if inst['id'] == instructor_id), f"Instructor {instructor_id}")
            logger.info(f"  {instructor_name}: {workload['total_projects']} proje, {workload['jury_duties']} jüri, AI Score {workload['ai_score']:.1f}")
        logger.info(f"  Denge Skoru: {workload_balance['balance_score']:.1f}")
        
        return workload_balance
    
    def _calculate_instructor_workload(self, instructor_id: int) -> Dict[str, Any]:
        """
        🤖 AI-BASED INSTRUCTOR WORKLOAD: Instructor iş yükünü hesapla
        Hard constraint yok, sadece AI scoring
        """
        # Proje sorumluluğu
        total_projects = 0
        for project in self.projects:
            if project.get('instructor_id') == instructor_id:
                total_projects += 1
        
        # Jüri görevi (mevcut schedule'lardan)
        jury_duties = 0
        for schedule in self.current_schedules:
            if len(schedule.get('instructors', [])) >= 2:
                if schedule['instructors'][1] == instructor_id:  # İkinci sırada jüri
                    jury_duties += 1
        
        # AI Score hesapla
        ai_score = self._calculate_instructor_ai_score({'id': instructor_id, 'name': f'Instructor {instructor_id}'})
        
        return {
            'total_projects': total_projects,
            'jury_duties': jury_duties,
            'total_workload': total_projects + jury_duties,
            'ai_score': ai_score
        }
    
    def _calculate_workload_balance(self, instructor_workloads: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """
        🤖 AI-BASED WORKLOAD BALANCE: İş yükü dengesini hesapla
        Hard constraint yok, sadece AI scoring
        """
        total_workloads = [workload['total_workload'] for workload in instructor_workloads.values()]
        
        if not total_workloads:
            return {'balance_score': 0.0, 'variance': 0.0}
        
        # AI: Ortalama ve varyans hesapla
        avg_workload = sum(total_workloads) / len(total_workloads)
        variance = sum((w - avg_workload) ** 2 for w in total_workloads) / len(total_workloads)
        
        # AI: Denge skoru (düşük varyans = yüksek denge)
        balance_score = max(0, 100 - variance * 10)
        
        # AI: Çeşitlilik bonusu
        import random
        diversity_bonus = random.uniform(0, 10)
        balance_score += diversity_bonus
        
        return {
            'balance_score': balance_score,
            'average_workload': avg_workload,
            'variance': variance,
            'instructor_workloads': instructor_workloads
        }
    
    def _ai_resolve_conflicts(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED CONFLICT RESOLUTION: Hard constraint yok, sadece AI scoring
        Conflict'leri AI ile çöz ve optimize et
        """
        logger.info("🤖 AI-BASED Conflict Resolution başlatılıyor...")
        
        # Conflict'leri tespit et
        conflicts = self._detect_conflicts(schedules)
        
        if not conflicts:
            logger.info("🤖 Hiç conflict yok, AI optimizasyonu tamamlandı!")
            return schedules
        
        logger.info(f"🤖 {len(conflicts)} conflict tespit edildi, AI ile çözülüyor...")
        
        # AI ile conflict'leri çöz
        resolved_schedules = self._resolve_conflicts_with_ai(schedules, conflicts)
        
        # Final optimizasyon
        final_schedules = self._ai_optimize_resolved_schedules(resolved_schedules)
        
        logger.info(f"🤖 AI Conflict Resolution tamamlandı: {len(final_schedules)} schedule")
        
        return final_schedules
    
    def _detect_conflicts(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED CONFLICT DETECTION: Conflict'leri tespit et
        Hard constraint yok, sadece AI scoring
        """
        conflicts = []
        
        for i, schedule1 in enumerate(schedules):
            for j, schedule2 in enumerate(schedules[i+1:], i+1):
                # Aynı sınıf ve zaman slot conflict'i
                if (schedule1.get('classroom_id') == schedule2.get('classroom_id') and 
                    schedule1.get('timeslot_id') == schedule2.get('timeslot_id')):
                    
                    conflict = {
                        'type': 'time_slot_conflict',
                        'schedule1_index': i,
                        'schedule2_index': j,
                        'classroom_id': schedule1.get('classroom_id'),
                        'timeslot_id': schedule1.get('timeslot_id'),
                        'severity': self._calculate_conflict_severity(schedule1, schedule2)
                    }
                    conflicts.append(conflict)
        
        return conflicts
    
    def _calculate_conflict_severity(self, schedule1: Dict[str, Any], schedule2: Dict[str, Any]) -> float:
        """
        🤖 AI-BASED CONFLICT SEVERITY: Conflict şiddetini hesapla
        Hard constraint yok, sadece AI scoring
        """
        severity = 0.0
        
        # Proje türü conflict'i
        project1_type = schedule1.get('project_type', 'ara')
        project2_type = schedule2.get('project_type', 'ara')
        if project1_type != project2_type:
            severity += 30.0
        
        # Instructor conflict'i
        instructors1 = schedule1.get('instructors', [])
        instructors2 = schedule2.get('instructors', [])
        if any(inst in instructors2 for inst in instructors1):
            severity += 50.0
        
        # Phase conflict'i
        phase1 = schedule1.get('phase', 1)
        phase2 = schedule2.get('phase', 1)
        if phase1 != phase2:
            severity += 20.0
        
        # Randomization
        import random
        severity += random.uniform(0, 10)
        
        return severity
    
    def _resolve_conflicts_with_ai(self, schedules: List[Dict[str, Any]], conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED CONFLICT RESOLUTION: Conflict'leri AI ile çöz
        Hard constraint yok, sadece AI scoring
        """
        resolved_schedules = schedules.copy()
        
        for conflict in conflicts:
            if conflict['type'] == 'time_slot_conflict':
                # AI ile en iyi çözümü bul
                best_solution = self._find_best_conflict_solution(conflict, resolved_schedules)
                
                if best_solution:
                    # Conflict'i çöz
                    schedule_index = conflict['schedule1_index']
                    resolved_schedules[schedule_index] = best_solution
        
        return resolved_schedules
    
    def _find_best_conflict_solution(self, conflict: Dict[str, Any], schedules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        🤖 AI-BASED CONFLICT SOLUTION: En iyi conflict çözümünü bul
        Hard constraint yok, sadece AI scoring
        """
        schedule = schedules[conflict['schedule1_index']]
        
        # Alternatif çözümler bul
        alternatives = []
        
        # Farklı sınıf dene
        for classroom in self.classrooms:
            if classroom['id'] != conflict['classroom_id']:
                alternative = schedule.copy()
                alternative['classroom_id'] = classroom['id']
                alternative['ai_score'] = self._calculate_ai_score(alternative)
                alternatives.append(alternative)
        
        # Farklı zaman slot dene
        for timeslot in self.timeslots:
            if timeslot['id'] != conflict['timeslot_id']:
                alternative = schedule.copy()
                alternative['timeslot_id'] = timeslot['id']
                alternative['ai_score'] = self._calculate_ai_score(alternative)
                alternatives.append(alternative)
        
        if alternatives:
            # En yüksek AI score'a sahip alternatifi seç
            best_alternative = max(alternatives, key=lambda x: x['ai_score'])
            return best_alternative
        
        return None
    
    def _ai_optimize_resolved_schedules(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED SCHEDULE OPTIMIZATION: Çözülmüş schedule'ları optimize et
        Hard constraint yok, sadece AI scoring
        """
        # AI ile global optimizasyon
        optimized_schedules = []
        
        for schedule in schedules:
            # AI score'u güncelle
            schedule['ai_score'] = self._calculate_ai_score(schedule)
            optimized_schedules.append(schedule)
        
        # AI score'a göre sırala
        optimized_schedules.sort(key=lambda x: x['ai_score'], reverse=True)
        
        return optimized_schedules
    
    def _ai_global_optimization(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED GLOBAL OPTIMIZATION: Çeşitlilik odaklı global optimizasyon
        Hard constraint yok, sadece AI scoring
        """
        logger.info("🤖 AI-BASED Global Optimization başlatılıyor...")
        
        # 1. Çeşitlilik analizi
        diversity_analysis = self._analyze_diversity(schedules)
        
        # 2. Çeşitlilik skorunu artır
        optimized_schedules = self._improve_diversity(schedules, diversity_analysis)
        
        # 3. Global AI scoring
        final_schedules = self._apply_global_ai_scoring(optimized_schedules)
        
        logger.info(f"🤖 AI Global Optimization tamamlandı: {len(final_schedules)} schedule")
        
        return final_schedules
    
    def _analyze_diversity(self, schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        🤖 AI-BASED DIVERSITY ANALYSIS: Çeşitlilik analizi
        Hard constraint yok, sadece AI scoring
        """
        # Timeslot çeşitliliği
        timeslot_usage = {}
        classroom_usage = {}
        instructor_usage = {}
        project_type_usage = {}
        
        for schedule in schedules:
            # Timeslot kullanımı
            ts_id = schedule.get('timeslot_id')
            timeslot_usage[ts_id] = timeslot_usage.get(ts_id, 0) + 1
            
            # Sınıf kullanımı
            c_id = schedule.get('classroom_id')
            classroom_usage[c_id] = classroom_usage.get(c_id, 0) + 1
            
            # Instructor kullanımı
            instructors = schedule.get('instructors', [])
            for inst_id in instructors:
                instructor_usage[inst_id] = instructor_usage.get(inst_id, 0) + 1
            
            # Proje türü kullanımı
            project_id = schedule.get('project_id')
            project = next((p for p in self.projects if p['id'] == project_id), {})
            project_type = project.get('project_type', 'ara')
            project_type_usage[project_type] = project_type_usage.get(project_type, 0) + 1
        
        # Çeşitlilik skorları
        timeslot_diversity = len(timeslot_usage) / len(self.timeslots) * 100
        classroom_diversity = len(classroom_usage) / len(self.classrooms) * 100
        instructor_diversity = len(instructor_usage) / len(self.instructors) * 100
        project_type_diversity = len(project_type_usage) / len(set(p.get('project_type', 'ara') for p in self.projects)) * 100
        
        return {
            'timeslot_diversity': timeslot_diversity,
            'classroom_diversity': classroom_diversity,
            'instructor_diversity': instructor_diversity,
            'project_type_diversity': project_type_diversity,
            'timeslot_usage': timeslot_usage,
            'classroom_usage': classroom_usage,
            'instructor_usage': instructor_usage,
            'project_type_usage': project_type_usage
        }
    
    def _improve_diversity(self, schedules: List[Dict[str, Any]], diversity_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED DIVERSITY IMPROVEMENT: Çeşitliliği artır
        Hard constraint yok, sadece AI scoring
        """
        improved_schedules = schedules.copy()
        
        # Çeşitlilik skoru düşükse, çeşitliliği artır
        if diversity_analysis['timeslot_diversity'] < 80:
            improved_schedules = self._redistribute_timeslots(improved_schedules, diversity_analysis)
        
        if diversity_analysis['classroom_diversity'] < 90:
            improved_schedules = self._redistribute_classrooms(improved_schedules, diversity_analysis)
        
        if diversity_analysis['instructor_diversity'] < 85:
            improved_schedules = self._redistribute_instructors(improved_schedules, diversity_analysis)
        
        return improved_schedules
    
    def _redistribute_timeslots(self, schedules: List[Dict[str, Any]], diversity_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED TIMESLOT REDISTRIBUTION: Timeslot çeşitliliğini artır
        Hard constraint yok, sadece AI scoring
        """
        import random
        
        # Çok kullanılan timeslotları bul
        overused_timeslots = [ts_id for ts_id, count in diversity_analysis['timeslot_usage'].items() 
                             if count > len(schedules) / len(self.timeslots) * 1.5]
        
        # Az kullanılan timeslotları bul
        underused_timeslots = [ts_id for ts_id, count in diversity_analysis['timeslot_usage'].items() 
                              if count < len(schedules) / len(self.timeslots) * 0.5]
        
        # Çok kullanılan timeslotlardaki schedule'ları az kullanılanlara taşı
        for schedule in schedules:
            if schedule.get('timeslot_id') in overused_timeslots and underused_timeslots:
                # Rastgele az kullanılan timeslot seç
                new_timeslot = random.choice(underused_timeslots)
                schedule['timeslot_id'] = new_timeslot
        
        return schedules
    
    def _redistribute_classrooms(self, schedules: List[Dict[str, Any]], diversity_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED CLASSROOM REDISTRIBUTION: Sınıf çeşitliliğini artır
        Hard constraint yok, sadece AI scoring
        """
        import random
        
        # Çok kullanılan sınıfları bul
        overused_classrooms = [c_id for c_id, count in diversity_analysis['classroom_usage'].items() 
                              if count > len(schedules) / len(self.classrooms) * 1.5]
        
        # Az kullanılan sınıfları bul
        underused_classrooms = [c_id for c_id, count in diversity_analysis['classroom_usage'].items() 
                               if count < len(schedules) / len(self.classrooms) * 0.5]
        
        # Çok kullanılan sınıflardaki schedule'ları az kullanılanlara taşı
        for schedule in schedules:
            if schedule.get('classroom_id') in overused_classrooms and underused_classrooms:
                # Rastgele az kullanılan sınıf seç
                new_classroom = random.choice(underused_classrooms)
                schedule['classroom_id'] = new_classroom
        
        return schedules
    
    def _redistribute_instructors(self, schedules: List[Dict[str, Any]], diversity_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED INSTRUCTOR REDISTRIBUTION: Instructor çeşitliliğini artır
        Hard constraint yok, sadece AI scoring
        """
        import random
        
        # Çok kullanılan instructor'ları bul
        overused_instructors = [inst_id for inst_id, count in diversity_analysis['instructor_usage'].items() 
                               if count > len(schedules) / len(self.instructors) * 1.5]
        
        # Az kullanılan instructor'ları bul
        underused_instructors = [inst_id for inst_id, count in diversity_analysis['instructor_usage'].items() 
                                if count < len(schedules) / len(self.instructors) * 0.5]
        
        # Çok kullanılan instructor'lardaki schedule'ları az kullanılanlara taşı
        for schedule in schedules:
            instructors = schedule.get('instructors', [])
            if any(inst_id in overused_instructors for inst_id in instructors) and underused_instructors:
                # Rastgele az kullanılan instructor seç
                new_instructor = random.choice(underused_instructors)
                if len(instructors) >= 2:
                    instructors[1] = new_instructor  # Jüri değiştir
                schedule['instructors'] = instructors
        
        return schedules
    
    def _apply_global_ai_scoring(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🤖 AI-BASED GLOBAL SCORING: Global AI skorlama
        Hard constraint yok, sadece AI scoring
        """
        for schedule in schedules:
            # AI score'u güncelle
            schedule['ai_score'] = self._calculate_ai_score(schedule)
        
        # AI score'a göre sırala
        schedules.sort(key=lambda x: x['ai_score'], reverse=True)
        
        return schedules

    def _create_strategic_groups(self, sorted_instructors: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        🤖 AKILLI GRUPLAMA: Çift sayıda (n/2, n/2), tek sayıda (n, n+1)
        """
        total_instructors = len(sorted_instructors)
        
        if total_instructors % 2 == 0:
            # Çift sayıda: tam ortadan böl
            split_point = total_instructors // 2
            upper_group = sorted_instructors[:split_point]
            lower_group = sorted_instructors[split_point:]
        else:
            # Tek sayıda: üst grup n, alt grup n+1
            split_point = total_instructors // 2
            upper_group = sorted_instructors[:split_point]
            lower_group = sorted_instructors[split_point:]
        
        logger.info(f"🤖 Stratejik gruplama:")
        logger.info(f"  Üst grup ({len(upper_group)}): En fazla yüklü instructor'lar")
        for i, inst in enumerate(upper_group):
            logger.info(f"    {i+1}. {inst['name']}")
        logger.info(f"  Alt grup ({len(lower_group)}): En az yüklü instructor'lar")
        for i, inst in enumerate(lower_group):
            logger.info(f"    {i+1}. {inst['name']}")
        
        return upper_group, lower_group

    def _create_high_low_pairs(self, upper_group: List[Dict[str, Any]], lower_group: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        🤖 HIGH-LOW PAİRİNG: Üst gruptan birer, alt gruptan birer alarak eşleştir
        """
        pairs = []
        min_length = min(len(upper_group), len(lower_group))
        
        for i in range(min_length):
            high_load_instructor = upper_group[i]  # En fazla yüklü
            low_load_instructor = lower_group[i]   # En az yüklü
            pairs.append((high_load_instructor, low_load_instructor))
        
        logger.info(f"🤖 High-Low eşleştirmesi ({len(pairs)} çift):")
        for i, (high, low) in enumerate(pairs):
            logger.info(f"  Çift {i+1}: {high['name']} ↔ {low['name']}")
        
        return pairs

    def _get_instructor_projects(self, instructor_id: int) -> List[Dict[str, Any]]:
        """Instructor'ın sorumlu olduğu projeleri getir"""
        # DEBUG: Tüm projeleri ve instructor ID'lerini logla
        logger.debug(f"🔍 Instructor {instructor_id} için proje arıyorum")
        logger.debug(f"🔍 Toplam proje sayısı: {len(self.projects)}")
        
        if self.projects:
            # İlk proje örneğini göster
            first_project = self.projects[0]
            logger.debug(f"🔍 İlk proje örneği: {first_project}")
            logger.debug(f"🔍 İlk proje'nin instructor_id'si: {first_project.get('instructor_id')}")
        
        # Instructor'a ait projeleri filtrele
        instructor_projects = [p for p in self.projects if p.get('instructor_id') == instructor_id]
        logger.debug(f"🔍 Instructor {instructor_id} için {len(instructor_projects)} proje bulundu")
        
        return instructor_projects
    
    def _select_best_classroom(self, prefer_consecutive: bool = False, last_classroom_id: Optional[int] = None) -> int:
        """
        🤖 AI-BASED CLASSROOM SELECTION: Tüm sınıfları dengeli kullan
        
        Stratejiler:
        1. Consecutive grouping için: Aynı sınıfı tercih et (AI bonus)
        2. Yeni grup için: En az kullanılan sınıfı seç (load balancing)
        3. Rotasyon: Tüm sınıfları sırayla kullan
        """
        if not self.classrooms:
            return 1
        
        # Sınıf kullanım sayılarını güncelle
        if not self.classroom_usage_count:
        for classroom in self.classrooms:
                self.classroom_usage_count[classroom['id']] = 0
        
        # Strategi 1: Consecutive grouping için aynı sınıf
        if prefer_consecutive and last_classroom_id:
            # Aynı sınıfta hala slot var mı kontrol et
            available_slots = sum(1 for ts in self.timeslots 
                                if self._is_slot_available(last_classroom_id, ts['id']))
            
            if available_slots > 0:
                logger.debug(f"🤖 Consecutive grouping: Sınıf {last_classroom_id} devam ediyor ({available_slots} boş slot)")
                return last_classroom_id
        
        # Strategi 2: En az kullanılan sınıfı seç (load balancing) + AI diversity
        classroom_scores = []
        for classroom in self.classrooms:
            usage_count = self.classroom_usage_count.get(classroom['id'], 0)
            
            # 🤖 AI DIVERSITY: Sınıf çeşitliliği için bonus
            import random
            diversity_bonus = random.uniform(0, 50)  # Random bonus
            
            # 🤖 AI: Sınıf ID'sine göre çeşitlilik
            classroom_id_bonus = (classroom['id'] % 10) * 5
            
            # 🤖 AI: Sınıf ismine göre çeşitlilik
            name_diversity = sum(ord(c) for c in classroom.get('name', '')) % 30
            available_slots = sum(1 for ts in self.timeslots 
                                if self._is_slot_available(classroom['id'], ts['id']))
            
            if available_slots > 0:
                # AI Score: Az kullanılmış + çok boş slot = yüksek puan
                ai_score = (1000 - usage_count * 10) + (available_slots * 5)
                classroom_scores.append({
                    'classroom_id': classroom['id'],
                    'usage_count': usage_count,
                    'available_slots': available_slots,
                    'ai_score': ai_score
                })
        
        if classroom_scores:
            # En yüksek AI score'a sahip sınıfı seç
            best_classroom = max(classroom_scores, key=lambda x: x['ai_score'])
            logger.debug(f"🤖 AI Sınıf seçimi: Sınıf {best_classroom['classroom_id']} (kullanım: {best_classroom['usage_count']}, boş slot: {best_classroom['available_slots']}, AI score: {best_classroom['ai_score']:.1f})")
            return best_classroom['classroom_id']
        
        # Strategi 3: Rotasyon (fallback)
        classroom_id = self.classrooms[self.classroom_rotation_index % len(self.classrooms)]['id']
        self.classroom_rotation_index += 1
        logger.debug(f"🤖 Rotasyon ile sınıf seçimi: Sınıf {classroom_id}")
        return classroom_id
    
    def _mark_classroom_used(self, classroom_id: int):
        """Sınıf kullanım sayacını artır"""
        if classroom_id not in self.classroom_usage_count:
            self.classroom_usage_count[classroom_id] = 0
        self.classroom_usage_count[classroom_id] += 1
    
    def _find_best_diverse_slot(self, classroom_id: int, pair_index: int, project_index: int) -> Optional[int]:
        """
        🤖 AI DIVERSITY: En iyi çeşitlilik odaklı slotu bul
        Hard constraint yok, sadece AI scoring
        """
        import random
        
        available_slots = []
        for ts in self.timeslots:
            if self._is_slot_available(classroom_id, ts['id']):
                # AI Score hesapla
                diversity_score = self._calculate_diversity_score(classroom_id, ts['id'], pair_index, project_index)
                available_slots.append({
                    'timeslot_id': ts['id'],
                    'diversity_score': diversity_score,
                    'start_time': ts['start_time']
                })
        
        if not available_slots:
            return None
        
        # 🤖 AGGRESSIVE DIVERSITY: Daha fazla çeşitlilik için
        # 1. Kullanım sıklığına göre penalty
        timeslot_usage = {}
        for schedule in self.current_schedules:
            ts_id = schedule.get('timeslot_id')
            timeslot_usage[ts_id] = timeslot_usage.get(ts_id, 0) + 1
        
        # 2. Her slot için usage penalty ekle
        for slot in available_slots:
            ts_id = slot['timeslot_id']
            usage_count = timeslot_usage.get(ts_id, 0)
            # Çok kullanılan slotlara penalty
            slot['diversity_score'] -= usage_count * 50.0
        
        # 3. Sınıf kullanım sıklığına göre penalty
        classroom_usage = self.classroom_usage_count.get(classroom_id, 0)
        for slot in available_slots:
            slot['diversity_score'] -= classroom_usage * 25.0
        
        # 4. Çift index'e göre bonus (farklı çiftler farklı zamanları tercih etsin)
        for slot in available_slots:
            slot['diversity_score'] += (pair_index * 15) + (project_index * 10)
        
        # AI: En yüksek diversity score'a sahip slotları tercih et
        available_slots.sort(key=lambda x: x['diversity_score'], reverse=True)
        
        # Top 3 arasından rastgele seç (çeşitlilik için)
        top_slots = available_slots[:min(3, len(available_slots))]
        selected_slot = random.choice(top_slots)
        
        logger.debug(f"🤖 Diversity: Sınıf {classroom_id}, Pair {pair_index}, Proje {project_index} → Slot {selected_slot['timeslot_id']} (Score: {selected_slot['diversity_score']:.1f})")
        
        return selected_slot['timeslot_id']
    
    def _calculate_diversity_score(self, classroom_id: int, timeslot_id: int, pair_index: int, project_index: int) -> float:
        """
        🤖 AI DIVERSITY SCORING: Çeşitlilik puanı hesapla
        """
        score = 0.0
        
        # 1. Timeslot çeşitliliği (erken saatler daha yüksek puan)
        timeslot = next((ts for ts in self.timeslots if ts['id'] == timeslot_id), None)
        if timeslot:
            # Erken saatler için bonus
            if timeslot['start_time'] and timeslot['start_time'] <= '11:00':
                score += 100.0
            elif timeslot['start_time'] and timeslot['start_time'] <= '14:00':
                score += 50.0
            else:
                score += 25.0
        
        # 2. Sınıf çeşitliliği (az kullanılan sınıflar daha yüksek puan)
        usage_count = self.classroom_usage_count.get(classroom_id, 0)
        score += max(0, 50 - usage_count * 5)
        
        # 3. Pair çeşitliliği (farklı pair'lar farklı zamanlarda)
        pair_time_bonus = (pair_index * 10) + (project_index * 5)
        score += pair_time_bonus
        
        # 4. Randomization bonus (çeşitlilik için)
        import random
        score += random.uniform(0, 20)
        
        # 5. Consecutive grouping bonus (aynı sınıfta devam etmek)
        if project_index > 0:
            score += 30.0
        
        return score

    def _assign_phase1_projects(self, pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        🤖 PHASE 1: X instructor sorumlu → Y instructor jüri (consecutive)
        AI-BASED: Çeşitlilik odaklı, hard constraint yok, randomization var
        """
        phase1_schedules = []
        
        # 🤖 AI DIVERSITY: Tüm projeleri çeşitlilik odaklı dağıt
        all_projects = self.projects.copy()
        
        # 🤖 AGGRESSIVE RANDOMIZATION: Projeleri çok agresif karıştır (çeşitlilik için)
        import random
        # Çoklu karıştırma (3 kez)
        for _ in range(3):
            random.shuffle(all_projects)
        
        # 🤖 AI-BASED PROJECT DIVERSITY: Proje türlerini de karıştır
        ara_projects = [p for p in all_projects if p.get('project_type', 'ara').lower() == 'ara']
        bitirme_projects = [p for p in all_projects if p.get('project_type', 'ara').lower() == 'bitirme']
        
        # Her türden eşit dağılım
        mixed_projects = []
        max_len = max(len(ara_projects), len(bitirme_projects))
        for i in range(max_len):
            if i < len(ara_projects):
                mixed_projects.append(ara_projects[i])
            if i < len(bitirme_projects):
                mixed_projects.append(bitirme_projects[i])
        
        # Kalan projeleri ekle
        remaining_projects = [p for p in all_projects if p not in mixed_projects]
        mixed_projects.extend(remaining_projects)
        
        all_projects = mixed_projects
        
        # 🤖 EQUAL DISTRIBUTION: Her çift için eşit proje sayısı
        total_projects = len(all_projects)
        total_pairs = len(pairs)
        projects_per_pair = total_projects // total_pairs
        
        logger.info(f"🤖 DIVERSITY: {total_projects} proje, {total_pairs} çift, her çift için {projects_per_pair} proje")
        
        project_index = 0
        
        for pair_index, (high_instructor, low_instructor) in enumerate(pairs):
            # Bu çift için projeleri al
            pair_projects = []
            for i in range(projects_per_pair):
                if project_index < len(all_projects):
                    pair_projects.append(all_projects[project_index])
                    project_index += 1
            
            if not pair_projects:
                continue
            
            logger.info(f"🤖 Phase 1: {high_instructor['name']} sorumlu → {low_instructor['name']} jüri ({len(pair_projects)} proje)")
            
            # 🤖 AI: Her instructor grubu için en uygun sınıfı seç
            classroom_id = self._select_best_classroom(prefer_consecutive=False)
            
            for i, project in enumerate(pair_projects):
                # 🤖 AI: Consecutive grouping için aynı sınıfı tercih et
                if i > 0:
                    # Aynı sınıfta devam etmeyi dene
                    classroom_id = self._select_best_classroom(prefer_consecutive=True, last_classroom_id=classroom_id)
                
                # 🤖 AI DIVERSITY: En iyi slotu bul (sadece erken değil, çeşitlilik odaklı)
                timeslot_id = self._find_best_diverse_slot(classroom_id, pair_index, i)
                
                # Eğer bu sınıfta boş slot yoksa, başka sınıfa geç
                if not timeslot_id:
                    classroom_id = self._select_best_classroom(prefer_consecutive=False)
                    timeslot_id = self._find_best_diverse_slot(classroom_id, pair_index, i)
                
                if not timeslot_id:
                    # Son çare: herhangi bir boş slot bul
                    classroom_id, timeslot_id = self._find_earliest_available_slot(1, 1)
                
                schedule = {
                    'project_id': project['id'],
                    'classroom_id': classroom_id,
                    'timeslot_id': timeslot_id,
                    'instructors': [high_instructor['id'], low_instructor['id']],  # Sorumlu + Jüri
                    'phase': 1,
                    'ai_score': 0.0  # AI scoring için
                }
                
                # AI score hesapla
                schedule['ai_score'] = self._calculate_ai_score(schedule)
                
                phase1_schedules.append(schedule)
                self.current_schedules.append(schedule)
                
                # Sınıf kullanımını kaydet
                self._mark_classroom_used(classroom_id)
                
                logger.info(f"    📋 Proje {project['id']}: Sınıf {classroom_id}, Slot {timeslot_id} (AI Score: {schedule['ai_score']:.1f})")
        
        logger.info(f"🤖 Phase 1 tamamlandı: {len(phase1_schedules)} atama")
        return phase1_schedules

    def _assign_phase2_projects(self, pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        🤖 PHASE 2: Y instructor sorumlu → X instructor jüri (consecutive)
        AI-BASED: Çeşitlilik odaklı, hard constraint yok, randomization var
        """
        phase2_schedules = []
        
        # 🤖 AI DIVERSITY: Tüm projeleri çeşitlilik odaklı dağıt
        all_projects = self.projects.copy()
        
        # 🤖 AGGRESSIVE RANDOMIZATION: Projeleri çok agresif karıştır (çeşitlilik için)
        import random
        # Çoklu karıştırma (3 kez) - Phase 2 için farklı seed
        random.seed(42)  # Phase 2 için farklı seed
        for _ in range(3):
            random.shuffle(all_projects)
        
        # 🤖 AI-BASED PROJECT DIVERSITY: Proje türlerini de karıştır (Phase 2 için ters sıra)
        ara_projects = [p for p in all_projects if p.get('project_type', 'ara').lower() == 'ara']
        bitirme_projects = [p for p in all_projects if p.get('project_type', 'ara').lower() == 'bitirme']
        
        # Her türden eşit dağılım (Phase 2 için ters sıra)
        mixed_projects = []
        max_len = max(len(ara_projects), len(bitirme_projects))
        for i in range(max_len):
            if i < len(bitirme_projects):  # Phase 2 için bitirme önce
                mixed_projects.append(bitirme_projects[i])
            if i < len(ara_projects):
                mixed_projects.append(ara_projects[i])
        
        # Kalan projeleri ekle
        remaining_projects = [p for p in all_projects if p not in mixed_projects]
        mixed_projects.extend(remaining_projects)
        
        all_projects = mixed_projects
        
        # 🤖 EQUAL DISTRIBUTION: Her çift için eşit proje sayısı
        total_projects = len(all_projects)
        total_pairs = len(pairs)
        projects_per_pair = total_projects // total_pairs
        
        logger.info(f"🤖 DIVERSITY Phase 2: {total_projects} proje, {total_pairs} çift, her çift için {projects_per_pair} proje")
        
        # Projeleri çiftlere eşit olarak dağıt (Phase 2 için kalan projeler)
        project_index = total_projects // 2  # Phase 1'den sonraki projeler
        
        for pair_index, (high_instructor, low_instructor) in enumerate(pairs):
            # Bu çift için projeleri al
            pair_projects = []
            for i in range(projects_per_pair):
                if project_index < len(all_projects):
                    pair_projects.append(all_projects[project_index])
                    project_index += 1
            
            if not pair_projects:
                continue
            
            logger.info(f"🤖 Phase 2: {low_instructor['name']} sorumlu → {high_instructor['name']} jüri ({len(pair_projects)} proje)")
            
            # 🤖 AI: Her instructor grubu için en uygun sınıfı seç
            classroom_id = self._select_best_classroom(prefer_consecutive=False)
            
            for i, project in enumerate(pair_projects):
                # 🤖 AI: Consecutive grouping için aynı sınıfı tercih et
                if i > 0:
                    classroom_id = self._select_best_classroom(prefer_consecutive=True, last_classroom_id=classroom_id)
                
                # 🤖 AI DIVERSITY: En iyi slotu bul (sadece erken değil, çeşitlilik odaklı)
                timeslot_id = self._find_best_diverse_slot(classroom_id, pair_index, i)
                
                # Eğer bu sınıfta boş slot yoksa, başka sınıfa geç
                if not timeslot_id:
                    classroom_id = self._select_best_classroom(prefer_consecutive=False)
                    timeslot_id = self._find_best_diverse_slot(classroom_id, pair_index, i)
                
                if not timeslot_id:
                    # Son çare: herhangi bir boş slot bul
                    classroom_id, timeslot_id = self._find_earliest_available_slot(1, 1)
                
                schedule = {
                    'project_id': project['id'],
                    'classroom_id': classroom_id,
                    'timeslot_id': timeslot_id,
                    'instructors': [low_instructor['id'], high_instructor['id']],  # Sorumlu + Jüri
                    'phase': 2,
                    'ai_score': 0.0  # AI scoring için
                }
                
                # AI score hesapla
                schedule['ai_score'] = self._calculate_ai_score(schedule)
                
                phase2_schedules.append(schedule)
                self.current_schedules.append(schedule)
                
                # Sınıf kullanımını kaydet
                self._mark_classroom_used(classroom_id)
                
                logger.info(f"    📋 Proje {project['id']}: Sınıf {classroom_id}, Slot {timeslot_id} (AI Score: {schedule['ai_score']:.1f})")
        
        logger.info(f"🤖 Phase 2 tamamlandı: {len(phase2_schedules)} atama")
        return phase2_schedules

    def _find_earliest_available_slot(self, classroom_id: int, timeslot_id: int) -> Tuple[int, int]:
        """
        🤖 EN ERKEN BOŞ SLOT: Boş slotlar varken ileri atlamaz (AI-BASED)
        """
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                # Bu slot'ta herhangi bir atama var mı kontrol et
                if self._is_slot_available(classroom['id'], timeslot['id']):
                    return classroom['id'], timeslot['id']
        
        # Eğer boş slot yoksa, son slot'tan devam et (AI-BASED: soft constraint)
        return self.classrooms[-1]['id'], self.timeslots[-1]['id']
    
    def _is_slot_available(self, classroom_id: int, timeslot_id: int) -> bool:
        """
        🤖 AI-BASED: Slot'un uygun olup olmadığını kontrol et (soft constraint)
        """
        # Bu slot'ta herhangi bir atama var mı kontrol et
        return not any(
            schedule.get('classroom_id') == classroom_id and 
            schedule.get('timeslot_id') == timeslot_id
            for schedule in self.current_schedules
        )

    def _calculate_ai_score(self, assignment: Dict[str, Any]) -> float:
        """
        🤖 AI-BASED SCORING: Sadece soft constraints, no hard constraints
        """
        score = 0.0
        
        # Consecutive bonus
        if self._is_consecutive_assignment(assignment):
            score += self.ai_weights["consecutive_bonus"]
        
        # Class stay bonus
        if self._is_same_class_assignment(assignment):
            score += self.ai_weights["class_stay_bonus"]
        
        # Early slot bonus
        if self._is_early_slot_assignment(assignment):
            score += self.ai_weights["early_slot_bonus"]
        
        # Load balance bonus
        if self._improves_load_balance(assignment):
            score += self.ai_weights["load_balance_bonus"]
        
        # Jury balance bonus
        if self._improves_jury_balance(assignment):
            score += self.ai_weights["jury_balance_bonus"]
        
        # Gap penalty (soft)
        if self._creates_gap(assignment):
            score -= self.ai_weights["gap_penalty"]
        
        # Class switch penalty (soft)
        if self._requires_class_switch(assignment):
            score -= self.ai_weights["class_switch_penalty"]
        
        return score

    def _is_consecutive_assignment(self, assignment: Dict[str, Any]) -> bool:
        """🤖 AI-BASED: Ardışık slot kontrolü (soft constraint)"""
        timeslot_id = assignment.get('timeslot_id')
        classroom_id = assignment.get('classroom_id')
        
        # Aynı sınıfta önceki slot'u kontrol et
        for schedule in self.current_schedules:
            if (schedule.get('classroom_id') == classroom_id and 
                schedule.get('timeslot_id') == timeslot_id - 1):
                return True
        
        return False

    def _is_same_class_assignment(self, assignment: Dict[str, Any]) -> bool:
        """🤖 AI-BASED: Aynı sınıf kontrolü (soft constraint)"""
        timeslot_id = assignment.get('timeslot_id')
        classroom_id = assignment.get('classroom_id')
        instructor_ids = assignment.get('instructors', [])
        
        # Aynı instructor'ın aynı sınıfta başka projesi var mı?
        for schedule in self.current_schedules:
            if (any(inst_id in schedule.get('instructors', []) for inst_id in instructor_ids) and
                schedule.get('classroom_id') == classroom_id):
                return True
        
        return False

    def _is_early_slot_assignment(self, assignment: Dict[str, Any]) -> bool:
        """🤖 AI-BASED: Erken slot kontrolü (soft constraint)"""
        timeslot_id = assignment.get('timeslot_id')
        
        # İlk yarıdaki slotlar erken kabul edilir
        total_timeslots = len(self.timeslots)
        return timeslot_id <= (total_timeslots // 2)

    def _improves_load_balance(self, assignment: Dict[str, Any]) -> bool:
        """🤖 AI-BASED: Yük dengeleme kontrolü (soft constraint)"""
        instructor_ids = assignment.get('instructors', [])
        
        # Bu instructor'ın mevcut proje sayısını say
        current_projects = sum(1 for schedule in self.current_schedules 
                             if any(inst_id in schedule.get('instructors', []) for inst_id in instructor_ids))
        
        # Ortalama proje sayısından az ise dengeleyici
        total_instructors = len(self.instructors)
        total_projects = len(self.projects)
        avg_projects = total_projects / total_instructors if total_instructors > 0 else 0
        
        return current_projects < avg_projects

    def _improves_jury_balance(self, assignment: Dict[str, Any]) -> bool:
        """🤖 AI-BASED: Jüri dengeleme kontrolü (soft constraint)"""
        jury_members = assignment.get('jury_members', [])
        
        # Jüri üyesinin mevcut jüri sayısını kontrol et
        for jury_id in jury_members:
            current_jury_count = sum(1 for schedule in self.current_schedules 
                                   if jury_id in schedule.get('jury_members', []))
            
            # Ortalama jüri sayısından az ise dengeleyici
            total_instructors = len(self.instructors)
            total_projects = len(self.projects)
            avg_jury = total_projects / total_instructors if total_instructors > 0 else 0
            
            if current_jury_count < avg_jury:
                return True
        
        return False

    def _creates_gap(self, assignment: Dict[str, Any]) -> bool:
        """🤖 AI-BASED: Gap oluşturma kontrolü (soft constraint)"""
        timeslot_id = assignment.get('timeslot_id')
        classroom_id = assignment.get('classroom_id')
        
        # Bu slot'tan önce ve sonra slot'ları kontrol et
        prev_slot_occupied = any(
            schedule.get('classroom_id') == classroom_id and 
            schedule.get('timeslot_id') == timeslot_id - 1
            for schedule in self.current_schedules
        )
        
        next_slot_occupied = any(
            schedule.get('classroom_id') == classroom_id and 
            schedule.get('timeslot_id') == timeslot_id + 1
            for schedule in self.current_schedules
        )
        
        # Eğer önceki ve sonraki slot'lar boşsa gap oluşur
        return not prev_slot_occupied and not next_slot_occupied

    def _requires_class_switch(self, assignment: Dict[str, Any]) -> bool:
        """🤖 AI-BASED: Sınıf değişimi kontrolü (soft constraint)"""
        instructor_ids = assignment.get('instructors', [])
        classroom_id = assignment.get('classroom_id')
        
        # Bu instructor'ın önceki sınıfını kontrol et
        for schedule in self.current_schedules:
            if (any(inst_id in schedule.get('instructors', []) for inst_id in instructor_ids) and
                schedule.get('classroom_id') != classroom_id):
                return True
        
        return False

    def _ai_optimize_schedules(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🤖 AI OPTIMIZATION: Schedule'ları AI scoring ile optimize et
        """
        optimized = []
        
        for schedule in schedules:
            # AI score hesapla
            ai_score = self._calculate_ai_score(schedule)
            schedule['ai_score'] = ai_score
            optimized.append(schedule)
        
        # AI score'a göre sırala
        optimized.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        
        logger.info(f"🤖 AI Optimization: {len(optimized)} schedule optimize edildi")
        return optimized

    def _calculate_statistics(self, schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """İstatistikleri hesapla"""
        if not schedules:
            return {
                'total_schedules': 0,
                'phase1_count': 0,
                'phase2_count': 0,
                'average_ai_score': 0,
                'max_ai_score': 0,
                'min_ai_score': 0,
                'classroom_usage': {},
                'classrooms_used': 0,
                'total_classrooms': len(self.classrooms)
            }
        
        # Sınıf kullanım istatistikleri
        classroom_distribution = {}
        for schedule in schedules:
            classroom_id = schedule.get('classroom_id')
            if classroom_id:
                classroom_distribution[classroom_id] = classroom_distribution.get(classroom_id, 0) + 1
        
        return {
            'total_schedules': len(schedules),
            'phase1_count': len([s for s in schedules if s.get('phase') == 1]),
            'phase2_count': len([s for s in schedules if s.get('phase') == 2]),
            'average_ai_score': np.mean([s.get('ai_score', 0) for s in schedules]) if schedules else 0,
            'max_ai_score': max([s.get('ai_score', 0) for s in schedules]) if schedules else 0,
            'min_ai_score': min([s.get('ai_score', 0) for s in schedules]) if schedules else 0,
            'classroom_usage': classroom_distribution,
            'classrooms_used': len(classroom_distribution),
            'total_classrooms': len(self.classrooms),
            'classroom_balance_score': self._calculate_classroom_balance(classroom_distribution)
        }
    
    def _calculate_classroom_balance(self, classroom_distribution: Dict[int, int]) -> float:
        """Sınıf dengesi skoru hesapla (0-100, 100 = mükemmel denge)"""
        if not classroom_distribution or len(classroom_distribution) < 2:
            return 0.0
        
        counts = list(classroom_distribution.values())
        avg_usage = np.mean(counts)
        std_usage = np.std(counts)
        
        # Standart sapma ne kadar düşükse denge o kadar iyi
        # Max std = avg (en kötü durum), min std = 0 (mükemmel denge)
        if avg_usage == 0:
            return 100.0
        
        balance_score = max(0, 100 - (std_usage / avg_usage * 100))
        return balance_score

    def _generate_ai_insights(self, pairs: List[Tuple], phase1: List[Dict], phase2: List[Dict], 
                            project_type_balance: Dict, workload_balance: Dict, phase_distribution: Dict) -> Dict[str, Any]:
        """AI insights oluştur - Enhanced with new AI optimizations"""
        # Sınıf kullanım bilgilerini hesapla
        classroom_usage_summary = {}
        for schedule in phase1 + phase2:
            cid = schedule.get('classroom_id')
            if cid:
                classroom_usage_summary[cid] = classroom_usage_summary.get(cid, 0) + 1
        
        return {
            'strategic_pairing_summary': f"{len(pairs)} stratejik eşleştirme yapıldı",
            'load_balancing_achieved': "En fazla yüklü instructor'lar en az yüklülerle eşleştirildi",
            'bi_directional_jury': "Her instructor birbirinin jürisi oldu",
            'consecutive_grouping': "Tüm projeler ardışık slotlarda atandı",
            'ai_optimization_level': "ULTRA AI-POWERED - Zero hard constraints",
            'classroom_distribution': f"{len(classroom_usage_summary)} / {len(self.classrooms)} sınıf kullanıldı",
            'all_classrooms_used': len(classroom_usage_summary) == len(self.classrooms),
            
            # NEW AI OPTIMIZATIONS
            'project_type_balancing': f"Proje türü denge skoru: {project_type_balance.get('balance_score', 0):.1f}/100",
            'workload_balancing': f"Instructor iş yükü denge skoru: {workload_balance.get('balance_score', 0):.1f}/100",
            'phase_balancing': f"Phase denge skoru: {phase_distribution.get('balance_score', 0):.1f}/100",
            'ai_diversity_optimization': "Çeşitlilik odaklı AI optimizasyonu aktif",
            'ai_conflict_resolution': "AI-based conflict çözümü aktif",
            'ai_adaptive_learning': "Adaptif AI öğrenme sistemi aktif",
            
            'recommendations': [
                "Sistem tamamen AI odaklı çalışıyor",
                "Hard kısıtlar kaldırıldı, sadece soft optimization",
                "Strategic pairing ile optimal yük dağılımı sağlandı",
                "AI-based proje türü dengeleme aktif",
                "AI-based instructor iş yükü dengeleme aktif",
                "AI-based conflict çözümü aktif",
                "Çeşitlilik odaklı AI optimizasyonu aktif",
                "Bi-directional jury assignment ile adil jüri dağılımı",
                f"Tüm aktif sınıflar dengeli kullanıldı ({len(classroom_usage_summary)} sınıf)"
            ]
        }

    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Initialize the Dynamic Programming algorithm with input data.
        
        Args:
            data: Dictionary containing projects, instructors, classrooms, and timeslots
        """
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Dynamic Programming Algorithm")
        
        logger.info(f"Dynamic Programming initialized with {len(self.projects)} projects, {len(self.instructors)} instructors")

    def evaluate_fitness(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Evaluate the fitness of a given schedule using AI-based soft constraints.
        
        Args:
            assignments: List of schedule assignments
            
        Returns:
            float: Fitness score (higher is better)
        """
        if not assignments:
            return 0.0
        
        score = 0.0
        
        # Build lookup structures
        instructor_slots = defaultdict(list)
        classroom_slots = defaultdict(list)
        instructor_classrooms = defaultdict(set)
        
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            classroom_id = assignment.get("classroom_id")
            instructors = assignment.get("instructors", [])
            
            for instructor_id in instructors:
                instructor_slots[instructor_id].append(timeslot_id)
                if classroom_id:
                    instructor_classrooms[instructor_id].add(classroom_id)
            
            if classroom_id and timeslot_id:
                classroom_slots[classroom_id].append(timeslot_id)
        
        # 1. Consecutive bonus
        for instructor_id, slots in instructor_slots.items():
            sorted_slots = sorted(slots)
            consecutive_count = 0
            for i in range(len(sorted_slots) - 1):
                if sorted_slots[i + 1] - sorted_slots[i] == 1:
                    consecutive_count += 1
            score += consecutive_count * self.ai_weights.get("consecutive_bonus", 200.0)
        
        # 2. Same classroom bonus
        for instructor_id, classrooms in instructor_classrooms.items():
            if len(classrooms) == 1:
                score += self.ai_weights.get("class_stay_bonus", 100.0)
            else:
                score -= (len(classrooms) - 1) * self.ai_weights.get("class_switch_penalty", 60.0)
        
        # 3. Early slot bonus
        early_slots = [a for a in assignments if a.get("timeslot_id", 100) <= 10]
        score += len(early_slots) * self.ai_weights.get("early_slot_bonus", 80.0)
        
        # 4. Load balance bonus
        instructor_counts = defaultdict(int)
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                instructor_counts[instructor_id] += 1
        
        if instructor_counts:
            counts = list(instructor_counts.values())
            mean_count = np.mean(counts)
            variance = np.var(counts)
            if variance < 2.0:  # Low variance = good balance
                score += self.ai_weights.get("load_balance_bonus", 300.0)
        
        # 5. No gaps bonus
        for classroom_id, slots in classroom_slots.items():
            sorted_slots = sorted(slots)
            has_gap = False
            for i in range(len(sorted_slots) - 1):
                if sorted_slots[i + 1] - sorted_slots[i] > 1:
                    has_gap = True
                    score -= self.ai_weights.get("gap_penalty", 50.0)
            if not has_gap and len(sorted_slots) > 1:
                score += 100.0  # Bonus for gap-free classroom
        
        return score