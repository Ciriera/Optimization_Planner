"""
Veritabanı tablolarını oluşturmak için script.
"""
import sys
import os
import asyncio
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.base import engine
from app.db.base_all import Base

async def create_tables():
    """Tüm veritabanı tablolarını oluştur"""
    try:
        print("Veritabanı tabloları oluşturuluyor...")
        async with engine.begin() as conn:
            # Tüm tabloları oluştur
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Veritabanı tabloları başarıyla oluşturuldu!")
        return True
    except Exception as e:
        print(f"❌ Veritabanı tabloları oluşturulurken hata: {e}")
        return False

async def main():
    print("="*50)
    print("Veritabanı Tabloları Oluşturma")
    print("="*50)
    
    # Tabloları oluştur
    await create_tables()
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main()) 