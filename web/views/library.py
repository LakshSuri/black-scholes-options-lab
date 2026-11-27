import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from web.components import (
    REPOSITORY,
    page_header,
    metric_row
)


ROOT = Path(__file__).resolve().parents[2]

DATA_DIRECTORY = ROOT / "results" / "data"
FIGURE_DIRECTORY = ROOT / "results" / "figures"
REPORT_PATH = ROOT / "research" / "technical_report.md"
ENVIRONMENT_PATH = ROOT / "results" / "environment.json"


DATASETS = {
    "tree_convergence.csv": (
        "Binomial convergence",
        "European lattice approximation errors across "
        "different strikes and tree resolutions.",
        ["option_type", "strike", "step_parity", "steps"]
    ),
    "monte_carlo_summary.csv": (
        "Monte Carlo summary",
        "Aggregated estimator accuracy, uncertainty, "
        "coverage and relative efficiency.",
        ["method", "budget"]
    ),
    "monte_carlo_replications.csv": (
        "Monte Carlo replications",
        "Individual stochastic estimates and "
        "confidence interval observations.",
        ["method", "budget", "covered"]
    ),
    "greek_stability.csv": (
        "Greek numerical stability",
        "Finite-difference approximation errors across "
        "scenarios and relative step sizes.",
        ["scenario", "option_type", "greek", "relative_step"]
    ),
    "optimal_greek_steps.csv": (
        "Observed optimal Greek steps",
        "Best observed finite-difference step sizes "
        "within the recorded numerical experiments.",
        ["scenario", "option_type", "greek"]
    ),
    "volatility_conditioning.csv": (
        "Implied volatility conditioning",
        "Volatility recovery and error amplification "
        "under synthetic price perturbations.",
        ["option_type", "strike", "expiration", "status"]
    ),
    "benchmark_summary.csv": (
        "Computational benchmark summary",
        "Aggregated runtime and numerical accuracy "
        "across pricing implementations.",
        ["model", "resolution"]
    ),
    "benchmark_replications.csv": (
        "Computational benchmark replications",
        "Individual runtime measurements and "
        "corresponding pricing errors.",
        ["model", "resolution"]
    )
}


FIGURES = {
    "tree_convergence.png": (
        "01 / Binomial convergence",
        "Signed lattice pricing errors across odd "
        "and even tree resolutions."
    ),
    "monte_carlo_convergence.png": (
        "02 / Monte Carlo convergence",
        "Root mean squared error across stochastic "
        "estimators and simulation budgets."
    ),
    "confidence_coverage.png": (
        "03 / Confidence interval coverage",
        "Empirical coverage compared with the "
        "nominal confidence level."
    ),
    "greek_stability.png": (
        "04 / Numerical Greek stability",
        "Finite-difference error across relative "
        "perturbation sizes."
    ),
    "volatility_conditioning.png": (
        "05 / Implied volatility conditioning",
        "Local inverse sensitivity and the "
        "conditioning of volatility recovery."
    ),
    "performance_benchmark.png": (
        "06 / Computational performance",
        "The relationship between measured runtime "
        "and numerical approximation error."
    )
}


PRIMARY_DATASETS = [
    "tree_convergence.csv",
    "monte_carlo_replications.csv",
    "greek_stability.csv",
    "volatility_conditioning.csv",
    "benchmark_replications.csv"
]


@st.cache_data
def load_dataset(filename):
    if filename not in DATASETS:
        raise ValueError("Unknown research dataset.")

    path = DATA_DIRECTORY / filename

    if filename in [
        "monte_carlo_replications.csv",
        "benchmark_replications.csv"
    ]:
        return pd.read_csv(
            path,
            dtype={"seed": "string"}
        )

    return pd.read_csv(path)


@st.cache_data
def load_environment():
    return json.loads(
        ENVIRONMENT_PATH.read_text(
            encoding="utf-8"
        )
    )


def archive_summary():
    records = []

    for filename, information in DATASETS.items():
        title, description, _ = information

        data = load_dataset(filename)

        records.append({
            "Dataset": title,
            "Observations": len(data),
            "Variables": len(data.columns),
            "File": filename
        })

    return pd.DataFrame(records)


