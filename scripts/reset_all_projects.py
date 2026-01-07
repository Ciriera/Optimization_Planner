#!/usr/bin/env python3
"""
Tüm projeleri silip sıfırdan yeniden oluşturma scripti
Görseldeki tabloya göre: 43 ara + 38 bitirme = 81 proje
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


# Instructor'lara göre proje sayıları (görseldeki tabloya göre)
INSTRUCTOR_PROJECTS = {
    "ACK": {"ara": 2, "bitirme": 3},
    "AÖ": {"ara": 4, "bitirme": 3},
    "AEL": {"ara": 5, "bitirme": 5},
    "BD": {"ara": 3, "bitirme": 5},
    "EU": {"ara": 2, "bitirme": 0},
    "FÇ": {"ara": 7, "bitirme": 0},
    "G1": {"ara": 1, "bitirme": 1},
    "GB": {"ara": 1, "bitirme": 4},
    "HİT": {"ara": 0, "bitirme": 2},
    "HOİ": {"ara": 1, "bitirme": 1},
    "MAG": {"ara": 2, "bitirme": 1},
    "MEK": {"ara": 3, "bitirme": 2},
    "MFA": {"ara": 1, "bitirme": 1},
    "MSA": {"ara": 1, "bitirme": 4},
    "OA": {"ara": 0, "bitirme": 1},
    "OK": {"ara": 0, "bitirme": 0},
    "SV": {"ara": 2, "bitirme": 0},
    "SY": {"ara": 0, "bitirme": 0},
    "UK": {"ara": 0, "bitirme": 0},
    "YES": {"ara": 2, "bitirme": 1},
    "ZCT": {"ara": 0, "bitirme": 0},
    "HTK": {"ara": 3, "bitirme": 3},
    "MKY": {"ara": 0, "bitirme": 1},
    "ÖMTK": {"ara": 0, "bitirme": 0},
    "ŞD": {"ara": 0, "bitirme": 0},
    "EA": {"ara": 2, "bitirme": 0},
    "MEÖ": {"ara": 1, "bitirme": 0},
}


async def delete_all_projects(db):
    """
    Tüm projeleri siler
    """
    print("=" * 60)
    print("🗑️  Tüm Projeleri Silme")
    print("=" * 60)
    
    # Önce proje sayısını kontrol et
    query = text("SELECT COUNT(*) FROM projects")
    result = await db.execute(query)
    total_count = result.scalar()
    
    print(f"\n📊 Mevcut Proje Sayısı: {total_count}")
    
    # Tüm projeleri sil
    print(f"\n🗑️  Tüm projeler siliniyor...")
    
    # Önce ilişkili tabloları temizle
    delete_assistants = text("DELETE FROM project_assistants")
    await db.execute(delete_assistants)
    print("   ✅ project_assistants temizlendi")
    
    delete_keywords = text("DELETE FROM project_keyword")
    await db.execute(delete_keywords)
    print("   ✅ project_keyword temizlendi")
    
    delete_schedules = text("DELETE FROM schedules")
    await db.execute(delete_schedules)
    print("   ✅ schedules temizlendi")
    
    # Sonra projeleri sil
    delete_projects = text("DELETE FROM projects")
    await db.execute(delete_projects)
    await db.commit()
    
    print(f"   ✅ {total_count} proje silindi")
    
    # Doğrula
    query = text("SELECT COUNT(*) FROM projects")
    result = await db.execute(query)
    remaining_count = result.scalar()
    
    if remaining_count == 0:
        print(f"\n✅ Tüm projeler başarıyla silindi!")
    else:
        print(f"\n⚠️  {remaining_count} proje hala mevcut!")


async def get_instructor_id(db, instructor_name):
    """
    Instructor ID'sini isme göre getirir
    """
    query = text("SELECT id FROM instructors WHERE name = :name")
    result = await db.execute(query, {"name": instructor_name})
    row = result.fetchone()
    return row[0] if row else None


async def create_projects_from_scratch(db):
    """
    Sıfırdan projeleri oluşturur
    """
    print("\n" + "=" * 60)
    print("📝 Projeleri Sıfırdan Oluşturma")
    print("=" * 60)
    
    created_count = {"ara": 0, "bitirme": 0}
    
    for instructor_name, counts in INSTRUCTOR_PROJECTS.items():
        instructor_id = await get_instructor_id(db, instructor_name)
        
        if not instructor_id:
            print(f"   ⚠️  Instructor '{instructor_name}' bulunamadı, atlanıyor...")
            continue
        
        # Ara projeleri oluştur
        for i in range(counts["ara"]):
            project = Project(
                title=f"Ara Proje ({instructor_name} - {i+1})",
                description=f"{instructor_name} için ara proje {i+1}",
                type=ProjectType.INTERIM,
                status=ProjectStatus.ACTIVE,
                student_capacity=1,
                responsible_instructor_id=instructor_id,
                is_makeup=False,
                is_active=True
            )
            db.add(project)
            created_count["ara"] += 1
        
        # Bitirme projelerini oluştur
        for i in range(counts["bitirme"]):
            project = Project(
                title=f"Bitirme Projesi ({instructor_name} - {i+1})",
                description=f"{instructor_name} için bitirme projesi {i+1}",
                type=ProjectType.FINAL,
                status=ProjectStatus.ACTIVE,
                student_capacity=1,
                responsible_instructor_id=instructor_id,
                is_makeup=False,
                is_active=True
            )
            db.add(project)
            created_count["bitirme"] += 1
    
    await db.commit()
    
    print(f"\n✅ Projeler oluşturuldu:")
    print(f"   - Ara Proje: {created_count['ara']}")
    print(f"   - Bitirme Projesi: {created_count['bitirme']}")
    print(f"   - Toplam: {created_count['ara'] + created_count['bitirme']}")
    
    return created_count


async def verify_projects(db):
    """
    Oluşturulan projeleri doğrular
    """
    print("\n" + "=" * 60)
    print("🔍 Projeleri Doğrulama")
    print("=" * 60)
    
    # Toplam sayıları kontrol et
    query = text("""
        SELECT 
            COUNT(*) FILTER (WHERE type::text = 'INTERIM' AND is_active = true) as ara_count,
            COUNT(*) FILTER (WHERE type::text = 'FINAL' AND is_active = true) as bitirme_count,
            COUNT(*) FILTER (WHERE is_active = true) as total_count
        FROM projects
    """)
    result = await db.execute(query)
    row = result.fetchone()
    ara_count, bitirme_count, total_count = row
    
    print(f"\n📊 Veritabanı Durumu:")
    print(f"   - Ara Proje: {ara_count}")
    print(f"   - Bitirme Projesi: {bitirme_count}")
    print(f"   - Toplam: {total_count}")
    
    print(f"\n🎯 Hedef:")
    print(f"   - Ara Proje: 43")
    print(f"   - Bitirme Projesi: 38")
    print(f"   - Toplam: 81")
    
    if ara_count == 43 and bitirme_count == 38 and total_count == 81:
        print(f"\n🎉 Proje sayıları hedef değerlere ulaştı!")
    else:
        print(f"\n⚠️  Fark var! Ara={ara_count}/43, Bitirme={bitirme_count}/38, Toplam={total_count}/81")
    
    # Instructor başına kontrol
    query = text("""
        SELECT i.name, 
               COUNT(CASE WHEN p.type::text = 'INTERIM' THEN 1 END) as ara_count,
               COUNT(CASE WHEN p.type::text = 'FINAL' THEN 1 END) as bitirme_count,
               i.ara_count as expected_ara,
               i.bitirme_count as expected_bitirme
        FROM instructors i
        LEFT JOIN projects p ON p.responsible_instructor_id = i.id AND p.is_active = true
        GROUP BY i.id, i.name, i.ara_count, i.bitirme_count
        ORDER BY i.name
    """)
    result = await db.execute(query)
    instructor_stats = result.fetchall()
    
    print(f"\n👥 Instructor İstatistikleri:")
    mismatches = []
    for stat in instructor_stats:
        name, actual_ara, actual_bitirme, expected_ara, expected_bitirme = stat
        if actual_ara != expected_ara or actual_bitirme != expected_bitirme:
            mismatches.append((name, actual_ara, expected_ara, actual_bitirme, expected_bitirme))
            print(f"   ⚠️  {name}: Ara={actual_ara}/{expected_ara}, Bitirme={actual_bitirme}/{expected_bitirme}")
        else:
            print(f"   ✅ {name}: Ara={actual_ara}/{expected_ara}, Bitirme={actual_bitirme}/{expected_bitirme}")
    
    if not mismatches:
        print(f"\n   🎉 Tüm instructor'lar beklenen sayıda proje aldı!")


async def main():
    """Ana fonksiyon"""
    async with async_session() as db:
        try:
            # Tüm projeleri sil
            await delete_all_projects(db)
            
            # Sıfırdan oluştur
            await create_projects_from_scratch(db)
            
            # Doğrula
            await verify_projects(db)
            
            print("\n" + "=" * 60)
            print("✅ İşlem başarıyla tamamlandı!")
            print("=" * 60)
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())












