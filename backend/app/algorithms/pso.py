import random
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class ParticleSwarmOptimization(BaseAlgorithm):
    """Particle Swarm Optimization algorithm implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        swarm_size=30,
        iterations=100,
        inertia_weight=0.7,
        cognitive_coefficient=1.5,
        social_coefficient=1.5,
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'swarm_size': swarm_size,
            'iterations': iterations,
            'inertia_weight': inertia_weight,
            'cognitive_coefficient': cognitive_coefficient,
            'social_coefficient': social_coefficient,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['swarm_size', 'iterations', 'inertia_weight', 
                          'cognitive_coefficient', 'social_coefficient',
                          'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        return True
        
    def optimize(self) -> Dict[str, Any]:
        """Run Particle Swarm Optimization algorithm."""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        # Initialize swarm
        particles, velocities = self._initialize_swarm()
        
        # Evaluate particles
        particle_fitness = [self._evaluate_fitness(p) for p in particles]
        
        # Initialize personal best and global best
        personal_best = particles.copy()
        personal_best_fitness = particle_fitness.copy()
        
        global_best_idx = np.argmax(particle_fitness)
        global_best = particles[global_best_idx].copy()
        global_best_fitness = particle_fitness[global_best_idx]
        
        # Main PSO loop
        for iteration in range(self.parameters['iterations']):
            # Update each particle
            for i in range(self.parameters['swarm_size']):
                # Update velocity
                velocities[i] = self._update_velocity(
                    velocities[i], 
                    particles[i], 
                    personal_best[i], 
                    global_best
                )
                
                # Update position
                particles[i] = self._update_position(particles[i], velocities[i])
                
                # Evaluate new position
                fitness = self._evaluate_fitness(particles[i])
                
                # Update personal best
                if fitness > personal_best_fitness[i]:
                    personal_best[i] = particles[i].copy()
                    personal_best_fitness[i] = fitness
                    
                    # Update global best
                    if fitness > global_best_fitness:
                        global_best = particles[i].copy()
                        global_best_fitness = fitness
        
        # Convert best solution to assignments
        assignments = self._solution_to_assignments(global_best)
        
        # Calculate metrics
        metrics = self._calculate_metrics(global_best)
        
        return {
            "assignments": assignments,
            "metrics": metrics,
            "fitness": global_best_fitness
        }
        
    def _initialize_swarm(self) -> Tuple[List[List[Tuple[int, int, int]]], List[List[Tuple[float, float, float]]]]:
        """Initialize particles and velocities."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        particles = []
        velocities = []
        
        # Generate initial particles
        for _ in range(self.parameters['swarm_size']):
            particle = []
            velocity = []
            
            for project_idx in range(len(project_ids)):
                project_id = project_ids[project_idx]
                project = self.projects[project_id]
                
                # For final projects, ensure responsible is professor
                if project.get("type") == "final" and professor_indices:
                    responsible_idx = random.choice(professor_indices)
                else:
                    responsible_idx = random.randrange(len(instructor_ids))
                    
                # Select assistants
                available = [i for i in range(len(instructor_ids)) if i != responsible_idx]
                if available:
                    if len(available) >= 2:
                        assistant1_idx, assistant2_idx = random.sample(available, 2)
                    else:
                        assistant1_idx = available[0]
                        assistant2_idx = available[0]
                else:
                    assistant1_idx = responsible_idx
                    assistant2_idx = responsible_idx
                    
                particle.append((responsible_idx, assistant1_idx, assistant2_idx))
                
                # Initialize random velocity components
                v_resp = random.uniform(-1, 1)
                v_asst1 = random.uniform(-1, 1)
                v_asst2 = random.uniform(-1, 1)
                velocity.append((v_resp, v_asst1, v_asst2))
            
            particles.append(particle)
            velocities.append(velocity)
        
        return particles, velocities
        
    def _update_velocity(
        self, 
        velocity: List[Tuple[float, float, float]], 
        position: List[Tuple[int, int, int]], 
        personal_best: List[Tuple[int, int, int]], 
        global_best: List[Tuple[int, int, int]]
    ) -> List[Tuple[float, float, float]]:
        """Update velocity using PSO formula."""
        new_velocity = []
        
        for i in range(len(velocity)):
            v_resp, v_asst1, v_asst2 = velocity[i]
            pos_resp, pos_asst1, pos_asst2 = position[i]
            pbest_resp, pbest_asst1, pbest_asst2 = personal_best[i]
            gbest_resp, gbest_asst1, gbest_asst2 = global_best[i]
            
            # Calculate new velocity components
            # v = w*v + c1*r1*(pbest - pos) + c2*r2*(gbest - pos)
            r1_resp = random.random()
            r1_asst1 = random.random()
            r1_asst2 = random.random()
            r2_resp = random.random()
            r2_asst1 = random.random()
            r2_asst2 = random.random()
            
            new_v_resp = (
                self.parameters['inertia_weight'] * v_resp +
                self.parameters['cognitive_coefficient'] * r1_resp * (pbest_resp - pos_resp) +
                self.parameters['social_coefficient'] * r2_resp * (gbest_resp - pos_resp)
            )
            
            new_v_asst1 = (
                self.parameters['inertia_weight'] * v_asst1 +
                self.parameters['cognitive_coefficient'] * r1_asst1 * (pbest_asst1 - pos_asst1) +
                self.parameters['social_coefficient'] * r2_asst1 * (gbest_asst1 - pos_asst1)
            )
            
            new_v_asst2 = (
                self.parameters['inertia_weight'] * v_asst2 +
                self.parameters['cognitive_coefficient'] * r1_asst2 * (pbest_asst2 - pos_asst2) +
                self.parameters['social_coefficient'] * r2_asst2 * (gbest_asst2 - pos_asst2)
            )
            
            # Clamp velocity to avoid excessive movement
            new_v_resp = max(min(new_v_resp, 2.0), -2.0)
            new_v_asst1 = max(min(new_v_asst1, 2.0), -2.0)
            new_v_asst2 = max(min(new_v_asst2, 2.0), -2.0)
            
            new_velocity.append((new_v_resp, new_v_asst1, new_v_asst2))
        
        return new_velocity
        
    def _update_position(
        self, 
        position: List[Tuple[int, int, int]], 
        velocity: List[Tuple[float, float, float]]
    ) -> List[Tuple[int, int, int]]:
        """Update position based on velocity."""
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        project_ids = list(self.projects.keys())
        
        new_position = []
        
        for i in range(len(position)):
            pos_resp, pos_asst1, pos_asst2 = position[i]
            v_resp, v_asst1, v_asst2 = velocity[i]
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            # Calculate new positions (continuous)
            new_pos_resp_cont = pos_resp + v_resp
            new_pos_asst1_cont = pos_asst1 + v_asst1
            new_pos_asst2_cont = pos_asst2 + v_asst2
            
            # Convert to discrete positions (indices)
            # Use probabilistic approach based on distance to each instructor index
            
            # For responsible position
            if project.get("type") == "final" and professor_indices:
                # For final projects, responsible must be professor
                probs = []
                for idx in professor_indices:
                    # Calculate probability based on distance (closer = higher probability)
                    distance = abs(new_pos_resp_cont - idx)
                    probs.append((idx, 1.0 / (distance + 0.1)))  # Add small constant to avoid division by zero
                
                # Select based on probabilities
                total_prob = sum(p[1] for p in probs)
                if total_prob > 0:
                    r = random.random() * total_prob
                    cumulative = 0
                    for idx, prob in probs:
                        cumulative += prob
                        if r <= cumulative:
                            new_pos_resp = idx
                            break
                    else:
                        new_pos_resp = professor_indices[0]
                else:
                    new_pos_resp = random.choice(professor_indices)
            else:
                # For other projects, can be any instructor
                probs = []
                for idx in range(len(instructor_ids)):
                    # Calculate probability based on distance
                    distance = abs(new_pos_resp_cont - idx)
                    probs.append((idx, 1.0 / (distance + 0.1)))
                
                # Select based on probabilities
                total_prob = sum(p[1] for p in probs)
                if total_prob > 0:
                    r = random.random() * total_prob
                    cumulative = 0
                    for idx, prob in probs:
                        cumulative += prob
                        if r <= cumulative:
                            new_pos_resp = idx
                            break
                    else:
                        new_pos_resp = random.randrange(len(instructor_ids))
                else:
                    new_pos_resp = random.randrange(len(instructor_ids))
            
            # For assistant positions, use similar approach but exclude responsible
            available = [i for i in range(len(instructor_ids)) if i != new_pos_resp]
            
            if available:
                # For assistant1
                probs = []
                for idx in available:
                    distance = abs(new_pos_asst1_cont - idx)
                    probs.append((idx, 1.0 / (distance + 0.1)))
                
                total_prob = sum(p[1] for p in probs)
                if total_prob > 0:
                    r = random.random() * total_prob
                    cumulative = 0
                    for idx, prob in probs:
                        cumulative += prob
                        if r <= cumulative:
                            new_pos_asst1 = idx
                            break
                    else:
                        new_pos_asst1 = random.choice(available)
                else:
                    new_pos_asst1 = random.choice(available)
                
                # For assistant2, exclude both responsible and assistant1 if possible
                available2 = [i for i in available if i != new_pos_asst1]
                if available2:
                    probs = []
                    for idx in available2:
                        distance = abs(new_pos_asst2_cont - idx)
                        probs.append((idx, 1.0 / (distance + 0.1)))
                    
                    total_prob = sum(p[1] for p in probs)
                    if total_prob > 0:
                        r = random.random() * total_prob
                        cumulative = 0
                        for idx, prob in probs:
                            cumulative += prob
                            if r <= cumulative:
                                new_pos_asst2 = idx
                                break
                        else:
                            new_pos_asst2 = random.choice(available2)
                    else:
                        new_pos_asst2 = random.choice(available2)
                else:
                    new_pos_asst2 = new_pos_asst1
            else:
                # If no available instructors, reuse responsible
                new_pos_asst1 = new_pos_resp
                new_pos_asst2 = new_pos_resp
            
            new_position.append((new_pos_resp, new_pos_asst1, new_pos_asst2))
        
        return new_position
        
    def _evaluate_fitness(self, solution: List[Tuple[int, int, int]]) -> float:
        """Evaluate fitness of a solution (higher is better)."""
        rule_violations = self._calculate_rule_violations(solution)
        load_imbalance = self._calculate_load_imbalance(solution)
        classroom_changes = self._calculate_classroom_changes(solution)
        
        # Calculate weighted fitness (negative because lower violations/imbalance/changes is better)
        fitness = -(
            rule_violations * self.parameters['rule_weight'] +
            load_imbalance * self.parameters['load_weight'] +
            classroom_changes * self.parameters['classroom_weight']
        )
        
        return fitness
        
    def _calculate_rule_violations(self, solution: List[Tuple[int, int, int]]) -> float:
        """Calculate number of rule violations in a solution."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        violations = 0
        
        for i, (responsible_idx, assistant1_idx, assistant2_idx) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            responsible_id = instructor_ids[responsible_idx]
            
            # Rule 1: Responsible should be professor
            if self.instructors[responsible_id].get("type") != "professor":
                violations += 1
            
            # Rule 2: Final projects need at least 2 professors
            if project.get("type") == "final":
                professor_count = 0
                for instr_idx in [responsible_idx, assistant1_idx, assistant2_idx]:
                    instr_id = instructor_ids[instr_idx]
                    if self.instructors[instr_id].get("type") == "professor":
                        professor_count += 1
                
                if professor_count < 2:
                    violations += 1
        
        return violations
        
    def _calculate_load_imbalance(self, solution: List[Tuple[int, int, int]]) -> float:
        """Calculate load imbalance among instructors."""
        instructor_ids = list(self.instructors.keys())
        instructor_loads = [0] * len(instructor_ids)
        
        for responsible_idx, assistant1_idx, assistant2_idx in solution:
            instructor_loads[responsible_idx] += 1
            instructor_loads[assistant1_idx] += 1
            instructor_loads[assistant2_idx] += 1
        
        # Calculate standard deviation as measure of imbalance
        if instructor_loads:
            return np.std(instructor_loads)
        return 0
        
    def _calculate_classroom_changes(self, solution: List[Tuple[int, int, int]]) -> float:
        """Calculate total classroom changes for instructors."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Track classrooms for each instructor
        instructor_classrooms = {i: [] for i in range(len(instructor_ids))}
        
        for i, (responsible_idx, assistant1_idx, assistant2_idx) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            if project.get("classroom"):
                instructor_classrooms[responsible_idx].append(project.get("classroom"))
                instructor_classrooms[assistant1_idx].append(project.get("classroom"))
                instructor_classrooms[assistant2_idx].append(project.get("classroom"))
        
        # Calculate changes
        total_changes = 0
        for instructor_idx, classrooms in instructor_classrooms.items():
            if classrooms:
                # Count unique classrooms - 1 = number of changes
                changes = len(set(classrooms)) - 1
                if changes > 0:
                    # Professors have higher penalty for changes
                    instructor_id = instructor_ids[instructor_idx]
                    if self.instructors[instructor_id].get("type") == "professor":
                        total_changes += changes * 2  # Higher weight for professors
                    else:
                        total_changes += changes
        
        return total_changes
        
    def _solution_to_assignments(self, solution: List[Tuple[int, int, int]]) -> Dict[int, Dict]:
        """Convert solution to assignment dictionary."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        assignments = {}
        for i, (responsible_idx, assistant1_idx, assistant2_idx) in enumerate(solution):
            project_id = project_ids[i]
            
            assignments[project_id] = {
                "responsible": instructor_ids[responsible_idx],
                "assistant1": instructor_ids[assistant1_idx],
                "assistant2": instructor_ids[assistant2_idx]
            }
        
        return assignments
        
    def _calculate_metrics(self, solution: List[Tuple[int, int, int]]) -> Dict[str, float]:
        """Calculate metrics for the solution."""
        rule_violations = self._calculate_rule_violations(solution)
        load_imbalance = self._calculate_load_imbalance(solution)
        classroom_changes = self._calculate_classroom_changes(solution)
        
        return {
            "rule_violations": rule_violations,
            "load_imbalance": load_imbalance,
            "classroom_changes": classroom_changes,
            "fitness": -(rule_violations * self.parameters['rule_weight'] + 
                       load_imbalance * self.parameters['load_weight'] + 
                       classroom_changes * self.parameters['classroom_weight'])
        }
