"""Pydantic schemas for API request/response validation."""

from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================

class AdoptionConfigSchema(BaseModel):
    """User adoption configuration."""
    start_active_cards: float = Field(..., ge=0, description="Starting number of active cards")
    monthly_net_adds: float = Field(0.0, description="Monthly net new cards added")
    churn_rate: float = Field(0.0, ge=0, le=1, description="Monthly churn rate (0-1)")


class IssuanceConfigSchema(BaseModel):
    """Card issuance configuration."""
    physical_share_issued: float = Field(0.0, ge=0, le=1, description="Share of physical cards issued")
    issued_equals_net_adds: bool = Field(True, description="Whether issued cards equal net adds")


class UsageConfigSchema(BaseModel):
    """Card usage configuration."""
    spend_per_active_card_month: float = Field(..., ge=0, description="Monthly spend per active card")
    in_app_share: float = Field(0.5, ge=0, le=1, description="Share of in-app spending")
    avg_ticket: float = Field(50.0, gt=0, description="Average transaction amount")
    ecom_share: float = Field(0.3, ge=0, le=1, description="Share of e-commerce transactions")
    three_ds_attempt_rate: float = Field(1.0, ge=0, le=1, description="3DS attempt rate for e-commerce")
    eea_share: float = Field(0.95, ge=0, le=1, description="Share of EEA transactions")
    auth_multiplier: float = Field(1.0, ge=0, description="Authorization multiplier")


class B2BTargetSchema(BaseModel):
    """B2B target configuration."""
    type: str = Field("breakeven", description="Target type: breakeven, profit, or margin")
    months: int = Field(12, ge=1, description="Target horizon in months")
    amount: float = Field(0.0, description="Target amount (for profit/margin types)")


class B2BConfigSchema(BaseModel):
    """B2B commercial configuration."""
    companies: int = Field(1, ge=1, description="Number of B2B companies")
    platform_fee_company_month: float = Field(0.0, ge=0, description="Monthly platform fee per company")
    employee_fee_month: float = Field(0.0, ge=0, description="Monthly fee per employee")
    mode: str = Field("solve_employee_fee", description="Mode: given or solve_employee_fee")
    target: B2BTargetSchema = Field(default_factory=B2BTargetSchema)


class CommercialConfigSchema(BaseModel):
    """Commercial configuration."""
    partner_fee_pct: float = Field(0.02, ge=0, le=1, description="Partner fee percentage")
    interchange_pct: float = Field(0.002, ge=0, le=1, description="Interchange percentage")
    b2b: B2BConfigSchema = Field(default_factory=B2BConfigSchema)


class EventFeesToggleSchema(BaseModel):
    """Toggle configuration for event fees."""
    card_issue: bool = Field(True)
    plastic_personalization: bool = Field(False)
    kyc_attempt: bool = Field(False)
    documents_confirmation: bool = Field(False)
    dispute_case: bool = Field(False)
    sms: bool = Field(False)
    pin_change: bool = Field(False)
    account_closure: bool = Field(False)


class TogglesSchema(BaseModel):
    """Feature toggles configuration."""
    program_maintenance: bool = Field(True)
    second_program: bool = Field(False)
    dedicated_bin_monthly: bool = Field(False)
    data_enrichment: bool = Field(False)
    oob_3ds_monthly: bool = Field(False)
    dedicated_bin_setup: bool = Field(False)
    apple_pay_setup: bool = Field(False)
    oob_3ds_setup: bool = Field(False)
    event_fees: EventFeesToggleSchema = Field(default_factory=EventFeesToggleSchema)
    physical_manufacturing: bool = Field(False)
    physical_delivery: bool = Field(False)
    delivery_method: str = Field("dhl_tracked")


class OpsAssumptionsSchema(BaseModel):
    """Operational assumptions for cost calculations."""
    kyc_attempts_per_new_user: float = Field(1.0, ge=0)
    doc_confirm_rate_per_new_user: float = Field(0.0, ge=0)
    dispute_rate_per_tx: float = Field(0.0, ge=0, le=1)
    sms_per_active_user_month: float = Field(0.0, ge=0)
    pin_changes_per_active_user_month: float = Field(0.0, ge=0)
    closures_per_churned_user: float = Field(0.0, ge=0)


