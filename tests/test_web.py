import numpy as np
import pandas as pd
import pytest

from pathlib import Path
from streamlit.testing.v1 import AppTest

from web.views import (
    overview,
    valuation,
    sensitivity,
    simulation,
    volatility,
    surfaces,
    library
)


ROOT = Path(__file__).resolve().parents[1]

PARAMETERS = {
    "stock_price": 100.0,
    "strike_price": 100.0,
    "time_to_expiration": 1.0,
    "risk_free_rate": 0.05,
    "volatility": 0.20,
    "dividend_yield": 0.02,
    "option_type": "call"
}

PAGES = {
    "Overview": "Derivatives Pricing Laboratory",
    "Option Valuation": "Option Valuation",
    "Sensitivity Analysis": "Sensitivity Analysis",
    "Monte Carlo Laboratory": "Monte Carlo Laboratory",
    "Implied Volatility": "Implied Volatility",
    "Pricing Surfaces": "Pricing Surfaces",
    "Research Library": "Research Library"
}

DATASET_ROWS = {
    "tree_convergence.csv": 128,
    "monte_carlo_summary.csv": 16,
    "monte_carlo_replications.csv": 1600,
    "greek_stability.csv": 390,
    "optimal_greek_steps.csv": 30,
    "volatility_conditioning.csv": 240,
    "benchmark_summary.csv": 20,
    "benchmark_replications.csv": 600
}

FIGURE_FILES = [
    "tree_convergence.png",
    "monte_carlo_convergence.png",
    "confidence_coverage.png",
    "greek_stability.png",
    "volatility_conditioning.png",
    "performance_benchmark.png"
]


def open_page(page):
    application = AppTest.from_file(
        str(ROOT / "app.py"),
        default_timeout=60
    ).run()

    assert not application.exception

    if page != "Overview":
        application.sidebar.radio[0].set_value(
            page
        ).run()

    assert not application.exception

    return application


def metric_value(application, label):
    for metric in application.metric:
        if metric.label == label:
            return metric.value

    raise AssertionError(
        f"Expected metric not found: {label}"
    )


# Application navigation and rendering


@pytest.mark.parametrize(
    "page,title",
    PAGES.items()
)
def test_workspace_navigation(page, title):
    application = open_page(page)

    assert application.title[0].value == title

    assert application.sidebar.radio[0].value == page


def test_overview_metrics():
    application = open_page("Overview")

    assert metric_value(
        application, "Recorded observations"
    ) == "2,958"

    assert metric_value(
        application, "RMSE reduction"
    ) == "79.9%"

    assert metric_value(
        application, "Empirical coverage"
    ) == "97%"


# Option valuation


@pytest.mark.parametrize(
    "option_type,expected",
    [
        ("call", 9.227005508),
        ("put", 6.330080628)
    ]
)
def test_analytical_valuation(option_type, expected):
    price = valuation.analytical_price(
        100, 100, 1, 0.05,
        0.20, 0.02, option_type
    )

    assert price == pytest.approx(
        expected, abs=1e-7
    )


@pytest.mark.parametrize(
    "option_type",
    ["call", "put"]
)
def test_american_exercise_premium(option_type):
    european = valuation.lattice_price(
        100, 100, 1, 0.05,
        0.20, 0.02, option_type,
        512, "european"
    )

    american = valuation.lattice_price(
        100, 100, 1, 0.05,
        0.20, 0.02, option_type,
        512, "american"
    )

    assert american >= european - 1e-10


def test_invalid_lattice_probability():
    with pytest.raises(ValueError):
        valuation.lattice_price(
            100, 100, 5, 0.15,
            0.05, 0.0, "call",
            32, "european"
        )


def test_valuation_convergence():
    data = valuation.convergence_data(
        100, 100, 1, 0.05,
        0.20, 0.02, "call"
    )

    assert len(data) == 12

    assert set(data["Parity"]) == {
        "Even", "Odd"
    }

    assert np.isfinite(
        data["Estimated value"]
    ).all()

    assert (
        data["Absolute error"] >= 0
    ).all()


# Analytical and numerical Greeks


@pytest.mark.parametrize(
    "option_type",
    ["call", "put"]
)
def test_greek_comparison(option_type):
    parameters = {
        **PARAMETERS,
        "option_type": option_type
    }

    data = sensitivity.comparison_data(
        parameters,
        0.001
    )

    assert len(data) == 5

    assert set(data["Greek"]) == {
        "Delta", "Gamma", "Theta", "Vega", "Rho"
    }

    assert (
        data["Absolute error"] < 1e-5
    ).all()


