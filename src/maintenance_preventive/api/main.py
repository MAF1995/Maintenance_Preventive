from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel

from maintenance_preventive.bootstrap import ensure_project_artifacts
from maintenance_preventive.config import FRONTEND_DIR
from maintenance_preventive.models.predict import predict_cycle
from maintenance_preventive.models.reporting import (
    build_confusion_summary,
    load_feature_importance,
    load_model_metrics,
    load_test_predictions,
)


HTTP_REQUESTS_TOTAL = Counter(
    "maintenance_api_http_requests_total",
    "Total number of HTTP requests handled by the API.",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "maintenance_api_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
PREDICTION_REQUESTS_TOTAL = Counter(
    "maintenance_prediction_requests_total",
    "Number of prediction requests served by class.",
    ["predicted_class"],
)
PREDICTION_PROBABILITY = Histogram(
    "maintenance_prediction_probability",
    "Distribution of prediction probabilities.",
)
MODEL_METRIC_GAUGE = Gauge(
    "maintenance_model_metric",
    "Model quality metrics loaded from the latest training artifact.",
    ["metric"],
)
MODEL_METADATA_GAUGE = Gauge(
    "maintenance_model_metadata",
    "Metadata values attached to the current model artifact.",
    ["name"],
)


class PredictionResponse(BaseModel):
    cycle_id: int
    predicted_label: int
    predicted_probability: float
    predicted_class_name: str
    actual_valve_pct: int


def refresh_model_metric_gauges() -> dict:
    metrics = load_model_metrics()
    for metric_name in ("accuracy", "precision", "recall", "f1", "roc_auc"):
        MODEL_METRIC_GAUGE.labels(metric=metric_name).set(float(metrics[metric_name]))
    for metadata_name in ("train_cycles", "test_cycles", "feature_count"):
        MODEL_METADATA_GAUGE.labels(name=metadata_name).set(float(metrics[metadata_name]))
    return metrics


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_project_artifacts()
    refresh_model_metric_gauges()
    yield


app = FastAPI(
    title="Maintenance Preventive API",
    description="API locale de prediction de la condition optimale de la valve par cycle.",
    version="0.2.0",
    lifespan=lifespan,
)

app.mount("/ui-assets", StaticFiles(directory=FRONTEND_DIR), name="ui-assets")


@app.middleware("http")
async def instrument_requests(request: Request, call_next):
    start_time = perf_counter()
    raw_path = request.url.path
    try:
        response = await call_next(request)
    except Exception:
        duration = perf_counter() - start_time
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=raw_path,
            status_code="500",
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=raw_path,
        ).observe(duration)
        raise

    route = request.scope.get("route")
    path_label = getattr(route, "path", raw_path)
    duration = perf_counter() - start_time

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        path=path_label,
        status_code=str(response.status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        path=path_label,
    ).observe(duration)
    return response


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ui", include_in_schema=False)
def web_ui() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/predict/{cycle_id}", response_model=PredictionResponse)
def predict(cycle_id: int) -> PredictionResponse:
    try:
        result = predict_cycle(cycle_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    PREDICTION_REQUESTS_TOTAL.labels(result["predicted_class_name"]).inc()
    PREDICTION_PROBABILITY.observe(result["predicted_probability"])
    return PredictionResponse(**result)


@app.get("/model/metrics")
def model_metrics() -> dict:
    metrics = refresh_model_metric_gauges()
    confusion = build_confusion_summary()
    return {
        "metrics": metrics,
        "confusion_matrix": confusion,
    }


@app.get("/model/test-sample")
def model_test_sample(limit: int = Query(default=25, ge=1, le=500)) -> list[dict]:
    predictions = load_test_predictions(limit=limit)
    return predictions.to_dict(orient="records")


@app.get("/model/feature-importance")
def model_feature_importance(limit: int = Query(default=10, ge=1, le=50)) -> list[dict]:
    feature_importance = load_feature_importance(limit=limit)
    return feature_importance.to_dict(orient="records")


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics() -> PlainTextResponse:
    refresh_model_metric_gauges()
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
