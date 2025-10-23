#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for slot insufficiency warning system
Tests the slot calculation logic and warning system
"""

import requests
import json
import sys

def test_slot_calculation():
    """Test slot calculation logic"""
    print("Testing Slot Calculation Logic")
    print("=" * 50)
    
    # Test scenarios
    test_cases = [
        {
            "classroom_count": 5,
            "expected_slots": 80,  # 5 * 16
            "description": "5 sınıf = 80 slot"
        },
        {
            "classroom_count": 6,
            "expected_slots": 96,  # 6 * 16
            "description": "6 sınıf = 96 slot"
        },
        {
            "classroom_count": 7,
            "expected_slots": 112,  # 7 * 16
            "description": "7 sınıf = 112 slot"
        }
    ]
    
    for case in test_cases:
        classroom_count = case["classroom_count"]
        expected_slots = case["expected_slots"]
        description = case["description"]
        
        # Calculate slots
        timeslot_count = 16  # Fixed 16 timeslots
        calculated_slots = classroom_count * timeslot_count
        
        print(f"Test: {description}")
        print(f"   Sınıf Sayısı: {classroom_count}")
        print(f"   Zaman Dilimi: {timeslot_count}")
        print(f"   Hesaplanan Slot: {calculated_slots}")
        print(f"   Beklenen Slot: {expected_slots}")
        print(f"   Sonuç: {'DOĞRU' if calculated_slots == expected_slots else 'HATALI'}")
        print()

def test_api_endpoints():
    """Test API endpoints for slot insufficiency check"""
    print("Testing API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test projects endpoint
        print("Testing /projects endpoint...")
        response = requests.get(f"{base_url}/projects")
        if response.status_code == 200:
            projects = response.json()
            project_count = len(projects)
            print(f"   Proje sayısı: {project_count}")
        else:
            print(f"   Proje endpoint hatası: {response.status_code}")
            return
            
        # Test classrooms endpoint
        print("Testing /classrooms endpoint...")
        response = requests.get(f"{base_url}/classrooms")
        if response.status_code == 200:
            classrooms = response.json()
            classroom_count = len(classrooms)
            print(f"   Sınıf sayısı: {classroom_count}")
        else:
            print(f"   Sınıf endpoint hatası: {response.status_code}")
            return
            
        # Test timeslots endpoint
        print("Testing /timeslots endpoint...")
        response = requests.get(f"{base_url}/timeslots")
        if response.status_code == 200:
            timeslots = response.json()
            timeslot_count = len(timeslots)
            print(f"   Zaman dilimi sayısı: {timeslot_count}")
        else:
            print(f"   Zaman dilimi endpoint hatası: {response.status_code}")
            return
            
        # Calculate slot sufficiency
        print("\nSlot Yetersizliği Analizi")
        print("-" * 30)
        
        available_slots = classroom_count * timeslot_count
        required_slots = project_count
        
        print(f"Sınıf Sayısı: {classroom_count}")
        print(f"Zaman Dilimi Sayısı: {timeslot_count}")
        print(f"Mevcut Slot Sayısı: {available_slots}")
        print(f"Gerekli Slot Sayısı: {required_slots}")
        
        if required_slots > available_slots:
            shortage = required_slots - available_slots
            coverage_percentage = round((available_slots / required_slots) * 100)
            print(f"SLOT YETERSİZLİĞİ TESPİT EDİLDİ!")
            print(f"   Eksik Slot: {shortage}")
            print(f"   Kapsama Oranı: %{coverage_percentage}")
            print(f"   {shortage} proje atanamayacaktır!")
        else:
            coverage_percentage = round((available_slots / required_slots) * 100)
            print(f"YETERLİ SLOT MEVCUT")
            print(f"   Kapsama Oranı: %{coverage_percentage}")
            print(f"   Tüm projeler atanabilecektir!")
            
    except requests.exceptions.ConnectionError:
        print("API bağlantı hatası - Sunucu çalışıyor mu?")
    except Exception as e:
        print(f"Test hatası: {e}")

def test_warning_scenarios():
    """Test different warning scenarios"""
    print("\nUyarı Senaryoları Testi")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Kritik Yetersizlik (5 sınıf, 100 proje)",
            "classrooms": 5,
            "projects": 100,
            "expected_warning": True
        },
        {
            "name": "Orta Yetersizlik (6 sınıf, 100 proje)",
            "classrooms": 6,
            "projects": 100,
            "expected_warning": True
        },
        {
            "name": "Yeterli Slot (7 sınıf, 100 proje)",
            "classrooms": 7,
            "projects": 100,
            "expected_warning": False
        },
        {
            "name": "Fazla Slot (7 sınıf, 50 proje)",
            "classrooms": 7,
            "projects": 50,
            "expected_warning": False
        }
    ]
    
    for scenario in scenarios:
        name = scenario["name"]
        classrooms = scenario["classrooms"]
        projects = scenario["projects"]
        expected_warning = scenario["expected_warning"]
        
        available_slots = classrooms * 16
        required_slots = projects
        has_shortage = required_slots > available_slots
        
        print(f"Test: {name}")
        print(f"   Sınıf: {classrooms}, Proje: {projects}")
        print(f"   Mevcut: {available_slots}, Gerekli: {required_slots}")
        print(f"   Uyarı Beklenen: {'EVET' if expected_warning else 'HAYIR'}")
        print(f"   Uyarı Gerçek: {'EVET' if has_shortage else 'HAYIR'}")
        print(f"   Sonuç: {'DOĞRU' if has_shortage == expected_warning else 'HATALI'}")
        print()

if __name__ == "__main__":
    print("Slot Yetersizliği Uyarı Sistemi Testi")
    print("=" * 60)
    print()
    
    # Test slot calculation
    test_slot_calculation()
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test warning scenarios
    test_warning_scenarios()
    
    print("Test tamamlandı!")
    print("\nNot: Frontend'de slot yetersizliği uyarısı görüntülenmek için:")
    print("   1. Sınıf sayısını 5 veya 6 yapın")
    print("   2. Proje sayısı slot sayısından fazla olmalı")
    print("   3. Algoritma çalıştırmayı deneyin")
    print("   4. Uyarı pop-up'ı görünecektir")
