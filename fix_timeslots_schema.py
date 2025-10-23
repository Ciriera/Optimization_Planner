"""
Timeslots tablosunu model ile senkronize eden script
"""
import asyncio
import sys

sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.base import async_session


async def fix_timeslots_schema():
    """Timeslots tablosuna eksik kolonları ekle"""
    
    print("=" * 60)
    print("TIMESLOTS SCHEMA FIX SCRIPT")
    print("=" * 60)
    
    async with async_session() as db:
        try:
            # Mevcut tablo yapısını kontrol et
            print("\n[1] Mevcut tablo yapısı kontrol ediliyor...")
            result = await db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'timeslots'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print(f"\n   Mevcut kolonlar:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")
            
            column_names = [col[0] for col in columns]
            
            # session_type kolonu var mı kontrol et
            if 'session_type' not in column_names:
                print("\n[2] session_type kolonu bulunamadı, ekleniyor...")
                
                # Enum type oluştur
                await db.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE sessiontype AS ENUM ('morning', 'break', 'afternoon');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # Kolonu ekle
                await db.execute(text("""
                    ALTER TABLE timeslots 
                    ADD COLUMN IF NOT EXISTS session_type sessiontype
                """))
                
                await db.commit()
                print("   [OK] session_type kolonu eklendi (nullable)")
                
            else:
                print("\n[2] session_type kolonu zaten mevcut")
            
            # is_morning kolonu var mı kontrol et
            if 'is_morning' not in column_names:
                print("\n[3] is_morning kolonu bulunamadı, ekleniyor...")
                await db.execute(text("""
                    ALTER TABLE timeslots 
                    ADD COLUMN IF NOT EXISTS is_morning BOOLEAN
                """))
                await db.commit()
                print("   [OK] is_morning kolonu eklendi")
            else:
                print("\n[3] is_morning kolonu zaten mevcut")
            
            # is_active kolonu var mı kontrol et
            if 'is_active' not in column_names:
                print("\n[4] is_active kolonu bulunamadı, ekleniyor...")
                await db.execute(text("""
                    ALTER TABLE timeslots 
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
                """))
                await db.commit()
                print("   [OK] is_active kolonu eklendi")
            else:
                print("\n[4] is_active kolonu zaten mevcut")
            
            # Güncellenmiş tablo yapısını göster
            print("\n[5] Güncellenmiş tablo yapısı:")
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'timeslots'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            for col in columns:
                nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                print(f"   - {col[0]}: {col[1]} ({nullable})")
            
            print("\n" + "=" * 60)
            print("[BASARILI] Schema güncellendi!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"\n[HATA] Schema güncellenirken hata oluştu:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Ana fonksiyon"""
    try:
        success = await fix_timeslots_schema()
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

