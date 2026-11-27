from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from web.components import (
    COLORS,
    METHOD_COLORS,
    REPOSITORY,
    page_header,
    metric_row,
    style_figure
)


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "results" / "data"


@st.cache_data
def load_convergence_data():
    return pd.read_csv(
        DATA / "monte_carlo_summary.csv"
    )


def convergence_chart(data, selected_budget=None):
    figure = go.Figure()

    for method in METHOD_COLORS:
        subset = data[
            data["method"] == method
        ].sort_values("budget")

        figure.add_trace(
            go.Scatter(
                x=subset["budget"],
                y=subset["rmse"],
                mode="lines+markers",
                name=method.capitalize(),
                line={
                    "color": METHOD_COLORS[method],
                    "width": 2
                },
                marker={
                    "size": [12 if n == selected_budget else 6 for n in subset["budget"]],
                    "line": {"width": 1, "color": COLORS["background"]}
                },
                hovertemplate=(
                    "Evaluations: %{x:,}"
                    "<br>RMSE: %{y:.6f}"
                    "<extra></extra>"
                )
            )
        )

    figure.update_xaxes(
        title="Total simulation evaluations",
        type="log",
        tickvals=[1024, 4096, 16384, 65536],
        ticktext=["1,024", "4,096", "16,384", "65,536"]
    )

    figure.update_yaxes(
        title="Root mean squared error",
        type="log"
    )

    style_figure(figure, height=430)
    figure.update_layout(hovermode="x unified")
    return figure


def render():
    page_header(
        "Research / Overview",
        "Derivatives Pricing Laboratory",
        "A computational workspace for option valuation, "
        "numerical approximation and statistical research."
    )

    metric_row([
        ("Pricing methods", "06"),
        ("Research studies", "05"),
        ("Recorded observations", "2,958"),
        ("Released validation tests", "309")
    ])

    st.divider()

    st.subheader("Monte Carlo convergence")

    st.caption(
        "Root mean squared pricing error across four "
        "estimators and four simulation budgets."
    )

    data = load_convergence_data()

    budgets = sorted(int(n) for n in data["budget"].unique())
    budget = st.select_slider(
        "Evaluations per run",
        options=budgets,
        value=budgets[-1],
        format_func=lambda count: f"{count:,}",
        key="overview_budget"
    )
    if st.button("Replay convergence curves", key="replay_convergence"):
        st.session_state["convergence_take"] = not st.session_state.get(
            "convergence_take", False
        )
    take = "b" if st.session_state.get("convergence_take") else "a"
    with st.container(key=f"study-{take}"):
        st.plotly_chart(
            convergence_chart(data, budget),
            width="stretch",
            theme=None,
            config={"displaylogo": False}
        )

    selected_rows = data[data["budget"] == budget].set_index("method")

    standard_rmse = selected_rows.loc[
        "standard", "rmse"
    ]

    combined_rmse = selected_rows.loc[
        "combined", "rmse"
    ]

    reduction = (
        1 - combined_rmse / standard_rmse
    ) * 100

    efficiency = selected_rows.loc[
        "combined", "relative_efficiency"
    ]

    coverage = selected_rows.loc[
        "combined", "coverage"
    ]

    metric_row([
        ("Combined RMSE", f"{combined_rmse:.6f}"),
        ("RMSE reduction", f"{reduction:.1f}%"),
        ("Relative MSE efficiency", f"{efficiency:.2f}"),
        ("Empirical coverage", f"{coverage:.0%}")
    ])

    st.caption(
        "Results are calculated from the recorded "
        f"{budget:,}-evaluation experiment. Relative MSE "
        "efficiency does not represent a runtime speedup."
    )

    st.divider()

    st.subheader("Research framework")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Mathematical methods")

        st.markdown(
            """
            - Black-Scholes-Merton analytical pricing
            - Cox-Ross-Rubinstein binomial valuation
            - Monte Carlo variance reduction
            - Analytical and numerical Greeks
            - Implied volatility inversion
            """
        )

    with right:
        st.markdown("#### Research resources")

        st.markdown(
            f"""
            - [Technical research report](
            {REPOSITORY}/blob/main/research/technical_report.md)
            - [Experimental datasets](
            {REPOSITORY}/tree/main/results/data)
            - [Research figures](
            {REPOSITORY}/tree/main/results/figures)
            - [Computational environment](
            {REPOSITORY}/blob/main/results/environment.json)
            - [Versioned releases](
            {REPOSITORY}/releases)
            """
        )

    st.info(
        "The laboratory uses synthetic market parameters "
        "to evaluate computational methods under controlled "
        "mathematical assumptions."
    )
