#include <stdio.h>
#include <string.h>
#include <errno.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "lwip/ip_addr.h"
#include "lwip/inet.h"
#include "lwip/sockets.h"
#include "espressif/esp8266/eagle_soc.h"
#include "espressif/esp8266/pin_mux_register.h"
#include "espressif/esp8266/uart_register.h"
#include "espressif/esp_system.h"
#include "espressif/esp_wifi.h"
#include "espressif/esp_sta.h"
#include "gpio.h"
#include "uart.h"
#include "config.h"

/**
 * IMPLEMENTAÇÃO NATIVA (ESP8266 RTOS SDK 1.5.0)
 * Sem dependência do framework Arduino.
 */

// Mapeamento de GPIOs para NodeMCU V3 (Nativo)
#define SENSOR_A_PIN 5
#define SENSOR_B_PIN 4

// No SDK 1.5.x as filas usam xQueueHandle em vez de QueueHandle_t
static xQueueHandle sensor_queue = NULL;

// Protótipos das Tasks
static void vTaskSensorA(void *pvParameters);
static void vTaskSensorB(void *pvParameters);
static void vTaskLogic(void *pvParameters);
static void vTaskNetworkInit(void *pvParameters);
static bool mqtt_publish_event(const char *event_label);
static bool wait_for_wifi(uint32 timeout_ms);
static void mqtt_build_client_id(char *buffer, size_t buffer_size);
static int mqtt_send_all(int socket_fd, const uint8 *data, size_t length);
static int mqtt_read_exact(int socket_fd, uint8 *buffer, size_t length);
static bool mqtt_read_connack(int socket_fd);
static size_t mqtt_encode_remaining_length(uint8 *buffer, size_t length);

void user_init(void) {
    UART_SetBaudrate(UART0, BIT_RATE_9600);

    // No SDK RTOS v1.5.0, as constantes podem variar.
    // Usamos PIN_FUNC_SELECT com os registradores do SOC
    PIN_FUNC_SELECT(PERIPHS_IO_MUX_GPIO5_U, FUNC_GPIO5);
    PIN_FUNC_SELECT(PERIPHS_IO_MUX_GPIO4_U, FUNC_GPIO4);
    
    // Configura como entrada via macros do gpio.h do SDK
    gpio_output_set(0, 0, 0, GPIO_ID_PIN(SENSOR_A_PIN));
    gpio_output_set(0, 0, 0, GPIO_ID_PIN(SENSOR_B_PIN));

    // Criação da fila para 10 caracteres
    sensor_queue = xQueueCreate(10, sizeof(char));

    if (sensor_queue != NULL) {
        // Criação das Tasks
        xTaskCreate(vTaskSensorA, (const signed char *)"SensorA", 256, NULL, 10, NULL);
        xTaskCreate(vTaskSensorB, (const signed char *)"SensorB", 256, NULL, 10, NULL);
        xTaskCreate(vTaskLogic, (const signed char *)"Logic", 512, NULL, 11, NULL);
        xTaskCreate(vTaskNetworkInit, (const signed char *)"NetInit", 384, NULL, 12, NULL);
        
        printf("\n--- ESP8266 RTOS SDK: Monitor iniciado ---\n");
    }
}

// Task do Sensor A: Monitora GPIO 5
static void vTaskSensorA(void *pvParameters) {
    int last_state = 1;
    for (;;) {
        // GPIO_INPUT_GET é a macro padrão para leitura de nível
        int current_state = GPIO_INPUT_GET(GPIO_ID_PIN(SENSOR_A_PIN));
        if (current_state == 0 && last_state == 1) {
            char msg = 'A';
            xQueueSend(sensor_queue, &msg, portMAX_DELAY);
            vTaskDelay(200 / portTICK_RATE_MS);
        }
        last_state = current_state;
        vTaskDelay(50 / portTICK_RATE_MS);
    }
}

// Task do Sensor B: Monitora GPIO 4
static void vTaskSensorB(void *pvParameters) {
    int last_state = 1;
    for (;;) {
        int current_state = GPIO_INPUT_GET(GPIO_ID_PIN(SENSOR_B_PIN));
        if (current_state == 0 && last_state == 1) {
            char msg = 'B';
            xQueueSend(sensor_queue, &msg, portMAX_DELAY);
            vTaskDelay(200 / portTICK_RATE_MS);
        }
        last_state = current_state;
        vTaskDelay(50 / portTICK_RATE_MS);
    }
}

/**
 * Funções Obrigatórias do SDK 1.5.0 para Linkagem
 */
uint32 user_rf_cal_sector_set(void) {
    return 1012; // Setor padrão para 4MB Flash
}

