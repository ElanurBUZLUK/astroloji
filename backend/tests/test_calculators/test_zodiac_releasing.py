"""
Tests for Zodiacal Releasing calculator
"""
import pytest
from datetime import date
from app.calculators.zodiac_releasing import ZRCalculator

def test_zr_calculator_initialization():
    """Test ZR calculator initialization"""
    calc = ZRCalculator()
    assert calc is not None
    assert len(calc.PERIOD_DURATIONS) == 12
    assert len(calc.SIGN_ORDER) == 12

def test_period_durations():
    """Test ZR period durations are correct"""
    calc = ZRCalculator()
    
    expected_durations = {
        "Aries": 15, "Taurus": 8, "Gemini": 20, "Cancer": 25,
        "Leo": 19, "Virgo": 20, "Libra": 8, "Scorpio": 15,
        "Sagittarius": 12, "Capricorn": 27, "Aquarius": 30, "Pisces": 12
    }
    
    for sign, expected_duration in expected_durations.items():
        assert calc.PERIOD_DURATIONS[sign] == expected_duration

def test_lot_calculations():
    """Test Lot of Spirit and Fortune calculations"""
    calc = ZRCalculator()
    
    # Test data: Sun at 0° Aries, Moon at 0° Taurus, ASC at 0° Gemini
    sun_lon = 0.0    # 0° Aries
    moon_lon = 30.0  # 0° Taurus  
    asc_lon = 60.0   # 0° Gemini
    
    # Day birth
    spirit_day = calc.lot_of_spirit(sun_lon, moon_lon, asc_lon, True)
    fortune_day = calc.lot_of_fortune(sun_lon, moon_lon, asc_lon, True)
    
    # Day Spirit: ASC + Sun - Moon = 60 + 0 - 30 = 30° (0° Taurus)
    assert abs(spirit_day - 30.0) < 0.01
    
    # Day Fortune: ASC + Moon - Sun = 60 + 30 - 0 = 90° (0° Cancer)
    assert abs(fortune_day - 90.0) < 0.01
    
    # Night birth
    spirit_night = calc.lot_of_spirit(sun_lon, moon_lon, asc_lon, False)
    fortune_night = calc.lot_of_fortune(sun_lon, moon_lon, asc_lon, False)
    
    # Night Spirit: ASC + Moon - Sun = 60 + 30 - 0 = 90° (0° Cancer)
    assert abs(spirit_night - 90.0) < 0.01
    
    # Night Fortune: ASC + Sun - Moon = 60 + 0 - 30 = 30° (0° Taurus)
    assert abs(fortune_night - 30.0) < 0.01

def test_longitude_to_sign():
    """Test longitude to sign conversion"""
    calc = ZRCalculator()
    
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
        (330.0, "Pisces")
    ]
    
    for longitude, expected_sign in test_cases:
        assert calc.longitude_to_sign(longitude) == expected_sign

def test_lb_transition_detection():
    """Test Loosing of Bond transition detection"""
    calc = ZRCalculator()
    
    # LB transitions
    assert calc.is_lb_transition("Cancer", "Leo")
    assert calc.is_lb_transition("Capricorn", "Aquarius")
    
    # Non-LB transitions
    assert not calc.is_lb_transition("Aries", "Taurus")
    assert not calc.is_lb_transition("Leo", "Virgo")

def test_lb_jump():
    """Test LB jump to opposite solstitial sign"""
    calc = ZRCalculator()
    
    assert calc.apply_lb_jump("Cancer") == "Capricorn"
    assert calc.apply_lb_jump("Capricorn") == "Cancer"
    assert calc.apply_lb_jump("Aries") == "Aries"  # No jump

def test_peak_period_detection():
    """Test peak period detection based on Fortune angles"""
    calc = ZRCalculator()
    
    # Fortune at 0° Aries
    fortune_sign = "Aries"
    
    # Test angular relationships (1st, 4th, 7th, 10th)
    assert calc.is_peak_period("Aries", fortune_sign)      # 1st house
    assert calc.is_peak_period("Cancer", fortune_sign)     # 4th house
    assert calc.is_peak_period("Libra", fortune_sign)      # 7th house
    assert calc.is_peak_period("Capricorn", fortune_sign)  # 10th house
    
    # Non-angular signs should not be peaks
    assert not calc.is_peak_period("Taurus", fortune_sign)
    assert not calc.is_peak_period("Gemini", fortune_sign)

