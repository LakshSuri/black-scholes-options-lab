import streamlit as st

from web.components import (
    REPOSITORY,
    apply_styles,
    sidebar_brand,
    footer
)

from web.views import (
    overview,
    valuation,
    sensitivity,
    simulation,
    volatility,
    surfaces,
    library
)


st.set_page_config(
    page_title="Derivatives Pricing Laboratory",
    layout="wide",
    initial_sidebar_state="expanded"
)


PAGE_HANDLERS = {
    "Overview": overview.render,
    "Option Valuation": valuation.render,
    "Sensitivity Analysis": sensitivity.render,
    "Monte Carlo Laboratory": simulation.render,
    "Implied Volatility": volatility.render,
    "Pricing Surfaces": surfaces.render,
    "Research Library": library.render
}


PAGES = tuple(PAGE_HANDLERS)


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
        "Laboratory release 1.1.0"
    )

    return selected


def main():
    apply_styles()

    selected = navigation()

    PAGE_HANDLERS[selected]()

    footer()


if __name__ == "__main__":
    main()