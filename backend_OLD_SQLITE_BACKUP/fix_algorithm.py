#!/usr/bin/env python3
"""
Çakışma sorunu için algoritma kodunu düzelt
"""

# Yeni algoritma kodu - basit ve çakışmasız
new_algorithm_code = '''
def _generate_fallback_assignments(db: Session) -> List[Dict[str, Any]]:
	"""
	Fallback algoritması: Basit greedy yaklaşım ile çakışmasız atama
	"""
	from app import crud, models, schemas
	from app.models.timeslot import TimeSlot
	from app.models.instructor import Instructor
	from app.models.classroom import Classroom
	from app.models.project import Project
	from typing import Dict, List, Any, Set
	
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
	
	# Yük takibi
	hoca_load: Dict[int, int] = {hoca.id: 0 for hoca in hocalar}
	asistan_load: Dict[int, int] = {asistan.id: 0 for asistan in asistanlar}
	
	# Sınıf boşlukları
	class_free_slots: Dict[int, List[int]] = {c.id: [] for c in classrooms}
	for c in classrooms:
		for ts in timeslots:
			if not crud.schedule.get_by_classroom_and_timeslot(db, classroom_id=c.id, timeslot_id=ts.id):
				class_free_slots[c.id].append(ts.id)
	
	generated: List[Dict[str, Any]] = []
	
	# TÜM PROJELERİ TEK TEK İŞLE - GRUPLANDIRMA YOK
	for proj in projects:
		responsible_id = getattr(proj, 'responsible_instructor_id', None)
		
		# En uygun sınıf ve zaman bul
		best_classroom = None
		best_timeslot = None
		
		for classroom_id, available_times in class_free_slots.items():
			if not available_times:
				continue
			
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
		
		# Hoca seçimi (çakışma kontrolü ile)
		min_senior_needed = 2 if str(getattr(proj, 'type', 'interim')) == 'final' else 1
		senior_count = 1 if responsible_id and responsible_id in [h.id for h in hocalar] else 0
		
		for hoca in hocalar:
			if senior_count >= min_senior_needed:
				break
			if hoca.id == responsible_id:
				continue
			if hoca.id in timeslot_instructors[best_timeslot]:
				continue  # Çakışma var
			
			# Yük kontrolü
			current_load = hoca_load.get(hoca.id, 0)
			max_load = max(hoca_load.values()) if hoca_load.values() else 0
			if current_load <= max_load + 2:
				jury.append(hoca.id)
				hoca_load[hoca.id] = current_load + 1
				timeslot_instructors[best_timeslot].add(hoca.id)
				senior_count += 1
		
		# Asistan seçimi (çakışma kontrolü ile)
		for asistan in asistanlar:
			if len(jury) >= 3:
				break
			if asistan.id in jury:
				continue
			if asistan.id in timeslot_instructors[best_timeslot]:
				continue  # Çakışma var
			
			# Yük kontrolü
			current_load = asistan_load.get(asistan.id, 0)
			max_load = max(asistan_load.values()) if asistan_load.values() else 0
			if current_load <= max_load + 1:
				jury.append(asistan.id)
				asistan_load[asistan.id] = current_load + 1
				timeslot_instructors[best_timeslot].add(asistan.id)
		
		# Eğer hala 3'den az jüri varsa, zorunlu ekle
		if len(jury) < 3:
			for instructor in instructors:
				if len(jury) >= 3:
					break
				if instructor.id not in jury and instructor.id not in timeslot_instructors[best_timeslot]:
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
	
	print(f"DEBUG: Toplam {len(generated)} atama oluşturuldu")
	return generated
'''

print("Yeni algoritma kodu hazırlandı!")
