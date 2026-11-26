import math

from pricing import (
    black_scholes_call,
    black_scholes_put,
    validate_inputs
)


def numerical_greeks(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    option_type="call",
    dividend_yield=0.0,
    relative_step=0.001
):
    validate_inputs(
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility,
        dividend_yield
    )

    if option_type not in ("call", "put"):
        raise ValueError(
            "Option type must be 'call' or 'put'."
        )

    if not math.isfinite(relative_step) or not (
        0 < relative_step < 1
    ):
        raise ValueError(
            "Relative step must be between zero and one."
        )

    pricing_function = (
        black_scholes_call
        if option_type == "call"
        else black_scholes_put
    )

    stock_step = stock_price * relative_step

    time_step = (
        time_to_expiration * relative_step
    )

    volatility_step = volatility * relative_step

    rate_step = (
        max(abs(risk_free_rate), 0.01)
        * relative_step
    )

    def price(
        stock=stock_price,
        time=time_to_expiration,
        rate=risk_free_rate,
        sigma=volatility
    ):
        return pricing_function(
            stock,
            strike_price,
            time,
            rate,
            sigma,
            dividend_yield
        )

    center_price = price()

    stock_upper = price(
        stock=stock_price + stock_step
    )

    stock_lower = price(
        stock=stock_price - stock_step
    )

    delta = (
        stock_upper - stock_lower
    ) / (2 * stock_step)

    gamma = (
        stock_upper
        - 2 * center_price
        + stock_lower
    ) / stock_step ** 2

    time_upper = price(
        time=time_to_expiration + time_step
    )

    time_lower = price(
        time=time_to_expiration - time_step
    )

    theta = -(
        time_upper - time_lower
    ) / (2 * time_step * 365)

    volatility_upper = price(
        sigma=volatility + volatility_step
    )

    volatility_lower = price(
        sigma=volatility - volatility_step
    )

    vega = (
        volatility_upper - volatility_lower
    ) / (2 * volatility_step * 100)

    rate_upper = price(
        rate=risk_free_rate + rate_step
    )

    rate_lower = price(
        rate=risk_free_rate - rate_step
    )

    rho = (
        rate_upper - rate_lower
    ) / (2 * rate_step * 100)

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho
    }