from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

from app import crud, models


def generate_load_distribution(db: Session) -> Dict[str, Any]:
    """
    Öğretim elemanlarının yük dağılımını hesaplar.
    
    Args:
        db: Veritabanı oturumu
        
    Returns:
        Yük dağılım istatistikleri
    """
    instructors = crud.instructor.get_multi(db)
    
    # Yük bilgilerini topla
    loads = {
        "hoca": [],
        "aras_gor": []
    }
    
    for instructor in instructors:
        if instructor.role == "hoca":
            loads["hoca"].append({
                "id": instructor.id,
                "name": instructor.name,
                "bitirme_count": instructor.bitirme_count,
                "ara_count": instructor.ara_count,
                "total_load": instructor.total_load,
                "responsible_projects_count": len(instructor.projects),
                "assistant_projects_count": len(instructor.assisted_projects)
            })
        else:
            loads["aras_gor"].append({
                "id": instructor.id,
                "name": instructor.name,
                "bitirme_count": instructor.bitirme_count,
                "ara_count": instructor.ara_count,
                "total_load": instructor.total_load,
                "responsible_projects_count": len(instructor.projects),
                "assistant_projects_count": len(instructor.assisted_projects)
            })
    
    # İstatistikleri hesapla
    stats = {
        "hoca": calculate_statistics([i["total_load"] for i in loads["hoca"]]),
        "aras_gor": calculate_statistics([i["total_load"] for i in loads["aras_gor"]]),
        "overall": calculate_statistics([i["total_load"] for i in loads["hoca"] + loads["aras_gor"]])
    }
    
    # Gini katsayısını hesapla
    if loads["hoca"]:
        stats["hoca"]["gini"] = calculate_gini([i["total_load"] for i in loads["hoca"]])
    if loads["aras_gor"]:
        stats["aras_gor"]["gini"] = calculate_gini([i["total_load"] for i in loads["aras_gor"]])
    if loads["hoca"] + loads["aras_gor"]:
        stats["overall"]["gini"] = calculate_gini([i["total_load"] for i in loads["hoca"] + loads["aras_gor"]])
    
    return {
        "loads": loads,
        "statistics": stats
    }


def calculate_statistics(values: List[float]) -> Dict[str, float]:
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


def calculate_gini(values: List[float]) -> float:
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


def generate_schedule_report(db: Session, format: str = "pdf") -> bytes:
    """
    Atama planı raporu oluşturur.
    
    Args:
        db: Veritabanı oturumu
        format: Rapor formatı ("pdf" veya "excel")
        
    Returns:
        Rapor verisi (bytes)
    """
    if format == "pdf":
        return generate_pdf_report(db)
    else:
        raise ValueError(f"Desteklenmeyen format: {format}")


def generate_pdf_report(db: Session) -> bytes:
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
    schedules = crud.schedule.get_multi(db)
    
    # Tablo verileri
    data = [["Proje ID", "Proje Başlığı", "Tür", "Sınıf", "Saat", "Katılımcılar", "Durum"]]
    
    for schedule in schedules:
        project = schedule.project
        classroom = schedule.classroom
        timeslot = schedule.timeslot
        instructors = schedule.instructors
        
        instructor_names = ", ".join([i.name for i in instructors])
        time_str = f"{timeslot.start_time.strftime('%H:%M')} - {timeslot.end_time.strftime('%H:%M')}"
        
        data.append([
            str(project.id),
            project.title,
            project.type.value,
            classroom.name,
            time_str,
            instructor_names,
            project.status.value
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
        if data[i][2] == "FINAL":
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightblue)
        else:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightyellow)
        
        # Bütünleme projeleri için gri renk
        if data[i][6] == "MAKEUP":
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Yük dağılımı özeti
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Yük Dağılımı Özeti", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    distribution = generate_load_distribution(db)
    stats = distribution["statistics"]
    
    # Yük dağılımı tablosu
    load_data = [
        ["Grup", "Min", "Max", "Ortalama", "Medyan", "Std. Sapma", "Gini"],
        ["Öğretim Üyeleri", 
         f"{stats['hoca']['min']:.1f}", 
         f"{stats['hoca']['max']:.1f}", 
         f"{stats['hoca']['mean']:.1f}", 
         f"{stats['hoca']['median']:.1f}", 
         f"{stats['hoca']['std']:.2f}", 
         f"{stats['hoca'].get('gini', 0):.3f}"],
        ["Araştırma Görevlileri", 
         f"{stats['aras_gor']['min']:.1f}", 
         f"{stats['aras_gor']['max']:.1f}", 
         f"{stats['aras_gor']['mean']:.1f}", 
         f"{stats['aras_gor']['median']:.1f}", 
         f"{stats['aras_gor']['std']:.2f}", 
         f"{stats['aras_gor'].get('gini', 0):.3f}"],
        ["Genel", 
         f"{stats['overall']['min']:.1f}", 
         f"{stats['overall']['max']:.1f}", 
         f"{stats['overall']['mean']:.1f}", 
         f"{stats['overall']['median']:.1f}", 
         f"{stats['overall']['std']:.2f}", 
         f"{stats['overall'].get('gini', 0):.3f}"]
    ]
    
    load_table = Table(load_data)
    load_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ])
    load_table.setStyle(load_table_style)
    elements.append(load_table)
    
    # Altbilgi
    elements.append(Spacer(1, 30))
    footer_text = f"Bu rapor {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} tarihinde otomatik olarak oluşturulmuştur."
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)
    
    # PDF oluştur
    doc.build(elements)
    buffer.seek(0)
    
    return buffer.getvalue() 