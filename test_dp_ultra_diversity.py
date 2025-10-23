"""
Test script for DP ULTRA DIVERSITY verification
Çeşitliliğin arttığını doğrulamak için multiple run testi
"""

import sys
import json
import time
from datetime import datetime
from collections import defaultdict

# Backend path'i ekle
sys.path.insert(0, 'e:/Optimization_Planner-main_v2/Optimization_Planner-main')

from app.algorithms.dynamic_programming import DynamicProgramming


def generate_test_data():
    """Test verisi oluştur"""
    # 30 proje
    projects = []
    for i in range(1, 31):
        projects.append({
            'id': i,
            'name': f'Project {i}',
            'project_type': 'ara' if i % 2 == 0 else 'bitirme',
            'instructor_id': (i % 6) + 1  # 6 instructor'a dağıt
        })
    
    # 6 instructor
    instructors = []
    for i in range(1, 7):
        instructors.append({
            'id': i,
            'name': f'Instructor {i}',
            'email': f'instructor{i}@test.com'
        })
    
    # 5 sınıf
    classrooms = []
    for i in range(1, 6):
        classrooms.append({
            'id': i,
            'name': f'Classroom {i}',
            'capacity': 30
        })
    
    # 24 timeslot
    timeslots = []
    start_times = [
        '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', 
        '15:00', '16:00', '09:00', '10:00', '11:00', '12:00',
        '13:00', '14:00', '15:00', '16:00', '09:00', '10:00',
        '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'
    ]
    for i in range(1, 25):
        timeslots.append({
            'id': i,
            'start_time': start_times[i-1],
            'day': f'Day {((i-1) // 8) + 1}'
        })
    
    return {
        'projects': projects,
        'instructors': instructors,
        'classrooms': classrooms,
        'timeslots': timeslots
    }


def analyze_diversity(schedules, run_number):
    """Çeşitlilik analizi yap"""
    # Timeslot kullanımı
    timeslot_usage = defaultdict(int)
    classroom_usage = defaultdict(int)
    instructor_pairs = set()
    project_timeslot_pairs = {}
    
    for schedule in schedules:
        ts_id = schedule.get('timeslot_id')
        c_id = schedule.get('classroom_id')
        p_id = schedule.get('project_id')
        instructors = schedule.get('instructors', [])
        
        timeslot_usage[ts_id] += 1
        classroom_usage[c_id] += 1
        
        if len(instructors) >= 2:
            pair = tuple(sorted([instructors[0], instructors[1]]))
            instructor_pairs.add(pair)
        
        project_timeslot_pairs[p_id] = ts_id
    
    # Çeşitlilik metrikleri
    metrics = {
        'run': run_number,
        'unique_timeslots_used': len(timeslot_usage),
        'unique_classrooms_used': len(classroom_usage),
        'unique_instructor_pairs': len(instructor_pairs),
        'timeslot_distribution': dict(timeslot_usage),
        'classroom_distribution': dict(classroom_usage),
        'project_timeslot_mapping': project_timeslot_pairs,
        
        # Denge metrikleri
        'timeslot_usage_variance': calculate_variance(list(timeslot_usage.values())),
        'classroom_usage_variance': calculate_variance(list(classroom_usage.values())),
        
        # En çok kullanılan
        'most_used_timeslot': max(timeslot_usage.items(), key=lambda x: x[1]) if timeslot_usage else None,
        'most_used_classroom': max(classroom_usage.items(), key=lambda x: x[1]) if classroom_usage else None,
    }
    
    return metrics


def calculate_variance(values):
    """Varyans hesapla"""
    if not values:
        return 0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance


def compare_diversity(all_metrics):
    """Çoklu çalıştırmalar arası çeşitlilik karşılaştırması"""
    print("\n" + "="*80)
    print("ULTRA DIVERSITY ANALYSIS - COKLU CALISTIRMA KARSILASTIRMASI")
    print("="*80)
    
    # Her proje için farklı timeslotlarda görünme sayısı
    project_timeslot_diversity = defaultdict(set)
    for metrics in all_metrics:
        for project_id, timeslot_id in metrics['project_timeslot_mapping'].items():
            project_timeslot_diversity[project_id].add(timeslot_id)
    
    # Çeşitlilik skorları
    print("\nPROJE BAZLI CESITLILIK (Her proje kac farkli timeslot'ta goruldu?):")
    total_diversity = 0
    for project_id in sorted(project_timeslot_diversity.keys()):
        diversity_count = len(project_timeslot_diversity[project_id])
        total_diversity += diversity_count
        timeslots = sorted(project_timeslot_diversity[project_id])
        print(f"  Proje {project_id}: {diversity_count} farkli timeslot -> {timeslots}")
    
    avg_diversity = total_diversity / len(project_timeslot_diversity) if project_timeslot_diversity else 0
    print(f"\nORTALAMA PROJE CESITLILIGI: {avg_diversity:.2f} farkli timeslot/proje")
    
    # Timeslot kullanım çeşitliliği
    print("\nTIMESLOT KULLANIM CESITLILIGI:")
    timeslot_appearances = defaultdict(int)
    for metrics in all_metrics:
        for ts_id in metrics['timeslot_distribution'].keys():
            timeslot_appearances[ts_id] += 1
    
    print(f"  Toplam farklı timeslot kullanıldı: {len(timeslot_appearances)} / 24")
    print(f"  Timeslot kullanım dağılımı (kaç çalıştırmada görüldü):")
    for ts_id in sorted(timeslot_appearances.keys()):
        appearance_count = timeslot_appearances[ts_id]
        percentage = (appearance_count / len(all_metrics)) * 100
        print(f"    Timeslot {ts_id}: {appearance_count}/{len(all_metrics)} çalıştırmada ({percentage:.1f}%)")
    
    # Classroom kullanım çeşitliliği
    print("\nCLASSROOM KULLANIM CESITLILIGI:")
    classroom_appearances = defaultdict(int)
    for metrics in all_metrics:
        for c_id in metrics['classroom_distribution'].keys():
            classroom_appearances[c_id] += 1
    
    print(f"  Toplam farklı classroom kullanıldı: {len(classroom_appearances)} / 5")
    print(f"  Classroom kullanım dağılımı (kaç çalıştırmada görüldü):")
    for c_id in sorted(classroom_appearances.keys()):
        appearance_count = classroom_appearances[c_id]
        percentage = (appearance_count / len(all_metrics)) * 100
        print(f"    Classroom {c_id}: {appearance_count}/{len(all_metrics)} çalıştırmada ({percentage:.1f}%)")
    
    # Genel çeşitlilik skorları
    print("\nGENEL CESITLILIK SKORLARI:")
    avg_unique_timeslots = sum(m['unique_timeslots_used'] for m in all_metrics) / len(all_metrics)
    avg_unique_classrooms = sum(m['unique_classrooms_used'] for m in all_metrics) / len(all_metrics)
    avg_unique_pairs = sum(m['unique_instructor_pairs'] for m in all_metrics) / len(all_metrics)
    
    print(f"  Ortalama kullanılan unique timeslot: {avg_unique_timeslots:.2f} / 24")
    print(f"  Ortalama kullanılan unique classroom: {avg_unique_classrooms:.2f} / 5")
    print(f"  Ortalama unique instructor çifti: {avg_unique_pairs:.2f}")
    
    # Varyans analizi (düşük varyans = dengeli kullanım)
    avg_timeslot_variance = sum(m['timeslot_usage_variance'] for m in all_metrics) / len(all_metrics)
    avg_classroom_variance = sum(m['classroom_usage_variance'] for m in all_metrics) / len(all_metrics)
    
    print(f"\nDENGE METRIKLERI (Dusuk = Iyi):")
    print(f"  Ortalama timeslot kullanım varyansı: {avg_timeslot_variance:.2f}")
    print(f"  Ortalama classroom kullanım varyansı: {avg_classroom_variance:.2f}")
    
    # BAŞARI KRİTERLERİ
    print("\n" + "="*80)
    print("BASARI KRITERLERI DEGERLENDIRMESI")
    print("="*80)
    
    success_criteria = []
    
    # 1. Proje çeşitliliği: Ortalama 3+ farklı timeslot/proje olmalı
    if avg_diversity >= 3.0:
        success_criteria.append(("[OK] BASARILI", f"Proje cesitliligi: {avg_diversity:.2f} >= 3.0"))
    else:
        success_criteria.append(("[FAIL] BASARISIZ", f"Proje cesitliligi: {avg_diversity:.2f} < 3.0"))
    
    # 2. Timeslot çeşitliliği: En az %80 timeslot kullanılmalı
    timeslot_usage_percentage = (len(timeslot_appearances) / 24) * 100
    if timeslot_usage_percentage >= 80:
        success_criteria.append(("[OK] BASARILI", f"Timeslot cesitliligi: %{timeslot_usage_percentage:.1f} >= %80"))
    else:
        success_criteria.append(("[FAIL] BASARISIZ", f"Timeslot cesitliligi: %{timeslot_usage_percentage:.1f} < %80"))
    
    # 3. Classroom çeşitliliği: Tüm classroomlar kullanılmalı
    classroom_usage_percentage = (len(classroom_appearances) / 5) * 100
    if classroom_usage_percentage >= 100:
        success_criteria.append(("[OK] BASARILI", f"Classroom cesitliligi: %{classroom_usage_percentage:.1f} = %100"))
    else:
        success_criteria.append(("[WARN] KABUL EDILEBILIR", f"Classroom cesitliligi: %{classroom_usage_percentage:.1f} < %100"))
    
    # 4. Instructor pairing çeşitliliği: Ortalama 8+ unique pair olmalı
    if avg_unique_pairs >= 8:
        success_criteria.append(("[OK] BASARILI", f"Instructor cesitliligi: {avg_unique_pairs:.2f} >= 8"))
    else:
        success_criteria.append(("[WARN] KABUL EDILEBILIR", f"Instructor cesitliligi: {avg_unique_pairs:.2f} < 8"))
    
    for status, message in success_criteria:
        print(f"  {status}: {message}")
    
    # Genel başarı skoru
    success_count = sum(1 for status, _ in success_criteria if "[OK]" in status)
    total_criteria = len(success_criteria)
    success_percentage = (success_count / total_criteria) * 100
    
    print(f"\nGENEL BASARI SKORU: {success_count}/{total_criteria} (%{success_percentage:.1f})")
    
    if success_percentage >= 75:
        print("SONUC: ULTRA DIVERSITY BASARIYLA GERCEKLESTIRILDI!")
    elif success_percentage >= 50:
        print("SONUC: CESITLILIK KABUL EDILEBILIR SEVIYEDE")
    else:
        print("SONUC: CESITLILIK YETERSIZ, IYILESTIRME GEREKLI")


