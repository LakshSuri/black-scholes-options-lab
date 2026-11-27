import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis import calculate_greeks
from numerical_greeks import numerical_greeks

from web.components import (
    COLORS,
    page_header,
    metric_row,
    style_figure
)


GREEKS = {
    "delta": {
        "name": "Delta",
        "unit": "Per unit of underlying price",
        "description": "First-order price sensitivity",
        "formula": r"\Delta=\frac{\partial V}{\partial S}"
    },
    "gamma": {
        "name": "Gamma",
        "unit": "Per squared unit of underlying price",
        "description": "Second-order price sensitivity",
        "formula": r"\Gamma=\frac{\partial^2 V}{\partial S^2}"
    },
    "theta": {
        "name": "Theta",
        "unit": "Per calendar day",
        "description": "Sensitivity to the passage of time",
        "formula": r"\Theta=-\frac{1}{365}\frac{\partial V}{\partial T}"
    },
    "vega": {
        "name": "Vega",
        "unit": "Per volatility percentage point",
        "description": "Volatility sensitivity",
        "formula": r"\nu=\frac{1}{100}\frac{\partial V}{\partial \sigma}"
    },
    "rho": {
        "name": "Rho",
        "unit": "Per interest rate percentage point",
        "description": "Interest rate sensitivity",
        "formula": r"\rho=\frac{1}{100}\frac{\partial V}{\partial r}"
    }
}


def model_inputs():
    st.subheader("Model parameters")

    left, center, right = st.columns(3)

    stock = left.number_input(
        "Underlying price",
        min_value=1.0,
        max_value=1000.0,
        value=100.0,
        step=5.0,
        key="greeks_stock"
    )

    strike = center.number_input(
        "Strike price",
        min_value=1.0,
        max_value=1000.0,
        value=100.0,
        step=5.0,
        key="greeks_strike"
    )

    expiration = right.number_input(
        "Time to expiration (years)",
        min_value=0.05,
        max_value=5.0,
        value=1.0,
        step=0.05,
        key="greeks_expiration"
    )

    rate = left.number_input(
        "Risk-free rate (%)",
        min_value=-5.0,
        max_value=15.0,
        value=5.0,
        step=0.5,
        key="greeks_rate"
    ) / 100

    volatility = center.number_input(
        "Volatility (%)",
        min_value=5.0,
        max_value=100.0,
        value=20.0,
        step=1.0,
        key="greeks_volatility"
    ) / 100

    dividend = right.number_input(
        "Dividend yield (%)",
        min_value=0.0,
        max_value=15.0,
        value=2.0,
        step=0.5,
        key="greeks_dividend"
    ) / 100

    option_type = st.radio(
        "Option type for numerical analysis",
        ["call", "put"],
        format_func=str.capitalize,
        horizontal=True,
        key="greeks_option"
    )

    return {
        "stock_price": stock,
        "strike_price": strike,
        "time_to_expiration": expiration,
        "risk_free_rate": rate,
        "volatility": volatility,
        "dividend_yield": dividend,
        "option_type": option_type
    }


def comparison_data(parameters, relative_step):
    analytical = calculate_greeks(**parameters)

    numerical = numerical_greeks(
        **parameters,
        relative_step=relative_step
    )

    records = []

    for greek, information in GREEKS.items():
        exact = analytical[greek]
        estimate = numerical[greek]

        records.append({
            "Greek": information["name"],
            "Analytical": exact,
            "Numerical": estimate,
            "Signed error": estimate - exact,
            "Absolute error": abs(estimate - exact),
            "Unit": information["unit"]
        })

    return pd.DataFrame(records)


