#!/usr/bin/env python3
"""
Projeleri instructor'lara atama scripti
Her instructor'ın ara_count ve bitirme_count değerlerine göre projeleri atar
"""

import asyncio
import sys
import os
from sqlalchemy import text, select
from collections import defaultdict

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows için event loop policy ayarı
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.db.base import async_session
from app.models.instructor import Instructor
from app.models.project import Project, ProjectType


async def get_projects_by_type(db):
    """
    Projeleri tipine göre ayırır
    """
    query = text("""
        SELECT id, title, type::text, responsible_instructor_id 
        FROM projects 
        WHERE is_active = true
        ORDER BY id
    """)
    result = await db.execute(query)
    projects = result.fetchall()
    
    interim_projects = [p for p in projects if p[2] == 'INTERIM']
    final_projects = [p for p in projects if p[2] == 'FINAL']
    
    return interim_projects, final_projects


async def get_instructors_with_capacity(db):
    """
    Instructor'ları kapasitelerine göre getirir
    """
    query = text("""
        SELECT id, name, ara_count, bitirme_count 
        FROM instructors 
        ORDER BY name
    """)
    result = await db.execute(query)
    instructors = result.fetchall()
    
    return instructors


async def assign_projects(db):
    """
    Projeleri instructor'lara dengeli bir şekilde atar
    """
    print("=" * 60)
    print("📋 Projeleri Instructor'lara Atama")
    print("=" * 60)
    
    # Projeleri ve instructor'ları getir
    interim_projects, final_projects = await get_projects_by_type(db)
    instructors = await get_instructors_with_capacity(db)
    
    print(f"\n📊 Durum:")
    print(f"   - Ara Proje (interim): {len(interim_projects)}")
    print(f"   - Bitirme Projesi (final): {len(final_projects)}")
    print(f"   - Toplam Instructor: {len(instructors)}")
    
    # Instructor'ları dictionary'ye çevir
    instructor_dict = {inst[0]: inst for inst in instructors}
    
    # Her instructor için atama sayacı
    assignments = defaultdict(lambda: {'ara': 0, 'bitirme': 0})
    
    # Ara projeleri atama
    print(f"\n🔄 Ara projeler atanıyor...")
    interim_idx = 0
    for instructor_id, instructor_data in instructor_dict.items():
        name = instructor_data[1]
        ara_capacity = instructor_data[2]
        
        while assignments[instructor_id]['ara'] < ara_capacity and interim_idx < len(interim_projects):
            project_id = interim_projects[interim_idx][0]
            project_title = interim_projects[interim_idx][1]
            
            # Projeyi instructor'a ata
            update_query = text("""
                UPDATE projects 
                SET responsible_instructor_id = :instructor_id
                WHERE id = :project_id
            """)
            await db.execute(update_query, {
                "instructor_id": instructor_id,
                "project_id": project_id
            })
            
            assignments[instructor_id]['ara'] += 1
            interim_idx += 1
            print(f"   ✅ {name}: {project_title[:50]}...")
    
    if interim_idx < len(interim_projects):
        print(f"   ⚠️  {len(interim_projects) - interim_idx} ara proje atanmadı (kapasite yetersiz)")
    
    # Bitirme projelerini atama
    print(f"\n🔄 Bitirme projeleri atanıyor...")
    final_idx = 0
    for instructor_id, instructor_data in instructor_dict.items():
        name = instructor_data[1]
        bitirme_capacity = instructor_data[3]
        
        while assignments[instructor_id]['bitirme'] < bitirme_capacity and final_idx < len(final_projects):
            project_id = final_projects[final_idx][0]
            project_title = final_projects[final_idx][1]
            
            # Projeyi instructor'a ata
            update_query = text("""
                UPDATE projects 
                SET responsible_instructor_id = :instructor_id
                WHERE id = :project_id
            """)
            await db.execute(update_query, {
                "instructor_id": instructor_id,
                "project_id": project_id
            })
            
            assignments[instructor_id]['bitirme'] += 1
            final_idx += 1
            print(f"   ✅ {name}: {project_title[:50]}...")
    
    if final_idx < len(final_projects):
        print(f"   ⚠️  {len(final_projects) - final_idx} bitirme projesi atanmadı (kapasite yetersiz)")
    
    await db.commit()
    
    # Özet
    print(f"\n📈 Atama Özeti:")
    print(f"   - Atanan Ara Proje: {interim_idx}/{len(interim_projects)}")
    print(f"   - Atanan Bitirme Projesi: {final_idx}/{len(final_projects)}")
    
    # Her instructor için atama durumu
    print(f"\n👥 Instructor Atama Durumu:")
    for instructor_id, instructor_data in sorted(instructor_dict.items(), key=lambda x: x[1][1]):
        name = instructor_data[1]
        ara_assigned = assignments[instructor_id]['ara']
        bitirme_assigned = assignments[instructor_id]['bitirme']
        ara_capacity = instructor_data[2]
        bitirme_capacity = instructor_data[3]
        
        ara_status = "✅" if ara_assigned == ara_capacity else "⚠️"
        bitirme_status = "✅" if bitirme_assigned == bitirme_capacity else "⚠️"
        
        print(f"   {ara_status} {bitirme_status} {name}: Ara={ara_assigned}/{ara_capacity}, Bitirme={bitirme_assigned}/{bitirme_capacity}")


async def verify_assignments(db):
    """
    Atamaları doğrular
    """
    print(f"\n🔍 Atamalar doğrulanıyor...")
    
    # Atanmamış projeleri kontrol et
    query = text("""
        SELECT COUNT(*) 
        FROM projects 
        WHERE responsible_instructor_id IS NULL AND is_active = true
    """)
    result = await db.execute(query)
    unassigned_count = result.scalar()
    
    if unassigned_count > 0:
        print(f"   ⚠️  {unassigned_count} proje atanmamış!")
        
        # Atanmamış projeleri listele
        query = text("""
            SELECT id, title, type 
            FROM projects 
            WHERE responsible_instructor_id IS NULL AND is_active = true
            LIMIT 10
        """)
        result = await db.execute(query)
        unassigned = result.fetchall()
        
        print(f"   İlk 10 atanmamış proje:")
        for proj in unassigned:
            print(f"      - [{proj[2]}] {proj[1][:50]}...")
    else:
        print(f"   ✅ Tüm projeler atandı!")
    
    # Instructor başına proje sayısını kontrol et
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
    
    print(f"\n📊 Instructor İstatistikleri:")
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
            await assign_projects(db)
            await verify_assignments(db)
            
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

