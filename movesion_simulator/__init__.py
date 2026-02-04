"""
Movesion Business Model Simulator

A comprehensive simulation engine for analyzing card program economics,
pricing strategies, and B2B partnership scenarios.
"""

__version__ = "1.0.0"
__author__ = "Movesion Team"

from .engine import SimulationEngine, TierCalculator

__all__ = ["SimulationEngine", "TierCalculator", "__version__"]
