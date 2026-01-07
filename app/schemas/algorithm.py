from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from app.models.algorithm import AlgorithmType
from app.schemas.base import BaseSchema

class AlgorithmRunBase(BaseModel):
    algorithm_type: str
    parameters: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    
    @field_validator('algorithm_type', mode='before')
    @classmethod
    def convert_enum_to_value(cls, v):
        """Convert AlgorithmType enum to its string value (lowercase)"""
        if isinstance(v, AlgorithmType):
            return v.value
        # Ensure string values are lowercase (enum values are lowercase)
        if isinstance(v, str):
            return v.lower()
        return v

class AlgorithmRunCreate(AlgorithmRunBase):
    pass

class AlgorithmRunResponse(BaseModel):
    id: int
    algorithm_type: AlgorithmType
    status: str
    task_id: str
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    gap_fix_result: Optional[Dict[str, Any]] = None
    schedule: Optional[List[Dict[str, Any]]] = None
    assignments: Optional[List[Dict[str, Any]]] = None
    solution: Optional[List[Dict[str, Any]]] = None

class AlgorithmRunUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    completed_at: Optional[datetime] = None

class AlgorithmRun(AlgorithmRunBase):
    id: int
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlgorithmRunWithResults(AlgorithmRun):
    """AlgorithmRun with detailed results and additional information."""
    detailed_metrics: Optional[Dict[str, Any]] = None
    visualization_data: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class AlgorithmRecommendation(BaseModel):
    recommended_algorithm: AlgorithmType
    reason: str
    estimated_score: float
    estimated_execution_time: float

class AlgorithmParameters(BaseSchema):
    # Genetic Algorithm parameters
    population_size: Optional[int] = Field(default=100, ge=10, le=1000)
    generations: Optional[int] = Field(default=50, ge=10, le=500)
    mutation_rate: Optional[float] = Field(default=0.1, ge=0.0, le=1.0)
    elite_size: Optional[int] = Field(default=10, ge=1, le=100)
    
    # Simulated Annealing parameters
    initial_temperature: Optional[float] = Field(default=1000.0, ge=0.0)
    cooling_rate: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    iterations_per_temp: Optional[int] = Field(default=100, ge=1)
    min_temperature: Optional[float] = Field(default=1.0, ge=0.0)

class OptimizationRequest(BaseSchema):
    algorithm_type: str = Field(..., description="Type of optimization algorithm to use")
    parameters: Optional[AlgorithmParameters] = None

class OptimizationResponse(BaseSchema):
    task_id: str
    status: str = "pending"

class OptimizationResult(BaseSchema):
    solution: Dict[str, Any]
    fitness_score: float
    execution_time: float
    iterations: int 