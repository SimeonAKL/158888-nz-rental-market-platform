"""Tests for the seasonal naive forecasting baseline."""

import pandas as pd
import pytest

from rmp.forecasting.seasonal_naive import (
    seasonal_naive_forecast,
)


def make_train_test() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """Create deterministic monthly train and test data."""

    train_dates = pd.date_range(
        "2019-01-01",
        periods=12,
        freq="MS",
    )

    test_dates = pd.date_range(
        "2020-01-01",
        periods=6,
        freq="MS",
    )

    train = pd.DataFrame(
        {
            "period_date": train_dates,
            "value": list(
                range(1, 13)
            ),
        }
    )

    test = pd.DataFrame(
        {
            "period_date": test_dates,
            "value": [
                101,
                102,
                103,
                104,
                105,
                106,
            ],
        }
    )

    return train, test


def test_seasonal_naive_uses_previous_year() -> None:
    """Forecast should use the same month one year earlier."""

    train, test = make_train_test()

    result = seasonal_naive_forecast(
        train,
        test,
        seasonal_period=12,
    )

    assert result[
        "predicted"
    ].tolist() == [
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        6.0,
    ]


def test_horizon_steps_are_sequential() -> None:
    """Forecast horizon should be numbered from one."""

    train, test = make_train_test()

    result = seasonal_naive_forecast(
        train,
        test,
    )

    assert result[
        "horizon_step"
    ].tolist() == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_reference_period_is_twelve_months_back() -> None:
    """Each forecast should record its seasonal reference period."""

    train, test = make_train_test()

    result = seasonal_naive_forecast(
        train,
        test,
    )

    expected = pd.date_range(
        "2019-01-01",
        periods=6,
        freq="MS",
    )

    assert pd.DatetimeIndex(
        result["reference_period"]
    ).equals(expected)


def test_future_actuals_do_not_change_forecast() -> None:
    """Changing future actuals must not change predictions."""

    train, test = make_train_test()

    first = seasonal_naive_forecast(
        train,
        test,
    )

    changed_test = test.copy()

    changed_test["value"] = [
        9999,
        8888,
        7777,
        6666,
        5555,
        4444,
    ]

    second = seasonal_naive_forecast(
        train,
        changed_test,
    )

    assert first[
        "predicted"
    ].tolist() == second[
        "predicted"
    ].tolist()


def test_error_is_actual_minus_predicted() -> None:
    """Forecast error should equal actual minus prediction."""

    train, test = make_train_test()

    result = seasonal_naive_forecast(
        train,
        test,
    )

    assert result.iloc[0][
        "error"
    ] == pytest.approx(
        100.0
    )

    assert result.iloc[0][
        "absolute_error"
    ] == pytest.approx(
        100.0
    )

    assert result.iloc[0][
        "squared_error"
    ] == pytest.approx(
        10000.0
    )


def test_missing_reference_period_is_rejected() -> None:
    """Forecasting should fail without required seasonal history."""

    train, test = make_train_test()

    train = train.loc[
        train["period_date"]
        != pd.Timestamp("2019-01-01")
    ].copy()

    with pytest.raises(
        ValueError,
        match="Seasonal reference period",
    ):
        seasonal_naive_forecast(
            train,
            test,
        )


def test_invalid_seasonal_period_is_rejected() -> None:
    """Seasonal period must be positive."""

    train, test = make_train_test()

    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        seasonal_naive_forecast(
            train,
            test,
            seasonal_period=0,
        )
