import math
import numpy as np

from pricing import validate_inputs


def monte_carlo_price(
    stock_price,
    strike_price,
    time_to_expiration,
    risk_free_rate,
    volatility,
    simulations=100000,
    option_type="call",
    dividend_yield=0.0,
    seed=None,
    method="standard",
    pilot_simulations=None
):
    validate_inputs(
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility,
        dividend_yield
    )

    if type(simulations) is not int or simulations < 2:
        raise ValueError(
            "Simulations must be an integer of at least 2."
        )

    if option_type not in ("call", "put"):
        raise ValueError(
            "Option type must be 'call' or 'put'."
        )

    methods = (
        "standard",
        "antithetic",
        "control",
        "combined"
    )

    if method not in methods:
        raise ValueError("Invalid simulation method.")

    use_antithetic = method in ("antithetic", "combined")
    use_control = method in ("control", "combined")

    minimum = 4 if use_antithetic else 2

    if use_antithetic and (
        simulations < 4 or simulations % 2 != 0
    ):
        raise ValueError(
            "Antithetic methods require an even simulation "
            "count of at least 4."
        )

    if use_control:
        if pilot_simulations is None:
            pilot_simulations = max(
                minimum, simulations // 8
            )

            if use_antithetic:
                pilot_simulations += pilot_simulations % 2

        if type(pilot_simulations) is not int:
            raise ValueError(
                "Pilot simulations must be an integer."
            )

        if (
            pilot_simulations < minimum
            or simulations - pilot_simulations < minimum
        ):
            raise ValueError(
                "Insufficient pilot or pricing simulations."
            )

        if use_antithetic and pilot_simulations % 2 != 0:
            raise ValueError(
                "Antithetic pilot count must be even."
            )

    else:
        if pilot_simulations is not None:
            raise ValueError(
                "Pilot simulations require a control method."
            )

        pilot_simulations = 0

    rng = np.random.default_rng(seed)

    drift = (
        risk_free_rate
        - dividend_yield
        - 0.5 * volatility ** 2
    ) * time_to_expiration

    diffusion = (
        volatility * math.sqrt(time_to_expiration)
    )

    discount = math.exp(
        -risk_free_rate * time_to_expiration
    )

    expected_control = stock_price * math.exp(
        -dividend_yield * time_to_expiration
    )

    sign = 1 if option_type == "call" else -1

    def evaluate(random_values):
        terminal_prices = stock_price * np.exp(
            drift + diffusion * random_values
        )

        payoffs = np.maximum(
            sign * (terminal_prices - strike_price),
            0.0
        )

        return (
            discount * payoffs,
            discount * terminal_prices
        )

    def generate_samples(count):
        if use_antithetic:
            shocks = rng.standard_normal(count // 2)

            positive_y, positive_x = evaluate(shocks)
            negative_y, negative_x = evaluate(-shocks)

            return (
                (positive_y + negative_y) / 2,
                (positive_x + negative_x) / 2
            )

        shocks = rng.standard_normal(count)

        return evaluate(shocks)

    beta = 0.0

    if use_control:
        pilot_y, pilot_x = generate_samples(
            pilot_simulations
        )

        centered_x = pilot_x - np.mean(pilot_x)
        centered_y = pilot_y - np.mean(pilot_y)

        denominator = np.dot(centered_x, centered_x)

        if denominator > 0:
            beta = float(
                np.dot(centered_x, centered_y)
                / denominator
            )

    pricing_simulations = simulations - pilot_simulations

    samples, controls = generate_samples(
        pricing_simulations
    )

    if use_control:
        samples = samples - beta * (
            controls - expected_control
        )

    independent_samples = len(samples)

    price = float(np.mean(samples))

    standard_deviation = float(
        np.std(samples, ddof=1)
    )

    standard_error = (
        standard_deviation
        / math.sqrt(independent_samples)
    )

    margin_of_error = 1.95996398454 * standard_error

    return {
        "price": price,
        "standard_deviation": standard_deviation,
        "standard_error": standard_error,
        "confidence_interval": (
            price - margin_of_error,
            price + margin_of_error
        ),
        "simulations": simulations,
        "pilot_simulations": pilot_simulations,
        "pricing_simulations": pricing_simulations,
        "independent_samples": independent_samples,
        "beta": beta,
        "method": method
    }