class ScenarioConfigSchema(BaseModel):
    """Complete scenario configuration."""
    name: str = Field("Custom Scenario", description="Scenario name")
    horizon_months: int = Field(36, ge=1, le=120, description="Simulation horizon in months")
    adoption: AdoptionConfigSchema
    issuance: IssuanceConfigSchema = Field(default_factory=IssuanceConfigSchema)
    usage: UsageConfigSchema
    commercial: CommercialConfigSchema = Field(default_factory=CommercialConfigSchema)
    toggles: TogglesSchema = Field(default_factory=TogglesSchema)
    ops_assumptions: OpsAssumptionsSchema = Field(default_factory=OpsAssumptionsSchema)


class RunSimulationRequest(BaseModel):
    """Request body for running a simulation."""
    scenario: dict[str, Any] = Field(..., description="Scenario configuration")
    pricing_plan_id: Optional[str] = Field(None, description="Optional pricing plan ID to use")
    
    model_config = {"extra": "allow"}


class CompareRequest(BaseModel):
    """Request body for comparing multiple scenarios."""
    scenarios: list[dict[str, Any]] = Field(..., min_length=2, description="List of scenarios to compare")
    pricing_plan_id: Optional[str] = Field(None, description="Optional pricing plan ID to use")


# ============================================================================
# Response Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    service: str


class MonthlyResultSchema(BaseModel):
    """Monthly simulation result."""
    month: int
    active_cards: float
    issued_cards: float
    issued_physical: float
    issued_virtual: float
    total_spend: float
    in_app_spend: float
    tx_count: float
    eea_auth: float
    non_eea_auth: float
    three_ds_attempts: float
    rev_partner: float
    rev_interchange: float
    rev_b2b: float
    cost_fixed: float
    cost_oneoff: float
    cost_active_cards: float
    cost_auth: float
    cost_3ds: float
    cost_events: float
    cost_physical: float
    total_revenue: float
    total_costs: float
    profit: float
    cumulative_profit: float
    costs_excl_b2b: float
    rev_excl_b2b: float


class SimulationKPIsSchema(BaseModel):
    """Key performance indicators from simulation."""
    breakeven_month: Optional[int]
    profit_year1: float
    profit_year2: Optional[float]
    profit_year3: Optional[float]
    required_employee_fee_month: Optional[float]
    total_revenue: float
    total_costs: float
    total_profit: float
    avg_monthly_profit: float
    roi_percent: Optional[float]


class SimulationResultSchema(BaseModel):
    """Complete simulation result."""
    rows: list[MonthlyResultSchema]
    kpis: SimulationKPIsSchema
    scenario_name: str
    pricing_plan_id: str


class CompareResultSchema(BaseModel):
    """Comparison result for multiple scenarios."""
    results: list[SimulationResultSchema]
    comparison: dict[str, Any]


class TierSchema(BaseModel):
    """Tier definition."""
    up_to: Optional[float]
    price: float


class TieredPricingSchema(BaseModel):
    """Tiered pricing configuration."""
    unit: str
    tiers: list[TierSchema]


class FixedMonthlyFeeSchema(BaseModel):
    """Fixed monthly fee."""
    key: str
    label: str
    amount: float
    enabled_by_default: bool


class OneOffFeeSchema(BaseModel):
    """One-time fee."""
    key: str
    label: str
    amount: float
    enabled_by_default: bool
    apply_month: int


class EventFeeSchema(BaseModel):
    """Event-based fee."""
    key: str
    label: str
    amount: float
    enabled_by_default: bool
    unit: str


class DeliveryMethodSchema(BaseModel):
    """Delivery method."""
    key: str
    label: str
    price: float


class ManufacturingTierSchema(BaseModel):
    """Manufacturing tier."""
    min_batch: int
    max_batch: Optional[int]
    price: float


class PricingPlanSchema(BaseModel):
    """Complete pricing plan."""
    id: str
    currency: str
    fixed_monthly: list[FixedMonthlyFeeSchema]
    one_offs: list[OneOffFeeSchema]
    tiered_monthly: dict[str, TieredPricingSchema]
    event_fees: list[EventFeeSchema]
    physical_manufacturing: dict[str, Any]
    physical_delivery: dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: str = "INTERNAL_ERROR"
