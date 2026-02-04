#!/usr/bin/env python3
"""
Movesion Business Model Simulator - Main Entry Point

This script provides convenient commands for running the application.

Usage:
    python main.py api      - Start the FastAPI server
    python main.py ui       - Start the Streamlit UI
    python main.py test     - Run tests
    python main.py demo     - Run a quick demo simulation
"""

import sys
import subprocess
from pathlib import Path


def run_api():
    """Start the FastAPI server."""
    print("Starting Movesion API Server...")
    print("API docs available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop\n")
    
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "movesion_simulator.api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])


def run_ui():
    """Start the Streamlit UI."""
    print("Starting Movesion Simulator UI...")
    print("Opening browser at: http://localhost:8501")
    print("Press Ctrl+C to stop\n")
    
    ui_path = Path(__file__).parent / "movesion_simulator" / "ui" / "app.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(ui_path),
        "--server.port", "8501"
    ])


def run_tests():
    """Run the test suite."""
    print("Running tests...\n")
    subprocess.run([
        sys.executable, "-m", "pytest",
        "movesion_simulator/tests",
        "-v", "--cov=movesion_simulator",
        "--cov-report=term-missing"
    ])


def run_demo():
    """Run a quick demonstration."""
    import json
    from movesion_simulator.engine import SimulationEngine
    
    # Load pricing plan
    data_dir = Path(__file__).parent / "movesion_simulator" / "data"
    pricing_plan = json.loads((data_dir / "pricing_plan_wallester.json").read_text())
    presets = json.loads((data_dir / "scenario_presets.json").read_text())
    
    print("=" * 60)
    print("Movesion Business Model Simulator - Demo")
    print("=" * 60)
    
    engine = SimulationEngine(pricing_plan)
    
    # Run simulation for first preset
    scenario = presets[0]
    print(f"\nRunning simulation: {scenario['name']}")
    print("-" * 40)
    
    result = engine.simulate(scenario)
    kpis = result.kpis
    
    print(f"\nKey Performance Indicators:")
    
    # Show profit status
    if kpis.profit_status == "balanced":
        print(f"  - Status: BALANCED (fee covers costs exactly)")
        print(f"  - Breakeven: Immediate (with recommended fee)")
    elif kpis.breakeven_month:
        print(f"  - Status: {kpis.profit_status.upper()}")
        print(f"  - Breakeven Month: Month {kpis.breakeven_month}")
    else:
        print(f"  - Status: {kpis.profit_status.upper()}")
        print(f"  - Breakeven Month: Not achieved")
    
    print(f"  - Year 1 Profit: €{kpis.profit_year1:,.2f}")
    print(f"  - Total Profit: €{kpis.total_profit:,.2f}")
    print(f"  - Required Employee Fee: €{kpis.required_employee_fee_month:.2f}/month" 
          if kpis.required_employee_fee_month else "  - Required Employee Fee: N/A")
    print(f"  - ROI: {kpis.roi_percent:.1f}%" if kpis.roi_percent else "  - ROI: 0.0% (balanced)")
    
    print(f"\nMonthly Summary (first 6 months):")
    print(f"  {'Month':<6} {'Cards':<8} {'Revenue':<12} {'Costs':<12} {'Profit':<12}")
    print("  " + "-" * 50)
    for row in result.rows[:6]:
        print(f"  {row.month:<6} {row.active_cards:<8,.0f} "
              f"€{row.total_revenue:<10,.0f} €{row.total_costs:<10,.0f} €{row.profit:<10,.0f}")
    
    print("\n" + "=" * 60)
    print("Demo complete! Run 'python main.py api' to start the full API.")
    print("=" * 60)


def print_help():
    """Print help message."""
    print(__doc__)
    print("Available commands:")
    print("  api   - Start the FastAPI backend server")
    print("  ui    - Start the Streamlit web interface")
    print("  test  - Run the test suite")
    print("  demo  - Run a quick simulation demo")
    print("\nExample:")
    print("  python main.py api")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        "api": run_api,
        "server": run_api,
        "ui": run_ui,
        "streamlit": run_ui,
        "test": run_tests,
        "tests": run_tests,
        "demo": run_demo,
        "help": print_help,
        "--help": print_help,
        "-h": print_help,
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
