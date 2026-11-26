import math

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks
from numerical_greeks import numerical_greeks
from implied_volatility import implied_volatility
from lattice import crr_price
from monte_carlo import monte_carlo_price

from visualization import (
    plot_option_prices,
    plot_volatility,
    plot_expiration,
    plot_greeks
)


def display_menu():
    print("\n" + "=" * 60)
    print("            DERIVATIVES PRICING LABORATORY")
    print("=" * 60)

    print("\nAnalytical Pricing")
    print("[1] European Call Pricing")
    print("[2] European Put Pricing")
    print("[3] Call and Put Comparison")
    print("[4] Analytical Greeks")

    print("\nSensitivity Analysis")
    print("[5] Volatility Sensitivity")
    print("[6] Expiration Sensitivity")
    print("[7] Interactive Visualizations")
    print("[8] Put-Call Parity Verification")

    print("\nComputational Finance")
    print("[9] Implied Volatility Solver")
    print("[10] European and American Binomial Pricing")
    print("[11] Monte Carlo Pricing")
    print("[12] Pricing Model Comparison")
    print("[13] Numerical Greeks Validation")

    print("\n[14] Exit Program")
    print("=" * 60)


def get_number(prompt, positive=False, nonnegative=False):
    while True:
        try:
            value = float(input(prompt))

            if not math.isfinite(value):
                print("Please enter a finite number.")
                continue

            if positive and value <= 0:
                print("Please enter a positive number.")
                continue

            if nonnegative and value < 0:
                print("Please enter a nonnegative number.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_integer(prompt, minimum, maximum):
    while True:
        try:
            value = int(input(prompt))

            if minimum <= value <= maximum:
                return value

        except ValueError:
            pass

        print(
            f"Enter an integer between "
            f"{minimum:,} and {maximum:,}."
        )


def get_choice(prompt, options):
    while True:
        choice = input(prompt).strip().lower()

        if choice in options:
            return choice

        print("Available choices: " + ", ".join(options))


def get_market_inputs():
    stock = get_number(
        "Current stock price ($): ", positive=True
    )

    strike = get_number(
        "Strike price ($): ", positive=True
    )

    time = get_number(
        "Time to expiration (years): ", positive=True
    )

    rate = get_number(
        "Risk-free interest rate (%): "
    ) / 100

    return stock, strike, time, rate


def get_dividend():
    return get_number(
        "Annual dividend yield (%): ",
        nonnegative=True
    ) / 100


def get_inputs():
    market = get_market_inputs()

    volatility = get_number(
        "Annual volatility (%): ", positive=True
    ) / 100

    dividend = get_dividend()

    return (*market, volatility, dividend)


def get_option_type():
    return get_choice(
        "Option type (call/put): ",
        ("call", "put")
    )


def get_simulation_budget():
    while True:
        budget = get_integer(
            "Simulation budget: ", 16, 1_000_000
        )

        if budget % 2 == 0:
            return budget

        print("Please enter an even simulation budget.")


def reference_price(parameters, option_type):
    function = (
        black_scholes_call
        if option_type == "call"
        else black_scholes_put
    )

    return function(*parameters)


def call_pricing():
    print("\n--- European Call Pricing ---")

    parameters = get_inputs()
    price = black_scholes_call(*parameters)

    print(f"\nTheoretical call price: ${price:,.6f}")


def put_pricing():
    print("\n--- European Put Pricing ---")

    parameters = get_inputs()
    price = black_scholes_put(*parameters)

    print(f"\nTheoretical put price: ${price:,.6f}")


def compare_options():
    print("\n--- Call and Put Comparison ---")

    parameters = get_inputs()

    call = black_scholes_call(*parameters)
    put = black_scholes_put(*parameters)

    print(f"\nCall price: ${call:,.6f}")
    print(f"Put price: ${put:,.6f}")
    print(f"Call minus put: ${call - put:,.6f}")


def greeks_analysis():
    print("\n--- Analytical Greeks ---")

    parameters = get_inputs()
    option_type = get_option_type()

    greeks = calculate_greeks(
        *parameters[:5],
        option_type=option_type,
        dividend_yield=parameters[5]
    )

    print("\nOption Sensitivities")
    print("-" * 35)

    for greek, value in greeks.items():
        print(f"{greek.capitalize():<10}: {value:.8f}")

    print("\nTheta: per calendar day")
    print("Vega and Rho: per percentage point")


def volatility_analysis():
    print("\n--- Volatility Sensitivity ---")

    stock, strike, time, rate, volatility, dividend = (
        get_inputs()
    )

    print(f"\n{'Volatility':<15}{'Call':>15}{'Put':>15}")
    print("-" * 45)

    for multiplier in (0.5, 0.75, 1, 1.25, 1.5, 2):
        vol = volatility * multiplier

        call = black_scholes_call(
            stock, strike, time, rate, vol, dividend
        )

        put = black_scholes_put(
            stock, strike, time, rate, vol, dividend
        )

        percentage = f"{vol * 100:.2f}%"

        print(
            f"{percentage:<15}"
            f"{call:>15.6f}{put:>15.6f}"
        )


def time_analysis():
    print("\n--- Expiration Sensitivity ---")

    stock, strike, time, rate, volatility, dividend = (
        get_inputs()
    )

    print(f"\n{'Years':<15}{'Call':>15}{'Put':>15}")
    print("-" * 45)

    for multiplier in (0.125, 0.25, 0.5, 1, 1.5, 2):
        expiration = time * multiplier

        call = black_scholes_call(
            stock, strike, expiration,
            rate, volatility, dividend
        )

        put = black_scholes_put(
            stock, strike, expiration,
            rate, volatility, dividend
        )

        print(
            f"{expiration:<15.4f}"
            f"{call:>15.6f}{put:>15.6f}"
        )


def visualization_menu():
    while True:
        print("\n--- Interactive Visualizations ---")
        print("[1] Option Pricing Curves")
        print("[2] Volatility Sensitivity")
        print("[3] Expiration Sensitivity")
        print("[4] Delta")
        print("[5] Gamma")
        print("[6] Theta")
        print("[7] Vega")
        print("[8] Rho")
        print("[9] Return to Main Menu")

        choice = input("Select a visualization: ").strip()

        if choice == "9":
            return

        functions = {
            "1": plot_option_prices,
            "2": plot_volatility,
            "3": plot_expiration
        }

        greeks = {
            "4": "delta",
            "5": "gamma",
            "6": "theta",
            "7": "vega",
            "8": "rho"
        }

        if choice not in functions and choice not in greeks:
            print("Invalid selection.")
            continue

        parameters = get_inputs()

        if choice in functions:
            functions[choice](*parameters)

        else:
            plot_greeks(
                *parameters[:5],
                greek=greeks[choice],
                dividend_yield=parameters[5]
            )


def verify_parity():
    print("\n--- Put-Call Parity Verification ---")

    parameters = get_inputs()

    stock, strike, time, rate, volatility, dividend = (
        parameters
    )

    call = black_scholes_call(*parameters)
    put = black_scholes_put(*parameters)

    left = call - put

    right = (
        stock * math.exp(-dividend * time)
        - strike * math.exp(-rate * time)
    )

    print(f"\nCall minus put: {left:.10f}")
    print(f"Discounted asset minus strike: {right:.10f}")
    print(f"Absolute difference: {abs(left - right):.3e}")

    if math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-8):
        print("Put-call parity successfully verified.")
    else:
        print("Put-call parity verification failed.")


