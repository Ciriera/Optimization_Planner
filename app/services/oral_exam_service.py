"""
Oral exam planning service for scheduling oral examinations
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

# Models are not directly used, we work with dict data


class OralExamService:
    """
    Service for planning and scheduling oral examinations
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Oral exam specific settings
        self.exam_duration = 30  # minutes per exam
        self.prep_time = 10  # minutes preparation time between exams
        self.break_duration = 15  # minutes break duration
        self.max_exams_per_day = 12  # maximum exams per day
        self.max_exams_per_instructor = 8  # maximum exams per instructor per day
    
    def plan_oral_exams(self, projects: List[Dict[str, Any]], 
                       instructors: List[Dict[str, Any]],
                       classrooms: List[Dict[str, Any]],
                       timeslots: List[Dict[str, Any]],
                       constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Plan oral examinations for projects.
        
        Args:
            projects: List of projects requiring oral exams
            instructors: List of available instructors
            classrooms: List of available classrooms
            timeslots: List of available timeslots
            constraints: Additional planning constraints
            
        Returns:
            Oral exam schedule with detailed planning
        """
        try:
            constraints = constraints or {}
            
            # Analyze requirements
            exam_requirements = self._analyze_exam_requirements(projects)
            
            # Generate exam schedule
            schedule = self._generate_exam_schedule(
                exam_requirements, instructors, classrooms, timeslots, constraints
            )
            
            # Calculate schedule metrics
            metrics = self._calculate_schedule_metrics(schedule, exam_requirements)
            
            # Generate conflict analysis
            conflicts = self._analyze_conflicts(schedule)
            
            return {
                "status": "success",
                "schedule": schedule,
                "metrics": metrics,
                "conflicts": conflicts,
                "total_exams": len(projects),
                "total_instructors": len(instructors),
                "total_classrooms": len(classrooms),
                "planning_algorithm": "constraint_based_scheduling",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Oral exam planning failed: {str(e)}",
                "schedule": [],
                "metrics": {},
                "conflicts": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _analyze_exam_requirements(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze oral exam requirements for each project."""
        requirements = {}
        
        for project in projects:
            project_id = project.get("id")
            project_type = project.get("type", "ara")
            
            # Determine exam requirements
            if project_type == "bitirme":
                required_instructors = 3  # Advisor + 2 jury members
                exam_duration = 45  # Longer for thesis
                preparation_time = 15
            else:  # ara project
                required_instructors = 2  # Advisor + 1 jury member
                exam_duration = 30
                preparation_time = 10
            
            requirements[project_id] = {
                "project_id": project_id,
                "project_type": project_type,
                "project_title": project.get("title", ""),
                "advisor_id": project.get("advisor_id"),
                "jury_members": project.get("jury_members", []),
                "required_instructors": required_instructors,
                "exam_duration": exam_duration,
                "preparation_time": preparation_time,
                "total_time_needed": exam_duration + preparation_time,
                "priority": self._calculate_exam_priority(project),
                "special_requirements": self._extract_special_requirements(project)
            }
        
        return requirements
    
    def _calculate_exam_priority(self, project: Dict[str, Any]) -> int:
        """Calculate exam priority based on project characteristics."""
        priority = 5  # Base priority
        
        project_type = project.get("type", "ara")
        if project_type == "bitirme":
            priority += 2  # Higher priority for thesis
        
        # Check for deadlines
        deadline = project.get("deadline")
        if deadline:
            try:
                deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                days_until_deadline = (deadline_date - datetime.utcnow()).days
                if days_until_deadline < 7:
                    priority += 3  # Urgent
                elif days_until_deadline < 14:
                    priority += 2  # High priority
                elif days_until_deadline < 30:
                    priority += 1  # Medium priority
            except:
                pass  # Invalid deadline format
        
        return min(priority, 10)  # Cap at 10
    
    def _extract_special_requirements(self, project: Dict[str, Any]) -> List[str]:
        """Extract special requirements for oral exams."""
        requirements = []
        
        # Check for special equipment needs
        if "presentation" in project.get("description", "").lower():
            requirements.append("projector")
        
        if "demo" in project.get("description", "").lower():
            requirements.append("demo_equipment")
        
        if "software" in project.get("description", "").lower():
            requirements.append("computer_access")
        
        # Check for specific time requirements
        if "morning" in project.get("preferences", "").lower():
            requirements.append("morning_slot")
        
        if "afternoon" in project.get("preferences", "").lower():
            requirements.append("afternoon_slot")
        
        return requirements
    
    def _generate_exam_schedule(self, requirements: Dict[str, Any],
                              instructors: List[Dict[str, Any]],
                              classrooms: List[Dict[str, Any]],
                              timeslots: List[Dict[str, Any]],
                              constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate the actual exam schedule."""
        schedule = []
        
        # Sort projects by priority
        sorted_projects = sorted(
            requirements.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        )
        
        # Track resource usage
        instructor_schedule = {}
        classroom_schedule = {}
        timeslot_schedule = {}
        
        # Initialize tracking
        for instructor in instructors:
            instructor_schedule[instructor["id"]] = {}
        
        for classroom in classrooms:
            classroom_schedule[classroom["id"]] = {}
        
        for timeslot in timeslots:
            timeslot_schedule[timeslot["id"]] = {
                "start_time": timeslot.get("start_time"),
                "end_time": timeslot.get("end_time"),
                "available": True,
                "exam_count": 0
            }
        
        # Schedule each project
        for project_id, requirement in sorted_projects:
            exam_slot = self._find_available_slot(
                requirement, instructor_schedule, classroom_schedule,
                timeslot_schedule, constraints
            )
            
            if exam_slot:
                # Create exam entry
                exam_entry = {
                    "project_id": project_id,
                    "project_title": requirement["project_title"],
                    "project_type": requirement["project_type"],
                    "exam_date": exam_slot["date"],
                    "exam_time": exam_slot["time"],
                    "duration": requirement["exam_duration"],
                    "classroom_id": exam_slot["classroom_id"],
                    "classroom_name": exam_slot["classroom_name"],
                    "instructors": exam_slot["instructors"],
                    "preparation_time": requirement["preparation_time"],
                    "total_time": requirement["total_time_needed"],
                    "priority": requirement["priority"],
                    "special_requirements": requirement["special_requirements"],
                    "status": "scheduled"
                }
                
                schedule.append(exam_entry)
                
                # Update resource schedules
                self._update_resource_schedules(
                    exam_slot, requirement, instructor_schedule,
                    classroom_schedule, timeslot_schedule
                )
            else:
                # Could not schedule - add as unscheduled
                unscheduled_entry = {
                    "project_id": project_id,
                    "project_title": requirement["project_title"],
                    "project_type": requirement["project_type"],
                    "status": "unscheduled",
                    "reason": "No available time slot found",
                    "priority": requirement["priority"],
                    "required_instructors": requirement["required_instructors"],
                    "special_requirements": requirement["special_requirements"]
                }
                
                schedule.append(unscheduled_entry)
        
        return schedule
    
    def _find_available_slot(self, requirement: Dict[str, Any],
                           instructor_schedule: Dict[str, Any],
                           classroom_schedule: Dict[str, Any],
                           timeslot_schedule: Dict[str, Any],
                           constraints: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find an available slot for an exam."""
        required_instructors = requirement["required_instructors"]
        advisor_id = requirement["advisor_id"]
        jury_members = requirement["jury_members"]
        
        # Get required instructor IDs
        required_instructor_ids = [advisor_id]
        for member in jury_members:
            if member.get("instructor_id") != "ra_placeholder":
                required_instructor_ids.append(member["instructor_id"])
        
        # Find common available times for all instructors
        for timeslot_id, timeslot_info in timeslot_schedule.items():
            if not timeslot_info["available"]:
                continue
            
            # Check if timeslot has capacity
            if timeslot_info["exam_count"] >= self.max_exams_per_day:
                continue
            
            # Find available classroom
            for classroom_id, classroom_info in classroom_schedule.items():
                if not classroom_info.get("available", True):
                    continue
                
                # Check instructor availability
                instructor_available = True
                available_instructors = []
                
                for instructor_id in required_instructor_ids:
                    instructor_slots = instructor_schedule.get(instructor_id, {})
                    if timeslot_id in instructor_slots:
                        instructor_available = False
                        break
                    
                    # Check daily exam limit
                    daily_count = sum(1 for slot in instructor_slots.values() 
                                    if slot.get("date") == timeslot_info.get("date", ""))
                    if daily_count >= self.max_exams_per_instructor:
                        instructor_available = False
                        break
                    
                    available_instructors.append(instructor_id)
                
                if instructor_available and len(available_instructors) >= required_instructors:
                    # Found available slot
                    return {
                        "timeslot_id": timeslot_id,
                        "time": timeslot_info["start_time"],
                        "date": timeslot_info.get("date", ""),
                        "classroom_id": classroom_id,
                        "classroom_name": classroom_info.get("name", ""),
                        "instructors": available_instructors[:required_instructors],
                        "duration": requirement["exam_duration"]
                    }
        
        return None
    
    def _update_resource_schedules(self, exam_slot: Dict[str, Any],
                                 requirement: Dict[str, Any],
                                 instructor_schedule: Dict[str, Any],
                                 classroom_schedule: Dict[str, Any],
                                 timeslot_schedule: Dict[str, Any]):
        """Update resource schedules after scheduling an exam."""
        timeslot_id = exam_slot["timeslot_id"]
        classroom_id = exam_slot["classroom_id"]
        
        # Update timeslot schedule
        timeslot_schedule[timeslot_id]["exam_count"] += 1
        
        # Update classroom schedule
        classroom_schedule[classroom_id][timeslot_id] = {
            "project_id": requirement["project_id"],
            "start_time": exam_slot["time"],
            "duration": requirement["exam_duration"]
        }
        
        # Update instructor schedules
        for instructor_id in exam_slot["instructors"]:
            instructor_schedule[instructor_id][timeslot_id] = {
                "project_id": requirement["project_id"],
                "classroom_id": classroom_id,
                "start_time": exam_slot["time"],
                "duration": requirement["exam_duration"],
                "role": "advisor" if instructor_id == requirement["advisor_id"] else "jury_member"
            }
    
    def _calculate_schedule_metrics(self, schedule: List[Dict[str, Any]],
                                  requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate schedule quality metrics."""
        if not schedule:
            return {
                "scheduling_rate": 0,
                "average_priority_scheduled": 0,
                "resource_utilization": 0,
                "time_efficiency": 0
            }
        
        # Calculate scheduling rate
        scheduled = [exam for exam in schedule if exam["status"] == "scheduled"]
        scheduling_rate = len(scheduled) / len(schedule) if schedule else 0
        
        # Calculate average priority of scheduled exams
        if scheduled:
            avg_priority = sum(exam["priority"] for exam in scheduled) / len(scheduled)
        else:
            avg_priority = 0
        
        # Calculate resource utilization
        total_exam_time = sum(exam["total_time"] for exam in scheduled)
        total_available_time = len(schedule) * 8 * 60  # 8 hours per day
        resource_utilization = min(total_exam_time / total_available_time, 1.0) if total_available_time > 0 else 0
        
        # Calculate time efficiency
        total_duration = sum(exam["duration"] for exam in scheduled)
        total_prep_time = sum(exam["preparation_time"] for exam in scheduled)
        time_efficiency = total_duration / (total_duration + total_prep_time) if (total_duration + total_prep_time) > 0 else 0
        
        return {
            "scheduling_rate": scheduling_rate,
            "average_priority_scheduled": avg_priority,
            "resource_utilization": resource_utilization,
            "time_efficiency": time_efficiency,
            "total_scheduled": len(scheduled),
            "total_unscheduled": len(schedule) - len(scheduled),
            "total_exam_time": total_exam_time,
            "average_exam_duration": total_duration / len(scheduled) if scheduled else 0
        }
    
    def _analyze_conflicts(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze scheduling conflicts."""
        conflicts = []
        
        # Check for instructor conflicts
        instructor_assignments = {}
        for exam in schedule:
            if exam["status"] == "scheduled":
                for instructor in exam["instructors"]:
                    if instructor not in instructor_assignments:
                        instructor_assignments[instructor] = []
                    instructor_assignments[instructor].append(exam)
        
        # Find double-booked instructors
        for instructor, exams in instructor_assignments.items():
            if len(exams) > 1:
                # Check for time conflicts
                for i, exam1 in enumerate(exams):
                    for exam2 in exams[i+1:]:
                        if exam1["exam_time"] == exam2["exam_time"]:
                            conflicts.append({
                                "type": "instructor_conflict",
                                "instructor_id": instructor,
                                "conflicting_exams": [exam1["project_id"], exam2["project_id"]],
                                "time": exam1["exam_time"],
                                "severity": "high"
                            })
        
        # Check for classroom conflicts
        classroom_assignments = {}
        for exam in schedule:
            if exam["status"] == "scheduled":
                classroom_id = exam["classroom_id"]
                if classroom_id not in classroom_assignments:
                    classroom_assignments[classroom_id] = []
                classroom_assignments[classroom_id].append(exam)
        
        # Find double-booked classrooms
        for classroom, exams in classroom_assignments.items():
            if len(exams) > 1:
                for i, exam1 in enumerate(exams):
                    for exam2 in exams[i+1:]:
                        if exam1["exam_time"] == exam2["exam_time"]:
                            conflicts.append({
                                "type": "classroom_conflict",
                                "classroom_id": classroom,
                                "conflicting_exams": [exam1["project_id"], exam2["project_id"]],
                                "time": exam1["exam_time"],
                                "severity": "high"
                            })
        
        return conflicts
    
    def optimize_schedule(self, schedule: List[Dict[str, Any]],
                         optimization_goals: List[str]) -> Dict[str, Any]:
        """
        Optimize the oral exam schedule based on specified goals.
        
        Args:
            schedule: Current exam schedule
            optimization_goals: List of optimization goals (e.g., ["minimize_conflicts", "maximize_utilization"])
            
        Returns:
            Optimized schedule with improvement metrics
        """
        try:
            original_metrics = self._calculate_schedule_metrics(schedule, {})
            
            optimized_schedule = schedule.copy()
            
            # Apply optimization strategies based on goals
            for goal in optimization_goals:
                if goal == "minimize_conflicts":
                    optimized_schedule = self._minimize_conflicts(optimized_schedule)
                elif goal == "maximize_utilization":
                    optimized_schedule = self._maximize_utilization(optimized_schedule)
                elif goal == "balance_instructor_load":
                    optimized_schedule = self._balance_instructor_load(optimized_schedule)
                elif goal == "minimize_duration":
                    optimized_schedule = self._minimize_total_duration(optimized_schedule)
            
            optimized_metrics = self._calculate_schedule_metrics(optimized_schedule, {})
            
            return {
                "status": "success",
                "original_schedule": schedule,
                "optimized_schedule": optimized_schedule,
                "improvements": {
                    "scheduling_rate": optimized_metrics["scheduling_rate"] - original_metrics["scheduling_rate"],
                    "resource_utilization": optimized_metrics["resource_utilization"] - original_metrics["resource_utilization"],
                    "time_efficiency": optimized_metrics["time_efficiency"] - original_metrics["time_efficiency"]
                },
                "optimization_goals": optimization_goals,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Schedule optimization failed: {str(e)}",
                "original_schedule": schedule,
                "optimized_schedule": schedule,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _minimize_conflicts(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Minimize scheduling conflicts."""
        # Implementation for conflict minimization
        # This would involve rescheduling conflicting exams
        return schedule  # Placeholder
    
    def _maximize_utilization(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Maximize resource utilization."""
        # Implementation for utilization maximization
        return schedule  # Placeholder
    
    def _balance_instructor_load(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Balance instructor workload."""
        # Implementation for load balancing
        return schedule  # Placeholder
    
    def _minimize_total_duration(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Minimize total schedule duration."""
        # Implementation for duration minimization
        return schedule  # Placeholder
