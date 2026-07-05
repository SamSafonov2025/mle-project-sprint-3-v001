# Инструкции по запуску микросервиса

Все команды выполняются из корня репозитория. В примерах ниже `<HOST>` - адрес
машины, на которой запущен сервис. Если команды выполняются на той же машине,
можно использовать `localhost`.

## 1. FastAPI микросервис в виртуальном окружении

```bash
cd services
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn ml_service.main:app --host 0.0.0.0 --port 8000
```

Адреса:

- микросервис: `http://<HOST>:8000`
- Swagger UI: `http://<HOST>:8000/docs`
- метрики микросервиса: `http://<HOST>:8000/metrics`

### Пример curl-запроса к микросервису

```bash
curl -X POST "http://<HOST>:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-001",
    "build_year": 2014,
    "building_id": 22588,
    "ceiling_height": 3.2,
    "floors_total": 9,
    "kitchen_area": 6.0,
    "latitude": 55.466316,
    "living_area": 28.0,
    "rooms": 2,
    "total_area": 44.0
  }'
```

Ожидаемый формат ответа:

```json
{"user_id":"demo-user-001","prediction":12345678.9}
```

## 2. FastAPI микросервис в Docker-контейнере

Dockerfile собирается из публичного образа `python:3.12-slim`, поэтому для
запуска не нужен доступ к приватному registry.

```bash
cd services
docker image build -f Dockerfile_ml_service -t sprint3-ml-service:latest .
docker container run --rm --name sprint3-ml-service \
  --env-file .env \
  -p 8000:8000 \
  sprint3-ml-service:latest
```

### Пример curl-запроса к микросервису

```bash
curl -X POST "http://<HOST>:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"docker-user","build_year":1991,"building_id":15631,"ceiling_height":2.64,"floors_total":14,"kitchen_area":9.0,"latitude":55.985683,"living_area":21.0,"rooms":1,"total_area":39.5}'
```

## 3. Docker Compose для микросервиса и системы мониторинга

```bash
cd services
docker compose down
docker compose up --build -d
```

Если Docker требует root-доступ, используйте те же команды через `sudo`.

Адреса сервисов:

- микросервис: `http://<HOST>:8000`
- Swagger UI: `http://<HOST>:8000/docs`
- метрики микросервиса: `http://<HOST>:8000/metrics`
- Prometheus: `http://<HOST>:9090`
- Grafana: `http://<HOST>:3000`

Логин и пароль Grafana задаются в `services/.env` переменными
`GRAFANA_USER` и `GRAFANA_PASS`.

### Пример curl-запроса к микросервису

```bash
curl -X POST "http://<HOST>:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"compose-user","build_year":1917,"building_id":297,"ceiling_height":2.8,"floors_total":3,"kitchen_area":11.0,"latitude":55.753326,"living_area":36.0,"rooms":3,"total_area":55.5}'
```

## 4. Скрипт симуляции нагрузки

Скрипт генерирует POST-запросы к `/predict`, чтобы на дашборде менялись
счетчики, latency histogram и прикладные метрики.

Вариант для виртуального окружения:

```bash
cd services
source .venv/bin/activate
python ml_service/load_test.py --url http://<HOST>:8000/predict --requests 120 --sleep 0.05
```

Вариант без активации основного окружения, если стек запущен в Docker Compose:

```bash
cd services
python3 -m venv .load-venv
source .load-venv/bin/activate
python ml_service/load_test.py --url http://<HOST>:8000/predict --requests 120 --sleep 0.05
```
