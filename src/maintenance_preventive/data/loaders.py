from __future__ import annotations

from pathlib import Path

import pandas as pd

from maintenance_preventive.config import FS1_PATH, PROFILE_COLUMNS, PROFILE_PATH, PS2_PATH


def load_sensor_matrix(path: Path) -> pd.DataFrame:
    """Load one tab-delimited sensor matrix where each row is a cycle."""
    return pd.read_csv(path, sep=r"\s+", header=None, engine="python")


def load_ps2() -> pd.DataFrame:
    return load_sensor_matrix(PS2_PATH)


def load_fs1() -> pd.DataFrame:
    return load_sensor_matrix(FS1_PATH)


def load_profile() -> pd.DataFrame:
    return pd.read_csv(
        PROFILE_PATH,
        sep=r"\s+",
        header=None,
        names=PROFILE_COLUMNS,
        engine="python",
    )


def load_project_subset() -> dict[str, pd.DataFrame]:
    return {
        "ps2": load_ps2(),
        "fs1": load_fs1(),
        "profile": load_profile(),
    }
