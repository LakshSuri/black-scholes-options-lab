from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing import black_scholes_call, black_scholes_put
from monte_carlo import monte_carlo_price

from web.components import (
    COLORS,
    METHOD_COLORS,
    page_header,
    metric_row,
    style_figure
)


ROOT = Path(__file__).resolve().parents[2]

METHODS = {
    "standard": "Standard",
    "antithetic": "Antithetic",
    "control": "Control variate",
    "combined": "Combined"
}

BUDGETS = [1024, 4096, 16384, 65536]


def model_inputs():
    st.subheader("Experimental parameters")

    with st.form("simulation_parameters"):
        left, center, right = st.columns(3)

        stock = left.number_input(
            "Underlying price",
            min_value=1.0,
            max_value=1000.0,
            value=100.0,
            step=5.0
        )

        strike = center.number_input(
            "Strike price",
            min_value=1.0,
            max_value=1000.0,
            value=105.0,
            step=5.0
        )

        expiration = right.number_input(
            "Time to expiration (years)",
            min_value=0.05,
            max_value=5.0,
            value=1.0,
            step=0.05
        )

        rate = left.number_input(
            "Risk-free rate (%)",
            min_value=-5.0,
            max_value=15.0,
            value=5.0,
            step=0.5
        ) / 100

        volatility = center.number_input(
            "Volatility (%)",
            min_value=5.0,
            max_value=100.0,
            value=25.0,
            step=1.0
        ) / 100

        dividend = right.number_input(
            "Dividend yield (%)",
            min_value=0.0,
            max_value=15.0,
            value=2.0,
            step=0.5
        ) / 100

        left, center, right = st.columns(3)

        option_type = left.radio(
            "Option type",
            ["call", "put"],
            format_func=str.capitalize,
            horizontal=True
        )

        budget = center.selectbox(
            "Simulation budget",
            BUDGETS,
            index=3,
            format_func=lambda value: f"{value:,}"
        )

        replications = right.selectbox(
            "Convergence replications",
            [10, 20, 40],
            index=1
        )

        seed = st.number_input(
            "Random seed",
            min_value=0,
            max_value=2147483647,
            value=42,
            step=1
        )

        submitted = st.form_submit_button(
            "Run experiment",
            type="primary"
        )

    parameters = {
        "stock_price": stock,
        "strike_price": strike,
        "time_to_expiration": expiration,
        "risk_free_rate": rate,
        "volatility": volatility,
        "dividend_yield": dividend,
        "option_type": option_type
    }

    if submitted or "mc_experiment" not in st.session_state:
        st.session_state["mc_experiment"] = (
            parameters,
            int(budget),
            int(replications),
            int(seed)
        )

    return st.session_state["mc_experiment"]


def reference_price(parameters):
    inputs = parameters.copy()

    option_type = inputs.pop("option_type")

    function = (
        black_scholes_call
        if option_type == "call"
        else black_scholes_put
    )

    return function(**inputs)


def evaluate_method(
    parameters, method, budget, seed, reference
):
    result = monte_carlo_price(
        **parameters,
        simulations=int(budget),
        method=method,
        seed=int(seed)
    )

    lower, upper = result["confidence_interval"]

    return {
        "method": method,
        "budget": budget,
        "seed": seed,
        "reference_price": reference,
        "estimate": result["price"],
        "signed_error": result["price"] - reference,
        "absolute_error": abs(
            result["price"] - reference
        ),
        "standard_deviation": result["standard_deviation"],
        "standard_error": result["standard_error"],
        "lower_bound": lower,
        "upper_bound": upper,
        "interval_width": upper - lower,
        "covered": lower <= reference <= upper,
        "pilot_simulations": result["pilot_simulations"],
        "pricing_simulations": result["pricing_simulations"],
        "independent_samples": result["independent_samples"],
        "beta": result["beta"]
    }