@pytest.mark.parametrize(
    "greek",
    ["delta", "gamma", "theta", "vega", "rho"]
)
def test_greek_stability(greek):
    data = sensitivity.stability_data(
        PARAMETERS,
        greek
    )

    assert len(data) == 13

    assert np.isfinite(
        data["Numerical"]
    ).all()

    assert (
        data["Absolute error"] >= 0
    ).all()


@pytest.mark.parametrize(
    "variable",
    [
        "Underlying price",
        "Volatility",
        "Time to expiration"
    ]
)
def test_sensitivity_curves(variable):
    data = sensitivity.sensitivity_data(
        PARAMETERS,
        "delta",
        variable
    )

    assert len(data) == 302

    assert set(data["Option type"]) == {
        "Call", "Put"
    }

    assert np.isfinite(
        data["Sensitivity"]
    ).all()


# Monte Carlo experiments


@pytest.mark.parametrize(
    "method",
    ["standard", "antithetic", "control", "combined"]
)
def test_simulation_reproducibility(method):
    reference = simulation.reference_price(
        PARAMETERS
    )

    first = simulation.evaluate_method(
        PARAMETERS, method, 4096,
        42, reference
    )

    second = simulation.evaluate_method(
        PARAMETERS, method, 4096,
        42, reference
    )

    assert first == second

    assert first["standard_error"] >= 0

    assert (
        first["lower_bound"]
        <= first["estimate"]
        <= first["upper_bound"]
    )

    assert (
        first["pilot_simulations"]
        + first["pricing_simulations"]
        == 4096
    )

    expected_samples = first["pricing_simulations"]

    if method in ("antithetic", "combined"):
        expected_samples //= 2

    assert (
        first["independent_samples"]
        == expected_samples
    )


def test_repeated_simulation_experiment():
    details, summary = simulation.repeated_experiment(
        PARAMETERS,
        3,
        42
    )

    assert len(details) == 48
    assert len(summary) == 16

    assert (
        summary["replications"] == 3
    ).all()

    assert (
        summary["rmse"] >= 0
    ).all()

    assert summary["coverage"].between(
        0, 1
    ).all()

    assert details["seed"].is_unique


# Implied volatility


@pytest.mark.parametrize(
    "option_type",
    ["call", "put"]
)
@pytest.mark.parametrize(
    "original_volatility",
    [0.10, 0.25, 0.60]
)
def test_volatility_recovery(
    option_type,
    original_volatility
):
    parameters = PARAMETERS.copy()

    parameters.pop("volatility")
    parameters["option_type"] = option_type

    price = volatility.model_price(
        parameters,
        original_volatility
    )

    recovered = volatility.recover_volatility(
        parameters,
        price
    )

    assert recovered == pytest.approx(
        original_volatility,
        abs=1e-8
    )


@pytest.mark.parametrize(
    "option_type",
    ["call", "put"]
)
def test_volatility_pricing_bounds(option_type):
    parameters = PARAMETERS.copy()

    parameters.pop("volatility")
    parameters["option_type"] = option_type

    lower, upper = volatility.pricing_bounds(
        parameters
    )

    for invalid_price in [
        lower - 1,
        lower,
        upper,
        upper + 1
    ]:
        with pytest.raises(ValueError):
            volatility.recover_volatility(
                parameters,
                invalid_price
            )


def test_volatility_perturbations():
    parameters = PARAMETERS.copy()

    parameters.pop("volatility")

    data = volatility.perturbation_data(
        parameters,
        0.25,
        0.10
    )

    assert len(data) == 21

    center = data.iloc[10]

    assert center["Status"] == "Success"

    assert center[
        "Recovered volatility (%)"
    ] == pytest.approx(
        25.0,
        abs=1e-6
    )


def test_recorded_conditioning_results():
    data = volatility.load_conditioning_data()

    counts = data["status"].value_counts()

    assert len(data) == 240
    assert counts.get("success", 0) == 208

    assert counts.get(
        "outside_pricing_bounds", 0
    ) == 32

    assert counts.get(
        "solver_failure", 0
    ) == 0


# Multidimensional pricing surfaces


