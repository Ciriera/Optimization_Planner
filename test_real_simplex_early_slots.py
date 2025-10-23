#!/usr/bin/env python3
"""
Test script for Real Simplex Algorithm with early timeslot optimization.
Tests the new priority early timeslot feature (15:30-17:00).
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from algorithms.real_simplex import RealSimplexAlgorithm

def test_real_simplex_early_optimization():
    """Test Real Simplex Algorithm with early timeslot optimization."""
    
    print("=" * 80)
    print("REAL SIMPLEX ALGORITHM - EARLY TIMESLOT OPTIMIZATION TEST")
    print("=" * 80)
    print(f"Test başlangıç zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Sample test data
    test_data = {
        "projects": [
            {"id": 1, "instructor_id": 1, "project_type": "Bitirme"},
            {"id": 2, "instructor_id": 2, "project_type": "Ara"},
            {"id": 3, "instructor_id": 1, "project_type": "Bitirme"},
            {"id": 4, "instructor_id": 3, "project_type": "Ara"},
            {"id": 5, "instructor_id": 2, "project_type": "Bitirme"},
            {"id": 6, "instructor_id": 4, "project_type": "Ara"},
        ],
        "instructors": [
            {"id": 1, "name": "Dr. Ogretim Uyesi 1"},
            {"id": 2, "name": "Dr. Ogretim Uyesi 2"},
            {"id": 3, "name": "Dr. Ogretim Uyesi 3"},
            {"id": 4, "name": "Dr. Ogretim Uyesi 4"},
        ],
        "classrooms": [
            {"id": 1, "name": "D105"},
            {"id": 2, "name": "D106"},
            {"id": 3, "name": "D107"},
            {"id": 4, "name": "D108"},
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
            {"id": 11, "start_time": "15:00", "end_time": "15:30"},
            {"id": 12, "start_time": "15:30", "end_time": "16:00"},  # Priority slot
            {"id": 13, "start_time": "16:00", "end_time": "16:30"},  # Priority slot
            {"id": 14, "start_time": "16:30", "end_time": "17:00"},  # Priority slot
            {"id": 15, "start_time": "17:00", "end_time": "17:30"},
            {"id": 16, "start_time": "17:30", "end_time": "18:00"},
        ]
    }
    
    print("Test Verileri:")
    print(f"   Projeler: {len(test_data['projects'])}")
    print(f"   Instructors: {len(test_data['instructors'])}")
    print(f"   Siniflar: {len(test_data['classrooms'])}")
    print(f"   Zaman Slotlari: {len(test_data['timeslots'])}")
    print()
    
    # Priority timeslots (15:30-17:00)
    priority_timeslots = [ts for ts in test_data['timeslots'] 
                         if "15:30" <= ts['start_time'] <= "17:00"]
    print(f"Oncelikli slotlar (15:30-17:00): {len(priority_timeslots)}")
    for ts in priority_timeslots:
        print(f"   - {ts['start_time']}-{ts['end_time']} (ID: {ts['id']})")
    print()
    
    try:
        # Initialize algorithm
        algorithm = RealSimplexAlgorithm()
        
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
        
        # Check priority timeslot usage
        priority_usage = 0
        late_usage = 0
        
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                timeslot = next((ts for ts in test_data['timeslots'] 
                               if ts['id'] == timeslot_id), None)
                if timeslot:
                    start_time = timeslot['start_time']
                    if "15:30" <= start_time <= "17:00":
                        priority_usage += 1
                    elif start_time > "17:00":
                        late_usage += 1
        
        print(f"Oncelikli slotlarda kullanim (15:30-17:00): {priority_usage}")
        print(f"Gec slotlarda kullanim (17:00+): {late_usage}")
        print()
        
        # Show assignments by timeslot
        print("Zaman Slotuna Gore Atamalar:")
        sorted_timeslots = sorted(test_data['timeslots'], key=lambda x: x['start_time'])
        
        for timeslot in sorted_timeslots:
            slot_assignments = [a for a in assignments 
                              if a.get('timeslot_id') == timeslot['id']]
            
            if slot_assignments:
                is_priority = "15:30" <= timeslot['start_time'] <= "17:00"
                priority_marker = "[PRIORITY]" if is_priority else "         "
                
                print(f"{priority_marker} {timeslot['start_time']}-{timeslot['end_time']}: {len(slot_assignments)} proje")
                for assignment in slot_assignments:
                    project_id = assignment.get('project_id')
                    instructor_id = assignment.get('instructors', [None])[0]
                    classroom_id = assignment.get('classroom_id')
                    classroom_name = next((c['name'] for c in test_data['classrooms'] 
                                         if c['id'] == classroom_id), 'Unknown')
                    print(f"      - Proje {project_id} (Instructor {instructor_id}) - {classroom_name}")
            else:
                print(f"         {timeslot['start_time']}-{timeslot['end_time']}: Bos")
        
        print()
        print("Test basariyla tamamlandi!")
        
        # Save results
        result_filename = f"real_simplex_early_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    success = test_real_simplex_early_optimization()
    sys.exit(0 if success else 1)
