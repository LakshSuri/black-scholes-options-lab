"""Closed-form European option pricing with continuous dividend yield."""

import math


def _validate_contract(stock, strike, time, rate, dividend):
    for value in (stock, strike, time, rate, dividend):
        if not math.isfinite(value):
            raise ValueError("Contract parameters must be finite.")
    if stock <= 0 or strike <= 0 or time < 0:
        raise ValueError("Spot and strike must be positive and time nonnegative.")


def _validate_volatility(volatility):
    if not math.isfinite(volatility) or volatility < 0:
        raise ValueError("Volatility must be finite and nonnegative.")


def _option_sign(option_type):
    if option_type not in ("call", "put"):
        raise ValueError("Option type must be 'call' or 'put'.")
    return 1 if option_type == "call" else -1


def validate_inputs(
    stock_price, strike_price, time_to_expiration, risk_free_rate, volatility
):
    """Validate the original Black–Scholes API's strictly positive domain."""
    _validate_contract(stock_price, strike_price, time_to_expiration, risk_free_rate, 0)
    _validate_volatility(volatility)
    if time_to_expiration == 0 or volatility == 0:
        raise ValueError("Time to expiration and volatility must be positive.")


def normal_cdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _log_ratio(stock, strike):
    if 0.5 * strike <= stock <= 2 * strike:
        return math.log1p((stock - strike) / strike)
    return math.log(stock) - math.log(strike)


def calculate_d1(
    stock_price, strike_price, time_to_expiration, risk_free_rate, volatility
):
    validate_inputs(
        stock_price, strike_price, time_to_expiration, risk_free_rate, volatility
    )
    width = volatility * math.sqrt(time_to_expiration)
    moneyness = _log_ratio(stock_price, strike_price) + risk_free_rate * time_to_expiration
    return moneyness / width + width / 2


def calculate_d2(d1, volatility, time_to_expiration):
    return d1 - volatility * math.sqrt(time_to_expiration)


def _discount(amount, exponent):
    if amount == 0:
        return 0.0
    if -700 <= exponent <= 700:
        return amount * math.exp(exponent)
    return math.exp(math.log(amount) + exponent)


def _discounted_values(stock, strike, time, rate, dividend):
    spot_pv = _discount(stock, -dividend * time)
    strike_pv = _discount(strike, -rate * time)
    for value in (spot_pv, strike_pv):
        if not math.isfinite(value) or value == 0:
            raise FloatingPointError("Discounted value is outside floating-point range.")
    return spot_pv, strike_pv


def _pricing_terms(stock, strike, time, rate, dividend, sign):
    spot_pv, strike_pv = _discounted_values(stock, strike, time, rate, dividend)
    moneyness = _log_ratio(stock, strike) + (rate - dividend) * time
    if rate == dividend:
        # A common discount factor applies to the payoff itself.
        payoff = max(sign * (stock - strike), 0.0)
        intrinsic = _discount(payoff, -rate * time)
    else:
        # expm1 retains small differences when the discounted values nearly match.
        if moneyness >= 0:
            difference = -spot_pv * math.expm1(-moneyness)
        else:
            difference = strike_pv * math.expm1(moneyness)
        intrinsic = max(sign * difference, 0.0)
    return spot_pv, strike_pv, moneyness, intrinsic


def _price_from_width(spot_pv, strike_pv, moneyness, width, sign, intrinsic):
    if width == 0:
        return intrinsic
    if math.isinf(width):
        return spot_pv if sign == 1 else strike_pv
    if moneyness == 0:
        return spot_pv * math.erf(width / (2 * math.sqrt(2)))

    d1 = moneyness / width + width / 2
    d2 = moneyness / width - width / 2
    # The smaller premium retains its time value when intrinsic value is large.
    if moneyness < 0:
        time_value = spot_pv * normal_cdf(d1) - strike_pv * normal_cdf(d2)
    else:
        time_value = strike_pv * normal_cdf(-d2) - spot_pv * normal_cdf(-d1)
    upper = spot_pv if sign == 1 else strike_pv
    return min(upper, intrinsic + max(time_value, 0.0))


def black_scholes_merton(
    stock, strike, time, rate, volatility, option_type="call", *, dividend_yield=0.0
):
    """Price a European call or put, including expiry and zero-volatility limits."""
    _validate_contract(stock, strike, time, rate, dividend_yield)
    _validate_volatility(volatility)
    sign = _option_sign(option_type)
    if time == 0:
        return max(sign * (stock - strike), 0.0)
    spot_pv, strike_pv, moneyness, intrinsic = _pricing_terms(
        stock, strike, time, rate, dividend_yield, sign
    )
    width = volatility * math.sqrt(time)
    return _price_from_width(spot_pv, strike_pv, moneyness, width, sign, intrinsic)


def black_scholes_call(
    stock_price, strike_price, time_to_expiration, risk_free_rate, volatility
):
    """Price a European call with zero dividends using the original API."""
    args = stock_price, strike_price, time_to_expiration, risk_free_rate, volatility
    validate_inputs(*args)
    return black_scholes_merton(*args)


def black_scholes_put(
    stock_price, strike_price, time_to_expiration, risk_free_rate, volatility
):
    """Price a European put with zero dividends using the original API."""
    args = stock_price, strike_price, time_to_expiration, risk_free_rate, volatility
    validate_inputs(*args)
    return black_scholes_merton(*args, "put")