@st.cache_data(max_entries=16)
def single_experiment(parameters, budget, seed):
    reference = reference_price(parameters)

    sequence = np.random.SeedSequence([seed, 0])

    children = sequence.spawn(len(METHODS))

    records = []

    for method, child in zip(METHODS, children):
        child_seed = int(
            child.generate_state(
                1, dtype=np.uint64
            )[0]
        )

        records.append(
            evaluate_method(
                parameters,
                method,
                budget,
                child_seed,
                reference
            )
        )

    return pd.DataFrame(records)


@st.cache_data(max_entries=8)
def repeated_experiment(parameters, replications, seed):
    reference = reference_price(parameters)

    sequence = np.random.SeedSequence([seed, 1])

    children = iter(
        sequence.spawn(
            len(METHODS)
            * len(BUDGETS)
            * replications
        )
    )

    records = []

    for budget in BUDGETS:
        for method in METHODS:
            for replication in range(replications):
                child = next(children)

                child_seed = int(
                    child.generate_state(
                        1, dtype=np.uint64
                    )[0]
                )

                record = evaluate_method(
                    parameters,
                    method,
                    budget,
                    child_seed,
                    reference
                )

                record["replication"] = replication + 1

                records.append(record)

    details = pd.DataFrame(records)

    summary_records = []

    for budget in BUDGETS:
        subset = details[
            details["budget"] == budget
        ]

        baseline = subset[
            subset["method"] == "standard"
        ]

        baseline_mse = float(
            np.mean(baseline["signed_error"] ** 2)
        )

        for method in METHODS:
            group = subset[
                subset["method"] == method
            ]

            mse = float(
                np.mean(group["signed_error"] ** 2)
            )

            efficiency = (
                baseline_mse / mse
                if mse > 0 else float("nan")
            )

            summary_records.append({
                "method": method,
                "budget": budget,
                "replications": replications,
                "reference_price": reference,
                "mean_estimate": group["estimate"].mean(),
                "bias": group["signed_error"].mean(),
                "rmse": np.sqrt(mse),
                "empirical_standard_deviation": (
                    group["estimate"].std(ddof=1)
                ),
                "mean_standard_error": (
                    group["standard_error"].mean()
                ),
                "coverage": group["covered"].mean(),
                "relative_efficiency": efficiency
            })

    return details, pd.DataFrame(summary_records)


def confidence_chart(data, reference):
    figure = go.Figure()

    for _, row in data.iterrows():
        method = row["method"]

        figure.add_trace(
            go.Scatter(
                x=[row["estimate"]],
                y=[METHODS[method]],
                mode="markers",
                name=METHODS[method],
                marker={
                    "size": 11,
                    "color": METHOD_COLORS[method]
                },
                error_x={
                    "type": "data",
                    "symmetric": False,
                    "array": [
                        row["upper_bound"]
                        - row["estimate"]
                    ],
                    "arrayminus": [
                        row["estimate"]
                        - row["lower_bound"]
                    ],
                    "thickness": 1.8,
                    "width": 6,
                    "color": METHOD_COLORS[method]
                },
                hovertemplate=(
                    "Estimate: %{x:.6f}"
                    "<extra></extra>"
                )
            )
        )

    figure.add_vline(
        x=reference,
        line_dash="dash",
        line_color=COLORS["amber"],
        annotation_text="Analytical reference"
    )

    figure.update_xaxes(
        title="Estimated option value"
    )

    figure.update_yaxes(
        autorange="reversed"
    )

    figure.update_layout(showlegend=False)

    return style_figure(figure, height=340)


