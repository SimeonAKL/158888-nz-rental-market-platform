"""Forecast model performance dashboard page."""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from rmp.dashboard.data import (
    load_metrics_by_horizon,
    load_model_comparison,
    load_monthly_panel,
    load_series_model_winners,
)
from rmp.dashboard.filters import metric_label
from rmp.dashboard.layout import (
    inject_home_styles,
    render_card_header,
    render_filter_header,
    render_footer,
    render_legend,
    render_page_hero,
    render_source_note,
    render_stat_card,
    render_top_navigation,
)

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Model Performance",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_home_styles()
render_top_navigation(
    active_page="Model Performance",
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HERO_IMAGE_PATH = PROJECT_ROOT / "assets" / "auckland_skyline.jpg"


# ---------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------

BLUE = "#1769ff"
MID_BLUE = "#5597ff"
LIGHT_BLUE = "#9cc4ff"

LABEL_COLOR = "#71809c"
TITLE_COLOR = "#52617e"
GRID_COLOR = "#edf1f7"
TICK_COLOR = "#d7dfeb"


MODEL_LABELS = {
    "seasonal_naive": ("Seasonal Naive"),
    "ets_additive_damped": ("ETS (Additive Damped)"),
    "xgboost_pooled_recursive": ("XGBoost (Pooled Recursive)"),
}


MODEL_SHORT_LABELS = {
    "seasonal_naive": ("Seasonal Naive"),
    "ets_additive_damped": ("ETS"),
    "xgboost_pooled_recursive": ("XGBoost"),
}


MODEL_ORDER = [
    "seasonal_naive",
    "ets_additive_damped",
    "xgboost_pooled_recursive",
]


MODEL_COLORS = {
    "seasonal_naive": LIGHT_BLUE,
    "ets_additive_damped": MID_BLUE,
    "xgboost_pooled_recursive": BLUE,
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def model_label(
    model: str,
) -> str:
    """Return a user-facing model name."""
    return MODEL_LABELS.get(
        model,
        model.replace(
            "_",
            " ",
        ).title(),
    )


def short_model_label(
    model: str,
) -> str:
    """Return a compact model name."""
    return MODEL_SHORT_LABELS.get(
        model,
        model_label(model),
    )


def format_error(
    value: float,
    metric: str,
) -> str:
    """Format forecast-error values."""
    if pd.isna(value):
        return "N/A"

    if metric == "median_rent":
        return f"${value:,.2f}"

    return f"{value:,.2f}"


def format_percentage(
    value: float,
) -> str:
    """Format a percentage metric."""
    if pd.isna(value):
        return "N/A"

    return f"{value:,.2f}%"


def model_color_scale() -> alt.Scale:
    """Return consistent model colors."""
    return alt.Scale(
        domain=MODEL_ORDER,
        range=[MODEL_COLORS[model] for model in MODEL_ORDER],
    )


# ---------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------

render_page_hero(
    "Model Performance",
    (
        "Compare forecasting accuracy across Seasonal Naive, "
        "ETS, and XGBoost using rolling-origin validation "
        "and standardized forecast-error metrics."
    ),
    HERO_IMAGE_PATH,
)


# ---------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------

try:
    comparison = load_model_comparison()

    horizon = load_metrics_by_horizon()

    winners = load_series_model_winners()

    panel = load_monthly_panel()

except (
    FileNotFoundError,
    ValueError,
) as exc:
    st.error(str(exc))
    st.stop()


if panel["source_snapshot_provisional"].fillna(False).any():
    render_source_note()


# ---------------------------------------------------------------------
# Indicator selection
# ---------------------------------------------------------------------

metrics = [
    metric
    for metric in [
        "median_rent",
        "bonds_lodged",
    ]
    if metric in comparison["metric"].dropna().unique()
]

if not metrics:
    metrics = sorted(comparison["metric"].dropna().unique())


with st.container(
    key="filters_model_performance",
):
    render_filter_header(
        "Performance Selection",
        (
            "Choose a market indicator to compare "
            "candidate-model accuracy, horizon performance, "
            "and series-level winner distribution."
        ),
    )

    selected_metric = st.selectbox(
        "Indicator",
        metrics,
        format_func=metric_label,
        key=("model_performance_metric"),
    )


# ---------------------------------------------------------------------
# Selected metric data
# ---------------------------------------------------------------------

metric_comparison = comparison.loc[comparison["metric"] == selected_metric].copy()

metric_horizon = horizon.loc[horizon["metric"] == selected_metric].copy()

metric_winners = winners.loc[winners["metric"] == selected_metric].copy()


if metric_comparison.empty:
    st.warning("No model-comparison results are available for this indicator.")
    st.stop()


eligible_series_count = metric_winners["series_id"].nunique()


# ---------------------------------------------------------------------
# Best model
# ---------------------------------------------------------------------

best_row = metric_comparison.sort_values(
    [
        "rank_mae",
        "mae",
    ]
).iloc[0]

best_model = str(best_row["model"])


# ---------------------------------------------------------------------
# Performance headline
# ---------------------------------------------------------------------

with st.container(
    key="card_model_performance_headline",
):
    render_card_header(
        f"{metric_label(selected_metric)} Performance",
        (
            "Headline statistics for the model with the "
            "lowest overall MAE across the rolling-origin "
            "evaluation."
        ),
    )

    headline_specs = [
        (
            "Best Overall Model",
            model_label(best_model),
            ("Ranked by overall MAE"),
        ),
        (
            "MAE",
            format_error(
                float(best_row["mae"]),
                selected_metric,
            ),
            ("Mean Absolute Error"),
        ),
        (
            "RMSE",
            format_error(
                float(best_row["rmse"]),
                selected_metric,
            ),
            ("Root Mean Squared Error"),
        ),
        (
            "sMAPE",
            format_percentage(float(best_row["smape"])),
            ("Symmetric percentage error"),
        ),
    ]

    for column, (
        label,
        value,
        note,
    ) in zip(
        st.columns(4),
        headline_specs,
    ):
        with column:
            render_stat_card(
                label,
                value,
                note,
            )


# ---------------------------------------------------------------------
# Overall model comparison
# ---------------------------------------------------------------------

with st.container(
    key="card_model_comparison",
):
    render_card_header(
        "Overall Model Comparison",
        (
            "Candidate models ranked using aggregated "
            "rolling-origin forecast performance for "
            f"{metric_label(selected_metric)}."
        ),
    )

    comparison_display = metric_comparison.sort_values("rank_mae").copy()

    comparison_display["Model"] = comparison_display["model"].map(model_label)

    comparison_display["MAE"] = [
        format_error(
            value,
            selected_metric,
        )
        for value in comparison_display["mae"]
    ]

    comparison_display["RMSE"] = [
        format_error(
            value,
            selected_metric,
        )
        for value in comparison_display["rmse"]
    ]

    comparison_display["sMAPE"] = [
        format_percentage(value) for value in comparison_display["smape"]
    ]

    comparison_display["MAE Rank"] = comparison_display["rank_mae"].astype(int)

    display_columns = [
        "Model",
        "MAE",
        "RMSE",
        "sMAPE",
        "MAE Rank",
    ]

    if "mae_improvement_vs_baseline_pct" in comparison_display.columns:
        comparison_display["MAE Improvement vs Baseline"] = [
            format_percentage(value)
            for value in comparison_display["mae_improvement_vs_baseline_pct"]
        ]

        display_columns.append("MAE Improvement vs Baseline")

    # Presentation-only styling for model comparison.
    # Smaller MAE, RMSE and sMAPE values indicate better accuracy.
    comparison_table = comparison_display[display_columns].copy()

    def improvement_style(value: object) -> str:
        """Style MAE improvement relative to the baseline."""
        try:
            numeric_value = float(
                str(value)
                .replace("%", "")
                .replace(",", "")
                .replace("−", "-")
            )
        except (TypeError, ValueError):
            return "color: #7b88a4"

        if numeric_value > 0:
            return "color: #13864a"

        if numeric_value < 0:
            return "color: #cc4545"

        return "color: #7b88a4"

    styled_comparison = comparison_table.style

    # Highlight the lowest error in each metric using raw values.
    metric_pairs = [
        ("MAE", "mae"),
        ("RMSE", "rmse"),
        ("sMAPE", "smape"),
    ]

    metric_styles = pd.DataFrame(
        "",
        index=comparison_table.index,
        columns=comparison_table.columns,
    )

    for display_column, numeric_column in metric_pairs:
        if (
            display_column in comparison_table.columns
            and numeric_column in comparison_display.columns
        ):
            numeric_values = pd.to_numeric(
                comparison_display[numeric_column],
                errors="coerce",
            )

            best_value = numeric_values.min()

            if pd.notna(best_value):
                best_rows = numeric_values.index[
                    numeric_values == best_value
                ]

                metric_styles.loc[
                    best_rows,
                    display_column,
                ] = "color: #13864a; font-weight: 600"

    styled_comparison = styled_comparison.apply(
        lambda _: metric_styles,
        axis=None,
    )

    styled_comparison = styled_comparison.map(
        lambda value: (
            "color: #1769ff; font-weight: 600"
            if value == 1 else ""
        ),
        subset=["MAE Rank"],
    )

    if "MAE Improvement vs Baseline" in comparison_table.columns:
        styled_comparison = styled_comparison.map(
            improvement_style,
            subset=["MAE Improvement vs Baseline"],
        )

    comparison_table_height = min(
        430,
        (len(comparison_table) + 1) * 35 + 3,
    )

    st.dataframe(
        styled_comparison,
        width="stretch",
        hide_index=True,
        height=comparison_table_height,
    )


# ---------------------------------------------------------------------
# MAE by model
# ---------------------------------------------------------------------

with st.container(
    key="card_model_mae",
):
    render_card_header(
        "MAE by Model",
        ("Lower MAE indicates better average out-of-sample forecast accuracy."),
    )

    mae_chart_data = metric_comparison[
        [
            "model",
            "mae",
        ]
    ].copy()

    mae_chart_data["model_label"] = mae_chart_data["model"].map(short_model_label)

    mae_chart = (
        alt.Chart(mae_chart_data)
        .mark_bar(
            cornerRadiusEnd=6,
        )
        .encode(
            y=alt.Y(
                "model_label:N",
                title=None,
                sort=[short_model_label(model) for model in MODEL_ORDER],
                axis=alt.Axis(
                    labelColor=(LABEL_COLOR),
                    tickColor=(TICK_COLOR),
                ),
            ),
            x=alt.X(
                "mae:Q",
                title="Mean Absolute Error",
                axis=alt.Axis(
                    labelColor=(LABEL_COLOR),
                    titleColor=(TITLE_COLOR),
                    gridColor=(GRID_COLOR),
                ),
            ),
            color=alt.Color(
                "model:N",
                scale=model_color_scale(),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "model_label:N",
                    title="Model",
                ),
                alt.Tooltip(
                    "mae:Q",
                    title="MAE",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=230)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(
        mae_chart,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Performance by forecast horizon
# ---------------------------------------------------------------------

with st.container(
    key="card_model_horizon",
):
    render_card_header(
        "Performance by Forecast Horizon",
        (
            "MAE across forecast horizons 1–6. "
            "This shows how model accuracy changes "
            "as forecasts extend further into the future."
        ),
    )

    render_legend(
        [
            (
                "Seasonal Naive",
                LIGHT_BLUE,
                3,
            ),
            (
                "ETS",
                MID_BLUE,
                3,
            ),
            (
                "XGBoost",
                BLUE,
                3,
            ),
        ]
    )

    if metric_horizon.empty:
        st.info("No horizon-level metrics are available for this indicator.")

    else:
        horizon_chart_data = metric_horizon.copy()

        horizon_chart_data["model_label"] = horizon_chart_data["model"].map(short_model_label)

        horizon_chart = (
            alt.Chart(horizon_chart_data)
            .mark_line(
                strokeWidth=2.6,
                point=alt.OverlayMarkDef(
                    filled=True,
                    size=65,
                ),
            )
            .encode(
                x=alt.X(
                    "horizon_step:O",
                    title="Forecast Horizon (months)",
                    axis=alt.Axis(
                        labelAngle=0,
                        labelColor=(LABEL_COLOR),
                        titleColor=(TITLE_COLOR),
                        tickColor=(TICK_COLOR),
                    ),
                ),
                y=alt.Y(
                    "mae:Q",
                    title="Mean Absolute Error",
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(
                        labelColor=(LABEL_COLOR),
                        titleColor=(TITLE_COLOR),
                        gridColor=(GRID_COLOR),
                    ),
                ),
                color=alt.Color(
                    "model:N",
                    scale=model_color_scale(),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip(
                        "model_label:N",
                        title="Model",
                    ),
                    alt.Tooltip(
                        "horizon_step:O",
                        title="Horizon",
                    ),
                    alt.Tooltip(
                        "mae:Q",
                        title="MAE",
                        format=",.2f",
                    ),
                ],
            )
            .properties(height=320)
            .configure_view(strokeWidth=0)
        )

        st.altair_chart(
            horizon_chart,
            width="stretch",
        )


# ---------------------------------------------------------------------
# Winner distribution
# ---------------------------------------------------------------------

with st.container(
    key="card_model_winners",
):
    render_card_header(
        "Series-Level Winner Distribution",
        (
            f"{eligible_series_count:,} forecast-eligible series "
            f"are included for {metric_label(selected_metric)}. "
            "The chart shows how many series selected each "
            "candidate model as the lowest-sMAPE winner, "
            "with MAE and RMSE used as tie-breakers."
        ),
    )

    if metric_winners.empty:
        st.info("No series-level winner data are available for this indicator.")

    else:
        winner_counts = (
            metric_winners["best_model"]
            .value_counts()
            .rename_axis("model")
            .reset_index(name="series_count")
        )

        # Ensure all three models appear in a fixed,
        # consistent order even if one has zero winners.
        winner_counts = pd.DataFrame({"model": (MODEL_ORDER)}).merge(
            winner_counts,
            on="model",
            how="left",
        )

        winner_counts["series_count"] = winner_counts["series_count"].fillna(0).astype(int)

        winner_counts["model_label"] = winner_counts["model"].map(short_model_label)

        total_winners = int(winner_counts["series_count"].sum())

        if total_winners > 0:
            winner_counts["share_pct"] = winner_counts["series_count"] / total_winners * 100
        else:
            winner_counts["share_pct"] = 0.0

        winner_chart = (
            alt.Chart(winner_counts)
            .mark_bar(
                cornerRadiusTopLeft=6,
                cornerRadiusTopRight=6,
            )
            .encode(
                x=alt.X(
                    "model_label:N",
                    title=None,
                    sort=[short_model_label(model) for model in MODEL_ORDER],
                    axis=alt.Axis(
                        labelAngle=0,
                        labelColor=(LABEL_COLOR),
                        tickColor=(TICK_COLOR),
                    ),
                ),
                y=alt.Y(
                    "series_count:Q",
                    title="Winning Series",
                    axis=alt.Axis(
                        labelColor=(LABEL_COLOR),
                        titleColor=(TITLE_COLOR),
                        gridColor=(GRID_COLOR),
                    ),
                ),
                color=alt.Color(
                    "model:N",
                    scale=model_color_scale(),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip(
                        "model_label:N",
                        title="Model",
                    ),
                    alt.Tooltip(
                        "series_count:Q",
                        title="Winning Series",
                    ),
                    alt.Tooltip(
                        "share_pct:Q",
                        title="Share",
                        format=".1f",
                    ),
                ],
            )
            .properties(height=300)
            .configure_view(strokeWidth=0)
        )

        st.altair_chart(
            winner_chart,
            width="stretch",
        )

        winner_columns = st.columns(len(MODEL_ORDER))

        for column, row in zip(
            winner_columns,
            winner_counts.itertuples(index=False),
        ):
            with column:
                render_stat_card(
                    short_model_label(row.model),
                    f"{row.series_count:,}",
                    (f"{row.share_pct:.1f}% of eligible series"),
                    flat=True,
                )


# ---------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------

with st.container(
    key="card_model_performance_note",
):
    render_card_header(
        "How to Read These Results",
        ("Overall model rankings and series-level winner counts answer different questions."),
    )

    st.info(
        "**Overall comparison** aggregates forecast errors "
        "across the selected indicator and is useful for "
        "comparing general model performance. "
        "**Series-level winner distribution** counts which "
        "model performs best for each individual "
        "forecast-eligible geographic series. "
        "These winners are retained as comparative research results "
        "and do not determine the final production forecast model. "
        "A model can therefore rank best overall without "
        "being the winner for every location."
    )


render_footer()
