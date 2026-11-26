import math

from pricing import (
    black_scholes_call,
    black_scholes_put,
    validate_inputs
)


def implied_volatility(
    market_price,
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    option_type="call",
    dividend_yield=0.0,
    tolerance=1e-10,
    max_iterations=200
):
    validate_inputs(
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        1.0,
        dividend_yield
    )

    if not math.isfinite(market_price) or market_price <= 0:
        raise ValueError("Market price must be positive and finite.")

    if option_type not in ("call", "put"):
        raise ValueError("Option type must be 'call' or 'put'.")

    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Tolerance must be positive and finite.")

    if not isinstance(max_iterations, int) or max_iterations <= 0:
        raise ValueError("Maximum iterations must be a positive integer.")

    discounted_stock = stock_price * math.exp(
        -dividend_yield * time_to_expiration
    )

    discounted_strike = strike_price * math.exp(
        -risk_free_rate * time_to_expiration
    )

    if option_type == "call":
        lower_price = max(
            0, discounted_stock - discounted_strike
        )
        upper_price = discounted_stock
        pricing_function = black_scholes_call

    else:
        lower_price = max(
            0, discounted_strike - discounted_stock
        )
        upper_price = discounted_strike
        pricing_function = black_scholes_put

    if not lower_price < market_price < upper_price:
        raise ValueError(
            "Market price violates strict option pricing bounds."
        )

    def model_price(volatility):
        return pricing_function(
            stock_price,
            strike_price,
            time_to_expiration,
            risk_free_rate,
            volatility,
            dividend_yield
        )

    low = 0.0
    high = 1.0
    maximum_volatility = 16.0

    while model_price(high) < market_price:
        if high >= maximum_volatility:
            raise ValueError(
                "Unable to bracket implied volatility."
            )

        high = min(high * 2, maximum_volatility)

    for iteration in range(max_iterations):
        midpoint = (low + high) / 2

        estimated_price = model_price(midpoint)

        if estimated_price == market_price:
            return midpoint

        if estimated_price < market_price:
            low = midpoint
        else:
            high = midpoint

        if high - low <= tolerance:
            return (low + high) / 2

    raise RuntimeError(
        "Implied volatility solver failed to converge."
    )
