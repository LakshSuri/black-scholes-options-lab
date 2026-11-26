import math

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks


def display_menu():
    print("\n" + "=" * 48)
    print("      BLACK-SCHOLES OPTIONS PRICING LAB")
    print("=" * 48)
    print("[1] Call Option Pricing")
    print("[2] Put Option Pricing")
    print("[3] Call and Put Comparison")
    print("[4] Option Greeks Analysis")
    print("[5] Volatility Sensitivity Analysis")
    print("[6] Time-to-Expiration Analysis")
    print("[7] Option Pricing Visualizations")
    print("[8] Put-Call Parity Verification")
    print("[9] Exit Program")
    print("=" * 48)


def get_number(prompt, positive=False):
    while True:
        try:
            value = float(input(prompt))

            if not math.isfinite(value):
                print("Please enter a finite number.")
                continue

            if positive and value <= 0:
                print("Please enter a positive number.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_inputs():
    stock_price = get_number(
        "Current stock price ($): ", True
    )

    strike_price = get_number(
        "Strike price ($): ", True
    )

    time_to_expiration = get_number(
        "Time to expiration (years): ", True
    )

    risk_free_rate = get_number(
        "Risk-free interest rate (%): "
    ) / 100

    volatility = get_number(
        "Annual volatility (%): ", True
    ) / 100

    return (
        stock_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility
    )


def call_pricing():
    print("\n--- Call Option Pricing ---")

    parameters = get_inputs()
    price = black_scholes_call(*parameters)

    print(f"\nTheoretical call price: ${price:,.2f}")


def put_pricing():
    print("\n--- Put Option Pricing ---")

    parameters = get_inputs()
    price = black_scholes_put(*parameters)

    print(f"\nTheoretical put price: ${price:,.2f}")


def compare_options():
    print("\n--- Call and Put Comparison ---")

    parameters = get_inputs()

    call = black_scholes_call(*parameters)
    put = black_scholes_put(*parameters)

    print(f"\nCall price: ${call:,.2f}")
    print(f"Put price: ${put:,.2f}")
    print(f"Price difference: ${abs(call - put):,.2f}")


def greeks_analysis():
    print("\n--- Option Greeks Analysis ---")

    parameters = get_inputs()

    while True:
        option_type = input(
            "Option type (call/put): "
        ).strip().lower()

        if option_type in ("call", "put"):
            break

        print("Please enter call or put.")

    greeks = calculate_greeks(
        *parameters, option_type=option_type
    )

    print("\nOption Greeks")
    print("-" * 32)

    for greek, value in greeks.items():
        print(f"{greek.capitalize():<10}: {value:.6f}")


def volatility_analysis():
    print("\n--- Volatility Sensitivity Analysis ---")

    stock, strike, time, rate, volatility = get_inputs()

    print(f"\nReference volatility: {volatility * 100:.2f}%")
    print(f"{'Volatility':<15}{'Call':>12}{'Put':>12}")
    print("-" * 39)

    for multiplier in (0.5, 0.75, 1, 1.25, 1.5, 2):
        vol = volatility * multiplier

        call = black_scholes_call(
            stock, strike, time, rate, vol
        )

        put = black_scholes_put(
            stock, strike, time, rate, vol
        )

        print(f"{vol * 100:<14.2f}%{call:>12.2f}{put:>12.2f}")


def time_analysis():
    print("\n--- Time-to-Expiration Analysis ---")

    stock, strike, time, rate, volatility = get_inputs()

    print(f"\nReference expiration: {time:.4f} years")
    print(f"{'Years':<15}{'Call':>12}{'Put':>12}")
    print("-" * 39)

    for multiplier in (0.125, 0.25, 0.5, 1, 1.5, 2):
        expiration = time * multiplier

        call = black_scholes_call(
            stock, strike, expiration, rate, volatility
        )

        put = black_scholes_put(
            stock, strike, expiration, rate, volatility
        )

        print(f"{expiration:<15.4f}{call:>12.2f}{put:>12.2f}")


def verify_parity():
    print("\n--- Put-Call Parity Verification ---")

    stock, strike, time, rate, volatility = get_inputs()

    call = black_scholes_call(
        stock, strike, time, rate, volatility
    )

    put = black_scholes_put(
        stock, strike, time, rate, volatility
    )

    left_side = call - put
    right_side = stock - strike * math.exp(-rate * time)

    difference = abs(left_side - right_side)

    print(f"\nC - P: {left_side:.8f}")
    print(f"S - Ke^(-rT): {right_side:.8f}")
    print(f"Numerical difference: {difference:.10f}")

    if math.isclose(left_side, right_side, rel_tol=1e-9,
                    abs_tol=1e-8):
        print("Put-call parity successfully verified.")
    else:
        print("Put-call parity verification failed.")


def main():
    while True:
        display_menu()

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            call_pricing()

        elif choice == "2":
            put_pricing()

        elif choice == "3":
            compare_options()

        elif choice == "4":
            greeks_analysis()

        elif choice == "5":
            volatility_analysis()

        elif choice == "6":
            time_analysis()

        elif choice == "7":
            print("\nVisualizations are coming in the next update.")

        elif choice == "8":
            verify_parity()

        elif choice == "9":
            print("\nThank you for using the Options Pricing Lab.")
            break

        else:
            print("\nInvalid selection. Please try again.")


if __name__ == "__main__":
    main()