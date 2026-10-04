"""Forecast model performance page."""

from __future__ import annotations

import streamlit as st

from rmp.dashboard.data import (
    load_metrics_by_horizon,
    load_model_comparison,
    load_series_model_winners,
)
from rmp.dashboard.filters import metric_label

st.set_page_config(
    page_title="Model Performance",
    page_icon="🧠",
    layout="wide",
)

st.title("Model Performance")

comparison = load_model_comparison()
horizon = load_metrics_by_horizon()
winners = load_series_model_winners()

metrics = sorted(
    comparison["metric"].unique()
)

selected_metric = st.sidebar.selectbox(
    "Metric",
    metrics,
    format_func=metric_label,
)

metric_comparison = comparison[
    comparison["metric"]
    == selected_metric
].copy()

st.subheader(
    metric_label(selected_metric)
)

best_mae = (
    metric_comparison
    .sort_values("rank_mae")
    .iloc[0]
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Best Model",
    best_mae["model"],
)

col2.metric(
    "MAE",
    f"{best_mae['mae']:.2f}",
)

col3.metric(
    "RMSE",
    f"{best_mae['rmse']:.2f}",
)

col4.metric(
    "sMAPE",
    f"{best_mae['smape']:.2f}%",
)

st.subheader("Overall Model Comparison")

st.dataframe(
    metric_comparison.sort_values(
        "rank_mae"
    ),
    use_container_width=True,
    hide_index=True,
)

st.subheader("MAE by Model")

st.bar_chart(
    metric_comparison[
        [
            "model",
            "mae",
        ]
    ].set_index("model"),
    use_container_width=True,
)

st.subheader("Performance by Forecast Horizon")

metric_horizon = horizon[
    horizon["metric"]
    == selected_metric
]

horizon_chart = (
    metric_horizon.pivot(
        index="horizon_step",
        columns="model",
        values="mae",
    )
)

st.line_chart(
    horizon_chart,
    use_container_width=True,
)

st.subheader("Winner Distribution")

winner_counts = (
    winners[
        winners["metric"]
        == selected_metric
    ]["best_model"]
    .value_counts()
    .rename_axis("model")
    .to_frame("series_count")
)

st.bar_chart(
    winner_counts,
    use_container_width=True,
)
