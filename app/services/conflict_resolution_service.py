"""
🔧 CONFLICT RESOLUTION SERVICE
Görsellerde tespit edilen çakışmaları otomatik olarak çözer
"""
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime, time

logger = logging.getLogger(__name__)

class ConflictResolutionService:
    """
    Gelişmiş çakışma tespit ve çözüm servisi
    
    Tespit edilen çakışmalar:
    1. Dr. Öğretim Üyesi 3: 14:30-15:00'da 2 farklı görev
    2. Dr. Öğretim Üyesi 21: 15:00-15:30'da 2 jüri görevi  
    3. Dr. Öğretim Üyesi 11: 16:00-16:30'da 2 farklı görev
    """
    
    def __init__(self):
        self.conflict_types = {
            'instructor_double_assignment': 'Aynı instructor aynı zaman diliminde 2 farklı görevde',
            'instructor_double_jury': 'Aynı instructor aynı zaman diliminde 2 farklı jüri üyesi',
            'instructor_supervisor_jury_conflict': 'Aynı instructor hem sorumlu hem jüri aynı zamanda',
            'classroom_double_booking': 'Aynı sınıf aynı zaman diliminde 2 projede',
            'timeslot_overflow': 'Zaman dilimi kapasitesi aşıldı'
        }
    
    def detect_all_conflicts(self, assignments: List[Dict[str, Any]], 
                           projects: List[Dict[str, Any]] = None,
                           instructors: List[Dict[str, Any]] = None,
                           classrooms: List[Dict[str, Any]] = None,
                           timeslots: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Tüm çakışma türlerini tespit eder
        
        Args:
            assignments: Atama listesi
            projects: Proje listesi
            instructors: Instructor listesi  
            classrooms: Sınıf listesi
            timeslots: Zaman dilimi listesi
            
        Returns:
            List[Dict]: Tespit edilen çakışmalar
        """
        all_conflicts = []
        
        logger.info("🔍 CONFLICT DETECTION STARTED")
        
        # 1. Instructor çakışmaları
        instructor_conflicts = self._detect_instructor_conflicts(assignments)
        all_conflicts.extend(instructor_conflicts)
        
        # 2. Classroom çakışmaları
        classroom_conflicts = self._detect_classroom_conflicts(assignments)
        all_conflicts.extend(classroom_conflicts)
        
        # 3. Timeslot çakışmaları
        timeslot_conflicts = self._detect_timeslot_conflicts(assignments, timeslots)
        all_conflicts.extend(timeslot_conflicts)
        
        # 4. Cross-reference conflicts (instructor-classroom-time)
        cross_conflicts = self._detect_cross_reference_conflicts(assignments)
        all_conflicts.extend(cross_conflicts)
        
        logger.info(f"🔍 CONFLICT DETECTION COMPLETED: {len(all_conflicts)} conflicts found")
        
        # Çakışmaları kategorize et
        conflict_summary = self._categorize_conflicts(all_conflicts)
        logger.info(f"📊 CONFLICT SUMMARY: {conflict_summary}")
        
        return all_conflicts
    
    def _detect_instructor_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Instructor çakışmalarını tespit eder"""
        conflicts = []
        
        # Instructor -> Timeslot -> Assignments mapping
        instructor_timeslot_assignments = defaultdict(lambda: defaultdict(list))
        
        for assignment in assignments:
            instructor_id = assignment.get('responsible_instructor_id')
            timeslot_id = assignment.get('timeslot_id')
            instructors_list = assignment.get('instructors', [])
            project_id = assignment.get('project_id')
            
            if not instructor_id or not timeslot_id:
                continue
            
            # Responsible instructor
            instructor_timeslot_assignments[instructor_id][timeslot_id].append({
                'project_id': project_id,
                'role': 'responsible',
                'assignment': assignment
            })
            
            # Jury instructors
            for jury_instructor_id in instructors_list:
                if jury_instructor_id != instructor_id:  # Kendi projesinde jüri olamaz
                    instructor_timeslot_assignments[jury_instructor_id][timeslot_id].append({
                        'project_id': project_id,
                        'role': 'jury',
                        'assignment': assignment
                    })
        
        # Çakışmaları tespit et
        for instructor_id, timeslot_assignments in instructor_timeslot_assignments.items():
            for timeslot_id, assignments_list in timeslot_assignments.items():
                if len(assignments_list) > 1:
                    # Çakışma tespit edildi!
                    conflict_type = self._determine_instructor_conflict_type(assignments_list)
                    
                    conflicts.append({
                        'type': conflict_type,
                        'instructor_id': instructor_id,
                        'timeslot_id': timeslot_id,
                        'conflicting_assignments': assignments_list,
                        'conflict_count': len(assignments_list),
                        'severity': self._calculate_conflict_severity(assignments_list),
                        'description': f"Instructor {instructor_id} has {len(assignments_list)} assignments in timeslot {timeslot_id}",
                        'resolution_strategy': self._get_resolution_strategy(conflict_type)
                    })
        
        logger.info(f"Instructor conflicts detected: {len(conflicts)}")
        return conflicts
    
    def _detect_classroom_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sınıf çakışmalarını tespit eder"""
        conflicts = []
        
        # Classroom -> Timeslot -> Assignments mapping
        classroom_timeslot_assignments = defaultdict(lambda: defaultdict(list))
        
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            timeslot_id = assignment.get('timeslot_id')
            project_id = assignment.get('project_id')
            
            if not classroom_id or not timeslot_id:
                continue
            
            classroom_timeslot_assignments[classroom_id][timeslot_id].append({
                'project_id': project_id,
                'assignment': assignment
            })
        
        # Çakışmaları tespit et
        for classroom_id, timeslot_assignments in classroom_timeslot_assignments.items():
            for timeslot_id, assignments_list in timeslot_assignments.items():
                if len(assignments_list) > 1:
                    conflicts.append({
                        'type': 'classroom_double_booking',
                        'classroom_id': classroom_id,
                        'timeslot_id': timeslot_id,
                        'conflicting_assignments': assignments_list,
                        'conflict_count': len(assignments_list),
                        'severity': 'HIGH',
                        'description': f"Classroom {classroom_id} has {len(assignments_list)} projects in timeslot {timeslot_id}",
                        'resolution_strategy': 'relocate_to_available_classroom'
                    })
        
        logger.info(f"Classroom conflicts detected: {len(conflicts)}")
        return conflicts
    
    def _detect_timeslot_conflicts(self, assignments: List[Dict[str, Any]], 
                                 timeslots: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Zaman dilimi çakışmalarını tespit eder"""
        conflicts = []
        
        if not timeslots:
            return conflicts
        
        # Timeslot capacity analysis
        timeslot_usage = defaultdict(list)
        
        for assignment in assignments:
            timeslot_id = assignment.get('timeslot_id')
            project_id = assignment.get('project_id')
            
            if timeslot_id:
                timeslot_usage[timeslot_id].append(project_id)
        
        # Her zaman diliminin kapasitesini kontrol et
        for timeslot in timeslots:
            timeslot_id = timeslot.get('id')
            capacity = timeslot.get('capacity', 10)  # Default capacity
            used_count = len(timeslot_usage.get(timeslot_id, []))
            
            if used_count > capacity:
                conflicts.append({
                    'type': 'timeslot_overflow',
                    'timeslot_id': timeslot_id,
                    'capacity': capacity,
                    'used_count': used_count,
                    'overflow': used_count - capacity,
                    'severity': 'HIGH',
                    'description': f"Timeslot {timeslot_id} overflow: {used_count}/{capacity}",
                    'resolution_strategy': 'redistribute_to_other_timeslots'
                })
        
        logger.info(f"Timeslot conflicts detected: {len(conflicts)}")
        return conflicts
    
    def _detect_cross_reference_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cross-reference çakışmalarını tespit eder"""
        conflicts = []
        
        # Instructor availability matrix
        instructor_availability = defaultdict(set)  # instructor_id -> {occupied_timeslots}
        
        for assignment in assignments:
            instructor_id = assignment.get('responsible_instructor_id')
            timeslot_id = assignment.get('timeslot_id')
            instructors_list = assignment.get('instructors', [])
            
            if instructor_id and timeslot_id:
                instructor_availability[instructor_id].add(timeslot_id)
            
            for jury_instructor_id in instructors_list:
                if jury_instructor_id != instructor_id:
                    instructor_availability[jury_instructor_id].add(timeslot_id)
        
        # Çakışmaları tespit et
        for instructor_id, occupied_timeslots in instructor_availability.items():
            if len(occupied_timeslots) > 1:
                # Bu instructor birden fazla zaman diliminde meşgul
                # Bu normal olabilir, ama aynı zaman diliminde birden fazla görev varsa problem
                pass  # Bu durum zaten _detect_instructor_conflicts'te tespit ediliyor
        
        return conflicts
    
    def _determine_instructor_conflict_type(self, assignments_list: List[Dict[str, Any]]) -> str:
        """Instructor çakışma türünü belirler"""
        roles = [assignment['role'] for assignment in assignments_list]
        
        if 'responsible' in roles and 'jury' in roles:
            return 'instructor_supervisor_jury_conflict'
        elif roles.count('responsible') > 1:
            return 'instructor_double_assignment'
        elif roles.count('jury') > 1:
            return 'instructor_double_jury'
        else:
            return 'instructor_multiple_roles'
    
    def _calculate_conflict_severity(self, assignments_list: List[Dict[str, Any]]) -> str:
        """Çakışma şiddetini hesaplar"""
        if len(assignments_list) > 2:
            return 'CRITICAL'
        elif len(assignments_list) == 2:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def _get_resolution_strategy(self, conflict_type: str) -> str:
        """Çakışma türüne göre çözüm stratejisi belirler"""
        strategies = {
            'instructor_supervisor_jury_conflict': 'reschedule_one_assignment',
            'instructor_double_assignment': 'reschedule_duplicate_assignment',
            'instructor_double_jury': 'replace_jury_member',
            'classroom_double_booking': 'relocate_to_available_classroom',
            'timeslot_overflow': 'redistribute_to_other_timeslots'
        }
        return strategies.get(conflict_type, 'manual_resolution')
    
    def _categorize_conflicts(self, conflicts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Çakışmaları kategorize eder"""
        categories = defaultdict(int)
        for conflict in conflicts:
            categories[conflict['type']] += 1
        return dict(categories)
    
    def resolve_conflicts(self, assignments: List[Dict[str, Any]], 
                         conflicts: List[Dict[str, Any]],
                         projects: List[Dict[str, Any]] = None,
                         instructors: List[Dict[str, Any]] = None,
                         classrooms: List[Dict[str, Any]] = None,
                         timeslots: List[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Çakışmaları çözer
        
        Returns:
            Tuple[List[Dict], List[Dict]]: (resolved_assignments, resolution_log)
        """
        logger.info(f"🔧 CONFLICT RESOLUTION STARTED: {len(conflicts)} conflicts to resolve")
        
        resolved_assignments = assignments.copy()
        resolution_log = []
        
        # Çakışmaları şiddete göre sırala (CRITICAL -> HIGH -> MEDIUM)
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_conflicts = sorted(conflicts, key=lambda x: severity_order.get(x.get('severity', 'LOW'), 3))
        
        for conflict in sorted_conflicts:
            try:
                resolution_result = self._resolve_single_conflict(
                    conflict, resolved_assignments, projects, instructors, classrooms, timeslots
                )
                
                if resolution_result['success']:
                    resolved_assignments = resolution_result['assignments']
                    resolution_log.append({
                        'conflict_id': conflict.get('type', 'unknown'),
                        'resolution_strategy': conflict.get('resolution_strategy', 'unknown'),
                        'success': True,
                        'changes_made': resolution_result.get('changes_made', []),
                        'description': f"Successfully resolved {conflict['type']}"
                    })
                    logger.info(f"✅ RESOLVED: {conflict['description']}")
                else:
                    resolution_log.append({
                        'conflict_id': conflict.get('type', 'unknown'),
                        'resolution_strategy': conflict.get('resolution_strategy', 'unknown'),
                        'success': False,
                        'error': resolution_result.get('error', 'Unknown error'),
                        'description': f"Failed to resolve {conflict['type']}"
                    })
                    logger.warning(f"❌ FAILED: {conflict['description']}")
                    
            except Exception as e:
                logger.error(f"Error resolving conflict {conflict.get('type', 'unknown')}: {e}")
                resolution_log.append({
                    'conflict_id': conflict.get('type', 'unknown'),
                    'success': False,
                    'error': str(e),
                    'description': f"Exception during resolution: {conflict['type']}"
                })
        
        # Çözüm sonrası doğrulama
        remaining_conflicts = self.detect_all_conflicts(resolved_assignments, projects, instructors, classrooms, timeslots)
        
        logger.info(f"🔧 CONFLICT RESOLUTION COMPLETED")
        logger.info(f"   - Conflicts resolved: {len([r for r in resolution_log if r['success']])}")
        logger.info(f"   - Conflicts failed: {len([r for r in resolution_log if not r['success']])}")
        logger.info(f"   - Remaining conflicts: {len(remaining_conflicts)}")
        
        return resolved_assignments, resolution_log
    
    def _resolve_single_conflict(self, conflict: Dict[str, Any], 
                                assignments: List[Dict[str, Any]],
                                projects: List[Dict[str, Any]] = None,
                                instructors: List[Dict[str, Any]] = None,
                                classrooms: List[Dict[str, Any]] = None,
                                timeslots: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Tek bir çakışmayı çözer"""
        
        conflict_type = conflict.get('type')
        strategy = conflict.get('resolution_strategy')
        
        try:
            if strategy == 'reschedule_one_assignment':
                return self._reschedule_one_assignment(conflict, assignments, timeslots)
            elif strategy == 'reschedule_duplicate_assignment':
                return self._reschedule_duplicate_assignment(conflict, assignments, timeslots)
            elif strategy == 'replace_jury_member':
                return self._replace_jury_member(conflict, assignments, instructors)
            elif strategy == 'relocate_to_available_classroom':
                return self._relocate_to_available_classroom(conflict, assignments, classrooms)
            elif strategy == 'redistribute_to_other_timeslots':
                return self._redistribute_to_other_timeslots(conflict, assignments, timeslots)
            else:
                return {'success': False, 'error': f'Unknown strategy: {strategy}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _reschedule_one_assignment(self, conflict: Dict[str, Any], 
                                  assignments: List[Dict[str, Any]], 
                                  timeslots: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Bir atamayı yeniden zamanla"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        if len(conflicting_assignments) < 2:
            return {'success': False, 'error': 'Not enough conflicting assignments'}
        
        # İkinci atamayı yeniden zamanla (birinciyi koru)
        assignment_to_move = conflicting_assignments[1]['assignment']
        
        if not timeslots:
            return {'success': False, 'error': 'No timeslots available for rescheduling'}
        
        # Boş zaman dilimi bul
        used_timeslots = {a.get('timeslot_id') for a in assignments if a.get('timeslot_id')}
        available_timeslots = [ts for ts in timeslots if ts.get('id') not in used_timeslots]
        
        if not available_timeslots:
            # Hiç boş zaman dilimi yok, mevcut olanlar arasından seç
            available_timeslots = timeslots
        
        # En uygun zaman dilimini seç
        new_timeslot = available_timeslots[0]
        old_timeslot_id = assignment_to_move.get('timeslot_id')
        
        # Atamayı güncelle
        for assignment in assignments:
            if assignment.get('project_id') == assignment_to_move.get('project_id'):
                assignment['timeslot_id'] = new_timeslot.get('id')
                changes_made.append({
                    'project_id': assignment.get('project_id'),
                    'old_timeslot': old_timeslot_id,
                    'new_timeslot': new_timeslot.get('id'),
                    'action': 'rescheduled'
                })
                break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _reschedule_duplicate_assignment(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]], 
                                       timeslots: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Çoğaltılmış atamayı yeniden zamanla"""
        return self._reschedule_one_assignment(conflict, assignments, timeslots)
    
    def _replace_jury_member(self, conflict: Dict[str, Any], 
                           assignments: List[Dict[str, Any]], 
                           instructors: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Jüri üyesini değiştir"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        instructor_id = conflict.get('instructor_id')
        timeslot_id = conflict.get('timeslot_id')
        
        # Bu zaman diliminde meşgul olmayan instructor bul
        busy_instructors = set()
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                busy_instructors.add(assignment.get('responsible_instructor_id'))
                busy_instructors.update(assignment.get('instructors', []))
        
        available_instructors = []
        if instructors:
            for instructor in instructors:
                if instructor.get('id') not in busy_instructors:
                    available_instructors.append(instructor)
        
        if not available_instructors:
            return {'success': False, 'error': 'No available instructors for replacement'}
        
        # İlk uygun instructor'ı seç
        replacement_instructor = available_instructors[0]['id']
        
        # Jüri üyesini değiştir
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                instructors_list = assignment.get('instructors', [])
                if instructor_id in instructors_list:
                    instructors_list.remove(instructor_id)
                    instructors_list.append(replacement_instructor)
                    assignment['instructors'] = instructors_list
                    
                    changes_made.append({
                        'assignment_id': assignment.get('project_id'),
                        'old_jury': instructor_id,
                        'new_jury': replacement_instructor,
                        'action': 'jury_replaced'
                    })
                    break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _relocate_to_available_classroom(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]], 
                                       classrooms: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Boş sınıfa taşı"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        classroom_id = conflict.get('classroom_id')
        timeslot_id = conflict.get('timeslot_id')
        
        # Bu zaman diliminde meşgul olmayan sınıf bul
        busy_classrooms = set()
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                busy_classrooms.add(assignment.get('classroom_id'))
        
        available_classrooms = []
        if classrooms:
            for classroom in classrooms:
                if classroom.get('id') not in busy_classrooms:
                    available_classrooms.append(classroom)
        
        if not available_classrooms:
            return {'success': False, 'error': 'No available classrooms for relocation'}
        
        # İlk uygun sınıfı seç
        new_classroom_id = available_classrooms[0]['id']
        
        # Sınıfı değiştir
        for assignment in assignments:
            if (assignment.get('classroom_id') == classroom_id and 
                assignment.get('timeslot_id') == timeslot_id):
                assignment['classroom_id'] = new_classroom_id
                
                changes_made.append({
                    'assignment_id': assignment.get('project_id'),
                    'old_classroom': classroom_id,
                    'new_classroom': new_classroom_id,
                    'action': 'relocated'
                })
                break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _redistribute_to_other_timeslots(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]], 
                                       timeslots: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Diğer zaman dilimlerine yeniden dağıt"""
        changes_made = []
        
        timeslot_id = conflict.get('timeslot_id')
        overflow = conflict.get('overflow', 0)
        
        if not timeslots or overflow <= 0:
            return {'success': False, 'error': 'Invalid overflow or no timeslots available'}
        
        # Bu zaman dilimindeki fazla atamaları bul
        timeslot_assignments = [a for a in assignments if a.get('timeslot_id') == timeslot_id]
        
        if len(timeslot_assignments) <= overflow:
            return {'success': False, 'error': 'Not enough assignments to redistribute'}
        
        # Boş zaman dilimleri bul
        used_timeslots = defaultdict(int)
        for assignment in assignments:
            used_timeslots[assignment.get('timeslot_id')] += 1
        
        available_timeslots = []
        for ts in timeslots:
            if ts.get('id') != timeslot_id and used_timeslots.get(ts.get('id'), 0) < ts.get('capacity', 10):
                available_timeslots.append(ts)
        
        if not available_timeslots:
            return {'success': False, 'error': 'No available timeslots for redistribution'}
        
        # Fazla atamaları yeniden dağıt
        assignments_to_move = timeslot_assignments[-overflow:]
        
        for i, assignment in enumerate(assignments_to_move):
            target_timeslot = available_timeslots[i % len(available_timeslots)]
            old_timeslot_id = assignment.get('timeslot_id')
            
            assignment['timeslot_id'] = target_timeslot.get('id')
            
            changes_made.append({
                'assignment_id': assignment.get('project_id'),
                'old_timeslot': old_timeslot_id,
                'new_timeslot': target_timeslot.get('id'),
                'action': 'redistributed'
            })
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def generate_conflict_report(self, conflicts: List[Dict[str, Any]], 
                               resolution_log: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Çakışma raporu oluşturur"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_conflicts': len(conflicts),
            'conflict_summary': self._categorize_conflicts(conflicts),
            'severity_breakdown': self._get_severity_breakdown(conflicts),
            'detailed_conflicts': conflicts
        }
        
        if resolution_log:
            report['resolution_summary'] = {
                'total_attempted': len(resolution_log),
                'successful': len([r for r in resolution_log if r.get('success', False)]),
                'failed': len([r for r in resolution_log if not r.get('success', False)]),
                'resolution_log': resolution_log
            }
        
        return report
    
    def _get_severity_breakdown(self, conflicts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Şiddet dağılımını hesaplar"""
        severity_counts = defaultdict(int)
        for conflict in conflicts:
            severity = conflict.get('severity', 'UNKNOWN')
            severity_counts[severity] += 1
        return dict(severity_counts)
    
    def _get_most_problematic_instructors(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """En problemli instructor'ları bulur"""
        instructor_conflicts = defaultdict(lambda: {'count': 0, 'types': set()})
        
        for conflict in conflicts:
            if 'instructor_id' in conflict:
                instructor_id = conflict['instructor_id']
                instructor_conflicts[instructor_id]['count'] += 1
                instructor_conflicts[instructor_id]['types'].add(conflict['type'])
        
        # En çok çakışması olan instructor'ları sırala
        problematic = []
        for instructor_id, data in instructor_conflicts.items():
            problematic.append({
                'instructor_id': instructor_id,
                'conflict_count': data['count'],
                'conflict_types': list(data['types'])
            })
        
        return sorted(problematic, key=lambda x: x['conflict_count'], reverse=True)
    
    def _get_most_problematic_timeslots(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """En problemli zaman dilimlerini bulur"""
        timeslot_conflicts = defaultdict(lambda: {'count': 0, 'types': set()})
        
        for conflict in conflicts:
            if 'timeslot_id' in conflict:
                timeslot_id = conflict['timeslot_id']
                timeslot_conflicts[timeslot_id]['count'] += 1
                timeslot_conflicts[timeslot_id]['types'].add(conflict['type'])
        
        # En çok çakışması olan zaman dilimlerini sırala
        problematic = []
        for timeslot_id, data in timeslot_conflicts.items():
            problematic.append({
                'timeslot_id': timeslot_id,
                'conflict_count': data['count'],
                'conflict_types': list(data['types'])
            })
        
        return sorted(problematic, key=lambda x: x['conflict_count'], reverse=True)
    
    def _get_most_problematic_classrooms(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """En problemli sınıfları bulur"""
        classroom_conflicts = defaultdict(lambda: {'count': 0, 'types': set()})
        
        for conflict in conflicts:
            if 'classroom_id' in conflict:
                classroom_id = conflict['classroom_id']
                classroom_conflicts[classroom_id]['count'] += 1
                classroom_conflicts[classroom_id]['types'].add(conflict['type'])
        
        # En çok çakışması olan sınıfları sırala
        problematic = []
        for classroom_id, data in classroom_conflicts.items():
            problematic.append({
                'classroom_id': classroom_id,
                'conflict_count': data['count'],
                'conflict_types': list(data['types'])
            })
        
        return sorted(problematic, key=lambda x: x['conflict_count'], reverse=True)
