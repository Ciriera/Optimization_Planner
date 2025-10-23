# Optimization Planner API Documentation

## Overview

The Optimization Planner API provides endpoints for managing academic project assignments, instructor scheduling, and optimization algorithms.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Projects

#### Create Project
```http
POST /projects/
Content-Type: application/json

{
  "title": "Test Project",
  "description": "Project description",
  "project_type": "ara",
  "student_name": "John Doe",
  "student_number": "12345678",
  "supervisor_id": 1,
  "keywords": ["optimization", "algorithms"]
}
```

#### Get Projects
```http
GET /projects/
```

#### Get Project by ID
```http
GET /projects/{project_id}
```

#### Update Project
```http
PUT /projects/{project_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "completed"
}
```

#### Delete Project
```http
DELETE /projects/{project_id}
```

### Instructors

#### Create Instructor
```http
POST /instructors/
Content-Type: application/json

{
  "name": "Dr. John Smith",
  "email": "john.smith@university.edu",
  "instructor_type": "instructor",
  "max_projects": 5,
  "keywords": ["optimization", "machine learning"]
}
```

#### Get Instructors
```http
GET /instructors/
```

#### Get Instructor by ID
```http
GET /instructors/{instructor_id}
```

#### Update Instructor
```http
PUT /instructors/{instructor_id}
Content-Type: application/json

{
  "max_projects": 7
}
```

### Classrooms

#### Create Classroom
```http
POST /classrooms/
Content-Type: application/json

{
  "name": "D106",
  "capacity": 30,
  "location": "Engineering Building",
  "is_active": true
}
```

#### Get Classrooms
```http
GET /classrooms/
```

#### Seed Default Classrooms
```http
POST /classrooms/seed-default
```

### Algorithms

#### Get Available Algorithms
```http
GET /algorithms/
```

#### Run Algorithm
```http
POST /algorithms/run
Content-Type: application/json

{
  "algorithm_type": "greedy",
  "parameters": {
    "max_iterations": 1000,
    "timeout": 30
  }
}
```

#### Get Algorithm Results
```http
GET /algorithms/results/{run_id}
```

### Reports

#### Generate Report
```http
POST /reports/generate
Content-Type: application/json

{
  "report_type": "schedule",
  "format": "pdf"
}
```

#### Get Report
```http
GET /reports/{report_id}
```

### Configuration

#### Get System Configuration
```http
GET /config/
```

#### Update Configuration
```http
PUT /config/
Content-Type: application/json

{
  "min_class_count": 5,
  "max_class_count": 7,
  "use_real_ortools": false
}
```

### Health Check

#### Check System Health
```http
GET /health
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Data Models

### Project
```json
{
  "id": 1,
  "title": "Test Project",
  "description": "Project description",
  "project_type": "ara",
  "status": "active",
  "student_name": "John Doe",
  "student_number": "12345678",
  "supervisor_id": 1,
  "keywords": ["optimization"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Instructor
```json
{
  "id": 1,
  "name": "Dr. John Smith",
  "email": "john.smith@university.edu",
  "instructor_type": "instructor",
  "max_projects": 5,
  "keywords": ["optimization"],
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Classroom
```json
{
  "id": 1,
  "name": "D106",
  "capacity": 30,
  "location": "Engineering Building",
  "is_active": true
}
```

## Rate Limiting

API requests are rate limited to 100 requests per minute per user.

## Pagination

List endpoints support pagination:

```http
GET /projects/?skip=0&limit=10
```

## Filtering

Many endpoints support filtering:

```http
GET /projects/?project_type=ara&status=active
```

## Sorting

List endpoints support sorting:

```http
GET /projects/?sort_by=created_at&sort_order=desc
```
