// Configuration for ESP32 firmware
#pragma once

// WiFi credentials (override at build time or use WiFiManager)
#define WIFI_SSID "your_ssid"
#define WIFI_PASS "your_password"

// MQTT broker
#define MQTT_BROKER_IP "192.168.1.100"
#define MQTT_BROKER_PORT 1883

// Device identifier
#define DEVICE_ID "esp32_001"

// Scan settings
#define SCAN_INTERVAL_MS 30000
#define MAX_WIFI_RESULTS 20

// MQTT topic
#define MQTT_TOPIC "esp32/wifi/scan"

// Promiscuous capture
#define PROMISCUOUS_MODE_ENABLED 1
