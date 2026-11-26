import math
import pytest

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks


@pytest.mark.parametrize("pricing_function,expected", [
    (black_scholes_call, 9.227005508154),
    (black_scholes_put, 6.330080627549)
])
def test_dividend_reference_price(pricing_function, expected):
    price = pricing_function(100, 100, 1, 0.05, 0.20, 0.02)

    assert price == pytest.approx(expected)


@pytest.mark.parametrize("dividend", [0.01, 0.03, 0.05])
def test_dividend_put_call_parity(dividend):
    stock = 100
    strike = 105
    time = 1.5
    rate = 0.04
    volatility = 0.25

    call = black_scholes_call(
        stock, strike, time, rate, volatility, dividend
    )

    put = black_scholes_put(
        stock, strike, time, rate, volatility, dividend
    )

    expected = (
        stock * math.exp(-dividend * time)
        - strike * math.exp(-rate * time)
    )

    assert call - put == pytest.approx(expected, abs=1e-10)


def test_call_dividend_sensitivity():
    low = black_scholes_call(100, 100, 1, 0.05, 0.20, 0.01)
    high = black_scholes_call(100, 100, 1, 0.05, 0.20, 0.05)

    assert high < low


def test_put_dividend_sensitivity():
    low = black_scholes_put(100, 100, 1, 0.05, 0.20, 0.01)
    high = black_scholes_put(100, 100, 1, 0.05, 0.20, 0.05)

    assert high > low


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_dividend_numerical_greeks(option_type):
    stock = 100
    strike = 105
    time = 1.5
    rate = 0.04
    volatility = 0.25
    dividend = 0.03

    h = 0.0001
    stock_step = 0.01

    price = (
        black_scholes_call if option_type == "call"
        else black_scholes_put
    )

    def value(s=stock, t=time, r=rate, v=volatility):
        return price(s, strike, t, r, v, dividend)

    center = value()
    upper = value(s=stock + stock_step)
    lower = value(s=stock - stock_step)

    numerical = {
        "delta": (upper - lower) / (2 * stock_step),

        "gamma": (
            upper - 2 * center + lower
        ) / stock_step ** 2,

        "theta": -(
            value(t=time + h) - value(t=time - h)
        ) / (2 * h * 365),

        "vega": (
            value(v=volatility + h) - value(v=volatility - h)
        ) / (2 * h * 100),

        "rho": (
            value(r=rate + h) - value(r=rate - h)
        ) / (2 * h * 100)
    }

    analytical = calculate_greeks(
        stock, strike, time, rate,
        volatility, option_type, dividend
    )

    for greek in numerical:
        assert analytical[greek] == pytest.approx(
            numerical[greek], abs=1e-5
        )


@pytest.mark.parametrize("pricing_function", [
    black_scholes_call,
    black_scholes_put
])
@pytest.mark.parametrize("dividend", [
    -0.02,
    float("nan"),
    float("inf")
])
def test_invalid_dividend(pricing_function, dividend):
    with pytest.raises(ValueError):
        pricing_function(100, 100, 1, 0.05, 0.20, dividend)


@pytest.mark.parametrize("dividend", [
    -0.02,
    float("nan"),
    float("inf")
])
def test_invalid_dividend_greeks(dividend):
    with pytest.raises(ValueError):
        calculate_greeks(
            100, 100, 1, 0.05, 0.20, "call", dividend
        )
