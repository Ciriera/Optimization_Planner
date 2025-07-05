"""
Veritabanına örnek veriler eklemek için script.
"""
import sys
import os
import asyncio
from pathlib import Path
import datetime

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.base import async_session, engine
from app.db.base_all import Base
from app.models import User, Instructor, Project, Classroom, TimeSlot, Schedule, AlgorithmRun, AuditLog
from app.core.security import get_password_hash
from app.models.user import UserRole

async def create_tables():
    """Tüm veritabanı tablolarını oluştur"""
    try:
        print("Veritabanı tabloları oluşturuluyor...")
        async with engine.begin() as conn:
            # Önce tabloları temizle
            await conn.run_sync(Base.metadata.drop_all)
            # Tüm tabloları oluştur
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Veritabanı tabloları başarıyla oluşturuldu!")
        return True
    except Exception as e:
        print(f"❌ Veritabanı tabloları oluşturulurken hata: {e}")
        return False

async def seed_users():
    """Örnek kullanıcılar ekle"""
    try:
        print("Kullanıcılar ekleniyor...")
        async with async_session() as db:
            # Admin kullanıcısı ekle
            admin = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_superuser=True,
                is_active=True
            )
            db.add(admin)
            
            # Normal kullanıcı ekle
            user = User(
                email="user@example.com",
                hashed_password=get_password_hash("user123"),
                full_name="Normal User",
                role=UserRole.HOCA,
                is_superuser=False,
                is_active=True
            )
            db.add(user)
            
            await db.commit()
            print("✅ Kullanıcılar başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Kullanıcılar eklenirken hata: {e}")
        return False

async def seed_instructors():
    """Örnek öğretim üyeleri ekle"""
    try:
        print("Öğretim üyeleri ekleniyor...")
        async with async_session() as db:
            # Profesörler ekle
            prof1 = Instructor(
                email="prof1@example.com",
                full_name="Prof. Dr. Ahmet Yılmaz",
                type="professor",
                department="Bilgisayar Mühendisliği",
                is_active=True,
                hashed_password=get_password_hash("prof123"),
                research_interests="Yapay Zeka, Makine Öğrenmesi",
                max_project_count=5
            )
            db.add(prof1)
            
            prof2 = Instructor(
                email="prof2@example.com",
                full_name="Prof. Dr. Ayşe Kaya",
                type="professor",
                department="Bilgisayar Mühendisliği",
                is_active=True,
                hashed_password=get_password_hash("prof123"),
                research_interests="Veri Bilimi, Büyük Veri",
                max_project_count=4
            )
            db.add(prof2)
            
            # Araştırma görevlileri ekle
            ra1 = Instructor(
                email="ra1@example.com",
                full_name="Arş. Gör. Mehmet Demir",
                type="research_assistant",
                department="Bilgisayar Mühendisliği",
                is_active=True,
                hashed_password=get_password_hash("ra123"),
                research_interests="Derin Öğrenme, Görüntü İşleme",
                max_project_count=3
            )
            db.add(ra1)
            
            ra2 = Instructor(
                email="ra2@example.com",
                full_name="Arş. Gör. Zeynep Aydın",
                type="research_assistant",
                department="Bilgisayar Mühendisliği",
                is_active=True,
                hashed_password=get_password_hash("ra123"),
                research_interests="Doğal Dil İşleme, Metin Madenciliği",
                max_project_count=3
            )
            db.add(ra2)
            
            await db.commit()
            print("✅ Öğretim üyeleri başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Öğretim üyeleri eklenirken hata: {e}")
        return False

