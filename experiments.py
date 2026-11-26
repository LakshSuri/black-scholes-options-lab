"""Generate seeded numerical studies and publication-ready figures."""

import argparse
import csv
from pathlib import Path
import platform

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np

from analysis import calculate_greeks, numerical_greeks
from lattice import crr_price
from monte_carlo import monte_carlo_price
from pricing import black_scholes_merton


CONTRACT = (100.0, 105.0, 1.0, 0.04, 0.24)
DIVIDEND = 0.02
SEED = 20261126
REPLICATIONS = 48


def tree_study():
    rows = []
    for strike in (85.0, 100.0, 105.0, 120.0):
        args = (CONTRACT[0], strike, *CONTRACT[2:])
        reference = black_scholes_merton(*args, dividend_yield=DIVIDEND)
        for count in (16, 32, 64, 128, 256, 512, 1024, 2048):
            for steps in (count, count + 1):
                price = crr_price(*args, dividend_yield=DIVIDEND, steps=steps)
                rows.append(dict(
                    strike=strike, steps=steps, price=price, reference=reference,
                    signed_error=price - reference, absolute_error=abs(price - reference),
                ))
    return rows


def sampling_study():
    rows = []
    reference = black_scholes_merton(*CONTRACT, dividend_yield=DIVIDEND)
    methods = (
        ("Plain", False, False),
        ("Antithetic", True, False),
        ("Control variate", False, True),
        ("Antithetic + control", True, True),
    )
    for budget in (1024, 4096, 16384, 65536):
        seeds = np.random.SeedSequence([SEED, budget]).spawn(REPLICATIONS)
        for name, antithetic, control in methods:
            # Include pilot work in the total payoff evaluation budget.
            pilot = budget // 8 if control else 0
            results = [
                monte_carlo_price(
                    *CONTRACT, dividend_yield=DIVIDEND, paths=budget - pilot,
                    seed=seed, antithetic=antithetic, control_variate=control,
                    pilot_paths=pilot,
                )
                for seed in seeds
            ]
            errors = np.array([result.price - reference for result in results])
            rows.append(dict(
                method=name, budget=budget, pilot_paths=pilot, reference=reference,
                replications=REPLICATIONS, mean_error=float(errors.mean()),
                rmse=float(np.sqrt(np.mean(errors ** 2))),
                mean_standard_error=float(np.mean([r.standard_error for r in results])),
                coverage=sum(
                    r.confidence_interval[0] <= reference <= r.confidence_interval[1]
                    for r in results
                ) / REPLICATIONS,
            ))
    return rows


def greek_study():
    rows = []
    for kind in ("call", "put"):
        reference = calculate_greeks(*CONTRACT, kind, dividend_yield=DIVIDEND)
        for step in np.logspace(-1, -7, 13):
            estimates = numerical_greeks(
                *CONTRACT, kind, dividend_yield=DIVIDEND, relative_step=step
            )
            for greek, exact in reference.items():
                estimate = estimates[greek]
                rows.append(dict(
                    option=kind, greek=greek, relative_step=float(step),
                    analytical=exact, numerical=estimate, absolute_error=abs(estimate - exact),
                ))
    return rows


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_study(path, groups, x, y, *, title, xlabel, ylabel, scale, guide=False):
    figure = Figure(figsize=(8.4, 4.9), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots()
    colors = ("#005D8F", "#C84520", "#007E68", "#804E92", "#8D6120")
    for color, (label, rows) in zip(colors, groups.items()):
        # Exact zero errors are retained in CSV and omitted on log axes.
        points = [(row[x], row[y]) for row in rows if scale != "log" or row[y] > 0]
        if points:
            xs, ys = zip(*points)
            axes.plot(xs, ys, "o-", color=color, label=label, linewidth=1.5, markersize=4)
    if guide:
        first = next(iter(groups.values()))
        budgets = [row[x] for row in first]
        baseline = first[0][y]
        axes.plot(
            budgets, [baseline * (budgets[0] / n) ** 0.5 for n in budgets],
            "--", color="#66707B", label=r"$N^{-1/2}$ reference", linewidth=1.2,
        )
    axes.set(
        title=title, xlabel=xlabel, ylabel=ylabel, xscale="log", yscale=scale,
        axisbelow=True,
    )
    axes.spines[["top", "right"]].set_visible(False)
    axes.grid(alpha=0.25, which="major")
    axes.legend(frameon=False)
    figure.savefig(path, dpi=180, facecolor="white")


def run(output):
    """Write source tables, plots, and environment metadata to output."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    tree, sampling, greeks = tree_study(), sampling_study(), greek_study()
    for name, rows in (("tree", tree), ("monte_carlo", sampling), ("greeks", greeks)):
        write_csv(output / f"{name}.csv", rows)

    plot_study(
        output / "tree.png",
        {
            "Even steps": [r for r in tree if r["strike"] == 105 and r["steps"] % 2 == 0],
            "Odd steps": [r for r in tree if r["strike"] == 105 and r["steps"] % 2 == 1],
        },
        "steps", "absolute_error", title="CRR convergence for the 105-strike call",
        xlabel="Tree steps", ylabel="Absolute pricing error ($)", scale="log",
    )
    plot_study(
        output / "monte_carlo.png",
        {name: [r for r in sampling if r["method"] == name] for name in
         dict.fromkeys(r["method"] for r in sampling)},
        "budget", "rmse", title="Monte Carlo accuracy at equal payoff budgets",
        xlabel="Payoff evaluations (including pilot)", ylabel="Empirical RMSE ($)",
        scale="log", guide=True,
    )
    plot_study(
        output / "greeks.png",
        {name: [r for r in greeks if r["option"] == "call" and r["greek"] == name]
         for name in ("delta", "gamma", "theta", "vega", "rho")},
        "relative_step", "absolute_error", title="Call Greek finite-difference accuracy",
        xlabel="Relative bump", ylabel="Absolute error (in each Greek’s units)",
        scale="log",
    )
    (output / "environment.txt").write_text(
        f"Python {platform.python_version()}\nNumPy {np.__version__}\n"
        f"Matplotlib {matplotlib.__version__}\nSeed {SEED}\nReplications {REPLICATIONS}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    run(parser.parse_args().output)