def filter_dataset(data, filename, fields):
    filtered = data.copy()

    columns = st.columns(2)

    for index, field in enumerate(fields):
        if field not in data.columns:
            continue

        options = sorted(
            data[field].dropna().unique().tolist()
        )

        selected = columns[
            index % 2
        ].multiselect(
            field.replace("_", " ").title(),
            options=options,
            key=f"library_{filename}_{field}"
        )

        if selected:
            filtered = filtered[
                filtered[field].isin(selected)
            ]

    return filtered


def render_datasets():
    st.subheader("Experimental data archive")

    summary = archive_summary()

    st.dataframe(
        summary,
        width="stretch",
        hide_index=True
    )

    st.divider()

    filename = st.selectbox(
        "Research dataset",
        list(DATASETS),
        format_func=lambda name: DATASETS[name][0]
    )

    title, description, fields = DATASETS[filename]

    st.markdown(f"### {title}")
    st.write(description)

    original = load_dataset(filename)

    st.markdown("#### Dataset filters")

    st.caption(
        "Leave a filter empty to include all "
        "values for that variable."
    )

    filtered = filter_dataset(
        original,
        filename,
        fields
    )

    metric_row([
        ("Original observations", f"{len(original):,}"),
        ("Filtered observations", f"{len(filtered):,}"),
        ("Variables", str(len(original.columns)))
    ])

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
        height=420
    )

    left, right = st.columns(2)

    left.download_button(
        "Download filtered dataset",
        filtered.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=f"filtered_{filename}",
        mime="text/csv"
    )

    right.download_button(
        "Download original dataset",
        (DATA_DIRECTORY / filename).read_bytes(),
        file_name=filename,
        mime="text/csv"
    )

    with st.expander("Dataset structure"):
        structure = pd.DataFrame({
            "Variable": original.columns,
            "Data type": [
                str(dtype)
                for dtype in original.dtypes
            ],
            "Missing observations": (
                original.isna().sum().to_numpy()
            )
        })

        st.dataframe(
            structure,
            width="stretch",
            hide_index=True
        )

    st.caption(
        "Filtering does not modify the original "
        "experimental data. Random seeds are preserved "
        "as text to avoid integer precision loss."
    )

    st.markdown(
        f"[View original file on GitHub]("
        f"{REPOSITORY}/blob/main/results/data/"
        f"{filename})"
    )


def render_figures():
    st.subheader("Research figure gallery")

    st.caption(
        "Original publication-quality figures generated "
        "by the reproducible research pipeline."
    )

    filename = st.selectbox(
        "Research figure",
        list(FIGURES),
        format_func=lambda name: FIGURES[name][0]
    )

    title, description = FIGURES[filename]

    path = FIGURE_DIRECTORY / filename

    st.markdown(f"### {title}")
    st.write(description)

    st.image(
        path.read_bytes(),
        width="stretch"
    )

    st.download_button(
        "Download original research figure",
        path.read_bytes(),
        file_name=filename,
        mime="image/png"
    )

    st.caption(
        "Original PNG output generated at 300 DPI."
    )

    st.markdown(
        f"[View figure on GitHub]("
        f"{REPOSITORY}/blob/main/results/figures/"
        f"{filename})"
    )

    st.divider()

    st.subheader("Figure collection")

    columns = st.columns(2)

    for index, (name, information) in enumerate(
        FIGURES.items()
    ):
        figure_title, _ = information

        with columns[index % 2]:
            st.image(
                (FIGURE_DIRECTORY / name).read_bytes(),
                width="stretch"
            )

            st.caption(figure_title)


def render_report():
    st.subheader("Technical research report")

    report = REPORT_PATH.read_text(
        encoding="utf-8"
    )

    sections = re.split(
        r"(?m)^## ",
        report
    )

    section_contents = {}

    for section in sections[1:]:
        heading, _, body = section.partition("\n")

        section_contents[heading.strip()] = body.strip()

    st.markdown(
        "### Computational Analysis of "
        "Derivatives Pricing Models"
    )

    selected = st.selectbox(
        "Report section",
        list(section_contents)
    )

    st.markdown(f"#### {selected}")

    body = section_contents[selected]

    parts = re.split(
        r"(!\[[^\]]*\]\("
        r"\.\./results/figures/[^)]+\))",
        body
    )

    for part in parts:
        match = re.fullmatch(
            r"!\[([^\]]*)\]\("
            r"\.\./results/figures/([^)]+)\)",
            part
        )

        if match:
            caption, filename = match.groups()

            if filename in FIGURES:
                st.image(
                    (FIGURE_DIRECTORY / filename).read_bytes(),
                    caption=caption,
                    width="stretch"
                )

        elif part.strip():
            st.markdown(part)

    st.download_button(
        "Download complete technical report",
        REPORT_PATH.read_bytes(),
        file_name="technical_report.md",
        mime="text/markdown"
    )

    st.markdown(
        f"[Read full technical report on GitHub]("
        f"{REPOSITORY}/blob/main/"
        "research/technical_report.md)"
    )


