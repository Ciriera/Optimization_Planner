from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/public", response_model=List[schemas.Project])
def read_projects_public(
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Tüm projeleri getir (public, no authentication required).
    """
    from app.db.session import SessionLocal
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    try:
        # İlişkili verileri yükle (assistant_instructors, responsible_instructor)
        projects = (
            db.query(models.Project)
            .options(
                joinedload(models.Project.assistant_instructors),
                joinedload(models.Project.responsible_instructor)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Assistant instructors'ları serialize et
        result = []
        for project in projects:
            project_dict = {
                "id": project.id,
                "title": project.title,
                "type": project.type,
                "is_makeup": project.is_makeup,
                "status": project.status,
                "responsible_instructor_id": project.responsible_instructor_id,
                "assistant_instructors": [
                    {
                        "id": ai.id,
                        "name": ai.name,
                        "role": ai.role,
                        "full_name": getattr(ai, 'full_name', ai.name)
                    }
                    for ai in (project.assistant_instructors or [])
                ]
            }
            result.append(project_dict)
        
        return result
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Project])
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Tüm projeleri getir.
    """
    # İlişkili verileri yükle (assistant_instructors, responsible_instructor)
    projects = (
        db.query(models.Project)
        .options(
            joinedload(models.Project.assistant_instructors),
            joinedload(models.Project.responsible_instructor)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Assistant instructors'ları serialize et
    result = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "title": project.title,
            "type": project.type,
            "is_makeup": project.is_makeup,
            "status": project.status,
            "responsible_instructor_id": project.responsible_instructor_id,
            "assistant_instructors": [
                {
                    "id": ai.id,
                    "name": ai.name,
                    "role": ai.role,
                    "full_name": getattr(ai, 'full_name', ai.name)
                }
                for ai in (project.assistant_instructors or [])
            ]
        }
        result.append(project_dict)
    
    return result

@router.post("/", response_model=schemas.Project)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Yeni proje oluştur.
    """
    project = crud.project.create(db=db, obj_in=project_in)
    return project

@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: schemas.ProjectUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Proje bilgilerini güncelle.
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    project = crud.project.update(db=db, db_obj=project, obj_in=project_in)
    return project

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Proje bilgilerini getir.
    """
    # İlişkili verileri yükle
    project = (
        db.query(models.Project)
        .options(
            joinedload(models.Project.assistant_instructors),
            joinedload(models.Project.responsible_instructor)
        )
        .filter(models.Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    return project

@router.delete("/{project_id}", response_model=schemas.Project)
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Projeyi sil.
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    project = crud.project.remove(db=db, id=project_id)
    return project

@router.post("/assign-jury/{project_id}")
def assign_jury_to_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Belirli bir proje için jüri ataması yap.
    Kurallar:
    - Sorumlu hoca her zaman jüri üyesi
    - Ara projelerde en az 1 hoca, bitirme projelerde en az 2 hoca
    - Hocalar aynı sınıfta kalmaya öncelik
    - Asistanlar sınıf değiştirebilir
    """
    # Projeyi bul
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    
    # Tüm öğretim üyelerini getir
    instructors = crud.instructor.get_multi(db=db)
    if not instructors:
        raise HTTPException(
            status_code=400,
            detail="No instructors found",
        )
    
    # Hoca ve asistan ayrımı yap
    senior_ids = [i.id for i in instructors if i.role == "hoca"]
    assistant_ids = [i.id for i in instructors if i.role == "aras_gor"]
    
    # Jüri listesi başlat (sorumlu hoca her zaman dahil)
    jury = []
    responsible_id = project.responsible_instructor_id
    
    if responsible_id:
        jury.append(responsible_id)
    
    # Bitirme projeleri için en az 2 hoca, ara projeler için en az 1 hoca
    min_senior_needed = 2 if project.type == "final" else 1
    senior_count = 1 if responsible_id in senior_ids else 0
    
    # Eksik hoca sayısını tamamla
    available_seniors = [i for i in senior_ids if i != responsible_id]
    
    for senior_id in available_seniors:
        if senior_count >= min_senior_needed:
            break
        jury.append(senior_id)
        senior_count += 1
    
    # Kalan jüri üyelerini asistanlardan doldur (3'e tamamlamak için)
    assistants = [i for i in assistant_ids if i not in jury]
    needed_assistants = 3 - len(jury)
    
    for i, assistant_id in enumerate(assistants[:needed_assistants]):
        if len(jury) >= 3:
            break
        jury.append(assistant_id)
    
    # Mevcut jüri atamalarını temizle
    if project.assistant_instructors:
        project.assistant_instructors.clear()
    
    # Yeni jüri atamalarını yap (sorumlu hariç)
    jury_without_responsible = [j for j in jury if j != responsible_id]
    if jury_without_responsible:
        assistant_instructors = db.query(models.Instructor).filter(
            models.Instructor.id.in_(jury_without_responsible)
        ).all()
        project.assistant_instructors = assistant_instructors
    
    db.commit()
    db.refresh(project)
    
    return {
        "project_id": project_id,
        "jury": jury,
        "responsible_instructor_id": responsible_id,
        "assistant_instructor_ids": jury_without_responsible,
        "message": f"Jury assigned successfully. Total members: {len(jury)}"
    }

@router.post("/assign-jury-balanced")
def assign_jury_balanced_to_all_projects(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Tüm projeler için dengeli jüri ataması yap.
    Kurallar:
    - Sorumlu hoca her zaman jüri üyesi
    - Ara projelerde en az 1 hoca, bitirme projelerde en az 2 hoca
    - Maksimum 2 fark olacak şekilde dengeli dağıtım
    """
    projects = crud.project.get_multi(db=db)
    instructors = crud.instructor.get_multi(db=db)
    
    if not instructors:
        raise HTTPException(
            status_code=400,
            detail="No instructors found",
        )
    
    # Hoca ve asistan ayrımı yap
    senior_ids = [i.id for i in instructors if i.role == "hoca"]
    assistant_ids = [i.id for i in instructors if i.role == "aras_gor"]
    
    # Yük takibi için
    instructor_load = {i.id: 0 for i in instructors}
    
    results = []
    
    for project in projects:
        try:
            # Jüri listesi başlat (sorumlu hoca her zaman dahil)
            jury = []
            responsible_id = project.responsible_instructor_id
            
            if responsible_id:
                jury.append(responsible_id)
            
            # Bitirme projeleri için en az 2 hoca, ara projeler için en az 1 hoca
            min_senior_needed = 2 if project.type == "final" else 1
            senior_count = 1 if responsible_id in senior_ids else 0
            
            # Eksik hoca sayısını tamamla
            available_seniors = [i for i in senior_ids if i != responsible_id]
            
            for senior_id in available_seniors:
                if senior_count >= min_senior_needed:
                    break
                jury.append(senior_id)
                senior_count += 1
                instructor_load[senior_id] += 1
            
            # Kalan jüri üyelerini asistanlardan doldur (dengeli dağıtım)
            assistants = [i for i in assistant_ids if i not in jury]
            needed_assistants = 3 - len(jury)
            
            # Dengeli dağıtım: Maksimum 2 fark olacak şekilde seç
            assistant_loads = {a_id: instructor_load[a_id] for a_id in assistants}
            sorted_assistants = sorted(assistant_loads.items(), key=lambda x: x[1])
            
            for assistant_id, current_load in sorted_assistants:
                if len(jury) >= 3:
                    break
                
                # Maksimum 2 fark kuralını kontrol et
                max_load = max(instructor_load.values()) if instructor_load else 0
                if current_load <= max_load + 2:  # Maksimum 2 fark
                    jury.append(assistant_id)
                    instructor_load[assistant_id] += 1
            
            # Mevcut jüri atamalarını temizle
            if project.assistant_instructors:
                project.assistant_instructors.clear()
            
            # Yeni jüri atamalarını yap (sorumlu hariç)
            jury_without_responsible = [j for j in jury if j != responsible_id]
            if jury_without_responsible:
                assistant_instructors = db.query(models.Instructor).filter(
                    models.Instructor.id.in_(jury_without_responsible)
                ).all()
                project.assistant_instructors = assistant_instructors
            
            results.append({
                "project_id": project.id,
                "jury": jury,
                "responsible_instructor_id": responsible_id,
                "assistant_instructor_ids": jury_without_responsible,
                "load_distribution": {k: v for k, v in instructor_load.items() if v > 0}
            })
            
        except Exception as e:
            results.append({
                "project_id": project.id,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_projects": len(projects),
        "successful_assignments": len([r for r in results if "error" not in r]),
        "load_distribution": instructor_load,
        "results": results
    } 