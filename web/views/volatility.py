import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks
from implied_volatility import implied_volatility

from web.components import (
    COLORS,
    page_header,
    metric_row,
    style_figure
)


ROOT = Path(__file__).resolve().parents[2]


def model_inputs():
    st.subheader("Model parameters")

    left, center, right = st.columns(3)

    stock = left.number_input(
        "Underlying price",
        min_value=1.0,
        max_value=1000.0,
        value=100.0,
        step=5.0,
        key="iv_stock"
    )

    strike = center.number_input(
        "Strike price",
        min_value=1.0,
        max_value=1000.0,
        value=100.0,
        step=5.0,
        key="iv_strike"
    )

    expiration = right.number_input(
        "Time to expiration (years)",
        min_value=0.05,
        max_value=5.0,
        value=1.0,
        step=0.05,
        key="iv_expiration"
    )

    rate = left.number_input(
        "Risk-free rate (%)",
        min_value=-5.0,
        max_value=15.0,
        value=5.0,
        step=0.5,
        key="iv_rate"
    ) / 100

    dividend = center.number_input(
        "Dividend yield (%)",
        min_value=0.0,
        max_value=15.0,
        value=2.0,
        step=0.5,
        key="iv_dividend"
    ) / 100

    original_volatility = right.number_input(
        "Reference volatility (%)",
        min_value=5.0,
        max_value=100.0,
        value=25.0,
        step=1.0,
        key="iv_reference"
    ) / 100

    option_type = st.radio(
        "Option type",
        ["call", "put"],
        format_func=str.capitalize,
        horizontal=True,
        key="iv_option"
    )

    parameters = {
        "stock_price": stock,
        "strike_price": strike,
        "time_to_expiration": expiration,
        "risk_free_rate": rate,
        "dividend_yield": dividend,
        "option_type": option_type
    }

    return parameters, original_volatility


def model_price(parameters, volatility):
    inputs = parameters.copy()

    option_type = inputs.pop("option_type")

    function = (
        black_scholes_call
        if option_type == "call"
        else black_scholes_put
    )

    return function(
        **inputs,
        volatility=volatility
    )


def pricing_bounds(parameters):
    stock = parameters["stock_price"]
    strike = parameters["strike_price"]
    expiration = parameters["time_to_expiration"]
    rate = parameters["risk_free_rate"]
    dividend = parameters["dividend_yield"]

    discounted_stock = stock * math.exp(
        -dividend * expiration
    )

    discounted_strike = strike * math.exp(
        -rate * expiration
    )

    if parameters["option_type"] == "call":
        return (
            max(
                0.0,
                discounted_stock - discounted_strike
            ),
            discounted_stock
        )

    return (
        max(
            0.0,
            discounted_strike - discounted_stock
        ),
        discounted_strike
    )


def recover_volatility(parameters, observed_price):
    return implied_volatility(
        market_price=observed_price,
        **parameters
    )


def raw_vega(parameters, volatility):
    result = calculate_greeks(
        **parameters,
        volatility=volatility
    )

    return result["vega"] * 100


def inversion_chart(
    parameters,
    observed_price,
    recovered
):
    maximum = max(
        1.0,
        recovered * 1.2 if recovered is not None
        else 1.0
    )

    volatility_values = np.linspace(
        0.0001,
        maximum,
        301
    )

    prices = [
        model_price(parameters, float(volatility))
        for volatility in volatility_values
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=volatility_values * 100,
            y=prices,
            mode="lines",
            name="Model price",
            line={
                "color": COLORS["primary"],
                "width": 2.5
            },
            hovertemplate=(
                "Volatility: %{x:.3f}%"
                "<br>Model value: %{y:.6f}"
                "<extra></extra>"
            )
        )
    )

    figure.add_hline(
        y=observed_price,
        line_color=COLORS["amber"],
        line_dash="dash",
        annotation_text="Synthetic observed price"
    )

    if recovered is not None:
        figure.add_vline(
            x=recovered * 100,
            line_color=COLORS["blue"],
            line_dash="dot"
        )

        figure.add_trace(
            go.Scatter(
                x=[recovered * 100],
                y=[
                    model_price(
                        parameters,
                        recovered
                    )
                ],
                mode="markers",
                name="Recovered solution",
                marker={
                    "color": COLORS["blue"],
                    "size": 12
                }
            )
        )

    figure.update_xaxes(
        title="Annualized volatility (%)"
    )

    figure.update_yaxes(
        title="Theoretical option value"
    )

    return style_figure(figure, height=440)


