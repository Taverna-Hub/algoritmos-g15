from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "esp32/wifi/scan"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "mqtt_dados_ineficiente.csv"
CLIENT_ID = "hardware-ineficiente-csv-logger"
RAW_PAYLOAD_LIMIT = 1000

CSV_COLUMNS = [
    "received_at",
    "topic",
    "device_id",
    "algorithm",
    "sequence",
    "payload_bytes",
    "packet_index",
    "source_mac",
    "rssi",
    "channel",
    "frequency",
    "frame_type",
    "seen_count",
    "parse_error",
    "raw_payload",
]

logger = logging.getLogger("mqtt_csv_logger")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_csv_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()


def append_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_csv_header(path)
    with path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def parse_payload(payload_text: str) -> tuple[dict[str, Any] | None, str]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as error:
        return None, f"json_decode_error: {error}"

    if not isinstance(payload, dict):
        return None, "payload_is_not_object"

    return payload, ""


def rows_from_message(topic: str, payload_bytes: bytes) -> list[dict[str, Any]]:
    received_at = utc_now_iso()
    payload_text = payload_bytes.decode("utf-8", errors="replace")
    payload_size = len(payload_bytes)
    payload, parse_error = parse_payload(payload_text)

    base_row = {
        "received_at": received_at,
        "topic": topic,
        "payload_bytes": payload_size,
    }

    if parse_error or payload is None:
        return [
            {
                **base_row,
                "parse_error": parse_error,
                "raw_payload": payload_text[:RAW_PAYLOAD_LIMIT],
            }
        ]

    packets = payload.get("packets")
    if not isinstance(packets, list):
        packets = []

    metadata = {
        **base_row,
        "device_id": payload.get("device_id", ""),
        "algorithm": payload.get("algorithm", ""),
        "sequence": payload.get("sequence", ""),
    }

    if not packets:
        return [
            {
                **metadata,
                "parse_error": "missing_or_empty_packets",
                "raw_payload": payload_text[:RAW_PAYLOAD_LIMIT],
            }
        ]

    rows = []
    for index, packet in enumerate(packets):
        if not isinstance(packet, dict):
            rows.append(
                {
                    **metadata,
                    "packet_index": index,
                    "parse_error": "packet_is_not_object",
                    "raw_payload": json.dumps(packet, ensure_ascii=True)[:RAW_PAYLOAD_LIMIT],
                }
            )
            continue

        rows.append(
            {
                **metadata,
                "packet_index": index,
                "source_mac": packet.get("source_mac")
                or packet.get("mac")
                or packet.get("mac_address")
                or packet.get("sa")
                or "",
                "rssi": packet.get("rssi", ""),
                "channel": packet.get("channel", ""),
                "frequency": packet.get("frequency", ""),
                "frame_type": packet.get("frame_type") or packet.get("subtype") or "",
                "seen_count": packet.get("seen_count", ""),
            }
        )

    return rows


def build_client(client_id: str) -> Any:
    try:
        import paho.mqtt.client as mqtt
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Dependencia ausente: instale paho-mqtt com "
            "`pip install paho-mqtt` ou `pip install -r requirements.txt`."
        ) from error

    callback_api_version = getattr(mqtt, "CallbackAPIVersion", None)
    if callback_api_version is not None:
        return mqtt.Client(callback_api_version.VERSION1, client_id=client_id)
    return mqtt.Client(client_id=client_id)


def run_logger(host: str, port: int, topic: str, output: Path) -> None:
    output = output.resolve()
    ensure_csv_header(output)

    def on_connect(client: Any, userdata: Any, flags: dict, rc: int) -> None:
        if rc == 0:
            logger.info("Conectado ao broker MQTT %s:%s", host, port)
            client.subscribe(topic)
            logger.info("Assinando topico '%s'", topic)
            logger.info("Salvando dados em %s", output)
        else:
            logger.error("Falha ao conectar no MQTT, codigo=%s", rc)

    def on_message(client: Any, userdata: Any, msg: Any) -> None:
        rows = rows_from_message(msg.topic, msg.payload)
        append_rows(output, rows)
        logger.info(
            "Mensagem recebida em %s: %s linha(s) gravada(s)",
            msg.topic,
            len(rows),
        )

    client = build_client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Conectando ao broker MQTT %s:%s...", host, port)
    client.connect(host, port, keepalive=60)
    client.loop_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Escuta mensagens MQTT do hardware ineficiente e salva packets em CSV."
    )
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", DEFAULT_PORT)))
    parser.add_argument("--topic", default=os.getenv("MQTT_TOPIC", DEFAULT_TOPIC))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(os.getenv("MQTT_CSV_OUTPUT", DEFAULT_OUTPUT)),
        help="Caminho do CSV de saida.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    args = parse_args()
    run_logger(args.host, args.port, args.topic, args.output)


if __name__ == "__main__":
    main()