def test_zr_timeline_creation():
    """Test ZR timeline creation"""
    calc = ZRCalculator()
    
    # Test data
    sun_lon = 120.0  # 0° Leo
    moon_lon = 210.0 # 0° Scorpio
    asc_lon = 0.0    # 0° Aries
    is_day = True
    birth_date = date(1990, 1, 1)
    
    timeline = calc.compute_zr_timeline(sun_lon, moon_lon, asc_lon, is_day, birth_date)
    
    assert timeline is not None
    assert timeline.lot_used == "Spirit"
    assert len(timeline.l1_periods) > 0
    assert len(timeline.l2_periods) > 0
    assert timeline.diagnostics["l1_count"] > 0
    assert timeline.diagnostics["l2_count"] > 0
    
    # Check that periods have proper structure
    first_period = timeline.l1_periods[0]
    assert first_period.level == 1
    assert first_period.sign in calc.SIGN_ORDER
    assert first_period.ruler in calc.sign_rulers.values()
    assert first_period.start_date == birth_date

def test_lb_jump_application():
    """Test that LB jumps are actually applied in the sequence"""
    calc = ZRCalculator()
    
    # Start with Cancer to trigger LB
    periods = calc.build_l1_periods("Cancer", date(1990, 1, 1))
    
    # Find Cancer period
    cancer_period = next(p for p in periods if p.sign == "Cancer")
    cancer_index = periods.index(cancer_period)
    
    # The period after Cancer should jump to Capricorn (not Leo)
    if cancer_index + 1 < len(periods):
        next_period = periods[cancer_index + 1]
        # Cancer period should be marked as LB
        assert cancer_period.is_lb == True
        # Next period should be Capricorn (jumped), not Leo (natural)
        assert next_period.sign == "Capricorn"

def test_lb_jump_capricorn_to_cancer():
    """Test LB jump from Capricorn to Cancer"""
    calc = ZRCalculator()
    
    # Start with Capricorn to trigger LB
    periods = calc.build_l1_periods("Capricorn", date(1990, 1, 1))
    
    # Find Capricorn period
    capricorn_period = next(p for p in periods if p.sign == "Capricorn")
    capricorn_index = periods.index(capricorn_period)
    
    # The period after Capricorn should jump to Cancer (not Aquarius)
    if capricorn_index + 1 < len(periods):
        next_period = periods[capricorn_index + 1]
        # Capricorn period should be marked as LB
        assert capricorn_period.is_lb == True
        # Next period should be Cancer (jumped), not Aquarius (natural)
        assert next_period.sign == "Cancer"

def test_l2_lb_application():
    """Test that LB jumps are applied in L2 subdivisions"""
    calc = ZRCalculator()
    
    # Import ZRPeriod from the module
    from app.calculators.zodiac_releasing import ZRPeriod
    
    # Create a Cancer L1 period to subdivide
    cancer_period = ZRPeriod(
        level=1,
        sign="Cancer",
        ruler="Moon",
        start_date=date(1990, 1, 1),
        end_date=date(2015, 1, 1)  # 25 years
    )
    
    l2_periods = calc.subdivide_l2(cancer_period)
    
    # Find the Cancer L2 period (should be first)
    cancer_l2 = next(p for p in l2_periods if p.sign == "Cancer")
    cancer_l2_index = l2_periods.index(cancer_l2)
    
    # The L2 period after Cancer should jump to Capricorn
    if cancer_l2_index + 1 < len(l2_periods):
        next_l2_period = l2_periods[cancer_l2_index + 1]
        assert cancer_l2.is_lb == True
        assert next_l2_period.sign == "Capricorn"

def test_l2_peaks_marked():
    """Test that L2 periods have peaks marked"""
    calc = ZRCalculator()
    
    # Test with Fortune in Aries for clear angular relationships
    sun_lon = 0.0    # 0° Aries
    moon_lon = 30.0  # 0° Taurus  
    asc_lon = 60.0   # 0° Gemini
    is_day = True
    birth_date = date(1990, 1, 1)
    
    timeline = calc.compute_zr_timeline(sun_lon, moon_lon, asc_lon, is_day, birth_date)
    
    # Check that some L2 periods are marked as peaks
    peak_l2_periods = [p for p in timeline.l2_periods if p.is_peak]
    assert len(peak_l2_periods) > 0
    
    # Verify peak periods are at Fortune angles
    fortune_sign = timeline.diagnostics["fortune_sign"]
    for peak_period in peak_l2_periods:
        assert calc.is_peak_period(peak_period.sign, fortune_sign)