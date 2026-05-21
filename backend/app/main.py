import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from app.config import get_settings
from app.database import engine, SessionLocal, Base
from app.mqtt import MQTTClient
from app.models import Device, Detection
from app.routes import devices_router, history_router
from app.services.ml_service import MLService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()
mqtt_client = None
db = None


def create_tables():
    """Create database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")


def process_mqtt_message(payload: dict):
    """Process MQTT message from Node-RED."""
    try:
        logger.debug(f"Processing MQTT payload: {payload}")
        
        db_session = SessionLocal()
        
        if "timestamp" in payload and "devices" in payload:
            timestamp = payload.get("timestamp")
            devices = payload.get("devices", [])
            
            for device_data in devices:
                mac = device_data.get("mac")
                rssi = device_data.get("rssi")
                frequency = device_data.get("frequency", 2412)
                ssid = device_data.get("ssid", "")
                
                if not mac:
                    continue
                
                # Get or create device
                db_device = db_session.query(Device).filter(
                    Device.mac_address == mac
                ).first()
                
                if not db_device:
                    db_device = Device(mac_address=mac)
                
                # Update device info
                db_device.rssi = rssi
                db_device.frequency = frequency
                if ssid:
                    db_device.ssid = ssid
                db_device.last_seen = datetime.utcnow()
                
                # Perform ML analysis
                analysis_results = MLService.analyze_device(mac, rssi, frequency)
                db_device.so_identified = analysis_results["so_identified"]
                db_device.distance_estimated = analysis_results["distance_estimated"]
                
                db_session.add(db_device)
                
                # Create detection log
                detection = Detection(
                    device_mac=mac,
                    rssi=rssi,
                    frequency=frequency,
                    location=analysis_results["location"],
                    timestamp=datetime.utcnow()
                )
                db_session.add(detection)
            
            db_session.commit()
            logger.info(f"Processed {len(devices)} devices from MQTT")
        
        db_session.close()
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")


def start_mqtt():
    """Start MQTT client."""
    global mqtt_client
    try:
        mqtt_client = MQTTClient(on_message_callback=process_mqtt_message)
        mqtt_client.connect()
        logger.info("MQTT client started")
    except Exception as e:
        logger.warning(f"Failed to connect to MQTT broker: {e}")
        logger.info("Continuing without MQTT - using mock data")


def stop_mqtt():
    """Stop MQTT client."""
    global mqtt_client
    if mqtt_client:
        mqtt_client.disconnect()
        logger.info("MQTT client stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting application...")
    create_tables()
    start_mqtt()
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    stop_mqtt()


# Create FastAPI app
app = FastAPI(
    title="WiFi Detection API",
    description="API for detecting and analyzing WiFi devices",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(devices_router)
app.include_router(history_router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "WiFi Detection API",
        "version": "1.0.0",
        "mqtt_connected": mqtt_client.is_connected() if mqtt_client else False
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.is_connected() if mqtt_client else False
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
    )