// Task de Lógica: Coordena Entrada/Saída
static void vTaskLogic(void *pvParameters) {
    char first_sensor = '\0';
    char received;
    
    for (;;) {
        // Aguarda um evento na fila (timeout de 3s)
        if (xQueueReceive(sensor_queue, &received, 3000 / portTICK_RATE_MS) == pdPASS) {
            if (first_sensor == '\0') {
                first_sensor = received;
            } else {
                if (first_sensor == 'A' && received == 'B') {
                    printf(">>> EVENTO: ENTRADA DETECTADA\n");
                    mqtt_publish_event("entrada");
                } else if (first_sensor == 'B' && received == 'A') {
                    printf(">>> EVENTO: SAIDA DETECTADA\n");
                    mqtt_publish_event("saida");
                }
                first_sensor = '\0';
            }
        } else {
            if (first_sensor != '\0') {
                first_sensor = '\0';
                printf("System Reset: Movimento incompleto.\n");
            }
        }
    }
}

static void vTaskNetworkInit(void *pvParameters) {
    struct station_config config;

    wifi_set_opmode_current(STATION_MODE);
    memset(&config, 0, sizeof(config));
    strncpy((char *)config.ssid, WIFI_SSID, sizeof(config.ssid) - 1);
    strncpy((char *)config.password, WIFI_PASS, sizeof(config.password) - 1);
    config.bssid_set = 0;

    wifi_station_set_config_current(&config);
    wifi_station_set_auto_connect(true);
    wifi_station_set_reconnect_policy(true);

    vTaskDelay(500 / portTICK_RATE_MS);
    wifi_station_connect();

    vTaskDelete(NULL);
}

static bool wait_for_wifi(uint32 timeout_ms) {
    uint32 waited = 0;

    while (waited < timeout_ms) {
        if (wifi_station_get_connect_status() == STATION_GOT_IP) {
            return true;
        }

        vTaskDelay(200 / portTICK_RATE_MS);
        waited += 200;
    }

    return false;
}

static void mqtt_build_client_id(char *buffer, size_t buffer_size) {
    snprintf(buffer, buffer_size, "%s_%06X", DEVICE_ID, (unsigned)system_get_chip_id());
}

static int mqtt_send_all(int socket_fd, const uint8 *data, size_t length) {
    size_t sent = 0;
    while (sent < length) {
        int result = send(socket_fd, data + sent, length - sent, 0);
        if (result <= 0) {
            printf("MQTT: send falhou result=%d errno=%d.\n", result, errno);
            return -1;
        }
        sent += (size_t)result;
    }
    return 0;
}

static int mqtt_read_exact(int socket_fd, uint8 *buffer, size_t length) {
    size_t received = 0;
    while (received < length) {
        int result = recv(socket_fd, buffer + received, length - received, 0);
        if (result <= 0) {
            if (result == 0) {
                printf("MQTT: broker fechou a conexao durante leitura (%u/%u bytes).\n",
                       (unsigned)received, (unsigned)length);
            } else {
                printf("MQTT: recv falhou result=%d errno=%d (%u/%u bytes).\n",
                       result, errno, (unsigned)received, (unsigned)length);
            }
            return -1;
        }
        received += (size_t)result;
    }
    return 0;
}

static bool mqtt_read_connack(int socket_fd) {
    uint8 fixed_header[2];
    if (mqtt_read_exact(socket_fd, fixed_header, sizeof(fixed_header)) < 0) {
        printf("MQTT: falha ao ler CONNACK.\n");
        return false;
    }

    if (fixed_header[0] != 0x20 || fixed_header[1] != 0x02) {
        printf("MQTT: CONNACK invalido header=%02X remaining=%02X.\n",
               fixed_header[0], fixed_header[1]);
        return false;
    }

    uint8 connack_payload[2];
    if (mqtt_read_exact(socket_fd, connack_payload, sizeof(connack_payload)) < 0) {
        printf("MQTT: falha ao ler payload do CONNACK.\n");
        return false;
    }

    if (connack_payload[1] != 0x00) {
        printf("MQTT: CONNACK recusado flags=%02X return_code=%u.\n",
               connack_payload[0], connack_payload[1]);
        return false;
    }

    printf("MQTT: CONNACK aceito flags=%02X return_code=%u.\n",
           connack_payload[0], connack_payload[1]);
    return true;
}

static size_t mqtt_encode_remaining_length(uint8 *buffer, size_t length) {
    size_t encoded = 0;
    do {
        uint8 digit = length % 128;
        length /= 128;
        if (length > 0) {
            digit |= 0x80;
        }
        buffer[encoded++] = digit;
    } while (length > 0 && encoded < 4);
    return encoded;
}

