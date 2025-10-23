from sqlalchemy import Column, Integer, Time, Boolean, String, Enum
from sqlalchemy.orm import relationship
from typing import Dict, Any, Tuple
import enum
from datetime import time as dt_time

from app.db.base_class import Base

class SessionType(str, enum.Enum):
    """Oturum türleri - Proje açıklamasına göre"""
    MORNING = "morning"        # Sabah oturumu: 09:00-11:30
    BREAK = "break"           # Öğle arası: 12:00-13:00
    AFTERNOON = "afternoon"   # Öğleden sonra: 13:00-16:30

class TimeSlot(Base):
    """Zaman dilimi modeli - Proje açıklamasına göre düzenlenmiş."""

    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    session_type = Column(Enum(SessionType), nullable=False)  # Oturum türü
    is_morning = Column(Boolean, default=None)  # Geriye uyumluluk için
    is_active = Column(Boolean, default=True)

    # İlişkiler
    schedules = relationship("Schedule", back_populates="timeslot")
    
    @property
    def is_valid_project_time(self) -> bool:
        """
        Proje açıklamasına göre geçerli zaman dilimi mi kontrol eder.
        Geçerli saatler: 09:00-11:30 (sabah), 13:00-16:30 (öğleden sonra)
        """
        try:
            if self.session_type == SessionType.BREAK:
                return False
            
            # Güvenli saat kontrolü
            if not self.start_time:
                return False
                
            hour = None
            minute = None
            
            # String olarak saklanıyorsa parse et
            if isinstance(self.start_time, str):
                time_str = self.start_time.strip()
                if ':' in time_str:
                    parts = time_str.split(':')
                    if len(parts) >= 2:
                        hour = int(parts[0])
                        minute = int(parts[1])
            # Time objesi olarak saklanıyorsa
            elif hasattr(self.start_time, 'hour') and hasattr(self.start_time, 'minute'):
                hour = self.start_time.hour
                minute = self.start_time.minute
            
            if hour is None or minute is None:
                return False
            
            # Geçersiz saatleri kontrol et
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False
            
            # Sabah oturumu: 09:00-11:30
            if self.session_type == SessionType.MORNING:
                return (hour >= 9 and hour <= 11 and 
                       (hour < 11 or minute <= 30))
            
            # Öğleden sonra oturumu: 13:00-16:30
            if self.session_type == SessionType.AFTERNOON:
                return (hour >= 13 and hour <= 16 and
                       (hour < 16 or minute <= 30))
        except (ValueError, AttributeError, TypeError):
            pass
        
        return False
    
    @property
    def is_morning_session(self) -> bool:
        """Sabah oturumu mu?"""
        try:
            return self.session_type == SessionType.MORNING
        except (ValueError, AttributeError):
            return False
    
    @property
    def is_afternoon_session(self) -> bool:
        """Öğleden sonra oturumu mu?"""
        try:
            return self.session_type == SessionType.AFTERNOON
        except (ValueError, AttributeError):
            return False
    
    @property
    def is_break_session(self) -> bool:
        """Öğle arası mı?"""
        try:
            return self.session_type == SessionType.BREAK
        except (ValueError, AttributeError):
            return False

    @property
    def time_range_formatted(self) -> str:
        """Tutarlı zaman aralığı formatı döndürür."""
        try:
            start_str = "09:00"
            end_str = "09:30"
            
            if self.start_time:
                try:
                    # String olarak saklanıyorsa parse et
                    if isinstance(self.start_time, str):
                        time_str = self.start_time.strip()
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                hour = int(parts[0])
                                minute = int(parts[1])
                                if 0 <= hour <= 23 and 0 <= minute <= 59:
                                    start_str = f"{hour:02d}:{minute:02d}"
                    # Time objesi olarak saklanıyorsa
                    elif hasattr(self.start_time, 'hour') and hasattr(self.start_time, 'minute'):
                        hour = self.start_time.hour
                        minute = self.start_time.minute
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            start_str = f"{hour:02d}:{minute:02d}"
                except (ValueError, AttributeError, TypeError):
                    pass
                    
            if self.end_time:
                try:
                    # String olarak saklanıyorsa parse et
                    if isinstance(self.end_time, str):
                        time_str = self.end_time.strip()
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                hour = int(parts[0])
                                minute = int(parts[1])
                                if 0 <= hour <= 23 and 0 <= minute <= 59:
                                    end_str = f"{hour:02d}:{minute:02d}"
                    # Time objesi olarak saklanıyorsa
                    elif hasattr(self.end_time, 'hour') and hasattr(self.end_time, 'minute'):
                        hour = self.end_time.hour
                        minute = self.end_time.minute
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            end_str = f"{hour:02d}:{minute:02d}"
                except (ValueError, AttributeError, TypeError):
                    pass
                    
        except (ValueError, AttributeError, TypeError):
            # Eğer time objesi geçersizse, varsayılan değerler kullan
            start_str = "09:00"
            end_str = "09:30"
        return f"{start_str}-{end_str}"

    @property
    def time_range(self) -> str:
        """DB'de kolonu olmayan, sadece okuma amaçlı zaman aralığı (09:00-09:30)."""
        return self.time_range_formatted

    @property
    def start_hour_minute(self) -> Tuple[int, int]:
        """Başlangıç saatini saat:dakika olarak döndürür."""
        try:
            if self.start_time:
                # String olarak saklanıyorsa parse et
                if isinstance(self.start_time, str):
                    time_str = self.start_time.strip()
                    if ':' in time_str:
                        parts = time_str.split(':')
                        if len(parts) >= 2:
                            hour = int(parts[0])
                            minute = int(parts[1])
                            if 0 <= hour <= 23 and 0 <= minute <= 59:
                                return hour, minute
                # Time objesi olarak saklanıyorsa
                elif hasattr(self.start_time, 'hour') and hasattr(self.start_time, 'minute'):
                    hour = self.start_time.hour
                    minute = self.start_time.minute
                    # Geçersiz saatleri kontrol et
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return hour, minute
                    else:
                        print(f"Warning: Invalid start_time hour={hour}, minute={minute} for timeslot {self.id}")
        except (ValueError, AttributeError, TypeError):
            pass
        return 9, 0  # Varsayılan

    @property
    def is_late_slot(self) -> bool:
        """16:30 sonrası slot mu? (cezalı slotlar)"""
        try:
            hour, minute = self.start_hour_minute
            return hour > 16 or (hour == 16 and minute >= 30)
        except (ValueError, AttributeError, TypeError):
            return False

    @property
    def slot_reward(self) -> float:
        """Slot ödülünü hesaplar - erken saatler yüksek puanlı."""
        try:
            hour, minute = self.start_hour_minute

            # 16:30 sonrası cezalı
            if self.is_late_slot:
                return -9999.0

            # Erken saatler yüksek ödül
            if hour == 9:
                return 1000.0
            elif hour == 10:
                return 900.0 - (minute * 0.5)  # Dakika başına azalma
            elif hour == 11:
                return 800.0 - (minute * 0.5)
            elif hour == 13:
                return 700.0
            elif hour == 14:
                return 600.0 - (minute * 0.5)
            elif hour == 15:
                return 500.0 - (minute * 0.5)
            elif hour == 16 and minute < 30:
                return 400.0
        except (ValueError, AttributeError, TypeError):
            pass

        return 100.0  # Varsayılan

    def to_dict(self) -> Dict[str, Any]:
        """Model objesini dict'e çevirir (frontend/algoritmalar için uyumlu)."""
        try:
            # Güvenli saat formatlaması
            start_time_str = "09:00"
            end_time_str = "09:30"

            if self.start_time:
                try:
                    # String olarak saklanıyorsa parse et
                    if isinstance(self.start_time, str):
                        time_str = self.start_time.strip()
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                hour = int(parts[0])
                                minute = int(parts[1])
                                if 0 <= hour <= 23 and 0 <= minute <= 59:
                                    start_time_str = f"{hour:02d}:{minute:02d}"
                    # Time objesi olarak saklanıyorsa
                    elif hasattr(self.start_time, 'hour') and hasattr(self.start_time, 'minute'):
                        hour = self.start_time.hour
                        minute = self.start_time.minute
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            start_time_str = f"{hour:02d}:{minute:02d}"
                except (ValueError, AttributeError, TypeError) as e:
                    print(f"Error parsing start_time for timeslot {self.id}: {e}")

            if self.end_time:
                try:
                    # String olarak saklanıyorsa parse et
                    if isinstance(self.end_time, str):
                        time_str = self.end_time.strip()
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                hour = int(parts[0])
                                minute = int(parts[1])
                                if 0 <= hour <= 23 and 0 <= minute <= 59:
                                    end_time_str = f"{hour:02d}:{minute:02d}"
                    # Time objesi olarak saklanıyorsa
                    elif hasattr(self.end_time, 'hour') and hasattr(self.end_time, 'minute'):
                        hour = self.end_time.hour
                        minute = self.end_time.minute
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            end_time_str = f"{hour:02d}:{minute:02d}"
                except (ValueError, AttributeError, TypeError) as e:
                    print(f"Error parsing end_time for timeslot {self.id}: {e}")

        except (ValueError, AttributeError, TypeError) as e:
            print(f"Error in to_dict for timeslot {self.id}: {e}")

        return {
            "id": self.id,
            "start_time": start_time_str,
            "end_time": end_time_str,
            "time_range": self.time_range,  # her zaman üretilecek
            "session_type": self.session_type.value if self.session_type else None,
            "is_morning": bool(self.is_morning) if self.is_morning is not None else self.is_morning_session,
            "is_afternoon": self.is_afternoon_session,
            "is_late_slot": self.is_late_slot,
            "slot_reward": self.slot_reward,
            "is_active": bool(self.is_active),
        }

    def __repr__(self):
        try:
            session_type_str = self.session_type.value if self.session_type else "unknown"
        except (ValueError, AttributeError):
            session_type_str = "unknown"
        return f"<TimeSlot {self.time_range} ({session_type_str})>" 