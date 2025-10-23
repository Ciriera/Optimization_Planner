"""
Projects tablosunu model ile senkronize eden script
"""
import asyncio
import sys

sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.base import async_session


async def fix_projects_schema():
    """Projects tablosuna eksik kolonları ekle"""
    
    print("=" * 60)
    print("PROJECTS SCHEMA FIX SCRIPT")
    print("=" * 60)
    
    async with async_session() as db:
        try:
            # Mevcut tablo yapısını kontrol et
            print("\n[1] Mevcut tablo yapısı kontrol ediliyor...")
            result = await db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'projects'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print(f"\n   Mevcut kolonlar:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")
            
            column_names = [col[0] for col in columns]
            
            # Eksik kolonları ekle
            updates = []
            
            # description kolonu
            if 'description' not in column_names:
                print("\n[2] description kolonu ekleniyor...")
                await db.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN IF NOT EXISTS description TEXT
                """))
                updates.append("description")
            
            # student_capacity kolonu
            if 'student_capacity' not in column_names:
                print("\n[3] student_capacity kolonu ekleniyor...")
                await db.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN IF NOT EXISTS student_capacity INTEGER DEFAULT 1
                """))
                updates.append("student_capacity")
            
            # is_active kolonu
            if 'is_active' not in column_names:
                print("\n[4] is_active kolonu ekleniyor...")
                await db.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
                """))
                updates.append("is_active")
            
            # advisor_id kolonu (geriye uyumluluk)
            if 'advisor_id' not in column_names:
                print("\n[5] advisor_id kolonu ekleniyor...")
                await db.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN IF NOT EXISTS advisor_id INTEGER REFERENCES instructors(id)
                """))
                updates.append("advisor_id")
            
            # co_advisor_id kolonu (geriye uyumluluk)
            if 'co_advisor_id' not in column_names:
                print("\n[6] co_advisor_id kolonu ekleniyor...")
                await db.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN IF NOT EXISTS co_advisor_id INTEGER REFERENCES instructors(id)
                """))
                updates.append("co_advisor_id")
            
            if updates:
                await db.commit()
                print(f"\n   [OK] {len(updates)} kolon eklendi: {', '.join(updates)}")
            else:
                print("\n   [INFO] Tüm kolonlar zaten mevcut")
            
            # Güncellenmiş tablo yapısını göster
            print("\n[7] Güncellenmiş tablo yapısı:")
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'projects'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            for col in columns:
                nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                print(f"   - {col[0]:30s}: {col[1]:25s} ({nullable})")
            
            print("\n" + "=" * 60)
            print("[BASARILI] Projects schema güncellendi!")
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
        success = await fix_projects_schema()
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

