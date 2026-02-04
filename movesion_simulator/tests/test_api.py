"""Tests for API endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from movesion_simulator.api.main import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_scenario():
    """Create a sample scenario for testing."""
    return {
        "name": "API Test Scenario",
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
            "event_fees": {"card_issue": True},
        },
        "ops_assumptions": {},
    }


class TestHealthEndpoints:
    """Test suite for health endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "service" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200


class TestPricingEndpoints:
    """Test suite for pricing endpoints."""
    
    def test_get_pricing_plan(self, client):
        """Test getting pricing plan."""
        response = client.get("/api/v1/pricing/plan")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "currency" in data
        assert "fixed_monthly" in data
        assert "tiered_monthly" in data
    
    def test_get_presets(self, client):
        """Test getting scenario presets."""
        response = client.get("/api/v1/pricing/presets")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]
    
    def test_get_preset_by_name(self, client):
        """Test getting a specific preset by name."""
        response = client.get("/api/v1/pricing/presets/S2 Baseline @3k")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "S2 Baseline @3k"
    
    def test_get_preset_not_found(self, client):
        """Test getting a non-existent preset."""
        response = client.get("/api/v1/pricing/presets/NonExistent")
        assert response.status_code == 404
    
    def test_get_tier_info(self, client):
        """Test getting tier information."""
        response = client.get("/api/v1/pricing/tiers/active_cards")
        assert response.status_code == 200
        
        data = response.json()
        assert "unit" in data
        assert "tiers" in data
    
    def test_get_tier_not_found(self, client):
        """Test getting non-existent tier."""
        response = client.get("/api/v1/pricing/tiers/nonexistent")
        assert response.status_code == 404


class TestSimulationEndpoints:
    """Test suite for simulation endpoints."""
    
    def test_run_simulation(self, client, sample_scenario):
        """Test running a simulation."""
        response = client.post(
            "/api/v1/simulation/run",
            json={"scenario": sample_scenario},
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "rows" in data
        assert "kpis" in data
        assert len(data["rows"]) == 12
    
    def test_run_simulation_missing_field(self, client):
        """Test running simulation with missing required field."""
        incomplete_scenario = {"name": "Incomplete"}
        response = client.post(
            "/api/v1/simulation/run",
            json={"scenario": incomplete_scenario},
        )
        assert response.status_code in [400, 500]
    
    def test_compare_scenarios(self, client, sample_scenario):
        """Test comparing multiple scenarios."""
        scenarios = [
            sample_scenario,
            {**sample_scenario, "name": "Modified Scenario"},
        ]
        scenarios[1]["adoption"]["start_active_cards"] = 6000
        
        response = client.post(
            "/api/v1/simulation/compare",
            json={"scenarios": scenarios},
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "comparison" in data
        assert len(data["results"]) == 2
    
    def test_sensitivity_analysis(self, client, sample_scenario):
        """Test sensitivity analysis."""
        response = client.post(
            "/api/v1/simulation/sensitivity/in_app_share",
            json={"scenario": sample_scenario},
            params={"min_value": 0.2, "max_value": 0.8, "steps": 3},
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 3
    
    def test_sensitivity_analysis_unsupported_param(self, client, sample_scenario):
        """Test sensitivity analysis with unsupported parameter."""
        response = client.post(
            "/api/v1/simulation/sensitivity/unsupported_param",
            json={"scenario": sample_scenario},
        )
        assert response.status_code == 400
    
    def test_export_template(self, client):
        """Test getting export template."""
        response = client.get("/api/v1/simulation/export/json")
        assert response.status_code == 200
        
        data = response.json()
        assert "template" in data
        assert "adoption" in data["template"]
