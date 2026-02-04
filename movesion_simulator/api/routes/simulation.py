"""Simulation routes."""

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from ..schemas import (
    CompareRequest,
    RunSimulationRequest,
)
from ...config import get_settings
from ...engine import SimulationEngine

router = APIRouter(prefix="/simulation", tags=["Simulation"])


def load_pricing_plan() -> dict[str, Any]:
    """Load pricing plan from JSON file."""
    settings = get_settings()
    try:
        return json.loads(settings.pricing_plan_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Pricing plan file not found: {settings.pricing_plan_path}",
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid pricing plan JSON: {e}",
        )


@router.post(
    "/run",
    summary="Run Simulation",
    description="Execute a business model simulation with the provided scenario.",
    response_model=dict[str, Any],
)
async def run_simulation(request: RunSimulationRequest) -> dict[str, Any]:
    """
    Run a simulation with the provided scenario configuration.
    
    The scenario should include:
    - name: Scenario identifier
    - horizon_months: Number of months to simulate
    - adoption: User adoption parameters (start_active_cards, monthly_net_adds, churn_rate)
    - issuance: Card issuance parameters
    - usage: Card usage parameters (spend, ticket size, etc.)
    - commercial: Commercial parameters (fees, interchange)
    - toggles: Feature flags for costs
    - ops_assumptions: Operational cost assumptions
    """
    try:
        plan = load_pricing_plan()
        engine = SimulationEngine(plan)
        result = engine.simulate(request.scenario)
        return engine.to_dict(result)
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required field in scenario: {e}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario value: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation error: {e}",
        )


@router.post(
    "/compare",
    summary="Compare Scenarios",
    description="Run multiple simulations and compare results.",
    response_model=dict[str, Any],
)
async def compare_scenarios(request: CompareRequest) -> dict[str, Any]:
    """
    Compare multiple scenarios side by side.
    
    Returns individual simulation results plus a comparison summary.
    """
    try:
        plan = load_pricing_plan()
        engine = SimulationEngine(plan)
        
        results = []
        for scenario in request.scenarios:
            result = engine.simulate(scenario)
            results.append(engine.to_dict(result))
        
        # Build comparison summary
        comparison = {
            "scenarios": [r["scenario_name"] for r in results],
            "breakeven_months": [r["kpis"]["breakeven_month"] for r in results],
            "profit_year1": [r["kpis"]["profit_year1"] for r in results],
            "total_profit": [r["kpis"]["total_profit"] for r in results],
            "required_employee_fee": [r["kpis"]["required_employee_fee_month"] for r in results],
            "roi_percent": [r["kpis"]["roi_percent"] for r in results],
        }
        
        # Find best scenario by profit
        best_profit_idx = max(
            range(len(results)),
            key=lambda i: results[i]["kpis"]["total_profit"]
        )
        comparison["best_by_profit"] = results[best_profit_idx]["scenario_name"]
        
        # Find fastest breakeven
        breakeven_values = [
            (i, r["kpis"]["breakeven_month"])
            for i, r in enumerate(results)
            if r["kpis"]["breakeven_month"] is not None
        ]
        if breakeven_values:
            best_breakeven_idx = min(breakeven_values, key=lambda x: x[1])[0]
            comparison["fastest_breakeven"] = results[best_breakeven_idx]["scenario_name"]
        else:
            comparison["fastest_breakeven"] = None
        
        return {
            "results": results,
            "comparison": comparison,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison error: {e}",
        )


