import pytest
from typing import Dict, Any

from app.algorithms.genetic_algorithm import EnhancedGeneticAlgorithm


@pytest.fixture()
def be_test_data() -> Dict[str, Any]:
    instructors = [
        {"id": 1, "name": "Dr. A"},
        {"id": 2, "name": "Dr. B"},
        {"id": 3, "name": "Dr. C"},
        {"id": 4, "name": "Dr. D"},
    ]
    classrooms = [
        {"id": 101, "name": "Room101"},
        {"id": 102, "name": "Room102"},
    ]
    timeslots = [
        {"id": 1, "start_time": "09:00"},
        {"id": 2, "start_time": "09:30"},
        {"id": 3, "start_time": "10:00"},
    ]
    projects = [
        {"id": 201, "type": "ara", "responsible_instructor_id": 1},
        {"id": 202, "type": "bitirme", "responsible_instructor_id": 2},
        {"id": 203, "type": "ara", "responsible_instructor_id": 3},
    ]

    return {
        "instructors": instructors,
        "classrooms": classrooms,
        "timeslots": timeslots,
        "projects": projects,
    }


def test_be_jury_refinement_basic(be_test_data: Dict[str, Any]):
    params = {
        "jury_refinement_layer": True,
        "population_size": 8,
        "generations": 2,
        "mutation_rate": 0.15,
        "crossover_rate": 0.85,
        "jury_continuity_weight": 0.6,
        "jury_proximity_weight": 0.4,
        "jury_semi_consecutive_weight": 0.5,
    }

    ga = EnhancedGeneticAlgorithm(params)
    result = ga.execute(be_test_data)

    assert isinstance(result, dict)
    assignments = result.get("assignments") or result.get("schedule") or []
    assert isinstance(assignments, list)

    # All projects that are assigned should end with 2 jury members (instructors length = 3)
    by_project = {}
    for a in assignments:
        if isinstance(a, dict) and a.get("project_id"):
            pid = a.get("project_id")
            juries = len(a.get("instructors", [])) - 1
            by_project[pid] = max(by_project.get(pid, 0), juries)

    # at least one project should have 2 juries
    assert any(juries >= 2 for juries in by_project.values())
