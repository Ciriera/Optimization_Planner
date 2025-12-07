#!/usr/bin/env python3
"""
Instructor verilerini güncelleme scripti
Mevcut instructor'ları siler ve yeni verileri ekler
"""

import asyncio
import sys
import os
from sqlalchemy import text, delete

# Windows için event loop policy ayarı
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import async_session
from app.models.instructor import Instructor, InstructorType


# Yeni instructor verileri
INSTRUCTORS_DATA = [
    {"name": "ACK", "ara_count": 2, "bitirme_count": 3},
    {"name": "AÖ", "ara_count": 4, "bitirme_count": 3},
    {"name": "AEL", "ara_count": 5, "bitirme_count": 5},
    {"name": "BD", "ara_count": 3, "bitirme_count": 5},
    {"name": "EU", "ara_count": 2, "bitirme_count": 0},
    {"name": "FÇ", "ara_count": 7, "bitirme_count": 0},
    {"name": "G1", "ara_count": 1, "bitirme_count": 1},
    {"name": "GB", "ara_count": 1, "bitirme_count": 4},
    {"name": "HİT", "ara_count": 0, "bitirme_count": 2},
    {"name": "HOİ", "ara_count": 1, "bitirme_count": 1},
    {"name": "MAG", "ara_count": 2, "bitirme_count": 1},
    {"name": "MEK", "ara_count": 3, "bitirme_count": 2},
    {"name": "MFA", "ara_count": 1, "bitirme_count": 1},
    {"name": "MSA", "ara_count": 1, "bitirme_count": 4},
    {"name": "OA", "ara_count": 0, "bitirme_count": 1},
    {"name": "OK", "ara_count": 0, "bitirme_count": 0},
    {"name": "SV", "ara_count": 2, "bitirme_count": 0},
    {"name": "SY", "ara_count": 0, "bitirme_count": 0},
    {"name": "UK", "ara_count": 0, "bitirme_count": 0},
    {"name": "YES", "ara_count": 2, "bitirme_count": 1},
    {"name": "ZCT", "ara_count": 0, "bitirme_count": 0},
    {"name": "HTK", "ara_count": 3, "bitirme_count": 3},
    {"name": "MKY", "ara_count": 0, "bitirme_count": 1},
    {"name": "ÖMTK", "ara_count": 0, "bitirme_count": 0},
    {"name": "ŞD", "ara_count": 0, "bitirme_count": 0},
    {"name": "EA", "ara_count": 2, "bitirme_count": 0},
    {"name": "MEÖ", "ara_count": 1, "bitirme_count": 0},
]


async def clear_existing_instructors(db):
    """
    Mevcut instructor'ları siler
    Önce projelerle ilişkileri kontrol eder
    """
    print("🗑️  Mevcut instructor'ları temizleniyor...")
    
    # Önce projelerle ilişkili instructor'ları kontrol et
    check_query = text("""
        SELECT COUNT(*) 
        FROM projects 
        WHERE responsible_instructor_id IS NOT NULL 
           OR advisor_id IS NOT NULL 
           OR co_advisor_id IS NOT NULL
    """)
    result = await db.execute(check_query)
    project_count = result.scalar()
    
    if project_count > 0:
        print(f"   ⚠️  Uyarı: {project_count} proje instructor'larla ilişkili!")
        print("   Projelerin instructor_id'leri NULL yapılacak...")
        
        # Projelerin instructor_id'lerini NULL yap
        update_query = text("""
            UPDATE projects 
            SET responsible_instructor_id = NULL,
                advisor_id = NULL,
                co_advisor_id = NULL
        """)
        await db.execute(update_query)
        print("   ✅ Projelerin instructor ilişkileri temizlendi")
    
    # project_assistants tablosunu temizle
    delete_assistants_query = text("DELETE FROM project_assistants")
    await db.execute(delete_assistants_query)
    print("   ✅ project_assistants tablosu temizlendi")
    
    # instructor_keyword tablosunu temizle
    delete_keywords_query = text("DELETE FROM instructor_keyword")
    await db.execute(delete_keywords_query)
    print("   ✅ instructor_keyword tablosu temizlendi")
    
    # Tüm instructor'ları sil
    delete_instructors_query = text("DELETE FROM instructors")
    await db.execute(delete_instructors_query)
    await db.commit()
    print("   ✅ Tüm instructor'lar silindi")


async def create_instructors(db):
    """
    Yeni instructor'ları oluşturur
    """
    print("\n📝 Yeni instructor'lar oluşturuluyor...")
    
    created_count = 0
    for instructor_data in INSTRUCTORS_DATA:
        instructor = Instructor(
            name=instructor_data["name"],
            type=InstructorType.INSTRUCTOR.value,
            ara_count=instructor_data["ara_count"],
            bitirme_count=instructor_data["bitirme_count"],
            total_load=instructor_data["ara_count"] + instructor_data["bitirme_count"],
            email=None
        )
        db.add(instructor)
        created_count += 1
    
    await db.commit()
    print(f"   ✅ {created_count} instructor oluşturuldu")


async def verify_instructors(db):
    """
    Oluşturulan instructor'ları doğrular
    """
    print("\n🔍 Instructor'lar doğrulanıyor...")
    
    query = text("SELECT name, ara_count, bitirme_count, total_load FROM instructors ORDER BY name")
    result = await db.execute(query)
    instructors = result.fetchall()
    
    print(f"   📊 Toplam {len(instructors)} instructor bulundu:\n")
    
    for instructor in instructors:
        name, ara_count, bitirme_count, total_load = instructor
        print(f"   • {name}: Ara Proje={ara_count}, Bitirme Projesi={bitirme_count}, Toplam={total_load}")
    
    # Toplamları hesapla
    total_ara = sum(inst[1] for inst in instructors)
    total_bitirme = sum(inst[2] for inst in instructors)
    total_load = sum(inst[3] for inst in instructors)
    
    print(f"\n   📈 Toplamlar:")
    print(f"      - Ara Proje: {total_ara}")
    print(f"      - Bitirme Projesi: {total_bitirme}")
    print(f"      - Toplam Yük: {total_load}")


async def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🔄 Instructor Verilerini Güncelleme")
    print("=" * 60)
    
    async with async_session() as db:
        try:
            # Mevcut instructor'ları temizle
            await clear_existing_instructors(db)
            
            # Yeni instructor'ları oluştur
            await create_instructors(db)
            
            # Doğrula
            await verify_instructors(db)
            
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

