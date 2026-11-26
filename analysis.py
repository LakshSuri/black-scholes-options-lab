import math

from pricing import calculate_d1, calculate_d2, normal_cdf


def normal_pdf(x):
    return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)


def calculate_greeks(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    option_type="call",
    dividend_yield=0.0
):
    if option_type not in ("call", "put"):
        raise ValueError("Option type must be 'call' or 'put'.")

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

    sqrt_time = math.sqrt(time_to_expiration)

    stock_discount = math.exp(
        -dividend_yield * time_to_expiration
    )

    strike_discount = math.exp(
        -risk_free_rate * time_to_expiration
    )

    discounted_stock = stock_price * stock_discount
    discounted_strike = strike_price * strike_discount

    pdf_d1 = normal_pdf(d1)

    gamma = (
        stock_discount * pdf_d1
        / (stock_price * volatility * sqrt_time)
    )

    vega = discounted_stock * pdf_d1 * sqrt_time / 100

    common_theta = (
        -discounted_stock * pdf_d1 * volatility
        / (2 * sqrt_time)
    )

    if option_type == "call":
        delta = stock_discount * normal_cdf(d1)

        theta = (
            common_theta
            - risk_free_rate
            * discounted_strike
            * normal_cdf(d2)
            + dividend_yield
            * discounted_stock
            * normal_cdf(d1)
        )

        rho = (
            discounted_strike
            * time_to_expiration
            * normal_cdf(d2)
        ) / 100

    else:
        delta = stock_discount * (normal_cdf(d1) - 1)

        theta = (
            common_theta
            + risk_free_rate
            * discounted_strike
            * normal_cdf(-d2)
            - dividend_yield
            * discounted_stock
            * normal_cdf(-d1)
        )

        rho = (
            -discounted_strike
            * time_to_expiration
            * normal_cdf(-d2)
        ) / 100

    theta = theta / 365

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho
    }