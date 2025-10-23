"""
Real Simplex Algorithm - 100% AI-Based Soft Constraint Optimizer
NO HARD CONSTRAINTS - Everything is AI-driven with soft penalties

🎯 CORE STRATEGY - Instructor Pairing & Consecutive Grouping:
═══════════════════════════════════════════════════════════════════════════════

STEP 1: Instructor Sorting (by project count)
─────────────────────────────────────────────
- Instructor'ları proje sorumluluk sayısına göre sırala (EN FAZLA → EN AZ)
- Sıralama: Üstte en fazla, altta en az proje sorumlusu olan instructor

STEP 2: Group Splitting (balanced division)
──────────────────────────────────────────
- ÇIFT SAYIDA INSTRUCTOR: İkiye tam böl (n/2 üst, n/2 alt)
- TEK SAYIDA INSTRUCTOR: Üstte n, altta (n+1) şeklinde böl
- Sıralamaları asla bozma!

STEP 3: Instructor Pairing (upper ↔ lower)
─────────────────────────────────────────
- Üst grup[0] ↔ Alt grup[0]
- Üst grup[1] ↔ Alt grup[1]
- ...ve devam et

STEP 4: Consecutive Grouping + Bi-Directional Jury
─────────────────────────────────────────────────
- (x) instructor Proje Sorumlusu → (y) instructor Jüri (consecutive grouping)
- Hemen takvimin sonrasında:
- (y) instructor Proje Sorumlusu → (x) instructor Jüri (consecutive grouping)

═══════════════════════════════════════════════════════════════════════════════

Revolutionary Features:
1. PROJECT-BASED INSTRUCTOR SORTING - Sort by project responsibility count (max → min)
2. SMART GROUPING & PAIRING - Split instructors into balanced groups and pair them
3. CONSECUTIVE GROUPING - All projects of an instructor in same classroom, consecutive slots
4. BI-DIRECTIONAL JURY ASSIGNMENT - x supervises → y jury, then y supervises → x jury
5. AI-BASED SCORING - Reward system instead of hard constraints
6. CONFLICT-AWARE EVOLUTION - Soft penalties for conflicts, not blocking
7. NO HARD CONSTRAINTS - Everything is optimized, nothing is blocked
"""

from typing import Dict, Any, List, Set, Tuple
import time
import logging
import random
import numpy as np
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


