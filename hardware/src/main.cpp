// ESP32 firmware: passive WiFi device capture + MQTT publish
#include "config.h"

#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_wifi_types.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <string.h>

struct ProbeEvent {
  uint8_t mac[6];
  int8_t rssi;
  uint8_t channel;
  uint8_t frameType;
};

struct ObservedDevice {
  bool used;
  uint8_t mac[6];
  int8_t strongestRssi;
  uint8_t channel;
  uint8_t frameType;
  uint16_t seenCount;
};

WiFiClient espClient;
PubSubClient mqttClient(espClient);

static QueueHandle_t probeQueue = nullptr;
static ObservedDevice observedDevices[MAX_CAPTURED_DEVICES];
static char mqttPayload[MQTT_BUFFER_SIZE];
static unsigned long lastCaptureMillis = 0;

int computeFrequencyFromChannel(uint8_t channel);
void wifiPromiscuousRx(void *buf, wifi_promiscuous_pkt_type_t type);

const char *frameTypeName(uint8_t frameType) {
  switch (frameType) {
    case 0:
      return "probe_req";
    case 1:
      return "probe_resp";
    case 2:
      return "beacon";
    default:
      return "management";
  }
}

bool sameMac(const uint8_t left[6], const uint8_t right[6]) {
  return memcmp(left, right, 6) == 0;
}

bool wifiCredentialsConfigured() {
  return strcmp(WIFI_SSID, "your_ssid") != 0 &&
         strcmp(WIFI_PASS, "your_password") != 0 &&
         strlen(WIFI_SSID) > 0;
}

bool isIgnoredMac(const uint8_t mac[6]) {
  bool allZero = true;
  bool allBroadcast = true;

  for (int i = 0; i < 6; ++i) {
    allZero = allZero && mac[i] == 0x00;
    allBroadcast = allBroadcast && mac[i] == 0xFF;
  }

  return allZero || allBroadcast || (mac[0] & 0x01);
}

void resetObservedDevices() {
  memset(observedDevices, 0, sizeof(observedDevices));
}

