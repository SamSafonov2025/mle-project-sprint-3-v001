# Sprint 3: релиз модели в продакшен

Проект выводит модель оценки стоимости недвижимости в online-сервис. Сервис
принимает признаки объекта недвижимости, возвращает прогноз цены и экспортирует
метрики для Prometheus/Grafana.

## Что внутри

- `services/ml_service/` - FastAPI-приложение и скрипт симуляции нагрузки.
- `services/models/flats_price_model/` - финальная модель Sprint 2 из MLflow
  run `f1c6a1a7bf7f48cdb563a53f2203fbfe`.
- `services/Dockerfile_ml_service` - Docker-образ микросервиса.
- `services/docker-compose.yaml` - ML service + Prometheus + Grafana.
- `services/prometheus/prometheus.yml` - scrape-конфигурация Prometheus.
- `dashboard.json`, `dashboard.jpg` - артефакты дашборда Grafana.
- `Instructions.md` - команды запуска для всех этапов.
- `Monitoring.md` - описание выбранных метрик и визуализаций.

## Технологии

FastAPI, Uvicorn, cloudpickle, scikit-learn, Docker, Docker Compose,
Prometheus, prometheus_client, prometheus_fastapi_instrumentator, Grafana.

Локальный S3 bucket, из которого взят артефакт модели: `yp-ml-engineer`.
