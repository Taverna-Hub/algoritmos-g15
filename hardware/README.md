# Hardware - Mock WiFi Scanner

Simulates an ESP32 publishing WiFi probe request packets via MQTT.

## Setup

### Prerequisites
- Python 3.8+
- MQTT Broker running (Node-RED or Mosquitto)

### Installation

```bash
pip install paho-mqtt
```

## Usage

### Basic usage - continuous probe capture
```bash
python mqtt_publisher.py
```

### Publish single probe capture and exit
```bash
python mqtt_publisher.py --single
```

### Custom MQTT broker
```bash
python mqtt_publisher.py --host 192.168.1.100 --port 1883 --topic esp32/wifi/scan
```

### Custom capture interval
```bash
python mqtt_publisher.py --interval 10  # 10 seconds between scans
```

## Options

- `--host` - MQTT broker host (default: localhost)
- `--port` - MQTT broker port (default: 1883)
- `--topic` - MQTT topic to publish to (default: esp32/wifi/scan)
- `--interval` - Interval between probe captures in seconds (default: 5)
- `--single` - Publish single probe capture and exit

## Output Format

The mock scanner publishes JSON data in this format:

```json
{
  "timestamp": "2026-05-19T10:30:45.123456Z",
  "message_type": "probe_requests",
  "device_id": "ESP32-001",
  "packets": [
    {
      "timestamp": "2026-05-19T10:30:45.123456Z",
      "frame_type": "management",
      "subtype": "probe_request",
      "source_mac": "AA:BB:CC:DD:EE:01",
      "destination_mac": "FF:FF:FF:FF:FF:FF",
      "bssid": "FF:FF:FF:FF:FF:FF",
      "ssid": "WiFi-Network-1",
      "channel": 1,
      "frequency": 2412,
      "rssi": -58,
      "sequence_number": 1234,
      "frame_control": "0x0040",
      "snr": 0
    },
    {
      "timestamp": "2026-05-19T10:30:45.123456Z",
      "frame_type": "management",
      "subtype": "probe_request",
      "source_mac": "5C:F3:70:11:22:33",
      "destination_mac": "FF:FF:FF:FF:FF:FF",
      "bssid": "FF:FF:FF:FF:FF:FF",
      "ssid": "Samsung-TV",
      "channel": 36,
      "frequency": 5180,
      "rssi": -63,
      "sequence_number": 567,
      "frame_control": "0x0040",
      "snr": 0
    }
  ]
}
```

## Mock Devices

The scanner includes 8 pre-configured mock devices:
- WiFi Network 1 & 2
- Samsung TV
- TP-Link Router
- Huawei Phone
- Xiaomi Device
- Cisco Access Point

Each device has:
- Unique MAC address
- SSID (network name)
- Base RSSI (±5dBm randomness added)
- Simulated frequency
- Probe request fields such as subtype, sequence number, and broadcast destination

## Integration with Node-RED

This mock scanner publishes to `esp32/wifi/scan` by default, but the payload now represents probe request packets and should be consumed by a Node-RED flow that validates and transforms the data before republishing to `nodered/wifi/data`.