async def seed_projects():
    """Örnek projeler ekle"""
    try:
        print("Projeler ekleniyor...")
        async with async_session() as db:
            # Öğretim üyelerini getir
            result = await db.execute(text("SELECT id FROM instructors"))
            instructor_ids = [row[0] for row in result.fetchall()]
            
            if len(instructor_ids) < 2:
                print("❌ Yeterli sayıda öğretim üyesi bulunamadı!")
                return False
            
            # Bitirme projeleri ekle
            project1 = Project(
                title="Yapay Zeka Destekli Proje Atama Sistemi",
                type="bitirme",
                responsible_id=instructor_ids[0],
                advisor_id=instructor_ids[0],
                co_advisor_id=instructor_ids[1],
                is_makeup=False
            )
            db.add(project1)
            
            project2 = Project(
                title="Derin Öğrenme ile Görüntü Sınıflandırma",
                type="bitirme",
                responsible_id=instructor_ids[1],
                advisor_id=instructor_ids[1],
                co_advisor_id=instructor_ids[0],
                is_makeup=False
            )
            db.add(project2)
            
            # Ara projeler ekle
            project3 = Project(
                title="Veri Madenciliği Uygulaması",
                type="ara",
                responsible_id=instructor_ids[0],
                advisor_id=instructor_ids[0],
                is_makeup=False
            )
            db.add(project3)
            
            project4 = Project(
                title="Web Tabanlı Öğrenci Bilgi Sistemi",
                type="ara",
                responsible_id=instructor_ids[1],
                advisor_id=instructor_ids[1],
                is_makeup=False
            )
            db.add(project4)
            
            await db.commit()
            print("✅ Projeler başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Projeler eklenirken hata: {e}")
        return False

async def seed_classrooms():
    """Örnek sınıflar ekle"""
    try:
        print("Sınıflar ekleniyor...")
        async with async_session() as db:
            # Sınıflar ekle
            classroom1 = Classroom(
                name="D101",
                capacity=30,
                is_active=True
            )
            db.add(classroom1)
            
            classroom2 = Classroom(
                name="D102",
                capacity=25,
                is_active=True
            )
            db.add(classroom2)
            
            classroom3 = Classroom(
                name="D103",
                capacity=35,
                is_active=True
            )
            db.add(classroom3)
            
            classroom4 = Classroom(
                name="D104",
                capacity=20,
                is_active=True
            )
            db.add(classroom4)
            
            await db.commit()
            print("✅ Sınıflar başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Sınıflar eklenirken hata: {e}")
        return False

async def seed_timeslots():
    """Örnek zaman dilimleri ekle"""
    try:
        print("Zaman dilimleri ekleniyor...")
        async with async_session() as db:
            # Sabah zaman dilimleri
            timeslot1 = TimeSlot(
                start_time=datetime.time(9, 0),
                end_time=datetime.time(9, 30),
                is_morning=True,
                is_active=True
            )
            db.add(timeslot1)
            
            timeslot2 = TimeSlot(
                start_time=datetime.time(9, 30),
                end_time=datetime.time(10, 0),
                is_morning=True,
                is_active=True
            )
            db.add(timeslot2)
            
            timeslot3 = TimeSlot(
                start_time=datetime.time(10, 0),
                end_time=datetime.time(10, 30),
                is_morning=True,
                is_active=True
            )
            db.add(timeslot3)
            
            # Öğleden sonra zaman dilimleri
            timeslot4 = TimeSlot(
                start_time=datetime.time(13, 0),
                end_time=datetime.time(13, 30),
                is_morning=False,
                is_active=True
            )
            db.add(timeslot4)
            
            timeslot5 = TimeSlot(
                start_time=datetime.time(13, 30),
                end_time=datetime.time(14, 0),
                is_morning=False,
                is_active=True
            )
            db.add(timeslot5)
            
            timeslot6 = TimeSlot(
                start_time=datetime.time(14, 0),
                end_time=datetime.time(14, 30),
                is_morning=False,
                is_active=True
            )
            db.add(timeslot6)
            
            await db.commit()
            print("✅ Zaman dilimleri başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Zaman dilimleri eklenirken hata: {e}")
        return False

