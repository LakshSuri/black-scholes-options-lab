"""Local development API. All model values originate in the Python engine."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import json
import math
from pricing import black_scholes_call, black_scholes_put
from analysis import calculate_greeks

LIMITS = {"spot": (1, 1000), "strike": (1, 1000), "years": (.05, 5), "rate": (-5, 15), "volatility": (5, 100), "dividend": (0, 15)}


def valuation(query):
    if set(query) != set(LIMITS) | {"kind"} or any(len(v) != 1 for v in query.values()):
        raise ValueError("Supply exactly one value for every model parameter.")
    a = {}
    for key, (low, high) in LIMITS.items():
        a[key] = float(query[key][0])
        if not math.isfinite(a[key]) or not low <= a[key] <= high:
            raise ValueError(f"{key} must be between {low:g} and {high:g}.")
    kind = query["kind"][0]
    if kind not in ("call", "put"):
        raise ValueError("Select call or put.")
    fn = black_scholes_call if kind == "call" else black_scholes_put
    def price(s, vol):
        return fn(s, a["strike"], a["years"], a["rate"]/100, vol/100, a["dividend"]/100)
    low, high = .5 * min(a["spot"], a["strike"]), 1.5 * max(a["spot"], a["strike"])
    spots = [low+(high-low)*i/40 for i in range(41)]
    xs = [low+(high-low)*i/20 for i in range(21)]
    ys = [5+95*i/20 for i in range(21)]
    return {"assumptions": {**a, "kind": kind}, "value": price(a["spot"], a["volatility"]),
            "greeks": calculate_greeks(a["spot"], a["strike"], a["years"], a["rate"]/100, a["volatility"]/100, option_type=kind, dividend_yield=a["dividend"]/100),
            "curve": [{"spot": s, "price": price(s, a["volatility"])} for s in spots],
            "surface": {"spots": xs, "vols": ys, "values": [[price(s,v) for s in xs] for v in ys]}}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path == "/api/health":
            self.send_json(200, {"status": "ok"})
            return
        if path.path != "/api/valuation":
            self.send_json(404, {"error": "Unknown endpoint."})
            return
        try:
            data = valuation(parse_qs(path.query, keep_blank_values=True, max_num_fields=7))
            self.send_json(200, data)
        except (ValueError, OverflowError) as exc:
            self.send_json(400, {"error": str(exc)})


if __name__ == "__main__":
    print("Local valuation API: http://127.0.0.1:8766", flush=True)
    with ThreadingHTTPServer(("127.0.0.1", 8766), Handler) as server:
        server.serve_forever()
