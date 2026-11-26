import math


def validate_inputs(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    dividend_yield=0.0
):
    parameters = {
        "Stock price": stock_price,
        "Strike price": strike_price,
        "Time to expiration": time_to_expiration,
        "Risk-free rate": risk_free_rate,
        "Volatility": volatility,
        "Dividend yield": dividend_yield
    }

    for name, value in parameters.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number.")

    if stock_price <= 0:
        raise ValueError("Stock price must be positive.")

    if strike_price <= 0:
        raise ValueError("Strike price must be positive.")

    if time_to_expiration <= 0:
        raise ValueError("Time to expiration must be positive.")

    if volatility <= 0:
        raise ValueError("Volatility must be positive.")

    if dividend_yield < 0:
        raise ValueError("Dividend yield cannot be negative.")


def normal_cdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def calculate_d1(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    dividend_yield=0.0
):
    validate_inputs(
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility,
        dividend_yield
    )

    numerator = (
        math.log(stock_price)
        - math.log(strike_price)
        + (
            risk_free_rate
            - dividend_yield
            + volatility ** 2 / 2
        ) * time_to_expiration
    )

    denominator = volatility * math.sqrt(time_to_expiration)

    return numerator / denominator


def calculate_d2(d1, volatility, time_to_expiration):
    return d1 - volatility * math.sqrt(time_to_expiration)


def black_scholes_call(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    dividend_yield=0.0
):
    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility,
        dividend_yield
    )

    d2 = calculate_d2(
        d1,
        volatility,
        time_to_expiration
    )

    discounted_stock = stock_price * math.exp(
        -dividend_yield * time_to_expiration
    )

    discounted_strike = strike_price * math.exp(
        -risk_free_rate * time_to_expiration
    )

    call_price = (
        discounted_stock * normal_cdf(d1)
        - discounted_strike * normal_cdf(d2)
    )

    return call_price


def black_scholes_put(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    dividend_yield=0.0
):
    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility,
        dividend_yield
    )

    d2 = calculate_d2(
        d1,
        volatility,
        time_to_expiration
    )

    discounted_stock = stock_price * math.exp(
        -dividend_yield * time_to_expiration
    )

    discounted_strike = strike_price * math.exp(
        -risk_free_rate * time_to_expiration
    )

    put_price = (
        discounted_strike * normal_cdf(-d2)
        - discounted_stock * normal_cdf(-d1)
    )

    return put_price
