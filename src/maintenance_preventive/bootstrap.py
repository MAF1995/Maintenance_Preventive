from __future__ import annotations

import argparse
import json
from pathlib import Path

from maintenance_preventive.config import (
    DATASET_MANIFEST_PATH,
    FEATURE_STORE_PATH,
    METRICS_PATH,
    MODEL_BUNDLE_PATH,
    MODEL_MANIFEST_PATH,
    PREDICTIONS_PATH,
    TRAIN_CYCLE_COUNT,
)
from maintenance_preventive.features.engineering import save_feature_store
from maintenance_preventive.mlflow_tracking import log_training_run
from maintenance_preventive.models.train import (
    load_feature_store,
    persist_training_outputs,
    train_baseline,
)
from maintenance_preventive.versioning import write_dataset_manifest, write_model_manifest


def ensure_project_artifacts(
    force: bool = False,
    random_state: int = 42,
    feature_store_path: Path = FEATURE_STORE_PATH,
    model_output: Path = MODEL_BUNDLE_PATH,
    metrics_output: Path = METRICS_PATH,
    predictions_output: Path = PREDICTIONS_PATH,
) -> dict[str, bool | str]:
    feature_store_ready = feature_store_path.exists()
    training_outputs_ready = (
        model_output.exists() and metrics_output.exists() and predictions_output.exists()
    )
    dataset_manifest_ready = DATASET_MANIFEST_PATH.exists()
    model_manifest_ready = MODEL_MANIFEST_PATH.exists()

    if force or not feature_store_ready:
        save_feature_store(feature_store_path)
        feature_store_ready = True
        dataset_manifest_ready = True

    if feature_store_ready and (force or not dataset_manifest_ready):
        write_dataset_manifest(
            feature_store_path=feature_store_path,
            manifest_path=DATASET_MANIFEST_PATH,
        )
        dataset_manifest_ready = True

    if force or not training_outputs_ready:
        df = load_feature_store(feature_store_path)
        result, predictions = train_baseline(df, TRAIN_CYCLE_COUNT, random_state)
        persist_training_outputs(
            result=result,
            predictions=predictions,
            model_output=model_output,
            metrics_output=metrics_output,
            predictions_output=predictions_output,
        )
        run_id = log_training_run(
            result=result,
            model_output=model_output,
            metrics_output=metrics_output,
            predictions_output=predictions_output,
            feature_store_path=feature_store_path,
            random_state=random_state,
        )
        write_model_manifest(
            model_path=model_output,
            metrics_path=metrics_output,
            predictions_path=predictions_output,
            feature_store_path=feature_store_path,
            manifest_path=MODEL_MANIFEST_PATH,
            mlflow_run_id=run_id,
            metrics_summary=result["metrics"],
        )
        training_outputs_ready = True
        model_manifest_ready = True

    if training_outputs_ready and (force or not model_manifest_ready):
        metrics_payload = json.loads(metrics_output.read_text(encoding="utf-8"))
        write_model_manifest(
            model_path=model_output,
            metrics_path=metrics_output,
            predictions_path=predictions_output,
            feature_store_path=feature_store_path,
            manifest_path=MODEL_MANIFEST_PATH,
            metrics_summary=metrics_payload,
        )
        model_manifest_ready = True

    return {
        "feature_store_ready": feature_store_ready,
        "training_outputs_ready": training_outputs_ready,
        "dataset_manifest_ready": dataset_manifest_ready,
        "model_manifest_ready": model_manifest_ready,
        "feature_store_path": str(feature_store_path),
        "model_output": str(model_output),
        "metrics_output": str(metrics_output),
        "predictions_output": str(predictions_output),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare automatiquement le feature store et les artefacts du projet."
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    status = ensure_project_artifacts(force=args.force, random_state=args.random_state)
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
