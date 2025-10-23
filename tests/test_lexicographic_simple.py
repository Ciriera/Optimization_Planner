"""
Lexicographic algoritması için basit test dosyası.
"""
import pytest
from app.algorithms.lexicographic import LexicographicAlgorithm

def test_lexicographic_initialization():
    """Test lexicographic algorithm initialization"""
    algorithm = LexicographicAlgorithm()
    assert algorithm is not None
    assert hasattr(algorithm, 'optimize')
    assert hasattr(algorithm, 'evaluate_fitness')
    
def test_lexicographic_optimization():
    """Test lexicographic optimization with minimal data"""
    # Test verisi
    data = {
        'instructors': [
            {'id': 1, 'name': 'Prof. Dr. Ahmet Yılmaz', 'availability': [True, True, True]},
            {'id': 2, 'name': 'Doç. Dr. Mehmet Kaya', 'availability': [True, True, True]},
            {'id': 3, 'name': 'Dr. Ayşe Demir', 'availability': [True, True, True]},
            {'id': 4, 'name': 'Arş. Gör. Ali Veli', 'availability': [True, True, True]}
        ],
        'projects': [
            {'id': 1, 'supervisor_id': 1},
            {'id': 2, 'supervisor_id': 1},
            {'id': 3, 'supervisor_id': 2},
            {'id': 4, 'supervisor_id': 3}
        ],
        'timeslots': [
            {'id': 1, 'start_time': '09:00', 'end_time': '09:30'},
            {'id': 2, 'start_time': '09:30', 'end_time': '10:00'},
            {'id': 3, 'start_time': '10:00', 'end_time': '10:30'}
        ]
    }
    
    # Algoritma oluştur ve optimize et
    algorithm = LexicographicAlgorithm()
    result = algorithm.optimize(data)
    
    # Sonuçları kontrol et
    assert result is not None
    assert 'assignments' in result
    assert 'metrics' in result
    assert len(result['assignments']) > 0
    
def test_ai_metrics():
    """Test AI metrics calculation"""
    # Test verisi
    data = {
        'instructors': [
            {'id': 1, 'name': 'Prof. Dr. Ahmet Yılmaz', 'availability': [True, True, True]},
            {'id': 2, 'name': 'Doç. Dr. Mehmet Kaya', 'availability': [True, True, True]}
        ],
        'projects': [
            {'id': 1, 'supervisor_id': 1},
            {'id': 2, 'supervisor_id': 1},
            {'id': 3, 'supervisor_id': 2}
        ],
        'timeslots': [
            {'id': 1, 'start_time': '09:00', 'end_time': '09:30'},
            {'id': 2, 'start_time': '09:30', 'end_time': '10:00'}
        ]
    }
    
    # Algoritma oluştur ve optimize et
    algorithm = LexicographicAlgorithm()
    algorithm.optimize(data)
    metrics = algorithm.get_ai_enhanced_metrics()
    
    # Metrikleri kontrol et
    assert 'workload_distribution' in metrics
    assert 'pairing_efficiency' in metrics
    assert 'schedule_optimization' in metrics
    assert isinstance(metrics['workload_distribution'], float)
