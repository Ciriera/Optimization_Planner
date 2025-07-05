from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.algorithm import AlgorithmType, AlgorithmStatus

# Algoritma çalıştırma şemaları
class AlgorithmBase(BaseModel):
    algorithm: str
    params: Dict[str, Any] = {}
    status: str = "pending"

class AlgorithmCreate(AlgorithmBase):
    pass

class AlgorithmUpdate(BaseModel):
    algorithm: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    result: Optional[str] = None
    execution_time: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AlgorithmInDBBase(AlgorithmBase):
    id: int
    result: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlgorithmRun(AlgorithmInDBBase):
    pass

# Algoritma çalıştırma isteği
class AlgorithmExecuteRequest(BaseModel):
    algorithm: str
    params: Dict[str, Any] = {}

# Algoritma önerisi
class AlgorithmRecommendation(BaseModel):
    recommended: str
    reason: str
    scores: Dict[str, Dict[str, Any]] = {}

# Algoritma parametreleri için özel şemalar
class SimplexParameters(BaseModel):
    objective_function: Dict[str, float]  # Amaç fonksiyonu katsayıları
    constraints: Dict[str, Dict[str, float]]  # Kısıtlamalar ve katsayıları
    optimization_type: str = "minimize"  # minimize veya maximize

class GeneticParameters(BaseModel):
    population_size: int = 100
    generations: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    fitness_function: str = "balanced_load"

class SimulatedAnnealingParameters(BaseModel):
    initial_temperature: float = 1000.0
    cooling_rate: float = 0.95
    iterations: int = 1000
    acceptance_probability: float = 0.3

class DeepSearchParameters(BaseModel):
    max_depth: int = 10
    branching_factor: int = 5
    heuristic_function: str = "min_classroom_changes"

class AntColonyParameters(BaseModel):
    colony_size: int = 50
    iterations: int = 100
    evaporation_rate: float = 0.1
    pheromone_factor: float = 1.0
    heuristic_factor: float = 2.0 