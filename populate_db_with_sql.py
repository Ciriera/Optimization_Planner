#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL veritabanina SQL ile hoca ve proje verilerini ekleyen script.
"""
import os
import sys
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


def create_database_url():
    """PostgreSQL connection URL olustur."""
    return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"


def populate_database():
    """Veritabanini hoca ve proje verileriyle doldur."""
    
    DATABASE_URL = create_database_url()
    print(f"[DB] Veritabanina baglaniliyor: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Transaction basla
        trans = conn.begin()
        
        try:
            # Mevcut verileri temizle
            print("\n[CLEAN] Mevcut veriler temizleniyor...")
            conn.execute(text("DELETE FROM projects"))
            conn.execute(text("DELETE FROM instructors"))
            
            # 21 Hoca Ekle
            print("\n[INSTRUCTOR] 21 Hoca ekleniyor...")
            departments = ["Bilgisayar Muhendisligi", "Yazilim Muhendisligi", "Endustri Muhendisligi"]
            
            for i in range(1, 22):
                dept = departments[i % len(departments)]
                conn.execute(
                    text("""
                        INSERT INTO instructors (name, role, bitirme_count, ara_count, total_load) 
                        VALUES (:name, :role, :bitirme_count, :ara_count, :total_load)
                    """),
                    {
                        "name": f"Dr. Ogretim Uyesi {i}",
                        "role": "instructor",
                        "bitirme_count": 0,
                        "ara_count": 0,
                        "total_load": 0
                    }
                )
            
            print(f"[OK] 21 hoca basariyla eklendi.")
            
            # Hocalari yukle
            result = conn.execute(text("SELECT id FROM instructors ORDER BY id"))
            instructor_ids = [row[0] for row in result]
            print(f"[LOAD] {len(instructor_ids)} hoca yuklendi.")
            
            # Proje sayilari
            ara_proje_sayisi = 61
            bitirme_proje_sayisi = 39
            toplam_proje = ara_proje_sayisi + bitirme_proje_sayisi
            
            print(f"\n[PROJECT] Proje Dagilimi:")
            print(f"   - Ara Proje: {ara_proje_sayisi}")
            print(f"   - Bitirme Projesi: {bitirme_proje_sayisi}")
            print(f"   - Toplam: {toplam_proje}")
            
            # Uniform dagilim hesaplama
            hoca_sayisi = len(instructor_ids)
            min_proje_per_hoca = toplam_proje // hoca_sayisi
            extra_proje = toplam_proje % hoca_sayisi
            
            print(f"\n[UNIFORM] Uniform Dagilim:")
            print(f"   - Her hocaya minimum: {min_proje_per_hoca} proje")
            print(f"   - {extra_proje} hocaya ekstra 1 proje")
            
            # Ara Projeler Ekle
            print(f"\n[ARA] {ara_proje_sayisi} Ara Proje ekleniyor...")
            current_instructor_index = 0
            instructor_project_counts = {inst_id: 0 for inst_id in instructor_ids}
            
            for i in range(1, ara_proje_sayisi + 1):
                instructor_id = instructor_ids[current_instructor_index % hoca_sayisi]
                
                conn.execute(
                    text("""
                        INSERT INTO projects (title, type, is_makeup, responsible_instructor_id, status) 
                        VALUES (:title, :type, :is_makeup, :instructor_id, :status)
                    """),
                    {
                        "title": f"Ara Proje {i}",
                        "type": "INTERIM",
                        "is_makeup": False,
                        "instructor_id": instructor_id,
                        "status": "ACTIVE"
                    }
                )
                
                instructor_project_counts[instructor_id] += 1
                current_instructor_index += 1
            
            print(f"[OK] {ara_proje_sayisi} ara proje basariyla eklendi.")
            
            # Bitirme Projeleri Ekle
            print(f"\n[BITIRME] {bitirme_proje_sayisi} Bitirme Projesi ekleniyor...")
            
            for i in range(1, bitirme_proje_sayisi + 1):
                instructor_id = instructor_ids[current_instructor_index % hoca_sayisi]
                
                conn.execute(
                    text("""
                        INSERT INTO projects (title, type, is_makeup, responsible_instructor_id, status) 
                        VALUES (:title, :type, :is_makeup, :instructor_id, :status)
                    """),
                    {
                        "title": f"Bitirme Projesi {i}",
                        "type": "FINAL",
                        "is_makeup": False,
                        "instructor_id": instructor_id,
                        "status": "ACTIVE"
                    }
                )
                
                instructor_project_counts[instructor_id] += 1
                current_instructor_index += 1
            
            print(f"[OK] {bitirme_proje_sayisi} bitirme projesi basariyla eklendi.")
            
            # Hoca sayaclarini guncelle
            print("\n[UPDATE] Hoca sayaclari guncelleniyor...")
            for inst_id in instructor_ids:
                # Ara ve bitirme proje sayilarini hesapla
                ara_result = conn.execute(
                    text("SELECT COUNT(*) FROM projects WHERE responsible_instructor_id = :id AND type = 'INTERIM'"),
                    {"id": inst_id}
                )
                ara_count = ara_result.scalar()
                
                bitirme_result = conn.execute(
                    text("SELECT COUNT(*) FROM projects WHERE responsible_instructor_id = :id AND type = 'FINAL'"),
                    {"id": inst_id}
                )
                bitirme_count = bitirme_result.scalar()
                
                total_load = ara_count + bitirme_count
                
                conn.execute(
                    text("""
                        UPDATE instructors 
                        SET ara_count = :ara_count, bitirme_count = :bitirme_count, total_load = :total_load
                        WHERE id = :id
                    """),
                    {
                        "id": inst_id,
                        "ara_count": ara_count,
                        "bitirme_count": bitirme_count,
                        "total_load": total_load
                    }
                )
            
            print("[OK] Hoca sayaclari guncellendi.")
            
            # Istatistikleri Goster
            print("\n" + "="*60)
            print("VERITABANI DOLDURMA ISTATISTIKLERI")
            print("="*60)
            
            print(f"\n[STATS] Hoca Istatistikleri:")
            print(f"{'Hoca Adi':<30} {'Toplam':<10} {'Ara':<10} {'Bitirme':<10}")
            print("-" * 60)
            
            result = conn.execute(text("SELECT name, total_load, ara_count, bitirme_count FROM instructors ORDER BY id"))
            for row in result:
                print(f"{row[0]:<30} {row[1]:<10} {row[2]:<10} {row[3]:<10}")
            
            # Proje istatistikleri
            total_projects_result = conn.execute(text("SELECT COUNT(*) FROM projects"))
            total_projects = total_projects_result.scalar()
            
            ara_projects_result = conn.execute(text("SELECT COUNT(*) FROM projects WHERE type = 'INTERIM'"))
            ara_projects = ara_projects_result.scalar()
            
            bitirme_projects_result = conn.execute(text("SELECT COUNT(*) FROM projects WHERE type = 'FINAL'"))
            bitirme_projects = bitirme_projects_result.scalar()
            
            print("\n" + "="*60)
            print(f"[TOTAL] Toplam Proje Sayisi: {total_projects}")
            print(f"   - Ara Proje: {ara_projects}")
            print(f"   - Bitirme Projesi: {bitirme_projects}")
            print("="*60)
            
            # Dagilim kontrolu
            project_counts = list(instructor_project_counts.values())
            print(f"\n[ANALYSIS] Uniform Dagilim Kontrolu:")
            print(f"   - Minimum proje/hoca: {min(project_counts)}")
            print(f"   - Maksimum proje/hoca: {max(project_counts)}")
            print(f"   - Ortalama proje/hoca: {sum(project_counts)/len(project_counts):.2f}")
            print(f"   - Standart sapma: {(sum((x - sum(project_counts)/len(project_counts))**2 for x in project_counts) / len(project_counts))**0.5:.2f}")
            
            # Transaction'i commit et
            trans.commit()
            print("\n[SUCCESS] Veritabani basariyla dolduruldu!")
            
        except Exception as e:
            print(f"\n[ERROR] Hata olustu: {e}")
            trans.rollback()
            raise


if __name__ == "__main__":
    print("PostgreSQL Veritabani Doldurma Islemi (SQL)")
    print("="*60)
    populate_database()

