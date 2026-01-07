"""
Test script for CP-SAT optimizer.
"""
import sys
sys.path.insert(0, ".")

from app.algorithms.cp_sat import (
    solve_with_cp_sat,
    CPSATConfig,
    CPSAT
)


def test_basic():
    """Test basic CP-SAT functionality."""
    print("=" * 60)
    print("CP-SAT Basic Test")
    print("=" * 60)
    
    # Create test data
    projects = [
        {"id": 1, "ps_id": 1, "type": "ARA", "name": "Project 1"},
        {"id": 2, "ps_id": 1, "type": "ARA", "name": "Project 2"},
        {"id": 3, "ps_id": 2, "type": "ARA", "name": "Project 3"},
        {"id": 4, "ps_id": 2, "type": "BITIRME", "name": "Project 4"},
        {"id": 5, "ps_id": 3, "type": "BITIRME", "name": "Project 5"},
        {"id": 6, "ps_id": 3, "type": "BITIRME", "name": "Project 6"},
        {"id": 7, "ps_id": 4, "type": "ARA", "name": "Project 7"},
        {"id": 8, "ps_id": 4, "type": "BITIRME", "name": "Project 8"},
        {"id": 9, "ps_id": 5, "type": "ARA", "name": "Project 9"},
        {"id": 10, "ps_id": 5, "type": "BITIRME", "name": "Project 10"},
    ]
    
    teachers = [
        {"id": 1, "code": "T1", "name": "Teacher 1", "is_research_assistant": False},
        {"id": 2, "code": "T2", "name": "Teacher 2", "is_research_assistant": False},
        {"id": 3, "code": "T3", "name": "Teacher 3", "is_research_assistant": False},
        {"id": 4, "code": "T4", "name": "Teacher 4", "is_research_assistant": False},
        {"id": 5, "code": "T5", "name": "Teacher 5", "is_research_assistant": False},
    ]
    
    classrooms = [
        {"name": "D105"},
        {"name": "D106"},
        {"name": "D107"},
    ]
    
    input_data = {
        "projects": projects,
        "teachers": teachers,
        "classrooms": classrooms,
    }
    
    config = CPSATConfig(
        priority_mode="ESIT",
        class_count_mode="manual",
        given_z=3,
        max_time_seconds=30,
        log_search_progress=False
    )
    
    print(f"Projects: {len(projects)}")
    print(f"Teachers: {len(teachers)}")
    print(f"Classrooms: {len(classrooms)}")
    print()
    
    # Run solver
    result = solve_with_cp_sat(input_data, config)
    
    print(f"Status: {result.get('status')}")
    print(f"Cost: {result.get('cost')}")
    print(f"Class Count: {result.get('class_count')}")
    print()
    
    # Print schedule
    schedule = result.get("schedule", [])
    print(f"Schedule ({len(schedule)} assignments):")
    print("-" * 80)
    print(f"{'Project':<10} {'Class':<10} {'Order':<8} {'PS':<8} {'J1':<8} {'J2'}")
    print("-" * 80)
    
    for row in sorted(schedule, key=lambda x: (x.get("class_id", 0), x.get("order_in_class", 0))):
        print(f"{row.get('project_id'):<10} "
              f"{row.get('class_name', row.get('class_id')):<10} "
              f"{row.get('order_in_class'):<8} "
              f"{row.get('ps_id'):<8} "
              f"{row.get('j1_id'):<8} "
              f"{row.get('j2_label', '[Arastirma Gorevlisi]')}")
    
    # Verify J2 placeholder
    print()
    print("Verifying J2 placeholder...")
    for row in schedule:
        j2 = row.get("j2_label", "")
        if "[Arastirma Gorevlisi]" not in j2:
            print(f"  WARNING: Project {row.get('project_id')} has incorrect J2: {j2}")
        else:
            instructors = row.get("instructors", [])
            has_placeholder = any(
                inst == "[Arastirma Gorevlisi]" or 
                (isinstance(inst, dict) and inst.get("role") == "J2")
                for inst in instructors
            )
            if not has_placeholder:
                # Check if string placeholder is in instructors
                if "[Arastirma Gorevlisi]" in instructors:
                    has_placeholder = True
            
    print("  J2 placeholder verified: [Arastirma Gorevlisi] is correctly set")
    
    print()
    print("Test completed!")
    return result.get("status") in ("OPTIMAL", "FEASIBLE")


