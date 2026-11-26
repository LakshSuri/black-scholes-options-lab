# Derivatives Pricing Laboratory

A computational finance framework for derivatives valuation, numerical approximation, statistical simulation, sensitivity analysis, and reproducible mathematical research.

The project investigates the accuracy, convergence, numerical stability, and computational efficiency of established option pricing methods under controlled market assumptions.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Tests](https://img.shields.io/badge/Local%20Tests-186%20Passed-brightgreen)
![Research](https://img.shields.io/badge/Research-5%20Computational%20Studies-blue)
![CI](https://github.com/LakshSuri/black-scholes-options-lab/actions/workflows/tests.yml/badge.svg)

## Project Overview

The laboratory integrates analytical, numerical, and stochastic methods for European and American option valuation.

Its research component examines the trade-offs between computational cost, approximation accuracy, statistical uncertainty, and numerical stability.

| Project Component | Total |
|---|---:|
| Pricing implementations | 6 |
| Monte Carlo estimators | 4 |
| Option Greeks | 5 |
| Interactive visualizations | 8 |
| Computational research studies | 5 |
| Experimental observations | 2,958 |
| Research datasets | 8 |
| Research figures | 6 |
| Locally passing automated tests | 186 |

## Mathematical Capabilities

### Analytical Pricing

- Dividend-adjusted Black-Scholes-Merton model
- European call and put valuation
- Put-call parity verification
- Analytical Greek calculations
- Volatility and expiration sensitivity analysis

### Numerical Pricing

- Cox-Ross-Rubinstein binomial trees
- European and American exercise styles
- Early-exercise premium estimation
- Implied volatility recovery through bisection
- Central finite-difference sensitivity calculations

### Monte Carlo Simulation

- Standard Monte Carlo
- Antithetic variates
- Control variates
- Combined variance reduction
- Independent pilot sample estimation
- Standard error calculations
- Approximate 95% confidence intervals
- Reproducible random sampling

## Selected Research Findings

### Binomial Convergence

The binomial convergence study evaluates four strike prices, two option types, and sixteen tree resolutions.

The results illustrate that increasing tree resolution does not necessarily produce monotonic reductions in pricing error.

![Binomial convergence](results/figures/tree_convergence.png)

### Monte Carlo Convergence

The Monte Carlo study compares four estimators across four simulation budgets using 100 replications per configuration.

At a budget of 65,536 simulations, the following RMSE values were observed:

| Estimator | RMSE | Relative Efficiency |
|---|---:|---:|
| Standard | 0.068021 | 1.00 |
| Antithetic | 0.050569 | 1.81 |
| Control | 0.028845 | 5.56 |
| Combined | 0.013657 | 24.81 |

Under the selected experimental conditions, combining antithetic and control variates reduced RMSE by approximately 79.9% relative to standard Monte Carlo.

![Monte Carlo convergence](results/figures/monte_carlo_convergence.png)

### Statistical Confidence

Empirical confidence interval coverage is evaluated against the nominal 95% confidence level.

At the largest simulation budget, observed coverage ranged from 94% to 98% across the four estimators.

![Confidence interval coverage](results/figures/confidence_coverage.png)

### Numerical Stability

Finite-difference calculations are evaluated across thirteen relative step sizes and six scenario and option-type combinations.

| Greek | Best Observed Relative Step |
|---|---|
| Delta | 1e-7 to 1e-6 |
| Gamma | 1e-4 |
| Theta | 1e-5 |
| Vega | 1e-6 to 1e-5 |
| Rho | 1e-5 to 1e-3 |

The results illustrate the interaction between truncation error and floating-point cancellation.

These values represent empirical minima within the tested grid rather than universal optimal step sizes.

![Numerical stability](results/figures/greek_stability.png)

### Implied Volatility Conditioning

The implied volatility study evaluates the sensitivity of volatility recovery to perturbations in theoretical option prices.

| Experimental Outcome | Observations |
|---|---:|
| Successful recoveries | 208 |
| Outside pricing bounds | 32 |
| Solver failures | 0 |

Low Vega increases the local sensitivity of implied volatility to changes in observed option prices.

![Volatility conditioning](results/figures/volatility_conditioning.png)

### Computational Benchmarking

Twenty pricing configurations were evaluated using thirty measured executions per configuration.

| Model | Resolution | Median Runtime (ms) | RMSE |
|---|---:|---:|---:|
| Black-Scholes | Analytical | 0.001167 | 0 |
| CRR Binomial | 1,024 | 2.086354 | 0.000449 |
| Standard Monte Carlo | 65,536 | 0.933958 | 0.056573 |
| Antithetic | 65,536 | 0.755375 | 0.052959 |
| Control | 65,536 | 0.920001 | 0.027772 |
| Combined | 65,536 | 0.794209 | 0.013368 |

Black-Scholes serves as the analytical reference and therefore has zero measured approximation error by construction.

Runtime measurements depend on hardware and software conditions.

![Computational performance](results/figures/performance_benchmark.png)

## Project Architecture

```text
black-scholes-options-lab/
|
|-- main.py
|-- pricing.py
|-- analysis.py
|-- implied_volatility.py
|-- lattice.py
|-- monte_carlo.py
|-- numerical_greeks.py
|-- visualization.py
|-- experiments.py
|
|-- research/
|   |-- numerical_stability.py
|   |-- volatility_conditioning.py
|   |-- benchmarks.py
|   |-- figures.py
|   |-- environment.py
|   |-- reproduce.py
|   |-- technical_report.md
|
|-- results/
|   |-- data/
|   |-- figures/
|   |-- environment.json
|
|-- tests/
|-- .github/workflows/
|-- requirements.txt
|-- README.md
```

## Installation

Python 3.14 is the primary development environment.

Clone the repository:

```bash
git clone https://github.com/LakshSuri/black-scholes-options-lab.git
cd black-scholes-options-lab
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

The application provides thirteen analytical and computational features.

```text
Analytical Pricing

[1] European Call Pricing
[2] European Put Pricing
[3] Call and Put Comparison
[4] Analytical Greeks

Sensitivity Analysis

[5] Volatility Sensitivity
[6] Expiration Sensitivity
[7] Interactive Visualizations
[8] Put-Call Parity Verification

Computational Finance

[9] Implied Volatility Solver
[10] European and American Binomial Pricing
[11] Monte Carlo Pricing
[12] Pricing Model Comparison
[13] Numerical Greeks Validation

[14] Exit Program
```

## Python Usage

The mathematical engines can also be imported directly into other Python programs.

### Black-Scholes-Merton Pricing

```python
from pricing import black_scholes_call

price = black_scholes_call(
    100, 105, 1, 0.05, 0.25,
    dividend_yield=0.02
)

print(price)
```

Expected result:

```text
8.941175726631428
```

### American Option Pricing

```python
from lattice import crr_price

price = crr_price(
    100, 105, 1, 0.05, 0.25,
    steps=1024,
    option_type="put",
    exercise_style="american",
    dividend_yield=0.02
)

print(price)
```

### Monte Carlo Variance Reduction

```python
from monte_carlo import monte_carlo_price

result = monte_carlo_price(
    100, 105, 1, 0.05, 0.25,
    simulations=65536,
    option_type="call",
    dividend_yield=0.02,
    seed=42,
    method="combined"
)

print(result["price"])
print(result["standard_error"])
print(result["confidence_interval"])
```

## Research Reproducibility

Reproduce all computational experiments and figures using:

```bash
python -m research.reproduce
```

Regenerated datasets, figures, and environment metadata are stored in a separate reproduced-results directory.

Original experimental results remain available in the results directory.

Random seeds and dependency versions are recorded to support reproducibility. Runtime measurements and floating-point results may vary between environments.

## Software Validation

Run the complete automated test suite:

```bash
python -m pytest -q
```

The current local validation contains 186 passing tests covering mathematical consistency, pricing accuracy, numerical convergence, input validation, stochastic reproducibility, statistical estimators, and research infrastructure.

Continuous integration is configured through GitHub Actions.

## Technical Research Report

The complete mathematical framework, experimental methodology, results, limitations, and academic references are documented in the technical report:

[Computational Analysis of Derivatives Pricing Models](research/technical_report.md)

## Technologies

- Python
- NumPy
- Matplotlib
- Pytest
- Git
- GitHub Actions

## Limitations

The models assume simplified financial market dynamics, including constant volatility, interest rates, and dividend yields.

The experiments use synthetic market configurations rather than observed historical option prices. Results evaluate numerical performance under the specified mathematical assumptions and should not be interpreted as evidence of trading profitability.

## Future Development

- Stochastic volatility models
- Heston model calibration
- Implied volatility surfaces
- Quasi-Monte Carlo methods
- Jump-diffusion processes
- Historical option chain analysis
- Advanced American option pricing
- Integration with a broader quantitative research platform

## Development Transparency

This educational project was developed with substantial ChatGPT coding assistance and technical guidance.

The repository owner executed the computational experiments and automated tests locally and managed the development repository.

The project investigates established mathematical methods through reproducible computational experiments.

## Author

Laksh Suri

Quantitative finance, computational mathematics, and software development.

This project is intended for educational and computational research purposes.