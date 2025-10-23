"""
Tests for rules enforcement service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.rules import RulesService


class TestRulesService:
    """Test cases for Rules service."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = RulesService()
        
        assert service.min_class_count == 5
        assert service.max_class_count == 7
        assert service.min_instructors_bitirme == 2
        assert service.min_instructors_ara == 1
    
    def test_initialization_custom_params(self):
        """Test service initialization with custom parameters."""
        service = RulesService()
        service.min_class_count = 3
        service.max_class_count = 10
        
        assert service.min_class_count == 3
        assert service.max_class_count == 10
    
    @pytest.mark.asyncio
    async def test_validate_solution_feasibility_valid(self):
        """Test validation of a valid solution."""
        service = RulesService()
        db_mock = AsyncMock()
        
        # Mock projects
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.type = "bitirme"
        
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.type = "ara"
        
        db_mock.execute.return_value.scalars.return_value.all.return_value = [
            mock_project1, mock_project2
        ]
        
        # Valid solution
        solution = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1, 2]
            },
            {
                "project_id": 2,
                "classroom_id": 2,
                "timeslot_id": 2,
                "instructors": [3]
            }
        ]
        
        result = await service.validate_solution_feasibility(db_mock, solution)
        
        assert "is_feasible" in result
        assert "violations" in result
        assert "warnings" in result
        assert "violation_count" in result
        assert "warning_count" in result
    
    @pytest.mark.asyncio
    async def test_validate_solution_feasibility_conflicts(self):
        """Test validation of solution with conflicts."""
        service = RulesService()
        db_mock = AsyncMock()
        
        # Mock projects
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.type = "bitirme"
        
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.type = "ara"
        
        db_mock.execute.return_value.scalars.return_value.all.return_value = [
            mock_project1, mock_project2
        ]
        
        # Solution with conflicts (same classroom and timeslot)
        solution = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1, 2]
            },
            {
                "project_id": 2,
                "classroom_id": 1,  # Same classroom
                "timeslot_id": 1,   # Same timeslot
                "instructors": [3]
            }
        ]
        
        result = await service.validate_solution_feasibility(db_mock, solution)
        
        assert result["is_feasible"] == False
        assert result["violation_count"] > 0
        
        # Check for slot conflict violation
        slot_conflicts = [v for v in result["violations"] if v["type"] == "slot_conflict"]
        assert len(slot_conflicts) > 0
    
    @pytest.mark.asyncio
    async def test_validate_solution_feasibility_insufficient_instructors(self):
        """Test validation with insufficient instructors."""
        service = RulesService()
        db_mock = AsyncMock()
        
        # Mock projects
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.type = "bitirme"  # Needs 2 instructors
        
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.type = "ara"  # Needs 1 instructor
        
        db_mock.execute.return_value.scalars.return_value.all.return_value = [
            mock_project1, mock_project2
        ]
        
        # Solution with insufficient instructors
        solution = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1]  # Only 1 instructor for bitirme project
            },
            {
                "project_id": 2,
                "classroom_id": 2,
                "timeslot_id": 2,
                "instructors": []  # No instructors for ara project
            }
        ]
        
        result = await service.validate_solution_feasibility(db_mock, solution)
        
        assert result["is_feasible"] == False
        assert result["violation_count"] > 0
        
        # Check for insufficient instructors violations
        instructor_violations = [v for v in result["violations"] if v["type"] == "insufficient_instructors"]
        assert len(instructor_violations) >= 2  # Both projects have insufficient instructors
    
    def test_check_class_count_constraints(self):
        """Test class count constraint checking."""
        service = RulesService()
        
        # Mock projects
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.type = "bitirme"
        
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.type = "ara"
        
        projects = [mock_project1, mock_project2]
        
        # Solution with too few classes
        solution = [
            {"project_id": 1, "classroom_id": 1},
            {"project_id": 2, "classroom_id": 1}  # Same classroom, so only 1 class
        ]
        
        import asyncio
        violations = asyncio.run(service._check_class_count_constraints(solution, projects))
        
        assert len(violations) > 0
        min_violations = [v for v in violations if v["type"] == "min_class_count"]
        assert len(min_violations) > 0
    
    def test_check_slot_conflicts(self):
        """Test slot conflict checking."""
        service = RulesService()
        
        # Solution with conflicts
        solution = [
            {"project_id": 1, "classroom_id": 1, "timeslot_id": 1},
            {"project_id": 2, "classroom_id": 1, "timeslot_id": 1}  # Conflict
        ]
        
        import asyncio
        violations = asyncio.run(service._check_slot_conflicts(solution))
        
        assert len(violations) > 0
        conflict_violations = [v for v in violations if v["type"] == "slot_conflict"]
        assert len(conflict_violations) > 0
    
    def test_fix_instructor_assignments(self):
        """Test fixing instructor assignments."""
        service = RulesService()
        
        # Mock projects
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.type = "bitirme"
        
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.type = "ara"
        
        projects = [mock_project1, mock_project2]
        
        # Mock instructors
        mock_instructor1 = MagicMock()
        mock_instructor1.id = 1
        mock_instructor1.type = "prof"
        
        mock_instructor2 = MagicMock()
        mock_instructor2.id = 2
        mock_instructor2.type = "assistant"
        
        instructors = [mock_instructor1, mock_instructor2]
        
        # Solution with insufficient instructors
        solution = [
            {"project_id": 1, "instructors": [1]},  # Needs 2 for bitirme
            {"project_id": 2, "instructors": []}    # Needs 1 for ara
        ]
        
        corrected = service._fix_instructor_assignments(solution, projects, instructors)
        
        assert len(corrected) == 2
        assert len(corrected[0]["instructors"]) >= 2  # Bitirme project should have at least 2
        assert len(corrected[1]["instructors"]) >= 1  # Ara project should have at least 1
    
    def test_fix_slot_conflicts(self):
        """Test fixing slot conflicts."""
        service = RulesService()
        
        # Mock classrooms
        mock_classroom1 = MagicMock()
        mock_classroom1.id = 1
        
        mock_classroom2 = MagicMock()
        mock_classroom2.id = 2
        
        classrooms = [mock_classroom1, mock_classroom2]
        
        # Mock timeslots
        mock_timeslot1 = MagicMock()
        mock_timeslot1.id = 1
        
        mock_timeslot2 = MagicMock()
        mock_timeslot2.id = 2
        
        timeslots = [mock_timeslot1, mock_timeslot2]
        
        # Solution with conflicts
        solution = [
            {"project_id": 1, "classroom_id": 1, "timeslot_id": 1},
            {"project_id": 2, "classroom_id": 1, "timeslot_id": 1}  # Conflict
        ]
        
        corrected = service._fix_slot_conflicts(solution, classrooms, timeslots)
        
        assert len(corrected) == 2
        # At least one assignment should be moved to avoid conflict
        classroom_timeslot_pairs = [(s["classroom_id"], s["timeslot_id"]) for s in corrected]
        assert len(set(classroom_timeslot_pairs)) == len(classroom_timeslot_pairs)  # No duplicates
    
    def test_get_configurable_constraints(self):
        """Test getting configurable constraints."""
        service = RulesService()
        
        constraints = service.get_configurable_constraints()
        
        assert "min_class_count" in constraints
        assert "max_class_count" in constraints
        assert "min_instructors_bitirme" in constraints
        assert "min_instructors_ara" in constraints
        assert "description" in constraints
        
        assert constraints["min_class_count"] == 5
        assert constraints["max_class_count"] == 7
        assert constraints["min_instructors_bitirme"] == 2
        assert constraints["min_instructors_ara"] == 1
    
    def test_update_constraints(self):
        """Test updating constraints."""
        service = RulesService()
        
        new_constraints = {
            "min_class_count": 3,
            "max_class_count": 10,
            "min_instructors_bitirme": 3,
            "min_instructors_ara": 2
        }
        
        service.update_constraints(new_constraints)
        
        assert service.min_class_count == 3
        assert service.max_class_count == 10
        assert service.min_instructors_bitirme == 3
        assert service.min_instructors_ara == 2
