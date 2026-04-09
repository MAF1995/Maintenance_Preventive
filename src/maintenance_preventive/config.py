import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "condition_monitoring_of_hydraulic_systems"
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MODELS_DIR = ARTIFACTS_DIR / "models"
METRICS_DIR = ARTIFACTS_DIR / "metrics"
PREDICTIONS_DIR = ARTIFACTS_DIR / "predictions"
METADATA_DIR = ARTIFACTS_DIR / "metadata"

PROFILE_PATH = RAW_DATA_DIR / "profile.txt"
PS2_PATH = RAW_DATA_DIR / "PS2.txt"
FS1_PATH = RAW_DATA_DIR / "FS1.txt"

FEATURE_STORE_PATH = PROCESSED_DATA_DIR / "feature_store.csv"
MODEL_BUNDLE_PATH = MODELS_DIR / "valve_baseline_model.joblib"
METRICS_PATH = METRICS_DIR / "baseline_metrics.json"
PREDICTIONS_PATH = PREDICTIONS_DIR / "test_predictions.csv"
DATASET_MANIFEST_PATH = METADATA_DIR / "dataset_version.json"
MODEL_MANIFEST_PATH = METADATA_DIR / "model_version.json"
TRAIN_CYCLE_COUNT = 2000
MLFLOW_DIR = ARTIFACTS_DIR / "mlflow"
MLFLOW_DB_PATH = MLFLOW_DIR / "mlflow.db"
MLFLOW_ARTIFACTS_DIR = MLFLOW_DIR / "artifacts"
MLFLOW_EXPERIMENT_NAME = "maintenance_preventive_baseline"
DEFAULT_MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    f"sqlite:///{MLFLOW_DB_PATH.as_posix()}",
)

PROFILE_COLUMNS = [
    "cooler_pct",
    "valve_pct",
    "pump_leakage",
    "accumulator_bar",
    "stable_flag",
]

TARGET_COLUMN = "is_valve_optimal"
