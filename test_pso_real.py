"""
PSO Test Script - Uygulama config'i ile gerçek veritabanından
"""
import sys
sys.path.insert(0, '.')

# Uygulama ayarlarını kullan
from app.core.config import settings
from app.db.session import SessionLocal

print("=" * 60)
print("Veritabanından veri çekiliyor...")
print(f"DB: {settings.POSTGRES_DB}")
print("=" * 60)

session = SessionLocal()

try:
    from sqlalchemy import text
    
    # Projects
    projects_result = session.execute(text("SELECT id, title, type, responsible_instructor_id FROM projects"))
    projects = [{"id": r[0], "title": r[1], "type": r[2], "responsible_id": r[3]} for r in projects_result]
    print(f"Projects: {len(projects)}")

    # Instructors
    instructors_result = session.execute(text("SELECT id, name, type FROM instructors"))
    instructors = [{"id": r[0], "name": r[1], "type": r[2]} for r in instructors_result]
    print(f"Instructors: {len(instructors)}")

    # Classrooms
    classrooms_result = session.execute(text("SELECT id, name FROM classrooms"))
    classrooms = [{"id": r[0], "name": r[1]} for r in classrooms_result]
    print(f"Classrooms: {len(classrooms)}")

    # Timeslots
    timeslots_result = session.execute(text("SELECT id, start_time, end_time FROM timeslots"))
    timeslots = [{"id": r[0], "start_time": str(r[1]), "end_time": str(r[2])} for r in timeslots_result]
    print(f"Timeslots: {len(timeslots)}")

    # Proje türlerini göster
    bitirme_count = len([p for p in projects if p.get('type') == 'bitirme'])
    ara_count = len([p for p in projects if p.get('type') == 'ara'])
    print(f"\nBitirme: {bitirme_count}, Ara: {ara_count}")

    # İlk 3 projeyi göster
    print("\nIlk 3 proje:")
    for p in projects[:3]:
        print(f"  {p}")

    # İlk 3 timeslot göster
    print("\nIlk 3 timeslot:")
    for t in timeslots[:3]:
        print(f"  {t}")

    print()
    print("=" * 60)
    print("PSO calistiriliyor...")
    print("=" * 60)

    from app.algorithms.pso import PSO

    test_data = {
        "projects": projects,
        "instructors": instructors,
        "classrooms": classrooms,
        "timeslots": timeslots
    }

    pso = PSO()
    result = pso.optimize(test_data)

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"Status: {result.get('status')}")
    print(f"Algorithm: {result.get('algorithm')}")
    print(f"Assignments count: {len(result.get('assignments', []))}")
    print(f"Fitness: {result.get('fitness')}")

    assignments = result.get('assignments', [])
    if assignments:
        # İlk 10 atamayı göster
        print("\nIlk 10 atama:")
        for a in assignments[:10]:
            print(f"  Project {a.get('project_id')} ({a.get('project_type')}) -> Timeslot {a.get('timeslot_id')}, Class {a.get('classroom_id')}")
        
        # Bitirme/Ara doğrulama
        bitirme_slots = [a.get('timeslot_id') for a in assignments if a.get('project_type') == 'bitirme']
        ara_slots = [a.get('timeslot_id') for a in assignments if a.get('project_type') == 'ara']
        
        if bitirme_slots and ara_slots:
            print(f"\nBitirme slot aralik: {min(bitirme_slots)} - {max(bitirme_slots)}")
            print(f"Ara slot aralik: {min(ara_slots)} - {max(ara_slots)}")
            
            if max(bitirme_slots) <= min(ara_slots):
                print("OK Bitirme onceligi SAGLANDI!")
            else:
                print("HATA Bitirme onceligi IHLAL!")
    else:
        print("\nHATA NO ASSIGNMENTS!")

finally:
    session.close()
