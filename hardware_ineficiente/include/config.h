// Configuration for ESP32 inefficient algorithm firmware
#pragma once

// WiFi credentials
#define WIFI_SSID "uaifai-tiradentes"
#define WIFI_PASS "bemvindoaocesar"

// MQTT broker. Use your computer's LAN IP, not localhost.
#define MQTT_BROKER_IP "172.26.67.34"
#define MQTT_BROKER_PORT 1883
#define MQTT_TOPIC "esp32/wifi/scan"

// Device identifier
#define DEVICE_ID "esp32_ineficiente_001"

// Capture settings
#define SCAN_INTERVAL_MS 30000
#define CAPTURE_WINDOW_MS 10000
#define CHANNEL_HOLD_MS 250
#define WIFI_CHANNEL_MIN 1
#define WIFI_CHANNEL_MAX 13
#define MAX_CAPTURED_DEVICES 64
#define PROBE_QUEUE_LENGTH 128
#define SERIAL_PRINT_CAPTURED_MACS 1

// Inefficient algorithm settings
#define INEFFICIENT_MAX_SAMPLES 20000
#define SERIAL_PRINT_PERFORMANCE 1
#define INEFFICIENT_PUBLISH_DELAY_MS 0

// Network timeouts
#define WIFI_CONNECT_TIMEOUT_MS 30000
#define MQTT_CONNECT_ATTEMPTS 3
#define MQTT_CONNECT_RETRY_MS 1500

// MQTT payload sizing
#define MQTT_BUFFER_SIZE 8192
#define MQTT_JSON_DOCUMENT_SIZE 12288
