"""
Availability schema tests
"""
import pytest
from datetime import date

from app.schemas.availability import TimeSlotInfo, InstructorAvailability

def test_timeslot_info_schema():
    """Test TimeSlotInfo schema"""
    data = {
        "id": 1,
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "is_morning": True
    }
    slot = TimeSlotInfo(**data)
    assert slot.id == data["id"]
    assert slot.start_time == data["start_time"]
    assert slot.end_time == data["end_time"]
    assert slot.is_morning == data["is_morning"]

def test_instructor_availability_schema():
    """Test InstructorAvailability schema"""
    slot1 = TimeSlotInfo(id=1, start_time="09:00:00", end_time="10:00:00", is_morning=True)
    slot2 = TimeSlotInfo(id=2, start_time="10:00:00", end_time="11:00:00", is_morning=True)
    slot3 = TimeSlotInfo(id=3, start_time="14:00:00", end_time="15:00:00", is_morning=False)
    
    data = {
        "instructor_id": 1,
        "date": date.today().isoformat(),
        "busy_slots": [slot1, slot2],
        "available_slots": [slot3]
    }
    
    availability = InstructorAvailability(**data)
    assert availability.instructor_id == data["instructor_id"]
    assert availability.date == data["date"]
    assert len(availability.busy_slots) == 2
    assert len(availability.available_slots) == 1
    assert availability.busy_slots[0].id == slot1.id
    assert availability.available_slots[0].id == slot3.id
