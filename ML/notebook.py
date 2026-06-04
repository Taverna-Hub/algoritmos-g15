import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for path in (ROOT_DIR, BACKEND_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.config import get_settings
from app.database import SessionLocal, engine, Base, ensure_optional_capture_columns
from app.models.device import Device, Detection, Analysis
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

settings = get_settings()

MQTT_TOPIC = "nodered/wifi/data"
MQTT_CLIENT_ID = "notebook-data-processor"
MAC_HEX_PATTERN = re.compile(r"^[0-9A-F]{12}$")


def normalize_mac(mac: str | None) -> str | None:
    if not mac or not isinstance(mac, str):
        return None

    compact_mac = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    if not MAC_HEX_PATTERN.match(compact_mac):
        return None

    return ":".join(compact_mac[index:index + 2] for index in range(0, 12, 2))


def should_ignore_mac(mac: str) -> bool:
    octets = [int(part, 16) for part in mac.split(":")]
    return all(octet == 0x00 for octet in octets) or all(
        octet == 0xFF for octet in octets
    ) or bool(octets[0] & 0x01)


def channel_to_frequency(channel: Any) -> int | None:
    try:
        channel_number = int(channel)
    except (TypeError, ValueError):
        return None

    if 1 <= channel_number <= 13:
        return 2407 + channel_number * 5
    if channel_number == 14:
        return 2484
    return None


def parse_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
            channel = parse_int(packet.get("channel"))
            devices.append({
                "mac": packet.get("source_mac") or packet.get("mac") or packet.get("mac_address"),
                "rssi": packet.get("rssi"),
                "frequency": packet.get("frequency") or channel_to_frequency(channel),
                "channel": channel,
                "frame_type": packet.get("frame_type") or packet.get("subtype"),
                "seen_count": packet.get("seen_count"),
                "ssid": packet.get("ssid") or packet.get("network_name") or "",
                "timestamp": packet.get("timestamp")
            })
        return devices

    return []


def build_device_record(device_data: dict, default_timestamp: datetime) -> dict | None:
    mac_raw = device_data.get("source_mac") or device_data.get("mac") or device_data.get("mac_address")
    mac = normalize_mac(mac_raw)
    if not mac:
        logger.debug("Skipping device record without a valid MAC")
        return None

    if should_ignore_mac(mac):
        logger.debug(f"Skipping ignored MAC address: {mac}")
        return None

    rssi = parse_int(device_data.get("rssi"), -80)
    channel = parse_int(device_data.get("channel"))
    frequency = parse_int(device_data.get("frequency")) or channel_to_frequency(channel) or 2412
    frame_type = device_data.get("frame_type") or device_data.get("subtype") or "management"
    seen_count = parse_int(device_data.get("seen_count"), 1) or 1
    ssid = device_data.get("ssid") or ""
    timestamp = parse_timestamp(device_data.get("timestamp") or default_timestamp)

    return {
        "mac": mac,
        "rssi": rssi,
        "channel": channel,
        "frequency": frequency,
        "frame_type": frame_type,
        "seen_count": seen_count,
        "ssid": ssid,
        "timestamp": timestamp,
    }


def deduplicate_device_records(records: list[dict]) -> list[dict]:
    deduplicated: dict[str, dict] = {}

    for record in records:
        mac = record["mac"]
        existing = deduplicated.get(mac)

        if not existing:
            deduplicated[mac] = record
            continue

        existing["seen_count"] = (existing.get("seen_count") or 0) + (
            record.get("seen_count") or 0
        )

        if record["timestamp"] >= existing["timestamp"]:
            existing["timestamp"] = record["timestamp"]
            for field in ("channel", "frequency", "frame_type"):
                if record.get(field) is not None:
                    existing[field] = record[field]
            if record.get("ssid"):
                existing["ssid"] = record["ssid"]

        if record["rssi"] is not None and (
            existing.get("rssi") is None or record["rssi"] > existing["rssi"]
        ):
            existing["rssi"] = record["rssi"]
            for field in ("channel", "frequency", "frame_type"):
                if record.get(field) is not None:
                    existing[field] = record[field]

    return list(deduplicated.values())


def upsert_device_record(session: SessionLocal, record: dict, batch_id: str | None = None) -> None:
    mac = record["mac"]
    rssi = record["rssi"]
    channel = record["channel"]
    frequency = record["frequency"]
    frame_type = record["frame_type"]
    seen_count = record["seen_count"]
    ssid = record["ssid"]
    timestamp = record["timestamp"]

    # Get or create device
    db_device = session.query(Device).filter(Device.mac_address == mac).first()
    if not db_device:
        db_device = Device(mac_address=mac, first_seen=timestamp)
        session.add(db_device)

    db_device.rssi = rssi
    db_device.frequency = frequency
    db_device.channel = channel
    db_device.frame_type = frame_type
    db_device.seen_count = seen_count
    if ssid:
        db_device.ssid = ssid
    db_device.last_seen = timestamp
    if batch_id:
        db_device.is_current_batch = True
        db_device.last_batch_id = batch_id

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

    # Keep one detection per MAC/timestamp. This prevents duplicated MQTT deliveries
    # from appending the same capture repeatedly while preserving real history.
    detection = session.query(Detection).filter(
        Detection.device_mac == mac,
        Detection.timestamp == timestamp,
    ).first()

    if not detection:
        detection = Detection(device_mac=mac, timestamp=timestamp)
        session.add(detection)

    detection.rssi = rssi or -80
    detection.frequency = frequency
    detection.channel = channel
    detection.frame_type = frame_type
    detection.seen_count = seen_count
    detection.location = analysis_results.get("location")


def process_device(session: SessionLocal, device_data: dict, default_timestamp: datetime) -> bool:
    record = build_device_record(device_data, default_timestamp)
    if not record:
        return False

    upsert_device_record(session, record)
    return True


def process_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        logger.warning("Payload is not a dictionary, skipping")
        return

    timestamp = parse_timestamp(payload.get("timestamp"))
    devices = extract_devices(payload)
    if not devices:
        logger.warning("No devices found in payload")
        return

    records = []
    skipped_count = 0
    for device_data in devices:
        record = build_device_record(device_data, timestamp)
        if record:
            records.append(record)
        else:
            skipped_count += 1

    records = deduplicate_device_records(records)
    if not records:
        logger.warning("No valid devices found in payload")
        return

    session = SessionLocal()
    try:
        batch_id = timestamp.isoformat()
        session.query(Device).update(
            {Device.is_current_batch: False},
            synchronize_session=False,
        )
        for record in records:
            upsert_device_record(session, record, batch_id)
        session.commit()
        logger.info(
            f"Upserted {len(records)} unique device records "
            f"({skipped_count} invalid/ignored, {len(devices)} received, batch {batch_id})"
        )
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
    ensure_optional_capture_columns()
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
