from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DetectionBase(BaseModel):
    rssi: int
    frequency: Optional[int] = None
    channel: Optional[int] = None
    frame_type: Optional[str] = None
    seen_count: Optional[int] = None
    location: Optional[str] = None


class DetectionCreate(DetectionBase):
    device_mac: str


class DetectionSchema(DetectionBase):
    id: int
    device_mac: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AnalysisBase(BaseModel):
    so_identified: Optional[str] = None
    distance_estimated: Optional[float] = None
    confidence: Optional[float] = None


class AnalysisCreate(AnalysisBase):
    device_mac: str


class AnalysisSchema(AnalysisBase):
    id: int
    device_mac: str
    last_updated: datetime
    
    class Config:
        from_attributes = True


class DeviceBase(BaseModel):
    mac_address: str
    rssi: Optional[int] = None
    frequency: Optional[int] = None
    channel: Optional[int] = None
    frame_type: Optional[str] = None
    seen_count: Optional[int] = None
    ssid: Optional[str] = None
    so_identified: Optional[str] = None
    distance_estimated: Optional[float] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    rssi: Optional[int] = None
    frequency: Optional[int] = None
    channel: Optional[int] = None
    frame_type: Optional[str] = None
    seen_count: Optional[int] = None
    ssid: Optional[str] = None
    so_identified: Optional[str] = None
    distance_estimated: Optional[float] = None
    last_seen: Optional[datetime] = None


class DeviceSchema(DeviceBase):
    id: int
    first_seen: datetime
    last_seen: datetime
    
    class Config:
        from_attributes = True


class DeviceDetailSchema(DeviceSchema):
    detections: list[DetectionSchema] = []
    analysis: Optional[AnalysisSchema] = None


class StatisticsSchema(BaseModel):
    total_devices: int
    total_detections: int
    unique_os: int
    devices_inside: int
    devices_outside: int
    os_distribution: dict[str, int] = {}
