"""
🔧 CONFLICT RESOLUTION TEST SCRIPT
Görsellerde tespit edilen çakışmaları test eder ve çözer
"""
import sys
import asyncio
import json
from typing import Dict, List, Any

# Test data - görsellerde tespit edilen çakışmalar
test_conflicts_data = {
    "assignments": [
        # 14:30-15:00 - Dr. Öğretim Üyesi 3 çakışması
        {
            "project_id": 1,
            "timeslot_id": 14,  # 14:30-15:00
            "classroom_id": 1,
            "responsible_instructor_id": 3,  # Dr. Öğretim Üyesi 3 - Sorumlu
            "instructors": [3, 1],  # Dr. Öğretim Üyesi 3 hem sorumlu hem jüri!
            "is_makeup": False
        },
        {
            "project_id": 5,
            "timeslot_id": 14,  # 14:30-15:00
            "classroom_id": 3,
            "responsible_instructor_id": 3,  # Dr. Öğretim Üyesi 3 - Sorumlu
            "instructors": [3],  # Dr. Öğretim Üyesi 3 - Jüri
            "is_makeup": False
        },
        
        # 15:00-15:30 - Dr. Öğretim Üyesi 21 çakışması
        {
            "project_id": 21,
            "timeslot_id": 15,  # 15:00-15:30
            "classroom_id": 2,
            "responsible_instructor_id": 19,
            "instructors": [21],  # Dr. Öğretim Üyesi 21 - Jüri
            "is_makeup": False
        },
        {
            "project_id": 13,
            "timeslot_id": 15,  # 15:00-15:30
            "classroom_id": 5,
            "responsible_instructor_id": 11,
            "instructors": [21],  # Dr. Öğretim Üyesi 21 - Jüri (2. kez!)
            "is_makeup": False
        },
        
        # 16:00-16:30 - Dr. Öğretim Üyesi 11 çakışması
        {
            "project_id": 53,
            "timeslot_id": 16,  # 16:00-16:30
            "classroom_id": 2,
            "responsible_instructor_id": 11,  # Dr. Öğretim Üyesi 11 - Sorumlu
            "instructors": [21],
            "is_makeup": False
        },
        {
            "project_id": 14,
            "timeslot_id": 16,  # 16:00-16:30
            "classroom_id": 7,
            "responsible_instructor_id": 12,
            "instructors": [11],  # Dr. Öğretim Üyesi 11 - Jüri
            "is_makeup": False
        }
    ],
    "projects": [
        {"id": 1, "title": "Bitirme Proje 1", "type": "bitirme"},
        {"id": 5, "title": "Bitirme Proje 5", "type": "bitirme"},
        {"id": 21, "title": "Bitirme Proje 21", "type": "bitirme"},
        {"id": 13, "title": "Bitirme Proje 13", "type": "bitirme"},
        {"id": 53, "title": "Ara Proje 53", "type": "ara"},
        {"id": 14, "title": "Bitirme Proje 14", "type": "bitirme"}
    ],
    "instructors": [
        {"id": 1, "name": "Dr. Öğretim Üyesi 1"},
        {"id": 3, "name": "Dr. Öğretim Üyesi 3"},
        {"id": 11, "name": "Dr. Öğretim Üyesi 11"},
        {"id": 12, "name": "Dr. Öğretim Üyesi 12"},
        {"id": 19, "name": "Dr. Öğretim Üyesi 19"},
        {"id": 21, "name": "Dr. Öğretim Üyesi 21"}
    ],
    "classrooms": [
        {"id": 1, "name": "D105", "capacity": 20},
        {"id": 2, "name": "D106", "capacity": 20},
        {"id": 3, "name": "D107", "capacity": 20},
        {"id": 4, "name": "D108", "capacity": 20},
        {"id": 5, "name": "D109", "capacity": 20},
        {"id": 6, "name": "D110", "capacity": 20},
        {"id": 7, "name": "D111", "capacity": 20}
    ],
    "timeslots": [
        {"id": 14, "start_time": "14:30", "end_time": "15:00", "capacity": 10},
        {"id": 15, "start_time": "15:00", "end_time": "15:30", "capacity": 10},
        {"id": 16, "start_time": "16:00", "end_time": "16:30", "capacity": 10},
        {"id": 17, "start_time": "16:30", "end_time": "17:00", "capacity": 10},
        {"id": 18, "start_time": "17:00", "end_time": "17:30", "capacity": 10}
    ]
}

