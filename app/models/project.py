from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum
from datetime import datetime

class ProjectType(str, enum.Enum):
    INTERIM = "interim"
    FINAL = "final"

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    MAKEUP = "makeup"

# Proje asistanları için ara tablo
project_assistants = Table(
    "project_assistants",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("instructor_id", Integer, ForeignKey("instructors.id"), primary_key=True),
    extend_existing=True
)

# Proje anahtar kelimeleri için ara tablo
project_keyword = Table(
    "project_keyword",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("keyword.id"), primary_key=True),
    extend_existing=True
)

class Project(Base):
    """
    Proje modeli - Proje açıklamasına göre düzenlenmiş.
    Her projede 3 kişi olmalı: 1. kişi (zorunlu hoca), 2. ve 3. kişi (hoca veya araştırma görevlisi)
    """
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    type = Column(Enum(ProjectType), nullable=False)  # "interim" veya "final"
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    student_capacity = Column(Integer, default=1)
    
    # Proje açıklamasına göre 3 kişilik katılımcı sistemi
    # 1. kişi: Zorunlu olarak hoca (sorumlu)
    responsible_instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    
    # Database'de olmayan kolonlar kaldırıldı
    
    # Geriye uyumluluk için eski alanlar
    advisor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    co_advisor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    
    is_makeup = Column(Boolean, default=False)  # True: bütünleme, False: final
    is_active = Column(Boolean, default=True)
    # Database'de olmayan kolonlar kaldırıldı
    
    # İlişkiler
    responsible = relationship("Instructor", foreign_keys=[responsible_instructor_id], back_populates="responsible_projects")
    
    # Geriye uyumluluk için eski ilişkiler
    advisor = relationship("Instructor", foreign_keys=[advisor_id], back_populates="advised_projects")
    co_advisor = relationship("Instructor", foreign_keys=[co_advisor_id], back_populates="co_advised_projects")
    assistants = relationship("Instructor", secondary=project_assistants, back_populates="assistant_projects")
    
    schedules = relationship("Schedule", back_populates="project")
    students = relationship("Student", secondary="project_student", back_populates="projects", lazy="select")
    keywords = relationship("Keyword", secondary=project_keyword, back_populates="projects", lazy="select")
    
    @property
    def participants(self) -> list:
        """
        Proje katılımcılarını döndürür (3 kişi).
        """
        participants = []
        if self.responsible_instructor_id:
            participants.append({
                "id": self.responsible_instructor_id,
                "role": "responsible",
                "instructor": self.responsible
            })
        # Database'de olmayan kolonlar kaldırıldı
        return participants
    
    @property
    def participant_count(self) -> int:
        """Toplam katılımcı sayısı."""
        count = 0
        if self.responsible_instructor_id:
            count += 1
        # Database'de olmayan kolonlar kaldırıldı
        return count
    
    @property
    def instructor_count(self) -> int:
        """Hoca sayısını döndürür."""
        count = 0
        participants = self.participants
        for participant in participants:
            if participant["instructor"] and participant["instructor"].role == "instructor":
                count += 1
        return count
    
    @property
    def research_assistant_count(self) -> int:
        """Araştırma görevlisi sayısını döndürür."""
        count = 0
        participants = self.participants
        for participant in participants:
            if participant["instructor"] and participant["instructor"].role == "research_assistant":
                count += 1
        return count
    
    def is_rule_compliant(self) -> dict:
        """
        Proje kurallarına uygunluğunu kontrol eder.
        """
        errors = []
        warnings = []
        
        # Kural 1: Her projede 3 kişi olmalı
        if self.participant_count != 3:
            errors.append(f"Project must have exactly 3 participants, currently has {self.participant_count}")
        
        # Kural 2: İlk kişi zorunlu olarak hoca olmalı
        if self.responsible_instructor_id and self.responsible:
            if self.responsible.role != "instructor":
                errors.append("First participant (responsible) must be an instructor")
        
        # Proje tipine göre kurallar
        if self.type == ProjectType.FINAL:
            # Kural 3: Bitirme projesinde en az 2 hoca olmalı
            if self.instructor_count < 2:
                errors.append(f"Bitirme project must have at least 2 instructors, currently has {self.instructor_count}")
        elif self.type == ProjectType.INTERIM:
            # Kural 4: Ara projede en az 1 hoca olmalı
            if self.instructor_count < 1:
                errors.append(f"Ara project must have at least 1 instructor, currently has {self.instructor_count}")
        
        # Uyarılar
        if self.instructor_count == 3:
            warnings.append("All 3 participants are instructors (no research assistants)")
        
        return {
            "compliant": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "instructor_count": self.instructor_count,
            "research_assistant_count": self.research_assistant_count,
            "participant_count": self.participant_count
        }
    
    def __repr__(self):
        return f"<Project {self.title} ({self.type.value})>"