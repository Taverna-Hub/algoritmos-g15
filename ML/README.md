# ML - Machine Learning Module

Machine learning module for WiFi device analysis, implemented as a Notebook service.

## Features

- **OS Identification**: Identify device operating system based on MAC OUI
- **Distance Estimation**: Estimate device distance using RSSI and frequency
- **Location Detection**: Determine if device is inside or outside
- **Batch Processing**: Analyze multiple devices at once

## Current Status

This module processes validated data from Node-RED and persists analysis results to the shared database.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Standalone

```bash
python notebook.py
```

The notebook service listens on the Node-RED output topic and saves processed device records into the database.

### In Python

```python
from ML.notebook import process_payload

payload = {
    "timestamp": "2026-05-19T10:30:45Z",
    "devices": [
        {"mac": "AA:BB:CC:DD:EE:01", "rssi": -55, "frequency": 2412, "ssid": "Test"}
    ]
}

process_payload(payload)
```

## Output Format

```json
{
  "mac_address": "AA:BB:CC:DD:EE:01",
  "so_identified": "Apple",
  "distance_estimated": 2.45,
  "location": "inside",
  "confidence": 0.75
}
```

## Distance Estimation

Uses simplified path loss model:

- **Formula**: Distance = 10^((TxPower - RSSI) / (10 \* N))
- **TxPower**: -30 dBm (typical WiFi)
- **N (path loss coefficient)**: 2.0 for 5GHz, 2.5 for 2.4GHz

## Location Detection

- **Inside**: RSSI > -70 dBm (strong signal)
- **Outside**: RSSI ≤ -70 dBm (weak signal)

## Future Enhancements

Phase 2+ will include:

- Real ML models for OS identification
- Advanced distance estimation using multiple frequencies
- Device type classification (phone, laptop, IoT, etc.)
- Crowd analysis and heat mapping
- Temporal pattern recognition

## Integration with Backend

The backend can call this notebook via:

- HTTP API (if exposed)
- Direct Python import
- Queue-based async processing

Currently, the backend includes the ML logic directly using `MLService`.
