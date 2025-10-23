from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import json
from typing import Any, List, Dict

from app import crud, models, schemas
from app.api import deps
from app.services.algorithm import run_algorithm

router = APIRouter()

# --- helpers ---

def _check_jury_conflicts(db: Session, schedules: List[Dict[str, Any]]) -> int:
    """
    Jüri çakışmalarını kontrol eder. Aynı jüri üyesi aynı saatte farklı sınıflarda olamaz.
    """
    conflicts = 0
    instructor_timeslots = {}  # {instructor_id: [timeslot_id, classroom_id]}
    
    for schedule in schedules:
        project_id = schedule.get('project_id')
        timeslot_id = schedule.get('timeslot_id')
        classroom_id = schedule.get('classroom_id')
        
        if not all([project_id, timeslot_id, classroom_id]):
            continue
            
        # Projeyi al ve jüri üyelerini bul
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            continue
            
        # Sorumlu öğretim üyesi
        responsible_id = project.responsible_instructor_id
        if responsible_id:
            if responsible_id not in instructor_timeslots:
                instructor_timeslots[responsible_id] = []
            
            # Aynı saatte başka sınıfta mı kontrol et
            for existing_time, existing_class in instructor_timeslots[responsible_id]:
                if existing_time == timeslot_id and existing_class != classroom_id:
                    conflicts += 1
                    print(f"ÇAKIŞMA: Öğretim üyesi {responsible_id} aynı saatte {existing_class} ve {classroom_id} sınıflarında")
            
            instructor_timeslots[responsible_id].append((timeslot_id, classroom_id))
        
        # Assistant instructors
        for assistant in project.assistant_instructors:
            assistant_id = assistant.id
            if assistant_id not in instructor_timeslots:
                instructor_timeslots[assistant_id] = []
            
            # Aynı saatte başka sınıfta mı kontrol et
            for existing_time, existing_class in instructor_timeslots[assistant_id]:
                if existing_time == timeslot_id and existing_class != classroom_id:
                    conflicts += 1
                    print(f"ÇAKIŞMA: Öğretim üyesi {assistant_id} aynı saatte {existing_class} ve {classroom_id} sınıflarında")
            
            instructor_timeslots[assistant_id].append((timeslot_id, classroom_id))
    
    return conflicts