def sensitivity_data(parameters, greek, variable):
    stock = parameters["stock_price"]
    strike = parameters["strike_price"]

    if variable == "Underlying price":
        parameter_name = "stock_price"

        values = np.linspace(
            0.5 * min(stock, strike),
            1.5 * max(stock, strike),
            151
        )

        scale = 1

    elif variable == "Volatility":
        parameter_name = "volatility"
        values = np.linspace(0.05, 1.0, 151)
        scale = 100

    else:
        parameter_name = "time_to_expiration"
        values = np.linspace(0.05, 5.0, 151)
        scale = 1

    records = []

    for option_type in ["call", "put"]:
        for value in values:
            scenario = parameters.copy()

            scenario[parameter_name] = float(value)
            scenario["option_type"] = option_type

            result = calculate_greeks(**scenario)

            records.append({
                "Parameter": float(value) * scale,
                "Option type": option_type.capitalize(),
                "Sensitivity": result[greek]
            })

    return pd.DataFrame(records)


def sensitivity_chart(data, greek, variable):
    figure = go.Figure()

    for option_type, color in [
        ("Call", COLORS["primary"]),
        ("Put", COLORS["blue"])
    ]:
        subset = data[
            data["Option type"] == option_type
        ]

        figure.add_trace(
            go.Scatter(
                x=subset["Parameter"],
                y=subset["Sensitivity"],
                mode="lines",
                name=option_type,
                line={
                    "color": color,
                    "width": 2.3,
                    "dash": (
                        "solid"
                        if option_type == "Call"
                        else "dash"
                    )
                },
                hovertemplate=(
                    "Parameter: %{x:.4f}"
                    "<br>Sensitivity: %{y:.8f}"
                    "<extra></extra>"
                )
            )
        )

    axis_labels = {
        "Underlying price": "Underlying price",
        "Volatility": "Volatility (%)",
        "Time to expiration": "Time to expiration (years)"
    }

    figure.update_xaxes(
        title=axis_labels[variable]
    )

    figure.update_yaxes(
        title=GREEKS[greek]["name"]
    )

    figure.add_hline(
        y=0,
        line_color=COLORS["muted"],
        line_dash="dot"
    )

    return style_figure(figure, height=450)


def stability_data(parameters, greek):
    analytical = calculate_greeks(
        **parameters
    )[greek]

    records = []

    for exponent in range(1, 14):
        step = 10.0 ** (-exponent)

        numerical = numerical_greeks(
            **parameters,
            relative_step=step
        )[greek]

        records.append({
            "Relative step": step,
            "Analytical": analytical,
            "Numerical": numerical,
            "Signed error": numerical - analytical,
            "Absolute error": abs(numerical - analytical)
        })

    return pd.DataFrame(records)


def stability_chart(data):
    positive = data[
        data["Absolute error"] > 0
    ].sort_values("Relative step")

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=positive["Relative step"],
            y=positive["Absolute error"],
            mode="lines+markers",
            name="Finite-difference error",
            line={
                "color": COLORS["primary"],
                "width": 2
            },
            marker={"size": 7},
            hovertemplate=(
                "Relative step: %{x:.1e}"
                "<br>Absolute error: %{y:.3e}"
                "<extra></extra>"
            )
        )
    )

    figure.update_xaxes(
        title="Relative finite-difference step",
        type="log",
        autorange="reversed"
    )

    figure.update_yaxes(
        title="Absolute numerical error",
        type="log"
    )

    return style_figure(figure, height=420)


