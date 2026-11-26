import math

import pytest

from pricing import black_scholes_call, black_scholes_put

BASE = (100, 100, 1, 0.05, 0.20)


def test_reference_call():
    assert black_scholes_call(*BASE) == pytest.approx(10.4505835722)


def test_reference_put():
    assert black_scholes_put(*BASE) == pytest.approx(5.5735260223)


@pytest.mark.parametrize("stock", [60, 100, 140])
@pytest.mark.parametrize("rate", [-0.02, 0.0, 0.05])
def test_parity_and_bounds(stock, rate):
    strike, time, vol = 100, 1.2, 0.25
    call = black_scholes_call(stock, strike, time, rate, vol)
    put = black_scholes_put(stock, strike, time, rate, vol)
    discounted = strike * math.exp(-rate * time)
    assert call - put == pytest.approx(stock - discounted, abs=1e-10)
    assert max(0, stock - discounted) - 1e-10 <= call <= stock + 1e-10
    assert max(0, discounted - stock) - 1e-10 <= put <= discounted + 1e-10


@pytest.mark.parametrize("price", [black_scholes_call, black_scholes_put])
def test_volatility_monotonicity(price):
    assert price(100, 100, 1, 0.05, 0.15) < price(*BASE)


def test_stock_monotonicity():
    assert black_scholes_call(90, *BASE[1:]) < black_scholes_call(*BASE)
    assert black_scholes_put(90, *BASE[1:]) > black_scholes_put(*BASE)


@pytest.mark.parametrize("index", [0, 1, 2, 4])
@pytest.mark.parametrize("bad", [0, -1])
def test_positive_inputs(index, bad):
    args = list(BASE)
    args[index] = bad
    for price in (black_scholes_call, black_scholes_put):
        with pytest.raises(ValueError):
            price(*args)


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_finite_inputs(index, bad):
    args = list(BASE)
    args[index] = bad
    for price in (black_scholes_call, black_scholes_put):
        with pytest.raises(ValueError):
            price(*args)
