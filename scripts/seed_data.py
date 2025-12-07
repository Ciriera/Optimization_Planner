#!/usr/bin/env python3
"""
Seed data script for Optimization Planner
Creates sample data for development and testing
"""

import asyncio
import sys
import os
from datetime import datetime, time, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import async_session
from sqlalchemy import text
from app.models.user import User, UserRole
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.instructor import Instructor, InstructorType
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.core.security import get_password_hash


async def seed_users():
    """Seed user data"""
    print("🌱 Seeding users...")
    
    users_data = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "full_name": "System Administrator",
            "role": UserRole.ADMIN,
            "hashed_password": "admin123",  # Plain text for development
            "is_active": True,
            "is_superuser": True
        },
        {
            "email": "demo@demo.com",
            "username": "demo",
            "full_name": "Demo User",
            "role": UserRole.ADMIN,
            "hashed_password": "demo123",  # Plain text for development
            "is_active": True,
            "is_superuser": True
        },
        {
            "email": "instructor1@university.edu",
            "username": "instructor1",
            "full_name": "Dr. Ahmet Yılmaz",
            "role": UserRole.INSTRUCTOR,
            "hashed_password": "instructor123",
            "is_active": True,
            "is_superuser": False
        },
        {
            "email": "instructor2@university.edu",
            "username": "instructor2",
            "full_name": "Dr. Fatma Demir",
            "role": UserRole.INSTRUCTOR,
            "hashed_password": "instructor123",
            "is_active": True,
            "is_superuser": False
        },
        {
            "email": "instructor3@university.edu",
            "username": "instructor3",
            "full_name": "Dr. Mehmet Kaya",
            "role": UserRole.INSTRUCTOR,
            "hashed_password": "instructor123",
            "is_active": True,
            "is_superuser": False
        }
    ]
    
    async with async_session() as db:
        for user_data in users_data:
            # Check if user already exists
            existing_user = await db.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": user_data["email"]}
            )
            if existing_user.fetchone():
                print(f"   User {user_data['email']} already exists")
                continue
            
            user = User(**user_data)
            db.add(user)
            await db.commit()
            print(f"   ✅ Created user: {user_data['full_name']} ({user_data['email']})")


async def seed_instructors():
    """Seed instructor data"""
    print("🌱 Seeding instructors...")
    
    instructors_data = [
        {
            "name": "Dr. Ahmet Yılmaz",
            "type": InstructorType.PROFESSOR,
            "department": "Computer Science",
            "bitirme_count": 0,
            "ara_count": 0,
            "total_load": 0,
            "user_id": 3
        },
        {
            "name": "Dr. Fatma Demir",
            "type": InstructorType.ASSOCIATE_PROFESSOR,
            "department": "Computer Engineering",
            "bitirme_count": 0,
            "ara_count": 0,
            "total_load": 0,
            "user_id": 4
        },
        {
            "name": "Dr. Mehmet Kaya",
            "type": InstructorType.ASSISTANT_PROFESSOR,
            "department": "Software Engineering",
            "bitirme_count": 0,
            "ara_count": 0,
            "total_load": 0,
            "user_id": 5
        },
        {
            "name": "Test Instructor",
            "type": InstructorType.ASSISTANT,
            "department": "Computer Science",
            "bitirme_count": 0,
            "ara_count": 0,
            "total_load": 0,
            "user_id": 2
        }
    ]
    
    async with async_session() as db:
        for instructor_data in instructors_data:
            # Check if instructor already exists
            existing_instructor = await db.execute(
                "SELECT id FROM instructors WHERE name = ?", (instructor_data["name"],)
            )
            if existing_instructor.fetchone():
                print(f"   Instructor {instructor_data['name']} already exists")
                continue
            
            instructor = Instructor(**instructor_data)
            db.add(instructor)
            await db.commit()
            print(f"   ✅ Created instructor: {instructor_data['name']}")


async def seed_classrooms():
    """Seed classroom data"""
    print("🌱 Seeding classrooms...")
    
    classrooms_data = [
        {"name": "A101", "capacity": 30, "is_active": True, "location": "Building A"},
        {"name": "A102", "capacity": 25, "is_active": True, "location": "Building A"},
        {"name": "A103", "capacity": 40, "is_active": True, "location": "Building A"},
        {"name": "B201", "capacity": 35, "is_active": True, "location": "Building B"},
        {"name": "B202", "capacity": 28, "is_active": True, "location": "Building B"},
        {"name": "C301", "capacity": 20, "is_active": True, "location": "Building C"},
        {"name": "D106", "capacity": 25, "is_active": True, "location": "Building D"},
        {"name": "D107", "capacity": 30, "is_active": True, "location": "Building D"},
        {"name": "D108", "capacity": 35, "is_active": True, "location": "Building D"},
        {"name": "D109", "capacity": 28, "is_active": True, "location": "Building D"},
        {"name": "D110", "capacity": 32, "is_active": True, "location": "Building D"},
        {"name": "D111", "capacity": 30, "is_active": True, "location": "Building D"},
        {"name": "D223", "capacity": 40, "is_active": True, "location": "Building D"}
    ]
    
    async with async_session() as db:
        for classroom_data in classrooms_data:
            # Check if classroom already exists
            existing_classroom = await db.execute(
                "SELECT id FROM classrooms WHERE name = ?", (classroom_data["name"],)
            )
            if existing_classroom.fetchone():
                print(f"   Classroom {classroom_data['name']} already exists")
                continue
            
            classroom = Classroom(**classroom_data)
            db.add(classroom)
            await db.commit()
            print(f"   ✅ Created classroom: {classroom_data['name']}")


