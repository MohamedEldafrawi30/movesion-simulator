"""Type definitions for the simulation engine."""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class TierDefinition:
    """Single tier in a tiered pricing structure."""
    up_to: Optional[float]  # None means unlimited
    price: float


@dataclass
class TieredPricing:
    """Tiered pricing configuration for a specific metric."""
    unit: str
    tiers: list[TierDefinition]


@dataclass
class FixedMonthlyFee:
    """Fixed monthly fee configuration."""
    key: str
    label: str
    amount: float
    enabled_by_default: bool = True


@dataclass
class OneOffFee:
    """One-time fee configuration."""
    key: str
    label: str
    amount: float
    enabled_by_default: bool = False
    apply_month: int = 1


@dataclass
class EventFee:
    """Event-based fee configuration."""
    key: str
    label: str
    amount: float
    enabled_by_default: bool = False
    unit: str = ""


@dataclass
class ManufacturingTier:
    """Physical card manufacturing tier."""
    min_batch: int
    max_batch: Optional[int]
    price: float


@dataclass
class DeliveryMethod:
    """Card delivery method."""
    key: str
    label: str
    price: float


@dataclass
class PhysicalManufacturing:
    """Physical card manufacturing configuration."""
    enabled_by_default: bool
    tiers: list[ManufacturingTier]
    ordering_policy: str = "monthly_same_as_issued"


@dataclass
class PhysicalDelivery:
    """Physical card delivery configuration."""
    enabled_by_default: bool
    methods: list[DeliveryMethod]
    default_method: str = "dhl_tracked"


@dataclass
class PricingPlan:
    """Complete pricing plan configuration."""
    id: str
    currency: str
    fixed_monthly: list[FixedMonthlyFee]
    one_offs: list[OneOffFee]
    tiered_monthly: dict[str, TieredPricing]
    event_fees: list[EventFee]
    physical_manufacturing: PhysicalManufacturing
    physical_delivery: PhysicalDelivery


@dataclass
class AdoptionConfig:
    """User adoption configuration."""
    start_active_cards: float
    monthly_net_adds: float = 0.0
    churn_rate: float = 0.0


@dataclass
class IssuanceConfig:
    """Card issuance configuration."""
    physical_share_issued: float = 0.0
    issued_equals_net_adds: bool = True


@dataclass
class UsageConfig:
    """Card usage configuration."""
    spend_per_active_card_month: float
    in_app_share: float = 0.5
    avg_ticket: float = 50.0
    ecom_share: float = 0.3
    three_ds_attempt_rate: float = 1.0
    eea_share: float = 0.95
    auth_multiplier: float = 1.0


@dataclass
class B2BTarget:
    """B2B target configuration."""
    type: Literal["breakeven", "profit", "margin"] = "breakeven"
    months: int = 12
    amount: float = 0.0


@dataclass
class B2BConfig:
    """B2B commercial configuration."""
    companies: int = 1
    platform_fee_company_month: float = 0.0
    employee_fee_month: float = 0.0
    mode: Literal["given", "solve_employee_fee"] = "solve_employee_fee"
    target: B2BTarget = field(default_factory=B2BTarget)


@dataclass
class CommercialConfig:
    """Commercial configuration."""
    partner_fee_pct: float = 0.02
    interchange_pct: float = 0.002
    b2b: B2BConfig = field(default_factory=B2BConfig)


@dataclass
class EventFeesToggle:
    """Toggle configuration for event fees."""
    card_issue: bool = True
    plastic_personalization: bool = False
    kyc_attempt: bool = False
    documents_confirmation: bool = False
    dispute_case: bool = False
    sms: bool = False
    pin_change: bool = False
    account_closure: bool = False


@dataclass
class Toggles:
    """Feature toggles configuration."""
    program_maintenance: bool = True
    second_program: bool = False
    dedicated_bin_monthly: bool = False
    data_enrichment: bool = False
    oob_3ds_monthly: bool = False
    dedicated_bin_setup: bool = False
    apple_pay_setup: bool = False
    oob_3ds_setup: bool = False
    event_fees: EventFeesToggle = field(default_factory=EventFeesToggle)
    physical_manufacturing: bool = False
    physical_delivery: bool = False
    delivery_method: str = "dhl_tracked"


@dataclass
class OpsAssumptions:
    """Operational assumptions for cost calculations."""
    kyc_attempts_per_new_user: float = 1.0
    doc_confirm_rate_per_new_user: float = 0.0
    dispute_rate_per_tx: float = 0.0
    sms_per_active_user_month: float = 0.0
    pin_changes_per_active_user_month: float = 0.0
    closures_per_churned_user: float = 0.0


@dataclass
class ScenarioConfig:
    """Complete scenario configuration."""
    name: str
    horizon_months: int
    adoption: AdoptionConfig
    issuance: IssuanceConfig
    usage: UsageConfig
    commercial: CommercialConfig
    toggles: Toggles
    ops_assumptions: OpsAssumptions = field(default_factory=OpsAssumptions)


@dataclass
class MonthlyResult:
    """Monthly simulation results."""
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
    
    # Revenue breakdown
    rev_partner: float
    rev_interchange: float
    rev_b2b: float
    
    # Cost breakdown
    cost_fixed: float
    cost_oneoff: float
    cost_active_cards: float
    cost_auth: float
    cost_3ds: float
    cost_events: float
    cost_physical: float
    
    # Totals
    total_revenue: float
    total_costs: float
    profit: float
    cumulative_profit: float
    
    # Intermediate values for debugging
    costs_excl_b2b: float
    rev_excl_b2b: float


@dataclass
class SimulationKPIs:
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
    # Profit status: "profitable", "loss", "balanced" (when solver makes profit ~= 0)
    profit_status: str = "unknown"
    # True if scenario was solved to breakeven (profit ≈ 0)
    is_solved_breakeven: bool = False


@dataclass
class SimulationResult:
    """Complete simulation result."""
    rows: list[MonthlyResult]
    kpis: SimulationKPIs
    scenario_name: str
    pricing_plan_id: str
