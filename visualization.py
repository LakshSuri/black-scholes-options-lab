import matplotlib.pyplot as plt

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks


def generate_range(start, end, points=100):
    if points < 2:
        raise ValueError("At least two points are required.")

    step = (end - start) / (points - 1)

    return [
        start + i * step
        for i in range(points)
    ]


def plot_curves(
    x_values,
    call_values,
    put_values,
    title,
    xlabel,
    ylabel,
    reference,
    reference_label
):
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        x_values,
        call_values,
        label="European Call",
        color="#0d9488",
        linewidth=2
    )

    ax.plot(
        x_values,
        put_values,
        label="European Put",
        color="#2563eb",
        linewidth=2,
        linestyle="--"
    )

    ax.axvline(
        reference,
        color="#64748b",
        linestyle=":",
        label=reference_label
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(frameon=False)
    ax.grid(alpha=0.2)

    fig.tight_layout()

    plt.show()
    plt.close(fig)


def plot_option_prices(
    stock, strike, time, rate,
    volatility, dividend_yield=0.0
):
    stocks = generate_range(
        stock * 0.5, stock * 1.5
    )

    calls = [
        black_scholes_call(
            value, strike, time, rate,
            volatility, dividend_yield
        )
        for value in stocks
    ]

    puts = [
        black_scholes_put(
            value, strike, time, rate,
            volatility, dividend_yield
        )
        for value in stocks
    ]

    plot_curves(
        stocks, calls, puts,
        "Black-Scholes-Merton Option Pricing",
        "Underlying asset price ($)",
        "Theoretical option price ($)",
        strike,
        "Strike price"
    )


def plot_volatility(
    stock, strike, time, rate,
    volatility, dividend_yield=0.0
):
    volatilities = generate_range(
        volatility * 0.25, volatility * 2
    )

    calls = [
        black_scholes_call(
            stock, strike, time, rate,
            value, dividend_yield
        )
        for value in volatilities
    ]

    puts = [
        black_scholes_put(
            stock, strike, time, rate,
            value, dividend_yield
        )
        for value in volatilities
    ]

    percentages = [
        value * 100 for value in volatilities
    ]

    plot_curves(
        percentages, calls, puts,
        "Option Price Sensitivity to Volatility",
        "Annualized volatility (%)",
        "Theoretical option price ($)",
        volatility * 100,
        "Reference volatility"
    )


def plot_expiration(
    stock, strike, time, rate,
    volatility, dividend_yield=0.0
):
    expirations = generate_range(
        time * 0.01, time * 2
    )

    calls = [
        black_scholes_call(
            stock, strike, value, rate,
            volatility, dividend_yield
        )
        for value in expirations
    ]

    puts = [
        black_scholes_put(
            stock, strike, value, rate,
            volatility, dividend_yield
        )
        for value in expirations
    ]

    plot_curves(
        expirations, calls, puts,
        "Option Price Sensitivity to Expiration",
        "Time to expiration (years)",
        "Theoretical option price ($)",
        time,
        "Reference expiration"
    )


def plot_greeks(
    stock, strike, time, rate,
    volatility, greek="delta",
    dividend_yield=0.0
):
    labels = {
        "delta": "Delta",
        "gamma": "Gamma",
        "theta": "Theta (per day)",
        "vega": "Vega (per percentage point)",
        "rho": "Rho (per percentage point)"
    }

    if greek not in labels:
        raise ValueError("Invalid Greek selected.")

    stocks = generate_range(
        stock * 0.5, stock * 1.5
    )

    calls = [
        calculate_greeks(
            value, strike, time, rate,
            volatility, "call", dividend_yield
        )[greek]
        for value in stocks
    ]

    puts = [
        calculate_greeks(
            value, strike, time, rate,
            volatility, "put", dividend_yield
        )[greek]
        for value in stocks
    ]

    plot_curves(
        stocks, calls, puts,
        f"{greek.capitalize()} Sensitivity Analysis",
        "Underlying asset price ($)",
        labels[greek],
        strike,
        "Strike price"
    )