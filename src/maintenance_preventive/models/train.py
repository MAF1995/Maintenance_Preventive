from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from maintenance_preventive.config import (
    DATASET_MANIFEST_PATH,
    FEATURE_STORE_PATH,
    METRICS_PATH,
    MODEL_BUNDLE_PATH,
    MODEL_MANIFEST_PATH,
    PREDICTIONS_PATH,
    TARGET_COLUMN,
    TRAIN_CYCLE_COUNT,
)
from maintenance_preventive.features.engineering import save_feature_store
from maintenance_preventive.mlflow_tracking import log_training_run
from maintenance_preventive.versioning import write_dataset_manifest, write_model_manifest


def load_feature_store(path: Path = FEATURE_STORE_PATH) -> pd.DataFrame:
    if not path.exists():
        save_feature_store(path)
    return pd.read_csv(path)


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col.startswith("ps2_") or col.startswith("fs1_")]


def subject_train_test_split(
    df: pd.DataFrame, train_cycles: int = TRAIN_CYCLE_COUNT
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(df) <= train_cycles:
        raise ValueError("Le dataset doit contenir plus de cycles que la borne d'apprentissage.")
    return df.iloc[:train_cycles].copy(), df.iloc[train_cycles:].copy()


def train_baseline(df: pd.DataFrame, train_cycles: int, random_state: int) -> tuple[dict, pd.DataFrame]:
    feature_columns = get_feature_columns(df)
    train_df, test_df = subject_train_test_split(df, train_cycles)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(train_df[feature_columns], train_df[TARGET_COLUMN])

    proba = model.predict_proba(test_df[feature_columns])[:, 1]
    pred = (proba >= 0.5).astype(int)

    metrics = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "train_cycles_rule": train_cycles,
        "split_mode": "first_2000_cycles_train_then_final_test",
        "train_cycles": int(len(train_df)),
        "test_cycles": int(len(test_df)),
        "feature_count": int(len(feature_columns)),
        "accuracy": float(accuracy_score(test_df[TARGET_COLUMN], pred)),
        "precision": float(precision_score(test_df[TARGET_COLUMN], pred, zero_division=0)),
        "recall": float(recall_score(test_df[TARGET_COLUMN], pred, zero_division=0)),
        "f1": float(f1_score(test_df[TARGET_COLUMN], pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(test_df[TARGET_COLUMN], proba)),
    }

    predictions = test_df[["cycle_id", "valve_pct", TARGET_COLUMN]].copy()
    predictions["predicted_label"] = pred
    predictions["predicted_probability"] = proba

    bundle = {
        "model": model,
        "feature_columns": feature_columns,
        "target_column": TARGET_COLUMN,
        "train_cycles_rule": train_cycles,
        "split_mode": "first_2000_cycles_train_then_final_test",
        "created_at_utc": metrics["generated_at_utc"],
    }
    return {"bundle": bundle, "metrics": metrics}, predictions


def persist_training_outputs(
    result: dict,
    predictions: pd.DataFrame,
    model_output: Path = MODEL_BUNDLE_PATH,
    metrics_output: Path = METRICS_PATH,
    predictions_output: Path = PREDICTIONS_PATH,
) -> None:
    model_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    predictions_output.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(result["bundle"], model_output)
    with metrics_output.open("w", encoding="utf-8") as fp:
        json.dump(result["metrics"], fp, indent=2, ensure_ascii=False)
    predictions.to_csv(predictions_output, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entraîne le modèle baseline de prédiction de valve.")
    parser.add_argument("--feature-store", type=Path, default=FEATURE_STORE_PATH)
    parser.add_argument("--train-cycles", type=int, default=TRAIN_CYCLE_COUNT)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--model-output", type=Path, default=MODEL_BUNDLE_PATH)
    parser.add_argument("--metrics-output", type=Path, default=METRICS_PATH)
    parser.add_argument("--predictions-output", type=Path, default=PREDICTIONS_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_feature_store(args.feature_store)
    result, predictions = train_baseline(df, args.train_cycles, args.random_state)
    persist_training_outputs(
        result=result,
        predictions=predictions,
        model_output=args.model_output,
        metrics_output=args.metrics_output,
        predictions_output=args.predictions_output,
    )

    run_id = log_training_run(
        result=result,
        model_output=args.model_output,
        metrics_output=args.metrics_output,
        predictions_output=args.predictions_output,
        feature_store_path=args.feature_store,
        random_state=args.random_state,
    )
    write_dataset_manifest(
        feature_store_path=args.feature_store,
        manifest_path=DATASET_MANIFEST_PATH,
    )
    write_model_manifest(
        model_path=args.model_output,
        metrics_path=args.metrics_output,
        predictions_path=args.predictions_output,
        feature_store_path=args.feature_store,
        manifest_path=MODEL_MANIFEST_PATH,
        mlflow_run_id=run_id,
        metrics_summary=result["metrics"],
    )

    print(f"[train] Modèle sauvegardé : {args.model_output}")
    print(f"[train] Métriques sauvegardées : {args.metrics_output}")
    print(f"[train] Prédictions de test sauvegardées : {args.predictions_output}")
    print(f"[train] MLflow run_id : {run_id}")
    print(json.dumps(result["metrics"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
