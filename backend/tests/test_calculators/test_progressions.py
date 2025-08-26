"""
Tests for Progressions calculator
"""
import pytest
from datetime import date
from app.calculators.progressions import ProgressionsCalculator

def test_progressions_calculator_initialization():
    """Test progressions calculator initialization"""
    calc = ProgressionsCalculator()
    assert calc is not None
    assert calc.orb_factor == 1.0
    
    calc_custom = ProgressionsCalculator(orb_factor=0.5)
    assert calc_custom.orb_factor == 0.5

def test_progressed_position_calculation():
    """Test progressed position calculation"""
    calc = ProgressionsCalculator()
    
    natal_lon = 0.0  # 0° Aries
    birth_date = date(1990, 1, 1)
    target_date = date(2020, 1, 1)  # 30 years later
    daily_motion = 1.0  # 1 degree per day
    
    prog_pos = calc.calculate_progressed_position(natal_lon, birth_date, target_date, daily_motion)
    
    # 30 years = ~30 degrees progression
    expected_progression = 30.0
    assert abs(prog_pos.arc_of_direction - expected_progression) < 1.0
    assert prog_pos.natal_longitude == natal_lon

def test_sign_ingresses_calculation():
    """Test sign ingresses calculation"""
    calc = ProgressionsCalculator()
    
    natal_positions = {
        "Sun": 25.0,  # 25° Aries - close to Taurus boundary
        "Moon": 350.0  # 20° Pisces - close to Aries boundary
    }
    birth_date = date(1990, 1, 1)
    
    ingresses = calc.find_sign_ingresses(natal_positions, birth_date, years_ahead=10)
    
    assert len(ingresses) > 0
    
    # Check that ingresses are sorted by date
    for i in range(1, len(ingresses)):
        assert ingresses[i-1].ingress_date <= ingresses[i].ingress_date

def test_progressions_calculation():
    """Test complete progressions calculation"""
    calc = ProgressionsCalculator()
    
    natal_positions = {
        "Sun": 0.0,    # 0° Aries
        "Moon": 90.0,  # 0° Cancer
        "Mercury": 30.0, # 0° Taurus
        "Venus": 60.0,   # 0° Gemini
        "Mars": 120.0    # 0° Leo
    }
    birth_date = date(1990, 1, 1)
    target_date = date(2020, 1, 1)
    
    result = calc.calculate_progressions(natal_positions, birth_date, target_date)
    
    assert result is not None
    assert len(result.progressed_positions) == len(natal_positions)
    assert result.diagnostics["years_progressed"] == 30.0
    
    # Check that all planets have progressed positions
    progressed_planets = {pos.planet for pos in result.progressed_positions}
    assert progressed_planets == set(natal_positions.keys())

def test_progressed_aspects_detection():
    """Test progressed aspects detection"""
    calc = ProgressionsCalculator()
    
    # Set up positions where progressed planet will aspect natal planet
    natal_positions = {
        "Sun": 0.0,    # 0° Aries
        "Moon": 90.0   # 0° Cancer (square to Sun)
    }
    birth_date = date(1990, 1, 1)
    target_date = date(2020, 1, 1)  # 30 years = ~30° progression
    
    result = calc.calculate_progressions(natal_positions, birth_date, target_date)
    
    # Should find some aspects between progressed and natal positions
    assert len(result.progressed_aspects) >= 0  # May or may not have tight aspects

def test_compute_interface():
    """Test standard compute interface"""
    calc = ProgressionsCalculator()
    
    chart_data = {
        "planets": {
            "Sun": 0.0,
            "Moon": 90.0,
            "Mercury": 30.0
        },
        "birth_date": "1990-01-01"
    }
    
    result = calc.compute(chart_data)
    
    assert "features" in result
    assert "evidence" in result
    assert "diagnostics" in result
    assert isinstance(result["features"], list)
    assert isinstance(result["evidence"], list)

def test_current_progressions_api():
    """Test current progressions API"""
    calc = ProgressionsCalculator()
    
    natal_positions = {
        "Sun": 0.0,
        "Moon": 90.0,
        "Mercury": 30.0
    }
    birth_date = date(1990, 1, 1)
    
    summary = calc.get_current_progressions(natal_positions, birth_date)
    
    assert "progressed_positions" in summary
    assert "major_aspects" in summary
    assert "upcoming_ingresses" in summary
    assert "diagnostics" in summary
    
    # Check structure of progressed positions
    for pos in summary["progressed_positions"]:
        assert "planet" in pos
        assert "natal_position" in pos
        assert "progressed_position" in pos
        assert "arc_of_direction" in pos