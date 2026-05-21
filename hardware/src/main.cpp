// ESP32 firmware: WiFi scan + MQTT publish with promiscuous probe capture
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include <time.h>
#include "esp_wifi.h"
#include "esp_wifi_types.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastScanMillis = 0;

// Promiscuous probe capture
typedef struct {
  uint8_t mac[6];
  int8_t rssi;
  uint8_t channel;
  uint16_t seq;
  uint8_t frame_type; // 0=probe_req,1=probe_resp,2=beacon
  char ssid[33];
} ProbeEvent;

static QueueHandle_t probeQueue = NULL;
#define MAX_PROBE_PER_PUBLISH 64
#define MAX_PROBE_PARSE 250

String getIsoTimestamp() {
  time_t now = time(nullptr);
  if (now == 0) return String("");
  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  char buf[32];
  snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02dZ",
           timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
           timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
  return String(buf);
}

void connectToWiFi() {
  Serial.printf("Connecting to WiFi '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  Serial.println("Scanning for nearby access points...");
  int found = WiFi.scanNetworks();
  if (found <= 0) {
    Serial.println("No networks found");
  } else {
    for (int i = 0; i < found; ++i) {
      Serial.printf("  %d: %s (RSSI: %d)\n", i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i));
    }
  }
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 30000) {
    delay(500);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("WiFi connected, IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("WiFi connection failed (timeout)");
  }
}

void initNTP() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.println("NTP initialized");
}

bool mqttReconnect() {
  static int attempt = 0;
  if (mqttClient.connect(DEVICE_ID)) {
    Serial.println("MQTT connected");
    attempt = 0;
    return true;
  }
  attempt++;
  int backoff = min(60, (1 << min(attempt, 6)));
  Serial.printf("MQTT connect failed, retry in %ds\n", backoff);
  delay(backoff * 1000);
  return false;
}

int computeFrequencyFromChannel(int channel) {
  if (channel >= 1 && channel <= 14) return 2407 + channel * 5;
  if (channel >= 36) return 5000 + (channel - 36) * 5;
  return 0;
}

static void parseMgmtSSID(const uint8_t *payload, int length, bool hasFixedFields, char *outSSID, size_t outLen) {
  const uint8_t *ptr = payload;
  int remaining = length;
  if (hasFixedFields) {
    if (remaining <= 12) {
      outSSID[0] = '\0';
      return;
    }
    ptr += 12;
    remaining -= 12;
  }

  while (remaining >= 2) {
    uint8_t tagNumber = ptr[0];
    uint8_t tagLength = ptr[1];
    if ((int)tagLength + 2 > remaining) break;
    if (tagNumber == 0) {
      size_t copyLen = min((size_t)tagLength, outLen - 1);
      memcpy(outSSID, ptr + 2, copyLen);
      outSSID[copyLen] = '\0';
      return;
    }
    ptr += 2 + tagLength;
    remaining -= 2 + tagLength;
  }
  outSSID[0] = '\0';
}

extern "C" void wifi_promiscuous_rx(void *buf, wifi_promiscuous_pkt_type_t type) {
  if (!buf) return;
  if (type != WIFI_PKT_MGMT) return;

  wifi_promiscuous_pkt_t *ppkt = (wifi_promiscuous_pkt_t *)buf;
  wifi_pkt_rx_ctrl_t rx_ctrl = ppkt->rx_ctrl;
  const uint8_t *payload = ppkt->payload;
  if (!payload) return;

  uint16_t fc = ((uint16_t)payload[0]) | (((uint16_t)payload[1]) << 8);
  uint8_t type_field = (fc >> 2) & 0x3;
  uint8_t subtype = (fc >> 4) & 0xF;
  if (type_field != 0) return;
  if (!(subtype == 4 || subtype == 5 || subtype == 8)) return;

  ProbeEvent ev;
  memcpy(ev.mac, payload + 10, 6);
  ev.rssi = rx_ctrl.rssi;
  ev.channel = rx_ctrl.channel;
  ev.seq = ((uint16_t)payload[22]) | (((uint16_t)payload[23]) << 8);
  ev.frame_type = (subtype == 4) ? 0 : (subtype == 5 ? 1 : 2);
  ev.ssid[0] = '\0';

  int hdrLen = 24;
  bool hasFixed = (subtype == 5 || subtype == 8);
  parseMgmtSSID(payload + hdrLen, MAX_PROBE_PARSE, hasFixed, ev.ssid, sizeof(ev.ssid));

  if (probeQueue) {
    BaseType_t ok = xQueueSendFromISR(probeQueue, &ev, NULL);
    (void)ok;
  }
}

