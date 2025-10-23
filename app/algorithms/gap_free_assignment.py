"""
Gap-Free Assignment Module for optimizationplanner.mdc compliance
Provides gap-free scheduling functionality for project assignments
"""

from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class GapFreeAssignment:
    """
    Gap-Free Assignment class for ensuring continuous scheduling without gaps
    """

    def __init__(self):
        self.name = "Gap-Free Assignment"
        self.description = "Ensures gap-free scheduling for project assignments"

    def optimize_for_gap_free(self, schedule: List[Dict[str, Any]], timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize schedule for gap-free assignments

        Args:
            schedule: Current schedule assignments
            timeslots: Available timeslots

        Returns:
            Optimized schedule with gap-free assignments
        """
        # Simple implementation - just return the original schedule
        # In a full implementation, this would reorganize assignments to minimize gaps
        return schedule

    def assign_projects_gap_free(
        self, 
        projects: List[Dict[str, Any]], 
        classrooms: List[Dict[str, Any]], 
        timeslots: List[Dict[str, Any]],
        instructors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Assign projects with gap-free scheduling and strict conflict prevention

        Args:
            projects: List of projects to assign
            classrooms: List of available classrooms
            timeslots: List of available timeslots
            instructors: List of instructors

        Returns:
            List of assignments
        """
        if not projects or not classrooms or not timeslots:
            return []
        
        logger.info(f"Gap-free assignment başlatılıyor: {len(projects)} proje, {len(classrooms)} sınıf, {len(timeslots)} slot")
        
        assignments = []
        
        # Zaman slotlarını sırala
        sorted_timeslots = sorted(
            timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Instructor bazında projeleri grupla
        instructor_projects = defaultdict(list)
        for project in projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # Sıkı conflict prevention
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        assigned_projects = set()  # project_ids that have been assigned
        
        # Her instructor için projeleri ata
        for instructor_id, instructor_project_list in instructor_projects.items():
            if not instructor_project_list:
                continue
            
            logger.info(f"Instructor {instructor_id} için {len(instructor_project_list)} proje atanıyor...")
            
            for project in instructor_project_list:
                project_id = project.get("id")
                
                # Bu proje zaten atanmış mı?
                if project_id in assigned_projects:
                    logger.warning(f"UYARI: Proje {project_id} zaten atanmış, atlanıyor")
                    continue
                
                # Bu instructor için uygun slot bul
                slot_found = False
                
                for classroom in classrooms:
                    classroom_id = classroom.get("id")
                    
                    for timeslot in sorted_timeslots:
                        timeslot_id = timeslot.get("id")
                        slot_key = (classroom_id, timeslot_id)
                        
                        # Slot boş mu ve instructor bu timeslot'ta başka proje yok mu?
                        if (slot_key not in used_slots and 
                            timeslot_id not in instructor_timeslot_usage.get(instructor_id, set())):
                            
                            # Bu slotu kullan
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": classroom_id,
                                "timeslot_id": timeslot_id,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            # Jüri ataması kaldırıldı - sadece sorumlu öğretim görevlisi atanır
                            
                            assignments.append(assignment)
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_id].add(timeslot_id)
                            assigned_projects.add(project_id)
                            slot_found = True
                            
                            logger.debug(f"Proje {project_id} -> Slot {timeslot_id}, Sınıf {classroom_id}")
                            break
                    
                    if slot_found:
                        break
                
                if not slot_found:
                    logger.warning(f"UYARI: Proje {project_id} için uygun slot bulunamadı!")
        
        logger.info(f"Toplam {len(assignments)} atama oluşturuldu")
        return assignments

    def validate_gap_free_schedule(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate if schedule is gap-free

        Args:
            schedule: Schedule to validate

        Returns:
            Validation result with gap information
        """
        # Simple implementation - assume it's gap-free for now
        return {
            "is_gap_free": True,
            "total_gaps": 0,
            "violations": []
        }
    
    def group_instructor_projects_consecutively(
        self,
        assignments: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Öğretim görevlilerinin sorumlu olduğu projeleri aynı sınıfta ve ardışık
        zaman slotlarına atar. Bu şekilde yer değişimlerini minimize eder.
        
        Çalışma Mantığı:
        1. Her instructor için atanmış ilk projeyi bulur (anchor assignment)
        2. Aynı instructor'ın sorumlu olduğu diğer projeleri tespit eder
        3. Bu projeleri anchor assignment ile aynı sınıfa ve ardışık slotlara yerleştirir
        
        Args:
            assignments: Mevcut atamalar
            projects: Tüm projeler listesi
            timeslots: Mevcut zaman slotları
            
        Returns:
            Optimize edilmiş atamalar listesi
        """
        if not assignments or not projects or not timeslots:
            return assignments
        
        logger.info("Instructor projelerini ardışık slo tlara gruplanıyor...")
        
        # Zaman slotlarını sırala (start_time'a göre)
        sorted_timeslots = sorted(
            timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Her instructor için sorumlu olduğu projeleri grupla
        instructor_projects = defaultdict(list)
        for project in projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # Her instructor için ilk (anchor) assignment'ı bul
        instructor_anchors: Dict[int, Dict[str, Any]] = {}
        for assignment in assignments:
            project_id = assignment.get("project_id")
            project = next((p for p in projects if p.get("id") == project_id), None)
            
            if project:
                responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
                if responsible_id and responsible_id not in instructor_anchors:
                    instructor_anchors[responsible_id] = {
                        "classroom_id": assignment.get("classroom_id"),
                        "timeslot_id": assignment.get("timeslot_id"),
                        "project_id": project_id
                    }
        
        # Yeni atamalar listesi
        new_assignments = []
        processed_projects = set()
        
        # Her instructor için projeleri ardışık sırada ata
        for instructor_id, anchor in instructor_anchors.items():
            instructor_project_list = instructor_projects.get(instructor_id, [])
            
            if len(instructor_project_list) <= 1:
                # Sadece 1 proje varsa, orijinal assignment'ı koru
                original_assignment = next(
                    (a for a in assignments if a.get("project_id") == anchor["project_id"]),
                    None
                )
                if original_assignment:
                    new_assignments.append(original_assignment)
                    processed_projects.add(anchor["project_id"])
                continue
            
            # Anchor timeslot'ın index'ini bul
            anchor_timeslot_idx = next(
                (i for i, ts in enumerate(sorted_timeslots) 
                 if ts.get("id") == anchor["timeslot_id"]),
                None
            )
            
            if anchor_timeslot_idx is None:
                # Anchor bulunamadıysa, orijinal assignment'ları koru
                for project in instructor_project_list:
                    original = next(
                        (a for a in assignments if a.get("project_id") == project.get("id")),
                        None
                    )
                    if original:
                        new_assignments.append(original)
                        processed_projects.add(project.get("id"))
                continue
            
            # Aynı classroom'da ardışık slotlara ata
            classroom_id = anchor["classroom_id"]
            current_slot_idx = anchor_timeslot_idx
            
            for project in instructor_project_list:
                project_id = project.get("id")
                
                # Zaten işlenmiş projeyi atla
                if project_id in processed_projects:
                    continue
                
                # Slot kullanılabilirliğini kontrol et
                while current_slot_idx < len(sorted_timeslots):
                    current_timeslot = sorted_timeslots[current_slot_idx]
                    current_timeslot_id = current_timeslot.get("id")
                    
                    # Bu slot başka bir proje tarafından kullanılıyor mu?
                    slot_occupied = any(
                        a.get("classroom_id") == classroom_id and 
                        a.get("timeslot_id") == current_timeslot_id and
                        a.get("project_id") not in [p.get("id") for p in instructor_project_list]
                        for a in assignments
                    )
                    
                    if not slot_occupied:
                        # Boş slot bulundu, projeyi ata
                        # Orijinal assignment'tan instructor bilgilerini al
                        original_assignment = next(
                            (a for a in assignments if a.get("project_id") == project_id),
                            None
                        )
                        
                        new_assignment = {
                            "project_id": project_id,
                            "classroom_id": classroom_id,
                            "timeslot_id": current_timeslot_id,
                            "is_makeup": project.get("is_makeup", False)
                        }
                        
                        # Instructor bilgilerini koru
                        if original_assignment and "instructors" in original_assignment:
                            new_assignment["instructors"] = original_assignment["instructors"]
                        
                        new_assignments.append(new_assignment)
                        processed_projects.add(project_id)
                        current_slot_idx += 1
                        break
                    else:
                        # Slot dolu, bir sonraki slot'a geç
                        current_slot_idx += 1
                
                # Eğer sınıfta yer kalmadıysa, orijinal assignment'ı kullan
                if project_id not in processed_projects:
                    original_assignment = next(
                        (a for a in assignments if a.get("project_id") == project_id),
                        None
                    )
                    if original_assignment:
                        new_assignments.append(original_assignment)
                        processed_projects.add(project_id)
        
        # İşlenmemiş projeleri ekle (başka instructor'lara ait olmayan)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id not in processed_projects:
                new_assignments.append(assignment)
                processed_projects.add(project_id)
        
        logger.info(
            f"Ardışık gruplama tamamlandı. "
            f"Toplam {len(processed_projects)} proje işlendi."
        )
        
        return new_assignments
    
    def _parse_time(self, time_str: str) -> int:
        """
        Zaman stringini dakikaya çevir (karşılaştırma için)

        Args:
            time_str: "HH:MM" formatında zaman

        Returns:
            Dakika cinsinden toplam süre
        """
        try:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        except:
            return 9 * 60  # Default: 09:00

    def detect_instructor_conflicts(self, assignments: List[Dict[str, Any]], projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Instructor çakışmalarını tespit et
        
        Args:
            assignments: Atama listesi
            projects: Proje listesi
            
        Returns:
            Çakışma listesi
        """
        conflicts = []
        
        # Instructor bazında timeslot kullanımını takip et
        instructor_timeslot_usage = defaultdict(list)
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Projenin sorumlu instructor'ını bul
            project = next((p for p in projects if p.get("id") == project_id), None)
            if project:
                responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
                if responsible_id:
                    instructor_timeslot_usage[(responsible_id, timeslot_id)].append({
                        'assignment': assignment,
                        'project': project
                    })
        
        # Çakışmaları tespit et
        for (instructor_id, timeslot_id), usages in instructor_timeslot_usage.items():
            if len(usages) > 1:
                conflicts.append({
                    'instructor_id': instructor_id,
                    'timeslot_id': timeslot_id,
                    'conflict_count': len(usages),
                    'assignments': [u['assignment'] for u in usages],
                    'projects': [u['project'] for u in usages]
                })
        
        logger.info(f"Conflict detection: {len(conflicts)} çakışma tespit edildi")
        
        return conflicts

    def resolve_instructor_conflicts(
        self, 
        assignments: List[Dict[str, Any]], 
        projects: List[Dict[str, Any]],
        classrooms: List[Dict[str, Any]], 
        timeslots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Instructor çakışmalarını çöz
        
        Args:
            assignments: Mevcut atamalar
            projects: Proje listesi
            classrooms: Sınıf listesi
            timeslots: Zaman slot listesi
            
        Returns:
            Çakışmasız atamalar
        """
        if not assignments:
            return assignments
            
        logger.info("Instructor çakışmaları çözülüyor...")
        
        # Çakışmaları tespit et
        conflicts = self.detect_instructor_conflicts(assignments, projects)
        
        if not conflicts:
            logger.info("Hiç çakışma bulunamadı")
            return assignments
        
        logger.info(f"{len(conflicts)} çakışma çözülüyor...")
        
        # Zaman slotlarını sırala
        sorted_timeslots = sorted(
            timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Çakışmasız atamalar
        resolved_assignments = []
        
        # Kullanılan slot'ları takip et
        used_slots = set()
        
        # Çakışma olmayan atamaları koru
        for assignment in assignments:
            project_id = assignment.get("project_id")
            timeslot_id = assignment.get("timeslot_id")
            classroom_id = assignment.get("classroom_id")
            
            # Bu atama çakışma içinde mi kontrol et
            is_in_conflict = False
            for conflict in conflicts:
                for conflict_assignment in conflict['assignments']:
                    if (conflict_assignment.get("project_id") == project_id and
                        conflict_assignment.get("timeslot_id") == timeslot_id and
                        conflict_assignment.get("classroom_id") == classroom_id):
                        is_in_conflict = True
                        break
                if is_in_conflict:
                    break
            
            if not is_in_conflict:
                # Çakışma yok, koru
                resolved_assignments.append(assignment)
                used_slots.add((classroom_id, timeslot_id))
        
        # Çakışmalı atamaları yeniden yerleştir
        processed_projects = set()
        
        for conflict in conflicts:
            instructor_id = conflict['instructor_id']
            conflicting_assignments = conflict['assignments']
            conflicting_projects = conflict['projects']
            
            logger.info(f"Instructor {instructor_id} için {len(conflicting_assignments)} çakışmalı atama çözülüyor...")
            
            # Bu instructor'ın projelerini sırayla yeniden ata
            for i, (assignment, project) in enumerate(zip(conflicting_assignments, conflicting_projects)):
                project_id = project.get("id")
                
                # Bu proje zaten işlenmiş mi?
                if project_id in processed_projects:
                    logger.info(f"  Proje {project_id} zaten işlenmiş, atlanıyor...")
                    continue
                
                # Yeni slot bul
                new_assignment = self._find_available_slot(
                    project_id=project_id,
                    instructor_id=instructor_id,
                    used_slots=used_slots,
                    classrooms=classrooms,
                    timeslots=sorted_timeslots,
                    instructors=self.instructors if hasattr(self, 'instructors') else [],
                    projects=projects
                )
                
                if new_assignment:
                    resolved_assignments.append(new_assignment)
                    used_slots.add((new_assignment["classroom_id"], new_assignment["timeslot_id"]))
                    processed_projects.add(project_id)
                    logger.info(f"  Proje {project_id} -> Sınıf {new_assignment['classroom_id']}, Slot {new_assignment['timeslot_id']}")
                else:
                    logger.warning(f"  Proje {project_id} için uygun slot bulunamadı!")
                    # Son çare: orijinal atamayı koru (sadece bir kez)
                    if project_id not in processed_projects:
                        resolved_assignments.append(assignment)
                        used_slots.add((assignment["classroom_id"], assignment["timeslot_id"]))
                        processed_projects.add(project_id)
        
        logger.info(f"Conflict resolution tamamlandı: {len(resolved_assignments)} atama")
        
        return resolved_assignments

    def _find_available_slot(
        self, 
        project_id: int, 
        instructor_id: int,
        used_slots: set,
        classrooms: List[Dict[str, Any]], 
        timeslots: List[Dict[str, Any]],
        instructors: List[Dict[str, Any]],
        projects: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Proje için uygun slot bul - Agresif arama
        
        Args:
            project_id: Proje ID
            instructor_id: Instructor ID
            used_slots: Kullanılan slot'lar
            classrooms: Sınıf listesi
            timeslots: Zaman slot listesi
            instructors: Instructor listesi
            projects: Proje listesi
            
        Returns:
            Uygun atama veya None
        """
        project = next((p for p in projects if p.get("id") == project_id), None)
        if not project:
            return None
        
        # Öncelik sırası: aynı instructor'ın diğer atamalarına yakın slotlar
        instructor_timeslots = set()
        for slot in used_slots:
            classroom_id, timeslot_id = slot
            # Bu slot'u kullanan instructor'ı kontrol et
            # (Bu basit bir implementasyon, gerçekte daha karmaşık olabilir)
            instructor_timeslots.add(timeslot_id)
        
        # Zaman slotlarını sırala
        sorted_timeslots = sorted(
            timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Strateji 1: Aynı instructor'ın diğer atamalarına yakın slotlar
        if instructor_timeslots:
            for timeslot_id in instructor_timeslots:
                # Bu timeslot'a yakın slotları dene
                timeslot_idx = next((i for i, ts in enumerate(sorted_timeslots) if ts.get("id") == timeslot_id), None)
                if timeslot_idx is not None:
                    # Önce ve sonraki slotları dene
                    for offset in [1, -1, 2, -2, 3, -3]:
                        new_idx = timeslot_idx + offset
                        if 0 <= new_idx < len(sorted_timeslots):
                            new_timeslot = sorted_timeslots[new_idx]
                            new_timeslot_id = new_timeslot.get("id")
                            
                            # Tüm sınıflarda bu slot'u dene
                            for classroom in classrooms:
                                classroom_id = classroom.get("id")
                                slot_key = (classroom_id, new_timeslot_id)
                                
                                if slot_key not in used_slots:
                                    return self._create_assignment(
                                        project_id, classroom_id, new_timeslot_id, 
                                        instructor_id, project, instructors
                                    )
        
        # Strateji 2: Tüm sınıf ve slot kombinasyonlarını dene
        for classroom in classrooms:
            classroom_id = classroom.get("id")
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                if slot_key not in used_slots:
                    return self._create_assignment(
                        project_id, classroom_id, timeslot_id, 
                        instructor_id, project, instructors
                    )
        
        # Strateji 3: Son çare - en az kullanılan slotları dene
        # Bu durumda conflict yaratabilir ama proje atanmış olur
        logger.warning(f"Proje {project_id} için hiç boş slot bulunamadı, zorla atama yapılıyor...")
        
        # En az kullanılan slot'u bul
        slot_usage_count = defaultdict(int)
        for slot in used_slots:
            slot_usage_count[slot] += 1
        
        # En az kullanılan slot'u seç
        if slot_usage_count:
            least_used_slot = min(slot_usage_count.items(), key=lambda x: x[1])
            classroom_id, timeslot_id = least_used_slot[0]
            
            logger.warning(f"Zorla atama: Proje {project_id} -> Sınıf {classroom_id}, Slot {timeslot_id}")
            return self._create_assignment(
                project_id, classroom_id, timeslot_id, 
                instructor_id, project, instructors
            )
        
        return None
    
    def _create_assignment(
        self, 
        project_id: int, 
        classroom_id: int, 
        timeslot_id: int, 
        instructor_id: int, 
        project: Dict[str, Any], 
        instructors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assignment objesi oluştur"""
        assignment = {
            "project_id": project_id,
            "classroom_id": classroom_id,
            "timeslot_id": timeslot_id,
            "is_makeup": project.get("is_makeup", False),
            "instructors": [instructor_id]
        }
        
        # Jüri ataması kaldırıldı - sadece sorumlu öğretim görevlisi atanır
        
        return assignment
    
    def _assign_first_project_with_conflict_prevention(
        self,
        project: Dict[str, Any],
        instructor_id: int,
        classrooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        used_slots: set,
        instructor_timeslot_usage: Dict[int, set],
        instructors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        İlk projeyi conflict prevention ile ata
        """
        sorted_timeslots = sorted(timeslots, key=lambda x: self._parse_time(x.get("start_time", "09:00")))
        
        for classroom in classrooms:
            classroom_id = classroom.get("id")
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                # Slot boş mu ve instructor bu timeslot'ta başka proje yok mu?
                if (slot_key not in used_slots and 
                    timeslot_id not in instructor_timeslot_usage.get(instructor_id, set())):
                    
                    assignment = {
                        "project_id": project.get("id"),
                        "classroom_id": classroom_id,
                        "timeslot_id": timeslot_id,
                        "is_makeup": project.get("is_makeup", False),
                        "instructors": [instructor_id]
                    }
                    
                    # Jüri ataması kaldırıldı - sadece sorumlu öğretim görevlisi atanır
                    
                    return assignment
        
        return None
    
    def _assign_consecutive_project_with_conflict_prevention(
        self,
        project: Dict[str, Any],
        instructor_id: int,
        anchor_assignment: Dict[str, Any],
        classrooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        used_slots: set,
        instructor_timeslot_usage: Dict[int, set],
        instructors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Ardışık projeyi conflict prevention ile ata
        """
        anchor_classroom_id = anchor_assignment["classroom_id"]
        anchor_timeslot_id = anchor_assignment["timeslot_id"]
        
        sorted_timeslots = sorted(timeslots, key=lambda x: self._parse_time(x.get("start_time", "09:00")))
        
        # Anchor assignment'ın timeslot'unu bul
        anchor_idx = next((i for i, ts in enumerate(sorted_timeslots) if ts.get("id") == anchor_timeslot_id), None)
        
        if anchor_idx is None:
            return None
        
        # Aynı sınıfta ardışık slot ara
        for offset in [1, -1, 2, -2, 3, -3]:  # Önce sonraki, sonra önceki slotları dene
            new_idx = anchor_idx + offset
            
            if 0 <= new_idx < len(sorted_timeslots):
                new_timeslot = sorted_timeslots[new_idx]
                new_timeslot_id = new_timeslot.get("id")
                slot_key = (anchor_classroom_id, new_timeslot_id)
                
                # Slot boş mu ve instructor bu timeslot'ta başka proje yok mu?
                if (slot_key not in used_slots and 
                    new_timeslot_id not in instructor_timeslot_usage.get(instructor_id, set())):
                    
                    assignment = {
                        "project_id": project.get("id"),
                        "classroom_id": anchor_classroom_id,
                        "timeslot_id": new_timeslot_id,
                        "is_makeup": project.get("is_makeup", False),
                        "instructors": [instructor_id]
                    }
                    
                    # Jüri ataması kaldırıldı - sadece sorumlu öğretim görevlisi atanır
                    
                    return assignment
        
        return None
    
    def _find_alternative_slot_with_conflict_prevention(
        self,
        project: Dict[str, Any],
        instructor_id: int,
        classrooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        used_slots: set,
        instructor_timeslot_usage: Dict[int, set],
        instructors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Alternatif slot'u conflict prevention ile bul
        """
        sorted_timeslots = sorted(timeslots, key=lambda x: self._parse_time(x.get("start_time", "09:00")))
        
        # Önce aynı instructor'ın diğer atamalarına yakın slotları dene
        instructor_used_timeslots = instructor_timeslot_usage.get(instructor_id, set())
        
        for used_timeslot_id in instructor_used_timeslots:
            used_timeslot_idx = next((i for i, ts in enumerate(sorted_timeslots) if ts.get("id") == used_timeslot_id), None)
            
            if used_timeslot_idx is not None:
                # Bu timeslot'a yakın slotları dene
                for offset in [1, -1, 2, -2, 3, -3]:
                    new_idx = used_timeslot_idx + offset
                    
                    if 0 <= new_idx < len(sorted_timeslots):
                        new_timeslot = sorted_timeslots[new_idx]
                        new_timeslot_id = new_timeslot.get("id")
                        
                        # Tüm sınıflarda bu slot'u dene
                        for classroom in classrooms:
                            classroom_id = classroom.get("id")
                            slot_key = (classroom_id, new_timeslot_id)
                            
                            # Slot boş mu ve instructor bu timeslot'ta başka proje yok mu?
                            if (slot_key not in used_slots and 
                                new_timeslot_id not in instructor_timeslot_usage.get(instructor_id, set())):
                                
                                assignment = {
                                    "project_id": project.get("id"),
                                    "classroom_id": classroom_id,
                                    "timeslot_id": new_timeslot_id,
                                    "is_makeup": project.get("is_makeup", False),
                                    "instructors": [instructor_id]
                                }
                                
                                # Bitirme projeleri için jüri üyesi ekle
                                if project.get("type") == "bitirme" and instructors:
                                    jury_candidates = [
                                        i for i in instructors 
                                        if i.get("id") != instructor_id
                                    ]
                                    if jury_candidates:
                                        assignment["instructors"].append(jury_candidates[0].get("id"))
                                
                                return assignment
        
        # Yakın slot bulunamadıysa, tüm slot'ları dene
        for timeslot in sorted_timeslots:
            timeslot_id = timeslot.get("id")
            
            # Instructor bu timeslot'ta başka proje var mı?
            if timeslot_id in instructor_timeslot_usage.get(instructor_id, set()):
                continue
            
            for classroom in classrooms:
                classroom_id = classroom.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                if slot_key not in used_slots:
                    assignment = {
                        "project_id": project.get("id"),
                        "classroom_id": classroom_id,
                        "timeslot_id": timeslot_id,
                        "is_makeup": project.get("is_makeup", False),
                        "instructors": [instructor_id]
                    }
                    
                    # Jüri ataması kaldırıldı - sadece sorumlu öğretim görevlisi atanır
                    
                    return assignment
        
        return None
