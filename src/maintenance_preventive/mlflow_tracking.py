from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient

from maintenance_preventive.config import (
    DEFAULT_MLFLOW_TRACKING_URI,
    MLFLOW_ARTIFACTS_DIR,
    MLFLOW_DB_PATH,
    MLFLOW_DIR,
    MLFLOW_EXPERIMENT_NAME,
)


def get_mlflow_tracking_uri() -> str:
    return os.getenv("MLFLOW_TRACKING_URI", DEFAULT_MLFLOW_TRACKING_URI)


def ensure_mlflow_directories() -> None:
    MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
    MLFLOW_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    if not MLFLOW_DB_PATH.parent.exists():
        MLFLOW_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def ensure_mlflow_experiment() -> str:
    ensure_mlflow_directories()
    tracking_uri = get_mlflow_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)

    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
    if experiment is not None:
        return experiment.experiment_id

    if tracking_uri.startswith("sqlite:"):
        experiment_id = client.create_experiment(
            name=MLFLOW_EXPERIMENT_NAME,
            artifact_location=MLFLOW_ARTIFACTS_DIR.as_uri(),
        )
    else:
        experiment_id = client.create_experiment(name=MLFLOW_EXPERIMENT_NAME)
    return experiment_id


def log_training_run(
    *,
    result: dict,
    model_output: Path,
    metrics_output: Path,
    predictions_output: Path,
    feature_store_path: Path,
    random_state: int,
) -> str:
    experiment_id = ensure_mlflow_experiment()
    tracking_uri = get_mlflow_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)

    metrics = result["metrics"]
    bundle = result["bundle"]

    run_name = (
        f"baseline_rf_train_{metrics['train_cycles']}_test_{metrics['test_cycles']}"
    )

    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name) as run:
        mlflow.set_tags(
            {
                "project": "maintenance_preventive",
                "model_family": "RandomForestClassifier",
                "split_mode": metrics["split_mode"],
            }
        )
        mlflow.log_params(
            {
                "train_cycles_rule": metrics["train_cycles_rule"],
                "train_cycles": metrics["train_cycles"],
                "test_cycles": metrics["test_cycles"],
                "feature_count": metrics["feature_count"],
                "random_state": random_state,
            }
        )
        mlflow.log_metrics(
            {
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "roc_auc": metrics["roc_auc"],
            }
        )
        mlflow.log_text(
            json.dumps(bundle["feature_columns"], indent=2, ensure_ascii=False),
            artifact_file="metadata/feature_columns.json",
        )
        mlflow.log_artifact(str(model_output), artifact_path="model")
        mlflow.log_artifact(str(metrics_output), artifact_path="metrics")
        mlflow.log_artifact(str(predictions_output), artifact_path="predictions")
        mlflow.log_artifact(str(feature_store_path), artifact_path="feature_store")
        return run.info.run_id
