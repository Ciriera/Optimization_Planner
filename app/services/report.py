from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pandas as pd

from app.models.instructor import Instructor
from app.models.project import Project
from app.models.schedule import Schedule
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot

class ReportService:
    async def get_load_distribution(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Öğretim elemanlarının yük dağılımını hesaplar.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Yük dağılım istatistikleri
        """
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        # Yük bilgilerini topla
        loads = {
            "hoca": [],
            "aras_gor": []
        }
        
        for instructor in instructors:
            if instructor.role == "hoca":
                loads["hoca"].append({
                    "id": instructor.id,
                    "name": instructor.full_name,
                    "bitirme_count": instructor.bitirme_count,
                    "ara_count": instructor.ara_count,
                    "total_load": instructor.total_load,
                    "responsible_projects_count": len(instructor.projects),
                    "assistant_projects_count": len(instructor.assisted_projects) if hasattr(instructor, "assisted_projects") else 0
                })
            else:
                loads["aras_gor"].append({
                    "id": instructor.id,
                    "name": instructor.full_name,
                    "bitirme_count": instructor.bitirme_count,
                    "ara_count": instructor.ara_count,
                    "total_load": instructor.total_load,
                    "responsible_projects_count": len(instructor.projects),
                    "assistant_projects_count": len(instructor.assisted_projects) if hasattr(instructor, "assisted_projects") else 0
                })
        
        # İstatistikleri hesapla
        stats = {
            "hoca": self._calculate_statistics([i["total_load"] for i in loads["hoca"]]),
            "aras_gor": self._calculate_statistics([i["total_load"] for i in loads["aras_gor"]]),
            "overall": self._calculate_statistics([i["total_load"] for i in loads["hoca"] + loads["aras_gor"]])
        }
        
        # Gini katsayısını hesapla
        if loads["hoca"]:
            stats["hoca"]["gini"] = self._calculate_gini([i["total_load"] for i in loads["hoca"]])
        if loads["aras_gor"]:
            stats["aras_gor"]["gini"] = self._calculate_gini([i["total_load"] for i in loads["aras_gor"]])
        if loads["hoca"] + loads["aras_gor"]:
            stats["overall"]["gini"] = self._calculate_gini([i["total_load"] for i in loads["hoca"] + loads["aras_gor"]])
        
        return {
            "loads": loads,
            "statistics": stats
        }

    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        Bir değer listesi için temel istatistikleri hesaplar.
        
        Args:
            values: Değer listesi
            
        Returns:
            İstatistik değerleri
        """
        if not values:
            return {
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "std": 0,
                "count": 0
            }
        
        return {
            "min": float(min(values)),
            "max": float(max(values)),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "count": len(values)
        }

    def _calculate_gini(self, values: List[float]) -> float:
        """
        Gini katsayısını hesaplar (eşitsizlik ölçüsü).
        
        Args:
            values: Değer listesi
            
        Returns:
            Gini katsayısı (0-1 arasında, 0: tam eşitlik, 1: tam eşitsizlik)
        """
        if not values:
            return 0
        
        # Tüm değerler 0 ise, tam eşitlik var demektir
        if all(v == 0 for v in values):
            return 0
        
        # Değerleri sırala
        values = sorted(values)
        n = len(values)
        
        # Lorenz eğrisi için kümülatif toplam
        cum_values = np.cumsum(values)
        
        # Gini katsayısı hesaplama
        gini = (n + 1 - 2 * np.sum(cum_values) / cum_values[-1]) / n
        
        return float(gini)

    async def generate_schedule_pdf(self, db: AsyncSession) -> bytes:
        """
        PDF formatında atama planı raporu oluşturur.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            PDF verisi (bytes)
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Stil ve içerik hazırlama
        styles = getSampleStyleSheet()
        elements = []
        
        # Başlık
        title = Paragraph(f"Proje Atama Planı - {datetime.now().strftime('%d.%m.%Y')}", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Açıklama
        description = Paragraph("Bu rapor, projelerin sınıf ve zaman dilimlerine göre atama planını içerir.", styles['Normal'])
        elements.append(description)
        elements.append(Spacer(1, 20))
        
        # Verileri al
        result = await db.execute(select(Schedule).order_by(Schedule.classroom_id, Schedule.timeslot_id))
        schedules = result.scalars().all()
        
        # Tablo verileri
        data = [["Proje ID", "Proje Türü", "Sınıf", "Saat", "Katılımcılar", "Durum"]]
        
        for schedule in schedules:
            project = schedule.project
            classroom = schedule.classroom
            timeslot = schedule.timeslot
            instructors = schedule.instructors
            
            instructor_names = ", ".join([i.full_name for i in instructors])
            time_str = f"{timeslot.start_time.strftime('%H:%M')} - {timeslot.end_time.strftime('%H:%M')}"
            project_type = "Bitirme" if project.type == "bitirme" else "Ara"
            status = "Final" if not project.is_makeup else "Bütünleme"
            
            data.append([
                str(project.id),
                project_type,
                classroom.name,
                time_str,
                instructor_names,
                status
            ])
        
        # Tablo oluştur
        table = Table(data)
        
        # Tablo stili
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Bitirme projeleri için mavi, ara projeler için sarı renk
        for i in range(1, len(data)):
            if data[i][1] == "Bitirme":
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightblue)
            else:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightyellow)
            
            # Bütünleme projeleri için gri renk
            if data[i][5] == "Bütünleme":
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        
        table.setStyle(table_style)
        elements.append(table)
        
        # PDF oluştur
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    async def generate_schedule_excel(self, db: AsyncSession) -> bytes:
        """
        Excel formatında atama planı raporu oluşturur.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Excel verisi (bytes)
        """
        # Verileri al
        result = await db.execute(select(Schedule).order_by(Schedule.classroom_id, Schedule.timeslot_id))
        schedules = result.scalars().all()
        
        # Excel dosyası için veri hazırlama
        data = []
        for schedule in schedules:
            project = schedule.project
            classroom = schedule.classroom
            timeslot = schedule.timeslot
            instructors = schedule.instructors
            
            instructor_names = ", ".join([i.full_name for i in instructors])
            project_type = "Bitirme" if project.type == "bitirme" else "Ara"
            status = "Final" if not project.is_makeup else "Bütünleme"
            
            data.append({
                "Proje ID": project.id,
                "Proje Türü": project_type,
                "Sınıf": classroom.name,
                "Başlangıç Saati": timeslot.start_time.strftime("%H:%M"),
                "Bitiş Saati": timeslot.end_time.strftime("%H:%M"),
                "Katılımcılar": instructor_names,
                "Sorumlu": project.responsible.full_name if project.responsible else "",
                "Durum": status
            })
        
        # Yük dağılımı verilerini al
        distribution = await self.get_load_distribution(db)
        
        # DataFrame oluştur
        df_schedule = pd.DataFrame(data)
        
        # Hocalar için DataFrame
        df_hocalar = pd.DataFrame(distribution["loads"]["hoca"])
        
        # Araştırma görevlileri için DataFrame
        df_aras_gor = pd.DataFrame(distribution["loads"]["aras_gor"])
        
        # İstatistikler için DataFrame
        stats = distribution["statistics"]
        stat_data = {
            "Grup": ["Hocalar", "Araş. Gör.", "Genel"],
            "Min Yük": [stats["hoca"]["min"], stats["aras_gor"]["min"], stats["overall"]["min"]],
            "Max Yük": [stats["hoca"]["max"], stats["aras_gor"]["max"], stats["overall"]["max"]],
            "Ortalama Yük": [stats["hoca"]["mean"], stats["aras_gor"]["mean"], stats["overall"]["mean"]],
            "Medyan Yük": [stats["hoca"]["median"], stats["aras_gor"]["median"], stats["overall"]["median"]],
            "Standart Sapma": [stats["hoca"]["std"], stats["aras_gor"]["std"], stats["overall"]["std"]],
            "Gini Katsayısı": [
                stats["hoca"].get("gini", 0), 
                stats["aras_gor"].get("gini", 0), 
                stats["overall"].get("gini", 0)
            ]
        }
        df_stats = pd.DataFrame(stat_data)
        
        # Excel dosyasını oluştur
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Planlama tablosu
            df_schedule.to_excel(writer, sheet_name='Atama Planı', index=False)
            
            # Hocalar tablosu
            if not df_hocalar.empty:
                df_hocalar.to_excel(writer, sheet_name='Hoca Yükleri', index=False)
            
            # Araştırma görevlileri tablosu
            if not df_aras_gor.empty:
                df_aras_gor.to_excel(writer, sheet_name='Araş.Gör. Yükleri', index=False)
            
            # İstatistikler tablosu
            df_stats.to_excel(writer, sheet_name='İstatistikler', index=False)
            
            # Biçimlendirme
            workbook = writer.book
            
            # Atama planı sayfası için
            worksheet = writer.sheets['Atama Planı']
            header_format = workbook.add_format({'bold': True, 'bg_color': '#CCCCCC', 'border': 1})
            
            # Başlık formatı
            for col_num, value in enumerate(df_schedule.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Sütun genişliklerini ayarla
            for i, col in enumerate(df_schedule.columns):
                column_width = max(df_schedule[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
            
            # Bitirme projelerini mavi, ara projeleri sarı renk ile belirt
            bitirme_format = workbook.add_format({'bg_color': '#CCEEFF'})
            ara_format = workbook.add_format({'bg_color': '#FFFFCC'})
            makeup_format = workbook.add_format({'bg_color': '#DDDDDD'})
            
            for row_num in range(1, len(df_schedule) + 1):
                if df_schedule.iloc[row_num-1]["Proje Türü"] == "Bitirme":
                    worksheet.set_row(row_num, None, bitirme_format)
                else:
                    worksheet.set_row(row_num, None, ara_format)
                    
                if df_schedule.iloc[row_num-1]["Durum"] == "Bütünleme":
                    worksheet.set_row(row_num, None, makeup_format)
            
            # İstatistikler sayfası için biçimlendirme
            if 'İstatistikler' in writer.sheets:
                worksheet = writer.sheets['İstatistikler']
                for i, col in enumerate(df_stats.columns):
                    column_width = max(df_stats[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_width)
                
                # Başlık formatı
                for col_num, value in enumerate(df_stats.columns.values):
                    worksheet.write(0, col_num, value, header_format)
        
        buffer.seek(0)
        return buffer.getvalue() 