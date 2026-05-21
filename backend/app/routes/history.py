from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Device, Detection, Analysis
from app.schemas import (
    DetectionSchema,
    StatisticsSchema,
)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/detections", response_model=list[DetectionSchema])
def get_detection_history(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """Get detection history with optional date range."""
    query = db.query(Detection).order_by(desc(Detection.timestamp))
    
    if start_date:
        query = query.filter(Detection.timestamp >= start_date)
    
    if end_date:
        query = query.filter(Detection.timestamp <= end_date)
    
    detections = query.limit(limit).all()
    return detections


@router.get("/stats", response_model=StatisticsSchema)
def get_statistics(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    db: Session = Depends(get_db)
):
    """Get overall statistics."""
    # Default to last 24 hours if no dates provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=1)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Total devices
    total_devices = db.query(func.count(Device.id)).scalar()
    
    # Total detections in period
    total_detections = db.query(func.count(Detection.id)).filter(
        Detection.timestamp >= start_date,
        Detection.timestamp <= end_date
    ).scalar()
    
    # Unique OS count
    unique_os = db.query(func.count(func.distinct(Device.so_identified))).scalar()
    
    # Devices inside (RSSI > -70)
    devices_inside = db.query(func.count(Device.id)).filter(
        Device.rssi > -70
    ).scalar()
    
    # Devices outside (RSSI <= -70)
    devices_outside = db.query(func.count(Device.id)).filter(
        Device.rssi <= -70
    ).scalar()
    
    # OS distribution
    os_distribution = {}
    os_counts = db.query(
        Device.so_identified,
        func.count(Device.id)
    ).group_by(Device.so_identified).all()
    
    for os_name, count in os_counts:
        if os_name:
            os_distribution[os_name] = count
    
    return StatisticsSchema(
        total_devices=total_devices or 0,
        total_detections=total_detections or 0,
        unique_os=unique_os or 0,
        devices_inside=devices_inside or 0,
        devices_outside=devices_outside or 0,
        os_distribution=os_distribution
    )


@router.get("/timeline")
def get_detection_timeline(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    interval: str = Query("hour"),
    db: Session = Depends(get_db)
):
    """
    Get detection timeline aggregated by interval.
    
    Args:
        start_date: Start date for timeline
        end_date: End date for timeline
        interval: "hour", "day", or "minute"
    """
    # Default to last 7 days
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()
    
    detections = db.query(Detection).filter(
        Detection.timestamp >= start_date,
        Detection.timestamp <= end_date
    ).all()
    
    # Aggregate by interval
    timeline = {}
    for detection in detections:
        if interval == "hour":
            key = detection.timestamp.strftime("%Y-%m-%d %H:00")
        elif interval == "day":
            key = detection.timestamp.strftime("%Y-%m-%d")
        elif interval == "minute":
            key = detection.timestamp.strftime("%Y-%m-%d %H:%M")
        else:
            key = detection.timestamp.isoformat()
        
        timeline[key] = timeline.get(key, 0) + 1
    
    return timeline
