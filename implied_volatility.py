"""Bracketed inversion of European Black–Scholes–Merton prices."""

import math

from pricing import (
    _discounted_difference,
    _discounted_values,
    _log_ratio,
    _option_sign,
    _price_from_width,
    _validate_contract,
)


def implied_volatility(price, stock, strike, time, rate, option_type="call", *,
                       dividend_yield=0.0):
    """Return annualized implied volatility for a price inside model bounds.

    The lower bound maps to zero. Expiry and the upper bound have no unique
    finite solution. Solve for total volatility before annualizing.
    """
    _validate_contract(stock, strike, time, rate, dividend_yield)
    sign = _option_sign(option_type)
    if time == 0 or not math.isfinite(price):
        raise ValueError("Implied volatility requires positive time and a finite price.")
    spot_pv, strike_pv = _discounted_values(stock, strike, time, rate, dividend_yield)
    moneyness = _log_ratio(stock, strike) + (rate - dividend_yield) * time
    intrinsic = max(sign * _discounted_difference(spot_pv, strike_pv, moneyness), 0.0)
    upper = spot_pv if sign == 1 else strike_pv
    if not intrinsic <= price < upper:
        raise ValueError("Price lies outside finite-volatility bounds.")
    if price == intrinsic:
        return 0.0

    # Invert the time value to avoid repeated addition of intrinsic value.
    target = price - intrinsic
    otm_sign = 1 if moneyness <= 0 else -1
    otm_upper = spot_pv if otm_sign == 1 else strike_pv
    if target >= otm_upper:
        raise ValueError("Price is indistinguishable from its upper bound after rounding.")
    low, high = 0.0, 1.0
    while _price_from_width(spot_pv, strike_pv, moneyness, high, otm_sign) < target:
        high *= 2

    # Halve the bracket until its width is small relative to total volatility.
    while high - low > 1e-12 * high:
        mid = low + (high - low) / 2
        if mid == low or mid == high:
            break
        estimate = _price_from_width(spot_pv, strike_pv, moneyness, mid, otm_sign)
        if estimate < target:
            low = mid
        else:
            high = mid
    return (low + (high - low) / 2) / math.sqrt(time)
