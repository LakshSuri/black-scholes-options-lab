import math
import pytest

from analysis import calculate_greeks
from numerical_greeks import numerical_greeks


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("stock,strike,time,rate,volatility,dividend", [
    (100, 100, 1, 0.05, 0.20, 0.00),
    (100, 90, 0.5, 0.03, 0.25, 0.02),
    (100, 110, 2, 0.04, 0.30, 0.03),
    (100, 100, 0.25, -0.01, 0.40, 0.01)
])
def test_numerical_accuracy(
    option_type, stock, strike, time,
    rate, volatility, dividend
):
    analytical = calculate_greeks(
        stock, strike, time, rate,
        volatility, option_type, dividend
    )

    numerical = numerical_greeks(
        stock, strike, time, rate,
        volatility, option_type, dividend
    )

    for greek in analytical:
        assert numerical[greek] == pytest.approx(
            analytical[greek],
            abs=3e-6,
            rel=2e-4
        )


@pytest.mark.parametrize("greek", ["delta", "gamma"])
def test_second_order_convergence(greek):
    analytical = calculate_greeks(
        100, 100, 1, 0.05, 0.20
    )[greek]

    errors = []

    for step in [0.04, 0.02, 0.01]:
        estimate = numerical_greeks(
            100, 100, 1, 0.05, 0.20,
            relative_step=step
        )[greek]

        errors.append(abs(estimate - analytical))

    assert errors[0] > errors[1] > errors[2]

    first_ratio = errors[0] / errors[1]
    second_ratio = errors[1] / errors[2]

    assert 3.5 < first_ratio < 4.5
    assert 3.5 < second_ratio < 4.5


def test_numerical_greek_parity():
    dividend = 0.03

    call = numerical_greeks(
        100, 100, 1, 0.05, 0.20,
        "call", dividend
    )

    put = numerical_greeks(
        100, 100, 1, 0.05, 0.20,
        "put", dividend
    )

    assert call["delta"] - put["delta"] == pytest.approx(
        math.exp(-dividend), abs=1e-8
    )

    assert call["gamma"] == pytest.approx(
        put["gamma"], abs=1e-8
    )

    assert call["vega"] == pytest.approx(
        put["vega"], abs=1e-8
    )


@pytest.mark.parametrize("step", [
    0,
    -0.01,
    1,
    2,
    float("nan"),
    float("inf")
])
def test_invalid_step_size(step):
    with pytest.raises(ValueError):
        numerical_greeks(
            100, 100, 1, 0.05, 0.20,
            relative_step=step
        )


def test_invalid_option_type():
    with pytest.raises(ValueError):
        numerical_greeks(
            100, 100, 1, 0.05, 0.20,
            option_type="invalid"
        )
