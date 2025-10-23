"""
Dynamic Programming Algorithm - Çeşitlilik Kontrolü
"""
import asyncio
from sqlalchemy import text
from app.db.base import async_session
import json
from collections import Counter

async def check_diversity():
    """DP algoritması sonuçlarında çeşitliliği kontrol et"""
    
    async with async_session() as db:
        # Schedules tablosundan atamaları al
        result = await db.execute(text("""
            SELECT 
                s.id,
                s.project_id,
                p.title as project_title,
                s.classroom_id,
                c.name as classroom_name,
                s.timeslot_id,
                t.start_time,
                s.instructors
            FROM schedules s
            JOIN projects p ON s.project_id = p.id
            JOIN classrooms c ON s.classroom_id = c.id
            JOIN timeslots t ON s.timeslot_id = t.id
            ORDER BY t.start_time, c.name
            LIMIT 30
        """))
        
        schedules = result.fetchall()
        
        print("=" * 100)
        print("DYNAMIC PROGRAMMING - ÇEŞİTLİLİK KONTROLÜ")
        print("=" * 100)
        print(f"Toplam kontrol edilen atama: {len(schedules)}")
        print()
        
        # Çeşitlilik analizi
        project_ids = []
        timeslots = []
        classrooms = []
        instructor_pairs = []
        
        for schedule in schedules:
            schedule_id, project_id, project_title, classroom_id, classroom_name, timeslot_id, start_time, instructors_json = schedule
            
            project_ids.append(project_id)
            timeslots.append(start_time)
            classrooms.append(classroom_name)
            
            if instructors_json:
                try:
                    if isinstance(instructors_json, str):
                        instructors_list = json.loads(instructors_json)
                    else:
                        instructors_list = instructors_json
                    
                    if len(instructors_list) >= 2:
                        pair = f"{instructors_list[0]}-{instructors_list[1]}"
                        instructor_pairs.append(pair)
                        
                except Exception as e:
                    print(f"  [HATA] JSON parse hatasi: {e}")
        
        # Çeşitlilik istatistikleri
        print("ÇEŞİTLİLİK İSTATİSTİKLERİ:")
        print("-" * 80)
        
        # 1. Proje çeşitliliği
        unique_projects = len(set(project_ids))
        total_projects = len(project_ids)
        project_diversity = (unique_projects / total_projects) * 100 if total_projects > 0 else 0
        
        print(f"1. PROJE ÇEŞİTLİLİĞİ:")
        print(f"   Toplam proje: {total_projects}")
        print(f"   Benzersiz proje: {unique_projects}")
        print(f"   Çeşitlilik oranı: {project_diversity:.1f}%")
        
        if project_diversity >= 80:
            print(f"   [BAŞARILI] YÜKSEK ÇEŞİTLİLİK")
        elif project_diversity >= 60:
            print(f"   [UYARI] ORTA ÇEŞİTLİLİK")
        else:
            print(f"   [HATA] DÜŞÜK ÇEŞİTLİLİK")
        
        # 2. Timeslot çeşitliliği
        unique_timeslots = len(set(timeslots))
        total_timeslots = len(timeslots)
        timeslot_diversity = (unique_timeslots / total_timeslots) * 100 if total_timeslots > 0 else 0
        
        print(f"\n2. ZAMAN SLOT ÇEŞİTLİLİĞİ:")
        print(f"   Toplam slot: {total_timeslots}")
        print(f"   Benzersiz slot: {unique_timeslots}")
        print(f"   Çeşitlilik oranı: {timeslot_diversity:.1f}%")
        
        if timeslot_diversity >= 70:
            print(f"   [BAŞARILI] YÜKSEK ÇEŞİTLİLİK")
        elif timeslot_diversity >= 50:
            print(f"   [UYARI] ORTA ÇEŞİTLİLİK")
        else:
            print(f"   [HATA] DÜŞÜK ÇEŞİTLİLİK")
        
        # 3. Sınıf çeşitliliği
        unique_classrooms = len(set(classrooms))
        total_classrooms = len(classrooms)
        classroom_diversity = (unique_classrooms / total_classrooms) * 100 if total_classrooms > 0 else 0
        
        print(f"\n3. SINIF ÇEŞİTLİLİĞİ:")
        print(f"   Toplam sınıf kullanımı: {total_classrooms}")
        print(f"   Benzersiz sınıf: {unique_classrooms}")
        print(f"   Çeşitlilik oranı: {classroom_diversity:.1f}%")
        
        if classroom_diversity >= 60:
            print(f"   [BAŞARILI] YÜKSEK ÇEŞİTLİLİK")
        elif classroom_diversity >= 40:
            print(f"   [UYARI] ORTA ÇEŞİTLİLİK")
        else:
            print(f"   [HATA] DÜŞÜK ÇEŞİTLİLİK")
        
        # 4. Instructor pair çeşitliliği
        unique_pairs = len(set(instructor_pairs))
        total_pairs = len(instructor_pairs)
        pair_diversity = (unique_pairs / total_pairs) * 100 if total_pairs > 0 else 0
        
        print(f"\n4. INSTRUCTOR PAIR ÇEŞİTLİLİĞİ:")
        print(f"   Toplam pair: {total_pairs}")
        print(f"   Benzersiz pair: {unique_pairs}")
        print(f"   Çeşitlilik oranı: {pair_diversity:.1f}%")
        
        if pair_diversity >= 70:
            print(f"   [BAŞARILI] YÜKSEK ÇEŞİTLİLİK")
        elif pair_diversity >= 50:
            print(f"   [UYARI] ORTA ÇEŞİTLİLİK")
        else:
            print(f"   [HATA] DÜŞÜK ÇEŞİTLİLİK")
        
        # 5. Genel çeşitlilik skoru
        overall_diversity = (project_diversity + timeslot_diversity + classroom_diversity + pair_diversity) / 4
        
        print(f"\n5. GENEL ÇEŞİTLİLİK SKORU:")
        print(f"   Toplam skor: {overall_diversity:.1f}/100")
        
        if overall_diversity >= 75:
            print(f"   [MÜKEMMEL] MÜKEMMEL ÇEŞİTLİLİK!")
        elif overall_diversity >= 60:
            print(f"   [BAŞARILI] İYİ ÇEŞİTLİLİK")
        elif overall_diversity >= 45:
            print(f"   [UYARI] ORTA ÇEŞİTLİLİK")
        else:
            print(f"   [HATA] DÜŞÜK ÇEŞİTLİLİK")
        
        # 6. Detaylı analiz
        print(f"\n6. DETAYLI ANALİZ:")
        print(f"   Kullanılan projeler: {sorted(set(project_ids))}")
        print(f"   Kullanılan zaman slotları: {sorted(set(timeslots))}")
        print(f"   Kullanılan sınıflar: {sorted(set(classrooms))}")
        print(f"   Instructor pair'lar: {sorted(set(instructor_pairs))}")
        
        print()
        print("=" * 100)

if __name__ == "__main__":
    asyncio.run(check_diversity())
