#!/usr/bin/env python3
import asyncio
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import async_session
from sqlalchemy import text

async def check():
    async with async_session() as db:
        # Proje tiplerini kontrol et
        result = await db.execute(text("SELECT DISTINCT type::text FROM projects LIMIT 10"))
        types = [r[0] for r in result.fetchall()]
        print(f"Proje tipleri: {types}")
        
        # Toplam proje sayısı
        result = await db.execute(text("SELECT COUNT(*) FROM projects WHERE is_active = true"))
        total = result.scalar()
        print(f"Toplam aktif proje: {total}")
        
        # Tip bazında sayılar
        result = await db.execute(text("""
            SELECT type::text, COUNT(*) 
            FROM projects 
            WHERE is_active = true
            GROUP BY type
        """))
        counts = result.fetchall()
        print(f"Tip bazında sayılar: {counts}")
        
        # NULL olan projeler
        result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM projects 
            WHERE responsible_instructor_id IS NULL AND is_active = true
        """))
        null_count = result.scalar()
        print(f"Atanmamış proje sayısı: {null_count}")

asyncio.run(check())













