import math
import numpy as np
import pytest

from monte_carlo import monte_carlo_price
from pricing import black_scholes_call, black_scholes_put


METHODS = [
    "standard",
    "antithetic",
    "control",
    "combined"
]


@pytest.mark.parametrize("method", METHODS)
def test_reproducibility(method):
    first = monte_carlo_price(
        100, 100, 1, 0.05, 0.20,
        simulations=8192,
        seed=42,
        method=method
    )

    second = monte_carlo_price(
        100, 100, 1, 0.05, 0.20,
        simulations=8192,
        seed=42,
        method=method
    )

    assert first == second


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("option_type", ["call", "put"])
def test_pricing_accuracy(method, option_type):
    pricing_function = (
        black_scholes_call if option_type == "call"
        else black_scholes_put
    )

    reference = pricing_function(
        100, 105, 1, 0.05, 0.25, 0.02
    )

    result = monte_carlo_price(
        100, 105, 1, 0.05, 0.25,
        simulations=65536,
        option_type=option_type,
        dividend_yield=0.02,
        seed=1234,
        method=method
    )

    error = abs(result["price"] - reference)

    assert error <= 5 * result["standard_error"] + 1e-10


@pytest.mark.parametrize("method", METHODS)
def test_computational_budget(method):
    result = monte_carlo_price(
        100, 100, 1, 0.05, 0.20,
        simulations=8192,
        seed=42,
        method=method
    )

    assert result["simulations"] == 8192

    assert (
        result["pilot_simulations"]
        + result["pricing_simulations"]
        == result["simulations"]
    )

    if method in ("antithetic", "combined"):
        assert result["independent_samples"] == (
            result["pricing_simulations"] // 2
        )
    else:
        assert result["independent_samples"] == (
            result["pricing_simulations"]
        )

    if method in ("control", "combined"):
        assert result["pilot_simulations"] > 0
    else:
        assert result["pilot_simulations"] == 0


@pytest.mark.parametrize("method", METHODS)
def test_statistical_consistency(method):
    result = monte_carlo_price(
        100, 100, 1, 0.05, 0.20,
        simulations=8192,
        seed=42,
        method=method
    )

    expected_error = (
        result["standard_deviation"]
        / math.sqrt(result["independent_samples"])
    )

    assert result["standard_error"] == pytest.approx(
        expected_error
    )

    lower, upper = result["confidence_interval"]

    margin = 1.95996398454 * expected_error

    assert lower == pytest.approx(
        result["price"] - margin
    )

    assert upper == pytest.approx(
        result["price"] + margin
    )

    assert math.isfinite(result["price"])
    assert result["standard_error"] > 0


def test_antithetic_pair_statistics():
    simulations = 8192
    seed = 42

    rng = np.random.default_rng(seed)
    shocks = rng.standard_normal(simulations // 2)

    drift = 0.05 - 0.5 * 0.20 ** 2

    positive = 100 * np.exp(
        drift + 0.20 * shocks
    )

    negative = 100 * np.exp(
        drift - 0.20 * shocks
    )

    pairs = math.exp(-0.05) * (
        np.maximum(positive - 100, 0)
        + np.maximum(negative - 100, 0)
    ) / 2

    expected_price = np.mean(pairs)

    expected_error = (
        np.std(pairs, ddof=1)
        / math.sqrt(len(pairs))
    )

    result = monte_carlo_price(
        100, 100, 1, 0.05, 0.20,
        simulations=simulations,
        seed=seed,
        method="antithetic"
    )

    assert result["price"] == pytest.approx(expected_price)

    assert result["standard_error"] == pytest.approx(
        expected_error
    )


@pytest.mark.parametrize("parameters", [
    {"simulations": 1},
    {"simulations": 1.5},
    {"simulations": True},
    {"option_type": "invalid"},
    {"method": "invalid"},
    {"method": "antithetic", "simulations": 5},
    {"method": "combined", "simulations": 6},
    {"method": "control", "pilot_simulations": 1},
    {"method": "control", "pilot_simulations": 100},
    {"method": "combined", "pilot_simulations": 5},
    {"method": "standard", "pilot_simulations": 10},
    {"method": "control", "pilot_simulations": 2.5}
])
def test_invalid_simulation_parameters(parameters):
    arguments = {"simulations": 100}
    arguments.update(parameters)

    with pytest.raises(ValueError):
        monte_carlo_price(
            100, 100, 1, 0.05, 0.20,
            **arguments
        )
