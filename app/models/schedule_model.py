from datetime import date, datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
import enum

from app.core.database_connection import Base

class ScheduleStatus(str, enum.Enum):
    BORRADOR = "borrador"
    PUBLICADO = "publicado"

class ScheduleModel(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    status = Column(String(20), default=ScheduleStatus.BORRADOR, nullable=False)
    responsible_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    responsible = relationship("Employee", backref="schedules")