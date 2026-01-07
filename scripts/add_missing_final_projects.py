#!/usr/bin/env python3
"""
Eksik bitirme projelerini aktif hale getirme scripti
Hedef: 38 bitirme projesi
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


async def check_and_activate_final_projects(db):
    """
    Pasif bitirme projelerini kontrol edip aktif hale getirir
    """
    print("=" * 60)
    print("🔍 Pasif Bitirme Projelerini Kontrol")
    print("=" * 60)
    
    # Aktif bitirme projesi sayısı
    query = text("""
        SELECT COUNT(*) 
        FROM projects 
        WHERE type::text = 'FINAL' AND is_active = true
    """)
    result = await db.execute(query)
    active_count = result.scalar()
    
    print(f"\n📊 Mevcut Aktif Bitirme Projesi: {active_count}")
    print(f"🎯 Hedef: 38")
    print(f"📉 Eksik: {38 - active_count}")
    
    if active_count >= 38:
        print("\n✅ Yeterli bitirme projesi var!")
        return
    
    # Pasif bitirme projelerini getir
    query = text("""
        SELECT id, title 
        FROM projects 
        WHERE type::text = 'FINAL' 
          AND is_active = false
        ORDER BY id
        LIMIT :limit
    """)
    result = await db.execute(query, {"limit": 38 - active_count})
    passive_projects = result.fetchall()
    
    if len(passive_projects) < (38 - active_count):
        print(f"\n⚠️  Sadece {len(passive_projects)} pasif bitirme projesi bulundu!")
        print(f"   {38 - active_count - len(passive_projects)} bitirme projesi eksik!")
        print(f"   Bu projeleri manuel olarak oluşturmanız gerekebilir.")
    
    if passive_projects:
        print(f"\n🔄 {len(passive_projects)} pasif bitirme projesi aktif yapılıyor...")
        
        project_ids = [p[0] for p in passive_projects]
        
        update_query = text("""
            UPDATE projects 
            SET is_active = true
            WHERE id = ANY(:project_ids)
        """)
        await db.execute(update_query, {"project_ids": project_ids})
        
        for project_id, title in passive_projects:
            print(f"   ✅ Aktif yapıldı: {title[:50]}...")
        
        await db.commit()
        
        # Yeni durumu kontrol et
        query = text("""
            SELECT COUNT(*) 
            FROM projects 
            WHERE type::text = 'FINAL' AND is_active = true
        """)
        result = await db.execute(query)
        new_count = result.scalar()
        
        print(f"\n✅ Yeni Aktif Bitirme Projesi Sayısı: {new_count}")
        
        if new_count == 38:
            print(f"\n🎉 Hedef değere ulaşıldı!")
        else:
            print(f"\n⚠️  Hala {38 - new_count} bitirme projesi eksik!")
    else:
        print("\n⚠️  Pasif bitirme projesi bulunamadı!")


async def main():
    """Ana fonksiyon"""
    async with async_session() as db:
        try:
            await check_and_activate_final_projects(db)
            
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












