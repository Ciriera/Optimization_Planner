"""
Lexicographic algoritmasının gereksinimlerini test eden dosya.
"""
import pytest
from app.algorithms.lexicographic import LexicographicAlgorithm, Instructor

def test_sort_instructors_by_project_count():
    """Test instructorların proje sayısına göre sıralanmasını"""
    # Test verileri
    instructors = [
        Instructor(id=1, name="Prof. A", project_count=5, availability=[True, True]),
        Instructor(id=2, name="Prof. B", project_count=3, availability=[True, True]),
        Instructor(id=3, name="Prof. C", project_count=7, availability=[True, True]),
        Instructor(id=4, name="Prof. D", project_count=2, availability=[True, True]),
        Instructor(id=5, name="Prof. E", project_count=4, availability=[True, True]),
    ]
    
    # Algoritma oluştur
    algorithm = LexicographicAlgorithm()
    algorithm.instructors = instructors
    
    # Sıralama yap
    sorted_instructors = algorithm.sort_instructors_by_project_count()
    
    # Kontroller
    assert len(sorted_instructors) == 5
    assert sorted_instructors[0].id == 3  # En çok projesi olan (7)
    assert sorted_instructors[1].id == 1  # İkinci en çok projesi olan (5)
    assert sorted_instructors[-1].id == 4  # En az projesi olan (2)
    
    # Proje sayılarının azalan sırada olduğunu kontrol et
    project_counts = [inst.project_count for inst in sorted_instructors]
    assert project_counts == sorted(project_counts, reverse=True)

def test_split_instructors_even_count():
    """Test instructorların çift sayıda olduğu durumda grupların doğru oluşturulmasını"""
    # Test verileri (çift sayıda instructor)
    instructors = [
        Instructor(id=1, name="Prof. A", project_count=6, availability=[True, True]),
        Instructor(id=2, name="Prof. B", project_count=5, availability=[True, True]),
        Instructor(id=3, name="Prof. C", project_count=4, availability=[True, True]),
        Instructor(id=4, name="Prof. D", project_count=3, availability=[True, True]),
    ]
    
    # Algoritma oluştur
    algorithm = LexicographicAlgorithm()
    
    # Grupları oluştur
    upper_group, lower_group = algorithm.split_instructors_into_groups(instructors)
    
    # Kontroller
    assert len(upper_group) == 2  # Üst grupta 2 instructor
    assert len(lower_group) == 2  # Alt grupta 2 instructor
    assert upper_group[0].id == 1  # Üst gruptaki ilk instructor
    assert upper_group[1].id == 2  # Üst gruptaki ikinci instructor
    assert lower_group[0].id == 3  # Alt gruptaki ilk instructor
    assert lower_group[1].id == 4  # Alt gruptaki ikinci instructor

def test_split_instructors_odd_count():
    """Test instructorların tek sayıda olduğu durumda grupların doğru oluşturulmasını"""
    # Test verileri (tek sayıda instructor)
    instructors = [
        Instructor(id=1, name="Prof. A", project_count=7, availability=[True, True]),
        Instructor(id=2, name="Prof. B", project_count=5, availability=[True, True]),
        Instructor(id=3, name="Prof. C", project_count=3, availability=[True, True]),
        Instructor(id=4, name="Prof. D", project_count=2, availability=[True, True]),
        Instructor(id=5, name="Prof. E", project_count=1, availability=[True, True]),
    ]
    
    # Algoritma oluştur
    algorithm = LexicographicAlgorithm()
    
    # Grupları oluştur
    upper_group, lower_group = algorithm.split_instructors_into_groups(instructors)
    
    # Kontroller
    assert len(upper_group) == 2  # Üst grupta 2 instructor
    assert len(lower_group) == 3  # Alt grupta 3 instructor (bir fazla)
    assert upper_group[0].id == 1  # Üst gruptaki ilk instructor
    assert upper_group[1].id == 2  # Üst gruptaki ikinci instructor
    assert lower_group[0].id == 3  # Alt gruptaki ilk instructor
    assert lower_group[-1].id == 5  # Alt gruptaki son instructor

