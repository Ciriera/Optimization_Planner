"""
PostgreSQL veritabanına timeslot'ları ekleyen script
"""
import asyncio
import sys
from datetime import time as dt_time

# Add parent directory to path
sys.path.insert(0, '.')

from sqlalchemy import text, select
from app.core.database import async_engine
from app.db.base import async_session
from app.models.timeslot import TimeSlot, SessionType


async def populate_timeslots():
    """Veritabanına timeslot'ları ekle"""
    
    # Timeslot verileri
    timeslots_data = [
        # Sabah zaman dilimleri (09:00-12:00)
        {"start_time": "09:00:00", "end_time": "09:30:00", "session_type": SessionType.MORNING, "is_morning": True},
        {"start_time": "09:30:00", "end_time": "10:00:00", "session_type": SessionType.MORNING, "is_morning": True},
        {"start_time": "10:00:00", "end_time": "10:30:00", "session_type": SessionType.MORNING, "is_morning": True},
        {"start_time": "10:30:00", "end_time": "11:00:00", "session_type": SessionType.MORNING, "is_morning": True},
        {"start_time": "11:00:00", "end_time": "11:30:00", "session_type": SessionType.MORNING, "is_morning": True},
        {"start_time": "11:30:00", "end_time": "12:00:00", "session_type": SessionType.MORNING, "is_morning": True},
        
        # Öğle arası 12:00-13:00 yok
        
        # Öğleden sonra zaman dilimleri (13:00-18:00)
        {"start_time": "13:00:00", "end_time": "13:30:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "13:30:00", "end_time": "14:00:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "14:00:00", "end_time": "14:30:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "14:30:00", "end_time": "15:00:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "15:00:00", "end_time": "15:30:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "15:30:00", "end_time": "16:00:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "16:00:00", "end_time": "16:30:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "16:30:00", "end_time": "17:00:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "17:00:00", "end_time": "17:30:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
        {"start_time": "17:30:00", "end_time": "18:00:00", "session_type": SessionType.AFTERNOON, "is_morning": False},
    ]
    
    print("=" * 60)
    print("TIMESLOT POPULATION SCRIPT")
    print("=" * 60)
    print(f"\nToplam {len(timeslots_data)} timeslot eklenecek...\n")
    
    async with async_session() as db:
        try:
            # Önce mevcut timeslot'ları kontrol et
            result = await db.execute(select(TimeSlot))
            existing_timeslots = result.scalars().all()
            
            if existing_timeslots:
                print(f"[UYARI] Veritabanında zaten {len(existing_timeslots)} timeslot var.")
                response = input("Mevcut timeslot'ları silip yeniden mi eklemek istiyorsunuz? (E/H): ")
                
                if response.upper() == 'E':
                    # Mevcut timeslot'ları sil
                    await db.execute(text("DELETE FROM timeslots"))
                    await db.commit()
                    print("[OK] Mevcut timeslot'lar silindi.\n")
                else:
                    print("[IPTAL] İşlem iptal edildi.")
                    return
            
            # Yeni timeslot'ları ekle
            added_count = 0
            
            for idx, ts_data in enumerate(timeslots_data, 1):
                # String'i time objesine dönüştür
                start_hour, start_min = map(int, ts_data["start_time"].split(":")[0:2])
                end_hour, end_min = map(int, ts_data["end_time"].split(":")[0:2])
                
                timeslot = TimeSlot(
                    start_time=dt_time(start_hour, start_min),
                    end_time=dt_time(end_hour, end_min),
                    session_type=ts_data["session_type"],
                    is_morning=ts_data["is_morning"],
                    is_active=True
                )
                
                db.add(timeslot)
                session_label = "Sabah" if ts_data["is_morning"] else "Öğleden Sonra"
                print(f"[{idx:2d}] Ekleniyor: {ts_data['start_time']} - {ts_data['end_time']} ({session_label})")
                added_count += 1
            
            # Değişiklikleri kaydet
            await db.commit()
            
            print("\n" + "=" * 60)
            print(f"[BASARILI] {added_count} timeslot başarıyla eklendi!")
            print("=" * 60)
            
            # Eklenen timeslot'ları doğrula
            result = await db.execute(select(TimeSlot).order_by(TimeSlot.id))
            all_timeslots = result.scalars().all()
            
            print(f"\n[DOGRULAMA] Veritabanında toplam {len(all_timeslots)} timeslot var:\n")
            
            morning_slots = [ts for ts in all_timeslots if ts.is_morning]
            afternoon_slots = [ts for ts in all_timeslots if not ts.is_morning]
            
            print("Sabah Zaman Dilimleri (09:00-12:00):")
            for ts in morning_slots:
                print(f"   ID: {ts.id:2d} | {ts.start_time} - {ts.end_time}")
            
            print("\nÖğleden Sonra Zaman Dilimleri (13:00-18:00):")
            for ts in afternoon_slots:
                print(f"   ID: {ts.id:2d} | {ts.start_time} - {ts.end_time}")
            
            print("\n" + "=" * 60)
            print("[OK] Timeslot'lar başarıyla veritabanına eklendi!")
            print("=" * 60)
            
        except Exception as e:
            await db.rollback()
            print(f"\n[HATA] Timeslot'lar eklenirken hata oluştu:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


async def main():
    """Ana fonksiyon"""
    try:
        success = await populate_timeslots()
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

