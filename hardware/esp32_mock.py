"""
Direct mock of ESP32 - simulates WiFi probe request packets.
"""

import json
import random
from datetime import datetime, timezone
from typing import List, Dict


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MockWiFiScanner:
    """Simulates WiFi probe request capture functionality of ESP32."""
    
    AVAILABLE_DEVICES = [
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
    
    def __init__(self, active_device_probability=0.7):
        """
        Initialize mock WiFi scanner.
        
        Args:
            active_device_probability: Probability (0-1) that a device is visible in scan
        """
        self.active_device_probability = active_device_probability
    
    def _generate_probe_packet(self, device: Dict) -> Dict:
        """Create a probe request packet for a device."""
        rssi = device["rssi_base"] + random.randint(-8, 8)
        frequency = random.choice(self.FREQUENCIES)
        channel_map = {
            2412: 1,
            2437: 6,
            2462: 11,
            2472: 13,
            5180: 36,
            5200: 40,
            5220: 44,
        }

        return {
            "timestamp": utcnow_iso(),
            "frame_type": "management",
            "subtype": "probe_request",
            "source_mac": device["mac"],
            "destination_mac": "FF:FF:FF:FF:FF:FF",
            "bssid": "FF:FF:FF:FF:FF:FF",
            "ssid": device["ssid"],
            "channel": channel_map.get(frequency, 1),
            "frequency": frequency,
            "rssi": rssi,
            "sequence_number": random.randint(1, 4095),
            "frame_control": "0x0040",
            "snr": max(0, 45 + rssi),
        }

    def capture_probe_requests(self) -> List[Dict]:
        """
        Simulate capture of WiFi probe request packets.

        Returns:
            List of detected probe request packets with their details
        """
        detected_packets = []
        
        for device in self.AVAILABLE_DEVICES:
            # Randomly determine if device is detected in this scan
            if random.random() < self.active_device_probability:
                detected_packets.append(self._generate_probe_packet(device))
        
        return detected_packets
    
    def get_probe_data(self) -> Dict:
        """
        Get formatted WiFi probe data.
        
        Returns:
            Dictionary with probe packets ready to send
        """
        packets = self.capture_probe_requests()
        
        return {
            "timestamp": utcnow_iso(),
            "message_type": "probe_requests",
            "device_id": "ESP32-001",
            "packets": packets
        }
    
    def get_scan_data(self) -> Dict:
        """Backward-compatible alias for older scan data callers."""
        return self.get_probe_data()

    def get_probe_json(self) -> str:
        """Get probe data as JSON string."""
        return json.dumps(self.get_probe_data(), indent=2)

    def get_scan_json(self) -> str:
        """Backward-compatible alias for older scan JSON callers."""
        return self.get_probe_json()


class MockESP32Device:
    """Mock ESP32 with WiFi scanning capabilities."""
    
    def __init__(self, device_id="ESP32-001"):
        self.device_id = device_id
        self.scanner = MockWiFiScanner()
        self.scan_count = 0
    
    def perform_scan(self) -> Dict:
        """Capture probe packets and return results."""
        self.scan_count += 1
        probe_data = self.scanner.get_probe_data()
        probe_data["device_id"] = self.device_id
        probe_data["scan_count"] = self.scan_count
        probe_data["captured_at"] = utcnow_iso()
        return probe_data
    
    def get_device_info(self) -> Dict:
        """Get device information."""
        return {
            "device_id": self.device_id,
            "type": "ESP32",
            "scan_count": self.scan_count,
            "last_scan": utcnow_iso()
        }


if __name__ == "__main__":
    # Test the mock
    esp32 = MockESP32Device()
    
    print("=== ESP32 Mock Device Test ===\n")
    print("Device Info:")
    print(json.dumps(esp32.get_device_info(), indent=2))
    print("\n--- Probe Capture 1 ---")
    print(json.dumps(esp32.perform_scan(), indent=2))
    print("\n--- Probe Capture 2 ---")
    print(json.dumps(esp32.perform_scan(), indent=2))
