import random
import math
import numpy as np
import time
from typing import Dict, Any, List, Tuple, Set
from app.algorithms.base import BaseAlgorithm

class SimulatedAnnealingAlgorithm(BaseAlgorithm):
    def __init__(
        self,
        projects=None,
        instructors=None,
        initial_temperature=100.0,
        cooling_rate=0.01,
        iterations=1000,
        acceptance_probability=0.7
    ):
        super().__init__(projects, instructors, {
            'initial_temperature': initial_temperature,
            'cooling_rate': cooling_rate,
            'iterations': iterations,
            'acceptance_probability': acceptance_probability
        })
        
    def _initialize_solution(self) -> Dict[str, Any]:
        """Kurallara uygun başlangıç çözümünü oluştur"""
        # Her çalıştırmada farklı sonuç için random seed
        random.seed(int(time.time() * 1000) % 2**32)
        np.random.seed(int(time.time() * 1000) % 2**32)
        
        # Projeleri responsible instructor'a göre grupla
        projects_by_instructor = {}
        for p_id, project in self.projects.items():
            responsible_id = project.get('responsible_instructor_id')
            if responsible_id not in projects_by_instructor:
                projects_by_instructor[responsible_id] = []
            projects_by_instructor[responsible_id].append(p_id)
        
        # Rastgele bir instructor seç ve onun projelerini işle
        instructor_ids = list(projects_by_instructor.keys())
        random.shuffle(instructor_ids)
        
        solution = {
            'assignments': {},  # {project_id: {classroom_id, timeslot_id, jury: [instructor_ids]}}
            'instructor_classrooms': {},  # {instructor_id: classroom_id} - hocalar sınıf değiştirmesin
            'instructor_loads': {'hoca': {}, 'asistan': {}}  # Yük takibi
        }
        
        # Instructor tiplerini ayır
        hocalar = []
        asistanlar = []
        for i_id, instructor in self.instructors.items():
            if self._is_senior(instructor.get('role', '')):
                hocalar.append(i_id)
            else:
                asistanlar.append(i_id)
        
        # Yük takibini başlat
        solution['instructor_loads']['hoca'] = {hoca_id: 0 for hoca_id in hocalar}
        solution['instructor_loads']['asistan'] = {asistan_id: 0 for asistan_id in asistanlar}
        
        # Her instructor'ın projelerini işle
        for instructor_id in instructor_ids:
            instructor_projects = projects_by_instructor[instructor_id]
            random.shuffle(instructor_projects)
            
            # Bu instructor için bir sınıf seç
            instructor_classroom = None
            
            for project_id in instructor_projects:
                project = self.projects[project_id]
                
                # Sınıf seçimi
                if instructor_classroom is None:
                    # İlk proje: rastgele sınıf seç
                    available_classrooms = list(range(1, 4))  # D-106, D-107, D-108
                    random.shuffle(available_classrooms)
                    instructor_classroom = available_classrooms[0]
                
                # Zaman dilimi seç (rastgele)
                timeslot_id = random.randint(1, 20)  # 1-20 arası zaman dilimi
                
                # Jüri seçimi - kurallara uygun
                jury = self._select_jury_for_project(
                    project, instructor_id, instructor_classroom, 
                    solution['instructor_loads'], solution['instructor_classrooms']
                )
                
                # Çözüme ekle
                solution['assignments'][project_id] = {
                    'classroom_id': instructor_classroom,
                    'timeslot_id': timeslot_id,
                    'jury': jury
                }
                
                # Instructor'ın sınıfını kaydet
                solution['instructor_classrooms'][instructor_id] = instructor_classroom
                
                # Yükleri güncelle
                for jury_member in jury:
                    if jury_member in hocalar:
                        solution['instructor_loads']['hoca'][jury_member] += 1
                    else:
                        solution['instructor_loads']['asistan'][jury_member] += 1
        
        return solution
    
    def _is_senior(self, role: str) -> bool:
        """Hoca mı asistan mı kontrol et"""
        senior_roles = ['Prof. Dr.', 'Doç. Dr.', 'Dr. Öğr. Üyesi', 'Öğr. Gör. Dr.', 'Öğr. Gör.']
        return any(senior_role in role for senior_role in senior_roles)
    
    def _select_jury_for_project(self, project: Dict, responsible_id: int, classroom_id: int, 
                                instructor_loads: Dict, instructor_classrooms: Dict) -> List[int]:
        """Proje için kurallara uygun jüri seç"""
        jury = [responsible_id]
        project_type = project.get('type', 'interim')
        
        # Minimum hoca sayısı
        min_hoca_needed = 2 if project_type == 'final' else 1
        
        # Mevcut hoca sayısı
        current_hoca_count = 1 if self._is_senior(self.instructors[responsible_id].get('role', '')) else 0
        
        # Hocaları seç - sınıf değiştirmeyenler ve yük dengesizliği kontrolü
        hocalar = [i_id for i_id, instructor in self.instructors.items() 
                  if self._is_senior(instructor.get('role', ''))]
        
        available_hocalar = []
        for hoca_id in hocalar:
            if hoca_id == responsible_id:
                continue
            
            # Sınıf değiştirme kontrolü
            if hoca_id in instructor_classrooms and instructor_classrooms[hoca_id] != classroom_id:
                continue
            
            # Yük dengesizliği kontrolü (max 2 fark)
            current_load = instructor_loads['hoca'].get(hoca_id, 0)
            min_load = min(instructor_loads['hoca'].values()) if instructor_loads['hoca'].values() else 0
            if current_load - min_load > 2:
                continue
            
            available_hocalar.append(hoca_id)
        
        # Hocaları yük sıralamasına göre seç
        available_hocalar.sort(key=lambda x: instructor_loads['hoca'].get(x, 0))
        
        for hoca_id in available_hocalar:
            if current_hoca_count >= min_hoca_needed:
                break
            jury.append(hoca_id)
            current_hoca_count += 1
        
        # Asistanları seç - yük dengesizliği kontrolü
        asistanlar = [i_id for i_id, instructor in self.instructors.items() 
                     if not self._is_senior(instructor.get('role', ''))]
        
        available_asistanlar = []
        for asistan_id in asistanlar:
            if asistan_id in jury:
                continue
            
            # Yük dengesizliği kontrolü (max 2 fark)
            current_load = instructor_loads['asistan'].get(asistan_id, 0)
            min_load = min(instructor_loads['asistan'].values()) if instructor_loads['asistan'].values() else 0
            if current_load - min_load > 2:
                continue
            
            available_asistanlar.append(asistan_id)
        
        # Asistanları yük sıralamasına göre seç
        available_asistanlar.sort(key=lambda x: instructor_loads['asistan'].get(x, 0))
        
        for asistan_id in available_asistanlar:
            if len(jury) >= 3:
                break
            jury.append(asistan_id)
        
        # Eğer hala 3'den az ise, zorunlu ekle
        while len(jury) < 3:
            all_instructors = list(self.instructors.keys())
            for instructor_id in all_instructors:
                if instructor_id not in jury:
                    jury.append(instructor_id)
                    break
        
        return jury[:3]  # Maksimum 3 kişi

    def _calculate_energy(self, solution: Dict[str, Any]) -> float:
        """Çözümün enerji değerini hesapla (daha düşük daha iyidir)"""
        energy = 0.0
        violations = 0
        
        # 1. Proje türü kuralları kontrolü
        for project_id, assignment in solution['assignments'].items():
            project = self.projects[project_id]
            project_type = project.get('type', 'interim')
            jury = assignment['jury']
            
            # Hoca sayısını say
            hoca_count = 0
            for jury_member in jury:
                if self._is_senior(self.instructors[jury_member].get('role', '')):
                    hoca_count += 1
            
            # Kural ihlali kontrolü
            if project_type == 'final' and hoca_count < 2:
                energy += 1000  # Büyük ceza
                violations += 1
            elif project_type == 'interim' and hoca_count < 1:
                energy += 500   # Orta ceza
                violations += 1
        
        # 2. Yük dengesizliği kontrolü
        hoca_loads = list(solution['instructor_loads']['hoca'].values())
        asistan_loads = list(solution['instructor_loads']['asistan'].values())
        
        if hoca_loads:
            max_hoca_load = max(hoca_loads)
            min_hoca_load = min(hoca_loads)
            hoca_imbalance = max_hoca_load - min_hoca_load
            if hoca_imbalance > 2:
                energy += (hoca_imbalance - 2) * 50  # Her fazla fark için ceza
        
        if asistan_loads:
            max_asistan_load = max(asistan_loads)
            min_asistan_load = min(asistan_loads)
            asistan_imbalance = max_asistan_load - min_asistan_load
            if asistan_imbalance > 2:
                energy += (asistan_imbalance - 2) * 50  # Her fazla fark için ceza
        
        # 3. Sınıf değiştirme kontrolü
        classroom_changes = 0
        for instructor_id, classroom_id in solution['instructor_classrooms'].items():
            # Bu instructor'ın projelerini kontrol et
            instructor_projects = []
            for project_id, assignment in solution['assignments'].items():
                if assignment['jury'][0] == instructor_id:  # Responsible instructor
                    instructor_projects.append(assignment['classroom_id'])
            
            # Farklı sınıflarda projesi var mı?
            if len(set(instructor_projects)) > 1:
                classroom_changes += len(set(instructor_projects)) - 1
        
        energy += classroom_changes * 100  # Sınıf değiştirme cezası
        
        # 4. Çakışma kontrolü (aynı instructor aynı zamanda birden fazla yerde)
        timeslot_instructors = {}
        conflicts = 0
        for project_id, assignment in solution['assignments'].items():
            timeslot_id = assignment['timeslot_id']
            for jury_member in assignment['jury']:
                if timeslot_id in timeslot_instructors:
                    if jury_member in timeslot_instructors[timeslot_id]:
                        conflicts += 1
                    timeslot_instructors[timeslot_id].add(jury_member)
                else:
                    timeslot_instructors[timeslot_id] = {jury_member}
        
        energy += conflicts * 200  # Çakışma cezası
        
        return energy

    def _get_neighbor_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Komşu çözüm oluştur - Simulated Annealing prensiplerine uygun"""
        neighbor = {
            'assignments': {k: v.copy() for k, v in solution['assignments'].items()},
            'instructor_classrooms': solution['instructor_classrooms'].copy(),
            'instructor_loads': {
                'hoca': solution['instructor_loads']['hoca'].copy(),
                'asistan': solution['instructor_loads']['asistan'].copy()
            }
        }
        
        # Rastgele bir değişiklik türü seç
        change_type = random.randrange(4)
        
        if change_type == 0:  # Sınıf değiştir
            project_id = random.choice(list(neighbor['assignments'].keys()))
            old_classroom = neighbor['assignments'][project_id]['classroom_id']
            new_classroom = random.choice([1, 2, 3])  # D-106, D-107, D-108
            neighbor['assignments'][project_id]['classroom_id'] = new_classroom
        
        elif change_type == 1:  # Zaman dilimi değiştir
            project_id = random.choice(list(neighbor['assignments'].keys()))
            neighbor['assignments'][project_id]['timeslot_id'] = random.randint(1, 20)
        
        elif change_type == 2:  # Jüri üyesi değiştir
            project_id = random.choice(list(neighbor['assignments'].keys()))
            assignment = neighbor['assignments'][project_id]
            
            # Responsible instructor'ı değiştirme
            if len(assignment['jury']) > 1:
                old_jury_member = random.choice(assignment['jury'][1:])  # Responsible'ı değiştirme
                new_jury_member = random.choice(list(self.instructors.keys()))
                if new_jury_member not in assignment['jury']:
                    assignment['jury'][assignment['jury'].index(old_jury_member)] = new_jury_member
        
        else:  # Jüri sırasını değiştir
            project_id = random.choice(list(neighbor['assignments'].keys()))
            assignment = neighbor['assignments'][project_id]
            if len(assignment['jury']) > 2:
                random.shuffle(assignment['jury'][1:])  # Responsible'ı değiştirme
        
        return neighbor

    def optimize(self) -> Dict[str, Any]:
        """Tavlama benzetimi algoritmasını çalıştır - Kurallara uygun"""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
        
        # Her çalıştırmada farklı sonuç için random seed
        random.seed(int(time.time() * 1000) % 2**32)
        np.random.seed(int(time.time() * 1000) % 2**32)
        
        # Başlangıç çözümünü oluştur
        current_solution = self._initialize_solution()
        current_energy = self._calculate_energy(current_solution)
        
        best_solution = current_solution.copy()
        best_energy = current_energy
        
        temperature = self.parameters['initial_temperature']
        cooling_rate = self.parameters['cooling_rate']
        iterations = self.parameters['iterations']
        
        print(f"DEBUG: Başlangıç enerji: {current_energy}")
        
        # Ana Simulated Annealing döngüsü
        for iteration in range(iterations):
            # Komşu çözüm oluştur
            neighbor_solution = self._get_neighbor_solution(current_solution)
            neighbor_energy = self._calculate_energy(neighbor_solution)
            
            # Kabul kriteri
            delta_energy = neighbor_energy - current_energy
            
            if delta_energy < 0:  # Daha iyi çözüm
                current_solution = neighbor_solution
                current_energy = neighbor_energy
                
                if neighbor_energy < best_energy:
                    best_solution = neighbor_solution.copy()
                    best_energy = neighbor_energy
                    print(f"DEBUG: İterasyon {iteration}: Yeni en iyi enerji: {best_energy}")
            
            elif random.random() < math.exp(-delta_energy / temperature):  # Kötü çözümü kabul et
                current_solution = neighbor_solution
                current_energy = neighbor_energy
            
            # Sıcaklığı düşür
            temperature *= (1 - cooling_rate)
        
        # Sonuçları hazırla
        assignments = {}
        for project_id, assignment in best_solution['assignments'].items():
            jury = assignment['jury']
            assignments[project_id] = {
                "responsible": jury[0],
                "assistants": jury[1:] if len(jury) > 1 else []
            }
        
        return {
            "assignments": assignments,
            "energy": best_energy,
            "iterations": iterations,
            "temperature": temperature
        }