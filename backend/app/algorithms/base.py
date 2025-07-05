from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAlgorithm(ABC):
    """Bütün optimizasyon algoritmaları için temel sınıf."""
    
    def __init__(self, projects=None, instructors=None, parameters=None):
        """
        Args:
            projects: Projelerin bilgileri
            instructors: Öğretim elemanlarının bilgileri
            parameters: Algoritma parametreleri
        """
        self.projects = projects or {}
        self.instructors = instructors or {}
        self.parameters = parameters or {}
        self.result = None
        
    @abstractmethod
    def optimize(self) -> Dict[str, Any]:
        """
        Optimizasyon algoritmasını çalıştır.
        
        Returns:
            Dict[str, Any]: Optimizasyon sonuçları
        """
        pass
    
    def validate_parameters(self) -> bool:
        """
        Algoritma parametrelerini doğrula.
        
        Returns:
            bool: Parametreler geçerli mi?
        """
        # Alt sınıflar için varsayılan davranış
        return True
        
    def run(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Algoritmayı verilen parametrelerle çalıştır.
        
        Args:
            params: Özel parametreler
            
        Returns:
            Dict[str, Any]: Algoritma çalışma sonuçları
        """
        if params:
            self.parameters.update(params)
        
        if not self.validate_parameters():
            return {"error": "Invalid parameters", "status": "failed"}
            
        try:
            result = self.optimize()
            self.result = result
            return {"result": result, "status": "completed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
            
    def get_result(self) -> Dict[str, Any]:
        """
        Son algoritma sonucunu döndür.
        
        Returns:
            Dict[str, Any]: Algoritma sonuçları
        """
        return self.result 