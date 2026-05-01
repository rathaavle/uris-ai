"""
Database models for URIS-AI system.
SQLAlchemy ORM models matching the database schema.
Requirements: 7.1
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Region(Base):
    """
    Model for administrative regions.

    Stores information about geographic regions including coordinates,
    elevation, and drainage capacity.
    """

    __tablename__ = "regions"

    region_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    elevation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    drainage_capacity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    weather_data: Mapped[List["WeatherData"]] = relationship(
        "WeatherData", back_populates="region", cascade="all, delete-orphan"
    )
    flood_events: Mapped[List["FloodEvent"]] = relationship(
        "FloodEvent", back_populates="region", cascade="all, delete-orphan"
    )
    roads: Mapped[List["Road"]] = relationship(
        "Road", back_populates="region", cascade="all, delete-orphan"
    )
    public_facilities: Mapped[List["PublicFacility"]] = relationship(
        "PublicFacility", back_populates="region", cascade="all, delete-orphan"
    )
    risk_scores: Mapped[List["RiskScore"]] = relationship(
        "RiskScore", back_populates="region", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="region", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Region(region_id={self.region_id}, name='{self.name}')>"


class WeatherData(Base):
    """
    Model for weather data per region.

    Stores time-series weather information including rainfall, humidity,
    temperature, and wind speed.
    """

    __tablename__ = "weather_data"
    __table_args__ = (Index("idx_weather_region_date", "region_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    rainfall: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="weather_data")

    def __repr__(self) -> str:
        return f"<WeatherData(id={self.id}, region_id={self.region_id}, date={self.date})>"


class FloodEvent(Base):
    """
    Model for historical flood events.

    Stores information about past flood occurrences including severity,
    water level, duration, and affected area.
    """

    __tablename__ = "flood_events"
    __table_args__ = (
        CheckConstraint("severity BETWEEN 1 AND 4", name="check_severity_range"),
        Index("idx_flood_region_date", "region_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    water_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    affected_area_km2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="flood_events")

    def __repr__(self) -> str:
        return f"<FloodEvent(id={self.id}, region_id={self.region_id}, severity={self.severity})>"


class Road(Base):
    """
    Model for road network data.

    Stores information about roads including type, density, length,
    and whether it's a main road.
    """

    __tablename__ = "roads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("regions.region_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    road_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    road_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    road_density: Mapped[float] = mapped_column(Float, nullable=False)
    length_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_main_road: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="roads")

    def __repr__(self) -> str:
        return f"<Road(id={self.id}, name='{self.road_name}', type='{self.road_type}')>"


class PublicFacility(Base):
    """
    Model for public facilities.

    Stores information about public service facilities including hospitals,
    clinics, schools, and government offices.
    """

    __tablename__ = "public_facilities"
    __table_args__ = (Index("idx_region_type", "region_id", "type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="public_facilities")

    def __repr__(self) -> str:
        return f"<PublicFacility(id={self.id}, name='{self.name}', type='{self.type}')>"


class RiskScore(Base):
    """
    Model for calculated risk scores.

    Stores the results of risk calculations including flood risk,
    traffic impact, service accessibility, and urban risk score.
    """

    __tablename__ = "risk_scores"
    __table_args__ = (
        CheckConstraint("flood_risk BETWEEN 0 AND 100", name="check_flood_risk_range"),
        CheckConstraint(
            "traffic_impact BETWEEN 0 AND 100", name="check_traffic_impact_range"
        ),
        CheckConstraint(
            "service_access BETWEEN 0 AND 100", name="check_service_access_range"
        ),
        CheckConstraint(
            "urban_risk_score BETWEEN 0 AND 100", name="check_urban_risk_score_range"
        ),
        Index("idx_risk_region_date", "region_id", "date"),
        Index("idx_urs", "urban_risk_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    flood_risk: Mapped[float] = mapped_column(Float, nullable=False)
    traffic_impact: Mapped[float] = mapped_column(Float, nullable=False)
    service_access: Mapped[float] = mapped_column(Float, nullable=False)
    urban_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="risk_scores")

    def __repr__(self) -> str:
        return f"<RiskScore(id={self.id}, region_id={self.region_id}, urs={self.urban_risk_score})>"


class Recommendation(Base):
    """
    Model for system-generated recommendations.

    Stores recommendations for actions based on risk analysis,
    including type, description, urgency level, and expiration.
    """

    __tablename__ = "recommendations"
    __table_args__ = (
        Index("idx_region_active", "region_id", "is_active"),
        Index("idx_urgency", "urgency_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="CASCADE"), nullable=False
    )
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    urgency_level: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, type='{self.recommendation_type}', urgency='{self.urgency_level}')>"


class User(Base):
    """
    Model for user information and roles.

    Stores user credentials, role information, and account status.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
