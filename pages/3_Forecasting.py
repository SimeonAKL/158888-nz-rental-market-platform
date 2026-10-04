"""Final forward forecasting dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from rmp.dashboard.data import (
    load_combined_predictions,
    load_final_forward_forecasts,
    load_monthly_panel,
    load_series_model_winners,
)

MODEL_LABELS = {
    "seasonal_naive": "Seasonal Naive",
    "ets_additive_damped": "ETS (Additive Damped)",
    "xgboost_pooled_recursive": (
        "XGBoost (Pooled Recursive)"
    ),
}

METRIC_LABELS = {
    "median_rent": "Median Weekly Rent",
    "bonds_lodged": "New Bond Lodgements",
}

GEOGRAPHY_LABELS = {
    "region": "Region",
    "territorial_authority": (
        "Territorial Authority"
    ),
}


def format_value(
    value: float,
    metric: str,
) -> str:
    """Format a model value for dashboard display."""
    if pd.isna(value):
        return "N/A"

    if metric == "median_rent":
        return f"${value:,.0f}"

    return f"{value:,.0f}"


def format_metric_value(
    value: float,
) -> str:
    """Format a forecast-error metric."""
    if pd.isna(value):
        return "N/A"

    return f"{value:,.2f}"


def format_smape(
    value: float,
) -> str:
    """Format sMAPE as a percentage."""
    if pd.isna(value):
        return "N/A"

    return f"{value:,.2f}%"


def model_label(
    model: str,
) -> str:
    """Return a user-facing model label."""
    return MODEL_LABELS.get(
        model,
        model,
    )


def metric_label(
    metric: str,
) -> str:
    """Return a user-facing metric label."""
    return METRIC_LABELS.get(
        metric,
        metric,
    )


st.set_page_config(
    page_title="Forecasting",
    page_icon="📈",
    layout="wide",
)

st.title("Forecasting")

st.caption(
    "Six-month forward forecasts are generated from the selected "
    "winner model for each forecast-eligible rental-market series. "
    "Rolling-origin results are retained below as model-evaluation "
    "evidence."
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

try:
    panel = load_monthly_panel()
    final_forecasts = (
        load_final_forward_forecasts()
    )
    winners = (
        load_series_model_winners()
    )
    backtest_predictions = (
        load_combined_predictions()
    )
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.stop()


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.header("Forecast Selection")

geography_options = [
    level
    for level in [
        "region",
        "territorial_authority",
    ]
    if level
    in panel["geography_level"].dropna().unique()
]

selected_geography = st.sidebar.selectbox(
    "Geography level",
    options=geography_options,
    format_func=lambda value: (
        GEOGRAPHY_LABELS.get(
            value,
            value,
        )
    ),
)

geography_data = panel.loc[
    panel["geography_level"]
    == selected_geography
].copy()

locations = sorted(
    geography_data[
        "location_name"
    ]
    .dropna()
    .unique()
    .tolist()
)

selected_location = st.sidebar.selectbox(
    "Location",
    options=locations,
)

location_data = geography_data.loc[
    geography_data["location_name"]
    == selected_location
].copy()

available_metrics = [
    metric
    for metric in [
        "median_rent",
        "bonds_lodged",
    ]
    if metric
    in location_data["metric"].dropna().unique()
]

selected_metric = st.sidebar.selectbox(
    "Metric",
    options=available_metrics,
    format_func=metric_label,
)


# ---------------------------------------------------------------------------
# Resolve selected analytical series
# ---------------------------------------------------------------------------

series_matches = location_data.loc[
    location_data["metric"]
    == selected_metric
].copy()

series_ids = (
    series_matches["series_id"]
    .dropna()
    .unique()
)

if len(series_ids) != 1:
    st.error(
        "The selected geography and metric do not resolve "
        "to exactly one analytical series."
    )
    st.stop()

series_id = str(
    series_ids[0]
)

history = panel.loc[
    panel["series_id"]
    == series_id
].copy()

history = history.sort_values(
    "period_date"
).reset_index(drop=True)

if history.empty:
    st.warning(
        "No historical observations are available "
        "for this series."
    )
    st.stop()

latest_observation = history.iloc[-1]

latest_date = pd.Timestamp(
    latest_observation["period_date"]
)

latest_value = float(
    latest_observation["value"]
)


# ---------------------------------------------------------------------------
# Series header
# ---------------------------------------------------------------------------

st.subheader(
    f"{selected_location} — "
    f"{metric_label(selected_metric)}"
)

st.caption(
    f"{GEOGRAPHY_LABELS.get(selected_geography, selected_geography)} "
    f"series · {series_id}"
)


# ---------------------------------------------------------------------------
# Determine forecast availability
# ---------------------------------------------------------------------------

series_forecast = final_forecasts.loc[
    final_forecasts["series_id"]
    == series_id
].copy()

series_winner = winners.loc[
    winners["series_id"]
    == series_id
].copy()


if series_forecast.empty or series_winner.empty:
    current_col, date_col = st.columns(2)

    current_col.metric(
        "Latest Observed Value",
        format_value(
            latest_value,
            selected_metric,
        ),
    )

    date_col.metric(
        "Latest Observation",
        latest_date.strftime(
            "%b %Y"
        ),
    )

    if (
        selected_geography == "territorial_authority"
        and selected_location == "Auckland"
    ):
        st.info(
            "**Auckland forecasts are provided at Region level.** "
            "The Auckland Territorial Authority series is retained "
            "for historical data analysis only. "
            "To view Auckland forward forecasts, select "
            "**Region → Auckland Region**."
        )
    else:
        st.warning(
            "Forward forecasting is not available for this series. "
            "The series remains available for historical analytics "
            "and historical anomaly detection."
        )

        st.info(
            "Forecast availability is determined during modelling "
            "preparation based on data continuity, data quality, "
            "and the defined forecasting scope."
        )

    st.subheader("Historical Series")

    historical_chart = (
        history[
            [
                "period_date",
                "value",
            ]
        ]
        .rename(
            columns={
                "period_date": "Date",
                "value": "Observed",
            }
        )
        .set_index("Date")
    )

    st.line_chart(
        historical_chart,
        y=["Observed"],
        use_container_width=True,
    )

    st.stop()


# ---------------------------------------------------------------------------
# Final forward forecast
# ---------------------------------------------------------------------------

series_forecast = series_forecast.sort_values(
    "horizon_step"
).reset_index(drop=True)

winner = series_winner.iloc[0]

winner_model = str(
    winner["best_model"]
)

forecast_origin = pd.Timestamp(
    series_forecast[
        "forecast_origin"
    ].iloc[0]
)

forecast_start = pd.Timestamp(
    series_forecast[
        "forecast_period"
    ].min()
)

forecast_end = pd.Timestamp(
    series_forecast[
        "forecast_period"
    ].max()
)

ending_forecast = float(
    series_forecast.sort_values(
        "horizon_step"
    )["predicted"].iloc[-1]
)

first_forecast = float(
    series_forecast.sort_values(
        "horizon_step"
    )["predicted"].iloc[0]
)

forecast_change = (
    ending_forecast
    - latest_value
)

if latest_value != 0:
    forecast_change_pct = (
        forecast_change
        / abs(latest_value)
        * 100.0
    )
else:
    forecast_change_pct = float("nan")


st.subheader("Final 6-Month Forward Forecast")

st.caption(
    "The final forecast uses all available historical observations "
    "through the forecast origin and the winner model selected from "
    "Phase 4 rolling-origin validation."
)

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)

kpi_1.metric(
    "Latest Observed",
    format_value(
        latest_value,
        selected_metric,
    ),
    help=(
        "Most recent published historical observation "
        "available to the model."
    ),
)

kpi_2.metric(
    "Winner Model",
    model_label(
        winner_model
    ),
    help=(
        "Series-level model selected using Phase 4 "
        "rolling-origin validation."
    ),
)

kpi_3.metric(
    "Forecast Origin",
    forecast_origin.strftime(
        "%b %Y"
    ),
    help=(
        "Latest observed month included when fitting "
        "the final forecasting model."
    ),
)

delta_text = None

if pd.notna(
    forecast_change_pct
):
    delta_text = (
        f"{forecast_change_pct:+.1f}% "
        "vs latest observed"
    )

kpi_4.metric(
    "6-Month Forecast",
    format_value(
        ending_forecast,
        selected_metric,
    ),
    delta=delta_text,
    help=(
        "Predicted value at forecast horizon 6."
    ),
)


# ---------------------------------------------------------------------------
# Historical + future chart
# ---------------------------------------------------------------------------

st.subheader("Observed History and Forward Forecast")

history_window_months = st.slider(
    "Historical months shown",
    min_value=12,
    max_value=min(
        120,
        len(history),
    ),
    value=min(
        60,
        len(history),
    ),
    step=12,
)

recent_history = history.tail(
    history_window_months
)[
    [
        "period_date",
        "value",
    ]
].copy()

observed_series = recent_history.rename(
    columns={
        "period_date": "Date",
        "value": "Observed",
    }
).set_index("Date")


forecast_chart_data = pd.concat(
    [
        pd.DataFrame(
            {
                "Date": [
                    forecast_origin
                ],
                "Forecast": [
                    latest_value
                ],
            }
        ),
        series_forecast[
            [
                "forecast_period",
                "predicted",
            ]
        ].rename(
            columns={
                "forecast_period": "Date",
                "predicted": "Forecast",
            }
        ),
    ],
    ignore_index=True,
).set_index("Date")


combined_index = (
    observed_series.index
    .union(
        forecast_chart_data.index
    )
    .sort_values()
)

chart_data = pd.DataFrame(
    index=combined_index
)

chart_data["Observed"] = (
    observed_series[
        "Observed"
    ]
)

chart_data["Forecast"] = (
    forecast_chart_data[
        "Forecast"
    ]
)

st.line_chart(
    chart_data,
    y=[
        "Observed",
        "Forecast",
    ],
    use_container_width=True,
)

st.caption(
    "Observed values end at the forecast origin. "
    "The forecast line begins at the final observed value and "
    f"extends from {forecast_start.strftime('%b %Y')} to "
    f"{forecast_end.strftime('%b %Y')}."
)


# ---------------------------------------------------------------------------
# Forecast table
# ---------------------------------------------------------------------------

st.subheader("Forecast Values")

display_forecast = series_forecast[
    [
        "forecast_period",
        "horizon_step",
        "predicted",
    ]
].copy()

display_forecast["forecast_period"] = (
    display_forecast[
        "forecast_period"
    ].dt.strftime(
        "%b %Y"
    )
)

if selected_metric == "median_rent":
    display_forecast[
        "predicted"
    ] = display_forecast[
        "predicted"
    ].map(
        lambda value: (
            f"${value:,.0f}"
        )
    )
else:
    display_forecast[
        "predicted"
    ] = display_forecast[
        "predicted"
    ].map(
        lambda value: (
            f"{value:,.0f}"
        )
    )

display_forecast = (
    display_forecast.rename(
        columns={
            "forecast_period": (
                "Forecast Month"
            ),
            "horizon_step": (
                "Horizon"
            ),
            "predicted": (
                "Predicted Value"
            ),
        }
    )
)

st.dataframe(
    display_forecast,
    use_container_width=True,
    hide_index=True,
)

download_data = series_forecast[
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
].to_csv(
    index=False
).encode(
    "utf-8"
)

st.download_button(
    label="Download Forecast CSV",
    data=download_data,
    file_name=(
        f"{series_id}_"
        "six_month_forecast.csv"
    ),
    mime="text/csv",
)


# ---------------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------------

st.subheader("Forecast Interpretation")

interpretation_1, interpretation_2 = st.columns(2)

with interpretation_1:
    st.markdown(
        "**Forecast window**  \n"
        f"{forecast_start.strftime('%b %Y')} – "
        f"{forecast_end.strftime('%b %Y')}"
    )

    st.markdown(
        "**First forecast**  \n"
        f"{format_value(first_forecast, selected_metric)}"
    )

with interpretation_2:
    st.markdown(
        "**Six-month forecast**  \n"
        f"{format_value(ending_forecast, selected_metric)}"
    )

    if pd.notna(
        forecast_change_pct
    ):
        st.markdown(
            "**Change from latest observed**  \n"
            f"{forecast_change:+,.1f} "
            f"({forecast_change_pct:+.1f}%)"
        )

st.info(
    "Forward forecasts are model-based estimates rather than "
    "observed rental-market values. They should be interpreted as "
    "analytical projections and not as guaranteed future outcomes "
    "or individual property valuations."
)


# ---------------------------------------------------------------------------
# Model evaluation
# ---------------------------------------------------------------------------

st.divider()

st.subheader("Model Evaluation")

st.caption(
    "The metrics below are calculated from rolling-origin "
    "out-of-sample evaluation. They are validation evidence and are "
    "separate from the six-month future forecast shown above."
)

evaluation_1, evaluation_2, evaluation_3 = st.columns(3)

evaluation_1.metric(
    "Backtest MAE",
    format_metric_value(
        float(
            winner["best_mae"]
        )
    ),
    help=(
        "Mean Absolute Error across the historical "
        "rolling-origin evaluation."
    ),
)

evaluation_2.metric(
    "Backtest RMSE",
    format_metric_value(
        float(
            winner["best_rmse"]
        )
    ),
    help=(
        "Root Mean Squared Error across the historical "
        "rolling-origin evaluation."
    ),
)

evaluation_3.metric(
    "Backtest sMAPE",
    format_smape(
        float(
            winner["best_smape"]
        )
    ),
    help=(
        "Symmetric Mean Absolute Percentage Error across "
        "the historical rolling-origin evaluation."
    ),
)


# ---------------------------------------------------------------------------
# Latest rolling-origin backtest
# ---------------------------------------------------------------------------

winner_backtest = backtest_predictions.loc[
    (
        backtest_predictions["series_id"]
        == series_id
    )
    & (
        backtest_predictions["model"]
        == winner_model
    )
].copy()

if not winner_backtest.empty:
    winner_backtest = winner_backtest.sort_values(
        [
            "origin",
            "horizon_step",
        ]
    )

    latest_origin = pd.Timestamp(
        winner_backtest[
            "origin"
        ].max()
    )

    latest_backtest = winner_backtest.loc[
        winner_backtest["origin"]
        == latest_origin
    ].copy()

    latest_backtest = latest_backtest.sort_values(
        "horizon_step"
    )

    with st.expander(
        "Latest Rolling-Origin Backtest",
        expanded=False,
    ):
        st.caption(
            "This section shows a historical test window where "
            "actual observations were withheld from model fitting "
            "and then compared with predictions."
        )

        st.markdown(
            "**Evaluation origin:** "
            f"{latest_origin.strftime('%b %Y')}"
        )

        backtest_chart = (
            latest_backtest[
                [
                    "forecast_period",
                    "actual",
                    "predicted",
                ]
            ]
            .rename(
                columns={
                    "forecast_period": "Date",
                    "actual": "Actual",
                    "predicted": "Predicted",
                }
            )
            .set_index("Date")
        )

        st.line_chart(
            backtest_chart,
            y=[
                "Actual",
                "Predicted",
            ],
            use_container_width=True,
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

        backtest_table[
            "forecast_period"
        ] = backtest_table[
            "forecast_period"
        ].dt.strftime(
            "%b %Y"
        )

        if selected_metric == "median_rent":
            for column in [
                "actual",
                "predicted",
                "absolute_error",
            ]:
                backtest_table[
                    column
                ] = backtest_table[
                    column
                ].map(
                    lambda value: (
                        f"${value:,.2f}"
                    )
                )
        else:
            for column in [
                "actual",
                "predicted",
                "absolute_error",
            ]:
                backtest_table[
                    column
                ] = backtest_table[
                    column
                ].map(
                    lambda value: (
                        f"{value:,.2f}"
                    )
                )

        backtest_table = (
            backtest_table.rename(
                columns={
                    "forecast_period": "Month",
                    "horizon_step": "Horizon",
                    "actual": "Actual",
                    "predicted": "Predicted",
                    "absolute_error": (
                        "Absolute Error"
                    ),
                }
            )
        )

        st.dataframe(
            backtest_table,
            use_container_width=True,
            hide_index=True,
        )


# ---------------------------------------------------------------------------
# Methodology note
# ---------------------------------------------------------------------------

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
  using lag, rolling, calendar and geography-aware location
  features.

Models are evaluated using rolling-origin validation with a
six-month forecast horizon. MAE, RMSE and sMAPE are used as
forecast-error measures.

A winner model is selected separately for each forecast-eligible
series. The winner is then refitted using all available historical
observations through the final forecast origin before generating
the six-month forward forecast.

The forward forecast therefore represents a genuine future
projection and is not the same dataset as the historical
rolling-origin backtest predictions.
"""
    )
