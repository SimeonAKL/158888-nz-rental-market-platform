"""Final forward forecasting dashboard page."""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from rmp.dashboard.data import (
    load_combined_predictions,
    load_final_forward_forecasts,
    load_monthly_panel,
    load_series_model_winners,
)
from rmp.dashboard.filters import (
    geography_label,
    metric_axis_label,
    metric_label,
    series_selector,
)
from rmp.dashboard.formatters import (
    format_percentage,
    format_value,
)
from rmp.dashboard.layout import (
    inject_home_styles,
    render_card_header,
    render_filter_header,
    render_legend,
    render_page_hero,
    render_series_header,
    render_source_note,
    render_stat_card,
    render_top_navigation,
    tone_for,
)

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Forecasting",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_home_styles()
render_top_navigation(
    active_page="Forecasting",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

HERO_IMAGE_PATH = PROJECT_ROOT / "assets" / "forecasting_hero.jpg"


# ---------------------------------------------------------------------
# Chart palette
# ---------------------------------------------------------------------

BLUE = "#1769ff"
DARK_BLUE = "#0b57d0"
LIGHT_BLUE = "#8fc4ff"
PALE_BLUE = "#e8f2ff"

LABEL_COLOR = "#71809c"
TITLE_COLOR = "#52617e"
TICK_COLOR = "#d7dfeb"
GRID_COLOR = "#edf1f7"


MODEL_LABELS = {
    "seasonal_naive": "Seasonal Naive",
    "ets_additive_damped": "ETS (Additive Damped)",
    "xgboost_pooled_recursive": ("XGBoost (Pooled Recursive)"),
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def model_label(
    model: str,
) -> str:
    """Return a user-facing model label."""
    return MODEL_LABELS.get(
        model,
        model.replace("_", " ").title(),
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


def format_smape(
    value: float,
) -> str:
    """Format sMAPE."""
    if pd.isna(value):
        return "N/A"

    return f"{value:,.2f}%"


def history_window_options(
    n_observations: int,
) -> tuple[list[int], int]:
    """Return sensible historical-window options."""
    candidates = [
        12,
        24,
        36,
        60,
        84,
        120,
    ]

    maximum = min(
        120,
        n_observations,
    )

    options = [value for value in candidates if value <= maximum]

    if maximum not in options:
        options.append(maximum)

    options = sorted(set(options))

    preferred = [value for value in options if value <= 60]

    default = max(preferred) if preferred else options[-1]

    return (
        options,
        default,
    )


# ---------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------

render_page_hero(
    "Forecasting",
    (
        "Six-month forward forecasts generated from "
        "the selected winner model for each "
        "forecast-eligible rental-market series."
    ),
    HERO_IMAGE_PATH,
)


# ---------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------

try:
    panel = load_monthly_panel()

    final_forecasts = load_final_forward_forecasts()

    winners = load_series_model_winners()

    backtest_predictions = load_combined_predictions()

except (
    FileNotFoundError,
    ValueError,
) as exc:
    st.error(str(exc))
    st.stop()


# ---------------------------------------------------------------------
# Forecast selection
# ---------------------------------------------------------------------

with st.container(
    key="filters_forecasting",
):
    render_filter_header(
        "Forecast Selection",
        (
            "Choose a geography, location, and "
            "market indicator to review its "
            "historical series and forecast availability."
        ),
    )

    (
        selected_geography,
        selected_location,
        selected_metric,
    ) = series_selector(
        panel,
        key_prefix="forecasting",
    )


# ---------------------------------------------------------------------
# Resolve selected analytical series
# ---------------------------------------------------------------------

series_matches = panel.loc[
    (panel["geography_level"] == selected_geography)
    & (panel["location_name"] == selected_location)
    & (panel["metric"] == selected_metric)
].copy()

series_ids = series_matches["series_id"].dropna().unique()

if len(series_ids) != 1:
    st.error(
        "The selected geography, location, and "
        "indicator do not resolve to exactly "
        "one analytical series."
    )
    st.stop()

series_id = str(series_ids[0])

history = (
    panel.loc[panel["series_id"] == series_id]
    .copy()
    .sort_values("period_date")
    .reset_index(drop=True)
)

if history.empty:
    st.warning("No historical observations are available for this series.")
    st.stop()

latest_observation = history.iloc[-1]

latest_date = pd.Timestamp(latest_observation["period_date"])

latest_value = float(latest_observation["value"])

axis_label = metric_axis_label(selected_metric)


# ---------------------------------------------------------------------
# Series header
# ---------------------------------------------------------------------

render_series_header(
    (f"{selected_location} — {metric_label(selected_metric)}"),
    (
        f"{geography_label(selected_geography)}"
        "  •  "
        f"{series_id}"
        "  •  "
        f"Latest observation {latest_date:%b %Y}"
    ),
)

if history["is_provisional"].fillna(False).any():
    render_source_note()


# ---------------------------------------------------------------------
# Forecast availability
# ---------------------------------------------------------------------

series_forecast = final_forecasts.loc[final_forecasts["series_id"] == series_id].copy()

series_winner = winners.loc[winners["series_id"] == series_id].copy()


# ---------------------------------------------------------------------
# Historical-only series
# ---------------------------------------------------------------------

if series_forecast.empty or series_winner.empty:
    historical_specs = [
        (
            "Latest Observed Value",
            format_value(
                latest_value,
                selected_metric,
            ),
            f"{latest_date:%b %Y}",
            "",
        ),
        (
            "Forecast Status",
            "Historical Only",
            ("No final forward forecast for this series"),
            "",
        ),
    ]

    for column, (
        label,
        value,
        note,
        tone,
    ) in zip(
        st.columns(2),
        historical_specs,
    ):
        with column:
            render_stat_card(
                label,
                value,
                note,
                tone,
            )

    if selected_geography == "territorial_authority" and selected_location == "Auckland":
        st.info(
            "**Auckland forecasts are provided at Region level.** "
            "The Auckland Territorial Authority series is retained "
            "for historical analysis only. To view Auckland forward "
            "forecasts, select **Region → Auckland Region**."
        )

    else:
        st.info(
            "This series is available for historical analysis "
            "but is not included in the forecast-eligible "
            "modelling subset. Forecast availability is determined "
            "during modelling preparation using data continuity, "
            "quality requirements, and defined modelling-scope rules."
        )

    with st.container(
        key="card_forecasting_historical_only",
    ):
        render_card_header(
            "Historical Series",
            (
                "Historical observations remain available "
                "even when a series is outside the "
                "forward-forecasting subset."
            ),
        )

        (
            window_options,
            window_default,
        ) = history_window_options(len(history))

        history_window = st.select_slider(
            "Historical months shown",
            options=window_options,
            value=window_default,
            key=("forecasting_historical_only_window"),
        )

        recent_history = history.tail(history_window)

        history_chart = (
            alt.Chart(recent_history)
            .mark_line(
                color=BLUE,
                strokeWidth=2.4,
            )
            .encode(
                x=alt.X(
                    "period_date:T",
                    title=None,
                    axis=alt.Axis(
                        format="%Y",
                        grid=False,
                        labelColor=(LABEL_COLOR),
                        tickColor=(TICK_COLOR),
                    ),
                ),
                y=alt.Y(
                    "value:Q",
                    title=axis_label,
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(
                        labelColor=(LABEL_COLOR),
                        titleColor=(TITLE_COLOR),
                        gridColor=(GRID_COLOR),
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "period_date:T",
                        title="Period",
                        format="%b %Y",
                    ),
                    alt.Tooltip(
                        "value:Q",
                        title=axis_label,
                        format=",.1f",
                    ),
                ],
            )
            .properties(height=340)
            .interactive(bind_y=False)
            .configure_view(strokeWidth=0)
        )

        st.altair_chart(
            history_chart,
            width="stretch",
        )

    st.stop()


# ---------------------------------------------------------------------
# Final forward forecast
# ---------------------------------------------------------------------

series_forecast = series_forecast.sort_values("horizon_step").reset_index(drop=True)

winner = series_winner.iloc[0]

winner_model = str(winner["best_model"])

forecast_origin = pd.Timestamp(series_forecast["forecast_origin"].iloc[0])

forecast_start = pd.Timestamp(series_forecast["forecast_period"].min())

forecast_end = pd.Timestamp(series_forecast["forecast_period"].max())

first_forecast = float(series_forecast.iloc[0]["predicted"])

ending_forecast = float(series_forecast.iloc[-1]["predicted"])

forecast_change = ending_forecast - latest_value

forecast_change_pct = None

if latest_value != 0:
    forecast_change_pct = forecast_change / abs(latest_value) * 100


# ---------------------------------------------------------------------
# Forecast headline
# ---------------------------------------------------------------------

with st.container(
    key="card_forecast_headline",
):
    render_card_header(
        "Final 6-Month Forward Forecast",
        (
            "The selected winner model is refitted "
            "using all available observations through "
            "the forecast origin before producing "
            "the six-month future projection."
        ),
    )

    headline_specs = [
        (
            "Latest Observed",
            format_value(
                latest_value,
                selected_metric,
            ),
            f"{latest_date:%b %Y}",
            "",
        ),
        (
            "Winner Model",
            model_label(winner_model),
            ("Selected by rolling-origin validation"),
            "",
        ),
        (
            "Forecast Origin",
            forecast_origin.strftime("%b %Y"),
            ("Latest month included in model fitting"),
            "",
        ),
        (
            "6-Month Forecast",
            format_value(
                ending_forecast,
                selected_metric,
            ),
            (
                format_percentage(forecast_change_pct) + " vs latest observed"
                if forecast_change_pct is not None
                else "Change unavailable"
            ),
            tone_for(forecast_change_pct),
        ),
    ]

    for column, (
        label,
        value,
        note,
        tone,
    ) in zip(
        st.columns(4),
        headline_specs,
    ):
        with column:
            render_stat_card(
                label,
                value,
                note,
                tone,
            )


# ---------------------------------------------------------------------
# Historical + forecast chart
# ---------------------------------------------------------------------

with st.container(
    key="card_forecast_chart",
):
    render_card_header(
        "Observed History and 6-Month Forecast",
        (
            "Historical observations are shown alongside "
            "the final winner-model forecast. The shaded "
            "area marks the future forecast period."
        ),
    )

    render_legend(
        [
            (
                "Observed",
                LIGHT_BLUE,
                2,
            ),
            (
                "Forecast",
                BLUE,
                4,
            ),
        ]
    )

    (
        window_options,
        window_default,
    ) = history_window_options(len(history))

    history_window = st.select_slider(
        "Historical months shown",
        options=window_options,
        value=window_default,
        key=("forecasting_history_window"),
    )

    recent_history = history.tail(history_window)[
        [
            "period_date",
            "value",
        ]
    ].copy()

    forecast_line = pd.concat(
        [
            pd.DataFrame(
                {
                    "forecast_period": [forecast_origin],
                    "predicted": [latest_value],
                }
            ),
            series_forecast[
                [
                    "forecast_period",
                    "predicted",
                ]
            ],
        ],
        ignore_index=True,
    )

    forecast_band = pd.DataFrame(
        {
            "start": [forecast_start],
            "end": [forecast_end],
        }
    )

    origin_frame = pd.DataFrame({"origin": [forecast_origin]})

    historical_line = (
        alt.Chart(recent_history)
        .mark_line(
            color=LIGHT_BLUE,
            strokeWidth=2,
        )
        .encode(
            x=alt.X(
                "period_date:T",
                title=None,
                axis=alt.Axis(
                    format="%Y",
                    grid=False,
                    labelColor=(LABEL_COLOR),
                    tickColor=(TICK_COLOR),
                ),
            ),
            y=alt.Y(
                "value:Q",
                title=axis_label,
                scale=alt.Scale(zero=False),
                axis=alt.Axis(
                    labelColor=(LABEL_COLOR),
                    titleColor=(TITLE_COLOR),
                    gridColor=(GRID_COLOR),
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "period_date:T",
                    title="Observed Month",
                    format="%b %Y",
                ),
                alt.Tooltip(
                    "value:Q",
                    title="Observed",
                    format=",.1f",
                ),
            ],
        )
    )

    forecast_area = (
        alt.Chart(forecast_band)
        .mark_rect(
            color=PALE_BLUE,
            opacity=0.55,
        )
        .encode(
            x="start:T",
            x2="end:T",
        )
    )

    origin_rule = (
        alt.Chart(origin_frame)
        .mark_rule(
            color="#8ba7d1",
            strokeDash=[
                5,
                4,
            ],
            strokeWidth=1.4,
        )
        .encode(x="origin:T")
    )

    forecast_path = (
        alt.Chart(forecast_line)
        .mark_line(
            color=BLUE,
            strokeWidth=3,
            point=alt.OverlayMarkDef(
                filled=True,
                fill=DARK_BLUE,
                size=70,
            ),
        )
        .encode(
            x=alt.X(
                "forecast_period:T",
                title=None,
            ),
            y=alt.Y(
                "predicted:Q",
                title=axis_label,
            ),
            tooltip=[
                alt.Tooltip(
                    "forecast_period:T",
                    title="Forecast Month",
                    format="%b %Y",
                ),
                alt.Tooltip(
                    "predicted:Q",
                    title="Forecast",
                    format=",.1f",
                ),
            ],
        )
    )

    forecast_chart = (
        alt.layer(
            forecast_area,
            historical_line,
            origin_rule,
            forecast_path,
        )
        .resolve_scale(y="shared")
        .properties(height=380)
        .interactive(bind_y=False)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(
        forecast_chart,
        width="stretch",
    )

    st.caption(
        "Observed values end at the forecast origin. "
        f"The future forecast covers {forecast_start:%b %Y} "
        f"to {forecast_end:%b %Y}."
    )


# ---------------------------------------------------------------------
# Forecast values
# ---------------------------------------------------------------------

with st.container(
    key="card_forecast_values",
):
    (
        forecast_title_col,
        forecast_button_col,
    ) = st.columns(
        [4, 1],
        vertical_alignment="center",
    )

    with forecast_title_col:
        render_card_header(
            "Forecast Values",
            (f"Six monthly predictions from the {model_label(winner_model)} model."),
        )

    download_data = (
        series_forecast[
            [
                "series_id",
                "metric",
                "geography_level",
                "location_id",
                "location_name",
                "model",
                "forecast_origin",
                "forecast_period",
                "horizon_step",
                "predicted",
                "backtest_mae",
                "backtest_rmse",
                "backtest_smape",
            ]
        ]
        .to_csv(index=False)
        .encode("utf-8")
    )

    with (
        forecast_button_col,
        st.container(
            key="download_forecast",
        ),
    ):
        st.download_button(
            label="Download CSV",
            data=download_data,
            file_name=(f"{series_id}_six_month_forecast.csv"),
            mime="text/csv",
            width="stretch",
        )

    display_forecast = series_forecast[
        [
            "forecast_period",
            "horizon_step",
            "predicted",
        ]
    ].copy()

    if latest_value != 0:
        display_forecast["change_vs_latest_pct"] = (
            display_forecast["predicted"] / latest_value - 1
        ) * 100
    else:
        display_forecast["change_vs_latest_pct"] = float("nan")

    display_forecast["Forecast Month"] = display_forecast["forecast_period"].dt.strftime("%b %Y")

    display_forecast["Predicted Value"] = [
        format_value(
            value,
            selected_metric,
        )
        for value in display_forecast["predicted"]
    ]

    display_forecast["Change vs Latest"] = [
        format_percentage(value) for value in display_forecast["change_vs_latest_pct"]
    ]

    display_forecast = display_forecast[
        [
            "Forecast Month",
            "horizon_step",
            "Predicted Value",
            "Change vs Latest",
        ]
    ].rename(
        columns={
            "horizon_step": "Horizon",
        }
    )

    st.dataframe(
        display_forecast,
        width="stretch",
        hide_index=True,
    )


# ---------------------------------------------------------------------
# Forecast interpretation
# ---------------------------------------------------------------------

with st.container(
    key="card_forecast_interpretation",
):
    render_card_header(
        "Forecast Interpretation",
        ("A concise summary of the forecast window and projected movement."),
    )

    interpretation_specs = [
        (
            "Forecast Window",
            (f"{forecast_start:%b %Y} – {forecast_end:%b %Y}"),
            "Six-month horizon",
            "",
        ),
        (
            "First Forecast",
            format_value(
                first_forecast,
                selected_metric,
            ),
            f"{forecast_start:%b %Y}",
            "",
        ),
        (
            "Change to Horizon 6",
            format_percentage(forecast_change_pct),
            (
                f"{format_value(latest_value, selected_metric)}"
                " → "
                f"{format_value(ending_forecast, selected_metric)}"
            ),
            tone_for(forecast_change_pct),
        ),
    ]

    for column, (
        label,
        value,
        note,
        tone,
    ) in zip(
        st.columns(3),
        interpretation_specs,
    ):
        with column:
            render_stat_card(
                label,
                value,
                note,
                tone,
                flat=True,
            )

    st.info(
        "Forward forecasts are model-based analytical "
        "projections rather than observed rental-market "
        "values. They should not be interpreted as "
        "guaranteed future outcomes or individual "
        "property valuations."
    )


# ---------------------------------------------------------------------
# Model evaluation
# ---------------------------------------------------------------------

with st.container(
    key="card_forecast_evaluation",
):
    render_card_header(
        "Model Evaluation",
        (
            "Winner-model performance from historical "
            "rolling-origin out-of-sample validation. "
            "These metrics are evaluation evidence and "
            "are separate from the future forecast above."
        ),
    )

    evaluation_specs = [
        (
            "Backtest MAE",
            format_error(
                float(winner["best_mae"]),
                selected_metric,
            ),
            "Mean Absolute Error",
        ),
        (
            "Backtest RMSE",
            format_error(
                float(winner["best_rmse"]),
                selected_metric,
            ),
            "Root Mean Squared Error",
        ),
        (
            "Backtest sMAPE",
            format_smape(float(winner["best_smape"])),
            ("Symmetric Mean Absolute Percentage Error"),
        ),
    ]

    for column, (
        label,
        value,
        note,
    ) in zip(
        st.columns(3),
        evaluation_specs,
    ):
        with column:
            render_stat_card(
                label,
                value,
                note,
                flat=True,
            )


# ---------------------------------------------------------------------
# Latest rolling-origin backtest
# ---------------------------------------------------------------------

winner_backtest = backtest_predictions.loc[
    (backtest_predictions["series_id"] == series_id)
    & (backtest_predictions["model"] == winner_model)
].copy()

if not winner_backtest.empty:
    winner_backtest = winner_backtest.sort_values(
        [
            "origin",
            "horizon_step",
        ]
    )

    latest_origin = pd.Timestamp(winner_backtest["origin"].max())

    latest_backtest = (
        winner_backtest.loc[winner_backtest["origin"] == latest_origin]
        .copy()
        .sort_values("horizon_step")
    )

    with st.expander(
        "Latest Rolling-Origin Backtest",
        expanded=False,
    ):
        st.caption(
            "This historical evaluation window withholds "
            "actual observations from model fitting and "
            "then compares the resulting predictions "
            "with those observed values."
        )

        st.markdown(f"**Evaluation origin:** {latest_origin:%b %Y}")

        render_legend(
            [
                (
                    "Actual",
                    LIGHT_BLUE,
                    2,
                ),
                (
                    "Predicted",
                    BLUE,
                    4,
                ),
            ]
        )

        actual_line = (
            alt.Chart(latest_backtest)
            .mark_line(
                color=LIGHT_BLUE,
                strokeWidth=2,
                point=True,
            )
            .encode(
                x=alt.X(
                    "forecast_period:T",
                    title=None,
                ),
                y=alt.Y(
                    "actual:Q",
                    title=axis_label,
                    scale=alt.Scale(zero=False),
                ),
                tooltip=[
                    alt.Tooltip(
                        "forecast_period:T",
                        title="Month",
                        format="%b %Y",
                    ),
                    alt.Tooltip(
                        "actual:Q",
                        title="Actual",
                        format=",.1f",
                    ),
                ],
            )
        )

        predicted_line = (
            alt.Chart(latest_backtest)
            .mark_line(
                color=BLUE,
                strokeWidth=3,
                point=True,
            )
            .encode(
                x="forecast_period:T",
                y="predicted:Q",
                tooltip=[
                    alt.Tooltip(
                        "forecast_period:T",
                        title="Month",
                        format="%b %Y",
                    ),
                    alt.Tooltip(
                        "predicted:Q",
                        title="Predicted",
                        format=",.1f",
                    ),
                ],
            )
        )

        st.altair_chart(
            (actual_line + predicted_line).properties(height=280).configure_view(strokeWidth=0),
            width="stretch",
        )

        backtest_table = latest_backtest[
            [
                "forecast_period",
                "horizon_step",
                "actual",
                "predicted",
                "absolute_error",
            ]
        ].copy()

        backtest_table["Month"] = backtest_table["forecast_period"].dt.strftime("%b %Y")

        backtest_table["Actual"] = [
            format_value(
                value,
                selected_metric,
            )
            for value in backtest_table["actual"]
        ]

        backtest_table["Predicted"] = [
            format_value(
                value,
                selected_metric,
            )
            for value in backtest_table["predicted"]
        ]

        backtest_table["Absolute Error"] = [
            format_error(
                value,
                selected_metric,
            )
            for value in backtest_table["absolute_error"]
        ]

        backtest_table = backtest_table[
            [
                "Month",
                "horizon_step",
                "Actual",
                "Predicted",
                "Absolute Error",
            ]
        ].rename(
            columns={
                "horizon_step": "Horizon",
            }
        )

        st.dataframe(
            backtest_table,
            width="stretch",
            hide_index=True,
        )


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

with st.expander(
    "Forecasting Methodology",
    expanded=False,
):
    st.markdown(
        """
The forecasting workflow evaluates three candidate models:

- **Seasonal Naive** — monthly seasonal baseline using the
  corresponding observation from the previous year.
- **ETS (Additive Damped)** — Holt-Winters exponential smoothing
  with additive trend, additive seasonality and a damped trend.
- **XGBoost (Pooled Recursive)** — pooled machine-learning model
  using lag, rolling, calendar and geography-aware location features.

Models are evaluated using **rolling-origin validation** with a
six-month forecast horizon. MAE, RMSE and sMAPE are used as
forecast-error measures.

A winner model is selected separately for each forecast-eligible
series. The winner is then refitted using all available historical
observations through the final forecast origin before generating
the six-month forward forecast.

The forward forecast is therefore a **genuine future projection**
and is separate from the historical rolling-origin backtest
predictions.
"""
    )
