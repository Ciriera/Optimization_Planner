"""
Test script for Genetic Algorithm implementation.
Verifies the GA works correctly with mock data.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.algorithms.genetic_algorithm import (
    GeneticAlgorithm,
    GAConfig,
    PriorityMode,
    TimePenaltyMode,
    WorkloadConstraintMode,
    create_genetic_algorithm
)


def create_mock_data():
    """Create mock data for testing."""
    # Mock instructors (27 instructors)
    instructors = [
        {"id": 1, "name": "ACK", "type": "instructor"},
        {"id": 2, "name": "AO", "type": "instructor"},
        {"id": 3, "name": "AEL", "type": "instructor"},
        {"id": 4, "name": "BD", "type": "instructor"},
        {"id": 5, "name": "EU", "type": "instructor"},
        {"id": 6, "name": "FC", "type": "instructor"},
        {"id": 7, "name": "G1", "type": "instructor"},
        {"id": 8, "name": "GB", "type": "instructor"},
        {"id": 9, "name": "HIT", "type": "instructor"},
        {"id": 10, "name": "HOI", "type": "instructor"},
        {"id": 11, "name": "MAG", "type": "instructor"},
        {"id": 12, "name": "MEK", "type": "instructor"},
        {"id": 13, "name": "MFA", "type": "instructor"},
        {"id": 14, "name": "MSA", "type": "instructor"},
        {"id": 15, "name": "OA", "type": "instructor"},
        {"id": 16, "name": "OK", "type": "instructor"},
        {"id": 17, "name": "SV", "type": "instructor"},
        {"id": 18, "name": "SY", "type": "instructor"},
        {"id": 19, "name": "UK", "type": "instructor"},
        {"id": 20, "name": "YES", "type": "instructor"},
        {"id": 21, "name": "ZCT", "type": "instructor"},
        {"id": 22, "name": "HTK", "type": "instructor"},
        {"id": 23, "name": "MKY", "type": "instructor"},
        {"id": 24, "name": "OMTK", "type": "instructor"},
        {"id": 25, "name": "SD", "type": "instructor"},
        {"id": 26, "name": "EA", "type": "instructor"},
        {"id": 27, "name": "MEO", "type": "instructor"},
    ]
    
    # Mock projects (81 projects total - 46 interim, 35 final)
    projects = []
    project_id = 1
    
    # Instructor project assignments (from the user's data)
    instructor_projects = {
        1: {"ara": 2, "bitirme": 3},   # ACK
        2: {"ara": 4, "bitirme": 3},   # AO
        3: {"ara": 5, "bitirme": 5},   # AEL
        4: {"ara": 3, "bitirme": 5},   # BD
        5: {"ara": 2, "bitirme": 0},   # EU
        6: {"ara": 7, "bitirme": 0},   # FC
        7: {"ara": 1, "bitirme": 1},   # G1
        8: {"ara": 1, "bitirme": 4},   # GB
        9: {"ara": 0, "bitirme": 2},   # HIT
        10: {"ara": 1, "bitirme": 1},  # HOI
        11: {"ara": 2, "bitirme": 1},  # MAG
        12: {"ara": 3, "bitirme": 2},  # MEK
        13: {"ara": 1, "bitirme": 1},  # MFA
        14: {"ara": 1, "bitirme": 4},  # MSA
        15: {"ara": 0, "bitirme": 1},  # OA
        16: {"ara": 0, "bitirme": 0},  # OK
        17: {"ara": 2, "bitirme": 0},  # SV
        18: {"ara": 0, "bitirme": 0},  # SY
        19: {"ara": 0, "bitirme": 0},  # UK
        20: {"ara": 2, "bitirme": 1},  # YES
        21: {"ara": 0, "bitirme": 0},  # ZCT
        22: {"ara": 3, "bitirme": 3},  # HTK
        23: {"ara": 0, "bitirme": 1},  # MKY
        24: {"ara": 0, "bitirme": 0},  # OMTK
        25: {"ara": 0, "bitirme": 0},  # SD
        26: {"ara": 2, "bitirme": 0},  # EA
        27: {"ara": 1, "bitirme": 0},  # MEO
    }
    
    for instructor_id, counts in instructor_projects.items():
        # Interim projects
        for i in range(counts["ara"]):
            projects.append({
                "id": project_id,
                "title": f"Ara Proje {project_id}",
                "type": "interim",
                "responsible_id": instructor_id,
                "is_makeup": False
            })
            project_id += 1
        
        # Final projects
        for i in range(counts["bitirme"]):
            projects.append({
                "id": project_id,
                "title": f"Bitirme Projesi {project_id}",
                "type": "final",
                "responsible_id": instructor_id,
                "is_makeup": False
            })
            project_id += 1
    
    # Mock classrooms
    classrooms = [
        {"id": 1, "name": "D105"},
        {"id": 2, "name": "D106"},
        {"id": 3, "name": "D107"},
        {"id": 4, "name": "D108"},
        {"id": 5, "name": "D109"},
        {"id": 6, "name": "D110"},
        {"id": 7, "name": "D111"},
    ]
    
    # Mock timeslots (15 slots per day)
    timeslots = []
    for i in range(15):
        hour = 9 + (i // 2)
        minute = "00" if i % 2 == 0 else "30"
        timeslots.append({
            "id": i + 1,
            "start_time": f"{hour}:{minute}",
            "end_time": f"{hour + (1 if minute == '30' else 0)}:{('30' if minute == '00' else '00')}",
            "day": "2025-01-15"
        })
    
    return {
        "projects": projects,
        "instructors": instructors,
        "classrooms": classrooms,
        "timeslots": timeslots
    }


def test_ga_basic():
    """Basic GA test."""
    print("=" * 60)
    print("GENETIC ALGORITHM TEST")
    print("=" * 60)
    
    # Create mock data
    data = create_mock_data()
    
    print(f"\nProje sayisi: {len(data['projects'])}")
    print(f"Ogretim gorevlisi sayisi: {len(data['instructors'])}")
    print(f"Sinif sayisi: {len(data['classrooms'])}")
    print(f"Timeslot sayisi: {len(data['timeslots'])}")
    
    # Count project types
    interim_count = sum(1 for p in data['projects'] if p['type'] == 'interim')
    final_count = sum(1 for p in data['projects'] if p['type'] == 'final')
    print(f"Ara proje: {interim_count}, Bitirme proje: {final_count}")
    
    # Create GA with parameters
    # class_count will be auto-detected from classrooms if auto_class_count is True
    params = {
        "population_size": 50,
        "max_generations": 30,
        "time_limit": 60,
        "no_improve_limit": 10,
        "class_count": 6,  # Will be overridden if auto_class_count is True
        "auto_class_count": True,  # Auto-detect from classrooms (7 classes)
        "priority_mode": "ESIT",
        "time_penalty_mode": "GAP_PROPORTIONAL",
        "workload_constraint_mode": "SOFT_ONLY",
        "crossover_rate": 0.85,
        "mutation_rate": 0.15,
        "elitism_rate": 0.10
    }
    
    ga = create_genetic_algorithm(params)
    
    print("\n" + "-" * 40)
    print("GA Calistiriliyor...")
    print("-" * 40)
    
    # Run optimization
    result = ga.optimize(data)
    
    print("\n" + "-" * 40)
    print("SONUCLAR")
    print("-" * 40)
    
    print(f"Status: {result.get('status')}")
    print(f"Fitness: {result.get('fitness', 0):.2f}")
    print(f"Cost: {result.get('cost', 0):.2f}")
    print(f"Nesil sayisi: {result.get('generations', 0)}")
    print(f"Calisma suresi: {result.get('execution_time', 0):.2f} saniye")
    print(f"Sinif sayisi: {result.get('class_count', 0)}")
    
    # Penalty breakdown
    pb = result.get('penalty_breakdown', {})
    print(f"\nCeza detaylari:")
    print(f"  H1 (Zaman/Gap): {pb.get('h1_time_penalty', 0):.2f}")
    print(f"  H2 (Is Yuku): {pb.get('h2_workload_penalty', 0):.2f}")
    print(f"  H3 (Sinif Degisimi): {pb.get('h3_class_change_penalty', 0):.2f}")
    print(f"  H4 (Sinif Dengesi): {pb.get('h4_class_load_penalty', 0):.2f}")
    print(f"  H5 (Continuity): {pb.get('continuity_penalty', 0):.2f}")
    print(f"  H6 (Timeslot Conflict): {pb.get('timeslot_conflict_penalty', 0):.2f}")
    
    # Schedule statistics
    schedule = result.get('schedule', [])
    print(f"\nSchedule uzunlugu: {len(schedule)}")
    
    if schedule:
        print("\nIlk 5 atama:")
        for a in schedule[:5]:
            print(f"  Proje {a.get('project_id')}: "
                  f"Sinif {a.get('class_id')}, "
                  f"Sira {a.get('class_order')}, "
                  f"Instructors: {a.get('instructors')}")
        
        # Check J2 placeholder
        print("\nJ2 Placeholder kontrolu:")
        j2_correct = 0
        for a in schedule:
            instructors = a.get('instructors', [])
            if len(instructors) >= 3 and instructors[2] == "[Arastirma Gorevlisi]":
                j2_correct += 1
        print(f"  Dogru J2 placeholder sayisi: {j2_correct}/{len(schedule)}")
        
        # Class distribution
        class_counts = {}
        for a in schedule:
            class_id = a.get('class_id', 0)
            class_counts[class_id] = class_counts.get(class_id, 0) + 1
        
        print("\nSinif dagilimi:")
        total_classes_used = 0
        for class_id, count in sorted(class_counts.items()):
            print(f"  Sinif {class_id}: {count} proje")
            if count > 0:
                total_classes_used += 1
        
        # Check if all classes are used
        expected_class_count = result.get('class_count', 0)
        print(f"\nKullanilan sinif sayisi: {total_classes_used}/{expected_class_count}")
        if total_classes_used == expected_class_count:
            print("  [OK] Tum siniflar kullaniliyor!")
        else:
            print(f"  [WARNING] {expected_class_count - total_classes_used} sinif kullanilmiyor!")
    
    return result


def test_ga_priority_modes():
    """Test different priority modes."""
    print("\n" + "=" * 60)
    print("PRIORITY MODE TESTS")
    print("=" * 60)
    
    data = create_mock_data()
    
    for priority_mode in ["ARA_ONCE", "BITIRME_ONCE", "ESIT"]:
        print(f"\n--- Priority Mode: {priority_mode} ---")
        
        params = {
            "population_size": 30,
            "max_generations": 15,
            "time_limit": 30,
            "class_count": 6,  # Will be auto-detected
            "auto_class_count": True,  # Auto-detect from classrooms
            "priority_mode": priority_mode
        }
        
        ga = create_genetic_algorithm(params)
        result = ga.optimize(data)
        
        print(f"Fitness: {result.get('fitness', 0):.2f}")
        print(f"Nesil: {result.get('generations', 0)}")
        
        # Check project ordering in first class
        schedule = result.get('schedule', [])
        class_0 = [a for a in schedule if a.get('class_id') == 0]
        class_0.sort(key=lambda x: x.get('class_order', 0))
        
        if class_0:
            project_types = []
            for a in class_0[:10]:  # First 10 in class 0
                p_id = a.get('project_id')
                p = next((p for p in data['projects'] if p['id'] == p_id), None)
                if p:
                    project_types.append(p['type'][:3])  # 'int' or 'fin'
            
            print(f"Sinif 0'daki ilk 10 proje turleri: {project_types}")


def test_ga_workload_balance():
    """Test workload balancing."""
    print("\n" + "=" * 60)
    print("WORKLOAD BALANCE TEST")
    print("=" * 60)
    
    data = create_mock_data()
    
    params = {
        "population_size": 50,
        "max_generations": 30,
        "time_limit": 60,
        "class_count": 6,  # Will be auto-detected
        "auto_class_count": True,  # Auto-detect from classrooms
        "workload_constraint_mode": "SOFT_AND_HARD",
        "workload_hard_limit": 4
    }
    
    ga = create_genetic_algorithm(params)
    result = ga.optimize(data)
    
    schedule = result.get('schedule', [])
    
    # Calculate workloads
    workloads = {}
    for a in schedule:
        instructors = a.get('instructors', [])
        if len(instructors) >= 2:
            ps_id = instructors[0]
            j1_id = instructors[1]
            
            if isinstance(ps_id, int):
                workloads[ps_id] = workloads.get(ps_id, 0) + 1
            if isinstance(j1_id, int):
                workloads[j1_id] = workloads.get(j1_id, 0) + 1
    
    if workloads:
        avg_load = sum(workloads.values()) / len(workloads)
        min_load = min(workloads.values())
        max_load = max(workloads.values())
        
        print(f"Ortalama is yuku: {avg_load:.2f}")
        print(f"Min is yuku: {min_load}")
        print(f"Max is yuku: {max_load}")
        print(f"Is yuku araligi: {max_load - min_load}")
        
        # Count instructors outside +/-2 band
        outside_band = 0
        for load in workloads.values():
            if abs(load - avg_load) > 2:
                outside_band += 1
        
        print(f"+/-2 bandi disindaki hoca sayisi: {outside_band}/{len(workloads)}")


if __name__ == "__main__":
    # Run tests
    test_ga_basic()
    test_ga_priority_modes()
    test_ga_workload_balance()
    
    print("\n" + "=" * 60)
    print("TUM TESTLER TAMAMLANDI")
    print("=" * 60)

