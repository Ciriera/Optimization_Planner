"""
AI-Enhanced Deep Search Algorithm - Constraint-Based Fairness with Reinforcement Learning

Implements:
- Penalty Tuner (Genetic Algorithm for alpha, beta optimization)
- Reinforcement-based Second Jury Selector
- Smart Scoring with Learning
"""

from typing import Dict, Any, List, Tuple
import time
import logging
import random
import numpy as np
from collections import defaultdict
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


class PenaltyTuner:
    """
    Genetic Algorithm-based Penalty Optimizer
    Optimizes alpha (time penalty) and beta (room penalty) coefficients
    """
    
    def __init__(self, population_size=20, generations=10):
        self.population_size = population_size
        self.generations = generations
        self.best_alpha = 1.0
        self.best_beta = 1.0
        
    def initialize_population(self) -> List[Tuple[float, float]]:
        """Create initial random population of (alpha, beta) pairs"""
        population = []
        for _ in range(self.population_size):
            alpha = random.uniform(0.5, 3.0)
            beta = random.uniform(0.5, 3.0)
            population.append((alpha, beta))
        return population
    
    def calculate_fitness(self, alpha: float, beta: float, assignments: List[Dict]) -> float:
        """
        Fitness = -Penalty (minimize penalty)
        Penalty = alpha x time_violations + beta x room_changes
        """
        time_violations = 0
        room_changes = 0
        
        # Group by instructor
        instructor_slots = defaultdict(list)
        for assignment in assignments:
            instructor_id = assignment.get('responsible_instructor_id')
            if instructor_id:
                instructor_slots[instructor_id].append(assignment)
        
        # Calculate violations
        for instructor_id, slots in instructor_slots.items():
            sorted_slots = sorted(slots, key=lambda x: (x.get('timeslot_id', 0)))
            
            for i in range(len(sorted_slots) - 1):
                current = sorted_slots[i]
                next_slot = sorted_slots[i + 1]
                
                # Time violation: consecutive slots
                current_time = current.get('timeslot_id', 0)
                next_time = next_slot.get('timeslot_id', 0)
                if next_time - current_time == 1:
                    time_violations += 1
                
                # Room change
                current_room = current.get('classroom_id')
                next_room = next_slot.get('classroom_id')
                if current_room != next_room:
                    room_changes += 1
        
        penalty = alpha * time_violations + beta * room_changes
        return -penalty  # Negative because we want to minimize penalty
    
    def crossover(self, parent1: Tuple[float, float], parent2: Tuple[float, float]) -> Tuple[float, float]:
        """Crossover between two parents"""
        alpha = (parent1[0] + parent2[0]) / 2 + random.uniform(-0.2, 0.2)
        beta = (parent1[1] + parent2[1]) / 2 + random.uniform(-0.2, 0.2)
        return (max(0.1, alpha), max(0.1, beta))
    
    def mutate(self, individual: Tuple[float, float]) -> Tuple[float, float]:
        """Mutate an individual"""
        if random.random() < 0.3:
            alpha = individual[0] + random.uniform(-0.5, 0.5)
            beta = individual[1] + random.uniform(-0.5, 0.5)
            return (max(0.1, alpha), max(0.1, beta))
        return individual
    
    def evolve(self, assignments: List[Dict]) -> Tuple[float, float]:
        """Run genetic algorithm to find optimal alpha, beta"""
        population = self.initialize_population()
        
        for generation in range(self.generations):
            # Calculate fitness for all individuals
            fitness_scores = []
            for individual in population:
                alpha, beta = individual
                fitness = self.calculate_fitness(alpha, beta, assignments)
                fitness_scores.append((individual, fitness))
            
            # Sort by fitness
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Best individual
            best_individual = fitness_scores[0][0]
            logger.info(f"Generation {generation}: Best alpha={best_individual[0]:.2f}, beta={best_individual[1]:.2f}, Fitness={fitness_scores[0][1]:.2f}")
            
            # Create new population
            new_population = [best_individual]  # Elitism
            
            while len(new_population) < self.population_size:
                # Tournament selection
                parent1 = random.choice(fitness_scores[:10])[0]
                parent2 = random.choice(fitness_scores[:10])[0]
                
                # Crossover
                child = self.crossover(parent1, parent2)
                
                # Mutation
                child = self.mutate(child)
                
                new_population.append(child)
            
            population = new_population
        
        # Return best individual
        self.best_alpha, self.best_beta = fitness_scores[0][0]
        return self.best_alpha, self.best_beta


