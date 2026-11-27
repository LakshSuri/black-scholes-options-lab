import streamlit as st

from web.components import (
    REPOSITORY,
    apply_styles,
    sidebar_brand,
    page_header,
    footer
)

from web.views import (
    overview,
    valuation,
    sensitivity,
    simulation,
    volatility
)


st.set_page_config(
    page_title="Derivatives Pricing Laboratory",
    layout="wide",
    initial_sidebar_state="expanded"
)


PAGES = (
    "Overview",
    "Option Valuation",
    "Sensitivity Analysis",
    "Monte Carlo Laboratory",
    "Implied Volatility",
    "Pricing Surfaces",
    "Research Library"
)


PAGE_HANDLERS = {
    "Overview": overview.render,
    "Option Valuation": valuation.render,
    "Sensitivity Analysis": sensitivity.render,
    "Monte Carlo Laboratory": simulation.render,
    "Implied Volatility": volatility.render
}


PAGE_DESCRIPTIONS = {
    "Pricing Surfaces": (
        "Multidimensional visualization of "
        "theoretical option values."
    ),
    "Research Library": (
        "Computational datasets, experimental figures "
        "and reproducibility resources."
    )
}


def navigation():
    sidebar_brand()

    st.sidebar.divider()

    selected = st.sidebar.radio(
        "Research workspace",
        PAGES
    )

    st.sidebar.divider()

    st.sidebar.caption("RESOURCES")

    st.sidebar.markdown(
        f"[GitHub Repository]({REPOSITORY})"
    )

    st.sidebar.markdown(
        f"[Technical Report]({REPOSITORY}/blob/main/"
        "research/technical_report.md)"
    )

    st.sidebar.markdown(
        f"[Release History]({REPOSITORY}/releases)"
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "Core software release 1.0.1"
    )

    return selected


def main():
    apply_styles()

    selected = navigation()

    if selected in PAGE_HANDLERS:
        PAGE_HANDLERS[selected]()

    else:
        page_header(
            "Research Workspace",
            selected,
            PAGE_DESCRIPTIONS[selected]
        )

        st.info(
            "This workspace is currently under development."
        )

    footer()


if __name__ == "__main__":
    main()