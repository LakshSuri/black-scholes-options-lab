import json
import platform
from pathlib import Path
from importlib.metadata import version


def collect_environment():
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.system(),
        "operating_system_release": platform.release(),
        "architecture": platform.machine(),
        "dependencies": {
            "numpy": version("numpy"),
            "matplotlib": version("matplotlib"),
            "pytest": version("pytest")
        },
        "experiment_configuration": {
            "monte_carlo_seed": 42,
            "monte_carlo_replications": 100,
            "benchmark_seed": 42,
            "benchmark_replications": 30
        },
        "reproducibility_notes": [
            "Stochastic experiments use fixed random seeds.",
            "Simulation budgets include pilot samples.",
            "Runtime measurements depend on hardware and system load.",
            "Floating-point results may vary across environments."
        ]
    }


def save_environment(path="results/environment.json"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    metadata = collect_environment()

    with path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    return metadata


if __name__ == "__main__":
    save_environment()
    print("Research environment metadata saved.")
