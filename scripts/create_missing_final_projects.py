#!/usr/bin/env python3
"""
Eksik bitirme projelerini oluşturma scripti
MSA: 1, OA: 1, YES: 1 bitirme projesi eksik
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows için event loop policy ayarı
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.db.base import async_session
from app.models.project import Project, ProjectType, ProjectStatus


async def get_instructor_id(db, instructor_name):
    """
    Instructor ID'sini isme göre getirir
    """
    query = text("SELECT id FROM instructors WHERE name = :name")
    result = await db.execute(query, {"name": instructor_name})
    row = result.fetchone()
    return row[0] if row else None


async def create_missing_final_projects(db):
    """
    Eksik bitirme projelerini oluşturur
    """
    print("=" * 60)
    print("📝 Eksik Bitirme Projelerini Oluşturma")
    print("=" * 60)
    
    # Instructor ID'lerini al
    msa_id = await get_instructor_id(db, "MSA")
    oa_id = await get_instructor_id(db, "OA")
    yes_id = await get_instructor_id(db, "YES")
    
    if not msa_id or not oa_id or not yes_id:
        print("\n❌ Instructor bulunamadı!")
        return
    
    print(f"\n👥 Instructor ID'leri:")
    print(f"   - MSA: {msa_id}")
    print(f"   - OA: {oa_id}")
    print(f"   - YES: {yes_id}")
    
    # Mevcut bitirme projesi sayısını kontrol et
    query = text("""
        SELECT COUNT(*) 
        FROM projects 
        WHERE type::text = 'FINAL' AND is_active = true
    """)
    result = await db.execute(query)
    current_count = result.scalar()
    
    print(f"\n📊 Mevcut Bitirme Projesi: {current_count}")
    print(f"🎯 Hedef: 38")
    print(f"📉 Eksik: {38 - current_count}")
    
    # Her instructor için eksik projeleri oluştur
    projects_to_create = [
        {"instructor_id": msa_id, "instructor_name": "MSA", "title": "Bitirme Projesi (MSA Ek)"},
        {"instructor_id": oa_id, "instructor_name": "OA", "title": "Bitirme Projesi (OA)"},
        {"instructor_id": yes_id, "instructor_name": "YES", "title": "Bitirme Projesi (YES)"},
    ]
    
    created_count = 0
    for project_data in projects_to_create:
        # Bu instructor'ın mevcut bitirme projesi sayısını kontrol et
        query = text("""
            SELECT COUNT(*) 
            FROM projects 
            WHERE type::text = 'FINAL' 
              AND is_active = true
              AND responsible_instructor_id = :instructor_id
        """)
        result = await db.execute(query, {"instructor_id": project_data["instructor_id"]})
        instructor_project_count = result.scalar()
        
        # Instructor'ın beklenen bitirme projesi sayısını al
        query = text("SELECT bitirme_count FROM instructors WHERE id = :id")
        result = await db.execute(query, {"id": project_data["instructor_id"]})
        expected_count = result.scalar()
        
        if instructor_project_count < expected_count:
            # Proje oluştur
            project = Project(
                title=project_data["title"],
                description=f"{project_data['instructor_name']} için ek bitirme projesi",
                type=ProjectType.FINAL,
                status=ProjectStatus.ACTIVE,
                student_capacity=1,
                responsible_instructor_id=project_data["instructor_id"],
                is_makeup=False,
                is_active=True
            )
            db.add(project)
            created_count += 1
            print(f"   ✅ Oluşturuldu: {project_data['title']} ({project_data['instructor_name']})")
        else:
            print(f"   ⏭️  Atlandı: {project_data['instructor_name']} zaten yeterli projeye sahip ({instructor_project_count}/{expected_count})")
    
    await db.commit()
    
    # Yeni durumu kontrol et
    query = text("""
        SELECT COUNT(*) 
        FROM projects 
        WHERE type::text = 'FINAL' AND is_active = true
    """)
    result = await db.execute(query)
    new_count = result.scalar()
    
    print(f"\n📊 Yeni Bitirme Projesi Sayısı: {new_count}")
    print(f"📈 Oluşturulan Proje: {created_count}")
    
    if new_count == 38:
        print(f"\n🎉 Hedef değere ulaşıldı!")
    else:
        print(f"\n⚠️  Hala {38 - new_count} bitirme projesi eksik!")


async def main():
    """Ana fonksiyon"""
    async with async_session() as db:
        try:
            await create_missing_final_projects(db)
            
            print("\n" + "=" * 60)
            print("✅ İşlem tamamlandı!")
            print("=" * 60)
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())












