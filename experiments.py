import argparse
import csv
import math
from pathlib import Path
from time import perf_counter

import numpy as np

from pricing import black_scholes_call, black_scholes_put
from lattice import crr_price
from monte_carlo import monte_carlo_price


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise ValueError("Cannot export an empty dataset.")

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(rows)


def tree_convergence_study():
    stock = 100
    time = 1
    rate = 0.05
    volatility = 0.20
    dividend = 0.02

    strikes = [80, 95, 100, 120]

    resolutions = [
        16, 17,
        32, 33,
        64, 65,
        128, 129,
        256, 257,
        512, 513,
        1024, 1025,
        2048, 2049
    ]

    rows = []

    for option_type in ["call", "put"]:
        pricing_function = (
            black_scholes_call
            if option_type == "call"
            else black_scholes_put
        )

        for strike in strikes:
            reference = pricing_function(
                stock, strike, time,
                rate, volatility, dividend
            )

            for steps in resolutions:
                estimate = crr_price(
                    stock, strike, time,
                    rate, volatility,
                    steps=steps,
                    option_type=option_type,
                    dividend_yield=dividend
                )

                signed_error = estimate - reference
                absolute_error = abs(signed_error)

                rows.append({
                    "option_type": option_type,
                    "stock": stock,
                    "strike": strike,
                    "expiration": time,
                    "risk_free_rate": rate,
                    "volatility": volatility,
                    "dividend_yield": dividend,
                    "steps": steps,
                    "step_parity": (
                        "even" if steps % 2 == 0 else "odd"
                    ),
                    "reference_price": reference,
                    "estimated_price": estimate,
                    "signed_error": signed_error,
                    "absolute_error": absolute_error,
                    "relative_error": (
                        absolute_error / reference
                        if reference > 0 else None
                    )
                })

    return rows


def monte_carlo_study(replications=100, seed=42):
    if type(replications) is not int or replications < 2:
        raise ValueError(
            "At least two replications are required."
        )

    stock = 100
    strike = 105
    time = 1
    rate = 0.05
    volatility = 0.25
    dividend = 0.02

    budgets = [
        1024,
        4096,
        16384,
        65536
    ]

    methods = [
        "standard",
        "antithetic",
        "control",
        "combined"
    ]

    reference = black_scholes_call(
        stock, strike, time,
        rate, volatility, dividend
    )

    seed_sequence = np.random.SeedSequence(seed)

    child_seeds = seed_sequence.spawn(
        len(budgets) * len(methods) * replications
    )

    seed_iterator = iter(child_seeds)

    summary_rows = []
    detailed_rows = []

    for budget in budgets:
        baseline_mse = None

        for method in methods:
            estimates = []
            errors = []
            standard_errors = []
            coverage = []
            runtimes = []

            for replication in range(replications):
                simulation_seed = int(
                    next(seed_iterator).generate_state(
                        1, dtype=np.uint64
                    )[0]
                )

                start = perf_counter()

                result = monte_carlo_price(
                    stock,
                    strike,
                    time,
                    rate,
                    volatility,
                    simulations=budget,
                    option_type="call",
                    dividend_yield=dividend,
                    seed=simulation_seed,
                    method=method
                )

                runtime = perf_counter() - start

                estimate = result["price"]
                error = estimate - reference

                lower, upper = result[
                    "confidence_interval"
                ]

                covered = lower <= reference <= upper

                estimates.append(estimate)
                errors.append(error)
                standard_errors.append(
                    result["standard_error"]
                )

                coverage.append(covered)
                runtimes.append(runtime)

                detailed_rows.append({
                    "method": method,
                    "budget": budget,
                    "replication": replication + 1,
                    "seed": simulation_seed,
                    "reference_price": reference,
                    "estimated_price": estimate,
                    "signed_error": error,
                    "absolute_error": abs(error),
                    "standard_error": result[
                        "standard_error"
                    ],
                    "confidence_lower": lower,
                    "confidence_upper": upper,
                    "covered": int(covered),
                    "pilot_simulations": result[
                        "pilot_simulations"
                    ],
                    "runtime_seconds": runtime
                })

            errors = np.asarray(errors)

            mse = float(np.mean(errors ** 2))
            rmse = math.sqrt(mse)

            if method == "standard":
                baseline_mse = mse

            summary_rows.append({
                "method": method,
                "budget": budget,
                "replications": replications,
                "reference_price": reference,
                "mean_estimate": float(
                    np.mean(estimates)
                ),
                "bias": float(np.mean(errors)),
                "rmse": rmse,
                "empirical_standard_deviation": float(
                    np.std(estimates, ddof=1)
                ),
                "mean_standard_error": float(
                    np.mean(standard_errors)
                ),
                "coverage": float(np.mean(coverage)),
                "relative_efficiency": (
                    baseline_mse / mse
                    if mse > 0 else None
                ),
                "mean_runtime_seconds": float(
                    np.mean(runtimes)
                )
            })

    return summary_rows, detailed_rows


def run(output_directory):
    output = Path(output_directory)

    tree_results = tree_convergence_study()

    write_csv(
        output / "tree_convergence.csv",
        tree_results
    )

    print("Tree convergence experiment completed.")
    print(f"Observations: {len(tree_results)}")

    summary, detailed = monte_carlo_study()

    write_csv(
        output / "monte_carlo_summary.csv",
        summary
    )

    write_csv(
        output / "monte_carlo_replications.csv",
        detailed
    )

    print("Monte Carlo experiment completed.")
    print(f"Configurations: {len(summary)}")
    print(f"Replications: {len(detailed)}")
    print(f"Output directory: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reproducible derivatives pricing experiments"
    )

    parser.add_argument(
        "--output",
        default="results/data",
        help="Directory for experimental datasets"
    )

    arguments = parser.parse_args()

    run(arguments.output)
