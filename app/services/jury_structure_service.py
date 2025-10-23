"""
Jury Structure Service
Manages the 3-person jury structure for each project as specified in requirements
"""

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
import logging

logger = logging.getLogger(__name__)


class JuryStructureService:
    """Service for managing 3-person jury structure"""
    
    def __init__(self):
        self.min_instructors_bitirme = 2  # Minimum 2 instructors for bitirme projects
        self.min_instructors_ara = 1      # Minimum 1 instructor for ara projects
        self.total_jury_size = 3          # Total jury size per project
        self.max_instructors = 3          # Maximum instructors per project
    
    async def analyze_jury_structure(self, db: AsyncSession) -> Dict[str, Any]:
        """Mevcut jüri yapısını analiz eder"""
        
        try:
            from app.models.project import Project
            from app.models.instructor import Instructor
            
            # Tüm projeleri getir
            result = await db.execute(select(Project))
            projects = result.scalars().all()
            
            # Tüm instructor'ları getir
            result = await db.execute(select(Instructor))
            instructors = result.scalars().all()
            
            analysis = {
                "total_projects": len(projects),
                "total_instructors": len(instructors),
                "projects_by_type": {
                    "bitirme": 0,
                    "ara": 0
                },
                "jury_compliance": {
                    "compliant_projects": 0,
                    "non_compliant_projects": 0,
                    "details": []
                },
                "instructor_assignment": {
                    "assigned_instructors": 0,
                    "unassigned_instructors": 0,
                    "over_assigned_instructors": 0
                },
                "recommendations": []
            }
            
            # Proje türlerini analiz et
            for project in projects:
                if project.type == "bitirme":
                    analysis["projects_by_type"]["bitirme"] += 1
                elif project.type == "ara":
                    analysis["projects_by_type"]["ara"] += 1
            
            # Jüri uyumluluğunu kontrol et
            for project in projects:
                jury_info = await self._analyze_project_jury(db, project)
                
                if jury_info["is_compliant"]:
                    analysis["jury_compliance"]["compliant_projects"] += 1
                else:
                    analysis["jury_compliance"]["non_compliant_projects"] += 1
                
                analysis["jury_compliance"]["details"].append(jury_info)
            
            # Instructor assignment analizi
            instructor_assignment_count = {}
            for instructor in instructors:
                assignment_count = await self._count_instructor_assignments(db, instructor.id)
                instructor_assignment_count[instructor.id] = assignment_count
                
                if assignment_count == 0:
                    analysis["instructor_assignment"]["unassigned_instructors"] += 1
                elif assignment_count > 5:  # Arbitrary threshold for over-assignment
                    analysis["instructor_assignment"]["over_assigned_instructors"] += 1
                else:
                    analysis["instructor_assignment"]["assigned_instructors"] += 1
            
            # Öneriler üret
            analysis["recommendations"] = await self._generate_jury_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing jury structure: {str(e)}")
            return {
                "success": False,
                "message": f"Error analyzing jury structure: {str(e)}"
            }
    
    async def _analyze_project_jury(self, db: AsyncSession, project: Any) -> Dict[str, Any]:
        """Tek bir projenin jüri yapısını analiz eder"""
        
        jury_info = {
            "project_id": project.id,
            "project_title": project.title,
            "project_type": project.type,
            "required_instructors": self.min_instructors_bitirme if project.type == "bitirme" else self.min_instructors_ara,
            "assigned_instructors": [],
            "total_assigned": 0,
            "is_compliant": False,
            "issues": [],
            "suggestions": []
        }
        
        # Atanmış instructor'ları topla (sorumlu + danışmanlar + asistan ilişkisi)
        if project.responsible_id:
            jury_info["assigned_instructors"].append({
                "id": project.responsible_id,
                "role": "responsible",
                "instructor": await self._get_instructor_by_id(db, project.responsible_id)
            })
        
        if project.advisor_id:
            jury_info["assigned_instructors"].append({
                "id": project.advisor_id,
                "role": "advisor",
                "instructor": await self._get_instructor_by_id(db, project.advisor_id)
            })
        
        if project.co_advisor_id:
            jury_info["assigned_instructors"].append({
                "id": project.co_advisor_id,
                "role": "co_advisor",
                "instructor": await self._get_instructor_by_id(db, project.co_advisor_id)
            })
        
        # Assistants (project_assistants) - responsible ile çakışanları çıkar, benzersiz tut
        try:
            from app.models.project import project_assistants
            from sqlalchemy import select as sa_select
            result = await db.execute(
                sa_select(project_assistants.c.instructor_id).where(project_assistants.c.project_id == project.id)
            )
            assistant_ids = [row[0] for row in result.fetchall()]
            unique_assistant_ids = []
            for aid in assistant_ids:
                if aid and aid != project.responsible_id and aid not in unique_assistant_ids:
                    unique_assistant_ids.append(aid)
            # Append assistant entries
            for aid in unique_assistant_ids:
                jury_info["assigned_instructors"].append({
                    "id": aid,
                    "role": "assistant",
                    "instructor": await self._get_instructor_by_id(db, aid)
                })
        except Exception:
            pass

        # Benzersiz hale getir (id bazlı)
        dedup = []
        seen_ids = set()
        for item in jury_info["assigned_instructors"]:
            iid = item.get("id")
            if iid and iid not in seen_ids:
                dedup.append(item)
                seen_ids.add(iid)
        jury_info["assigned_instructors"] = dedup

        jury_info["total_assigned"] = len(jury_info["assigned_instructors"])
        
        # Uyumluluk kontrolü
        issues = []
        
        if jury_info["total_assigned"] < jury_info["required_instructors"]:
            issues.append(f"Insufficient instructors: {jury_info['total_assigned']}/{jury_info['required_instructors']}")
        
        if jury_info["total_assigned"] > self.max_instructors:
            issues.append(f"Too many instructors: {jury_info['total_assigned']}/{self.max_instructors}")
        
        if jury_info["total_assigned"] < self.total_jury_size:
            issues.append(f"Jury size too small: {jury_info['total_assigned']}/{self.total_jury_size}")
        
        # Duplicate instructor kontrolü
        instructor_ids = [inst["id"] for inst in jury_info["assigned_instructors"]]
        if len(instructor_ids) != len(set(instructor_ids)):
            issues.append("Duplicate instructors assigned")
        
        jury_info["issues"] = issues
        jury_info["is_compliant"] = len(issues) == 0
        
        # Öneriler
        if not jury_info["is_compliant"]:
            suggestions = []
            
            if jury_info["total_assigned"] < jury_info["required_instructors"]:
                needed = jury_info["required_instructors"] - jury_info["total_assigned"]
                suggestions.append(f"Assign {needed} more instructor(s)")
            
            if jury_info["total_assigned"] < self.total_jury_size:
                needed = self.total_jury_size - jury_info["total_assigned"]
                suggestions.append(f"Complete jury with {needed} more instructor(s)")
            
            jury_info["suggestions"] = suggestions
        
        return jury_info
    
    async def _get_instructor_by_id(self, db: AsyncSession, instructor_id: int) -> Optional[Dict[str, Any]]:
        """Instructor bilgisini ID ile getirir"""
        
        try:
            from app.models.instructor import Instructor
            
            result = await db.execute(select(Instructor).where(Instructor.id == instructor_id))
            instructor = result.scalar_one_or_none()
            
            if instructor:
                return {
                    "id": instructor.id,
                    "name": instructor.name,
                    "type": instructor.type,
                    "department": instructor.department
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting instructor {instructor_id}: {str(e)}")
            return None
    
    async def _count_instructor_assignments(self, db: AsyncSession, instructor_id: int) -> int:
        """Instructor'ın kaç projede atandığını sayar"""
        
        try:
            from app.models.project import Project
            
            result = await db.execute(
                select(Project).where(
                    (Project.responsible_id == instructor_id) |
                    (Project.advisor_id == instructor_id) |
                    (Project.co_advisor_id == instructor_id)
                )
            )
            projects = result.scalars().all()
            
            return len(projects)
            
        except Exception as e:
            logger.error(f"Error counting assignments for instructor {instructor_id}: {str(e)}")
            return 0
    
    async def _generate_jury_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Jüri yapısı önerileri üretir"""
        
        recommendations = []
        
        # Non-compliant projects
        non_compliant_count = analysis["jury_compliance"]["non_compliant_projects"]
        if non_compliant_count > 0:
            recommendations.append({
                "type": "fix_non_compliant",
                "priority": "high",
                "message": f"Fix {non_compliant_count} non-compliant project(s)",
                "action": "assign_missing_instructors",
                "affected_projects": non_compliant_count
            })
        
        # Unassigned instructors
        unassigned_count = analysis["instructor_assignment"]["unassigned_instructors"]
        if unassigned_count > 0:
            recommendations.append({
                "type": "assign_unassigned",
                "priority": "medium",
                "message": f"Assign {unassigned_count} unassigned instructor(s) to projects",
                "action": "distribute_instructors",
                "unassigned_count": unassigned_count
            })
        
        # Over-assigned instructors
        over_assigned_count = analysis["instructor_assignment"]["over_assigned_instructors"]
        if over_assigned_count > 0:
            recommendations.append({
                "type": "balance_assignments",
                "priority": "medium",
                "message": f"Balance load for {over_assigned_count} over-assigned instructor(s)",
                "action": "redistribute_assignments",
                "over_assigned_count": over_assigned_count
            })
        
        # Jury size consistency
        total_projects = analysis["total_projects"]
        expected_jury_positions = total_projects * self.total_jury_size
        total_assigned_positions = sum(
            detail["total_assigned"] for detail in analysis["jury_compliance"]["details"]
        )
        
        if total_assigned_positions < expected_jury_positions:
            missing_positions = expected_jury_positions - total_assigned_positions
            recommendations.append({
                "type": "complete_juries",
                "priority": "high",
                "message": f"Complete {missing_positions} missing jury positions",
                "action": "assign_missing_jury_members",
                "missing_positions": missing_positions
            })
        
        return recommendations
    
    async def fix_jury_structure(self, db: AsyncSession) -> Dict[str, Any]:
        """Jüri yapısını düzeltir"""
        
        try:
            from app.models.project import Project
            from app.models.instructor import Instructor
            
            # Mevcut durumu analiz et
            analysis = await self.analyze_jury_structure(db)
            
            # Düzeltme işlemleri
            fixes_applied = []
            
            # Non-compliant projeleri düzelt
            for project_detail in analysis["jury_compliance"]["details"]:
                if not project_detail["is_compliant"]:
                    fix_result = await self._fix_project_jury(db, project_detail)
                    if fix_result["success"]:
                        fixes_applied.append(fix_result)
            
            # Unassigned instructor'ları dağıt
            unassigned_instructors = await self._get_unassigned_instructors(db)
            if unassigned_instructors:
                distribution_result = await self._distribute_unassigned_instructors(db, unassigned_instructors)
                if distribution_result["success"]:
                    fixes_applied.append(distribution_result)
            
            # Son durumu analiz et
            final_analysis = await self.analyze_jury_structure(db)
            
            return {
                "success": True,
                "message": f"Applied {len(fixes_applied)} fixes to jury structure",
                "fixes_applied": fixes_applied,
                "before_analysis": analysis,
                "after_analysis": final_analysis,
                "improvement": {
                    "compliant_projects_increase": final_analysis["jury_compliance"]["compliant_projects"] - analysis["jury_compliance"]["compliant_projects"],
                    "non_compliant_projects_decrease": analysis["jury_compliance"]["non_compliant_projects"] - final_analysis["jury_compliance"]["non_compliant_projects"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error fixing jury structure: {str(e)}")
            return {
                "success": False,
                "message": f"Error fixing jury structure: {str(e)}"
            }
    
    async def _fix_project_jury(self, db: AsyncSession, project_detail: Dict[str, Any]) -> Dict[str, Any]:
        """Tek bir projenin jüri yapısını düzeltir"""
        
        try:
            from app.models.project import Project
            
            project_id = project_detail["project_id"]
            
            # Projeyi getir
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            
            if not project:
                return {
                    "success": False,
                    "message": f"Project {project_id} not found"
                }
            
            # Eksik instructor'ları ata
            current_assigned = len(project_detail["assigned_instructors"])
            needed = self.total_jury_size - current_assigned
            
            if needed > 0:
                # Uygun instructor'ları bul
                available_instructors = await self._find_available_instructors(db, project_id)
                
                # Eksik pozisyonları doldur
                assigned_count = 0
                for instructor in available_instructors[:needed]:
                    if not project.responsible_id:
                        project.responsible_id = instructor["id"]
                        assigned_count += 1
                    elif not project.advisor_id:
                        project.advisor_id = instructor["id"]
                        assigned_count += 1
                    elif not project.co_advisor_id:
                        project.co_advisor_id = instructor["id"]
                        assigned_count += 1
                
                await db.commit()
                
                return {
                    "success": True,
                    "message": f"Assigned {assigned_count} instructors to project {project_id}",
                    "project_id": project_id,
                    "assigned_count": assigned_count
                }
            
            return {
                "success": True,
                "message": f"Project {project_id} already has complete jury",
                "project_id": project_id,
                "assigned_count": 0
            }
            
        except Exception as e:
            logger.error(f"Error fixing project jury {project_detail['project_id']}: {str(e)}")
            return {
                "success": False,
                "message": f"Error fixing project jury: {str(e)}"
            }
    
    async def _find_available_instructors(self, db: AsyncSession, exclude_project_id: int) -> List[Dict[str, Any]]:
        """Projeye atanabilecek instructor'ları bulur"""
        
        try:
            from app.models.instructor import Instructor
            from app.models.project import Project
            
            # Tüm instructor'ları getir
            result = await db.execute(select(Instructor))
            all_instructors = result.scalars().all()
            
            available_instructors = []
            
            for instructor in all_instructors:
                # Bu instructor'ın kaç projede atandığını kontrol et
                assignment_count = await self._count_instructor_assignments(db, instructor.id)
                
                # Maksimum atama sayısını kontrol et (örneğin 5 proje)
                max_assignments = 5
                if assignment_count < max_assignments:
                    available_instructors.append({
                        "id": instructor.id,
                        "name": instructor.name,
                        "type": instructor.type,
                        "current_assignments": assignment_count,
                        "available_slots": max_assignments - assignment_count
                    })
            
            # Mevcut atama sayısına göre sırala (daha az atanan önce)
            available_instructors.sort(key=lambda x: x["current_assignments"])
            
            return available_instructors
            
        except Exception as e:
            logger.error(f"Error finding available instructors: {str(e)}")
            return []
    
    async def _get_unassigned_instructors(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Atanmamış instructor'ları getirir"""
        
        try:
            from app.models.instructor import Instructor
            
            result = await db.execute(select(Instructor))
            all_instructors = result.scalars().all()
            
            unassigned = []
            
            for instructor in all_instructors:
                assignment_count = await self._count_instructor_assignments(db, instructor.id)
                
                if assignment_count == 0:
                    unassigned.append({
                        "id": instructor.id,
                        "name": instructor.name,
                        "type": instructor.type,
                        "department": instructor.department
                    })
            
            return unassigned
            
        except Exception as e:
            logger.error(f"Error getting unassigned instructors: {str(e)}")
            return []
    
    async def _distribute_unassigned_instructors(self, db: AsyncSession, 
                                              unassigned_instructors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Atanmamış instructor'ları projelere dağıtır"""
        
        try:
            from app.models.project import Project
            
            # Eksik instructor'ı olan projeleri bul
            result = await db.execute(select(Project))
            all_projects = result.scalars().all()
            
            projects_needing_instructors = []
            
            for project in all_projects:
                jury_info = await self._analyze_project_jury(db, project)
                if jury_info["total_assigned"] < self.total_jury_size:
                    projects_needing_instructors.append({
                        "project": project,
                        "jury_info": jury_info,
                        "needed": self.total_jury_size - jury_info["total_assigned"]
                    })
            
            # Instructor'ları dağıt
            distributed_count = 0
            
            for instructor in unassigned_instructors:
                for project_info in projects_needing_instructors:
                    if project_info["needed"] > 0:
                        project = project_info["project"]
                        
                        # Instructor'ı ata
                        if not project.responsible_id:
                            project.responsible_id = instructor["id"]
                        elif not project.advisor_id:
                            project.advisor_id = instructor["id"]
                        elif not project.co_advisor_id:
                            project.co_advisor_id = instructor["id"]
                        
                        project_info["needed"] -= 1
                        distributed_count += 1
                        break
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Distributed {distributed_count} unassigned instructors",
                "distributed_count": distributed_count,
                "remaining_unassigned": len(unassigned_instructors) - distributed_count
            }
            
        except Exception as e:
            logger.error(f"Error distributing unassigned instructors: {str(e)}")
            return {
                "success": False,
                "message": f"Error distributing instructors: {str(e)}"
            }
    
    async def get_jury_structure_summary(self, db: AsyncSession) -> Dict[str, Any]:
        """Jüri yapısı özetini getirir"""
        
        try:
            analysis = await self.analyze_jury_structure(db)
            
            summary = {
                "total_projects": analysis["total_projects"],
                "compliant_projects": analysis["jury_compliance"]["compliant_projects"],
                "non_compliant_projects": analysis["jury_compliance"]["non_compliant_projects"],
                "compliance_rate": (analysis["jury_compliance"]["compliant_projects"] / analysis["total_projects"]) * 100 if analysis["total_projects"] > 0 else 0,
                "jury_size_requirements": {
                    "bitirme_min": self.min_instructors_bitirme,
                    "ara_min": self.min_instructors_ara,
                    "total_jury_size": self.total_jury_size
                },
                "projects_by_type": analysis["projects_by_type"],
                "instructor_assignment": analysis["instructor_assignment"],
                "status": "healthy" if analysis["jury_compliance"]["non_compliant_projects"] == 0 else "needs_attention",
                "top_recommendations": analysis["recommendations"][:3]  # İlk 3 öneri
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting jury structure summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting jury structure summary: {str(e)}"
            }
