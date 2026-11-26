import argparse
from pathlib import Path

from analysis import calculate_greeks
from numerical_greeks import numerical_greeks
from experiments import write_csv


def greek_stability_study():
    configurations = [
        ("at_the_money", 100, 100, 1, 0.05, 0.20, 0.02),
        ("in_the_money_call", 120, 100, 0.5, 0.04, 0.25, 0.01),
        ("short_expiration", 100, 105, 0.08, 0.03, 0.35, 0.02)
    ]

    step_sizes = [
        10.0 ** (-exponent)
        for exponent in range(1, 14)
    ]

    rows = []

    for configuration in configurations:
        (
            scenario, stock, strike,
            time, rate, volatility, dividend
        ) = configuration

        for option_type in ["call", "put"]:
            analytical = calculate_greeks(
                stock,
                strike,
                time,
                rate,
                volatility,
                option_type,
                dividend
            )

            for step in step_sizes:
                numerical = numerical_greeks(
                    stock,
                    strike,
                    time,
                    rate,
                    volatility,
                    option_type,
                    dividend,
                    relative_step=step
                )

                for greek in analytical:
                    reference = analytical[greek]
                    estimate = numerical[greek]

                    signed_error = estimate - reference
                    absolute_error = abs(signed_error)

                    relative_error = (
                        absolute_error / abs(reference)
                        if reference != 0 else None
                    )

                    rows.append({
                        "scenario": scenario,
                        "option_type": option_type,
                        "stock": stock,
                        "strike": strike,
                        "expiration": time,
                        "risk_free_rate": rate,
                        "volatility": volatility,
                        "dividend_yield": dividend,
                        "greek": greek,
                        "relative_step": step,
                        "analytical_value": reference,
                        "numerical_value": estimate,
                        "signed_error": signed_error,
                        "absolute_error": absolute_error,
                        "relative_error": relative_error
                    })

    return rows


def optimal_step_study(rows):
    groups = {}

    for row in rows:
        key = (
            row["scenario"],
            row["option_type"],
            row["greek"]
        )

        groups.setdefault(key, []).append(row)

    summary = []

    for key, observations in groups.items():
        best = min(
            observations,
            key=lambda row: row["absolute_error"]
        )

        summary.append({
            "scenario": key[0],
            "option_type": key[1],
            "greek": key[2],
            "optimal_relative_step": best["relative_step"],
            "minimum_absolute_error": best["absolute_error"],
            "analytical_value": best["analytical_value"],
            "numerical_value": best["numerical_value"]
        })

    return summary


def run(output_directory):
    output = Path(output_directory)

    rows = greek_stability_study()
    summary = optimal_step_study(rows)

    write_csv(
        output / "greek_stability.csv",
        rows
    )

    write_csv(
        output / "optimal_greek_steps.csv",
        summary
    )

    print("Numerical stability experiment completed.")
    print(f"Observations: {len(rows)}")
    print(f"Optimal step configurations: {len(summary)}")
    print(f"Output directory: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Finite-difference numerical stability research"
    )

    parser.add_argument(
        "--output",
        default="results/data"
    )

    arguments = parser.parse_args()

    run(arguments.output)
