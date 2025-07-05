"""
API endpointlerini test etmek için script.
"""
import sys
import os
import asyncio
import json
import httpx
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

# API URL'si
API_URL = f"{settings.SERVER_HOST}{settings.API_V1_STR}"

async def test_health_check():
    """
    Sağlık kontrolü endpointini test et.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/health")
            
            print(f"Sağlık kontrolü yanıtı: {response.status_code}")
            if response.status_code == 200:
                print("✅ Sağlık kontrolü başarılı")
                return True
            else:
                print(f"❌ Sağlık kontrolü başarısız: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Sağlık kontrolü hatası: {e}")
        return False

async def test_algorithms_list():
    """
    Algoritma listesi endpointini test et.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/algorithms/list")
            
            print(f"Algoritma listesi yanıtı: {response.status_code}")
            if response.status_code == 200:
                algorithms = response.json()
                print(f"Kullanılabilir algoritmalar: {algorithms}")
                print("✅ Algoritma listesi başarılı")
                return True
            else:
                print(f"❌ Algoritma listesi başarısız: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Algoritma listesi hatası: {e}")
        return False

async def test_instructors_list():
    """
    Öğretim üyeleri listesi endpointini test et.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/instructors/")
            
            print(f"Öğretim üyeleri listesi yanıtı: {response.status_code}")
            if response.status_code == 200:
                instructors = response.json()
                print(f"Öğretim üyeleri sayısı: {len(instructors)}")
                print("✅ Öğretim üyeleri listesi başarılı")
                return True
            else:
                print(f"❌ Öğretim üyeleri listesi başarısız: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Öğretim üyeleri listesi hatası: {e}")
        return False

async def test_projects_list():
    """
    Projeler listesi endpointini test et.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/projects/")
            
            print(f"Projeler listesi yanıtı: {response.status_code}")
            if response.status_code == 200:
                projects = response.json()
                print(f"Projeler sayısı: {len(projects)}")
                print("✅ Projeler listesi başarılı")
                return True
            else:
                print(f"❌ Projeler listesi başarısız: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Projeler listesi hatası: {e}")
        return False

async def test_classrooms_list():
    """
    Sınıflar listesi endpointini test et.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/classrooms/")
            
            print(f"Sınıflar listesi yanıtı: {response.status_code}")
            if response.status_code == 200:
                classrooms = response.json()
                print(f"Sınıflar sayısı: {len(classrooms)}")
                print("✅ Sınıflar listesi başarılı")
                return True
            else:
                print(f"❌ Sınıflar listesi başarısız: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Sınıflar listesi hatası: {e}")
        return False

async def test_timeslots_list():
    """
    Zaman dilimleri listesi endpointini test et.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/timeslots/")
            
            print(f"Zaman dilimleri listesi yanıtı: {response.status_code}")
            if response.status_code == 200:
                timeslots = response.json()
                print(f"Zaman dilimleri sayısı: {len(timeslots)}")
                print("✅ Zaman dilimleri listesi başarılı")
                return True
            else:
                print(f"❌ Zaman dilimleri listesi başarısız: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Zaman dilimleri listesi hatası: {e}")
        return False

async def main():
    print("="*50)
    print("API Endpointleri Testi")
    print("="*50)
    
    # Sağlık kontrolü
    health_check = await test_health_check()
    
    if health_check:
        # Algoritma listesi
        await test_algorithms_list()
        
        # Öğretim üyeleri listesi
        await test_instructors_list()
        
        # Projeler listesi
        await test_projects_list()
        
        # Sınıflar listesi
        await test_classrooms_list()
        
        # Zaman dilimleri listesi
        await test_timeslots_list()
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main()) 