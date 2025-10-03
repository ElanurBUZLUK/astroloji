"""
Database models for Astro-AA
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Chart(Base):
    """Astrological chart model"""
    __tablename__ = "charts"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)  # For future user association
    birth_date = Column(String, nullable=False)
    birth_time = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String, default="UTC")
    place_name = Column(String, nullable=True)

    # Chart data as JSON
    planets = Column(JSON, nullable=False)
    houses = Column(JSON, nullable=False)
    almuten = Column(JSON, nullable=False)
    zodiacal_releasing = Column(JSON, nullable=False)
    lots = Column(JSON, nullable=False)
    lots_data = Column(JSON, nullable=False)  # Additional lots data
    is_day_birth = Column(Integer, nullable=False)  # 0 for night, 1 for day

    # Additional calculations
    profection = Column(JSON, nullable=True)
    firdaria = Column(JSON, nullable=True)
    antiscia = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zr_periods = relationship("ZRPeriod", back_populates="chart", cascade="all, delete-orphan")
    profection_periods = relationship("ProfectionPeriod", back_populates="chart", cascade="all, delete-orphan")
    firdaria_periods = relationship("FirdariaPeriod", back_populates="chart", cascade="all, delete-orphan")

class Interpretation(Base):
    """Interpretation result model"""
    __tablename__ = "interpretations"

    id = Column(String, primary_key=True)
    chart_id = Column(String, ForeignKey('charts.id'), nullable=False)
    query = Column(Text, nullable=False)
    mode = Column(String, default="natal")  # natal, timing, today

    # Results
    interpretation = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    sources = Column(JSON, nullable=True)  # RAG sources used
    metadata_info = Column(JSON, nullable=True)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    chart = relationship("Chart")

class Alert(Base):
    """Alert/notification model"""
    __tablename__ = "alerts"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)  # For future user association
    alert_type = Column(String, nullable=False)  # system, chart, interpretation, etc.
    severity = Column(String, default="info")  # info, warning, error, critical
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    metadata_info = Column(JSON, nullable=True)  # Additional alert data
    is_read = Column(Integer, default=0)  # 0=unread, 1=read
    is_resolved = Column(Integer, default=0)  # 0=active, 1=resolved

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    is_superuser = Column(Integer, default=0)

    # Profile
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    birth_time = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class ZRPeriod(Base):
    __tablename__ = "zr_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chart_id = Column(String, ForeignKey("charts.id"), index=True, nullable=False)
    level = Column(Integer, nullable=False)  # 1 or 2
    sign = Column(String, nullable=False)
    ruler = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_peak = Column(Integer, default=0)
    is_lb = Column(Integer, default=0)
    tone = Column(String, nullable=True)

    chart = relationship("Chart", back_populates="zr_periods")


class ProfectionPeriod(Base):
    __tablename__ = "profection_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chart_id = Column(String, ForeignKey("charts.id"), index=True, nullable=False)
    age = Column(Integer, nullable=False)
    profected_house = Column(Integer, nullable=False)
    profected_sign = Column(String, nullable=False)
    year_lord = Column(String, nullable=True)
    activated_topics = Column(JSON, nullable=True)

    chart = relationship("Chart", back_populates="profection_periods")


class FirdariaPeriod(Base):
    __tablename__ = "firdaria_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chart_id = Column(String, ForeignKey("charts.id"), index=True, nullable=False)
    period_type = Column(String, nullable=False)  # major or minor
    lord = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    chart = relationship("Chart", back_populates="firdaria_periods")
