# Backend - WiFi MAC Capture API

FastAPI backend for nearby WiFi MAC capture and signal analysis.

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- MQTT Broker and Node-RED for data orchestration

### Installation

1. Create virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/wifi_detection
```

4. Run migrations (if using Alembic):

```bash
alembic upgrade head
```

4. Run migrations (if using Alembic):

```bash
alembic upgrade head
```

### Running the API

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── routes/          # API endpoints
│   ├── mqtt/            # MQTT client
│   ├── services/        # Business logic (ML service)
│   ├── main.py          # FastAPI app
│   ├── config.py        # Configuration
│   └── database.py      # Database setup
├── requirements.txt     # Dependencies
├── .env                 # Environment variables
└── README.md
```

## API Endpoints

### Devices

- `GET /api/devices` - List all devices
- `GET /api/devices/{mac}` - Get device details
- `POST /api/devices` - Create/update device
- `GET /api/devices/{mac}/detections` - Get device detections

### History

- `GET /api/history/detections` - Get detection history
- `GET /api/history/stats` - Get statistics
- `GET /api/history/timeline` - Get timeline data

### System

- `GET /` - Root endpoint
- `GET /health` - Health check

## Features

- REST API for devices, history, and statistics
- Device OS identification using MAC OUI lookup
- Distance estimation using RSSI
- Detection history logging
- Statistics and aggregation
- Automatic database table creation

## Database Schema

### devices

- MAC address (unique)
- First/last seen timestamps
- RSSI, channel, frequency, frame type, seen count, SSID
- OS identification
- Distance estimation

### detections

- Device MAC
- Timestamp
- RSSI
- Channel and frequency
- Frame type and seen count
- Location (inside/outside)

### analysis

- Device MAC
- OS identified
- Distance estimated
- Confidence score
- Last updated

## Integration with Node-RED and Notebook

The backend consumes data only from the database. All MQTT ingestion and device analysis are handled by the Notebook service.

A separate notebook process subscribes to Node-RED output on topic `nodered/wifi/data` and persists analyzed device records to the shared database.
