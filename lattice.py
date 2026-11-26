"""Cox–Ross–Rubinstein lattice for European options."""

import math

import numpy as np

from pricing import (
    _discounted_values,
    _option_sign,
    _validate_contract,
    _validate_volatility,
    black_scholes_merton,
)


def crr_price(stock, strike, time, rate, volatility, option_type="call", *,
              dividend_yield=0.0, steps=256):
    """Price a European option with a recombining tree and linear storage."""
    _validate_contract(stock, strike, time, rate, dividend_yield)
    _validate_volatility(volatility)
    sign = _option_sign(option_type)
    if type(steps) is not int or steps < 1:
        raise ValueError("steps must be a positive integer.")
    if time == 0 or volatility == 0:
        return black_scholes_merton(
            stock, strike, time, rate, volatility, option_type,
            dividend_yield=dividend_yield,
        )

    dt = time / steps
    move = volatility * math.sqrt(dt)
    carry = (rate - dividend_yield) * dt
    if move == 0 or not abs(carry) < move:
        raise ValueError("CRR requires down < exp((r-q) dt) < up. Check the step size.")
    # Compute both weights without subtracting a probability close to one.
    denominator = -math.expm1(-2 * move)
    up = math.exp(carry - move) * -math.expm1(-carry - move) / denominator
    down = -math.expm1(carry - move) / denominator
    _, strike_pv = _discounted_values(stock, strike, time, rate, dividend_yield)
    nodes = np.arange(steps + 1, dtype=float)
    log_nodes = math.log(stock) - rate * time + (2 * nodes - steps) * move
    with np.errstate(over="raise", invalid="raise"):
        values = np.maximum(sign * (np.exp(log_nodes) - strike_pv), 0.0)
    # The entire lattice is expressed in present-value units.
    for _ in range(steps):
        values = down * values[:-1] + up * values[1:]
    return float(values[0])
