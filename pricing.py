"""Closed-form European option pricing with continuous dividend yield."""

import math


def _validate_contract(stock, strike, time, rate, dividend):
    if not all(map(math.isfinite, (stock, strike, time, rate, dividend))):
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


def _discounted_values(stock, strike, time, rate, dividend):
    def discount(amount, exponent):
        if -700 <= exponent <= 700:
            result = amount * math.exp(exponent)
        else:
            result = math.exp(math.log(amount) + exponent)
        if not math.isfinite(result) or result == 0:
            raise FloatingPointError("Discounted value is outside floating-point range.")
        return result

    return discount(stock, -dividend * time), discount(strike, -rate * time)


def _discounted_difference(spot_pv, strike_pv, moneyness):
    # expm1 preserves the difference for nearly equal discounted values.
    if moneyness >= 0:
        return -spot_pv * math.expm1(-moneyness)
    return strike_pv * math.expm1(moneyness)


def _price_from_width(spot_pv, strike_pv, moneyness, width, sign):
    difference = _discounted_difference(spot_pv, strike_pv, moneyness)
    intrinsic = max(sign * difference, 0.0)
    if width == 0:
        return intrinsic
    if math.isinf(width):
        return spot_pv if sign == 1 else strike_pv
    if moneyness == 0:
        return spot_pv * math.erf(width / (2 * math.sqrt(2)))

    d1 = moneyness / width + width / 2
    d2 = moneyness / width - width / 2
    # Evaluate the out-of-the-money leg directly, then apply put-call parity.
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
    spot_pv, strike_pv = _discounted_values(stock, strike, time, rate, dividend_yield)
    moneyness = _log_ratio(stock, strike) + (rate - dividend_yield) * time
    return _price_from_width(
        spot_pv, strike_pv, moneyness, volatility * math.sqrt(time), sign
    )


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
