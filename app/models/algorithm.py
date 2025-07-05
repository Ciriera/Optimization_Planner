from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Enum
from sqlalchemy.sql import func
from app.db.base_class import Base
import enum

class AlgorithmType(str, enum.Enum):
    SIMPLEX = "simplex"
    GENETIC_ALGORITHM = "genetic_algorithm"
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

class AlgorithmRun(Base):
    __tablename__ = "algorithm_runs"

    id = Column(Integer, primary_key=True, index=True)
    algorithm_type = Column(Enum(AlgorithmType), nullable=False)
    parameters = Column(JSON)  # Algoritma parametreleri
    status = Column(String, default="running")  # running, completed, failed
    result = Column(JSON)  # Sonuç detayları
    error = Column(String)  # Hata mesajı
    execution_time = Column(Float)  # ms cinsinden çalışma süresi
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Eski metrikler - geriye uyumluluk için tutulabilir
    score = Column(Float)  # Optimizasyon skoru
    classroom_change_score = Column(Float)  # Sınıf değişim minimizasyonu skoru
    load_balance_score = Column(Float)  # Yük dengesi skoru
    constraint_satisfaction_score = Column(Float)  # Kısıt sağlama skoru
    gini_coefficient = Column(Float)  # Gini katsayısı 