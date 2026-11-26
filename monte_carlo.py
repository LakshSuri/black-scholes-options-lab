"""Exact terminal sampling for European Black–Scholes–Merton payoffs."""

from dataclasses import dataclass
import math

import numpy as np

from pricing import (
    _discounted_values,
    _option_sign,
    _validate_contract,
    _validate_volatility,
    black_scholes_merton,
)


@dataclass(frozen=True)
class MonteCarloResult:
    price: float
    standard_error: float
    confidence_interval: tuple[float, float]
    paths: int
    independent_samples: int
    pilot_paths: int


def monte_carlo_price(
    stock, strike, time, rate, volatility, option_type="call", *,
    dividend_yield=0.0, paths=10_000, seed=None, antithetic=False,
    control_variate=False, pilot_paths=2_048,
):
    """Return an estimate and normal-approximation 95% confidence interval.

    paths counts production payoff evaluations. A control variate fits its
    coefficient on a separate pilot sample to preserve unbiasedness.
    """
    _validate_contract(stock, strike, time, rate, dividend_yield)
    _validate_volatility(volatility)
    sign = _option_sign(option_type)
    pair_size = 2 if antithetic else 1
    if type(paths) is not int or paths < 2 * pair_size or paths % pair_size:
        raise ValueError("paths must supply at least two complete observations.")
    if control_variate and (
        type(pilot_paths) is not int or pilot_paths < 2 * pair_size
        or pilot_paths % pair_size
    ):
        raise ValueError("pilot_paths must supply at least two complete observations.")

    sample_count = paths // pair_size
    if time == 0 or volatility == 0:
        price = black_scholes_merton(
            stock, strike, time, rate, volatility, option_type,
            dividend_yield=dividend_yield,
        )
        return MonteCarloResult(price, 0.0, (price, price), paths, sample_count, 0)

    spot_pv, strike_pv = _discounted_values(stock, strike, time, rate, dividend_yield)
    width = volatility * math.sqrt(time)
    log_location = math.log(stock) - dividend_yield * time - width * width / 2
    rng = np.random.default_rng(seed)

    def sample(count):
        shocks = rng.standard_normal(count)
        with np.errstate(over="raise", invalid="raise"):
            terminal = np.exp(log_location + width * shocks)
            payoff = np.maximum(sign * (terminal - strike_pv), 0.0)
            if antithetic:
                opposite = np.exp(log_location - width * shocks)
                opposite_payoff = np.maximum(sign * (opposite - strike_pv), 0.0)
                terminal = terminal / 2 + opposite / 2
                payoff = payoff / 2 + opposite_payoff / 2
        return payoff, terminal

    # Draw production observations first so a fixed seed gives paired comparisons.
    payoff, terminal = sample(sample_count)
    used_pilot = 0
    if control_variate:
        pilot_payoff, pilot_terminal = sample(pilot_paths // pair_size)
        centered = pilot_terminal - pilot_terminal.mean()
        sum_squares = np.dot(centered, centered)
        if sum_squares > 0:
            beta = np.dot(centered, pilot_payoff - pilot_payoff.mean()) / sum_squares
            payoff -= beta * (terminal - spot_pv)
        used_pilot = pilot_paths

    price = float(payoff.mean())
    standard_error = float(payoff.std(ddof=1) / math.sqrt(sample_count))
    margin = 1.959963984540054 * standard_error
    return MonteCarloResult(
        price, standard_error, (price - margin, price + margin),
        paths, sample_count, used_pilot,
    )
