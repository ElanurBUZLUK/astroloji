"""
Integration tests for chart calculation workflow
"""
import pytest
from datetime import datetime, date
from app.calculators.ephemeris import EphemerisService, PlanetPosition
from app.calculators.almuten import almuten_figuris, Point
from app.calculators.zodiac_releasing import ZRCalculator

@pytest.mark.integration
def test_full_chart_calculation_workflow():
    """Test complete chart calculation workflow"""
    
    # Sample birth data
    birth_datetime = datetime(1990, 6, 15, 14, 30, 0)  # June 15, 1990, 2:30 PM
    birth_date = birth_datetime.date()
    latitude = 40.7128  # New York
    longitude = -74.0060
    
    # Initialize services
    ephemeris = EphemerisService()
    zr_calc = ZRCalculator()
    
    try:
        # 1. Calculate Julian Day
        jd = ephemeris.julian_day(birth_datetime)
        assert jd > 0
        
        # 2. Get planet positions (mock for now since we don't have ephemeris files)
        # In real implementation, this would use Swiss Ephemeris
        mock_planets = {
            'Sun': PlanetPosition("Sun", 84.5, 0.0, 1.0, 1.0, 0.0, 0.0),      # ~24° Gemini
            'Moon': PlanetPosition("Moon", 210.3, 0.0, 1.0, 13.0, 0.0, 0.0),  # ~20° Scorpio
            'Mercury': PlanetPosition("Mercury", 75.2, 0.0, 1.0, 1.5, 0.0, 0.0), # ~15° Gemini
            'Venus': PlanetPosition("Venus", 45.8, 0.0, 1.0, 1.2, 0.0, 0.0),   # ~15° Taurus
            'Mars': PlanetPosition("Mars", 315.1, 0.0, 1.0, 0.5, 0.0, 0.0),   # ~15° Aquarius
            'Jupiter': PlanetPosition("Jupiter", 120.7, 0.0, 1.0, 0.3, 0.0, 0.0), # ~0° Leo
            'Saturn': PlanetPosition("Saturn", 285.4, 0.0, 1.0, 0.1, 0.0, 0.0)   # ~15° Capricorn
        }
        
        # 3. Calculate houses (mock)
        from app.calculators.ephemeris import HouseSystem
        mock_houses = HouseSystem(
            cusps=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
            asc=0.0,    # 0° Aries
            mc=270.0,   # 0° Capricorn
            armc=270.0,
            vertex=180.0,
            equatorial_asc=0.0,
            co_asc_koch=0.0,
            co_asc_munkasey=0.0,
            polar_asc=0.0
        )
        
        # 4. Determine day/night
        is_day = ephemeris.is_day_birth(mock_planets, mock_houses)
        
        # 5. Calculate lots
        lots = ephemeris.calculate_lots(mock_planets, mock_houses, is_day)
        assert 'Fortune' in lots
        assert 'Spirit' in lots
        
        # 6. Calculate Almuten Figuris
        almuten_points = [
            Point("Sun", mock_planets['Sun'].longitude, mock_planets['Sun'].sign, 
                  mock_planets['Sun'].degree_in_sign),
            Point("Moon", mock_planets['Moon'].longitude, mock_planets['Moon'].sign,
                  mock_planets['Moon'].degree_in_sign),
            Point("ASC", mock_houses.asc, "Aries", 0.0),
            Point("MC", mock_houses.mc, "Capricorn", 0.0),
            Point("Fortune", lots['Fortune'], ephemeris._longitude_to_sign(lots['Fortune']), 
                  lots['Fortune'] % 30),
            Point("Spirit", lots['Spirit'], ephemeris._longitude_to_sign(lots['Spirit']),
                  lots['Spirit'] % 30)
        ]
        
        chart_data = {"is_day": is_day}
        almuten_result = almuten_figuris(almuten_points, chart_data)
        
        assert almuten_result.winner is not None
        assert almuten_result.winner != "None"
        
        # 7. Calculate ZR timeline
        zr_timeline = zr_calc.compute_zr_timeline(
            mock_planets['Sun'].longitude,
            mock_planets['Moon'].longitude,
            mock_houses.asc,
            is_day,
            birth_date
        )
        
        assert zr_timeline is not None
        assert len(zr_timeline.l1_periods) > 0
        assert zr_timeline.lot_used == "Spirit"
        
        # 8. Verify integration
        assert zr_timeline.diagnostics['lot_longitude'] == lots['Spirit']
        
        print(f"✅ Chart calculation successful!")
        print(f"   Almuten: {almuten_result.winner}")
        print(f"   ZR Lot: {zr_timeline.lot_used} at {zr_timeline.diagnostics['lot_sign']}")
        print(f"   First ZR period: {zr_timeline.l1_periods[0].sign} ({zr_timeline.l1_periods[0].ruler})")
        
    finally:
        ephemeris.close()

def ephemeris_longitude_to_sign(longitude: float) -> str:
    """Helper function to convert longitude to sign"""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[int(longitude // 30)]

# Add the helper method to EphemerisService for testing
EphemerisService._longitude_to_sign = staticmethod(ephemeris_longitude_to_sign)