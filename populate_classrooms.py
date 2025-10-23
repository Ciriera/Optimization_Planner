"""
PostgreSQL veritabanına classroom'ları ekleyen script
"""
import asyncio
import sys

# Add parent directory to path
sys.path.insert(0, '.')

from sqlalchemy import text, select
from app.db.base import async_session
from app.models.classroom import Classroom


async def populate_classrooms():
    """Veritabanına classroom'ları ekle"""
    
    # Classroom verileri
    classrooms_data = [
        {"name": "D105", "capacity": 3, "is_active": True},
        {"name": "D106", "capacity": 3, "is_active": True},
        {"name": "D107", "capacity": 3, "is_active": True},
        {"name": "D108", "capacity": 3, "is_active": True},
        {"name": "D109", "capacity": 3, "is_active": True},
        {"name": "D110", "capacity": 3, "is_active": True},
        {"name": "D111", "capacity": 3, "is_active": True},
    ]
    
    print("=" * 60)
    print("CLASSROOM POPULATION SCRIPT")
    print("=" * 60)
    print(f"\nToplam {len(classrooms_data)} classroom eklenecek...\n")
    
    async with async_session() as db:
        try:
            # Önce mevcut classroom'ları kontrol et
            result = await db.execute(select(Classroom))
            existing_classrooms = result.scalars().all()
            
            if existing_classrooms:
                print(f"[UYARI] Veritabanında zaten {len(existing_classrooms)} classroom var.")
                response = input("Mevcut classroom'ları silip yeniden mi eklemek istiyorsunuz? (E/H): ")
                
                if response.upper() == 'E':
                    # Mevcut classroom'ları sil
                    await db.execute(text("DELETE FROM classrooms"))
                    await db.commit()
                    print("[OK] Mevcut classroom'lar silindi.\n")
                else:
                    print("[IPTAL] İşlem iptal edildi.")
                    return
            
            # Yeni classroom'ları ekle
            added_count = 0
            
            for idx, classroom_data in enumerate(classrooms_data, 1):
                classroom = Classroom(
                    name=classroom_data["name"],
                    capacity=classroom_data["capacity"],
                    is_active=classroom_data["is_active"]
                )
                
                db.add(classroom)
                print(f"[{idx}] Ekleniyor: {classroom_data['name']} (Kapasite: {classroom_data['capacity']})")
                added_count += 1
            
            # Değişiklikleri kaydet
            await db.commit()
            
            print("\n" + "=" * 60)
            print(f"[BASARILI] {added_count} classroom başarıyla eklendi!")
            print("=" * 60)
            
            # Eklenen classroom'ları doğrula
            result = await db.execute(select(Classroom).order_by(Classroom.id))
            all_classrooms = result.scalars().all()
            
            print(f"\n[DOGRULAMA] Veritabanında toplam {len(all_classrooms)} classroom var:\n")
            
            for classroom in all_classrooms:
                status = "Aktif" if classroom.is_active else "Pasif"
                print(f"   ID: {classroom.id:2d} | {classroom.name:5s} | Kapasite: {classroom.capacity} | {status}")
            
            print("\n" + "=" * 60)
            print("[OK] Classroom'lar başarıyla veritabanına eklendi!")
            print("=" * 60)
            
        except Exception as e:
            await db.rollback()
            print(f"\n[HATA] Classroom'lar eklenirken hata oluştu:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


async def main():
    """Ana fonksiyon"""
    try:
        success = await populate_classrooms()
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
    except Exception as e:
        print(f"\n\n[HATA] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

