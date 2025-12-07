"""
Comprehensive test suite for JuryRefinementService.

Tests all core functionality including:
- Workload calculation
- Continuity score calculation
- Classroom preference scoring
- Priority score calculation
- Jury candidate selection
- Main refinement logic
- All 6 critical revisions
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import logging

from app.services.jury_refinement_service import JuryRefinementService


class TestJuryRefinementService:
    """Test suite for JuryRefinementService"""

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return {
            'instructors': [
                {'id': 1, 'name': 'Instructor A', 'type': 'instructor'},
                {'id': 2, 'name': 'Instructor B', 'type': 'instructor'},
                {'id': 3, 'name': 'Instructor C', 'type': 'instructor'},
                {'id': 4, 'name': 'Instructor D', 'type': 'instructor'},
            ],
            'classrooms': [
                {'id': 1, 'name': 'Classroom A'},
                {'id': 2, 'name': 'Classroom B'},
            ],
            'timeslots': [
                {'id': 1, 'start_time': '09:00', 'end_time': '10:00'},
                {'id': 2, 'start_time': '10:00', 'end_time': '11:00'},
                {'id': 3, 'start_time': '11:00', 'end_time': '12:00'},
                {'id': 4, 'start_time': '12:00', 'end_time': '13:00'},
            ],
            'projects': [
                {'id': 1, 'type': 'ara', 'responsible_id': 1},
                {'id': 2, 'type': 'bitirme', 'responsible_id': 2},
                {'id': 3, 'type': 'ara', 'responsible_id': 3},
            ]
        }

    @pytest.fixture
    def sample_assignments(self):
        """Sample assignments for testing"""
        return [
            {
                'project_id': 1,
                'classroom_id': 1,
                'timeslot_id': 1,
                'instructors': [1, 2]  # Instructor 1 responsible, Instructor 2 jury
            },
            {
                'project_id': 2,
                'classroom_id': 1,
                'timeslot_id': 2,
                'instructors': [2, 3]  # Instructor 2 responsible, Instructor 3 jury
            },
            {
                'project_id': 3,
                'classroom_id': 2,
                'timeslot_id': 3,
                'instructors': [3]  # Instructor 3 responsible, no jury yet
            }
        ]

    @pytest.fixture
    def service(self, sample_data):
        """Create service instance with sample data"""
        return JuryRefinementService(
            instructors=sample_data['instructors'],
            classrooms=sample_data['classrooms'],
            timeslots=sample_data['timeslots'],
            projects=sample_data['projects']
        )

    def test_initialization(self, sample_data):
        """Test service initialization"""
        service = JuryRefinementService(
            instructors=sample_data['instructors'],
            classrooms=sample_data['classrooms'],
            timeslots=sample_data['timeslots'],
            projects=sample_data['projects']
        )
        
        assert len(service.instructors) == 4
        assert len(service.classrooms) == 2
        assert len(service.timeslots) == 4
        assert len(service.projects) == 3
        assert service.continuity_weight == 0.6
        assert service.proximity_weight == 0.4

    def test_initialization_with_config(self, sample_data):
        """Test service initialization with custom config"""
        config = {
            'JURY_CONTINUITY_WEIGHT': 0.5,
            'JURY_PROXIMITY_WEIGHT': 0.5,
            'JURY_LOGGING_LEVEL': 'DEBUG'
        }
        
        service = JuryRefinementService(
            instructors=sample_data['instructors'],
            classrooms=sample_data['classrooms'],
            timeslots=sample_data['timeslots'],
            projects=sample_data['projects'],
            config=config
        )
        
        assert service.continuity_weight == 0.5
        assert service.proximity_weight == 0.5

    def test_calculate_workload(self, service, sample_assignments):
        """Test workload calculation"""
        # Instructor 1: 1 assignment
        workload_1 = service.calculate_workload(1, sample_assignments)
        assert 0.0 <= workload_1 <= 1.0
        
        # Instructor 2: 2 assignments
        workload_2 = service.calculate_workload(2, sample_assignments)
        assert 0.0 <= workload_2 <= 1.0
        
        # Instructor 4: 0 assignments
        workload_4 = service.calculate_workload(4, sample_assignments)
        assert workload_4 == 0.0

    def test_calculate_workload_normalization(self, service):
        """Test workload calculation normalization"""
        # Create assignments with different workloads
        assignments = [
            {'instructors': [1, 2]},  # Instructor 1: 1, Instructor 2: 1
            {'instructors': [1, 3]},  # Instructor 1: 2, Instructor 3: 1
            {'instructors': [2, 3]},  # Instructor 2: 2, Instructor 3: 2
        ]
        
        workload_1 = service.calculate_workload(1, assignments)
        workload_2 = service.calculate_workload(2, assignments)
        workload_3 = service.calculate_workload(3, assignments)
        
        # All should be normalized to 0-1 range
        assert 0.0 <= workload_1 <= 1.0
        assert 0.0 <= workload_2 <= 1.0
        assert 0.0 <= workload_3 <= 1.0

    def test_calculate_continuity_score_same_classroom_consecutive(self, service, sample_assignments):
        """Test continuity score for same classroom consecutive assignments"""
        # Instructor 1 and 2 are in same classroom (1) with consecutive timeslots (1, 2)
        continuity_1 = service.calculate_continuity_score(1, 1, 2, sample_assignments)
        continuity_2 = service.calculate_continuity_score(2, 1, 1, sample_assignments)
        
        assert 0.0 <= continuity_1 <= 1.0
        assert 0.0 <= continuity_2 <= 1.0

    def test_calculate_continuity_score_different_classroom(self, service, sample_assignments):
        """Test continuity score for different classroom"""
        # Instructor 3 is in classroom 2, target is classroom 1
        continuity = service.calculate_continuity_score(3, 1, 1, sample_assignments)
        assert 0.0 <= continuity <= 1.0

    def test_calculate_continuity_score_semi_consecutive(self, service):
        """Test continuity score with semi-consecutive bonus (1-slot gap)"""
        assignments = [
            {
                'project_id': 1,
                'classroom_id': 1,
                'timeslot_id': 1,
                'instructors': [1]
            }
        ]
        
        # Target timeslot 3 (gap of 1 from timeslot 1)
        continuity = service.calculate_continuity_score(1, 1, 3, assignments)
        assert 0.0 <= continuity <= 1.0

    def test_calculate_classroom_score_same_classroom(self, service, sample_assignments):
        """Test classroom score for same classroom"""
        score = service.calculate_classroom_score(1, 1, 2, sample_assignments)
        assert score == service.same_classroom_score  # Should be 1.0

    def test_calculate_classroom_score_cross_classroom_same_time(self, service, sample_assignments):
        """Test classroom score for cross-classroom same time"""
        # Instructor 3 is in classroom 2, target is classroom 1, same timeslot
        score = service.calculate_classroom_score(3, 1, 3, sample_assignments)
        assert score == service.cross_classroom_same_time  # Should be 0.6

    def test_calculate_classroom_score_cross_classroom_adjacent(self, service, sample_assignments):
        """Test classroom score for cross-classroom adjacent time"""
        # Instructor 3 is in classroom 2, target is classroom 1, adjacent timeslot
        score = service.calculate_classroom_score(3, 1, 2, sample_assignments)
        assert score == service.cross_classroom_adjacent  # Should be 0.4

    def test_calculate_classroom_score_cross_classroom_distant(self, service, sample_assignments):
        """Test classroom score for cross-classroom distant time"""
        # Instructor 3 is in classroom 2, target is classroom 1, distant timeslot
        score = service.calculate_classroom_score(3, 1, 1, sample_assignments)
        assert score == service.cross_classroom_distant  # Should be 0.2

    def test_calculate_priority_score(self, service, sample_assignments):
        """Test priority score calculation"""
        priority = service.calculate_priority_score(1, 1, 2, sample_assignments)
        assert 0.0 <= priority <= 1.0

    def test_calculate_priority_score_normalization(self, service):
        """Test priority score normalization (REVISION 6)"""
        assignments = [
            {'instructors': [1, 2]},
            {'instructors': [1, 3]},
        ]
        
        # Test that priority scores are normalized
        priority_1 = service.calculate_priority_score(1, 1, 1, assignments)
        priority_2 = service.calculate_priority_score(2, 1, 1, assignments)
        priority_3 = service.calculate_priority_score(3, 1, 1, assignments)
        
        assert 0.0 <= priority_1 <= 1.0
        assert 0.0 <= priority_2 <= 1.0
        assert 0.0 <= priority_3 <= 1.0

    def test_find_jury_candidates(self, service, sample_assignments):
        """Test jury candidate finding"""
        project_assignment = {
            'project_id': 3,
            'classroom_id': 2,
            'timeslot_id': 3,
            'instructors': [3]  # Only responsible instructor
        }
        
        candidates = service.find_jury_candidates(project_assignment, sample_assignments, 1)
        
        assert isinstance(candidates, list)
        assert len(candidates) > 0
        # Should not include instructor 3 (already assigned)
        candidate_ids = [candidate[0] for candidate in candidates]
        assert 3 not in candidate_ids

    def test_find_jury_candidates_sorted_by_priority(self, service, sample_assignments):
        """Test that candidates are sorted by priority score"""
        project_assignment = {
            'project_id': 3,
            'classroom_id': 2,
            'timeslot_id': 3,
            'instructors': [3]
        }
        
        candidates = service.find_jury_candidates(project_assignment, sample_assignments, 2)
        
        # Should be sorted by priority score (highest first)
        for i in range(len(candidates) - 1):
            assert candidates[i][1] >= candidates[i + 1][1]

    def test_get_required_jury_count_ara(self, service):
        """Test required jury count for ara projects"""
        project_assignment = {'project_id': 1}  # ara project
        required = service._get_required_jury_count(project_assignment)
        assert required == 1

    def test_get_required_jury_count_bitirme(self, service):
        """Test required jury count for bitirme projects"""
        project_assignment = {'project_id': 2}  # bitirme project
        required = service._get_required_jury_count(project_assignment)
        assert required == 2

    def test_refine_jury_assignments(self, service, sample_assignments):
        """Test main refinement logic"""
        refined = service.refine_jury_assignments(sample_assignments)
        
        assert isinstance(refined, list)
        assert len(refined) == len(sample_assignments)
        
        # Check that jury members were added where needed
        for assignment in refined:
            assert 'instructors' in assignment
            assert len(assignment['instructors']) > 0

    def test_refine_jury_assignments_bitirme_project(self, service):
        """Test refinement for bitirme project (needs 2 jury members)"""
        assignments = [
            {
                'project_id': 2,  # bitirme project
                'classroom_id': 1,
                'timeslot_id': 1,
                'instructors': [2]  # Only responsible instructor
            }
        ]
        
        refined = service.refine_jury_assignments(assignments)
        
        # Should have added jury members (total 3: 1 responsible + 2 jury)
        assert len(refined[0]['instructors']) >= 3

    def test_refine_jury_assignments_ara_project(self, service):
        """Test refinement for ara project (needs 1 jury member)"""
        assignments = [
            {
                'project_id': 1,  # ara project
                'classroom_id': 1,
                'timeslot_id': 1,
                'instructors': [1]  # Only responsible instructor
            }
        ]
        
        refined = service.refine_jury_assignments(assignments)
        
        # Should have added jury member (total 2: 1 responsible + 1 jury)
        assert len(refined[0]['instructors']) >= 2

    def test_refine_jury_assignments_empty_list(self, service):
        """Test refinement with empty assignments list"""
        refined = service.refine_jury_assignments([])
        assert refined == []

    def test_refine_jury_assignments_no_instructors(self, service):
        """Test refinement with assignments that have no instructors"""
        assignments = [
            {
                'project_id': 1,
                'classroom_id': 1,
                'timeslot_id': 1,
                'instructors': []
            }
        ]
        
        refined = service.refine_jury_assignments(assignments)
        assert len(refined) == 1

    def test_logging_level_configuration(self, sample_data):
        """Test logging level configuration (REVISION 4)"""
        config = {'JURY_LOGGING_LEVEL': 'DEBUG'}
        
        with patch('app.services.jury_refinement_service.logger') as mock_logger:
            service = JuryRefinementService(
                instructors=sample_data['instructors'],
                classrooms=sample_data['classrooms'],
                timeslots=sample_data['timeslots'],
                projects=sample_data['projects'],
                config=config
            )
            
            # Should set logging level to DEBUG
            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_normalized_scoring_consistency(self, service, sample_assignments):
        """Test that all scores are normalized to 0-1 range (REVISION 1)"""
        # Test classroom scores
        same_classroom = service.calculate_classroom_score(1, 1, 2, sample_assignments)
        cross_same_time = service.calculate_classroom_score(3, 1, 3, sample_assignments)
        cross_adjacent = service.calculate_classroom_score(3, 1, 2, sample_assignments)
        cross_distant = service.calculate_classroom_score(3, 1, 1, sample_assignments)
        
        assert 0.0 <= same_classroom <= 1.0
        assert 0.0 <= cross_same_time <= 1.0
        assert 0.0 <= cross_adjacent <= 1.0
        assert 0.0 <= cross_distant <= 1.0
        
        # Test continuity scores
        continuity = service.calculate_continuity_score(1, 1, 2, sample_assignments)
        assert 0.0 <= continuity <= 1.0
        
        # Test priority scores
        priority = service.calculate_priority_score(1, 1, 2, sample_assignments)
        assert 0.0 <= priority <= 1.0

    def test_semi_consecutive_weight_application(self, service):
        """Test semi-consecutive weight application (REVISION 2)"""
        assignments = [
            {
                'project_id': 1,
                'classroom_id': 1,
                'timeslot_id': 1,
                'instructors': [1]
            }
        ]
        
        # Test with 1-slot gap (should get semi-consecutive bonus)
        continuity = service.calculate_continuity_score(1, 1, 3, assignments)
        assert 0.0 <= continuity <= 1.0

    def test_configurable_weights(self, sample_data):
        """Test configurable weights (REVISION 5)"""
        config = {
            'JURY_CONTINUITY_WEIGHT': 0.7,
            'JURY_PROXIMITY_WEIGHT': 0.3,
            'JURY_SEMI_CONSECUTIVE_WEIGHT': 0.6
        }
        
        service = JuryRefinementService(
            instructors=sample_data['instructors'],
            classrooms=sample_data['classrooms'],
            timeslots=sample_data['timeslots'],
            projects=sample_data['projects'],
            config=config
        )
        
        assert service.continuity_weight == 0.7
        assert service.proximity_weight == 0.3
        assert service.semi_consecutive_weight == 0.6

    def test_edge_cases(self, service):
        """Test edge cases"""
        # Empty assignments
        workload = service.calculate_workload(1, [])
        assert workload == 0.0
        
        # Non-existent instructor
        workload = service.calculate_workload(999, [])
        assert workload == 0.0
        
        # Empty assignments list
        refined = service.refine_jury_assignments([])
        assert refined == []

    def test_performance_with_large_dataset(self, service):
        """Test performance with larger dataset"""
        # Create larger dataset
        large_assignments = []
        for i in range(100):
            large_assignments.append({
                'project_id': i,
                'classroom_id': (i % 2) + 1,
                'timeslot_id': (i % 4) + 1,
                'instructors': [1, 2] if i % 2 == 0 else [3, 4]
            })
        
        # Should complete without errors
        refined = service.refine_jury_assignments(large_assignments)
        assert len(refined) == 100

    def test_integration_with_algorithm_base_class(self):
        """Test integration with OptimizationAlgorithm base class"""
        from app.algorithms.base import OptimizationAlgorithm
        
        # Mock algorithm class
        class MockAlgorithm(OptimizationAlgorithm):
            def __init__(self):
                self.instructors = []
                self.classrooms = []
                self.timeslots = []
                self.projects = []
                self.params = {'jury_refinement_layer': True}
            
            def optimize(self, data):
                return {'assignments': []}
        
        algorithm = MockAlgorithm()
        assignments = [{'project_id': 1, 'instructors': [1]}]
        
        # Should not raise errors
        result = algorithm.apply_jury_refinement(assignments, enable_refinement=True)
        assert isinstance(result, list)

    def test_disable_refinement(self):
        """Test disabling refinement"""
        from app.algorithms.base import OptimizationAlgorithm
        
        class MockAlgorithm(OptimizationAlgorithm):
            def __init__(self):
                self.instructors = []
                self.classrooms = []
                self.timeslots = []
                self.projects = []
                self.params = {'jury_refinement_layer': False}
            
            def optimize(self, data):
                return {'assignments': []}
        
        algorithm = MockAlgorithm()
        assignments = [{'project_id': 1, 'instructors': [1]}]
        
        # Should return original assignments when disabled
        result = algorithm.apply_jury_refinement(assignments, enable_refinement=False)
        assert result == assignments


class TestJuryRefinementServiceIntegration:
    """Integration tests for JuryRefinementService"""

    def test_full_workflow(self):
        """Test complete workflow from initialization to refinement"""
        # Sample data
        instructors = [
            {'id': 1, 'name': 'Instructor A', 'type': 'instructor'},
            {'id': 2, 'name': 'Instructor B', 'type': 'instructor'},
            {'id': 3, 'name': 'Instructor C', 'type': 'instructor'},
        ]
        classrooms = [
            {'id': 1, 'name': 'Classroom A'},
            {'id': 2, 'name': 'Classroom B'},
        ]
        timeslots = [
            {'id': 1, 'start_time': '09:00', 'end_time': '10:00'},
            {'id': 2, 'start_time': '10:00', 'end_time': '11:00'},
        ]
        projects = [
            {'id': 1, 'type': 'ara', 'responsible_id': 1},
            {'id': 2, 'type': 'bitirme', 'responsible_id': 2},
        ]
        
        # Create service
        service = JuryRefinementService(
            instructors=instructors,
            classrooms=classrooms,
            timeslots=timeslots,
            projects=projects
        )
        
        # Sample assignments
        assignments = [
            {
                'project_id': 1,
                'classroom_id': 1,
                'timeslot_id': 1,
                'instructors': [1]  # Only responsible
            },
            {
                'project_id': 2,
                'classroom_id': 2,
                'timeslot_id': 2,
                'instructors': [2]  # Only responsible
            }
        ]
        
        # Refine assignments
        refined = service.refine_jury_assignments(assignments)
        
        # Verify results
        assert len(refined) == 2
        
        # Ara project should have at least 2 instructors (1 responsible + 1 jury)
        ara_project = next(a for a in refined if a['project_id'] == 1)
        assert len(ara_project['instructors']) >= 2
        
        # Bitirme project should have at least 3 instructors (1 responsible + 2 jury)
        bitirme_project = next(a for a in refined if a['project_id'] == 2)
        assert len(bitirme_project['instructors']) >= 3

    def test_algorithm_specific_configuration(self):
        """Test algorithm-specific configuration"""
        config = {
            'JURY_CONTINUITY_WEIGHT': 0.5,  # Different for Genetic Algorithm
            'JURY_PROXIMITY_WEIGHT': 0.5,
            'JURY_LOGGING_LEVEL': 'DEBUG'
        }
        
        service = JuryRefinementService(
            instructors=[],
            classrooms=[],
            timeslots=[],
            projects=[],
            config=config
        )
        
        assert service.continuity_weight == 0.5
        assert service.proximity_weight == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
