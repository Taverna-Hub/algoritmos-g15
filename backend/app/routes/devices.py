from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Device, Detection, Analysis
from app.schemas import (
    DeviceSchema,
    DeviceDetailSchema,
    DeviceCreate,
    DeviceUpdate,
    DetectionSchema,
    DetectionCreate,
    AnalysisSchema,
    StatisticsSchema,
)

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceSchema])
def get_devices(db: Session = Depends(get_db)):
    """Get all devices detected."""
    devices = db.query(Device).order_by(desc(Device.last_seen)).all()
    return devices


@router.get("/{mac}", response_model=DeviceDetailSchema)
def get_device(mac: str, db: Session = Depends(get_db)):
    """Get details of a specific device."""
    device = db.query(Device).filter(Device.mac_address == mac).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("", response_model=DeviceSchema)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Create or update a device record without processing MQTT data."""
    db_device = db.query(Device).filter(Device.mac_address == device.mac_address).first()
    
    if db_device:
        # Update existing device metadata
        for key, value in device.dict(exclude_unset=True).items():
            setattr(db_device, key, value)
        db_device.last_seen = datetime.utcnow()
    else:
        # Create new device record
        db_device = Device(**device.dict())
        db_device.last_seen = datetime.utcnow()
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    return db_device


@router.get("/{mac}/detections", response_model=list[DetectionSchema])
def get_device_detections(
    mac: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get detections for a specific device."""
    detections = (
        db.query(Detection)
        .filter(Detection.device_mac == mac)
        .order_by(desc(Detection.timestamp))
        .limit(limit)
        .all()
    )
    return detections
