from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
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
    NSGA_II_ENHANCED = "nsga_ii_enhanced"
    GREEDY = "greedy"
    TABU_SEARCH = "tabu_search"
    PSO = "particle_swarm"
    HARMONY_SEARCH = "harmony_search"
    FIREFLY = "firefly"
    GREY_WOLF = "grey_wolf"
    CP_SAT = "cp_sat"
    LEXICOGRAPHIC = "lexicographic"
    HYBRID_CP_SAT_NSGA = "hybrid_cp_sat_nsga"
    # Yeni algoritmalar
    ARTIFICIAL_BEE_COLONY = "artificial_bee_colony"
    CUCKOO_SEARCH = "cuckoo_search"
    BRANCH_AND_BOUND = "branch_and_bound"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    WHALE_OPTIMIZATION = "whale_optimization"
    # Daha fazla algoritma
    BAT_ALGORITHM = "bat_algorithm"
    DRAGONFLY_ALGORITHM = "dragonfly_algorithm"
    A_STAR_SEARCH = "a_star_search"
    INTEGER_LINEAR_PROGRAMMING = "integer_linear_programming"
    GENETIC_LOCAL_SEARCH = "genetic_local_search"
    COMPREHENSIVE_OPTIMIZER = "comprehensive_optimizer"

class AlgorithmRun(Base):
    __tablename__ = "algorithm_runs"

    id = Column(Integer, primary_key=True, index=True)
    algorithm_type = Column(Enum(AlgorithmType), nullable=False)
    parameters = Column(JSON)  # Algoritma parametreleri
    data = Column(JSON)  # Algoritma giriş verisi
    status = Column(String, default="running")  # running, completed, failed
    result = Column(JSON)  # Sonuç detayları
    error = Column(String)  # Hata mesajı
    execution_time = Column(Float)  # ms cinsinden çalışma süresi
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Added user_id

    # Eski metrikler - geriye uyumluluk için tutulabilir
    score = Column(Float)  # Optimizasyon skoru
    classroom_change_score = Column(Float)  # Sınıf değişim minimizasyonu skoru
    load_balance_score = Column(Float)  # Yük dengesi skoru
    constraint_satisfaction_score = Column(Float)  # Kısıt sağlama skoru
    gini_coefficient = Column(Float)  # Gini katsayısı
    
    # İlişkiler
    user = relationship("User", back_populates="algorithm_runs") 