def _generate_fallback_assignments(db: Session) -> List[Dict[str, Any]]:
	"""
	YENİ ÇAKIŞMASIZ ALGORİTMA: Saat bazında instructor takibi ile dengeli dağıtım
	"""
	import time
	import random
	from app import crud, models, schemas
	from app.models.timeslot import TimeSlot
	from app.models.instructor import Instructor
	from app.models.classroom import Classroom
	from app.models.project import Project
	from typing import Dict, List, Any, Set
	
	# Her çalıştırmada farklı sonuç için random seed
	random.seed(int(time.time() * 1000) % 2**32)
	
	# Verileri getir
	projects = db.query(Project).all()
	classrooms = db.query(Classroom).all()
	timeslots = db.query(TimeSlot).order_by(TimeSlot.start_time).all()
	instructors = db.query(Instructor).all()

	# Hoca/asistan ayrımı
	def is_senior(role):
		try:
			r = (role or '').lower()
			return any(keyword in r for keyword in ['prof', 'doç', 'dr. öğr'])
		except Exception:
			return False

	hocalar = [i for i in instructors if is_senior(getattr(i, 'role', None))]
	asistanlar = [i for i in instructors if not is_senior(getattr(i, 'role', None))]
	
	print(f"DEBUG: {len(hocalar)} hoca, {len(asistanlar)} asistan")
	print(f"DEBUG: {len(projects)} proje, {len(classrooms)} sınıf, {len(timeslots)} zaman dilimi")

	# SAAT BAZINDA INSTRUCTOR TAKİBİ - ÇAKIŞMA ÖNLEME
	timeslot_instructors: Dict[int, Set[int]] = {}  # {timeslot_id: {instructor_ids}}
	
	# Yük takibi - SADECE ASSISTANT JÜRİ ÜYELİĞİ
	hoca_load: Dict[int, int] = {hoca.id: 0 for hoca in hocalar}
	asistan_load: Dict[int, int] = {asistan.id: 0 for asistan in asistanlar}
	
	# Sınıf boşlukları
	class_free_slots: Dict[int, List[int]] = {c.id: [] for c in classrooms}
	for c in classrooms:
		for ts in timeslots:
			if not crud.schedule.get_by_classroom_and_timeslot(db, classroom_id=c.id, timeslot_id=ts.id):
				class_free_slots[c.id].append(ts.id)
	
	generated: List[Dict[str, Any]] = []
	
	# TÜM PROJELERİ RASTGELE SIRALAYIP İŞLE - FARKLI DÜZENLER İÇİN
	random.shuffle(projects)
	
	for proj in projects:
		responsible_id = getattr(proj, 'responsible_instructor_id', None)
		
		# En uygun sınıf ve zaman bul - RASTGELE SIRALAMA İLE
		best_classroom = None
		best_timeslot = None
		
		# Sınıfları rastgele sırala
		available_classrooms = [(classroom_id, available_times) for classroom_id, available_times in class_free_slots.items() if available_times]
		random.shuffle(available_classrooms)
		
		for classroom_id, available_times in available_classrooms:
			# Zaman dilimlerini de rastgele sırala
			random.shuffle(available_times)
			
			for timeslot_id in available_times:
				# Responsible instructor çakışıyor mu?
				if timeslot_id in timeslot_instructors and responsible_id in timeslot_instructors[timeslot_id]:
					continue
				
				best_classroom = classroom_id
				best_timeslot = timeslot_id
				break
			
			if best_classroom is not None:
				break
		
		if best_classroom is None or best_timeslot is None:
			print(f"UYARI: Proje {proj.id} için uygun sınıf/zaman bulunamadı!")
			continue
		
		# Bu zaman dilimini kullan
		class_free_slots[best_classroom].remove(best_timeslot)
		
		# Saat takibini başlat
		if best_timeslot not in timeslot_instructors:
			timeslot_instructors[best_timeslot] = set()
		
		# Responsible instructor'ı ekle
		if responsible_id:
			timeslot_instructors[best_timeslot].add(responsible_id)
		
		# Jüri oluştur
		jury = [responsible_id] if responsible_id else []
		
		# HOCA SEÇİMİ - ÇAKIŞMA KONTROLÜ İLE
		min_senior_needed = 2 if str(getattr(proj, 'type', 'interim')) == 'final' else 1
		senior_count = 1 if responsible_id and responsible_id in [h.id for h in hocalar] else 0
		
		# Kullanılabilir hocaları filtrele (çakışma olmayanlar)
		available_hocalar = []
		for hoca in hocalar:
			if (hoca.id != responsible_id and 
				hoca.id not in timeslot_instructors[best_timeslot]):
				available_hocalar.append(hoca)
		
		# Hocaları YÜK SIRALAMASINA GÖRE seç - EN AZ YÜKLÜ ÖNCE
		available_hocalar.sort(key=lambda x: hoca_load.get(x.id, 0))
		
		# Hocaları seç - sadece en az yüklü olanları seç
		for hoca in available_hocalar:
			if senior_count >= min_senior_needed:
				break
			
			# Yük dengesizliği kontrolü - eğer bu hocanın yükü çok yüksekse atla
			current_hoca_load = hoca_load.get(hoca.id, 0)
			min_hoca_load = min(hoca_load.values()) if hoca_load.values() else 0
			
			if current_hoca_load - min_hoca_load > 2:  # Maksimum 2 fark
				continue  # Bu hocayı atla, daha az yüklü birini bul
			
			jury.append(hoca.id)
			hoca_load[hoca.id] = hoca_load.get(hoca.id, 0) + 1
			timeslot_instructors[best_timeslot].add(hoca.id)
			senior_count += 1
		
		# ASİSTAN SEÇİMİ - ÇAKIŞMA KONTROLÜ İLE
		# Kullanılabilir asistanları filtrele (çakışma olmayanlar)
		available_asistanlar = []
		for asistan in asistanlar:
			if (asistan.id not in jury and 
				asistan.id not in timeslot_instructors[best_timeslot]):
				available_asistanlar.append(asistan)
		
		# Asistanları YÜK SIRALAMASINA GÖRE seç - EN AZ YÜKLÜ ÖNCE
		available_asistanlar.sort(key=lambda x: asistan_load.get(x.id, 0))
		
		# Asistanları seç - yük dengesizliği kontrolü ile
		for asistan in available_asistanlar:
			if len(jury) >= 3:
				break
			
			# Yük dengesizliği kontrolü - eğer bu asistanın yükü çok yüksekse atla
			current_asistan_load = asistan_load.get(asistan.id, 0)
			min_asistan_load = min(asistan_load.values()) if asistan_load.values() else 0
			
			if current_asistan_load - min_asistan_load > 2:  # Maksimum 2 fark
				continue  # Bu asistanı atla, daha az yüklü birini bul
			
			jury.append(asistan.id)
			asistan_load[asistan.id] = asistan_load.get(asistan.id, 0) + 1
			timeslot_instructors[best_timeslot].add(asistan.id)
		
		# Eğer hala 3'den az jüri varsa, zorunlu ekle - YÜK DENGESİZLİĞİ KONTROLÜ İLE
		if len(jury) < 3:
			all_instructors = [i for i in instructors if i.id not in jury and i.id not in timeslot_instructors[best_timeslot]]
			
			# Önce yük dengesizliği kontrolü yaparak seç
			for instructor in all_instructors:
				if len(jury) >= 3:
					break
				
				# Instructor tipine göre yük kontrolü
				if is_senior(instructor.role):
					current_load = hoca_load.get(instructor.id, 0)
					min_load = min(hoca_load.values()) if hoca_load.values() else 0
					if current_load - min_load > 2:
						continue  # Bu hocayı atla
					hoca_load[instructor.id] = current_load + 1
				else:
					current_load = asistan_load.get(instructor.id, 0)
					min_load = min(asistan_load.values()) if asistan_load.values() else 0
					if current_load - min_load > 2:
						continue  # Bu asistanı atla
					asistan_load[instructor.id] = current_load + 1
				
				jury.append(instructor.id)
				timeslot_instructors[best_timeslot].add(instructor.id)
			
			# Eğer hala yeterli jüri yoksa, yük kontrolü olmadan zorunlu ekle
			if len(jury) < 3:
				for instructor in all_instructors:
					if len(jury) >= 3:
						break
					if instructor.id not in jury:
						jury.append(instructor.id)
						timeslot_instructors[best_timeslot].add(instructor.id)
		
		print(f"DEBUG: Proje {proj.id} -> Sınıf {best_classroom}, Zaman {best_timeslot}")
		print(f"DEBUG: Proje {proj.id} jüri: {jury} (toplam: {len(jury)})")
		
		# Schedule oluştur
		generated.append({
			'project_id': proj.id,
			'classroom_id': best_classroom,
			'timeslot_id': best_timeslot
		})
		
		# Jüri atamalarını veritabanına kaydet
		try:
			if proj.assistant_instructors:
				proj.assistant_instructors.clear()
			
			jury_without_responsible = [j for j in jury if j != responsible_id]
			if jury_without_responsible:
				assistant_instructors = db.query(models.Instructor).filter(
					models.Instructor.id.in_(jury_without_responsible)
				).all()
				proj.assistant_instructors = assistant_instructors
			
			db.commit()
			print(f"Jüri ataması başarılı - Proje {proj.id}, Jüri: {jury} (toplam: {len(jury)})")
		except Exception as e:
			print(f"Jüri atama hatası proje {proj.id}: {e}")
			db.rollback()
	
	# Yük dağılımını rapor et
	print("=== YÜK DAĞILIMI RAPORU ===")
	print("HOCALAR:")
	for hoca in hocalar:
		print(f"  {hoca.id}: {hoca_load[hoca.id]} assistant jüri")
	print("ASİSTANLAR:")
	for asistan in asistanlar:
		print(f"  {asistan.id}: {asistan_load[asistan.id]} assistant jüri")
	
	hoca_max = max(hoca_load.values()) if hoca_load.values() else 0
	hoca_min = min(hoca_load.values()) if hoca_load.values() else 0
	asistan_max = max(asistan_load.values()) if asistan_load.values() else 0
	asistan_min = min(asistan_load.values()) if asistan_load.values() else 0
	
	print(f"HOCALAR ARASI YÜK FARKI: {hoca_max} - {hoca_min} = {hoca_max - hoca_min}")
	print(f"ASİSTANLAR ARASI YÜK FARKI: {asistan_max} - {asistan_min} = {asistan_max - asistan_min}")
	
	print(f"DEBUG: Toplam {len(generated)} atama oluşturuldu")
	return generated


