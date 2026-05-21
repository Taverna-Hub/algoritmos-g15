"""
Mock WiFi Scanner - Simulates ESP32 publishing WiFi probe request packets via MQTT.
"""

import paho.mqtt.client as mqtt
import json
import random
import time
import logging
from datetime import datetime, timezone
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock MAC addresses and their details
MOCK_DEVICES = [
    {"mac": "AA:BB:CC:DD:EE:01", "ssid": "WiFi-Network-1", "rssi_base": -55},
    {"mac": "AA:BB:CC:DD:EE:02", "ssid": "WiFi-Network-2", "rssi_base": -65},
    {"mac": "AA:BB:CC:DD:EE:03", "ssid": "", "rssi_base": -75},
    {"mac": "5C:F3:70:11:22:33", "ssid": "Samsung-TV", "rssi_base": -60},
    {"mac": "D8:BB:C1:44:55:66", "ssid": "TP-Link-Router", "rssi_base": -45},
    {"mac": "2C:F0:EE:77:88:99", "ssid": "Huawei-Phone", "rssi_base": -70},
    {"mac": "B4:B0:24:AA:BB:CC", "ssid": "Xiaomi-Device", "rssi_base": -65},
    {"mac": "00:1A:2B:DD:EE:FF", "ssid": "Cisco-Access-Point", "rssi_base": -50},
]

FREQUENCIES = [2412, 2437, 2462, 2472, 5180, 5200, 5220]
CHANNEL_MAP = {
    2412: 1,
    2437: 6,
    2462: 11,
    2472: 13,
    5180: 36,
    5200: 40,
    5220: 44,
}


def utcnow_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MockESP32:
    def __init__(self, broker_host="localhost", broker_port=1883, publish_topic="esp32/wifi/scan"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.publish_topic = publish_topic
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.connected = False
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.connected = True
        else:
            logger.error(f"Connection failed with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection: {rc}")
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from broker."""
        self.client.loop_stop()
        self.client.disconnect()
    
    def generate_probe_data(self, num_devices=None):
        """Generate mock WiFi probe request packets."""
        if num_devices is None:
            # Randomly select how many devices to include (between 3-8)
            num_devices = random.randint(3, min(8, len(MOCK_DEVICES)))
        
        # Randomly select devices
        devices = random.sample(MOCK_DEVICES, min(num_devices, len(MOCK_DEVICES)))
        
        packets = {
            "timestamp": utcnow_iso(),
            "message_type": "probe_requests",
            "device_id": "ESP32-001",
            "packets": []
        }
        
        for device in devices:
            # Add random variance to RSSI (±5 dBm)
            rssi = device["rssi_base"] + random.randint(-5, 5)
            frequency = random.choice(FREQUENCIES)
            
            packets["packets"].append({
                "timestamp": utcnow_iso(),
                "frame_type": "management",
                "subtype": "probe_request",
                "source_mac": device["mac"],
                "destination_mac": "FF:FF:FF:FF:FF:FF",
                "bssid": "FF:FF:FF:FF:FF:FF",
                "ssid": device["ssid"],
                "channel": CHANNEL_MAP.get(frequency, 1),
                "frequency": frequency,
                "rssi": rssi,
                "sequence_number": random.randint(1, 4095),
                "frame_control": "0x0040",
                "snr": max(0, 45 + rssi),
            })
        
        return packets
    
    def publish_probe_packets(self, num_devices=None):
        """Publish probe request packets."""
        if not self.connected:
            logger.warning("Not connected to broker, cannot publish")
            return False
        
        try:
            probe_data = self.generate_probe_data(num_devices)
            payload = json.dumps(probe_data)
            
            self.client.publish(self.publish_topic, payload, qos=1)
            logger.info(f"Published probe capture with {len(probe_data['packets'])} packets to {self.publish_topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish: {e}")
            return False
    
    def start_scanning(self, interval=5):
        """Start publishing scans at regular intervals."""
        try:
            logger.info(f"Starting mock WiFi probe capture (interval: {interval}s)")
            while True:
                self.publish_probe_packets()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Probe capture stopped by user")


def main():
    parser = argparse.ArgumentParser(description="Mock ESP32 WiFi probe request generator")
    parser.add_argument("--host", default="localhost", help="MQTT broker host (default: localhost)")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    parser.add_argument("--topic", default="esp32/wifi/scan", help="MQTT topic to publish to")
    parser.add_argument("--interval", type=int, default=5, help="Interval between scans in seconds")
    parser.add_argument("--single", action="store_true", help="Publish single scan and exit")
    
    args = parser.parse_args()
    
    # Create and start mock ESP32
    mock_esp32 = MockESP32(
        broker_host=args.host,
        broker_port=args.port,
        publish_topic=args.topic
    )
    
    try:
        mock_esp32.connect()
        
        if args.single:
            # Publish single probe capture
            mock_esp32.publish_probe_packets()
        else:
            # Start continuous probe capture
            mock_esp32.start_scanning(interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        mock_esp32.disconnect()


if __name__ == "__main__":
    main()
