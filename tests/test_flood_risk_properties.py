"""
Property-based tests for Flood Risk Engine.

This module contains property tests that validate universal correctness
properties of the flood risk prediction system.

Requirements: 1.3
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.uris_ai.ml.flood_risk_engine import FloodRiskEngine, RiskCategory


class TestFloodRiskProperties:
    """Property-based tests for Flood Risk Engine."""

    @given(risk_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    def test_risk_score_to_category_mapping_consistency(self, risk_score: float):
        """
        **Property 1: Risk Score to Category Mapping Consistency**
        
        **Validates: Requirements 1.3**
        
        For every risk score in range 0-100, the category mapping must be
        consistent with the thresholds defined:
        - Score 0-25 → RENDAH
        - Score 26-50 → SEDANG
        - Score 51-75 → TINGGI
        - Score 76-100 → KRITIS
        
        This property ensures that:
        1. Every score maps to exactly one category
        2. The mapping is consistent with defined thresholds
        3. Boundary values are handled correctly
        """
        engine = FloodRiskEngine()
        
        category = engine.get_risk_category(risk_score)
        
        # Verify category is one of the valid categories
        assert category in [
            RiskCategory.RENDAH,
            RiskCategory.SEDANG,
            RiskCategory.TINGGI,
            RiskCategory.KRITIS
        ], f"Invalid category {category} for score {risk_score}"
        
        # Verify mapping consistency with thresholds
        if risk_score <= 25:
            assert category == RiskCategory.RENDAH, \
                f"Score {risk_score} should map to RENDAH, got {category}"
        elif risk_score <= 50:
            assert category == RiskCategory.SEDANG, \
                f"Score {risk_score} should map to SEDANG, got {category}"
        elif risk_score <= 75:
            assert category == RiskCategory.TINGGI, \
                f"Score {risk_score} should map to TINGGI, got {category}"
        else:  # risk_score <= 100
            assert category == RiskCategory.KRITIS, \
                f"Score {risk_score} should map to KRITIS, got {category}"

    @given(risk_score=st.floats(min_value=0.0, max_value=25.0, allow_nan=False, allow_infinity=False))
    def test_rendah_category_range(self, risk_score: float):
        """
        Test that all scores in [0, 25] map to RENDAH category.
        
        **Validates: Requirements 1.3**
        """
        engine = FloodRiskEngine()
        category = engine.get_risk_category(risk_score)
        assert category == RiskCategory.RENDAH, \
            f"Score {risk_score} in [0, 25] should be RENDAH, got {category}"

    @given(risk_score=st.floats(min_value=25.01, max_value=50.0, allow_nan=False, allow_infinity=False))
    def test_sedang_category_range(self, risk_score: float):
        """
        Test that all scores in (25, 50] map to SEDANG category.
        
        **Validates: Requirements 1.3**
        """
        engine = FloodRiskEngine()
        category = engine.get_risk_category(risk_score)
        assert category == RiskCategory.SEDANG, \
            f"Score {risk_score} in (25, 50] should be SEDANG, got {category}"

    @given(risk_score=st.floats(min_value=50.01, max_value=75.0, allow_nan=False, allow_infinity=False))
    def test_tinggi_category_range(self, risk_score: float):
        """
        Test that all scores in (50, 75] map to TINGGI category.
        
        **Validates: Requirements 1.3**
        """
        engine = FloodRiskEngine()
        category = engine.get_risk_category(risk_score)
        assert category == RiskCategory.TINGGI, \
            f"Score {risk_score} in (50, 75] should be TINGGI, got {category}"

    @given(risk_score=st.floats(min_value=75.01, max_value=100.0, allow_nan=False, allow_infinity=False))
    def test_kritis_category_range(self, risk_score: float):
        """
        Test that all scores in (75, 100] map to KRITIS category.
        
        **Validates: Requirements 1.3**
        """
        engine = FloodRiskEngine()
        category = engine.get_risk_category(risk_score)
        assert category == RiskCategory.KRITIS, \
            f"Score {risk_score} in (75, 100] should be KRITIS, got {category}"

    def test_boundary_values(self):
        """
        Test exact boundary values for category mapping.
        
        **Validates: Requirements 1.3**
        """
        engine = FloodRiskEngine()
        
        # Test exact boundaries
        assert engine.get_risk_category(0.0) == RiskCategory.RENDAH
        assert engine.get_risk_category(25.0) == RiskCategory.RENDAH
        assert engine.get_risk_category(25.01) == RiskCategory.SEDANG
        assert engine.get_risk_category(50.0) == RiskCategory.SEDANG
        assert engine.get_risk_category(50.01) == RiskCategory.TINGGI
        assert engine.get_risk_category(75.0) == RiskCategory.TINGGI
        assert engine.get_risk_category(75.01) == RiskCategory.KRITIS
        assert engine.get_risk_category(100.0) == RiskCategory.KRITIS

    @given(risk_score=st.floats(min_value=-1000.0, max_value=-0.01, allow_nan=False, allow_infinity=False))
    def test_negative_scores_clamped_to_rendah(self, risk_score: float):
        """
        Test that negative scores are clamped and treated as RENDAH.
        
        **Validates: Requirements 1.3, 1.4 (error handling)
        """
        engine = FloodRiskEngine()
        category = engine.get_risk_category(risk_score)
        # Negative scores should be clamped to 0, which maps to RENDAH
        assert category == RiskCategory.RENDAH, \
            f"Negative score {risk_score} should be clamped and map to RENDAH, got {category}"

    @given(risk_score=st.floats(min_value=100.01, max_value=1000.0, allow_nan=False, allow_infinity=False))
    def test_excessive_scores_clamped_to_kritis(self, risk_score: float):
        """
        Test that scores > 100 are clamped and treated as KRITIS.
        
        **Validates: Requirements 1.3, 1.4 (error handling)
        """
        engine = FloodRiskEngine()
        category = engine.get_risk_category(risk_score)
        # Scores > 100 should be clamped to 100, which maps to KRITIS
        assert category == RiskCategory.KRITIS, \
            f"Score {risk_score} > 100 should be clamped and map to KRITIS, got {category}"

    @given(
        score1=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        score2=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    def test_category_ordering_consistency(self, score1: float, score2: float):
        """
        Test that higher scores never map to lower categories.
        
        If score1 < score2, then category(score1) <= category(score2) in severity.
        
        **Validates: Requirements 1.3**
        """
        assume(abs(score1 - score2) > 0.01)  # Avoid floating point comparison issues
        
        engine = FloodRiskEngine()
        
        cat1 = engine.get_risk_category(score1)
        cat2 = engine.get_risk_category(score2)
        
        # Define category ordering
        category_order = {
            RiskCategory.RENDAH: 1,
            RiskCategory.SEDANG: 2,
            RiskCategory.TINGGI: 3,
            RiskCategory.KRITIS: 4
        }
        
        if score1 < score2:
            assert category_order[cat1] <= category_order[cat2], \
                f"Score {score1} (cat={cat1}) < {score2} (cat={cat2}), " \
                f"but category ordering is violated"

    @given(risk_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    def test_idempotency(self, risk_score: float):
        """
        Test that calling get_risk_category multiple times with the same score
        returns the same category (idempotency).
        
        **Validates: Requirements 1.3**
        """
        engine = FloodRiskEngine()
        
        category1 = engine.get_risk_category(risk_score)
        category2 = engine.get_risk_category(risk_score)
        category3 = engine.get_risk_category(risk_score)
        
        assert category1 == category2 == category3, \
            f"get_risk_category not idempotent for score {risk_score}: " \
            f"{category1}, {category2}, {category3}"
