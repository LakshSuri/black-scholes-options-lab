import argparse
import math
from pathlib import Path
from time import perf_counter_ns

import numpy as np

from pricing import black_scholes_call
from lattice import crr_price
from monte_carlo import monte_carlo_price
from experiments import write_csv


def benchmark_study(replications=30, seed=42):
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

    reference = black_scholes_call(
        stock, strike, time,
        rate, volatility, dividend
    )

    configurations = [
        ("black_scholes", 0)
    ]

    for steps in [64, 256, 1024]:
        configurations.append(
            ("binomial", steps)
        )

    methods = [
        "standard",
        "antithetic",
        "control",
        "combined"
    ]

    for method in methods:
        for budget in [1024, 4096, 16384, 65536]:
            configurations.append(
                (method, budget)
            )

    seeds = np.random.SeedSequence(seed).spawn(
        len(configurations) * replications
    )

    seed_iterator = iter(seeds)

    def evaluate(model, resolution, simulation_seed):
        if model == "black_scholes":
            return black_scholes_call(
                stock, strike, time,
                rate, volatility, dividend
            )

        if model == "binomial":
            return crr_price(
                stock, strike, time,
                rate, volatility,
                steps=resolution,
                dividend_yield=dividend
            )

        result = monte_carlo_price(
            stock, strike, time,
            rate, volatility,
            simulations=resolution,
            dividend_yield=dividend,
            seed=simulation_seed,
            method=model
        )

        return result["price"]

    summary = []
    detailed = []

    for model, resolution in configurations:
        runtimes = []
        errors = []

        # Warm up the implementation before measuring.
        evaluate(model, resolution, 0)

        for replication in range(replications):
            simulation_seed = int(
                next(seed_iterator).generate_state(
                    1, dtype=np.uint64
                )[0]
            )

            start = perf_counter_ns()

            estimate = evaluate(
                model,
                resolution,
                simulation_seed
            )

            elapsed = (
                perf_counter_ns() - start
            ) / 1_000_000

            error = estimate - reference

            runtimes.append(elapsed)
            errors.append(error)

            detailed.append({
                "model": model,
                "resolution": resolution,
                "replication": replication + 1,
                "seed": simulation_seed,
                "reference_price": reference,
                "estimated_price": estimate,
                "signed_error": error,
                "absolute_error": abs(error),
                "runtime_ms": elapsed
            })

        errors = np.asarray(errors)

        rmse = math.sqrt(
            float(np.mean(errors ** 2))
        )

        summary.append({
            "model": model,
            "resolution": resolution,
            "replications": replications,
            "reference_price": reference,
            "mean_runtime_ms": float(
                np.mean(runtimes)
            ),
            "median_runtime_ms": float(
                np.median(runtimes)
            ),
            "p90_runtime_ms": float(
                np.percentile(runtimes, 90)
            ),
            "rmse": rmse,
            "mean_absolute_error": float(
                np.mean(np.abs(errors))
            ),
            "maximum_absolute_error": float(
                np.max(np.abs(errors))
            ),
            "bias": float(np.mean(errors))
        })

    return summary, detailed


def run(output_directory):
    output = Path(output_directory)

    summary, detailed = benchmark_study()

    write_csv(
        output / "benchmark_summary.csv",
        summary
    )

    write_csv(
        output / "benchmark_replications.csv",
        detailed
    )

    print("Computational benchmarking completed.")
    print(f"Configurations: {len(summary)}")
    print(f"Measured executions: {len(detailed)}")
    print(f"Output directory: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Derivatives pricing performance benchmarks"
    )

    parser.add_argument(
        "--output",
        default="results/data"
    )

    arguments = parser.parse_args()

    run(arguments.output)
