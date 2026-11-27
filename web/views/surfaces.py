import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks

from web.components import (
    COLORS,
    page_header,
    metric_row,
    style_figure
)


MEASURES = {
    "price": "Option value",
    "delta": "Delta",
    "gamma": "Gamma",
    "theta": "Theta",
    "vega": "Vega",
    "rho": "Rho"
}

UNITS = {
    "price": "Price units",
    "delta": "Value per underlying price unit",
    "gamma": "Value per squared underlying price unit",
    "theta": "Value per calendar day",
    "vega": "Value per volatility percentage point",
    "rho": "Value per interest rate percentage point"
}

AXES = {
    "stock_price": "Underlying price",
    "volatility": "Volatility (%)",
    "time_to_expiration": "Expiration (years)"
}

AXIS_PAIRS = {
    "Underlying price / Volatility": (
        "stock_price",
        "volatility"
    ),
    "Underlying price / Expiration": (
        "stock_price",
        "time_to_expiration"
    ),
    "Volatility / Expiration": (
        "volatility",
        "time_to_expiration"
    )
}

SURFACE_COLORS = [
    [0.00, "#172A40"],
    [0.25, "#315F78"],
    [0.50, "#398F91"],
    [0.75, "#69D3B5"],
    [1.00, "#E0C889"]
]


def model_inputs():
    st.subheader("Model parameters")

    specifications = [
        (
            "stock_price",
            "Underlying price",
            1.0, 1000.0, 100.0, 5.0, 1
        ),
        (
            "strike_price",
            "Strike price",
            1.0, 1000.0, 100.0, 5.0, 1
        ),
        (
            "time_to_expiration",
            "Time to expiration (years)",
            0.05, 5.0, 1.0, 0.05, 1
        ),
        (
            "risk_free_rate",
            "Risk-free rate (%)",
            -5.0, 15.0, 5.0, 0.5, 100
        ),
        (
            "volatility",
            "Volatility (%)",
            5.0, 100.0, 20.0, 1.0, 100
        ),
        (
            "dividend_yield",
            "Dividend yield (%)",
            0.0, 15.0, 2.0, 0.5, 100
        )
    ]

    parameters = {}

    columns = st.columns(3)

    for index, specification in enumerate(specifications):
        (
            name, label, minimum, maximum,
            default, step, scale
        ) = specification

        parameters[name] = columns[
            index % 3
        ].number_input(
            label,
            min_value=minimum,
            max_value=maximum,
            value=default,
            step=step,
            key=f"surface_{name}"
        ) / scale

    parameters["option_type"] = st.radio(
        "Option type",
        ["call", "put"],
        format_func=str.capitalize,
        horizontal=True,
        key="surface_option"
    )

    return parameters


def evaluate(parameters, measure):
    if measure == "price":
        inputs = parameters.copy()

        option_type = inputs.pop("option_type")

        function = (
            black_scholes_call
            if option_type == "call"
            else black_scholes_put
        )

        return function(**inputs)

    return calculate_greeks(
        **parameters
    )[measure]


def axis_values(parameters, variable, resolution):
    if variable == "stock_price":
        stock = parameters["stock_price"]
        strike = parameters["strike_price"]

        minimum = 0.5 * min(stock, strike)
        maximum = 1.5 * max(stock, strike)

    elif variable == "volatility":
        minimum = 0.05
        maximum = 1.0

    elif variable == "time_to_expiration":
        minimum = 0.05
        maximum = 5.0

    else:
        raise ValueError("Unsupported surface axis.")

    return np.linspace(
        minimum,
        maximum,
        resolution
    )


def display_axis(values, variable):
    if variable == "volatility":
        return np.asarray(values) * 100

    return np.asarray(values)


@st.cache_data(max_entries=16)
def generate_surface(
    parameters,
    measure,
    x_variable,
    y_variable,
    resolution
):
    if x_variable == y_variable:
        raise ValueError(
            "Surface axes must be different."
        )

    x_values = axis_values(
        parameters,
        x_variable,
        resolution
    )

    y_values = axis_values(
        parameters,
        y_variable,
        resolution
    )

    z_values = np.empty(
        (len(y_values), len(x_values))
    )

    for row, y_value in enumerate(y_values):
        for column, x_value in enumerate(x_values):
            scenario = parameters.copy()

            scenario[x_variable] = float(x_value)
            scenario[y_variable] = float(y_value)

            z_values[row, column] = evaluate(
                scenario,
                measure
            )

    return x_values, y_values, z_values


