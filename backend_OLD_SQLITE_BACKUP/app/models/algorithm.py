from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class AlgorithmType(str, enum.Enum):
    """Algorithm type enumeration"""
    SIMPLEX = "simplex"
    GENETIC = "genetic"
    SIMULATED_ANNEALING = "simulated_annealing"
    DEEP_SEARCH = "deep_search"
    ANT_COLONY = "ant_colony"
    NSGA_II = "nsga_ii"
    GREEDY = "greedy"
    TABU_SEARCH = "tabu_search"
    PSO = "particle_swarm"
    HARMONY_SEARCH = "harmony_search"
    FIREFLY = "firefly"
    GREY_WOLF = "grey_wolf"
    CP_SAT = "cp_sat"
    HYBRID_CPSAT_TABU_NSGA = "hybrid_cpsat_tabu_nsga"
    LEXICOGRAPHIC_ADVANCED = "lexicographic_advanced"

class AlgorithmStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AlgorithmRun(Base):
    """Algoritma çalıştırma kaydı modeli"""
    __tablename__ = "algorithm_runs"

    id = Column(Integer, primary_key=True, index=True)
    algorithm = Column(String, nullable=False)
    params = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")
    result = Column(String, nullable=True)
    execution_time = Column(Float, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Model nesnesini sözlüğe dönüştür"""
        return {
            "id": self.id,
            "algorithm": self.algorithm,
            "params": self.params,
            "status": self.status,
            "result": self.result,
            "execution_time": self.execution_time,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }

class Algorithm(Base):
    """Algorithm model for optimization runs"""
    __tablename__ = "algorithms"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(AlgorithmType), nullable=False)
    parameters = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    execution_time = Column(Float, nullable=True)  # in seconds
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 