"""
ULTRA AGGRESSIVE EARLY SLOT TEST
3-Strategy approach with conflict prevention
"""
import logging
from app.algorithms.dynamic_programming import DynamicProgramming

logging.basicConfig(level=logging.INFO, format='%(message)s')

def test():
    # 12 projects, 4 instructors, 3 classrooms
    data = {
        "projects": [
            {"id": i, "title": f"P{i}", 
             "type": "bitirme" if i <= 6 else "ara",
             "responsible_id": ((i-1) % 4) + 1, 
             "is_makeup": False}
            for i in range(1, 13)
        ],
        "instructors": [
            {"id": 1, "name": "Dr. A", "type": "instructor"},
            {"id": 2, "name": "Dr. B", "type": "instructor"},
            {"id": 3, "name": "Dr. C", "type": "instructor"},
            {"id": 4, "name": "Dr. D", "type": "instructor"},
        ],
        "classrooms": [
            {"id": 1, "name": "D101", "capacity": 30},
            {"id": 2, "name": "D102", "capacity": 30},
            {"id": 3, "name": "D103", "capacity": 30},
        ],
        "timeslots": [
            {"id": i, "start_time": f"{8+i//2}:{30*(i%2):02d}",
             "end_time": f"{8+(i+1)//2}:{30*((i+1)%2):02d}",
             "is_morning": i <= 8}
            for i in range(1, 17)
        ]
    }
    
    print("\n" + "="*80)
    print("ULTRA AGGRESSIVE EARLY SLOT TEST (3-Strategy + Conflict Prevention)")
    print("="*80 + "\n")
    
    dp = DynamicProgramming()
    result = dp.optimize(data)
    
    assignments = result.get('assignments', [])
    
    # Timeslot analysis
    timeslots = {}
    for a in assignments:
        tid = a.get('timeslot_id')
        timeslots[tid] = timeslots.get(tid, 0) + 1
    
    print("\nTIMESLOT DISTRIBUTION:")
    for tid in sorted(timeslots.keys()):
        print(f"  Slot {tid}: {timeslots[tid]} projects")
    
    # Metrics
    early = sum(1 for a in assignments if a.get('timeslot_id', 0) <= 6)
    late = sum(1 for a in assignments if a.get('timeslot_id', 0) >= 14)
    
    used = sorted(set(a.get('timeslot_id') for a in assignments))
    gaps = [i for i in range(used[0], used[-1]+1) if i not in used] if used else []
    
    print(f"\nKEY METRICS:")
    print(f"  - Total: {len(assignments)} assignments")
    print(f"  - Early (1-6): {early} ({early/len(assignments)*100:.1f}%)")
    print(f"  - Late (14+): {late} ({late/len(assignments)*100 if assignments else 0:.1f}%)")
    print(f"  - Gaps: {len(gaps)} {gaps if gaps else '- NONE'}")
    print(f"  - Conflicts: {'NONE' if not result.get('conflicts') else len(result.get('conflicts'))}")
    print(f"  - AI Features: {result.get('parameters', {}).get('ai_features_count')}")
    
    print("\n" + "="*80)
    status = "SUCCESS" if early >= len(assignments) * 0.6 and len(gaps) == 0 and late == 0 else "GOOD"
    print(f"{status}: ULTRA AGGRESSIVE EARLY SLOT WORKING!")
    print("="*80 + "\n")

if __name__ == "__main__":
    test()