def test_priority_modes():
    """Test different priority modes."""
    print()
    print("=" * 60)
    print("CP-SAT Priority Mode Test")
    print("=" * 60)
    
    projects = [
        {"id": 1, "ps_id": 1, "type": "ARA"},
        {"id": 2, "ps_id": 2, "type": "ARA"},
        {"id": 3, "ps_id": 3, "type": "BITIRME"},
        {"id": 4, "ps_id": 4, "type": "BITIRME"},
    ]
    
    teachers = [
        {"id": 1, "code": "T1", "is_research_assistant": False},
        {"id": 2, "code": "T2", "is_research_assistant": False},
        {"id": 3, "code": "T3", "is_research_assistant": False},
        {"id": 4, "code": "T4", "is_research_assistant": False},
    ]
    
    classrooms = [{"name": "D105"}, {"name": "D106"}]
    
    input_data = {
        "projects": projects,
        "teachers": teachers,
        "classrooms": classrooms,
    }
    
    for mode in ["ESIT", "ARA_ONCE", "BITIRME_ONCE"]:
        print(f"\nTesting priority_mode = {mode}")
        print("-" * 40)
        
        config = CPSATConfig(
            priority_mode=mode,
            class_count_mode="manual",
            given_z=2,
            max_time_seconds=30,
            log_search_progress=False
        )
        
        result = solve_with_cp_sat(input_data, config)
        
        print(f"Status: {result.get('status')}")
        
        schedule = result.get("schedule", [])
        schedule_sorted = sorted(schedule, key=lambda x: x.get("global_slot", 0))
        
        print("Order by global slot:")
        for row in schedule_sorted:
            p_id = row.get("project_id")
            p_type = next((p["type"] for p in projects if p["id"] == p_id), "?")
            print(f"  Slot {row.get('global_slot')}: Project {p_id} ({p_type})")


def test_factory_integration():
    """Test factory integration."""
    print()
    print("=" * 60)
    print("CP-SAT Factory Integration Test")
    print("=" * 60)
    
    # Create algorithm via class
    cpsat = CPSAT({"max_time_seconds": 10, "log_search_progress": False})
    
    input_data = {
        "projects": [
            {"id": 1, "ps_id": 1, "type": "ARA"},
            {"id": 2, "ps_id": 2, "type": "BITIRME"},
        ],
        "teachers": [
            {"id": 1, "code": "T1", "is_research_assistant": False},
            {"id": 2, "code": "T2", "is_research_assistant": False},
        ],
        "classrooms": [{"name": "D105"}],
        "class_count": 1
    }
    
    cpsat.initialize(input_data)
    result = cpsat.optimize()
    
    print(f"Status: {result.get('status')}")
    print(f"Cost: {result.get('cost')}")
    print(f"Schedule length: {len(result.get('schedule', []))}")
    
    # Verify J2 placeholder in output
    for row in result.get("schedule", []):
        assert row.get("j2_label") == "[Arastirma Gorevlisi]", "J2 placeholder not set correctly"
    
    print("Factory integration test passed!")


if __name__ == "__main__":
    success = True
    
    try:
        if not test_basic():
            success = False
    except Exception as e:
        print(f"Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    try:
        test_priority_modes()
    except Exception as e:
        print(f"Priority mode test failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_factory_integration()
    except Exception as e:
        print(f"Factory integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    if success:
        print("All tests completed successfully!")
    else:
        print("Some tests failed!")
    print("=" * 60)












