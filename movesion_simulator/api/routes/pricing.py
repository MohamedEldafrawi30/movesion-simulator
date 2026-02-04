"""Pricing plan routes."""

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from ...config import get_settings

router = APIRouter(prefix="/pricing", tags=["Pricing"])


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


def load_scenario_presets() -> list[dict[str, Any]]:
    """Load scenario presets from JSON file."""
    settings = get_settings()
    try:
        return json.loads(settings.scenario_presets_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Scenario presets file not found: {settings.scenario_presets_path}",
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid scenario presets JSON: {e}",
        )


@router.get(
    "/plan",
    summary="Get Pricing Plan",
    description="Retrieve the current pricing plan configuration.",
    response_model=dict[str, Any],
)
async def get_pricing_plan() -> dict[str, Any]:
    """Return the complete pricing plan."""
    return load_pricing_plan()


@router.get(
    "/presets",
    summary="Get Scenario Presets",
    description="Retrieve available scenario presets for quick simulation setup.",
    response_model=list[dict[str, Any]],
)
async def get_presets() -> list[dict[str, Any]]:
    """Return available scenario presets."""
    return load_scenario_presets()


@router.get(
    "/presets/{preset_name}",
    summary="Get Specific Preset",
    description="Retrieve a specific scenario preset by name.",
    response_model=dict[str, Any],
)
async def get_preset_by_name(preset_name: str) -> dict[str, Any]:
    """Return a specific preset by name."""
    presets = load_scenario_presets()
    
    for preset in presets:
        if preset.get("name") == preset_name:
            return preset
    
    raise HTTPException(
        status_code=404,
        detail=f"Preset not found: {preset_name}",
    )


@router.get(
    "/tiers/{metric}",
    summary="Get Tier Information",
    description="Retrieve tier information for a specific metric.",
    response_model=dict[str, Any],
)
async def get_tier_info(metric: str) -> dict[str, Any]:
    """Return tier information for a specific metric."""
    plan = load_pricing_plan()
    tiered = plan.get("tiered_monthly", {})
    
    if metric not in tiered:
        raise HTTPException(
            status_code=404,
            detail=f"Metric not found: {metric}. Available: {list(tiered.keys())}",
        )
    
    return tiered[metric]


@router.get(
    "/fees/fixed",
    summary="Get Fixed Monthly Fees",
    description="Retrieve all fixed monthly fees.",
    response_model=list[dict[str, Any]],
)
async def get_fixed_fees() -> list[dict[str, Any]]:
    """Return fixed monthly fees."""
    plan = load_pricing_plan()
    return plan.get("fixed_monthly", [])


@router.get(
    "/fees/events",
    summary="Get Event Fees",
    description="Retrieve all event-based fees.",
    response_model=list[dict[str, Any]],
)
async def get_event_fees() -> list[dict[str, Any]]:
    """Return event-based fees."""
    plan = load_pricing_plan()
    return plan.get("event_fees", [])


@router.get(
    "/fees/oneoff",
    summary="Get One-Off Fees",
    description="Retrieve all one-time fees.",
    response_model=list[dict[str, Any]],
)
async def get_oneoff_fees() -> list[dict[str, Any]]:
    """Return one-off fees."""
    plan = load_pricing_plan()
    return plan.get("one_offs", [])
