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
    option_type="call"
):
    if stock_price <= 0 or strike_price <= 0:
        raise ValueError("Stock and strike prices must be positive.")

    if time_to_expiration <= 0:
        raise ValueError("Time to expiration must be positive.")

    if volatility <= 0:
        raise ValueError("Volatility must be positive.")

    if option_type not in ("call", "put"):
        raise ValueError("Option type must be 'call' or 'put'.")

    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility
    )

    d2 = calculate_d2(
        d1,
        volatility,
        time_to_expiration
    )

    discount_factor = math.exp(
        -risk_free_rate * time_to_expiration
    )

    pdf_d1 = normal_pdf(d1)

    gamma = pdf_d1 / (
        stock_price * volatility * math.sqrt(time_to_expiration)
    )

    vega = (
        stock_price * pdf_d1 * math.sqrt(time_to_expiration)
    ) / 100

    if option_type == "call":
        delta = normal_cdf(d1)

        theta = (
            -(stock_price * pdf_d1 * volatility)
            / (2 * math.sqrt(time_to_expiration))
            - risk_free_rate
            * strike_price
            * discount_factor
            * normal_cdf(d2)
        )

        rho = (
            strike_price
            * time_to_expiration
            * discount_factor
            * normal_cdf(d2)
        ) / 100

    else:
        delta = normal_cdf(d1) - 1

        theta = (
            -(stock_price * pdf_d1 * volatility)
            / (2 * math.sqrt(time_to_expiration))
            + risk_free_rate
            * strike_price
            * discount_factor
            * normal_cdf(-d2)
        )

        rho = (
            -strike_price
            * time_to_expiration
            * discount_factor
            * normal_cdf(-d2)
        ) / 100

    # Convert annual theta to daily theta.
    theta = theta / 365

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho
    }