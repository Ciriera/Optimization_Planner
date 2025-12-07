"""
Notification service for generating and sending instructor notification emails.
Handles planner data parsing, personalization, and email template generation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Instructor, Schedule, Project, Classroom, TimeSlot, NotificationLog, NotificationStatus
from app.services.email_service import EmailService
from app.services.planner_export_service import exportPlannerToExcel
from app.services.excel_to_image_service import excel_to_png
from io import BytesIO

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for generating and sending instructor notifications."""
    
    def __init__(self):
        self.email_service = EmailService()
    
    async def get_global_planner_preview(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get the current planner data for global preview.
        
        Returns:
            Dict with planner data structure matching frontend expectations
        """
        try:
            # Fetch all schedules with related data
            schedules_query = select(Schedule).options(
                # Eager load relationships
            )
            schedules_result = await db.execute(schedules_query)
            schedules = schedules_result.scalars().all()
            
            # Fetch related data
            classrooms_query = select(Classroom)
            classrooms_result = await db.execute(classrooms_query)
            classrooms = classrooms_result.scalars().all()
            
            timeslots_query = select(TimeSlot).order_by(TimeSlot.start_time)
            timeslots_result = await db.execute(timeslots_query)
            timeslots = timeslots_result.scalars().all()
            
            projects_query = select(Project)
            projects_result = await db.execute(projects_query)
            projects = projects_result.scalars().all()
            
            instructors_query = select(Instructor)
            instructors_result = await db.execute(instructors_query)
            instructors = instructors_result.scalars().all()
            
            # Build planner data structure
            classes = [cls.name for cls in classrooms]
            time_slots = []
            if timeslots:
                for ts in timeslots:
                    start_str = ts.start_time.strftime("%H:%M") if hasattr(ts.start_time, 'strftime') else str(ts.start_time)[:5]
                    time_slots.append(start_str)
            
            # Build projects list
            projects_list = []
            for schedule in schedules:
                project = next((p for p in projects if p.id == schedule.project_id), None)
                classroom = next((c for c in classrooms if c.id == schedule.classroom_id), None)
                timeslot = next((t for t in timeslots if t.id == schedule.timeslot_id), None)
                
                if not project or not classroom or not timeslot:
                    continue
                
                # Get responsible instructor
                responsible = next((i for i in instructors if i.id == project.responsible_instructor_id), None)
                responsible_name = responsible.name if responsible else ""
                
                # Get jury members from schedule.instructors JSON
                jury_list = []
                if schedule.instructors:
                    for inst_id in schedule.instructors:
                        if isinstance(inst_id, dict):
                            inst_id = inst_id.get("id", inst_id)
                        inst = next((i for i in instructors if i.id == inst_id), None)
                        if inst and inst.id != project.responsible_instructor_id:
                            jury_list.append(inst.name)
                
                time_str = timeslot.start_time.strftime("%H:%M") if hasattr(timeslot.start_time, 'strftime') else str(timeslot.start_time)[:5]
                
                projects_list.append({
                    "class": classroom.name,
                    "time": time_str,
                    "projectTitle": project.title or f"Proje {project.id}",
                    "type": "Bitirme" if project.type.value == "final" else "Ara",
                    "responsible": responsible_name,
                    "jury": jury_list,
                    "color": "#1976d2" if project.type.value == "final" else "#dc004e",
                })
            
            return {
                "success": True,
                "planner_data": {
                    "classes": classes,
                    "timeSlots": time_slots,
                    "projects": projects_list,
                    "title": "BİLGİSAYAR ve BİTİRME Projesi Jüri Programı",
                    "date": datetime.now().strftime("%d %B %Y").upper(),
                },
                "metadata": {
                    "total_schedules": len(schedules),
                    "total_instructors": len(instructors),
                    "total_classrooms": len(classrooms),
                    "generated_at": datetime.now().isoformat(),
                }
            }
        except Exception as e:
            logger.error(f"Error getting global planner preview: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "planner_data": None,
            }
    
    async def get_instructor_preview(
        self,
        instructor_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get personalized preview for a specific instructor.
        
        Args:
            instructor_id: Instructor ID
            db: Database session
            
        Returns:
            Dict with instructor assignments and preview data
        """
        try:
            # Fetch instructor
            instructor_query = select(Instructor).where(Instructor.id == instructor_id)
            instructor_result = await db.execute(instructor_query)
            instructor = instructor_result.scalar_one_or_none()
            
            if not instructor:
                return {
                    "success": False,
                    "error": "Instructor not found",
                }
            
            if not instructor.email:
                return {
                    "success": False,
                    "error": "Instructor email not set",
                }
            
            # Fetch schedules
            schedules_query = select(Schedule)
            schedules_result = await db.execute(schedules_query)
            schedules = schedules_result.scalars().all()
            
            # Fetch related data
            projects_query = select(Project)
            projects_result = await db.execute(projects_query)
            projects = projects_result.scalars().all()
            
            classrooms_query = select(Classroom)
            classrooms_result = await db.execute(classrooms_query)
            classrooms = classrooms_result.scalars().all()
            
            timeslots_query = select(TimeSlot)
            timeslots_result = await db.execute(timeslots_query)
            timeslots = timeslots_result.scalars().all()
            
            instructors_query = select(Instructor)
            instructors_result = await db.execute(instructors_query)
            all_instructors = instructors_result.scalars().all()
            
            # Filter schedules where instructor appears
            assignments = []
            for schedule in schedules:
                project = next((p for p in projects if p.id == schedule.project_id), None)
                if not project:
                    continue
                
                # Check if instructor is responsible
                is_responsible = project.responsible_instructor_id == instructor_id
                
                # Check if instructor is in jury
                is_jury = False
                if schedule.instructors:
                    for inst_id in schedule.instructors:
                        if isinstance(inst_id, dict):
                            inst_id = inst_id.get("id", inst_id)
                        if inst_id == instructor_id:
                            is_jury = True
                            break
                
                if not (is_responsible or is_jury):
                    continue
                
                # Determine role
                role = "Project Responsible" if is_responsible else "Jury Member"
                
                # Get other instructors
                other_instructors = []
                if project.responsible_instructor_id and project.responsible_instructor_id != instructor_id:
                    resp_inst = next((i for i in all_instructors if i.id == project.responsible_instructor_id), None)
                    if resp_inst:
                        other_instructors.append(f"{resp_inst.name} (Responsible)")
                
                if schedule.instructors:
                    for inst_id in schedule.instructors:
                        if isinstance(inst_id, dict):
                            inst_id = inst_id.get("id", inst_id)
                        if inst_id != instructor_id and inst_id != project.responsible_instructor_id:
                            inst = next((i for i in all_instructors if i.id == inst_id), None)
                            if inst:
                                other_instructors.append(f"{inst.name} (Jury)")
                
                classroom = next((c for c in classrooms if c.id == schedule.classroom_id), None)
                timeslot = next((t for t in timeslots if t.id == schedule.timeslot_id), None)
                
                if not classroom or not timeslot:
                    continue
                
                # Format date and time
                date_str = "17 June 2025"  # Default - should come from timeslot if available
                if hasattr(timeslot, 'date') and timeslot.date:
                    date_str = timeslot.date.strftime("%d %B %Y")
                
                time_str = timeslot.start_time.strftime("%H:%M") if hasattr(timeslot.start_time, 'strftime') else str(timeslot.start_time)[:5]
                end_time = timeslot.end_time.strftime("%H:%M") if hasattr(timeslot.end_time, 'strftime') else str(timeslot.end_time)[:5]
                time_range = f"{time_str}-{end_time}"
                
                assignments.append({
                    "date": date_str,
                    "time": time_range,
                    "room": classroom.name,
                    "project": project.title or f"Proje {project.id}",
                    "role": role,
                    "otherInstructors": other_instructors,
                    "projectType": "Bitirme" if project.type.value == "final" else "Ara",
                })
            
            # Sort by date and time
            assignments.sort(key=lambda x: (x["date"], x["time"]))
            
            return {
                "success": True,
                "instructor": {
                    "id": instructor.id,
                    "name": instructor.name,
                    "email": instructor.email,
                },
                "assignments": assignments,
                "hasAssignments": len(assignments) > 0,
                "assignmentCount": len(assignments),
            }
        except Exception as e:
            logger.error(f"Error getting instructor preview: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _generate_email_html(
        self,
        instructor_name: str,
        assignments: List[Dict[str, Any]],
        global_planner_html: str,
        calendar_image_filename: Optional[str] = None,
        calendar_image_base64: Optional[str] = None,
        calendar_image_base64_large: Optional[str] = None,
    ) -> str:
        """
        Generate HTML email content.
        
        Args:
            instructor_name: Instructor full name
            assignments: List of assignment dictionaries
            global_planner_html: HTML table of global planner
            
        Returns:
            HTML email content
        """
        assignments_table_html = ""
        if assignments:
            assignments_table_html = """
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px;">
                <thead>
                    <tr style="background-color: #0f172a; color: white;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #334155;">Date</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #334155;">Time</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #334155;">Room</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #334155;">Project</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #334155;">Role</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #334155;">Colleagues</th>
                    </tr>
                </thead>
                <tbody>
            """
            for idx, assignment in enumerate(assignments):
                row_color = "#f8fafc" if idx % 2 == 0 else "#ffffff"
                assignments_table_html += f"""
                    <tr style="background-color: {row_color};">
                        <td style="padding: 10px; border: 1px solid #e2e8f0;">{assignment['date']}</td>
                        <td style="padding: 10px; border: 1px solid #e2e8f0;">{assignment['time']}</td>
                        <td style="padding: 10px; border: 1px solid #e2e8f0;">{assignment['room']}</td>
                        <td style="padding: 10px; border: 1px solid #e2e8f0;">{assignment['project']}</td>
                        <td style="padding: 10px; border: 1px solid #e2e8f0;">{assignment['role']}</td>
                        <td style="padding: 10px; border: 1px solid #e2e8f0;">{', '.join(assignment['otherInstructors']) if assignment['otherInstructors'] else '-'}</td>
                    </tr>
                """
            assignments_table_html += """
                </tbody>
            </table>
            """
        else:
            assignments_table_html = """
            <p style="padding: 20px; background-color: #f1f5f9; border-radius: 8px; color: #64748b;">
                You have no assigned duties in this planner.
            </p>
            """
        
        # Calendar image HTML
        # NOTE: PNG snapshot for the full calendar turned out to be hard to read and unreliable
        # across different email clients. We now rely on the rich HTML table (global_planner_html)
        # for the visual calendar, and attach the original Excel file for full-resolution viewing.
        # To avoid confusing empty/blank images, we intentionally do NOT render any PNG here.
        calendar_image_html = ""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Exam Planner Notification</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f6fa; margin: 0; padding: 24px;">
    <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);">
        
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 32px; padding-bottom: 20px; border-bottom: 2px solid #e2e8f0;">
            <div style="display: inline-block; padding: 6px 16px; background-color: #e0f2fe; border-radius: 999px; font-size: 12px; color: #0369a1; font-weight: 600; margin-bottom: 12px;">
                Optimization Planner · Final Jury 2025
            </div>
            <h1 style="margin: 0; color: #0f172a; font-size: 24px; font-weight: 700;">Exam Duty Notification</h1>
        </div>
        
        <!-- Greeting -->
        <div style="margin-bottom: 32px;">
            <p style="font-size: 18px; font-weight: 600; color: #0f172a; margin-bottom: 12px;">Dear {instructor_name},</p>
            <p style="font-size: 14px; color: #475569; line-height: 1.6;">
                Here are your scheduled duties for the upcoming final jury program. Please review your assignments below.
            </p>
        </div>
        
        <!-- Personal Assignments -->
        <div style="margin-bottom: 32px;">
            <h2 style="font-size: 18px; font-weight: 600; color: #0f172a; margin-bottom: 16px;">Your Assignments</h2>
            {assignments_table_html}
        </div>
        
        <!-- Footer -->
        <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center;">
            <p style="font-size: 12px; color: #64748b; margin: 0;">
                This message was generated automatically by the Optimization Planner system.<br/>
                If you have questions or need changes, please contact the planning team.
            </p>
        </div>
        
    </div>
