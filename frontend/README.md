# Valuation Laboratory — custom frontend preview

React and TypeScript interface for European valuation, analytical Greeks, pricing curve and rotatable price/volatility surface. All values are computed by the existing Python pricing and analysis modules. All seven original Streamlit workspaces remain available. This preview does not replace lattice, Monte Carlo, implied volatility, numerical Greek or research library features.

From the repository root activate the existing virtual environment and run `python valuation_api.py`. In a second terminal run `cd frontend && npm install && npm run build && npm run dev`. Open http://127.0.0.1:5175. Run `python -m pytest -q` before committing. The loopback API is development-only; no production hosting is configured.
