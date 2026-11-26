import pytest

from lattice import crr_price
from pricing import black_scholes_call, black_scholes_put


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("stock,strike,time,rate,volatility,dividend", [
    (100, 100, 1, 0.05, 0.20, 0.00),
    (100, 90, 0.5, 0.03, 0.25, 0.02),
    (100, 110, 2, 0.04, 0.30, 0.03)
])
def test_european_convergence(
    option_type, stock, strike, time,
    rate, volatility, dividend
):
    pricing_function = (
        black_scholes_call if option_type == "call"
        else black_scholes_put
    )

    reference = pricing_function(
        stock, strike, time, rate, volatility, dividend
    )

    estimate = crr_price(
        stock, strike, time, rate, volatility,
        steps=2000,
        option_type=option_type,
        dividend_yield=dividend
    )

    assert estimate == pytest.approx(
        reference, abs=0.03, rel=0
    )


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("stock", [80, 100, 120])
def test_american_option_dominance(option_type, stock):
    european = crr_price(
        stock, 100, 1, 0.05, 0.20,
        steps=500,
        option_type=option_type,
        exercise_style="european"
    )

    american = crr_price(
        stock, 100, 1, 0.05, 0.20,
        steps=500,
        option_type=option_type,
        exercise_style="american"
    )

    assert american >= european - 1e-10


def test_american_call_without_dividends():
    european = crr_price(
        100, 100, 1, 0.05, 0.20,
        steps=1000,
        option_type="call"
    )

    american = crr_price(
        100, 100, 1, 0.05, 0.20,
        steps=1000,
        option_type="call",
        exercise_style="american"
    )

    assert american == pytest.approx(
        european, abs=1e-8, rel=0
    )


def test_american_put_early_exercise():
    european = crr_price(
        100, 100, 1, 0.05, 0.20,
        option_type="put"
    )

    american = crr_price(
        100, 100, 1, 0.05, 0.20,
        option_type="put",
        exercise_style="american"
    )

    assert american > european


@pytest.mark.parametrize("steps", [10, 50, 100, 500])
def test_american_intrinsic_value(steps):
    price = crr_price(
        70, 100, 1, 0.05, 0.20,
        steps=steps,
        option_type="put",
        exercise_style="american"
    )

    assert price >= 30 - 1e-10


@pytest.mark.parametrize("parameters", [
    {"steps": 0},
    {"steps": -10},
    {"steps": 10.5},
    {"steps": True},
    {"option_type": "invalid"},
    {"exercise_style": "invalid"},
    {"dividend_yield": -0.02}
])
def test_invalid_lattice_parameters(parameters):
    with pytest.raises(ValueError):
        crr_price(
            100, 100, 1, 0.05, 0.20,
            **parameters
        )


def test_invalid_risk_neutral_probability():
    with pytest.raises(ValueError):
        crr_price(
            100, 100, 1, 0.50, 0.01,
            steps=1
        )
