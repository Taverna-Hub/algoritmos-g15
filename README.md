# WiFi MAC Capture e Analise de Sinal

Projeto embarcado para captura passiva de dispositivos WiFi proximos, orquestracao dos dados via MQTT/Node-RED, analise com modulo de Machine Learning e exposicao dos resultados por uma API FastAPI.

O fluxo principal do sistema e:

```text
ESP32 -> MQTT Mosquitto -> Node-RED -> Notebook/ML -> PostgreSQL -> Backend API
```

## Visao Geral

Este projeto identifica dispositivos proximos a partir de pacotes WiFi capturados passivamente. Os dados capturados pelo ESP32 sao enviados para um broker MQTT, passam por validacao e transformacao no Node-RED, sao analisados pelo servico de ML/Notebook e gravados em um banco compartilhado. O backend consulta esse banco e disponibiliza endpoints REST para dispositivos, historico e estatisticas.

## Modulos

### Hardware

Codigo embarcado do ESP32 responsavel pela captura passiva de pacotes WiFi e publicacao dos dados no topico MQTT de entrada.

Arquivos principais:

- `hardware/src/main.cpp`
- `hardware/include/config.h`
- `hardware/platformio.ini`

### Node-RED e MQTT

O modulo `nodered/` atua como broker MQTT e orquestrador dos dados de captura.

Servicos iniciados via Docker Compose:

- Node-RED: `http://localhost:1880`
- Mosquitto MQTT Broker: `localhost:1883`

Topicos principais:

- Entrada: `esp32/wifi/scan`
- Saida validada: `nodered/wifi/data`
- Erros: `nodered/errors`

O fluxo do Node-RED:

1. Recebe dados brutos do ESP32.
2. Faz parse do JSON.
3. Valida estrutura, MAC address, RSSI, canal e frequencia.
4. Normaliza MAC addresses para uppercase.
5. Remove campos vazios e adiciona timestamp de processamento.
6. Publica os dados validados para o Notebook/ML.

### ML / Notebook

O modulo `ML/` processa os dados validados publicados pelo Node-RED e persiste os resultados no banco compartilhado.

Funcionalidades:

- Identificacao de sistema operacional por MAC OUI.
- Estimativa de distancia usando RSSI e frequencia.
- Preservacao de metadados da captura passiva, como canal, tipo de frame e quantidade de aparicoes.
- Classificacao simples de localizacao como `inside` ou `outside`.
- Processamento em lote de multiplos dispositivos.

O servico escuta o topico `nodered/wifi/data`, processa o payload e grava os registros analisados no banco.

### Backend

O modulo `backend/` contem uma API FastAPI para consulta dos dispositivos detectados, historico, estatisticas e status do sistema.

Funcionalidades:

- API REST para dispositivos, historico e estatisticas.
- Identificacao de SO usando lookup de MAC OUI.
- Estimativa de distancia por RSSI.
- Registro de historico de deteccoes.
- Agregacoes e estatisticas.
- Criacao automatica das tabelas do banco.

Importante: a ingestao MQTT e a analise dos dispositivos sao feitas pelo Notebook/ML. O backend consome os dados ja persistidos no banco.

### Frontend

O projeto tambem possui um frontend em `frontend/`, preparado para consumir a API e exibir painel, lista de dispositivos, detalhes, filtros e estatisticas.

## Requisitos

- Python 3.8+
- PostgreSQL 12+
- Docker
- Docker Compose
- Node-RED e Mosquitto via `nodered/docker-compose.yml`
- MQTT CLI opcional para testes (`mosquitto_pub` e `mosquitto_sub`)

## Configuracao

Configure as variaveis de ambiente do backend em `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/wifi_detection
```

Se o projeto for executado em modulos separados, instale as dependencias Python de cada parte:

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
pip install -r ML/requirements.txt
```

## Executando o Node-RED e o MQTT Broker

A partir da pasta `nodered/`:

```bash
docker-compose up -d
```

Para parar os servicos:

```bash
docker-compose down
```

Para acompanhar logs:

```bash
docker-compose logs -f node-red
docker-compose logs -f mosquitto
```

## Executando o Notebook/ML

A partir da raiz do projeto:

```bash
python ML/notebook.py
```

O servico escuta o topico `nodered/wifi/data` e salva no banco os dispositivos processados.

Tambem e possivel usar a funcao diretamente em Python:

```python
from ML.notebook import process_payload

payload = {
    "timestamp": "2026-05-19T10:30:45Z",
    "packets": [
        {
            "source_mac": "AA:BB:CC:DD:EE:01",
            "rssi": -55,
            "channel": 1,
            "frequency": 2412,
            "frame_type": "probe_req",
            "seen_count": 3,
        }
    ],
}

process_payload(payload)
```

## Executando o Backend

A partir da pasta `backend/`:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Se estiver usando Alembic:

```bash
alembic upgrade head
```

Inicie a API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API ficara disponivel em:

- API: `http://localhost:8000`
- Documentacao Swagger: `http://localhost:8000/docs`

## Endpoints da API

### Devices

