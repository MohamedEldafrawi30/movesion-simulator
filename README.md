# Movesion Business Model Simulator

A professional-grade simulation engine for analyzing card program economics, pricing strategies, and B2B partnership scenarios. Built with FastAPI, Streamlit, and Python.

## Features

- **Comprehensive Simulation Engine**: Calculate monthly projections for revenue, costs, and profitability
- **Tiered Pricing Support**: Automatic calculation based on Wallester pricing tiers
- **B2B Fee Solver**: Automatically determine required employee fees to reach breakeven
- **Scenario Comparison**: Compare multiple scenarios side-by-side
- **Sensitivity Analysis**: Understand how key parameters affect profitability
- **Modern UI**: Interactive Streamlit dashboard with real-time visualization
- **RESTful API**: Full-featured FastAPI backend with OpenAPI documentation

## Quick Start

### Installation

1. **Clone and setup the project**:
   ```bash
   cd Traffic-Assignment
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

**Option 1: Quick Demo**
```bash
python main.py demo
```

**Option 2: API Server Only**
```bash
python main.py api
```
Then visit http://localhost:8000/docs for API documentation.

**Option 3: Full Application (API + UI)**

In terminal 1:
```bash
python main.py api
```

In terminal 2:
```bash
python main.py ui
```
Then visit http://localhost:8501 for the interactive dashboard.

## Project Structure

```
movesion_simulator/
├── api/                    # FastAPI backend
│   ├── main.py            # Application factory
│   ├── schemas.py         # Pydantic models
│   └── routes/            # API endpoints
│       ├── health.py      # Health checks
│       ├── pricing.py     # Pricing plan endpoints
│       └── simulation.py  # Simulation endpoints
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py        # Pydantic settings
├── data/                   # Data files
│   ├── pricing_plan_wallester.json
│   └── scenario_presets.json
├── engine/                 # Core simulation engine
│   ├── __init__.py
│   ├── model.py           # SimulationEngine class
│   ├── tiers.py           # Tiered pricing calculations
│   └── types.py           # Type definitions
├── tests/                  # Test suite
│   ├── test_api.py
│   ├── test_model.py
│   └── test_tiers.py
└── ui/                     # Streamlit frontend
    └── app.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/pricing/plan` | GET | Get pricing plan |
| `/api/v1/pricing/presets` | GET | Get scenario presets |
| `/api/v1/pricing/presets/{name}` | GET | Get specific preset |
| `/api/v1/simulation/run` | POST | Run simulation |
| `/api/v1/simulation/compare` | POST | Compare scenarios |
| `/api/v1/simulation/sensitivity/{param}` | POST | Sensitivity analysis |

## Scenario Configuration

A scenario consists of the following sections:

### Adoption
```json
{
  "start_active_cards": 3000,
  "monthly_net_adds": 100,
  "churn_rate": 0.02
}
```

### Usage
```json
{
  "spend_per_active_card_month": 200,
  "in_app_share": 0.5,
  "avg_ticket": 50,
  "ecom_share": 0.3,
  "eea_share": 0.95
}
```

### Commercial
```json
{
  "partner_fee_pct": 0.02,
  "interchange_pct": 0.002,
  "b2b": {
    "mode": "solve_employee_fee",
    "target": {"type": "breakeven", "months": 12}
  }
}
```

## Pricing Model

The simulator uses Wallester's pricing structure:

### Fixed Monthly Fees
- Program maintenance: €2,495/month
- Additional program: €995/month
- Dedicated BIN: €995/month
- Data enrichment: €500/month
- 3DS Out-of-band: €1,000/month

### Tiered Pricing (Active Cards)
| Volume | Price |
|--------|-------|
| ≤7,500 | €0.95 |
| ≤15,000 | €0.85 |
| >15,000 | €0.75 |

### Event Fees
- Card issue: €0.30
- Plastic personalization: €0.70
- KYC attempt: €1.50
- Dispute case: €20.00

## Running Tests

```bash
python main.py test

# Or with pytest directly
pytest movesion_simulator/tests -v --cov=movesion_simulator
```

## Configuration

Environment variables can be set in `.env`:

```bash
# Copy example config
cp movesion_simulator/.env.example .env
```

Key settings:
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `DEBUG`: Enable debug mode (default: false)

## Development

### Code Style
```bash
# Format code
black movesion_simulator

# Lint
ruff check movesion_simulator

# Type check
mypy movesion_simulator
```

### Adding New Features

1. **New Cost Component**: Add to `engine/model.py` in `_compute_*` methods
2. **New API Endpoint**: Add to `api/routes/`
3. **New UI Section**: Modify `ui/app.py`

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Streamlit  │────▶│   FastAPI    │────▶│   Engine     │
│      UI      │     │     API      │     │  (Compute)   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  JSON Data   │
                     │   (Config)   │
                     └──────────────┘
```

## License

Proprietary - Movesion

## Support

For questions or issues, please contact the development team.
