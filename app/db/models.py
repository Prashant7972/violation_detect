import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, default=lambda: f"sess-{uuid.uuid4().hex[:12]}")
    user_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="CREATED")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    events = relationship("EventModel", back_populates="session", cascade="all, delete-orphan")


class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    rule_triggered = Column(String(128), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    session = relationship("SessionModel", back_populates="events")
    evidence = relationship("EvidenceModel", back_populates="event", uselist=False, cascade="all, delete-orphan")


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(256), nullable=False)
    bbox_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    event = relationship("EventModel", back_populates="evidence")