</body>
</html>
        """
        return html_content
    
    def _generate_global_planner_html(self, planner_data: Dict[str, Any]) -> str:
        """
        Generate HTML table for global planner.
        
        Args:
            planner_data: Planner data dictionary
            
        Returns:
            HTML table string
        """
        classes = planner_data.get("classes", [])
        time_slots = planner_data.get("timeSlots", [])
        projects = planner_data.get("projects", [])
        
        # Build a lookup dictionary for faster access
        project_lookup = {}
        for proj in projects:
            key = (proj.get("class"), proj.get("time"))
            if key not in project_lookup:
                project_lookup[key] = []
            project_lookup[key].append(proj)
        
        html = """
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; background-color: #ffffff;">
            <thead>
                <tr style="background-color: #0f172a; color: white;">
                    <th style="padding: 12px; border: 1px solid #334155; text-align: center; font-weight: 600; min-width: 80px;">Time</th>
        """
        
        for cls in classes:
            html += f'<th style="padding: 12px; border: 1px solid #334155; text-align: center; font-weight: 600; min-width: 200px;">{cls}</th>'
        
        html += """
                </tr>
            </thead>
            <tbody>
        """
        
        for idx, time_slot in enumerate(time_slots):
            row_bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            html += f"""
                <tr style="background-color: {row_bg};">
                    <td style="padding: 10px; border: 1px solid #e2e8f0; text-align: center; font-weight: 600; background-color: #f1f5f9;">{time_slot}</td>
            """
            for cls in classes:
                # Find projects for this class and time
                proj_list = project_lookup.get((cls, time_slot), [])
                
                if proj_list:
                    # Build cell content with project details
                    cell_content = ""
                    for proj in proj_list:
                        proj_title = proj.get('projectTitle', 'N/A')
                        responsible = proj.get('responsible', '')
                        jury = proj.get('jury', [])
                        proj_type = proj.get('type', '')
                        proj_color = proj.get('color', '#ffffff')
                        
                        # Create a colored box for each project
                        jury_text = f"<br/><small style='color: #64748b;'>Jüri: {', '.join(jury) if jury else 'N/A'}</small>" if jury else ""
                        cell_content += f"""
                        <div style="margin-bottom: 8px; padding: 8px; background-color: {proj_color}; border-radius: 4px; border-left: 3px solid {proj_color};">
                            <div style="font-weight: 600; color: #0f172a; margin-bottom: 4px;">{proj_title}</div>
                            <div style="font-size: 10px; color: #475569; margin-bottom: 2px;">Sorumlu: {responsible}</div>
                            <div style="font-size: 10px; color: #64748b;">{proj_type}{jury_text}</div>
                        </div>
                        """
                    
                    html += f'<td style="padding: 8px; border: 1px solid #e2e8f0; vertical-align: top;">{cell_content}</td>'
                else:
                    html += '<td style="padding: 8px; border: 1px solid #e2e8f0; text-align: center; color: #94a3b8;">-</td>'
            
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        return html
    
    async def send_notification_to_instructor(
        self,
        instructor_id: int,
        db: AsyncSession,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Send notification email to a specific instructor.
        
        Args:
            instructor_id: Instructor ID
            db: Database session
            dry_run: If True, don't actually send email
            
        Returns:
            Dict with success status and details
        """
        notification_log = None  # Initialize outside try block for exception handling
        try:
            # Get instructor preview
            preview_result = await self.get_instructor_preview(instructor_id, db)
            if not preview_result.get("success"):
                return preview_result
            
            instructor_data = preview_result["instructor"]
            assignments = preview_result["assignments"]
            
            # Validate email
            if not instructor_data.get("email"):
                error_msg = f"Instructor {instructor_id} ({instructor_data.get('name', 'Unknown')}) has no email address"
                logger.error(error_msg)
                
                # Still create a log entry for tracking
                try:
                    notification_log = NotificationLog(
                        instructor_id=instructor_id,
                        instructor_email="NO_EMAIL",
                        instructor_name=instructor_data.get("name", "Unknown"),
                        planner_timestamp=datetime.now(),
                        subject="Failed - No Email Address",
                        status=NotificationStatus.ERROR,
                        error_message=error_msg,
                        attempt_count=1,
                        meta_data={
                            "assignment_count": len(assignments),
                        }
                    )
                    db.add(notification_log)
                    await db.commit()
                    logger.info(f"Error log created for instructor {instructor_id}: {notification_log.id}")
                except Exception as log_e:
                    logger.error(f"Failed to create error log: {str(log_e)}", exc_info=True)
                    await db.rollback()
                
                return {
                    "success": False,
                    "error": error_msg,
                }
            
            # Get global planner
            planner_result = await self.get_global_planner_preview(db)
            if not planner_result.get("success"):
                error_msg = "Failed to get planner data"
                logger.error(error_msg)
                
                # Create error log
                try:
                    notification_log = NotificationLog(
                        instructor_id=instructor_id,
                        instructor_email=instructor_data.get("email", "UNKNOWN"),
                        instructor_name=instructor_data.get("name", "Unknown"),
                        planner_timestamp=datetime.now(),
                        subject="Failed - No Planner Data",
                        status=NotificationStatus.ERROR,
                        error_message=error_msg,
                        attempt_count=1,
                        meta_data={
                            "assignment_count": len(assignments),
                        }
                    )
                    db.add(notification_log)
                    await db.commit()
                    logger.info(f"Error log created for instructor {instructor_id}: {notification_log.id}")
                except Exception as log_e:
                    logger.error(f"Failed to create error log: {str(log_e)}", exc_info=True)
                    await db.rollback()
                
                return {
                    "success": False,
                    "error": error_msg,
                }
            
            planner_data = planner_result["planner_data"]
            
            # Create notification log entry FIRST (before any operations that might fail)
            notification_log = None
            try:
                notification_log = NotificationLog(
                    instructor_id=instructor_id,
                    instructor_email=instructor_data["email"],
                    instructor_name=instructor_data["name"],
                    planner_timestamp=datetime.now(),
                    subject=f"Your Final Exam Duties – {planner_data.get('date', '2025')}",
                    status=NotificationStatus.PENDING,
                    attempt_count=1,
                    meta_data={
                        "assignment_count": len(assignments),
                    }
                )
                db.add(notification_log)
                await db.flush()
                logger.info(f"Notification log created for instructor {instructor_id} (dry_run={dry_run}): {notification_log.id}")
            except Exception as log_e:
                logger.error(f"Failed to create notification log: {str(log_e)}", exc_info=True)
                await db.rollback()
                # Continue anyway - don't fail the whole operation
            
            # Generate global planner HTML for rich visual representation
            global_planner_html = self._generate_global_planner_html(planner_data)
            
            # Generate Excel file (will be attached as .xlsx for full-resolution viewing)
            try:
                excel_bytes = exportPlannerToExcel(planner_data)
                logger.info(f"Excel file generated for instructor {instructor_id}: {len(excel_bytes)} bytes")
            except Exception as e:
                logger.error(f"Error generating Excel for instructor {instructor_id}: {str(e)}", exc_info=True)
                excel_bytes = None
            
            # Generate email HTML (no PNG image – uses HTML table + Excel attachment instead)
            email_html = self._generate_email_html(
                instructor_name=instructor_data["name"],
                assignments=assignments,
                global_planner_html=global_planner_html,
            )
            
            if dry_run:
                # Even in dry_run, commit the log entry
                if notification_log:
                    try:
                        await db.commit()
                        logger.info(f"✅ Dry-run notification log COMMITTED: id={notification_log.id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to commit dry-run notification log: {str(e)}", exc_info=True)
                        try:
                            await db.rollback()
                        except:
                            pass
                
                return {
                    "success": True,
                    "dry_run": True,
                    "instructor_email": instructor_data["email"],
                    "notification_log_id": notification_log.id if notification_log else None,
                }
            
            # Prepare attachments – attach Excel workbook for full planner view
            attachments = []
            if excel_bytes:
                attachments.append(
                    (
                        excel_bytes,
                        "final_exam_planner.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                )
                logger.info(
                    "Adding Excel attachment for instructor %s (%d bytes)",
                    instructor_data["email"],
                    len(excel_bytes),
                )
            
            # Send email (with or without attachment)
            email_result = self.email_service.send_email(
                to_email=instructor_data["email"],
                subject=f"Your Final Exam Duties – {planner_data.get('date', '2025')}",
                html_content=email_html,
                attachments=attachments if attachments else None,
            )
            
            # Update notification log
            if email_result["success"]:
                notification_log.status = NotificationStatus.SUCCESS
                notification_log.sent_at = datetime.now()
            else:
                notification_log.status = NotificationStatus.ERROR
                notification_log.error_message = email_result.get("error", "Unknown error")
            
            try:
                await db.commit()
                logger.info(f"✅ Notification log COMMITTED for instructor {instructor_id}: status={notification_log.status}, id={notification_log.id}")
            except Exception as e:
                logger.error(f"❌ Failed to commit notification log: {str(e)}", exc_info=True)
                try:
                    await db.rollback()
                except:
                    pass
                # Don't raise - log the error but continue
                logger.warning(f"Notification log was created but not committed: {notification_log.id}")
            
            return {
                "success": email_result["success"],
                "error": email_result.get("error"),
                "instructor_email": instructor_data["email"],
                "notification_log_id": notification_log.id if notification_log else None,
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error sending notification to instructor {instructor_id}: {error_msg}", exc_info=True)
            
            # Try to update or create error log
            try:
                if notification_log and notification_log.id:
                    # Update existing log
                    notification_log.status = NotificationStatus.ERROR
                    notification_log.error_message = error_msg
                    await db.commit()
                    logger.info(f"Error log updated for instructor {instructor_id}: {notification_log.id}")
                else:
                    # Create new error log
                    try:
                        instructor_name = instructor_data.get("name", "Unknown") if 'instructor_data' in locals() else "Unknown"
                        instructor_email = instructor_data.get("email", "UNKNOWN") if 'instructor_data' in locals() else "UNKNOWN"
                    except:
                        instructor_name = "Unknown"
                        instructor_email = "UNKNOWN"
                    
                    error_log = NotificationLog(
                        instructor_id=instructor_id,
                        instructor_email=instructor_email,
                        instructor_name=instructor_name,
                        planner_timestamp=datetime.now(),
                        subject="Failed - Exception",
                        status=NotificationStatus.ERROR,
                        error_message=error_msg,
                        attempt_count=1,
                        meta_data={}
                    )
                    db.add(error_log)
                    await db.commit()
                    logger.info(f"Error log created for instructor {instructor_id}: {error_log.id}")
            except Exception as log_e:
                logger.error(f"Failed to create/update error log: {str(log_e)}", exc_info=True)
                try:
                    await db.rollback()
                except:
                    pass
            
            return {
                "success": False,
                "error": error_msg,
            }
    
    async def send_notifications_to_all(
        self,
        db: AsyncSession,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Send notifications to all instructors with email addresses.
        
        Args:
            db: Database session
            dry_run: If True, don't actually send emails
            
        Returns:
            Dict with summary statistics
        """
        try:
            # Get all instructors with email
            instructors_query = select(Instructor).where(Instructor.email.isnot(None)).where(Instructor.email != "")
            instructors_result = await db.execute(instructors_query)
            instructors = instructors_result.scalars().all()
            
            if not instructors:
                return {
                    "success": False,
                    "error": "No instructors with email addresses found",
                }
            
            results = {
                "total": len(instructors),
                "success": 0,
                "failed": 0,
                "errors": [],
            }
            
            # Send to each instructor
            for instructor in instructors:
                result = await self.send_notification_to_instructor(
                    instructor_id=instructor.id,
                    db=db,
                    dry_run=dry_run,
                )
                
                if result.get("success"):
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "instructor_id": instructor.id,
                        "instructor_email": instructor.email,
                        "error": result.get("error", "Unknown error"),
                    })
            
            return {
                "success": True,
                "results": results,
            }
            
        except Exception as e:
            logger.error(f"Error sending notifications to all: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_notification_logs(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        status: Optional[NotificationStatus] = None,
    ) -> Dict[str, Any]:
        """
        Get notification logs with pagination and filtering.
        
        Args:
            db: Database session
            limit: Maximum number of logs to return
            offset: Offset for pagination
            status: Filter by status (optional)
            
        Returns:
            Dict with logs list and total count
        """
        try:
            query = select(NotificationLog)
            
            if status:
                query = query.where(NotificationLog.status == status)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            logger.info(f"Found {total} notification logs (status={status}, limit={limit}, offset={offset})")
            
            # Get paginated results
            query = query.order_by(NotificationLog.created_at.desc()).limit(limit).offset(offset)
            logs_result = await db.execute(query)
            logs = logs_result.scalars().all()
            
            # Convert to dict
            logs_list = []
            for log in logs:
                try:
                    logs_list.append(log.to_dict())
                except Exception as e:
                    logger.error(f"Error converting log {log.id} to dict: {str(e)}")
                    # Fallback: manual conversion
                    logs_list.append({
                        "id": log.id,
                        "instructor_id": log.instructor_id,
                        "instructor_email": log.instructor_email,
                        "instructor_name": log.instructor_name,
                        "planner_timestamp": log.planner_timestamp.isoformat() if log.planner_timestamp else None,
                        "subject": log.subject,
                        "status": log.status.value if hasattr(log.status, 'value') else str(log.status),
                        "error_message": log.error_message,
                        "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                        "attempt_count": log.attempt_count or 0,
                        "metadata": log.meta_data,
                        "created_at": log.created_at.isoformat() if log.created_at else None,
                        "updated_at": log.updated_at.isoformat() if log.updated_at else None,
                    })
            
            logger.info(f"Returning {len(logs_list)} notification logs")
            return {
                "success": True,
                "logs": logs_list,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error getting notification logs: {error_msg}", exc_info=True)
            
            # Check if error is due to missing table
            if "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
                logger.warning("notification_logs table does not exist. Please run migration at /api/v1/notification/migrate")
                return {
                    "success": False,
                    "error": "notification_logs table does not exist. Please run migration at /api/v1/notification/migrate",
                    "logs": [],
                    "total": 0,
                }
            
            return {
                "success": False,
                "error": error_msg,
                "logs": [],
                "total": 0,
            }
    
    async def send_notification_to_custom_email(
        self,
        email: str,
        recipient_name: str = "TEST_ADMIN",
        db: AsyncSession = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Send notification email to a custom email address (e.g., TEST_ADMIN).
        This sends the global planner without personal assignments.
        
        Args:
            email: Recipient email address
            recipient_name: Recipient name (default: TEST_ADMIN)
            db: Database session (optional, for logging)
            dry_run: If True, don't actually send email
            
        Returns:
            Dict with success status and details
        """
        try:
            # Get global planner
            if db:
                planner_result = await self.get_global_planner_preview(db)
            else:
                # If no DB session, create minimal planner data
                planner_result = {
                    "success": True,
                    "planner_data": {
                        "classes": [],
                        "timeSlots": [],
                        "projects": [],
                        "title": "BİLGİSAYAR ve BİTİRME Projesi Jüri Programı",
                        "date": datetime.now().strftime("%d %B %Y").upper(),
                    },
                }
            
            if not planner_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to get planner data",
                }
            
            planner_data = planner_result["planner_data"]
            
            # Generate global planner HTML
            global_planner_html = self._generate_global_planner_html(planner_data)
            
            # Generate Excel file (will be attached as .xlsx for full-resolution viewing)
            try:
                excel_bytes = exportPlannerToExcel(planner_data)
                logger.info(f"Excel file generated for custom email {email}: {len(excel_bytes)} bytes")
            except Exception as e:
                logger.error(f"Error generating Excel for custom email {email}: {str(e)}", exc_info=True)
                excel_bytes = None
            
            # Generate email HTML (no PNG image – uses HTML table + Excel attachment instead)
            email_html = self._generate_email_html(
                instructor_name=recipient_name,
                assignments=[],  # No personal assignments for custom email
                global_planner_html=global_planner_html,
            )
            
            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "email": email,
                }
            
            # Prepare attachments – attach Excel workbook for full planner view
            attachments = []
            if excel_bytes:
                attachments.append(
                    (
                        excel_bytes,
                        "final_exam_planner.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                )
                logger.info(
                    "Adding Excel attachment for custom email %s (%d bytes)",
                    email,
                    len(excel_bytes),
                )
            
            # Send email (with or without attachment)
            email_result = self.email_service.send_email(
                to_email=email,
                subject=f"Final Exam Planner – {planner_data.get('date', '2025')}",
                html_content=email_html,
                attachments=attachments if attachments else None,
            )
            
            # Log to database if DB session provided (log both success and failure)
            if db:
                try:
                    notification_log = NotificationLog(
                        instructor_id=None,  # No instructor ID for custom email (NULL in DB)
                        instructor_email=email,
                        instructor_name=recipient_name,
                        planner_timestamp=datetime.now(),
                        subject=f"Final Exam Planner – {planner_data.get('date', '2025')}",
                        status=NotificationStatus.SUCCESS if email_result["success"] else NotificationStatus.ERROR,
                        error_message=email_result.get("error"),
                        sent_at=datetime.now() if email_result["success"] else None,
                        attempt_count=1,
                        meta_data={
                            "is_custom_email": True,
                        }
                    )
                    db.add(notification_log)
                    await db.flush()
                    logger.info(f"Notification log created for custom email {email}: {notification_log.id}")
                    await db.commit()
                    logger.info(f"Notification log saved for custom email {email}: status={notification_log.status}, id={notification_log.id}")
                except Exception as e:
                    logger.error(f"Failed to log custom email notification: {str(e)}", exc_info=True)
                    # Don't fail the whole operation if logging fails
                    try:
                        await db.rollback()
                    except:
                        pass
            
            return {
                "success": email_result["success"],
                "error": email_result.get("error"),
                "email": email,
            }
            
        except Exception as e:
            logger.error(f"Error sending notification to custom email {email}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

