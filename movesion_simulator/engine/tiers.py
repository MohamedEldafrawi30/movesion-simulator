"""Tiered pricing calculation utilities."""

from typing import Any


class TierCalculator:
    """Calculator for tiered pricing structures."""
    
    @staticmethod
    def apply_tiers(volume: float, tiers: list[dict[str, Any]]) -> float:
        """
        Apply a simple 'all units at tier price' model based on the tier where volume falls.
        
        This matches common offer tables that quote a unit price for a volume bracket.
        For example:
        - 0-7500 cards: €0.95/card
        - 7501-15000 cards: €0.85/card
        - 15001+ cards: €0.75/card
        
        The entire volume is charged at the tier price where the volume falls.
        
        Args:
            volume: The quantity to calculate pricing for
            tiers: List of tier definitions with 'up_to' and 'price' keys
            
        Returns:
            Total cost for the volume
            
        Raises:
            ValueError: If volume is negative or tiers list is empty
        """
        if volume < 0:
            raise ValueError("Volume must be >= 0")
        
        if not tiers:
            raise ValueError("Tiers list cannot be empty")
        
        if volume == 0:
            return 0.0
        
        for tier in tiers:
            up_to = tier.get("up_to")
            price = float(tier["price"])
            
            if up_to is None or volume <= up_to:
                return volume * price
        
        # Fallback to last tier price (should never reach here with proper tier config)
        return volume * float(tiers[-1]["price"])
    
    @staticmethod
    def apply_graduated_tiers(volume: float, tiers: list[dict[str, Any]]) -> float:
        """
        Apply graduated tiered pricing where different portions are charged at different rates.
        
        For example, with tiers [0-100: $1, 101-500: $0.80, 501+: $0.60]:
        - Volume of 600 would be: 100*$1 + 400*$0.80 + 100*$0.60 = $480
        
        This is NOT used in the current Wallester pricing but included for flexibility.
        
        Args:
            volume: The quantity to calculate pricing for
            tiers: List of tier definitions with 'up_to' and 'price' keys
            
        Returns:
            Total cost calculated using graduated pricing
        """
        if volume < 0:
            raise ValueError("Volume must be >= 0")
        
        if not tiers:
            raise ValueError("Tiers list cannot be empty")
        
        if volume == 0:
            return 0.0
        
        total_cost = 0.0
        remaining = volume
        previous_up_to = 0
        
        for tier in tiers:
            up_to = tier.get("up_to")
            price = float(tier["price"])
            
            if up_to is None:
                # Last tier - apply to all remaining
                total_cost += remaining * price
                break
            
            tier_volume = min(remaining, up_to - previous_up_to)
            if tier_volume > 0:
                total_cost += tier_volume * price
                remaining -= tier_volume
            
            previous_up_to = up_to
            
            if remaining <= 0:
                break
        
        return total_cost
    
    @staticmethod
    def get_effective_rate(volume: float, tiers: list[dict[str, Any]]) -> float:
        """
        Get the effective per-unit rate for a given volume.
        
        Args:
            volume: The quantity to check
            tiers: List of tier definitions
            
        Returns:
            The price per unit for this volume level
        """
        if volume <= 0:
            return float(tiers[0]["price"]) if tiers else 0.0
        
        for tier in tiers:
            up_to = tier.get("up_to")
            if up_to is None or volume <= up_to:
                return float(tier["price"])
        
        return float(tiers[-1]["price"])
    
    @staticmethod
    def find_tier_index(volume: float, tiers: list[dict[str, Any]]) -> int:
        """
        Find which tier index a volume falls into.
        
        Args:
            volume: The quantity to check
            tiers: List of tier definitions
            
        Returns:
            Index of the applicable tier (0-based)
        """
        for i, tier in enumerate(tiers):
            up_to = tier.get("up_to")
            if up_to is None or volume <= up_to:
                return i
        return len(tiers) - 1