static bool mqtt_publish_event(const char *event_label) {
    if (!wait_for_wifi(WIFI_CONNECT_TIMEOUT_MS)) {
        printf("MQTT: WiFi indisponivel, abortando envio.\n");
        return false;
    }

    int socket_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (socket_fd < 0) {
        printf("MQTT: falha ao abrir socket.\n");
        return false;
    }

    int timeout_ms = MQTT_SOCKET_TIMEOUT_MS;
    setsockopt(socket_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout_ms, sizeof(timeout_ms));
    setsockopt(socket_fd, SOL_SOCKET, SO_SNDTIMEO, &timeout_ms, sizeof(timeout_ms));

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(MQTT_BROKER_PORT);
    server_addr.sin_addr.s_addr = inet_addr(MQTT_BROKER_IP);

    if (connect(socket_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        printf("MQTT: falha ao conectar no broker %s:%d errno=%d.\n",
               MQTT_BROKER_IP, MQTT_BROKER_PORT, errno);
        close(socket_fd);
        return false;
    }

    char client_id[48];
    mqtt_build_client_id(client_id, sizeof(client_id));
    printf("MQTT: TCP conectado em %s:%d client_id=%s.\n",
           MQTT_BROKER_IP, MQTT_BROKER_PORT, client_id);

    uint8 connect_packet[128];
    size_t offset = 0;
    connect_packet[offset++] = 0x10;

    uint8 variable_header[10];
    size_t vh_len = 0;
    variable_header[vh_len++] = 0x00;
    variable_header[vh_len++] = 0x04;
    variable_header[vh_len++] = 'M';
    variable_header[vh_len++] = 'Q';
    variable_header[vh_len++] = 'T';
    variable_header[vh_len++] = 'T';
    variable_header[vh_len++] = 0x04;
    variable_header[vh_len++] = 0x02;
    variable_header[vh_len++] = (MQTT_KEEPALIVE_SEC >> 8) & 0xFF;
    variable_header[vh_len++] = MQTT_KEEPALIVE_SEC & 0xFF;

    uint8 payload[64];
    size_t payload_len = 0;
    size_t client_id_len = strlen(client_id);
    payload[payload_len++] = (client_id_len >> 8) & 0xFF;
    payload[payload_len++] = client_id_len & 0xFF;
    memcpy(payload + payload_len, client_id, client_id_len);
    payload_len += client_id_len;

    size_t remaining_length = vh_len + payload_len;
    offset += mqtt_encode_remaining_length(connect_packet + offset, remaining_length);
    memcpy(connect_packet + offset, variable_header, vh_len);
    offset += vh_len;
    memcpy(connect_packet + offset, payload, payload_len);
    offset += payload_len;

    printf("MQTT: enviando CONNECT MQTT 3.1.1 (%u bytes, remaining=%u).\n",
           (unsigned)offset, (unsigned)remaining_length);
        
    if (mqtt_send_all(socket_fd, connect_packet, offset) < 0) {
        printf("MQTT: falha ao enviar CONNECT.\n");
        close(socket_fd);
        return false;
    }

    if (!mqtt_read_connack(socket_fd)) {
        close(socket_fd);
        return false;
    }

    uint32 timestamp_ms = system_get_time() / 1000;
    char payload_json[128];
    int payload_size = snprintf(payload_json, sizeof(payload_json),
                                "{\"device_id\":\"%s\",\"event\":\"%s\",\"ts\":%u}",
                                DEVICE_ID, event_label, (unsigned)timestamp_ms);
    if (payload_size <= 0 || payload_size >= (int)sizeof(payload_json)) {
        printf("MQTT: payload invalido.\n");
        close(socket_fd);
        return false;
    }

    uint8 publish_packet[256];
    size_t publish_offset = 0;
    publish_packet[publish_offset++] = 0x30;

    size_t topic_len = strlen(MQTT_TOPIC);
    size_t publish_remaining = 2 + topic_len + (size_t)payload_size;
    publish_offset += mqtt_encode_remaining_length(publish_packet + publish_offset, publish_remaining);
    publish_packet[publish_offset++] = (topic_len >> 8) & 0xFF;
    publish_packet[publish_offset++] = topic_len & 0xFF;
    memcpy(publish_packet + publish_offset, MQTT_TOPIC, topic_len);
    publish_offset += topic_len;
    memcpy(publish_packet + publish_offset, payload_json, payload_size);
    publish_offset += (size_t)payload_size;

    if (mqtt_send_all(socket_fd, publish_packet, publish_offset) < 0) {
        printf("MQTT: falha ao publicar evento.\n");
        close(socket_fd);
        return false;
    }

    close(socket_fd);
    printf("MQTT: evento publicado em %s.\n", MQTT_TOPIC);
    return true;
}
