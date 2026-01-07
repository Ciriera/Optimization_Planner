"""
Tabu Search algoritmasını test etmek için script.
"""
import sys
import os

# Parent directory'yi path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.algorithms.tabu_search import TabuSearch, TabuConfig, PriorityMode

def main():
    print("=" * 60)
    print("TABU SEARCH ALGORITHM TEST")
    print("=" * 60)
    
    # Test initialization
    ts = TabuSearch({
        'max_iterations': 100,
        'time_limit': 30,
        'class_count': 6,
        'auto_class_count': False,
        'priority_mode': 'ESIT'
    })
    
    # Mock data for testing
    test_data = {
        'projects': [
            {
                'id': i, 
                'title': f'Project {i}', 
                'type': 'interim' if i % 2 == 0 else 'final', 
                'responsible_id': (i % 5) + 1
            }
            for i in range(1, 21)  # 20 projects
        ],
        'instructors': [
            {'id': i, 'name': f'Instructor {i}', 'type': 'instructor'}
            for i in range(1, 11)  # 10 instructors
        ],
        'classrooms': [
            {'id': i, 'name': f'D10{i}'}
            for i in range(1, 8)  # 7 classrooms
        ],
        'timeslots': [
            {
                'id': i, 
                'start_time': f'{9 + i//2:02d}:{(i%2)*30:02d}', 
                'end_time': f'{9 + (i+1)//2:02d}:{((i+1)%2)*30:02d}'
            }
            for i in range(1, 15)  # 14 timeslots
        ]
    }
    
    print(f"Test Data:")
    print(f"  - Projects: {len(test_data['projects'])}")
    print(f"  - Instructors: {len(test_data['instructors'])}")
    print(f"  - Classrooms: {len(test_data['classrooms'])}")
    print(f"  - Timeslots: {len(test_data['timeslots'])}")
    print()
    
    # Initialize and optimize
    print("Running Tabu Search optimization...")
    ts.initialize(test_data)
    result = ts.optimize()
    
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Status: {result.get('status')}")
    print(f"Iterations: {result.get('iterations')}")
    print(f"Execution Time: {result.get('execution_time', 0):.2f} seconds")
    print(f"Cost: {result.get('cost', 0):.2f}")
    print(f"Class Count: {result.get('class_count')}")
    print(f"Scheduled Projects: {len(result.get('schedule', []))}")
    print()
    
    print("Penalty Breakdown:")
    breakdown = result.get('penalty_breakdown', {})
    for key, value in breakdown.items():
        print(f"  {key}: {value:.2f}")
    print()
    
    print("First 5 Assignments:")
    for a in result.get('schedule', [])[:5]:
        print(f"  Project {a.get('project_id')}: "
              f"Class {a.get('class_id')}, "
              f"Instructors: {a.get('instructors')}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()












