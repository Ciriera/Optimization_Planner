"""
PSO Test Script - Algoritmanın neden boş döndüğünü tespit et
"""
import sys
sys.path.insert(0, '.')

from app.algorithms.pso import PSO

# Test verisi oluştur
test_data = {
    "projects": [
        {"id": 1, "type": "bitirme", "title": "Bitirme 1", "responsible_id": 1},
        {"id": 2, "type": "bitirme", "title": "Bitirme 2", "responsible_id": 2},
        {"id": 3, "type": "bitirme", "title": "Bitirme 3", "responsible_id": 3},
        {"id": 4, "type": "ara", "title": "Ara 1", "responsible_id": 1},
        {"id": 5, "type": "ara", "title": "Ara 2", "responsible_id": 2},
        {"id": 6, "type": "ara", "title": "Ara 3", "responsible_id": 3},
    ],
    "instructors": [
        {"id": 1, "name": "Instructor 1", "type": "instructor"},
        {"id": 2, "name": "Instructor 2", "type": "instructor"},
        {"id": 3, "name": "Instructor 3", "type": "instructor"},
        {"id": 4, "name": "Instructor 4", "type": "instructor"},
    ],
    "classrooms": [
        {"id": 1, "name": "D105"},
        {"id": 2, "name": "D106"},
    ],
    "timeslots": [
        {"id": 1, "start_time": "09:00", "end_time": "09:30"},
        {"id": 2, "start_time": "09:30", "end_time": "10:00"},
        {"id": 3, "start_time": "10:00", "end_time": "10:30"},
        {"id": 4, "start_time": "10:30", "end_time": "11:00"},
        {"id": 5, "start_time": "11:00", "end_time": "11:30"},
        {"id": 6, "start_time": "11:30", "end_time": "12:00"},
    ]
}

print("=" * 60)
print("PSO TEST - Veri kontrolü")
print("=" * 60)
print(f"Projects: {len(test_data['projects'])}")
print(f"Instructors: {len(test_data['instructors'])}")
print(f"Classrooms: {len(test_data['classrooms'])}")
print(f"Timeslots: {len(test_data['timeslots'])}")
print()

# PSO çalıştır
pso = PSO()
print("PSO instance created")

result = pso.optimize(test_data)

print()
print("=" * 60)
print("RESULT")
print("=" * 60)
print(f"Status: {result.get('status')}")
print(f"Algorithm: {result.get('algorithm')}")
print(f"Assignments count: {len(result.get('assignments', []))}")
print(f"Fitness: {result.get('fitness')}")
print()

if result.get('assignments'):
    print("Assignments:")
    for a in result['assignments']:
        print(f"  Project {a.get('project_id')} -> Timeslot {a.get('timeslot_id')}, Class {a.get('classroom_id')}, Type: {a.get('project_type')}")
else:
    print("NO ASSIGNMENTS!")
