import pytest
from app.algorithms.lexicographic import LexicographicOptimizer, Instructor, Project, TimeSlot

@pytest.fixture
def sample_data():
    instructors = [
        Instructor(id=1, name="Prof. A", project_count=5, availability=[True] * 10),
        Instructor(id=2, name="Prof. B", project_count=4, availability=[True] * 10),
        Instructor(id=3, name="Prof. C", project_count=3, availability=[True] * 10),
        Instructor(id=4, name="Prof. D", project_count=2, availability=[True] * 10),
        Instructor(id=5, name="Prof. E", project_count=1, availability=[True] * 10),
    ]
    
    projects = [
        Project(id=1, supervisor_id=1),
        Project(id=2, supervisor_id=1),
        Project(id=3, supervisor_id=2),
        Project(id=4, supervisor_id=3),
    ]
    
    time_slots = [
        TimeSlot(id=1, start_time="09:00", end_time="10:00"),
        TimeSlot(id=2, start_time="10:00", end_time="11:00"),
        TimeSlot(id=3, start_time="11:00", end_time="12:00"),
    ]
    
    return instructors, projects, time_slots

def test_sort_instructors(sample_data):
    instructors, projects, time_slots = sample_data
    optimizer = LexicographicOptimizer(instructors, projects, time_slots)
    sorted_instructors = optimizer.sort_instructors_by_project_count()
    
    assert len(sorted_instructors) == 5
    assert sorted_instructors[0].project_count == 5
    assert sorted_instructors[-1].project_count == 1

def test_split_instructors(sample_data):
    instructors, projects, time_slots = sample_data
    optimizer = LexicographicOptimizer(instructors, projects, time_slots)
    sorted_instructors = optimizer.sort_instructors_by_project_count()
    upper_group, lower_group = optimizer.split_instructors_into_groups(sorted_instructors)
    
    assert len(upper_group) == 2  # n
    assert len(lower_group) == 3  # n+1 (tek sayı durumu)
    assert upper_group[0].project_count == 5
    assert lower_group[-1].project_count == 1

def test_create_pairs(sample_data):
    instructors, projects, time_slots = sample_data
    optimizer = LexicographicOptimizer(instructors, projects, time_slots)
    sorted_instructors = optimizer.sort_instructors_by_project_count()
    upper_group, lower_group = optimizer.split_instructors_into_groups(sorted_instructors)
    pairs = optimizer.create_instructor_pairs(upper_group, lower_group)
    
    assert len(pairs) == 2
    assert pairs[0][0].project_count > pairs[0][1].project_count

def test_consecutive_assignments(sample_data):
    instructors, projects, time_slots = sample_data
    optimizer = LexicographicOptimizer(instructors, projects, time_slots)
    pair = (instructors[0], instructors[1])  # Prof. A ve Prof. B
    assignments = optimizer.assign_consecutive_slots(pair)
    
    assert len(assignments) == 2
    assert assignments[0]['supervisor'].id == instructors[0].id
    assert assignments[0]['jury'].id == instructors[1].id
    assert assignments[1]['supervisor'].id == instructors[1].id
    assert assignments[1]['jury'].id == instructors[0].id

def test_full_optimization(sample_data):
    instructors, projects, time_slots = sample_data
    optimizer = LexicographicOptimizer(instructors, projects, time_slots)
    result = optimizer.optimize()
    
    assert 'assignments' in result
    assert 'instructor_pairs' in result
    assert 'metrics' in result
    assert len(result['assignments']) > 0
    assert len(result['instructor_pairs']) > 0

def test_ai_metrics(sample_data):
    instructors, projects, time_slots = sample_data
    optimizer = LexicographicOptimizer(instructors, projects, time_slots)
    optimizer.optimize()  # Önce optimize etmeliyiz
    metrics = optimizer.get_ai_enhanced_metrics()
    
    assert 'workload_distribution' in metrics
    assert 'pairing_efficiency' in metrics
    assert 'schedule_optimization' in metrics
    assert isinstance(metrics['workload_distribution'], float)
    assert 0 <= metrics['pairing_efficiency'] <= 1
    assert 0 <= metrics['schedule_optimization'] <= 1