@pytest.mark.parametrize(
    "measure",
    ["price", "delta", "gamma", "theta", "vega", "rho"]
)
@pytest.mark.parametrize(
    "axes",
    [
        ("stock_price", "volatility"),
        ("stock_price", "time_to_expiration"),
        ("volatility", "time_to_expiration")
    ]
)
@pytest.mark.parametrize(
    "option_type",
    ["call", "put"]
)
def test_surface_generation(
    measure,
    axes,
    option_type
):
    parameters = {
        **PARAMETERS,
        "option_type": option_type
    }

    x_variable, y_variable = axes

    x_values, y_values, z_values = (
        surfaces.generate_surface(
            parameters,
            measure,
            x_variable,
            y_variable,
            9
        )
    )

    assert len(x_values) == 9
    assert len(y_values) == 9

    assert z_values.shape == (9, 9)

    assert np.isfinite(z_values).all()

    for row, column in [
        (0, 0),
        (4, 4),
        (8, 8)
    ]:
        scenario = parameters.copy()

        scenario[x_variable] = float(
            x_values[column]
        )

        scenario[y_variable] = float(
            y_values[row]
        )

        expected = surfaces.evaluate(
            scenario,
            measure
        )

        assert z_values[row, column] == pytest.approx(
            expected
        )


def test_surface_export():
    x_values, y_values, z_values = (
        surfaces.generate_surface(
            PARAMETERS,
            "price",
            "stock_price",
            "volatility",
            9
        )
    )

    data = surfaces.export_data(
        PARAMETERS,
        "price",
        "stock_price",
        "volatility",
        x_values,
        y_values,
        z_values
    )

    assert len(data) == 81

    assert np.allclose(
        data["value"].to_numpy(),
        z_values.flatten()
    )


def test_surface_rejects_duplicate_axes():
    with pytest.raises(ValueError):
        surfaces.generate_surface(
            PARAMETERS,
            "price",
            "stock_price",
            "stock_price",
            9
        )


# Research archive integrity


@pytest.mark.parametrize(
    "filename,expected_rows",
    DATASET_ROWS.items()
)
def test_research_dataset(
    filename,
    expected_rows
):
    data = library.load_dataset(filename)

    assert len(data) == expected_rows

    assert len(data.columns) > 0

    assert not data.columns.duplicated().any()


@pytest.mark.parametrize(
    "filename",
    FIGURE_FILES
)
def test_research_figure(filename):
    path = library.FIGURE_DIRECTORY / filename

    assert path.is_file()

    with path.open("rb") as file:
        signature = file.read(8)

    assert signature == b"\x89PNG\r\n\x1a\n"


def test_archive_observation_count():
    observations = sum(
        len(library.load_dataset(filename))
        for filename in library.PRIMARY_DATASETS
    )

    assert observations == 2958

    assert len(library.DATASETS) == 8
    assert len(library.FIGURES) == 6


def test_recorded_seed_precision():
    data = library.load_dataset(
        "monte_carlo_replications.csv"
    )

    assert pd.api.types.is_string_dtype(
        data["seed"]
    )

    assert data["seed"].iloc[0] == (
        "16138347438539916964"
    )


def test_unknown_dataset_rejection():
    with pytest.raises(ValueError):
        library.load_dataset(
            "../environment.json"
        )


def test_recorded_environment():
    environment = library.load_environment()

    assert environment["python_version"] == "3.14.6"

    configuration = environment[
        "experiment_configuration"
    ]

    assert configuration["monte_carlo_seed"] == 42

    assert configuration[
        "monte_carlo_replications"
    ] == 100

    assert configuration[
        "benchmark_replications"
    ] == 30


def test_technical_report():
    report = library.REPORT_PATH.read_text(
        encoding="utf-8"
    )

    assert "## Abstract" in report

    assert "## 6. Reproducibility" in report

    assert "## 7. Limitations" in report

    for filename in FIGURE_FILES:
        assert filename in report


def test_recorded_convergence():
    data = overview.load_convergence_data()

    assert len(data) == 16

    assert set(data["method"]) == {
        "standard",
        "antithetic",
        "control",
        "combined"
    }

    combined = data[
        (data["method"] == "combined")
        & (data["budget"] == 65536)
    ].iloc[0]

    assert combined["rmse"] == pytest.approx(
        0.01365672453138423
    )

    assert combined["coverage"] == pytest.approx(
        0.97
    )