def main():
    """Ana test fonksiyonu"""
    print("="*80)
    print("DP ULTRA DIVERSITY TEST - BASLIYOR")
    print("="*80)
    print(f"Test Zamani: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Test Amaci: Coklu calistirmalarda cesitliligin arttigini dogrula")
    print("="*80)
    
    # Test verisi
    data = generate_test_data()
    print(f"\nTest Verisi:")
    print(f"  - {len(data['projects'])} proje")
    print(f"  - {len(data['instructors'])} instructor")
    print(f"  - {len(data['classrooms'])} classroom")
    print(f"  - {len(data['timeslots'])} timeslot")
    
    # Algoritma oluştur ve birden fazla kez çalıştır
    num_runs = 5
    print(f"\n{num_runs} kez calistirilacak...")
    
    all_metrics = []
    
    for i in range(num_runs):
        print(f"\n{'='*80}")
        print(f"RUN {i+1}/{num_runs}")
        print(f"{'='*80}")
        
        # Yeni instance oluştur
        dp = DynamicProgramming()
        
        # Çalıştır
        start_time = time.time()
        result = dp.optimize(data)
        end_time = time.time()
        
        schedules = result.get('assignments', [])
        
        print(f"Tamamlandi: {len(schedules)} atama yapildi ({end_time - start_time:.2f}s)")
        
        # Çeşitlilik analizi
        metrics = analyze_diversity(schedules, i+1)
        all_metrics.append(metrics)
        
        # Bu run için özet
        print(f"\nRun {i+1} Ozet:")
        print(f"  - Unique timeslot kullanildi: {metrics['unique_timeslots_used']}/24")
        print(f"  - Unique classroom kullanildi: {metrics['unique_classrooms_used']}/5")
        print(f"  - Unique instructor cifti: {metrics['unique_instructor_pairs']}")
        print(f"  - En cok kullanilan timeslot: {metrics['most_used_timeslot']}")
        print(f"  - En cok kullanilan classroom: {metrics['most_used_classroom']}")
        
        # Kısa bekleme (entropy için)
        time.sleep(0.1)
    
    # Karşılaştırmalı analiz
    compare_diversity(all_metrics)
    
    # Sonuçları kaydet
    output_file = f"dp_ultra_diversity_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'num_runs': num_runs,
            'test_data_size': {
                'projects': len(data['projects']),
                'instructors': len(data['instructors']),
                'classrooms': len(data['classrooms']),
                'timeslots': len(data['timeslots'])
            },
            'metrics': all_metrics
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nSonuclar kaydedildi: {output_file}")
    print("\n" + "="*80)
    print("TEST TAMAMLANDI!")
    print("="*80)


if __name__ == "__main__":
    main()

