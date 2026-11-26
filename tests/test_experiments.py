import csv

from experiments import run


def test_experiment_outputs(tmp_path):
    run(tmp_path)
    for name, expected_rows in (("tree", 64), ("monte_carlo", 16), ("greeks", 130)):
        with (tmp_path / f"{name}.csv").open(newline="", encoding="utf-8") as stream:
            assert len(list(csv.DictReader(stream))) == expected_rows
        assert (tmp_path / f"{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "Seed 20261126" in (tmp_path / "environment.txt").read_text(encoding="utf-8")
