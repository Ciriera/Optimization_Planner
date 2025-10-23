"""
Rules enforcement service for optimization constraints
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schedule import Schedule
from app.models.project import Project
from app.models.instructor import Instructor
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.core.config import settings


class RulesService:
    """Service for enforcing optimization rules and constraints."""
    
    def __init__(self):
        # Configuration parameters
        self.min_class_count = getattr(settings, 'MIN_CLASS_COUNT', 5)
        self.max_class_count = getattr(settings, 'MAX_CLASS_COUNT', 7)
        self.min_instructors_bitirme = getattr(settings, 'MIN_INSTRUCTORS_BITIRME', 2)
        self.min_instructors_ara = getattr(settings, 'MIN_INSTRUCTORS_ARA', 1)
        
    async def validate_solution_feasibility(self, db: AsyncSession, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate if a solution satisfies all feasibility constraints.
        
        Args:
            db: Database session
            solution: Proposed solution
            
        Returns:
            Validation result with violations
        """
        violations = []
        warnings = []
        
        # Get current data
        result = await db.execute(select(Project))
        projects = result.scalars().all()
        
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        result = await db.execute(select(Classroom))
        classrooms = result.scalars().all()
        
        result = await db.execute(select(TimeSlot))
        timeslots = result.scalars().all()
        
        # Check basic constraints
        violations.extend(await self._check_class_count_constraints(solution, projects))
        violations.extend(await self._check_instructor_constraints(solution, projects, instructors))
        violations.extend(await self._check_slot_conflicts(solution))
        violations.extend(await self._check_classroom_capacity(solution, classrooms))
        violations.extend(await self._check_time_block_constraints(solution))
        
        # Check warnings (non-blocking issues)
        warnings.extend(self._check_load_balance_warnings(solution, instructors))
        warnings.extend(self._check_preference_warnings(solution, projects, instructors))
        
        is_feasible = len(violations) == 0
        
        return {
            "is_feasible": is_feasible,
            "violations": violations,
            "warnings": warnings,
            "violation_count": len(violations),
            "warning_count": len(warnings)
        }
    
    async def _check_class_count_constraints(self, solution: List[Dict[str, Any]], projects: List[Project]) -> List[Dict[str, Any]]:
        """Check minimum/maximum class count constraints."""
        violations = []
        
        # Count classes by type
        bitirme_classes = set()
        ara_classes = set()
        
        for assignment in solution:
            project = next((p for p in projects if p.id == assignment["project_id"]), None)
            if project:
                if project.type == "bitirme":
                    bitirme_classes.add(assignment["classroom_id"])
                else:
                    ara_classes.add(assignment["classroom_id"])
        
        # Check minimum class count
        total_classes = len(bitirme_classes) + len(ara_classes)
        if total_classes < self.min_class_count:
            violations.append({
                "type": "min_class_count",
                "message": f"Total classes ({total_classes}) below minimum ({self.min_class_count})",
                "current": total_classes,
                "required": self.min_class_count
            })
        
        if total_classes > self.max_class_count:
            violations.append({
                "type": "max_class_count", 
                "message": f"Total classes ({total_classes}) above maximum ({self.max_class_count})",
                "current": total_classes,
                "required": self.max_class_count
            })
        
        return violations
    
    async def _check_instructor_constraints(self, solution: List[Dict[str, Any]], projects: List[Project], instructors: List[Instructor]) -> List[Dict[str, Any]]:
        """Check instructor assignment constraints."""
        violations = []
        
        for assignment in solution:
            project = next((p for p in projects if p.id == assignment["project_id"]), None)
            if project:
                assigned_instructors = assignment.get("instructors", [])
                required_count = self.min_instructors_bitirme if project.type == "bitirme" else self.min_instructors_ara
                
                if len(assigned_instructors) < required_count:
                    violations.append({
                        "type": "insufficient_instructors",
                        "message": f"Project {project.id} ({project.type}) needs {required_count} instructors, has {len(assigned_instructors)}",
                        "project_id": project.id,
                        "project_type": project.type,
                        "current": len(assigned_instructors),
                        "required": required_count
                    })
                
                # Check if instructors are available (simplified check)
                for instructor_id in assigned_instructors:
                    instructor = next((i for i in instructors if i.id == instructor_id), None)
                    if not instructor:
                        violations.append({
                            "type": "invalid_instructor",
                            "message": f"Instructor {instructor_id} not found for project {project.id}",
                            "project_id": project.id,
                            "instructor_id": instructor_id
                        })
        
        return violations
    
    async def _check_slot_conflicts(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for classroom-timeslot conflicts."""
        violations = []
        used_slots = {}
        
        for assignment in solution:
            slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
            if slot_key in used_slots:
                violations.append({
                    "type": "slot_conflict",
                    "message": f"Multiple projects assigned to classroom {assignment['classroom_id']}, timeslot {assignment['timeslot_id']}",
                    "classroom_id": assignment["classroom_id"],
                    "timeslot_id": assignment["timeslot_id"],
                    "conflicting_project": assignment["project_id"],
                    "original_project": used_slots[slot_key]
                })
            else:
                used_slots[slot_key] = assignment["project_id"]
        
        return violations
    
    async def _check_classroom_capacity(self, solution: List[Dict[str, Any]], classrooms: List[Classroom]) -> List[Dict[str, Any]]:
        """Check classroom capacity constraints."""
        violations = []
        classroom_usage = {}
        
        # Count projects per classroom
        for assignment in solution:
            classroom_id = assignment["classroom_id"]
            classroom_usage[classroom_id] = classroom_usage.get(classroom_id, 0) + 1
        
        # Check capacity
        for classroom in classrooms:
            usage = classroom_usage.get(classroom.id, 0)
            capacity = classroom.capacity or 20  # Default capacity
            
            if usage > capacity:
                violations.append({
                    "type": "capacity_exceeded",
                    "message": f"Classroom {classroom.id} usage ({usage}) exceeds capacity ({capacity})",
                    "classroom_id": classroom.id,
                    "usage": usage,
                    "capacity": capacity
                })
        
        return violations
    
    async def _check_time_block_constraints(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check time block constraints (no gaps, same classroom preference)."""
        violations = []
        
        # Group assignments by instructor
        instructor_schedules = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_schedules:
                    instructor_schedules[instructor_id] = []
                instructor_schedules[instructor_id].append(assignment)
        
        # Check for gaps and classroom changes
        for instructor_id, assignments in instructor_schedules.items():
            if len(assignments) > 1:
                # Sort by timeslot
                sorted_assignments = sorted(assignments, key=lambda x: x["timeslot_id"])
                
                # Check for gaps
                for i in range(1, len(sorted_assignments)):
                    current_slot = sorted_assignments[i]["timeslot_id"]
                    previous_slot = sorted_assignments[i-1]["timeslot_id"]
                    
                    if current_slot - previous_slot > 1:
                        violations.append({
                            "type": "time_gap",
                            "message": f"Instructor {instructor_id} has gap between timeslots {previous_slot} and {current_slot}",
                            "instructor_id": instructor_id,
                            "previous_timeslot": previous_slot,
                            "current_timeslot": current_slot
                        })
                
                # Check for excessive classroom changes
                classroom_changes = 0
                current_classroom = sorted_assignments[0]["classroom_id"]
                for assignment in sorted_assignments[1:]:
                    if assignment["classroom_id"] != current_classroom:
                        classroom_changes += 1
                        current_classroom = assignment["classroom_id"]
                
                # Warning for too many classroom changes (not a violation)
                if classroom_changes > 3:  # Threshold for warnings
                    violations.append({
                        "type": "excessive_classroom_changes",
                        "message": f"Instructor {instructor_id} has {classroom_changes} classroom changes",
                        "instructor_id": instructor_id,
                        "changes": classroom_changes
                    })
        
        return violations
    
    def _check_load_balance_warnings(self, solution: List[Dict[str, Any]], instructors: List[Instructor]) -> List[Dict[str, Any]]:
        """Check for load balance issues (warnings, not violations)."""
        warnings = []
        
        # Calculate instructor loads
        instructor_loads = {}
        for instructor in instructors:
            instructor_loads[instructor.id] = 0
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id in instructor_loads:
                    instructor_loads[instructor_id] += 1
        
        # Check for unbalanced loads
        loads = [load for load in instructor_loads.values() if load > 0]
        if loads:
            avg_load = sum(loads) / len(loads)
            max_load = max(loads)
            min_load = min(loads)
            
            if max_load - min_load > avg_load * 0.5:  # 50% deviation from average
                warnings.append({
                    "type": "load_imbalance",
                    "message": f"Significant load imbalance detected: min={min_load}, max={max_load}, avg={avg_load:.1f}",
                    "min_load": min_load,
                    "max_load": max_load,
                    "avg_load": avg_load
                })
        
        return warnings
    
    def _check_preference_warnings(self, solution: List[Dict[str, Any]], projects: List[Project], instructors: List[Instructor]) -> List[Dict[str, Any]]:
        """Check for instructor preference violations (warnings)."""
        warnings = []
        
        # This is a placeholder for preference checking
        # Real implementation would check actual instructor preferences
        
        return warnings
    
    async def apply_constraints_to_solution(self, db: AsyncSession, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply constraint corrections to a solution to make it feasible.
        
        Args:
            db: Database session
            solution: Original solution
            
        Returns:
            Corrected solution
        """
        corrected_solution = [assignment.copy() for assignment in solution]
        
        # Get current data
        result = await db.execute(select(Project))
        projects = result.scalars().all()
        
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        result = await db.execute(select(Classroom))
        classrooms = result.scalars().all()
        
        result = await db.execute(select(TimeSlot))
        timeslots = result.scalars().all()
        
        # Fix instructor assignments
        corrected_solution = self._fix_instructor_assignments(corrected_solution, projects, instructors)
        
        # Fix slot conflicts
        corrected_solution = self._fix_slot_conflicts(corrected_solution, classrooms, timeslots)
        
        return corrected_solution
    
    def _fix_instructor_assignments(self, solution: List[Dict[str, Any]], projects: List[Project], instructors: List[Instructor]) -> List[Dict[str, Any]]:
        """Fix insufficient instructor assignments."""
        # Get available instructors by type
        prof_instructors = [i for i in instructors if i.type and 'prof' in i.type.lower()]
        other_instructors = [i for i in instructors if not i.type or 'prof' not in i.type.lower()]
        
        for assignment in solution:
            project = next((p for p in projects if p.id == assignment["project_id"]), None)
            if project:
                required_count = self.min_instructors_bitirme if project.type == "bitirme" else self.min_instructors_ara
                current_instructors = assignment.get("instructors", [])
                
                # Add instructors if needed
                while len(current_instructors) < required_count:
                    # Prefer professors for bitirme projects
                    if project.type == "bitirme" and prof_instructors:
                        instructor = prof_instructors[0]
                        prof_instructors.pop(0)
                    elif other_instructors:
                        instructor = other_instructors[0]
                        other_instructors.pop(0)
                    else:
                        break  # No more instructors available
                    
                    if instructor.id not in current_instructors:
                        current_instructors.append(instructor.id)
                
                assignment["instructors"] = current_instructors
        
        return solution
    
    def _fix_slot_conflicts(self, solution: List[Dict[str, Any]], classrooms: List[Classroom], timeslots: List[TimeSlot]) -> List[Dict[str, Any]]:
        """Fix classroom-timeslot conflicts by reassigning conflicting projects."""
        used_slots = {}
        fixed_solution = []
        
        for assignment in solution:
            slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
            
            if slot_key not in used_slots:
                used_slots[slot_key] = assignment["project_id"]
                fixed_solution.append(assignment)
            else:
                # Find alternative slot
                alternative_found = False
                for classroom in classrooms:
                    for timeslot in timeslots:
                        alt_slot_key = (classroom.id, timeslot.id)
                        if alt_slot_key not in used_slots:
                            assignment["classroom_id"] = classroom.id
                            assignment["timeslot_id"] = timeslot.id
                            used_slots[alt_slot_key] = assignment["project_id"]
                            fixed_solution.append(assignment)
                            alternative_found = True
                            break
                    if alternative_found:
                        break
                
                if not alternative_found:
                    # No alternative found, keep original (will be a violation)
                    fixed_solution.append(assignment)
        
        return fixed_solution
    
    def get_configurable_constraints(self) -> Dict[str, Any]:
        """Get current configurable constraint values."""
        return {
            "min_class_count": self.min_class_count,
            "max_class_count": self.max_class_count,
            "min_instructors_bitirme": self.min_instructors_bitirme,
            "min_instructors_ara": self.min_instructors_ara,
            "description": {
                "min_class_count": "Minimum number of classes to be scheduled",
                "max_class_count": "Maximum number of classes to be scheduled", 
                "min_instructors_bitirme": "Minimum instructors required for bitirme projects",
                "min_instructors_ara": "Minimum instructors required for ara projects"
            }
        }
    
    def update_constraints(self, new_constraints: Dict[str, Any]) -> None:
        """Update constraint values."""
        if "min_class_count" in new_constraints:
            self.min_class_count = new_constraints["min_class_count"]
        if "max_class_count" in new_constraints:
            self.max_class_count = new_constraints["max_class_count"]
        if "min_instructors_bitirme" in new_constraints:
            self.min_instructors_bitirme = new_constraints["min_instructors_bitirme"]
        if "min_instructors_ara" in new_constraints:
            self.min_instructors_ara = new_constraints["min_instructors_ara"]
