"""Reproduce the tree, implied volatility, and Greek comparisons."""

import argparse
from pathlib import Path

from experiments import greek_study, tree_study, write_csv
from implied_volatility import implied_volatility
from pricing import black_scholes_merton


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "tree.csv", tree_study())
    write_csv(output / "greeks.csv", greek_study())
    rows = []
    for strike in (85, 100, 120):
        for kind in ("call", "put"):
            vol = 0.24
            price = black_scholes_merton(100, strike, 1, 0.04, vol, kind, dividend_yield=0.02)
            recovered = implied_volatility(price, 100, strike, 1, 0.04, kind, dividend_yield=0.02)
            rows.append(dict(strike=strike, option=kind, price=price, input_vol=vol,
                             recovered_vol=recovered, absolute_error=abs(recovered - vol)))
    write_csv(output / "volatility.csv", rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
