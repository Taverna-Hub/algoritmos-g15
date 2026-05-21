# Node-RED - MQTT Broker & Data Orchestration

Node-RED acts as the central MQTT broker and orchestrator for WiFi data flow from ESP32 to the Notebook service.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed

### Start Node-RED and MQTT Broker

```bash
docker-compose up -d
```

This will start:

- **Node-RED**: http://localhost:1880
- **MQTT Broker (Mosquitto)**: localhost:1883

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
docker-compose logs -f node-red
docker-compose logs -f mosquitto
```

## Flows

The main flow performs these operations:

### Input: `esp32/wifi/scan`

- Receives raw WiFi scan data from ESP32 (real or mocked)
- Format:
  ```json
  {
    "timestamp": "2026-05-19T10:30:45Z",
    "devices": [
      {
        "mac": "AA:BB:CC:DD:EE:FF",
        "rssi": -65,
        "frequency": 2412,
        "ssid": "WiFiNetwork"
      }
    ]
  }
  ```

### Processing

1. **JSON Parse**: Parse incoming JSON
2. **Validate**:
   - Check data structure
   - Validate MAC address format
   - Ensure RSSI and frequency are numeric
3. **Transform**:
   - Normalize MAC addresses to uppercase
   - Add processing timestamp
   - Clean empty fields

### Output: `nodered/wifi/data`

- Publishes validated and transformed data
- Format (same as input, but validated):
  ```json
  {
    "timestamp": "2026-05-19T10:30:45Z",
    "devices": [
      {
        "mac": "AA:BB:CC:DD:EE:FF",
        "rssi": -65,
        "frequency": 2412,
        "ssid": "WiFiNetwork"
      }
    ]
  }
  ```

### Error Handling

- Invalid data publishes to `nodered/errors`
- All errors logged in Node-RED debug panel

## Access Node-RED UI

1. Open browser to `http://localhost:1880`
2. You'll see the flow editor
3. Click "Deploy" button to save changes
4. Use the Debug panel (right side) to see messages flowing through

## Importing Flows

The `flows.json` file is automatically loaded when Node-RED starts.

To manually import:

1. In Node-RED UI, click menu → Import
2. Paste the contents of `flows.json`
3. Click Import

## Testing

### Using MQTT CLI

Test publishing to esp32/wifi/scan:

```bash
mosquitto_pub -h localhost -t esp32/wifi/scan -m '{
  "timestamp": "2026-05-19T10:30:45Z",
  "devices": [
    {"mac": "AA:BB:CC:DD:EE:01", "rssi": -55, "frequency": 2412, "ssid": "Test"}
  ]
}'
```

Subscribe to output:

```bash
mosquitto_sub -h localhost -t nodered/wifi/data
```

### Hardware Source

Use a real ESP32 or another MQTT publisher to send WiFi scan payloads to `esp32/wifi/scan`.

## Configuration

### MQTT Broker Settings

Edit `docker-compose.yml` to:

- Change port mappings
- Add authentication
- Adjust volume mounts
- Change restart policies

### Node-RED Settings

Edit the flows to:

- Change input/output topics
- Add additional transformations
- Implement retry logic
- Add more validation rules

## Monitoring

Node-RED provides a debug panel to see:

- All messages flowing through the system
- Validation results
- Errors and warnings
- Processing times

Monitor MQTT topics with mosquitto_sub:

```bash
mosquitto_sub -h localhost -v -t "nodered/#"
mosquitto_sub -h localhost -v -t "esp32/#"
```

## Production Considerations

For production deployment:

- Enable authentication (username/password)
- Use TLS/SSL for MQTT
- Add message persistence
- Implement backup and recovery
- Monitor broker performance
- Set up proper logging
- Configure automatic restarts

## Troubleshooting

### MQTT connection refused

- Check if mosquitto container is running: `docker ps`
- Check logs: `docker-compose logs mosquitto`
- Verify firewall isn't blocking port 1883

### Node-RED can't connect to MQTT

- Check broker hostname (should be `mosquitto` for docker network)
- Verify network connectivity: `docker network ls`
- Check Node-RED logs

### No messages flowing

- Check if ESP32/mock is publishing to correct topic
- Verify topic names are spelled correctly
- Enable debug nodes in Node-RED to see message flow
- Use `mosquitto_sub` to verify messages are being published

## Documentation

- [Node-RED Official Docs](https://nodered.org/docs/)
- [Mosquitto Documentation](https://mosquitto.org/documentation/)
- [MQTT Protocol](http://mqtt.org/)
