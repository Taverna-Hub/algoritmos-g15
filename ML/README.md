# ML - Machine Learning Module

Machine learning models for WiFi device analysis (currently mocked).

## Features

- **OS Identification**: Identify device operating system based on MAC OUI
- **Distance Estimation**: Estimate device distance using RSSI and frequency
- **Location Detection**: Determine if device is inside or outside
- **Batch Processing**: Analyze multiple devices at once

## Current Status

This module is **MOCKED** for Phase 1. It provides:
- Deterministic OS identification based on MAC address patterns
- Simple RSSI-based distance estimation
- Location determination based on signal strength threshold

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Standalone

```bash
python notebook_mock.py
```

### In Python

```python
from notebook_mock import MockMLNotebook

notebook = MockMLNotebook()

# Analyze single device
result = notebook.analyze_device("AA:BB:CC:DD:EE:01", -55, 2412)
print(result)

# Batch analyze
devices = [
    {"mac": "AA:BB:CC:DD:EE:01", "rssi": -55, "frequency": 2412},
    {"mac": "5C:F3:70:11:22:33", "rssi": -60, "frequency": 5180},
]
results = notebook.batch_analyze(devices)
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
- **Formula**: Distance = 10^((TxPower - RSSI) / (10 * N))
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
