"""
Base algorithm classes for optimization algorithms.
This file contains the base classes that all optimization algorithms should inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime
from app.models.project import Project
from app.models.instructor import Instructor
from app.models.student import Student
from app.algorithms.validator import validate_solution, generate_reports
from app.algorithms.fitness_helpers import FitnessMetrics


class OptimizationAlgorithm(ABC):
    """
    Optimizasyon algoritmalari icin temel sinif.
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Optimizasyon algoritmasi baslatici.
        
        Args:
            params: Algoritma parametreleri.
        """
        self.params = params or {}
        self.fitness_score = float('-inf')

    @abstractmethod
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Algoritmayi baslangic cozumuyle baslatir.
        
        Args:
            data: Algoritma giris verileri.
        """
        pass

    @abstractmethod
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Algoritmayi calistirir ve en iyi cozumu dondurur.
        
        Args:
            data: Algoritma giris verileri.
            
        Returns:
            Dict[str, Any]: Algoritma sonucu.
        """
        pass
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Cozumun kalitesini degerlendirir.
        
        Default implementation - algoritmaların override etmesi opsiyonel.

        Args:
            solution: Degerlendirilecek cozum.

        Returns:
            float: Cozum kalitesi skoru.
        """
        # Default: 0 döndür (algoritma kendi hesaplamasını yapabilir)
        return 0.0

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Algoritmayi calistirir ve sonucu dondurur.
        
        Args:
            data: Algoritma giris verileri.
            
        Returns:
            Dict[str, Any]: Algoritma sonucu.
        """
        # Initialize algorithm before optimization
        self.initialize(data)
        return self.optimize(data)
    
    def get_name(self) -> str:
        """
        Algoritma adini dondurur.
        
        Returns:
            str: Algoritma adi.
        """
        return self.__class__.__name__
    
    def apply_jury_refinement(
        self, 
        assignments: List[Dict[str, Any]], 
        enable_refinement: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Apply second-layer jury refinement to assignments.
        
        Args:
            assignments: Initial assignments from algorithm
            enable_refinement: Whether to apply refinement (configurable)
        
        Returns:
            Refined assignments
        """
        return assignments