def render():
    page_header(
        "Research / Sensitivity Analysis",
        "Sensitivity Analysis",
        "Investigate analytical derivatives, numerical "
        "approximations and finite-difference stability."
    )

    parameters = model_inputs()

    analytical = calculate_greeks(**parameters)

    st.divider()

    st.subheader("Analytical sensitivities")

    metric_row([
        (
            information["name"],
            f"{analytical[greek]:.6f}"
        )
        for greek, information in GREEKS.items()
    ])

    st.caption(
        "Theta is reported per calendar day. "
        "Vega and Rho are reported per percentage point."
    )

    st.divider()

    curves_tab, comparison_tab, stability_tab = st.tabs([
        "Sensitivity curves",
        "Numerical comparison",
        "Numerical stability"
    ])

    with curves_tab:
        left, right = st.columns(2)

        greek = left.selectbox(
            "Sensitivity measure",
            list(GREEKS),
            format_func=lambda value: GREEKS[value]["name"]
        )

        variable = right.selectbox(
            "Independent variable",
            [
                "Underlying price",
                "Volatility",
                "Time to expiration"
            ]
        )

        information = GREEKS[greek]

        st.markdown(
            f"#### {information['description']}"
        )

        st.latex(information["formula"])
        st.caption(information["unit"])

        data = sensitivity_data(
            parameters,
            greek,
            variable
        )

        st.plotly_chart(
            sensitivity_chart(data, greek, variable),
            width="stretch",
            config={"displaylogo": False}
        )

        if greek in ["gamma", "vega"]:
            st.caption(
                "European call and put sensitivities "
                "coincide for this Greek under the "
                "Black-Scholes-Merton assumptions."
            )

        st.download_button(
            "Download sensitivity data",
            data.to_csv(index=False).encode("utf-8"),
            file_name=f"{greek}_sensitivity.csv",
            mime="text/csv"
        )

    with comparison_tab:
        st.subheader("Analytical and numerical derivatives")

        exponent = st.slider(
            "Finite-difference step exponent",
            min_value=1,
            max_value=13,
            value=3
        )

        relative_step = 10.0 ** (-exponent)

        st.caption(
            f"Relative step: {relative_step:.1e}"
        )

        data = comparison_data(
            parameters,
            relative_step
        )

        st.dataframe(
            data.style.format({
                "Analytical": "{:.8f}",
                "Numerical": "{:.8f}",
                "Signed error": "{:.3e}",
                "Absolute error": "{:.3e}"
            }),
            width="stretch",
            hide_index=True
        )

        st.download_button(
            "Download numerical comparison",
            data.to_csv(index=False).encode("utf-8"),
            file_name="greek_comparison.csv",
            mime="text/csv"
        )

        st.caption(
            "Each numerical derivative is compared with "
            "its corresponding analytical reference. "
            "Errors across different Greeks have "
            "different measurement units."
        )

    with stability_tab:
        st.subheader("Finite-difference stability")

        selected = st.selectbox(
            "Greek for stability experiment",
            list(GREEKS),
            format_func=lambda value: GREEKS[value]["name"],
            key="stability_greek"
        )

        data = stability_data(
            parameters,
            selected
        )

        best = data.loc[
            data["Absolute error"].idxmin()
        ]

        metric_row([
            (
                "Step sizes evaluated",
                str(len(data))
            ),
            (
                "Best observed step",
                f"{best['Relative step']:.1e}"
            ),
            (
                "Minimum observed error",
                f"{best['Absolute error']:.3e}"
            )
        ])

        st.plotly_chart(
            stability_chart(data),
            width="stretch",
            config={"displaylogo": False}
        )

        st.caption(
            "Zero errors are omitted from the logarithmic "
            "chart but retained in the table. The minimum "
            "observed error is specific to this experiment "
            "and is not a universal optimal step."
        )

        st.dataframe(
            data.style.format({
                "Relative step": "{:.1e}",
                "Analytical": "{:.8f}",
                "Numerical": "{:.8f}",
                "Signed error": "{:.3e}",
                "Absolute error": "{:.3e}"
            }),
            width="stretch",
            hide_index=True
        )

        st.download_button(
            "Download stability experiment",
            data.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected}_stability.csv",
            mime="text/csv"
        )

        st.markdown(
            """
            #### Numerical interpretation

            Larger finite-difference steps can introduce
            truncation error. Extremely small steps can
            amplify floating-point rounding and
            cancellation errors.

            The interaction between these effects
            determines the observed numerical accuracy.
            """
        )

    st.divider()

    st.caption(
        "All sensitivities are evaluated using synthetic "
        "parameters for computational research."
    )