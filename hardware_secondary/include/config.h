// Configuration for ESP8266 event publisher
#pragma once

// WiFi credentials
#define WIFI_SSID "uaifai-tiradentes"
#define WIFI_PASS "bemvindoaocesar"

// MQTT broker (reuse from hardware)
#define MQTT_BROKER_IP "172.26.67.34"
#define MQTT_BROKER_PORT 1883

// MQTT topic for events
#define MQTT_TOPIC "esp8266/event"

// Device identifier
#define DEVICE_ID "esp8266_001"

// Timeouts
#define WIFI_CONNECT_TIMEOUT_MS 10000
#define MQTT_KEEPALIVE_SEC 60
#define MQTT_SOCKET_TIMEOUT_MS 8000
