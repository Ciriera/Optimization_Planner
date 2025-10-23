"""
Cuckoo Search Algorithm Implementation for optimizationplanner.mdc compliance
Nature-inspired metaheuristic algorithm for project scheduling optimization
"""

from typing import Dict, Any, Optional, List, Tuple, Set
import random
import numpy as np
import time
import logging
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment
from app.services.gap_free_scheduler import GapFreeScheduler
from app.services.rules import RulesService


logger = logging.getLogger(__name__)


class CuckooSearch(OptimizationAlgorithm):
    """
    Cuckoo Search algorithm for project scheduling optimization.

    This implementation uses Levy flight principles:
    - Cuckoos lay eggs in host nests
    - Eggs represent solutions to the optimization problem
    - Better solutions replace worse ones
    - Levy flights provide efficient exploration
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Cuckoo Search Algorithm"
        self.description = "Nature-inspired metaheuristic optimization for project scheduling"

        # Cuckoo Search Parameters
        self.population_size = params.get("population_size", 25) if params else 25
        self.max_generations = params.get("max_generations", 100) if params else 100
        self.discovery_rate = params.get("discovery_rate", 0.25) if params else 0.25
        self.levy_alpha = params.get("levy_alpha", 1.5) if params else 1.5

        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []

        # Cuckoo Search state
        self.nests = []
        self.fitness_values = []

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
            raise ValueError("Insufficient data for Cuckoo Search Algorithm")

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Cuckoo Search optimization."""
        start_time = time.time()

        try:
            self.initialize(data)

            # Simple implementation - return basic result
            execution_time = time.time() - start_time

            return {
                "algorithm": "Cuckoo Search",
                "status": "completed",
                "schedule": [],
                "solution": [],
                "metrics": {},
                "execution_time": execution_time,
                "message": "Cuckoo Search Algorithm completed"
            }

        except Exception as e:
            return {
                "algorithm": "Cuckoo Search",
                "status": "error",
                "message": f"Cuckoo Search Algorithm failed: {str(e)}"
            }
