# Derivatives Pricing Laboratory

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Continuous Integration](https://github.com/LakshSuri/black-scholes-options-lab/actions/workflows/tests.yml/badge.svg)

A computational finance laboratory for derivatives pricing, numerical approximation, statistical simulation, and sensitivity analysis.

This project investigates the accuracy, convergence, numerical stability, and computational efficiency of established option pricing methods through reproducible computational experiments.

## Overview

The laboratory combines analytical pricing, lattice-based numerical methods, Monte Carlo simulation, variance reduction, implied volatility estimation, and numerical differentiation within a modular Python framework.

| Component | Current Status |
|---|---:|
| Pricing implementations | 6 |
| Monte Carlo estimators | 4 |
| Option Greeks | 5 |
| Interactive analytical features | 13 |
| Interactive visualization types | 8 |
| Computational studies | 5 |
| Experimental observations | 2,958 |
| Published CSV datasets | 8 |
| Research figures | 6 |
| Locally passing automated tests | 186 |

## Contents

- Mathematical Framework
- Research Findings
- Project Architecture
- Installation
- Interactive Application
- Python Examples
- Research Reproducibility
- Software Validation
- Technical Documentation
- Limitations
- References
- Future Development

## Mathematical Framework

### Analytical Option Pricing

The Black-Scholes-Merton implementation supports European call and put valuation with continuous dividend yields.

Features include:

- European call and put pricing.
- Dividend-adjusted valuation.
- Put-call parity verification.
- Analytical option Greeks.
- Volatility sensitivity analysis.
- Time-to-expiration sensitivity analysis.

The dividend-adjusted European call pricing equation is

$$
C=Se^{-qT}N(d_1)-Ke^{-rT}N(d_2)
$$

where

$$
d_1=\frac{\ln(S/K)+(r-q+\sigma^2/2)T}{\sigma\sqrt{T}}
$$

$$
d_2=d_1-\sigma\sqrt{T}
$$

Here, S represents the underlying asset price, K represents the strike price, T represents time to expiration, r represents the risk-free rate, q represents the continuous dividend yield, and sigma represents annualized volatility.

### Binomial Option Pricing

The Cox-Ross-Rubinstein model approximates asset price movements using a recombining binomial tree.

The implementation supports:

- European call and put options.
- American call and put options.
- Continuous dividend yields.
- Risk-neutral probability calculations.
- Backward induction.
- Early-exercise premium estimation.
- Adjustable tree resolution.

American option valuation compares continuation value against immediate exercise value at each applicable tree node.

### Monte Carlo Simulation

The Monte Carlo engine models terminal asset prices under risk-neutral geometric Brownian motion.

Four estimators are implemented:

| Estimator | Methodology |
|---|---|
| Standard | Independent random sampling |
| Antithetic | Paired positive and negative random shocks |
| Control variate | Adjustment using a control with known expectation |
| Combined | Antithetic sampling with control variates |

The engine also provides:

- Fixed-seed reproducibility.
- Independent pilot sample estimation.
- Standard deviation calculations.
- Standard error calculations.
- Approximate 95% confidence intervals.
- Simulation budget accounting.

Pilot evaluations are included in the total simulation budget.

### Implied Volatility

The implied volatility solver uses an expanding search bracket followed by bisection to recover volatility from a European option price.

The implementation validates theoretical pricing bounds before attempting numerical inversion.

### Option Greeks

Both analytical and numerical implementations are available for five option sensitivities.

| Greek | Sensitivity |
|---|---|
| Delta | Underlying asset price |
| Gamma | Rate of change of Delta |
| Theta | Passage of calendar time |
| Vega | Implied model volatility |
| Rho | Risk-free interest rate |

The numerical implementation uses central finite differences.

Theta is reported per calendar day. Vega and Rho are reported per percentage-point change in their respective parameters.

## Research Findings

Five computational studies investigate numerical accuracy, statistical uncertainty, model convergence, and execution time.

| Study | Observations |
|---|---:|
| Binomial convergence | 128 |
| Monte Carlo convergence | 1,600 |
| Numerical Greek stability | 390 |
| Implied volatility conditioning | 240 |
| Computational benchmarking | 600 |
| Total | 2,958 |

The total excludes summary datasets and does not imply that every observation is statistically independent.

### 1. Binomial Convergence

The binomial convergence experiment evaluates four strike prices, two option types, and sixteen tree resolutions ranging from 16 to 2,049 steps.

Consecutive even and odd resolutions are included to investigate oscillatory convergence.

For a European call with a strike price of 80, the following signed pricing errors were observed:

| Tree Steps | Signed Pricing Error |
|---:|---:|
| 16 | -0.002995 |
| 17 | 0.005047 |
| 32 | -0.009224 |
| 33 | 0.010221 |
| 64 | 0.007758 |

The results demonstrate that increasing tree resolution does not necessarily reduce pricing error monotonically.

![CRR binomial convergence](results/figures/tree_convergence.png)

Dataset: [Tree convergence results](results/data/tree_convergence.csv)

### 2. Monte Carlo Convergence and Variance Reduction

Four Monte Carlo estimators were evaluated across four simulation budgets using 100 replications per configuration.

The reference configuration uses:

| Parameter | Value |
|---|---:|
| Underlying asset price | $100 |
| Strike price | $105 |
| Time to expiration | 1 year |
| Risk-free rate | 5% |
| Annualized volatility | 25% |
| Continuous dividend yield | 2% |
| Option type | European call |
| Analytical reference price | $8.941176 |

The experiment produced the following root mean squared errors:

| Simulation Budget | Standard | Antithetic | Control | Combined |
|---:|---:|---:|---:|---:|
| 1,024 | 0.516336 | 0.359410 | 0.239647 | 0.109060 |
| 4,096 | 0.223915 | 0.192989 | 0.115875 | 0.056191 |
| 16,384 | 0.121932 | 0.097804 | 0.060858 | 0.025163 |
| 65,536 | 0.068021 | 0.050569 | 0.028845 | 0.013657 |

The combined estimator achieved the lowest measured RMSE at every tested simulation budget.

At the largest budget, combining antithetic and control variates reduced RMSE by approximately 79.9% relative to standard Monte Carlo.

The corresponding empirical mean squared error ratio was approximately 24.81.

These findings apply to the selected experimental configuration and should not be interpreted as universal performance guarantees.

![Monte Carlo convergence](results/figures/monte_carlo_convergence.png)

Datasets:

- [Monte Carlo summary](results/data/monte_carlo_summary.csv)
- [Monte Carlo replications](results/data/monte_carlo_replications.csv)

#### Confidence Interval Coverage

The observed confidence interval coverage at a simulation budget of 65,536 was:

| Estimator | Empirical Coverage | Relative MSE Efficiency |
|---|---:|---:|
| Standard | 94% | 1.00 |
| Antithetic | 98% | 1.81 |
| Control | 97% | 5.56 |
| Combined | 97% | 24.81 |

The coverage estimates are broadly consistent with the nominal 95% confidence level, although the number of replications limits their statistical precision.

Relative efficiency measures the ratio of empirical mean squared errors at equal simulation budgets, not a direct execution-time speedup.

![Confidence interval coverage](results/figures/confidence_coverage.png)

### 3. Numerical Greek Stability

The numerical differentiation study evaluates thirteen relative step sizes across three market scenarios, two option types, and five Greeks.

The experiment examines the competing effects of truncation error and floating-point cancellation.

| Greek | Best Observed Relative Step Sizes |
|---|---|
| Delta | 1e-7 to 1e-6 |
| Gamma | 1e-4 |
| Theta | 1e-5 |
| Vega | 1e-6 to 1e-5 |
| Rho | 1e-5 to 1e-3 |

Gamma achieved its minimum observed numerical error at a relative step size of 1e-4 in all six tested scenario and option-type combinations.

The reported step sizes represent empirical minima within the tested grid rather than universally optimal numerical parameters.

![Finite-difference numerical stability](results/figures/greek_stability.png)

Datasets:

- [Greek stability results](results/data/greek_stability.csv)
- [Best observed Greek step sizes](results/data/optimal_greek_steps.csv)

### 4. Implied Volatility Conditioning

The implied volatility study evaluates how perturbations in theoretical option prices affect recovered volatility.

The experiment examines five strike prices, four expiration periods, two option types, and six price perturbations.

| Outcome | Observations |
|---|---:|
| Successful numerical recoveries | 208 |
| Outside theoretical pricing bounds | 32 |
| Solver failures | 0 |
| Total | 240 |

Local implied volatility sensitivity is inversely related to Vega:

$$
\frac{\partial \sigma}{\partial V}
=
\frac{1}{\partial V/\partial \sigma}
$$

Consequently, options with low Vega may exhibit substantial implied volatility sensitivity even when pricing perturbations are small.

The figure represents theoretical local inverse sensitivity rather than realized errors from individual perturbations.

![Implied volatility conditioning](results/figures/volatility_conditioning.png)

Dataset: [Volatility conditioning results](results/data/volatility_conditioning.csv)

### 5. Computational Benchmarking

Twenty computational configurations were evaluated using thirty measured executions per configuration.

Selected results are presented below.

| Model | Resolution | Median Runtime (ms) | RMSE |
|---|---:|---:|---:|
| Black-Scholes-Merton | Analytical | 0.001167 | 0 |
| CRR binomial | 1,024 steps | 2.086354 | 0.000449 |
| Standard Monte Carlo | 65,536 | 0.933958 | 0.056573 |
| Antithetic Monte Carlo | 65,536 | 0.755375 | 0.052959 |
| Control variate | 65,536 | 0.920001 | 0.027772 |
| Combined Monte Carlo | 65,536 | 0.794209 | 0.013368 |

The analytical model serves as the reference and therefore has zero measured approximation error by construction.

Among the tested numerical configurations, the 1,024-step binomial tree produced the lowest numerical pricing error.

The combined estimator produced the lowest RMSE among the four stochastic methods.

Runtime measurements are specific to the recorded software and hardware environment.

![Computational performance benchmark](results/figures/performance_benchmark.png)

Datasets:

- [Benchmark summary](results/data/benchmark_summary.csv)
- [Benchmark replications](results/data/benchmark_replications.csv)

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
|   |-- __init__.py
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
|-- .github/
|   |-- workflows/
|       |-- tests.yml
|
|-- .gitignore
|-- requirements.txt
|-- README.md
```

### Core Modules

| Module | Responsibility |
|---|---|
| main.py | Interactive command-line application |
| pricing.py | Analytical option valuation |
| analysis.py | Analytical option Greeks |
| implied_volatility.py | Numerical volatility inversion |
| lattice.py | European and American binomial pricing |
| monte_carlo.py | Stochastic pricing and variance reduction |
| numerical_greeks.py | Finite-difference sensitivity calculations |
| visualization.py | Interactive analytical figures |
| experiments.py | Binomial and Monte Carlo research studies |
| research/ | Numerical experiments, figures, and documentation |
| results/ | Published computational results |
| tests/ | Automated software validation |

## Installation

### Requirements

The recorded development environment uses Python 3.14.6.

| Dependency | Recorded Version |
|---|---|
| Python | 3.14.6 |
| NumPy | 2.5.5 |
| Matplotlib | 3.11.2 |
| Pytest | 9.2.0 |

Dependency versions are recorded in [requirements.txt](requirements.txt).

### Clone the Repository

```bash
git clone https://github.com/LakshSuri/black-scholes-options-lab.git
cd black-scholes-options-lab
```

### Create a Virtual Environment

Use an installed Python 3.14 interpreter.

For macOS or Linux:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

For Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
python -m pip install -r requirements.txt
```

Validate the installed dependencies:

```bash
python -m pip check
```

## Interactive Application

Launch the application from the repository root:

```bash
python main.py
```

The application contains thirteen analytical and computational features.

```text
============================================================
            DERIVATIVES PRICING LABORATORY
============================================================

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
============================================================
```

The visualization menu includes option pricing curves, volatility sensitivity, expiration sensitivity, and graphical analysis of all five Greeks.

## Python Examples

The mathematical modules can also be imported directly into Python programs.

### European Option Pricing

```python
from pricing import black_scholes_call

price = black_scholes_call(
    100,
    105,
    1,
    0.05,
    0.25,
    dividend_yield=0.02
)

print(price)
```

Expected output, subject to floating-point precision:

```text
8.941175726631428
```

Interest rates, volatility, and dividend yields are expressed as decimals when using the Python functions.

### American Option Pricing

```python
from lattice import crr_price

price = crr_price(
    100,
    105,
    1,
    0.05,
    0.25,
    steps=1024,
    option_type="put",
    exercise_style="american",
    dividend_yield=0.02
)

print(price)
```

### Monte Carlo Pricing

```python
from monte_carlo import monte_carlo_price

result = monte_carlo_price(
    100,
    105,
    1,
    0.05,
    0.25,
    simulations=65536,
    option_type="call",
    dividend_yield=0.02,
    seed=42,
    method="combined"
)

print("Estimated price:", result["price"])
print("Standard error:", result["standard_error"])
print("Confidence interval:", result["confidence_interval"])
```

### Implied Volatility Recovery

```python
from implied_volatility import implied_volatility

volatility = implied_volatility(
    8.941175726631428,
    100,
    105,
    1,
    0.05,
    option_type="call",
    dividend_yield=0.02
)

print(f"Implied volatility: {volatility:.2%}")
```

Expected output:

```text
Implied volatility: 25.00%
```

### Analytical Greeks

```python
from analysis import calculate_greeks

greeks = calculate_greeks(
    100,
    105,
    1,
    0.05,
    0.25,
    option_type="call",
    dividend_yield=0.02
)

for greek, value in greeks.items():
    print(f"{greek}: {value:.6f}")
```

## Research Reproducibility

All computational studies, datasets, figures, and environment metadata can be regenerated using a unified command:

```bash
python -m research.reproduce
```

The regenerated results are stored in:

```text
reproduced-results/
|-- data/
|-- figures/
|-- environment.json
```

Original published measurements remain unchanged in the results directory.

Individual studies can also be executed separately:

```bash
python experiments.py
python -m research.numerical_stability
python -m research.volatility_conditioning
python -m research.benchmarks
python -m research.figures
python -m research.environment
```

Unlike the unified reproduction command, these individual commands use the original results directory by default and may overwrite existing outputs.

### Experimental Environment

The original experiments were conducted using:

- CPython 3.14.6
- macOS
- ARM64 architecture
- NumPy 2.5.5
- Matplotlib 3.11.2
- Pytest 9.2.0

The recorded experimental seeds and dependency versions are available in [environment.json](results/environment.json).

Fixed random seeds support stochastic reproducibility within consistent software environments. Runtime measurements and floating-point calculations may vary between systems.

## Software Validation

Run the complete automated test suite:

```bash
python -m pytest -q
```

Recorded local validation:

```text
186 passed
```

The automated tests cover:

- Analytical pricing.
- Put-call parity.
- Mathematical input validation.
- Analytical Greeks.
- Implied volatility recovery.
- European and American binomial valuation.
- Monte Carlo reproducibility.
- Statistical uncertainty.
- Variance reduction.
- Finite-difference accuracy and convergence.
- Research dataset integrity.
- Figure generation.
- Environment metadata.

Continuous integration is configured through GitHub Actions using Python 3.14 on Ubuntu.

View the latest workflow status:

[GitHub Actions](https://github.com/LakshSuri/black-scholes-options-lab/actions)

Passing tests establish correctness within the tested configurations rather than guaranteeing correctness for every possible input.

## Technical Documentation

The complete mathematical framework, experimental methodology, results, limitations, and references are documented in:

[Computational Analysis of Derivatives Pricing Models](research/technical_report.md)

The technical report provides additional detail on the mathematical assumptions, numerical techniques, statistical estimators, and computational experiments implemented within the laboratory.

## Limitations

The current framework has several limitations:

- Constant volatility, interest rates, and dividend yields.
- Synthetic market configurations rather than historical option chain data.
- No transaction costs, liquidity modeling, or market microstructure.
- Limited experimental market configurations.
- Approximate Monte Carlo confidence intervals.
- Finite-sample statistical uncertainty.
- Floating-point sensitivity in numerical differentiation.
- Restricted implied volatility search domain.
- Discrete approximation of American early exercise.
- European terminal-payoff Monte Carlo pricing.
- Hardware-dependent runtime measurements.

The project evaluates established mathematical models under controlled assumptions. It does not establish real-world predictive accuracy or trading profitability.

## References and Further Reading

1. Black, F., and Scholes, M. (1973). The Pricing of Options and Corporate Liabilities. Journal of Political Economy, 81(3), 637-654.

   https://doi.org/10.1086/260062

2. Merton, R. C. (1973). Theory of Rational Option Pricing. Bell Journal of Economics and Management Science, 4(1), 141-183.

   https://doi.org/10.2307/3003143

3. Cox, J. C., Ross, S. A., and Rubinstein, M. (1979). Option Pricing: A Simplified Approach. Journal of Financial Economics, 7(3), 229-263.

   https://doi.org/10.1016/0304-405X(79)90015-1

4. Glasserman, P. (2004). Monte Carlo Methods in Financial Engineering. Springer.

   https://doi.org/10.1007/978-0-387-21617-1

## Future Development

Potential research extensions include:

- Stochastic volatility modeling.
- Heston model calibration.
- Implied volatility surface construction.
- Quasi-Monte Carlo simulation.
- Jump-diffusion processes.
- Longstaff-Schwartz American option pricing.
- Adaptive numerical differentiation.
- Historical option chain validation.
- Broader computational performance analysis.
- Integration with a comprehensive quantitative research platform.

## Development Transparency

This educational project was developed with substantial ChatGPT-assisted coding and technical guidance.

The repository owner executed the computational experiments and automated tests locally and managed the repository.

The project investigates established mathematical methods through reproducible experiments rather than claiming original discoveries of the underlying models.

## Author

Laksh Suri

Research interests: quantitative finance, computational mathematics, probability, statistics, and software development.

---

Developed for educational and computational research purposes. Not intended for investment or trading decisions.