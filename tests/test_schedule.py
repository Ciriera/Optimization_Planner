"""
Schedule tests
"""
import pytest
from datetime import time, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_schedule, crud_timeslot
from app.schemas.schedule import ScheduleCreate
from app.schemas.timeslot import TimeSlotCreate
from tests.utils import create_random_classroom, create_random_project, create_random_instructor

pytestmark = pytest.mark.asyncio

class TestSchedule:
    async def test_create_timeslot(self, db_session: AsyncSession):
        """Test creating a timeslot"""
        # Saat ve dakika değerlerini ayrı ayrı oluştur
        start_time = time(hour=9, minute=0)
        end_time = time(hour=10, minute=0)
        
        timeslot_in = TimeSlotCreate(
            start_time=start_time,
            end_time=end_time,
            is_morning=True
        )
        timeslot = await crud_timeslot.create(db_session, obj_in=timeslot_in)
        
        assert timeslot.start_time.hour == 9
        assert timeslot.end_time.hour == 10
        assert timeslot.is_morning is True

    async def test_create_schedule(self, db_session: AsyncSession):
        """Test creating a schedule"""
        # Create test data
        classroom = await create_random_classroom(db_session)
        instructor = await create_random_instructor(db_session)
        project = await create_random_project(db_session, responsible_id=instructor.id)
        
        # Create timeslot
        start_time = time(hour=9, minute=0)
        end_time = time(hour=10, minute=0)
        timeslot_in = TimeSlotCreate(
            start_time=start_time,
            end_time=end_time,
            is_morning=True
        )
        timeslot = await crud_timeslot.create(db_session, obj_in=timeslot_in)
        
        # Create schedule
        schedule_in = ScheduleCreate(
            project_id=project.id,
            classroom_id=classroom.id,
            timeslot_id=timeslot.id
        )
        schedule = await crud_schedule.create(db_session, obj_in=schedule_in)
        
        assert schedule.project_id == project.id
        assert schedule.classroom_id == classroom.id
        assert schedule.timeslot_id == timeslot.id

    async def test_schedule_conflict(self, db_session: AsyncSession):
        """Test schedule conflict detection"""
        # Create test data
        classroom = await create_random_classroom(db_session)
        instructor = await create_random_instructor(db_session)
        project1 = await create_random_project(db_session, responsible_id=instructor.id)
        project2 = await create_random_project(db_session, responsible_id=instructor.id)
        
        # Create timeslot
        start_time = time(hour=9, minute=0)
        end_time = time(hour=10, minute=0)
        timeslot_in = TimeSlotCreate(
            start_time=start_time,
            end_time=end_time,
            is_morning=True
        )
        timeslot = await crud_timeslot.create(db_session, obj_in=timeslot_in)
        
        # Create first schedule
        schedule1_in = ScheduleCreate(
            project_id=project1.id,
            classroom_id=classroom.id,
            timeslot_id=timeslot.id
        )
        schedule1 = await crud_schedule.create(db_session, obj_in=schedule1_in)
        
        # Try to create second schedule with same timeslot and classroom
        schedule2_in = ScheduleCreate(
            project_id=project2.id,
            classroom_id=classroom.id,
            timeslot_id=timeslot.id
        )
        
        with pytest.raises(ValueError):
            await crud_schedule.create_with_validation(db_session, obj_in=schedule2_in)

    async def test_instructor_availability(self, db_session: AsyncSession):
        """Test instructor availability check"""
        # Create test data
        classroom = await create_random_classroom(db_session)
        instructor = await create_random_instructor(db_session)
        project1 = await create_random_project(db_session, responsible_id=instructor.id)
        project2 = await create_random_project(db_session, responsible_id=instructor.id)
        
        # Create timeslot
        start_time = time(hour=9, minute=0)
        end_time = time(hour=10, minute=0)
        timeslot_in = TimeSlotCreate(
            start_time=start_time,
            end_time=end_time,
            is_morning=True
        )
        timeslot = await crud_timeslot.create(db_session, obj_in=timeslot_in)
        
        # Create first schedule
        schedule1_in = ScheduleCreate(
            project_id=project1.id,
            classroom_id=classroom.id,
            timeslot_id=timeslot.id
        )
        schedule1 = await crud_schedule.create(db_session, obj_in=schedule1_in)
        
        # Try to create second schedule with same timeslot and instructor
        schedule2_in = ScheduleCreate(
            project_id=project2.id,
            classroom_id=classroom.id,
            timeslot_id=timeslot.id
        )
        
        with pytest.raises(ValueError):
            await crud_schedule.create_with_validation(db_session, obj_in=schedule2_in)

    async def test_get_available_timeslots(self, db_session: AsyncSession):
        """Test getting available timeslots"""
        # Create test data
        classroom = await create_random_classroom(db_session)
        
        # Create timeslots
        timeslots = []
        for hour in range(9, 12):
            start_time = time(hour=hour, minute=0)
            end_time = time(hour=hour+1, minute=0)
            timeslot_in = TimeSlotCreate(
                start_time=start_time,
                end_time=end_time,
                is_morning=True
            )
            timeslot = await crud_timeslot.create(db_session, obj_in=timeslot_in)
            timeslots.append(timeslot)
        
        # Get available timeslots
        available_timeslots = await crud_timeslot.get_available(db_session)
        assert len(available_timeslots) == len(timeslots)

    async def test_get_classroom_schedule(self, db_session: AsyncSession):
        """Test getting classroom schedule"""
        # Create test data
        classroom = await create_random_classroom(db_session)
        instructor = await create_random_instructor(db_session)
        project = await create_random_project(db_session, responsible_id=instructor.id)
        
        # Create timeslot
        start_time = time(hour=9, minute=0)
        end_time = time(hour=10, minute=0)
        timeslot_in = TimeSlotCreate(
            start_time=start_time,
            end_time=end_time,
            is_morning=True
        )
        timeslot = await crud_timeslot.create(db_session, obj_in=timeslot_in)
        
        # Create schedule
        schedule_in = ScheduleCreate(
            project_id=project.id,
            classroom_id=classroom.id,
            timeslot_id=timeslot.id
        )
        schedule = await crud_schedule.create(db_session, obj_in=schedule_in)
        
        # Get classroom schedule
        classroom_schedule = await crud_schedule.get_by_classroom(
            db_session,
            classroom_id=classroom.id
        )
        assert len(classroom_schedule) == 1
        assert classroom_schedule[0].id == schedule.id 