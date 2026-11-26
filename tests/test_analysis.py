import pytest

from analysis import calculate_greeks
from pricing import black_scholes_call, black_scholes_put

BASE = (100, 100, 1, 0.05, 0.20)


def test_call_greeks_reference():
    expected = {
        "delta": 0.6368306512,
        "gamma": 0.01876201735,
        "theta": -0.01757267821,
        "vega": 0.3752403469,
        "rho": 0.5323248155,
    }
    assert calculate_greeks(*BASE) == pytest.approx(expected)


@pytest.mark.parametrize("stock", [70, 100, 130])
def test_greek_identities(stock):
    args = (stock, *BASE[1:])
    call = calculate_greeks(*args, "call")
    put = calculate_greeks(*args, "put")
    assert call["delta"] - put["delta"] == pytest.approx(1)
    assert call["gamma"] == pytest.approx(put["gamma"])
    assert call["vega"] == pytest.approx(put["vega"])


@pytest.mark.parametrize("kind,price", [
    ("call", black_scholes_call), ("put", black_scholes_put)
])
@pytest.mark.parametrize("stock", [80, 100, 120])
def test_finite_difference_greeks(kind, price, stock):
    args = [stock, *BASE[1:]]
    greeks = calculate_greeks(*args, option_type=kind)

    def shifted(index, shift):
        values = args.copy()
        values[index] += shift
        return price(*values)

    def derivative(index, h):
        return (shifted(index, h) - shifted(index, -h)) / (2*h)

    h = 0.01
    gamma = (shifted(0, h) - 2*price(*args) + shifted(0, -h)) / h**2
    assert greeks["delta"] == pytest.approx(derivative(0, h), abs=1e-6)
    assert greeks["gamma"] == pytest.approx(gamma, abs=1e-6)
    assert greeks["theta"] == pytest.approx(-derivative(2, 1e-4)/365, abs=1e-7)
    assert greeks["rho"] == pytest.approx(derivative(3, 1e-4)/100, abs=1e-6)
    assert greeks["vega"] == pytest.approx(derivative(4, 1e-4)/100, abs=1e-6)


def test_invalid_option_type():
    with pytest.raises(ValueError):
        calculate_greeks(*BASE, option_type="other")
