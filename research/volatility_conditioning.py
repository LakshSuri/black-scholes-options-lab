import argparse
import math
from pathlib import Path

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks
from implied_volatility import implied_volatility
from experiments import write_csv


def volatility_conditioning_study():
    stock = 100
    rate = 0.05
    dividend = 0.02
    volatility = 0.25

    strikes = [60, 80, 100, 120, 140]

    expirations = [0.05, 0.25, 1, 2]

    perturbations = [
        -0.10, -0.01, -0.001,
        0.001, 0.01, 0.10
    ]

    rows = []

    for option_type in ["call", "put"]:
        pricing_function = (
            black_scholes_call
            if option_type == "call"
            else black_scholes_put
        )

        for strike in strikes:
            for time in expirations:
                reference_price = pricing_function(
                    stock, strike, time,
                    rate, volatility, dividend
                )

                greeks = calculate_greeks(
                    stock, strike, time,
                    rate, volatility,
                    option_type, dividend
                )

                raw_vega = greeks["vega"] * 100

                inverse_sensitivity = (
                    1 / raw_vega
                    if raw_vega > 0 else None
                )

                discounted_stock = stock * math.exp(
                    -dividend * time
                )

                discounted_strike = strike * math.exp(
                    -rate * time
                )

                if option_type == "call":
                    lower_bound = max(
                        0, discounted_stock - discounted_strike
                    )
                    upper_bound = discounted_stock
                else:
                    lower_bound = max(
                        0, discounted_strike - discounted_stock
                    )
                    upper_bound = discounted_strike

                for perturbation in perturbations:
                    observed_price = (
                        reference_price + perturbation
                    )

                    recovered = None
                    signed_error = None
                    absolute_error = None
                    amplification = None

                    predicted_error = (
                        perturbation / raw_vega
                        if raw_vega > 0 else None
                    )

                    if not lower_bound < observed_price < upper_bound:
                        status = "outside_pricing_bounds"

                    else:
                        try:
                            recovered = implied_volatility(
                                observed_price,
                                stock,
                                strike,
                                time,
                                rate,
                                option_type,
                                dividend
                            )

                            signed_error = recovered - volatility

                            absolute_error = abs(signed_error)

                            amplification = (
                                absolute_error
                                / abs(perturbation)
                            )

                            status = "success"

                        except (ValueError, RuntimeError):
                            status = "solver_failure"

                    rows.append({
                        "option_type": option_type,
                        "stock": stock,
                        "strike": strike,
                        "moneyness": stock / strike,
                        "expiration": time,
                        "risk_free_rate": rate,
                        "dividend_yield": dividend,
                        "original_volatility": volatility,
                        "reference_price": reference_price,
                        "price_perturbation": perturbation,
                        "observed_price": observed_price,
                        "raw_vega": raw_vega,
                        "inverse_sensitivity": inverse_sensitivity,
                        "predicted_volatility_error": predicted_error,
                        "recovered_volatility": recovered,
                        "signed_volatility_error": signed_error,
                        "absolute_volatility_error": absolute_error,
                        "error_amplification": amplification,
                        "status": status
                    })

    return rows


def run(output_directory):
    output = Path(output_directory)

    rows = volatility_conditioning_study()

    write_csv(
        output / "volatility_conditioning.csv",
        rows
    )

    successful = sum(
        row["status"] == "success"
        for row in rows
    )

    invalid = sum(
        row["status"] == "outside_pricing_bounds"
        for row in rows
    )

    failures = sum(
        row["status"] == "solver_failure"
        for row in rows
    )

    print("Volatility conditioning experiment completed.")
    print(f"Observations: {len(rows)}")
    print(f"Successful recoveries: {successful}")
    print(f"Outside pricing bounds: {invalid}")
    print(f"Solver failures: {failures}")
    print(f"Output directory: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Implied volatility conditioning research"
    )

    parser.add_argument(
        "--output",
        default="results/data"
    )

    arguments = parser.parse_args()

    run(arguments.output)