void formatMac(const uint8_t mac[6], char *buffer, size_t bufferSize) {
  snprintf(buffer, bufferSize, "%02X:%02X:%02X:%02X:%02X:%02X",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

void aggregateProbeEvent(const ProbeEvent &event) {
  if (isIgnoredMac(event.mac)) {
    return;
  }

  int freeSlot = -1;

  for (int i = 0; i < MAX_CAPTURED_DEVICES; ++i) {
    ObservedDevice &device = observedDevices[i];

    if (!device.used) {
      if (freeSlot < 0) {
        freeSlot = i;
      }
      continue;
    }

    if (sameMac(device.mac, event.mac)) {
      device.seenCount++;
      if (event.rssi > device.strongestRssi) {
        device.strongestRssi = event.rssi;
        device.channel = event.channel;
        device.frameType = event.frameType;
      }
      return;
    }
  }

  if (freeSlot >= 0) {
    ObservedDevice &device = observedDevices[freeSlot];
    device.used = true;
    memcpy(device.mac, event.mac, 6);
    device.strongestRssi = event.rssi;
    device.channel = event.channel;
    device.frameType = event.frameType;
    device.seenCount = 1;
  }
}

void drainProbeQueue() {
  if (!probeQueue) {
    return;
  }

  ProbeEvent event;
  while (xQueueReceive(probeQueue, &event, 0) == pdTRUE) {
    aggregateProbeEvent(event);
  }
}

int observedCount() {
  int count = 0;
  for (int i = 0; i < MAX_CAPTURED_DEVICES; ++i) {
    if (observedDevices[i].used) {
      count++;
    }
  }
  return count;
}

void printObservedDevices() {
#if SERIAL_PRINT_CAPTURED_MACS
  const int count = observedCount();
  if (count == 0) {
    Serial.println("No MAC addresses captured in this window");
    return;
  }

  Serial.println("Captured MAC addresses:");
  Serial.println("#  MAC Address        RSSI  Ch  Freq MHz  Frame       Seen");

  int printed = 0;
  for (int i = 0; i < MAX_CAPTURED_DEVICES; ++i) {
    const ObservedDevice &device = observedDevices[i];
    if (!device.used) {
      continue;
    }

    char mac[18];
    formatMac(device.mac, mac, sizeof(mac));

    printed++;
    Serial.printf("%02d %s  %4d  %2u  %8d  %-10s  %u\n",
                  printed,
                  mac,
                  device.strongestRssi,
                  device.channel,
                  computeFrequencyFromChannel(device.channel),
                  frameTypeName(device.frameType),
                  device.seenCount);
  }
#endif
}

void configureRadioForCapture() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
}

void disconnectNetworkForCapture() {
  if (mqttClient.connected()) {
    mqttClient.disconnect();
  }

  WiFi.disconnect(true, false);
  delay(100);
  configureRadioForCapture();
}

void startPromiscuousCapture() {
  wifi_promiscuous_filter_t filter = {};
  filter.filter_mask = WIFI_PROMIS_FILTER_MASK_MGMT;

  esp_wifi_set_promiscuous(false);
  esp_wifi_set_promiscuous_filter(&filter);
  esp_wifi_set_promiscuous_rx_cb(&wifiPromiscuousRx);
  esp_wifi_set_promiscuous(true);
}

void stopPromiscuousCapture() {
  esp_wifi_set_promiscuous(false);
  esp_wifi_set_promiscuous_rx_cb(nullptr);
}

void runCaptureWindow() {
#if !SERIAL_PRINT_CAPTURED_MACS
  Serial.printf("Starting passive WiFi capture for %lu ms\n",
                (unsigned long)CAPTURE_WINDOW_MS);
#endif

  resetObservedDevices();
  drainProbeQueue();
  disconnectNetworkForCapture();
  startPromiscuousCapture();

  const unsigned long startedAt = millis();
  while (millis() - startedAt < CAPTURE_WINDOW_MS) {
    for (uint8_t channel = WIFI_CHANNEL_MIN; channel <= WIFI_CHANNEL_MAX; ++channel) {
      if (millis() - startedAt >= CAPTURE_WINDOW_MS) {
        break;
      }

      esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
      delay(CHANNEL_HOLD_MS);
      drainProbeQueue();
    }
  }

  stopPromiscuousCapture();
  drainProbeQueue();

#if !SERIAL_PRINT_CAPTURED_MACS
  Serial.printf("Passive capture complete: %d unique MACs observed\n", observedCount());
#endif
  printObservedDevices();
}

bool connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("WiFi already connected, IP: %s\n", WiFi.localIP().toString().c_str());
    return true;
  }

  Serial.printf("Connecting to WiFi '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  const unsigned long startedAt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startedAt < WIFI_CONNECT_TIMEOUT_MS) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("WiFi connected, IP: %s\n", WiFi.localIP().toString().c_str());
    return true;
  }

  Serial.println("WiFi connection failed");
  return false;
}

bool connectToMqtt() {
  if (mqttClient.connected()) {
    return true;
  }

  for (int attempt = 1; attempt <= MQTT_CONNECT_ATTEMPTS; ++attempt) {
    Serial.printf("Connecting to MQTT broker %s:%d (attempt %d/%d)...\n",
                  MQTT_BROKER_IP, MQTT_BROKER_PORT, attempt, MQTT_CONNECT_ATTEMPTS);

    if (mqttClient.connect(DEVICE_ID)) {
      Serial.println("MQTT connected");
      return true;
    }

    Serial.printf("MQTT connect failed, rc=%d\n", mqttClient.state());
    delay(MQTT_CONNECT_RETRY_MS);
  }

  return false;
}

