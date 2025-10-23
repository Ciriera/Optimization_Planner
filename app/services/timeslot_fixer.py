"""
Timeslot Structure Fixer Service
Fixes time slot structure to include proper lunch break gap (12:00-13:00)
"""

from typing import Dict, Any, List, Optional
from datetime import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

logger = logging.getLogger(__name__)


class TimeslotFixer:
    """Service for fixing timeslot structure according to project requirements"""
    
    def __init__(self):
        # Correct time slots as per project requirements
        self.correct_timeslots = [
            # Morning slots
            {"start_time": time(9, 0), "end_time": time(9, 30), "is_morning": True, "slot_name": "09:00-09:30"},
            {"start_time": time(9, 30), "end_time": time(10, 0), "is_morning": True, "slot_name": "09:30-10:00"},
            {"start_time": time(10, 0), "end_time": time(10, 30), "is_morning": True, "slot_name": "10:00-10:30"},
            {"start_time": time(10, 30), "end_time": time(11, 0), "is_morning": True, "slot_name": "10:30-11:00"},
            {"start_time": time(11, 0), "end_time": time(11, 30), "is_morning": True, "slot_name": "11:00-11:30"},
            {"start_time": time(11, 30), "end_time": time(12, 0), "is_morning": True, "slot_name": "11:30-12:00"},
            
            # Lunch break: 12:00-13:00 (NO SLOT - explicitly empty)
            
            # Afternoon slots
            {"start_time": time(13, 0), "end_time": time(13, 30), "is_morning": False, "slot_name": "13:00-13:30"},
            {"start_time": time(13, 30), "end_time": time(14, 0), "is_morning": False, "slot_name": "13:30-14:00"},
            {"start_time": time(14, 0), "end_time": time(14, 30), "is_morning": False, "slot_name": "14:00-14:30"},
            {"start_time": time(14, 30), "end_time": time(15, 0), "is_morning": False, "slot_name": "15:00-15:30"},
            {"start_time": time(15, 0), "end_time": time(15, 30), "is_morning": False, "slot_name": "15:00-15:30"},
            {"start_time": time(15, 30), "end_time": time(16, 0), "is_morning": False, "slot_name": "15:30-16:00"},
            {"start_time": time(16, 0), "end_time": time(16, 30), "is_morning": False, "slot_name": "16:00-16:30"},
            {"start_time": time(16, 30), "end_time": time(17, 0), "is_morning": False, "slot_name": "16:30-17:00"}
        ]
        
        # Lunch break definition
        self.lunch_break = {
            "start_time": time(12, 0),
            "end_time": time(13, 0),
            "is_lunch_break": True,
            "description": "Öğle arası - boş zaman dilimi"
        }
    
    async def fix_timeslot_structure(self, db: AsyncSession) -> Dict[str, Any]:
        """Zaman dilimi yapısını düzeltir"""
        
        try:
            from app.models.timeslot import TimeSlot
            
            # Mevcut timeslot'ları kontrol et
            result = await db.execute(select(TimeSlot))
            existing_timeslots = result.scalars().all()
            
            # Mevcut yapıyı analiz et
            current_analysis = self._analyze_current_structure(existing_timeslots)
            
            # Doğru yapıyı oluştur
            await self._create_correct_structure(db)
            
            # Düzeltme sonrası analiz
            result = await db.execute(select(TimeSlot))
            fixed_timeslots = result.scalars().all()
            fixed_analysis = self._analyze_current_structure(fixed_timeslots)
            
            return {
                "success": True,
                "message": "Timeslot structure fixed successfully",
                "before_analysis": current_analysis,
                "after_analysis": fixed_analysis,
                "changes_made": self._compare_structures(current_analysis, fixed_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error fixing timeslot structure: {str(e)}")
            return {
                "success": False,
                "message": f"Error fixing timeslot structure: {str(e)}"
            }
    
    def _analyze_current_structure(self, timeslots: List[Any]) -> Dict[str, Any]:
        """Mevcut timeslot yapısını analiz eder"""
        
        analysis = {
            "total_slots": len(timeslots),
            "morning_slots": 0,
            "afternoon_slots": 0,
            "lunch_break_present": False,
            "incorrect_slots": [],
            "missing_slots": [],
            "extra_slots": [],
            "structure_valid": False
        }
        
        # Mevcut slot'ları kategorize et
        existing_slots = []
        for slot in timeslots:
            slot_info = {
                "id": slot.id,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "is_morning": slot.is_morning,
                "slot_name": f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
            }
            existing_slots.append(slot_info)
            
            if slot.is_morning:
                analysis["morning_slots"] += 1
            else:
                analysis["afternoon_slots"] += 1
        
        # Lunch break kontrolü
        lunch_start = time(12, 0)
        lunch_end = time(13, 0)
        
        for slot in existing_slots:
            if slot["start_time"] == lunch_start or slot["end_time"] == lunch_end:
                analysis["lunch_break_present"] = True
                analysis["incorrect_slots"].append({
                    "slot": slot,
                    "issue": "Lunch break slot should not exist"
                })
        
        # Doğru slot'ları kontrol et
        correct_slot_names = [ts["slot_name"] for ts in self.correct_timeslots]
        existing_slot_names = [slot["slot_name"] for slot in existing_slots]
        
        # Eksik slot'lar
        for correct_slot in self.correct_timeslots:
            if correct_slot["slot_name"] not in existing_slot_names:
                analysis["missing_slots"].append(correct_slot)
        
        # Fazla slot'lar
        for existing_slot in existing_slots:
            if existing_slot["slot_name"] not in correct_slot_names:
                analysis["extra_slots"].append(existing_slot)
        
        # Yapı geçerliliği
        analysis["structure_valid"] = (
            len(analysis["missing_slots"]) == 0 and
            len(analysis["extra_slots"]) == 0 and
            not analysis["lunch_break_present"] and
            analysis["morning_slots"] == 6 and
            analysis["afternoon_slots"] == 8
        )
        
        return analysis
    
    async def _create_correct_structure(self, db: AsyncSession) -> None:
        """Doğru timeslot yapısını oluşturur"""
        
        from app.models.timeslot import TimeSlot
        
        # Mevcut timeslot'ları temizle
        await db.execute(delete(TimeSlot))
        await db.commit()
        
        # Doğru timeslot'ları oluştur
        for slot_data in self.correct_timeslots:
            timeslot = TimeSlot(
                start_time=slot_data["start_time"],
                end_time=slot_data["end_time"],
                is_morning=slot_data["is_morning"]
            )
            db.add(timeslot)
        
        await db.commit()
    
    def _compare_structures(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Yapı değişikliklerini karşılaştırır"""
        
        return {
            "slots_added": len(after["missing_slots"]) - len(before["missing_slots"]),
            "slots_removed": len(before["extra_slots"]) - len(after["extra_slots"]),
            "lunch_break_fixed": before["lunch_break_present"] and not after["lunch_break_present"],
            "structure_became_valid": not before["structure_valid"] and after["structure_valid"],
            "total_changes": abs(after["total_slots"] - before["total_slots"])
        }
    
    async def validate_timeslot_structure(self, db: AsyncSession) -> Dict[str, Any]:
        """Timeslot yapısını validate eder"""
        
        try:
            from app.models.timeslot import TimeSlot
            
            result = await db.execute(select(TimeSlot))
            timeslots = result.scalars().all()
            
            analysis = self._analyze_current_structure(timeslots)
            
            # Lunch break validation
            lunch_validation = self._validate_lunch_break(timeslots)
            
            return {
                "structure_analysis": analysis,
                "lunch_break_validation": lunch_validation,
                "overall_valid": analysis["structure_valid"] and lunch_validation["valid"],
                "recommendations": self._generate_structure_recommendations(analysis, lunch_validation)
            }
            
        except Exception as e:
            logger.error(f"Error validating timeslot structure: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating timeslot structure: {str(e)}"
            }
    
    def _validate_lunch_break(self, timeslots: List[Any]) -> Dict[str, Any]:
        """Öğle arası boşluğunu validate eder"""
        
        lunch_start = time(12, 0)
        lunch_end = time(13, 0)
        
        # Lunch break'te slot var mı kontrol et
        lunch_slots = []
        for slot in timeslots:
            if (slot.start_time < lunch_end and slot.end_time > lunch_start):
                lunch_slots.append({
                    "id": slot.id,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "overlap_type": "full" if slot.start_time >= lunch_start and slot.end_time <= lunch_end else "partial"
                })
        
        # Önceki ve sonraki slot'ları kontrol et
        previous_slot = None
        next_slot = None
        
        for slot in timeslots:
            if slot.end_time == lunch_start:
                previous_slot = slot
            if slot.start_time == lunch_end:
                next_slot = slot
        
        return {
            "valid": len(lunch_slots) == 0,
            "lunch_slots_found": lunch_slots,
            "previous_slot": {
                "exists": previous_slot is not None,
                "ends_at_lunch": previous_slot.end_time == lunch_start if previous_slot else False,
                "slot": {
                    "id": previous_slot.id,
                    "start_time": previous_slot.start_time,
                    "end_time": previous_slot.end_time
                } if previous_slot else None
            },
            "next_slot": {
                "exists": next_slot is not None,
                "starts_after_lunch": next_slot.start_time == lunch_end if next_slot else False,
                "slot": {
                    "id": next_slot.id,
                    "start_time": next_slot.start_time,
                    "end_time": next_slot.end_time
                } if next_slot else None
            },
            "lunch_break_duration": "1 hour (12:00-13:00)",
            "issues": [
                f"Found {len(lunch_slots)} slots during lunch break" if lunch_slots else None,
                "Previous slot does not end at 12:00" if previous_slot and previous_slot.end_time != lunch_start else None,
                "Next slot does not start at 13:00" if next_slot and next_slot.start_time != lunch_end else None
            ]
        }
    
    def _generate_structure_recommendations(self, analysis: Dict[str, Any], 
                                         lunch_validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Yapı önerileri üretir"""
        
        recommendations = []
        
        if not analysis["structure_valid"]:
            if analysis["missing_slots"]:
                recommendations.append({
                    "type": "missing_slots",
                    "priority": "high",
                    "message": f"Missing {len(analysis['missing_slots'])} required timeslots",
                    "action": "add_missing_slots",
                    "slots": analysis["missing_slots"]
                })
            
            if analysis["extra_slots"]:
                recommendations.append({
                    "type": "extra_slots",
                    "priority": "medium",
                    "message": f"Found {len(analysis['extra_slots'])} extra timeslots",
                    "action": "remove_extra_slots",
                    "slots": analysis["extra_slots"]
                })
        
        if not lunch_validation["valid"]:
            recommendations.append({
                "type": "lunch_break_issue",
                "priority": "high",
                "message": "Lunch break (12:00-13:00) should be empty",
                "action": "fix_lunch_break",
                "details": lunch_validation["issues"]
            })
        
        if analysis["morning_slots"] != 6:
            recommendations.append({
                "type": "morning_slots_count",
                "priority": "medium",
                "message": f"Expected 6 morning slots, found {analysis['morning_slots']}",
                "action": "adjust_morning_slots"
            })
        
        if analysis["afternoon_slots"] != 8:
            recommendations.append({
                "type": "afternoon_slots_count",
                "priority": "medium",
                "message": f"Expected 8 afternoon slots, found {analysis['afternoon_slots']}",
                "action": "adjust_afternoon_slots"
            })
        
        return recommendations
    
    async def get_timeslot_schedule_template(self) -> Dict[str, Any]:
        """Doğru zaman dilimi şablonunu döndürür"""
        
        return {
            "schedule_template": {
                "morning_session": {
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "duration": "3 hours",
                    "slots": [
                        {"time": "09:00-09:30", "is_morning": True},
                        {"time": "09:30-10:00", "is_morning": True},
                        {"time": "10:00-10:30", "is_morning": True},
                        {"time": "10:30-11:00", "is_morning": True},
                        {"time": "11:00-11:30", "is_morning": True},
                        {"time": "11:30-12:00", "is_morning": True}
                    ]
                },
                "lunch_break": {
                    "start_time": "12:00",
                    "end_time": "13:00",
                    "duration": "1 hour",
                    "description": "Öğle arası - boş zaman dilimi",
                    "is_available": False
                },
                "afternoon_session": {
                    "start_time": "13:00",
                    "end_time": "17:00",
                    "duration": "4 hours",
                    "slots": [
                        {"time": "13:00-13:30", "is_morning": False},
                        {"time": "13:30-14:00", "is_morning": False},
                        {"time": "14:00-14:30", "is_morning": False},
                        {"time": "14:30-15:00", "is_morning": False},
                        {"time": "15:00-15:30", "is_morning": False},
                        {"time": "15:30-16:00", "is_morning": False},
                        {"time": "16:00-16:30", "is_morning": False},
                        {"time": "16:30-17:00", "is_morning": False}
                    ]
                }
            },
            "total_available_slots": 14,
            "total_working_hours": 7,  # 3 morning + 4 afternoon
            "lunch_break_hours": 1
        }
