import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing import black_scholes_call, black_scholes_put
from lattice import crr_price

from web.components import (
    COLORS,
    page_header,
    metric_row,
    style_figure
)


def model_inputs():
    st.subheader("Model parameters")

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
        value=100.0,
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
        value=20.0,
        step=1.0
    ) / 100

    dividend = right.number_input(
        "Dividend yield (%)",
        min_value=0.0,
        max_value=15.0,
        value=2.0,
        step=0.5
    ) / 100

    left, right = st.columns(2)

    option_type = left.radio(
        "Option type",
        ["call", "put"],
        format_func=str.capitalize,
        horizontal=True
    )

    steps = right.select_slider(
        "Binomial tree steps",
        options=[
            32, 64, 128, 256, 512, 1024, 2048
        ],
        value=512
    )

    return (
        stock,
        strike,
        expiration,
        rate,
        volatility,
        dividend,
        option_type,
        steps
    )


def analytical_price(
    stock, strike, expiration, rate,
    volatility, dividend, option_type
):
    function = (
        black_scholes_call
        if option_type == "call"
        else black_scholes_put
    )

    return function(
        stock,
        strike,
        expiration,
        rate,
        volatility,
        dividend_yield=dividend
    )


def lattice_price(
    stock, strike, expiration, rate,
    volatility, dividend, option_type,
    steps, exercise_style
):
    return crr_price(
        stock,
        strike,
        expiration,
        rate,
        volatility,
        steps=steps,
        option_type=option_type,
        exercise_style=exercise_style,
        dividend_yield=dividend
    )


def valuation_chart(
    stock, strike, expiration, rate,
    volatility, dividend, option_type
):
    stock_values = np.linspace(
        0.5 * min(stock, strike),
        1.5 * max(stock, strike),
        151
    )

    option_values = [
        analytical_price(
            value, strike, expiration, rate,
            volatility, dividend, option_type
        )
        for value in stock_values
    ]

    if option_type == "call":
        payoff = np.maximum(stock_values - strike, 0)
    else:
        payoff = np.maximum(strike - stock_values, 0)

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=stock_values,
            y=option_values,
            name="European model value",
            mode="lines",
            line={
                "color": COLORS["primary"],
                "width": 2.5
            }
        )
    )

    figure.add_trace(
        go.Scatter(
            x=stock_values,
            y=payoff,
            name="Expiration payoff",
            mode="lines",
            line={
                "color": COLORS["amber"],
                "width": 1.8,
                "dash": "dash"
            }
        )
    )

    figure.add_vline(
        x=strike,
        line_dash="dot",
        line_color=COLORS["muted"],
        annotation_text="Strike"
    )

    figure.add_trace(
        go.Scatter(
            x=[stock],
            y=[
                analytical_price(
                    stock, strike, expiration, rate,
                    volatility, dividend, option_type
                )
            ],
            mode="markers",
            name="Selected parameters",
            marker={
                "color": COLORS["blue"],
                "size": 10
            }
        )
    )

    figure.update_xaxes(
        title="Underlying price"
    )

    figure.update_yaxes(
        title="Option value / payoff"
    )

    return style_figure(figure, height=450)


@st.cache_data(max_entries=64)
def convergence_data(
    stock, strike, expiration, rate,
    volatility, dividend, option_type
):
    reference = analytical_price(
        stock, strike, expiration, rate,
        volatility, dividend, option_type
    )

    records = []

    for base_steps in [32, 64, 128, 256, 512, 1024]:
        for steps in [base_steps, base_steps + 1]:
            try:
                estimate = lattice_price(
                    stock, strike, expiration, rate,
                    volatility, dividend, option_type,
                    steps, "european"
                )
            except ValueError:
                estimate = float("nan")

            records.append({
                "Steps": steps,
                "Parity": (
                    "Even" if steps % 2 == 0 else "Odd"
                ),
                "Estimated value": estimate,
                "Reference value": reference,
                "Signed error": estimate - reference,
                "Absolute error": abs(
                    estimate - reference
                )
            })

    return pd.DataFrame(records)


def convergence_chart(data):
    figure = go.Figure()

    for parity, color in [
        ("Even", COLORS["primary"]),
        ("Odd", COLORS["blue"])
    ]:
        subset = data[data["Parity"] == parity]

        figure.add_trace(
            go.Scatter(
                x=subset["Steps"],
                y=subset["Signed error"],
                name=f"{parity} steps",
                mode="lines+markers",
                connectgaps=False,
                line={
                    "color": color,
                    "width": 2
                },
                marker={"size": 7}
            )
        )

    figure.add_hline(
        y=0,
        line_dash="dash",
        line_color=COLORS["amber"]
    )

    figure.update_xaxes(
        title="Binomial tree steps",
        type="log"
    )

    figure.update_yaxes(
        title="Signed error relative to BSM"
    )

    return style_figure(figure, height=420)


