# Derivatives pricing

How closely do a binomial tree, a volatility solver, and finite-difference Greeks reproduce known Black–Scholes–Merton values?

From the repository root, install `requirements-dev.txt` and run `python -m research.derivatives.study --output /tmp/derivatives`. The three CSV files contain tree errors for four strikes, implied volatilities for calls and puts at three strikes, and Greek errors across thirteen bump sizes.

For the 105-strike call the tree's absolute error falls from $0.1310 at 16 steps to $0.001013 at 2,048 steps. The volatility solver recovers the 24% input to within 0.00000001 percentage points in all six cases. The gamma comparison shows why smaller bumps eventually hurt accuracy when rounding dominates. All comparisons use European exercise and constant model parameters.
