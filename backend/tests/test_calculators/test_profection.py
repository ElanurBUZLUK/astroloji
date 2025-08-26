"""
Tests for Profection calculator
"""
import pytest
from datetime import date
from app.calculators.profection import ProfectionCalculator

def test_profection_calculator_initialization():
    """Test profection calculator initialization"""
    calc = ProfectionCalculator()
    assert calc is not None
    assert len(calc.HOUSE_TOPICS) == 12
    assert len(calc.SIGN_RULERS) == 12

def test_age_calculation():
    """Test age calculation"""
    calc = ProfectionCalculator()
    
    # Test exact birthday
    birth_date = date(1990, 6, 15)
    target_date = date(2023, 6, 15)
    age = calc.calculate_age(birth_date, target_date)
    assert age == 33
    
    # Test before birthday
    target_date = date(2023, 6, 14)
    age = calc.calculate_age(birth_date, target_date)
    assert age == 32
    
    # Test after birthday
    target_date = date(2023, 6, 16)
    age = calc.calculate_age(birth_date, target_date)
    assert age == 33

def test_profection_house_calculation():
    """Test profection house calculation"""
    calc = ProfectionCalculator()
    
    birth_date = date(1990, 6, 15)
    asc_longitude = 0.0  # 0° Aries
    
    # Age 0 = House 1
    target_date = date(1990, 6, 15)  # Birth day
    result = calc.calculate_profection(birth_date, asc_longitude, target_date)
    assert result.age == 0
    assert result.profected_house == 1
    assert result.profected_sign == "Aries"
    
    # Age 1 = House 2
    target_date = date(1991, 6, 15)
    result = calc.calculate_profection(birth_date, asc_longitude, target_date)
    assert result.age == 1
    assert result.profected_house == 2
    assert result.profected_sign == "Taurus"
    
    # Age 12 = House 1 again (cycle repeats)
    target_date = date(2002, 6, 15)
    result = calc.calculate_profection(birth_date, asc_longitude, target_date)
    assert result.age == 12
    assert result.profected_house == 1
    assert result.profected_sign == "Aries"

def test_profection_with_different_ascendant():
    """Test profection with different ascendant signs"""
    calc = ProfectionCalculator()
    
    birth_date = date(1990, 6, 15)
    target_date = date(1991, 6, 15)  # Age 1, House 2
    
    # ASC in Leo (120°)
    asc_longitude = 120.0
    result = calc.calculate_profection(birth_date, asc_longitude, target_date)
    assert result.profected_sign == "Virgo"  # Leo + 1 house = Virgo
    assert result.year_lord == "Mercury"  # Ruler of Virgo
    
    # ASC in Scorpio (210°)
    asc_longitude = 210.0
    result = calc.calculate_profection(birth_date, asc_longitude, target_date)
    assert result.profected_sign == "Sagittarius"  # Scorpio + 1 house = Sagittarius
    assert result.year_lord == "Jupiter"  # Ruler of Sagittarius

def test_year_lord_calculation():
    """Test year lord calculation"""
    calc = ProfectionCalculator()
    
    birth_date = date(1990, 6, 15)
    asc_longitude = 0.0  # Aries ASC
    
    test_cases = [
        (1991, 2, "Taurus", "Venus"),
        (1992, 3, "Gemini", "Mercury"),
        (1993, 4, "Cancer", "Moon"),
        (1994, 5, "Leo", "Sun"),
        (1995, 6, "Virgo", "Mercury"),
        (1996, 7, "Libra", "Venus"),
        (1997, 8, "Scorpio", "Mars"),
        (1998, 9, "Sagittarius", "Jupiter"),
        (1999, 10, "Capricorn", "Saturn"),
        (2000, 11, "Aquarius", "Saturn"),
        (2001, 12, "Pisces", "Jupiter")
    ]
    
    for year, expected_house, expected_sign, expected_lord in test_cases:
        target_date = date(year, 6, 15)
        result = calc.calculate_profection(birth_date, asc_longitude, target_date)
        assert result.profected_house == expected_house
        assert result.profected_sign == expected_sign
        assert result.year_lord == expected_lord

def test_activated_topics():
    """Test activated topics for each house"""
    calc = ProfectionCalculator()
    
    birth_date = date(1990, 6, 15)
    asc_longitude = 0.0
    
    # Test House 1 topics
    target_date = date(1990, 6, 15)  # Age 0, House 1
    result = calc.calculate_profection(birth_date, asc_longitude, target_date)
    assert "Identity" in result.activated_topics
    assert "Vitality" in result.activated_topics
    
    # Test House 7 topics
    target_date = date(1996, 6, 15)  # Age 6, House 7
    result = calc.calculate_profection(birth_date, asc_longitude, target_date)
    assert "Partnerships" in result.activated_topics
    assert "Marriage" in result.activated_topics

def test_profection_timeline():
    """Test profection timeline generation"""
    calc = ProfectionCalculator()
    
    birth_date = date(1990, 6, 15)
    asc_longitude = 0.0
    
    timeline = calc.get_profection_timeline(birth_date, asc_longitude, years_ahead=5)
    
    assert len(timeline) == 6  # Current year + 5 ahead
    assert all(isinstance(p.age, int) for p in timeline)
    assert all(1 <= p.profected_house <= 12 for p in timeline)
    assert all(p.profected_sign in calc.SIGNS for p in timeline)

def test_monthly_profections():
    """Test monthly profections within a year"""
    calc = ProfectionCalculator()
    
    birth_date = date(1990, 6, 15)
    asc_longitude = 0.0  # Aries ASC
    
    year_lord_periods = calc.get_year_lord_periods(birth_date, asc_longitude, 1991)
    
    assert year_lord_periods["year"] == 1991
    assert year_lord_periods["annual"]["house"] == 2  # Age 1 = House 2
    assert year_lord_periods["annual"]["sign"] == "Taurus"
    assert year_lord_periods["annual"]["year_lord"] == "Venus"
    
    # Check monthly profections
    monthly = year_lord_periods["monthly"]
    assert len(monthly) == 12
    
    # First month should be same as annual
    assert monthly[0]["house"] == 2
    assert monthly[0]["sign"] == "Taurus"
    assert monthly[0]["lord"] == "Venus"
    
    # Second month should advance one house
    assert monthly[1]["house"] == 3
    assert monthly[1]["sign"] == "Gemini"
    assert monthly[1]["lord"] == "Mercury"