"""
Tests for Ephemeris service
"""
import pytest
from datetime import datetime
from app.calculators.ephemeris import EphemerisService, PlanetPosition

def test_ephemeris_service_initialization():
    """Test ephemeris service can be initialized"""
    ephemeris = EphemerisService()
    assert ephemeris is not None
    assert ephemeris.flags is not None

def test_julian_day_calculation():
    """Test Julian Day calculation"""
    ephemeris = EphemerisService()
    
    # Test known date: January 1, 2000, 12:00 UTC
    dt = datetime(2000, 1, 1, 12, 0, 0)
    jd = ephemeris.julian_day(dt)
    
    # Known Julian Day for this date
    expected_jd = 2451545.0
    assert abs(jd - expected_jd) < 0.1

def test_planet_position_properties():
    """Test planet position properties"""
    pos = PlanetPosition(
        name="Sun",
        longitude=15.5,  # 15.5° Aries
        latitude=0.0,
        distance=1.0,
        speed_longitude=1.0,
        speed_latitude=0.0,
        speed_distance=0.0
    )
    
    assert pos.sign == "Aries"
    assert abs(pos.degree_in_sign - 15.5) < 0.01
    assert not pos.is_retrograde

def test_retrograde_detection():
    """Test retrograde detection"""
    pos = PlanetPosition(
        name="Mercury",
        longitude=120.0,
        latitude=0.0,
        distance=1.0,
        speed_longitude=-0.5,  # Negative speed = retrograde
        speed_latitude=0.0,
        speed_distance=0.0
    )
    
    assert pos.is_retrograde

def test_sign_calculation():
    """Test zodiac sign calculation from longitude"""
    test_cases = [
        (0.0, "Aries"),
        (30.0, "Taurus"),
        (60.0, "Gemini"),
        (90.0, "Cancer"),
        (120.0, "Leo"),
        (150.0, "Virgo"),
        (180.0, "Libra"),
        (210.0, "Scorpio"),
        (240.0, "Sagittarius"),
        (270.0, "Capricorn"),
        (300.0, "Aquarius"),
        (330.0, "Pisces"),
        (359.9, "Pisces")
    ]
    
    for longitude, expected_sign in test_cases:
        pos = PlanetPosition("Test", longitude, 0, 1, 0, 0, 0)
        assert pos.sign == expected_sign

def test_whole_sign_houses():
    """Test Whole Sign house calculation"""
    ephemeris = EphemerisService()
    
    # ASC at 15° Aries (15.0)
    asc_longitude = 15.0
    cusps = ephemeris.get_whole_sign_houses(asc_longitude)
    
    assert len(cusps) == 12
    assert cusps[0] == 0.0    # House 1 starts at 0° Aries
    assert cusps[1] == 30.0   # House 2 starts at 0° Taurus
    assert cusps[11] == 330.0 # House 12 starts at 0° Pisces

def test_day_night_determination():
    """Test day/night birth determination"""
    ephemeris = EphemerisService()
    
    # Mock planet positions
    planets = {
        'Sun': PlanetPosition("Sun", 120.0, 0, 1, 0, 0, 0)  # 0° Leo
    }
    
    # Mock house system with ASC at 90° (0° Cancer)
    from app.calculators.ephemeris import HouseSystem
    houses = HouseSystem(
        cusps=[90, 120, 150, 180, 210, 240, 270, 300, 330, 0, 30, 60],
        asc=90.0,  # 0° Cancer
        mc=0.0,
        armc=0.0,
        vertex=0.0,
        equatorial_asc=0.0,
        co_asc_koch=0.0,
        co_asc_munkasey=0.0,
        polar_asc=0.0
    )
    
    # Sun at 120° (0° Leo) with ASC at 90° (0° Cancer) = day birth
    is_day = ephemeris.is_day_birth(planets, houses)
    assert is_day