#!/usr/bin/env python3
"""
Detaylı gap analizi - gap'ların nerede olduğunu gösterir
"""

import asyncio
import sys
import os
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Proje kök dizinini Python path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import get_db
from app.models.schedule import Schedule
from app.models.timeslot import TimeSlot
from app.models.instructor import Instructor
from app.models.project import Project
from app.models.classroom import Classroom

async def analyze_gaps_detailed():
    """Detaylı gap analizi yapar"""
    print("Detaylı gap analizi başlatılıyor...")
    
    async for db in get_db():
        try:
            # Tüm schedule'ları al (timeslot bilgileri ile birlikte)
            result = await db.execute(
                select(Schedule, TimeSlot, Project)
                .join(TimeSlot, Schedule.timeslot_id == TimeSlot.id)
                .join(Project, Schedule.project_id == Project.id)
                .join(Classroom, Schedule.classroom_id == Classroom.id)
                .order_by(Schedule.timeslot_id)
            )
            schedule_data = result.all()
            
            print(f"Toplam schedule sayısı: {len(schedule_data)}")
            
            # Instructor'lara göre grupla (project üzerinden)
            instructor_schedules = {}
            for schedule, timeslot, project in schedule_data:
                if project and project.responsible_id:
                    instructor_id = project.responsible_id
                    if instructor_id not in instructor_schedules:
                        instructor_schedules[instructor_id] = []
                    instructor_schedules[instructor_id].append((schedule, timeslot, project))
            
            print(f"Toplam instructor sayısı: {len(instructor_schedules)}")
            
            # Her instructor için gap analizi yap
            total_gaps = 0
            for instructor_id, schedule_data_list in instructor_schedules.items():
                print(f"\n--- Instructor {instructor_id} ---")
                print(f"Toplam atama: {len(schedule_data_list)}")
                
                # Timeslot'ları sırala
                sorted_schedules = sorted(schedule_data_list, key=lambda x: x[1].start_time)
                
                # Gap'ları tespit et
                gaps = []
                for i in range(len(sorted_schedules) - 1):
                    current_slot = sorted_schedules[i][1]  # timeslot
                    next_slot = sorted_schedules[i + 1][1]  # timeslot
                    
                    # Eğer aralarında boş slot varsa gap var
                    if current_slot.end_time != next_slot.start_time:
                        # Time objelerini datetime'a çevir
                        from datetime import datetime, date
                        current_end = datetime.combine(date.today(), current_slot.end_time)
                        next_start = datetime.combine(date.today(), next_slot.start_time)
                        
                        gap_info = {
                            'instructor_id': instructor_id,
                            'current_slot': f"{current_slot.start_time.strftime('%H:%M')}-{current_slot.end_time.strftime('%H:%M')}",
                            'next_slot': f"{next_slot.start_time.strftime('%H:%M')}-{next_slot.end_time.strftime('%H:%M')}",
                            'gap_duration': (next_start - current_end).total_seconds() / 60
                        }
                        gaps.append(gap_info)
                        total_gaps += 1
                
                print(f"Gap sayısı: {len(gaps)}")
                for gap in gaps[:5]:  # İlk 5 gap'i göster
                    print(f"  Gap: {gap['current_slot']} -> {gap['next_slot']} (süre: {gap['gap_duration']} dk)")
                
                if len(gaps) > 5:
                    print(f"  ... ve {len(gaps) - 5} gap daha")
            
            print(f"\n=== ÖZET ===")
            print(f"Toplam gap sayısı: {total_gaps}")
            print(f"Ortalama gap per instructor: {total_gaps / len(instructor_schedules):.2f}")
            
            # En çok gap olan instructor'ları göster
            instructor_gap_counts = {}
            for instructor_id, schedule_data_list in instructor_schedules.items():
                sorted_schedules = sorted(schedule_data_list, key=lambda x: x[1].start_time)
                gaps = 0
                for i in range(len(sorted_schedules) - 1):
                    current_slot = sorted_schedules[i][1]  # timeslot
                    next_slot = sorted_schedules[i + 1][1]  # timeslot
                    if current_slot.end_time != next_slot.start_time:
                        gaps += 1
                instructor_gap_counts[instructor_id] = gaps
            
            # En çok gap olan 5 instructor'ı göster
            top_gap_instructors = sorted(instructor_gap_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\nEn çok gap olan instructor'lar:")
            for instructor_id, gap_count in top_gap_instructors:
                print(f"  Instructor {instructor_id}: {gap_count} gap")
            
        except Exception as e:
            print(f"Hata: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(analyze_gaps_detailed())