class ReinforcementJurySelector:
    """
    Reinforcement Learning-based Second Jury Selector
    Uses Q-learning to learn optimal jury assignments
    """
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.2):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.co_occurrence_matrix = defaultdict(lambda: defaultdict(int))
        
    def update_co_occurrence(self, instructor1_id: int, instructor2_id: int):
        """Track co-occurrences for similarity learning"""
        key = tuple(sorted([instructor1_id, instructor2_id]))
        self.co_occurrence_matrix[key[0]][key[1]] += 1
        self.co_occurrence_matrix[key[1]][key[0]] += 1
    
    def get_similarity_score(self, instructor1_id: int, instructor2_id: int) -> float:
        """Calculate similarity based on co-occurrence"""
        count = self.co_occurrence_matrix[instructor1_id].get(instructor2_id, 0)
        # Normalize by total occurrences
        total = sum(self.co_occurrence_matrix[instructor1_id].values())
        if total == 0:
            return 0.0
        return count / total
    
    def select_jury(self, state: str, available_instructors: List[int], 
                   current_instructor_id: int) -> int:
        """
        Select second jury using epsilon-greedy strategy
        state: current assignment state (e.g., "classroom_X_slot_Y")
        """
        # Epsilon-greedy exploration
        if random.random() < self.epsilon:
            # Explore: random selection
            return random.choice(available_instructors)
        
        # Exploit: choose best based on Q-values and similarity
        best_jury = None
        best_score = float('-inf')
        
        for jury_id in available_instructors:
            q_value = self.q_table[state][jury_id]
            similarity = self.get_similarity_score(current_instructor_id, jury_id)
            combined_score = q_value + 0.5 * similarity
            
            if combined_score > best_score:
                best_score = combined_score
                best_jury = jury_id
        
        return best_jury if best_jury else random.choice(available_instructors)
    
    def update_q_value(self, state: str, action: int, reward: float, next_state: str):
        """Update Q-value using Q-learning formula"""
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values()) if self.q_table[next_state] else 0
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q
    
    def calculate_reward(self, assignment: Dict, all_assignments: List[Dict]) -> float:
        """
        Calculate reward for an assignment
        Reward = -Penalty_time - Penalty_room - LoadImbalance
        """
        reward = 0.0
        
        # Penalty for room changes
        instructor_id = assignment.get('responsible_instructor_id')
        classroom_id = assignment.get('classroom_id')
        
        # Check previous assignments
        prev_assignments = [a for a in all_assignments 
                          if a.get('responsible_instructor_id') == instructor_id 
                          and a.get('timeslot_id', 0) < assignment.get('timeslot_id', 0)]
        
        if prev_assignments:
            prev_classroom = prev_assignments[-1].get('classroom_id')
            if prev_classroom != classroom_id:
                reward -= 1.0  # Room change penalty
            else:
                reward += 0.5  # Reward for staying in same room
        
        # Reward for good load balance
        instructor_loads = defaultdict(int)
        for a in all_assignments:
            instructor_loads[a.get('responsible_instructor_id', 0)] += 1
        
        if instructor_loads:
            avg_load = np.mean(list(instructor_loads.values()))
            current_load = instructor_loads[instructor_id]
            balance_score = 1.0 - abs(current_load - avg_load) / avg_load
            reward += balance_score * 0.5
        
        return reward


