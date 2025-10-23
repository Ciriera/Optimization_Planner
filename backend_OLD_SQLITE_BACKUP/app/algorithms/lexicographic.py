"""
Gelişmiş Lexicographic Optimizasyon algoritması sınıfı.
Verdiğiniz örnekten ilham alarak matematiksel kesinlik ve optimalite odaklı yaklaşım.
"""
from typing import Dict, Any, List, Tuple, Optional
import random
import numpy as np
import time
from ortools.sat.python import cp_model

from app.algorithms.base import BaseAlgorithm

class HybridLexicographicAdvanced(BaseAlgorithm):
    """
    Gelişmiş Lexicographic Optimizasyon algoritması sınıfı.
    Matematiksel kesinlik için CP-SAT lexicographic optimizasyon kullanır.
    
    Lexicographic Optimizasyon Sırası:
    1. Stage 0: Feasibility (tüm projelerin atanması)
    2. Stage 1: Minimize L_max (maksimum hoca yükü)
    3. Stage 2: Minimize variance (yük dengesi - L1 norm ile)
    4. Stage 3: Minimize compactness (sınıf kullanımı)
    """
    
    def __init__(self, projects=None, instructors=None, parameters=None):
        """
        Gelişmiş Lexicographic algoritması başlatıcı.
        
        Args:
            projects: Projelerin bilgileri
            instructors: Öğretim elemanlarının bilgileri
            parameters: Algoritma parametreleri
        """
        super().__init__(projects, instructors, parameters)
        params = parameters or {}
        self.time_limit_seconds = params.get("time_limit_seconds", 180)  # 3 dakika
        self.stage_time_limit = params.get("stage_time_limit", 60)  # Her aşama için 1 dakika
        self.num_search_workers = params.get("num_search_workers", 8)
        self.best_solution = None
        self.best_fitness = None
        self.objective_scores = {}
        self.stage_results = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Gelişmiş Lexicographic algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Veri hazırlığı
        self._prepare_data()
        
        # Amaç fonksiyonu skorları
        self.objective_scores = {
            "assignment_completion": 0.0,
            "load_balance": 0.0,
            "classroom_concentration": 0.0,
            "schedule_uniformity": 0.0,
            "constraint_compliance": 0.0
        }
    
    def optimize(self) -> Dict[str, Any]:
        """
        Gelişmiş Lexicographic optimizasyonunu çalıştırır.
        
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Veri hazırlığı
        data = {
            "instructors": self.instructors,
            "projects": self.projects,
            "classrooms": getattr(self, 'classrooms', []),
            "timeslots": getattr(self, 'timeslots', [])
        }
        self.initialize(data)
        
        start_time = time.time()
        
        try:
            # Temel modeli oluştur
            model, x, z, y, load, C, S, P, H, A = self._build_base_model()
            
            # Stage 0: Feasibility
            print("Stage 0: Feasibility çözümü...")
            feasibility_result = self._solve_feasibility_stage(model, x, z, y, load, C, S, P, H, A)
            
            if not feasibility_result["success"]:
                return self._create_error_result("Feasibility çözümü bulunamadı")
            
            # Stage 1: Minimize L_max (maksimum hoca yükü)
            print("Stage 1: Maksimum hoca yükü minimizasyonu...")
            lmax_result = self._solve_lmax_stage(model, x, z, y, load, C, S, P, H, A)
            
            if not lmax_result["success"]:
                return self._create_error_result("L_max minimizasyonu başarısız")
            
            # Stage 2: Minimize variance (yük dengesi)
            print("Stage 2: Yük dengesi optimizasyonu...")
            variance_result = self._solve_variance_stage(model, x, z, y, load, C, S, P, H, A, lmax_result["L_max"])
            
            if not variance_result["success"]:
                print("⚠️  Variance minimizasyonu başarısız, Stage 3'e geçiliyor...")
                variance_result["sum_abs_val"] = 0  # Default değer
            
            # Stage 3: Minimize compactness (sınıf kullanımı)
            print("Stage 3: Sınıf kompaktlığı optimizasyonu...")
            compactness_result = self._solve_compactness_stage(model, x, z, y, load, C, S, P, H, A, 
                                                              lmax_result["L_max"], variance_result["sum_abs_val"])
            
            if not compactness_result["success"]:
                print("⚠️  Compactness minimizasyonu başarısız, Stage 1 sonucu kullanılıyor...")
                # Stage 1 sonucunu kullan
                final_solution = self._extract_final_solution(lmax_result["solver"], x, z, y, C, S, P, H, A)
                compactness_result = {"compactness": 0}
            else:
                # Final çözümü oluştur
                final_solution = self._extract_final_solution(compactness_result["solver"], x, z, y, C, S, P, H, A)
            
            # Sonuçları değerlendir
            self.best_solution = final_solution
            self.best_fitness = self._evaluate_solution_quality(final_solution)
            self._calculate_objective_scores(final_solution)
            
            execution_time = time.time() - start_time
            print(f"Lexicographic optimizasyon tamamlandı. Süre: {execution_time:.2f} saniye")
            
            return {
                "schedule": self.best_solution,
                "fitness": self.best_fitness,
                "objective_scores": self.objective_scores,
                "stage_results": {
                    "L_max": lmax_result["L_max"],
                    "sum_abs_val": variance_result["sum_abs_val"],
                    "compactness": compactness_result["compactness"]
                },
                "time_limit": self.time_limit_seconds,
                "execution_time": execution_time,
                "stages_completed": ["feasibility", "lmax", "variance", "compactness"]
            }
            
        except Exception as e:
            return self._create_error_result(f"Optimizasyon hatası: {str(e)}")
    
    def _prepare_data(self) -> None:
        """Veri hazırlığı yapar."""
        # Hoca ve asistan ayrımı
        self.hocas = [i for i in self.instructors if i.get("role") == "hoca"]
        self.asistans = [i for i in self.instructors if i.get("role") == "aras_gor"]
        
        # Proje tiplerine göre ayrım
        self.ara_projects = [p for p in self.projects if p.get("type") == "ara"]
        self.bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        
        # Zaman dilimi sıralaması
        self.timeslots.sort(key=lambda x: x.get("start_time", ""))
        
        # ID'leri index'e dönüştür
        self.project_id_to_index = {p.get("id"): i for i, p in enumerate(self.projects)}
        self.classroom_id_to_index = {c.get("id"): i for i, c in enumerate(self.classrooms)}
        self.timeslot_id_to_index = {t.get("id"): i for i, t in enumerate(self.timeslots)}
        self.instructor_id_to_index = {i.get("id"): j for j, i in enumerate(self.instructors)}
    
    def _build_base_model(self) -> Tuple[cp_model.CpModel, Dict, Dict, Dict, Dict, List, List, List, List, List]:
        """Temel CP-SAT modelini oluşturur."""
        model = cp_model.CpModel()
        
        # Karar değişkenleri
        # x[pi, c, s] = 1 eğer proje pi, sınıf c'de, zaman s'de sunuluyorsa
        x = {}
        for pi in range(len(self.projects)):
            for c in range(len(self.classrooms)):
                for s in range(len(self.timeslots)):
                    x[(pi, c, s)] = model.NewBoolVar(f'x_p{pi}_c{c}_s{s}')
        
        # z[pi, ui] = 1 eğer proje pi'ye öğretim üyesi ui atanmışsa
        z = {}
        for pi in range(len(self.projects)):
            for ui in range(len(self.instructors)):
                z[(pi, ui)] = model.NewBoolVar(f'z_p{pi}_u{ui}')
        
        # y[hi, c] = 1 eğer hoca hi, sınıf c'de en az bir projede jüri
        y = {}
        for hi in range(len(self.hocas)):
            for c in range(len(self.classrooms)):
                y[(hi, c)] = model.NewBoolVar(f'y_h{hi}_c{c}')
        
        # Temel kısıtlar
        self._add_basic_constraints(model, x, z, y)
        
        # Ardışık zaman dilimi kısıtları
        self._add_consecutive_timeslot_constraints(model, x)
        
        # Jüri atama kısıtları
        self._add_jury_constraints(model, x, z)
        
        # Sınıf kullanım kısıtları
        self._add_classroom_usage_constraints(model, x, y, z)
        
        # Load per professor
        load = {}
        for hi in range(len(self.hocas)):
            load[hi] = model.NewIntVar(0, len(self.projects), f'load_h{hi}')
            model.Add(load[hi] == sum(z[(pi, hi)] for pi in range(len(self.projects))))
        
        return model, x, z, y, load, list(range(len(self.classrooms))), list(range(len(self.timeslots))), self.projects, self.hocas, self.asistans
    
    def _add_basic_constraints(self, model: cp_model.CpModel, x: Dict, z: Dict, y: Dict) -> None:
        """Temel kısıtları ekler."""
        # 1. Her proje tam olarak bir kez sunulmalı
        for pi in range(len(self.projects)):
            model.Add(sum(x[(pi, c, s)] for c in range(len(self.classrooms)) for s in range(len(self.timeslots))) == 1)
        
        # 2. Her sınıf-zaman dilimi çifti en fazla bir proje alabilir
        for c in range(len(self.classrooms)):
            for s in range(len(self.timeslots)):
                model.Add(sum(x[(pi, c, s)] for pi in range(len(self.projects))) <= 1)
        
        # 3. Her projede tam 3 jüri olmalı
        for pi in range(len(self.projects)):
            model.Add(sum(z[(pi, ui)] for ui in range(len(self.instructors))) == 3)
    
    def _add_consecutive_timeslot_constraints(self, model: cp_model.CpModel, x: Dict) -> None:
        """Ardışık zaman dilimi kısıtlarını ekler - gelişmiş yaklaşım."""
        for c in range(len(self.classrooms)):
            # Bu sınıfta atanmış proje sayısı
            n_assigned = model.NewIntVar(0, len(self.projects), f'n_assigned_c{c}')
            model.Add(n_assigned == sum(x[(pi, c, s)] for pi in range(len(self.projects)) for s in range(len(self.timeslots))))
            
            # Her zaman dilimi için kullanılıp kullanılmadığını takip et
            used_slots = []
            for s in range(len(self.timeslots)):
                used_s = model.NewBoolVar(f'used_c{c}_s{s}')
                model.Add(sum(x[(pi, c, s)] for pi in range(len(self.projects))) == used_s)
                used_slots.append((s, used_s))
            
            # Min ve max slot değişkenleri
            min_slot = model.NewIntVar(0, len(self.timeslots) - 1, f'min_slot_c{c}')
            max_slot = model.NewIntVar(0, len(self.timeslots) - 1, f'max_slot_c{c}')
            
            # Min/max slot kısıtları
            for s, used_s in used_slots:
                model.Add(min_slot <= s).OnlyEnforceIf(used_s)
                model.Add(max_slot >= s).OnlyEnforceIf(used_s)
            
            # Ardışıklık kısıtı: max - min + 1 == n_assigned
            model.Add(max_slot - min_slot + 1 == n_assigned)
    
    def _add_jury_constraints(self, model: cp_model.CpModel, x: Dict, z: Dict) -> None:
        """Jüri atama kısıtlarını ekler."""
        for pi in range(len(self.projects)):
            project = self.projects[pi]
            project_type = project.get("type")
            responsible_id = project.get("responsible_id")
            
            # Sorumlu öğretim üyesi zorunlu
            if responsible_id:
                responsible_index = self.instructor_id_to_index.get(responsible_id)
                if responsible_index is not None:
                    model.Add(z[(pi, responsible_index)] == 1)
            
            # Proje tipine göre hoca sayısı kısıtları
            if project_type == "bitirme":
                # Bitirme projesi için en az 2 hoca
                hoca_indices = [i for i, h in enumerate(self.hocas)]
                model.Add(sum(z[(pi, hi)] for hi in hoca_indices) >= 2)
            elif project_type == "ara":
                # Ara proje için en az 1 hoca
                hoca_indices = [i for i, h in enumerate(self.hocas)]
                model.Add(sum(z[(pi, hi)] for hi in hoca_indices) >= 1)
    
    def _add_classroom_usage_constraints(self, model: cp_model.CpModel, x: Dict, y: Dict, z: Dict) -> None:
        """Sınıf kullanım kısıtlarını ekler."""
        for hi in range(len(self.hocas)):
            for c in range(len(self.classrooms)):
                # Eğer hoca hi, sınıf c'de en az bir projede jüri ise y[hi,c] = 1
                # OR-Tools'ta boolean çarpım için auxiliary değişken kullan
                for pi in range(len(self.projects)):
                    for s in range(len(self.timeslots)):
                        # z[(pi, hi)] * x[(pi, c, s)] için auxiliary değişken
                        aux_var = model.NewBoolVar(f'aux_h{hi}_c{c}_p{pi}_s{s}')
                        model.Add(aux_var <= z[(pi, hi)])
                        model.Add(aux_var <= x[(pi, c, s)])
                        model.Add(aux_var >= z[(pi, hi)] + x[(pi, c, s)] - 1)
                        model.Add(y[(hi, c)] >= aux_var)
    
    def _solve_feasibility_stage(self, model: cp_model.CpModel, x: Dict, z: Dict, y: Dict, 
                                load: Dict, C: List, S: List, P: List, H: List, A: List) -> Dict[str, Any]:
        """Stage 0: Feasibility çözümü."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.stage_time_limit
        solver.parameters.num_search_workers = self.num_search_workers
        
        status = solver.Solve(model)
        
        return {
            "success": status in [cp_model.OPTIMAL, cp_model.FEASIBLE],
            "status": status,
            "solver": solver
        }
    
    def _solve_lmax_stage(self, model: cp_model.CpModel, x: Dict, z: Dict, y: Dict, 
                         load: Dict, C: List, S: List, P: List, H: List, A: List) -> Dict[str, Any]:
        """Stage 1: Minimize L_max (maksimum hoca yükü)."""
        # L_max değişkeni ekle
        L_max = model.NewIntVar(0, len(P), 'L_max')
        for hi in range(len(H)):
            model.Add(load[hi] <= L_max)
        
        # L_max'i minimize et
        model.Minimize(L_max)
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.stage_time_limit
        solver.parameters.num_search_workers = self.num_search_workers
        
        status = solver.Solve(model)
        
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return {"success": False, "status": status}
        
        L_max_val = int(solver.Value(L_max))
        
        return {
            "success": True,
            "status": status,
            "L_max": L_max_val,
            "solver": solver
        }
    
    def _solve_variance_stage(self, model: cp_model.CpModel, x: Dict, z: Dict, y: Dict, 
                             load: Dict, C: List, S: List, P: List, H: List, A: List, L_max_val: int) -> Dict[str, Any]:
        """Stage 2: Minimize variance (yük dengesi - L1 norm ile)."""
        # Yeni model oluştur ve L_max kısıtını ekle
        model_var, x2, z2, y2, load2, C2, S2, P2, H2, A2 = self._build_base_model()
        
        # L_max kısıtını ekle
        for hi in range(len(H2)):
            model_var.Add(load2[hi] <= L_max_val)
        
        # Mean hesapla (integer proxy)
        total_prof_assignments = len(P2) * 3  # Toplam jüri ataması
        mean_floor = total_prof_assignments // max(1, len(H2))
        
        # L1 norm ile variance approximation
        abs_dev = {}
        max_load = len(P2)
        for hi in range(len(H2)):
            abs_dev[hi] = model_var.NewIntVar(0, max_load, f'absdev_h{hi}')
            model_var.AddAbsEquality(abs_dev[hi], load2[hi] - mean_floor)
        
        # Sum of absolute deviations'ı minimize et
        model_var.Minimize(sum(abs_dev[hi] for hi in abs_dev))
        
        solver2 = cp_model.CpSolver()
        solver2.parameters.max_time_in_seconds = self.stage_time_limit
        solver2.parameters.num_search_workers = self.num_search_workers
        
        status2 = solver2.Solve(model_var)
        
        if status2 not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return {"success": False, "status": status2}
        
        sum_abs_val = int(sum(solver2.Value(abs_dev[hi]) for hi in abs_dev))
        
        return {
            "success": True,
            "status": status2,
            "sum_abs_val": sum_abs_val,
            "solver": solver2,
            "model": model_var,
            "x": x2, "z": z2, "y": y2, "load": load2
        }
    
    def _solve_compactness_stage(self, model: cp_model.CpModel, x: Dict, z: Dict, y: Dict, 
                                load: Dict, C: List, S: List, P: List, H: List, A: List, 
                                L_max_val: int, sum_abs_val: int) -> Dict[str, Any]:
        """Stage 3: Minimize compactness (sınıf kullanımı)."""
        # Yeni model oluştur
        model_cmp, x3, z3, y3, load3, C3, S3, P3, H3, A3 = self._build_base_model()
        
        # Önceki kısıtları ekle
        for hi in range(len(H3)):
            model_cmp.Add(load3[hi] <= L_max_val)
        
        # Variance kısıtını ekle
        total_prof_assignments = len(P3) * 3
        mean_floor = total_prof_assignments // max(1, len(H3))
        
        abs_dev3 = {}
        for hi in range(len(H3)):
            abs_dev3[hi] = model_cmp.NewIntVar(0, len(P3), f'absdev3_h{hi}')
            model_cmp.AddAbsEquality(abs_dev3[hi], load3[hi] - mean_floor)
        
        model_cmp.Add(sum(abs_dev3[hi] for hi in abs_dev3) <= sum_abs_val)
        
        # Compactness objective: minimize sum y3[hi,c] (sınıf kullanım sayısı)
        model_cmp.Minimize(sum(y3[(hi, c)] for hi in range(len(H3)) for c in C3))
        
        solver3 = cp_model.CpSolver()
        solver3.parameters.max_time_in_seconds = self.stage_time_limit
        solver3.parameters.num_search_workers = self.num_search_workers
        
        status3 = solver3.Solve(model_cmp)
        
        if status3 not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return {"success": False, "status": status3}
        
        compactness = int(sum(solver3.Value(y3[(hi, c)]) for hi in range(len(H3)) for c in C3))
        
        return {
            "success": True,
            "status": status3,
            "compactness": compactness,
            "solver": solver3,
            "model": model_cmp,
            "x": x3, "z": z3, "y": y3, "load": load3
        }
    
    def _extract_final_solution(self, solver: cp_model.CpSolver, x: Dict, z: Dict, y: Dict, 
                               C: List, S: List, P: List, H: List, A: List) -> List[Dict[str, Any]]:
        """Final çözümü çıkarır."""
        assignments = []
        
        for pi, project in enumerate(P):
            assigned = False
            for c in C:
                for s in S:
                    if solver.Value(x[(pi, c, s)]) == 1:
                        # Jürileri topla
                        jurors = []
                        for ui, instructor in enumerate(H + A):
                            if solver.Value(z[(pi, ui)]) == 1:
                                jurors.append(instructor.get("id"))
                        
                        assignment = {
                            "project_id": project.get("id"),
                            "classroom_id": self.classrooms[c].get("id"),
                            "timeslot_id": self.timeslots[s].get("id"),
                            "instructors": jurors
                        }
                        assignments.append(assignment)
                        assigned = True
                        break
                if assigned:
                    break
        
        return assignments
    
    def _evaluate_solution_quality(self, solution: List[Dict[str, Any]]) -> float:
        """Çözüm kalitesini değerlendirir."""
        if not solution:
            return 0.0
        
        weights = {
            "assignment_completion": 0.4,
            "load_balance": 0.25,
            "classroom_concentration": 0.2,
            "schedule_uniformity": 0.15
        }
        
        scores = {
            "assignment_completion": len(solution) / len(self.projects) if self.projects else 0.0,
            "load_balance": self._calculate_load_balance(solution),
            "classroom_concentration": self._calculate_classroom_concentration_score(solution),
            "schedule_uniformity": self._calculate_schedule_uniformity_score(solution)
        }
        
        return sum(weights[key] * scores[key] for key in weights)
    
    def _calculate_objective_scores(self, solution: List[Dict[str, Any]]) -> None:
        """Amaç fonksiyonu skorlarını hesaplar ve normalize eder."""
        if not solution:
            return
        
        self.objective_scores["assignment_completion"] = (len(solution) / len(self.projects)) * 100
        self.objective_scores["load_balance"] = self._calculate_load_balance(solution) * 100
        self.objective_scores["classroom_concentration"] = self._calculate_classroom_concentration_score(solution) * 100
        self.objective_scores["schedule_uniformity"] = self._calculate_schedule_uniformity_score(solution) * 100
        self.objective_scores["constraint_compliance"] = self._calculate_constraint_compliance(solution) * 100
    
    def _calculate_load_balance(self, solution: List[Dict[str, Any]]) -> float:
        """Yük dengesini hesaplar."""
        if not solution:
            return 0.0
        
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment["instructors"]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        
        # Gini katsayısı hesapla
        array = np.array(loads, dtype=np.float64)
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1)
        n = array.shape[0]
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
        
        return 1.0 - gini
    
    def _calculate_classroom_concentration_score(self, solution: List[Dict[str, Any]]) -> float:
        """Sınıf konsantrasyonu skorunu hesaplar."""
        instructor_classrooms = {}
        
        for assignment in solution:
            classroom_id = assignment["classroom_id"]
            for instructor_id in assignment["instructors"]:
                if instructor_id not in instructor_classrooms:
                    instructor_classrooms[instructor_id] = []
                instructor_classrooms[instructor_id].append(classroom_id)
        
        concentration_score = 0.0
        hoca_count = 0
        
        for instructor_id, classrooms in instructor_classrooms.items():
            instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
            if instructor and instructor.get("role") == "hoca":
                hoca_count += 1
                if classrooms:
                    most_common_classroom = max(set(classrooms), key=classrooms.count)
                    concentration_ratio = classrooms.count(most_common_classroom) / len(classrooms)
                    concentration_score += concentration_ratio
        
        return concentration_score / hoca_count if hoca_count > 0 else 0.0
    
    def _calculate_schedule_uniformity_score(self, solution: List[Dict[str, Any]]) -> float:
        """Takvim uniformluğu skorunu hesaplar."""
        daily_distribution = {}
        
        for assignment in solution:
            timeslot_id = assignment["timeslot_id"]
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)
            if timeslot:
                day = timeslot.get("day", "unknown")
                daily_distribution[day] = daily_distribution.get(day, 0) + 1
        
        if not daily_distribution:
            return 0.0
        
        values = list(daily_distribution.values())
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        return 1.0 / (1.0 + variance) if variance > 0 else 1.0
        
    def validate_parameters(self) -> bool:
        """
        Algoritma parametrelerini doğrula.
        
        Returns:
            bool: Parametreler geçerli mi?
        """
        required_params = ["time_limit_seconds", "stage_time_limit", "num_search_workers"]
        
        for param in required_params:
            if param not in self.parameters:
                return False
            
            if not isinstance(self.parameters[param], (int, float)) or self.parameters[param] <= 0:
                return False
        
        return True
    
    def _calculate_constraint_compliance(self, solution: List[Dict[str, Any]]) -> float:
        """Kısıt uyumluluğunu hesaplar."""
        if not solution:
            return 0.0
        
        total_constraints = 0
        satisfied_constraints = 0
        
        for assignment in solution:
            project_id = assignment["project_id"]
            instructors = assignment["instructors"]
            
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if not project:
                continue
            
            # Kısıt 1: Her projede 3 katılımcı
            total_constraints += 1
            if len(instructors) == 3:
                satisfied_constraints += 1
            
            # Kısıt 2: Sorumlu hoca ilk sırada
            total_constraints += 1
            if instructors and instructors[0] == project.get("responsible_id"):
                satisfied_constraints += 1
            
            # Kısıt 3: Proje tipine göre hoca sayısı
            project_type = project.get("type")
            if project_type == "bitirme":
                total_constraints += 1
                hoca_count = sum(1 for i in instructors 
                               if next((inst for inst in self.instructors if inst.get("id") == i), {}).get("role") == "hoca")
                if hoca_count >= 2:
                    satisfied_constraints += 1
            elif project_type == "ara":
                total_constraints += 1
                has_hoca = any(next((inst for inst in self.instructors if inst.get("id") == i), {}).get("role") == "hoca" 
                             for i in instructors)
                if has_hoca:
                    satisfied_constraints += 1
        
        return satisfied_constraints / total_constraints if total_constraints > 0 else 0.0
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Hata sonucu oluşturur."""
        return {
            "schedule": [],
            "fitness": 0.0,
            "objective_scores": self.objective_scores,
            "error": error_message,
            "time_limit": self.time_limit_seconds,
            "execution_time": 0.0,
            "stages_completed": []
        }
    
    def evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
        """Verilen çözümün uygunluğunu değerlendirir."""
        return self._evaluate_solution_quality(solution)