@router.get("/list", response_model=List[str])
def list_algorithms() -> Any:
    """
    List available algorithms.
    """
    from app.services.algorithm import AlgorithmService
    from app.db.session import get_db
    
    # Get database session
    db = next(get_db())
    service = AlgorithmService(db)
    algorithms = service.get_available_algorithms()
    
    # Return algorithm IDs
    return [alg["id"] for alg in algorithms]


@router.get("/public-list", response_model=List[str])
def public_list_algorithms() -> Any:
    """
    Public list of available algorithms (no authentication required).
    """
    from app.services.algorithm import AlgorithmService
    from app.db.session import get_db
    
    # Get database session
    db = next(get_db())
    service = AlgorithmService(db)
    algorithms = service.get_available_algorithms()
    
    # Return algorithm IDs
    return [alg["id"] for alg in algorithms]


@router.post("/execute", response_model=schemas.AlgorithmRun)
async def execute_algorithm(
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    algorithm_in: schemas.AlgorithmExecuteRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Execute an algorithm with given parameters.
    """
    # Validate algorithm exists
    available_algorithms = list_algorithms()
    if algorithm_in.algorithm not in available_algorithms:
        raise HTTPException(
            status_code=400,
            detail=f"Algorithm '{algorithm_in.algorithm}' not found. Available algorithms: {', '.join(available_algorithms)}",
        )
    
    # Create a record for the algorithm run
    from app.models.algorithm import AlgorithmRun
    algorithm_run = AlgorithmRun(
        algorithm=algorithm_in.algorithm,
        params=algorithm_in.params,
        status="pending"
    )
    db.add(algorithm_run)
    db.commit()
    db.refresh(algorithm_run)
    
    # Run algorithm in background
    background_tasks.add_task(
        run_algorithm,
        db=db,
        algorithm_run_id=algorithm_run.id,
        algorithm_name=algorithm_in.algorithm,
        params=algorithm_in.params
    )
    
    return algorithm_run


@router.get("/results/{algorithm_run_id}", response_model=schemas.AlgorithmRun)
def get_algorithm_results(
    *,
    db: Session = Depends(deps.get_db),
    algorithm_run_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get results of an algorithm run.
    """
    from app.models.algorithm import AlgorithmRun
    algorithm_run = db.query(AlgorithmRun).filter(AlgorithmRun.id == algorithm_run_id).first()
    if not algorithm_run:
        raise HTTPException(
            status_code=404,
            detail="Algorithm run not found",
        )
    return algorithm_run


@router.post("/apply/{algorithm_run_id}")
def apply_algorithm_results(
    *,
    db: Session = Depends(deps.get_db),
    algorithm_run_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Apply the results of an algorithm run to create actual schedules.
    """
    from app.models.algorithm import AlgorithmRun
    algorithm_run = db.query(AlgorithmRun).filter(AlgorithmRun.id == algorithm_run_id).first()
    if not algorithm_run:
        raise HTTPException(
            status_code=404,
            detail="Algorithm run not found",
        )
    
    if algorithm_run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Algorithm run is not completed yet",
        )
    
    # Apply results by creating schedules
    import json
    result = json.loads(algorithm_run.result)
    assignments = result.get("assignments", [])
    
    created_schedules = []
    for assignment in assignments:
        schedule_data = schemas.ScheduleCreate(
            project_id=assignment["project_id"],
            classroom_id=assignment["classroom_id"],
            timeslot_id=assignment["timeslot_id"]
        )
        schedule = crud.schedule.create(db, obj_in=schedule_data)
        created_schedules.append(schedule)
    
    return {"message": f"Created {len(created_schedules)} schedules", "schedules": created_schedules}


@router.post("/apply-fallback")
def apply_fallback_algorithm(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Apply fallback algorithm directly.
    """
    try:
        assignments = _generate_fallback_assignments(db)
        
        # Create schedules from assignments
        created_schedules = []
        for assignment in assignments:
            # Check if schedule already exists
            existing_schedule = crud.schedule.get_by_project(db, project_id=assignment["project_id"])
            if existing_schedule:
                # Update existing schedule
                existing_schedule.classroom_id = assignment["classroom_id"]
                existing_schedule.timeslot_id = assignment["timeslot_id"]
                schedule = existing_schedule
            else:
                # Create new schedule
                schedule_data = schemas.ScheduleCreate(
                    project_id=assignment["project_id"],
                    classroom_id=assignment["classroom_id"],
                    timeslot_id=assignment["timeslot_id"]
                )
                schedule = crud.schedule.create(db, obj_in=schedule_data)
            created_schedules.append(schedule)
        
        return {
            "message": f"Fallback algorithm applied successfully. Created/updated {len(created_schedules)} schedules.",
            "assignments": assignments,
            "schedules_count": len(created_schedules)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error applying fallback algorithm: {str(e)}"
        )

@router.get("/runs", response_model=List[Dict[str, Any]])
def get_algorithm_runs(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get all algorithm runs.
    """
    try:
        algorithm_runs = db.query(models.AlgorithmRun).order_by(models.AlgorithmRun.created_at.desc()).limit(10).all()
        
        runs_data = []
        for run in algorithm_runs:
            runs_data.append({
                "id": run.id,
                "algorithm_name": run.algorithm_name,
                "status": run.status,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "execution_time": run.execution_time,
                "result": None  # JSON parsing'i geçici olarak devre dışı bırak
            })
        
        return runs_data
    except Exception as e:
        print(f"Error in get_algorithm_runs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching algorithm runs: {str(e)}"
        )

