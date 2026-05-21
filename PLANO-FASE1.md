# Plano do Projeto: Detecção WiFi com ESP32

## 📋 Visão Geral

Sistema inteligente para detectar dispositivos WiFi próximos usando ESP32, identificar tipos de SO, estimar distância e visualizar dados em um dashboard. O backend atua como coordenador central recebendo dados via MQTT.

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONT (React)                             │
│          Dashboard + Visualização de Dados                   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────────┐
│                BACK (FastAPI)                                │
│      ┌──────────────────────────────────────────────┐       │
│      │ - API REST (dados para frontend)             │       │
│      │ - MQTT Client (se inscreve em tópicos)       │       │
│      │ - Processamento de dados                     │       │
│      │ - Banco de dados (persistência)              │       │
│      └──────────────────────────────────────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │ MQTT
        ┌────────────▼────────────────────┐
        │                                 │
┌───────▼──────────────────┐     ┌────────▼────────┐
│   Node-RED (Broker)      │     │   ML/Notebook   │
│  ┌────────────────────┐  │     │   (Mockado)     │
│  │ - MQTT Broker      │  │     │                 │
│  │ - Fluxos de dados  │  │     │ Processa dados  │
│  │ - Transformações   │  │     │ e retorna SOs   │
│  │ - Orquestração     │  │     │ e distâncias    │
│  └────────────────────┘  │     └─────────────────┘
│          ▲               │
│          │ MQTT          │
│    ┌─────┴──────┐        │
│    │            │        │
│ ┌──▼──┐    ┌───▼──┐     │
│ │ESP32│    │Mock  │     │
│ │Real │    │Hard- │     │
│ │     │    │ware  │     │
│ └─────┘    └──────┘     │
└────────────────────────┘
```

---

## 📁 Estrutura de Pastas

```
embarcados/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── device.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── device.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── devices.py
│   │   │   └── history.py
│   │   ├── mqtt/
│   │   │   ├── __init__.py
│   │   │   └── client.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── ml_service.py
│   ├── requirements.txt
│   ├── .env
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── DeviceList.jsx
│   │   │   ├── DeviceDetail.jsx
│   │   │   ├── HistoryChart.jsx
│   │   │   └── Filters.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── History.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
├── hardware/
│   ├── esp32_mock.py
│   ├── mqtt_publisher.py
│   └── README.md
│
├── ML/
│   ├── notebook_mock.py
│   ├── models/
│   ├── requirements.txt
│   └── README.md
│
├── nodered/
│   ├── flows.json
│   ├── docker-compose.yml
│   └── README.md
│
└── PLANO.md
```

---

## 🎯 Fase 1: Frontend + Backend (Mock de Hardware e ML)

### BACKEND - FastAPI

#### 1.1 Estrutura Base
- [ ] Setup inicial do projeto FastAPI
- [ ] Configurar banco de dados (PostgreSQL)
- [ ] Criar models de dados (Device, Log)
- [ ] Configurar variáveis de ambiente

#### 1.2 API REST
**Endpoints:**
- `GET /api/devices` - Lista dispositivos detectados atualmente
- `GET /api/devices/{mac}` - Detalhes de um dispositivo
- `GET /api/history` - Histórico de detecções
- `GET /api/history?start=date&end=date` - Histórico por período
- `GET /api/stats` - Estatísticas gerais (total detectados, SOs, etc)

#### 1.3 MQTT Client
- [ ] Implementar cliente MQTT que se conecta ao broker Node-RED
- [ ] Se inscrever em tópicos de interesse (ex: `nodered/wifi/data`)
- [ ] Parser de dados WiFi (MAC, RSSI, frequência)
- [ ] Salvar dados no banco de dados
- [ ] Mock: Gerar dados simulados se nenhum dado MQTT for recebido

#### 1.4 Banco de Dados
**Tabelas:**
- `devices` - Dispositivos únicos detectados (MAC, último visto, etc)
- `detections` - Log de cada detecção (timestamp, MAC, RSSI, frequência)
- `analysis` - Análise de SO e distância (MAC, SO identificado, distância estimada)

#### 1.5 Integração com ML
- [ ] Chamar notebook/serviço de ML para analisar dados
- [ ] Cachear resultados para melhor performance
- [ ] Mock: Retornar dados simulados

---

### NODE-RED (Broker MQTT)

#### 2.0 Propósito
Node-RED atua como orquestrador central, conectando ESP32(s), validando dados e repassando para o backend. Permite lógica visual e fácil manipulação de fluxos sem código.

#### 2.1 Configuração
- [ ] Deploy de Node-RED via Docker ou local
- [ ] Configurar Broker MQTT interno
- [ ] Aceitar conexões de ESP32 (real e mock)
- [ ] Tópicos:
  - `esp32/wifi/scan` - Dados brutos da ESP32
  - `nodered/wifi/data` - Dados processados para o Backend
  - `nodered/status` - Status do sistema

#### 2.2 Fluxos
- [ ] Fluxo de recepção: `esp32/wifi/scan` → Validação → `nodered/wifi/data`
- [ ] Fluxo de transformação: Normalizar dados, adicionar timestamp
- [ ] Fluxo de resiliência: Retry em caso de falha
- [ ] Dashboard interno (opcional) para monitoramento

#### 2.3 Comunicação Backend
- Backend se conecta como cliente ao broker Node-RED
- Subscreve a `nodered/wifi/data`
- Publica confirmações em `nodered/ack` (opcional)

---

### FRONTEND - React

#### 3.1 Componentes Principais
- [ ] **Dashboard**: Visão geral com cards de estatísticas
- [ ] **DeviceList**: Tabela de dispositivos detectados
- [ ] **DeviceDetail**: Modal/página com detalhes do dispositivo
- [ ] **HistoryChart**: Gráfico de detecções ao longo do tempo
- [ ] **Filters**: Filtros por SO, período, frequência, etc

#### 3.2 Funcionalidades
- [ ] Listagem de dispositivos em tempo real
- [ ] Mostrar: MAC, SO, Distância, Força de sinal (RSSI), Timestamp
- [ ] Filtros: Por SO, Por período, Por força de sinal
- [ ] Gráficos: Detecções por hora, Distribuição de SOs
- [ ] Auto-refresh a cada 5-10 segundos

#### 3.3 UI/UX
- [ ] Usar library de UI (Material-UI, Chakra, TailwindCSS)
- [ ] Responsive design
- [ ] Tema claro/escuro

---

### HARDWARE - Mockado

#### 4.1 Simulador de dados
- [ ] Script Python que gera dados WiFi fictícios
- [ ] Simula RSSI em diferentes faixas
- [ ] Gera MAC addresses aleatórios
- [ ] Publica via MQTT para o Node-RED (tópico: `esp32/wifi/scan`)

#### 4.2 Formato de dados MQTT
```json
{
  "timestamp": "2026-05-19T10:30:45Z",
  "devices": [
    {
      "mac": "AA:BB:CC:DD:EE:FF",
      "rssi": -65,
      "frequency": 2412,
      "ssid": "WiFiNetwork"
    },
    {
      "mac": "11:22:33:44:55:66",
      "rssi": -72,
      "frequency": 5180,
      "ssid": ""
    }
  ]
}
```

---

### ML - Mockado

#### 5.1 Análise de dados
- [ ] Função para identificar SO baseado em MAC OUI (organizationally unique identifier)
- [ ] Função para estimar distância baseada em RSSI
- [ ] Caching de resultados
- [ ] Mock: Retornar dados simulados

#### 5.2 Lógica de distância
- Mock: Converter RSSI em metros usando fórmula simplificada
- RSSI forte (-30) = perto (dentro da loja)
- RSSI fraco (-80) = longe (fora da loja)

---

## 📊 Detalhes de Implementação

### Fluxo de Dados
1. ESP32 (mock/real) faz WiFi scan
2. Publica dados via MQTT para Node-RED (`esp32/wifi/scan`)
3. Node-RED valida, transforma e republica (`nodered/wifi/data`)
4. Backend (FastAPI) recebe via MQTT e salva no banco
5. Backend chama ML para análise de SO e distância
6. Frontend faz poll na API
7. Dashboard atualiza com novos dados

### Banco de Dados
**Tabela `devices`:**
```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    rssi INT,
    frequency INT,
    ssid VARCHAR(32),
    so_identified VARCHAR(50),
    distance_estimated FLOAT
);

CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    device_mac VARCHAR(17) REFERENCES devices(mac_address),
    timestamp TIMESTAMP DEFAULT NOW(),
    rssi INT,
    frequency INT,
    location VARCHAR(50) -- "inside" ou "outside"
);
```

---

## 🚀 Ordem de Implementação (Recomendado)

### Semana 1: Node-RED + Setup Backend
1. Deploy Node-RED e configurar MQTT broker
2. Criar fluxos básicos de validação e transformação
3. Setup FastAPI + PostgreSQL
4. Models e schemas

### Semana 1-2: Backend Base + MQTT
1. API REST básica
2. Banco de dados
3. Cliente MQTT conectando ao Node-RED

### Semana 2: MQTT + Lógica Backend
1. Parser de dados WiFi
2. Integração com banco
3. Mock de dados (simulador de ESP32)

### Semana 2-3: ML Mock
1. Função de identificação de SO
2. Função de cálculo de distância
3. Service de integração

### Semana 3-4: Frontend Base
1. Setup React + Vite
2. Componentes básicos
3. API client
4. Dashboard

### Semana 4-5: Frontend + Refino
1. Gráficos e filtros
2. Styling
3. Responsividade
4. Testes e ajustes finais

---

## 📝 Considerações Importantes

- **Banco de Dados**: Inicialmente PostgreSQL local, depois considerar migração para cloud
- **MQTT Broker**: Usar Mosquitto local para desenvolvimento
- **Autenticação**: Não prioritário nesta fase
- **Performance**: Considerar índices no banco para queries de histórico
- **Escalabilidade**: Pensar em particionamento de dados históricos

---

## ✅ Checklist de Definições Pendentes

- [ ] Qual banco de dados será usado? (PostgreSQL recomendado)
- [ ] Detalhes do dashboard (layout, prioridade de informações)
- [ ] Intervalo de atualização preferido (frontend refresh)
- [ ] Período de retenção de dados históricos
- [ ] Definição exata de "dentro/fora da loja" (limiares de RSSI)
- [ ] Branding/cores do dashboard
- [ ] Requisitos de performance/latência