def test_create_instructor_pairs():
    """Test üst ve alt gruptan instructorların doğru eşleştirilmesini"""
    # Test verileri
    upper_group = [
        Instructor(id=1, name="Prof. A", project_count=7, availability=[True, True]),
        Instructor(id=2, name="Prof. B", project_count=5, availability=[True, True]),
    ]
    
    lower_group = [
        Instructor(id=3, name="Prof. C", project_count=3, availability=[True, True]),
        Instructor(id=4, name="Prof. D", project_count=2, availability=[True, True]),
        Instructor(id=5, name="Prof. E", project_count=1, availability=[True, True]),
    ]
    
    # Algoritma oluştur
    algorithm = LexicographicAlgorithm()
    
    # Eşleştirmeleri yap
    pairs = algorithm.create_instructor_pairs(upper_group, lower_group)
    
    # Kontroller
    assert len(pairs) == 2  # 2 eşleştirme (üst gruptaki instructor sayısı kadar)
    assert pairs[0][0].id == 1 and pairs[0][1].id == 3  # İlk eşleştirme
    assert pairs[1][0].id == 2 and pairs[1][1].id == 4  # İkinci eşleştirme
    
    # Eşleştirmelerde üst gruptaki instructor'ın proje sayısının alt gruptakinden fazla olduğunu kontrol et
    for upper, lower in pairs:
        assert upper.project_count > lower.project_count

def test_assign_consecutive_slots():
    """Test ardışık zaman dilimlerinde rol değişiminin doğru yapılmasını"""
    # Test verileri
    from app.algorithms.lexicographic import TimeSlot
    
    instructor1 = Instructor(id=1, name="Prof. A", project_count=7, availability=[True, True])
    instructor2 = Instructor(id=3, name="Prof. C", project_count=3, availability=[True, True])
    
    # Algoritma oluştur
    algorithm = LexicographicAlgorithm()
    algorithm.time_slots = [
        TimeSlot(id=1, start_time="09:00", end_time="09:30"),
        TimeSlot(id=2, start_time="09:30", end_time="10:00"),
    ]
    
    # Ardışık atama yap
    assignments = algorithm.assign_consecutive_slots((instructor1, instructor2))
    
    # Kontroller
    assert len(assignments) == 2  # İki zaman dilimi için iki atama
    
    # İlk zaman diliminde instructor1 supervisor, instructor2 jury
    assert assignments[0]['supervisor_id'] == instructor1.id
    assert assignments[0]['jury_id'] == instructor2.id
    assert assignments[0]['time_slot_id'] == 1
    
    # İkinci zaman diliminde instructor2 supervisor, instructor1 jury
    assert assignments[1]['supervisor_id'] == instructor2.id
    assert assignments[1]['jury_id'] == instructor1.id
    assert assignments[1]['time_slot_id'] == 2

def test_end_to_end_optimization():
    """Test algoritmanın uçtan uca çalışmasını"""
    # Test verileri
    from app.algorithms.lexicographic import TimeSlot, Project
    
    data = {
        "instructors": [
            {"id": 1, "name": "Prof. A", "project_count": 5, "availability": [True, True]},
            {"id": 2, "name": "Prof. B", "project_count": 4, "availability": [True, True]},
            {"id": 3, "name": "Prof. C", "project_count": 3, "availability": [True, True]},
            {"id": 4, "name": "Prof. D", "project_count": 2, "availability": [True, True]},
        ],
        "projects": [
            {"id": 1, "supervisor_id": 1},
            {"id": 2, "supervisor_id": 1},
            {"id": 3, "supervisor_id": 2},
            {"id": 4, "supervisor_id": 3},
        ],
        "timeslots": [
            {"id": 1, "start_time": "09:00", "end_time": "09:30"},
            {"id": 2, "start_time": "09:30", "end_time": "10:00"},
        ],
    }
    
    # Algoritma oluştur
    algorithm = LexicographicAlgorithm()
    
    # Optimizasyonu çalıştır
    result = algorithm.optimize(data)
    
    # Kontroller
    assert 'assignments' in result
    assert 'instructor_pairs' in result
    assert 'metrics' in result
    
    assignments = result['assignments']
    assert len(assignments) > 0
    
    # Ardışık zaman dilimlerinde rol değişimini kontrol et
    if len(assignments) >= 2:
        first = assignments[0]
        second = assignments[1]
        assert first['supervisor_id'] == second['jury_id']
        assert first['jury_id'] == second['supervisor_id']
    
    # AI metriklerini kontrol et
    metrics = result['metrics'].get('ai_metrics', {})
    assert 'workload_distribution' in metrics
    assert 'pairing_efficiency' in metrics
    assert 'schedule_optimization' in metrics
