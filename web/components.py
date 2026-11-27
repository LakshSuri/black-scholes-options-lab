import streamlit as st


COLORS = {
    "background": "#0B1016",
    "surface": "#141C25",
    "border": "#293440",
    "text": "#E5E9EF",
    "muted": "#94A3B8",
    "primary": "#69D3B5",
    "blue": "#639CC9",
    "amber": "#D6B77A",
    "gray": "#9AA9BC"
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
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1440px;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.035em;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid #293440;
        }

        [data-testid="stMetricValue"] {
            font-family: monospace;
            font-size: 2rem;
            letter-spacing: -0.04em;
        }

        [data-testid="stMetricLabel"] {
            color: #94A3B8;
        }

        hr {
            border-color: #293440;
        }

        .laboratory-wordmark {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: #E5E9EF;
        }

        .laboratory-subtitle {
            font-size: 0.75rem;
            color: #94A3B8;
            margin-top: 0.25rem;
        }

        .section-label {
            color: #69D3B5;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def sidebar_brand():
    st.sidebar.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;">
            <svg width="40" height="40"
                 viewBox="0 0 40 40"
                 xmlns="http://www.w3.org/2000/svg">
                <rect width="40" height="40" rx="5"
                      fill="#18302C"/>
                <path d="M8 8 V32 H33"
                      fill="none"
                      stroke="#78948D"
                      stroke-width="1"/>
                <path d="M8 30 C17 30 21 26 25 18
                         S31 7 34 6"
                      fill="none"
                      stroke="#69D3B5"
                      stroke-width="2.3"/>
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