@router.post(
    "/sensitivity/{parameter}",
    summary="Sensitivity Analysis",
    description="Run sensitivity analysis on a specific parameter.",
    response_model=dict[str, Any],
)
async def sensitivity_analysis(
    parameter: str,
    request: RunSimulationRequest,
    min_value: float = 0.0,
    max_value: float = 1.0,
    steps: int = 5,
) -> dict[str, Any]:
    """
    Run sensitivity analysis on a specific parameter.
    
    Varies the parameter from min_value to max_value in the specified number of steps.
    
    Supported parameters:
    - in_app_share
    - ecom_share
    - avg_ticket
    - physical_share_issued
    - partner_fee_pct
    - interchange_pct
    - churn_rate
    """
    supported_params = {
        "in_app_share": ("usage", "in_app_share"),
        "ecom_share": ("usage", "ecom_share"),
        "avg_ticket": ("usage", "avg_ticket"),
        "physical_share_issued": ("issuance", "physical_share_issued"),
        "partner_fee_pct": ("commercial", "partner_fee_pct"),
        "interchange_pct": ("commercial", "interchange_pct"),
        "churn_rate": ("adoption", "churn_rate"),
        "start_active_cards": ("adoption", "start_active_cards"),
        "monthly_net_adds": ("adoption", "monthly_net_adds"),
        "spend_per_active_card_month": ("usage", "spend_per_active_card_month"),
    }
    
    if parameter not in supported_params:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported parameter: {parameter}. Supported: {list(supported_params.keys())}",
        )
    
    try:
        plan = load_pricing_plan()
        engine = SimulationEngine(plan)
        
        section, field = supported_params[parameter]
        step_size = (max_value - min_value) / (steps - 1) if steps > 1 else 0
        
        results = []
        for i in range(steps):
            value = min_value + i * step_size
            
            # Deep copy scenario
            scenario = json.loads(json.dumps(request.scenario))
            
            # Set parameter value
            if section in scenario:
                scenario[section][field] = value
            
            result = engine.simulate(scenario)
            result_dict = engine.to_dict(result)
            result_dict["parameter_value"] = value
            results.append(result_dict)
        
        # Summary
        summary = {
            "parameter": parameter,
            "values": [r["parameter_value"] for r in results],
            "profit_year1": [r["kpis"]["profit_year1"] for r in results],
            "total_profit": [r["kpis"]["total_profit"] for r in results],
            "breakeven_month": [r["kpis"]["breakeven_month"] for r in results],
        }
        
        return {
            "results": results,
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sensitivity analysis error: {e}",
        )


@router.get(
    "/export/{format}",
    summary="Export Template",
    description="Get a scenario template for export.",
    response_model=dict[str, Any],
)
async def get_export_template(format: str) -> dict[str, Any]:
    """Return a scenario template for creating new scenarios."""
    if format not in ["json", "csv_template"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: json, csv_template",
        )
    
    template = {
        "name": "New Scenario",
        "horizon_months": 36,
        "adoption": {
            "start_active_cards": 3000,
            "monthly_net_adds": 0,
            "churn_rate": 0.0,
        },
        "issuance": {
            "physical_share_issued": 0.0,
            "issued_equals_net_adds": True,
        },
        "usage": {
            "spend_per_active_card_month": 200,
            "in_app_share": 0.5,
            "avg_ticket": 50,
            "ecom_share": 0.3,
            "three_ds_attempt_rate": 1.0,
            "eea_share": 0.95,
            "auth_multiplier": 1.0,
        },
        "commercial": {
            "partner_fee_pct": 0.02,
            "interchange_pct": 0.002,
            "b2b": {
                "companies": 1,
                "platform_fee_company_month": 0.0,
                "employee_fee_month": 0.0,
                "mode": "solve_employee_fee",
                "target": {"type": "breakeven", "months": 12},
            },
        },
        "toggles": {
            "program_maintenance": True,
            "second_program": False,
            "dedicated_bin_monthly": False,
            "data_enrichment": False,
            "oob_3ds_monthly": False,
            "dedicated_bin_setup": False,
            "apple_pay_setup": False,
            "oob_3ds_setup": False,
            "event_fees": {
                "card_issue": True,
                "plastic_personalization": False,
                "kyc_attempt": False,
                "documents_confirmation": False,
                "dispute_case": False,
                "sms": False,
                "pin_change": False,
                "account_closure": False,
            },
            "physical_manufacturing": False,
            "physical_delivery": False,
            "delivery_method": "dhl_tracked",
        },
        "ops_assumptions": {
            "kyc_attempts_per_new_user": 1.0,
            "doc_confirm_rate_per_new_user": 0.0,
            "dispute_rate_per_tx": 0.0,
            "sms_per_active_user_month": 0.0,
            "pin_changes_per_active_user_month": 0.0,
            "closures_per_churned_user": 0.0,
        },
    }
    
    return {"format": format, "template": template}