class OptimizationAlgorithmWrapper:
    """
    Algoritma wrapper sınıfı - sadece validation yapar, repair yapmaz.
    Her algoritma kendi repair'ini yapmalı.
    """
    
    def __init__(self, algorithm: OptimizationAlgorithm, data: Dict[str, Any]):
        self.algorithm = algorithm
        self.data = data
        self.original_solution = []
        self.validated_solution = []
        self.result = {}
        self.repair_iterations = 0
        self.max_repair_iterations = 10

    def optimize_with_validation(self) -> Dict[str, Any]:
        """
        Algoritmayi calistirir ve validation yapar.
        Repair işlemleri algoritmanın kendisi tarafından yapılmalı.
        """
        try:
            # 1. Algoritmayi calistir
            self.result = self.algorithm.optimize(self.data)
            
            # 2. Sonucu cikar
            assignments = []
            for key in ("schedule", "assignments", "solution"):
                if isinstance(self.result.get(key), list):
                    assignments = self.result[key]
                    break
            
            self.original_solution = assignments.copy()

            # 3. Validation yap
            validation_result = validate_solution(
                assignments,
                self.data.get("projects", []),
                self.data.get("instructors", []),
                self.data.get("classrooms", []),
                self.data.get("timeslots", [])
            )

            print(f"📊 Validation sonucu: {validation_result.get('overall_accepted', False)}")

            # 4. Algoritma kendi repair'ini yapmalı
            if hasattr(self.algorithm, 'repair_solution'):
                print("🔧 Algoritma kendi repair metodunu çalıştırıyor...")
                repair_result = self.algorithm.repair_solution(
                    {"assignments": self.original_solution},
                    validation_result
                )
                self.validated_solution = repair_result.get("assignments", self.original_solution)
                print(f"✅ Algoritma repair tamamlandı: {len(self.validated_solution)} atama")
            else:
                print("⚠️  Algoritma repair metodu yok, orijinal çözüm kullanılıyor")
                self.validated_solution = self.original_solution

            # 5. Final validation
            final_validation = validate_solution(
                self.validated_solution,
                self.data.get("projects", []),
                self.data.get("instructors", []),
                self.data.get("classrooms", []),
                self.data.get("timeslots", [])
            )

            # 6. Kapsamlı raporlar oluştur
            reports = generate_reports(
                self.validated_solution,
                self.data.get("projects", []),
                self.data.get("instructors", []),
                self.data.get("classrooms", []),
                self.data.get("timeslots", [])
            )

            # 7. Sonucu guncelle
            self.result.update({
                "validation": final_validation,
                "reports": reports,
                "status": "completed" if final_validation.get("overall_accepted", False) else "completed_with_issues",
                "message": self._generate_success_message(final_validation, reports)
            })

            # 8. Sadece validation raporları oluştur (repair yok)
            self._generate_validation_reports()

        except Exception as e:
            self.result = {
                "status": "error",
                "message": f"Algoritma hatası: {str(e)}",
                "error": str(e)
            }

        print(f"🎯 Tamamlandı: {self.result['status']} - {self.result['message']}")
        return self.result

    def _generate_validation_reports(self):
        """Sadece validation raporları oluştur - repair yapma"""
        try:
            import os
            timeslots = getattr(self.algorithm, "timeslots", []) or []
            projects = getattr(self.algorithm, "projects", []) or []
            instructors = getattr(self.algorithm, "instructors", []) or []

            def late_pred(ts):
                try:
                    start = ts.get("start_time", "09:00")
                    parts = str(start).split(":")
                    h = int(parts[0])
                    m = int(parts[1]) if len(parts) > 1 else 0
                    return h > 16 or (h == 16 and m >= 30)
                except Exception:
                    return False

            expected_ids = [p.get("id") for p in projects]

            # Sadece detection ve raporlama
            from app.algorithms.validator import detect_duplicates, detect_coverage, detect_gaps, detect_late_slots, write_json, export_schedule_to_excel, write_validator_summary
            final_dup = detect_duplicates(self.validated_solution)
            final_cov = detect_coverage(self.validated_solution, expected_ids)
            final_gaps = detect_gaps(self.validated_solution, timeslots)
            final_late = detect_late_slots(self.validated_solution, timeslots, late_pred)

            self.result["duplicate_report"] = final_dup
            self.result["coverage_report"] = final_cov
            self.result["gap_report"] = final_gaps
            self.result["late_slots_report"] = final_late

            # Load balance raporu
            from collections import defaultdict
            instr_load = defaultdict(int)
            for a in self.validated_solution:
                for ins in a.get("instructors", []):
                    instr_load[ins] += 1
            self.result["load_balance_report"] = {"per_instructor": dict(instr_load)}

            # Raporları kaydet - Windows path uyumluluğu için
            try:
                reports_dir = os.path.normpath("reports")
                os.makedirs(reports_dir, exist_ok=True)
                write_json(os.path.join(reports_dir, f"duplicate_report_{self.algorithm.get_name()}.json"), final_dup)
                write_json(os.path.join(reports_dir, f"coverage_report_{self.algorithm.get_name()}.json"), final_cov)
                write_json(os.path.join(reports_dir, f"gap_report_{self.algorithm.get_name()}.json"), final_gaps)
                write_json(os.path.join(reports_dir, f"late_slots_report_{self.algorithm.get_name()}.json"), final_late)
                write_json(os.path.join(reports_dir, f"load_balance_report_{self.algorithm.get_name()}.json"), {"per_instructor": dict(instr_load)})
            except OSError as e:
                # Log but don't crash - raporlar opsiyonel
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to write report files: {e}")

            # Excel export
            try:
                reports_dir = os.path.normpath("reports")
                out_path = os.path.join(reports_dir, f"final_plan_{self.algorithm.get_name()}.xlsx")
                written = export_schedule_to_excel(self.validated_solution, getattr(self.algorithm, 'projects', []), getattr(self.algorithm, 'instructors', []), getattr(self.algorithm, 'classrooms', []), getattr(self.algorithm, 'timeslots', []), out_path)
                self.result['final_plan_path'] = written
            except Exception:
                pass

            # Write validator summary
            try:
                reports_dir = os.path.normpath("reports")
                summary_path = os.path.join(reports_dir, f"validator_summary_{self.algorithm.get_name()}.txt")
                write_validator_summary(summary_path, self.result)
                self.result['validator_summary_path'] = summary_path
            except Exception:
                pass
        except Exception:
            pass

    def _generate_success_message(self, validation: Dict[str, Any], reports: Dict[str, Any]) -> str:
        """Başarı mesajı oluştur."""
        if validation.get("overall_accepted", False):
            return "Tüm kriterler sağlandı ✅"
        else:
            issues = []
            if validation.get("duplicates", 0) > 0:
                issues.append(f"Duplicate: {validation.get('duplicates', 0)}")
            if validation.get("gaps", 0) > 0:
                issues.append(f"Gap: {validation.get('gaps', 0)}")
            if validation.get("coverage", 0) < 100:
                issues.append(f"Coverage: {validation.get('coverage', 0)}%")
            
            if issues:
                return f"Kısmi başarı: {', '.join(issues)} ⚠️"
            else:
                return "Bilinmeyen durum ❓"