bool publishCaptureResults() {
  const int count = observedCount();
  if (count == 0) {
    Serial.println("No captured MACs to publish");
    return true;
  }

  DynamicJsonDocument doc(MQTT_JSON_DOCUMENT_SIZE);
  doc["device_id"] = DEVICE_ID;

  JsonArray packets = doc.createNestedArray("packets");
  for (int i = 0; i < MAX_CAPTURED_DEVICES; ++i) {
    const ObservedDevice &device = observedDevices[i];
    if (!device.used) {
      continue;
    }

    char mac[18];
    formatMac(device.mac, mac, sizeof(mac));

    JsonObject packet = packets.createNestedObject();
    packet["source_mac"] = mac;
    packet["rssi"] = device.strongestRssi;
    packet["channel"] = device.channel;
    packet["frequency"] = computeFrequencyFromChannel(device.channel);
    packet["frame_type"] = frameTypeName(device.frameType);
    packet["seen_count"] = device.seenCount;
  }

  const size_t payloadSize = measureJson(doc);
  if (payloadSize >= MQTT_BUFFER_SIZE) {
    Serial.printf("MQTT payload too large: %u bytes (buffer %u)\n",
                  (unsigned)payloadSize, (unsigned)MQTT_BUFFER_SIZE);
    return false;
  }

  const size_t len = serializeJson(doc, mqttPayload, sizeof(mqttPayload));

  Serial.printf("Publishing %u bytes with %d MACs to %s\n",
                (unsigned)len, count, MQTT_TOPIC);

  if (!mqttClient.publish(MQTT_TOPIC, mqttPayload, len)) {
    Serial.printf("MQTT publish failed, rc=%d\n", mqttClient.state());
    return false;
  }

  Serial.println("MQTT publish succeeded");
  return true;
}

int computeFrequencyFromChannel(uint8_t channel) {
  if (channel >= 1 && channel <= 13) {
    return 2407 + channel * 5;
  }
  if (channel == 14) {
    return 2484;
  }
  return 0;
}

void wifiPromiscuousRx(void *buf, wifi_promiscuous_pkt_type_t type) {
  if (!buf || type != WIFI_PKT_MGMT) {
    return;
  }

  const wifi_promiscuous_pkt_t *packet = static_cast<wifi_promiscuous_pkt_t *>(buf);
  const wifi_pkt_rx_ctrl_t rxCtrl = packet->rx_ctrl;
  const uint8_t *payload = packet->payload;

  if (!payload || rxCtrl.sig_len < 24) {
    return;
  }

  const uint16_t frameControl = payload[0] | (payload[1] << 8);
  const uint8_t frameType = (frameControl >> 2) & 0x03;
  const uint8_t subtype = (frameControl >> 4) & 0x0F;

  if (frameType != 0 || !(subtype == 4 || subtype == 5 || subtype == 8)) {
    return;
  }

  ProbeEvent event;
  memcpy(event.mac, payload + 10, 6);
  event.rssi = rxCtrl.rssi;
  event.channel = rxCtrl.channel;
  event.frameType = subtype == 4 ? 0 : (subtype == 5 ? 1 : 2);

  if (probeQueue) {
    xQueueSendFromISR(probeQueue, &event, nullptr);
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  probeQueue = xQueueCreate(PROBE_QUEUE_LENGTH, sizeof(ProbeEvent));
  if (!probeQueue) {
    Serial.println("Failed to create probe event queue");
  }

  mqttClient.setServer(MQTT_BROKER_IP, MQTT_BROKER_PORT);
  mqttClient.setBufferSize(MQTT_BUFFER_SIZE);
  configureRadioForCapture();

  lastCaptureMillis = millis() - SCAN_INTERVAL_MS;
}

void loop() {
  if (millis() - lastCaptureMillis < SCAN_INTERVAL_MS) {
    if (mqttClient.connected()) {
      mqttClient.loop();
    }
    delay(50);
    return;
  }

  runCaptureWindow();

  if (!wifiCredentialsConfigured()) {
    Serial.println("WiFi credentials are not configured; skipping MQTT publish");
    lastCaptureMillis = millis();
    return;
  }

  if (connectToWiFi() && connectToMqtt()) {
    publishCaptureResults();
    mqttClient.loop();
  }

  lastCaptureMillis = millis();
}
