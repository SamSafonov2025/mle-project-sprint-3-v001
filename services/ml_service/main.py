import os
import time
from pathlib import Path
from typing import Any

import cloudpickle
import pandas as pd
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, ConfigDict, Field, model_validator


MODEL_COLUMNS = [
    "build_year",
    "building_id",
    "ceiling_height",
    "floors_total",
    "kitchen_area",
    "latitude",
    "living_area",
    "rooms",
    "total_area",
]

DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[1] / "models" / "flats_price_model"
)

PREDICTION_COUNTER = Counter(
    "ml_service_predictions_total",
    "Total number of prediction requests by status.",
    ["status"],
)
PREDICTION_LATENCY = Histogram(
    "ml_service_prediction_latency_seconds",
    "Prediction handler latency in seconds.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
LAST_PREDICTION = Gauge(
    "ml_service_last_prediction_rub",
    "Last predicted flat price in rubles.",
)
REQUESTED_AREA = Histogram(
    "ml_service_requested_total_area_sqm",
    "Requested total_area values in square meters.",
    buckets=(20, 35, 50, 70, 90, 120, 160, 220, 320),
)


class FlatFeatures(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "demo-user-001",
                "build_year": 2014,
                "building_id": 22588,
                "ceiling_height": 3.2,
                "floors_total": 9,
                "kitchen_area": 6.0,
                "latitude": 55.466316,
                "living_area": 28.0,
                "rooms": 2,
                "total_area": 44.0,
            }
        }
    )
    user_id: str = Field(..., min_length=1, description="External request user id")
    build_year: int = Field(..., ge=1800, le=2035)
    building_id: int = Field(..., ge=0)
    ceiling_height: float = Field(..., gt=1.0, le=10.0)
    floors_total: int = Field(..., ge=1, le=100)
    kitchen_area: float = Field(..., ge=0.0, le=300.0)
    latitude: float = Field(..., ge=54.0, le=57.0)
    living_area: float = Field(..., gt=0.0, le=1000.0)
    rooms: int = Field(..., ge=0, le=20)
    total_area: float = Field(..., gt=0.0, le=1500.0)

    @model_validator(mode="after")
    def check_area_consistency(self) -> "FlatFeatures":
        if self.living_area > self.total_area:
            raise ValueError("living_area must be less than or equal to total_area")
        if self.kitchen_area > self.total_area:
            raise ValueError("kitchen_area must be less than or equal to total_area")
        return self

    def to_frame(self) -> pd.DataFrame:
        row: dict[str, Any] = {column: getattr(self, column) for column in MODEL_COLUMNS}
        return pd.DataFrame([row], columns=MODEL_COLUMNS)


class PredictionResponse(BaseModel):
    user_id: str
    prediction: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str


class ModelHandler:
    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.model = None

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model path does not exist: {self.model_path}")
        with (self.model_path / "model.pkl").open("rb") as model_file:
            self.model = cloudpickle.load(model_file)

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, features: FlatFeatures) -> float:
        if self.model is None:
            raise RuntimeError("Model is not loaded")
        prediction = self.model.predict(features.to_frame())
        return float(prediction[0])


def create_app() -> FastAPI:
    model_path = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
    handler = ModelHandler(model_path)

    app = FastAPI(
        title="Yandex Realty Price Prediction Service",
        description="Sprint 3 FastAPI service for online flat price predictions.",
        version="1.0.0",
    )
    app.state.handler = handler

    @app.on_event("startup")
    def load_model() -> None:
        handler.load()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok" if handler.is_loaded else "not_ready",
            model_loaded=handler.is_loaded,
            model_path=str(handler.model_path),
        )

    @app.post("/predict", response_model=PredictionResponse)
    def predict(payload: FlatFeatures) -> PredictionResponse:
        started = time.perf_counter()
        REQUESTED_AREA.observe(payload.total_area)
        try:
            value = handler.predict(payload)
        except Exception as exc:
            PREDICTION_COUNTER.labels(status="error").inc()
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            PREDICTION_LATENCY.observe(time.perf_counter() - started)

        PREDICTION_COUNTER.labels(status="success").inc()
        LAST_PREDICTION.set(value)
        return PredictionResponse(user_id=payload.user_id, prediction=value)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    return app


app = create_app()
