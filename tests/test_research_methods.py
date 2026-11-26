import math

import pytest

from analysis import calculate_greeks, numerical_greeks
from implied_volatility import implied_volatility
from lattice import crr_price
from monte_carlo import monte_carlo_price
from pricing import black_scholes_merton, normal_cdf


ARGS = (100, 105, 1, 0.04, 0.24)
Q = 0.02


def test_known_forward_at_the_money_price_and_small_width():
    price = black_scholes_merton(100, 100, 1, 0.03, 0.2, dividend_yield=0.03)
    assert price == pytest.approx(7.730149359277918, abs=1e-12)
    tiny = black_scholes_merton(100, 100, 1, 0, 1e-16)
    assert tiny == pytest.approx(100e-16 / math.sqrt(2 * math.pi), rel=1e-14, abs=0)
    assert normal_cdf(-12) == pytest.approx(1.776482112077679e-33, rel=1e-13, abs=0)
    assert black_scholes_merton(100, 160, 1, 0, 0.05) > 0


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("volatility", [0.015, 0.24, 1.1, 6.0])
def test_implied_volatility_round_trip(option_type, volatility):
    args = ARGS[:4]
    price = black_scholes_merton(*args, volatility, option_type, dividend_yield=Q)
    assert implied_volatility(price, *args, option_type, dividend_yield=Q) == pytest.approx(
        volatility, rel=1e-8
    )


@pytest.mark.parametrize("kind,stock", [("call", 105), ("put", 75)])
@pytest.mark.parametrize("rate", [0.0, 0.03, -0.02])
def test_implied_volatility_at_discounted_intrinsic_value(kind, stock, rate):
    strike, years = 100, 1.0
    args = (stock, strike, years, rate)
    lower = abs(stock - strike) * math.exp(-rate * years)
    assert black_scholes_merton(*args, 0, kind, dividend_yield=rate) == lower
    assert implied_volatility(lower, *args, kind, dividend_yield=rate) == 0

    below = math.nextafter(lower, -math.inf)
    with pytest.raises(ValueError, match="bounds"):
        implied_volatility(below, *args, kind, dividend_yield=rate)

    above = math.nextafter(lower, math.inf)
    vol = implied_volatility(above, *args, kind, dividend_yield=rate)
    assert vol > 0
    assert black_scholes_merton(*args, vol, kind, dividend_yield=rate) == above


def test_implied_volatility_bounds_and_near_expiry():
    assert implied_volatility(0, 100, 110, 1, 0) == 0
    assert implied_volatility(10, 110, 100, 1, 0) == pytest.approx(0, abs=1e-14)
    for invalid in (-1, 100, 101, math.nan):
        with pytest.raises(ValueError):
            implied_volatility(invalid, 100, 110, 1, 0)
    with pytest.raises(ValueError):
        implied_volatility(0, 100, 110, 0, 0)
    price = black_scholes_merton(100, 100, 1e-14, 0, 0.2)
    assert implied_volatility(price, 100, 100, 1e-14, 0) == pytest.approx(0.2, rel=1e-10)


@pytest.mark.parametrize("pricer", [black_scholes_merton, crr_price, monte_carlo_price])
@pytest.mark.parametrize("time,vol", [(0, 0.24), (1, 0)])
def test_deterministic_limits(pricer, time, vol):
    result = pricer(100, 105, time, -0.01, vol, "put", dividend_yield=Q)
    expected = 105 * math.exp(0.01 * time) - 100 * math.exp(-Q * time)
    if pricer is monte_carlo_price:
        assert result.standard_error == 0
        assert result.confidence_interval == (result.price, result.price)
        result = result.price
    assert result == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("rate", [0.04, -0.03])
@pytest.mark.parametrize("pricer,kwargs", [
    (black_scholes_merton, {}),
    (crr_price, {"steps": 1024}),
])
def test_dividend_parity_and_convergence(pricer, kwargs, rate):
    args = (100, 105, 1, rate, 0.24)
    call = pricer(*args, dividend_yield=Q, **kwargs)
    put = pricer(*args, "put", dividend_yield=Q, **kwargs)
    assert call - put == pytest.approx(100 * math.exp(-Q) - 105 * math.exp(-rate), abs=1e-10)
    assert call == pytest.approx(black_scholes_merton(*args, dividend_yield=Q), abs=0.004)


def test_crr_single_step_and_invalid_probability():
    up = math.exp(0.2)
    down = 1 / up
    prob = (math.exp(0.03 - Q) - down) / (up - down)
    assert crr_price(100, 100, 1, 0.03, 0.2, steps=1, dividend_yield=Q) == pytest.approx(
        math.exp(-0.03) * prob * (100 * up - 100)
    )
    with pytest.raises(ValueError, match="CRR requires"):
        crr_price(100, 100, 1, 0.2, 0.01, steps=1)
    with pytest.raises(ValueError, match="steps"):
        crr_price(*ARGS, steps=True)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_monte_carlo_accuracy_and_sampling_accounting(option_type):
    kwargs = dict(dividend_yield=Q, seed=42, paths=20_000)
    plain = monte_carlo_price(*ARGS, option_type, **kwargs)
    antithetic = monte_carlo_price(*ARGS, option_type, **kwargs, antithetic=True)
    reduced = monte_carlo_price(
        *ARGS, option_type, **kwargs, antithetic=True, control_variate=True
    )
    exact = black_scholes_merton(*ARGS, option_type, dividend_yield=Q)
    assert reduced == monte_carlo_price(
        *ARGS, option_type, **kwargs, antithetic=True, control_variate=True
    )
    assert reduced.independent_samples == 10_000
    assert reduced.paths == 20_000
    assert reduced.pilot_paths == 2048
    assert abs(reduced.price - exact) <= 4 * reduced.standard_error
    assert reduced.standard_error < antithetic.standard_error < plain.standard_error
    assert reduced.confidence_interval[1] - reduced.price == pytest.approx(
        1.959963984540054 * reduced.standard_error
    )


def test_monte_carlo_validates_pair_counts():
    with pytest.raises(ValueError, match="paths"):
        monte_carlo_price(*ARGS, paths=7, antithetic=True)
    with pytest.raises(ValueError, match="pilot_paths"):
        monte_carlo_price(*ARGS, control_variate=True, pilot_paths=1)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_all_dividend_greeks_match_centered_differences(option_type):
    expected = calculate_greeks(*ARGS, option_type, dividend_yield=Q)
    observed = numerical_greeks(*ARGS, option_type, dividend_yield=Q, relative_step=1e-4)
    assert observed == pytest.approx(expected, rel=1e-6)
    with pytest.raises(ValueError, match="relative_step"):
        numerical_greeks(*ARGS, relative_step=1)


@pytest.mark.parametrize("pricer", [black_scholes_merton, crr_price, monte_carlo_price])
def test_pricers_reject_invalid_contracts(pricer):
    with pytest.raises(ValueError):
        pricer(*ARGS, dividend_yield=math.nan)
    with pytest.raises(ValueError):
        pricer(*ARGS, "straddle")
    with pytest.raises(ValueError):
        pricer(*ARGS[:4], -1)
