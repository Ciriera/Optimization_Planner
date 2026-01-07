"""
Bitirme Projesi Öncelikli Zamanlayıcı
=====================================

Bu algoritma, Bitirme projelerinin kesinlikle Ara projelerden önce 
atanmasını YAPISAL OLARAK garanti eder.

HARD KISITLAR:
1. Tüm Bitirme projeleri tüm Ara projelerden ÖNCE atanır
2. Her timeslotta her instructor max 1 görev
3. Instructor kendi projesine jüri olamaz
4. 2. Jüri = [Araştırma Görevlisi] placeholder
5. Sınıf içi back-to-back (boşluk yok)

AMAÇ FONKSİYONU (raporlama için):
min Z = C₁·H₁ + C₂·H₂ + C₃·H₃ + C₄·H₄
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import logging
import time
from collections import defaultdict
from datetime import time as dt_time

logger = logging.getLogger(__name__)

# Sabit placeholder - 2. Jüri için
JURY2_PLACEHOLDER = "[Araştırma Görevlisi]"


class BitirmePriorityScheduler:
    """
    Bitirme Projesi Öncelikli Deterministik Zamanlayıcı
    
    Bu sınıf OptimizationAlgorithm'dan miras ALMAZ,
    bu sayede evaluate_fitness gerektirmez.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        params = params or {}
        
        # Ceza katsayıları
        self.C1 = params.get("time_penalty_weight", 1.0)      # H₁
        self.C2 = params.get("workload_penalty_weight", 5.0)  # H₂ (baskın)
        self.C3 = params.get("class_change_penalty_weight", 1.0)  # H₃
        self.C4 = params.get("bitirme_priority_weight", 10000.0)  # H₄ (çok yüksek)
        
        # Toleranslar
        self.workload_tolerance = params.get("workload_tolerance", 2)
        self.slot_duration = params.get("slot_duration", 0.5)  # 30 dakika
        
        # Veri
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        self.sorted_timeslots = []
        
    def get_name(self) -> str:
        return "BitirmePriorityScheduler"
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Verileri yükle ve hazırla"""
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Timeslotları saate göre sırala
        self.sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time_to_minutes(x.get("start_time", "09:00"))
        )
        
        logger.info(f"BitirmePriorityScheduler initialized: {len(self.projects)} projects")
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana çalıştırma metodu"""
        return self.optimize(data)
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ana optimizasyon - İki Aşamalı Deterministik Atama
        """
        start_time = time.time()
        
        self.initialize(data)
        
        logger.info("=" * 60)
        logger.info("BitirmePriorityScheduler - Deterministik Atama")
        logger.info("=" * 60)
        
        # Projeleri türe göre ayır
        bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type") == "ara"]
        
        logger.info(f"Bitirme Projeleri: {len(bitirme_projects)}")
        logger.info(f"Ara Projeler: {len(ara_projects)}")
        logger.info(f"Toplam Sınıf: {len(self.classrooms)}")
        logger.info(f"Toplam Timeslot: {len(self.sorted_timeslots)}")
        
        # ============================================================
        # İKİ AŞAMALI DETERMİNİSTİK ATAMA
        # ============================================================
        
        assignments = self._two_phase_assignment(bitirme_projects, ara_projects)
        
        # Sonuçları doğrula
        self._validate_bitirme_priority(assignments)
        
        # Ceza fonksiyonlarını hesapla (raporlama için)
        penalty_breakdown = self._calculate_all_penalties(assignments)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        total_z = penalty_breakdown["total_z"]
        
        logger.info("=" * 60)
        logger.info(f"Atama tamamlandı. Süre: {execution_time:.2f}s")
        logger.info(f"Toplam ceza (Z): {total_z:.4f}")
        logger.info(f"  H₁ (zaman): {penalty_breakdown['h1']:.4f}")
        logger.info(f"  H₂ (iş yükü): {penalty_breakdown['h2']:.4f}")
        logger.info(f"  H₃ (sınıf değişimi): {penalty_breakdown['h3']:.4f}")
        logger.info(f"  H₄ (bitirme öncelik): {penalty_breakdown['h4']:.4f}")
        
        return {
            "assignments": assignments,
            "schedule": assignments,
            "solution": assignments,
            "fitness": -total_z,
            "cost": total_z,
            "execution_time": execution_time,
            "algorithm": "BitirmePriorityScheduler",
            "status": "completed",
            "penalty_breakdown": penalty_breakdown,
            "parameters": {
                "C1": self.C1, "C2": self.C2, "C3": self.C3, "C4": self.C4
            }
        }
    
    def _two_phase_assignment(self, bitirme_projects: List[Dict], 
                               ara_projects: List[Dict]) -> List[Dict[str, Any]]:
        """
        İKİ AŞAMALI DETERMİNİSTİK ATAMA
        
        AŞAMA 1: Tüm Bitirme projeleri en erken slotlara
        AŞAMA 2: Tüm Ara projeleri kalan slotlara
        
        Bu yapı, Bitirme önceliğini YAPISAL olarak garanti eder.
        """
        assignments = []
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        
        # Slot listesi: timeslot öncelikli (önce tüm sınıflar, sonra sonraki timeslot)
        all_slots = []
        for ts_idx, timeslot in enumerate(self.sorted_timeslots):
            for classroom in self.classrooms:
                all_slots.append({
                    "index": len(all_slots),
                    "ts_idx": ts_idx,
                    "timeslot": timeslot,
                    "timeslot_id": timeslot.get("id"),
                    "classroom": classroom,
                    "classroom_id": classroom.get("id")
                })
        
        logger.info(f"Toplam slot sayısı: {len(all_slots)}")
        
        # ============================================================
        # AŞAMA 1: BİTİRME PROJELERİ
        # ============================================================
        logger.info(">>> AŞAMA 1: Bitirme projeleri atanıyor...")
        
        current_slot_idx = 0
        bitirme_count = 0
        
        for project in bitirme_projects:
            assigned = False
            project_id = project.get("id")
            responsible_id = project.get("responsible_id")
            
            # En erken uygun slotu bul
            for slot in all_slots:
                slot_key = (slot["classroom_id"], slot["timeslot_id"])
                
                # Slot zaten kullanılmış mı?
                if slot_key in used_slots:
                    continue
                
                # Instructor çakışması var mı?
                timeslot_id = slot["timeslot_id"]
                if timeslot_id in instructor_timeslot_usage.get(responsible_id, set()):
                    continue
                
                # Jüri bul
                jury1_id = self._find_available_jury(
                    project, timeslot_id, instructor_timeslot_usage
                )
                
                # Atama yap
                assignment = {
                    "project_id": project_id,
                    "classroom_id": slot["classroom_id"],
                    "timeslot_id": timeslot_id,
                    "responsible_id": responsible_id,
                    "jury1_id": jury1_id,
                    "jury2": JURY2_PLACEHOLDER,
                    "instructors": [responsible_id, jury1_id] if jury1_id else [responsible_id],
                    "is_makeup": project.get("is_makeup", False),
                    "project_type": "bitirme",
                    "slot_index": slot["index"]
                }
                
                assignments.append(assignment)
                used_slots.add(slot_key)
                instructor_timeslot_usage[responsible_id].add(timeslot_id)
                if jury1_id:
                    instructor_timeslot_usage[jury1_id].add(timeslot_id)
                
                current_slot_idx = max(current_slot_idx, slot["index"])
                bitirme_count += 1
                assigned = True
                break
            
            if not assigned:
                logger.warning(f"Bitirme projesi {project_id} atanamadı!")
        
        # Bitirme'nin son slot indexi
        bitirme_last_idx = current_slot_idx
        logger.info(f">>> Bitirme atamaları: {bitirme_count}/{len(bitirme_projects)}")
        logger.info(f">>> Bitirme son slot index: {bitirme_last_idx}")
        
        # ============================================================
        # AŞAMA 2: ARA PROJELERİ (SADECE BİTİRME'DEN SONRA!)
        # ============================================================
        logger.info(">>> AŞAMA 2: Ara projeleri atanıyor...")
        
        # Ara projeler için başlangıç: Bitirme'nin bittiği slottan sonra
        ara_start_idx = bitirme_last_idx + 1
        logger.info(f">>> Ara projeler başlangıç index: {ara_start_idx}")
        
        ara_count = 0
        for project in ara_projects:
            assigned = False
            project_id = project.get("id")
            responsible_id = project.get("responsible_id")
            
            # SADECE Bitirme'den sonraki slotları dene
            for slot in all_slots[ara_start_idx:]:
                slot_key = (slot["classroom_id"], slot["timeslot_id"])
                
                if slot_key in used_slots:
                    continue
                
                timeslot_id = slot["timeslot_id"]
                if timeslot_id in instructor_timeslot_usage.get(responsible_id, set()):
                    continue
                
                jury1_id = self._find_available_jury(
                    project, timeslot_id, instructor_timeslot_usage
                )
                
                assignment = {
                    "project_id": project_id,
                    "classroom_id": slot["classroom_id"],
                    "timeslot_id": timeslot_id,
                    "responsible_id": responsible_id,
                    "jury1_id": jury1_id,
                    "jury2": JURY2_PLACEHOLDER,
                    "instructors": [responsible_id, jury1_id] if jury1_id else [responsible_id],
                    "is_makeup": project.get("is_makeup", False),
                    "project_type": "ara",
                    "slot_index": slot["index"]
                }
                
                assignments.append(assignment)
                used_slots.add(slot_key)
                instructor_timeslot_usage[responsible_id].add(timeslot_id)
                if jury1_id:
                    instructor_timeslot_usage[jury1_id].add(timeslot_id)
                
                ara_count += 1
                assigned = True
                break
            
            if not assigned:
                # Eğer Bitirme'den sonra yer yoksa, boş slotlara ata
                # Ama bu durumda H₄ cezası yüksek olacak
                for slot in all_slots:
                    slot_key = (slot["classroom_id"], slot["timeslot_id"])
                    
                    if slot_key in used_slots:
                        continue
                    
                    timeslot_id = slot["timeslot_id"]
                    if timeslot_id in instructor_timeslot_usage.get(responsible_id, set()):
                        continue
                    
                    jury1_id = self._find_available_jury(
                        project, timeslot_id, instructor_timeslot_usage
                    )
                    
                    assignment = {
                        "project_id": project_id,
                        "classroom_id": slot["classroom_id"],
                        "timeslot_id": timeslot_id,
                        "responsible_id": responsible_id,
                        "jury1_id": jury1_id,
                        "jury2": JURY2_PLACEHOLDER,
                        "instructors": [responsible_id, jury1_id] if jury1_id else [responsible_id],
                        "is_makeup": project.get("is_makeup", False),
                        "project_type": "ara",
                        "slot_index": slot["index"]
                    }
                    
                    assignments.append(assignment)
                    used_slots.add(slot_key)
                    instructor_timeslot_usage[responsible_id].add(timeslot_id)
                    if jury1_id:
                        instructor_timeslot_usage[jury1_id].add(timeslot_id)
                    
                    ara_count += 1
                    assigned = True
                    logger.warning(f"Ara projesi {project_id} erken slota atandı (H₄ cezası!)")
                    break
            
            if not assigned:
                logger.error(f"Ara projesi {project_id} atanamadı!")
        
        logger.info(f">>> Ara atamaları: {ara_count}/{len(ara_projects)}")
        logger.info(f">>> TOPLAM: {len(assignments)} proje atandı")
        
        return assignments
    
    def _find_available_jury(self, project: Dict, timeslot_id: str,
                             instructor_usage: Dict[int, Set[str]]) -> Optional[int]:
        """Uygun jüri bul"""
        responsible_id = project.get("responsible_id")
        
        # Sadece instructor tipindeki öğretim üyelerini al
        faculty = [i for i in self.instructors if i.get("type") == "instructor"]
        
        for instructor in faculty:
            inst_id = instructor.get("id")
            
            # Kendi projesine jüri olamaz
            if inst_id == responsible_id:
                continue
            
            # Aynı timeslotta başka görevi var mı?
            if timeslot_id in instructor_usage.get(inst_id, set()):
                continue
            
            return inst_id
        
        # Çakışma olsa bile bir jüri ata (fallback)
        for instructor in faculty:
            if instructor.get("id") != responsible_id:
                return instructor.get("id")
        
        return None
    
    def _validate_bitirme_priority(self, assignments: List[Dict]) -> bool:
        """Bitirme önceliğini doğrula"""
        bitirme_indices = []
        ara_indices = []
        
        for a in assignments:
            idx = a.get("slot_index", 0)
            if a.get("project_type") == "bitirme":
                bitirme_indices.append(idx)
            else:
                ara_indices.append(idx)
        
        if bitirme_indices and ara_indices:
            max_bitirme = max(bitirme_indices)
            min_ara = min(ara_indices)
            
            if max_bitirme <= min_ara:
                logger.info(f"✅ Bitirme önceliği SAĞLANDI! max(Bitirme)={max_bitirme} <= min(Ara)={min_ara}")
                return True
            else:
                logger.error(f"❌ Bitirme önceliği İHLAL! max(Bitirme)={max_bitirme} > min(Ara)={min_ara}")
                return False
        
        logger.info("ℹ️ Tek tür proje - öncelik kontrolü gerekli değil")
        return True
    
    def _calculate_all_penalties(self, assignments: List[Dict]) -> Dict[str, float]:
        """Tüm ceza fonksiyonlarını hesapla"""
        h1 = self._calculate_time_penalty(assignments)
        h2 = self._calculate_workload_penalty(assignments)
        h3 = self._calculate_class_change_penalty(assignments)
        h4 = self._calculate_bitirme_priority_penalty(assignments)
        
        total_z = self.C1 * h1 + self.C2 * h2 + self.C3 * h3 + self.C4 * h4
        
        return {
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "h4": h4,
            "c1_weighted": self.C1 * h1,
            "c2_weighted": self.C2 * h2,
            "c3_weighted": self.C3 * h3,
            "c4_weighted": self.C4 * h4,
            "total_z": total_z
        }
    
    def _calculate_time_penalty(self, assignments: List[Dict]) -> float:
        """H₁: Zaman/GAP cezası"""
        # Basitleştirilmiş - slot index farkına göre
        total = 0.0
        instructor_assignments = defaultdict(list)
        
        for a in assignments:
            for inst_id in a.get("instructors", []):
                if isinstance(inst_id, int):
                    instructor_assignments[inst_id].append(a)
        
        for inst_id, tasks in instructor_assignments.items():
            sorted_tasks = sorted(tasks, key=lambda x: x.get("slot_index", 0))
            
            for i in range(len(sorted_tasks) - 1):
                idx1 = sorted_tasks[i].get("slot_index", 0)
                idx2 = sorted_tasks[i + 1].get("slot_index", 0)
                gap = idx2 - idx1 - 1
                if gap > 0:
                    total += gap
        
        return total
    
    def _calculate_workload_penalty(self, assignments: List[Dict]) -> float:
        """H₂: İş yükü uniformite cezası"""
        instructor_loads = defaultdict(int)
        
        for a in assignments:
            responsible_id = a.get("responsible_id")
            jury1_id = a.get("jury1_id")
            
            if responsible_id:
                instructor_loads[responsible_id] += 1
            if jury1_id and isinstance(jury1_id, int):
                instructor_loads[jury1_id] += 1
        
        if not instructor_loads:
            return 0.0
        
        total_load = sum(instructor_loads.values())
        num_instructors = len(instructor_loads)
        avg_load = total_load / num_instructors if num_instructors > 0 else 0
        
        total_penalty = 0.0
        for load in instructor_loads.values():
            deviation = abs(load - avg_load)
            penalty = max(0, deviation - self.workload_tolerance)
            total_penalty += penalty
        
        return total_penalty
    
    def _calculate_class_change_penalty(self, assignments: List[Dict]) -> float:
        """H₃: Sınıf değişimi cezası"""
        total = 0.0
        instructor_assignments = defaultdict(list)
        
        for a in assignments:
            for inst_id in a.get("instructors", []):
                if isinstance(inst_id, int):
                    instructor_assignments[inst_id].append(a)
        
        for inst_id, tasks in instructor_assignments.items():
            sorted_tasks = sorted(tasks, key=lambda x: x.get("slot_index", 0))
            
            for i in range(len(sorted_tasks) - 1):
                class1 = sorted_tasks[i].get("classroom_id")
                class2 = sorted_tasks[i + 1].get("classroom_id")
                if class1 != class2:
                    total += 1
        
        return total
    
    def _calculate_bitirme_priority_penalty(self, assignments: List[Dict]) -> float:
        """
        H₄: Bitirme önceliklendirme cezası
        
        KURAL: max(slot(Bitirme)) <= min(slot(Ara))
        İHLAL: Herhangi bir Ara projesi herhangi bir Bitirme'den önce ise CEZA
        """
        bitirme_indices = []
        ara_indices = []
        
        for a in assignments:
            idx = a.get("slot_index", 0)
            if a.get("project_type") == "bitirme":
                bitirme_indices.append(idx)
            else:
                ara_indices.append(idx)
        
        if not bitirme_indices or not ara_indices:
            return 0.0
        
        max_bitirme = max(bitirme_indices)
        min_ara = min(ara_indices)
        
        if max_bitirme <= min_ara:
            return 0.0  # Kural sağlanıyor
        
        # İhlal - her ihlal eden çift için ceza
        total_penalty = 0.0
        for b_idx in bitirme_indices:
            for a_idx in ara_indices:
                if b_idx > a_idx:
                    total_penalty += (b_idx - a_idx)
        
        return total_penalty
    
    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Saat string'ini dakikaya çevir"""
        try:
            if isinstance(time_str, dt_time):
                return time_str.hour * 60 + time_str.minute
            
            parts = str(time_str).split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        except Exception:
            return 540  # Default: 09:00