- `GET /api/devices` - Lista todos os dispositivos.
- `GET /api/devices/{mac}` - Retorna detalhes de um dispositivo.
- `POST /api/devices` - Cria ou atualiza um dispositivo.
- `GET /api/devices/{mac}/detections` - Retorna deteccoes de um dispositivo.

### History

- `GET /api/history/detections` - Retorna historico de deteccoes.
- `GET /api/history/stats` - Retorna estatisticas.
- `GET /api/history/timeline` - Retorna dados de timeline.

### System

- `GET /` - Endpoint raiz.
- `GET /health` - Health check.

## Formatos de Dados

### Entrada do ESP32

Topico: `esp32/wifi/scan`

```json
{
  "device_id": "esp32_001",
  "timestamp": "2026-05-19T10:30:45Z",
  "packets": [
    {
      "source_mac": "AA:BB:CC:DD:EE:FF",
      "rssi": -65,
      "channel": 1,
      "frequency": 2412,
      "frame_type": "probe_req",
      "seen_count": 3
    }
  ]
}
```

### Saida Validada do Node-RED

Topico: `nodered/wifi/data`

```json
{
  "timestamp": "2026-05-19T10:30:45Z",
  "devices": [
    {
      "mac": "AA:BB:CC:DD:EE:FF",
      "rssi": -65,
      "channel": 1,
      "frequency": 2412,
      "frame_type": "probe_req",
      "seen_count": 3
    }
  ]
}
```

### Resultado da Analise

```json
{
  "mac_address": "AA:BB:CC:DD:EE:01",
  "so_identified": "Apple",
  "distance_estimated": 2.45,
  "location": "inside",
  "confidence": 0.75
}
```

## Banco de Dados

### `devices`

- MAC address unico.
- Timestamps de primeira e ultima deteccao.
- RSSI, canal, frequencia, tipo de frame, quantidade de aparicoes e SSID.
- SO identificado.
- Distancia estimada.

### `detections`

- MAC do dispositivo.
- Timestamp.
- RSSI.
- Canal e frequencia.
- Tipo de frame e quantidade de aparicoes.
- Localizacao (`inside` ou `outside`).

### `analysis`

- MAC do dispositivo.
- SO identificado.
- Distancia estimada.
- Score de confianca.
- Ultima atualizacao.

## Estimativa de Distancia e Localizacao

A estimativa de distancia usa um modelo simplificado de perda de percurso:

```text
Distance = 10^((TxPower - RSSI) / (10 * N))
```

Parametros usados:

- `TxPower`: `-30 dBm`, valor tipico para WiFi.
- `N`: `2.0` para 5 GHz.
- `N`: `2.5` para 2.4 GHz.

Classificacao de localizacao:

- `inside`: RSSI maior que `-70 dBm`.
- `outside`: RSSI menor ou igual a `-70 dBm`.

## Testes com MQTT CLI

Publicar uma mensagem simulada:

```bash
mosquitto_pub -h localhost -t esp32/wifi/scan -m '{
  "timestamp": "2026-05-19T10:30:45Z",
  "packets": [
    {
      "source_mac": "AA:BB:CC:DD:EE:01",
      "rssi": -55,
      "channel": 1,
      "frequency": 2412,
      "frame_type": "probe_req",
      "seen_count": 3
    }
  ]
}'
```

Assinar o topico de saida:

```bash
mosquitto_sub -h localhost -t nodered/wifi/data
```

Monitorar topicos:

```bash
mosquitto_sub -h localhost -v -t "nodered/#"
mosquitto_sub -h localhost -v -t "esp32/#"
```

## Troubleshooting

### MQTT connection refused

- Verifique se o container do Mosquitto esta rodando: `docker ps`.
- Consulte os logs: `docker-compose logs mosquitto`.
- Verifique se a porta `1883` nao esta bloqueada.

### Node-RED nao conecta no MQTT

- Verifique o hostname do broker. Em rede Docker, ele deve ser `mosquitto`.
- Confira a conectividade da rede Docker: `docker network ls`.
- Consulte os logs do Node-RED.

### Nenhuma mensagem trafegando

- Verifique se o ESP32 ou publicador mock esta enviando para o topico correto.
- Confira se os nomes dos topicos estao corretos.
- Habilite os nos de debug no Node-RED.
- Use `mosquitto_sub` para confirmar se as mensagens estao sendo publicadas.

## Consideracoes de Producao

- Habilitar autenticacao no MQTT.
- Usar TLS/SSL.
- Persistir mensagens no broker.
- Implementar backup e recovery.
- Monitorar desempenho do broker.
- Configurar logs e restart automatico.
- Revisar regras de validacao e tolerancia a falhas.

## Melhorias Futuras

- Modelos reais de ML para identificacao de SO.
- Estimativa de distancia mais avancada usando multiplas frequencias.
- Classificacao de tipo de dispositivo, como celular, notebook ou IoT.
- Analise de aglomeracao e mapas de calor.
- Reconhecimento de padroes temporais.

## Referencias

- [Node-RED Official Docs](https://nodered.org/docs/)
- [Mosquitto Documentation](https://mosquitto.org/documentation/)
- [MQTT Protocol](http://mqtt.org/)
