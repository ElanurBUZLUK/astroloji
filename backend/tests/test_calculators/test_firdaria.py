"""
Tests for Firdaria (Persian Periods) calculator
"""
import pytest
from datetime import date, timedelta
from app.calculators.firdaria import FirdariaCalculator

def test_firdaria_calculator_initialization():
    """Test Firdaria calculator initialization"""
    calc = FirdariaCalculator()
    assert calc is not None
    assert len(calc.DIURNAL_SEQUENCE) == 7
    assert len(calc.NOCTURNAL_SEQUENCE) == 7

def test_sequence_durations():
    """Test that sequence durations are correct"""
    calc = FirdariaCalculator()
    
    # Check diurnal sequence
    expected_diurnal = [
        ("Sun", 10), ("Venus", 8), ("Mercury", 13), ("Moon", 9),
        ("Saturn", 11), ("Jupiter", 12), ("Mars", 7)
    ]
    assert calc.DIURNAL_SEQUENCE == expected_diurnal
    
    # Check nocturnal sequence
    expected_nocturnal = [
        ("Moon", 9), ("Saturn", 11), ("Jupiter", 12), ("Mars", 7),
        ("Sun", 10), ("Venus", 8), ("Mercury", 13)
    ]
    assert calc.NOCTURNAL_SEQUENCE == expected_nocturnal

def test_major_periods_day_birth():
    """Test major periods for day birth"""
    calc = FirdariaCalculator()
    birth_date = date(1990, 1, 1)
    
    result = calc.calculate_firdaria(birth_date, is_day_birth=True)
    
    assert len(result.major_periods) == 7
    
    # Check sequence order for day birth
    expected_lords = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
    actual_lords = [p.lord for p in result.major_periods]
    assert actual_lords == expected_lords
    
    # Check durations
    expected_durations = [10, 8, 13, 9, 11, 12, 7]
    actual_durations = [p.duration_years for p in result.major_periods]
    assert actual_durations == expected_durations
    
    # Check dates are continuous
    for i in range(1, len(result.major_periods)):
        assert result.major_periods[i-1].end_date == result.major_periods[i].start_date

def test_major_periods_night_birth():
    """Test major periods for night birth"""
    calc = FirdariaCalculator()
    birth_date = date(1990, 1, 1)
    
    result = calc.calculate_firdaria(birth_date, is_day_birth=False)
    
    assert len(result.major_periods) == 7
    
    # Check sequence order for night birth
    expected_lords = ["Moon", "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury"]
    actual_lords = [p.lord for p in result.major_periods]
    assert actual_lords == expected_lords

def test_minor_periods_weighted_durations():
    """Test that minor periods use weighted durations, not equal slices"""
    calc = FirdariaCalculator()
    birth_date = date(1990, 1, 1)
    
    result = calc.calculate_firdaria(birth_date, is_day_birth=True)
    
    # Get Sun major period (first in diurnal sequence)
    sun_major = result.major_periods[0]
    assert sun_major.lord == "Sun"
    
    # Get minor periods for Sun major period
    sun_minors = [p for p in result.minor_periods if 
                  p.start_date >= sun_major.start_date and p.end_date <= sun_major.end_date]
    
    assert len(sun_minors) == 7
    
    # Check that minor periods are NOT equal duration
    durations = [p.duration_years for p in sun_minors]
    
    # They should be proportional to major period durations
    # Sun minor should be longest (10 years weight)
    # Mars minor should be shortest (7 years weight)
    sun_minor_duration = next(p.duration_years for p in sun_minors if p.lord == "Sun")
    mars_minor_duration = next(p.duration_years for p in sun_minors if p.lord == "Mars")
    
    # Sun minor should be longer than Mars minor
    assert sun_minor_duration > mars_minor_duration
    
    # Check proportions are roughly correct
    # Sun (10) vs Mars (7) should be about 10/7 ratio
    ratio = sun_minor_duration / mars_minor_duration
    expected_ratio = 10 / 7
    assert abs(ratio - expected_ratio) < 0.1  # Allow small floating point errors

