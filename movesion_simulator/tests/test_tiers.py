"""Tests for tiered pricing calculations."""

import pytest

from movesion_simulator.engine.tiers import TierCalculator


class TestTierCalculator:
    """Test suite for TierCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create a TierCalculator instance."""
        return TierCalculator()
    
    @pytest.fixture
    def sample_tiers(self):
        """Sample tiered pricing structure."""
        return [
            {"up_to": 7500, "price": 0.95},
            {"up_to": 15000, "price": 0.85},
            {"up_to": None, "price": 0.75},
        ]
    
    def test_apply_tiers_first_tier(self, calculator, sample_tiers):
        """Test pricing in the first tier."""
        result = calculator.apply_tiers(5000, sample_tiers)
        assert result == 5000 * 0.95
    
    def test_apply_tiers_exact_boundary(self, calculator, sample_tiers):
        """Test pricing at exact tier boundary."""
        result = calculator.apply_tiers(7500, sample_tiers)
        assert result == 7500 * 0.95
    
    def test_apply_tiers_second_tier(self, calculator, sample_tiers):
        """Test pricing in the second tier."""
        result = calculator.apply_tiers(10000, sample_tiers)
        assert result == 10000 * 0.85
    
    def test_apply_tiers_last_tier(self, calculator, sample_tiers):
        """Test pricing in the unlimited tier."""
        result = calculator.apply_tiers(50000, sample_tiers)
        assert result == 50000 * 0.75
    
    def test_apply_tiers_zero_volume(self, calculator, sample_tiers):
        """Test zero volume."""
        result = calculator.apply_tiers(0, sample_tiers)
        assert result == 0.0
    
    def test_apply_tiers_negative_volume_raises(self, calculator, sample_tiers):
        """Test that negative volume raises an error."""
        with pytest.raises(ValueError, match="must be >= 0"):
            calculator.apply_tiers(-100, sample_tiers)
    
    def test_apply_tiers_empty_tiers_raises(self, calculator):
        """Test that empty tiers list raises an error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            calculator.apply_tiers(100, [])
    
    def test_get_effective_rate_first_tier(self, calculator, sample_tiers):
        """Test getting effective rate in first tier."""
        rate = calculator.get_effective_rate(5000, sample_tiers)
        assert rate == 0.95
    
    def test_get_effective_rate_second_tier(self, calculator, sample_tiers):
        """Test getting effective rate in second tier."""
        rate = calculator.get_effective_rate(10000, sample_tiers)
        assert rate == 0.85
    
    def test_get_effective_rate_last_tier(self, calculator, sample_tiers):
        """Test getting effective rate in last tier."""
        rate = calculator.get_effective_rate(50000, sample_tiers)
        assert rate == 0.75
    
    def test_find_tier_index(self, calculator, sample_tiers):
        """Test finding tier index."""
        assert calculator.find_tier_index(5000, sample_tiers) == 0
        assert calculator.find_tier_index(7500, sample_tiers) == 0
        assert calculator.find_tier_index(7501, sample_tiers) == 1
        assert calculator.find_tier_index(15000, sample_tiers) == 1
        assert calculator.find_tier_index(15001, sample_tiers) == 2
        assert calculator.find_tier_index(100000, sample_tiers) == 2


class TestGraduatedTiers:
    """Test suite for graduated tiered pricing."""
    
    @pytest.fixture
    def calculator(self):
        """Create a TierCalculator instance."""
        return TierCalculator()
    
    @pytest.fixture
    def graduated_tiers(self):
        """Sample graduated tier structure."""
        return [
            {"up_to": 100, "price": 1.00},
            {"up_to": 500, "price": 0.80},
            {"up_to": None, "price": 0.60},
        ]
    
    def test_graduated_first_tier_only(self, calculator, graduated_tiers):
        """Test graduated pricing within first tier."""
        result = calculator.apply_graduated_tiers(50, graduated_tiers)
        assert result == 50 * 1.00
    
    def test_graduated_spans_two_tiers(self, calculator, graduated_tiers):
        """Test graduated pricing spanning two tiers."""
        result = calculator.apply_graduated_tiers(200, graduated_tiers)
        expected = 100 * 1.00 + 100 * 0.80
        assert result == expected
    
    def test_graduated_spans_all_tiers(self, calculator, graduated_tiers):
        """Test graduated pricing spanning all tiers."""
        result = calculator.apply_graduated_tiers(700, graduated_tiers)
        expected = 100 * 1.00 + 400 * 0.80 + 200 * 0.60
        assert result == expected
    
    def test_graduated_zero_volume(self, calculator, graduated_tiers):
        """Test graduated pricing with zero volume."""
        result = calculator.apply_graduated_tiers(0, graduated_tiers)
        assert result == 0.0