def perturbation_data(
    parameters,
    reference_volatility,
    magnitude
):
    reference = model_price(
        parameters,
        reference_volatility
    )

    vega = raw_vega(
        parameters,
        reference_volatility
    )

    lower, upper = pricing_bounds(parameters)

    records = []

    perturbations = np.linspace(
        -magnitude,
        magnitude,
        21
    )

    for perturbation in perturbations:
        perturbation = float(perturbation)

        observed = reference + perturbation

        recovered = float("nan")
        actual_error = float("nan")

        predicted_error = (
            perturbation / vega
            if vega > 0
            else float("nan")
        )

        if not lower < observed < upper:
            status = "Outside pricing bounds"

        else:
            try:
                recovered = recover_volatility(
                    parameters,
                    observed
                )

                actual_error = (
                    recovered - reference_volatility
                )

                status = "Success"

            except (ValueError, RuntimeError):
                status = "Solver failure"

        records.append({
            "Price perturbation": perturbation,
            "Observed price": observed,
            "Recovered volatility (%)": recovered * 100,
            "Predicted error (pp)": predicted_error * 100,
            "Actual error (pp)": actual_error * 100,
            "Status": status
        })

    return pd.DataFrame(records)


def perturbation_chart(data):
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=data["Price perturbation"],
            y=data["Actual error (pp)"],
            mode="lines+markers",
            name="Recovered volatility error",
            connectgaps=False,
            line={
                "color": COLORS["primary"],
                "width": 2.2
            },
            marker={"size": 6}
        )
    )

    predicted = data["Predicted error (pp)"].where(
        data["Status"] == "Success"
    )

    figure.add_trace(
        go.Scatter(
            x=data["Price perturbation"],
            y=predicted,
            mode="lines",
            name="First-order Vega approximation",
            line={
                "color": COLORS["amber"],
                "width": 1.8,
                "dash": "dash"
            }
        )
    )

    figure.add_hline(
        y=0,
        line_color=COLORS["muted"],
        line_dash="dot"
    )

    figure.update_xaxes(
        title="Synthetic option price perturbation"
    )

    figure.update_yaxes(
        title="Volatility error (percentage points)"
    )

    return style_figure(figure, height=430)


@st.cache_data
def load_conditioning_data():
    return pd.read_csv(
        ROOT / "results" / "data"
        / "volatility_conditioning.csv"
    )


def conditioning_chart(data, option_type):
    subset = data[
        data["option_type"] == option_type
    ].drop_duplicates(
        subset=["strike", "expiration"]
    )

    matrix = subset.pivot(
        index="expiration",
        columns="strike",
        values="inverse_sensitivity"
    ).sort_index()

    values = matrix.to_numpy(dtype=float)

    logarithms = np.full(
        values.shape,
        np.nan
    )

    valid = (
        np.isfinite(values)
        & (values > 0)
    )

    logarithms[valid] = np.log10(
        values[valid]
    )

    figure = go.Figure(
        go.Heatmap(
            x=[
                str(int(strike))
                for strike in matrix.columns
            ],
            y=[
                str(expiration)
                for expiration in matrix.index
            ],
            z=logarithms,
            customdata=values,
            colorscale=[
                [0.0, "#18302C"],
                [0.35, "#69D3B5"],
                [0.7, "#D6B77A"],
                [1.0, "#BA655B"]
            ],
            colorbar={
                "title": "log10(1/Vega)"
            },
            hovertemplate=(
                "Strike: %{x}"
                "<br>Expiration: %{y} years"
                "<br>Inverse sensitivity: "
                "%{customdata:.6e}"
                "<extra></extra>"
            )
        )
    )

    figure.update_xaxes(
        title="Strike price",
        type="category"
    )

    figure.update_yaxes(
        title="Time to expiration (years)",
        type="category"
    )

    return style_figure(figure, height=430)


def render_solver(
    parameters,
    reference_volatility
):
    st.subheader("Volatility inversion")

    reference = model_price(
        parameters,
        reference_volatility
    )

    lower, upper = pricing_bounds(parameters)

    perturbation = st.number_input(
        "Synthetic price adjustment",
        min_value=-1000.0,
        max_value=1000.0,
        value=0.0,
        step=0.01,
        format="%.6f",
        key="iv_adjustment"
    )

    observed = reference + perturbation

    metric_row([
        ("Reference price", f"{reference:.6f}"),
        ("Adjusted price", f"{observed:.6f}"),
        ("Lower boundary", f"{lower:.6f}"),
        ("Upper boundary", f"{upper:.6f}")
    ])

    st.caption(
        "The adjusted price must lie strictly "
        "between the two pricing boundaries."
    )

    recovered = None

    if not lower < observed < upper:
        st.warning(
            "The synthetic observed price violates "
            "strict no-arbitrage pricing bounds."
        )

    else:
        try:
            recovered = recover_volatility(
                parameters,
                observed
            )

        except (ValueError, RuntimeError) as error:
            st.warning(str(error))

    if recovered is not None:
        repriced = model_price(
            parameters,
            recovered
        )

        residual = repriced - observed

        vega = raw_vega(
            parameters,
            recovered
        )

        inverse = (
            1 / vega
            if vega > 0
            else float("inf")
        )

        metric_row([
            (
                "Recovered volatility",
                f"{recovered * 100:.6f}%"
            ),
            (
                "Repricing residual",
                f"{residual:.3e}"
            ),
            (
                "Raw Vega",
                f"{vega:.6e}"
            ),
            (
                "Inverse sensitivity",
                f"{inverse:.6e}"
            )
        ])

        if abs(residual) <= 1e-8:
            st.success(
                "The recovered solution reproduces "
                "the synthetic observed price."
            )
        else:
            st.warning(
                "The repricing residual exceeds "
                "the display tolerance."
            )

        if vega < 1e-8:
            st.warning(
                "Vega is extremely small. A small "
                "repricing residual does not establish "
                "accurate volatility recovery."
            )

    st.plotly_chart(
        inversion_chart(
            parameters,
            observed,
            recovered
        ),
        width="stretch",
        config={"displaylogo": False}
    )

    st.caption(
        "The existing solver uses bisection with an "
        "adaptive upper bracket. Its stopping tolerance "
        "applies to the volatility interval."
    )


