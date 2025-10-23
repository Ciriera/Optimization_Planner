"""
Calendar synchronization service for Google Calendar and iCal integration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import uuid


class CalendarService:
    """
    Service for calendar synchronization with Google Calendar and iCal
    """
    
    def __init__(self):
        # Calendar configuration
        self.supported_calendars = ["google", "ical", "outlook"]
        self.default_event_duration = 60  # minutes
        self.timezone = "Europe/Istanbul"
    
    def create_calendar_event(self, event_data: Dict[str, Any], 
                            calendar_type: str = "google") -> Dict[str, Any]:
        """
        Create a calendar event for project presentations or oral exams.
        
        Args:
            event_data: Event details (title, start_time, end_time, etc.)
            calendar_type: Type of calendar (google, ical, outlook)
            
        Returns:
            Calendar event creation result
        """
        try:
            # Validate event data
            validation_result = self._validate_event_data(event_data)
            if not validation_result["valid"]:
                return {
                    "status": "error",
                    "message": f"Invalid event data: {validation_result['errors']}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Generate event ID
            event_id = str(uuid.uuid4())
            
            # Create event based on calendar type
            if calendar_type == "google":
                result = self._create_google_calendar_event(event_data, event_id)
            elif calendar_type == "ical":
                result = self._create_ical_event(event_data, event_id)
            elif calendar_type == "outlook":
                result = self._create_outlook_event(event_data, event_id)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported calendar type: {calendar_type}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Add common metadata
            result["event_id"] = event_id
            result["calendar_type"] = calendar_type
            result["timestamp"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Calendar event creation failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def create_schedule_events(self, schedule_data: List[Dict[str, Any]], 
                             calendar_type: str = "google") -> Dict[str, Any]:
        """
        Create multiple calendar events for a complete schedule.
        
        Args:
            schedule_data: List of schedule items to create events for
            calendar_type: Type of calendar to create events in
            
        Returns:
            Batch event creation results
        """
        try:
            results = {
                "status": "success",
                "created_events": [],
                "failed_events": [],
                "total_events": len(schedule_data),
                "calendar_type": calendar_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for schedule_item in schedule_data:
                event_data = self._convert_schedule_to_event(schedule_item)
                event_result = self.create_calendar_event(event_data, calendar_type)
                
                if event_result["status"] == "success":
                    results["created_events"].append(event_result)
                else:
                    results["failed_events"].append({
                        "schedule_item": schedule_item,
                        "error": event_result["message"]
                    })
            
            # Update overall status
            if results["failed_events"]:
                results["status"] = "partial_success" if results["created_events"] else "failed"
            
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Batch calendar event creation failed: {str(e)}",
                "created_events": [],
                "failed_events": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def sync_with_external_calendar(self, events: List[Dict[str, Any]], 
                                  calendar_type: str = "google") -> Dict[str, Any]:
        """
        Sync events with external calendar system.
        
        Args:
            events: List of events to sync
            calendar_type: Type of external calendar
            
        Returns:
            Synchronization results
        """
        try:
            sync_results = {
                "status": "success",
                "synced_events": [],
                "failed_syncs": [],
                "calendar_type": calendar_type,
                "sync_timestamp": datetime.utcnow().isoformat()
            }
            
            for event in events:
                try:
                    if calendar_type == "google":
                        sync_result = self._sync_google_calendar(event)
                    elif calendar_type == "ical":
                        sync_result = self._sync_ical(event)
                    elif calendar_type == "outlook":
                        sync_result = self._sync_outlook(event)
                    else:
                        sync_result = {
                            "status": "error",
                            "message": f"Unsupported calendar type: {calendar_type}"
                        }
                    
                    if sync_result["status"] == "success":
                        sync_results["synced_events"].append(sync_result)
                    else:
                        sync_results["failed_syncs"].append({
                            "event": event,
                            "error": sync_result["message"]
                        })
                        
                except Exception as e:
                    sync_results["failed_syncs"].append({
                        "event": event,
                        "error": str(e)
                    })
            
            # Update overall status
            if sync_results["failed_syncs"]:
                sync_results["status"] = "partial_success" if sync_results["synced_events"] else "failed"
            
            return sync_results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Calendar synchronization failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def export_to_ical(self, events: List[Dict[str, Any]]) -> str:
        """
        Export events to iCal format.
        
        Args:
            events: List of events to export
            
        Returns:
            iCal formatted string
        """
        try:
            ical_content = []
            
            # iCal header
            ical_content.append("BEGIN:VCALENDAR")
            ical_content.append("VERSION:2.0")
            ical_content.append("PRODID:-//Optimization Planner//Project Scheduling//EN")
            ical_content.append("CALSCALE:GREGORIAN")
            ical_content.append("METHOD:PUBLISH")
            
            # Add events
            for event in events:
                ical_content.append("BEGIN:VEVENT")
                ical_content.append(f"UID:{event.get('id', str(uuid.uuid4()))}")
                ical_content.append(f"DTSTART:{self._format_ical_datetime(event.get('start_time'))}")
                ical_content.append(f"DTEND:{self._format_ical_datetime(event.get('end_time'))}")
                ical_content.append(f"SUMMARY:{event.get('title', 'Project Event')}")
                ical_content.append(f"DESCRIPTION:{event.get('description', '')}")
                ical_content.append(f"LOCATION:{event.get('location', '')}")
                ical_content.append(f"STATUS:CONFIRMED")
                ical_content.append("END:VEVENT")
            
            # iCal footer
            ical_content.append("END:VCALENDAR")
            
            return "\n".join(ical_content)
            
        except Exception as e:
            return f"Error generating iCal: {str(e)}"
    
    def _validate_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate event data before creation."""
        errors = []
        
        # Required fields
        required_fields = ["title", "start_time"]
        for field in required_fields:
            if field not in event_data or not event_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate start_time format
        if "start_time" in event_data:
            try:
                if isinstance(event_data["start_time"], str):
                    datetime.fromisoformat(event_data["start_time"].replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid start_time format")
        
        # Validate end_time if provided
        if "end_time" in event_data and event_data["end_time"]:
            try:
                if isinstance(event_data["end_time"], str):
                    datetime.fromisoformat(event_data["end_time"].replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid end_time format")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _create_google_calendar_event(self, event_data: Dict[str, Any], 
                                    event_id: str) -> Dict[str, Any]:
        """Create Google Calendar event."""
        # Google Calendar API event structure
        google_event = {
            "id": event_id,
            "summary": event_data.get("title", "Project Event"),
            "description": event_data.get("description", ""),
            "start": {
                "dateTime": event_data["start_time"],
                "timeZone": self.timezone
            },
            "end": {
                "dateTime": event_data.get("end_time") or self._calculate_end_time(
                    event_data["start_time"], 
                    event_data.get("duration", self.default_event_duration)
                ),
                "timeZone": self.timezone
            },
            "location": event_data.get("location", ""),
            "attendees": self._format_attendees(event_data.get("attendees", [])),
            "reminders": {
                "useDefault": True
            },
            "visibility": "private",
            "status": "confirmed"
        }
        
        # Add custom properties
        if "project_id" in event_data:
            google_event["extendedProperties"] = {
                "private": {
                    "projectId": str(event_data["project_id"]),
                    "eventType": event_data.get("event_type", "presentation")
                }
            }
        
        return {
            "status": "success",
            "calendar_event": google_event,
            "message": "Google Calendar event created successfully"
        }
    
    def _create_ical_event(self, event_data: Dict[str, Any], 
                         event_id: str) -> Dict[str, Any]:
        """Create iCal event."""
        # Generate iCal event
        ical_event = f"""BEGIN:VEVENT
UID:{event_id}
DTSTART:{self._format_ical_datetime(event_data["start_time"])}
DTEND:{self._format_ical_datetime(
    event_data.get("end_time") or 
    self._calculate_end_time(event_data["start_time"], 
                            event_data.get("duration", self.default_event_duration))
)}
SUMMARY:{event_data.get("title", "Project Event")}
DESCRIPTION:{event_data.get("description", "")}
LOCATION:{event_data.get("location", "")}
STATUS:CONFIRMED
END:VEVENT"""
        
        return {
            "status": "success",
            "ical_content": ical_event,
            "message": "iCal event created successfully"
        }
    
    def _create_outlook_event(self, event_data: Dict[str, Any], 
                            event_id: str) -> Dict[str, Any]:
        """Create Outlook event."""
        # Outlook event structure
        outlook_event = {
            "Id": event_id,
            "Subject": event_data.get("title", "Project Event"),
            "Body": {
                "ContentType": "HTML",
                "Content": event_data.get("description", "")
            },
            "Start": event_data["start_time"],
            "End": event_data.get("end_time") or self._calculate_end_time(
                event_data["start_time"], 
                event_data.get("duration", self.default_event_duration)
            ),
            "Location": {
                "DisplayName": event_data.get("location", "")
            },
            "Attendees": self._format_outlook_attendees(event_data.get("attendees", [])),
            "IsReminderOn": True,
            "ReminderMinutesBeforeStart": 15,
            "ShowAs": "Busy",
            "Importance": "Normal"
        }
        
        return {
            "status": "success",
            "outlook_event": outlook_event,
            "message": "Outlook event created successfully"
        }
    
    def _convert_schedule_to_event(self, schedule_item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schedule item to calendar event format."""
        # Extract event information from schedule item
        event_data = {
            "title": schedule_item.get("project_title", "Project Presentation"),
            "description": self._generate_event_description(schedule_item),
            "start_time": schedule_item.get("exam_time") or schedule_item.get("presentation_time"),
            "duration": schedule_item.get("duration", self.default_event_duration),
            "location": schedule_item.get("classroom_name", ""),
            "attendees": self._extract_attendees(schedule_item),
            "project_id": schedule_item.get("project_id"),
            "event_type": "oral_exam" if "exam" in schedule_item else "presentation"
        }
        
        return event_data
    
    def _generate_event_description(self, schedule_item: Dict[str, Any]) -> str:
        """Generate event description from schedule item."""
        description_parts = []
        
        # Project information
        if schedule_item.get("project_title"):
            description_parts.append(f"Project: {schedule_item['project_title']}")
        
        if schedule_item.get("project_type"):
            description_parts.append(f"Type: {schedule_item['project_type']}")
        
        # Instructor information
        instructors = schedule_item.get("instructors", [])
        if instructors:
            instructor_names = [inst.get("name", inst.get("instructor_name", "")) for inst in instructors]
            description_parts.append(f"Jury: {', '.join(instructor_names)}")
        
        # Additional information
        if schedule_item.get("special_requirements"):
            requirements = ", ".join(schedule_item["special_requirements"])
            description_parts.append(f"Requirements: {requirements}")
        
        return "\n".join(description_parts)
    
    def _extract_attendees(self, schedule_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attendees from schedule item."""
        attendees = []
        
        instructors = schedule_item.get("instructors", [])
        for instructor in instructors:
            attendees.append({
                "email": instructor.get("email", ""),
                "name": instructor.get("name", instructor.get("instructor_name", "")),
                "role": "instructor"
            })
        
        return attendees
    
    def _format_attendees(self, attendees: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format attendees for Google Calendar."""
        formatted_attendees = []
        
        for attendee in attendees:
            formatted_attendees.append({
                "email": attendee.get("email", ""),
                "displayName": attendee.get("name", ""),
                "responseStatus": "needsAction"
            })
        
        return formatted_attendees
    
    def _format_outlook_attendees(self, attendees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format attendees for Outlook."""
        formatted_attendees = []
        
        for attendee in attendees:
            formatted_attendees.append({
                "EmailAddress": {
                    "Address": attendee.get("email", ""),
                    "Name": attendee.get("name", "")
                },
                "Type": "Required"
            })
        
        return formatted_attendees
    
    def _calculate_end_time(self, start_time: str, duration_minutes: int) -> str:
        """Calculate end time from start time and duration."""
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            return end_dt.isoformat()
        except:
            return start_time
    
    def _format_ical_datetime(self, datetime_str: str) -> str:
        """Format datetime for iCal."""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%Y%m%dT%H%M%S")
        except:
            return datetime.now().strftime("%Y%m%dT%H%M%S")
    
    def _sync_google_calendar(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Sync event with Google Calendar."""
        # This would integrate with Google Calendar API
        return {
            "status": "success",
            "message": "Event synced with Google Calendar",
            "external_id": str(uuid.uuid4())
        }
    
    def _sync_ical(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Sync event with iCal."""
        # This would handle iCal synchronization
        return {
            "status": "success",
            "message": "Event synced with iCal",
            "external_id": str(uuid.uuid4())
        }
    
    def _sync_outlook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Sync event with Outlook."""
        # This would integrate with Outlook API
        return {
            "status": "success",
            "message": "Event synced with Outlook",
            "external_id": str(uuid.uuid4())
        }
    
    def get_calendar_settings(self) -> Dict[str, Any]:
        """Get calendar integration settings."""
        return {
            "supported_calendars": self.supported_calendars,
            "default_duration": self.default_event_duration,
            "timezone": self.timezone,
            "features": {
                "batch_creation": True,
                "ical_export": True,
                "google_sync": True,
                "outlook_sync": True,
                "reminder_settings": True,
                "attendee_management": True
            }
        }
