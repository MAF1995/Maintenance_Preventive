from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from maintenance_preventive.config import FEATURE_STORE_PATH, PROCESSED_DATA_DIR, TARGET_COLUMN
from maintenance_preventive.data.loaders import load_fs1, load_profile, load_ps2
from maintenance_preventive.versioning import write_dataset_manifest


def _ensure_output_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _extract_summary_features(matrix: pd.DataFrame, prefix: str) -> pd.DataFrame:
    values = matrix.to_numpy(dtype=float)
    series_diff = np.diff(values, axis=1)

    features = pd.DataFrame(
        {
            f"{prefix}_mean": values.mean(axis=1),
            f"{prefix}_std": values.std(axis=1),
            f"{prefix}_min": values.min(axis=1),
            f"{prefix}_max": values.max(axis=1),
            f"{prefix}_median": np.median(values, axis=1),
            f"{prefix}_q05": np.quantile(values, 0.05, axis=1),
            f"{prefix}_q25": np.quantile(values, 0.25, axis=1),
            f"{prefix}_q75": np.quantile(values, 0.75, axis=1),
            f"{prefix}_q95": np.quantile(values, 0.95, axis=1),
            f"{prefix}_range": values.max(axis=1) - values.min(axis=1),
            f"{prefix}_rms": np.sqrt(np.mean(np.square(values), axis=1)),
            f"{prefix}_energy": np.mean(np.square(values), axis=1),
            f"{prefix}_first": values[:, 0],
            f"{prefix}_last": values[:, -1],
            f"{prefix}_slope": (values[:, -1] - values[:, 0]) / values.shape[1],
            f"{prefix}_abs_diff_mean": np.abs(series_diff).mean(axis=1),
        }
    )
    return features


def build_feature_table() -> pd.DataFrame:
    ps2 = load_ps2()
    fs1 = load_fs1()
    profile = load_profile()

    features = pd.DataFrame({"cycle_id": np.arange(1, len(profile) + 1)})
    features = pd.concat(
        [
            features,
            _extract_summary_features(ps2, "ps2"),
            _extract_summary_features(fs1, "fs1"),
        ],
        axis=1,
    )

    features["valve_pct"] = profile["valve_pct"]
    features["cooler_pct"] = profile["cooler_pct"]
    features["pump_leakage"] = profile["pump_leakage"]
    features["accumulator_bar"] = profile["accumulator_bar"]
    features["stable_flag"] = profile["stable_flag"]
    features[TARGET_COLUMN] = (profile["valve_pct"] == 100).astype(int)
    return features


def save_feature_store(output_path: Path = FEATURE_STORE_PATH) -> Path:
    _ensure_output_dir(output_path)
    features = build_feature_table()
    features.to_csv(output_path, index=False)
    write_dataset_manifest(feature_store_path=output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construit le feature store à partir de PS2, FS1 et profile."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=FEATURE_STORE_PATH,
        help="Chemin de sortie du feature store CSV.",
    )
    return parser.parse_args()


def main() -> None:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    args = parse_args()
    output_path = save_feature_store(args.output)
    print(f"[features] Feature store généré : {output_path}")


if __name__ == "__main__":
    main()
