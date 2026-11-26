import math
import pytest

from pricing import black_scholes_call, black_scholes_put


def test_call_price():
    price = black_scholes_call(100, 100, 1, 0.05, 0.20)
    assert price == pytest.approx(10.45058357)


def test_put_price():
    price = black_scholes_put(100, 100, 1, 0.05, 0.20)
    assert price == pytest.approx(5.57352602)


@pytest.mark.parametrize("pricing_function", [
    black_scholes_call,
    black_scholes_put
])
@pytest.mark.parametrize("parameters", [
    (-100, 100, 1, 0.05, 0.20),
    (0, 100, 1, 0.05, 0.20),
    (100, -100, 1, 0.05, 0.20),
    (100, 0, 1, 0.05, 0.20),
    (100, 100, -1, 0.05, 0.20),
    (100, 100, 0, 0.05, 0.20),
    (100, 100, 1, 0.05, -0.20),
    (100, 100, 1, 0.05, 0),
])
def test_invalid_parameters(pricing_function, parameters):
    with pytest.raises(ValueError):
        pricing_function(*parameters)


@pytest.mark.parametrize("stock,strike,time,rate,volatility", [
    (80, 100, 1, 0.05, 0.20),
    (100, 100, 1, 0.05, 0.20),
    (120, 100, 1, 0.05, 0.20),
    (100, 110, 0.5, 0.03, 0.30),
    (150, 120, 2, 0.04, 0.40),
])
def test_put_call_parity(stock, strike, time, rate, volatility):
    call = black_scholes_call(stock, strike, time, rate, volatility)
    put = black_scholes_put(stock, strike, time, rate, volatility)

    expected = stock - strike * math.exp(-rate * time)

    assert call - put == pytest.approx(expected, abs=1e-10)


def test_call_stock_sensitivity():
    low = black_scholes_call(90, 100, 1, 0.05, 0.20)
    high = black_scholes_call(110, 100, 1, 0.05, 0.20)

    assert high > low


def test_put_stock_sensitivity():
    low = black_scholes_put(90, 100, 1, 0.05, 0.20)
    high = black_scholes_put(110, 100, 1, 0.05, 0.20)

    assert high < low


def test_call_strike_sensitivity():
    low = black_scholes_call(100, 90, 1, 0.05, 0.20)
    high = black_scholes_call(100, 110, 1, 0.05, 0.20)

    assert high < low


def test_put_strike_sensitivity():
    low = black_scholes_put(100, 90, 1, 0.05, 0.20)
    high = black_scholes_put(100, 110, 1, 0.05, 0.20)

    assert high > low


@pytest.mark.parametrize("pricing_function", [
    black_scholes_call,
    black_scholes_put
])
def test_volatility_sensitivity(pricing_function):
    low = pricing_function(100, 100, 1, 0.05, 0.10)
    high = pricing_function(100, 100, 1, 0.05, 0.40)

    assert high > low


@pytest.mark.parametrize("stock", [50, 80, 100, 120, 150])
def test_pricing_bounds(stock):
    strike = 100
    time = 1
    rate = 0.05
    volatility = 0.20

    call = black_scholes_call(stock, strike, time, rate, volatility)
    put = black_scholes_put(stock, strike, time, rate, volatility)

    discounted_strike = strike * math.exp(-rate * time)

    assert max(0, stock - discounted_strike) <= call <= stock
    assert max(0, discounted_strike - stock) <= put <= discounted_strike
