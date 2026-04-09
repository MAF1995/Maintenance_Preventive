from maintenance_preventive.config import TRAIN_CYCLE_COUNT
from maintenance_preventive.data.loaders import load_fs1, load_profile, load_ps2
from maintenance_preventive.features.engineering import build_feature_table
from maintenance_preventive.models.train import subject_train_test_split


def test_profile_has_expected_shape():
    profile = load_profile()
    assert profile.shape == (2205, 5)
    assert set(profile["valve_pct"].unique()) == {73, 80, 90, 100}


def test_sensor_subset_shapes():
    ps2 = load_ps2()
    fs1 = load_fs1()
    assert ps2.shape == (2205, 6000)
    assert fs1.shape == (2205, 600)


def test_feature_table_contains_target_and_cycle():
    feature_table = build_feature_table()
    assert len(feature_table) == 2205
    assert "cycle_id" in feature_table.columns
    assert "is_valve_optimal" in feature_table.columns
    assert feature_table["is_valve_optimal"].isin([0, 1]).all()


def test_subject_split_matches_pdf_constraint():
    feature_table = build_feature_table()
    train_df, test_df = subject_train_test_split(feature_table, train_cycles=TRAIN_CYCLE_COUNT)
    assert len(train_df) == TRAIN_CYCLE_COUNT
    assert len(test_df) == len(feature_table) - TRAIN_CYCLE_COUNT
    assert train_df["cycle_id"].max() == TRAIN_CYCLE_COUNT
    assert test_df["cycle_id"].min() == TRAIN_CYCLE_COUNT + 1
    assert len(train_df) + len(test_df) == len(feature_table)
