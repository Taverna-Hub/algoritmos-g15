import paho.mqtt.client as mqtt
import json
import logging
from typing import Callable, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MQTTClient:
    """MQTT Client for receiving WiFi data from Node-RED."""
    
    def __init__(self, on_message_callback: Optional[Callable] = None):
        """
        Initialize MQTT client.
        
        Args:
            on_message_callback: Callback function when message is received
        """
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.on_message_callback = on_message_callback
        self.connected = False
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
    
    def _on_connect(self, client, userdata, flags, rc):
        """Called when connected to broker."""
        if rc == 0:
            logger.info("MQTT connected successfully")
            self.connected = True
            # Subscribe to topic
            client.subscribe(settings.mqtt_subscribe_topic)
            logger.info(f"Subscribed to {settings.mqtt_subscribe_topic}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Called when disconnected from broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {rc}")
        else:
            logger.info("MQTT disconnected")
    
    def _on_message(self, client, userdata, msg):
        """Called when message is received."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"Received MQTT message: {msg.topic}")
            
            if self.on_message_callback:
                self.on_message_callback(payload)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from MQTT: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Called when subscription is acknowledged."""
        logger.debug(f"Subscribed with QoS: {granted_qos}")
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            if settings.mqtt_username and settings.mqtt_password:
                self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
            
            logger.info(f"Connecting to MQTT broker at {settings.mqtt_broker}:{settings.mqtt_port}")
            self.client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self.connected