def volatility_solver():
    print("\n--- Implied Volatility Solver ---")

    market = get_market_inputs()
    dividend = get_dividend()
    option_type = get_option_type()

    observed_price = get_number(
        "Observed European option price ($): ",
        positive=True
    )

    volatility = implied_volatility(
        observed_price,
        *market,
        option_type=option_type,
        dividend_yield=dividend
    )

    recovered_price = reference_price(
        (*market, volatility, dividend),
        option_type
    )

    print(f"\nImplied volatility: {volatility * 100:.6f}%")
    print(f"Recovered model price: ${recovered_price:.8f}")
    print(
        f"Pricing residual: "
        f"{abs(recovered_price - observed_price):.3e}"
    )


def binomial_pricing():
    print("\n--- Binomial Option Pricing ---")

    parameters = get_inputs()
    option_type = get_option_type()

    exercise_style = get_choice(
        "Exercise style (european/american): ",
        ("european", "american")
    )

    steps = get_integer(
        "Number of tree steps: ", 1, 4096
    )

    price = crr_price(
        *parameters[:5],
        steps=steps,
        option_type=option_type,
        exercise_style=exercise_style,
        dividend_yield=parameters[5]
    )

    reference = reference_price(
        parameters, option_type
    )

    print(f"\nBinomial price: ${price:.8f}")
    print(f"European BSM reference: ${reference:.8f}")

    if exercise_style == "european":
        print(
            f"Absolute pricing error: "
            f"${abs(price - reference):.8f}"
        )

    else:
        european = crr_price(
            *parameters[:5],
            steps=steps,
            option_type=option_type,
            exercise_style="european",
            dividend_yield=parameters[5]
        )

        print(f"European tree price: ${european:.8f}")

        print(
            f"Estimated early-exercise premium: "
            f"${price - european:.8f}"
        )


