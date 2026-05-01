"""
Property-based tests for Risk Scoring Engine.

This module contains property tests that validate universal correctness
properties of the Urban Risk Score calculation system.

Requirements: 4.1
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.uris_ai.ml.risk_scoring_engine import RiskScoringEngine


# Custom strategies for generating test data
@st.composite
def valid_risk_scores(draw):
    """
    Generate valid risk scores in range [0, 100].
    
    Returns a tuple of (flood_risk, traffic_impact, service_accessibility)
    """
    flood_risk = draw(st.floats(min_value=0.0, max_value=100.0))
    traffic_impact = draw(st.floats(min_value=0.0, max_value=100.0))
    service_accessibility = draw(st.floats(min_value=0.0, max_value=100.0))
    
    return flood_risk, traffic_impact, service_accessibility


@st.composite
def valid_weights(draw):
    """
    Generate valid weights that sum to 1.0.
    
    Returns a dict with keys 'flood', 'traffic', 'service'
    """
    # Generate two random values between 0 and 1
    w1 = draw(st.floats(min_value=0.0, max_value=1.0))
    w2 = draw(st.floats(min_value=0.0, max_value=1.0 - w1))
    w3 = 1.0 - w1 - w2
    
    # Ensure w3 is non-negative (handle floating point precision)
    assume(w3 >= -0.001)
    w3 = max(0.0, w3)
    
    # Normalize to ensure exact sum of 1.0
    total = w1 + w2 + w3
    if total > 0:
        w1 = w1 / total
        w2 = w2 / total
        w3 = w3 / total
    
    return {
        'flood': w1,
        'traffic': w2,
        'service': w3
    }


class TestRiskScoringEngineProperties:
    """Property-based tests for Risk Scoring Engine."""

    @given(
        scores=valid_risk_scores(),
        weights=valid_weights()
    )
    def test_urban_risk_score_calculation_correctness(self, scores, weights):
        """
        **Property 4: Urban Risk Score Calculation Correctness**
        
        **Validates: Requirements 4.1**
        
        For any valid input scores (flood_risk, traffic_impact, service_accessibility ∈ [0,100])
        and valid weights (sum = 1.0), the URS must:
        1. Be in range [0,100]
        2. Follow the weighted sum formula
        3. Be monotonic (if all inputs increase, URS increases)
        
        This property ensures that:
        - URS is always within valid bounds
        - The calculation follows the specified formula exactly
        - The scoring is mathematically consistent
        """
        flood_risk, traffic_impact, service_accessibility = scores
        
        # Create engine
        engine = RiskScoringEngine()
        
        # Calculate URS
        urs = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility,
            weights=weights
        )
        
        # Property 1: Range constraint [0, 100]
        assert 0 <= urs <= 100, (
            f"URS out of range [0, 100]:\n"
            f"  URS: {urs}\n"
            f"  Inputs: flood={flood_risk}, traffic={traffic_impact}, service={service_accessibility}\n"
            f"  Weights: {weights}"
        )
        
        # Property 2: Formula correctness
        expected_urs = (
            weights['flood'] * flood_risk +
            weights['traffic'] * traffic_impact +
            weights['service'] * service_accessibility
        )
        
        assert abs(urs - expected_urs) < 0.01, (
            f"URS does not match formula:\n"
            f"  Calculated URS: {urs}\n"
            f"  Expected URS: {expected_urs}\n"
            f"  Difference: {abs(urs - expected_urs)}\n"
            f"  Inputs: flood={flood_risk}, traffic={traffic_impact}, service={service_accessibility}\n"
            f"  Weights: {weights}"
        )

    @given(
        scores=valid_risk_scores(),
        weights=valid_weights()
    )
    def test_urs_monotonicity(self, scores, weights):
        """
        Test that URS is monotonic: if all input scores increase, URS increases.
        
        **Validates: Requirements 4.1**
        """
        flood_risk, traffic_impact, service_accessibility = scores
        
        # Ensure we have room to increase
        assume(flood_risk < 99.0)
        assume(traffic_impact < 99.0)
        assume(service_accessibility < 99.0)
        
        # Create engine
        engine = RiskScoringEngine()
        
        # Calculate original URS
        urs_original = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility,
            weights=weights
        )
        
        # Increase all scores by 1
        urs_increased = engine.calculate_urban_risk_score(
            flood_risk=flood_risk + 1.0,
            traffic_impact=traffic_impact + 1.0,
            service_accessibility=service_accessibility + 1.0,
            weights=weights
        )
        
        # Verify monotonicity
        assert urs_increased > urs_original, (
            f"URS not monotonic:\n"
            f"  Original URS: {urs_original}\n"
            f"  Increased URS: {urs_increased}\n"
            f"  Original inputs: flood={flood_risk}, traffic={traffic_impact}, service={service_accessibility}\n"
            f"  Increased inputs: flood={flood_risk+1}, traffic={traffic_impact+1}, service={service_accessibility+1}\n"
            f"  Weights: {weights}"
        )

    @given(scores=valid_risk_scores())
    def test_urs_with_default_weights(self, scores):
        """
        Test URS calculation with default weights.
        
        **Validates: Requirements 4.1**
        """
        flood_risk, traffic_impact, service_accessibility = scores
        
        # Create engine
        engine = RiskScoringEngine()
        
        # Calculate URS with default weights (None)
        urs = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility,
            weights=None
        )
        
        # Verify range
        assert 0 <= urs <= 100, (
            f"URS with default weights out of range:\n"
            f"  URS: {urs}\n"
            f"  Inputs: flood={flood_risk}, traffic={traffic_impact}, service={service_accessibility}"
        )
        
        # Verify formula with default weights (0.5, 0.3, 0.2)
        expected_urs = (
            0.5 * flood_risk +
            0.3 * traffic_impact +
            0.2 * service_accessibility
        )
        
        assert abs(urs - expected_urs) < 0.01, (
            f"URS with default weights does not match formula:\n"
            f"  Calculated URS: {urs}\n"
            f"  Expected URS: {expected_urs}\n"
            f"  Inputs: flood={flood_risk}, traffic={traffic_impact}, service={service_accessibility}"
        )

    @given(
        scores=valid_risk_scores(),
        weights=valid_weights()
    )
    def test_urs_idempotency(self, scores, weights):
        """
        Test that calculating URS multiple times with same inputs returns same result.
        
        **Validates: Requirements 4.1**
        """
        flood_risk, traffic_impact, service_accessibility = scores
        
        # Create engine
        engine = RiskScoringEngine()
        
        # Calculate URS multiple times
        urs1 = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility,
            weights=weights
        )
        
        urs2 = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility,
            weights=weights
        )
        
        urs3 = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility,
            weights=weights
        )
        
        # Verify idempotency
        assert urs1 == urs2 == urs3, (
            f"URS calculation not idempotent:\n"
            f"  URS 1: {urs1}\n"
            f"  URS 2: {urs2}\n"
            f"  URS 3: {urs3}\n"
            f"  Inputs: flood={flood_risk}, traffic={traffic_impact}, service={service_accessibility}\n"
            f"  Weights: {weights}"
        )

    @given(weights=valid_weights())
    def test_urs_boundary_values(self, weights):
        """
        Test URS calculation with boundary values (0 and 100).
        
        **Validates: Requirements 4.1**
        """
        # Create engine
        engine = RiskScoringEngine()
        
        # Test all zeros
        urs_zeros = engine.calculate_urban_risk_score(
            flood_risk=0.0,
            traffic_impact=0.0,
            service_accessibility=0.0,
            weights=weights
        )
        assert urs_zeros == 0.0, f"URS with all zeros should be 0, got {urs_zeros}"
        
        # Test all 100s
        urs_hundreds = engine.calculate_urban_risk_score(
            flood_risk=100.0,
            traffic_impact=100.0,
            service_accessibility=100.0,
            weights=weights
        )
        assert abs(urs_hundreds - 100.0) < 0.01, (
            f"URS with all 100s should be 100, got {urs_hundreds}"
        )

    @given(
        flood_risk=st.floats(min_value=0.0, max_value=100.0),
        weights=valid_weights()
    )
    def test_urs_single_component_dominance(self, flood_risk, weights):
        """
        Test that when only one component is non-zero, URS equals that component
        weighted by its weight.
        
        **Validates: Requirements 4.1**
        """
        # Create engine
        engine = RiskScoringEngine()
        
        # Calculate URS with only flood_risk non-zero
        urs = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=0.0,
            service_accessibility=0.0,
            weights=weights
        )
        
        expected_urs = weights['flood'] * flood_risk
        
        assert abs(urs - expected_urs) < 0.01, (
            f"URS with single component does not match expected:\n"
            f"  Calculated URS: {urs}\n"
            f"  Expected URS: {expected_urs}\n"
            f"  Flood risk: {flood_risk}\n"
            f"  Flood weight: {weights['flood']}"
        )

    @given(
        scores=valid_risk_scores(),
        weights=valid_weights()
    )
    def test_urs_commutative_property(self, scores, weights):
        """
        Test that URS calculation is commutative with respect to input order.
        (This is inherent in addition, but validates implementation)
        
        **Validates: Requirements 4.1**
        """
        flood_risk, traffic_impact, service_accessibility = scores
        
        # Create engine
        engine = RiskScoringEngine()
        
        # Calculate URS
        urs = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility,
            weights=weights
        )
        
        # Calculate with different parameter order (same values)
        urs_reordered = engine.calculate_urban_risk_score(
            service_accessibility=service_accessibility,
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            weights=weights
        )
        
        assert urs == urs_reordered, (
            f"URS calculation not commutative:\n"
            f"  Original order URS: {urs}\n"
            f"  Reordered URS: {urs_reordered}"
        )

    @given(
        scores=valid_risk_scores(),
        scale_factor=st.floats(min_value=0.1, max_value=1.0)
    )
    def test_urs_linear_scaling(self, scores, scale_factor):
        """
        Test that scaling all inputs by the same factor scales URS by that factor.
        
        **Validates: Requirements 4.1**
        """
        flood_risk, traffic_impact, service_accessibility = scores
        
        # Create engine
        engine = RiskScoringEngine()
        
        # Calculate original URS with default weights
        urs_original = engine.calculate_urban_risk_score(
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_accessibility=service_accessibility
        )
        
        # Calculate scaled URS
        urs_scaled = engine.calculate_urban_risk_score(
            flood_risk=flood_risk * scale_factor,
            traffic_impact=traffic_impact * scale_factor,
            service_accessibility=service_accessibility * scale_factor
        )
        
        expected_scaled_urs = urs_original * scale_factor
        
        assert abs(urs_scaled - expected_scaled_urs) < 0.01, (
            f"URS linear scaling property violated:\n"
            f"  Original URS: {urs_original}\n"
            f"  Scaled URS: {urs_scaled}\n"
            f"  Expected scaled URS: {expected_scaled_urs}\n"
            f"  Scale factor: {scale_factor}"
        )

    def test_urs_invalid_input_rejection(self):
        """
        Test that invalid inputs (out of range) are rejected.
        
        **Validates: Requirements 4.1**
        """
        # Create engine
        engine = RiskScoringEngine()
        
        # Test negative flood_risk
        with pytest.raises(ValueError, match="flood_risk must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=-10.0,
                traffic_impact=50.0,
                service_accessibility=50.0
            )
        
        # Test flood_risk > 100
        with pytest.raises(ValueError, match="flood_risk must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=150.0,
                traffic_impact=50.0,
                service_accessibility=50.0
            )
        
        # Test negative traffic_impact
        with pytest.raises(ValueError, match="traffic_impact must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=50.0,
                traffic_impact=-5.0,
                service_accessibility=50.0
            )
        
        # Test service_accessibility > 100
        with pytest.raises(ValueError, match="service_accessibility must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=50.0,
                traffic_impact=50.0,
                service_accessibility=120.0
            )

    def test_urs_invalid_weights_rejection(self):
        """
        Test that invalid weights (not summing to 1.0) are rejected.
        
        **Validates: Requirements 4.1**
        """
        # Create engine
        engine = RiskScoringEngine()
        
        # Test weights summing to > 1.0
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            engine.calculate_urban_risk_score(
                flood_risk=50.0,
                traffic_impact=50.0,
                service_accessibility=50.0,
                weights={'flood': 0.5, 'traffic': 0.5, 'service': 0.5}
            )
        
        # Test weights summing to < 1.0
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            engine.calculate_urban_risk_score(
                flood_risk=50.0,
                traffic_impact=50.0,
                service_accessibility=50.0,
                weights={'flood': 0.2, 'traffic': 0.2, 'service': 0.2}
            )
