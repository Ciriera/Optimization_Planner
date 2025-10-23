# Lexicographic AI Optimization Guide

## Genel Bakış

Bu algoritma, proje jüri atamalarını optimize etmek için geliştirilmiş AI destekli bir lexicographic optimizasyon sistemidir. Algoritma, öğretim görevlilerinin iş yüklerini dengeli bir şekilde dağıtmayı ve ardışık oturumlarda verimli eşleştirmeler yapmayı hedefler.

## Temel Özellikler

1. **Akıllı Sıralama**
   - Öğretim görevlileri proje sorumluluk sayılarına göre sıralanır
   - Sıralama azalan düzende yapılır (en çok projeden en aza)

2. **Dinamik Grup Oluşturma**
   - Tek/çift sayı durumlarına göre otomatik adaptasyon
   - Üst grup: n kişi
   - Alt grup: n veya n+1 kişi (toplam sayıya bağlı olarak)

3. **Consecutive Grouping**
   - Ardışık oturumlarda rol değişimi
   - Supervisor ↔ Jury rotasyonu
   - Optimal zaman dilimi kullanımı

## AI Metrikleri

### 1. Workload Distribution (İş Yükü Dağılımı)
- Standart sapma bazlı denge ölçümü
- 0'a yakın değerler daha dengeli dağılımı gösterir

### 2. Pairing Efficiency (Eşleştirme Verimliliği)
- 0-1 arası normalize edilmiş skor
- 1'e yakın değerler optimal eşleştirmeyi gösterir

### 3. Schedule Optimization (Çizelge Optimizasyonu)
- Ardışık geçişlerin verimliliği
- Rol değişimlerinin başarı oranı

## Kullanım Örneği

```python
from app.algorithms.lexicographic import LexicographicOptimizer, Instructor, Project, TimeSlot

# Veri hazırlama
instructors = [
    Instructor(id=1, name="Prof. A", project_count=5, availability=[True] * 10),
    Instructor(id=2, name="Prof. B", project_count=3, availability=[True] * 10),
]

projects = [Project(id=1, supervisor_id=1)]
time_slots = [
    TimeSlot(id=1, start_time="09:00", end_time="10:00"),
    TimeSlot(id=2, start_time="10:00", end_time="11:00"),
]

# Optimizasyon
optimizer = LexicographicOptimizer(instructors, projects, time_slots)
result = optimizer.optimize()

# AI Metrikleri
metrics = optimizer.get_ai_enhanced_metrics()
```

## Best Practices

1. **Veri Hazırlığı**
   - Instructor availability bilgilerinin doğru girilmesi
   - Proje sayılarının güncel tutulması
   - Zaman dilimlerinin çakışmaması

2. **Optimizasyon**
   - Küçük gruplarla test edilmesi
   - Metrik sonuçlarının analiz edilmesi
   - Gerektiğinde parametrelerin ayarlanması

3. **Sonuçların Değerlendirilmesi**
   - Workload distribution < 2.0 hedeflenmeli
   - Pairing efficiency > 0.7 olmalı
   - Schedule optimization > 0.8 ideal

## Hata Durumları

1. **Yetersiz Veri**
   - En az 2 instructor gerekli
   - En az 1 proje gerekli
   - En az 2 zaman dilimi öneriliyor

2. **Uyumsuz Veriler**
   - Proje sayısı > Instructor sayısı durumu
   - Availability çakışmaları
   - Geçersiz zaman dilimleri

## Performans İpuçları

1. **Büyük Veri Setleri**
   - 100+ instructor için batch processing
   - Numpy vectorization kullanımı
   - Cache mekanizması implementasyonu

2. **Optimizasyon Stratejileri**
   - Greedy yaklaşım ile başlangıç çözümü
   - Iterative improvement
   - Local search optimizasyonu