def monte_carlo_pricing():
    print("\n--- Monte Carlo Pricing ---")

    parameters = get_inputs()
    option_type = get_option_type()

    budget = get_simulation_budget()

    method = get_choice(
        "Method (standard/antithetic/control/combined): ",
        ("standard", "antithetic", "control", "combined")
    )

    result = monte_carlo_price(
        *parameters[:5],
        simulations=budget,
        option_type=option_type,
        dividend_yield=parameters[5],
        seed=42,
        method=method
    )

    reference = reference_price(
        parameters, option_type
    )

    lower, upper = result["confidence_interval"]

    print(f"\nEstimated price: ${result['price']:.8f}")
    print(f"Analytical reference: ${reference:.8f}")
    print(f"Standard error: {result['standard_error']:.8f}")
    print(f"Approximate 95% CI: [{lower:.6f}, {upper:.6f}]")
    print(f"Absolute error: ${abs(result['price'] - reference):.8f}")
    print(f"Total evaluations: {result['simulations']:,}")
    print(f"Pilot evaluations: {result['pilot_simulations']:,}")
    print(f"Independent observations: {result['independent_samples']:,}")
    print(f"Control coefficient: {result['beta']:.6f}")
    print("Random seed: 42")


def model_comparison():
    print("\n--- European Pricing Model Comparison ---")

    parameters = get_inputs()
    option_type = get_option_type()

    steps = get_integer(
        "Binomial tree steps: ", 1, 4096
    )

    budget = get_simulation_budget()

    reference = reference_price(
        parameters, option_type
    )

    tree_price = crr_price(
        *parameters[:5],
        steps=steps,
        option_type=option_type,
        dividend_yield=parameters[5]
    )

    results = [
        ("Black-Scholes", reference, None),
        ("CRR Binomial", tree_price, None)
    ]

    for method in (
        "standard", "antithetic", "control", "combined"
    ):
        result = monte_carlo_price(
            *parameters[:5],
            simulations=budget,
            option_type=option_type,
            dividend_yield=parameters[5],
            seed=42,
            method=method
        )

        results.append((
            method.capitalize(),
            result["price"],
            result["standard_error"]
        ))

    print(
        f"\n{'Model':<18}{'Price':>14}"
        f"{'Abs. Error':>14}{'Std. Error':>14}"
    )

    print("-" * 60)

    for model, price, standard_error in results:
        error = abs(price - reference)

        se = (
            f"{standard_error:.8f}"
            if standard_error is not None
            else "-"
        )

        print(
            f"{model:<18}{price:>14.8f}"
            f"{error:>14.8f}{se:>14}"
        )

    print("\nAll Monte Carlo methods use seed 42.")
    print("This is a single-run comparison, not an RMSE study.")


def compare_greeks():
    print("\n--- Numerical Greeks Validation ---")

    parameters = get_inputs()
    option_type = get_option_type()

    analytical = calculate_greeks(
        *parameters[:5],
        option_type=option_type,
        dividend_yield=parameters[5]
    )

    numerical = numerical_greeks(
        *parameters[:5],
        option_type=option_type,
        dividend_yield=parameters[5]
    )

    print(
        f"\n{'Greek':<10}{'Analytical':>16}"
        f"{'Numerical':>16}{'Abs. Error':>16}"
    )

    print("-" * 58)

    for greek in analytical:
        error = abs(
            analytical[greek] - numerical[greek]
        )

        print(
            f"{greek.capitalize():<10}"
            f"{analytical[greek]:>16.8f}"
            f"{numerical[greek]:>16.8f}"
            f"{error:>16.3e}"
        )

    print("\nRelative finite-difference step: 0.001")
    print("Theta: per day")
    print("Vega and Rho: per percentage point")


def main():
    actions = {
        "1": call_pricing,
        "2": put_pricing,
        "3": compare_options,
        "4": greeks_analysis,
        "5": volatility_analysis,
        "6": time_analysis,
        "7": visualization_menu,
        "8": verify_parity,
        "9": volatility_solver,
        "10": binomial_pricing,
        "11": monte_carlo_pricing,
        "12": model_comparison,
        "13": compare_greeks
    }

    while True:
        try:
            display_menu()

            choice = input("\nSelect an option: ").strip()

            if choice == "14":
                print("\nDerivatives Pricing Laboratory closed.")
                return

            if choice not in actions:
                print("Invalid selection.")
                continue

            actions[choice]()

        except (ValueError, OverflowError, RuntimeError) as error:
            print(f"\nCalculation error: {error}")

        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            return


if __name__ == "__main__":
    main()