async def seed_projects():
    """Seed project data"""
    print("🌱 Seeding projects...")
    
    projects_data = [
        {
            "title": "Machine Learning ile Akıllı Ders Programı Optimizasyonu",
            "description": "Yapay zeka teknikleri kullanarak ders programı optimizasyonu",
            "project_type": ProjectType.FINAL,
            "student_name": "Ali Veli",
            "student_number": "12345678",
            "status": ProjectStatus.ACTIVE,
            "student_capacity": 1,
            "responsible_id": 1,
            "advisor_id": 1,
            "co_advisor_id": 2,
            "is_makeup": False,
            "is_active": True
        },
        {
            "title": "Web Tabanlı Proje Yönetim Sistemi",
            "description": "Modern web teknolojileri ile proje yönetim sistemi",
            "project_type": ProjectType.INTERIM,
            "student_name": "Ayşe Yılmaz",
            "student_number": "87654321",
            "status": ProjectStatus.ACTIVE,
            "student_capacity": 1,
            "responsible_id": 2,
            "advisor_id": 2,
            "co_advisor_id": 3,
            "is_makeup": False,
            "is_active": True
        },
        {
            "title": "Mobil Uygulama Geliştirme",
            "description": "Cross-platform mobil uygulama geliştirme",
            "project_type": ProjectType.FINAL,
            "student_name": "Mehmet Kaya",
            "student_number": "11223344",
            "status": ProjectStatus.ACTIVE,
            "student_capacity": 1,
            "responsible_id": 3,
            "advisor_id": 3,
            "co_advisor_id": 1,
            "is_makeup": False,
            "is_active": True
        },
        {
            "title": "Veritabanı Optimizasyonu",
            "description": "Büyük veri setleri için veritabanı optimizasyonu",
            "project_type": ProjectType.INTERIM,
            "student_name": "Fatma Demir",
            "student_number": "55667788",
            "status": ProjectStatus.ACTIVE,
            "student_capacity": 1,
            "responsible_id": 1,
            "advisor_id": 1,
            "co_advisor_id": 2,
            "is_makeup": False,
            "is_active": True
        },
        {
            "title": "Güvenlik Analizi ve Penetrasyon Testi",
            "description": "Web uygulamaları için güvenlik analizi",
            "project_type": ProjectType.FINAL,
            "student_name": "Zeynep Özkan",
            "student_number": "99887766",
            "status": ProjectStatus.ACTIVE,
            "student_capacity": 1,
            "responsible_id": 2,
            "advisor_id": 2,
            "co_advisor_id": 3,
            "is_makeup": False,
            "is_active": True
        }
    ]
    
    async with async_session() as db:
        for project_data in projects_data:
            # Check if project already exists
            existing_project = await db.execute(
                "SELECT id FROM projects WHERE title = ?", (project_data["title"],)
            )
            if existing_project.fetchone():
                print(f"   Project {project_data['title']} already exists")
                continue
            
            project = Project(**project_data)
            db.add(project)
            await db.commit()
            print(f"   ✅ Created project: {project_data['title']}")


async def seed_timeslots():
    """Seed timeslot data"""
    print("🌱 Seeding timeslots...")
    
    # Create basic timeslots for each day of the week
    days_of_week = [1, 2, 3, 4, 5]  # Monday to Friday
    start_times = [
        time(9, 0),   # 09:00
        time(10, 30), # 10:30
        time(13, 0),  # 13:00
        time(14, 30), # 14:30
        time(16, 0)   # 16:00
    ]
    end_times = [
        time(10, 30), # 10:30
        time(12, 0),  # 12:00
        time(14, 30), # 14:30
        time(16, 0),  # 16:00
        time(17, 30)  # 17:30
    ]
    
    async with async_session() as db:
        # Get classroom IDs
        classrooms_result = await db.execute("SELECT id FROM classrooms LIMIT 5")
        classroom_ids = [row[0] for row in classrooms_result.fetchall()]
        
        if not classroom_ids:
            print("   ⚠️ No classrooms found, skipping timeslots")
            return
        
        for day in days_of_week:
            for i, (start_time, end_time) in enumerate(zip(start_times, end_times)):
                for classroom_id in classroom_ids:
                    # Check if timeslot already exists
                    existing_timeslot = await db.execute(
                        "SELECT id FROM timeslots WHERE day_of_week = ? AND start_time = ? AND classroom_id = ?",
                        (day, start_time, classroom_id)
                    )
                    if existing_timeslot.fetchone():
                        continue
                    
                    timeslot = TimeSlot(
                        start_time=start_time,
                        end_time=end_time,
                        day_of_week=day,
                        classroom_id=classroom_id,
                        project_id=None,
                        instructor_id=None,
                        is_available=True
                    )
                    db.add(timeslot)
        
        await db.commit()
        print(f"   ✅ Created timeslots for {len(days_of_week)} days and {len(classroom_ids)} classrooms")


async def main():
    """Main seeding function"""
    print("🌱 Starting data seeding...")
    print("=" * 50)
    
    try:
        await seed_users()
        print()
        await seed_instructors()
        print()
        await seed_classrooms()
        print()
        await seed_projects()
        print()
        await seed_timeslots()
        print()
        
        print("=" * 50)
        print("🎉 Data seeding completed successfully!")
        print()
        print("📊 Summary:")
        print("   - Users: 5 (1 admin, 4 instructors)")
        print("   - Instructors: 4")
        print("   - Classrooms: 13")
        print("   - Projects: 5")
        print("   - Timeslots: Multiple slots per classroom per day")
        print()
        print("🔑 Default credentials:")
        print("   - Admin: admin@example.com / admin123")
        print("   - Demo: demo@example.com / demo123")
        print("   - Instructors: instructor1@university.edu / instructor123")
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
