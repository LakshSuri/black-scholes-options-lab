import csv

from research.derivatives.study import run


def test_volatility_recovery_experiment(tmp_path):
    run(tmp_path)
    with (tmp_path / "volatility.csv").open() as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 6
    assert max(float(row["absolute_error"]) for row in rows) < 1e-10
