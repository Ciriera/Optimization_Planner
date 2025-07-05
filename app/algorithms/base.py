"""
Temel algoritma sınıfları.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.models.project import Project
from app.models.instructor import Instructor
from app.models.student import Student

class BaseAlgorithm(ABC):
    """
    Tüm algoritmaların temel sınıfı.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Temel algoritma başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        self.params = params or {}
        self.result = None
    
    @abstractmethod
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Algoritmayı çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Algoritma sonucu.
        """
        pass
    
    def get_name(self) -> str:
        """
        Algoritma adını döndürür.
        
        Returns:
            str: Algoritma adı.
        """
        return self.__class__.__name__
    
    def get_description(self) -> str:
        """
        Algoritma açıklamasını döndürür.
        
        Returns:
            str: Algoritma açıklaması.
        """
        return self.__doc__ or "Açıklama yok."
    
    def get_result(self) -> Optional[Dict[str, Any]]:
        """
        Son çalıştırma sonucunu döndürür.
        
        Returns:
            Dict[str, Any]: Algoritma sonucu.
        """
        return self.result

class OptimizationAlgorithm(BaseAlgorithm):
    """
    Optimizasyon algoritmaları için temel sınıf.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Optimizasyon algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        self.fitness_score = float('-inf')
    
    @abstractmethod
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Algoritmayı başlangıç çözümüyle başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        pass
    
    @abstractmethod
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimizasyon algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        pass
    
    @abstractmethod
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Verilen çözümün uygunluğunu değerlendirir.
        
        Args:
            solution: Değerlendirilecek çözüm.
            
        Returns:
            float: Uygunluk puanı.
        """
        pass
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimizasyon algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        self.initialize(data)
        self.result = self.optimize(data)
        return self.result
    
    def get_fitness_score(self) -> float:
        """
        En iyi çözümün uygunluk puanını döndürür.
        
        Returns:
            float: Uygunluk puanı.
        """
        return self.fitness_score

    def get_solution(self) -> Dict[str, Any]:
        """Return the best solution found"""
        if not self.result:
            raise ValueError("No solution found. Run execute() first.")
        return self.result

    def validate_solution(self, solution: Dict[str, Any]) -> bool:
        """Validate if the solution meets all constraints"""
        try:
            # Check project capacity constraints
            for project_id, assigned in solution.get("project_assignments", {}).items():
                project = next(p for p in self.projects if p.id == int(project_id))
                if len(assigned.get("students", [])) > project.student_capacity:
                    return False

            # Check instructor load constraints
            instructor_loads = {}
            for project_id, assigned in solution.get("project_assignments", {}).items():
                advisor_id = assigned.get("advisor_id")
                if advisor_id:
                    instructor_loads[advisor_id] = instructor_loads.get(advisor_id, 0) + 1
                    instructor = next(i for i in self.instructors if i.id == advisor_id)
                    if instructor_loads[advisor_id] > instructor.max_project_count:
                        return False

            return True
        except Exception:
            return False 