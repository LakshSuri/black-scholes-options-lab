import argparse
from pathlib import Path

from experiments import run as run_experiments
from research.numerical_stability import run as run_stability
from research.volatility_conditioning import run as run_conditioning
from research.benchmarks import run as run_benchmarks
from research.figures import run as generate_figures
from research.environment import save_environment


def reproduce(output_directory="reproduced-results"):
    output = Path(output_directory)

    data = output / "data"
    figures = output / "figures"

    print("Starting computational research pipeline.\n")

    run_experiments(data)
    run_stability(data)
    run_conditioning(data)
    run_benchmarks(data)

    generate_figures(data, figures)

    save_environment(
        output / "environment.json"
    )

    print("\nResearch reproduction completed.")
    print(f"Datasets: {data}")
    print(f"Figures: {figures}")
    print(f"Metadata: {output / 'environment.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reproduce all derivatives research experiments"
    )

    parser.add_argument(
        "--output",
        default="reproduced-results",
        help="Directory for regenerated research results"
    )

    arguments = parser.parse_args()

    reproduce(arguments.output)
