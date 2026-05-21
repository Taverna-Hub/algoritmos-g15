"""
Mock ML Notebook - Simulates machine learning analysis for WiFi devices.
Can be used standalone or via HTTP API.
"""

import json
import logging
from typing import Dict, Optional
from app_utils import MLService  # Import from backend if available

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockMLNotebook:
    """Mock ML notebook for device analysis."""
    
    def __init__(self):
        """Initialize mock ML notebook."""
        self.analysis_count = 0
        self.ml_service = self._init_ml_service()
    
    def _init_ml_service(self):
        """Initialize ML service (from backend or local)."""
        try:
            # Try to import from backend
            import sys
            sys.path.insert(0, '../backend')
            from app.services.ml_service import MLService
            return MLService
        except ImportError:
            logger.warning("Could not import from backend, using inline implementation")
            return None
    
    def analyze_device(self, mac_address: str, rssi: int, frequency: int = 2412) -> Dict:
        """
        Analyze device using ML models.
        
        Args:
            mac_address: Device MAC address
            rssi: Received Signal Strength Indicator
            frequency: WiFi frequency in MHz
            
        Returns:
            Analysis results
        """
        self.analysis_count += 1
        
        if self.ml_service:
            return self.ml_service.analyze_device(mac_address, rssi, frequency)
        else:
            # Inline implementation
            return {
                "mac_address": mac_address,
                "so_identified": self._identify_os_mock(mac_address),
                "distance_estimated": self._estimate_distance_mock(rssi, frequency),
                "location": self._determine_location_mock(rssi),
                "confidence": 0.75,
                "analysis_number": self.analysis_count
            }
    
    @staticmethod
    def _identify_os_mock(mac_address: str) -> str:
        """Mock OS identification."""
        mac_upper = mac_address.upper()
        
        if mac_upper.startswith("AA:BB"):
            return "Apple"
        elif mac_upper.startswith("5C:F3"):
            return "Samsung"
        elif mac_upper.startswith("D8:BB"):
            return "TP-Link"
        elif mac_upper.startswith("2C:F0"):
            return "Huawei"
        elif mac_upper.startswith("B4:B0"):
            return "Xiaomi"
        elif mac_upper.startswith("00:"):
            return "Legacy/Unknown"
        else:
            return "Unknown"
    
    @staticmethod
    def _estimate_distance_mock(rssi: int, frequency: int) -> float:
        """Mock distance estimation."""
        if rssi is None or rssi == 0:
            return 0.0
        
        tx_power = -30
        n = 2.0 if frequency > 2500 else 2.5
        distance = 10 ** ((tx_power - rssi) / (10 * n))
        return round(distance, 2)
    
    @staticmethod
    def _determine_location_mock(rssi: int) -> str:
        """Mock location determination."""
        return "inside" if rssi > -70 else "outside"
    
    def batch_analyze(self, devices: list) -> list:
        """
        Analyze multiple devices.
        
        Args:
            devices: List of device data
            
        Returns:
            List of analysis results
        """
        results = []
        for device in devices:
            result = self.analyze_device(
                device.get("mac"),
                device.get("rssi", -70),
                device.get("frequency", 2412)
            )
            results.append(result)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get notebook statistics."""
        return {
            "analysis_count": self.analysis_count,
            "status": "running"
        }


def main():
    """Test the mock ML notebook."""
    notebook = MockMLNotebook()
    
    print("=== Mock ML Notebook Test ===\n")
    
    # Test single device analysis
    print("Single Device Analysis:")
    result = notebook.analyze_device("AA:BB:CC:DD:EE:01", -55, 2412)
    print(json.dumps(result, indent=2))
    
    print("\n--- Batch Analysis ---")
    test_devices = [
        {"mac": "AA:BB:CC:DD:EE:01", "rssi": -55, "frequency": 2412},
        {"mac": "5C:F3:70:11:22:33", "rssi": -60, "frequency": 5180},
        {"mac": "D8:BB:C1:44:55:66", "rssi": -45, "frequency": 2437},
    ]
    
    batch_results = notebook.batch_analyze(test_devices)
    print(json.dumps(batch_results, indent=2))
    
    print("\n--- Statistics ---")
    print(json.dumps(notebook.get_statistics(), indent=2))


if __name__ == "__main__":
    main()
