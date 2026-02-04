"""
Movesion Business Model Simulator - CEO Dashboard
Simplified, focused UI for executive decision-making.
"""

import json
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ============================================================================
# Configuration
# ============================================================================

st.set_page_config(
    page_title="Mobility Pay Business Model Simulator",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",  # Start with sidebar collapsed
)

# Clean, minimal styling
st.markdown("""
<style>
    /* Force wide mode - target all possible Streamlit containers */
    .main .block-container,
    [data-testid="stAppViewContainer"] .block-container,
    .st-emotion-cache-1y4p8pa,
    .st-emotion-cache-z5fcl4,
    .css-1y4p8pa,
    .css-z5fcl4 {
        max-width: 95% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main .block-container,
        [data-testid="stAppViewContainer"] .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .main-title {
            font-size: 1.5rem !important;
        }
        .subtitle {
            font-size: 0.9rem !important;
        }
    }
    
    /* Clean header */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Pricing cards */
    .price-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        color: white;
        margin: 8px 0;
    }
    .price-card.recommended {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        transform: scale(1.05);
        box-shadow: 0 10px 40px rgba(17, 153, 142, 0.3);
    }
    .price-card.minimum {
        background: linear-gradient(135deg, #636363 0%, #a2a2a2 100%);
    }
    .price-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 8px;
    }
    .price-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 8px 0;
    }
    .price-detail {
        font-size: 0.85rem;
        opacity: 0.85;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Input section */
    .input-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# API Functions
# ============================================================================

def get_api_url() -> str:
    """Get API URL from session state or default."""
    return st.session_state.get("api_url", "http://127.0.0.1:8000")


def run_simulation(api_url: str, scenario: dict[str, Any]) -> dict[str, Any]:
    """Run simulation via API."""
    response = requests.post(
        f"{api_url}/api/v1/simulation/run",
        json={"scenario": scenario},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_pricing_plan(api_url: str) -> dict[str, Any]:
    """Get pricing plan from API."""
    response = requests.get(f"{api_url}/api/v1/pricing/plan", timeout=10)
    response.raise_for_status()
    return response.json()


# ============================================================================
# Helper Functions
# ============================================================================

def create_default_scenario(employees: int, spend_year: float, physical_pct: float) -> dict[str, Any]:
    """Create a scenario with the given parameters."""
    return {
        "name": "Custom Scenario",
        "horizon_months": 12,
        "adoption": {
            "start_active_cards": float(employees),
            "monthly_net_adds": 0.0,
            "churn_rate": 0.0,
        },
        "issuance": {
            "physical_share_issued": physical_pct,
            "issued_equals_net_adds": True,
        },
        "usage": {
            "spend_per_active_card_month": spend_year / 12,
            "in_app_share": 0.5,
            "avg_ticket": 50.0,
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
            "additional_program": False,
            "dedicated_bin": False,
            "data_enrichment": False,
            "three_ds_oob": False,
            "apple_pay": False,
            "event_fees": {
                "card_issue": True,
                "plastic_personalization": physical_pct > 0,
                "kyc_attempt": False,
                "account_documents": False,
                "dispute": False,
                "sms": False,
                "pin_change": False,
                "account_closure": False,
            },
            "physical_manufacturing": physical_pct > 0,
            "physical_delivery": physical_pct > 0,
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


def run_scale_comparison(api_url: str, base_scenario: dict[str, Any]) -> list[dict]:
    """Run simulations for different scales."""
    base_employees = int(base_scenario["adoption"]["start_active_cards"])
    scales = [1000, 3000, 6000, 10000, 20000, 50000]
    
    # Ensure current scale is included
    if base_employees not in scales:
        scales.append(base_employees)
        scales.sort()
    
    results = []
    for scale in scales:
        scenario = json.loads(json.dumps(base_scenario))
        scenario["adoption"]["start_active_cards"] = float(scale)
        try:
            result = run_simulation(api_url, scenario)
            min_fee = result["kpis"].get("required_employee_fee_month", 0) or 0
            results.append({
                "employees": scale,
                "min_fee": min_fee,
                "is_current": scale == base_employees,
            })
        except Exception:
            pass
    
    return results


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application."""
    
    # Header
    st.markdown('<h1 class="main-title">💳 Mobility Pay Business Model Simulator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Model your employee card business profitability</p>', unsafe_allow_html=True)
    
    # Check API connection (optional - app works standalone)
    api_url = get_api_url()
    api_available = False
    try:
        get_pricing_plan(api_url)
        api_available = True
    except Exception:
        pass  # API not available - app will work standalone
    
    # ========================================================================
    # INPUT SECTION - 3 Key Variables
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 🎯 Cost Assumptions")
    st.caption("These affect your cost per card")
    
    col1, col2 = st.columns(2)
    
    with col1:
        spend_year = st.number_input(
            "Avg Spend per Card / Year (€)",
            min_value=100,
            max_value=50000,
            value=2400,
            step=100,
            help="Average spending per card per year (affects transaction costs)",
        )
    
    with col2:
        physical_pct = st.slider(
            "Physical Cards (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=10,
            help="What % of cards are physical (vs virtual)? Physical cards cost more.",
        ) / 100
    
    # Default values for cost calculation
    employees = 1000  # Use 1000 cards as reference for cost calculation
    
    # Additional cost settings
    st.markdown("**Additional Settings**")
    adv_col1, adv_col2, adv_col3, adv_col4, adv_col5 = st.columns(5)
    
    with adv_col1:
        in_app_share = st.slider("In-app spend share", 0.0, 1.0, 0.5, 0.05)
        partner_fee = st.slider("Partner fee (%)", 0.0, 5.0, 2.0, 0.1) / 100
    
    with adv_col2:
        avg_ticket = st.number_input("Avg transaction (€)", 1, 500, 50)
        ecom_share = st.slider("E-commerce share", 0.0, 1.0, 0.3, 0.05)
    
    with adv_col3:
        eea_share = st.slider("EEA transactions", 0.0, 1.0, 0.95, 0.05)
        interchange = st.slider("Interchange (%)", 0.0, 1.0, 0.2, 0.05) / 100
    
    with adv_col4:
        auth_multiplier = st.slider("Auth multiplier", 1.0, 2.0, 1.0, 0.1, 
                                    help="Authorizations per transaction (1.0 = 1 auth per txn, 1.2 = 20% more auths due to retries/pre-auths)")
        three_ds_multiplier = st.slider("3DS multiplier", 1.0, 2.0, 1.0, 0.1,
                                        help="3DS attempts per e-commerce transaction")
    
    with adv_col5:
        inactive_pct = st.slider("Inactive users (%)", 0, 50, 10, 5,
                                 help="% of cardholders who don't use their cards. They still cost you (card fees) but don't generate transactions.") / 100
        active_user_rate = 1 - inactive_pct
    
    # ========================================================================
    # WALLESTER PRICING (Configurable)
    # ========================================================================
    
    with st.expander("💶 Wallester Pricing (Edit if needed)", expanded=False):
        st.caption("These are the fees Wallester charges. Update if pricing changes.")
        
        price_col1, price_col2, price_col3 = st.columns(3)
        
        with price_col1:
            st.markdown("**Fixed Fees**")
            cfg_platform_fee = st.number_input("Platform Fee (€/month)", value=2495, step=100, key="cfg_platform")
            
            st.markdown("**Card Issuance**")
            cfg_card_issue_fee = st.number_input("Card Issue Fee (€)", value=0.30, step=0.05, format="%.2f", key="cfg_issue")
        
        with price_col2:
            st.markdown("**Authorization Fees**")
            cfg_auth_fee_eea = st.number_input("EEA Auth (€)", value=0.13, step=0.01, format="%.2f", key="cfg_auth_eea")
            cfg_auth_fee_non_eea = st.number_input("Non-EEA Auth (€)", value=0.20, step=0.01, format="%.2f", key="cfg_auth_non_eea")
            
            st.markdown("**3DS Fees**")
            cfg_three_ds_fee = st.number_input("3DS Attempt (€)", value=0.11, step=0.01, format="%.2f", key="cfg_3ds")
        
        with price_col3:
            st.markdown("**Physical Card Fees**")
            cfg_personalization_fee = st.number_input("Personalization (€)", value=0.70, step=0.10, format="%.2f", key="cfg_perso")
            cfg_manufacturing_fee = st.number_input("Manufacturing (€)", value=3.50, step=0.50, format="%.2f", key="cfg_manuf")
            cfg_delivery_fee = st.number_input("Delivery (€)", value=12.00, step=1.00, format="%.2f", key="cfg_delivery")
        
        # Active card tier pricing
        st.markdown("---")
        st.markdown("**Active Card Tiers (cost per card/month based on volume)**")
        tier_cols = st.columns(4)
        with tier_cols[0]:
            cfg_tier_7500 = st.number_input("0-7,500 cards (€)", value=0.95, step=0.05, format="%.2f", key="cfg_t1")
            cfg_tier_10000 = st.number_input("7,500-10,000 (€)", value=0.90, step=0.05, format="%.2f", key="cfg_t2")
        with tier_cols[1]:
            cfg_tier_15000 = st.number_input("10,000-15,000 (€)", value=0.85, step=0.05, format="%.2f", key="cfg_t3")
            cfg_tier_30000 = st.number_input("15,000-30,000 (€)", value=0.80, step=0.05, format="%.2f", key="cfg_t4")
        with tier_cols[2]:
            cfg_tier_60000 = st.number_input("30,000-60,000 (€)", value=0.70, step=0.05, format="%.2f", key="cfg_t5")
            cfg_tier_100000 = st.number_input("60,000-100,000 (€)", value=0.65, step=0.05, format="%.2f", key="cfg_t6")
        with tier_cols[3]:
            cfg_tier_500000 = st.number_input("100,000-500,000 (€)", value=0.60, step=0.05, format="%.2f", key="cfg_t7")
            cfg_tier_max = st.number_input("500,000+ (€)", value=0.55, step=0.05, format="%.2f", key="cfg_t8")
    
    # Use configurable values (app works standalone without API)
    cost_per_card_month = cfg_tier_7500  # Use base tier as reference
    
    # Use configurable platform fee
    monthly_platform_fee = cfg_platform_fee
    annual_platform_fee = monthly_platform_fee * 12
    
    # ========================================================================
    # CLIENT PACKAGES - 3 Options
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 📦 Client Packages")
    
    # Show cost reference with tiered info
    st.info(f"""💡 **Your card cost is volume-based (Wallester tiered pricing):**
- Small volume (0-7,500 cards): €{cfg_tier_7500:.2f}/card/month
- Medium volume (7,500-30,000 cards): €{cfg_tier_30000:.2f}-€{cfg_tier_10000:.2f}/card/month  
- Large volume (30,000+ cards): €{cfg_tier_max:.2f}-€{cfg_tier_60000:.2f}/card/month

Set your card fees above these costs to make profit!""")
    
    # Define 3 packages with profitable defaults (card fee > cost)
    base_card_fee = max(cost_per_card_month * 1.3, 2.0)  # At least 30% margin or €2
    
    packages = [
        {
            "name": "Basic",
            "color": "#6c757d",
            "annual_fee": 5000,
            "card_fee": round(base_card_fee + 0.50, 2),  # Higher fee for small clients
            "cards_range": "Up to 500",
            "avg_cards": 300,
        },
        {
            "name": "Business", 
            "color": "#667eea",
            "annual_fee": 8000,
            "card_fee": round(base_card_fee + 0.25, 2),  # Medium fee
            "cards_range": "500 - 2,000",
            "avg_cards": 1000,
        },
        {
            "name": "Enterprise",
            "color": "#11998e",
            "annual_fee": 15000,
            "card_fee": round(base_card_fee, 2),  # Lower fee for large clients (volume discount)
            "cards_range": "2,000+",
            "avg_cards": 5000,
        },
    ]
    
    # Let user customize packages
    with st.expander("✏️ Customize Package Pricing", expanded=True):
        pkg_cols = st.columns(3)
        
        # Define card limits for each package
        card_limits = [
            {"min": 50, "max": 500, "default": 300},      # Basic
            {"min": 500, "max": 2000, "default": 1000},   # Business
            {"min": 2000, "max": 10000, "default": 5000}, # Enterprise
        ]
        
        for i, (col, pkg) in enumerate(zip(pkg_cols, packages)):
            with col:
                st.markdown(f"**{pkg['name']}** ({pkg['cards_range']})")
                
                packages[i]["avg_cards"] = st.number_input(
                    f"Avg Cards/Client",
                    min_value=card_limits[i]["min"],
                    max_value=card_limits[i]["max"],
                    value=card_limits[i]["default"],
                    step=50,
                    key=f"cards_{i}"
                )
                
                packages[i]["annual_fee"] = st.number_input(
                    f"Annual Fee (€)", 
                    value=pkg["annual_fee"], 
                    step=500, 
                    key=f"ann_{i}"
                )
                
                new_card_fee = st.number_input(
                    f"Per Card/Month (€)", 
                    value=pkg["card_fee"], 
                    step=0.10,
                    format="%.2f",
                    key=f"card_{i}"
                )
                packages[i]["card_fee"] = new_card_fee
                
                # Warning if below minimum cost (first tier)
                if new_card_fee < cfg_tier_7500:
                    st.warning(f"⚠️ Below min cost (€{cfg_tier_7500:.2f})!")
    
    # Display packages with actual numbers
    pkg_cols = st.columns(3)
    for col, pkg in zip(pkg_cols, packages):
        with col:
            st.markdown(f"""
            <div style="background: {pkg['color']}; border-radius: 16px; padding: 24px; text-align: center; color: white;">
                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 12px;">{pkg['name'].upper()}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">{pkg['avg_cards']:,} cards/client</div>
                <hr style="opacity: 0.3; margin: 12px 0;">
                <div style="font-size: 2rem; font-weight: 700;">€{pkg['annual_fee']:,}</div>
                <div style="font-size: 0.85rem;">/year subscription</div>
                <div style="margin-top: 12px; font-size: 1.3rem; font-weight: 600;">+ €{pkg['card_fee']:.2f}</div>
                <div style="font-size: 0.85rem;">/card/month</div>
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # BUSINESS CALCULATOR - How many clients?
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 🧮 Business Calculator")
    st.markdown("How many clients of each package type?")
    
    calc_cols = st.columns(3)
    with calc_cols[0]:
        num_basic = st.number_input(
            f"Basic Clients ({packages[0]['avg_cards']} cards each)", 
            min_value=0, value=5, step=1,
            key="num_basic_clients"
        )
    with calc_cols[1]:
        num_business = st.number_input(
            f"Business Clients ({packages[1]['avg_cards']} cards each)", 
            min_value=0, value=3, step=1,
            key="num_business_clients"
        )
    with calc_cols[2]:
        num_enterprise = st.number_input(
            f"Enterprise Clients ({packages[2]['avg_cards']} cards each)", 
            min_value=0, value=1, step=1,
            key="num_enterprise_clients"
        )
    
    # Calculate totals
    total_clients = num_basic + num_business + num_enterprise
    total_cards = (num_basic * packages[0]["avg_cards"] + 
                   num_business * packages[1]["avg_cards"] + 
                   num_enterprise * packages[2]["avg_cards"])
    
    # Tiered pricing based on total cards (Wallester pricing - configurable)
    card_tiers = [
        (7500, cfg_tier_7500),
        (10000, cfg_tier_10000),
        (15000, cfg_tier_15000),
        (30000, cfg_tier_30000),
        (60000, cfg_tier_60000),
        (100000, cfg_tier_100000),
        (500000, cfg_tier_500000),
        (float('inf'), cfg_tier_max),
    ]
    
    # Get tiered cost per card based on total volume
    tiered_cost_per_card = cfg_tier_7500  # Default to first tier
    current_tier_label = "0 - 7,500"
    for tier_max, tier_price in card_tiers:
        if total_cards <= tier_max:
            tiered_cost_per_card = tier_price
            if tier_max == float('inf'):
                current_tier_label = "500,000+"
            else:
                prev_tier = 0
                for i, (t_max, _) in enumerate(card_tiers):
                    if t_max == tier_max and i > 0:
                        prev_tier = card_tiers[i-1][0] + 1
                        break
                current_tier_label = f"{prev_tier:,} - {tier_max:,}"
            break
    
    # Revenue calculation (what clients pay you)
    rev_basic = num_basic * (packages[0]["annual_fee"] + packages[0]["card_fee"] * packages[0]["avg_cards"] * 12)
    rev_business = num_business * (packages[1]["annual_fee"] + packages[1]["card_fee"] * packages[1]["avg_cards"] * 12)
    rev_enterprise = num_enterprise * (packages[2]["annual_fee"] + packages[2]["card_fee"] * packages[2]["avg_cards"] * 12)
    subscription_revenue = rev_basic + rev_business + rev_enterprise
    
    # Additional revenue from card usage (based on spend from ACTIVE users only)
    active_cards = int(total_cards * active_user_rate)  # Only active users transact
    total_annual_spend = active_cards * spend_year  # spend_year is per active card per year
    partner_revenue = total_annual_spend * partner_fee * in_app_share  # Partner fee on in-app spend
    interchange_revenue = total_annual_spend * interchange  # Interchange on all spend
    
    # Total revenue = subscriptions + partner fees + interchange
    total_revenue = subscription_revenue + partner_revenue + interchange_revenue
    
    # ========================================================================
    # COMPREHENSIVE COST CALCULATION (All Wallester Costs)
    # ========================================================================
    
    # 1. Fixed Costs - Platform Fee
    cost_platform = annual_platform_fee
    
    # 2. Active Card Costs (tiered) - You pay for ALL cards, even inactive ones!
    cost_active_cards = tiered_cost_per_card * total_cards * 12
    
    # 3. Transaction-based costs (only from active users)
    num_transactions = total_annual_spend / avg_ticket if avg_ticket > 0 else 0
    
    # Authorization fees (with multiplier for retries/pre-auths)
    auth_fee_eea = cfg_auth_fee_eea
    auth_fee_non_eea = cfg_auth_fee_non_eea
    total_authorizations = num_transactions * auth_multiplier  # Apply multiplier
    eea_authorizations = total_authorizations * eea_share
    non_eea_authorizations = total_authorizations * (1 - eea_share)
    cost_auth = (eea_authorizations * auth_fee_eea) + (non_eea_authorizations * auth_fee_non_eea)
    
    # 3DS fees for e-commerce transactions (with multiplier)
    three_ds_fee = cfg_three_ds_fee
    ecom_transactions = num_transactions * ecom_share
    total_3ds_attempts = ecom_transactions * three_ds_multiplier  # Apply multiplier
    cost_3ds = total_3ds_attempts * three_ds_fee
    
    # 4. Card issuance fees (one-time per card)
    card_issue_fee = cfg_card_issue_fee
    cost_card_issue = total_cards * card_issue_fee
    
    # 5. Physical card costs
    physical_cards = int(total_cards * physical_pct)
    personalization_fee = cfg_personalization_fee
    manufacturing_fee = cfg_manufacturing_fee
    delivery_fee = cfg_delivery_fee
    cost_physical = physical_cards * (personalization_fee + manufacturing_fee + delivery_fee)
    
    # Total variable costs (excluding platform fee)
    total_variable_costs = cost_active_cards + cost_auth + cost_3ds + cost_card_issue + cost_physical
    
    # Total costs
    total_cost = cost_platform + total_variable_costs
    
    # Net profit = Revenue - Costs
    net_profit = total_revenue - total_cost
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # ========================================================================
    # RESULTS - Simple Summary
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 💵 Year 1 Results")
    
    # Show key assumptions
    inactive_cards = total_cards - active_cards
    st.info(f"""📊 **Key Metrics:** {total_cards:,} total cards ({active_cards:,} active, {inactive_cards:,} inactive @ {inactive_pct*100:.0f}%) | {num_transactions:,.0f} transactions | {total_authorizations:,.0f} auths | {total_3ds_attempts:,.0f} 3DS
    
**Active Card Tier:** {current_tier_label} cards = €{tiered_cost_per_card:.2f}/card/month | ⚠️ You pay for ALL {total_cards:,} cards, but only {active_cards:,} generate revenue""")
    
    # Big summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Clients", f"{total_clients}")
    with col2:
        st.metric("Total Cards", f"{total_cards:,}")
    with col3:
        st.metric("Revenue", f"€{total_revenue:,.0f}")
    with col4:
        profit_delta = f"{profit_margin:.0f}% margin" if net_profit >= 0 else "Loss"
        st.metric("Net Profit", f"€{net_profit:,.0f}", delta=profit_delta)
    
    # Simple breakdown
    if net_profit >= 0:
        st.success(f"✅ **Profitable!** Revenue €{total_revenue:,.0f} (Subs: €{subscription_revenue:,.0f} + Partner: €{partner_revenue:,.0f} + Interchange: €{interchange_revenue:,.0f}) - Costs €{total_cost:,.0f} = **€{net_profit:,.0f} profit**")
    else:
        st.error(f"❌ **Loss!** Revenue €{total_revenue:,.0f} - Costs €{total_cost:,.0f} = **€{net_profit:,.0f}**")
    
    # Expandable details
    with st.expander("📊 See Breakdown", expanded=True):
        
        # ====== REVENUE BREAKDOWN ======
        st.markdown("### 💰 Revenue Breakdown")
        
        rev_chart_col, rev_detail_col = st.columns([1, 1])
        
        with rev_chart_col:
            # Revenue pie chart
            rev_labels = ['Subscriptions', 'Partner Fees', 'Interchange']
            rev_values = [subscription_revenue, partner_revenue, interchange_revenue]
            rev_colors = ['#667eea', '#11998e', '#f093fb']
            
            fig_rev = go.Figure(data=[go.Pie(
                labels=rev_labels,
                values=rev_values,
                hole=0.4,
                marker_colors=rev_colors,
                textinfo='label+percent',
                textposition='outside',
                pull=[0.05, 0, 0]
            )])
            fig_rev.update_layout(
                title=dict(text=f"Total Revenue: €{total_revenue:,.0f}", x=0.5),
                showlegend=False,
                height=350,
                margin=dict(t=60, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_rev, use_container_width=True)
        
        with rev_detail_col:
            st.markdown("**Subscription Revenue:**")
            st.markdown(f"- Basic ({num_basic} clients): €{rev_basic:,.0f}")
            st.markdown(f"- Business ({num_business} clients): €{rev_business:,.0f}")
            st.markdown(f"- Enterprise ({num_enterprise} clients): €{rev_enterprise:,.0f}")
            st.markdown(f"- **Subtotal: €{subscription_revenue:,.0f}**")
            st.markdown("")
            st.markdown(f"**Transaction Revenue:**")
            st.markdown(f"- Active cards spending: €{total_annual_spend:,.0f}/year")
            st.markdown(f"- Partner Fee ({partner_fee*100:.1f}% × {in_app_share*100:.0f}% in-app): **€{partner_revenue:,.0f}**")
            st.markdown(f"- Interchange ({interchange*100:.2f}%): **€{interchange_revenue:,.0f}**")
        
        # ====== COST BREAKDOWN ======
        st.markdown("---")
        st.markdown("### 📉 Cost Breakdown")
        
        cost_chart_col, cost_detail_col = st.columns([1, 1])
        
        with cost_chart_col:
            # Cost pie chart
            cost_labels = ['Platform Fee', 'Active Cards', 'Authorizations', '3DS Fees', 'Card Issuance', 'Physical Cards']
            cost_values = [cost_platform, cost_active_cards, cost_auth, cost_3ds, cost_card_issue, cost_physical]
            cost_colors = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1', '#5f27cd', '#ff9ff3']
            
            # Filter out zero values
            filtered_labels = [l for l, v in zip(cost_labels, cost_values) if v > 0]
            filtered_values = [v for v in cost_values if v > 0]
            filtered_colors = [c for c, v in zip(cost_colors, cost_values) if v > 0]
            
            fig_cost = go.Figure(data=[go.Pie(
                labels=filtered_labels,
                values=filtered_values,
                hole=0.4,
                marker_colors=filtered_colors,
                textinfo='label+percent',
                textposition='outside'
            )])
            fig_cost.update_layout(
                title=dict(text=f"Total Costs: €{total_cost:,.0f}", x=0.5),
                showlegend=False,
                height=350,
                margin=dict(t=60, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_cost, use_container_width=True)
        
        with cost_detail_col:
            st.markdown("**Fixed Costs:**")
            st.markdown(f"- Platform Fee: **€{cost_platform:,.0f}**/year (€{monthly_platform_fee:,}/mo)")
            st.markdown("")
            st.markdown("**Variable Costs:**")
            st.markdown(f"- Active Cards ({total_cards:,} × €{tiered_cost_per_card:.2f} × 12): **€{cost_active_cards:,.0f}**")
            st.markdown(f"- Auth Fees ({total_authorizations:,.0f} auths): **€{cost_auth:,.0f}**")
            st.markdown(f"- 3DS Fees ({total_3ds_attempts:,.0f} attempts): **€{cost_3ds:,.0f}**")
            st.markdown(f"- Card Issuance ({total_cards:,} cards): **€{cost_card_issue:,.0f}**")
            if physical_cards > 0:
                st.markdown(f"- Physical Cards ({physical_cards:,}): **€{cost_physical:,.0f}**")
            st.markdown(f"- **Total Variable: €{total_variable_costs:,.0f}**")
        
        # ====== REVENUE VS COSTS BAR CHART ======
        st.markdown("---")
        st.markdown("### 📊 Revenue vs Costs Comparison")
        
        # Stacked bar chart comparing revenue and costs
        fig_compare = go.Figure()
        
        # Revenue bars
        fig_compare.add_trace(go.Bar(
            name='Subscriptions',
            x=['Revenue'],
            y=[subscription_revenue],
            marker_color='#667eea',
            text=[f'€{subscription_revenue:,.0f}'],
            textposition='inside'
        ))
        fig_compare.add_trace(go.Bar(
            name='Partner Fees',
            x=['Revenue'],
            y=[partner_revenue],
            marker_color='#11998e',
            text=[f'€{partner_revenue:,.0f}'] if partner_revenue > 1000 else [''],
            textposition='inside'
        ))
        fig_compare.add_trace(go.Bar(
            name='Interchange',
            x=['Revenue'],
            y=[interchange_revenue],
            marker_color='#f093fb',
            text=[f'€{interchange_revenue:,.0f}'] if interchange_revenue > 1000 else [''],
            textposition='inside'
        ))
        
        # Cost bars
        fig_compare.add_trace(go.Bar(
            name='Platform Fee',
            x=['Costs'],
            y=[cost_platform],
            marker_color='#ff6b6b',
            text=[f'€{cost_platform:,.0f}'],
            textposition='inside'
        ))
        fig_compare.add_trace(go.Bar(
            name='Active Cards',
            x=['Costs'],
            y=[cost_active_cards],
            marker_color='#feca57',
            text=[f'€{cost_active_cards:,.0f}'],
            textposition='inside'
        ))
        fig_compare.add_trace(go.Bar(
            name='Transaction Costs',
            x=['Costs'],
            y=[cost_auth + cost_3ds],
            marker_color='#48dbfb',
            text=[f'€{cost_auth + cost_3ds:,.0f}'] if (cost_auth + cost_3ds) > 1000 else [''],
            textposition='inside'
        ))
        fig_compare.add_trace(go.Bar(
            name='Card/Physical',
            x=['Costs'],
            y=[cost_card_issue + cost_physical],
            marker_color='#5f27cd',
            text=[f'€{cost_card_issue + cost_physical:,.0f}'] if (cost_card_issue + cost_physical) > 1000 else [''],
            textposition='inside'
        ))
        
        # Add profit line
        fig_compare.add_trace(go.Scatter(
            name='Net Profit',
            x=['Revenue', 'Costs'],
            y=[total_revenue, total_cost],
            mode='lines+markers+text',
            line=dict(color='#2d3436', width=3, dash='dash'),
            marker=dict(size=12),
            text=[f'€{total_revenue:,.0f}', f'€{total_cost:,.0f}'],
            textposition='top center'
        ))
        
        fig_compare.update_layout(
            barmode='stack',
            height=400,
            xaxis_title='',
            yaxis_title='Amount (€)',
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
        )
        
        # Add profit annotation
        profit_color = '#27ae60' if net_profit >= 0 else '#e74c3c'
        fig_compare.add_annotation(
            x=0.5, y=max(total_revenue, total_cost) * 1.1,
            text=f"<b>Net Profit: €{net_profit:,.0f}</b>",
            showarrow=False,
            font=dict(size=16, color=profit_color),
            xref='paper'
        )
        
        st.plotly_chart(fig_compare, use_container_width=True)
        
        # ====== DETAILED COST TABLE ======
        st.markdown("---")
        st.markdown("#### 📋 Detailed Cost Table")
        
        # Cost breakdown table
        cost_data = pd.DataFrame({
            "Cost Category": [
                "Platform Fee (Fixed)",
                "Active Cards",
                "Authorization Fees",
                "3DS Fees (E-commerce)",
                "Card Issuance",
                "Physical Cards",
                "**TOTAL COSTS**"
            ],
            "Calculation": [
                f"€{monthly_platform_fee:,}/mo × 12",
                f"{total_cards:,} cards × €{tiered_cost_per_card:.2f} × 12mo",
                f"{total_authorizations:,.0f} auths ({num_transactions:,.0f} txns × {auth_multiplier}x)",
                f"{total_3ds_attempts:,.0f} attempts ({ecom_transactions:,.0f} e-com × {three_ds_multiplier}x)",
                f"{total_cards:,} cards × €{card_issue_fee:.2f}",
                f"{physical_cards:,} cards × €{personalization_fee + manufacturing_fee + delivery_fee:.2f}" if physical_cards > 0 else "No physical cards",
                ""
            ],
            "Annual Cost": [
                f"€{cost_platform:,.0f}",
                f"€{cost_active_cards:,.0f}",
                f"€{cost_auth:,.0f}",
                f"€{cost_3ds:,.0f}",
                f"€{cost_card_issue:,.0f}",
                f"€{cost_physical:,.0f}",
                f"**€{total_cost:,.0f}**"
            ]
        })
        st.dataframe(cost_data, hide_index=True, use_container_width=True)
    
    # ========================================================================
    # BREAK-EVEN - Simple
    # ========================================================================
    
    with st.expander("📊 Break-Even Analysis"):
        st.markdown("**How many clients to cover the platform fee?**")
        st.caption(f"Using current tier pricing: €{tiered_cost_per_card:.2f}/card/month")
        
        breakeven_data = []
        for pkg in packages:
            rev_per_client = pkg["annual_fee"] + pkg["card_fee"] * pkg["avg_cards"] * 12
            cost_per_client = tiered_cost_per_card * pkg["avg_cards"] * 12  # Use tiered cost
            profit_per_client = rev_per_client - cost_per_client
            
            if profit_per_client > 0:
                clients_needed = annual_platform_fee / profit_per_client
                clients_needed_rounded = int(clients_needed) + (1 if clients_needed % 1 > 0 else 0)  # Round up
                breakeven_data.append({
                    "Package": pkg["name"],
                    "Profit/Client/Year": f"€{profit_per_client:,.0f}",
                    "Clients Needed": f"{clients_needed_rounded}",
                })
            else:
                breakeven_data.append({
                    "Package": pkg["name"],
                    "Profit/Client/Year": f"€{profit_per_client:,.0f}",
                    "Clients Needed": "❌ Not viable",
                })
        
        st.dataframe(pd.DataFrame(breakeven_data), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
