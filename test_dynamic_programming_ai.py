#!/usr/bin/env python3
"""
Test script for Dynamic Programming Algorithm with AI-based Strategic Pairing.
Tests the new AI-powered instructor pairing and consecutive grouping features.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from algorithms.dynamic_programming import DynamicProgramming

def test_dynamic_programming_ai():
    """Test Dynamic Programming Algorithm with AI-based Strategic Pairing."""
    
    print("=" * 80)
    print("DYNAMIC PROGRAMMING ALGORITHM - AI-BASED STRATEGIC PAIRING TEST")
    print("=" * 80)
    print(f"Test baslangic zamani: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Sample test data with instructor project loads (more realistic)
    test_data = {
        "projects": [
            # Instructor 1: 5 proje (en fazla)
            {"id": 1, "instructor_id": 1, "project_type": "Bitirme", "title": "Proje 1"},
            {"id": 2, "instructor_id": 1, "project_type": "Bitirme", "title": "Proje 2"},
            {"id": 3, "instructor_id": 1, "project_type": "Ara", "title": "Proje 3"},
            {"id": 4, "instructor_id": 1, "project_type": "Ara", "title": "Proje 4"},
            {"id": 5, "instructor_id": 1, "project_type": "Bitirme", "title": "Proje 5"},
            
            # Instructor 2: 3 proje
            {"id": 6, "instructor_id": 2, "project_type": "Bitirme", "title": "Proje 6"},
            {"id": 7, "instructor_id": 2, "project_type": "Ara", "title": "Proje 7"},
            {"id": 8, "instructor_id": 2, "project_type": "Bitirme", "title": "Proje 8"},
            
            # Instructor 3: 2 proje
            {"id": 9, "instructor_id": 3, "project_type": "Ara", "title": "Proje 9"},
            {"id": 10, "instructor_id": 3, "project_type": "Bitirme", "title": "Proje 10"},
            
            # Instructor 4: 1 proje (en az)
            {"id": 11, "instructor_id": 4, "project_type": "Ara", "title": "Proje 11"},
        ],
        "instructors": [
            {"id": 1, "name": "Dr. Ogretim Uyesi 1", "email": "instructor1@university.edu"},
            {"id": 2, "name": "Dr. Ogretim Uyesi 2", "email": "instructor2@university.edu"},
            {"id": 3, "name": "Dr. Ogretim Uyesi 3", "email": "instructor3@university.edu"},
            {"id": 4, "name": "Dr. Ogretim Uyesi 4", "email": "instructor4@university.edu"},
        ],
        "classrooms": [
            {"id": 1, "name": "D105", "capacity": 30},
            {"id": 2, "name": "D106", "capacity": 30},
            {"id": 3, "name": "D107", "capacity": 30},
        ],
        "timeslots": [
            {"id": 1, "start_time": "09:00", "end_time": "09:30"},
            {"id": 2, "start_time": "09:30", "end_time": "10:00"},
            {"id": 3, "start_time": "10:00", "end_time": "10:30"},
            {"id": 4, "start_time": "10:30", "end_time": "11:00"},
            {"id": 5, "start_time": "11:00", "end_time": "11:30"},
            {"id": 6, "start_time": "11:30", "end_time": "12:00"},
            {"id": 7, "start_time": "13:00", "end_time": "13:30"},
            {"id": 8, "start_time": "13:30", "end_time": "14:00"},
            {"id": 9, "start_time": "14:00", "end_time": "14:30"},
            {"id": 10, "start_time": "14:30", "end_time": "15:00"},
        ]
    }
    
    print("Test Verileri:")
    print(f"   Projeler: {len(test_data['projects'])}")
    print(f"   Instructors: {len(test_data['instructors'])}")
    print(f"   Siniflar: {len(test_data['classrooms'])}")
    print(f"   Zaman Slotlari: {len(test_data['timeslots'])}")
    print()
    
    # Instructor proje yukleri
    print("Instructor Proje Yukleri:")
    instructor_loads = {}
    for instructor in test_data['instructors']:
        load = sum(1 for p in test_data['projects'] if p['instructor_id'] == instructor['id'])
        instructor_loads[instructor['id']] = load
        print(f"   {instructor['name']}: {load} proje")
    print()
    
    try:
        # Initialize algorithm
        algorithm = DynamicProgramming()
        
        # Run optimization
        start_time = time.time()
        result = algorithm.optimize(test_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print("=" * 80)
        print("OPTIMIZATION SONUCLARI")
        print("=" * 80)
        print(f"Calisma suresi: {execution_time:.2f} saniye")
        print()
        
        # Analyze results
        assignments = result.get("assignments", [])
        print(f"Toplam atama: {len(assignments)}")
        
        # Check strategic pairing
        algorithm_info = result.get("algorithm_info", {})
        print(f"Stratejik eslesme sayisi: {algorithm_info.get('strategic_pairs_count', 0)}")
        print(f"Phase 1 atamalari: {algorithm_info.get('phase1_assignments', 0)}")
        print(f"Phase 2 atamalari: {algorithm_info.get('phase2_assignments', 0)}")
        print()
        
        # Show AI insights
        ai_insights = result.get("ai_insights", {})
        print("AI Insights:")
        print(f"   Strategic Pairing: {ai_insights.get('strategic_pairing_summary', 'N/A')}")
        print(f"   Load Balancing: {ai_insights.get('load_balancing_achieved', 'N/A')}")
        print(f"   Bi-directional Jury: {ai_insights.get('bi_directional_jury', 'N/A')}")
        print(f"   Consecutive Grouping: {ai_insights.get('consecutive_grouping', 'N/A')}")
        print(f"   AI Optimization Level: {ai_insights.get('ai_optimization_level', 'N/A')}")
        print()
        
        # Show assignments by phase
        print("Zaman Slotuna Gore Atamalar:")
        sorted_timeslots = sorted(test_data['timeslots'], key=lambda x: x['start_time'])
        
        for timeslot in sorted_timeslots:
            slot_assignments = [a for a in assignments 
                              if a.get('timeslot_id') == timeslot['id']]
            
            if slot_assignments:
                print(f"   {timeslot['start_time']}-{timeslot['end_time']}: {len(slot_assignments)} proje")
                for assignment in slot_assignments:
                    project_id = assignment.get('project_id')
                    instructor_ids = assignment.get('instructors', [])
                    jury_members = assignment.get('jury_members', [])
                    classroom_id = assignment.get('classroom_id')
                    phase = assignment.get('phase', 'N/A')
                    ai_score = assignment.get('ai_score', 0)
                    
                    classroom_name = next((c['name'] for c in test_data['classrooms'] 
                                         if c['id'] == classroom_id), 'Unknown')
                    
                    instructor_names = [next((i['name'] for i in test_data['instructors'] 
                                            if i['id'] == inst_id), 'Unknown') 
                                       for inst_id in instructor_ids]
                    jury_names = [next((i['name'] for i in test_data['instructors'] 
                                      if i['id'] == jury_id), 'Unknown') 
                                 for jury_id in jury_members]
                    
                    print(f"      - Proje {project_id} (Phase {phase}): {', '.join(instructor_names)} -> {', '.join(jury_names)} - {classroom_name} (AI Score: {ai_score:.1f})")
            else:
                print(f"   {timeslot['start_time']}-{timeslot['end_time']}: Bos")
        
        print()
        
        # Show statistics
        stats = result.get("statistics", {})
        print("Istatistikler:")
        print(f"   Toplam schedule: {stats.get('total_schedules', 0)}")
        print(f"   Phase 1 sayisi: {stats.get('phase1_count', 0)}")
        print(f"   Phase 2 sayisi: {stats.get('phase2_count', 0)}")
        print(f"   Ortalama AI Score: {stats.get('average_ai_score', 0):.2f}")
        print(f"   Maksimum AI Score: {stats.get('max_ai_score', 0):.2f}")
        print(f"   Minimum AI Score: {stats.get('min_ai_score', 0):.2f}")
        print()
        
        print("Test basariyla tamamlandi!")
        
        # Save results
        result_filename = f"dynamic_programming_ai_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Sonuclar kaydedildi: {result_filename}")
        
        return True
        
    except Exception as e:
        print(f"Test hatasi: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dynamic_programming_ai()
    sys.exit(0 if success else 1)
