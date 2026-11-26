import csv
import json
import math

import pytest

from experiments import (
    write_csv,
    tree_convergence_study,
    monte_carlo_study
)

from research.numerical_stability import (
    greek_stability_study,
    optimal_step_study
)

from research.volatility_conditioning import (
    volatility_conditioning_study
)

from research.benchmarks import benchmark_study
from research.environment import save_environment


@pytest.fixture(scope="module")
def tree_results():
    return tree_convergence_study()


@pytest.fixture(scope="module")
def stability_results():
    return greek_stability_study()


@pytest.fixture(scope="module")
def conditioning_results():
    return volatility_conditioning_study()


def test_tree_dataset_structure(tree_results):
    assert len(tree_results) == 128

    configurations = {
        (
            row["option_type"],
            row["strike"],
            row["steps"]
        )
        for row in tree_results
    }

    assert len(configurations) == 128

    for row in tree_results:
        assert math.isfinite(row["estimated_price"])

        assert row["absolute_error"] == pytest.approx(
            abs(row["signed_error"])
        )


def test_monte_carlo_dataset_structure():
    summary, detailed = monte_carlo_study(
        replications=4
    )

    assert len(summary) == 16
    assert len(detailed) == 64

    for row in summary:
        assert row["rmse"] >= 0
        assert row["mean_standard_error"] >= 0
        assert 0 <= row["coverage"] <= 1

        assert row["relative_efficiency"] > 0

        if row["method"] == "standard":
            assert row["relative_efficiency"] == 1


def test_monte_carlo_reproducibility():
    first_summary, first_details = monte_carlo_study(
        replications=4,
        seed=123
    )

    second_summary, second_details = monte_carlo_study(
        replications=4,
        seed=123
    )

    for first, second in zip(
        first_summary, second_summary
    ):
        first = {
            key: value for key, value in first.items()
            if key != "mean_runtime_seconds"
        }

        second = {
            key: value for key, value in second.items()
            if key != "mean_runtime_seconds"
        }

        assert first == second

    for first, second in zip(
        first_details, second_details
    ):
        first = {
            key: value for key, value in first.items()
            if key != "runtime_seconds"
        }

        second = {
            key: value for key, value in second.items()
            if key != "runtime_seconds"
        }

        assert first == second


def test_numerical_stability_dataset(stability_results):
    assert len(stability_results) == 390

    for row in stability_results:
        assert row["relative_step"] > 0

        assert math.isfinite(
            row["absolute_error"]
        )

        assert row["absolute_error"] >= 0


def test_optimal_step_selection(stability_results):
    summary = optimal_step_study(stability_results)

    assert len(summary) == 30

    for row in summary:
        matching = [
            observation
            for observation in stability_results
            if observation["scenario"] == row["scenario"]
            and observation["option_type"] == row["option_type"]
            and observation["greek"] == row["greek"]
        ]

        minimum_error = min(
            observation["absolute_error"]
            for observation in matching
        )

        assert row["minimum_absolute_error"] == minimum_error


def test_volatility_conditioning(conditioning_results):
    assert len(conditioning_results) == 240

    allowed_statuses = {
        "success",
        "outside_pricing_bounds",
        "solver_failure"
    }

    for row in conditioning_results:
        assert row["status"] in allowed_statuses

        if row["status"] == "success":
            assert math.isfinite(
                row["recovered_volatility"]
            )

            assert row["recovered_volatility"] > 0

            assert row["absolute_volatility_error"] >= 0

        else:
            assert row["recovered_volatility"] is None


def test_benchmark_dataset():
    summary, detailed = benchmark_study(
        replications=2
    )

    assert len(summary) == 20
    assert len(detailed) == 40

    for row in summary:
        assert row["median_runtime_ms"] >= 0
        assert row["rmse"] >= 0

        if row["model"] == "black_scholes":
            assert row["rmse"] == 0


def test_csv_export(tmp_path):
    path = tmp_path / "test_results.csv"

    rows = [
        {"model": "standard", "price": 10.5},
        {"model": "combined", "price": 10.4}
    ]

    write_csv(path, rows)

    with path.open(encoding="utf-8") as file:
        exported = list(csv.DictReader(file))

    assert len(exported) == 2
    assert exported[0]["model"] == "standard"
    assert float(exported[0]["price"]) == 10.5


def test_empty_csv_rejected(tmp_path):
    with pytest.raises(ValueError):
        write_csv(tmp_path / "empty.csv", [])


def test_environment_metadata(tmp_path):
    path = tmp_path / "environment.json"

    metadata = save_environment(path)

    with path.open(encoding="utf-8") as file:
        saved = json.load(file)

    assert saved == metadata

    assert saved["python_version"]
    assert saved["dependencies"]["numpy"]
    assert saved["dependencies"]["matplotlib"]

    assert saved["experiment_configuration"][
        "monte_carlo_seed"
    ] == 42


def test_research_figure_generation(
    tmp_path,
    tree_results,
    stability_results,
    conditioning_results
):
    from research.figures import run

    data = tmp_path / "data"
    figures = tmp_path / "figures"

    mc_summary, _ = monte_carlo_study(
        replications=4
    )

    benchmark_summary, _ = benchmark_study(
        replications=2
    )

    write_csv(
        data / "tree_convergence.csv",
        tree_results
    )

    write_csv(
        data / "monte_carlo_summary.csv",
        mc_summary
    )

    write_csv(
        data / "greek_stability.csv",
        stability_results
    )

    write_csv(
        data / "volatility_conditioning.csv",
        conditioning_results
    )

    write_csv(
        data / "benchmark_summary.csv",
        benchmark_summary
    )

    run(data, figures)

    expected = {
        "tree_convergence.png",
        "monte_carlo_convergence.png",
        "confidence_coverage.png",
        "greek_stability.png",
        "volatility_conditioning.png",
        "performance_benchmark.png"
    }

    assert {
        path.name for path in figures.glob("*.png")
    } == expected

    for path in figures.glob("*.png"):
        assert path.stat().st_size > 0

        with path.open("rb") as file:
            assert file.read(8) == b"\x89PNG\r\n\x1a\n"