def test_minor_periods_sum_to_major():
    """Test that minor periods sum exactly to their major period"""
    calc = FirdariaCalculator()
    birth_date = date(1990, 1, 1)
    
    result = calc.calculate_firdaria(birth_date, is_day_birth=True)
    
    for major_period in result.major_periods:
        # Get minor periods for this major period
        minors = [p for p in result.minor_periods if 
                  p.start_date >= major_period.start_date and p.end_date <= major_period.end_date]
        
        # Check that minor periods cover the entire major period
        assert minors[0].start_date == major_period.start_date
        assert minors[-1].end_date == major_period.end_date
        
        # Check continuity
        for i in range(1, len(minors)):
            assert minors[i-1].end_date == minors[i].start_date

def test_minor_period_sequence_order():
    """Test that minor periods follow correct sequence starting from major lord"""
    calc = FirdariaCalculator()
    birth_date = date(1990, 1, 1)
    
    result = calc.calculate_firdaria(birth_date, is_day_birth=True)
    
    # Test Venus major period (2nd in sequence)
    venus_major = result.major_periods[1]
    assert venus_major.lord == "Venus"
    
    # Get minor periods for Venus major
    venus_minors = [p for p in result.minor_periods if 
                    p.start_date >= venus_major.start_date and p.end_date <= venus_major.end_date]
    
    # Minor sequence should start with Venus and follow diurnal order
    expected_minor_sequence = ["Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars", "Sun"]
    actual_minor_sequence = [p.lord for p in venus_minors]
    
    assert actual_minor_sequence == expected_minor_sequence

def test_current_period_detection():
    """Test current period detection"""
    calc = FirdariaCalculator()
    
    # Use a birth date that makes today fall in a specific period
    birth_date = date(1980, 1, 1)  # 44+ years ago
    
    result = calc.calculate_firdaria(birth_date, is_day_birth=True)
    
    # Should find current major and minor periods
    assert result.current_major is not None
    assert result.current_minor is not None
    
    # Current date should be within the periods
    today = date.today()
    assert result.current_major.start_date <= today <= result.current_major.end_date
    assert result.current_minor.start_date <= today <= result.current_minor.end_date

def test_firdaria_timeline_api():
    """Test the timeline API method"""
    calc = FirdariaCalculator()
    birth_date = date(1990, 1, 1)
    
    timeline = calc.get_firdaria_timeline(birth_date, is_day_birth=True, years_ahead=10)
    
    assert "major_periods" in timeline
    assert "minor_periods" in timeline
    assert "current" in timeline
    assert "diagnostics" in timeline
    
    # Should have reasonable number of periods
    assert len(timeline["major_periods"]) > 0
    assert len(timeline["minor_periods"]) > 0

def test_lord_themes():
    """Test lord themes are available"""
    calc = FirdariaCalculator()
    
    # Test all major lords have themes
    for lord, _ in calc.DIURNAL_SEQUENCE:
        themes = calc.get_lord_themes(lord)
        assert len(themes) > 0
        assert isinstance(themes, list)
        assert all(isinstance(theme, str) for theme in themes)
    
    # Test unknown lord
    unknown_themes = calc.get_lord_themes("Unknown")
    assert unknown_themes == ["Unknown themes"]

def test_weighted_vs_equal_duration_difference():
    """Test that weighted durations are significantly different from equal durations"""
    calc = FirdariaCalculator()
    birth_date = date(1990, 1, 1)
    
    result = calc.calculate_firdaria(birth_date, is_day_birth=True)
    
    # Get first major period and its minors
    first_major = result.major_periods[0]
    first_minors = [p for p in result.minor_periods if 
                    p.start_date >= first_major.start_date and p.end_date <= first_major.end_date]
    
    # Calculate what equal durations would be
    total_days = (first_major.end_date - first_major.start_date).days
    equal_duration_days = total_days / 7
    
    # Check that actual durations vary significantly from equal
    actual_durations_days = [(p.end_date - p.start_date).days for p in first_minors]
    
    # At least some periods should be significantly different from equal duration
    significant_differences = [abs(d - equal_duration_days) > equal_duration_days * 0.1 
                              for d in actual_durations_days]
    
    assert any(significant_differences), "Weighted durations should differ significantly from equal durations"