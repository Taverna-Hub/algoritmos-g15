from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Device(Base):
    """Device model - represents unique WiFi devices detected."""
    
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    rssi = Column(Integer, nullable=True)
    frequency = Column(Integer, nullable=True)
    ssid = Column(String(32), nullable=True)
    so_identified = Column(String(50), nullable=True)
    distance_estimated = Column(Float, nullable=True)
    
    # Relationships
    detections = relationship("Detection", back_populates="device")
    analysis = relationship("Analysis", back_populates="device", uselist=False)


class Detection(Base):
    """Detection model - logs each detection event."""
    
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    device_mac = Column(String(17), ForeignKey("devices.mac_address"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    rssi = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=True)
    location = Column(String(50), nullable=True)  # "inside" or "outside"
    
    # Relationships
    device = relationship("Device", back_populates="detections")


class Analysis(Base):
    """Analysis model - stores ML analysis results for devices."""
    
    __tablename__ = "analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    device_mac = Column(String(17), ForeignKey("devices.mac_address"), nullable=False, unique=True, index=True)
    so_identified = Column(String(50), nullable=True)
    distance_estimated = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="analysis")
