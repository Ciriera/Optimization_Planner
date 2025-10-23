"""
Dynamic Programming Algorithm - Çakışma Kontrol Scripti
"""
import asyncio
from sqlalchemy import text
from app.db.base import async_session

async def check_conflicts():
    """DP algoritması sonuçlarında çakışmaları kontrol et"""
    
    async with async_session() as db:
        # Schedules tablosundan tüm atamaları al
        result = await db.execute(text("""
            SELECT 
                s.id,
                s.project_id,
                p.title as project_title,
                s.classroom_id,
                c.name as classroom_name,
                s.timeslot_id,
                t.start_time,
                t.end_time,
                s.instructors
            FROM schedules s
            JOIN projects p ON s.project_id = p.id
            JOIN classrooms c ON s.classroom_id = c.id
            JOIN timeslots t ON s.timeslot_id = t.id
            ORDER BY t.start_time, c.name
        """))
        
        schedules = result.fetchall()
        
        print("=" * 100)
        print("DYNAMIC PROGRAMMING - ÇAKIŞMA ANALİZİ")
        print("=" * 100)
        print(f"Toplam atama: {len(schedules)}")
        print()
        
        # Çakışmaları kontrol et
        conflicts = []
        
        # 1. Aynı sınıf + aynı slot çakışması
        classroom_slot_map = {}
        for schedule in schedules:
            schedule_id, project_id, project_title, classroom_id, classroom_name, timeslot_id, start_time, end_time, instructors = schedule
            
            key = (classroom_id, timeslot_id)
            if key in classroom_slot_map:
                conflicts.append({
                    "type": "classroom_slot",
                    "schedule1": classroom_slot_map[key],
                    "schedule2": {
                        "schedule_id": schedule_id,
                        "project_id": project_id,
                        "project_title": project_title,
                        "classroom": classroom_name,
                        "timeslot": f"{start_time}-{end_time}",
                        "instructors": instructors
                    }
                })
            else:
                classroom_slot_map[key] = {
                    "schedule_id": schedule_id,
                    "project_id": project_id,
                    "project_title": project_title,
                    "classroom": classroom_name,
                    "timeslot": f"{start_time}-{end_time}",
                    "instructors": instructors
                }
        
        # 2. Aynı instructor + aynı slot çakışması
        instructor_slot_map = {}
        for schedule in schedules:
            schedule_id, project_id, project_title, classroom_id, classroom_name, timeslot_id, start_time, end_time, instructors = schedule
            
            if instructors:  # JSON array
                import json
                instructor_list = json.loads(instructors) if isinstance(instructors, str) else instructors
                
                for instructor_id in instructor_list:
                    key = (instructor_id, timeslot_id)
                    if key in instructor_slot_map:
                        conflicts.append({
                            "type": "instructor_slot",
                            "instructor_id": instructor_id,
                            "schedule1": instructor_slot_map[key],
                            "schedule2": {
                                "schedule_id": schedule_id,
                                "project_id": project_id,
                                "project_title": project_title,
                                "classroom": classroom_name,
                                "timeslot": f"{start_time}-{end_time}"
                            }
                        })
                    else:
                        instructor_slot_map[key] = {
                            "schedule_id": schedule_id,
                            "project_id": project_id,
                            "project_title": project_title,
                            "classroom": classroom_name,
                            "timeslot": f"{start_time}-{end_time}"
                        }
        
        # Sonuçları yazdır
        print(f"Toplam {len(conflicts)} çakışma bulundu")
        print()
        
        if conflicts:
            print("=" * 100)
            print("ÇAKIŞMALAR:")
            print("=" * 100)
            
            for i, conflict in enumerate(conflicts, 1):
                print(f"\n{i}. Çakışma ({conflict['type']}):")
                if conflict['type'] == 'classroom_slot':
                    print(f"   Sınıf: {conflict['schedule1']['classroom']}")
                    print(f"   Zaman: {conflict['schedule1']['timeslot']}")
                    print(f"   Proje 1: {conflict['schedule1']['project_title']}")
                    print(f"   Proje 2: {conflict['schedule2']['project_title']}")
                elif conflict['type'] == 'instructor_slot':
                    print(f"   Instructor ID: {conflict['instructor_id']}")
                    print(f"   Zaman: {conflict['schedule1']['timeslot']}")
                    print(f"   Proje 1: {conflict['schedule1']['project_title']} ({conflict['schedule1']['classroom']})")
                    print(f"   Proje 2: {conflict['schedule2']['project_title']} ({conflict['schedule2']['classroom']})")
        else:
            print("Hic cakisma yok! Mukemmel planlama!")
        
        print()
        print("=" * 100)

if __name__ == "__main__":
    asyncio.run(check_conflicts())

