"""
Dynamic Programming Algorithm - Juri Uyeleri Kontrolu
"""
import asyncio
from sqlalchemy import text
from app.db.base import async_session
import json

async def check_jury_members():
    """DP algoritması sonuçlarında jüri üyelerini kontrol et"""
    
    async with async_session() as db:
        # Schedules tablosundan ilk 10 atamayı al
        result = await db.execute(text("""
            SELECT 
                s.id,
                s.project_id,
                p.title as project_title,
                s.classroom_id,
                c.name as classroom_name,
                s.timeslot_id,
                t.start_time,
                s.instructors
            FROM schedules s
            JOIN projects p ON s.project_id = p.id
            JOIN classrooms c ON s.classroom_id = c.id
            JOIN timeslots t ON s.timeslot_id = t.id
            ORDER BY t.start_time, c.name
            LIMIT 10
        """))
        
        schedules = result.fetchall()
        
        print("=" * 100)
        print("DYNAMIC PROGRAMMING - JURI UYELERI KONTROLU")
        print("=" * 100)
        print(f"Toplam kontrol edilen atama: {len(schedules)}")
        print()
        
        # Instructor bilgilerini al
        instructor_result = await db.execute(text("SELECT id, name FROM instructors"))
        instructors_dict = {row[0]: row[1] for row in instructor_result.fetchall()}
        
        for schedule in schedules:
            schedule_id, project_id, project_title, classroom_id, classroom_name, timeslot_id, start_time, instructors_json = schedule
            
            print(f"\nProje: {project_title}")
            print(f"Sinif: {classroom_name}, Zaman: {start_time}")
            
            if instructors_json:
                # JSON array'i parse et
                try:
                    if isinstance(instructors_json, str):
                        instructors_list = json.loads(instructors_json)
                    else:
                        instructors_list = instructors_json
                    
                    print(f"Instructors: {instructors_list}")
                    
                    if len(instructors_list) >= 1:
                        print(f"  - Sorumlu: {instructors_dict.get(instructors_list[0], 'BILINMIYOR')} (ID: {instructors_list[0]})")
                    if len(instructors_list) >= 2:
                        print(f"  - Juri: {instructors_dict.get(instructors_list[1], 'BILINMIYOR')} (ID: {instructors_list[1]})")
                    if len(instructors_list) > 2:
                        print(f"  - Diger Juriler: {', '.join([str(x) for x in instructors_list[2:]])}")
                    
                    if len(instructors_list) < 2:
                        print("  [UYARI] Juri uyesi eksik!")
                except Exception as e:
                    print(f"  [HATA] JSON parse hatasi: {e}")
            else:
                print("  [UYARI] Instructors alani bos!")
        
        print()
        print("=" * 100)

if __name__ == "__main__":
    asyncio.run(check_jury_members())

