"""
Standard Fitness Scoring System for All Algorithms

This module provides a standardized fitness scoring system that can be used
across all optimization algorithms to ensure consistent evaluation and comparison.

🎯 CORE METRICS:
1. Coverage Score: How many projects are scheduled
2. Consecutive Score: How well consecutive grouping is achieved
3. Load Balance Score: How evenly workload is distributed
4. Classroom Efficiency: How well classrooms are utilized
5. Time Efficiency: How well timeslots are utilized
6. Conflict Score: Penalty for any conflicts
7. Gap Score: Penalty for gaps in schedule
8. Early Slot Score: Reward for using early timeslots

All metrics are normalized to 0-100 scale for consistency.
"""

from typing import Dict, Any, List, Set, Tuple
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class StandardFitnessScorer:
    """
    Standard fitness scoring system for all optimization algorithms.
    
    Provides consistent, comparable fitness scores across different algorithms.
    All scores are normalized to 0-100 scale.
    """
    
    def __init__(
        self,
        projects: List[Dict[str, Any]],
        instructors: List[Dict[str, Any]],
        classrooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]]
    ):
        """
        Initialize the standard fitness scorer.
        
        Args:
            projects: List of projects
            instructors: List of instructors
            classrooms: List of classrooms
            timeslots: List of timeslots
        """
        self.projects = projects
        self.instructors = instructors
        self.classrooms = classrooms
        self.timeslots = timeslots
        
        # Standard weights (can be customized)
        self.weights = {
            "coverage": 25.0,      # W1: Project coverage
            "consecutive": 20.0,   # W2: Consecutive grouping
            "load_balance": 20.0,  # W3: Load balance
            "classroom": 15.0,     # W4: Classroom efficiency
            "time": 10.0,          # W5: Time efficiency
            "conflicts": 10.0,     # W6: Conflict penalty
            "gaps": 5.0,           # W7: Gap penalty
            "early_slots": 5.0     # W8: Early slot bonus
        }
    
    def calculate_total_fitness(
        self, 
        assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate total fitness score with detailed breakdown.
        
        Args:
            assignments: List of schedule assignments
            
        Returns:
            Dict with total score and component scores
        """
        if not assignments:
            return {
                "total": 0.0,
                "components": {},
                "grade": "F",
                "percentage": 0.0
            }
        
        # Calculate individual components
        coverage_score = self._calculate_coverage_score(assignments)
        consecutive_score = self._calculate_consecutive_score(assignments)
        load_balance_score = self._calculate_load_balance_score(assignments)
        classroom_score = self._calculate_classroom_efficiency(assignments)
        time_score = self._calculate_time_efficiency(assignments)
        conflict_penalty = self._calculate_conflict_penalty(assignments)
        gap_penalty = self._calculate_gap_penalty(assignments)
        early_slot_bonus = self._calculate_early_slot_bonus(assignments)
        
        # Calculate weighted total
        total_score = (
            coverage_score * self.weights["coverage"] / 100.0 +
            consecutive_score * self.weights["consecutive"] / 100.0 +
            load_balance_score * self.weights["load_balance"] / 100.0 +
            classroom_score * self.weights["classroom"] / 100.0 +
            time_score * self.weights["time"] / 100.0 -
            conflict_penalty * self.weights["conflicts"] / 100.0 -
            gap_penalty * self.weights["gaps"] / 100.0 +
            early_slot_bonus * self.weights["early_slots"] / 100.0
        )
        
        # Normalize to 0-100 scale
        total_score = max(0, min(100, total_score))
        
        # Determine grade
        grade = self._get_grade(total_score)
        
        return {
            "total": round(total_score, 2),
            "percentage": round(total_score, 2),
            "grade": grade,
            "components": {
                "coverage": round(coverage_score, 2),
                "consecutive": round(consecutive_score, 2),
                "load_balance": round(load_balance_score, 2),
                "classroom": round(classroom_score, 2),
                "time": round(time_score, 2),
                "conflict_penalty": round(conflict_penalty, 2),
                "gap_penalty": round(gap_penalty, 2),
                "early_slot_bonus": round(early_slot_bonus, 2)
            },
            "weights": self.weights
        }
    
    def _calculate_coverage_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate project coverage score (0-100).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Coverage score
        """
        if not self.projects:
            return 0.0
        
        scheduled_projects = set(a.get("project_id") for a in assignments if a.get("project_id"))
        total_projects = len(self.projects)
        
        coverage = len(scheduled_projects) / total_projects
        return coverage * 100.0
    
    def _calculate_consecutive_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate consecutive grouping score (0-100).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Consecutive score
        """
        if not assignments:
            return 0.0
        
        # Build instructor timeslot mapping
        instructor_slots = defaultdict(list)
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                timeslot_id = assignment.get("timeslot_id")
                if timeslot_id:
                    instructor_slots[instructor_id].append(timeslot_id)
        
        # Count consecutive sequences
        total_consecutive = 0
        total_possible = 0
        
        for instructor_id, slots in instructor_slots.items():
            sorted_slots = sorted(slots)
            if len(sorted_slots) <= 1:
                continue
            
            total_possible += len(sorted_slots) - 1
            
            for i in range(len(sorted_slots) - 1):
                if sorted_slots[i + 1] - sorted_slots[i] == 1:
                    total_consecutive += 1
        
        if total_possible == 0:
            return 100.0  # No slots to compare
        
        consecutive_ratio = total_consecutive / total_possible
        return consecutive_ratio * 100.0
    
    def _calculate_load_balance_score(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate load balance score (0-100).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Load balance score
        """
        if not assignments or not self.instructors:
            return 0.0
        
        # Count assignments per instructor
        instructor_counts = defaultdict(int)
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                instructor_counts[instructor_id] += 1
        
        if not instructor_counts:
            return 0.0
        
        # Calculate variance
        counts = list(instructor_counts.values())
        mean_count = np.mean(counts)
        variance = np.var(counts)
        
        # Normalize: Low variance = high score
        if mean_count == 0:
            return 0.0
        
        # Use coefficient of variation (CV)
        cv = np.sqrt(variance) / mean_count if mean_count > 0 else 0
        
        # Convert to score: CV = 0 → 100, CV = 1 → 0
        balance_score = max(0, (1 - cv) * 100.0)
        return balance_score
    
    def _calculate_classroom_efficiency(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate classroom efficiency score (0-100).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Classroom efficiency score
        """
        if not assignments or not self.classrooms:
            return 0.0
        
        # Build classroom usage mapping
        classroom_usage = defaultdict(int)
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            if classroom_id:
                classroom_usage[classroom_id] += 1
        
        # Calculate usage variance
        if not classroom_usage:
            return 0.0
        
        usages = list(classroom_usage.values())
        mean_usage = np.mean(usages)
        variance = np.var(usages)
        
        # Normalize
        if mean_usage == 0:
            return 0.0
        
        cv = np.sqrt(variance) / mean_usage if mean_usage > 0 else 0
        efficiency_score = max(0, (1 - cv) * 100.0)
        
        return efficiency_score
    
    def _calculate_time_efficiency(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate time efficiency score (0-100).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Time efficiency score
        """
        if not assignments or not self.timeslots:
            return 0.0
        
        used_timeslots = set(a.get("timeslot_id") for a in assignments if a.get("timeslot_id"))
        total_timeslots = len(self.timeslots)
        
        # More timeslots used = better efficiency (spreading the load)
        usage_ratio = len(used_timeslots) / total_timeslots if total_timeslots > 0 else 0
        return usage_ratio * 100.0
    
    def _calculate_conflict_penalty(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate conflict penalty (0-100, higher is worse).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Conflict penalty
        """
        if not assignments:
            return 0.0
        
        conflicts = 0
        
        # Check for instructor conflicts (same instructor, same timeslot)
        instructor_timeslots = defaultdict(set)
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            for instructor_id in assignment.get("instructors", []):
                if timeslot_id in instructor_timeslots[instructor_id]:
                    conflicts += 1
                instructor_timeslots[instructor_id].add(timeslot_id)
        
        # Check for classroom conflicts (same classroom, same timeslot)
        classroom_timeslots = defaultdict(set)
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            if classroom_id and timeslot_id:
                if timeslot_id in classroom_timeslots[classroom_id]:
                    conflicts += 1
                classroom_timeslots[classroom_id].add(timeslot_id)
        
        # Normalize
        max_possible_conflicts = len(assignments)
        conflict_ratio = conflicts / max_possible_conflicts if max_possible_conflicts > 0 else 0
        return conflict_ratio * 100.0
    
    def _calculate_gap_penalty(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate gap penalty (0-100, higher is worse).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Gap penalty
        """
        if not assignments:
            return 0.0
        
        # Build classroom timeslot mapping
        classroom_slots = defaultdict(list)
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            if classroom_id and timeslot_id:
                classroom_slots[classroom_id].append(timeslot_id)
        
        # Count gaps
        total_gaps = 0
        total_sequences = 0
        
        for classroom_id, slots in classroom_slots.items():
            sorted_slots = sorted(slots)
            if len(sorted_slots) <= 1:
                continue
            
            total_sequences += 1
            
            for i in range(len(sorted_slots) - 1):
                gap_size = sorted_slots[i + 1] - sorted_slots[i] - 1
                if gap_size > 0:
                    total_gaps += gap_size
        
        if total_sequences == 0:
            return 0.0
        
        # Normalize
        avg_gap = total_gaps / total_sequences
        gap_score = min(100.0, avg_gap * 20.0)  # Each gap worth 20 points penalty
        return gap_score
    
    def _calculate_early_slot_bonus(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Calculate early slot bonus (0-100).
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Early slot bonus
        """
        if not assignments or not self.timeslots:
            return 0.0
        
        # Count assignments in early slots (first half of timeslots)
        mid_point = len(self.timeslots) // 2
        early_timeslot_ids = set(ts.get("id") for ts in self.timeslots[:mid_point])
        
        early_assignments = sum(
            1 for a in assignments 
            if a.get("timeslot_id") in early_timeslot_ids
        )
        
        total_assignments = len(assignments)
        early_ratio = early_assignments / total_assignments if total_assignments > 0 else 0
        return early_ratio * 100.0
    
    def _get_grade(self, score: float) -> str:
        """
        Convert numeric score to letter grade.
        
        Args:
            score: Numeric score (0-100)
            
        Returns:
            Letter grade (A+, A, B, C, D, F)
        """
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def get_detailed_report(self, assignments: List[Dict[str, Any]]) -> str:
        """
        Generate a detailed fitness report.
        
        Args:
            assignments: Schedule assignments
            
        Returns:
            Formatted report string
        """
        fitness = self.calculate_total_fitness(assignments)
        
        report = []
        report.append("=" * 60)
        report.append("STANDARD FITNESS REPORT")
        report.append("=" * 60)
        report.append(f"Total Score: {fitness['total']:.2f}/100 (Grade: {fitness['grade']})")
        report.append("")
        report.append("Component Breakdown:")
        report.append("-" * 60)
        
        for component, score in fitness['components'].items():
            weight = fitness['weights'].get(component, 0)
            report.append(f"  {component.ljust(20)}: {score:6.2f}/100 (weight: {weight:.1f}%)")
        
        report.append("=" * 60)
        
        return "\n".join(report)