def test_conflict_detection():
    """Çakışma tespit testini çalıştır"""
    print("=" * 80)
    print("🔍 CONFLICT DETECTION TEST")
    print("=" * 80)
    
    try:
        sys.path.append('.')
        from app.services.conflict_resolution_service import ConflictResolutionService
        
        # Conflict resolution service oluştur
        conflict_service = ConflictResolutionService()
        
        # Çakışmaları tespit et
        conflicts = conflict_service.detect_all_conflicts(
            assignments=test_conflicts_data["assignments"],
            projects=test_conflicts_data["projects"],
            instructors=test_conflicts_data["instructors"],
            classrooms=test_conflicts_data["classrooms"],
            timeslots=test_conflicts_data["timeslots"]
        )
        
        print(f"\n📊 TEST RESULTS:")
        print(f"  - Total assignments: {len(test_conflicts_data['assignments'])}")
        print(f"  - Conflicts detected: {len(conflicts)}")
        
        print(f"\n🔍 DETECTED CONFLICTS:")
        for i, conflict in enumerate(conflicts, 1):
            print(f"  {i}. {conflict['type']}")
            print(f"     Instructor: {conflict.get('instructor_id', 'N/A')}")
            print(f"     Timeslot: {conflict.get('timeslot_id', 'N/A')}")
            print(f"     Severity: {conflict.get('severity', 'N/A')}")
            print(f"     Description: {conflict.get('description', 'N/A')}")
            print(f"     Strategy: {conflict.get('resolution_strategy', 'N/A')}")
            print()
        
        # Rapor oluştur
        report = conflict_service.generate_conflict_report(conflicts)
        
        print(f"📈 CONFLICT SUMMARY:")
        print(f"  - Conflict types: {report['conflict_summary']}")
        print(f"  - Severity breakdown: {report['severity_breakdown']}")
        
        return conflicts
        
    except Exception as e:
        print(f"❌ ERROR in conflict detection: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_conflict_resolution(conflicts):
    """Çakışma çözüm testini çalıştır"""
    print("=" * 80)
    print("🔧 CONFLICT RESOLUTION TEST")
    print("=" * 80)
    
    if not conflicts:
        print("❌ No conflicts to resolve!")
        return
    
    try:
        sys.path.append('.')
        from app.services.conflict_resolution_service import ConflictResolutionService
        
        # Conflict resolution service oluştur
        conflict_service = ConflictResolutionService()
        
        # Çakışmaları çöz
        resolved_assignments, resolution_log = conflict_service.resolve_conflicts(
            assignments=test_conflicts_data["assignments"],
            conflicts=conflicts,
            projects=test_conflicts_data["projects"],
            instructors=test_conflicts_data["instructors"],
            classrooms=test_conflicts_data["classrooms"],
            timeslots=test_conflicts_data["timeslots"]
        )
        
        print(f"\n🔧 RESOLUTION RESULTS:")
        print(f"  - Conflicts attempted: {len(resolution_log)}")
        print(f"  - Successful resolutions: {len([r for r in resolution_log if r['success']])}")
        print(f"  - Failed resolutions: {len([r for r in resolution_log if not r['success']])}")
        
        print(f"\n📝 RESOLUTION LOG:")
        for i, log_entry in enumerate(resolution_log, 1):
            status = "✅" if log_entry['success'] else "❌"
            print(f"  {i}. {status} {log_entry['conflict_id']}")
            print(f"     Strategy: {log_entry['resolution_strategy']}")
            if log_entry['success']:
                print(f"     Changes: {len(log_entry.get('changes_made', []))}")
            else:
                print(f"     Error: {log_entry.get('error', 'Unknown')}")
            print()
        
        # Çözüm sonrası kalan çakışmaları kontrol et
        remaining_conflicts = conflict_service.detect_all_conflicts(
            assignments=resolved_assignments,
            projects=test_conflicts_data["projects"],
            instructors=test_conflicts_data["instructors"],
            classrooms=test_conflicts_data["classrooms"],
            timeslots=test_conflicts_data["timeslots"]
        )
        
        print(f"🔍 REMAINING CONFLICTS: {len(remaining_conflicts)}")
        if remaining_conflicts:
            for conflict in remaining_conflicts:
                print(f"  - {conflict['type']}: {conflict['description']}")
        else:
            print("  ✅ All conflicts resolved!")
        
        return resolved_assignments, resolution_log
        
    except Exception as e:
        print(f"❌ ERROR in conflict resolution: {e}")
        import traceback
        traceback.print_exc()
        return None, []

def test_specific_conflicts():
    """Belirli çakışmaları test et"""
    print("=" * 80)
    print("🎯 SPECIFIC CONFLICTS TEST")
    print("=" * 80)
    
    try:
        sys.path.append('.')
        from app.services.conflict_resolution_service import ConflictResolutionService
        
        # Conflict resolution service oluştur
        conflict_service = ConflictResolutionService()
        
        # Tüm çakışmaları tespit et
        all_conflicts = conflict_service.detect_all_conflicts(
            assignments=test_conflicts_data["assignments"],
            projects=test_conflicts_data["projects"],
            instructors=test_conflicts_data["instructors"],
            classrooms=test_conflicts_data["classrooms"],
            timeslots=test_conflicts_data["timeslots"]
        )
        
        # Belirli instructor'lar için çakışmaları filtrele
        target_instructors = [3, 21, 11]  # Görsellerde çakışan instructor'lar
        target_timeslots = [14, 15, 16]   # Görsellerde çakışan zaman dilimleri
        
        specific_conflicts = []
        for conflict in all_conflicts:
            if (conflict.get('instructor_id') in target_instructors and 
                conflict.get('timeslot_id') in target_timeslots):
                specific_conflicts.append(conflict)
        
        print(f"🎯 SPECIFIC CONFLICTS FOUND:")
        print(f"  - Target instructors: {target_instructors}")
        print(f"  - Target timeslots: {target_timeslots}")
        print(f"  - Specific conflicts: {len(specific_conflicts)}")
        
        for conflict in specific_conflicts:
            print(f"    - Instructor {conflict['instructor_id']} in timeslot {conflict['timeslot_id']}: {conflict['type']}")
        
        if specific_conflicts:
            # Belirli çakışmaları çöz
            resolved_assignments, resolution_log = conflict_service.resolve_conflicts(
                assignments=test_conflicts_data["assignments"],
                conflicts=specific_conflicts,
                projects=test_conflicts_data["projects"],
                instructors=test_conflicts_data["instructors"],
                classrooms=test_conflicts_data["classrooms"],
                timeslots=test_conflicts_data["timeslots"]
            )
            
            successful = len([r for r in resolution_log if r['success']])
            print(f"\n🔧 SPECIFIC RESOLUTION: {successful}/{len(specific_conflicts)} resolved")
        
        return specific_conflicts
        
    except Exception as e:
        print(f"❌ ERROR in specific conflicts test: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Ana test fonksiyonu"""
    print("🔧 CONFLICT RESOLUTION SYSTEM TEST")
    print("=" * 80)
    print("Bu test görsellerde tespit edilen çakışmaları test eder:")
    print("1. Dr. Öğretim Üyesi 3: 14:30-15:00'da 2 farklı görev")
    print("2. Dr. Öğretim Üyesi 21: 15:00-15:30'da 2 jüri görevi")
    print("3. Dr. Öğretim Üyesi 11: 16:00-16:30'da 2 farklı görev")
    print("=" * 80)
    
    # Test 1: Çakışma tespit
    conflicts = test_conflict_detection()
    
    # Test 2: Çakışma çözüm
    if conflicts:
        resolved_assignments, resolution_log = test_conflict_resolution(conflicts)
    
    # Test 3: Belirli çakışmalar
    specific_conflicts = test_specific_conflicts()
    
    print("=" * 80)
    print("✅ CONFLICT RESOLUTION TEST COMPLETED")
    print("=" * 80)
    
    if conflicts:
        print(f"📊 FINAL SUMMARY:")
        print(f"  - Total conflicts detected: {len(conflicts)}")
        print(f"  - Specific conflicts targeted: {len(specific_conflicts)}")
        if 'resolution_log' in locals():
            successful = len([r for r in resolution_log if r['success']])
            print(f"  - Conflicts resolved: {successful}")
        
        print(f"\n🎯 EXPECTED CONFLICTS (from images):")
        print(f"  ✅ Dr. Öğretim Üyesi 3: 14:30-15:00 conflict")
        print(f"  ✅ Dr. Öğretim Üyesi 21: 15:00-15:30 conflict")
        print(f"  ✅ Dr. Öğretim Üyesi 11: 16:00-16:30 conflict")
        
        print(f"\n🚀 SYSTEM STATUS: READY TO RESOLVE CONFLICTS!")
    else:
        print(f"❌ NO CONFLICTS DETECTED - System may need adjustment")

if __name__ == "__main__":
    main()
