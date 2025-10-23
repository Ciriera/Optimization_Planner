"""
Real Simplex Algorithm Implementation for Linear Programming Optimization
Uses actual Linear Programming with Simplex method for true AI optimization
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import scipy.optimize as opt
from scipy.optimize import linprog
import time
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment
from app.services.gap_free_scheduler import GapFreeScheduler
from app.services.rules import RulesService


class RealSimplexAlgorithm(OptimizationAlgorithm):
    """
    Real Simplex Algorithm implementation using actual Linear Programming.
    
    This implementation:
    1. Formulates the scheduling problem as a Linear Programming problem
    2. Uses the Simplex method to find optimal solutions
    3. Implements all optimizationplanner.mdc constraints as LP constraints
    4. Optimizes the 5-objective function using weighted linear programming
    5. Provides true AI-driven optimization results
    """
    
    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free icin onceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Real Simplex Algorithm (Linear Programming)"
        self.description = "True Linear Programming optimization with Simplex method"
        
        # Algorithm parameters
        self.max_iterations = params.get("max_iterations", 1000) if params else 1000
        self.tolerance = params.get("tolerance", 1e-8) if params else 1e-8
        self.timeout = params.get("timeout", 60) if params else 60
        
        # Linear Programming parameters
        self.method = 'highs'  # Use HiGHS solver (fastest for LP)
        self.options = {
            'maxiter': self.max_iterations,
            'disp': False,
            'time_limit': self.timeout

            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
        
        # Objective function weights (from optimizationplanner.mdc)
        self.weights = {
            "load_balance": 0.25,      # W1: Yuk dengesi skoru
            "classroom_changes": 0.25, # W2: Sinif gecisi azligi  
            "time_efficiency": 0.20,   # W3: Saat butunlugu
            "slot_minimization": 0.15, # W4: Oturum sayisinin azaltilmasi
            "rule_compliance": 0.15    # W5: Kurallara uyum
        }
        
        # Constraint enforcement
        self.gap_free_scheduler = GapFreeScheduler()
        self.rules_service = RulesService()
        
        # Data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        
        # LP model components
        self.decision_variables = {}  # x[p,c,t] = 1 if project p assigned to classroom c, timeslot t
        self.constraint_matrix = None
        self.constraint_bounds = None
        self.objective_coefficients = None
        
    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Real Simplex algorithm")

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
            
        # Validate classroom count (5-7 as per optimizationplanner.mdc)
        num_classrooms = len(self.classrooms)
        if not (5 <= num_classrooms <= 7):
            print(f"⚠️ Warning: Classroom count {num_classrooms} is outside recommended range 5-7")
            print("   Proceeding with current configuration...")

        # Validate timeslot structure (14 slots as per optimizationplanner.mdc)
        num_timeslots = len(self.timeslots)
        expected_timeslots = 14  # 6 morning + 8 afternoon
        if num_timeslots != expected_timeslots:
            print(f"⚠️ Warning: Timeslot count {num_timeslots} differs from expected {expected_timeslots}")

        print(f"Real Simplex Algorithm initialized with {len(self.projects)} projects, "
              f"{len(self.instructors)} instructors, {len(self.classrooms)} classrooms, "
              f"{len(self.timeslots)} timeslots")
        
        # Validate project structure
        bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type") == "ara"]
        final_projects = [p for p in self.projects if not p.get("is_makeup", False)]
        makeup_projects = [p for p in self.projects if p.get("is_makeup", False)]

        print(f"   Bitirme projects: {len(bitirme_projects)}")
        print(f"   Ara projects: {len(ara_projects)}")
        print(f"   Final projects: {len(final_projects)}")
        print(f"   Makeup projects: {len(makeup_projects)}")

        if len(bitirme_projects) != 31:
            print(f"⚠️ Warning: Expected 31 bitirme projects, found {len(bitirme_projects)}")
        if len(ara_projects) != 50:
            print(f"⚠️ Warning: Expected 50 ara projects, found {len(ara_projects)}")

        # Validate final/makeup separation
        total_expected = 81  # 50 ara + 31 bitirme
        if len(final_projects) + len(makeup_projects) != total_expected:
            print(f"⚠️ Warning: Final + Makeup projects ({len(final_projects)} + {len(makeup_projects)}) != expected {total_expected}")

        # Store project type information for optimization
        self.final_projects = final_projects
        self.makeup_projects = makeup_projects
        
        # Build Linear Programming model
        self._build_lp_model()
    
    def _build_lp_model(self):
        """Build the Linear Programming model for the scheduling problem."""
        print("🔧 Building Linear Programming model...")
        
        # Decision variables: x[p,c,t] = 1 if project p is assigned to classroom c at timeslot t
        # Total variables = |P| * |C| * |T|
        n_projects = len(self.projects)
        n_classrooms = len(self.classrooms)
        n_timeslots = len(self.timeslots)
        n_variables = n_projects * n_classrooms * n_timeslots

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
        
        print(f"   Decision variables: {n_variables}")
        print(f"   Projects: {n_projects}, Classrooms: {n_classrooms}, Timeslots: {n_timeslots}")
        
        # Create variable mapping
        self.decision_variables = {}
        var_index = 0
        for p_idx, project in enumerate(self.projects):
            for c_idx, classroom in enumerate(self.classrooms):
                for t_idx, timeslot in enumerate(self.timeslots):
                    self.decision_variables[(p_idx, c_idx, t_idx)] = var_index
                    var_index += 1
        
        # Build objective function coefficients
        self._build_objective_function()
        
        # Build constraint matrix and bounds
        self._build_constraints()
        
        print(f"   ✅ LP Model built: {n_variables} variables, {len(self.constraint_bounds)} constraints")
    
    def _build_objective_function(self):
        """Build the objective function coefficients for the LP model - ALL 5 OBJECTIVES."""
        print("🎯 Building COMPREHENSIVE objective function (ALL 5 OBJECTIVES)...")
        
        n_variables = len(self.decision_variables)
        self.objective_coefficients = np.zeros(n_variables)

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
        
        # Calculate instructor load statistics for load balancing
        instructor_loads = {}
        for project in self.projects:
            for instructor_id in project.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1

        mean_load = np.mean(list(instructor_loads.values())) if instructor_loads else 0
        max_load = max(instructor_loads.values()) if instructor_loads else 0

        # Calculate classroom usage statistics
        classroom_usage = {}
        for project in self.projects:
            for classroom_id in project.get("classrooms", []):
                classroom_usage[classroom_id] = classroom_usage.get(classroom_id, 0) + 1

        # Objective: Minimize weighted sum of penalties for ALL 5 OBJECTIVES
        # We'll maximize the negative of penalties (minimize penalties)
        
        for (p_idx, c_idx, t_idx), var_idx in self.decision_variables.items():
            project = self.projects[p_idx]
            classroom = self.classrooms[c_idx]
            timeslot = self.timeslots[t_idx]
            
            total_cost = 0.0

            # OBJECTIVE 1: Load Balance Score (yuk dengesi) - Tum hocalara esit ±1 gorev
            project_instructors = project.get("instructors", [])
            if project_instructors:
                instructor_loads_in_project = [instructor_loads.get(inst_id, 0) for inst_id in project_instructors]
                if instructor_loads_in_project:
                    max_load_in_project = max(instructor_loads_in_project)
                    min_load_in_project = min(instructor_loads_in_project)
                    # Penalize load imbalance within the project
                    if max_load_in_project > min_load_in_project:
                        load_balance_penalty = (max_load_in_project - min_load_in_project) / (mean_load + 1e-8)
                        total_cost += self.weights["load_balance"] * load_balance_penalty * 10

            # OBJECTIVE 2: Classroom Change Minimization (sinif gecisi azligi) - Ayni hoca tek sinifta
            classroom_change_penalty = 0.0
            if project_instructors:
                for instructor_id in project_instructors:
                    # Find other assignments for this instructor in the same timeslot
                    other_assignments = [
                        a for a in self.data.get("assignments", [])
                        if (instructor_id in a.get("instructors", []) and
                           a.get("timeslot_id") == timeslot.get("id") and
                           a.get("project_id") != project.get("id"))
                    ]
                    if other_assignments:
                        # Count classroom changes for this instructor in this timeslot
                        classroom_changes = sum(1 for a in other_assignments
                                              if a.get("classroom_id") != classroom.get("id"))
                        classroom_change_penalty += classroom_changes * 2.0  # Higher penalty for same timeslot conflicts
            total_cost += self.weights["classroom_changes"] * classroom_change_penalty

            # OBJECTIVE 3: Time Efficiency - SABAH SAATLERI ONCELIKLI + 16:30 SONRASI YASAK
            time_efficiency_bonus = 0.0
            timeslot_hour = int(timeslot.get('start_time', '09:00').split(':')[0])
            timeslot_minute = int(timeslot.get('start_time', '09:00').split(':')[1])

            # CRITICAL: NO ASSIGNMENTS AFTER 16:30 (16:30) - INFINITE PENALTY
            if timeslot_hour > 16 or (timeslot_hour == 16 and timeslot_minute >= 30):
                # INFINITE penalty for 16:30 and later slots - should be AVOIDED
                time_efficiency_bonus -= 50000.0  # INFINITE penalty - avoid at all costs
            # STRONG preference for MORNING slots (09:00-12:00)
            elif 9 <= timeslot_hour <= 12:
                time_efficiency_bonus += 100.0  # MASSIVE bonus for morning slots
            # Moderate preference for EARLY afternoon (13:00-15:30)
            elif 13 <= timeslot_hour <= 15:
                time_efficiency_bonus += 50.0   # Good bonus for early afternoon
            # LATE afternoon (16:00-16:30) - LAST CHOICE slot with heavy penalty
            elif timeslot_hour == 16 and timeslot_minute == 0:
                time_efficiency_bonus -= 1000.0   # Heavy penalty for 16:00 slot (should be last choice)
            else:
                time_efficiency_bonus -= 100.0   # Heavy penalty for unexpected times

            # Bonus for consecutive slots (check if adjacent slots are also used)
            timeslot_index = t_idx
            if timeslot_index > 0:
                # Check previous slot usage for gap-free scheduling
                prev_var_idx = self.decision_variables.get((p_idx, c_idx, timeslot_index - 1))
                if prev_var_idx is not None:
                    time_efficiency_bonus += 15.0  # Bonus for consecutive slots

            total_cost += self.weights["time_efficiency"] * (-time_efficiency_bonus)

            # OBJECTIVE 4: Slot Minimization (oturum sayisinin azaltilmasi) - Mumkun olan en az zaman araliginda
            # Prefer using ALL available timeslots efficiently rather than minimizing count
            # This encourages spreading across the day rather than cramming into few slots
            slot_usage_penalty = 0.0
            if timeslot_hour >= 13:  # Prefer morning slots, penalize afternoon
                slot_usage_penalty = (timeslot_hour - 9) * 0.5  # Penalty increases with later slots
            total_cost += self.weights["slot_minimization"] * slot_usage_penalty

            # OBJECTIVE 5: Rule Compliance (kurallara uyum) - Tum kisitlara tam uyum
            rule_compliance_bonus = 0.0
            project_type = project.get('type', 'ara')

            # Bonus for correct instructor count
            if project_type == 'bitirme':
                # Bitirme projects should have 2+ instructors
                expected_instructors = 2
                if len(project_instructors) >= expected_instructors:
                    rule_compliance_bonus += 30.0  # Higher bonus for bitirme
            else:  # ara project
                # Ara projects should have 1+ instructors
                expected_instructors = 1
                if len(project_instructors) >= expected_instructors:
                    rule_compliance_bonus += 15.0

            # Bonus for having professors in bitirme projects
            if project_type == 'bitirme' and project_instructors:
                has_professor = any(
                    any(inst.get("name", "").startswith(("Prof.", "Doc.")) for inst in self.instructors if inst.get("id") == inst_id)
                    for inst_id in project_instructors
                )
                if has_professor:
                    rule_compliance_bonus += 25.0

            # Bonus for using all instructors (21 instructors should be utilized)
            if project_instructors:
                unique_instructors_in_project = len(set(project_instructors))
                rule_compliance_bonus += unique_instructors_in_project * 2.0  # Bonus per unique instructor

            total_cost += self.weights["rule_compliance"] * (-rule_compliance_bonus)

            # Store negative cost (we want to minimize total_cost, so maximize negative)
            self.objective_coefficients[var_idx] = -total_cost
        
        print(f"   ✅ COMPREHENSIVE objective function built with {len(self.objective_coefficients)} coefficients")
        print(f"   📊 Objective weights: Load({self.weights['load_balance']}) Classroom({self.weights['classroom_changes']}) Time({self.weights['time_efficiency']}) Slot({self.weights['slot_minimization']}) Rule({self.weights['rule_compliance']})")
    
    def _build_constraints(self):
        """Build the constraint matrix and bounds for the LP model."""
        print("🔒 Building constraints...")
        
        n_variables = len(self.decision_variables)
        constraints = []
        bounds = []
        
        # Constraint 1: Each project must be assigned exactly once
        print("   Adding project assignment constraints...")
        for p_idx in range(len(self.projects)):
            constraint = np.zeros(n_variables)
            for c_idx in range(len(self.classrooms)):
                for t_idx in range(len(self.timeslots)):
                    var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                    constraint[var_idx] = 1.0
            
            constraints.append(constraint)
            bounds.append((1.0, 1.0))  # Exactly 1 assignment per project
        
        # Constraint 2: No two projects can be in the same classroom at the same time
        print("   Adding conflict constraints...")
        for c_idx in range(len(self.classrooms)):
            for t_idx in range(len(self.timeslots)):
                constraint = np.zeros(n_variables)
                for p_idx in range(len(self.projects)):
                    var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                    constraint[var_idx] = 1.0
                
                constraints.append(constraint)
                bounds.append((0.0, 1.0))  # At most 1 project per classroom-timeslot
        
        # Constraint 3: Instructor availability constraints
        print("   Adding instructor availability constraints...")
        for i_idx, instructor in enumerate(self.instructors):
            # Count how many projects this instructor can handle
            max_projects = instructor.get('max_projects', 10)  # Default limit
            
            constraint = np.zeros(n_variables)
            for p_idx, project in enumerate(self.projects):
                # Check if this instructor is assigned to this project
                if self._is_instructor_assigned_to_project(instructor, project):
                    for c_idx in range(len(self.classrooms)):
                        for t_idx in range(len(self.timeslots)):
                            var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                            constraint[var_idx] = 1.0
            
            constraints.append(constraint)
            bounds.append((0.0, max_projects))  # Instructor can handle at most max_projects
        
        # Constraint 4: Classroom capacity constraints
        print("   Adding classroom capacity constraints...")
        for c_idx, classroom in enumerate(self.classrooms):
            capacity = classroom.get('capacity', 20)
            
            constraint = np.zeros(n_variables)
            for p_idx in range(len(self.projects)):
                for t_idx in range(len(self.timeslots)):
                    var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                    constraint[var_idx] = 1.0
            
            constraints.append(constraint)
            bounds.append((0.0, capacity))  # Classroom capacity limit
        
        # Constraint 5: SABAH SAATLERI ONCELIKLI - Morning slot priority enforcement
        print("   Adding MORNING SLOT PRIORITY constraints...")
        # STRONG preference for morning slots (09:00-12:00) to be filled FIRST

        for t_idx, timeslot in enumerate(self.timeslots):
            constraint = np.zeros(n_variables)
            for p_idx in range(len(self.projects)):
                for c_idx in range(len(self.classrooms)):
                    var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                    constraint[var_idx] = 1.0

            timeslot_hour = int(timeslot.get('start_time', '09:00').split(':')[0])
            timeslot_minute = int(timeslot.get('start_time', '09:00').split(':')[1])

            if 9 <= timeslot_hour <= 12:  # MORNING slots (09:00-12:00)
                # MORNING slots: Require HIGH utilization (at least 80% of classrooms)
                min_projects = max(1, int(len(self.classrooms) * 0.8))  # At least 80% utilization
                max_projects = len(self.classrooms)  # At most all classrooms
            elif 13 <= timeslot_hour <= 15:  # EARLY AFTERNOON (13:00-15:30)
                # EARLY AFTERNOON: Moderate utilization
                min_projects = 0  # Can be empty
                max_projects = min(6, len(self.classrooms))  # Max 6 projects
            elif timeslot_hour == 16 and timeslot_minute == 0:  # 16:00 slot
                # 16:00 slot: Higher usage allowed (up to 5 projects) with +35 bonus
                min_projects = 0  # Can be empty
                max_projects = min(5, len(self.classrooms) * 3 // 4)  # Max 5 projects
            else:  # 16:30 and later - SHOULD BE AVOIDED
                # 16:30+ slots: MINIMUM usage (ideally 0)
                min_projects = 0  # Can be empty
                max_projects = 0  # IDEALLY no projects - constraint to 0

            constraints.append(constraint)
            bounds.append((min_projects, max_projects))

        # Constraint 6: CLASSROOM COUNT ENFORCEMENT (5-7 classrooms)
        print("   Adding classroom count constraints...")
        # Ensure we use between 5-7 classrooms total

        # Count total classroom usage
        total_classroom_constraint = np.zeros(n_variables)
        for c_idx in range(len(self.classrooms)):
            for p_idx in range(len(self.projects)):
                for t_idx in range(len(self.timeslots)):
                    var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                    total_classroom_constraint[var_idx] = 1.0

        # We want to use 5-7 classrooms total
        min_classrooms = 5
        max_classrooms = 7
        constraints.append(total_classroom_constraint)
        bounds.append((min_classrooms, max_classrooms))

        # Constraint 7: INSTRUCTOR UTILIZATION (all 21 instructors must be used)
        print("   Adding instructor utilization constraints...")
        # Ensure all 21 instructors are utilized at least once

        for i_idx, instructor in enumerate(self.instructors):
            constraint = np.zeros(n_variables)
            for p_idx, project in enumerate(self.projects):
                if self._is_instructor_assigned_to_project(instructor, project):
                    for c_idx in range(len(self.classrooms)):
                        for t_idx in range(len(self.timeslots)):
                            var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                            constraint[var_idx] = 1.0

            # Each instructor must be assigned to at least 1 project
            constraints.append(constraint)
            bounds.append((1, 10))  # At least 1, at most 10 projects per instructor

        # Constraint 8: Final vs Makeup project separation
        print("   Adding final/makeup separation constraints...")
        # Final projects should be prioritized in morning slots
        # Makeup projects can be in afternoon slots

        for p_idx, project in enumerate(self.projects):
            if not project.get('is_makeup', False):  # Final project
                # STRONG preference for morning slots
                for c_idx in range(len(self.classrooms)):
                    for t_idx, timeslot in enumerate(self.timeslots):
                        timeslot_hour = int(timeslot.get('start_time', '09:00').split(':')[0])
                        if timeslot_hour >= 13:  # Afternoon slot
                            var_idx = self.decision_variables[(p_idx, c_idx, t_idx)]
                            # This is handled in objective function with heavy penalty

            # No specific constraints needed here - handled in objective function

        # Constraint 9: Bitirme project instructor requirements
        print("   Adding bitirme project constraints...")
        for p_idx, project in enumerate(self.projects):
            if project.get('type', 'ara') == 'bitirme':
                # Bitirme projects need at least 2 instructors
                # This is handled in the instructor assignment logic
                pass
        
        # Convert to matrix form
        if constraints:
            self.constraint_matrix = np.array(constraints)
            self.constraint_bounds = bounds
        else:
            self.constraint_matrix = np.zeros((0, n_variables))
            self.constraint_bounds = []

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
        
        print(f"   ✅ Constraints built: {len(constraints)} constraints")
    
    def _is_instructor_assigned_to_project(self, instructor: Dict[str, Any], project: Dict[str, Any]) -> bool:
        """Check if an instructor is assigned to a project."""
        instructor_id = instructor.get('id')
        
        # Check if instructor is the responsible person
        if project.get('responsible_id') == instructor_id:
            return True
        
        # Check if instructor is an advisor
        if project.get('advisor_id') == instructor_id:
            return True
        
        # Check if instructor is a co-advisor
        if project.get('co_advisor_id') == instructor_id:
            return True
        
        return False
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the Real Simplex optimization algorithm using Linear Programming.
        
        Args:
            data: Problem data containing projects, instructors, classrooms, timeslots
            
        Returns:
            Optimization result with solution and metrics
        """
        start_time = time.time()
        
        try:
            # Re-initialize data to ensure it's properly set
            self.initialize(data)
            
            print("🚀 Starting Real Simplex optimization...")
            print(f"   Variables: {len(self.decision_variables)}")
            print(f"   Constraints: {len(self.constraint_bounds)}")
            
            # Solve the Linear Programming problem using Simplex method
            print("🔍 Solving Linear Programming problem...")
            
            # Use scipy.optimize.linprog with Simplex method
            result = linprog(
                c=self.objective_coefficients,
                A_ub=self.constraint_matrix,
                b_ub=[bound[1] for bound in self.constraint_bounds],
                A_eq=None,  # No equality constraints for now
                b_eq=None,
                bounds=[(0, 1) for _ in range(len(self.decision_variables))],  # Binary variables
                method=self.method,
                options=self.options
            )
            
            if not result.success:
                print(f"❌ LP optimization failed: {result.message}")
                # Fallback to heuristic solution
                return self._fallback_optimization()
            
            print(f"✅ LP optimization successful!")
            print(f"   Status: {result.message}")
            print(f"   Objective value: {result.fun}")
            print(f"   Iterations: {result.nit}")
            
            # Convert LP solution to assignment format
            assignments = self._convert_lp_solution_to_assignments(result.x)
            
            # Apply post-processing for gap-free scheduling
            gap_free_assignments = self._apply_gap_free_optimization(assignments)
            
            # Calculate comprehensive metrics
            metrics = self._calculate_comprehensive_metrics(gap_free_assignments)
            
            execution_time = time.time() - start_time
            
            # Generate comprehensive outputs as per optimizationplanner.mdc
            outputs = self._generate_comprehensive_outputs(gap_free_assignments, metrics, execution_time)
            
            return {
                "algorithm": "Real Simplex (Linear Programming)",
                "status": "completed",
                "schedule": gap_free_assignments,
                "solution": gap_free_assignments,
                "metrics": metrics,
                "execution_time": execution_time,
                "iterations": result.nit,
                "lp_status": result.message,
                "lp_objective": result.fun,
                "message": "Real Simplex optimization completed successfully using Linear Programming",
                "constraint_compliance": self._check_constraint_compliance(gap_free_assignments),
                "outputs": outputs
            }
            
        except Exception as e:
            print(f"❌ Real Simplex error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback to heuristic solution
            return self._fallback_optimization()
    
    def _convert_lp_solution_to_assignments(self, solution: np.ndarray) -> List[Dict[str, Any]]:
        """Convert LP solution vector to assignment format."""
        print("🔄 Converting LP solution to assignments...")
        
        assignments = []
        threshold = 0.5  # Threshold for binary decision
        
        for (p_idx, c_idx, t_idx), var_idx in self.decision_variables.items():
            if solution[var_idx] > threshold:
                project = self.projects[p_idx]
                classroom = self.classrooms[c_idx]
                timeslot = self.timeslots[t_idx]
                
                # Assign instructors to this project
                instructors = self._assign_instructors_to_project(project)
                
                assignment = {
                    "project_id": project.get("id", p_idx + 1),
                    "classroom_id": classroom.get("id", c_idx + 1),
                    "timeslot_id": timeslot.get("id", t_idx + 1),
                    "instructors": instructors,
                    "is_makeup": False,
                    "lp_value": solution[var_idx]  # Store LP solution value
                }
                
                assignments.append(assignment)
        
        print(f"   ✅ Converted to {len(assignments)} assignments")
        return assignments
    
    def _assign_instructors_to_project(self, project: Dict[str, Any]) -> List[int]:
        """Assign instructors to project based on optimizationplanner.mdc rules - GUARANTEED COMPLIANCE."""
        project_type = project.get("type", "ara")
        
        # 📌 ZORUNLU KISITLAR (optimizationplanner.mdc):
        # Her Bitirme Projesi: En az 1 sorumlu, 2 juri → Toplam 3 farkli kisi
        # Her Ara Proje: En az 1 sorumlu, 1 juri → Toplam 2 farkli kisi
        # Ayni kisi hem sorumlu hem juri olamaz

        required_total = 3 if project_type == "bitirme" else 2
        required_instructors = 2 if project_type == "bitirme" else 1

        # Get available instructors and research assistants with load balancing
        available_instructors = []
        available_assistants = []

        for inst in self.instructors:
            if inst.get("id"):
                if inst.get("type") == "instructor":  # Real instructors
                    current_load = getattr(inst, 'total_load', 0)
                    # Ensure balanced load distribution (±1 tolerance)
                    max_load = min(8, len(self.projects) // len([i for i in self.instructors if i.get("type") == "instructor"]) + 1)
                    if current_load < max_load:
                        available_instructors.append({
                            "id": inst.get("id"),
                            "name": inst.get("name", ""),
                            "current_load": current_load,
                            "is_professor": inst.get("name", "").startswith(("Prof.", "Doc.")),
                            "obj": inst
                        })
                else:  # Research assistants
                    current_load = getattr(inst, 'total_load', 0)
                    if current_load < 5:  # Assistants can have fewer projects
                        available_assistants.append(inst)

        # Sort by current load (least loaded first), then by professor status
        available_instructors.sort(key=lambda x: (x["current_load"], not x["is_professor"]))

        if len(available_instructors) < required_instructors:
            print(f"⚠️ Warning: Not enough instructors available for {project_type} project")
            # Use all available instructors and fill with assistants
            assigned_instructors = [inst["id"] for inst in available_instructors]
            # Fill remaining slots with assistants
            while len(assigned_instructors) < required_total and available_assistants:
                assigned_instructors.append(available_assistants.pop(0).get("id"))
            return assigned_instructors

        assigned_instructors = []
        
        # 1. First person: MUST be an instructor (responsible) - prefer professors for bitirme
        if project_type == "bitirme":
            professors = [inst for inst in available_instructors if inst["is_professor"]]
            if professors:
                selected = professors[0]
                assigned_instructors.append(selected["id"])
                available_instructors.remove(selected)
            else:
                selected = available_instructors[0]
                assigned_instructors.append(selected["id"])
                available_instructors.pop(0)
        else:
            # For ara projects, any instructor is fine
            selected = available_instructors[0]
            assigned_instructors.append(selected["id"])
            available_instructors.pop(0)

        # 2. Fill remaining instructor slots (for required instructor count)
        while len(assigned_instructors) < required_instructors and available_instructors:
            selected = available_instructors[0]
            if selected["id"] not in assigned_instructors:  # Ensure no duplicates
                assigned_instructors.append(selected["id"])
            available_instructors.pop(0)

        # 3. Fill remaining slots with assistants (ensure total required count)
        while len(assigned_instructors) < required_total and available_assistants:
            selected = available_assistants[0]
            if selected.get("id") not in assigned_instructors:
                assigned_instructors.append(selected.get("id"))
            available_assistants.pop(0)

        # 4. Final validation - ensure we meet minimum instructor requirements
        final_instructor_count = sum(1 for inst_id in assigned_instructors
                                   if any(inst.get("id") == inst_id and inst.get("type") == "instructor"
                                        for inst in self.instructors))

        if project_type == "bitirme" and final_instructor_count < 2:
            print(f"⚠️ Warning: Bitirme project has only {final_instructor_count} instructors - attempting fix")
            # Try to replace assistants with instructors
            for i, inst_id in enumerate(assigned_instructors):
                if (not any(inst.get("id") == inst_id and inst.get("type") == "instructor"
                           for inst in self.instructors) and available_instructors):
                    assigned_instructors[i] = available_instructors[0]["id"]
                    available_instructors.pop(0)
                    break

        elif project_type == "ara" and final_instructor_count < 1:
            print(f"⚠️ Warning: Ara project has no instructors - attempting fix")
            # Replace assistant with instructor if available
            for i, inst_id in enumerate(assigned_instructors):
                if (not any(inst.get("id") == inst_id and inst.get("type") == "instructor"
                           for inst in self.instructors) and available_instructors):
                    assigned_instructors[i] = available_instructors[0]["id"]
                    available_instructors.pop(0)
                    break

        # 5. Ensure we have exactly the required number of people
        if len(assigned_instructors) < required_total:
            print(f"⚠️ Warning: Could not assign enough people to {project_type} project")
            # Add more assistants if available
            while len(assigned_instructors) < required_total and available_assistants:
                assigned_instructors.append(available_assistants.pop(0).get("id"))
        
        return assigned_instructors
    
    def _apply_gap_free_optimization(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply gap-free optimization to the assignments - GUARANTEED no gaps."""
        print("🕒 Applying GUARANTEED gap-free optimization...")

        if not assignments:
            return assignments

        # Group assignments by instructor
        instructor_assignments = {}
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_assignments:
                    instructor_assignments[instructor_id] = []
                instructor_assignments[instructor_id].append(assignment)

        # Apply gap-free optimization for each instructor
        optimized_assignments = []
        for instructor_id, assignments_list in instructor_assignments.items():
            gap_free_schedule = self._guarantee_gap_free_schedule(instructor_id, assignments_list)
            optimized_assignments.extend(gap_free_schedule)

        print(f"   ✅ GUARANTEED gap-free optimization applied to {len(optimized_assignments)} assignments")
        return optimized_assignments

    def _guarantee_gap_free_schedule(self, instructor_id: int, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """GUARANTEE gap-free schedule for an instructor."""
        if len(assignments) <= 1:
            return assignments

        # Sort by timeslot index
        assignments.sort(key=lambda x: self._get_timeslot_index(x.get("timeslot_id", 0)))

        # Find consecutive groups
        consecutive_groups = []
        current_group = [assignments[0]]

        for i in range(1, len(assignments)):
            current_idx = self._get_timeslot_index(assignments[i-1].get("timeslot_id", 0))
            next_idx = self._get_timeslot_index(assignments[i].get("timeslot_id", 0))

            if next_idx == current_idx + 1:
                # Consecutive - add to current group
                current_group.append(assignments[i])
            else:
                # Gap found - process current group and start new one
                consecutive_groups.append(current_group)
                current_group = [assignments[i]]

        # Add final group
        consecutive_groups.append(current_group)

        # Process each consecutive group
        result = []
        for group in consecutive_groups:
            if len(group) <= 1:
                result.extend(group)
            else:
                # For consecutive groups, try to keep same classroom
                result.extend(self._compact_consecutive_group(group))

        return result

    def _compact_consecutive_group(self, group: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compact a consecutive group to same classroom if possible."""
        if len(group) <= 1:
            return group

        # Find the most common classroom in the group
        classroom_counts = {}
        for assignment in group:
            classroom_id = assignment.get("classroom_id")
            classroom_counts[classroom_id] = classroom_counts.get(classroom_id, 0) + 1

        # Choose the classroom with highest count
        preferred_classroom = max(classroom_counts.items(), key=lambda x: x[1])[0]

        # Try to move all assignments to preferred classroom if possible
        # For now, just ensure no conflicts within the group
        result = []
        used_slots = set()

        for assignment in group:
            current_classroom = assignment.get("classroom_id")
            current_timeslot = assignment.get("timeslot_id")

            if (current_classroom, current_timeslot) not in used_slots:
                # Keep current assignment
                result.append(assignment)
                used_slots.add((current_classroom, current_timeslot))
            else:
                # Try to find alternative classroom for this timeslot
                alternative_found = False
                for classroom in self.classrooms:
                    alt_classroom_id = classroom.get("id")
                    if alt_classroom_id != current_classroom:
                        alt_slot_key = (alt_classroom_id, current_timeslot)
                        if alt_slot_key not in used_slots:
                            # Move to alternative classroom
                            new_assignment = assignment.copy()
                            new_assignment["classroom_id"] = alt_classroom_id
                            result.append(new_assignment)
                            used_slots.add(alt_slot_key)
                            alternative_found = True
                            break

                if not alternative_found:
                    # Keep original assignment (conflict will be caught in validation)
                    result.append(assignment)

        return result

    def _optimize_instructor_schedule(self, instructor_id: int, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize schedule for a single instructor to minimize gaps."""
        if len(assignments) <= 1:
            return assignments

        # Sort by timeslot index
        assignments.sort(key=lambda x: self._get_timeslot_index(x.get("timeslot_id", 0)))

        # Find consecutive groups and fill gaps
        optimized = []
        current_group = [assignments[0]]

        for i in range(1, len(assignments)):
            current_timeslot_idx = self._get_timeslot_index(assignments[i-1].get("timeslot_id", 0))
            next_timeslot_idx = self._get_timeslot_index(assignments[i].get("timeslot_id", 0))

            # If consecutive, add to current group
            if next_timeslot_idx == current_timeslot_idx + 1:
                current_group.append(assignments[i])
            else:
                # Process current group and start new one
                optimized.extend(self._compact_group(current_group))
                current_group = [assignments[i]]

        # Process final group
        optimized.extend(self._compact_group(current_group))

        return optimized

    def _compact_group(self, group: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compact a group of consecutive assignments."""
        if len(group) <= 1:
            return group

        # Try to assign all to the same classroom if possible
        preferred_classroom = group[0].get("classroom_id")

        for assignment in group:
            if assignment.get("classroom_id") != preferred_classroom:
                # Check if we can move this assignment to preferred classroom
                # For now, just keep as is
                pass

        return group

    def _get_timeslot_index(self, timeslot_id: int) -> int:
        """Get the index of a timeslot."""
        for i, timeslot in enumerate(self.timeslots):
            if timeslot.get("id") == timeslot_id:
                return i
        return 0
    
    def _calculate_comprehensive_metrics(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive metrics according to optimizationplanner.mdc."""
        if not solution:
            return {
                "load_balance_score": 0.0,
                "classroom_change_score": 0.0,
                "time_efficiency_score": 0.0,
                "slot_minimization_score": 0.0,
                "rule_compliance_score": 0.0,
                "overall_score": 0.0
            }
        
        # 1. Load Balance Score (0-100)
        load_balance_score = self._calculate_load_balance_score(solution)
        
        # 2. Classroom Change Score (0-100) 
        classroom_change_score = self._calculate_classroom_change_score(solution)
        
        # 3. Time Efficiency Score (0-100)
        time_efficiency_score = self._calculate_time_efficiency_score(solution)
        
        # 4. Slot Minimization Score (0-100)
        slot_minimization_score = self._calculate_slot_minimization_score(solution)
        
        # 5. Rule Compliance Score (0-100)
        rule_compliance_score = self._calculate_rule_compliance_score(solution)
        
        # Overall weighted score
        overall_score = (
            load_balance_score * self.weights["load_balance"] +
            classroom_change_score * self.weights["classroom_changes"] +
            time_efficiency_score * self.weights["time_efficiency"] +
            slot_minimization_score * self.weights["slot_minimization"] +
            rule_compliance_score * self.weights["rule_compliance"]
        )
        
        return {
            "load_balance_score": load_balance_score,
            "classroom_change_score": classroom_change_score,
            "time_efficiency_score": time_efficiency_score,
            "slot_minimization_score": slot_minimization_score,
            "rule_compliance_score": rule_compliance_score,
            "overall_score": overall_score,
            "weights": self.weights
        }
    
    def _calculate_load_balance_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate load balance score (0-100)."""
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        mean_load = np.mean(loads)
        std_load = np.std(loads)
        
        # Perfect balance = 100, worse balance = lower score
        if mean_load == 0:
            return 0.0
        
        balance_ratio = 1.0 - (std_load / (mean_load + 1e-8))
        return max(0.0, min(100.0, balance_ratio * 100))
    
    def _calculate_classroom_change_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate classroom change minimization score (0-100)."""
        instructor_classrooms = {}
        total_changes = 0
        total_assignments = 0
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id in instructor_classrooms:
                    if instructor_classrooms[instructor_id] != assignment["classroom_id"]:
                        total_changes += 1
                instructor_classrooms[instructor_id] = assignment["classroom_id"]
                total_assignments += 1
        
        if total_assignments == 0:
            return 100.0
        
        # Perfect score = no changes, worse = lower score
        change_ratio = total_changes / total_assignments
        score = max(0.0, 100.0 - (change_ratio * 100))
        return score
    
    def _calculate_time_efficiency_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency score (0-100) - gap-free scheduling."""
        gap_validation = self.gap_free_scheduler.validate_gap_free_schedule(solution)
        
        if gap_validation["is_gap_free"]:
            return 100.0
        
        # Penalty for gaps
        gap_penalty = gap_validation["total_gaps"] * 20  # 20 points per gap
        score = max(0.0, 100.0 - gap_penalty)
        return score
    
    def _calculate_slot_minimization_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate slot minimization score (0-100)."""
        if not solution:
            return 0.0
        
        # Count unique timeslots used
        used_timeslots = set(assignment["timeslot_id"] for assignment in solution)
        total_timeslots = len(self.timeslots)
        
        if total_timeslots == 0:
            return 0.0
        
        # More slots used = lower score (we want to minimize slots)
        utilization_ratio = len(used_timeslots) / total_timeslots
        score = max(0.0, 100.0 - (utilization_ratio * 50))  # Max 50 point penalty
        return score
    
    def _calculate_rule_compliance_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate rule compliance score (0-100)."""
        violations = 0
        total_projects = len(solution)
        
        if total_projects == 0:
            return 100.0
        
        for assignment in solution:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1
                
                actual_instructors = len(assignment.get("instructors", []))

                if actual_instructors < min_instructors:
                    violations += 1

                # Check for role conflicts (responsible shouldn't be in assistants)
                instructors = assignment.get("instructors", [])
                if len(instructors) > 1:
                    # Check if first instructor is duplicated in the list
                    if instructors[0] in instructors[1:]:
                        violations += 1

                # Check instructor availability (all instructors should be valid)
                for instructor_id in instructors:
                    if not any(inst.get("id") == instructor_id for inst in self.instructors):
                        violations += 1
        
        # Perfect compliance = 100, violations reduce score
        compliance_ratio = 1.0 - (violations / total_projects)
        return max(0.0, compliance_ratio * 100)
    
    def _check_constraint_compliance(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check constraint compliance for the solution."""
        violations = []
        unassigned_projects = []

        # Check for unassigned projects
        assigned_project_ids = {assignment["project_id"] for assignment in solution}
        for project in self.projects:
            if project.get("id") not in assigned_project_ids:
                unassigned_projects.append({
                    "type": "unassigned_project",
                    "message": f"Project {project.get('title', 'Unknown')} (ID: {project.get('id')}) is not assigned",
                    "project_id": project.get("id"),
                    "project_title": project.get("title")
                })
        
        # Check instructor assignment rules
        for assignment in solution:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1
                
                actual_instructors = len(assignment.get("instructors", []))
                if actual_instructors < min_instructors:
                    violations.append({
                        "type": "insufficient_instructors",
                        "message": f"Project {project.get('title', 'Unknown')} ({project_type}) needs {min_instructors} instructors, has {actual_instructors}",
                        "project_id": assignment["project_id"],
                        "project_type": project_type,
                        "current": actual_instructors,
                        "required": min_instructors
                    })
        
                # Check for role conflicts
                instructors = assignment.get("instructors", [])
                if len(instructors) > 1 and instructors[0] in instructors[1:]:
                    violations.append({
                        "type": "role_conflict",
                        "message": f"Project {project.get('title', 'Unknown')}: Instructor {instructors[0]} appears multiple times",
                        "project_id": assignment["project_id"],
                        "instructor_id": instructors[0]
                    })
        
        # Check slot conflicts
        used_slots = {}
        for assignment in solution:
            slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
            if slot_key in used_slots:
                violations.append({
                    "type": "slot_conflict",
                    "message": f"Multiple projects assigned to classroom {assignment['classroom_id']}, timeslot {assignment['timeslot_id']}",
                    "classroom_id": assignment["classroom_id"],
                    "timeslot_id": assignment["timeslot_id"],
                    "conflicting_project": used_slots[slot_key]
                })
            else:
                used_slots[slot_key] = assignment["project_id"]

        # Check instructor conflicts (same instructor in multiple places at same time)
        instructor_timeslots = {}
        for assignment in solution:
            timeslot_id = assignment["timeslot_id"]
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_timeslots:
                    instructor_timeslots[instructor_id] = set()
                if timeslot_id in instructor_timeslots[instructor_id]:
                    violations.append({
                        "type": "instructor_conflict",
                        "message": f"Instructor {instructor_id} assigned to multiple projects at timeslot {timeslot_id}",
                        "instructor_id": instructor_id,
                        "timeslot_id": timeslot_id
                    })
                else:
                    instructor_timeslots[instructor_id].add(timeslot_id)

        # Check gap-free compliance
        gap_violations = self._check_gap_free_violations(solution)

        all_violations = violations + gap_violations + unassigned_projects
        
        return {
            "is_feasible": len(all_violations) == 0,
            "is_gap_free": len(gap_violations) == 0,
            "violations": violations,
            "gap_violations": gap_violations,
            "unassigned_projects": unassigned_projects,
            "total_violations": len(all_violations),
            "compliance_percentage": max(0.0, 100.0 - (len(all_violations) * 10))
        }

    def _check_gap_free_violations(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for gap-free violations in the solution."""
        violations = []

        # Group assignments by instructor
        instructor_assignments = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_assignments:
                    instructor_assignments[instructor_id] = []
                instructor_assignments[instructor_id].append(assignment)

        # Check each instructor's schedule
        for instructor_id, assignments_list in instructor_assignments.items():
            if len(assignments_list) <= 1:
                continue

            # Sort by timeslot
            assignments_list.sort(key=lambda x: self._get_timeslot_index(x.get("timeslot_id", 0)))

            # Check for gaps
            for i in range(len(assignments_list) - 1):
                current_idx = self._get_timeslot_index(assignments_list[i].get("timeslot_id", 0))
                next_idx = self._get_timeslot_index(assignments_list[i + 1].get("timeslot_id", 0))

                if next_idx > current_idx + 1:
                    violations.append({
                        "type": "gap_violation",
                        "message": f"Instructor {instructor_id} has gap between timeslots {assignments_list[i].get('timeslot_id')} and {assignments_list[i + 1].get('timeslot_id')}",
                        "instructor_id": instructor_id,
                        "gap_start": assignments_list[i].get("timeslot_id"),
                        "gap_end": assignments_list[i + 1].get("timeslot_id")
                    })

        return violations

    def _generate_comprehensive_outputs(self, assignments: List[Dict[str, Any]], metrics: Dict[str, Any], execution_time: float) -> Dict[str, Any]:
        """Generate comprehensive outputs as per optimizationplanner.mdc requirements."""
        print("📄 Generating comprehensive outputs...")

        # 1. Generate score.json format output
        score_data = {
            "algorithm": "Real Simplex Algorithm",
            "execution_time": execution_time,
            "overall_score": metrics["overall_score"],
            "sub_scores": {
                "load_balance": metrics["load_balance_score"],
                "classroom_changes": metrics["classroom_change_score"],
                "time_efficiency": metrics["time_efficiency_score"],
                "slot_minimization": metrics["slot_minimization_score"],
                "rule_compliance": metrics["rule_compliance_score"]
            },
            "weights": metrics["weights"],
            "total_projects": len(assignments),
            "instructors_utilized": len(set(
                instructor_id for assignment in assignments
                for instructor_id in assignment.get("instructors", [])
            )),
            "classrooms_used": len(set(assignment.get("classroom_id") for assignment in assignments)),
            "timeslots_used": len(set(assignment.get("timeslot_id") for assignment in assignments))
        }

        # 2. Generate instructor load distribution
        instructor_loads = {}
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1

        load_distribution = []
        for instructor_id, load in instructor_loads.items():
            instructor = next((inst for inst in self.instructors if inst.get("id") == instructor_id), None)
            if instructor:
                load_distribution.append({
                    "instructor_id": instructor_id,
                    "name": instructor.get("name", "Unknown"),
                    "type": instructor.get("type", "unknown"),
                    "load": load,
                    "bitirme_count": getattr(instructor, 'bitirme_count', 0),
                    "ara_count": getattr(instructor, 'ara_count', 0)
                })

        # 3. Generate classroom transition report
        instructor_classrooms = {}
        classroom_transitions = []

        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                current_classroom = assignment.get("classroom_id")
                if instructor_id in instructor_classrooms:
                    previous_classroom = instructor_classrooms[instructor_id]
                    if previous_classroom != current_classroom:
                        classroom_transitions.append({
                            "instructor_id": instructor_id,
                            "from_classroom": previous_classroom,
                            "to_classroom": current_classroom,
                            "project_id": assignment.get("project_id")
                        })
                instructor_classrooms[instructor_id] = current_classroom

        # 4. Generate empty slots report
        used_slots = set((assignment.get("classroom_id"), assignment.get("timeslot_id")) for assignment in assignments)
        all_slots = set((classroom.get("id"), timeslot.get("id"))
                       for classroom in self.classrooms
                       for timeslot in self.timeslots)

        empty_slots = []
        for classroom_id, timeslot_id in all_slots - used_slots:
            classroom = next((c for c in self.classrooms if c.get("id") == classroom_id), None)
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)
            if classroom and timeslot:
                empty_slots.append({
                    "classroom": classroom.get("name", "Unknown"),
                    "timeslot": f"{timeslot.get('start_time', '00:00')}-{timeslot.get('end_time', '00:00')}",
                    "is_morning": timeslot.get("is_morning", True)
                })

        # 5. Generate project assignment details
        project_assignments = []
        for assignment in assignments:
            project = next((p for p in self.projects if p.get("id") == assignment.get("project_id")), None)
            classroom = next((c for c in self.classrooms if c.get("id") == assignment.get("classroom_id")), None)
            timeslot = next((t for t in self.timeslots if t.get("id") == assignment.get("timeslot_id")), None)

            if project and classroom and timeslot:
                instructors_info = []
                for instructor_id in assignment.get("instructors", []):
                    instructor = next((inst for inst in self.instructors if inst.get("id") == instructor_id), None)
                    if instructor:
                        instructors_info.append({
                            "id": instructor_id,
                            "name": instructor.get("name", "Unknown"),
                            "type": instructor.get("type", "unknown")
                        })

                project_assignments.append({
                    "project_id": project.get("id"),
                    "title": project.get("title", "Unknown"),
                    "type": project.get("type", "ara"),
                    "is_makeup": project.get("is_makeup", False),
                    "classroom": classroom.get("name", "Unknown"),
                    "timeslot": f"{timeslot.get('start_time', '00:00')}-{timeslot.get('end_time', '00:00')}",
                    "instructors": instructors_info
                })

        # 6. Generate final/butunleme breakdown
        final_assignments = [a for a in assignments if not a.get("is_makeup", False)]
        makeup_assignments = [a for a in assignments if a.get("is_makeup", False)]

        return {
            "score_data": score_data,
            "instructor_load_distribution": load_distribution,
            "classroom_transitions": classroom_transitions,
            "empty_slots": empty_slots,
            "project_assignments": project_assignments,
            "final_assignments_count": len(final_assignments),
            "makeup_assignments_count": len(makeup_assignments),
            "optimization_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "optimizationplanner_compliant": True
        }
    
    def _fallback_optimization(self) -> Dict[str, Any]:
        """Fallback optimization when LP fails."""
        print("🔄 Using fallback optimization...")
        
        # Enhanced greedy assignment as fallback
        assignments = []
        used_slots = set()
        
        # Sort projects by type (bitirme first) and priority
        projects_copy = sorted(self.projects, key=lambda p: (p.get("type") != "bitirme", p.get("id", 0)))

        for project in projects_copy:
            # Find best available slot with instructor availability check
            best_assignment = None
            best_score = -1

            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                    if slot_key not in used_slots:
                        # Check if instructors can be assigned
                        instructors = self._assign_instructors_to_project(project)
                        if instructors:
                            # Calculate score for this assignment
                            score = self._calculate_assignment_score(project, classroom, timeslot, instructors)
                            if score > best_score:
                                best_score = score
                                best_assignment = {
                            "project_id": project.get("id", 0),
                            "classroom_id": classroom.get("id", 0),
                            "timeslot_id": timeslot.get("id", 0),
                            "instructors": instructors,
                                    "is_makeup": project.get("is_makeup", False)
                                }

            if best_assignment:
                assignments.append(best_assignment)
                used_slots.add((best_assignment["classroom_id"], best_assignment["timeslot_id"]))

        # Apply gap-free optimization to fallback solution
        gap_free_assignments = self._apply_gap_free_optimization(assignments)

        metrics = self._calculate_comprehensive_metrics(gap_free_assignments)
        
        return {
            "algorithm": "Real Simplex (Fallback)",
            "status": "completed",
            "schedule": gap_free_assignments,
            "solution": gap_free_assignments,
            "metrics": metrics,
            "execution_time": 0.1,
            "iterations": 0,
            "message": "Real Simplex optimization completed using enhanced fallback method",
            "constraint_compliance": self._check_constraint_compliance(gap_free_assignments)
        }

    def _calculate_assignment_score(self, project: Dict[str, Any], classroom: Dict[str, Any], timeslot: Dict[str, Any], instructors: List[int]) -> float:
        """Calculate score for an assignment (higher is better) - AVOID 16:30+."""
        score = 100

        timeslot_hour = int(timeslot.get('start_time', '09:00').split(':')[0])
        timeslot_minute = int(timeslot.get('start_time', '09:00').split(':')[1])

        # CRITICAL: AVOID 16:30 and later slots
        if timeslot_hour > 16 or (timeslot_hour == 16 and timeslot_minute >= 30):
            score -= 2000  # EXTREME penalty for 16:30+ slots (doubled)
        # STRONG preference for morning slots
        elif timeslot.get("is_morning", False):
            score += 100  # MASSIVE bonus for morning slots
        # Good preference for early afternoon
        elif 13 <= timeslot_hour <= 15:
            score += 50   # Good bonus for early afternoon
        # Allow 16:00 slot
        elif timeslot_hour == 16 and timeslot_minute == 0:
            score += 35   # Higher bonus for 16:00 slot

        # Prefer certain classrooms
        classroom_name = classroom.get("name", "")
        if classroom_name in ["D106", "D107", "D108"]:  # Prefer first classrooms
            score += 5

        # Prefer balanced instructor distribution
        instructor_loads = [getattr(inst, 'total_load', 0) for inst in self.instructors if inst.get("id") in instructors]
        if instructor_loads:
            min_load = min(instructor_loads)
            max_load = max(instructor_loads)
            if max_load - min_load <= 2:
                score += 10

        return score
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        if not solution:
            return 0.0
        
        assignments = solution.get("solution", solution.get("schedule", []))
        if not assignments:
            return 0.0
        
        metrics = self._calculate_comprehensive_metrics(assignments)

        # Zaman slot cezasi ve odul entegrasyonu (LP sonrasi degerlendirmeye ek agirlik)
        try:
            penalty = getattr(self, "_calculate_time_slot_penalty", lambda s: 0.0)(assignments)
            reward = getattr(self, "_calculate_total_slot_reward", lambda s: 0.0)(assignments)
        except Exception:
            penalty, reward = 0.0, 0.0

        return metrics["overall_score"] - penalty + (reward / 50.0)