def reference_point(
    parameters,
    measure,
    x_variable,
    y_variable
):
    x = parameters[x_variable]
    y = parameters[y_variable]

    if x_variable == "volatility":
        x *= 100

    if y_variable == "volatility":
        y *= 100

    z = evaluate(parameters, measure)

    return x, y, z


def surface_chart(
    x_values,
    y_values,
    z_values,
    x_variable,
    y_variable,
    measure,
    reference
):
    figure = go.Figure()

    figure.add_trace(
        go.Surface(
            x=display_axis(
                x_values, x_variable
            ),
            y=display_axis(
                y_values, y_variable
            ),
            z=z_values,
            colorscale=SURFACE_COLORS,
            colorbar={
                "title": MEASURES[measure],
                "len": 0.75
            },
            contours={
                "z": {
                    "show": True,
                    "usecolormap": True,
                    "project_z": True
                }
            },
            hovertemplate=(
                AXES[x_variable] + ": %{x:.3f}"
                "<br>" + AXES[y_variable] + ": %{y:.3f}"
                "<br>" + MEASURES[measure] + ": %{z:.6f}"
                "<extra></extra>"
            ),
            name=MEASURES[measure],
            showlegend=False
        )
    )

    figure.add_trace(
        go.Scatter3d(
            x=[reference[0]],
            y=[reference[1]],
            z=[reference[2]],
            mode="markers",
            name="Reference scenario",
            marker={
                "size": 6,
                "color": "#F5F5F5",
                "symbol": "diamond"
            }
        )
    )

    axis_style = {
        "backgroundcolor": COLORS["surface"],
        "gridcolor": COLORS["border"],
        "showbackground": True,
        "zerolinecolor": COLORS["muted"]
    }

    figure.update_layout(
        scene={
            "xaxis": {
                **axis_style,
                "title": AXES[x_variable]
            },
            "yaxis": {
                **axis_style,
                "title": AXES[y_variable]
            },
            "zaxis": {
                **axis_style,
                "title": MEASURES[measure]
            },
            "camera": {
                "eye": {
                    "x": 1.55,
                    "y": 1.55,
                    "z": 1.15
                }
            },
            "aspectmode": "cube"
        }
    )

    figure = style_figure(
        figure,
        height=650
    )

    figure.update_layout(
        margin={
            "l": 0,
            "r": 0,
            "t": 30,
            "b": 0
        }
    )

    return figure


def contour_chart(
    x_values,
    y_values,
    z_values,
    x_variable,
    y_variable,
    measure,
    reference
):
    figure = go.Figure()

    figure.add_trace(
        go.Contour(
            x=display_axis(
                x_values, x_variable
            ),
            y=display_axis(
                y_values, y_variable
            ),
            z=z_values,
            colorscale=SURFACE_COLORS,
            ncontours=20,
            contours={
                "coloring": "heatmap",
                "showlabels": True
            },
            line={"width": 0.7},
            colorbar={
                "title": MEASURES[measure]
            },
            hovertemplate=(
                AXES[x_variable] + ": %{x:.3f}"
                "<br>" + AXES[y_variable] + ": %{y:.3f}"
                "<br>" + MEASURES[measure] + ": %{z:.6f}"
                "<extra></extra>"
            )
        )
    )

    figure.add_trace(
        go.Scatter(
            x=[reference[0]],
            y=[reference[1]],
            mode="markers",
            name="Reference scenario",
            marker={
                "size": 11,
                "color": "#F5F5F5",
                "symbol": "diamond",
                "line": {
                    "color": "#0B1016",
                    "width": 1
                }
            }
        )
    )

    figure.update_xaxes(
        title=AXES[x_variable]
    )

    figure.update_yaxes(
        title=AXES[y_variable]
    )

    return style_figure(
        figure,
        height=520
    )


