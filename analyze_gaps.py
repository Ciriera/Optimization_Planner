#!/usr/bin/env python3
import sys
import asyncio
sys.path.append('.')

from app.db.base import async_session
from app.models.schedule import Schedule
from app.models.timeslot import TimeSlot
from app.models.project import Project
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def analyze_gaps():
    async with async_session() as db:
        # Tüm schedule'ları instructor'lara göre grupla
        result = await db.execute(
            select(Schedule)
            .options(selectinload(Schedule.timeslot))
            .options(selectinload(Schedule.project))
        )
        schedules = result.scalars().all()

        # Instructor bazında grupla
        instructor_schedules = {}
        for schedule in schedules:
            if schedule.project and schedule.timeslot:
                instructor_id = schedule.project.responsible_id
                if instructor_id not in instructor_schedules:
                    instructor_schedules[instructor_id] = []

                instructor_schedules[instructor_id].append({
                    'timeslot_id': schedule.timeslot_id,
                    'time_range': schedule.timeslot.time_range,
                    'project_title': schedule.project.title
                })

        print(f'Gap analizi için {len(instructor_schedules)} instructor inceleniyor:')
        total_gaps = 0
        problematic_instructors = []

        for instructor_id, assignments in instructor_schedules.items():
            # Zaman sırasına göre sırala
            assignments.sort(key=lambda x: x['timeslot_id'])

            gaps = 0
            gap_details = []

            for i in range(len(assignments) - 1):
                current_slot = assignments[i]['timeslot_id']
                next_slot = assignments[i + 1]['timeslot_id']
                gap_size = next_slot - current_slot

                if gap_size > 1:
                    gaps += 1
                    gap_details.append({
                        'from': assignments[i]['time_range'],
                        'to': assignments[i + 1]['time_range'],
                        'gap_size': gap_size - 1,
                        'project_from': assignments[i]['project_title'],
                        'project_to': assignments[i + 1]['project_title']
                    })

            if gaps > 0:
                total_gaps += gaps
                problematic_instructors.append({
                    'instructor_id': instructor_id,
                    'gaps': gaps,
                    'gap_details': gap_details
                })
                print(f'Instructor {instructor_id}: {gaps} gap')
                for gap in gap_details[:3]:  # İlk 3 gap'ı göster
                    print(f'  Gap: {gap["from"]} -> {gap["to"]} (boyut: {gap["gap_size"]})')
                    print(f'    {gap["project_from"]} -> {gap["project_to"]}')

        print(f'TOPLAM GAP SAYISI: {total_gaps}')
        print(f'SORUNLU INSTRUCTOR SAYISI: {len(problematic_instructors)}')

        return problematic_instructors, total_gaps

if __name__ == "__main__":
    asyncio.run(analyze_gaps())
