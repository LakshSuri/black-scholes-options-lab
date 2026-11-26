import math
import pytest

from analysis import calculate_greeks
from pricing import black_scholes_call, black_scholes_put


@pytest.mark.parametrize("option_type,expected", [
    ("call", {
        "delta": 0.63683065,
        "gamma": 0.01876202,
        "theta": -0.01757268,
        "vega": 0.37524035,
        "rho": 0.53232482
    }),
    ("put", {
        "delta": -0.36316935,
        "gamma": 0.01876202,
        "theta": -0.00454214,
        "vega": 0.37524035,
        "rho": -0.41890461
    })
])
def test_reference_greeks(option_type, expected):
    actual = calculate_greeks(
        100, 100, 1, 0.05, 0.20, option_type
    )

    for greek in expected:
        assert actual[greek] == pytest.approx(
            expected[greek], abs=1e-7
        )


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("greek", [
    "delta", "gamma", "theta", "vega", "rho"
])
def test_numerical_greeks(option_type, greek):
    stock = 100
    strike = 100
    time = 1
    rate = 0.05
    volatility = 0.20
    h = 0.001

    price = (
        black_scholes_call if option_type == "call"
        else black_scholes_put
    )

    actual = calculate_greeks(
        stock, strike, time, rate, volatility, option_type
    )

    if greek == "delta":
        upper = price(stock + h, strike, time, rate, volatility)
        lower = price(stock - h, strike, time, rate, volatility)

        numerical = (upper - lower) / (2 * h)

    elif greek == "gamma":
        upper = price(stock + h, strike, time, rate, volatility)
        center = price(stock, strike, time, rate, volatility)
        lower = price(stock - h, strike, time, rate, volatility)

        numerical = (upper - 2 * center + lower) / h ** 2

    elif greek == "theta":
        upper = price(stock, strike, time + h, rate, volatility)
        lower = price(stock, strike, time - h, rate, volatility)

        numerical = -(upper - lower) / (2 * h * 365)

    elif greek == "vega":
        upper = price(stock, strike, time, rate, volatility + h)
        lower = price(stock, strike, time, rate, volatility - h)

        numerical = (upper - lower) / (2 * h * 100)

    else:
        upper = price(stock, strike, time, rate + h, volatility)
        lower = price(stock, strike, time, rate - h, volatility)

        numerical = (upper - lower) / (2 * h * 100)

    assert actual[greek] == pytest.approx(
        numerical, abs=1e-5
    )


def test_greek_parity():
    call = calculate_greeks(100, 100, 1, 0.05, 0.20, "call")
    put = calculate_greeks(100, 100, 1, 0.05, 0.20, "put")

    assert call["delta"] - put["delta"] == pytest.approx(1)
    assert call["gamma"] == pytest.approx(put["gamma"])
    assert call["vega"] == pytest.approx(put["vega"])

    assert call["rho"] - put["rho"] == pytest.approx(
        math.exp(-0.05)
    )