async def seed_schedules():
    """Örnek program atamaları ekle"""
    try:
        print("Program atamaları ekleniyor...")
        async with async_session() as db:
            # Proje, sınıf ve zaman dilimlerini getir
            projects_result = await db.execute(text("SELECT id FROM projects"))
            project_ids = [row[0] for row in projects_result.fetchall()]
            
            classrooms_result = await db.execute(text("SELECT id FROM classrooms"))
            classroom_ids = [row[0] for row in classrooms_result.fetchall()]
            
            timeslots_result = await db.execute(text("SELECT id FROM timeslots"))
            timeslot_ids = [row[0] for row in timeslots_result.fetchall()]
            
            if not project_ids or not classroom_ids or not timeslot_ids:
                print("❌ Gerekli veriler bulunamadı!")
                return False
            
            # Program atamaları ekle
            schedule1 = Schedule(
                project_id=project_ids[0],
                classroom_id=classroom_ids[0],
                timeslot_id=timeslot_ids[0],
                is_makeup=False
            )
            db.add(schedule1)
            
            schedule2 = Schedule(
                project_id=project_ids[1],
                classroom_id=classroom_ids[1],
                timeslot_id=timeslot_ids[1],
                is_makeup=False
            )
            db.add(schedule2)
            
            schedule3 = Schedule(
                project_id=project_ids[2],
                classroom_id=classroom_ids[2],
                timeslot_id=timeslot_ids[2],
                is_makeup=False
            )
            db.add(schedule3)
            
            schedule4 = Schedule(
                project_id=project_ids[3],
                classroom_id=classroom_ids[3],
                timeslot_id=timeslot_ids[3],
                is_makeup=False
            )
            db.add(schedule4)
            
            await db.commit()
            print("✅ Program atamaları başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Program atamaları eklenirken hata: {e}")
        return False

async def seed_algorithm_runs():
    """Örnek algoritma çalıştırmaları ekle"""
    try:
        print("Algoritma çalıştırmaları ekleniyor...")
        async with async_session() as db:
            # Algoritma çalıştırmaları ekle
            algo_run1 = AlgorithmRun(
                algorithm="genetic_algorithm",
                params={"population_size": 100, "generations": 50},
                score=0.85,
                execution_time=2.5,
                result_json={"assignments": [{"project_id": 1, "classroom_id": 1, "timeslot_id": 1}]},
                created_at=datetime.datetime.now(),
                classroom_change_score=0.9,
                load_balance_score=0.8,
                constraint_satisfaction_score=0.95,
                gini_coefficient=0.2
            )
            db.add(algo_run1)
            
            algo_run2 = AlgorithmRun(
                algorithm="simulated_annealing",
                params={"initial_temperature": 1000, "cooling_rate": 0.95},
                score=0.82,
                execution_time=1.8,
                result_json={"assignments": [{"project_id": 2, "classroom_id": 2, "timeslot_id": 2}]},
                created_at=datetime.datetime.now(),
                classroom_change_score=0.85,
                load_balance_score=0.75,
                constraint_satisfaction_score=0.9,
                gini_coefficient=0.25
            )
            db.add(algo_run2)
            
            await db.commit()
            print("✅ Algoritma çalıştırmaları başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Algoritma çalıştırmaları eklenirken hata: {e}")
        return False

async def seed_audit_logs():
    """Örnek denetim kayıtları ekle"""
    try:
        print("Denetim kayıtları ekleniyor...")
        async with async_session() as db:
            # Kullanıcıları getir
            result = await db.execute(text("SELECT id FROM users"))
            user_ids = [row[0] for row in result.fetchall()]
            
            if not user_ids:
                print("❌ Kullanıcı bulunamadı!")
                return False
            
            # Denetim kayıtları ekle
            audit_log1 = AuditLog(
                user_id=user_ids[0],
                action="create",
                resource_type="project",
                resource_id=1,
                details={"title": "Yapay Zeka Destekli Proje Atama Sistemi"},
                created_at=datetime.datetime.now()
            )
            db.add(audit_log1)
            
            audit_log2 = AuditLog(
                user_id=user_ids[0],
                action="update",
                resource_type="instructor",
                resource_id=1,
                details={"field": "max_project_count", "old_value": 4, "new_value": 5},
                created_at=datetime.datetime.now()
            )
            db.add(audit_log2)
            
            await db.commit()
            print("✅ Denetim kayıtları başarıyla eklendi!")
            return True
    except Exception as e:
        print(f"❌ Denetim kayıtları eklenirken hata: {e}")
        return False

async def main():
    print("="*50)
    print("Örnek Veri Ekleme")
    print("="*50)
    
    # Tabloları oluştur
    tables_created = await create_tables()
    
    if tables_created:
        # Örnek verileri ekle
        await seed_users()
        await seed_instructors()
        await seed_projects()
        await seed_classrooms()
        await seed_timeslots()
        await seed_schedules()
        await seed_algorithm_runs()
        await seed_audit_logs()
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())