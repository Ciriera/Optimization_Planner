import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.algorithm import AlgorithmFactory
from app.models.project import Project
from app.models.instructor import Instructor
from app.models.user import User, UserRole
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

async def test_get_available_algorithms(client: AsyncClient, admin_token: str):
    """Kullanılabilir algoritmaları getirme testi"""
    response = await client.get(
        "/api/v1/algorithms/available",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("name" in algo for algo in data)
    assert all("description" in algo for algo in data)

async def test_recommend_algorithm(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Algoritma önerisi testi"""
    # Test verileri oluştur
    projects = []
    instructors = []

    # Öğretim elemanları oluştur
    for i in range(3):
        user = User(
            email=f"instructor{i}@example.com",
            username=f"instructor{i}",
            hashed_password=get_password_hash("test123"),
            full_name=f"Test Instructor {i}",
            role=UserRole.INSTRUCTOR,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        instructor = Instructor(
            type="professor" if i < 2 else "research_assistant",
            department="Test Department",
            user_id=user.id
        )
        db_session.add(instructor)
        await db_session.commit()
        await db_session.refresh(instructor)
        instructors.append(instructor)

    # Projeler oluştur
    for i in range(5):
        project = Project(
            title=f"Test Project {i}",
            type="final" if i % 2 == 0 else "interim",
            responsible_id=instructors[i % len(instructors)].id,
            is_active=True
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        projects.append(project)

    response = await client.post(
        "/api/v1/algorithms/recommend",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "project_count": len(projects),
            "instructor_count": len(instructors)
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "params" in data
    assert "reason" in data

async def test_create_algorithm_run(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Algoritma çalıştırma testi"""
    # Test verileri oluştur
    project = Project(
        title="Test Project",
        type="final",
        responsible_id=1,
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()

    response = await client.post(
        "/api/v1/algorithms/run",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "simulated_annealing",
            "params": {
                "initial_temperature": 100.0,
                "cooling_rate": 0.01,
                "iterations": 1000
            }
        }
    )
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert "run_id" in data

async def test_get_algorithm_results(client: AsyncClient, admin_token: str):
    """Algoritma sonuçlarını getirme testi"""
    # Önce bir algoritma çalıştır
    run_response = await client.post(
        "/api/v1/algorithms/run",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "simulated_annealing",
            "params": {
                "initial_temperature": 100.0,
                "cooling_rate": 0.01,
                "iterations": 100  # Test için düşük iterasyon
            }
        }
    )
    run_id = run_response.json()["run_id"]

    # Sonuçları kontrol et
    response = await client.get(
        f"/api/v1/algorithms/results/{run_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "results" in data

async def test_compare_algorithms(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Algoritma karşılaştırma testi"""
    # Test verileri oluştur
    projects = []
    instructors = []

    # Öğretim elemanları oluştur
    for i in range(3):
        user = User(
            email=f"instructor{i}@example.com",
            username=f"instructor{i}",
            hashed_password=get_password_hash("test123"),
            full_name=f"Test Instructor {i}",
            role=UserRole.INSTRUCTOR,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        instructor = Instructor(
            type="professor" if i < 2 else "research_assistant",
            department="Test Department",
            user_id=user.id
        )
        db_session.add(instructor)
        await db_session.commit()
        await db_session.refresh(instructor)
        instructors.append(instructor)

    # Projeler oluştur
    for i in range(5):
        project = Project(
            title=f"Test Project {i}",
            type="final" if i % 2 == 0 else "interim",
            responsible_id=instructors[i % len(instructors)].id,
            is_active=True
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        projects.append(project)

    response = await client.post(
        "/api/v1/algorithms/compare",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "algorithms": [
                {
                    "name": "simulated_annealing",
                    "params": {
                        "initial_temperature": 100.0,
                        "cooling_rate": 0.01,
                        "iterations": 100
                    }
                },
                {
                    "name": "genetic",
                    "params": {
                        "population_size": 50,
                        "generations": 100,
                        "mutation_rate": 0.1
                    }
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert all("name" in result for result in data)
    assert all("metrics" in result for result in data)

def test_genetic_algorithm():
    """Genetik algoritma testi"""
    projects = {
        1: {"type": "final"},
        2: {"type": "interim"}
    }
    instructors = {
        1: {"type": "professor"},
        2: {"type": "professor"},
        3: {"type": "research_assistant"}
    }

    algorithm = AlgorithmFactory.create_algorithm(
        name="genetic",
        projects=projects,
        instructors=instructors,
        params={
            "population_size": 50,
            "generations": 100,
            "mutation_rate": 0.1
        }
    )
    result = algorithm.run()
    assert result is not None
    assert "assignments" in result
    assert "fitness" in result

def test_simulated_annealing():
    """Simulated Annealing testi"""
    projects = {
        1: {"type": "final"},
        2: {"type": "interim"}
    }
    instructors = {
        1: {"type": "professor"},
        2: {"type": "professor"},
        3: {"type": "research_assistant"}
    }

    algorithm = AlgorithmFactory.create_algorithm(
        name="simulated_annealing",
        projects=projects,
        instructors=instructors,
        params={
            "initial_temperature": 100.0,
            "cooling_rate": 0.01,
            "iterations": 1000
        }
    )
    result = algorithm.run()
    assert result is not None
    assert "assignments" in result
    assert "energy" in result

def test_ant_colony():
    """Ant Colony Optimization testi"""
    projects = {
        1: {"type": "final"},
        2: {"type": "interim"}
    }
    instructors = {
        1: {"type": "professor"},
        2: {"type": "professor"},
        3: {"type": "research_assistant"}
    }

    algorithm = AlgorithmFactory.create_algorithm(
        name="ant_colony",
        projects=projects,
        instructors=instructors,
        params={
            "n_ants": 10,
            "n_iterations": 100,
            "decay": 0.1,
            "alpha": 1,
            "beta": 2
        }
    )
    result = algorithm.run()
    assert result is not None
    assert "assignments" in result
    assert "pheromone_levels" in result

def test_algorithm_factory():
    """Algoritma factory testi"""
    # Kullanılabilir algoritmaları kontrol et
    algorithms = AlgorithmFactory.get_available_algorithms()
    assert len(algorithms) > 0
    assert all("name" in algo for algo in algorithms)
    assert all("description" in algo for algo in algorithms)

    # Algoritma önerisini kontrol et
    projects = {i: {"type": "final"} for i in range(5)}
    instructors = {i: {"type": "professor"} for i in range(5)}

    recommendation = AlgorithmFactory.recommend_algorithm(projects, instructors)
    assert "name" in recommendation
    assert "params" in recommendation
    assert "reason" in recommendation 