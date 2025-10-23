from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.algorithm import (
    AlgorithmCreate,
    AlgorithmUpdate,
    AlgorithmResponse,
    AlgorithmListResponse,
    AlgorithmComparisonRequest
)
from app.services.algorithm import AlgorithmService

router = APIRouter()

@router.get("/available", response_model=List[Dict[str, Any]])
def get_available_algorithms(
    db: Session = Depends(get_db)
):
    """Kullanılabilir algoritmaları listele"""
    service = AlgorithmService(db)
    return service.get_available_algorithms()

@router.get("/list", response_model=List[str])
def list_algorithms(
    db: Session = Depends(get_db)
):
    """Algoritma ID'lerini listele (frontend uyumluluğu için)"""
    service = AlgorithmService(db)
    algorithms = service.get_available_algorithms()
    return [alg["id"] for alg in algorithms]

@router.post("/recommend", response_model=Dict[str, Any])
def recommend_algorithm(
    projects: Dict[int, Dict],
    instructors: Dict[int, Dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Problem özelliklerine göre en uygun algoritmayı öner"""
    service = AlgorithmService(db)
    return service.recommend_algorithm(projects, instructors)

@router.post("/run", response_model=AlgorithmResponse)
def create_algorithm_run(
    data: AlgorithmCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Yeni bir algoritma çalıştırma işlemi başlat"""
    service = AlgorithmService(db)
    try:
        return service.create_algorithm_run(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/run/{algorithm_id}", response_model=AlgorithmResponse)
def get_algorithm_run(
    algorithm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Algoritma çalıştırma detaylarını getir"""
    service = AlgorithmService(db)
    algorithm = service.get_algorithm_by_id(algorithm_id)
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algoritma çalıştırma kaydı bulunamadı")
    return algorithm

@router.put("/run/{algorithm_id}", response_model=AlgorithmResponse)
def update_algorithm_run(
    algorithm_id: int,
    data: AlgorithmUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Algoritma çalıştırma kaydını güncelle"""
    service = AlgorithmService(db)
    algorithm = service.update_algorithm_run(algorithm_id, data)
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algoritma çalıştırma kaydı bulunamadı")
    return algorithm

@router.delete("/run/{algorithm_id}")
def delete_algorithm_run(
    algorithm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Algoritma çalıştırma kaydını sil"""
    service = AlgorithmService(db)
    if not service.delete_algorithm_run(algorithm_id):
        raise HTTPException(status_code=404, detail="Algoritma çalıştırma kaydı bulunamadı")
    return {"status": "success"}

@router.get("/run/{algorithm_id}/results", response_model=Dict[str, Any])
def get_algorithm_results(
    algorithm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Algoritma sonuçlarını getir"""
    service = AlgorithmService(db)
    results = service.get_algorithm_results(algorithm_id)
    if not results:
        raise HTTPException(status_code=404, detail="Algoritma sonuçları bulunamadı")
    return results

@router.post("/compare", response_model=Dict[str, Any])
def compare_algorithms(
    data: AlgorithmComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Seçilen algoritmaları karşılaştır"""
    service = AlgorithmService(db)
    try:
        return service.compare_algorithms(
            projects=data.projects,
            instructors=data.instructors,
            algorithms=data.algorithms
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 