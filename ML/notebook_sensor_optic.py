import json
import logging
import os
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
from app.database import Base, SessionLocal, engine
from app.models import SensorCounter

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()

MQTT_TOPIC = "nodered/esp8266/event"
MQTT_CLIENT_ID = "notebook-sensor-optic-processor"
OPTIC_SENSOR_ID = "sensor-2"
VALID_EVENTS = {"entrada", "saida"}


def normalize_event(payload: dict[str, Any]) -> str | None:
    event = str(payload.get("event") or "").strip().lower()
    if event not in VALID_EVENTS:
        return None
    return event


def update_people_count(event: str) -> int:
    session = SessionLocal()
    try:
        counter = (
            session.query(SensorCounter)
            .filter(SensorCounter.sensor_id == OPTIC_SENSOR_ID)
            .first()
        )
        if not counter:
            counter = SensorCounter(sensor_id=OPTIC_SENSOR_ID, people_count=0)
            session.add(counter)

        if event == "entrada":
            counter.people_count += 1
        elif event == "saida":
            counter.people_count = max(0, counter.people_count - 1)

        counter.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(counter)
        logger.info(
            "Sensor %s processed %s; people_count=%s",
            OPTIC_SENSOR_ID,
            event,
            counter.people_count,
        )
        return counter.people_count
    except Exception as error:
        session.rollback()
        logger.error("Failed to update optic sensor counter: %s", error)
        raise
    finally:
        session.close()


def process_payload(payload: dict[str, Any]) -> int | None:
    if not isinstance(payload, dict):
        logger.warning("Optic sensor payload is not a dictionary, skipping")
        return None

    event = normalize_event(payload)
    if not event:
        logger.warning("Invalid optic sensor event payload: %s", payload)
        return None

    return update_people_count(event)


def on_connect(client: mqtt.Client, userdata: Any, flags: dict, rc: int) -> None:
    if rc == 0:
        logger.info(
            "Connected to MQTT broker at %s:%s",
            settings.mqtt_broker,
            settings.mqtt_port,
        )
        client.subscribe(MQTT_TOPIC)
        logger.info("Subscribed to topic '%s'", MQTT_TOPIC)
    else:
        logger.error("MQTT connection failed with code %s", rc)


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        logger.debug("Received MQTT message on %s: %s", msg.topic, payload)
        process_payload(payload)
    except json.JSONDecodeError as error:
        logger.error("Invalid JSON payload: %s", error)
    except Exception as error:
        logger.error("Error handling optic sensor message: %s", error)


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
        logger.info("Optic sensor notebook stopped by user")
    except Exception as error:
        logger.error("Optic sensor notebook error: %s", error)


if __name__ == "__main__":
    main()
