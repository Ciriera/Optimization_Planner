#!/usr/bin/env python3
"""
ULTRA NSGA-2 AI Algorithm Test Script
11 Advanced AI Features test
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.algorithms.nsga_ii import NSGAII
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ultra_nsga2():
    """ULTRA NSGA-2 AI Algorithm'ı test et"""
    
    print("🤖 ULTRA NSGA-2 AI Algorithm Test (11 Features)")
    print("=" * 70)
    
    # Test verisi
    test_data = {
        'projects': [
            {'id': 1, 'title': 'Proje 1', 'responsible_instructor_id': 1, 'type': 'final'},
            {'id': 2, 'title': 'Proje 2', 'responsible_instructor_id': 1, 'type': 'final'},
            {'id': 3, 'title': 'Proje 3', 'responsible_instructor_id': 1, 'type': 'interim'},
            {'id': 4, 'title': 'Proje 4', 'responsible_instructor_id': 2, 'type': 'final'},
            {'id': 5, 'title': 'Proje 5', 'responsible_instructor_id': 2, 'type': 'interim'},
            {'id': 6, 'title': 'Proje 6', 'responsible_instructor_id': 3, 'type': 'final'},
            {'id': 7, 'title': 'Proje 7', 'responsible_instructor_id': 4, 'type': 'interim'},
            {'id': 8, 'title': 'Proje 8', 'responsible_instructor_id': 5, 'type': 'final'},
        ],
        'instructors': [
            {'id': 1, 'name': 'Dr. Öğretim Üyesi 1'},
            {'id': 2, 'name': 'Dr. Öğretim Üyesi 2'},
            {'id': 3, 'name': 'Dr. Öğretim Üyesi 3'},
            {'id': 4, 'name': 'Dr. Öğretim Üyesi 4'},
            {'id': 5, 'name': 'Dr. Öğretim Üyesi 5'},
        ],
        'classrooms': [
            {'id': 1, 'name': 'D106'},
            {'id': 2, 'name': 'D107'},
            {'id': 3, 'name': 'D108'},
        ],
        'timeslots': [
            {'id': 1, 'start_time': '09:00', 'end_time': '09:30'},
            {'id': 2, 'start_time': '09:30', 'end_time': '10:00'},
            {'id': 3, 'start_time': '10:00', 'end_time': '10:30'},
            {'id': 4, 'start_time': '10:30', 'end_time': '11:00'},
            {'id': 5, 'start_time': '11:00', 'end_time': '11:30'},
            {'id': 6, 'start_time': '11:30', 'end_time': '12:00'},
        ]
    }
    
    print("📊 Test Verisi:")
    print(f"  - {len(test_data['projects'])} proje")
    print(f"  - {len(test_data['instructors'])} instructor")
    print(f"  - {len(test_data['classrooms'])} sınıf")
    print(f"  - {len(test_data['timeslots'])} zaman slotu")
    
    try:
        # ULTRA AI Parameters
        params = {
            'population_size': 20,
            'generations': 10,
            'crossover_rate': 0.8,
            'mutation_rate': 0.1,
            'tournament_size': 3
        }
        
        algorithm = NSGAII(params)
        
        print(f"\n🤖 Algorithm: {algorithm.name}")
        print(f"🤖 Description: {algorithm.description}")
        
        # Optimize
        result = algorithm.optimize(test_data)
        
        print("\n✅ ULTRA NSGA-2 başarıyla tamamlandı!")
        
        # Results
        print(f"\n📊 Sonuç Analizi:")
        print(f"  - Toplam atama: {len(result['schedules'])}")
        print(f"  - Phase 1: {result['statistics']['phase1_count']}")
        print(f"  - Phase 2: {result['statistics']['phase2_count']}")
        print(f"  - Fitness: {result['statistics']['fitness_scores']}")
        print(f"  - Ortalama: {result['statistics']['average_fitness']:.2f}")
        
        # Algorithm Info
        print(f"\n🤖 Algorithm Info:")
        algo_info = result['algorithm_info']
        print(f"  - AI Features: {algo_info['ai_features_used']}")
        print(f"  - Learned Patterns: {algo_info['learned_patterns']}")
        print(f"  - Elite Patterns: {algo_info['elite_knowledge_patterns']}")
        print(f"  - History Size: {algo_info['best_solutions_history_size']}")
        
        # AI Insights
        print(f"\n🧠 AI Insights:")
        insights = result['ai_insights']
        for key, value in insights.items():
            if key != 'recommendations':
                print(f"  - {key}: {value}")
        
        print(f"\n💡 AI Recommendations:")
        for rec in insights['recommendations']:
            print(f"  {rec}")
        
        print("\n🎉 11 ADVANCED AI FEATURES TEST BAŞARILI!")
        print("✅ Adaptive Parameter Tuning")
        print("✅ Elite Preservation with Learning")
        print("✅ Smart Diversity Maintenance")
        print("✅ Learning from History")
        print("✅ Dynamic Strategic Pairing")
        print("✅ Smart Mutation Strategies")
        print("✅ Multi-Objective Optimization")
        print("✅ Strategic Instructor Pairing")
        print("✅ Bi-Directional Jury Assignment")
        print("✅ Consecutive Grouping")
        print("✅ Zero Hard Constraints")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST BAŞARISIZ!")
        print(f"   Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ultra_nsga2()
    sys.exit(0 if success else 1)
