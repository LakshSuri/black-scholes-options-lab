import math
import numpy as np

from pricing import validate_inputs


def crr_price(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    steps=100,
    option_type="call",
    exercise_style="european",
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

    if type(steps) is not int or steps <= 0:
        raise ValueError("Steps must be a positive integer.")

    if option_type not in ("call", "put"):
        raise ValueError("Option type must be 'call' or 'put'.")

    if exercise_style not in ("european", "american"):
        raise ValueError(
            "Exercise style must be 'european' or 'american'."
        )

    dt = time_to_expiration / steps
    move = volatility * math.sqrt(dt)

    up = math.exp(move)
    down = math.exp(-move)

    growth = math.exp(
        (risk_free_rate - dividend_yield) * dt
    )

    probability = (growth - down) / (up - down)

    if not 0 < probability < 1:
        raise ValueError(
            "Invalid risk-neutral probability. Increase steps."
        )

    discount = math.exp(-risk_free_rate * dt)
    sign = 1 if option_type == "call" else -1

    indices = np.arange(steps + 1)

    stock_values = stock_price * np.exp(
        (steps - 2 * indices) * move
    )

    values = np.maximum(
        sign * (stock_values - strike_price),
        0.0
    )

    for level in range(steps - 1, -1, -1):
        values = discount * (
            probability * values[:-1]
            + (1 - probability) * values[1:]
        )

        if exercise_style == "american":
            indices = np.arange(level + 1)

            stock_values = stock_price * np.exp(
                (level - 2 * indices) * move
            )

            exercise_values = np.maximum(
                sign * (stock_values - strike_price),
                0.0
            )

            values = np.maximum(
                values,
                exercise_values
            )

    return float(values[0])