import pytest
from valuation_api import valuation
from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks


def query(**changes):
    a = dict(spot="100", strike="100", years="1", rate="5", volatility="20", dividend="2", kind="call")
    a.update(changes)
    return {k:[v] for k,v in a.items()}

@pytest.mark.parametrize("kind,fn", [("call",black_scholes_call),("put",black_scholes_put)])
def test_matches_engine(kind,fn):
    d=valuation(query(kind=kind))
    assert d["value"] == fn(100,100,1,.05,.2,.02)
    assert d["greeks"] == calculate_greeks(100,100,1,.05,.2,option_type=kind,dividend_yield=.02)
    assert len(d["curve"]) == 41
    for p in d["curve"]:
        assert p["price"] == fn(p["spot"],100,1,.05,.2,.02)
    s=d["surface"]
    assert len(s["values"]) == len(s["vols"]) == 21
    for v,row in zip(s["vols"],s["values"]):
        assert len(row) == len(s["spots"]) == 21
        for x,z in zip(s["spots"],row):
            assert z == fn(x,100,1,.05,v/100,.02)

@pytest.mark.parametrize("changes", [{"spot":"0"},{"years":"nan"},{"volatility":"101"},{"kind":"invalid"},{"dividend":"-1"},{"rate":"inf"},{"strike":""}])
def test_invalid(changes):
    with pytest.raises(ValueError): valuation(query(**changes))

def test_duplicate():
    q=query(); q["spot"].append("101")
    with pytest.raises(ValueError): valuation(q)
