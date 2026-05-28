import csv
import re
from pathlib import Path
from urllib.request import urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "backend" / "app" / "data" / "mac_vendors.csv"

SOURCES = [
    ("MA-L", 24, "https://standards-oui.ieee.org/oui/oui.csv"),
    ("MA-M", 28, "https://standards-oui.ieee.org/oui28/mam.csv"),
    ("MA-S", 36, "https://standards-oui.ieee.org/oui36/oui36.csv"),
]


def clean_hex(value: str) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", value or "").upper()


def clean_vendor(value: str) -> str:
    return " ".join((value or "").split())


def read_source(registry: str, prefix_bits: int, url: str) -> list[dict[str, str]]:
    expected_nibbles = prefix_bits // 4

    with urlopen(url, timeout=30) as response:
        text = response.read().decode("utf-8-sig")

    rows: list[dict[str, str]] = []
    reader = csv.DictReader(text.splitlines())

    for row in reader:
        assignment = clean_hex(row.get("Assignment", ""))
        vendor = clean_vendor(row.get("Organization Name", ""))

        if len(assignment) < expected_nibbles or not vendor:
            continue

        rows.append({
            "prefix_bits": str(prefix_bits),
            "prefix_hex": assignment[:expected_nibbles],
            "vendor": vendor,
            "registry": registry,
        })

    return rows


def main() -> None:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for registry, prefix_bits, url in SOURCES:
        for row in read_source(registry, prefix_bits, url):
            key = (row["prefix_bits"], row["prefix_hex"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)

    rows.sort(key=lambda row: (int(row["prefix_bits"]), row["prefix_hex"]))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["prefix_bits", "prefix_hex", "vendor", "registry"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} MAC vendor records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
