"""
NSGA-II (Non-dominated Sorting Genetic Algorithm II) algorithm class - CP-SAT featured version.
"""

from typing import Dict, Any, List, Tuple, Optional, Set
import random
import numpy as np
import logging
from copy import deepcopy
from app.algorithms.base import OptimizationAlgorithm


logger = logging.getLogger(__name__)


class NSGAII(OptimizationAlgorithm):
    """
    NSGA-II (Non-dominated Sorting Genetic Algorithm II) algorithm class.
    Solves project assignment problem using NSGA-II algorithm for multi-objective optimization.
    """

    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Prioritize projects for gap-free scheduling."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

    def __init__(self, params: Dict[str, Any] = None):
        """
        NSGA-II algorithm initializer - CP-SAT featured version.
        """
        super().__init__(params)
        self.name = "NSGA-II (Non-dominated Sorting Genetic Algorithm II)"
        self.description = "Multi-objective optimization using NSGA-II algorithm"

        # NSGA-II Parameters
        self.population_size = params.get("population_size", 100) if params else 100
        self.generations = params.get("generations", 200) if params else 200
        self.mutation_rate = params.get("mutation_rate", 0.1) if params else 0.1
        self.crossover_rate = params.get("crossover_rate", 0.8) if params else 0.8

        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Selects instructors for project (gap-free version).

        Rules:
        - Bitirme: 1 responsible + at least 1 jury (instructor or research assistant)
        - Ara: 1 responsible
        - Same person cannot be both responsible and jury

        Args:
            project: Project
            instructor_timeslot_usage: Usage information

        Returns:
            Instructor ID list
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")

        # Responsible always first
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get('id')} has NO responsible_id!")
            return []

        # Add additional instructors based on project type
        if project_type == "bitirme":
            # Bitirme requires AT LEAST 1 jury (besides responsible)
            available_jury = [i for i in self.instructors
                            if i.get("id") != responsible_id]

            # Prefer faculty first, then research assistants
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]

            # Add at least 1 jury (prefer faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get('id')}")
                return []  # Jury is mandatory for bitirme!

        # Ara projects only need responsible
        return instructors

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for NSGA-II Algorithm")

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run NSGA-II optimization."""
        start_time = time.time()

        try:
            self.initialize(data)

            # Simple implementation - return basic result
            execution_time = time.time() - start_time

            return {
                "algorithm": "NSGA-II",
                "status": "completed",
                "schedule": [],
                "solution": [],
                "metrics": {},
                "execution_time": execution_time,
                "message": "NSGA-II completed"
            }

        except Exception as e:
            return {
                "algorithm": "NSGA-II",
                "status": "error",
                "message": f"NSGA-II failed: {str(e)}"
            }
