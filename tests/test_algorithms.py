"""
Algoritma modüllerini test etmek için script.
"""
import sys
import os
import asyncio
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.algorithms.factory import AlgorithmFactory
from app.algorithms.base import BaseAlgorithm

def test_algorithm_factory():
    """AlgorithmFactory'yi test et"""
    try:
        factory = AlgorithmFactory()
        
        # Kullanılabilir algoritmaları listele
        algorithms = factory.list_algorithms()
        print(f"Kullanılabilir algoritmalar: {algorithms}")
        
        # Her algoritmayı test et
        for algo_name in algorithms:
            try:
                algorithm = factory.create_algorithm(algo_name)
                print(f"✅ {algo_name} algoritması başarıyla oluşturuldu")
                
                # Algoritmanın BaseAlgorithm'den türediğini kontrol et
                assert isinstance(algorithm, BaseAlgorithm), f"{algo_name} BaseAlgorithm'den türetilmemiş"
                
                # Gerekli metodların var olduğunu kontrol et
                assert hasattr(algorithm, "execute"), f"{algo_name} execute metoduna sahip değil"
                assert hasattr(algorithm, "get_name"), f"{algo_name} get_name metoduna sahip değil"
                assert hasattr(algorithm, "get_description"), f"{algo_name} get_description metoduna sahip değil"
                
            except Exception as e:
                print(f"❌ {algo_name} algoritması hatası: {e}")
        
        return True
    except Exception as e:
        print(f"❌ AlgorithmFactory testi hatası: {e}")
        return False

async def test_algorithm_execution():
    """Algoritma yürütmeyi test et"""
    try:
        factory = AlgorithmFactory()
        algorithms = factory.list_algorithms()
        
        if not algorithms:
            print("❌ Test edilecek algoritma bulunamadı")
            return False
        
        print("\nAlgoritma yürütme testi:")
        
        # İlk algoritmayı test et
        algo_name = algorithms[0]
        algorithm = factory.create_algorithm(algo_name)
        
        # Test verileri oluştur
        test_data = {
            "instructors": [
                {"id": 1, "name": "Prof. Test", "type": "professor"},
                {"id": 2, "name": "Asst. Test", "type": "research_assistant"}
            ],
            "projects": [
                {"id": 1, "title": "Test Project", "type": "final", "responsible_id": 1},
                {"id": 2, "title": "Test Project 2", "type": "final", "responsible_id": 2}
            ],
            "classrooms": [
                {"id": 1, "name": "D101", "capacity": 30},
                {"id": 2, "name": "D102", "capacity": 25}
            ],
            "timeslots": [
                {"id": 1, "start_time": "09:00", "end_time": "09:30", "is_morning": True},
                {"id": 2, "start_time": "10:00", "end_time": "10:30", "is_morning": True}
            ]
        }
        
        # Algoritmayı çalıştır
        print(f"Algoritma çalıştırılıyor: {algo_name}")
        result = algorithm.execute(test_data)
        
        # Sonucu kontrol et
        print(f"Algoritma sonucu: {result}")
        assert result is not None, "Algoritma sonucu None"
        assert "schedule" in result, "Sonuçta schedule anahtarı yok"
        
        print(f"✅ {algo_name} algoritması başarıyla çalıştırıldı")
        return True
    except Exception as e:
        print(f"❌ Algoritma yürütme testi hatası: {e}")
        return False

def main():
    print("="*50)
    print("Algoritma Modülü Testi")
    print("="*50)
    
    # AlgorithmFactory'yi test et
    factory_success = test_algorithm_factory()
    
    # Algoritma yürütmeyi test et
    if factory_success:
        asyncio.run(test_algorithm_execution())
    
    print("="*50)

if __name__ == "__main__":
    main() 