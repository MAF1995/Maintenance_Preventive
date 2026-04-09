from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from maintenance_preventive.config import FEATURE_STORE_PATH, MODEL_BUNDLE_PATH
from maintenance_preventive.features.engineering import save_feature_store


def load_model_bundle(model_path: Path = MODEL_BUNDLE_PATH) -> dict:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Modele introuvable : {model_path}. Lancez d'abord l'entrainement."
        )
    return joblib.load(model_path)


def load_feature_store(path: Path = FEATURE_STORE_PATH) -> pd.DataFrame:
    if not path.exists():
        save_feature_store(path)
    return pd.read_csv(path)


def predict_cycle(cycle_id: int, model_path: Path = MODEL_BUNDLE_PATH) -> dict:
    bundle = load_model_bundle(model_path)
    feature_store = load_feature_store()

    row = feature_store.loc[feature_store["cycle_id"] == cycle_id]
    if row.empty:
        raise ValueError(f"Cycle introuvable : {cycle_id}")

    feature_columns = bundle["feature_columns"]
    model = bundle["model"]

    proba = float(model.predict_proba(row[feature_columns])[:, 1][0])
    label = int(proba >= 0.5)

    return {
        "cycle_id": int(cycle_id),
        "predicted_label": label,
        "predicted_probability": proba,
        "predicted_class_name": "optimal" if label == 1 else "non_optimal",
        "actual_valve_pct": int(row["valve_pct"].iloc[0]),
    }

