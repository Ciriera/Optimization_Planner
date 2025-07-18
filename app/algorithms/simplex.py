"""
Simplex algoritması sınıfı.
"""
import numpy as np
from typing import Dict, Any, List, Optional
from scipy.optimize import linprog

from app.algorithms.base import OptimizationAlgorithm

class Simplex(OptimizationAlgorithm):
    """
    Simplex algoritması sınıfı.
    Doğrusal programlama kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Simplex algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        self.params = params or {}
        self.solution = None
        
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Simplex algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplex optimizasyonunu çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Problem boyutlarını hesapla
        n_projects = len(self.projects)
        n_instructors = len(self.instructors)
        n_classrooms = len(self.classrooms)
        n_timeslots = len(self.timeslots)
        
        # Değişken sayısını hesapla
        # x[p, c, t, i] = 1 if project p is assigned to classroom c at timeslot t with instructor i
        n_variables = n_projects * n_classrooms * n_timeslots * n_instructors
        
        # Amaç fonksiyonu katsayıları (minimize)
        c = np.zeros(n_variables)
        
        # Proje-sınıf-zaman-öğretim üyesi kombinasyonları için maliyet hesapla
        var_index = 0
        for p_idx, project in enumerate(self.projects):
            for c_idx, classroom in enumerate(self.classrooms):
                for t_idx, timeslot in enumerate(self.timeslots):
                    for i_idx, instructor in enumerate(self.instructors):
                        # Öğretim üyesi yükünü dengele
                        c[var_index] = instructor.get("total_load", 0)
                        var_index += 1
        
        # Kısıtlar
        # 1. Her proje tam olarak bir sınıf-zaman-öğretim üyesi kombinasyonuna atanmalı
        A_eq = []
        b_eq = []
        
        for p_idx in range(n_projects):
            constraint = np.zeros(n_variables)
            for c_idx in range(n_classrooms):
                for t_idx in range(n_timeslots):
                    for i_idx in range(n_instructors):
                        var_idx = self._get_variable_index(p_idx, c_idx, t_idx, i_idx, n_classrooms, n_timeslots, n_instructors)
                        constraint[var_idx] = 1
            A_eq.append(constraint)
            b_eq.append(1)  # Her proje için tam olarak bir atama
        
        # 2. Bir sınıf-zaman diliminde en fazla bir proje olabilir
        A_ineq = []
        b_ineq = []
        
        for c_idx in range(n_classrooms):
            for t_idx in range(n_timeslots):
                constraint = np.zeros(n_variables)
                for p_idx in range(n_projects):
                    for i_idx in range(n_instructors):
                        var_idx = self._get_variable_index(p_idx, c_idx, t_idx, i_idx, n_classrooms, n_timeslots, n_instructors)
                        constraint[var_idx] = 1
                A_ineq.append(constraint)
                b_ineq.append(1)  # Her sınıf-zaman için en fazla bir proje
        
        # 3. Bir öğretim üyesi aynı anda birden fazla yerde olamaz
        for i_idx in range(n_instructors):
            for t_idx in range(n_timeslots):
                constraint = np.zeros(n_variables)
                for p_idx in range(n_projects):
                    for c_idx in range(n_classrooms):
                        var_idx = self._get_variable_index(p_idx, c_idx, t_idx, i_idx, n_classrooms, n_timeslots, n_instructors)
                        constraint[var_idx] = 1
                A_ineq.append(constraint)
                b_ineq.append(1)  # Her öğretim üyesi-zaman için en fazla bir atama
        
        # Değişken sınırları (0 <= x <= 1)
        bounds = [(0, 1) for _ in range(n_variables)]
        
        # Simplex algoritmasını çalıştır
        result = linprog(
            c=c,
            A_eq=A_eq,
            b_eq=b_eq,
            A_ub=A_ineq,
            b_ub=b_ineq,
            bounds=bounds,
            method="highs"
        )
        
        # Sonucu işle
        if result.success:
            # Çözümü 0-1 değerlerine yuvarla
            solution_binary = np.round(result.x).astype(int)
            
            # Atama planını oluştur
            schedule = self._create_schedule_from_solution(solution_binary, n_classrooms, n_timeslots, n_instructors)
            
            self.solution = schedule
            self.fitness_score = -result.fun  # Minimize ettiğimiz için negatifini al
            
            return {
                "schedule": schedule,
                "fitness": self.fitness_score,
                "status": result.status,
                "message": result.message
            }
        else:
            return {
                "schedule": [],
                "fitness": float('-inf'),
                "status": result.status,
                "message": result.message
            }
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Verilen çözümün uygunluğunu değerlendirir.
        
        Args:
            solution: Değerlendirilecek çözüm.
            
        Returns:
            float: Uygunluk puanı.
        """
        # Basit bir fitness fonksiyonu örneği
        score = 0.0
        
        # Çözüm geçerli mi?
        if not solution:
            return float('-inf')
        
        # Sınıf değişim sayısını minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        score -= instructor_changes * 10
        
        # Yük dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        score += load_balance * 20
        
        return score
    
    def _get_variable_index(self, p_idx: int, c_idx: int, t_idx: int, i_idx: int, n_classrooms: int, n_timeslots: int, n_instructors: int) -> int:
        """
        4 boyutlu indeksi tek boyuta dönüştürür.
        
        Args:
            p_idx: Proje indeksi
            c_idx: Sınıf indeksi
            t_idx: Zaman dilimi indeksi
            i_idx: Öğretim üyesi indeksi
            n_classrooms: Toplam sınıf sayısı
            n_timeslots: Toplam zaman dilimi sayısı
            n_instructors: Toplam öğretim üyesi sayısı
            
        Returns:
            int: Değişken indeksi
        """
        return p_idx * (n_classrooms * n_timeslots * n_instructors) + c_idx * (n_timeslots * n_instructors) + t_idx * n_instructors + i_idx
    
    def _create_schedule_from_solution(self, solution: np.ndarray, n_classrooms: int, n_timeslots: int, n_instructors: int) -> List[Dict[str, Any]]:
        """
        Simplex çözümünden atama planı oluşturur.
        
        Args:
            solution: Simplex çözümü
            n_classrooms: Toplam sınıf sayısı
            n_timeslots: Toplam zaman dilimi sayısı
            n_instructors: Toplam öğretim üyesi sayısı
            
        Returns:
            List[Dict[str, Any]]: Atama planı
        """
        schedule = []
        
        for p_idx, project in enumerate(self.projects):
            for c_idx, classroom in enumerate(self.classrooms):
                for t_idx, timeslot in enumerate(self.timeslots):
                    instructors_assigned = []
                    
                    for i_idx, instructor in enumerate(self.instructors):
                        var_idx = self._get_variable_index(p_idx, c_idx, t_idx, i_idx, n_classrooms, n_timeslots, n_instructors)
                        if solution[var_idx] == 1:
                            instructors_assigned.append(instructor["id"])
                    
                    if instructors_assigned:
                        assignment = {
                            "project_id": project["id"],
                            "classroom_id": classroom["id"],
                            "timeslot_id": timeslot["id"],
                            "instructors": instructors_assigned
                        }
                        schedule.append(assignment)
        
        return schedule
    
    def _count_instructor_classroom_changes(self, solution: List[Dict[str, Any]]) -> int:
        """
        Öğretim üyelerinin sınıf değişim sayısını hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            int: Toplam sınıf değişim sayısı
        """
        if not solution:
            return 0
        
        # Öğretim üyesi başına sınıf değişim sayısını hesapla
        instructor_locations = {}
        changes = 0
        
        # Zaman dilimine göre sırala
        sorted_solution = sorted(solution, key=lambda x: x["timeslot_id"])
        
        for assignment in sorted_solution:
            classroom_id = assignment["classroom_id"]
            for instructor_id in assignment["instructors"]:
                if instructor_id in instructor_locations:
                    if instructor_locations[instructor_id] != classroom_id:
                        changes += 1
                        instructor_locations[instructor_id] = classroom_id
                else:
                    instructor_locations[instructor_id] = classroom_id
        
        return changes
    
    def _calculate_load_balance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Öğretim üyesi yük dengesini hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            float: Yük dengesi skoru (0-1 arası, 1 en iyi)
        """
        if not solution:
            return 0.0
        
        # Öğretim üyesi başına atama sayısını hesapla
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment["instructors"]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        # Yük dengesini hesapla (Gini katsayısı)
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        
        # Gini katsayısı hesapla
        array = np.array(loads)
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1)
        n = array.shape[0]
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
        
        # Gini katsayısı 0 (tam eşitlik) ile 1 (tam eşitsizlik) arasındadır
        # Biz dengeyi istediğimiz için 1 - gini döndürüyoruz
        return 1.0 - gini
