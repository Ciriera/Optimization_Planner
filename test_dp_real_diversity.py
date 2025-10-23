"""
GERÇEK ÇEŞİTLİLİK TESTİ - Aynı veriyle 3 kez çalıştır, sonuçlar FARKLI olmalı!
"""

import sys
sys.path.insert(0, 'e:/Optimization_Planner-main_v2/Optimization_Planner-main')

from app.algorithms.dynamic_programming import DynamicProgramming
import json

def generate_test_data():
    """Basit test verisi"""
    projects = [{'id': i, 'name': f'Project {i}', 'project_type': 'ara' if i % 2 == 0 else 'bitirme', 'instructor_id': (i % 6) + 1} for i in range(1, 31)]
    instructors = [{'id': i, 'name': f'Instructor {i}', 'email': f'inst{i}@test.com'} for i in range(1, 7)]
    classrooms = [{'id': i, 'name': f'Classroom {i}', 'capacity': 30} for i in range(1, 6)]
    timeslots = [{'id': i, 'start_time': f'{9 + (i-1) % 8}:00', 'day': f'Day {((i-1) // 8) + 1}'} for i in range(1, 25)]
    
    return {'projects': projects, 'instructors': instructors, 'classrooms': classrooms, 'timeslots': timeslots}

def main():
    print("="*80)
    print("GERCEK CESITLILIK TESTI - Ayni veriyle 3 kez calistir")
    print("="*80)
    
    data = generate_test_data()
    results = []
    
    for i in range(3):
        print(f"\n{'='*80}")
        print(f"RUN {i+1}/3")
        print(f"{'='*80}")
        
        # YENİ INSTANCE OLUŞTUR
        dp = DynamicProgramming()
        result = dp.optimize(data)
        schedules = result.get('assignments', [])
        
        # TÜM projelerin timeslot atamasını kaydet
        all_assignments = {}
        for schedule in schedules:
            project_id = schedule.get('project_id')
            timeslot_id = schedule.get('timeslot_id')
            classroom_id = schedule.get('classroom_id')
            all_assignments[project_id] = {'timeslot': timeslot_id, 'classroom': classroom_id}
        
        results.append(all_assignments)
        
        print(f"\nIlk 10 Proje Atamalari:")
        for pid in sorted(all_assignments.keys())[:10]:
            info = all_assignments[pid]
            print(f"  Proje {pid}: Timeslot {info['timeslot']}, Classroom {info['classroom']}")
    
    # KARŞILAŞTIRMA
    print(f"\n{'='*80}")
    print("SONUC KARSILASTIRMASI")
    print(f"{'='*80}")
    
    # Her proje için kaç farklı timeslot kullanıldı?
    project_diversity = {}
    for i in range(1, 31):  # TÜM projeler
        timeslots = set()
        classrooms = set()
        for run_result in results:
            if i in run_result:
                timeslots.add(run_result[i]['timeslot'])
                classrooms.add(run_result[i]['classroom'])
        project_diversity[i] = {'timeslots': timeslots, 'classrooms': classrooms}
    
    print("\nIlk 10 proje kac farkli yerde goruldu?")
    total_diversity = 0
    diverse_projects = 0
    for pid in sorted(project_diversity.keys())[:10]:
        info = project_diversity[pid]
        ts_count = len(info['timeslots'])
        cl_count = len(info['classrooms'])
        total_diversity += ts_count
        if ts_count >= 2:
            diverse_projects += 1
        print(f"  Proje {pid}: {ts_count} farkli timeslot {info['timeslots']}, {cl_count} farkli classroom {info['classrooms']}")
    
    avg_diversity = total_diversity / 10  # İlk 10 proje üzerinden
    diversity_percentage = (diverse_projects / 10) * 100
    
    print(f"\n{'='*80}")
    print("BASARI KRITERLERI")
    print(f"{'='*80}")
    
    # BAŞARI KRİTERİ 1: Ortalama çeşitlilik >= 2.0
    # BAŞARI KRİTERİ 2: En az %50 proje farklı yerlerde görülmeli
    success1 = avg_diversity >= 2.0
    success2 = diversity_percentage >= 50.0
    
    print(f"Ortalama cesitlilik: {avg_diversity:.2f} (Hedef: >= 2.0)")
    print(f"Farkli yerlerde gorunen projeler: %{diversity_percentage:.1f} (Hedef: >= %50)")
    
    if success1 and success2:
        print(f"\n[OK] BASARILI: Her iki kriter de karsilandi!")
        print("SONUC: Her calistirmada FARKLI sonuclar aliniyor! [OK]")
    elif success1 or success2:
        print(f"\n[WARN] KISMEN BASARILI: Bir kriter karsilandi")
        print("SONUC: Bazi projeler farkli yerlerde gorunuyor")
    else:
        print(f"\n[FAIL] BASARISIZ: Kriterler karsilanmadi")
        print("SONUC: Hala ayni sonuclar aliniyor! [FAIL]")
        print("SORUN: Deterministik davranis devam ediyor!")
    
    print(f"{'='*80}")
    
    # Detaylı sonuçları kaydet
    with open('dp_real_diversity_test.json', 'w', encoding='utf-8') as f:
        json.dump({
            'run1': {str(k): v for k, v in results[0].items()},
            'run2': {str(k): v for k, v in results[1].items()},
            'run3': {str(k): v for k, v in results[2].items()},
            'diversity_analysis': {str(k): {'timeslots': list(v['timeslots']), 'classrooms': list(v['classrooms'])} for k, v in project_diversity.items()},
            'average_diversity': avg_diversity,
            'success1': success1,
            'success2': success2,
            'overall_success': success1 and success2
        }, f, indent=2)
    
    print("\nSonuclar kaydedildi: dp_real_diversity_test.json")

if __name__ == "__main__":
    main()

