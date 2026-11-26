import matplotlib.pyplot as plt

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks


def generate_range(start, end, points=100):
    step = (end - start) / (points - 1)

    return [
        start + i * step
        for i in range(points)
    ]


def plot_option_prices(stock, strike, time, rate, volatility):
    stock_prices = generate_range(
        stock * 0.5, stock * 1.5
    )

    call_prices = []
    put_prices = []

    for price in stock_prices:
        call_prices.append(
            black_scholes_call(
                price, strike, time, rate, volatility
            )
        )

        put_prices.append(
            black_scholes_put(
                price, strike, time, rate, volatility
            )
        )

    plt.figure(figsize=(10, 6))

    plt.plot(
        stock_prices, call_prices,
        label="Call Option", color="green", linewidth=2
    )

    plt.plot(
        stock_prices, put_prices,
        label="Put Option", color="blue", linewidth=2
    )

    plt.axvline(
        strike, color="gray",
        linestyle="--", label="Strike Price"
    )

    plt.title("Black-Scholes Option Pricing Curves")
    plt.xlabel("Stock Price ($)")
    plt.ylabel("Theoretical Option Price ($)")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.show()
    plt.close()


def plot_volatility(stock, strike, time, rate, volatility):
    volatilities = generate_range(
        volatility * 0.25, volatility * 2
    )

    call_prices = []
    put_prices = []

    for vol in volatilities:
        call_prices.append(
            black_scholes_call(
                stock, strike, time, rate, vol
            )
        )

        put_prices.append(
            black_scholes_put(
                stock, strike, time, rate, vol
            )
        )

    percentages = [
        vol * 100 for vol in volatilities
    ]

    plt.figure(figsize=(10, 6))

    plt.plot(
        percentages, call_prices,
        label="Call Option", color="green", linewidth=2
    )

    plt.plot(
        percentages, put_prices,
        label="Put Option", color="blue", linewidth=2
    )

    plt.axvline(
        volatility * 100,
        color="gray",
        linestyle="--",
        label="Reference Volatility"
    )

    plt.title("Option Price Sensitivity to Volatility")
    plt.xlabel("Annual Volatility (%)")
    plt.ylabel("Theoretical Option Price ($)")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.show()
    plt.close()


def plot_expiration(stock, strike, time, rate, volatility):
    expiration_periods = generate_range(
        time * 0.01, time * 2
    )

    call_prices = []
    put_prices = []

    for expiration in expiration_periods:
        call_prices.append(
            black_scholes_call(
                stock, strike, expiration, rate, volatility
            )
        )

        put_prices.append(
            black_scholes_put(
                stock, strike, expiration, rate, volatility
            )
        )

    plt.figure(figsize=(10, 6))

    plt.plot(
        expiration_periods, call_prices,
        label="Call Option", color="green", linewidth=2
    )

    plt.plot(
        expiration_periods, put_prices,
        label="Put Option", color="blue", linewidth=2
    )

    plt.axvline(
        time, color="gray",
        linestyle="--", label="Reference Expiration"
    )

    plt.title("Option Price Sensitivity to Expiration")
    plt.xlabel("Time to Expiration (Years)")
    plt.ylabel("Theoretical Option Price ($)")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.show()
    plt.close()


def plot_greeks(
    stock, strike, time, rate, volatility,
    greek="delta"
):
    labels = {
        "delta": "Delta",
        "gamma": "Gamma",
        "theta": "Theta (Per Day)",
        "vega": "Vega (Per Percentage Point)",
        "rho": "Rho (Per Percentage Point)"
    }

    if greek not in labels:
        raise ValueError("Invalid Greek selected.")

    stock_prices = generate_range(
        stock * 0.5, stock * 1.5
    )

    call_values = []
    put_values = []

    for price in stock_prices:
        call_greeks = calculate_greeks(
            price, strike, time, rate,
            volatility, "call"
        )

        put_greeks = calculate_greeks(
            price, strike, time, rate,
            volatility, "put"
        )

        call_values.append(call_greeks[greek])
        put_values.append(put_greeks[greek])

    plt.figure(figsize=(10, 6))

    plt.plot(
        stock_prices, call_values,
        label="Call Option", color="green", linewidth=2
    )

    plt.plot(
        stock_prices, put_values,
        label="Put Option", color="blue",
        linewidth=2, linestyle="--"
    )

    plt.axvline(
        strike, color="gray",
        linestyle="--", label="Strike Price"
    )

    plt.title(f"{greek.capitalize()} Sensitivity Analysis")
    plt.xlabel("Stock Price ($)")
    plt.ylabel(labels[greek])
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.show()
    plt.close()