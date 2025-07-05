# University Project Assignment System - Backend

This project provides a backend system for optimally assigning university projects to faculty members and research assistants.

## Features

- FastAPI-based RESTful API
- PostgreSQL database
- Redis cache and Celery task queue
- JWT-based authentication
- Swagger/ReDoc API documentation
- Docker and Docker Compose support
- Alembic database migrations
- PDF and Excel report generation
- Audit logging
- Workload optimization algorithms

## Optimization Algorithms

- Simulated Annealing
- Genetic Algorithm (coming soon)
- Ant Colony Optimization (coming soon)
- Deep Search (coming soon)
- Simplex (coming soon)

## Setup

### Requirements

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (optional)

### Local Setup

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create an `.env` file:
```bash
cp .env.example .env
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the application:
```bash
# On Linux/macOS
./run.sh

# On Windows
run.bat
```

### Docker Setup

1. Start services with Docker Compose:
```bash
docker-compose up -d
```

2. Access the API:
```
http://localhost:8000
```

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Creating a New Migration

```bash
alembic revision --autogenerate -m "Migration description"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Lint
flake8 app tests

# Format
black app tests
isort app tests
```

## System Architecture

### Core Components

1. **API Layer**: FastAPI endpoints for user interaction
2. **Service Layer**: Business logic implementation
3. **Data Layer**: Database models and CRUD operations
4. **Task Queue**: Background processing with Celery
5. **Cache Layer**: Redis for caching and task results
6. **Algorithm Module**: Optimization algorithms for project assignments
7. **Reporting Module**: PDF and Excel report generation

### Database Schema

#### Users
- id: Integer (PK)
- email: String (unique)
- username: String (unique)
- hashed_password: String
- full_name: String
- role: String (admin, user, instructor, aras_gor)
- is_active: Boolean
- is_superuser: Boolean

#### Projects
- id: Integer (PK)
- title: String
- type: String (FINAL, INTERIM)
- status: String (active, makeup, completed)
- responsible_instructor_id: Integer (FK)
- student_capacity: Integer

#### Assignments
- id: Integer (PK)
- project_id: Integer (FK)
- faculty_id: Integer (FK)
- role: String (advisor, committee_member)
- created_at: DateTime

#### Algorithms
- id: Integer (PK)
- type: String (simulated_annealing, genetic, ant_colony)
- status: String (pending, running, completed, failed)
- parameters: JSON
- result: JSON
- error_message: String
- created_at: DateTime
- completed_at: DateTime
- created_by_id: Integer (FK)

#### AuditLogs
- id: Integer (PK)
- user_id: Integer (FK)
- action: String
- entity_type: String
- entity_id: Integer
- details: Text
- ip_address: String
- timestamp: DateTime

## License

MIT

## İletişim

- Geliştirici: [Ad Soyad]
- E-posta: [E-posta adresi] 