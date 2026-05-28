from typing import Optional, Dict
import logging

from app.services.vendor_lookup import identify_vendor

logger = logging.getLogger(__name__)


class MLService:
    """Machine Learning service for device analysis."""
    
    @staticmethod
    def identify_vendor(mac_address: str) -> str:
        """
        Identify device vendor/company based on MAC address assignment.

        Args:
            mac_address: Device MAC address

        Returns:
            Identified vendor/company or fallback label
        """
        return identify_vendor(mac_address)

    @staticmethod
    def identify_os(mac_address: str) -> Optional[str]:
        """Backward-compatible alias for vendor identification."""
        return MLService.identify_vendor(mac_address)
    
    @staticmethod
    def estimate_distance(rssi: int, frequency: int = 2412) -> float:
        """
        Estimate distance based on RSSI and frequency.
        
        Uses simplified path loss formula:
        Distance = 10 ^ ((TxPower - RSSI) / (10 * N))
        
        Args:
            rssi: Received Signal Strength Indicator (typically -30 to -100)
            frequency: WiFi frequency in MHz (2412 for 2.4GHz, 5180+ for 5GHz)
            
        Returns:
            Estimated distance in meters
        """
        if rssi is None or rssi == 0:
            return 0.0
        
        # Reference power (TxPower) - typical value for WiFi
        tx_power = -30
        
        # Path loss coefficient (N) - adjusted for frequency
        if frequency > 2500:  # 5GHz
            n = 2.0
        else:  # 2.4GHz
            n = 2.5
        
        # Calculate distance
        distance = 10 ** ((tx_power - rssi) / (10 * n))
        
        return round(distance, 2)
    
    @staticmethod
    def determine_location(rssi: int) -> str:
        """
        Determine if device is inside or outside based on RSSI.
        
        Args:
            rssi: Received Signal Strength Indicator
            
        Returns:
            "inside" or "outside"
        """
        # Strong signal (> -70 dBm) typically means inside
        if rssi > -70:
            return "inside"
        return "outside"
    
    @staticmethod
    def analyze_device(mac_address: str, rssi: int, frequency: int = 2412) -> Dict:
        """
        Perform full analysis on a device.
        
        Args:
            mac_address: Device MAC address
            rssi: Received Signal Strength Indicator
            frequency: WiFi frequency in MHz
            
        Returns:
            Dictionary with analysis results
        """
        os_identified = MLService.identify_vendor(mac_address)
        distance = MLService.estimate_distance(rssi, frequency)
        location = MLService.determine_location(rssi)
        
        return {
            "mac_address": mac_address,
            "so_identified": os_identified,
            "distance_estimated": distance,
            "location": location,
            "confidence": 0.75,  # Mock confidence score
        }
