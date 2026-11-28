from pathlib import Path

import streamlit as st


COLORS = {
    "background": "#191A17",
    "surface": "#23251F",
    "border": "#44473D",
    "text": "#F1EFE7",
    "muted": "#BDC2B3",
    "primary": "#FF925F",
    "blue": "#99BCE8",
    "amber": "#A5D5BD",
    "gray": "#D1CCBA"
}

METHOD_COLORS = {
    "standard": COLORS["gray"],
    "antithetic": COLORS["blue"],
    "control": COLORS["amber"],
    "combined": COLORS["primary"]
}

REPOSITORY = (
    "https://github.com/LakshSuri/derivatives-pricing-lab"
)


def apply_styles():
    stylesheet = Path(__file__).resolve().parents[1] / "static" / "laboratory.css"
    st.html(stylesheet)


def sidebar_brand():
    st.sidebar.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;">
            <svg width="40" height="40" viewBox="0 0 40 40"
                 xmlns="http://www.w3.org/2000/svg"
                 aria-hidden="true" focusable="false">
                <rect width="40" height="40" rx="5" fill="#393124"/>
                <path d="M10 7 H23 L30 14 V32 H10 Z"
                      fill="#F0C477" fill-opacity=".08"
                      stroke="#F0C477" stroke-width="1.5" stroke-linejoin="round"/>
                <path d="M23 7 V14 H30 M15 18 H24 M15 22 H20"
                      fill="none" stroke="#F0C477" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="27.5" cy="28" r="7.5" fill="#393124" stroke="#F0C477" stroke-width="1.5"/>
                <path d="M24 28 H31 M28.5 25.5 L31 28 L28.5 30.5"
                      fill="none" stroke="#F0C477" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div>
                <div class="laboratory-wordmark">
                    DERIVATIVES LAB
                </div>
                <div class="laboratory-subtitle">
                    Computational Research
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def page_header(section, title, description):
    st.caption(section.upper())
    st.title(title)
    st.markdown(description)
    st.divider()


def metric_row(items):
    columns = st.columns(len(items))

    for column, (label, value) in zip(columns, items):
        column.metric(label, value)


def style_figure(figure, height=400):
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font={
            "family": "Arial, sans-serif",
            "size": 12,
            "color": COLORS["text"]
        },
        margin={
            "l": 55,
            "r": 25,
            "t": 35,
            "b": 50
        },
        height=height,
        hovermode="closest",
        legend={
            "orientation": "h",
            "y": 1.08,
            "x": 0
        }
    )

    figure.update_xaxes(
        gridcolor=COLORS["border"],
        linecolor=COLORS["border"],
        zerolinecolor=COLORS["border"]
    )

    figure.update_yaxes(
        gridcolor=COLORS["border"],
        linecolor=COLORS["border"],
        zerolinecolor=COLORS["border"]
    )

    return figure


def footer():
    st.divider()

    st.caption(
        "Derivatives Pricing Laboratory | "
        "Educational and computational research"
    )

    st.markdown(
        f"[Source code]({REPOSITORY}) · "
        f"[Technical report]({REPOSITORY}/blob/main/"
        "research/technical_report.md) · "
        f"[MIT License]({REPOSITORY}/blob/main/LICENSE)"
    )
