from maintenance_preventive.config import MLFLOW_DB_PATH
from maintenance_preventive.mlflow_tracking import get_mlflow_tracking_uri


def test_mlflow_tracking_uri_uses_env_when_available(monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    assert get_mlflow_tracking_uri() == "http://127.0.0.1:5000"


def test_mlflow_tracking_uri_defaults_to_local_sqlite(monkeypatch):
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    assert get_mlflow_tracking_uri().endswith(MLFLOW_DB_PATH.as_posix())
