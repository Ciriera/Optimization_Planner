from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import pandas as pd
import io
from datetime import datetime

from app import crud, models, schemas
from app.api import deps
from app.services.report import generate_load_distribution, generate_schedule_report

router = APIRouter()


@router.get("/load-distribution")
def get_load_distribution(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Tüm öğretim elemanlarının yük dağılım istatistiklerini getirir.
    """
    distribution = generate_load_distribution(db)
    return {
        "status": "success",
        "data": distribution,
        "message": "Yük dağılımı başarıyla getirildi."
    }


@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Atama planını PDF formatında dışa aktarır.
    """
    try:
        pdf_data = generate_schedule_report(db, format="pdf")
        
        response = Response(content=pdf_data, media_type="application/pdf")
        response.headers["Content-Disposition"] = f"attachment; filename=schedule_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return response
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"PDF oluşturma hatası: {str(e)}"
        }


@router.get("/export/excel")
def export_excel(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Atama planını Excel formatında dışa aktarır.
    """
    try:
        # Verileri al
        schedules = crud.schedule.get_multi(db)
        
        # Excel dosyasını oluştur
        output = io.BytesIO()
        
        # Veri çerçevesi oluştur
        data = []
        for schedule in schedules:
            project = schedule.project
            classroom = schedule.classroom
            timeslot = schedule.timeslot
            instructors = schedule.instructors
            
            instructor_names = ", ".join([i.name for i in instructors])
            
            data.append({
                "Proje ID": project.id,
                "Proje Başlığı": project.title,
                "Proje Türü": project.type.value,
                "Sınıf": classroom.name,
                "Başlangıç Saati": timeslot.start_time.strftime("%H:%M"),
                "Bitiş Saati": timeslot.end_time.strftime("%H:%M"),
                "Katılımcılar": instructor_names,
                "Sorumlu": project.responsible_instructor.name,
                "Durum": project.status.value
            })
        
        df = pd.DataFrame(data)
        
        # Excel'e yaz
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Atama Planı', index=False)
            
            # Sütun genişliklerini ayarla
            worksheet = writer.sheets['Atama Planı']
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
        
        output.seek(0)
        
        response = Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response.headers["Content-Disposition"] = f"attachment; filename=schedule_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return response
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Excel oluşturma hatası: {str(e)}"
        } 