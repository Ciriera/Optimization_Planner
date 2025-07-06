"""
Veritabanı bağlantısını test etmek için basit bir script.
"""
import sys
import os
import asyncio
import pytest
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.base import async_session
from app.models import User, Instructor, Project, Classroom, TimeSlot, Schedule, AlgorithmRun, AuditLog

@pytest.mark.asyncio
async def test_db_connection():
    """Veritabanı bağlantısını test et"""
    try:
        # Veritabanı bağlantısını oluştur
        async with async_session() as db:
            # Bağlantıyı test et
            result = await db.execute(text("SELECT 1"))
            value = result.scalar()
            
            if value == 1:
                print("✅ Veritabanı bağlantısı başarılı!")
                return True
            else:
                print("❌ Veritabanı bağlantısı başarısız!")
                return False
    except Exception as e:
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return False

@pytest.mark.asyncio
async def test_models():
    """Veritabanı modellerini test et"""
    try:
        # Veritabanı bağlantısını oluştur
        async with async_session() as db:
            # Tüm modelleri kontrol et
            models = [User, Instructor, Project, Classroom, TimeSlot, Schedule, AlgorithmRun, AuditLog]
            
            print("\nModel tabloları kontrol ediliyor...")
            for model in models:
                try:
                    # Tablonun varlığını kontrol et
                    table_name = model.__tablename__
                    query = text(f"SELECT 1 FROM {table_name} LIMIT 1")
                    result = await db.execute(query)
                    result.fetchall()  # Sonucu tüket
                    print(f"✅ {table_name} tablosu mevcut")
                except Exception as e:
                    print(f"❌ {table_name} tablosu hatası: {e}")
            
            return True
    except Exception as e:
        print(f"❌ Model testi hatası: {e}")
        return False

async def main():
    print("="*50)
    print("Veritabanı Bağlantı Testi")
    print("="*50)
    
    # Veritabanı bağlantısını test et
    connection_success = await test_db_connection()
    
    if connection_success:
        # Modelleri test et
        await test_models()
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main()) 