def render_perturbations(
    parameters,
    reference_volatility
):
    st.subheader("Price perturbation experiment")

    magnitude = st.select_slider(
        "Maximum absolute price perturbation",
        options=[
            0.001,
            0.005,
            0.01,
            0.05,
            0.10,
            0.50,
            1.0
        ],
        value=0.10
    )

    data = perturbation_data(
        parameters,
        reference_volatility,
        magnitude
    )

    successful = data[
        data["Status"] == "Success"
    ]

    maximum_error = (
        successful["Actual error (pp)"].abs().max()
        if not successful.empty
        else float("nan")
    )

    metric_row([
        ("Perturbations", str(len(data))),
        ("Successful recoveries", str(len(successful))),
        (
            "Rejected or failed cases",
            str(len(data) - len(successful))
        ),
        (
            "Maximum volatility error",
            f"{maximum_error:.6f} pp"
            if not successful.empty
            else "Unavailable"
        )
    ])

    st.plotly_chart(
        perturbation_chart(data),
        width="stretch",
        config={"displaylogo": False}
    )

    st.latex(
        r"\Delta \sigma\approx"
        r"\frac{\Delta V}{\partial V/\partial \sigma}"
    )

    st.caption(
        "The first-order approximation describes "
        "local sensitivity. It can become inaccurate "
        "for larger perturbations or very small Vega."
    )

    st.dataframe(
        data,
        width="stretch",
        hide_index=True
    )

    st.download_button(
        "Download perturbation experiment",
        data.to_csv(index=False).encode("utf-8"),
        file_name="volatility_perturbations.csv",
        mime="text/csv"
    )


def render_recorded():
    st.subheader("Recorded conditioning research")

    data = load_conditioning_data()

    successful = (
        data["status"] == "success"
    ).sum()

    invalid = (
        data["status"]
        == "outside_pricing_bounds"
    ).sum()

    failures = (
        data["status"] == "solver_failure"
    ).sum()

    metric_row([
        ("Observations", str(len(data))),
        ("Successful recoveries", str(successful)),
        ("Outside bounds", str(invalid)),
        ("Solver failures", str(failures))
    ])

    option_type = st.radio(
        "Recorded option type",
        ["call", "put"],
        format_func=str.capitalize,
        horizontal=True,
        key="recorded_iv_option"
    )

    st.plotly_chart(
        conditioning_chart(data, option_type),
        width="stretch",
        config={"displaylogo": False}
    )

    st.caption(
        "The recorded experiment uses an underlying "
        "price of 100, volatility of 25%, a risk-free "
        "rate of 5% and dividend yield of 2%. "
        "Higher inverse sensitivity indicates "
        "greater local error amplification."
    )

    filtered = data[
        data["option_type"] == option_type
    ]

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True
    )

    st.download_button(
        "Download recorded conditioning dataset",
        data.to_csv(index=False).encode("utf-8"),
        file_name="volatility_conditioning.csv",
        mime="text/csv"
    )


def render():
    page_header(
        "Research / Implied Volatility",
        "Implied Volatility",
        "Investigate numerical inversion, pricing "
        "boundaries and the conditioning of "
        "volatility recovery."
    )

    parameters, reference_volatility = model_inputs()

    st.divider()

    solver_tab, perturbation_tab, recorded_tab = st.tabs([
        "Volatility solver",
        "Price perturbations",
        "Recorded research"
    ])

    with solver_tab:
        render_solver(
            parameters,
            reference_volatility
        )

    with perturbation_tab:
        render_perturbations(
            parameters,
            reference_volatility
        )

    with recorded_tab:
        render_recorded()

    st.divider()

    st.subheader("Mathematical framework")

    st.latex(
        r"V_{\mathrm{BSM}}(\sigma^*)"
        r"=V_{\mathrm{observed}}"
    )

    st.latex(
        r"\frac{\partial \sigma}{\partial V}"
        r"=\frac{1}{\partial V/\partial \sigma}"
    )

    st.markdown(
        """
        Implied volatility inversion seeks a volatility
        parameter that reproduces a specified option
        value under the pricing model.

        When Vega is small, relatively minor changes
        in the observed price can produce substantial
        differences in recovered volatility.

        Consequently, a successful numerical inversion
        does not necessarily imply a well-conditioned
        mathematical problem.
        """
    )

    st.caption(
        "All observations use hypothetical parameters "
        "for numerical and educational research."
    )