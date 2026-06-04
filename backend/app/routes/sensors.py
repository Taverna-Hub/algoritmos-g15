from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SensorCounter
from app.schemas import SensorCounterSchema

OPTIC_SENSOR_ID = "sensor-2"

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


def get_or_create_sensor_counter(db: Session, sensor_id: str = OPTIC_SENSOR_ID) -> SensorCounter:
    counter = db.query(SensorCounter).filter(SensorCounter.sensor_id == sensor_id).first()
    if counter:
        return counter

    counter = SensorCounter(
        sensor_id=sensor_id,
        people_count=0,
        updated_at=datetime.utcnow(),
    )
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return counter


@router.get("/optic/sensor-2", response_model=SensorCounterSchema)
def get_optic_sensor_counter(db: Session = Depends(get_db)):
    """Get the persisted people count for optic sensor 2."""
    return get_or_create_sensor_counter(db)
