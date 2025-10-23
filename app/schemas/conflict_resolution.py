"""
🔧 CONFLICT RESOLUTION SCHEMAS
Conflict resolution API için Pydantic şemaları
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class ConflictResolutionRequest(BaseModel):
    """Conflict resolution isteği"""
    auto_resolve: bool = Field(default=True, description="Otomatik çözüm yapılsın mı?")
    resolution_strategy: Optional[str] = Field(default=None, description="Çözüm stratejisi")
    preserve_assignments: bool = Field(default=True, description="Mevcut atamaları koru")
    
    class Config:
        schema_extra = {
            "example": {
                "auto_resolve": True,
                "resolution_strategy": "smart_reschedule",
                "preserve_assignments": True
            }
        }

class ConflictInfo(BaseModel):
    """Çakışma bilgisi"""
    type: str = Field(description="Çakışma türü")
    instructor_id: Optional[int] = Field(default=None, description="Instructor ID")
    timeslot_id: Optional[int] = Field(default=None, description="Zaman dilimi ID")
    classroom_id: Optional[int] = Field(default=None, description="Sınıf ID")
    conflict_count: int = Field(description="Çakışma sayısı")
    severity: str = Field(description="Çakışma şiddeti")
    description: str = Field(description="Çakışma açıklaması")
    resolution_strategy: str = Field(description="Çözüm stratejisi")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "instructor_supervisor_jury_conflict",
                "instructor_id": 3,
                "timeslot_id": 14,
                "conflict_count": 2,
                "severity": "HIGH",
                "description": "Instructor 3 has 2 assignments in timeslot 14",
                "resolution_strategy": "reschedule_one_assignment"
            }
        }

class ResolutionLog(BaseModel):
    """Çözüm log bilgisi"""
    conflict_id: str = Field(description="Çakışma ID")
    resolution_strategy: str = Field(description="Çözüm stratejisi")
    success: bool = Field(description="Başarılı mı?")
    changes_made: List[Dict[str, Any]] = Field(default=[], description="Yapılan değişiklikler")
    error: Optional[str] = Field(default=None, description="Hata mesajı")
    description: str = Field(description="Çözüm açıklaması")
    
    class Config:
        schema_extra = {
            "example": {
                "conflict_id": "instructor_supervisor_jury_conflict",
                "resolution_strategy": "reschedule_one_assignment",
                "success": True,
                "changes_made": [
                    {
                        "project_id": 5,
                        "old_timeslot": 14,
                        "new_timeslot": 15,
                        "action": "rescheduled"
                    }
                ],
                "description": "Successfully resolved instructor_supervisor_jury_conflict"
            }
        }

class ConflictResolutionResponse(BaseModel):
    """Conflict resolution yanıtı"""
    success: bool = Field(description="Başarılı mı?")
    conflicts_detected: int = Field(description="Tespit edilen çakışma sayısı")
    conflicts_resolved: int = Field(description="Çözülen çakışma sayısı")
    remaining_conflicts: int = Field(description="Kalan çakışma sayısı")
    resolution_log: List[ResolutionLog] = Field(description="Çözüm logları")
    resolved_assignments: List[Dict[str, Any]] = Field(default=[], description="Çözülen atamalar")
    message: str = Field(description="Yanıt mesajı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "conflicts_detected": 3,
                "conflicts_resolved": 2,
                "remaining_conflicts": 1,
                "resolution_log": [
                    {
                        "conflict_id": "instructor_supervisor_jury_conflict",
                        "resolution_strategy": "reschedule_one_assignment",
                        "success": True,
                        "changes_made": [
                            {
                                "project_id": 5,
                                "old_timeslot": 14,
                                "new_timeslot": 15,
                                "action": "rescheduled"
                            }
                        ],
                        "description": "Successfully resolved instructor_supervisor_jury_conflict"
                    }
                ],
                "message": "2/3 çakışma çözüldü"
            }
        }

class ConflictStatistics(BaseModel):
    """Çakışma istatistikleri"""
    total_assignments: int = Field(description="Toplam atama sayısı")
    total_conflicts: int = Field(description="Toplam çakışma sayısı")
    conflict_rate: float = Field(description="Çakışma oranı")
    conflict_types: Dict[str, int] = Field(description="Çakışma türü dağılımı")
    severity_breakdown: Dict[str, int] = Field(description="Şiddet dağılımı")
    most_problematic_instructors: List[Dict[str, Any]] = Field(description="En problemli instructor'lar")
    most_problematic_timeslots: List[Dict[str, Any]] = Field(description="En problemli zaman dilimleri")
    most_problematic_classrooms: List[Dict[str, Any]] = Field(description="En problemli sınıflar")
    
    class Config:
        schema_extra = {
            "example": {
                "total_assignments": 50,
                "total_conflicts": 3,
                "conflict_rate": 0.06,
                "conflict_types": {
                    "instructor_supervisor_jury_conflict": 2,
                    "classroom_double_booking": 1
                },
                "severity_breakdown": {
                    "HIGH": 2,
                    "MEDIUM": 1
                },
                "most_problematic_instructors": [
                    {
                        "instructor_id": 3,
                        "conflict_count": 2,
                        "conflict_types": ["instructor_supervisor_jury_conflict"]
                    }
                ],
                "most_problematic_timeslots": [
                    {
                        "timeslot_id": 14,
                        "conflict_count": 2,
                        "time_range": "14:30-15:00"
                    }
                ],
                "most_problematic_classrooms": []
            }
        }
