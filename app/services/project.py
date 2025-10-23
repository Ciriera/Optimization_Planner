from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.base import BaseService
from app.services.instructor import InstructorService
from typing import Dict

class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self):
        super().__init__(Project)
        self.instructor_service = InstructorService()

    async def create_with_instructors(self, db: AsyncSession, *, obj_in: ProjectCreate) -> Project:
        """Proje ve öğretim elemanı ilişkilerini oluşturma"""
        # Proje oluştur
        db_obj = Project(
            title=obj_in.title,
            type=obj_in.type,
            is_makeup=obj_in.is_makeup,
            status=ProjectStatus.ACTIVE,
            responsible_id=obj_in.responsible_id,
            remaining_students=obj_in.remaining_students
        )
        
        # Güvenlik: Sorumlu ile aynı olan veya tekrar eden asistanları temizle
        try:
            cleaned_assistant_ids = []
            seen = set()
            for a_id in (obj_in.assistant_ids or []):
                if a_id and a_id != obj_in.responsible_id and a_id not in seen:
                    cleaned_assistant_ids.append(a_id)
                    seen.add(a_id)
        except Exception:
            cleaned_assistant_ids = obj_in.assistant_ids or []

        # Sorumlu hocanın yükünü güncelle
        if obj_in.type == "bitirme":
            await self.instructor_service.update_load_counts(db, obj_in.responsible_id, bitirme_delta=1)
        else:
            await self.instructor_service.update_load_counts(db, obj_in.responsible_id, ara_delta=1)
        
        # Asistanları ekle
        for assistant_id in cleaned_assistant_ids:
            assistant = await self.instructor_service.get(db, assistant_id)
            if assistant:
                db_obj.assistants.append(assistant)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: Project, obj_in: Union[ProjectUpdate, Dict[str, Any]]) -> Project:
        """
        Proje güncelleme - assistant_ids desteği ile
        """
        from sqlalchemy import delete
        
        # Base update işlemini yap
        updated_project = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        
        # assistant_ids varsa özel işlem yap
        if hasattr(obj_in, 'assistant_ids') and obj_in.assistant_ids is not None:
            # Mevcut assistant linklerini temizle
            from app.models.project import project_assistants
            await db.execute(
                delete(project_assistants).where(project_assistants.c.project_id == db_obj.id)
            )
            
            # Yeni assistant linklerini ekle
            for assistant_id in obj_in.assistant_ids:
                # Sorumlu ile çakışma kontrolü
                if assistant_id != db_obj.responsible_id:
                    await db.execute(
                        project_assistants.insert().values(
                            project_id=db_obj.id,
                            instructor_id=assistant_id
                        )
                    )
        
        await db.commit()
        await db.refresh(updated_project)
        return updated_project

    async def cleanup_jury_conflicts(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Jüri çakışmalarını temizler:
        - Sorumlu öğretim üyesi asistan listesinde yer alamaz
        - Asistan listesi benzersiz tutulur
        Log: app/logs/fixes.log
        """
        from sqlalchemy import select
        import os, datetime

        # Sadece gerekli alanları çek (lazy-load tetiklememek için)
        result = await db.execute(select(Project.id, Project.responsible_id))
        rows = result.all()
        total = len(rows)
        fixed_projects = 0
        removed_links = 0

        # Association table üzerinden doğrudan temizlik yap
        from sqlalchemy import delete
        from app.models.project import project_assistants

        for pid, rid in rows:
            if not rid:
                continue
            del_stmt = delete(project_assistants).where(
                (project_assistants.c.project_id == pid) &
                (project_assistants.c.instructor_id == rid)
            )
            res = await db.execute(del_stmt)
            if res.rowcount and res.rowcount > 0:
                fixed_projects += 1
                removed_links += res.rowcount or 0

        await db.commit()

        # fixes.log dosyasına yaz
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            log_dir = os.path.abspath(log_dir)
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "fixes.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.datetime.utcnow().isoformat()}] jury_cleanup: projects={total}, fixed={fixed_projects}, removed_links={removed_links}\n"
                )
        except Exception:
            pass

        return {
            "total_projects": total,
            "fixed_projects": fixed_projects,
            "removed_links": removed_links,
            "status": "ok"
        }

    async def reconcile_instructor_references(self, db: AsyncSession, reassign_missing: bool = True) -> Dict[str, Any]:
        """
        Tüm projelerdeki sorumlu/danışman/katılımcı alanlarını Instructor tablosu ile
        karşılaştırır. Instructor listesinde olmayan ID'leri temizler veya en az yüklü
        hocaya yeniden atar. Ayrıca association tablosundaki geçersiz kayıtları da temizler.

        Dönüş: özet istatistikler ve fixes.log'a kayıt
        """
        from sqlalchemy import select, delete, func
        from app.models.instructor import Instructor
        from app.models.project import project_assistants
        import os, datetime

        # Geçerli instructor id'lerini çek
        res_inst = await db.execute(select(Instructor.id))
        valid_instructor_ids = set([row[0] for row in res_inst.all()])

        # Proje alanlarını hafif çek
        res_proj = await db.execute(
            select(
                Project.id,
                Project.title,
                Project.responsible_id,
                Project.advisor_id,
                Project.co_advisor_id,
                Project.second_participant_id,
                Project.third_participant_id,
                Project.type
            )
        )
        rows = res_proj.all()

        # Yük hesapla (sadece responsible üzerinden)
        res_load = await db.execute(
            select(Project.responsible_id, func.count())
            .where(Project.responsible_id.isnot(None))
            .group_by(Project.responsible_id)
        )
        load_map: Dict[int, int] = {rid: cnt for rid, cnt in res_load.all()}

        def pick_least_loaded() -> int:
            if not valid_instructor_ids:
                return None  # type: ignore
            # Varsayılan 0 yük
            candidate = None
            best = 10**9
            for iid in valid_instructor_ids:
                current = load_map.get(iid, 0)
                if current < best:
                    best = current
                    candidate = iid
            if candidate is not None:
                load_map[candidate] = load_map.get(candidate, 0) + 1
            return candidate  # type: ignore

        fixed_responsible = 0
        nulled_refs = 0
        reassigned_refs = 0
        cleaned_assist_links = 0

        for (pid, _title, rid, aid, coid, spid, tpid, _ptype) in rows:
            project_changed = False

            # Helper to validate a single field
            async def fix_field(field_name: str, current_value: Any) -> Any:
                nonlocal nulled_refs, reassigned_refs, project_changed, fixed_responsible
                if current_value and current_value not in valid_instructor_ids:
                    # Missing instructor
                    if field_name == "responsible_id" and reassign_missing:
                        new_id = pick_least_loaded()
                        setattr(project, field_name, new_id)
                        reassigned_refs += 1
                        fixed_responsible += 1
                        project_changed = True
                        return new_id
                    else:
                        setattr(project, field_name, None)
                        nulled_refs += 1
                        project_changed = True
                        return None
                return current_value

            # Proje nesnesini yükle (sadece güncellemek için)
            project = await self.get(db, pid)
            if not project:
                continue

            # Alanları doğrula
            rid = await fix_field("responsible_id", project.responsible_id)
            aid = await fix_field("advisor_id", project.advisor_id)
            coid = await fix_field("co_advisor_id", project.co_advisor_id)
            spid = await fix_field("second_participant_id", project.second_participant_id)
            tpid = await fix_field("third_participant_id", project.third_participant_id)

            if project_changed:
                db.add(project)

            # Association table: invalid assistant links (including responsible) sil
            del_stmt = delete(project_assistants).where(
                (project_assistants.c.project_id == pid) &
                (~project_assistants.c.instructor_id.in_(valid_instructor_ids))
            )
            res = await db.execute(del_stmt)
            cleaned_assist_links += res.rowcount or 0

            # Responsible ile çakışan linkleri temizle
            if rid:
                del_stmt2 = delete(project_assistants).where(
                    (project_assistants.c.project_id == pid) &
                    (project_assistants.c.instructor_id == rid)
                )
                res2 = await db.execute(del_stmt2)
                cleaned_assist_links += res2.rowcount or 0

        await db.commit()

        # fixes.log
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            log_dir = os.path.abspath(log_dir)
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "fixes.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.datetime.utcnow().isoformat()}] reconcile_instructors: projects={len(rows)}, fixed_responsible={fixed_responsible}, nulled_refs={nulled_refs}, reassigned_refs={reassigned_refs}, cleaned_assistant_links={cleaned_assist_links}\n"
                )
        except Exception:
            pass

        return {
            "projects_scanned": len(rows),
            "fixed_responsible": fixed_responsible,
            "nulled_refs": nulled_refs,
            "reassigned_refs": reassigned_refs,
            "cleaned_assistant_links": cleaned_assist_links,
            "status": "ok"
        }

    async def get_with_relations(self, db: AsyncSession, id: int) -> Optional[Project]:
        """İlişkili verilerle birlikte proje getirme"""
        result = await db.execute(
            select(Project)
            .options(
                selectinload(Project.responsible_instructor),
                selectinload(Project.assistants),
                selectinload(Project.schedule)
            )
            .filter(Project.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_instructor(self, db: AsyncSession, instructor_id: int) -> List[Project]:
        """Öğretim elemanının projelerini getirme"""
        from sqlalchemy.sql.expression import or_
        result = await db.execute(
            select(Project)
            .filter(
                or_(
                    Project.responsible_id == instructor_id,
                    Project.assistants.any(id=instructor_id)
                )
            )
        )
        return result.scalars().all()

    async def mark_as_makeup(self, db: AsyncSession, id: int, remaining_students: int) -> Project:
        """Projeyi bütünleme olarak işaretleme"""
        project = await self.get(db, id)
        if project:
            project.is_makeup = True
            project.remaining_students = remaining_students
            project.status = ProjectStatus.MAKEUP
            db.add(project)
            await db.commit()
            await db.refresh(project)
        return project

    async def get_projects_by_type(self, db: AsyncSession, project_type: str, is_makeup: bool = False) -> List[Project]:
        """Türe göre projeleri getirme"""
        result = await db.execute(
            select(Project)
            .filter(Project.type == project_type)
            .filter(Project.is_makeup == is_makeup)
        )
        return result.scalars().all()
    
    async def validate_project_rules(self, db: AsyncSession, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proje kurallarına uygunluğunu validate eder.
        Proje açıklamasına göre: Her projede 3 kişi, 1. kişi zorunlu hoca, 2. ve 3. kişi hoca veya araştırma görevlisi
        """
        errors = []
        warnings = []
        
        # Kural 1: Her projede 3 kişi olmalı
        participant_count = 0
        if project_data.get("responsible_id"):
            participant_count += 1
        if project_data.get("second_participant_id"):
            participant_count += 1
        if project_data.get("third_participant_id"):
            participant_count += 1
        
        if participant_count != 3:
            errors.append(f"Project must have exactly 3 participants, currently has {participant_count}")
        
        # Kural 2: İlk kişi zorunlu olarak hoca olmalı
        if project_data.get("responsible_id"):
            from app.services.instructor import InstructorService
            instructor_service = InstructorService()
            responsible = await instructor_service.get(db, project_data["responsible_id"])
            if responsible and responsible.type != "instructor":
                errors.append("First participant (responsible) must be an instructor")
        
        # Proje tipine göre kurallar
        project_type = project_data.get("type")
        if project_type == "bitirme":
            # Kural 3: Bitirme projesinde en az 2 hoca olmalı
            instructor_count = 0
            for field in ["responsible_id", "second_participant_id", "third_participant_id"]:
                if project_data.get(field):
                    instructor = await instructor_service.get(db, project_data[field])
                    if instructor and instructor.type == "instructor":
                        instructor_count += 1
            
            if instructor_count < 2:
                errors.append(f"Bitirme project must have at least 2 instructors, currently has {instructor_count}")
                
        elif project_type == "ara":
            # Kural 4: Ara projede en az 1 hoca olmalı
            instructor_count = 0
            for field in ["responsible_id", "second_participant_id", "third_participant_id"]:
                if project_data.get(field):
                    instructor = await instructor_service.get(db, project_data[field])
                    if instructor and instructor.type == "instructor":
                        instructor_count += 1
            
            if instructor_count < 1:
                errors.append(f"Ara project must have at least 1 instructor, currently has {instructor_count}")
        
        # Uyarılar
        if instructor_count == 3:
            warnings.append("All 3 participants are instructors (no research assistants)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "participant_count": participant_count,
            "instructor_count": instructor_count,
            "project_specification_compliant": len(errors) == 0
        }
    
    async def create_with_validation(self, db: AsyncSession, *, obj_in: ProjectCreate) -> Project:
        """
        Proje kurallarına uygunluk kontrolü yaparak proje oluşturur.
        """
        # Validation yap
        project_data = obj_in.dict()
        validation_result = await self.validate_project_rules(db, project_data)
        
        if not validation_result["valid"]:
            raise ValueError(f"Project validation failed: {'; '.join(validation_result['errors'])}")
        
        # Proje oluştur
        project = await self.create(db, obj_in=obj_in)
        
        # Uyarıları logla
        if validation_result["warnings"]:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Project {project.id} created with warnings: {'; '.join(validation_result['warnings'])}")
        
        return project 