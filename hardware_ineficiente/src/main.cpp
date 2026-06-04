// ESP32 firmware: passive WiFi capture + intentionally inefficient MQTT publish
#include "config.h"

#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_wifi_types.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <stdlib.h>
#include <string.h>

struct ProbeEvent {
  uint8_t mac[6];
  int8_t rssi;
  uint8_t channel;
  uint8_t frameType;
};

struct InefficientSample {
  uint8_t mac[6];
  int8_t rssi;
  uint8_t channel;
  uint8_t frameType;
};

struct PerformanceStats {
  unsigned long runId;
  unsigned long timestampMs;
  uint32_t samples;
  uint32_t droppedSamples;
  uint32_t reallocFailures;
  uint32_t publishFailures;
  uint32_t publishSuccesses;
  unsigned long insertUsTotal;
  unsigned long serializeUsTotal;
  unsigned long publishUsTotal;
  size_t payloadBytesTotal;
  uint32_t freeHeap;
  uint32_t minFreeHeap;
};

WiFiClient espClient;
PubSubClient mqttClient(espClient);

static QueueHandle_t probeQueue = nullptr;
static InefficientSample *inefficientSamples = nullptr;
static size_t inefficientSampleCount = 0;
static char mqttPayload[MQTT_BUFFER_SIZE];
static unsigned long lastCaptureMillis = 0;
static unsigned long runCounter = 0;
static PerformanceStats performanceStats = {};

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

void resetPerformanceStats() {
  memset(&performanceStats, 0, sizeof(performanceStats));
  performanceStats.runId = ++runCounter;
  performanceStats.timestampMs = millis();
}

void releaseInefficientSamples() {
  if (inefficientSamples) {
    free(inefficientSamples);
  }

  inefficientSamples = nullptr;
  inefficientSampleCount = 0;
}

