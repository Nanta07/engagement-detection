from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class EngagementSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    responden = Column(String)
    sesi = Column(String)
    start_time = Column(DateTime, default=datetime.utcnow)

    frames = relationship("EngagementFrame", back_populates="session")


class EngagementFrame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    timestamp = Column(DateTime)
    engagement_level = Column(Integer)
    fps = Column(Float)
    response_time = Column(Float)
    confidence = Column(Float)

    session = relationship("EngagementSession", back_populates="frames")
