import math

import pytest

import main
import visualization

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks


MARKET = ["100", "105", "1", "5", "25", "2"]

PARAMETERS = (100, 105, 1, 0.05, 0.25, 0.02)


def run_session(monkeypatch, capsys, commands):
    responses = iter(commands)

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(responses)
    )

    main.main()

    return capsys.readouterr().out


@pytest.mark.parametrize(
    "choice,inputs,expected",
    [
        ("1", MARKET, "8.941176"),
        ("2", MARKET, "Theoretical put price"),
        ("3", MARKET, "Call minus put"),
        ("4", MARKET + ["call"], "Gamma"),
        ("5", MARKET, "25.00%"),
        ("6", MARKET, "1.0000"),
        ("8", MARKET, "Put-call parity successfully verified"),
        (
            "9",
            ["100", "105", "1", "5", "2", "call",
             "8.941175726631428"],
            "25.000000%"
        ),
        (
            "10",
            MARKET + ["call", "european", "1024"],
            "Absolute pricing error"
        ),
        (
            "10",
            MARKET + ["put", "american", "1024"],
            "Estimated early-exercise premium"
        ),
        (
            "11",
            MARKET + ["call", "1024", "standard"],
            "Approximate 95% CI"
        ),
        (
            "11",
            MARKET + ["call", "1024", "antithetic"],
            "Approximate 95% CI"
        ),
        (
            "11",
            MARKET + ["call", "1024", "control"],
            "Approximate 95% CI"
        ),
        (
            "11",
            MARKET + ["call", "1024", "combined"],
            "Approximate 95% CI"
        ),
        (
            "12",
            MARKET + ["call", "1024", "65536"],
            "8.94117573"
        ),
        (
            "13",
            MARKET + ["call"],
            "Relative finite-difference step"
        )
    ]
)
def test_application_features(
    monkeypatch, capsys, choice, inputs, expected
):
    output = run_session(
        monkeypatch,
        capsys,
        [choice, *inputs, "14"]
    )

    assert expected in output
    assert "Calculation error" not in output
    assert "Laboratory closed" in output


@pytest.mark.parametrize(
    "choice",
    ["1", "2", "3", "4", "5", "6", "7", "8"]
)
def test_visualization_data(
    monkeypatch, capsys, choice
):
    captured = []

    def capture_curves(*args):
        captured.append(args)

    monkeypatch.setattr(
        visualization,
        "plot_curves",
        capture_curves
    )

    output = run_session(
        monkeypatch,
        capsys,
        ["7", choice, *MARKET, "9", "14"]
    )

    assert "Calculation error" not in output
    assert len(captured) == 1

    x_values, calls, puts = captured[0][:3]

    assert len(x_values) == 100
    assert len(calls) == 100
    assert len(puts) == 100

    assert all(math.isfinite(x) for x in calls)
    assert all(math.isfinite(x) for x in puts)

    stock, strike, time, rate, vol, dividend = PARAMETERS

    if choice == "1":
        stock = x_values[0]

    elif choice == "2":
        vol = x_values[0] / 100

    elif choice == "3":
        time = x_values[0]

    else:
        stock = x_values[0]

        greek = {
            "4": "delta",
            "5": "gamma",
            "6": "theta",
            "7": "vega",
            "8": "rho"
        }[choice]

        expected_call = calculate_greeks(
            stock, strike, time, rate, vol,
            "call", dividend
        )[greek]

        expected_put = calculate_greeks(
            stock, strike, time, rate, vol,
            "put", dividend
        )[greek]

        assert calls[0] == pytest.approx(expected_call)
        assert puts[0] == pytest.approx(expected_put)

        return

    expected_call = black_scholes_call(
        stock, strike, time, rate, vol, dividend
    )

    expected_put = black_scholes_put(
        stock, strike, time, rate, vol, dividend
    )

    assert calls[0] == pytest.approx(expected_call)
    assert puts[0] == pytest.approx(expected_put)


def test_invalid_input_recovery(monkeypatch, capsys):
    output = run_session(
        monkeypatch,
        capsys,
        [
            "99",
            "1",
            "invalid",
            "nan",
            "-100",
            *MARKET,
            "14"
        ]
    )

    assert "Invalid selection" in output
    assert "Please enter a valid number" in output
    assert "Please enter a finite number" in output
    assert "Please enter a positive number" in output
    assert "8.941176" in output
    assert "Laboratory closed" in output


def test_invalid_option_price_recovery(
    monkeypatch, capsys
):
    output = run_session(
        monkeypatch,
        capsys,
        [
            "9",
            "100", "105", "1", "5", "2",
            "call", "1000",
            "14"
        ]
    )

    assert "Calculation error" in output
    assert "Laboratory closed" in output