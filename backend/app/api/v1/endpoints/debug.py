from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, time, timedelta
import random

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.post('/generate-fake-data')
def generate_fake_data(
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Test icin sahte veri uretir.
    Sadece gelistirme ortaminda calisir.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Bu islem sadece gelistirme ortaminda kullanilabilir."
        )
    
    try:
        # Ogretim uyeleri olustur
        instructors = []
        for i in range(10):
            instructor = models.Instructor(
                name=f"Ogretim Uyesi {i+1}",
                role="hoca" if i < 7 else "aras_gor",
                bitirme_count=random.randint(2, 5),
                ara_count=random.randint(3, 8),
                department_id=1
            )
            db.add(instructor)
            db.flush()
            instructors.append(instructor)
            
        # Projeler olustur
        projects = []
        for i in range(20):
            project = models.Project(
                name=f"Proje {i+1}",
                type="bitirme" if i < 12 else "ara",
                is_makeup=False,
                responsible_id=instructors[random.randint(0, 6)].id,
                status="active",
                description=f"Bu bir {i+1} numarali test projesidir."
            )
            db.add(project)
            db.flush()
            projects.append(project)
            
        # Siniflar olustur
        classrooms = []
        for i in range(8):
            classroom = models.Classroom(
                name=f"D10{i+1}",
                capacity=30,
                location="Ana Bina"
            )
            db.add(classroom)
            db.flush()
            classrooms.append(classroom)
            
        # Zaman dilimleri olustur
        timeslots = []
        morning_starts = [time(9, 0), time(9, 30), time(10, 0), time(10, 30), time(11, 0), time(11, 30)]
        afternoon_starts = [time(13, 0), time(13, 30), time(14, 0), time(14, 30), time(15, 0), time(15, 30), time(16, 0), time(16, 30)]
        
        for t in morning_starts + afternoon_starts:
            end_time = (datetime.combine(datetime.today(), t) + timedelta(minutes=30)).time()
            timeslot = models.TimeSlot(
                start_time=t,
                end_time=end_time
            )
            db.add(timeslot)
            db.flush()
            timeslots.append(timeslot)
            
        # Planlamalar olustur
        for i in range(10):
            project = projects[i]
            classroom = classrooms[random.randint(0, 7)]
            timeslot = timeslots[random.randint(0, len(timeslots)-1)]
            
            # Proje katilimcilari
            participants = []
            participants.append(project.responsible_id)  # Sorumlu hoca
            
            # Bitirme projesi icin en az 2 hoca gerekli
            if project.type == "bitirme":
                # Ikinci hoca
                available_instructors = [ins.id for ins in instructors if ins.role == "hoca" and ins.id != project.responsible_id]
                participants.append(random.choice(available_instructors))
                
                # Ucuncu kisi (hoca veya aras. gor.)
                available_instructors = [ins.id for ins in instructors if ins.id not in participants]
                participants.append(random.choice(available_instructors))
            else:
                # Ara proje icin en az 1 hoca yeterli (zaten sorumlu hoca var)
                # Ikinci ve ucuncu kisi
                for _ in range(2):
                    available_instructors = [ins.id for ins in instructors if ins.id not in participants]
                    participants.append(random.choice(available_instructors))
            
            schedule = models.Schedule(
                project_id=project.id,
                classroom_id=classroom.id,
                timeslot_id=timeslot.id,
                instructor_ids=participants
            )
            db.add(schedule)
            
        # Algoritma calistirma ornekleri
        algorithms = ["genetic", "simulated_annealing", "ant_colony"]
        for alg in algorithms:
            algorithm_run = models.AlgorithmRun(
                algorithm=alg,
                params={"iterations": 100},
                status="completed",
                result='{"assignments": [1, 2, 3], "quality": 0.85}',
                execution_time=random.uniform(0.5, 5.0),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
                started_at=datetime.utcnow() - timedelta(days=random.randint(1, 10), minutes=-30),
                completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 10), minutes=-15)
            )
            db.add(algorithm_run)
        
        db.commit()
        
        return {
            'status': 'success', 
            'message': 'Sahte veri uretimi tamamlandi',
            'data': {
                'instructors': len(instructors),
                'projects': len(projects),
                'classrooms': len(classrooms),
                'timeslots': len(timeslots),
                'algorithms': len(algorithms)
            }
        }
    except Exception as e:
        db.rollback()
        return {
            'status': 'error',
            'message': f'Sahte veri uretimi basarisiz: {str(e)}'
        }


@router.post('/reset-db')
def reset_db(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Veritabanini sifirlar.
    Sadece gelistirme ortaminda calisir.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Bu islem sadece gelistirme ortaminda kullanilabilir."
        )
    
    try:
        # Tum tablolari temizle
        db.execute("TRUNCATE TABLE schedules CASCADE")
        db.execute("TRUNCATE TABLE timeslots CASCADE")
        db.execute("TRUNCATE TABLE classrooms CASCADE")
        db.execute("TRUNCATE TABLE projects CASCADE")
        db.execute("TRUNCATE TABLE instructors CASCADE")
        db.execute("TRUNCATE TABLE algorithm_runs CASCADE")
        db.execute("TRUNCATE TABLE audit_logs CASCADE")
        db.commit()
        
        return {
            'status': 'success',
            'message': 'Veritabani basariyla sifirlandi'
        }
    except Exception as e:
        db.rollback()
        return {
            'status': 'error',
            'message': f'Veritabani sifirlama basarisiz: {str(e)}'
        }