void enablePromiscuousMode() {
#if PROMISCUOUS_MODE_ENABLED
  if (!probeQueue) {
    probeQueue = xQueueCreate(128, sizeof(ProbeEvent));
    if (!probeQueue) {
      Serial.println("Failed to create probe queue");
      return;
    }
  }
  wifi_promiscuous_filter_t filt;
  filt.filter_mask = WIFI_PROMIS_FILTER_MASK_MGMT;
  esp_wifi_set_promiscuous_filter(&filt);
  esp_wifi_set_promiscuous_rx_cb(&wifi_promiscuous_rx);
  esp_wifi_set_promiscuous(true);
  Serial.println("Promiscuous mode enabled");
#else
  Serial.println("Promiscuous mode disabled");
#endif
}

void publishScanResults() {
  Serial.println("Starting WiFi scan...");
  int n = WiFi.scanNetworks();
  if (n < 0) {
    Serial.println("WiFi scan error");
  }
  int limit = min(max(n, 0), MAX_WIFI_RESULTS);

  DynamicJsonDocument doc(6144);
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = getIsoTimestamp();
  doc["source"] = "scan_and_probe";
  JsonArray results = doc.createNestedArray("scan_results");
  JsonArray probes = doc.createNestedArray("probe_results");

  for (int i = 0; i < limit; ++i) {
    JsonObject obj = results.createNestedObject();
    obj["ssid"] = WiFi.SSID(i);
    obj["mac_address"] = WiFi.BSSIDstr(i);
    obj["rssi"] = WiFi.RSSI(i);
    int channel = WiFi.channel(i);
    obj["channel"] = channel;
    obj["frequency"] = computeFrequencyFromChannel(channel);
    obj["is_hidden"] = false;
  }

#if PROMISCUOUS_MODE_ENABLED
  if (probeQueue) {
    ProbeEvent ev;
    int count = 0;
    while (xQueueReceive(probeQueue, &ev, 0) == pdTRUE && count < MAX_PROBE_PER_PUBLISH) {
      JsonObject p = probes.createNestedObject();
      char macstr[18];
      snprintf(macstr, sizeof(macstr), "%02X:%02X:%02X:%02X:%02X:%02X",
               ev.mac[0], ev.mac[1], ev.mac[2], ev.mac[3], ev.mac[4], ev.mac[5]);
      p["mac_address"] = String(macstr);
      p["rssi"] = ev.rssi;
      p["channel"] = ev.channel;
      p["frequency"] = computeFrequencyFromChannel(ev.channel);
      p["frame_type"] = ev.frame_type == 0 ? "probe_req" : (ev.frame_type == 1 ? "probe_resp" : "beacon");
      p["seq_number"] = ev.seq;
      p["ssid_requested"] = String(ev.ssid);
      count++;
    }
  }
#endif

  String payload;
  serializeJson(doc, payload);
  size_t len = payload.length();
  Serial.printf("Publishing %u bytes to %s\n", (unsigned)len, MQTT_TOPIC);
  if (!mqttClient.publish(MQTT_TOPIC, payload.c_str())) {
    Serial.println("MQTT publish failed");
  }
  WiFi.scanDelete();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  connectToWiFi();
  initNTP();

  mqttClient.setServer(MQTT_BROKER_IP, MQTT_BROKER_PORT);
  enablePromiscuousMode();
  lastScanMillis = millis();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!mqttClient.connected()) {
    mqttReconnect();
  }
  mqttClient.loop();

  if (millis() - lastScanMillis >= SCAN_INTERVAL_MS) {
    publishScanResults();
    lastScanMillis = millis();
  }
}