def parity_verification(
    stock, strike, expiration, rate,
    volatility, dividend
):
    call = black_scholes_call(
        stock, strike, expiration, rate,
        volatility, dividend_yield=dividend
    )

    put = black_scholes_put(
        stock, strike, expiration, rate,
        volatility, dividend_yield=dividend
    )

    left_side = call - put

    right_side = (
        stock * math.exp(-dividend * expiration)
        - strike * math.exp(-rate * expiration)
    )

    residual = left_side - right_side

    st.latex(
        r"C-P=Se^{-qT}-Ke^{-rT}"
    )

    metric_row([
        ("Call minus put", f"{left_side:.8f}"),
        ("Discounted difference", f"{right_side:.8f}"),
        ("Absolute residual", f"{abs(residual):.2e}")
    ])

    if abs(residual) < 1e-10:
        st.success(
            "Put-call parity satisfied within "
            "numerical tolerance."
        )
    else:
        st.warning(
            "The parity residual exceeds the "
            "specified numerical tolerance."
        )


def render():
    page_header(
        "Research / Option Valuation",
        "Option Valuation",
        "Compare analytical and lattice-based valuation "
        "under controlled mathematical assumptions."
    )

    (
        stock, strike, expiration, rate,
        volatility, dividend, option_type, steps
    ) = model_inputs()

    st.divider()

    analytical = analytical_price(
        stock, strike, expiration, rate,
        volatility, dividend, option_type
    )

    try:
        european = lattice_price(
            stock, strike, expiration, rate,
            volatility, dividend, option_type,
            steps, "european"
        )

        american = lattice_price(
            stock, strike, expiration, rate,
            volatility, dividend, option_type,
            steps, "american"
        )

    except ValueError as error:
        european = None
        american = None
        st.warning(f"Lattice calculation: {error}")

    st.subheader("Valuation summary")

    metric_row([
        (
            "Black-Scholes-Merton",
            f"{analytical:,.6f}"
        ),
        (
            "European lattice",
            f"{european:,.6f}"
            if european is not None else "Unavailable"
        ),
        (
            "American lattice",
            f"{american:,.6f}"
            if american is not None else "Unavailable"
        )
    ])

    if european is not None and american is not None:
        metric_row([
            (
                "Absolute pricing error",
                f"{abs(european - analytical):.6f}"
            ),
            (
                "Early exercise premium",
                f"{american - european:.6f}"
            ),
            (
                "Underlying / strike",
                f"{stock / strike:.4f}"
            )
        ])

    st.caption(
        "The early exercise premium compares American "
        "and European values using the same lattice."
    )

    st.divider()

    curve_tab, convergence_tab, parity_tab = st.tabs([
        "Valuation curves",
        "Numerical convergence",
        "Put-call parity"
    ])

    with curve_tab:
        st.subheader("Option value and expiration payoff")

        st.plotly_chart(
            valuation_chart(
                stock, strike, expiration, rate,
                volatility, dividend, option_type
            ),
            width="stretch",
            config={"displaylogo": False}
        )

        st.caption(
            "The analytical curve represents the European "
            "model value before expiration. The dashed "
            "curve represents the payoff at expiration."
        )

    with convergence_tab:
        st.subheader("Lattice approximation error")

        data = convergence_data(
            stock, strike, expiration, rate,
            volatility, dividend, option_type
        )

        st.plotly_chart(
            convergence_chart(data),
            width="stretch",
            config={"displaylogo": False}
        )

        if data["Estimated value"].isna().any():
            st.warning(
                "Some coarse lattices have invalid "
                "risk-neutral probabilities. Their "
                "estimates are omitted from the chart."
            )

        st.dataframe(
            data,
            width="stretch",
            hide_index=True
        )

        st.download_button(
            "Download convergence data",
            data.to_csv(index=False).encode("utf-8"),
            file_name="valuation_convergence.csv",
            mime="text/csv"
        )

        st.caption(
            "Odd and even step counts are shown separately "
            "because binomial convergence can oscillate "
            "rather than improve monotonically."
        )

    with parity_tab:
        st.subheader("European put-call parity")

        parity_verification(
            stock, strike, expiration, rate,
            volatility, dividend
        )

    st.divider()

    st.subheader("Mathematical assumptions")

    st.markdown(
        """
        - Constant volatility and risk-free interest rate.
        - Continuous dividend yield.
        - Lognormal underlying dynamics.
        - Frictionless markets.
        - Early exercise permitted in the American lattice.
        """
    )

    st.caption(
        "All parameters are hypothetical and intended "
        "for numerical and educational research."
    )