def render_environment():
    st.subheader("Recorded computational environment")

    environment = load_environment()

    metric_row([
        (
            "Python",
            environment["python_version"]
        ),
        (
            "Implementation",
            environment["python_implementation"]
        ),
        (
            "Operating system",
            environment["operating_system"]
        ),
        (
            "Architecture",
            environment["architecture"]
        )
    ])

    st.caption(
        "This describes the environment used to generate "
        "the original research results, not necessarily "
        "the environment hosting this website."
    )

    left, right = st.columns(2)

    with left:
        st.markdown("#### Recorded dependencies")

        dependencies = pd.DataFrame([
            {
                "Dependency": name,
                "Version": version
            }
            for name, version in
            environment["dependencies"].items()
        ])

        st.dataframe(
            dependencies,
            width="stretch",
            hide_index=True
        )

    with right:
        st.markdown("#### Experiment configuration")

        configuration = pd.DataFrame([
            {
                "Parameter": name.replace("_", " ").title(),
                "Value": str(value)
            }
            for name, value in
            environment[
                "experiment_configuration"
            ].items()
        ])

        st.dataframe(
            configuration,
            width="stretch",
            hide_index=True
        )

    st.markdown("#### Reproducibility considerations")

    for note in environment["reproducibility_notes"]:
        st.write(f"- {note}")

    st.download_button(
        "Download environment metadata",
        ENVIRONMENT_PATH.read_bytes(),
        file_name="environment.json",
        mime="application/json"
    )


def render_reproduction():
    st.subheader("Reproduce the research")

    st.write(
        "The complete numerical research pipeline can "
        "be executed independently of this website."
    )

    st.markdown("#### 1. Clone the repository")

    st.code(
        f"git clone {REPOSITORY}.git\n"
        "cd derivatives-pricing-lab",
        language="bash"
    )

    st.markdown("#### 2. Prepare the environment")

    st.code(
        "python3 -m venv .venv\n"
        "source .venv/bin/activate\n"
        "python -m pip install -r requirements.txt",
        language="bash"
    )

    st.markdown("#### 3. Validate the software")

    st.code(
        "python -m pytest -q",
        language="bash"
    )

    st.markdown("#### 4. Reproduce the experiments")

    st.code(
        "python -m research.reproduce",
        language="bash"
    )

    st.markdown("#### 5. Launch the interactive laboratory")

    st.code(
        "python -m streamlit run app.py",
        language="bash"
    )

    st.info(
        "Reproduced research outputs are written to "
        "reproduced-results/ by default, preserving "
        "the original recorded datasets."
    )

    st.markdown(
        f"[Repository documentation]({REPOSITORY})"
        f" · [Release history]({REPOSITORY}/releases)"
        f" · [MIT License]("
        f"{REPOSITORY}/blob/main/LICENSE)"
    )


def render():
    page_header(
        "Research / Library",
        "Research Library",
        "Experimental datasets, scientific figures, "
        "technical documentation and reproducible "
        "computational research."
    )

    observations = sum(
        len(load_dataset(filename))
        for filename in PRIMARY_DATASETS
    )

    metric_row([
        ("Research datasets", str(len(DATASETS))),
        ("Research figures", str(len(FIGURES))),
        ("Recorded observations", f"{observations:,}"),
        ("Computational studies", "5")
    ])

    st.divider()

    data_tab, figures_tab, docs_tab = st.tabs([
        "Data archive",
        "Figure gallery",
        "Documentation"
    ], key="library_tabs", on_change="rerun")

    if data_tab.open:
        with data_tab:
            render_datasets()

    if figures_tab.open:
        with figures_tab:
            render_figures()

    if docs_tab.open:
        with docs_tab:
            render_report()

            st.divider()

            render_environment()

            st.divider()

            render_reproduction()

    st.divider()

    st.caption(
        "The archived results describe controlled "
        "computational experiments. Summary datasets "
        "are excluded from the primary observation "
        "count to prevent double counting."
    )
