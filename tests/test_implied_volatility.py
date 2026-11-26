import math
import pytest

from pricing import black_scholes_call, black_scholes_put
from implied_volatility import implied_volatility


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("volatility", [0.15, 0.35, 1.40])
@pytest.mark.parametrize("stock,strike,time,rate,dividend", [
    (100, 100, 1, 0.05, 0.00),
    (100, 85, 0.5, 0.03, 0.02),
    (100, 115, 2, 0.04, 0.03)
])
def test_volatility_recovery(
    option_type, volatility, stock, strike,
    time, rate, dividend
):
    pricing_function = (
        black_scholes_call if option_type == "call"
        else black_scholes_put
    )

    market_price = pricing_function(
        stock, strike, time, rate, volatility, dividend
    )

    recovered = implied_volatility(
        market_price, stock, strike, time,
        rate, option_type, dividend
    )

    assert recovered == pytest.approx(
        volatility, abs=1e-8, rel=0
    )

    recovered_price = pricing_function(
        stock, strike, time, rate, recovered, dividend
    )

    assert recovered_price == pytest.approx(
        market_price, abs=1e-8, rel=0
    )


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("scenario", [
    "below_lower",
    "at_lower",
    "at_upper",
    "above_upper"
])
def test_invalid_pricing_bounds(option_type, scenario):
    stock = 100
    strike = 100
    time = 1
    rate = 0.05
    dividend = 0.02

    discounted_stock = stock * math.exp(-dividend * time)
    discounted_strike = strike * math.exp(-rate * time)

    if option_type == "call":
        lower = max(0, discounted_stock - discounted_strike)
        upper = discounted_stock
    else:
        lower = max(0, discounted_strike - discounted_stock)
        upper = discounted_strike

    prices = {
        "below_lower": lower - 1,
        "at_lower": lower,
        "at_upper": upper,
        "above_upper": upper + 1
    }

    with pytest.raises(ValueError):
        implied_volatility(
            prices[scenario],
            stock, strike, time,
            rate, option_type, dividend
        )


@pytest.mark.parametrize("parameters", [
    {"option_type": "invalid"},
    {"tolerance": 0},
    {"tolerance": float("nan")},
    {"max_iterations": 0},
    {"max_iterations": 1.5},
    {"dividend_yield": -0.02}
])
def test_invalid_solver_parameters(parameters):
    with pytest.raises(ValueError):
        implied_volatility(
            10.45, 100, 100, 1, 0.05, **parameters
        )


def test_nonconvergence():
    market_price = black_scholes_call(
        100, 100, 1, 0.05, 0.23
    )

    with pytest.raises(RuntimeError):
        implied_volatility(
            market_price,
            100, 100, 1, 0.05,
            max_iterations=1
        )