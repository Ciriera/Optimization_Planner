"""
Integer Linear Programming (ILP) Algorithm Implementation - CP-SAT ozellikli versiyon
"""

import random
from typing import Dict, List, Any, Optional
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment


class IntegerLinearProgramming(OptimizationAlgorithm):
    """
    Integer Linear Programming algorithm for optimization problems.
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
        self.max_iterations = self.params.get('max_iterations', 100)
        self.tolerance = self.params.get('tolerance', 1e-6)
        self.time_limit = self.params.get('time_limit', 60)

        # CP-SAT ozellikleri
        self.max_load_tolerance = self.params.get('max_load_tolerance', 2) if self.params else 2
        self.best_solution = None
        self.best_fitness = float('-inf')

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

        # CP-SAT ozellikleri icin ek veri yapilari
        self._instructor_timeslot_usage = {}
        
    def initialize(self, data: Dict[str, Any]):
        """Initialize the ILP algorithm with problem data - CP-SAT ozellikli versiyon."""
        self.projects = data.get('projects', [])
        self.resources = data.get('resources', [])
        self.constraints = data.get('constraints', {})

        # CP-SAT ozelligi: instructor timeslot kullanim takibi
        self._instructor_timeslot_usage = {}
        for inst in self.instructors:
            self._instructor_timeslot_usage[inst.get("id")] = set()

        # ILP variables
        self.variables = {}
        self.objective_value = 0
        self.solution = []

        # Initialize variables
        self._initialize_variables()
        
    def _initialize_variables(self):
        """Initialize ILP variables."""
        for i, project in enumerate(self.projects):
            self.variables[f'x_{i}'] = 0  # Binary variable for project selection
            
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the ILP optimization - CP-SAT ozellikli versiyon."""
        import time
        start_time = time.time()

        # CP-SAT ozelligi: Baslangic cozumu olustur ve degerlendir
        initial_solution = self._generate_feasible_solution()
        initial_fitness = self.evaluate_fitness({"solution": initial_solution}) if initial_solution else 0.0

        # En iyi cozumu guncelle (CP-SAT ozelligi)
        self.best_solution = initial_solution
        self.best_fitness = initial_fitness

        # CP-SAT ozelligi: Yerel arama ile cozumu iyilestir (zaman limiti icinde)
        current_solution = initial_solution
        current_fitness = initial_fitness

        iteration = 0
        while time.time() - start_time < self.time_limit and iteration < self.max_iterations:
            # Komsu cozum olustur
            neighbor = self._generate_neighbor_solution(current_solution)

            # Komsu cozumun uygunlugunu degerlendir
            neighbor_fitness = self.evaluate_fitness({"solution": neighbor}) if neighbor else 0.0

            # Daha iyi cozumu kabul et
            if neighbor_fitness > current_fitness:
                current_solution = neighbor
                current_fitness = neighbor_fitness

                # En iyi cozumu guncelle
                if current_fitness > self.best_fitness:
                    self.best_solution = current_solution
                    self.best_fitness = current_fitness

            iteration += 1

        return {
            'solution': self.best_solution,
            'fitness': self.best_fitness,
            'iterations': iteration,
            'execution_time': time.time() - start_time
        }
        
    def _generate_feasible_solution(self) -> List[Dict[str, Any]]:
        """Generate a feasible solution respecting constraints."""
        solution = []
        used_resources = {resource['id']: 0 for resource in self.resources}
        
        # Randomly select projects while respecting constraints
        available_projects = self.projects.copy()
        random.shuffle(available_projects)
        
        for project in available_projects:
            if self._can_add_project(project, used_resources):
                solution.append(project)
                self._update_resources(project, used_resources)
                
        return solution
        
    def _can_add_project(self, project: Dict[str, Any], used_resources: Dict[str, float]) -> bool:
        """Check if a project can be added without violating constraints."""
        for requirement in project.get('requirements', []):
            resource_id = requirement['resource_id']
            amount = requirement['amount']
            
            if used_resources[resource_id] + amount > self._get_resource_limit(resource_id):
                return False
                
        return True
        
    def _get_resource_limit(self, resource_id: str) -> float:
        """Get the limit for a specific resource."""
        for resource in self.resources:
            if resource['id'] == resource_id:
                return resource.get('limit', float('inf'))
        return float('inf')
        
    def _update_resources(self, project: Dict[str, Any], used_resources: Dict[str, float]):
        """Update resource usage after adding a project."""
        for requirement in project.get('requirements', []):
            resource_id = requirement['resource_id']
            amount = requirement['amount']
            used_resources[resource_id] += amount
            
    def _evaluate_solution(self, solution: List[Dict[str, Any]]) -> float:
        """Evaluate the fitness of a solution."""
        if not solution:
            return 0
            
        total_value = sum(project.get('value', 0) for project in solution)
        total_cost = sum(project.get('cost', 0) for project in solution)

        # Slot cezasi ve odulleri dahil et (mevcut veri modeline uyumlu sekilde guvenli cagri)
        try:
            penalty = getattr(self, "_calculate_time_slot_penalty", lambda s: 0.0)(solution)
            reward = getattr(self, "_calculate_total_slot_reward", lambda s: 0.0)(solution)
        except Exception:
            penalty, reward = 0.0, 0.0

        base = total_value / max(total_cost, 1)
        return base - penalty + (reward / 50.0)
        
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """CP-SAT ozelligi: Verilen cozumun uygunlugunu degerlendirir."""
        if not solution:
            return float('-inf')

        assignments = solution.get("solution", solution.get("schedule", []))
        if not assignments:
            return float('-inf')

        # Cozum gecerli mi?
        if not self._is_valid_solution(assignments):
            return float('-inf')

        score = 0.0

        # Kural uygunlugu
        rule_compliance = self._calculate_rule_compliance(assignments)
        score += rule_compliance * 100.0

        # Sinif degisim sayisini minimize et
        instructor_changes = self._count_instructor_classroom_changes(assignments)
        score -= instructor_changes * 10.0

        # Yuk dengesini maksimize et
        load_balance = self._calculate_load_balance(assignments)
        score += load_balance * 50.0

        # Zaman slot cezasi - 16:30 sonrasi cok agir, 16:00–16:30 orta seviye
        time_penalty = self._calculate_time_slot_penalty(assignments)
        score -= time_penalty

        return score
        
    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get information about the algorithm."""
        return {
            'name': 'Integer Linear Programming',
            'description': 'A mathematical optimization technique for problems with linear objective function and constraints.',
            'type': 'mathematical',
            'parameters': {
                'max_iterations': self.max_iterations,
                'tolerance': self.tolerance,
                'time_limit': self.time_limit

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
            
        }
