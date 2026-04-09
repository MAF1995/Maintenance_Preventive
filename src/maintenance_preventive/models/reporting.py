from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from maintenance_preventive.bootstrap import ensure_project_artifacts
from maintenance_preventive.config import METRICS_PATH, MODEL_BUNDLE_PATH, PREDICTIONS_PATH


def _load_json_with_recovery(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        ensure_project_artifacts(force=True)
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)


def _load_csv_with_recovery(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, OSError, ValueError):
        ensure_project_artifacts(force=True)
        return pd.read_csv(path)


def _load_bundle_with_recovery(model_path: Path) -> dict:
    try:
        return joblib.load(model_path)
    except (FileNotFoundError, EOFError, OSError, ValueError):
        ensure_project_artifacts(force=True)
        return joblib.load(model_path)


def load_model_metrics(path: Path = METRICS_PATH) -> dict:
    ensure_project_artifacts()
    return _load_json_with_recovery(path)


def load_test_predictions(path: Path = PREDICTIONS_PATH, limit: int | None = None) -> pd.DataFrame:
    ensure_project_artifacts()
    predictions = _load_csv_with_recovery(path)
    if limit is not None:
        return predictions.head(limit).copy()
    return predictions


def load_feature_importance(
    model_path: Path = MODEL_BUNDLE_PATH, limit: int | None = 10
) -> pd.DataFrame:
    ensure_project_artifacts()
    bundle = _load_bundle_with_recovery(model_path)
    importances = getattr(bundle["model"], "feature_importances_", None)
    if importances is None:
        return pd.DataFrame(columns=["feature", "importance"])

    feature_importance = (
        pd.DataFrame(
            {
                "feature": bundle["feature_columns"],
                "importance": importances,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    if limit is not None:
        return feature_importance.head(limit).copy()
    return feature_importance


def build_confusion_summary(predictions: pd.DataFrame | None = None) -> dict[str, int]:
    if predictions is None:
        predictions = load_test_predictions()

    actual = predictions["is_valve_optimal"]
    predicted = predictions["predicted_label"]

    return {
        "true_negative": int(((actual == 0) & (predicted == 0)).sum()),
        "false_positive": int(((actual == 0) & (predicted == 1)).sum()),
        "false_negative": int(((actual == 1) & (predicted == 0)).sum()),
        "true_positive": int(((actual == 1) & (predicted == 1)).sum()),
    }
