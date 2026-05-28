import csv
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "mac_vendors.csv"
UNKNOWN_VENDOR = "Desconhecido"
PRIVATE_VENDOR = "MAC privado/aleatorio"
MAX_VENDOR_LENGTH = 50


@dataclass(frozen=True)
class VendorRecord:
    prefix_bits: int
    prefix_hex: str
    vendor: str
    registry: str


def normalize_mac(mac_address: str | None) -> Optional[str]:
    if not mac_address:
        return None

    normalized = re.sub(r"[^0-9A-Fa-f]", "", mac_address).upper()
    if len(normalized) != 12 or not re.fullmatch(r"[0-9A-F]{12}", normalized):
        return None

    return normalized


def is_locally_administered(mac_hex: str) -> bool:
    first_octet = int(mac_hex[:2], 16)
    return bool(first_octet & 0x02)


def fit_vendor_name(vendor: str) -> str:
    vendor = " ".join((vendor or "").split())
    if not vendor:
        return UNKNOWN_VENDOR
    return vendor[:MAX_VENDOR_LENGTH]


@lru_cache(maxsize=1)
def load_vendor_records() -> dict[int, dict[str, VendorRecord]]:
    records: dict[int, dict[str, VendorRecord]] = {36: {}, 28: {}, 24: {}}

    if not DATA_FILE.exists():
        logger.warning("MAC vendor data file not found: %s", DATA_FILE)
        return records

    with DATA_FILE.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                prefix_bits = int(row["prefix_bits"])
            except (KeyError, TypeError, ValueError):
                continue

            if prefix_bits not in records:
                continue

            prefix_hex = re.sub(r"[^0-9A-Fa-f]", "", row.get("prefix_hex", "")).upper()
            expected_nibbles = prefix_bits // 4
            if len(prefix_hex) < expected_nibbles:
                continue

            prefix_hex = prefix_hex[:expected_nibbles]
            records[prefix_bits][prefix_hex] = VendorRecord(
                prefix_bits=prefix_bits,
                prefix_hex=prefix_hex,
                vendor=fit_vendor_name(row.get("vendor", "")),
                registry=row.get("registry", ""),
            )

    return records


def identify_vendor(mac_address: str | None) -> str:
    mac_hex = normalize_mac(mac_address)
    if not mac_hex:
        return UNKNOWN_VENDOR

    if is_locally_administered(mac_hex):
        return PRIVATE_VENDOR

    records = load_vendor_records()
    for prefix_bits in (36, 28, 24):
        prefix = mac_hex[: prefix_bits // 4]
        record = records[prefix_bits].get(prefix)
        if record:
            return record.vendor

    return UNKNOWN_VENDOR