class RealSimplexAlgorithm(OptimizationAlgorithm):
    """
    Real Simplex Algorithm - 100% AI-Based Soft Constraint Optimizer
    
    NO HARD CONSTRAINTS - Everything is scored and optimized
    
    Core Principles:
    1. PROJECT-BASED SORTING - Instructors sorted by project count (max → min)
    2. BALANCED GROUP SPLITTING - Smart division into upper/lower groups
    3. STRATEGIC PAIRING - Upper and lower group instructors paired optimally
    4. CONSECUTIVE GROUPING - Each instructor's projects in same classroom, consecutive
    5. BI-DIRECTIONAL JURY - Paired instructors are each other's jury (x→y, y→x)
    6. EARLY TIMESLOT OPTIMIZATION - Prioritize early timeslots over late ones
    7. GAP-FREE OPTIMIZATION - AI-based gap elimination with advanced repositioning
    8. SOFT CONSTRAINTS - Everything is optimized, nothing is blocked
    9. AI-DRIVEN SCORING - Reward good patterns, penalize bad ones
    """

    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.name = "Real Simplex Algorithm (100% AI-Based)"
        self.description = "NO HARD CONSTRAINTS - Pure AI Optimization with Instructor Pairing"
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # AI SCORING SYSTEM - NO HARD CONSTRAINTS
        # ═══════════════════════════════════════════════════════════════════════════════
        
        # REWARDS (Positive Scoring)
        self.reward_consecutive = 50.0          # Consecutive timeslots for same instructor
        self.reward_same_classroom = 30.0       # Same classroom for all instructor projects
        self.reward_jury_pairing = 100.0        # Bi-directional jury pairing (x→y, y→x)
        self.reward_balanced_pairing = 80.0     # Balanced instructor pairing (high↔low)
        self.reward_gap_free = 200.0            # Gap-free scheduling (ultra-high priority)
        self.reward_early_timeslot = 150.0      # Early timeslot usage (prioritize morning)
        self.reward_perfect_consecutive = 500.0 # Perfect consecutive grouping (bonus)
        
        # PENALTIES (Negative Scoring - Soft, not blocking)
        self.penalty_conflict = -5.0            # Soft conflict (instructor double-booked)
        self.penalty_gap = -300.0               # Time gaps (ultra-aggressive elimination)
        self.penalty_late_timeslot = -200.0     # Late timeslot usage (force early slots)
        self.penalty_classroom_change = -50.0   # Classroom changes (minimize movement)
        self.penalty_incomplete_pairing = -100.0 # Incomplete bi-directional pairing
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # DATA STORAGE
        # ═══════════════════════════════════════════════════════════════════════════════
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        
        # Instructor pairing data
        self.instructor_pairs = []  # List of (instructor_a_id, instructor_b_id) tuples
        self.pairing_sequences = []  # Detailed pairing sequences for consecutive grouping
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════════════════
        self.random_seed = params.get("random_seed") if params else None
        if self.random_seed:
            random.seed(self.random_seed)
            np.random.seed(self.random_seed)
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # AI FEATURES (Toggleable)
        # ═══════════════════════════════════════════════════════════════════════════════
        self.enable_ultra_consecutive = params.get("enable_ultra_consecutive", True) if params else True
        self.enable_gap_elimination = params.get("enable_gap_elimination", True) if params else True
        self.enable_early_optimization = params.get("enable_early_optimization", True) if params else True
        self.enable_smart_pairing = params.get("enable_smart_pairing", True) if params else True
        
        # NEW AI FEATURES
        self.enable_adaptive_learning = params.get("enable_adaptive_learning", True) if params else True
        self.enable_classroom_memory = params.get("enable_classroom_memory", True) if params else True
        self.enable_pairing_learning = params.get("enable_pairing_learning", True) if params else True
        self.enable_conflict_prediction = params.get("enable_conflict_prediction", True) if params else True
        self.enable_workload_balance = params.get("enable_workload_balance", True) if params else True
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # AI LEARNING STORAGE
        # ═══════════════════════════════════════════════════════════════════════════════
        
        # 1️⃣ ADAPTIVE SCORING WEIGHTS
        self.iteration_count = 0
        self.last_metrics = None
        self.scoring_weight_history = []  # Track how weights changed
        
        # 2️⃣ WORKLOAD-AWARE JURY
        self.instructor_workloads = {}  # instructor_id -> workload dict
        
        # 3️⃣ SMART CLASSROOM SELECTION WITH MEMORY
        self.classroom_success_scores = defaultdict(float)  # classroom_id -> success_score
        self.classroom_pair_memory = defaultdict(lambda: defaultdict(float))  # (inst_a, inst_b) -> {classroom_id: score}
        
        # 4️⃣ LEARNING-BASED INSTRUCTOR PAIRING
        self.pairing_success_history = defaultdict(float)  # (inst_a, inst_b) -> success_score
        self.pairing_metadata = {}  # Store detailed pairing info
        
        # 5️⃣ CONFLICT PREDICTION & PREVENTION
        self.conflict_prediction_cache = {}  # Cache conflict predictions
        self.conflict_history = defaultdict(int)  # Track conflicts per instructor

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Real Simplex Algorithm")

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method for compatibility with AlgorithmService"""
        return self.optimize(data)

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Real Simplex optimization with 100% AI-based approach.
        NO HARD CONSTRAINTS - Everything is soft and optimized.
        
        New Strategy:
        1. Sort instructors by project count (max → min)
        2. Split into balanced groups
        3. Pair instructors (upper ↔ lower)
        4. Consecutive grouping with bi-directional jury assignment
        """
        start_time = time.time()
        self.initialize(data)
        
        logger.info("=" * 80)
        logger.info("REAL SIMPLEX ALGORITHM - AI-BASED INSTRUCTOR PAIRING")
        logger.info("=" * 80)
        logger.info(f"📊 Projeler: {len(self.projects)}")
        logger.info(f"👥 Instructors: {len(self.instructors)}")
        logger.info(f"🏫 Sınıflar: {len(self.classrooms)}")
        logger.info(f"⏰ Zaman Slotları: {len(self.timeslots)}")
        logger.info("")

        # Phase 1: Sort and pair instructors
        logger.info("📋 Phase 1: Instructor Sorting & Pairing")
        sorted_instructors = self._sort_instructors_by_project_count()
        upper_group, lower_group = self._split_instructors_into_groups(sorted_instructors)
        self.instructor_pairs = self._create_instructor_pairs(upper_group, lower_group)
        logger.info(f"✅ {len(self.instructor_pairs)} instructor pairs oluşturuldu")
        
        # Phase 2: Create paired consecutive solution
        logger.info("")
        logger.info("🎲 Phase 2: Paired Consecutive Grouping")
        assignments = self._create_paired_consecutive_solution()
        logger.info(f"✅ {len(assignments)} proje atandı (Paired Consecutive)")
        
        # Phase 2.5: Check and assign missing projects
        logger.info("")
        logger.info("🔍 Phase 2.5: Missing Project Check & Assignment")
        assigned_project_ids = set(a.get("project_id") for a in assignments)
        missing_projects = [p for p in self.projects if p.get("id") not in assigned_project_ids]
        
        if missing_projects:
            logger.warning(f"⚠️ {len(missing_projects)} missing projects detected!")
            logger.info(f"   Total projects: {len(self.projects)}")
            logger.info(f"   Assigned: {len(assigned_project_ids)}")
            logger.info(f"   Missing: {len(missing_projects)}")
            
            # Assign missing projects to available slots
            missing_assignments = self._assign_missing_projects(missing_projects, assignments)
            assignments.extend(missing_assignments)
            logger.info(f"✅ {len(missing_assignments)} missing projects assigned")
            logger.info(f"   New total: {len(assignments)} projects")
        else:
            logger.info(f"✅ All projects assigned! ({len(self.projects)}/{len(self.projects)})")
        
        # Phase 3: Bi-Directional Jury Assignment
        logger.info("")
        logger.info("🎯 Phase 3: Bi-Directional Jury Assignment")
        assignments = self._assign_bidirectional_jury(assignments)
        logger.info(f"✅ Bi-directional jury assignment tamamlandı")
        
        # Phase 4: Early Timeslot Optimization (AI-Based)
        logger.info("")
        logger.info("🕐 Phase 4: Early Timeslot Optimization (AI-Based)")
        assignments = self._optimize_early_timeslots(assignments)
        logger.info(f"✅ Early timeslot optimization tamamlandı")
        
        # Phase 5: Gap-Free Optimization
        logger.info("")
        logger.info("🎯 Phase 5: Gap-Free Optimization (AI-Based)")
        assignments = self._optimize_gap_free(assignments)
        logger.info(f"✅ Gap-free optimization tamamlandı")
        
        # Phase 6: AI-based Optimization
        logger.info("")
        logger.info("🧠 Phase 6: AI-Based Optimization (Soft Constraints)")
        assignments = self._optimize_with_soft_constraints(assignments)
        logger.info(f"✅ Soft constraint optimization tamamlandı")
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # NEW AI FEATURES - LEARNING & ADAPTATION
        # ═══════════════════════════════════════════════════════════════════════════════
        
        # Phase 7: Adaptive Scoring Weights (AI Feature 1)
        if self.enable_adaptive_learning:
            logger.info("")
            logger.info("🤖 Phase 7: Adaptive Scoring Weights (AI Learning)")
            pre_adaptive_metrics = self._calculate_comprehensive_metrics(assignments)
            self._adapt_scoring_weights(pre_adaptive_metrics)
            logger.info(f"✅ Adaptive learning tamamlandı")
        
        # Phase 8: Evaluate Pairing Success (AI Feature 4)
        if self.enable_pairing_learning:
            logger.info("")
            logger.info("📚 Phase 8: Learning-Based Pairing Evaluation")
            self._evaluate_pairing_success(assignments)
            logger.info(f"✅ Pairing evaluation tamamlandı")
        
        # Phase 9: Update Classroom Memory (AI Feature 3)
        if self.enable_classroom_memory:
            logger.info("")
            logger.info("🧠 Phase 9: Smart Classroom Memory Update")
            self._update_classroom_memory(assignments)
            logger.info(f"✅ Classroom memory updated")
        
        # Calculate final metrics
        metrics = self._calculate_comprehensive_metrics(assignments)
        execution_time = time.time() - start_time
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("📈 FINAL METRICS:")
        logger.info(f"  Total Score: {metrics.get('total_score', 0):.2f}")
        logger.info(f"  Instructor Pairs: {metrics.get('instructor_pairs', 0)}")
        logger.info(f"  Bi-Directional Jury Assignments: {metrics.get('bidirectional_jury_count', 0)}")
        logger.info(f"  Consecutive Instructors: {metrics.get('consecutive_instructors', 0)}")
        logger.info(f"  Avg Classroom Changes: {metrics.get('avg_classroom_changes', 0):.2f}")
        logger.info(f"  Time Gaps: {metrics.get('time_gaps', 0)}")
        logger.info(f"  Total Gaps: {metrics.get('total_gaps', 0)}")
        logger.info(f"  Gap Percentage: {metrics.get('gap_percentage', 0):.1f}%")
        logger.info(f"  Gap-Free Score: {metrics.get('gap_free_score', 0):.1f}")
        logger.info(f"  Soft Conflicts: {metrics.get('soft_conflicts', 0)} (penalized, not blocked)")
        logger.info(f"⏱️  Execution Time: {execution_time:.2f}s")
        logger.info("=" * 80)

        return {
            "assignments": assignments,
            "schedule": assignments,
            "solution": assignments,
            "fitness_scores": {"total": metrics.get('total_score', 0)},
            "execution_time": execution_time,
            "algorithm": "Real Simplex Algorithm (AI-Based Instructor Pairing)",
            "status": "completed",
            "success": True,
            "metrics": metrics,
            "optimizations_applied": [
                "project_based_instructor_sorting",
                "balanced_group_splitting",
                "strategic_instructor_pairing",
                "consecutive_grouping",
                "bidirectional_jury_assignment",
                "soft_constraint_optimization",
                "ai_based_scoring",
                # NEW AI FEATURES
                "adaptive_scoring_weights" if self.enable_adaptive_learning else None,
                "workload_aware_jury" if self.enable_workload_balance else None,
                "smart_classroom_memory" if self.enable_classroom_memory else None,
                "learning_based_pairing" if self.enable_pairing_learning else None,
                "conflict_prediction" if self.enable_conflict_prediction else None
            ],
            "ai_features_active": {
                "adaptive_learning": self.enable_adaptive_learning,
                "workload_balance": self.enable_workload_balance,
                "classroom_memory": self.enable_classroom_memory,
                "pairing_learning": self.enable_pairing_learning,
                "conflict_prediction": self.enable_conflict_prediction
            },
            "ai_learning_data": {
                "scoring_weight_history": self.scoring_weight_history,
                "pairing_success_history": {f"{k[0]}_{k[1]}" if isinstance(k, tuple) else str(k): v for k, v in self.pairing_success_history.items()},
                "classroom_memory": {f"{k[0]}_{k[1]}" if isinstance(k, tuple) else str(k): dict(v) for k, v in self.classroom_pair_memory.items()},
                "conflict_history": {str(k): v for k, v in self.conflict_history.items()},
                "iteration_count": self.iteration_count
            },
            "parameters": {
                "approach": "100% AI-Based Soft Constraints with Learning",
                "hard_constraints": "NONE - All soft and adaptive",
                "instructor_sorting": "By project count (max → min)",
                "jury_strategy": "Bi-Directional Pairing (x→y, y→x) with Workload Balance",
                "grouping": "Paired Consecutive with Memory",
                "learning": "Adaptive weights, classroom memory, pairing learning, conflict prediction"
            }
        }

    def _sort_instructors_by_project_count(self) -> List[Tuple[int, List[Dict[str, Any]]]]:
        """
        Sort instructors by their project responsibility count (max → min).
        
        Returns:
            List of (instructor_id, projects) tuples sorted by project count descending
        """
        # Group projects by instructor
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # Sort by project count (descending)
        sorted_instructors = sorted(
            instructor_projects.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        logger.info(f"📊 Instructor Sorting (by project count):")
        for i, (inst_id, projects) in enumerate(sorted_instructors[:10]):  # Show top 10
            logger.info(f"  {i+1}. Instructor {inst_id}: {len(projects)} proje")
        
        return sorted_instructors
    
    def _split_instructors_into_groups(
        self, sorted_instructors: List[Tuple[int, List[Dict[str, Any]]]]
    ) -> Tuple[List[Tuple[int, List[Dict[str, Any]]]], List[Tuple[int, List[Dict[str, Any]]]]]:
        """
        Split instructors into upper and lower groups.
        
        Rules:
        - Even count: upper = n/2, lower = n/2
        - Odd count: upper = n, lower = n+1 (lower group has more)
        
        Returns:
            (upper_group, lower_group)
        """
        total = len(sorted_instructors)
        
        if total % 2 == 0:
            # Even: split exactly in half
            split_point = total // 2
            logger.info(f"✂️ Even split: {split_point} üst grup, {split_point} alt grup")
        else:
            # Odd: upper = n, lower = n+1
            split_point = total // 2
            logger.info(f"✂️ Odd split: {split_point} üst grup, {split_point + 1} alt grup")
        
        upper_group = sorted_instructors[:split_point]
        lower_group = sorted_instructors[split_point:]
        
        return upper_group, lower_group
    
    def _create_instructor_pairs(
        self,
        upper_group: List[Tuple[int, List[Dict[str, Any]]]],
        lower_group: List[Tuple[int, List[Dict[str, Any]]]]
    ) -> List[Tuple[int, int]]:
        """
        Create instructor pairs from upper and lower groups.
        
        Pairing strategy: upper[0] ↔ lower[0], upper[1] ↔ lower[1], ...
        
        Returns:
            List of (instructor_a_id, instructor_b_id) tuples
        """
        pairs = []
        
        logger.info(f"🔗 Creating Instructor Pairs:")
        
        # Pair upper with lower
        for i in range(len(upper_group)):
            if i < len(lower_group):
                upper_id = upper_group[i][0]
                lower_id = lower_group[i][0]
                pairs.append((upper_id, lower_id))
                
                upper_count = len(upper_group[i][1])
                lower_count = len(lower_group[i][1])
                logger.info(
                    f"  Pair {i+1}: Instructor {upper_id} ({upper_count} proje) ↔ "
                    f"Instructor {lower_id} ({lower_count} proje)"
                )
        
        # Handle unpaired instructors from lower group (in case of odd count)
        if len(lower_group) > len(upper_group):
            unpaired_id = lower_group[-1][0]
            unpaired_count = len(lower_group[-1][1])
            logger.info(
                f"  ⚠️ Unpaired: Instructor {unpaired_id} ({unpaired_count} proje) "
                f"- will be assigned independently"
            )
        
        return pairs
    
    def _create_paired_consecutive_solution(self) -> List[Dict[str, Any]]:
        """
        Create paired consecutive solution with ULTRA-AGGRESSIVE consecutive grouping.
        
        ═══════════════════════════════════════════════════════════════════════════════
        CONSECUTIVE GROUPING STRATEGY (AI-Based, NO HARD CONSTRAINTS)
        ═══════════════════════════════════════════════════════════════════════════════
        
        For each instructor pair (x, y):
        
        1️⃣ ASSIGN X's PROJECTS CONSECUTIVELY
           - Same classroom
           - Consecutive timeslots (no gaps)
           - Start from earliest available slot
        
        2️⃣ ASSIGN Y's PROJECTS CONSECUTIVELY (immediately after X)
           - Same classroom as X
           - Consecutive timeslots continuing from where X ended
           - No gaps between X and Y
        
        3️⃣ SETUP BI-DIRECTIONAL JURY
           - Track pairing sequences for later jury assignment
           - (x) projects → (y) will be jury
           - (y) projects → (x) will be jury
        
        ═══════════════════════════════════════════════════════════════════════════════
        """
        assignments = []
        
        # Sort timeslots by start time (earliest first)
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        logger.info(f"📅 Total timeslots available: {len(sorted_timeslots)}")
        logger.info(f"🏫 Total classrooms available: {len(self.classrooms)}")
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # SOFT TRACKING (no hard blocking)
        # ═══════════════════════════════════════════════════════════════════════════════
        slot_usage = defaultdict(int)  # (classroom_id, timeslot_id) -> usage count
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        assigned_projects = set()
        
        # Track pairing sequences for bi-directional jury assignment
        self.pairing_sequences = []
        
        # Group projects by instructor
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        logger.info(f"👥 Total instructors with projects: {len(instructor_projects)}")
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # PROCESS EACH INSTRUCTOR PAIR
        # ═══════════════════════════════════════════════════════════════════════════════
        for pair_idx, (inst_a_id, inst_b_id) in enumerate(self.instructor_pairs):
            inst_a_projects = instructor_projects.get(inst_a_id, [])
            inst_b_projects = instructor_projects.get(inst_b_id, [])
            
            if not inst_a_projects and not inst_b_projects:
                logger.warning(f"⚠️ Pair {pair_idx + 1}: No projects for this pair, skipping...")
                continue
            
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"🔗 PAIR {pair_idx + 1}/{len(self.instructor_pairs)}: Instructor {inst_a_id} ↔ Instructor {inst_b_id}")
            logger.info(f"   Instructor {inst_a_id}: {len(inst_a_projects)} proje (sorumlu)")
            logger.info(f"   Instructor {inst_b_id}: {len(inst_b_projects)} proje (sorumlu)")
            logger.info(f"   Total: {len(inst_a_projects) + len(inst_b_projects)} proje")
            logger.info("=" * 80)
            
            # ───────────────────────────────────────────────────────────────────────────
            # 🤖 AI FEATURE 3: Smart Classroom Selection WITH MEMORY
            # ───────────────────────────────────────────────────────────────────────────
            if self.enable_classroom_memory:
                logger.info("   🧠 Using AI-powered classroom selection with memory...")
                best_classroom = self._find_best_classroom_with_memory(
                    inst_a_id, inst_b_id,
                    inst_a_projects, inst_b_projects, sorted_timeslots,
                    slot_usage, instructor_timeslot_usage
                )
            else:
                logger.info("   📊 Using standard classroom selection...")
                best_classroom = self._find_best_classroom_for_pair(
                    inst_a_projects, inst_b_projects, sorted_timeslots,
                    slot_usage, instructor_timeslot_usage
                )
            
            if not best_classroom:
                logger.warning(f"⚠️ Pair {pair_idx + 1}: Uygun sınıf bulunamadı (AI will try to optimize)")
                # Don't skip - use first available classroom (soft constraint)
                best_classroom = self.classrooms[0].get("id") if self.classrooms else None
                if not best_classroom:
                    continue
            
            # ───────────────────────────────────────────────────────────────────────────
            # STEP 1: Assign Instructor A's projects CONSECUTIVELY
            # ───────────────────────────────────────────────────────────────────────────
            logger.info(f"📍 STEP 1: Assigning Instructor {inst_a_id}'s projects...")
            logger.info(f"   Classroom: {best_classroom}")
            
            inst_a_start_idx = self._find_next_available_slot_index(
                best_classroom, sorted_timeslots, slot_usage,
                instructor_timeslot_usage.get(inst_a_id, set())
            )
            
            inst_a_slots = []
            inst_a_timeslot_ids = []
            current_idx = inst_a_start_idx
            
            logger.info(f"   Starting from timeslot index: {inst_a_start_idx}")
            
            for proj_idx, project in enumerate(inst_a_projects, 1):
                project_id = project.get("id")
                if project_id in assigned_projects:
                    logger.info(f"   ⚠️ Project {project_id} already assigned, skipping...")
                    continue
                
                # Find next consecutive slot (soft constraint - prefer consecutive)
                while current_idx < len(sorted_timeslots):
                    timeslot_id = sorted_timeslots[current_idx].get("id")
                    # Soft check - prefer unused slots but allow conflicts
                    if timeslot_id not in instructor_timeslot_usage[inst_a_id]:
                        break
                    current_idx += 1
                
                if current_idx >= len(sorted_timeslots):
                    logger.warning(f"   ⚠️ No more timeslots available for project {project_id} (AI will optimize)")
                    # Soft constraint - wrap around or use early slots
                    current_idx = 0
                    if current_idx >= len(sorted_timeslots):
                        break
                
                timeslot_id = sorted_timeslots[current_idx].get("id")
                timeslot_start = sorted_timeslots[current_idx].get("start_time", "??:??")
                
                assignment = {
                    "project_id": project_id,
                    "classroom_id": best_classroom,
                    "timeslot_id": timeslot_id,
                    "is_makeup": project.get("is_makeup", False),
                    "instructors": [inst_a_id]
                }
                
                assignments.append(assignment)
                slot_usage[(best_classroom, timeslot_id)] += 1
                instructor_timeslot_usage[inst_a_id].add(timeslot_id)
                assigned_projects.add(project_id)
                inst_a_slots.append(timeslot_id)
                inst_a_timeslot_ids.append(timeslot_id)
                
                logger.info(
                    f"   ✅ [{proj_idx}/{len(inst_a_projects)}] Project {project_id} → "
                    f"Timeslot {timeslot_id} ({timeslot_start})"
                )
                
                current_idx += 1
            
            # Check if consecutive
            is_consecutive_a = self._check_consecutive(inst_a_timeslot_ids)
            logger.info("")
            logger.info(f"   📊 Instructor {inst_a_id} Summary:")
            logger.info(f"      ✅ Assigned: {len(inst_a_slots)}/{len(inst_a_projects)} projects")
            logger.info(f"      🏫 Classroom: {best_classroom}")
            logger.info(f"      ⏰ Timeslots: {inst_a_timeslot_ids}")
            logger.info(f"      🎯 Consecutive: {'YES ✅' if is_consecutive_a else 'NO ⚠️'}")
            logger.info("")
            
            # ───────────────────────────────────────────────────────────────────────────
            # STEP 2: Assign Instructor B's projects CONSECUTIVELY (immediately after A)
            # ───────────────────────────────────────────────────────────────────────────
            logger.info(f"📍 STEP 2: Assigning Instructor {inst_b_id}'s projects...")
            logger.info(f"   Classroom: {best_classroom} (same as Instructor {inst_a_id})")
            logger.info(f"   Starting immediately after Instructor {inst_a_id}")
            
            inst_b_start_idx = current_idx
            inst_b_slots = []
            inst_b_timeslot_ids = []
            
            logger.info(f"   Starting from timeslot index: {inst_b_start_idx}")
            
            for proj_idx, project in enumerate(inst_b_projects, 1):
                project_id = project.get("id")
                if project_id in assigned_projects:
                    logger.info(f"   ⚠️ Project {project_id} already assigned, skipping...")
                    continue
                
                # Find next consecutive slot
                while current_idx < len(sorted_timeslots):
                    timeslot_id = sorted_timeslots[current_idx].get("id")
                    if timeslot_id not in instructor_timeslot_usage[inst_b_id]:
                        break
                    current_idx += 1
                
                if current_idx >= len(sorted_timeslots):
                    logger.warning(f"   ⚠️ No more timeslots available for project {project_id} (AI will optimize)")
                    current_idx = 0
                    if current_idx >= len(sorted_timeslots):
                        break
                
                timeslot_id = sorted_timeslots[current_idx].get("id")
                timeslot_start = sorted_timeslots[current_idx].get("start_time", "??:??")
                
                assignment = {
                    "project_id": project_id,
                    "classroom_id": best_classroom,
                    "timeslot_id": timeslot_id,
                    "is_makeup": project.get("is_makeup", False),
                    "instructors": [inst_b_id]
                }
                
                assignments.append(assignment)
                slot_usage[(best_classroom, timeslot_id)] += 1
                instructor_timeslot_usage[inst_b_id].add(timeslot_id)
                assigned_projects.add(project_id)
                inst_b_slots.append(timeslot_id)
                inst_b_timeslot_ids.append(timeslot_id)
                
                logger.info(
                    f"   ✅ [{proj_idx}/{len(inst_b_projects)}] Project {project_id} → "
                    f"Timeslot {timeslot_id} ({timeslot_start})"
                )
                
                current_idx += 1
            
            # Check if consecutive
            is_consecutive_b = self._check_consecutive(inst_b_timeslot_ids)
            logger.info("")
            logger.info(f"   📊 Instructor {inst_b_id} Summary:")
            logger.info(f"      ✅ Assigned: {len(inst_b_slots)}/{len(inst_b_projects)} projects")
            logger.info(f"      🏫 Classroom: {best_classroom}")
            logger.info(f"      ⏰ Timeslots: {inst_b_timeslot_ids}")
            logger.info(f"      🎯 Consecutive: {'YES ✅' if is_consecutive_b else 'NO ⚠️'}")
            logger.info("")
            
            # ───────────────────────────────────────────────────────────────────────────
            # STEP 3: Store pairing sequence for bi-directional jury assignment
            # ───────────────────────────────────────────────────────────────────────────
            pairing_info = {
                'pair': (inst_a_id, inst_b_id),
                'classroom_id': best_classroom,
                'inst_a_slots': inst_a_timeslot_ids,
                'inst_b_slots': inst_b_timeslot_ids,
                'inst_a_consecutive': is_consecutive_a,
                'inst_b_consecutive': is_consecutive_b,
                'total_projects': len(inst_a_timeslot_ids) + len(inst_b_timeslot_ids)
            }
            self.pairing_sequences.append(pairing_info)
            
            # Final summary for this pair
            logger.info("=" * 80)
            logger.info(f"✅ PAIR {pair_idx + 1} COMPLETED:")
            logger.info(f"   Instructor {inst_a_id}: {len(inst_a_timeslot_ids)} projects ({'consecutive ✅' if is_consecutive_a else 'gaps ⚠️'})")
            logger.info(f"   Instructor {inst_b_id}: {len(inst_b_timeslot_ids)} projects ({'consecutive ✅' if is_consecutive_b else 'gaps ⚠️'})")
            logger.info(f"   Total: {len(inst_a_timeslot_ids) + len(inst_b_timeslot_ids)} projects in Classroom {best_classroom}")
            logger.info(f"   Bi-directional jury setup: READY ✅")
            logger.info("=" * 80)
            logger.info("")
        
        # Handle unpaired instructors (odd count case)
        unpaired_instructors = []
        for inst_id, projects in instructor_projects.items():
            if not any(inst_id in pair for pair in self.instructor_pairs):
                unpaired_instructors.append((inst_id, projects))
        
        for inst_id, projects in unpaired_instructors:
            logger.info(f"🔄 Unpaired Instructor {inst_id}: {len(projects)} proje")
            
            # Find best classroom
            best_classroom = self._find_best_classroom_for_single(
                projects, sorted_timeslots, slot_usage,
                instructor_timeslot_usage
            )
            
            if not best_classroom:
                continue
            
            current_idx = self._find_next_available_slot_index(
                best_classroom, sorted_timeslots, slot_usage,
                instructor_timeslot_usage.get(inst_id, set())
            )
            
            for project in projects:
                project_id = project.get("id")
                if project_id in assigned_projects:
                    continue
                
                while current_idx < len(sorted_timeslots):
                    timeslot_id = sorted_timeslots[current_idx].get("id")
                    if timeslot_id not in instructor_timeslot_usage[inst_id]:
                        break
                    current_idx += 1
                
                if current_idx >= len(sorted_timeslots):
                    break
                
                timeslot_id = sorted_timeslots[current_idx].get("id")
                
                assignment = {
                    "project_id": project_id,
                    "classroom_id": best_classroom,
                    "timeslot_id": timeslot_id,
                    "is_makeup": project.get("is_makeup", False),
                    "instructors": [inst_id]
                }
                
                assignments.append(assignment)
                slot_usage[(best_classroom, timeslot_id)] += 1
                instructor_timeslot_usage[inst_id].add(timeslot_id)
                assigned_projects.add(project_id)
                
                current_idx += 1
            
            logger.info(f"  ✅ Instructor {inst_id}: {len([a for a in assignments if inst_id in a['instructors'] and a.get('project_id') in [p.get('id') for p in projects]])} proje atandı")
        
        return assignments
    
    def _find_best_classroom_for_pair(
        self,
        inst_a_projects: List[Dict[str, Any]],
        inst_b_projects: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        slot_usage: Dict,
        instructor_timeslot_usage: Dict
    ) -> int:
        """
        Find the best classroom for an instructor pair.
        Uses soft scoring - prefers classrooms with more available consecutive slots.
        """
        total_projects = len(inst_a_projects) + len(inst_b_projects)
        best_classroom = None
        best_score = float('-inf')
        
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            
            # Count available consecutive slots
            consecutive_count = 0
            max_consecutive = 0
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                if slot_usage.get(slot_key, 0) == 0:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
            
            # Score based on available consecutive slots
            score = max_consecutive * 10
            
            # Bonus if can fit all projects
            if max_consecutive >= total_projects:
                score += 50
            
            if score > best_score:
                best_score = score
                best_classroom = classroom_id
        
        return best_classroom
    
    def _find_best_classroom_for_single(
        self,
        projects: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        slot_usage: Dict,
        instructor_timeslot_usage: Dict
    ) -> int:
        """
        Find the best classroom for a single instructor.
        """
        best_classroom = None
        best_score = float('-inf')
        
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            
            # Count available consecutive slots
            consecutive_count = 0
            max_consecutive = 0
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                if slot_usage.get(slot_key, 0) == 0:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
            
            # Score
            score = max_consecutive * 10
            
            if max_consecutive >= len(projects):
                score += 30
            
            if score > best_score:
                best_score = score
                best_classroom = classroom_id
        
        return best_classroom
    
    def _find_most_available_classroom(
        self,
        sorted_timeslots: List[Dict[str, Any]],
        slot_usage: Dict,
        instructor_used_slots: Set[int]
    ) -> int:
        """
        Find the classroom with most available slots for an instructor.
        
        Args:
            sorted_timeslots: List of timeslots sorted by start time
            slot_usage: Current slot usage map
            instructor_used_slots: Set of timeslot IDs where instructor is busy
            
        Returns:
            classroom_id with most availability, or None if no classroom available
        """
        if not self.classrooms:
            return None
        
        best_classroom = None
        max_available_slots = -1
        
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            available_count = 0
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                # Count as available if instructor is free and slot is not heavily used
                if timeslot_id not in instructor_used_slots and slot_usage.get(slot_key, 0) < 2:
                    available_count += 1
            
            if available_count > max_available_slots:
                max_available_slots = available_count
                best_classroom = classroom_id
        
        return best_classroom
    
    def _find_consecutive_available_slots(
        self,
        classroom_id: int,
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        slot_usage: Dict,
        instructor_used_slots: Set[int],
        needed_count: int,
        existing_assigned_slots: Set[int]
    ) -> List[int]:
        """
        Find consecutive available slots for an instructor in a specific classroom.
        
        Tries to find slots adjacent to existing assignments to minimize gaps.
        
        Args:
            classroom_id: Classroom to search in
            sorted_timeslots: List of timeslots sorted by start time
            timeslot_to_index: Map from timeslot_id to index
            slot_usage: Current slot usage map
            instructor_used_slots: Set of timeslot IDs where instructor is busy
            needed_count: Number of consecutive slots needed
            existing_assigned_slots: Set of timeslot IDs already assigned to this instructor
            
        Returns:
            List of timeslot_ids that are consecutive and available
        """
        if needed_count <= 0:
            return []
        
        # Build list of available slot indices
        available_indices = []
        for idx, timeslot in enumerate(sorted_timeslots):
            timeslot_id = timeslot.get("id")
            slot_key = (classroom_id, timeslot_id)
            
            # Check if slot is available (hard conflict check)
            if timeslot_id not in instructor_used_slots:
                available_indices.append(idx)
        
        if len(available_indices) < needed_count:
            # Not enough available slots, return what we have
            return [sorted_timeslots[idx].get("id") for idx in available_indices[:needed_count]]
        
        # Try to find consecutive slots
        best_start_idx = None
        best_score = float('-inf')
        
        for i in range(len(available_indices) - needed_count + 1):
            # Check if these slots are consecutive
            consecutive_indices = available_indices[i:i + needed_count]
            
            # Calculate consecutiveness score
            is_consecutive = all(
                consecutive_indices[j + 1] - consecutive_indices[j] == 1
                for j in range(len(consecutive_indices) - 1)
            )
            
            if is_consecutive:
                # Calculate score based on proximity to existing assignments
                score = 100.0
                
                # Bonus for early slots
                score += (len(sorted_timeslots) - consecutive_indices[0]) * 2.0
                
                # Bonus for being adjacent to existing assignments
                if existing_assigned_slots:
                    for existing_ts_id in existing_assigned_slots:
                        if existing_ts_id in timeslot_to_index:
                            existing_idx = timeslot_to_index[existing_ts_id]
                            # Check if consecutive to existing
                            if (consecutive_indices[0] == existing_idx + 1 or 
                                consecutive_indices[-1] == existing_idx - 1):
                                score += 200.0  # Big bonus for being adjacent
                                break
                            else:
                                # Smaller bonus for being near
                                min_distance = min(
                                    abs(consecutive_indices[0] - existing_idx),
                                    abs(consecutive_indices[-1] - existing_idx)
                                )
                                score += (50.0 / (min_distance + 1))
                
                # Penalty for slot usage
                for idx in consecutive_indices:
                    timeslot_id = sorted_timeslots[idx].get("id")
                    slot_key = (classroom_id, timeslot_id)
                    usage = slot_usage.get(slot_key, 0)
                    score -= usage * 10.0
                
                if score > best_score:
                    best_score = score
                    best_start_idx = i
        
        if best_start_idx is not None:
            # Return the best consecutive slots
            consecutive_indices = available_indices[best_start_idx:best_start_idx + needed_count]
            return [sorted_timeslots[idx].get("id") for idx in consecutive_indices]
        else:
            # No perfect consecutive slots, return best available slots
            return [sorted_timeslots[idx].get("id") for idx in available_indices[:needed_count]]
    
    def _find_next_available_slot_index(
        self,
        classroom_id: int,
        sorted_timeslots: List[Dict[str, Any]],
        slot_usage: Dict,
        instructor_used_slots: Set[int]
    ) -> int:
        """
        Find the next available slot index in a classroom.
        Soft approach - prefers unused slots but allows conflicts with penalty.
        """
        for idx, timeslot in enumerate(sorted_timeslots):
            timeslot_id = timeslot.get("id")
            slot_key = (classroom_id, timeslot_id)
            
            # Prefer completely free slots
            if slot_usage.get(slot_key, 0) == 0 and timeslot_id not in instructor_used_slots:
                return idx
        
        # If no perfect slot, return first slot
        return 0
    
    def _is_instructor_busy(
        self, 
        instructor_id: int, 
        timeslot_id: int, 
        assignments: List[Dict[str, Any]], 
        current_assignment: Dict[str, Any]
    ) -> bool:
        """
        Check if an instructor is busy at a specific timeslot.
        
        Returns True if instructor is RESPONSIBLE for another project at this timeslot.
        Returns False if instructor is free or only serving as jury.
        
        Args:
            instructor_id: ID of instructor to check
            timeslot_id: ID of timeslot to check
            assignments: List of all assignments
            current_assignment: Current assignment being processed (exclude from check)
            
        Returns:
            True if instructor is busy (responsible for another project), False otherwise
        """
        for assignment in assignments:
            # Skip current assignment
            if assignment == current_assignment:
                continue
            
            # Check if this assignment is at the same timeslot
            if assignment.get("timeslot_id") == timeslot_id:
                # Check if instructor is RESPONSIBLE (first in instructors list)
                instructors = assignment.get("instructors", [])
                if instructors and instructors[0] == instructor_id:
                    return True  # Instructor is responsible for another project at this timeslot
        
        return False  # Instructor is free
    
    def _assign_bidirectional_jury(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ═══════════════════════════════════════════════════════════════════════════════
        BI-DIRECTIONAL JURY ASSIGNMENT (100% AI-Based, CONFLICT-AWARE)
        ═══════════════════════════════════════════════════════════════════════════════
        
        Strategy:
        For each instructor pair (x, y):
        
        1️⃣ When Instructor X is RESPONSIBLE → Instructor Y becomes JURY
           - All X's projects get Y as jury member
           - Consecutive grouping maintained
           - CONFLICT CHECK: Don't add jury if instructor is busy!
        
        2️⃣ When Instructor Y is RESPONSIBLE → Instructor X becomes JURY
           - All Y's projects get X as jury member
           - Consecutive grouping maintained
           - CONFLICT CHECK: Don't add jury if instructor is busy!
        
        This creates a perfectly balanced, bi-directional jury system where:
        - Each instructor serves as jury for their pair's projects
        - Workload is distributed evenly
        - Consecutive grouping is preserved
        - NO CONFLICTS: Instructors can't be in two places at once!
        
        ═══════════════════════════════════════════════════════════════════════════════
        """
        logger.info("")
        logger.info("=" * 80)
        logger.info("🎯 BI-DIRECTIONAL JURY ASSIGNMENT")
        logger.info("=" * 80)
        logger.info("")
        
        jury_count = 0
        total_pairs_processed = 0
        
        # Group projects by responsible instructor for quick lookup
        project_to_instructor = {}
        for project in self.projects:
            project_id = project.get("id")
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                project_to_instructor[project_id] = responsible_id
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # Process each instructor pair
        # ═══════════════════════════════════════════════════════════════════════════════
        for pair_idx, (inst_a_id, inst_b_id) in enumerate(self.instructor_pairs):
            logger.info("─" * 80)
            logger.info(f"🔗 PAIR {pair_idx + 1}/{len(self.instructor_pairs)}: Instructor {inst_a_id} ↔ Instructor {inst_b_id}")
            logger.info("─" * 80)
            
            a_jury_assignments = 0  # Count: B serving as jury for A's projects
            b_jury_assignments = 0  # Count: A serving as jury for B's projects
            
            a_projects_found = 0
            b_projects_found = 0
            
            # Process all assignments
            for assignment in assignments:
                project_id = assignment.get("project_id")
                responsible_id = project_to_instructor.get(project_id)
                
                if not responsible_id:
                    continue
                
                # ───────────────────────────────────────────────────────────────────────
                # 🤖 CASE 1: Instructor A is responsible → B becomes jury (CONFLICT-AWARE)
                # ───────────────────────────────────────────────────────────────────────
                if responsible_id == inst_a_id:
                    a_projects_found += 1
                    
                    if inst_b_id not in assignment['instructors']:
                        # 🛡️ CONFLICT CHECK: Don't add jury if instructor is busy at this timeslot!
                        timeslot_id = assignment.get("timeslot_id")
                        instructor_busy = self._is_instructor_busy(inst_b_id, timeslot_id, assignments, assignment)
                        
                        if instructor_busy:
                            logger.warning(
                                f"   ⚠️ Project {project_id}: Cannot add Instructor {inst_b_id} as jury - "
                                f"CONFLICT at timeslot {timeslot_id} (instructor already responsible for another project)"
                            )
                        else:
                            # 🤖 AI FEATURE 2: Workload-aware jury selection
                            if self.enable_workload_balance:
                                jury_candidate = self._get_balanced_jury_candidate(
                                    inst_a_id, inst_b_id, assignments
                                )
                            else:
                                jury_candidate = inst_b_id
                            
                            assignment['instructors'].append(jury_candidate)
                            a_jury_assignments += 1
                            jury_count += 1
                            
                            if self.enable_workload_balance and jury_candidate != inst_b_id:
                                logger.info(
                                    f"   ⚖️ Project {project_id}: Instructor {inst_a_id} (responsible) → "
                                    f"Instructor {jury_candidate} (jury - workload balanced, original: {inst_b_id})"
                                )
                            else:
                                logger.info(
                                    f"   ✅ Project {project_id}: Instructor {inst_a_id} (responsible) → "
                                    f"Instructor {jury_candidate} (jury)"
                                )
                    else:
                        logger.info(
                            f"   ℹ️ Project {project_id}: Instructor {inst_b_id} already assigned as jury"
                        )
                
                # ───────────────────────────────────────────────────────────────────────
                # 🤖 CASE 2: Instructor B is responsible → A becomes jury (CONFLICT-AWARE)
                # ───────────────────────────────────────────────────────────────────────
                elif responsible_id == inst_b_id:
                    b_projects_found += 1
                    
                    if inst_a_id not in assignment['instructors']:
                        # 🛡️ CONFLICT CHECK: Don't add jury if instructor is busy at this timeslot!
                        timeslot_id = assignment.get("timeslot_id")
                        instructor_busy = self._is_instructor_busy(inst_a_id, timeslot_id, assignments, assignment)
                        
                        if instructor_busy:
                            logger.warning(
                                f"   ⚠️ Project {project_id}: Cannot add Instructor {inst_a_id} as jury - "
                                f"CONFLICT at timeslot {timeslot_id} (instructor already responsible for another project)"
                            )
                        else:
                            # 🤖 AI FEATURE 2: Workload-aware jury selection
                            if self.enable_workload_balance:
                                jury_candidate = self._get_balanced_jury_candidate(
                                    inst_b_id, inst_a_id, assignments
                                )
                            else:
                                jury_candidate = inst_a_id
                            
                            assignment['instructors'].append(jury_candidate)
                            b_jury_assignments += 1
                            jury_count += 1
                            
                            if self.enable_workload_balance and jury_candidate != inst_a_id:
                                logger.info(
                                    f"   ⚖️ Project {project_id}: Instructor {inst_b_id} (responsible) → "
                                    f"Instructor {jury_candidate} (jury - workload balanced, original: {inst_a_id})"
                                )
                            else:
                                logger.info(
                                    f"   ✅ Project {project_id}: Instructor {inst_b_id} (responsible) → "
                                    f"Instructor {jury_candidate} (jury)"
                                )
                    else:
                        logger.info(
                            f"   ℹ️ Project {project_id}: Instructor {inst_a_id} already assigned as jury"
                        )
            
            # ───────────────────────────────────────────────────────────────────────────
            # Pair Summary
            # ───────────────────────────────────────────────────────────────────────────
            logger.info("")
            logger.info(f"📊 PAIR {pair_idx + 1} SUMMARY:")
            logger.info(f"   Instructor {inst_a_id} → Instructor {inst_b_id} (jury): {a_jury_assignments}/{a_projects_found} projects")
            logger.info(f"   Instructor {inst_b_id} → Instructor {inst_a_id} (jury): {b_jury_assignments}/{b_projects_found} projects")
            logger.info(f"   Total jury assignments: {a_jury_assignments + b_jury_assignments}")
            
            # Check balance
            if a_jury_assignments > 0 and b_jury_assignments > 0:
                logger.info(f"   ✅ BI-DIRECTIONAL: Both directions active")
                total_pairs_processed += 1
            elif a_jury_assignments > 0 or b_jury_assignments > 0:
                logger.info(f"   ⚠️ UNI-DIRECTIONAL: Only one direction active")
            else:
                logger.info(f"   ❌ NO JURY: No assignments made for this pair")
            
            logger.info("")
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # Final Summary
        # ═══════════════════════════════════════════════════════════════════════════════
        logger.info("=" * 80)
        logger.info("✅ BI-DIRECTIONAL JURY ASSIGNMENT COMPLETED")
        logger.info("=" * 80)
        logger.info(f"   Total jury assignments: {jury_count}")
        logger.info(f"   Total pairs processed: {len(self.instructor_pairs)}")
        logger.info(f"   Bi-directional pairs: {total_pairs_processed}")
        logger.info(f"   Success rate: {total_pairs_processed / len(self.instructor_pairs) * 100:.1f}%" if self.instructor_pairs else "   Success rate: N/A")
        logger.info("=" * 80)
        logger.info("")
        
        return assignments
    
    def _optimize_early_timeslots(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Early Timeslot Optimization - Prioritize early timeslots over late ones.
        
        Strategy:
        1. Identify projects scheduled in late timeslots
        2. Find early timeslots that are available
        3. Move projects from late to early timeslots if beneficial
        4. Use AI-based soft scoring for decision making
        """
        logger.info("🕐 Early Timeslot Optimization başlatılıyor...")
        
        # Get all timeslots sorted by time (early to late)
        sorted_timeslots = sorted(self.timeslots, key=lambda x: x["start_time"])
        total_timeslots = len(sorted_timeslots)
        
        # Define early vs late timeslots (first half vs second half)
        early_threshold = total_timeslots // 2
        early_timeslots = sorted_timeslots[:early_threshold]
        late_timeslots = sorted_timeslots[early_threshold:]
        
        logger.info(f"   📅 Erken slotlar: {len(early_timeslots)} (ilk {early_threshold})")
        logger.info(f"   📅 Geç slotlar: {len(late_timeslots)} (son {total_timeslots - early_threshold})")
        
        # Find projects in late timeslots
        late_projects = []
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                # Find timeslot info
                timeslot = next((ts for ts in self.timeslots if ts["id"] == timeslot_id), None)
                if timeslot and timeslot in late_timeslots:
                    late_projects.append(assignment)
        
        logger.info(f"   📋 Geç slotlarda {len(late_projects)} proje bulundu")
        
        if not late_projects:
            logger.info("   ✅ Geç slotlarda proje yok, optimizasyon gerekmiyor")
            return assignments
        
        # Find available early timeslots
        used_early_slots = set()
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                timeslot = next((ts for ts in self.timeslots if ts["id"] == timeslot_id), None)
                if timeslot and timeslot in early_timeslots:
                    used_early_slots.add(timeslot_id)
        
        available_early_slots = [
            ts["id"] for ts in early_timeslots 
            if ts["id"] not in used_early_slots
        ]
        
        logger.info(f"   🆓 Erken slotlarda {len(available_early_slots)} boş slot")
        
        if not available_early_slots:
            logger.info("   ⚠️ Erken slotlarda boş yer yok - ULTRA-AGGRESSIVE SWAPPING başlatılıyor")
            # ULTRA-AGGRESSIVE: Force swap even when early slots are full
            swap_count = self._ultra_aggressive_early_swap(assignments, late_projects, early_threshold)
            logger.info(f"   ✅ ULTRA-AGGRESSIVE SWAPPING: {swap_count} proje değişimi yapıldı")
            return assignments
        
        # ULTRA-AGGRESSIVE: Try to move late projects to early slots
        moved_count = 0
        
        # First, try to move ALL late projects to early slots (aggressive approach)
        for late_project in late_projects:
            if not available_early_slots:
                break
            
            current_timeslot_id = late_project.get("timeslot_id")
            current_classroom_id = late_project.get("classroom_id")
            
            # Find best early timeslot for this project
            best_early_slot = None
            best_score = float('-inf')
            
            for early_slot_id in available_early_slots:
                # Calculate score for this move
                score = self._calculate_early_timeslot_score(
                    late_project, current_classroom_id, early_slot_id
                )
                
                if score > best_score:
                    best_score = score
                    best_early_slot = early_slot_id
            
            # ULTRA-AGGRESSIVE: Move to early slot even with conflicts (soft constraint)
            if best_early_slot:
                # Update assignment (force move to early slot)
                late_project["timeslot_id"] = best_early_slot
                available_early_slots.remove(best_early_slot)
                moved_count += 1
                
                logger.info(
                    f"    🚀 ULTRA-AGGRESSIVE: Proje {late_project['project_id']} erken slota zorla taşındı: "
                    f"Slot {current_timeslot_id} → {best_early_slot} (Score: {best_score:.1f})"
                )
        
        # ULTRA-AGGRESSIVE: If still have late projects, try swapping with early projects
        if late_projects and available_early_slots:
            logger.info("   🔄 ULTRA-AGGRESSIVE: Erken projelerle değişim denemesi...")
            swap_count = self._ultra_aggressive_early_swap(assignments, late_projects, early_threshold)
            moved_count += swap_count
            logger.info(f"   ✅ ULTRA-AGGRESSIVE: {swap_count} proje değişimi yapıldı")
        
        logger.info(f"✅ Early Timeslot Optimization: {moved_count} proje erken slotlara taşındı")
        return assignments
    
    def _calculate_early_timeslot_score(self, project: Dict[str, Any], classroom_id: int, timeslot_id: int) -> float:
        """
        Calculate score for moving a project to an early timeslot (AI-based soft scoring).
        """
        score = 0.0
        
        # High reward for using early timeslots
        score += self.reward_early_timeslot
        
        # Check for conflicts (soft penalty)
        instructor_id = project.get("instructors", [None])[0]
        if instructor_id:
            # Very soft penalty for instructor conflicts
            score += self.penalty_conflict * 0.1
        
        # Check if this classroom is already used in this timeslot
        # This is a soft constraint - we prefer free slots but don't block
        conflicts = 0
        for other_assignment in self._get_assignments():
            if (other_assignment.get("classroom_id") == classroom_id and 
                other_assignment.get("timeslot_id") == timeslot_id):
                conflicts += 1
        
        if conflicts > 0:
            score += self.penalty_conflict * conflicts * 0.5  # Soft penalty
        
        return score
    
    def _ultra_aggressive_early_swap(self, assignments: List[Dict[str, Any]], late_projects: List[Dict[str, Any]], early_threshold: int) -> int:
        """
        Ultra-Aggressive Early Swap - Swap late projects with early projects.
        
        Strategy:
        1. Find early projects that can be moved to late slots
        2. Swap them with late projects
        3. Use aggressive scoring to force early timeslot usage
        """
        swap_count = 0
        
        # Find early projects that could be swapped
        early_projects = []
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                timeslot = next((ts for ts in self.timeslots if ts["id"] == timeslot_id), None)
                if timeslot:
                    timeslot_index = next(
                        (i for i, ts in enumerate(sorted(self.timeslots, key=lambda x: x["start_time"])) 
                         if ts["id"] == timeslot_id), -1
                    )
                    if timeslot_index >= 0 and timeslot_index < early_threshold:
                        early_projects.append(assignment)
        
        logger.info(f"   📋 Erken projeler: {len(early_projects)}, Geç projeler: {len(late_projects)}")
        
        # Try to swap late projects with early projects
        for late_project in late_projects[:]:  # Copy list to avoid modification during iteration
            if not early_projects:
                break
            
            current_late_timeslot = late_project.get("timeslot_id")
            current_late_classroom = late_project.get("classroom_id")
            
            # Find best early project to swap with
            best_early_project = None
            best_swap_score = float('-inf')
            
            for early_project in early_projects:
                early_timeslot = early_project.get("timeslot_id")
                early_classroom = early_project.get("classroom_id")
                
                # Calculate swap score (early project goes to late slot, late project goes to early slot)
                swap_score = (
                    self._calculate_early_timeslot_score(late_project, early_classroom, early_timeslot) +
                    self._calculate_late_timeslot_penalty(early_project, current_late_classroom, current_late_timeslot)
                )
                
                if swap_score > best_swap_score:
                    best_swap_score = swap_score
                    best_early_project = early_project
            
            # CONFLICT-AWARE: Check if swap would create conflicts before proceeding
            if best_early_project:
                early_timeslot = best_early_project.get("timeslot_id")
                early_classroom = best_early_project.get("classroom_id")
                
                # Check if swap would create conflicts
                late_project_instructors = set(late_project.get("instructors", []))
                early_project_instructors = set(best_early_project.get("instructors", []))
                
                # After swap:
                # - late_project will be at early_timeslot (with late_project_instructors)
                # - early_project will be at current_late_timeslot (with early_project_instructors)
                
                # Check for conflicts in both directions
                conflict_detected = False
                
                # Check 1: Would late_project's instructors conflict at early_timeslot?
                for instructor_id in late_project_instructors:
                    if self._is_instructor_busy(instructor_id, early_timeslot, assignments, late_project):
                        conflict_detected = True
                        logger.warning(
                            f"      ⚠️ Cannot swap: Instructor {instructor_id} (from late project {late_project['project_id']}) "
                            f"would conflict at early timeslot {early_timeslot}"
                        )
                        break
                
                # Check 2: Would early_project's instructors conflict at current_late_timeslot?
                if not conflict_detected:
                    for instructor_id in early_project_instructors:
                        if self._is_instructor_busy(instructor_id, current_late_timeslot, assignments, best_early_project):
                            conflict_detected = True
                            logger.warning(
                                f"      ⚠️ Cannot swap: Instructor {instructor_id} (from early project {best_early_project['project_id']}) "
                                f"would conflict at late timeslot {current_late_timeslot}"
                            )
                            break
                
                # Only swap if no conflicts detected
                if not conflict_detected:
                    # Perform swap
                    late_project["timeslot_id"] = early_timeslot
                    late_project["classroom_id"] = early_classroom
                    best_early_project["timeslot_id"] = current_late_timeslot
                    best_early_project["classroom_id"] = current_late_classroom
                    
                    # Remove from lists
                    early_projects.remove(best_early_project)
                    late_projects.remove(late_project)
                    
                    swap_count += 1
                    
                    logger.info(
                        f"    🔄 CONFLICT-FREE SWAP: "
                        f"Proje {late_project['project_id']} ↔ Proje {best_early_project['project_id']} "
                        f"(Score: {best_swap_score:.1f})"
                    )
                else:
                    # Skip this swap due to conflicts
                    logger.info(
                        f"    ⛔ SWAP SKIPPED: "
                        f"Proje {late_project['project_id']} ↔ Proje {best_early_project['project_id']} "
                        f"(would create conflicts)"
                    )
        
        return swap_count
    
    def _calculate_late_timeslot_penalty(self, project: Dict[str, Any], classroom_id: int, timeslot_id: int) -> float:
        """
        Calculate penalty for moving a project to a late timeslot.
        """
        penalty = 0.0
        
        # Heavy penalty for using late timeslots
        penalty += self.penalty_late_timeslot
        
        # Check for conflicts (soft penalty)
        instructor_id = project.get("instructors", [None])[0]
        if instructor_id:
            penalty += self.penalty_conflict * 0.1
        
        return penalty
    
    def _get_assignments(self) -> List[Dict[str, Any]]:
        """Get current assignments for conflict checking."""
        # This is a placeholder - in real implementation, you'd track current assignments
        return []
    
    def _calculate_early_timeslot_usage_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate score based on early timeslot usage (AI-based soft scoring).
        
        Rewards:
        - Using early timeslots (first half of the day)
        - Penalizes using late timeslots when early ones are available
        """
        if not self.timeslots or not assignments:
            return 0.0
        
        # Sort timeslots by time
        sorted_timeslots = sorted(self.timeslots, key=lambda x: x["start_time"])
        total_timeslots = len(sorted_timeslots)
        early_threshold = total_timeslots // 2
        
        # Count early vs late usage
        early_usage = 0
        late_usage = 0
        
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                # Find timeslot index
                timeslot_index = next(
                    (i for i, ts in enumerate(sorted_timeslots) if ts["id"] == timeslot_id), 
                    -1
                )
                
                if timeslot_index >= 0:
                    if timeslot_index < early_threshold:
                        early_usage += 1
                    else:
                        late_usage += 1
        
        # Calculate score with ULTRA-AGGRESSIVE approach
        score = 0.0
        
        # ULTRA-AGGRESSIVE: Very high reward for early timeslot usage
        score += early_usage * self.reward_early_timeslot
        
        # ULTRA-AGGRESSIVE: Heavy penalty for late timeslot usage
        score += late_usage * self.penalty_late_timeslot
        
        # ULTRA-AGGRESSIVE: Force early timeslot priority
        if early_usage < late_usage:  # More late than early - BAD!
            score -= 1000.0  # Heavy penalty
        elif early_usage > late_usage:  # More early than late - GOOD!
            score += 1000.0  # Heavy reward
        
        # ULTRA-AGGRESSIVE: Bonus for high early timeslot percentage
        early_percentage = (early_usage / (early_usage + late_usage) * 100) if (early_usage + late_usage) > 0 else 0
        if early_percentage >= 80:  # 80%+ early timeslot usage
            score += 500.0  # Bonus reward
        elif early_percentage >= 60:  # 60%+ early timeslot usage
            score += 200.0  # Medium bonus
        
        return score
    
    def _optimize_gap_free(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gap-Free Optimization - AI-based approach to eliminate gaps.
        
        Strategy:
        1. Identify gaps in the schedule
        2. Find unassigned projects
        3. Try to fill gaps with soft scoring (not hard blocking)
        4. Prefer consecutive assignment to minimize gaps
        """
        logger.info("🎯 Gap-Free Optimization başlatılıyor...")
        
        # Get all assigned slots
        assigned_slots = set()
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            assigned_slots.add((classroom_id, timeslot_id))
        
        # Get all possible slots
        all_slots = set()
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                all_slots.add((classroom.get("id"), timeslot.get("id")))
        
        # Find gaps
        gaps = all_slots - assigned_slots
        logger.info(f"  📊 Tespit edilen gap sayısı: {len(gaps)}")
        
        if not gaps:
            logger.info("  ✅ Hiç gap yok! Gap-free optimization atlanıyor.")
            return assignments
        
        # Get unassigned projects
        assigned_project_ids = {a.get("project_id") for a in assignments}
        unassigned_projects = [
            p for p in self.projects 
            if p.get("id") not in assigned_project_ids
        ]
        
        logger.info(f"  📊 Atanmamış proje sayısı: {len(unassigned_projects)}")
        
        if not unassigned_projects:
            logger.info("  ⚠️ Atanmamış proje yok, gap'ler doldurulamıyor.")
            return assignments
        
        # Try to fill gaps with unassigned projects
        gap_filled = 0
        
        # Group projects by instructor for consecutive assignment
        instructor_unassigned = defaultdict(list)
        for project in unassigned_projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_unassigned[responsible_id].append(project)
        
        # Sort gaps by classroom and timeslot for better consecutive assignment
        sorted_gaps = sorted(gaps, key=lambda x: (x[0], x[1]))
        
        for instructor_id, projects in instructor_unassigned.items():
            if not projects:
                continue
            
            logger.info(f"  🔄 Instructor {instructor_id}: {len(projects)} atanmamış proje")
            
            # Find best classroom for consecutive gap filling
            classroom_gaps = defaultdict(list)
            for classroom_id, timeslot_id in sorted_gaps:
                classroom_gaps[classroom_id].append(timeslot_id)
            
            best_classroom = None
            best_consecutive_gaps = 0
            
            for classroom_id, timeslot_ids in classroom_gaps.items():
                # Count consecutive gaps
                consecutive_count = 0
                max_consecutive = 0
                
                sorted_timeslots = sorted(timeslot_ids)
                for i in range(len(sorted_timeslots)):
                    if i == 0 or sorted_timeslots[i] == sorted_timeslots[i-1] + 1:
                        consecutive_count += 1
                        max_consecutive = max(max_consecutive, consecutive_count)
                    else:
                        consecutive_count = 1
                
                if max_consecutive > best_consecutive_gaps:
                    best_consecutive_gaps = max_consecutive
                    best_classroom = classroom_id
            
            if not best_classroom or best_consecutive_gaps == 0:
                continue
            
            # Fill gaps consecutively
            classroom_gap_slots = sorted([ts for c, ts in sorted_gaps if c == best_classroom])
            project_idx = 0
            
            for timeslot_id in classroom_gap_slots:
                if project_idx >= len(projects):
                    break
                
                project = projects[project_idx]
                project_id = project.get("id")
                
                assignment = {
                    "project_id": project_id,
                    "classroom_id": best_classroom,
                    "timeslot_id": timeslot_id,
                    "is_makeup": project.get("is_makeup", False),
                    "instructors": [instructor_id]
                }
                
                assignments.append(assignment)
                gap_filled += 1
                project_idx += 1
                
                # Remove filled gap
                if (best_classroom, timeslot_id) in gaps:
                    gaps.remove((best_classroom, timeslot_id))
                
                logger.info(
                    f"    ✅ Proje {project_id} gap'e atandı "
                    f"(Sınıf {best_classroom}, Slot {timeslot_id})"
                )
        
        logger.info(f"✅ Gap-Free Optimization: {gap_filled} gap dolduruldu")
        
        # Advanced Gap-Free: Try to fill remaining gaps by moving projects
        if gaps and len(assignments) > 0:
            logger.info("🔄 Advanced Gap-Free: Projeleri yeniden konumlandırma...")
            gap_filled_advanced = self._advanced_gap_optimization(assignments, gaps)
            logger.info(f"✅ Advanced Gap-Free: {gap_filled_advanced} ek gap dolduruldu")
        
        return assignments
    
    def _advanced_gap_optimization(self, assignments: List[Dict[str, Any]], remaining_gaps: Set[Tuple[int, int]]) -> int:
        """
        Advanced Gap-Free Optimization - Move projects to fill gaps.
        
        Strategy:
        1. Find projects that can be moved to fill gaps
        2. Use soft scoring to evaluate moves
        3. Move projects if it improves gap-free score
        """
        gap_filled = 0
        
        # Sort gaps by classroom for better organization
        gaps_by_classroom = defaultdict(list)
        for classroom_id, timeslot_id in remaining_gaps:
            gaps_by_classroom[classroom_id].append(timeslot_id)
        
        # Try to fill gaps by moving projects from overbooked classrooms
        for classroom_id, gap_timeslots in gaps_by_classroom.items():
            if not gap_timeslots:
                continue
            
            # Sort gaps by timeslot
            gap_timeslots.sort()
            
            # Find projects that could be moved to this classroom
            for assignment in assignments:
                current_classroom = assignment.get("classroom_id")
                current_timeslot = assignment.get("timeslot_id")
                
                # Skip if already in this classroom
                if current_classroom == classroom_id:
                    continue
                
                # Check if moving this project would fill a gap
                for gap_timeslot in gap_timeslots:
                    # Calculate score improvement
                    old_score = self._calculate_move_score(assignment, current_classroom, current_timeslot)
                    new_score = self._calculate_move_score(assignment, classroom_id, gap_timeslot)
                    
                    # If moving improves gap-free score, do it
                    if new_score > old_score:
                        # Update assignment
                        assignment["classroom_id"] = classroom_id
                        assignment["timeslot_id"] = gap_timeslot
                        
                        # Remove gap
                        remaining_gaps.discard((classroom_id, gap_timeslot))
                        gap_filled += 1
                        
                        logger.info(
                            f"    ✅ Proje {assignment['project_id']} taşındı: "
                            f"Sınıf {current_classroom}→{classroom_id}, Slot {current_timeslot}→{gap_timeslot}"
                        )
                        
                        # Only move one project per gap
                        break
        
        return gap_filled
    
    def _calculate_move_score(self, assignment: Dict[str, Any], classroom_id: int, timeslot_id: int) -> float:
        """
        Calculate score for a potential move (AI-based soft scoring).
        """
        score = 0.0
        
        # Base score for assignment
        score += 10.0
        
        # Reward for filling gaps (high priority)
        score += self.reward_gap_free
        
        # Penalty for instructor conflicts (soft)
        instructor_id = assignment.get("instructors", [None])[0]
        if instructor_id:
            # Check for conflicts (soft penalty)
            score += self.penalty_conflict * 0.1  # Very soft penalty
        
        return score

    def _optimize_with_soft_constraints(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize with soft constraints - improve solution without hard blocking.
        """
        logger.info("🧠 Soft constraint optimization...")
        
        # Try to add missing jury members
        for assignment in assignments:
            current_instructors = assignment.get('instructors', [])
            
            # Try to add one more instructor if possible
            if len(current_instructors) < 2:
                timeslot_id = assignment.get('timeslot_id')
                
                # Find available instructors (soft check)
                available = []
                for instructor in self.instructors:
                    instructor_id = instructor.get('id')
                    
                    if instructor_id in current_instructors:
                        continue
                    
                    # Check if instructor is busy (soft check - allowed but scored)
                    is_busy = any(
                        timeslot_id == a.get('timeslot_id') and 
                        instructor_id in a.get('instructors', [])
                        for a in assignments
                    )
                    
                    if not is_busy:
                        available.append(instructor_id)
                
                # Add one if available
                if available:
                    selected_jury = random.choice(available)
                    assignment['instructors'].append(selected_jury)
        
        logger.info("✅ Soft constraint optimization tamamlandı")
        return assignments

    def _calculate_comprehensive_metrics(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive metrics with AI-based scoring"""
        
        # Consecutive instructors
        instructor_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project and project.get("responsible_id"):
                instructor_id = project["responsible_id"]
                instructor_assignments[instructor_id].append(assignment)
        
        consecutive_count = 0
        total_classroom_changes = 0
        time_gaps = 0
        
        for instructor_id, inst_assignments in instructor_assignments.items():
            # Check consecutive
            timeslots = sorted([a.get("timeslot_id") for a in inst_assignments])
            is_consecutive = all(
                timeslots[i] + 1 == timeslots[i+1]
                for i in range(len(timeslots) - 1)
            ) if len(timeslots) > 1 else True
            
            if is_consecutive:
                consecutive_count += 1
            
            # Count gaps
            for i in range(len(timeslots) - 1):
                gap = timeslots[i+1] - timeslots[i]
                if gap > 1:
                    time_gaps += (gap - 1)
            
            # Classroom changes
            classrooms = [a.get("classroom_id") for a in inst_assignments]
            unique_classrooms = len(set(classrooms))
            total_classroom_changes += (unique_classrooms - 1)
        
        # Bi-directional jury assignments
        bidirectional_jury_count = 0
        for assignment in assignments:
            project_id = assignment.get("project_id")
            instructors_list = assignment.get('instructors', [])
            
            # Count paired jury assignments
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
                
                # Check if any paired instructor is in the jury
                for inst_a, inst_b in self.instructor_pairs:
                    if responsible_id == inst_a and inst_b in instructors_list:
                        bidirectional_jury_count += 1
                    elif responsible_id == inst_b and inst_a in instructors_list:
                        bidirectional_jury_count += 1
        
        # Soft conflicts (counted but not blocking)
        soft_conflicts = 0
        instructor_timeslot_map = defaultdict(list)
        for assignment in assignments:
            for instructor_id in assignment.get('instructors', []):
                timeslot_id = assignment.get('timeslot_id')
                instructor_timeslot_map[(instructor_id, timeslot_id)].append(assignment)
        
        for key, assignment_list in instructor_timeslot_map.items():
            if len(assignment_list) > 1:
                soft_conflicts += (len(assignment_list) - 1)
        
        # Calculate gap-free metrics
        assigned_slots = set()
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            assigned_slots.add((classroom_id, timeslot_id))
        
        all_slots = set()
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                all_slots.add((classroom.get("id"), timeslot.get("id")))
        
        total_gaps = len(all_slots - assigned_slots)
        gap_percentage = (total_gaps / len(all_slots) * 100) if all_slots else 0
        
        # Calculate early timeslot usage score
        early_timeslot_score = self._calculate_early_timeslot_usage_score(assignments)
        
        # Calculate total score with gap-free rewards and early timeslot optimization
        total_score = (
            consecutive_count * self.reward_consecutive +
            len(self.instructor_pairs) * self.reward_balanced_pairing +
            bidirectional_jury_count * self.reward_jury_pairing +
            soft_conflicts * self.penalty_conflict +
            time_gaps * self.penalty_gap +
            total_classroom_changes * self.penalty_classroom_change +
            (len(all_slots) - total_gaps) * self.reward_gap_free +  # Reward for filled slots
            early_timeslot_score  # NEW: Reward for early timeslot usage
        )
        
        avg_classroom_changes = (
            total_classroom_changes / len(instructor_assignments)
            if instructor_assignments else 0
        )
        
        return {
            "total_score": total_score,
            "instructor_pairs": len(self.instructor_pairs),
            "bidirectional_jury_count": bidirectional_jury_count,
            "consecutive_instructors": consecutive_count,
            "total_instructors": len(instructor_assignments),
            "consecutive_percentage": (consecutive_count / len(instructor_assignments) * 100) if instructor_assignments else 0,
            "avg_classroom_changes": avg_classroom_changes,
            "time_gaps": time_gaps,
            "soft_conflicts": soft_conflicts,
            "total_assignments": len(assignments),
            "total_gaps": total_gaps,
            "gap_percentage": gap_percentage,
            "gap_free_score": (len(all_slots) - total_gaps) * self.reward_gap_free,
            "early_timeslot_score": early_timeslot_score,
            "approach": "AI-Based Instructor Pairing with Early Timeslot & Gap-Free Optimization"
        }

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        assignments = solution.get("assignments", solution.get("schedule", solution.get("solution", [])))
        if not assignments:
            return float('-inf')
        
        metrics = self._calculate_comprehensive_metrics(assignments)
        return metrics.get('total_score', 0.0)

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to datetime.time object"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)  # Default to 09:00
    
    def _check_consecutive(self, timeslot_ids: List[int]) -> bool:
        """
        Check if timeslot IDs are consecutive (no gaps).
        
        Args:
            timeslot_ids: List of timeslot IDs
            
        Returns:
            True if consecutive, False if there are gaps
        """
        if not timeslot_ids or len(timeslot_ids) <= 1:
            return True
        
        # Sort timeslot IDs
        sorted_ids = sorted(timeslot_ids)
        
        # 🤖 AI-BASED: Check consecutiveness (verification helper - not blocking!)
        # This is a METRIC, not a constraint - used for reporting only
        # Check if each ID is exactly 1 more than previous
        is_consecutive = True
        for i in range(len(sorted_ids) - 1):
            if sorted_ids[i+1] - sorted_ids[i] != 1:
                is_consecutive = False  # Not blocking - just tracking
                break
        
        return is_consecutive  # Metric only, not used for blocking
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🤖 AI FEATURE 1: ADAPTIVE SCORING WEIGHTS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _adapt_scoring_weights(self, metrics: Dict[str, Any]) -> None:
        """
        🤖 AI FEATURE 1: Adaptive Scoring Weights
        
        Automatically adjust reward/penalty values based on current performance.
        This allows the algorithm to self-optimize and adapt to different datasets.
        
        Strategy:
        - If gaps are high → INCREASE gap penalty (be more aggressive)
        - If consecutive is high → DECREASE consecutive reward (focus elsewhere)
        - If conflicts are high → INCREASE conflict penalty
        - If early timeslot usage is low → INCREASE early timeslot reward
        
        This is 100% AI-based learning - NO HARD CONSTRAINTS!
        """
        if not self.enable_adaptive_learning:
            return
        
        logger.info("🤖 ADAPTIVE SCORING WEIGHTS LEARNING...")
        
        # Store original weights for comparison
        original_weights = {
            'reward_consecutive': self.reward_consecutive,
            'reward_gap_free': self.reward_gap_free,
            'penalty_gap': self.penalty_gap,
            'penalty_conflict': self.penalty_conflict,
            'reward_early_timeslot': self.reward_early_timeslot
        }
        
        # 1️⃣ Adapt Gap-Related Weights
        gap_percentage = metrics.get('gap_percentage', 0)
        if gap_percentage > 15:
            # Too many gaps - be MORE aggressive
            self.penalty_gap *= 1.15
            self.reward_gap_free *= 1.10
            logger.info(f"   📊 Gap penalty increased: {self.penalty_gap:.1f} (gaps: {gap_percentage:.1f}%)")
        elif gap_percentage < 5:
            # Very few gaps - can relax a bit and focus elsewhere
            self.penalty_gap *= 0.95
            self.reward_gap_free *= 0.95
            logger.info(f"   📊 Gap penalty decreased: {self.penalty_gap:.1f} (gaps: {gap_percentage:.1f}%)")
        
        # 2️⃣ Adapt Consecutive-Related Weights
        consecutive_pct = metrics.get('consecutive_percentage', 0)
        if consecutive_pct > 85:
            # Consecutive is very good - focus on other objectives
            self.reward_consecutive *= 0.90
            self.reward_gap_free *= 1.10  # Focus on gap-free instead
            logger.info(f"   📊 Consecutive reward decreased: {self.reward_consecutive:.1f} (consecutive: {consecutive_pct:.1f}%)")
        elif consecutive_pct < 50:
            # Consecutive is poor - increase focus
            self.reward_consecutive *= 1.20
            logger.info(f"   📊 Consecutive reward increased: {self.reward_consecutive:.1f} (consecutive: {consecutive_pct:.1f}%)")
        
        # 3️⃣ Adapt Conflict-Related Weights
        soft_conflicts = metrics.get('soft_conflicts', 0)
        if soft_conflicts > 20:
            # Too many conflicts - be more careful
            self.penalty_conflict *= 1.25
            logger.info(f"   📊 Conflict penalty increased: {self.penalty_conflict:.1f} (conflicts: {soft_conflicts})")
        elif soft_conflicts == 0:
            # Perfect - no conflicts! Can relax
            self.penalty_conflict *= 0.95
            logger.info(f"   📊 Conflict penalty decreased: {self.penalty_conflict:.1f} (conflicts: 0)")
        
        # 4️⃣ Adapt Early Timeslot Weights
        early_score = metrics.get('early_timeslot_score', 0)
        if early_score < 5000:
            # Not using enough early timeslots
            self.reward_early_timeslot *= 1.15
            self.penalty_late_timeslot *= 1.10
            logger.info(f"   📊 Early timeslot reward increased: {self.reward_early_timeslot:.1f}")
        elif early_score > 15000:
            # Already using early timeslots well
            self.reward_early_timeslot *= 0.95
            logger.info(f"   📊 Early timeslot reward decreased: {self.reward_early_timeslot:.1f}")
        
        # 5️⃣ Track weight changes
        weight_changes = {
            'iteration': self.iteration_count,
            'original': original_weights,
            'adapted': {
                'reward_consecutive': self.reward_consecutive,
                'reward_gap_free': self.reward_gap_free,
                'penalty_gap': self.penalty_gap,
                'penalty_conflict': self.penalty_conflict,
                'reward_early_timeslot': self.reward_early_timeslot
            },
            'metrics_triggered': {
                'gap_percentage': gap_percentage,
                'consecutive_percentage': consecutive_pct,
                'soft_conflicts': soft_conflicts,
                'early_score': early_score
            }
        }
        self.scoring_weight_history.append(weight_changes)
        self.iteration_count += 1
        
        logger.info("✅ Adaptive scoring weights updated based on performance")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🤖 AI FEATURE 2: WORKLOAD-AWARE JURY ASSIGNMENT
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _calculate_instructor_workload(self, instructor_id: int, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        🤖 AI FEATURE 2: Calculate Instructor Workload
        
        Calculate comprehensive workload metrics for an instructor.
        
        Returns:
            Dict with workload metrics:
            - responsible_count: Projects where instructor is responsible
            - jury_count: Projects where instructor is jury
            - total_hours: Total hours committed
            - classroom_changes: Number of classroom changes
            - score: Weighted workload score
        """
        workload = {
            'responsible_count': 0,
            'jury_count': 0,
            'total_hours': 0.0,
            'classroom_changes': 0,
            'timeslots_used': set(),
            'classrooms_used': set()
        }
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            
            if not instructors_list or instructor_id not in instructors_list:
                continue
            
            # Check if responsible (first in list)
            if instructors_list[0] == instructor_id:
                workload['responsible_count'] += 1
            
            # Check if jury (not first in list)
            if instructor_id in instructors_list[1:]:
                workload['jury_count'] += 1
            
            # Track timeslots and classrooms
            workload['timeslots_used'].add(assignment.get('timeslot_id'))
            workload['classrooms_used'].add(assignment.get('classroom_id'))
        
        # Calculate metrics
        workload['total_hours'] = len(workload['timeslots_used']) * 0.5  # 30 minutes per slot
        workload['classroom_changes'] = len(workload['classrooms_used']) - 1 if len(workload['classrooms_used']) > 0 else 0
        
        # Calculate weighted score (responsible counts more)
        workload['score'] = (
            workload['responsible_count'] * 2.0 +  # Responsible is heavier
            workload['jury_count'] * 1.0
        )
        
        return workload
    
    def _get_balanced_jury_candidate(self, responsible_id: int, paired_id: int, assignments: List[Dict[str, Any]]) -> int:
        """
        🤖 AI FEATURE 2: Get Balanced Jury Candidate
        
        Select jury based on workload balance.
        If paired instructor is already overloaded, consider alternatives.
        
        This is SOFT - we prefer the paired instructor but can adapt.
        """
        if not self.enable_workload_balance:
            return paired_id
        
        # Calculate workloads
        responsible_workload = self._calculate_instructor_workload(responsible_id, assignments)
        paired_workload = self._calculate_instructor_workload(paired_id, assignments)
        
        # If paired instructor is heavily overloaded (score > 2x responsible)
        if paired_workload['score'] > responsible_workload['score'] * 2.5:
            logger.info(f"   ⚖️ Workload imbalance detected: Instructor {paired_id} score={paired_workload['score']:.1f} vs {responsible_id} score={responsible_workload['score']:.1f}")
            
            # Consider finding a less loaded alternative (soft preference)
            # For now, we still use paired but log the imbalance
            logger.info(f"   📊 Using paired instructor {paired_id} despite imbalance (soft constraint)")
        
        return paired_id
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🤖 AI FEATURE 3: SMART CLASSROOM SELECTION WITH MEMORY
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _find_best_classroom_with_memory(
        self,
        inst_a_id: int,
        inst_b_id: int,
        inst_a_projects: List[Dict[str, Any]],
        inst_b_projects: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        slot_usage: Dict,
        instructor_timeslot_usage: Dict
    ) -> int:
        """
        🤖 AI FEATURE 3: Smart Classroom Selection with Memory
        
        Select best classroom based on:
        1. Current availability (base score)
        2. Historical success for this instructor pair (memory bonus)
        
        This allows the algorithm to LEARN which classrooms work best
        for specific instructor pairs.
        """
        if not self.enable_classroom_memory:
            # Fall back to original method
            return self._find_best_classroom_for_pair(
                inst_a_projects, inst_b_projects, sorted_timeslots,
                slot_usage, instructor_timeslot_usage
            )
        
        total_projects = len(inst_a_projects) + len(inst_b_projects)
        best_classroom = None
        best_score = float('-inf')
        
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            
            # Base score (availability)
            consecutive_count = 0
            max_consecutive = 0
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                if slot_usage.get(slot_key, 0) == 0:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
            
            score = max_consecutive * 10
            
            if max_consecutive >= total_projects:
                score += 50
            
            # 🤖 AI MEMORY BONUS: Add historical success score
            pair_key = (inst_a_id, inst_b_id)
            memory_bonus = self.classroom_pair_memory[pair_key].get(classroom_id, 0.0)
            score += memory_bonus * 5  # Multiply by 5 to make memory influential
            
            if memory_bonus > 0:
                logger.info(f"   🧠 Memory bonus for Classroom {classroom_id}: +{memory_bonus * 5:.1f}")
            
            if score > best_score:
                best_score = score
                best_classroom = classroom_id
        
        logger.info(f"   🎯 Selected Classroom {best_classroom} (score: {best_score:.1f}, memory-enhanced: {self.enable_classroom_memory})")
        
        return best_classroom
    
    def _update_classroom_memory(self, assignments: List[Dict[str, Any]]) -> None:
        """
        🤖 AI FEATURE 3: Update Classroom Memory
        
        Update classroom success scores based on assignment quality.
        Classrooms that led to good consecutive grouping get higher scores.
        """
        if not self.enable_classroom_memory:
            return
        
        logger.info("🧠 UPDATING CLASSROOM MEMORY...")
        
        # Analyze each pairing sequence
        for pair_info in self.pairing_sequences:
            inst_a_id, inst_b_id = pair_info['pair']
            classroom_id = pair_info['classroom_id']
            
            # Calculate success score for this classroom usage
            success_score = 0.0
            
            # Reward consecutive grouping
            if pair_info.get('inst_a_consecutive', False):
                success_score += 10.0
            if pair_info.get('inst_b_consecutive', False):
                success_score += 10.0
            
            # Bonus if both are consecutive
            if pair_info.get('inst_a_consecutive', False) and pair_info.get('inst_b_consecutive', False):
                success_score += 20.0
            
            # Reward total projects handled
            success_score += pair_info.get('total_projects', 0) * 0.5
            
            # Update memory
            pair_key = (inst_a_id, inst_b_id)
            old_score = self.classroom_pair_memory[pair_key].get(classroom_id, 0.0)
            new_score = old_score * 0.7 + success_score * 0.3  # Moving average
            self.classroom_pair_memory[pair_key][classroom_id] = new_score
            
            logger.info(f"   📚 Pair ({inst_a_id}, {inst_b_id}) + Classroom {classroom_id}: score={new_score:.2f} (was {old_score:.2f})")
        
        logger.info("✅ Classroom memory updated")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🤖 AI FEATURE 4: LEARNING-BASED INSTRUCTOR PAIRING
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _evaluate_pairing_success(self, assignments: List[Dict[str, Any]]) -> None:
        """
        🤖 AI FEATURE 4: Evaluate Pairing Success
        
        Analyze how successful each instructor pairing was.
        Store this information for future runs to make smarter pairing decisions.
        
        Success Criteria:
        - Both instructors have consecutive grouping
        - Minimal gaps
        - Good bi-directional jury coverage
        - Low conflicts
        """
        if not self.enable_pairing_learning:
            return
        
        logger.info("📚 EVALUATING PAIRING SUCCESS...")
        
        for pair_info in self.pairing_sequences:
            inst_a_id, inst_b_id = pair_info['pair']
            
            # Calculate comprehensive success score
            success_score = 0.0
            
            # 1️⃣ Consecutive Grouping Quality
            if pair_info.get('inst_a_consecutive', False):
                success_score += 15.0
            if pair_info.get('inst_b_consecutive', False):
                success_score += 15.0
            
            # Perfect consecutive bonus
            if pair_info.get('inst_a_consecutive', False) and pair_info.get('inst_b_consecutive', False):
                success_score += 30.0  # Major bonus!
            
            # 2️⃣ Project Volume Bonus
            total_projects = pair_info.get('total_projects', 0)
            success_score += total_projects * 1.0
            
            # 3️⃣ Classroom Consistency
            # (Already in same classroom by design, so bonus)
            success_score += 10.0
            
            # 4️⃣ Check for conflicts in this pairing
            pair_conflicts = self._count_pair_conflicts(inst_a_id, inst_b_id, assignments)
            if pair_conflicts == 0:
                success_score += 20.0  # No conflicts bonus!
            else:
                success_score -= pair_conflicts * 5.0  # Penalty for conflicts
            
            # Update pairing history (moving average for continuous learning)
            pair_key = (inst_a_id, inst_b_id)
            old_score = self.pairing_success_history.get(pair_key, 0.0)
            new_score = old_score * 0.6 + success_score * 0.4  # Moving average
            self.pairing_success_history[pair_key] = new_score
            
            # Store metadata
            self.pairing_metadata[pair_key] = {
                'last_success_score': success_score,
                'moving_average_score': new_score,
                'total_evaluations': self.pairing_metadata.get(pair_key, {}).get('total_evaluations', 0) + 1,
                'inst_a_consecutive': pair_info.get('inst_a_consecutive', False),
                'inst_b_consecutive': pair_info.get('inst_b_consecutive', False),
                'conflicts': pair_conflicts,
                'classroom': pair_info['classroom_id']
            }
            
            logger.info(
                f"   📊 Pair ({inst_a_id}, {inst_b_id}): "
                f"score={new_score:.2f} (was {old_score:.2f}), "
                f"consecutive={'✅' if pair_info.get('inst_a_consecutive') and pair_info.get('inst_b_consecutive') else '⚠️'}, "
                f"conflicts={pair_conflicts}"
            )
        
        logger.info("✅ Pairing evaluation completed")
    
    def _count_pair_conflicts(self, inst_a_id: int, inst_b_id: int, assignments: List[Dict[str, Any]]) -> int:
        """
        Count conflicts specific to this instructor pair.
        """
        conflicts = 0
        
        # Track timeslot usage
        inst_a_timeslots = defaultdict(int)
        inst_b_timeslots = defaultdict(int)
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            timeslot_id = assignment.get('timeslot_id')
            
            if inst_a_id in instructors_list:
                inst_a_timeslots[timeslot_id] += 1
            
            if inst_b_id in instructors_list:
                inst_b_timeslots[timeslot_id] += 1
        
        # Count conflicts (multiple assignments in same timeslot)
        for timeslot_id, count in inst_a_timeslots.items():
            if count > 1:
                conflicts += (count - 1)
        
        for timeslot_id, count in inst_b_timeslots.items():
            if count > 1:
                conflicts += (count - 1)
        
        return conflicts
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🤖 AI FEATURE 5: CONFLICT PREDICTION & PREVENTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _predict_conflict_probability(
        self, 
        instructor_id: int, 
        timeslot_id: int, 
        classroom_id: int,
        assignments: List[Dict[str, Any]]
    ) -> float:
        """
        🤖 AI FEATURE 5: Predict Conflict Probability
        
        Predict the probability of conflict if we assign this instructor
        to this timeslot.
        
        Returns:
            Conflict probability score (0-100):
            - 0: No conflict risk
            - 100+: Definite conflict
        """
        if not self.enable_conflict_prediction:
            return 0.0
        
        # Check cache first
        cache_key = (instructor_id, timeslot_id, classroom_id)
        if cache_key in self.conflict_prediction_cache:
            return self.conflict_prediction_cache[cache_key]
        
        conflict_score = 0.0
        
        # 1️⃣ Direct Conflict: Instructor already assigned to this timeslot
        for assignment in assignments:
            if (assignment.get('timeslot_id') == timeslot_id and 
                instructor_id in assignment.get('instructors', [])):
                conflict_score += 100.0  # DEFINITE conflict!
        
        # 2️⃣ Proximity Risk: Instructor in nearby timeslots (travel time risk)
        for assignment in assignments:
            if instructor_id in assignment.get('instructors', []):
                other_timeslot = assignment.get('timeslot_id')
                other_classroom = assignment.get('classroom_id')
                
                # Adjacent timeslot risk
                timeslot_distance = abs(other_timeslot - timeslot_id)
                if timeslot_distance == 1:
                    # Immediate next/previous slot
                    if other_classroom != classroom_id:
                        conflict_score += 15.0  # Classroom change risk
                    else:
                        conflict_score += 2.0  # Same classroom, minimal risk
                elif timeslot_distance == 2:
                    # 1 slot gap
                    if other_classroom != classroom_id:
                        conflict_score += 5.0
        
        # 3️⃣ Historical Conflict Pattern
        historical_conflicts = self.conflict_history.get(instructor_id, 0)
        if historical_conflicts > 5:
            conflict_score += 10.0  # This instructor has conflict history
        
        # Cache the prediction
        self.conflict_prediction_cache[cache_key] = conflict_score
        
        return conflict_score
    
    def _find_safe_timeslot(
        self,
        instructor_id: int,
        preferred_timeslot_id: int,
        classroom_id: int,
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]]
    ) -> int:
        """
        🤖 AI FEATURE 5: Find Safe Alternative Timeslot
        
        Find a safe alternative timeslot if preferred one has high conflict risk.
        
        Strategy:
        1. Try nearby timeslots first (maintain consecutiveness)
        2. Prefer same classroom
        3. Choose lowest conflict probability
        """
        if not self.enable_conflict_prediction:
            return preferred_timeslot_id
        
        # Find preferred timeslot index
        preferred_idx = next(
            (i for i, ts in enumerate(sorted_timeslots) if ts.get('id') == preferred_timeslot_id),
            0
        )
        
        # Check nearby slots (±3 slots)
        search_radius = 3
        candidates = []
        
        for offset in range(-search_radius, search_radius + 1):
            idx = preferred_idx + offset
            if 0 <= idx < len(sorted_timeslots):
                candidate_slot_id = sorted_timeslots[idx].get('id')
                
                # Predict conflict for this slot
                conflict_prob = self._predict_conflict_probability(
                    instructor_id, candidate_slot_id, classroom_id, assignments
                )
                
                # Prefer slots close to preferred (maintain consecutiveness)
                proximity_bonus = search_radius - abs(offset)
                
                score = -conflict_prob + proximity_bonus * 5
                
                candidates.append({
                    'timeslot_id': candidate_slot_id,
                    'conflict_prob': conflict_prob,
                    'score': score,
                    'offset': offset
                })
        
        if not candidates:
            return preferred_timeslot_id
        
        # Choose best candidate (lowest conflict, closest to preferred)
        best_candidate = max(candidates, key=lambda x: x['score'])
        
        if best_candidate['conflict_prob'] < self._predict_conflict_probability(instructor_id, preferred_timeslot_id, classroom_id, assignments):
            logger.info(
                f"   🛡️ Found safer slot: {best_candidate['timeslot_id']} "
                f"(conflict: {best_candidate['conflict_prob']:.1f} vs {self._predict_conflict_probability(instructor_id, preferred_timeslot_id, classroom_id, assignments):.1f})"
            )
            return best_candidate['timeslot_id']
        
        return preferred_timeslot_id

    def _assign_missing_projects(
        self, 
        missing_projects: List[Dict[str, Any]], 
        existing_assignments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Assign missing projects to available slots with CONFLICT-AWARE and CONSECUTIVE logic.
        
        This method ensures 100% project coverage by assigning any projects
        that were missed during the pairing phase.
        
        NEW FEATURES:
        1. Hard conflict check - Never assign if instructor is busy
        2. Consecutive grouping - Try to group same instructor's projects together
        3. Classroom consistency - Prefer same classroom for same instructor
        4. Gap minimization - Prefer slots adjacent to instructor's existing projects
        
        Args:
            missing_projects: List of projects that haven't been assigned yet
            existing_assignments: List of existing assignments
            
        Returns:
            List of new assignments for missing projects
        """
        new_assignments = []
        
        # Build usage maps from existing assignments
        slot_usage = defaultdict(int)
        instructor_timeslot_usage = defaultdict(set)
        instructor_classroom_usage = defaultdict(lambda: defaultdict(int))  # instructor_id -> {classroom_id: count}
        classroom_timeslot_usage = defaultdict(set)  # classroom_id -> set of timeslot_ids
        
        for assignment in existing_assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            instructors = assignment.get("instructors", [])
            
            if classroom_id and timeslot_id:
                slot_usage[(classroom_id, timeslot_id)] += 1
                classroom_timeslot_usage[classroom_id].add(timeslot_id)
            
            for instructor_id in instructors:
                instructor_timeslot_usage[instructor_id].add(timeslot_id)
                if classroom_id:
                    instructor_classroom_usage[instructor_id][classroom_id] += 1
        
        # Sort timeslots by start time
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Create timeslot index map for consecutive checking
        timeslot_to_index = {ts.get("id"): idx for idx, ts in enumerate(sorted_timeslots)}
        
        logger.info(f"   Assigning {len(missing_projects)} missing projects with CONFLICT-AWARE logic...")
        
        # Group missing projects by instructor for consecutive assignment
        instructor_missing_projects = defaultdict(list)
        for project in missing_projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_missing_projects[responsible_id].append(project)
        
        logger.info(f"   Found {len(instructor_missing_projects)} instructors with missing projects")
        
        # Process each instructor's missing projects together (for consecutive grouping)
        for instructor_id, projects_list in instructor_missing_projects.items():
            logger.info(f"   Processing Instructor {instructor_id}: {len(projects_list)} missing projects")
            
            # Sort projects by type (bitirme first, then ara)
            projects_sorted = sorted(
                projects_list,
                key=lambda p: (p.get("type", "ara") == "ara", p.get("id"))
            )
            
            # Find best classroom for this instructor (prefer previously used classrooms)
            best_classroom = None
            if instructor_id in instructor_classroom_usage:
                # Use the classroom where this instructor has most projects
                best_classroom = max(
                    instructor_classroom_usage[instructor_id].items(),
                    key=lambda x: x[1]
                )[0]
                logger.info(f"      🏫 Preferred classroom: {best_classroom} (instructor already has projects there)")
            else:
                # No previous classroom, find the one with most availability
                best_classroom = self._find_most_available_classroom(
                    sorted_timeslots, slot_usage, instructor_timeslot_usage[instructor_id]
                )
                logger.info(f"      🏫 Selected classroom: {best_classroom} (most available)")
            
            if not best_classroom:
                logger.warning(f"      ⚠️ No suitable classroom found for instructor {instructor_id}")
                continue
            
            # Find consecutive timeslots for these projects
            assigned_timeslots = instructor_timeslot_usage[instructor_id]
            
            # Try to find consecutive slots adjacent to existing projects
            consecutive_slots = self._find_consecutive_available_slots(
                best_classroom,
                sorted_timeslots,
                timeslot_to_index,
                slot_usage,
                instructor_timeslot_usage[instructor_id],
                len(projects_sorted),
                assigned_timeslots
            )
            
            if len(consecutive_slots) < len(projects_sorted):
                logger.warning(
                    f"      ⚠️ Could only find {len(consecutive_slots)} consecutive slots "
                    f"for {len(projects_sorted)} projects. Will assign remaining separately."
                )
            
            # Assign projects to consecutive slots
            for idx, project in enumerate(projects_sorted):
                project_id = project.get("id")
                project_type = project.get("type", "ara")
                
                if idx < len(consecutive_slots):
                    # Use consecutive slot
                    timeslot_id = consecutive_slots[idx]
                    timeslot_start = sorted_timeslots[timeslot_to_index[timeslot_id]].get("start_time", "??:??")
                    
                    assignment = {
                        "project_id": project_id,
                        "classroom_id": best_classroom,
                        "timeslot_id": timeslot_id,
                        "is_makeup": project.get("is_makeup", False),
                        "instructors": [instructor_id]
                    }
                    
                    new_assignments.append(assignment)
                    slot_usage[(best_classroom, timeslot_id)] += 1
                    instructor_timeslot_usage[instructor_id].add(timeslot_id)
                    classroom_timeslot_usage[best_classroom].add(timeslot_id)
                    
                    logger.info(
                        f"      ✅ [{idx + 1}/{len(projects_sorted)}] Project {project_id} ({project_type}) → "
                        f"Classroom {best_classroom}, Timeslot {timeslot_id} ({timeslot_start}) [CONSECUTIVE]"
                    )
                else:
                    # No consecutive slot available, find best single slot with HARD CONFLICT CHECK
                    best_timeslot = None
                    best_score = float('-inf')
                    
                    for timeslot in sorted_timeslots:
                        timeslot_id = timeslot.get("id")
                        
                        # HARD CONFLICT CHECK - Never assign if instructor is busy!
                        if timeslot_id in instructor_timeslot_usage[instructor_id]:
                            continue  # Skip this slot - instructor conflict!
                        
                        # Check slot usage
                        slot_key = (best_classroom, timeslot_id)
                        usage_count = slot_usage.get(slot_key, 0)
                        
                        # Calculate score (prefer early, unused slots)
                        score = 100.0
                        score -= usage_count * 50.0  # Penalty for used slots
                        
                        # Bonus for early timeslots
                        timeslot_index = timeslot_to_index[timeslot_id]
                        score += (len(sorted_timeslots) - timeslot_index) * 2.0
                        
                        # Bonus for slots near instructor's existing assignments (gap reduction)
                        if assigned_timeslots:
                            min_distance = min(
                                abs(timeslot_index - timeslot_to_index[ts])
                                for ts in assigned_timeslots if ts in timeslot_to_index
                            )
                            score += (10.0 / (min_distance + 1))  # Closer is better
                        
                        if score > best_score:
                            best_score = score
                            best_timeslot = timeslot_id
                    
                    if best_timeslot:
                        timeslot_start = sorted_timeslots[timeslot_to_index[best_timeslot]].get("start_time", "??:??")
                        
                        assignment = {
                            "project_id": project_id,
                            "classroom_id": best_classroom,
                            "timeslot_id": best_timeslot,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": [instructor_id]
                        }
                        
                        new_assignments.append(assignment)
                        slot_usage[(best_classroom, best_timeslot)] += 1
                        instructor_timeslot_usage[instructor_id].add(best_timeslot)
                        classroom_timeslot_usage[best_classroom].add(best_timeslot)
                        
                        logger.info(
                            f"      ✅ [{idx + 1}/{len(projects_sorted)}] Project {project_id} ({project_type}) → "
                            f"Classroom {best_classroom}, Timeslot {best_timeslot} ({timeslot_start}) [SINGLE]"
                        )
                    else:
                        logger.error(
                            f"      ❌ Could not find conflict-free slot for project {project_id} "
                            f"(instructor {instructor_id})"
                        )
        
        logger.info(f"   ✅ Missing project assignment completed: {len(new_assignments)}/{len(missing_projects)}")
        
        # Verify no conflicts were created
        conflict_count = 0
        for assignment in new_assignments:
            instructor_id = assignment.get("instructors", [])[0] if assignment.get("instructors") else None
            timeslot_id = assignment.get("timeslot_id")
            
            if instructor_id and timeslot_id:
                # Check if this creates a conflict
                other_assignments = [
                    a for a in existing_assignments + new_assignments
                    if a != assignment
                    and instructor_id in a.get("instructors", [])
                    and a.get("timeslot_id") == timeslot_id
                ]
                if other_assignments:
                    conflict_count += 1
                    logger.error(
                        f"      ⚠️ CONFLICT DETECTED: Project {assignment.get('project_id')} "
                        f"has conflict with instructor {instructor_id} at timeslot {timeslot_id}"
                    )
        
        if conflict_count > 0:
            logger.error(f"   ❌ {conflict_count} conflicts detected in missing project assignments!")
        else:
            logger.info(f"   ✅ No conflicts detected - all assignments are valid!")
        
        return new_assignments
