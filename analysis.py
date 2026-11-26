"""Analytical Greeks and centered finite-difference estimates."""

import math

from pricing import (
    _discounted_values,
    _log_ratio,
    _option_sign,
    _validate_contract,
    black_scholes_merton,
    normal_cdf,
    validate_inputs,
)


def normal_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def calculate_greeks(
    stock_price, strike_price, time_to_expiration, risk_free_rate, volatility,
    option_type="call", *, dividend_yield=0.0
):
    """Return delta, gamma, daily theta, and vega/rho per percentage point."""
    stock, strike, time, rate = stock_price, strike_price, time_to_expiration, risk_free_rate
    validate_inputs(stock, strike, time, rate, volatility)
    _validate_contract(stock, strike, time, rate, dividend_yield)
    sign = _option_sign(option_type)
    root_time = math.sqrt(time)
    width = volatility * root_time
    moneyness = _log_ratio(stock, strike) + (rate - dividend_yield) * time
    d1 = moneyness / width + width / 2
    d2 = moneyness / width - width / 2
    spot_pv, strike_pv = _discounted_values(stock, strike, time, rate, dividend_yield)
    discount_yield = math.exp(-dividend_yield * time)
    density = normal_pdf(d1)
    stock_delta = sign * normal_cdf(sign * d1)
    strike_delta = sign * normal_cdf(sign * d2)
    theta = (
        -spot_pv * density * volatility / (2 * root_time)
        + dividend_yield * spot_pv * stock_delta
        - rate * strike_pv * strike_delta
    )
    return {
        "delta": discount_yield * stock_delta,
        "gamma": discount_yield * density / width / stock,
        "theta": theta / 365,
        "vega": spot_pv * density * root_time / 100,
        "rho": strike_pv * strike_delta * time / 100,
    }


def numerical_greeks(stock, strike, time, rate, volatility, option_type="call", *,
                     dividend_yield=0.0, relative_step=1e-3):
    """Estimate the same Greeks by centered bumps in spot, time, vol and rate."""
    validate_inputs(stock, strike, time, rate, volatility)
    if not 0 < relative_step < 1:
        raise ValueError("relative_step must be between zero and one.")

    def price(s=stock, t=time, r=rate, vol=volatility):
        return black_scholes_merton(
            s, strike, t, r, vol, option_type, dividend_yield=dividend_yield
        )

    ds, dt, dv = (value * relative_step for value in (stock, time, volatility))
    dr = max(abs(rate), 0.01) * relative_step
    for value, bump in ((stock, ds), (time, dt), (volatility, dv), (rate, dr)):
        if value + bump == value or value - bump == value:
            raise ValueError("Finite-difference bump is below floating-point resolution.")
    up, down, center = price(s=stock + ds), price(s=stock - ds), price()
    return {
        "delta": (up - down) / (2 * ds),
        "gamma": ((up - center) + (down - center)) / ds / ds,
        "theta": (price(t=time - dt) - price(t=time + dt)) / (2 * dt * 365),
        "vega": (price(vol=volatility + dv) - price(vol=volatility - dv)) / (200 * dv),
        "rho": (price(r=rate + dr) - price(r=rate - dr)) / (200 * dr),
    }
