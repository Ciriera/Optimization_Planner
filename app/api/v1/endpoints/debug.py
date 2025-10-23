from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, time, timedelta
import random

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.crud.instructor import crud_instructor
from app.crud.classroom import crud_classroom
from app.crud.timeslot import crud_timeslot
from app.crud.project import crud_project

router = APIRouter()


@router.post("/generate-fake-data")
async def generate_fake_data(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Sahte veri üretir (test için).
    """
    # Sadece geliştirme ortamında çalışır
    if not settings.DEBUG:
        raise HTTPException(
            status_code=400,
            detail="Bu endpoint sadece geliştirme ortamında kullanılabilir."
        )
    
    # Arka planda veri üretme
    background_tasks.add_task(
        _generate_fake_data_task,
        db=db
    )
    
    return {
        "status": "success",
        "data": None,
        "message": "Sahte veri üretimi başlatıldı. Bu işlem arka planda devam edecek."
    }


@router.post("/reset-db")
async def reset_db(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Veritabanını sıfırlar.
    """
    # Sadece geliştirme ortamında çalışır
    if not settings.DEBUG:
        raise HTTPException(
            status_code=400,
            detail="Bu endpoint sadece geliştirme ortamında kullanılabilir."
        )
    
    # Veritabanını sıfırla
    await _reset_db(db)
    
    return {
        "status": "success",
        "data": None,
        "message": "Veritabanı başarıyla sıfırlandı."
    }


async def _generate_fake_data_task(db: AsyncSession) -> None:
    """
    Sahte veri üretme görevi.
    """
    # Öğretim üyeleri
    hocalar = [
        {"name": "Prof. Dr. Ahmet Yılmaz", "role": "hoca"},
        {"name": "Prof. Dr. Ayşe Kaya", "role": "hoca"},
        {"name": "Doç. Dr. Mehmet Demir", "role": "hoca"},
        {"name": "Doç. Dr. Zeynep Çelik", "role": "hoca"},
        {"name": "Dr. Öğr. Üyesi Ali Can", "role": "hoca"},
        {"name": "Dr. Öğr. Üyesi Elif Yıldız", "role": "hoca"},
    ]
    
    # Araştırma görevlileri
    aras_gorler = [
        {"name": "Arş. Gör. Mustafa Şahin", "role": "aras_gor"},
        {"name": "Arş. Gör. Selin Öztürk", "role": "aras_gor"},
        {"name": "Arş. Gör. Emre Kara", "role": "aras_gor"},
        {"name": "Arş. Gör. Deniz Aydın", "role": "aras_gor"},
    ]
    
    # Öğretim elemanlarını ekle
    instructors = []
    for hoca in hocalar:
        instructor = await crud_instructor.create(
            db,
            obj_in=schemas.InstructorCreate(
                name=hoca["name"],
                role=hoca["role"],
                bitirme_count=random.randint(2, 5),
                ara_count=random.randint(3, 8)
            )
        )
        instructors.append(instructor)
    
    for aras_gor in aras_gorler:
        instructor = await crud_instructor.create(
            db,
            obj_in=schemas.InstructorCreate(
                name=aras_gor["name"],
                role=aras_gor["role"],
                bitirme_count=0,
                ara_count=random.randint(5, 10)
            )
        )
        instructors.append(instructor)
    
    # Sınıflar
    classroom_names = ["D101", "D102", "D103", "D104", "D105", "D106", "D107", "D108"]
    classrooms = []
    for name in classroom_names:
        classroom = await crud_classroom.create(
            db,
            obj_in=schemas.ClassroomCreate(
                name=name,
                capacity=30,
                location=f"D Blok, 1. Kat, {name} Nolu Sınıf"
            )
        )
        classrooms.append(classroom)
    
    # Zaman dilimleri
    morning_times = [
        (time(9, 0), time(9, 30), "morning"),
        (time(9, 30), time(10, 0), "morning"),
        (time(10, 0), time(10, 30), "morning"),
        (time(10, 30), time(11, 0), "morning"),
        (time(11, 0), time(11, 30), "morning"),
        (time(11, 30), time(12, 0), "morning"),
    ]
    
    afternoon_times = [
        (time(13, 0), time(13, 30), "afternoon"),
        (time(13, 30), time(14, 0), "afternoon"),
        (time(14, 0), time(14, 30), "afternoon"),
        (time(14, 30), time(15, 0), "afternoon"),
        (time(15, 0), time(15, 30), "afternoon"),
        (time(15, 30), time(16, 0), "afternoon"),
        (time(16, 0), time(16, 30), "afternoon"),
        (time(16, 30), time(17, 0), "afternoon"),
    ]
    
    timeslots = []
    for start, end, period in morning_times + afternoon_times:
        timeslot = await crud_timeslot.create(
            db,
            obj_in=schemas.TimeSlotCreate(
                start_time=start,
                end_time=end,
                period=period
            )
        )
        timeslots.append(timeslot)
    
    # Projeler
    bitirme_projeleri = [
        "Yapay Zeka Destekli Trafik Yönetim Sistemi",
        "Blok Zincir Tabanlı Tedarik Zinciri Yönetimi",
        "Nesnelerin İnterneti ile Akıllı Ev Otomasyonu",
        "Büyük Veri Analizi ile Müşteri Davranış Tahmini",
        "Derin Öğrenme ile Tıbbi Görüntü Analizi",
        "Doğal Dil İşleme ile Duygu Analizi Sistemi",
        "Robotik Süreç Otomasyonu ile İş Akışı Optimizasyonu",
        "Artırılmış Gerçeklik Tabanlı Eğitim Platformu",
        "Siber Güvenlik Tehdit Tespit Sistemi",
        "Bulut Tabanlı Mikroservis Mimarisi",
    ]
    
    ara_projeleri = [
        "Web Tabanlı Öğrenci Bilgi Sistemi",
        "Mobil Uygulama ile Fitness Takibi",
        "E-Ticaret Platformu Geliştirme",
        "Sosyal Medya Analiz Aracı",
        "Kütüphane Yönetim Sistemi",
        "Otel Rezervasyon Sistemi",
        "Restoran Sipariş Takip Uygulaması",
        "Personel Yönetim Yazılımı",
        "Envanter Takip Sistemi",
        "Araç Kiralama Platformu",
        "Online Sınav Sistemi",
        "Etkinlik Yönetim Uygulaması",
        "Hastane Randevu Sistemi",
        "Fatura Yönetim Yazılımı",
        "Müşteri İlişkileri Yönetimi (CRM)",
    ]
    
    # Bitirme projeleri
    projects = []
    for title in bitirme_projeleri:
        # Sorumlu hoca seç
        responsible = random.choice([i for i in instructors if i.role == "hoca"])
        
        # Yardımcı hoca ve araş. gör. seç
        available_instructors = [i for i in instructors if i != responsible]
        assistant_hoca = random.choice([i for i in available_instructors if i.role == "hoca"])
        available_instructors = [i for i in available_instructors if i != assistant_hoca]
        assistant_aragor = random.choice([i for i in available_instructors if i.role == "aras_gor"])
        
        project = await crud_project.create(
            db,
            obj_in=schemas.ProjectCreate(
                title=title,
                type="FINAL",
                is_makeup=False,
                status="ACTIVE"
            )
        )
        
        # İlişkileri ayarla
        project.responsible_instructor_id = responsible.id
        project.assistant_instructors = [assistant_hoca, assistant_aragor]
        db.add(project)
        projects.append(project)
    
    # Ara projeleri
    for title in ara_projeleri:
        # Sorumlu hoca seç
        responsible = random.choice([i for i in instructors if i.role == "hoca"])
        
        # Yardımcıları seç (hoca veya araş. gör. olabilir)
        available_instructors = [i for i in instructors if i != responsible]
        assistant1 = random.choice(available_instructors)
        available_instructors = [i for i in available_instructors if i != assistant1]
        assistant2 = random.choice(available_instructors)
        
        project = await crud_project.create(
            db,
            obj_in=schemas.ProjectCreate(
                title=title,
                type="INTERIM",
                is_makeup=False,
                status="ACTIVE"
            )
        )
        
        # İlişkileri ayarla
        project.responsible_instructor_id = responsible.id
        project.assistant_instructors = [assistant1, assistant2]
        db.add(project)
        projects.append(project)
    
    await db.commit()
    
    # Planlamalar
    from sqlalchemy import select
    from app.models.project import Project
    from app.models.instructor import Instructor
    
    # Her öğretim elemanı için proje sayılarını güncelle
    for instructor in instructors:
        # Sorumlu olduğu projeler
        result = await db.execute(
            select(Project).filter(Project.responsible_instructor_id == instructor.id)
        )
        responsible_projects = result.scalars().all()
        
        # Yardımcı olduğu projeler
        result = await db.execute(
            select(Project)
            .join(Project.assistant_instructors)
            .filter(Instructor.id == instructor.id)
        )
        assistant_projects = result.scalars().all()
        
        # Proje sayılarını hesapla
        bitirme_count = len([p for p in responsible_projects + assistant_projects if p.type == "FINAL"])
        ara_count = len([p for p in responsible_projects + assistant_projects if p.type == "INTERIM"])
        
        # Güncelle
        await crud_instructor.update(
            db,
            db_obj=instructor,
            obj_in=schemas.InstructorUpdate(
                bitirme_count=bitirme_count,
                ara_count=ara_count
            )
        )
    
    await db.commit()


async def _reset_db(db: AsyncSession) -> None:
    """
    Veritabanını sıfırlar.
    """
    # Planlamaları sil
    from sqlalchemy import delete
    from app.models.schedule import Schedule
    from app.models.project import Project
    from app.models.timeslot import TimeSlot
    from app.models.classroom import Classroom
    from app.models.instructor import Instructor
    from app.models.algorithm import AlgorithmRun
    
    await db.execute(delete(Schedule))
    
    # Schedule-Instructor ilişkilerini sil
    await db.execute("DELETE FROM schedule_instructor")
    
    # Project-Instructor ilişkilerini sil
    await db.execute("DELETE FROM project_instructor")
    
    # Projeleri sil
    await db.execute(delete(Project))
    
    # Zaman dilimlerini sil
    await db.execute(delete(TimeSlot))
    
    # Sınıfları sil
    await db.execute(delete(Classroom))
    
    # Öğretim elemanlarını sil
    await db.execute(delete(Instructor))
    
    # Algoritma çalıştırmalarını sil
    await db.execute(delete(AlgorithmRun))
    
    await db.commit() 