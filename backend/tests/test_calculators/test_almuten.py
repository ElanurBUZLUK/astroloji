"""
Tests for Almuten Figuris calculator
"""
import pytest
from app.calculators.almuten import almuten_figuris, Point, DignityTables

def test_dignity_tables():
    """Test dignity tables basic functionality"""
    tables = DignityTables()
    
    # Test rulerships
    assert tables.is_ruler("Mars", "Aries")
    assert tables.is_ruler("Venus", "Taurus")
    assert not tables.is_ruler("Mars", "Taurus")
    
    # Test exaltations
    assert tables.is_exalted("Sun", "Aries")
    assert tables.is_exalted("Moon", "Taurus")
    assert not tables.is_exalted("Sun", "Taurus")

def test_almuten_basic_calculation():
    """Test basic Almuten calculation"""
    points = [
        Point("Sun", 15.5, "Leo", 15.5),
        Point("Moon", 120.3, "Cancer", 0.3),
        Point("ASC", 45.0, "Taurus", 15.0),
        Point("MC", 315.0, "Aquarius", 15.0)
    ]
    
    chart_data = {"is_day": True}
    result = almuten_figuris(points, chart_data)
    
    assert result.winner is not None
    assert isinstance(result.scores, dict)
    assert len(result.scores) > 0

def test_almuten_with_spirit_fortune():
    """Test Almuten with Lot of Spirit and Fortune"""
    points = [
        Point("Sun", 15.5, "Leo", 15.5),
        Point("Moon", 120.3, "Cancer", 0.3),
        Point("ASC", 45.0, "Taurus", 15.0),
        Point("MC", 315.0, "Aquarius", 15.0),
        Point("Spirit", 200.0, "Libra", 20.0),
        Point("Fortune", 100.0, "Cancer", 10.0)
    ]
    
    chart_data = {"is_day": True}
    result = almuten_figuris(points, chart_data)
    
    assert result.winner is not None
    assert result.diagnostics["points_analyzed"] == 6

def test_almuten_golden_case():
    """Golden test case: Sun at 20° Aries, Moon 4° Taurus, ASC Cancer, MC Pisces, Fortuna Leo, Spirit Aquarius"""
    points = [
        Point("Sun", 20.0, "Aries", 20.0),      # Sun at 20° Aries
        Point("Moon", 34.0, "Taurus", 4.0),     # Moon at 4° Taurus  
        Point("ASC", 90.0, "Cancer", 0.0),      # ASC at 0° Cancer
        Point("MC", 330.0, "Pisces", 0.0),      # MC at 0° Pisces
        Point("Fortune", 120.0, "Leo", 0.0),    # Fortune at 0° Leo
        Point("Spirit", 300.0, "Aquarius", 0.0) # Spirit at 0° Aquarius
    ]
    
    chart_data = {"is_day": True}
    result = almuten_figuris(points, chart_data)
    
    # Verify calculation completed successfully
    assert result.winner is not None
    assert result.winner in ["Mars", "Venus", "Sun", "Moon", "Mercury", "Jupiter", "Saturn"]
    
    # Mars should have significant score due to ruling Aries (where Sun is located)
    assert "Mars" in result.scores
    assert result.scores["Mars"] > 0
    
    # Venus might win due to ruling Taurus (where Moon is) and potentially other dignities
    # The exact winner depends on the dignity table implementation
    assert result.winner in result.scores
    assert result.scores[result.winner] > 0
    
    # Verify all major planets have scores
    expected_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    scored_planets = set(result.scores.keys())
    assert len(scored_planets.intersection(expected_planets)) >= 5  # At least 5 planets should have scores
    
    # Winner should have the highest score
    winner_score = result.scores[result.winner]
    for planet, score in result.scores.items():
        if planet != result.winner:
            assert winner_score >= score

def test_almuten_tie_breaker_scenarios():
    """Test tie-breaker scenarios with angles and sect"""
    # Case where multiple planets have similar dignity scores
    points = [
        Point("Sun", 0.0, "Aries", 0.0),        # Sun exalted in Aries
        Point("Moon", 30.0, "Taurus", 0.0),     # Moon exalted in Taurus
        Point("ASC", 120.0, "Leo", 0.0),        # ASC in Leo (Sun's rulership)
        Point("MC", 240.0, "Sagittarius", 0.0), # MC in Sagittarius
        Point("Fortune", 150.0, "Virgo", 0.0),
        Point("Spirit", 210.0, "Scorpio", 0.0)
    ]
    
    # Day chart should favor diurnal planets (Sun, Jupiter, Saturn)
    chart_data = {"is_day": True}
    result_day = almuten_figuris(points, chart_data)
    
    # Night chart should favor nocturnal planets (Moon, Venus, Mars)  
    chart_data = {"is_day": False}
    result_night = almuten_figuris(points, chart_data)
    
    # Results should be different due to sect considerations
    # (unless there's a very dominant planet that overrides sect)
    assert result_day.winner is not None
    assert result_night.winner is not None
    
    # At minimum, the scores should be different
    day_scores = result_day.scores
    night_scores = result_night.scores
    
    # Find common planets and verify sect affects scoring
    common_planets = set(day_scores.keys()) & set(night_scores.keys())
    assert len(common_planets) > 0
    
    # At least one planet should have different scores
    score_differences = [abs(day_scores[p] - night_scores[p]) > 0.01 for p in common_planets]
    assert any(score_differences), "Sect should affect planet scores"