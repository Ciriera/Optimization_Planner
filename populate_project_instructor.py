"""
project_instructor tablosunu dolduran script
Her projeye instructor(lar) atar
"""
import asyncio
import sys
import random

sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.base import async_session


async def populate_project_instructor():
    """project_instructor tablosunu doldur"""
    
    print("=" * 60)
    print("PROJECT-INSTRUCTOR ASSIGNMENT SCRIPT")
    print("=" * 60)
    
    async with async_session() as db:
        try:
            # Mevcut projeleri al
            print("\n[1] Projeler getiriliyor...")
            result = await db.execute(text("""
                SELECT id, title, type, responsible_instructor_id 
                FROM projects 
                WHERE responsible_instructor_id IS NOT NULL
                ORDER BY id
            """))
            projects = result.fetchall()
            print(f"   {len(projects)} proje bulundu (responsible_instructor_id olan)")
            
            # Mevcut instructorları al
            print("\n[2] Instructorlar getiriliyor...")
            result = await db.execute(text("""
                SELECT id, name, role 
                FROM instructors 
                ORDER BY id
            """))
            instructors = result.fetchall()
            print(f"   {len(instructors)} instructor bulundu")
            
            # Instructor tiplerini ayır (role kolonuna göre)
            faculty = [i for i in instructors if i[2] and 'instructor' in i[2].lower()]
            assistants = [i for i in instructors if i[2] and 'assistant' in i[2].lower()]
            
            print(f"   - Faculty: {len(faculty)}")
            print(f"   - Assistants: {len(assistants)}")
            
            # Mevcut kayıtları kontrol et
            result = await db.execute(text("SELECT COUNT(*) FROM project_instructor"))
            existing_count = result.scalar()
            
            if existing_count > 0:
                print(f"\n[UYARI] Veritabanında zaten {existing_count} kayıt var.")
                response = input("Mevcut kayıtları silip yeniden mi eklemek istiyorsunuz? (E/H): ")
                
                if response.upper() == 'E':
                    await db.execute(text("DELETE FROM project_instructor"))
                    await db.commit()
                    print("[OK] Mevcut kayıtlar silindi.\n")
                else:
                    print("[IPTAL] İşlem iptal edildi.")
                    return
            
            # Her projeye instructor ata
            print("\n[3] Project-Instructor ilişkileri oluşturuluyor...")
            added_count = 0
            
            for idx, project in enumerate(projects, 1):
                project_id = project[0]
                project_type = project[2]
                responsible_id = project[3]
                
                # Sorumlu instructor her zaman eklenir
                instructors_for_project = [responsible_id]
                
                # Proje tipine göre ek instructor'lar ekle
                if project_type in ['bitirme', 'final']:
                    # Bitirme projesi: 2-3 instructor (1 sorumlu + 1-2 ek)
                    # Sorumlu harici faculty seç
                    available_faculty = [f[0] for f in faculty if f[0] != responsible_id]
                    if available_faculty:
                        num_additional = min(random.randint(1, 2), len(available_faculty))
                        additional = random.sample(available_faculty, num_additional)
                        instructors_for_project.extend(additional)
                
                elif project_type in ['ara', 'interim']:
                    # Ara proje: 1-2 instructor (1 sorumlu + 0-1 ek)
                    # Bazen assistant ekle
                    if assistants and random.random() > 0.5:
                        instructors_for_project.append(random.choice(assistants)[0])
                
                # Dublikasyonları temizle
                instructors_for_project = list(set(instructors_for_project))
                
                # İlişkileri ekle
                for instructor_id in instructors_for_project:
                    await db.execute(text("""
                        INSERT INTO project_instructor (project_id, instructor_id)
                        VALUES (:project_id, :instructor_id)
                    """), {"project_id": project_id, "instructor_id": instructor_id})
                    added_count += 1
                
                if idx % 20 == 0:
                    print(f"   {idx}/{len(projects)} proje işlendi...")
            
            # Değişiklikleri kaydet
            await db.commit()
            
            print(f"\n   Tamamlandı: {len(projects)} proje işlendi")
            print("\n" + "=" * 60)
            print(f"[BASARILI] {added_count} ilişki başarıyla eklendi!")
            print("=" * 60)
            
            # İstatistikler
            print("\n[4] İstatistikler:")
            
            # Proje başına ortalama instructor sayısı
            result = await db.execute(text("""
                SELECT 
                    AVG(instructor_count) as avg_instructors,
                    MIN(instructor_count) as min_instructors,
                    MAX(instructor_count) as max_instructors
                FROM (
                    SELECT project_id, COUNT(*) as instructor_count
                    FROM project_instructor
                    GROUP BY project_id
                ) counts
            """))
            stats = result.fetchone()
            print(f"   Proje başına instructor:")
            print(f"   - Ortalama: {stats[0]:.2f}")
            print(f"   - Minimum: {stats[1]}")
            print(f"   - Maksimum: {stats[2]}")
            
            # Instructor başına ortalama proje sayısı
            result = await db.execute(text("""
                SELECT 
                    AVG(project_count) as avg_projects,
                    MIN(project_count) as min_projects,
                    MAX(project_count) as max_projects
                FROM (
                    SELECT instructor_id, COUNT(*) as project_count
                    FROM project_instructor
                    GROUP BY instructor_id
                ) counts
            """))
            stats = result.fetchone()
            print(f"\n   Instructor başına proje:")
            print(f"   - Ortalama: {stats[0]:.2f}")
            print(f"   - Minimum: {stats[1]}")
            print(f"   - Maksimum: {stats[2]}")
            
            # Örnek kayıtlar
            print("\n[5] Örnek kayıtlar:")
            result = await db.execute(text("""
                SELECT 
                    p.id as project_id,
                    p.title,
                    i.id as instructor_id,
                    i.name as instructor_name,
                    i.role as instructor_role
                FROM project_instructor pi
                JOIN projects p ON pi.project_id = p.id
                JOIN instructors i ON pi.instructor_id = i.id
                ORDER BY p.id, i.id
                LIMIT 10
            """))
            
            samples = result.fetchall()
            for sample in samples:
                print(f"   Proje {sample[0]:3d} ({sample[1][:30]:30s}) -> {sample[3]} ({sample[4]})")
            
            print("\n" + "=" * 60)
            print("[OK] project_instructor tablosu başarıyla dolduruldu!")
            print("=" * 60)
            
        except Exception as e:
            await db.rollback()
            print(f"\n[HATA] İlişkiler eklenirken hata oluştu:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


async def main():
    """Ana fonksiyon"""
    try:
        success = await populate_project_instructor()
        return 0 if success else 1
    except Exception as e:
        print(f"\n[HATA] Script çalıştırılırken hata oluştu:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[IPTAL] İşlem kullanıcı tarafından iptal edildi.")
        sys.exit(1)

