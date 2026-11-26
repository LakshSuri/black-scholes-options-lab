import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np


METHODS = {
    "standard": ("Standard", "#64748b"),
    "antithetic": ("Antithetic", "#2563eb"),
    "control": ("Control variate", "#0d9488"),
    "combined": ("Combined", "#9333ea")
}


plt.rcParams.update({
    "figure.figsize": (10, 6),
    "figure.dpi": 120,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.2,
    "legend.frameon": False,
    "savefig.facecolor": "white"
})


def read_csv(path):
    with Path(path).open(
        encoding="utf-8", newline=""
    ) as file:
        return list(csv.DictReader(file))


def save_figure(fig, output, name):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)

    fig.tight_layout()

    fig.savefig(
        output / f"{name}.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)


def tree_convergence(data, output):
    rows = read_csv(data / "tree_convergence.csv")

    fig, axes = plt.subplots(
        2, 2, figsize=(12, 8)
    )

    for ax, strike in zip(
        axes.flat, [80, 95, 100, 120]
    ):
        for parity, color in [
            ("even", "#2563eb"),
            ("odd", "#d97706")
        ]:
            selected = [
                row for row in rows
                if row["option_type"] == "call"
                and float(row["strike"]) == strike
                and row["step_parity"] == parity
            ]

            selected.sort(
                key=lambda row: int(row["steps"])
            )

            ax.semilogx(
                [int(row["steps"]) for row in selected],
                [float(row["signed_error"]) for row in selected],
                marker="o",
                color=color,
                label=parity.capitalize()
            )

        ax.axhline(
            0, color="black",
            linestyle="--", linewidth=1
        )

        ax.set_title(f"Strike = ${strike}")
        ax.set_xlabel("Tree steps")
        ax.set_ylabel("Signed pricing error ($)")
        ax.legend()

    fig.suptitle(
        "CRR Binomial Convergence: European Calls",
        fontsize=16
    )

    save_figure(fig, output, "tree_convergence")


def monte_carlo_convergence(data, output):
    rows = read_csv(
        data / "monte_carlo_summary.csv"
    )

    fig, ax = plt.subplots()

    for method, (label, color) in METHODS.items():
        selected = [
            row for row in rows
            if row["method"] == method
        ]

        selected.sort(
            key=lambda row: int(row["budget"])
        )

        ax.loglog(
            [int(row["budget"]) for row in selected],
            [float(row["rmse"]) for row in selected],
            marker="o",
            linewidth=2,
            color=color,
            label=label
        )

    standard = sorted(
        [
            row for row in rows
            if row["method"] == "standard"
        ],
        key=lambda row: int(row["budget"])
    )

    budgets = np.array([
        int(row["budget"]) for row in standard
    ])

    initial_error = float(standard[0]["rmse"])

    theoretical = initial_error * np.sqrt(
        budgets[0] / budgets
    )

    ax.loglog(
        budgets,
        theoretical,
        color="black",
        linestyle="--",
        label="Reference slope: -1/2"
    )

    ax.set_title("Monte Carlo RMSE Convergence")
    ax.set_xlabel("Total simulation budget")
    ax.set_ylabel("Root mean squared error ($)")
    ax.legend()

    save_figure(
        fig, output, "monte_carlo_convergence"
    )


def confidence_coverage(data, output):
    rows = read_csv(
        data / "monte_carlo_summary.csv"
    )

    fig, ax = plt.subplots()

    for method, (label, color) in METHODS.items():
        selected = sorted(
            [
                row for row in rows
                if row["method"] == method
            ],
            key=lambda row: int(row["budget"])
        )

        ax.semilogx(
            [int(row["budget"]) for row in selected],
            [100 * float(row["coverage"]) for row in selected],
            marker="o",
            color=color,
            linewidth=2,
            label=label
        )

    ax.axhline(
        95,
        color="black",
        linestyle="--",
        label="Nominal 95% coverage"
    )

    ax.set_title("Monte Carlo Confidence Interval Coverage")
    ax.set_xlabel("Total simulation budget")
    ax.set_ylabel("Empirical coverage (%)")
    ax.set_ylim(0, 102)
    ax.legend()

    save_figure(fig, output, "confidence_coverage")


def greek_stability(data, output):
    rows = read_csv(data / "greek_stability.csv")

    fig, axes = plt.subplots(
        1, 2, figsize=(12, 5)
    )

    for ax, greek in zip(axes, ["delta", "gamma"]):
        for option_type, color in [
            ("call", "#2563eb"),
            ("put", "#d97706")
        ]:
            selected = sorted(
                [
                    row for row in rows
                    if row["scenario"] == "at_the_money"
                    and row["greek"] == greek
                    and row["option_type"] == option_type
                    and float(row["absolute_error"]) > 0
                ],
                key=lambda row: float(row["relative_step"])
            )

            ax.loglog(
                [
                    float(row["relative_step"])
                    for row in selected
                ],
                [
                    float(row["absolute_error"])
                    for row in selected
                ],
                marker="o",
                color=color,
                label=option_type.capitalize()
            )

        ax.set_title(f"{greek.capitalize()} Stability")
        ax.set_xlabel("Relative finite-difference step")
        ax.set_ylabel("Absolute numerical error")
        ax.legend()

    fig.suptitle(
        "Finite-Difference Truncation and Roundoff Error",
        fontsize=16
    )

    save_figure(fig, output, "greek_stability")


def volatility_conditioning(data, output):
    rows = read_csv(
        data / "volatility_conditioning.csv"
    )

    strikes = sorted({
        float(row["strike"]) for row in rows
    })

    expirations = sorted({
        float(row["expiration"]) for row in rows
    })

    matrix = np.full(
        (len(expirations), len(strikes)),
        np.nan
    )

    for row in rows:
        if row["option_type"] != "call":
            continue

        if not row["inverse_sensitivity"]:
            continue

        value = float(row["inverse_sensitivity"])

        if not np.isfinite(value) or value <= 0:
            continue

        i = expirations.index(
            float(row["expiration"])
        )

        j = strikes.index(
            float(row["strike"])
        )

        matrix[i, j] = value

    fig, ax = plt.subplots()

    image = ax.imshow(
        np.ma.masked_invalid(matrix),
        aspect="auto",
        origin="lower",
        cmap="viridis",
        norm=LogNorm()
    )

    ax.set_xticks(range(len(strikes)))
    ax.set_xticklabels([
        f"${strike:g}" for strike in strikes
    ])

    ax.set_yticks(range(len(expirations)))
    ax.set_yticklabels([
        f"{time:g}" for time in expirations
    ])

    ax.set_title("Implied Volatility Conditioning")
    ax.set_xlabel("Strike price")
    ax.set_ylabel("Time to expiration (years)")
    ax.grid(False)

    fig.colorbar(
        image,
        ax=ax,
        label="Inverse Vega (volatility per dollar)"
    )

    save_figure(
        fig, output, "volatility_conditioning"
    )


def performance_benchmark(data, output):
    rows = read_csv(
        data / "benchmark_summary.csv"
    )

    fig, ax = plt.subplots()

    models = {
        **METHODS,
        "binomial": ("CRR binomial", "#dc2626")
    }

    for model, (label, color) in models.items():
        selected = sorted(
            [
                row for row in rows
                if row["model"] == model
                and float(row["rmse"]) > 0
                and float(row["median_runtime_ms"]) > 0
            ],
            key=lambda row: int(row["resolution"])
        )

        ax.loglog(
            [
                float(row["median_runtime_ms"])
                for row in selected
            ],
            [
                float(row["rmse"])
                for row in selected
            ],
            marker="o",
            linewidth=2,
            color=color,
            label=label
        )

    ax.set_title("Computational Cost versus Pricing Accuracy")
    ax.set_xlabel("Median runtime (milliseconds)")
    ax.set_ylabel("Root mean squared error ($)")
    ax.legend()

    save_figure(
        fig, output, "performance_benchmark"
    )


def run(data_directory, output_directory):
    data = Path(data_directory)
    output = Path(output_directory)

    figures = [
        tree_convergence,
        monte_carlo_convergence,
        confidence_coverage,
        greek_stability,
        volatility_conditioning,
        performance_benchmark
    ]

    for figure in figures:
        figure(data, output)
        print(f"Created: {figure.__name__}.png")

    print(f"Figures generated: {len(figures)}")
    print(f"Output directory: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate derivatives research figures"
    )

    parser.add_argument(
        "--data",
        default="results/data"
    )

    parser.add_argument(
        "--output",
        default="results/figures"
    )

    arguments = parser.parse_args()

    run(arguments.data, arguments.output)
