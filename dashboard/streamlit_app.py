from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
import streamlit as st


def _candidate_api_urls() -> list[str]:
    env_value = os.getenv("MAINTENANCE_API_BASE_URL")
    candidates = []
    if env_value:
        candidates.append(env_value.rstrip("/"))
    candidates.extend(
        [
            "http://127.0.0.1:8011",
            "http://127.0.0.1:8010",
        ]
    )
    deduplicated = []
    for candidate in candidates:
        if candidate not in deduplicated:
            deduplicated.append(candidate)
    return deduplicated


def _resolve_api_base_url() -> str:
    for candidate in _candidate_api_urls():
        try:
            with urlopen(f"{candidate}/model/metrics", timeout=3) as response:
                if response.status == 200:
                    return candidate
        except (HTTPError, URLError):
            continue
    return _candidate_api_urls()[0]


API_BASE_URL = _resolve_api_base_url()


def fetch_json(path: str, params: dict | None = None) -> dict | list:
    url = f"{API_BASE_URL}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"

    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _read_http_error_payload(exc: HTTPError) -> dict:
    try:
        return json.loads(exc.read().decode("utf-8"))
    except Exception:
        return {}


def _extract_max_allowed_limit(error_payload: dict) -> int | None:
    for detail in error_payload.get("detail", []):
        ctx = detail.get("ctx", {})
        max_allowed = ctx.get("le")
        if isinstance(max_allowed, int):
            return max_allowed
    return None


def fetch_test_sample_with_fallback(requested_limit: int) -> tuple[list[dict], int | None]:
    try:
        return fetch_json("/model/test-sample", {"limit": requested_limit}), None
    except HTTPError as exc:
        if exc.code != 422:
            raise
        error_payload = _read_http_error_payload(exc)
        max_allowed = _extract_max_allowed_limit(error_payload)
        if max_allowed is None or max_allowed >= requested_limit:
            raise
        return fetch_json("/model/test-sample", {"limit": max_allowed}), max_allowed


st.set_page_config(
    page_title="Maintenance Preventive Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

st.markdown(
    """
    <style>
      .stApp {
        background: linear-gradient(180deg, #f7f4ec 0%, #fbfaf7 100%);
      }
      .main h1, .main h2, .main h3 {
        font-family: "Garamond", "Georgia", serif;
        letter-spacing: 0.02em;
      }
      .metric-card {
        padding: 1rem;
        border-radius: 1rem;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(45, 58, 74, 0.08);
        box-shadow: 0 12px 30px rgba(45, 58, 74, 0.06);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Maintenance Preventive Dashboard")
st.caption(
    "Vue de supervision du modele : metriques, variables les plus contributives "
    "et lecture chronologique de la condition de la valve."
)
st.caption(f"API cible : {API_BASE_URL}")

try:
    model_payload = fetch_json("/model/metrics")
    feature_importance_payload = fetch_json("/model/feature-importance", {"limit": 10})
    test_sample_payload, test_sample_limit_fallback = fetch_test_sample_with_fallback(205)
except (HTTPError, URLError) as exc:
    st.error(
        "Impossible de joindre une API compatible. Lancez `powershell -ExecutionPolicy Bypass -File .\\scripts\\run-api.ps1` "
        "ou la stack Docker, puis verifiez que l'endpoint `/model/metrics` repond bien."
    )
    st.exception(exc)
    st.stop()

metrics = model_payload["metrics"]
confusion = model_payload["confusion_matrix"]
feature_importance = pd.DataFrame(feature_importance_payload)
test_sample = pd.DataFrame(test_sample_payload)

if test_sample_limit_fallback is not None:
    st.warning(
        f"L'API actuellement joignable limite `/model/test-sample` a {test_sample_limit_fallback} cycles. "
        "La frise est affichee avec cette fenetre reduite. Pour voir les 205 cycles du test final, "
        "relancez l'API Docker avec une image rebuild."
    )

metric_cols = st.columns(4)
metric_cols[0].metric("Accuracy", f"{metrics['accuracy']:.3f}")
metric_cols[1].metric("F1", f"{metrics['f1']:.3f}")
metric_cols[2].metric("ROC AUC", f"{metrics['roc_auc']:.3f}")
metric_cols[3].metric("Cycles de test", metrics["test_cycles"])

detail_cols = st.columns([1.3, 1])

with detail_cols[0]:
    st.subheader("Importance des features")
    if feature_importance.empty:
        st.info("Le modele ne fournit pas d'importance des variables.")
    else:
        chart_df = feature_importance.set_index("feature")
        st.bar_chart(chart_df)
        st.dataframe(feature_importance, use_container_width=True, hide_index=True)

with detail_cols[1]:
    st.subheader("Matrice de confusion")
    confusion_df = pd.DataFrame(
        [
            {"categorie": "TN", "valeur": confusion["true_negative"]},
            {"categorie": "FP", "valeur": confusion["false_positive"]},
            {"categorie": "FN", "valeur": confusion["false_negative"]},
            {"categorie": "TP", "valeur": confusion["true_positive"]},
        ]
    )
    st.dataframe(confusion_df, use_container_width=True, hide_index=True)

    st.subheader("Split impose par le sujet")
    st.markdown(
        f"""
        - Train : **{metrics['train_cycles']}** cycles
        - Test final : **{metrics['test_cycles']}** cycles
        - Variables construites : **{metrics['feature_count']}**
        """
    )

st.subheader("Extrait des predictions de test")
st.dataframe(test_sample.head(20), use_container_width=True, hide_index=True)

st.subheader("Frise chronologique de l'efficacite de la valve")
st.caption(
    "Cette vue permet d'estimer l'evolution des cycles dans le temps en comparant la condition reelle "
    "de la valve et la probabilite predite d'etat optimal."
)

if test_sample.empty:
    st.info("Aucune prediction de test n'est disponible pour alimenter la frise chronologique.")
else:
    timeline_df = test_sample.copy().sort_values("cycle_id")
    timeline_df["predicted_optimality_pct"] = timeline_df["predicted_probability"] * 100

    min_cycle = int(timeline_df["cycle_id"].min())
    max_cycle = int(timeline_df["cycle_id"].max())
    range_start, range_end = st.slider(
        "Fenetre de cycles",
        min_value=min_cycle,
        max_value=max_cycle,
        value=(min_cycle, max_cycle),
    )

    filtered_timeline = timeline_df[
        (timeline_df["cycle_id"] >= range_start) & (timeline_df["cycle_id"] <= range_end)
    ].copy()

    chart_df = (
        filtered_timeline.rename(
            columns={
                "valve_pct": "valve_reelle_pct",
                "predicted_optimality_pct": "probabilite_predite_pct",
            }
        )
        .set_index("cycle_id")[["valve_reelle_pct", "probabilite_predite_pct"]]
    )
    st.line_chart(chart_df, use_container_width=True)

    selected_cycle = st.selectbox(
        "Cycle a inspecter",
        options=filtered_timeline["cycle_id"].tolist(),
        index=0,
    )
    selected_row = filtered_timeline[filtered_timeline["cycle_id"] == selected_cycle].iloc[0]

    pred_cols = st.columns(4)
    pred_cols[0].metric("Cycle", int(selected_row["cycle_id"]))
    pred_cols[1].metric("Valve reelle (%)", int(selected_row["valve_pct"]))
    pred_cols[2].metric("Probabilite predite (%)", f"{selected_row['predicted_optimality_pct']:.1f}")
    pred_cols[3].metric("Label predit", int(selected_row["predicted_label"]))
