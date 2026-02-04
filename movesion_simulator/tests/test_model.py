"""Tests for simulation model."""

import json
from pathlib import Path

import pytest

from movesion_simulator.engine import SimulationEngine


@pytest.fixture
def pricing_plan():
    """Load the Wallester pricing plan."""
    plan_path = Path(__file__).parent.parent / "data" / "pricing_plan_wallester.json"
    return json.loads(plan_path.read_text())


@pytest.fixture
def base_scenario():
    """Create a base scenario for testing."""
    return {
        "name": "Test Scenario",
        "horizon_months": 12,
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
            "spend_per_active_card_month": 200.0,
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
                "mode": "given",
                "target": {"type": "breakeven", "months": 12},
            },
        },
        "toggles": {
            "program_maintenance": True,
            "additional_program": False,
            "dedicated_bin": False,
            "data_enrichment": False,
            "three_ds_out_of_band": False,
            "apple_pay": False,
            "event_fees": {
                "card_issue": True,
                "plastic_personalization": False,
                "kyc_attempt": False,
                "account_documents": False,
                "dispute": False,
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


class TestSimulationEngine:
    """Test suite for SimulationEngine."""
    
    def test_simulation_creates_correct_number_of_rows(self, pricing_plan, base_scenario):
        """Test that simulation creates one row per month."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        assert len(result.rows) == 12
        assert result.rows[0].month == 1
        assert result.rows[-1].month == 12
    
    def test_active_cards_constant_without_net_adds(self, pricing_plan, base_scenario):
        """Test that active cards stay constant without net adds."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        for row in result.rows:
            assert row.active_cards == 3000
    
    def test_active_cards_grow_with_net_adds(self, pricing_plan, base_scenario):
        """Test that active cards grow with monthly net adds."""
        base_scenario["adoption"]["monthly_net_adds"] = 100
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # Cards should grow each month
        assert result.rows[0].active_cards == 3100
        assert result.rows[-1].active_cards == 4200
    
    def test_active_cards_decrease_with_churn(self, pricing_plan, base_scenario):
        """Test that active cards decrease with churn."""
        base_scenario["adoption"]["churn_rate"] = 0.05
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # Cards should decrease each month
        assert result.rows[0].active_cards < 3000
        assert result.rows[-1].active_cards < result.rows[0].active_cards
    
    def test_revenue_calculation(self, pricing_plan, base_scenario):
        """Test revenue calculation."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        row = result.rows[0]
        
        # Partner revenue = in_app_spend * partner_fee_pct
        expected_partner_rev = 3000 * 200 * 0.5 * 0.02
        assert abs(row.rev_partner - expected_partner_rev) < 0.01
        
        # Interchange = total_spend * interchange_pct
        expected_interchange = 3000 * 200 * 0.002
        assert abs(row.rev_interchange - expected_interchange) < 0.01
    
    def test_fixed_costs_applied(self, pricing_plan, base_scenario):
        """Test that fixed costs are applied correctly."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # Program maintenance is mandatory
        assert result.rows[0].cost_fixed == 2495.0
    
    def test_one_off_costs_applied_in_first_month(self, pricing_plan, base_scenario):
        """Test that one-off costs are applied in the specified month."""
        base_scenario["toggles"]["dedicated_bin"] = True
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # One-off setup should be in month 1 (8995)
        assert result.rows[0].cost_oneoff == 8995.0
        # Not in subsequent months
        assert result.rows[1].cost_oneoff == 0.0
        # But monthly fee should be in fixed costs
        assert result.rows[1].cost_fixed >= 2495.0 + 995.0
    
    def test_tiered_pricing_active_cards(self, pricing_plan, base_scenario):
        """Test tiered pricing for active cards."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # 3000 cards at first tier (0.95)
        expected_cost = 3000 * 0.95
        assert result.rows[0].cost_active_cards == expected_cost
    
    def test_kpi_calculation(self, pricing_plan, base_scenario):
        """Test KPI calculation."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # Check that KPIs are calculated
        assert result.kpis.profit_year1 is not None
        assert result.kpis.total_revenue > 0
        assert result.kpis.total_costs > 0
    
    def test_solve_employee_fee(self, pricing_plan, base_scenario):
        """Test solving for employee fee to break even."""
        base_scenario["commercial"]["b2b"]["mode"] = "solve_employee_fee"
        base_scenario["commercial"]["b2b"]["target"]["months"] = 12
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # Should have calculated a required employee fee
        assert result.kpis.required_employee_fee_month is not None
        assert result.kpis.required_employee_fee_month >= 0
    
    def test_cumulative_profit_calculation(self, pricing_plan, base_scenario):
        """Test cumulative profit calculation."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # Verify cumulative profit is sum of monthly profits
        cumulative = 0
        for row in result.rows:
            cumulative += row.profit
            assert abs(row.cumulative_profit - cumulative) < 0.01
    
    def test_to_dict_conversion(self, pricing_plan, base_scenario):
        """Test conversion to dictionary format."""
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        result_dict = engine.to_dict(result)
        
        assert "rows" in result_dict
        assert "kpis" in result_dict
        assert "scenario_name" in result_dict
        assert "pricing_plan_id" in result_dict
        assert len(result_dict["rows"]) == 12


class TestPhysicalCardCosts:
    """Test suite for physical card cost calculations."""
    
    def test_physical_manufacturing_cost(self, pricing_plan, base_scenario):
        """Test physical card manufacturing costs."""
        base_scenario["adoption"]["monthly_net_adds"] = 1000
        base_scenario["issuance"]["physical_share_issued"] = 0.5
        base_scenario["toggles"]["physical_manufacturing"] = True
        base_scenario["toggles"]["physical_delivery"] = True
        base_scenario["toggles"]["event_fees"]["plastic_personalization"] = True
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # Should have physical costs
        assert result.rows[0].cost_physical > 0
        assert result.rows[0].issued_physical == 500


class TestEventFees:
    """Test suite for event fee calculations."""
    
    def test_kyc_attempt_fee(self, pricing_plan, base_scenario):
        """Test KYC attempt fee calculation."""
        base_scenario["adoption"]["monthly_net_adds"] = 100
        base_scenario["toggles"]["event_fees"]["kyc_attempt"] = True
        base_scenario["ops_assumptions"]["kyc_attempts_per_new_user"] = 1.5
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # KYC cost = 100 users * 1.5 attempts * 1.50 EUR
        expected_kyc_cost = 100 * 1.5 * 1.50
        # Event cost includes KYC + card issue (100 * 0.30)
        expected_total = expected_kyc_cost + 100 * 0.30
        assert abs(result.rows[0].cost_events - expected_total) < 0.01
    
    def test_sms_fee(self, pricing_plan, base_scenario):
        """Test SMS fee calculation."""
        base_scenario["toggles"]["event_fees"]["sms"] = True
        base_scenario["ops_assumptions"]["sms_per_active_user_month"] = 3.0
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # SMS cost = 3000 users * 3 SMS * 0.20 EUR
        expected_sms_cost = 3000 * 3 * 0.20
        assert result.rows[0].cost_events >= expected_sms_cost


class TestAuthorizationCosts:
    """Test suite for authorization cost calculations."""
    
    def test_eea_authorization_cost(self, pricing_plan, base_scenario):
        """Test EEA authorization costs."""
        # Set high EEA share
        base_scenario["usage"]["eea_share"] = 1.0
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        # All authorizations should be EEA
        row = result.rows[0]
        assert row.non_eea_auth == 0
        assert row.eea_auth > 0
        
        # Cost should be calculated at EEA rate
        # tx = (3000 * 200 / 50) = 12000 transactions at 0.13
        expected_cost = 12000 * 0.13
        assert abs(row.cost_auth - expected_cost) < 0.01
    
    def test_non_eea_authorization_cost(self, pricing_plan, base_scenario):
        """Test non-EEA authorization costs."""
        # Set all non-EEA
        base_scenario["usage"]["eea_share"] = 0.0
        
        engine = SimulationEngine(pricing_plan)
        result = engine.simulate(base_scenario)
        
        row = result.rows[0]
        assert row.eea_auth == 0
        assert row.non_eea_auth > 0
        
        # Cost should be calculated at non-EEA rate (0.20)
        expected_cost = 12000 * 0.20
        assert abs(row.cost_auth - expected_cost) < 0.01
