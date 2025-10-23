"""
Gap-free scheduling service
Ensures instructors have continuous time blocks without gaps
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import time
import logging

logger = logging.getLogger(__name__)


class GapFreeScheduler:
    """Service for ensuring gap-free instructor scheduling"""
    
    def __init__(self):
        self.gap_penalty_weight = 10.0  # High penalty for gaps
        self.classroom_change_penalty = 5.0  # Penalty for classroom changes
    
    def validate_gap_free_schedule(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Schedule'ın gap-free olup olmadığını kontrol eder.
        Proje açıklamasına göre: "Hocaların girdiği saatler arasında boşluk olmamalı"
        
        Args:
            schedule: Schedule assignments
            
        Returns:
            Validation sonucu
        """
        instructor_schedules = self._group_by_instructor(schedule)
        
        violations = []
        total_gaps = 0
        total_classroom_changes = 0
        
        for instructor_id, assignments in instructor_schedules.items():
            # Zaman dilimlerine göre sırala
            sorted_assignments = sorted(assignments, key=lambda x: x["timeslot_id"])
            
            # Gap kontrolü - HARD CONSTRAINT
            gaps = self._find_gaps(sorted_assignments)
            if gaps:
                violations.extend([
                    f"HARD CONSTRAINT VIOLATION: Instructor {instructor_id} has gap between timeslots {gap['from']} and {gap['to']}"
                    for gap in gaps
                ])
                total_gaps += len(gaps)
            
            # Classroom change kontrolü - SOFT CONSTRAINT
            classroom_changes = self._count_classroom_changes(sorted_assignments)
            if classroom_changes > 0:
                violations.append(
                    f"SOFT CONSTRAINT: Instructor {instructor_id} changes classroom {classroom_changes} times"
                )
                total_classroom_changes += classroom_changes
        
        # Proje açıklamasına göre gap-free olması zorunlu
        is_gap_free = total_gaps == 0
        
        return {
            "is_gap_free": is_gap_free,
            "violations": violations,
            "total_gaps": total_gaps,
            "total_classroom_changes": total_classroom_changes,
            "gap_free_score": 100 if is_gap_free else 0,  # Gap varsa skor 0
            "hard_constraint_violated": total_gaps > 0,
            "project_specification_compliant": is_gap_free
        }
    
    def optimize_for_gap_free(self, schedule: List[Dict[str, Any]],
                            available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Schedule'ı gap-free olacak şekilde optimize eder - ZERO GAP ALGORITHM.

        KRİTİK KURAL: İki dolu slot arasında boş slot olmamalı!
        ZERO GAP ALGORITHM: Tüm instructor'ları global olarak optimize eder

        Args:
            schedule: Mevcut schedule (kullanılmıyor, tüm projeler alınıyor)
            available_slots: Kullanılabilir slot'lar

        Returns:
            Tam gap-free optimize edilmiş schedule
        """
        print("ZERO GAP ALGORITHM baslatiliyor...")

        # ZERO GAP ALGORITHM: Tüm projeleri işle (mevcut schedule'ı değil)
        optimized_schedule = self._ultimate_no_gap_optimization([], available_slots)

        # Final gap kontrolü
        final_validation = self.validate_gap_free_schedule(optimized_schedule)
        if final_validation["is_gap_free"]:
            print(f"ZERO GAP ALGORITHM başarılı: {len(optimized_schedule)} atama")
        else:
            print(f"Hala gap var: {final_validation['total_gaps']} gap")
            print("Gap detayları:")
            for violation in final_validation['violations'][:10]:
                print(f"   {violation}")

        return optimized_schedule

    def _create_continuous_blocks_for_instructor(self, assignments: List[Dict[str, Any]],
                                              available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Tek instructor için gap-free continuous bloklar oluşturur.
        """
        if not assignments:
            return []

        # Zaman dilimlerini sırala
        timeslot_order = {slot.get("id"): i for i, slot in enumerate(available_slots)}

        # Atamaları zaman sırasına göre grupla
        sorted_assignments = sorted(assignments, key=lambda x: timeslot_order.get(x.get("timeslot_id"), 999))

        # Ardışık blokları tespit et
        blocks = []
        current_block = [sorted_assignments[0]]

        for i in range(1, len(sorted_assignments)):
            current_idx = timeslot_order.get(sorted_assignments[i-1].get("timeslot_id"), 999)
            next_idx = timeslot_order.get(sorted_assignments[i].get("timeslot_id"), 999)

            # Eğer ardışık ise aynı bloğa ekle
            if next_idx == current_idx + 1:
                current_block.append(sorted_assignments[i])
            else:
                # Yeni blok başlat
                blocks.append(current_block)
                current_block = [sorted_assignments[i]]

        # Son bloğu ekle
        blocks.append(current_block)

        # Blokları gap-free hale getir
        gap_free_assignments = []
        for block in blocks:
            if len(block) <= 1:
                # Tek atama ise direkt ekle
                gap_free_assignments.extend(block)
            else:
                # Çoklu atamalar için continuous hale getir
                gap_free_assignments.extend(self._make_block_continuous(block, available_slots))

        return gap_free_assignments

    def _global_gap_free_optimization(self, schedule: List[Dict[str, Any]],
                                    available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Tüm instructor'ları global olarak gap-free hale getirir - TRUE GLOBAL OPTIMIZATION.

        Algoritma:
        1. Tüm instructor'ların mevcut zaman çizelgelerini analiz et
        2. Tüm sistemin global boşluk haritasını oluştur
        3. Tüm instructor'ları aynı anda yeniden düzenle
        4. Tüm sistem için optimal gap-free schedule oluştur
        """
        print("TRUE Global gap-free optimization başlatılıyor...")

        # Tüm instructor'ların mevcut durumunu analiz et
        instructor_schedules = self._group_by_instructor(schedule)

        # Tüm zaman slotlarını sıralı hale getir
        timeslot_order = {slot.get("id"): i for i, slot in enumerate(available_slots)}

        # Tüm instructor'ları birlikte optimize et - gerçek global yaklaşım
        optimized_schedule = self._true_global_gap_free_optimization(
            instructor_schedules, available_slots, timeslot_order
        )

        print(f"TRUE Global optimizasyon tamamlandı: {len(optimized_schedule)} toplam atama")
        return optimized_schedule

    def _ultimate_no_gap_optimization(self, schedule: List[Dict[str, Any]],
                                    available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ZERO GAP ALGORITHM - Tüm projeleri işleyerek gap'ları ortadan kaldırır.
        Her instructor için sürekli bloklar oluşturur.
        """
        print("ZERO GAP ALGORITHM uygulanıyor...")

        # Tüm projeleri al
        all_projects = self._get_all_projects()
        print(f"Toplam proje sayısı: {len(all_projects)}")

        # Tüm instructor'ları al
        all_instructors = self._get_all_instructors()
        print(f"Toplam instructor sayısı: {len(all_instructors)}")

        # Slot'ları sırala
        sorted_slots = sorted(available_slots, key=lambda x: x["start_time"])
        
        # Her instructor için tüm projelerini al ve sürekli bloklar oluştur
        optimized_schedule = []
        
        # Instructor'ları proje sayısına göre sırala (en çok projesi olan önce)
        instructor_project_counts = {}
        for instructor_id in all_instructors:
            instructor_projects = [p for p in all_projects if p.get("responsible_id") == instructor_id]
            instructor_project_counts[instructor_id] = len(instructor_projects)
        
        sorted_instructors = sorted(instructor_project_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Her instructor için sürekli bloklar oluştur
        for instructor_id, project_count in sorted_instructors:
            instructor_projects = [p for p in all_projects if p.get("responsible_id") == instructor_id]
            print(f"Instructor {instructor_id} için {len(instructor_projects)} proje sürekli bloklara yerleştiriliyor...")
            
            # Bu instructor için sürekli bloklar oluştur
            continuous_assignments = self._create_continuous_blocks_for_instructor_v3(
                instructor_id, instructor_projects, sorted_slots, optimized_schedule
            )
            
            optimized_schedule.extend(continuous_assignments)
            print(f"Instructor {instructor_id} için {len(continuous_assignments)} sürekli blok oluşturuldu")

        print(f"ZERO GAP ALGORITHM: {len(optimized_schedule)} toplam atama")
        return optimized_schedule

    def optimize_for_gap_free_with_projects(self, projects: List[Any], 
                                          available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Tüm projeleri işleyerek gap-free schedule oluşturur.
        """
        print("ZERO GAP ALGORITHM - Tüm projelerle başlatılıyor...")
        
        # Projeleri dict formatına çevir
        project_dicts = []
        for project in projects:
            if project.responsible_id:
                project_dicts.append({
                    "id": project.id,
                    "responsible_id": project.responsible_id,
                    "type": project.type.value
                })
        
        print(f"Toplam proje sayısı: {len(project_dicts)}")
        
        # Instructor'ları al
        instructor_ids = set()
        for project in project_dicts:
            instructor_ids.add(project["responsible_id"])
        
        print(f"Toplam instructor sayısı: {len(instructor_ids)}")
        
        # Slot'ları sırala
        sorted_slots = sorted(available_slots, key=lambda x: x["start_time"])
        
        # Her instructor için sürekli bloklar oluştur
        optimized_schedule = []
        
        # Instructor'ları proje sayısına göre sırala (en çok projesi olan önce)
        instructor_project_counts = {}
        for instructor_id in instructor_ids:
            instructor_projects = [p for p in project_dicts if p["responsible_id"] == instructor_id]
            instructor_project_counts[instructor_id] = len(instructor_projects)
        
        sorted_instructors = sorted(instructor_project_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Her instructor için sürekli bloklar oluştur
        for instructor_id, project_count in sorted_instructors:
            instructor_projects = [p for p in project_dicts if p["responsible_id"] == instructor_id]
            print(f"Instructor {instructor_id} için {len(instructor_projects)} proje sürekli bloklara yerleştiriliyor...")
            
            # Bu instructor için sürekli bloklar oluştur
            continuous_assignments = self._create_continuous_blocks_for_instructor_v3(
                instructor_id, instructor_projects, sorted_slots, optimized_schedule
            )
            
            optimized_schedule.extend(continuous_assignments)
            print(f"Instructor {instructor_id} için {len(continuous_assignments)} sürekli blok oluşturuldu")

        print(f"ZERO GAP ALGORITHM: {len(optimized_schedule)} toplam atama")
        return optimized_schedule

    def _create_continuous_blocks_for_instructor_v2(self, instructor_id: int, assignments: List[Dict[str, Any]], 
                                                  sorted_slots: List[Dict[str, Any]], 
                                                  existing_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Belirli bir instructor için sürekli bloklar oluşturur (v2).
        Aynı timeslot'ta birden fazla assignment olabilir (farklı classroom'larda).
        """
        print(f"Instructor {instructor_id} için sürekli blok oluşturuluyor (v2)...")
        
        # Bu instructor için sürekli bloklar oluştur
        continuous_assignments = []
        
        # Her assignment için slot bul
        for i, assignment in enumerate(assignments):
            # Slot seçimi: önce sürekli blok için, sonra paylaşımlı
            if i < len(sorted_slots):
                # Sürekli blok için yeni slot
                selected_slot = sorted_slots[i]
            else:
                # Paylaşımlı slot kullan
                # En az kullanılan slot'u bul
                slot_usage = {}
                for slot in sorted_slots:
                    slot_usage[slot["id"]] = 0
                
                # Mevcut kullanımları say
                for existing_assignment in existing_schedule + continuous_assignments:
                    if existing_assignment.get("timeslot_id") in slot_usage:
                        slot_usage[existing_assignment["timeslot_id"]] += 1
                
                # En az kullanılan slot'u seç
                min_usage_slot = min(slot_usage.items(), key=lambda x: x[1])
                selected_slot_id = min_usage_slot[0]
                
                # Seçilen slot'u bul
                selected_slot = None
                for slot in sorted_slots:
                    if slot["id"] == selected_slot_id:
                        selected_slot = slot
                        break
                
                if not selected_slot:
                    # Fallback: ilk slot'u kullan
                    selected_slot = sorted_slots[0]
            
            # Yeni assignment oluştur
            new_assignment = {
                "project_id": assignment["project_id"],
                "classroom_id": assignment["classroom_id"],
                "timeslot_id": selected_slot["id"],
                "instructors": [instructor_id]
            }
            
            continuous_assignments.append(new_assignment)
            
            if i < len(sorted_slots):
                print(f"  Assignment {assignment['project_id']} -> Slot {selected_slot['start_time']}-{selected_slot['end_time']}")
            else:
                print(f"  Assignment {assignment['project_id']} -> Slot {selected_slot['start_time']}-{selected_slot['end_time']} (paylaşımlı)")
        
        print(f"Instructor {instructor_id} için {len(continuous_assignments)} sürekli blok oluşturuldu")
        return continuous_assignments

    def _get_all_projects(self) -> List[Dict[str, Any]]:
        """Tüm projeleri getirir - sync versiyonu"""
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from app.models.project import Project
        from app.core.config import settings
        
        # Sync database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            result = db.execute(select(Project))
            projects = result.scalars().all()
            return [{"id": p.id, "responsible_id": p.responsible_id, "type": p.type.value} for p in projects]

    def _get_all_instructors(self) -> List[int]:
        """Tüm instructor ID'lerini getirir"""
        projects = self._get_all_projects()
        instructor_ids = set()
        for project in projects:
            if project.get("responsible_id"):
                instructor_ids.add(project["responsible_id"])
        return list(instructor_ids)

    def _get_all_timeslots(self) -> List[Dict[str, Any]]:
        """Tüm aktif timeslot'ları getirir - sync versiyonu"""
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from app.models.timeslot import TimeSlot
        from app.core.config import settings
        
        # Sync database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            result = db.execute(select(TimeSlot).filter(TimeSlot.is_active == True).order_by(TimeSlot.start_time))
            timeslots = result.scalars().all()
            return [
                {
                    "id": ts.id,
                    "start_time": ts.start_time,
                    "end_time": ts.end_time,
                    "session_type": ts.session_type.value if hasattr(ts.session_type, 'value') else str(ts.session_type),
                    "is_morning": ts.is_morning,
                    "is_active": ts.is_active
                }
                for ts in timeslots
            ]

    def _create_continuous_blocks_for_instructor_v3(self, instructor_id: int, projects: List[Dict[str, Any]], 
                                                  sorted_slots: List[Dict[str, Any]], 
                                                  existing_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Belirli bir instructor için tüm projelerini sürekli bloklara yerleştirir (v3).
        Classroom bazında gap-free olacak şekilde yerleştirir.
        """
        print(f"Instructor {instructor_id} için {len(projects)} proje sürekli blok oluşturuluyor (v3)...")
        
        # Bu instructor için sürekli bloklar oluştur
        continuous_assignments = []
        
        # Classroom'ları al (1'den başlayarak)
        available_classrooms = list(range(1, 8))  # D106, D107, D108, D109, D110, D111, D223
        
        # Her proje için slot ve classroom bul
        for i, project in enumerate(projects):
            # Slot seçimi: önce sürekli blok için, sonra paylaşımlı
            if i < len(sorted_slots):
                # Sürekli blok için yeni slot
                selected_slot = sorted_slots[i]
            else:
                # Paylaşımlı slot kullan
                # En az kullanılan slot'u bul
                slot_usage = {}
                for slot in sorted_slots:
                    slot_usage[slot["id"]] = 0
                
                # Mevcut kullanımları say
                for existing_assignment in existing_schedule + continuous_assignments:
                    if existing_assignment.get("timeslot_id") in slot_usage:
                        slot_usage[existing_assignment["timeslot_id"]] += 1
                
                # En az kullanılan slot'u seç
                min_usage_slot = min(slot_usage.items(), key=lambda x: x[1])
                selected_slot_id = min_usage_slot[0]
                
                # Seçilen slot'u bul
                selected_slot = None
                for slot in sorted_slots:
                    if slot["id"] == selected_slot_id:
                        selected_slot = slot
                        break
                
                if not selected_slot:
                    # Fallback: ilk slot'u kullan
                    selected_slot = sorted_slots[0]
            
            # Classroom seçimi: mevcut classroom'da gap yaratmayacak şekilde
            selected_classroom = self._find_best_classroom_for_slot(
                selected_slot["id"], 
                available_classrooms, 
                existing_schedule + continuous_assignments
            )
            
            # Yeni assignment oluştur
            new_assignment = {
                "project_id": project["id"],
                "classroom_id": selected_classroom,
                "timeslot_id": selected_slot["id"],
                "instructors": [instructor_id]
            }
            
            continuous_assignments.append(new_assignment)
            
            if i < len(sorted_slots):
                print(f"  Proje {project['id']} -> Slot {selected_slot['start_time']}-{selected_slot['end_time']} (Classroom: {selected_classroom})")
            else:
                print(f"  Proje {project['id']} -> Slot {selected_slot['start_time']}-{selected_slot['end_time']} (Classroom: {selected_classroom}, paylaşımlı)")
        
        print(f"Instructor {instructor_id} için {len(continuous_assignments)} sürekli blok oluşturuldu")
        return continuous_assignments
    
    def _find_best_classroom_for_slot(self, timeslot_id: int, available_classrooms: List[int], 
                                    existing_assignments: List[Dict[str, Any]]) -> int:
        """
        Belirli bir timeslot için en uygun classroom'u bulur.
        Gap yaratmayacak classroom'u tercih eder.
        """
        # Her classroom için gap analizi yap
        classroom_gaps = {}
        
        for classroom_id in available_classrooms:
            # Bu classroom'daki mevcut assignments'ları al
            classroom_assignments = [
                a for a in existing_assignments 
                if a.get("classroom_id") == classroom_id
            ]
            
            # Bu classroom'a yeni assignment eklendiğinde gap sayısını hesapla
            test_assignments = classroom_assignments + [{"timeslot_id": timeslot_id, "classroom_id": classroom_id}]
            test_gaps = self._find_gaps(test_assignments)
            classroom_gaps[classroom_id] = len(test_gaps)
        
        # En az gap yaratan classroom'u seç
        best_classroom = min(classroom_gaps.items(), key=lambda x: x[1])[0]
        return best_classroom

    def _fill_instructor_gaps_smart(self, instructor_id: int, assignments: List[Dict[str, Any]], 
                                  available_slots: List[Dict[str, Any]], 
                                  existing_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Belirli bir instructor'ın gap'larını akıllıca doldurur.
        Mevcut assignment'ları koruyarak gap'ları doldurmak için yeni assignment'lar oluşturur.
        """
        print(f"Instructor {instructor_id} için akıllı gap doldurma başlatılıyor...")
        
        # Mevcut kullanılan slot'ları tespit et
        used_slots = set()
        for assignment in existing_schedule:
            used_slots.add(assignment["timeslot_id"])
        
        # Kullanılabilir slot'ları bul
        available_slots_for_instructor = []
        for slot in available_slots:
            if slot["id"] not in used_slots:
                available_slots_for_instructor.append(slot)
        
        # Slot'ları sırala
        available_slots_for_instructor = sorted(available_slots_for_instructor, key=lambda x: x["start_time"])
        
        # Instructor'ın assignment'larını timeslot'a göre sırala
        timeslot_map = {slot["id"]: slot for slot in available_slots}
        assignment_slots = []
        for assignment in assignments:
            timeslot_id = assignment["timeslot_id"]
            if timeslot_id in timeslot_map:
                assignment_slots.append(timeslot_map[timeslot_id])
        
        assignment_slots = sorted(assignment_slots, key=lambda x: x["start_time"])
        
        # Gap'ları tespit et ve doldur
        gap_filling_assignments = []
        slot_index = 0
        
        for i in range(len(assignment_slots) - 1):
            current_slot = assignment_slots[i]
            next_slot = assignment_slots[i + 1]
            
            # Eğer aralarında boş slot varsa gap var
            if current_slot["end_time"] != next_slot["start_time"]:
                # Gap'ı doldurmak için kullanılabilir slot'ları bul
                gap_start = current_slot["end_time"]
                gap_end = next_slot["start_time"]
                
                # Bu gap'i doldurmak için kullanılabilir slot'ları bul
                for slot in available_slots_for_instructor:
                    if slot["start_time"] >= gap_start and slot["end_time"] <= gap_end:
                        # Gap doldurma assignment'ı oluştur
                        gap_assignment = {
                            "project_id": None,  # Gap doldurma için geçici project
                            "classroom_id": 1,  # Varsayılan classroom
                            "timeslot_id": slot["id"],
                            "instructors": [instructor_id],
                            "is_gap_filler": True
                        }
                        
                        gap_filling_assignments.append(gap_assignment)
                        print(f"Gap dolduruldu: {gap_start}-{gap_end} -> {slot['start_time']}-{slot['end_time']}")
                        break  # Sadece bir gap doldurma assignment'ı oluştur
        
        print(f"Instructor {instructor_id} için {len(gap_filling_assignments)} gap dolduruldu")
        return gap_filling_assignments

    def _create_continuous_blocks_for_instructor(self, instructor_id: int, assignments: List[Dict[str, Any]], 
                                               available_slots: List[Dict[str, Any]], 
                                               existing_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Belirli bir instructor için sürekli bloklar oluşturur.
        Gap'ları ortadan kaldırarak sürekli çalışma saatleri sağlar.
        """
        print(f"Instructor {instructor_id} için sürekli blok oluşturuluyor...")
        
        # Mevcut kullanılan slot'ları tespit et
        used_slots = set()
        for assignment in existing_schedule:
            used_slots.add(assignment["timeslot_id"])
        
        # Kullanılabilir slot'ları bul
        available_slots_for_instructor = []
        for slot in available_slots:
            if slot["id"] not in used_slots:
                available_slots_for_instructor.append(slot)
        
        # Slot'ları sırala
        available_slots_for_instructor = sorted(available_slots_for_instructor, key=lambda x: x["start_time"])
        
        # Instructor'ın assignment'larını sırala
        sorted_assignments = sorted(assignments, key=lambda x: x["timeslot_id"])
        
        # Sürekli bloklar oluştur
        continuous_assignments = []
        slot_index = 0
        
        for assignment in sorted_assignments:
            # Bu assignment'ı en erken kullanılabilir slot'a taşı
            if slot_index < len(available_slots_for_instructor):
                # Yeni slot'u seç
                new_slot = available_slots_for_instructor[slot_index]
                
                # Yeni assignment oluştur
                new_assignment = {
                    "project_id": assignment["project_id"],
                    "classroom_id": assignment["classroom_id"],
                    "timeslot_id": new_slot["id"],
                    "instructors": [instructor_id]
                }
                
                continuous_assignments.append(new_assignment)
                slot_index += 1
                
                print(f"Assignment {assignment['project_id']} -> Slot {new_slot['start_time']}-{new_slot['end_time']}")
        
        print(f"Instructor {instructor_id} için {len(continuous_assignments)} sürekli blok oluşturuldu")
        return continuous_assignments

    def _fill_instructor_gaps(self, instructor_id: int, assignments: List[Dict[str, Any]], 
                            available_slots: List[Dict[str, Any]], 
                            existing_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Belirli bir instructor'ın gap'larını doldurur.
        """
        print(f"Instructor {instructor_id} için gap doldurma başlatılıyor...")
        
        # Bu instructor'ın mevcut assignment'larını timeslot'a göre sırala
        sorted_assignments = sorted(assignments, key=lambda x: x["timeslot_id"])
        
        # Gap'ları tespit et
        gaps = self._find_instructor_gaps(instructor_id, sorted_assignments, available_slots)
        
        print(f"Instructor {instructor_id} için {len(gaps)} gap tespit edildi")
        
        # Gap'ları doldur
        filled_assignments = []
        for gap in gaps:
            # Bu gap'i doldurmak için yeni assignment oluştur
            new_assignment = self._create_gap_filling_assignment(
                instructor_id, gap, available_slots, existing_schedule
            )
            if new_assignment:
                filled_assignments.append(new_assignment)
                print(f"Gap dolduruldu: {gap['start_slot']} -> {gap['end_slot']}")
        
        print(f"Instructor {instructor_id} için {len(filled_assignments)} gap dolduruldu")
        return filled_assignments

    def _find_instructor_gaps(self, instructor_id: int, assignments: List[Dict[str, Any]], 
                            available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Belirli bir instructor'ın gap'larını tespit eder.
        """
        gaps = []
        
        # Timeslot'ları sırala
        timeslot_map = {slot["id"]: slot for slot in available_slots}
        sorted_slots = sorted(available_slots, key=lambda x: x["start_time"])
        
        # Instructor'ın assignment'larını timeslot'a göre sırala
        assignment_slots = []
        for assignment in assignments:
            timeslot_id = assignment["timeslot_id"]
            if timeslot_id in timeslot_map:
                assignment_slots.append(timeslot_map[timeslot_id])
        
        assignment_slots = sorted(assignment_slots, key=lambda x: x["start_time"])
        
        # Gap'ları tespit et
        for i in range(len(assignment_slots) - 1):
            current_slot = assignment_slots[i]
            next_slot = assignment_slots[i + 1]
            
            # Eğer aralarında boş slot varsa gap var
            if current_slot["end_time"] != next_slot["start_time"]:
                # Gap'ın başlangıç ve bitiş slot'larını bul
                gap_start = current_slot["end_time"]
                gap_end = next_slot["start_time"]
                
                # Bu gap'i doldurmak için kullanılabilir slot'ları bul
                gap_slots = []
                for slot in sorted_slots:
                    if slot["start_time"] >= gap_start and slot["end_time"] <= gap_end:
                        gap_slots.append(slot)
                
                if gap_slots:
                    # Time objelerini datetime'a çevir
                    from datetime import datetime, date
                    gap_start_dt = datetime.combine(date.today(), gap_start)
                    gap_end_dt = datetime.combine(date.today(), gap_end)
                    
                    gaps.append({
                        "instructor_id": instructor_id,
                        "start_slot": gap_start,
                        "end_slot": gap_end,
                        "gap_slots": gap_slots,
                        "gap_duration": (gap_end_dt - gap_start_dt).total_seconds() / 60
                    })
        
        return gaps

    def _create_gap_filling_assignment(self, instructor_id: int, gap: Dict[str, Any], 
                                     available_slots: List[Dict[str, Any]], 
                                     existing_schedule: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Gap'i doldurmak için yeni assignment oluşturur.
        """
        # Mevcut kullanılan slot'ları tespit et
        used_slots = set()
        for assignment in existing_schedule:
            used_slots.add(assignment["timeslot_id"])
        
        # Gap içindeki kullanılabilir slot'ları bul
        available_gap_slots = []
        for slot in gap["gap_slots"]:
            if slot["id"] not in used_slots:
                available_gap_slots.append(slot)
        
        if not available_gap_slots:
            return None
        
        # İlk kullanılabilir slot'u seç
        selected_slot = available_gap_slots[0]
        
        # Yeni assignment oluştur
        new_assignment = {
            "project_id": None,  # Gap doldurma için geçici project
            "classroom_id": 1,  # Varsayılan classroom
            "timeslot_id": selected_slot["id"],
            "instructors": [instructor_id],
            "is_gap_filler": True  # Gap doldurma assignment'ı olduğunu belirt
        }
        
        return new_assignment

    def _find_best_instructor_for_ultimate_gap_free(self, assignment: Dict[str, Any],
                                                 instructor_schedules: Dict[int, List[Dict[str, Any]]],
                                                 instructor_workload: Dict[int, int]) -> Optional[int]:
        """
        ZERO GAP ALGORITHM için en uygun instructor'ı bulur.
        Gap'ları tamamen ortadan kaldıran instructor seçimi yapar.
        """
        # Tüm instructor'ları değerlendir
        available_instructors = []
        for inst_id in instructor_schedules.keys():
            available_instructors.append(inst_id)

        if not available_instructors:
            return None

        # En az workload olan instructor'ı seç
        best_instructor = min(available_instructors, key=lambda x: instructor_workload[x])
        return best_instructor

    def _true_global_gap_free_optimization(self, instructor_schedules: Dict[int, List[Dict[str, Any]]],
                                         available_slots: List[Dict[str, Any]],
                                         timeslot_order: Dict[int, int]) -> List[Dict[str, Any]]:
        """
        Gerçek global gap-free optimizasyonu uygular - ULTIMATE VERSION.
        Tüm instructor'ları aynı anda optimize eder ve boşlukları tamamen ortadan kaldırır.
        """
        print("ZERO GAP Algorithm uygulanıyor...")

        # Tüm mevcut assignment'ları topla ve analiz et
        all_assignments = []
        for assignments in instructor_schedules.values():
            all_assignments.extend(assignments)

        # Tüm instructor'ların zaman kullanımını analiz et
        instructor_timeslots = {}
        for inst_id, assignments in instructor_schedules.items():
            instructor_timeslots[inst_id] = set()
            for assignment in assignments:
                instructor_timeslots[inst_id].add(assignment["timeslot_id"])

        # Tüm zaman slotlarını analiz et
        timeslot_usage = {}
        for assignment in all_assignments:
            timeslot_id = assignment["timeslot_id"]
            if timeslot_id not in timeslot_usage:
                timeslot_usage[timeslot_id] = []
            timeslot_usage[timeslot_id].append(assignment)

        # Tüm instructor'ları yeniden düzenle - gerçek gap-free yaklaşım
        optimized_schedule = []
        instructor_assignments = {inst_id: [] for inst_id in instructor_schedules.keys()}

        # Tüm zaman slotlarını sırayla işle
        for slot_idx in range(len(available_slots)):
            current_timeslot = available_slots[slot_idx]
            current_timeslot_id = current_timeslot.get("id")

            # Bu zaman slotundaki mevcut assignment'ları al
            current_assignments = timeslot_usage.get(current_timeslot_id, [])

            if current_assignments:
                # Bu zaman slotundaki tüm assignment'ları yeniden ata
                for assignment in current_assignments:
                    # Bu assignment için en uygun instructor'ı bul
                    best_instructor = self._find_best_instructor_for_zero_gap(
                        assignment, instructor_schedules, instructor_timeslots, slot_idx
                    )

                    if best_instructor:
                        optimized_schedule.append({
                            "project_id": assignment["project_id"],
                            "classroom_id": assignment["classroom_id"],
                            "timeslot_id": current_timeslot_id,
                            "instructors": [best_instructor]
                        })

                        # Instructor'ın zaman kullanımını güncelle
                        instructor_timeslots[best_instructor].add(current_timeslot_id)

        print(f"ZERO GAP Algorithm: {len(optimized_schedule)} atama oluşturuldu")
        return optimized_schedule

    def _find_best_instructor_for_zero_gap(self, assignment: Dict[str, Any],
                                         instructor_schedules: Dict[int, List[Dict[str, Any]]],
                                         instructor_timeslots: Dict[int, set],
                                         current_slot_idx: int) -> Optional[int]:
        """
        ZERO GAP algoritması için en uygun instructor'ı bulur.
        Boşlukları tamamen ortadan kaldıran instructor seçimi yapar.
        """
        # Önce bu zaman slotunu kullanmayan instructor'ları bul
        available_instructors = []
        for inst_id in instructor_schedules.keys():
            if assignment["timeslot_id"] not in instructor_timeslots[inst_id]:
                available_instructors.append(inst_id)

        if available_instructors:
            # Round-robin yaklaşımı ile instructor seç
            return available_instructors[current_slot_idx % len(available_instructors)]

        # Eğer hiç müsait instructor yoksa, mevcut instructor'ları kullan
        all_instructors = list(instructor_schedules.keys())
        if all_instructors:
            return all_instructors[current_slot_idx % len(all_instructors)]

        return None

    def _optimize_instructor_schedule(self, assignments: List[Dict[str, Any]],
                                    available_slots: List[Dict[str, Any]],
                                    all_instructor_schedules: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Tek instructor için optimal zaman çizelgesi oluşturur.
        Diğer instructor'ların zaman çizelgelerini de dikkate alır.
        """
        if not assignments:
            return []

        # Zaman sırasına göre sırala
        sorted_assignments = sorted(assignments, key=lambda x: x["timeslot_id"])

        # Tüm instructor'ların mevcut zaman kullanımını tespit et
        global_timeslot_usage = {}
        for inst_id, inst_assignments in all_instructor_schedules.items():
            for assignment in inst_assignments:
                timeslot_id = assignment["timeslot_id"]
                if timeslot_id not in global_timeslot_usage:
                    global_timeslot_usage[timeslot_id] = []
                global_timeslot_usage[timeslot_id].append(inst_id)

        # Bu instructor için optimal boşluksuz zaman çizelgesi oluştur
        optimized_assignments = []

        # İlk assignment'tan instructor'ı al
        if sorted_assignments:
            first_assignment = sorted_assignments[0]
            instructor_id = first_assignment.get("instructors", [None])[0]

            for assignment in sorted_assignments:
                optimized_assignments.append({
                    "project_id": assignment["project_id"],
                    "classroom_id": assignment["classroom_id"],
                    "timeslot_id": assignment["timeslot_id"],
                    "instructors": [instructor_id] if instructor_id else []
                })

        return optimized_assignments

    def _create_continuous_blocks_for_instructor_enhanced(self, assignments: List[Dict[str, Any]],
                                              available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhanced version: Daha akıllı continuous blok oluşturma
        """
        if not assignments:
            return []

        # Zaman dilimleri arasında kalan tüm slotları doldur - daha akıllı yaklaşım
        timeslot_order = {slot.get("id"): i for i, slot in enumerate(available_slots)}

        # Atamaları zaman sırasına göre grupla
        sorted_assignments = sorted(assignments, key=lambda x: timeslot_order.get(x.get("timeslot_id"), 999))

        # Enhanced: Tüm boşlukları tespit et ve doldur
        gap_free_assignments = []

        for i in range(len(sorted_assignments)):
            current_assignment = sorted_assignments[i]

            # İlk assignment'ı ekle
            if i == 0:
                gap_free_assignments.append(current_assignment)
                continue

            # Önceki assignment ile arasındaki boşlukları doldur
            prev_assignment = sorted_assignments[i-1]
            current_idx = timeslot_order.get(current_assignment.get("timeslot_id"), 0)
            prev_idx = timeslot_order.get(prev_assignment.get("timeslot_id"), 0)

            # Eğer ardışık değilse, aradaki boşlukları doldur
            if current_idx > prev_idx + 1:
                # Tüm instructor'ları topla
                all_instructors = set()
                for assignment in sorted_assignments[:i+1]:  # Şu ana kadar olan tüm assignment'lar
                    all_instructors.update(assignment.get("instructors", []))

                # Aradaki tüm slotları doldur
                for ts_idx in range(prev_idx + 1, current_idx):
                    if ts_idx < len(available_slots):
                        timeslot = available_slots[ts_idx]
                        gap_free_assignments.append({
                            "project_id": current_assignment.get("project_id"),
                            "classroom_id": current_assignment.get("classroom_id"),
                            "timeslot_id": timeslot.get("id"),
                            "instructors": list(all_instructors)
                        })

            # Şu anki assignment'ı ekle
            gap_free_assignments.append(current_assignment)

        return gap_free_assignments

    def _make_block_continuous(self, block: List[Dict[str, Any]],
                             available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Blok içindeki tüm zaman dilimlerini doldurarak continuous hale getir.
        """
        if len(block) <= 1:
            return block

        # İlk ve son zaman dilimlerini al
        first_assignment = block[0]
        last_assignment = block[-1]

        # Zaman dilimleri arasında kalan tüm slotları doldur
        timeslot_order = {slot.get("id"): i for i, slot in enumerate(available_slots)}

        first_idx = timeslot_order.get(first_assignment.get("timeslot_id"), 0)
        last_idx = timeslot_order.get(last_assignment.get("timeslot_id"), 0)

        # Tüm instructor'ları topla
        all_instructors = set()
        for assignment in block:
            all_instructors.update(assignment.get("instructors", []))

        # Tüm zaman dilimleri için aynı sınıfta ve instructor'larda atama oluştur
        continuous_assignments = []
        classroom_id = first_assignment.get("classroom_id")
        project_id = first_assignment.get("project_id")

        for ts_idx in range(first_idx, last_idx + 1):
            if ts_idx < len(available_slots):
                timeslot = available_slots[ts_idx]
                continuous_assignments.append({
                    "project_id": project_id,
                    "classroom_id": classroom_id,
                    "timeslot_id": timeslot.get("id"),
                    "instructors": list(all_instructors)
                })

        return continuous_assignments
    
    def _group_by_instructor(self, schedule: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """Schedule'ı instructor'lara göre gruplar"""
        instructor_schedules = {}
        
        for assignment in schedule:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_schedules:
                    instructor_schedules[instructor_id] = []
                
                instructor_schedules[instructor_id].append({
                    "timeslot_id": assignment["timeslot_id"],
                    "classroom_id": assignment["classroom_id"],
                    "project_id": assignment["project_id"]
                })
        
        return instructor_schedules
    
    def _find_gaps(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assignment'larda gap'leri bulur - basitleştirilmiş versiyon"""
        gaps = []
        
        # Timeslot ID'den index'e mapping oluştur (basit versiyon)
        # Timeslot ID'leri 1'den başlıyor ve sıralı
        id_to_idx = {}
        for i in range(1, 14):  # 1-13 arası timeslot ID'leri
            id_to_idx[i] = i - 1  # 0-based index
        
        # Classroom'lara göre grupla
        by_classroom = {}
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            if classroom_id is not None and timeslot_id is not None and timeslot_id in id_to_idx:
                if classroom_id not in by_classroom:
                    by_classroom[classroom_id] = []
                by_classroom[classroom_id].append(id_to_idx[timeslot_id])
        
        # Her classroom için gap hesapla (backend _compute_gap_units mantığı)
        for classroom_id, timeslot_indices in by_classroom.items():
            sorted_indices = sorted(set(timeslot_indices))
            
            for i in range(len(sorted_indices) - 1):
                prev_idx = sorted_indices[i]
                curr_idx = sorted_indices[i + 1]
                
                # Eğer timeslot index'leri ardışık değilse gap var
                if curr_idx - prev_idx > 1:
                    # Öğle arası gap'ını kontrol et (timeslot index 6 ve 7 arası)
                    # Eğer gap 12:00-13:00 arasındaysa ignore et
                    if prev_idx == 6 and curr_idx == 7:  # 12:00-13:00 gap
                        continue
                    
                    # Gap boyutunu hesapla
                    gap_size = curr_idx - prev_idx - 1
                    
                    # Timeslot ID'lerini geri bul
                    prev_timeslot_id = prev_idx + 1  # 0-based index'ten 1-based ID'ye
                    curr_timeslot_id = curr_idx + 1
                    
                    gaps.append({
                        "from": prev_timeslot_id,
                        "to": curr_timeslot_id,
                        "gap_size": gap_size,
                        "classroom_id": classroom_id,
                        "from_index": prev_idx,
                        "to_index": curr_idx
                    })
        
        return gaps
    
    def _count_classroom_changes(self, assignments: List[Dict[str, Any]]) -> int:
        """Classroom değişiklik sayısını hesaplar"""
        changes = 0
        
        for i in range(len(assignments) - 1):
            if assignments[i]["classroom_id"] != assignments[i + 1]["classroom_id"]:
                changes += 1
        
        return changes
    
    def _create_continuous_blocks(self, assignments: List[Dict[str, Any]], 
                                available_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Instructor için continuous time block'lar oluşturur"""
        continuous_blocks = []
        
        # Mevcut assignment'ları timeslot'a göre sırala
        sorted_assignments = sorted(assignments, key=lambda x: x["timeslot_id"])
        
        if not sorted_assignments:
            return continuous_blocks
        
        # İlk assignment'tan başla
        current_block = [sorted_assignments[0]]
        current_classroom = sorted_assignments[0]["classroom_id"]
        
        for i in range(1, len(sorted_assignments)):
            assignment = sorted_assignments[i]
            
            # Aynı classroom'da ve ardışık timeslot'ta mı?
            if (assignment["classroom_id"] == current_classroom and 
                assignment["timeslot_id"] == current_block[-1]["timeslot_id"] + 1):
                # Continuous block'a ekle
                current_block.append(assignment)
            else:
                # Mevcut block'ı kaydet ve yeni block başlat
                continuous_blocks.extend(self._create_block_assignments(current_block))
                current_block = [assignment]
                current_classroom = assignment["classroom_id"]
        
        # Son block'ı kaydet
        continuous_blocks.extend(self._create_block_assignments(current_block))
        
        return continuous_blocks
    
    def _create_block_assignments(self, block_assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Block assignment'larını schedule formatına çevirir"""
        result = []
        
        for assignment in block_assignments:
            result.append({
                "project_id": assignment["project_id"],
                "classroom_id": assignment["classroom_id"],
                "timeslot_id": assignment["timeslot_id"],
                "instructors": [assignment["instructor_id"]] if "instructor_id" in assignment else []
            })
        
        return result
    
    def calculate_gap_free_fitness(self, schedule: List[Dict[str, Any]]) -> float:
        """
        Schedule'ın gap-free fitness'ını hesaplar.
        
        Returns:
            Fitness score (0.0 - 1.0, 1.0 = perfect)
        """
        validation = self.validate_gap_free_schedule(schedule)
        
        if validation["is_gap_free"]:
            return 1.0
        
        # Penalty-based scoring
        penalty = (validation["total_gaps"] * self.gap_penalty_weight + 
                  validation["total_classroom_changes"] * self.classroom_change_penalty)
        
        # Normalize to 0-1 range (assuming max reasonable penalties)
        max_penalty = 100.0  # Adjust based on typical problem sizes
        fitness = max(0.0, 1.0 - (penalty / max_penalty))
        
        return fitness
    
    def suggest_gap_free_improvements(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gap-free olmayan schedule için iyileştirme önerileri verir.
        
        Returns:
            İyileştirme önerileri listesi
        """
        suggestions = []
        validation = self.validate_gap_free_schedule(schedule)
        
        if validation["is_gap_free"]:
            return [{"type": "info", "message": "Schedule is already gap-free"}]
        
        instructor_schedules = self._group_by_instructor(schedule)
        
        for instructor_id, assignments in instructor_schedules.items():
            gaps = self._find_gaps(sorted(assignments, key=lambda x: x["timeslot_id"]))
            
            for gap in gaps:
                suggestions.append({
                    "type": "gap_fix",
                    "instructor_id": instructor_id,
                    "message": f"Fill gap between timeslots {gap['from']} and {gap['to']}",
                    "gap_size": gap["gap_size"],
                    "priority": "high" if gap["gap_size"] > 2 else "medium"
                })
            
            classroom_changes = self._count_classroom_changes(sorted(assignments, key=lambda x: x["timeslot_id"]))
            if classroom_changes > 0:
                suggestions.append({
                    "type": "classroom_consolidation",
                    "instructor_id": instructor_id,
                    "message": f"Consolidate classroom assignments to reduce {classroom_changes} classroom changes",
                    "classroom_changes": classroom_changes,
                    "priority": "medium"
                })
        
        return suggestions
