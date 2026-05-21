import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.config import get_settings
from backend.app.database import SessionLocal, engine, Base
from backend.app.models.device import Device, Detection, Analysis
from backend.app.services.ml_service import MLService

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

settings = get_settings()

MQTT_TOPIC = "nodered/wifi/data"
MQTT_CLIENT_ID = "notebook-data-processor"


def normalize_mac(mac: str | None) -> str | None:
    if not mac:
        return None
    normalized = mac.strip().upper().replace("-", ":")
    return normalized


def parse_timestamp(value: Any) -> datetime:
    if not value:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception:
            logger.warning(f"Unable to parse timestamp '{value}', using UTC now")
            return datetime.utcnow()


def extract_devices(payload: dict) -> list[dict]:
    if "devices" in payload and isinstance(payload["devices"], list):
        return payload["devices"]

    if "packets" in payload and isinstance(payload["packets"], list):
        devices = []
        for packet in payload["packets"]:
            devices.append({
                "mac": packet.get("source_mac") or packet.get("mac"),
                "rssi": packet.get("rssi"),
                "frequency": packet.get("frequency"),
                "ssid": packet.get("ssid") or packet.get("network_name") or "",
                "timestamp": packet.get("timestamp")
            })
        return devices

    return []


def process_device(session: SessionLocal, device_data: dict, default_timestamp: datetime) -> None:
    mac_raw = device_data.get("mac") or device_data.get("source_mac")
    mac = normalize_mac(mac_raw)
    if not mac:
        logger.debug("Skipping device record without MAC")
        return

    rssi = device_data.get("rssi")
    frequency = device_data.get("frequency") or 2412
    ssid = device_data.get("ssid") or ""
    timestamp = parse_timestamp(device_data.get("timestamp") or default_timestamp)

    # Get or create device
    db_device = session.query(Device).filter(Device.mac_address == mac).first()
    if not db_device:
        db_device = Device(mac_address=mac, first_seen=timestamp)
        session.add(db_device)

    db_device.rssi = rssi
    db_device.frequency = frequency
    if ssid:
        db_device.ssid = ssid
    db_device.last_seen = timestamp

    analysis_results = MLService.analyze_device(mac, rssi or -70, frequency)
    db_device.so_identified = analysis_results["so_identified"]
    db_device.distance_estimated = analysis_results["distance_estimated"]

    # Save or update analysis
    analysis = session.query(Analysis).filter(Analysis.device_mac == mac).first()
    if not analysis:
        analysis = Analysis(device_mac=mac)
        session.add(analysis)

    analysis.so_identified = analysis_results["so_identified"]
    analysis.distance_estimated = analysis_results["distance_estimated"]
    analysis.confidence = analysis_results.get("confidence")
    analysis.last_updated = timestamp

    # Create detection log
    detection = Detection(
        device_mac=mac,
        timestamp=timestamp,
        rssi=rssi or 0,
        frequency=frequency,
        location=analysis_results.get("location")
    )
    session.add(detection)


def process_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        logger.warning("Payload is not a dictionary, skipping")
        return

    timestamp = parse_timestamp(payload.get("timestamp"))
    devices = extract_devices(payload)
    if not devices:
        logger.warning("No devices found in payload")
        return

    session = SessionLocal()
    try:
        for device_data in devices:
            process_device(session, device_data, timestamp)
        session.commit()
        logger.info(f"Processed {len(devices)} device records")
    except Exception as error:
        session.rollback()
        logger.error(f"Failed to save device records: {error}")
    finally:
        session.close()


def on_connect(client: mqtt.Client, userdata: Any, flags: dict, rc: int) -> None:
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {settings.mqtt_broker}:{settings.mqtt_port}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic '{MQTT_TOPIC}'")
    else:
        logger.error(f"MQTT connection failed with code {rc}")


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        logger.debug(f"Received MQTT message on {msg.topic}: {payload}")
        process_payload(payload)
    except json.JSONDecodeError as error:
        logger.error(f"Invalid JSON payload: {error}")
    except Exception as error:
        logger.error(f"Error handling MQTT message: {error}")


def build_database() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")


def main() -> None:
    build_database()

    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Notebook service stopped by user")
    except Exception as error:
        logger.error(f"Notebook service error: {error}")


if __name__ == "__main__":
    main()
