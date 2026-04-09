import json

from maintenance_preventive.bootstrap import ensure_project_artifacts
from maintenance_preventive.config import DATASET_MANIFEST_PATH, MODEL_MANIFEST_PATH


def test_version_manifests_are_generated():
    ensure_project_artifacts(force=True)

    dataset_manifest = json.loads(DATASET_MANIFEST_PATH.read_text(encoding="utf-8"))
    model_manifest = json.loads(MODEL_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert dataset_manifest["doi"] == "10.24432/C5CW21"
    assert dataset_manifest["license"] == "CC BY 4.0"
    assert "feature_store" in dataset_manifest["files"]
    assert "model" in model_manifest["files"]
    assert "metrics_summary" in model_manifest