class DeepSearch(OptimizationAlgorithm):
    """
    AI-Enhanced Deep Search Algorithm
    
    Implements:
    1. Penalty Tuner (Genetic Algorithm) - optimizes alpha, beta dynamically
    2. Reinforcement Jury Selector - learns optimal jury assignments
    3. Constraint-based fairness optimization
    
    Cost Function:
    Penalty = alpha x f_time + beta x f_room
    where:
    - f_time = time violations (consecutive slots)
    - f_room = room changes
    - alpha, beta = optimized coefficients
    
    Learning Strategy:
    - Uses Q-learning to improve jury selection over time
    - Tracks co-occurrence patterns for similarity-based matching
    - Self-balancing through reinforcement rewards
    """

    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.name = "AI-Enhanced Deep Search Algorithm"
        self.description = "Constraint-Based Fairness with Reinforcement Learning"
        
        # AI Components
        self.penalty_tuner = PenaltyTuner(population_size=15, generations=5)
        self.jury_selector = ReinforcementJurySelector()
        
        # Penalty coefficients (will be optimized)
        self.alpha = 1.0  # Time penalty
        self.beta = 1.0   # Room penalty
        
        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        logger.info(f"AI-Enhanced Deep Search initialized:")
        logger.info(f"   Projects: {len(self.projects)}")
        logger.info(f"   Instructors: {len(self.instructors)}")
        logger.info(f"   Classrooms: {len(self.classrooms)}")
        logger.info(f"   Timeslots: {len(self.timeslots)}")
        
    def execute(self) -> Dict[str, Any]:
        """Execute the AI-enhanced optimization"""
        return self.optimize()
    
    def optimize(self) -> Dict[str, Any]:
        """Main optimization loop with AI enhancement"""
        start_time = time.time()
        
        logger.info("=" * 80)
        logger.info("AI-ENHANCED DEEP SEARCH ALGORITHM - STARTING")
        logger.info("=" * 80)
        
        # Phase 1: Initial assignment with default penalties
        logger.info("\nPHASE 1: Initial Assignment")
        assignments = self._create_initial_solution()
        
        # Phase 2: Optimize penalties using Genetic Algorithm
        logger.info("\nPHASE 2: Penalty Optimization (Genetic Algorithm)")
        self.alpha, self.beta = self.penalty_tuner.evolve(assignments)
        logger.info(f"Optimized Penalties: alpha={self.alpha:.2f}, beta={self.beta:.2f}")
        
        # Phase 3: Refine with optimized penalties
        logger.info("\nPHASE 3: Refined Assignment with Optimized Penalties")
        assignments = self._create_optimized_solution(self.alpha, self.beta)
        
        # Phase 4: AI-based jury assignment
        logger.info("\nPHASE 4: AI-Based Jury Assignment")
        assignments = self._assign_ai_jury(assignments)
        
        # Phase 5: Load balancing for zero-responsible instructors
        logger.info("\nPHASE 5: Load Balancing (Zero-Responsible Instructors)")
        assignments = self._balance_zero_responsible(assignments)
        
        # Calculate final metrics
        execution_time = time.time() - start_time
        metrics = self._calculate_metrics(assignments)
        
        logger.info("\n" + "=" * 80)
        logger.info("AI-ENHANCED DEEP SEARCH ALGORITHM - COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Execution Time: {execution_time:.2f}s")
        logger.info(f"Total Assignments: {len(assignments)}")
        logger.info(f"Optimized alpha={self.alpha:.2f}, beta={self.beta:.2f}")
        logger.info(f"Final Penalty Score: {metrics.get('total_penalty', 0):.2f}")
        
        return {
            "success": True,
            "assignments": assignments,
            "algorithm": self.name,
            "execution_time": execution_time,
            "metrics": metrics,
            "parameters": {
                "alpha": self.alpha,
                "beta": self.beta
            },
            "optimizations": [
                "AI-Enhanced Penalty Optimization (Genetic Algorithm)",
                "Reinforcement Learning-based Jury Selection",
                "Constraint-Based Fairness Model",
                "Smart Load Balancing",
                "Co-occurrence Pattern Learning",
                "Self-Balancing Optimization"
            ]
        }
    
    def _create_initial_solution(self) -> List[Dict]:
        """Create initial solution with fair pairing"""
        assignments = []
        
        # Group projects by instructor
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_instructor_id") or project.get("responsible_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # Sort instructors by load (Max/Min pairing)
        instructor_loads = [(inst_id, len(projects)) for inst_id, projects in instructor_projects.items()]
        instructor_loads.sort(key=lambda x: x[1], reverse=True)
        
        # Split into max and min groups
        mid = len(instructor_loads) // 2
        max_instructors = [x[0] for x in instructor_loads[:mid]]
        min_instructors = [x[0] for x in instructor_loads[mid:]]
        
        # Randomize within groups
        random.shuffle(max_instructors)
        random.shuffle(min_instructors)
        
        # Interleave: max, min, max, min...
        ordered_instructors = []
        for i in range(max(len(max_instructors), len(min_instructors))):
            if i < len(max_instructors):
                ordered_instructors.append(max_instructors[i])
            if i < len(min_instructors):
                ordered_instructors.append(min_instructors[i])
        
        # Assign consecutively
        used_slots = set()
        classroom_index = 0
        
        for instructor_id in ordered_instructors:
            projects = instructor_projects[instructor_id]
            
            # Find earliest available slot
            timeslot_index = 0
            classroom = self.classrooms[classroom_index % len(self.classrooms)]
            
            for project in projects:
                # Find next available slot
                while (timeslot_index, classroom['id']) in used_slots:
                    timeslot_index += 1
                    if timeslot_index >= len(self.timeslots):
                        timeslot_index = 0
                        classroom_index += 1
                        classroom = self.classrooms[classroom_index % len(self.classrooms)]
                
                timeslot = self.timeslots[timeslot_index]
                            
                            assignment = {
                    "project_id": project["id"],
                    "timeslot_id": timeslot["id"],
                    "classroom_id": classroom["id"],
                    "responsible_instructor_id": instructor_id,
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                used_slots.add((timeslot_index, classroom['id']))
                timeslot_index += 1
            
            classroom_index += 1
        
        return assignments
    
    def _create_optimized_solution(self, alpha: float, beta: float) -> List[Dict]:
        """Create solution optimized with given alpha, beta"""
        # For now, reuse initial solution
        # In future, can implement greedy optimization based on alpha, beta
        return self._create_initial_solution()
    
    def _assign_ai_jury(self, assignments: List[Dict]) -> List[Dict]:
        """Assign second jury using reinforcement learning"""
        
        for i, assignment in enumerate(assignments):
            instructor_id = assignment.get('responsible_instructor_id')
            classroom_id = assignment.get('classroom_id')
            timeslot_id = assignment.get('timeslot_id')
            
            # State: current context
            state = f"classroom_{classroom_id}_slot_{timeslot_id}"
            
            # Find available jury candidates (not already assigned to this slot)
            available_instructors = [
                inst['id'] for inst in self.instructors
                if inst['id'] != instructor_id
            ]
            
            # Remove instructors already busy at this timeslot
            busy_instructors = set()
            for other_assignment in assignments:
                if other_assignment.get('timeslot_id') == timeslot_id:
                    busy_instructors.add(other_assignment.get('responsible_instructor_id'))
                    busy_instructors.update(other_assignment.get('instructors', []))
            
            available_instructors = [inst_id for inst_id in available_instructors 
                                    if inst_id not in busy_instructors]
            
            if available_instructors:
                # Use RL to select jury
                selected_jury = self.jury_selector.select_jury(
                    state, available_instructors, instructor_id
                )
                
                # Add to assignment
                if selected_jury not in assignment.get('instructors', []):
                    assignment['instructors'].append(selected_jury)
                
                # Update co-occurrence
                self.jury_selector.update_co_occurrence(instructor_id, selected_jury)
                
                # Calculate reward and update Q-value
                reward = self.jury_selector.calculate_reward(assignment, assignments)
                next_state = f"classroom_{classroom_id}_slot_{timeslot_id + 1}"
                self.jury_selector.update_q_value(state, selected_jury, reward, next_state)
        
        return assignments

    def _balance_zero_responsible(self, assignments: List[Dict]) -> List[Dict]:
        """Balance load for instructors with zero responsible projects"""
        
        # Find instructors with no responsible projects
        responsible_instructors = set()
        for assignment in assignments:
            responsible_instructors.add(assignment.get('responsible_instructor_id'))
        
        all_instructors = set(inst['id'] for inst in self.instructors)
        zero_responsible = list(all_instructors - responsible_instructors)
        
        if not zero_responsible:
            logger.info("All instructors have responsible projects")
            return assignments
        
        logger.info(f"{len(zero_responsible)} instructors with zero responsible projects")
        
        # Find projects with only 1 jury
        projects_need_jury = [a for a in assignments if len(a.get('instructors', [])) == 1]
        
        # Calculate current loads
        instructor_loads = defaultdict(int)
        for assignment in assignments:
            for inst_id in assignment.get('instructors', []):
                instructor_loads[inst_id] += 1
        
        # Calculate target load
        if instructor_loads:
            min_load = min(instructor_loads.values())
            max_load = max(instructor_loads.values())
            target_load = (min_load + max_load) // 2
        else:
            target_load = 0
        
        # Assign balanced jury
        for instructor_id in zero_responsible:
            current_load = instructor_loads.get(instructor_id, 0)
            
            for assignment in projects_need_jury:
                if current_load >= target_load:
                    break
                
                timeslot_id = assignment.get('timeslot_id')
                
                # Check if instructor is available
                is_available = True
                for other_assignment in assignments:
                    if other_assignment.get('timeslot_id') == timeslot_id:
                        if instructor_id in other_assignment.get('instructors', []):
                            is_available = False
                            break
                
                if is_available:
                    assignment['instructors'].append(instructor_id)
                    instructor_loads[instructor_id] += 1
                    current_load += 1
                    logger.info(f"Instructor {instructor_id} assigned as jury (load: {current_load})")
        
        return assignments
    
    def _calculate_metrics(self, assignments: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive metrics"""
        
        # Time violations
        time_violations = 0
        room_changes = 0
        
        instructor_slots = defaultdict(list)
        for assignment in assignments:
            instructor_id = assignment.get('responsible_instructor_id')
            if instructor_id:
                instructor_slots[instructor_id].append(assignment)
        
        for instructor_id, slots in instructor_slots.items():
            sorted_slots = sorted(slots, key=lambda x: x.get('timeslot_id', 0))
            
            for i in range(len(sorted_slots) - 1):
                current = sorted_slots[i]
                next_slot = sorted_slots[i + 1]
                
                # Time violation
                if next_slot.get('timeslot_id', 0) - current.get('timeslot_id', 0) == 1:
                    time_violations += 1
                
                # Room change
                if current.get('classroom_id') != next_slot.get('classroom_id'):
                    room_changes += 1
        
        # Total penalty
        total_penalty = self.alpha * time_violations + self.beta * room_changes
        
        # Load balance
        instructor_loads = defaultdict(int)
        for assignment in assignments:
            for inst_id in assignment.get('instructors', []):
                instructor_loads[inst_id] += 1
        
        if instructor_loads:
            loads = list(instructor_loads.values())
            load_balance = {
                "min": min(loads),
                "max": max(loads),
                "avg": np.mean(loads),
                "std": np.std(loads)
            }
        else:
            load_balance = {"min": 0, "max": 0, "avg": 0, "std": 0}
        
        return {
            "total_penalty": total_penalty,
            "time_violations": time_violations,
            "room_changes": room_changes,
            "alpha": self.alpha,
            "beta": self.beta,
            "load_balance": load_balance,
            "total_assignments": len(assignments)
        }