def summary_chart(data, metric):
    figure = go.Figure()

    for method, label in METHODS.items():
        subset = data[
            data["method"] == method
        ].sort_values("budget")

        values = subset[metric]

        if metric == "rmse":
            values = values.where(values > 0)

        figure.add_trace(
            go.Scatter(
                x=subset["budget"],
                y=values,
                mode="lines+markers",
                name=label,
                connectgaps=False,
                line={
                    "color": METHOD_COLORS[method],
                    "width": 2.2
                },
                marker={"size": 7}
            )
        )

    figure.update_xaxes(
        title="Total simulation evaluations",
        type="log",
        tickvals=BUDGETS,
        ticktext=[
            f"{budget:,}" for budget in BUDGETS
        ]
    )

    if metric == "rmse":
        figure.update_yaxes(
            title="Root mean squared error",
            type="log"
        )

    elif metric == "coverage":
        figure.update_yaxes(
            title="Empirical interval coverage",
            tickformat=".0%",
            range=[0, 1.05]
        )

        figure.add_hline(
            y=0.95,
            line_color=COLORS["amber"],
            line_dash="dash",
            annotation_text="Nominal 95%"
        )

    else:
        figure.update_yaxes(
            title="Relative MSE efficiency"
        )

        figure.add_hline(
            y=1,
            line_color=COLORS["muted"],
            line_dash="dot"
        )

    return style_figure(figure, height=440)


@st.cache_data
def load_recorded_results():
    return pd.read_csv(
        ROOT / "results" / "data"
        / "monte_carlo_summary.csv"
    )


def render_single(parameters, budget, seed):
    reference = reference_price(parameters)

    data = single_experiment(
        parameters,
        budget,
        seed
    )

    standard = data[
        data["method"] == "standard"
    ].iloc[0]

    combined = data[
        data["method"] == "combined"
    ].iloc[0]

    standard_error_reduction = (
        1 - combined["standard_error"]
        / standard["standard_error"]
    ) * 100 if standard["standard_error"] > 0 else None

    metric_row([
        ("Analytical reference", f"{reference:.6f}"),
        ("Evaluations per method", f"{budget:,}"),
        (
            "Combined estimate",
            f"{combined['estimate']:.6f}"
        ),
        (
            "Combined SE reduction",
            f"{standard_error_reduction:.1f}%"
            if standard_error_reduction is not None
            else "Undefined"
        )
    ])

    st.subheader("Estimates and confidence intervals")

    st.plotly_chart(
        confidence_chart(data, reference),
        width="stretch",
        config={"displaylogo": False}
    )

    st.caption(
        "Intervals use the normal approximation at a "
        "nominal 95% confidence level. Standard error "
        "reduction describes this particular run."
    )

    display = data[[
        "method",
        "estimate",
        "absolute_error",
        "standard_error",
        "lower_bound",
        "upper_bound",
        "covered"
    ]].copy()

    display["method"] = display["method"].map(METHODS)

    st.dataframe(
        display,
        width="stretch",
        hide_index=True
    )

    st.subheader("Simulation budget allocation")

    st.dataframe(
        data[[
            "method",
            "budget",
            "pilot_simulations",
            "pricing_simulations",
            "independent_samples",
            "beta"
        ]],
        width="stretch",
        hide_index=True
    )

    st.caption(
        "Pilot evaluations are included in the total "
        "budget. Antithetic pairs are counted as "
        "independent pair averages rather than "
        "independent individual payoffs."
    )

    if (data["estimate"] < 0).any():
        st.warning(
            "A variance-reduced estimate is negative "
            "in this run. It is retained rather than "
            "clamped to zero."
        )

    st.download_button(
        "Download estimator comparison",
        data.to_csv(index=False).encode("utf-8"),
        file_name="monte_carlo_comparison.csv",
        mime="text/csv"
    )


def render_convergence(parameters, replications, seed):
    st.subheader("Repeated convergence experiment")

    st.caption(
        f"{replications} independent replications "
        "per method and simulation budget."
    )

    with st.spinner("Evaluating stochastic estimators..."):
        details, summary = repeated_experiment(
            parameters,
            replications,
            seed
        )

    metric_row([
        ("Estimators", str(len(METHODS))),
        ("Simulation budgets", str(len(BUDGETS))),
        ("Replications per configuration", str(replications)),
        ("Total estimates", f"{len(details):,}")
    ])

    metric = st.selectbox(
        "Convergence measure",
        ["rmse", "coverage", "relative_efficiency"],
        format_func=lambda value: {
            "rmse": "Root mean squared error",
            "coverage": "Confidence interval coverage",
            "relative_efficiency": "Relative MSE efficiency"
        }[value],
        key="live_mc_metric"
    )

    st.plotly_chart(
        summary_chart(summary, metric),
        width="stretch",
        config={"displaylogo": False}
    )

    st.caption(
        "RMSE evaluates error across repeated estimates. "
        "Relative efficiency is the standard estimator's "
        "MSE divided by the selected estimator's MSE. "
        "It is not a runtime speedup."
    )

    st.dataframe(
        summary,
        width="stretch",
        hide_index=True
    )

    left, right = st.columns(2)

    left.download_button(
        "Download experiment summary",
        summary.to_csv(index=False).encode("utf-8"),
        file_name="live_mc_summary.csv",
        mime="text/csv"
    )

    right.download_button(
        "Download individual replications",
        details.to_csv(index=False).encode("utf-8"),
        file_name="live_mc_replications.csv",
        mime="text/csv"
    )