def export_data(
    parameters,
    measure,
    x_variable,
    y_variable,
    x_values,
    y_values,
    z_values
):
    records = []

    for row, y_value in enumerate(y_values):
        for column, x_value in enumerate(x_values):
            scenario = parameters.copy()

            scenario[x_variable] = float(x_value)
            scenario[y_variable] = float(y_value)

            records.append({
                **scenario,
                "measure": measure,
                "value": float(
                    z_values[row, column]
                ),
                "unit": UNITS[measure],
                "x_axis": x_variable,
                "y_axis": y_variable
            })

    return pd.DataFrame(records)


def render():
    page_header(
        "Research / Pricing Surfaces",
        "Pricing Surfaces",
        "Explore the multidimensional structure of "
        "option valuation and analytical sensitivities."
    )

    parameters = model_inputs()

    st.divider()

    st.subheader("Surface configuration")

    left, center, right = st.columns(3)

    measure = left.selectbox(
        "Dependent variable",
        list(MEASURES),
        format_func=lambda value: MEASURES[value]
    )

    selected_pair = center.selectbox(
        "Independent variables",
        list(AXIS_PAIRS)
    )

    resolution = right.selectbox(
        "Grid resolution",
        [25, 41, 61],
        index=1,
        format_func=lambda size: (
            f"{size} x {size}"
        )
    )

    x_variable, y_variable = AXIS_PAIRS[
        selected_pair
    ]

    x_values, y_values, z_values = generate_surface(
        parameters,
        measure,
        x_variable,
        y_variable,
        resolution
    )

    reference = reference_point(
        parameters,
        measure,
        x_variable,
        y_variable
    )

    metric_row([
        (
            "Reference scenario",
            f"{reference[2]:.6f}"
        ),
        (
            "Surface minimum",
            f"{np.min(z_values):.6f}"
        ),
        (
            "Surface maximum",
            f"{np.max(z_values):.6f}"
        ),
        (
            "Grid evaluations",
            f"{z_values.size:,}"
        )
    ])

    st.caption(
        f"Dependent variable: {MEASURES[measure]}. "
        f"Units: {UNITS[measure]}."
    )

    st.divider()

    surface_tab, contour_tab, data_tab = st.tabs([
        "3D surface",
        "Contour analysis",
        "Numerical grid"
    ])

    with surface_tab:
        st.subheader(
            f"{MEASURES[measure]} surface"
        )

        st.plotly_chart(
            surface_chart(
                x_values,
                y_values,
                z_values,
                x_variable,
                y_variable,
                measure,
                reference
            ),
            width="stretch",
            theme=None,
            config={"displaylogo": False}
        )

        st.caption(
            "Drag to rotate the surface and scroll "
            "to zoom. The white diamond identifies "
            "the reference parameter configuration."
        )

    with contour_tab:
        st.subheader("Two-dimensional contour map")

        st.plotly_chart(
            contour_chart(
                x_values,
                y_values,
                z_values,
                x_variable,
                y_variable,
                measure,
                reference
            ),
            width="stretch",
            theme=None,
            config={"displaylogo": False}
        )

        st.caption(
            "Contour lines connect parameter "
            "combinations with approximately equal "
            "model values or sensitivities."
        )

    with data_tab:
        st.subheader("Computed numerical observations")

        data = export_data(
            parameters,
            measure,
            x_variable,
            y_variable,
            x_values,
            y_values,
            z_values
        )

        st.dataframe(
            data,
            width="stretch",
            hide_index=True
        )

        st.download_button(
            "Download complete surface dataset",
            data.to_csv(index=False).encode("utf-8"),
            file_name=f"{measure}_surface.csv",
            mime="text/csv"
        )

        st.caption(
            "Exported interest rates, dividend yields "
            "and volatility use decimal notation. "
            "Expiration is measured in years."
        )

    st.divider()

    st.subheader("Mathematical interpretation")

    st.latex(
        r"V=V(S,K,T,r,\sigma,q)"
    )

    st.markdown(
        """
        Each surface evaluates a dependent variable
        over a two-dimensional parameter grid.

        The remaining model parameters are held
        constant. This isolates the mathematical
        relationship between the selected variables
        and the model output.

        Increasing grid resolution improves visual
        sampling density but does not change the
        analytical pricing formula.
        """
    )

    st.caption(
        "These surfaces represent theoretical model "
        "outputs under synthetic assumptions, not "
        "observed market prices or forecasts."
    )