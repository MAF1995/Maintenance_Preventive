from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from maintenance_preventive.config import (
    DATASET_MANIFEST_PATH,
    FEATURE_STORE_PATH,
    FS1_PATH,
    MODEL_MANIFEST_PATH,
    PROFILE_PATH,
    PS2_PATH,
)


DATASET_SOURCE_URL = "https://archive.ics.uci.edu/dataset/447/condition+monitoring+of+hydraulic+systems"
DATASET_DOI = "10.24432/C5CW21"
DATASET_LICENSE = "CC BY 4.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_metadata(path: Path) -> dict[str, str | int]:
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _write_manifest(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return path


def write_dataset_manifest(
    *,
    feature_store_path: Path = FEATURE_STORE_PATH,
    manifest_path: Path = DATASET_MANIFEST_PATH,
) -> Path:
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": "Condition monitoring of hydraulic systems",
        "source_url": DATASET_SOURCE_URL,
        "doi": DATASET_DOI,
        "license": DATASET_LICENSE,
        "files": {
            "ps2": _file_metadata(PS2_PATH),
            "fs1": _file_metadata(FS1_PATH),
            "profile": _file_metadata(PROFILE_PATH),
            "feature_store": _file_metadata(feature_store_path),
        },
    }
    return _write_manifest(manifest_path, payload)


def write_model_manifest(
    *,
    model_path: Path,
    metrics_path: Path,
    predictions_path: Path,
    feature_store_path: Path = FEATURE_STORE_PATH,
    manifest_path: Path = MODEL_MANIFEST_PATH,
    mlflow_run_id: str | None = None,
    metrics_summary: dict | None = None,
) -> Path:
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mlflow_run_id": mlflow_run_id,
        "files": {
            "model": _file_metadata(model_path),
            "metrics": _file_metadata(metrics_path),
            "predictions": _file_metadata(predictions_path),
            "feature_store": _file_metadata(feature_store_path),
        },
        "metrics_summary": metrics_summary or {},
    }
    return _write_manifest(manifest_path, payload)