def render_recorded():
    st.subheader("Recorded research experiment")

    st.write(
        "The original research dataset contains "
        "100 replications for each estimator and budget."
    )

    st.caption(
        "Recorded scenario: European call, S = 100, "
        "K = 105, T = 1 year, r = 5%, "
        "volatility = 25%, dividend yield = 2%."
    )

    data = load_recorded_results()

    metric_row([
        ("Configurations", str(len(data))),
        ("Replications per configuration", "100"),
        ("Total estimates", "1,600"),
        (
            "Reference value",
            f"{data['reference_price'].iloc[0]:.6f}"
        )
    ])

    metric = st.selectbox(
        "Recorded research measure",
        ["rmse", "coverage", "relative_efficiency"],
        format_func=lambda value: {
            "rmse": "Root mean squared error",
            "coverage": "Confidence interval coverage",
            "relative_efficiency": "Relative MSE efficiency"
        }[value],
        key="recorded_mc_metric"
    )

    st.plotly_chart(
        summary_chart(data, metric),
        width="stretch",
        config={"displaylogo": False}
    )

    st.dataframe(
        data,
        width="stretch",
        hide_index=True
    )

    st.download_button(
        "Download recorded research dataset",
        data.to_csv(index=False).encode("utf-8"),
        file_name="recorded_mc_summary.csv",
        mime="text/csv"
    )


def render():
    page_header(
        "Research / Monte Carlo Laboratory",
        "Monte Carlo Laboratory",
        "Investigate stochastic estimation, variance "
        "reduction and statistical uncertainty through "
        "reproducible computational experiments."
    )

    parameters, budget, replications, seed = model_inputs()

    st.caption(
        f"Active experiment: "
        f"{parameters['option_type'].capitalize()} | "
        f"S = {parameters['stock_price']:.2f} | "
        f"K = {parameters['strike_price']:.2f} | "
        f"T = {parameters['time_to_expiration']:.2f} | "
        f"Seed = {seed}"
    )

    st.divider()

    single_tab, convergence_tab, recorded_tab = st.tabs([
        "Estimator comparison",
        "Live convergence",
        "Recorded research"
    ])

    with single_tab:
        render_single(parameters, budget, seed)

    with convergence_tab:
        render_convergence(
            parameters,
            replications,
            seed
        )

    with recorded_tab:
        render_recorded()

    st.divider()

    st.subheader("Statistical framework")

    st.latex(
        r"\widehat{V}_N="
        r"\frac{1}{N}\sum_{i=1}^{N}"
        r"e^{-rT}g(S_T^{(i)})"
    )

    st.latex(
        r"\mathrm{SE}(\widehat{V})="
        r"\frac{s}{\sqrt{n_{\mathrm{ind}}}}"
    )

    st.markdown(
        """
        The standard estimator averages discounted
        simulated payoffs.

        Antithetic sampling pairs opposite random shocks.
        Control variates use the known expectation of
        discounted terminal stock values. The combined
        estimator incorporates both methods.

        Variance reduction performance depends on
        model parameters, payoff structure, simulation
        budget and the quality of the estimated control
        coefficient.
        """
    )

    st.caption(
        "Synthetic model parameters are used throughout "
        "for educational and computational research."
    )