void formatMac(const uint8_t mac[6], char *buffer, size_t bufferSize) {
  snprintf(buffer, bufferSize, "%02X:%02X:%02X:%02X:%02X:%02X",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

void storeInefficientSample(const ProbeEvent &event) {
  if (isIgnoredMac(event.mac)) {
    return;
  }

  const unsigned long startedAt = micros();

  if (inefficientSampleCount >= INEFFICIENT_MAX_SAMPLES) {
    performanceStats.droppedSamples++;
    performanceStats.insertUsTotal += micros() - startedAt;
    return;
  }

  const size_t newCount = inefficientSampleCount + 1;
  InefficientSample *resizedSamples = static_cast<InefficientSample *>(
      realloc(inefficientSamples, newCount * sizeof(InefficientSample)));

  if (!resizedSamples) {
    performanceStats.reallocFailures++;
    performanceStats.droppedSamples++;
    performanceStats.insertUsTotal += micros() - startedAt;
    return;
  }

  inefficientSamples = resizedSamples;

  // Anti-pattern required for the inefficient variant: shift the whole history
  // on each new reading, producing O(n) work per insertion.
  if (inefficientSampleCount > 0) {
    memmove(inefficientSamples + 1,
            inefficientSamples,
            inefficientSampleCount * sizeof(InefficientSample));
  }

  InefficientSample &sample = inefficientSamples[0];
  memcpy(sample.mac, event.mac, 6);
  sample.rssi = event.rssi;
  sample.channel = event.channel;
  sample.frameType = event.frameType;
  inefficientSampleCount = newCount;
  performanceStats.samples = static_cast<uint32_t>(inefficientSampleCount);
  performanceStats.insertUsTotal += micros() - startedAt;
}

void drainProbeQueue() {
  if (!probeQueue) {
    return;
  }

  ProbeEvent event;
  while (xQueueReceive(probeQueue, &event, 0) == pdTRUE) {
    storeInefficientSample(event);
  }
}

void printCapturedSamples() {
#if SERIAL_PRINT_CAPTURED_MACS
  if (inefficientSampleCount == 0) {
    Serial.println("No MAC addresses captured in this window");
    return;
  }

  Serial.println("Captured samples in inefficient dynamic list:");
  Serial.println("#  MAC Address        RSSI  Ch  Freq MHz  Frame");

  for (size_t i = 0; i < inefficientSampleCount; ++i) {
    const InefficientSample &sample = inefficientSamples[i];

    char mac[18];
    formatMac(sample.mac, mac, sizeof(mac));

    Serial.printf("%02u %s  %4d  %2u  %8d  %-10s\n",
                  static_cast<unsigned>(i + 1),
                  mac,
                  sample.rssi,
                  sample.channel,
                  computeFrequencyFromChannel(sample.channel),
                  frameTypeName(sample.frameType));
  }
#endif
}

void printPerformanceStats() {
#if SERIAL_PRINT_PERFORMANCE
  const double insertAvg = performanceStats.samples > 0
                               ? static_cast<double>(performanceStats.insertUsTotal) /
                                     static_cast<double>(performanceStats.samples)
                               : 0.0;
  const double publishAvg = performanceStats.publishSuccesses > 0
                                ? static_cast<double>(performanceStats.publishUsTotal) /
                                      static_cast<double>(performanceStats.publishSuccesses)
                                : 0.0;

  Serial.println("PERF_HEADER,run_id,timestamp,samples,insert_us_total,insert_us_avg,publish_us_total,publish_us_avg,free_heap,min_free_heap,publish_failures");
  Serial.printf("PERF_DATA,%lu,%lu,%u,%lu,%.2f,%lu,%.2f,%u,%u,%u\n",
                performanceStats.runId,
                performanceStats.timestampMs,
                performanceStats.samples,
                performanceStats.insertUsTotal,
                insertAvg,
                performanceStats.publishUsTotal,
                publishAvg,
                performanceStats.freeHeap,
                performanceStats.minFreeHeap,
                performanceStats.publishFailures);

  Serial.printf("PERF_DETAIL,dropped=%u,realloc_failures=%u,publish_successes=%u,serialize_us_total=%lu,payload_bytes_total=%u\n",
                performanceStats.droppedSamples,
                performanceStats.reallocFailures,
                performanceStats.publishSuccesses,
                performanceStats.serializeUsTotal,
                static_cast<unsigned>(performanceStats.payloadBytesTotal));
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
  Serial.printf("Starting inefficient passive WiFi capture for %lu ms\n",
                static_cast<unsigned long>(CAPTURE_WINDOW_MS));
#endif

  releaseInefficientSamples();
  resetPerformanceStats();
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

  performanceStats.freeHeap = ESP.getFreeHeap();
  performanceStats.minFreeHeap = ESP.getMinFreeHeap();

#if !SERIAL_PRINT_CAPTURED_MACS
  Serial.printf("Inefficient passive capture complete: %u samples captured\n",
                static_cast<unsigned>(inefficientSampleCount));
#endif
  printCapturedSamples();
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

bool publishOneSample(const InefficientSample &sample, size_t sequence) {
  DynamicJsonDocument doc(MQTT_JSON_DOCUMENT_SIZE);
  doc["device_id"] = DEVICE_ID;
  doc["algorithm"] = "ineficiente";
  doc["sequence"] = static_cast<unsigned>(sequence);

  JsonArray packets = doc.createNestedArray("packets");
  JsonObject packet = packets.createNestedObject();

  char mac[18];
  formatMac(sample.mac, mac, sizeof(mac));

  packet["source_mac"] = mac;
  packet["rssi"] = sample.rssi;
  packet["channel"] = sample.channel;
  packet["frequency"] = computeFrequencyFromChannel(sample.channel);
  packet["frame_type"] = frameTypeName(sample.frameType);
  packet["seen_count"] = 1;

  const unsigned long serializeStartedAt = micros();
  const size_t payloadSize = measureJson(doc);
  if (payloadSize >= MQTT_BUFFER_SIZE) {
    Serial.printf("MQTT payload too large: %u bytes (buffer %u)\n",
                  static_cast<unsigned>(payloadSize),
                  static_cast<unsigned>(MQTT_BUFFER_SIZE));
    performanceStats.publishFailures++;
    performanceStats.serializeUsTotal += micros() - serializeStartedAt;
    return false;
  }

  const size_t len = serializeJson(doc, mqttPayload, sizeof(mqttPayload));
  performanceStats.serializeUsTotal += micros() - serializeStartedAt;
  performanceStats.payloadBytesTotal += len;

  Serial.printf("Synchronously publishing inefficient sample %u/%u (%u bytes) to %s\n",
                static_cast<unsigned>(sequence + 1),
                static_cast<unsigned>(inefficientSampleCount),
                static_cast<unsigned>(len),
                MQTT_TOPIC);

  const unsigned long publishStartedAt = micros();
  const bool published = mqttClient.publish(MQTT_TOPIC, mqttPayload, len);
  performanceStats.publishUsTotal += micros() - publishStartedAt;

  if (!published) {
    Serial.printf("MQTT publish failed, rc=%d\n", mqttClient.state());
    performanceStats.publishFailures++;
    return false;
  }

  performanceStats.publishSuccesses++;
  mqttClient.loop();

#if INEFFICIENT_PUBLISH_DELAY_MS > 0
  delay(INEFFICIENT_PUBLISH_DELAY_MS);
#endif

  return true;
}

bool publishCaptureResults() {
  if (inefficientSampleCount == 0) {
    Serial.println("No captured samples to publish");
    printPerformanceStats();
    return true;
  }

  bool allPublished = true;
  for (size_t i = 0; i < inefficientSampleCount; ++i) {
    if (!publishOneSample(inefficientSamples[i], i)) {
      allPublished = false;
    }
  }

  performanceStats.freeHeap = ESP.getFreeHeap();
  performanceStats.minFreeHeap = ESP.getMinFreeHeap();
  printPerformanceStats();

  return allPublished;
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
    printPerformanceStats();
    lastCaptureMillis = millis();
    return;
  }

  if (connectToWiFi() && connectToMqtt()) {
    publishCaptureResults();
    mqttClient.loop();
  } else {
    performanceStats.publishFailures += static_cast<uint32_t>(inefficientSampleCount);
    performanceStats.freeHeap = ESP.getFreeHeap();
    performanceStats.minFreeHeap = ESP.getMinFreeHeap();
    printPerformanceStats();
  }

  lastCaptureMillis = millis();
}
