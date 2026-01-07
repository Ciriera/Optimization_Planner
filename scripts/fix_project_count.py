#!/usr/bin/env python3
"""
Proje sayısını görseldeki tabloya göre düzenleme scripti
Toplam 81 proje olmalı: 43 ara + 38 bitirme
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


async def check_current_status(db):
    """
    Mevcut durumu kontrol eder
    """
    print("=" * 60)
    print("📊 Mevcut Durum Kontrolü")
    print("=" * 60)
    
    # Toplam proje sayısı
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
    
    print(f"\n📈 Mevcut Durum:")
    print(f"   - Ara Proje: {ara_count}")
    print(f"   - Bitirme Projesi: {bitirme_count}")
    print(f"   - Toplam: {total_count}")
    
    print(f"\n🎯 Hedef Durum:")
    print(f"   - Ara Proje: 43")
    print(f"   - Bitirme Projesi: 38")
    print(f"   - Toplam: 81")
    
    print(f"\n📉 Fark:")
    print(f"   - Ara Proje fazlası: {ara_count - 43}")
    print(f"   - Bitirme Projesi fazlası: {bitirme_count - 38}")
    print(f"   - Toplam fazla: {total_count - 81}")
    
    return ara_count, bitirme_count, total_count


async def fix_project_count(db):
    """
    Proje sayısını hedef değerlere göre düzenler
    """
    print("\n" + "=" * 60)
    print("🔧 Proje Sayısını Düzenleme")
    print("=" * 60)
    
    # Ara projeleri kontrol et ve fazlaları pasif yap
    query = text("""
        SELECT id, title 
        FROM projects 
        WHERE type::text = 'INTERIM' 
          AND is_active = true
        ORDER BY id
    """)
    result = await db.execute(query)
    ara_projects = result.fetchall()
    
    if len(ara_projects) > 43:
        excess_ara = len(ara_projects) - 43
        print(f"\n🗑️  {excess_ara} fazla ara proje pasif yapılıyor...")
        
        # Son N projeyi pasif yap
        excess_ids = [p[0] for p in ara_projects[43:]]
        
        update_query = text("""
            UPDATE projects 
            SET is_active = false
            WHERE id = ANY(:project_ids)
        """)
        await db.execute(update_query, {"project_ids": excess_ids})
        
        for project_id, title in ara_projects[43:]:
            print(f"   ⚠️  Pasif yapıldı: {title[:50]}...")
    
    # Bitirme projelerini kontrol et ve fazlaları pasif yap
    query = text("""
        SELECT id, title 
        FROM projects 
        WHERE type::text = 'FINAL' 
          AND is_active = true
        ORDER BY id
    """)
    result = await db.execute(query)
    final_projects = result.fetchall()
    
    if len(final_projects) > 38:
        excess_final = len(final_projects) - 38
        print(f"\n🗑️  {excess_final} fazla bitirme projesi pasif yapılıyor...")
        
        # Son N projeyi pasif yap
        excess_ids = [p[0] for p in final_projects[38:]]
        
        update_query = text("""
            UPDATE projects 
            SET is_active = false
            WHERE id = ANY(:project_ids)
        """)
        await db.execute(update_query, {"project_ids": excess_ids})
        
        for project_id, title in final_projects[38:]:
            print(f"   ⚠️  Pasif yapıldı: {title[:50]}...")
    
    await db.commit()
    
    # Yeni durumu kontrol et
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
    
    print(f"\n✅ Yeni Durum:")
    print(f"   - Ara Proje: {ara_count}")
    print(f"   - Bitirme Projesi: {bitirme_count}")
    print(f"   - Toplam: {total_count}")
    
    if ara_count == 43 and bitirme_count == 38 and total_count == 81:
        print(f"\n🎉 Proje sayıları hedef değerlere ulaştı!")
    else:
        print(f"\n⚠️  Hala fark var! Ara={ara_count}/43, Bitirme={bitirme_count}/38, Toplam={total_count}/81")


async def main():
    """Ana fonksiyon"""
    async with async_session() as db:
        try:
            ara_count, bitirme_count, total_count = await check_current_status(db)
            
            if total_count > 81:
                await fix_project_count(db)
            else:
                print("\n✅ Proje sayıları zaten hedef değerlerde veya altında!")
            
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












