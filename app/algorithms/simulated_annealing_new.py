"""
Benzetimli Tavlama algoritmasi sinifi.
"""
import random
import math
from typing import Dict, Any, List, Tuple
import numpy as np

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class SimulatedAnnealing(OptimizationAlgorithm):
    """
    Benzetimli Tavlama algoritmasi sinifi.
    Benzetimli Tavlama kullanarak proje atama problemini cozer.
    """
    
    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free icin onceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Dict[str, Any] = None):
        """
        Benzetimli Tavlama algoritmasi baslatici.

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.initial_temperature = params.get("initial_temperature", 1000.0)
        self.cooling_rate = params.get("cooling_rate", 0.95)
        self.iterations_per_temp = params.get("iterations_per_temp", 100)
        self.min_temperature = params.get("min_temperature", 1.0)
        self.temperature = self.initial_temperature
        self.current_solution = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Benzetimli Tavlama algoritmasini baslangic cozumu ile baslatir.
        
        Args:
            data: Algoritma giris verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Baslangic cozumunu olustur
        self.current_solution = self._create_random_solution()
        self.fitness_score = self.evaluate_fitness(self.current_solution)
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Benzetimli Tavlama optimizasyonunu calistirir.
        
        Args:
            data: Algoritma giris verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        temperature = self.initial_temperature
        current_solution = self.current_solution
        current_fitness = self.fitness_score
        best_solution = current_solution
        best_fitness = current_fitness
        
        # Sicaklik dusene kadar devam et
        while temperature > self.min_temperature:
            for _ in range(self.iterations_per_temp):
                # Komsu cozum olustur
                neighbor = self._get_neighbor_solution(current_solution)
                neighbor_fitness = self.evaluate_fitness(neighbor)
                
                # Komsu cozumu kabul et veya reddet
                if self._acceptance_probability(current_fitness, neighbor_fitness, temperature) > random.random():
                    current_solution = neighbor
                    current_fitness = neighbor_fitness
                    
                    # En iyi cozumu guncelle
                    if current_fitness > best_fitness:
                        best_solution = current_solution
                        best_fitness = current_fitness
            
            # Sicakligi dusur
            temperature *= self.cooling_rate
        
        # Sonucu dondur
        return {
            "schedule": best_solution,
            "fitness": best_fitness,
            "temperature": self.initial_temperature,
            "cooling_rate": self.cooling_rate
        }
    
    def evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
        """
        Verilen cozumun uygunlugunu degerlendirir.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Uygunluk puani.
        """
        # Basit bir fitness fonksiyonu ornegi
        score = 0.0
        
        # Cozum gecerli mi?
        if not self._is_valid_solution(solution):
            return float('-inf')
        
        # Sinif degisim sayisini minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        score -= instructor_changes * 10
        
        # Yuk dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        score += load_balance * 20

        # Zaman slot cezasi ve odul entegrasyonu
        try:
            penalty = getattr(self, "_calculate_time_slot_penalty", lambda s: 0.0)(solution)
            reward = getattr(self, "_calculate_total_slot_reward", lambda s: 0.0)(solution)
            score = score - penalty + (reward / 50.0)
        except Exception:
            pass
        
        return score
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """
        Rastgele bir cozum olusturur.
        
        Returns:
            List[Dict[str, Any]]: Rastgele cozum.
        """
        solution = []
        
        # Her proje icin rastgele bir sinif ve zaman dilimi ata
        for project in self.projects:
            classroom = random.choice(self.classrooms) if self.classrooms else None
            timeslot = random.choice(self.timeslots) if self.timeslots else None
            
            if classroom and timeslot:
                assignment = {
                    "project_id": project["id"],
                    "classroom_id": classroom["id"],
                    "timeslot_id": timeslot["id"],
                    "instructors": [project["responsible_id"]]
                }
                
                # Rastgele 1-2 yardimci katilimci ekle
                available_instructors = [i for i in self.instructors if i["id"] != project["responsible_id"]]
                if available_instructors:
                    assistant_count = random.randint(1, 2)
                    assistants = random.sample(available_instructors, min(assistant_count, len(available_instructors)))
                    for assistant in assistants:
                        assignment["instructors"].append(assistant["id"])
                
                solution.append(assignment)
        
        return solution
    
    def _get_neighbor_solution(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Komsu cozum olusturur.
        
        Args:
            solution: Mevcut cozum.
            
        Returns:
            List[Dict[str, Any]]: Komsu cozum.
        """
        # Cozumu kopyala
        neighbor = [assignment.copy() for assignment in solution]
        
        # Rastgele bir degisiklik yap
        if not neighbor:
            return neighbor
        
        change_type = random.choice(["classroom", "timeslot", "instructor"])
        assignment_index = random.randint(0, len(neighbor) - 1)
        
        if change_type == "classroom" and self.classrooms:
            # Sinif degistir
            new_classroom = random.choice(self.classrooms)
            neighbor[assignment_index]["classroom_id"] = new_classroom["id"]
        
        elif change_type == "timeslot" and self.timeslots:
            # Zaman dilimi degistir
            new_timeslot = random.choice(self.timeslots)
            neighbor[assignment_index]["timeslot_id"] = new_timeslot["id"]
        
        elif change_type == "instructor" and len(self.instructors) > 1:
            # Yardimci katilimci degistir
            assignment = neighbor[assignment_index]
            responsible_id = assignment["instructors"][0]  # Ilk katilimci her zaman sorumlu kisidir
            
            # Mevcut yardimci katilimcilari kaldir
            assignment["instructors"] = [responsible_id]
            
            # Yeni yardimci katilimcilar ekle
            available_instructors = [i for i in self.instructors if i["id"] != responsible_id]
            if available_instructors:
                assistant_count = random.randint(1, 2)
                assistants = random.sample(available_instructors, min(assistant_count, len(available_instructors)))
                for assistant in assistants:
                    assignment["instructors"].append(assistant["id"])
        
        return neighbor
    
    def _acceptance_probability(self, current_fitness: float, neighbor_fitness: float, temperature: float) -> float:
        """
        Kotu bir cozumu kabul etme olasiligini hesaplar.
        
        Args:
            current_fitness: Mevcut cozumun uygunluk puani.
            neighbor_fitness: Komsu cozumun uygunluk puani.
            temperature: Mevcut sicaklik.
            
        Returns:
            float: Kabul olasiligi (0-1 arasi).
        """
        # Daha iyi cozumu her zaman kabul et
        if neighbor_fitness > current_fitness:
            return 1.0
        
        # Kotu cozumu sicakliga bagli olarak kabul et
        delta = neighbor_fitness - current_fitness
        return math.exp(delta / temperature)
    
    def _is_valid_solution(self, solution: List[Dict[str, Any]]) -> bool:
        """
        Cozumun gecerli olup olmadigini kontrol eder.
        
        Args:
            solution: Kontrol edilecek cozum.
            
        Returns:
            bool: Cozum gecerli ise True, degilse False.
        """
        # Cakisma kontrolu
        assignments = {}
        
        for assignment in solution:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Ayni sinif ve zaman diliminde baska bir atama var mi?
            key = f"{classroom_id}_{timeslot_id}"
            if key in assignments:
                return False
            
            assignments[key] = True
        
        return True
    
    def _count_instructor_classroom_changes(self, solution: List[Dict[str, Any]]) -> int:
        """
        Ogretim uyelerinin sinif degisim sayisini hesaplar.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            int: Sinif degisim sayisi.
        """
        instructor_schedule = {}
        changes = 0
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_schedule:
                    instructor_schedule[instructor_id] = []
                
                instructor_schedule[instructor_id].append(assignment)
        
        # Her ogretim uyesi icin sinif degisim sayisini hesapla
        for instructor_id, assignments in instructor_schedule.items():
            # Zaman dilimine gore sirala
            assignments.sort(key=lambda x: x.get("timeslot_id"))
            
            # Ardisik atamalar arasinda sinif degisimi var mi?
            for i in range(1, len(assignments)):
                if assignments[i].get("classroom_id") != assignments[i-1].get("classroom_id"):
                    changes += 1
        
        return changes
    
    def _calculate_load_balance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Ogretim uyeleri arasindaki yuk dengesini hesaplar.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Yuk dengesi puani (0-1 arasi).
        """
        instructor_loads = {}
        
        # Her ogretim uyesi icin yuk hesapla
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        # Standart sapma hesapla
        loads = list(instructor_loads.values())
        mean = sum(loads) / len(loads)
        variance = sum((load - mean) ** 2 for load in loads) / len(loads)
        std_dev = variance ** 0.5
        
        # Standart sapma ne kadar dusukse, denge o kadar iyi
        if mean == 0:
            return 1.0
        
        # Normalize edilmis denge puani (0-1 arasi)
        balance = max(0, 1 - (std_dev / mean))
        
        return balance 