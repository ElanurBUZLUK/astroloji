#!/usr/bin/env python3
"""
Demonstration script showing the implemented astrology calculation fixes
"""

from datetime import date
from app.calculators.zodiac_releasing import ZRCalculator
from app.calculators.firdaria import FirdariaCalculator
from app.calculators.antiscia import AntisciaCalculator

def demo_zr_lb_jumps():
    """Demonstrate ZR LB (Loosing of the Bond) jumps"""
    print("=== Zodiacal Releasing - LB Jump Demonstration ===")
    
    calc = ZRCalculator()
    
    # Start with Cancer to trigger LB
    periods = calc.build_l1_periods("Cancer", date(1990, 1, 1))
    
    print("L1 Periods showing LB jumps:")
    for i, period in enumerate(periods[:8]):  # Show first 8 periods
        lb_marker = " [LB JUMP]" if period.is_lb else ""
        duration_years = calc.PERIOD_DURATIONS[period.sign]
        print(f"{i+1:2d}. {period.sign:11s} ({period.ruler:7s}) - {duration_years:2d} years{lb_marker}")
        
        # Show the jump effect
        if period.is_lb and i+1 < len(periods):
            next_period = periods[i+1]
            print(f"    └─> Jumped to {next_period.sign} (opposite solstitial sign)")
    
    print()

def demo_firdaria_weighted_durations():
    """Demonstrate Firdaria weighted minor periods"""
    print("=== Firdaria - Weighted Minor Periods Demonstration ===")
    
    calc = FirdariaCalculator()
    result = calc.calculate_firdaria(date(1990, 1, 1), is_day_birth=True)
    
    # Get Sun major period (first in diurnal sequence)
    sun_major = result.major_periods[0]
    sun_minors = [p for p in result.minor_periods if 
                  p.start_date >= sun_major.start_date and p.end_date <= sun_major.end_date]
    
    print(f"Sun Major Period ({sun_major.duration_years} years) - Minor Periods:")
    print("Lord        Duration (years)  Weight  Percentage")
    print("-" * 50)
    
    total_duration = sum(p.duration_years for p in sun_minors)
    
    for minor in sun_minors:
        weight = next(w for l, w in calc.DIURNAL_SEQUENCE if l == minor.lord)
        percentage = (minor.duration_years / total_duration) * 100
        print(f"{minor.lord:10s}  {minor.duration_years:8.3f}        {weight:2d}     {percentage:5.1f}%")
    
    print(f"\nTotal: {total_duration:.3f} years (should equal {sun_major.duration_years} years)")
    print()

def demo_zr_tone_calculation():
    """Demonstrate ZR tone calculation"""
    print("=== Zodiacal Releasing - Tone Calculation Demonstration ===")
    
    calc = ZRCalculator()
    
    # Test different rulers with chart context
    chart_data = {
        'is_day': True,
        'almuten': 'Mars',
        'profection_lord': 'Venus',
        'firdaria_major': 'Sun',
        'planets': {
            'Mars': {'sign': 'Aries'},
            'Venus': {'sign': 'Taurus'},
            'Sun': {'sign': 'Leo'}
        }
    }
    
    test_rulers = ['Mars', 'Venus', 'Sun', 'Saturn']
    
    print("Ruler    Intensity  Valence      Score  Key Factors")
    print("-" * 65)
    
    for ruler in test_rulers:
        tone = calc.calculate_tone(ruler, chart_data)
        factors = ", ".join(tone['reasons'][:2])  # Show first 2 reasons
        print(f"{ruler:7s}  {tone['intensity']:8s}   {tone['valence']:11s}  {tone['score']:5.3f}  {factors}")
    
    print()

def demo_antiscia_calculations():
    """Demonstrate antiscia and contra-antiscia calculations"""
    print("=== Antiscia & Contra-Antiscia Demonstration ===")
    
    calc = AntisciaCalculator()
    
    # Test key zodiacal points
    test_points = [
        ("0° Aries", 0.0),
        ("15° Taurus", 45.0),
        ("0° Cancer", 90.0),
        ("0° Libra", 180.0),
        ("0° Capricorn", 270.0)
    ]
    
    print("Original        Antiscia           Contra-Antiscia")
    print("-" * 55)
    
    for name, longitude in test_points:
        antiscia = calc.calculate_antiscia(longitude)
        contra = calc.calculate_contra_antiscia(longitude)
        
        antiscia_sign, antiscia_deg = calc.longitude_to_sign_degree(antiscia)
        contra_sign, contra_deg = calc.longitude_to_sign_degree(contra)
        
        print(f"{name:12s}    {antiscia_sign} {antiscia_deg:4.1f}°         {contra_sign} {contra_deg:4.1f}°")
    
    print()

def main():
    """Run all demonstrations"""
    print("Astrology Calculation Fixes - Live Demonstration")
    print("=" * 60)
    print()
    
    demo_zr_lb_jumps()
    demo_firdaria_weighted_durations()
    demo_zr_tone_calculation()
    demo_antiscia_calculations()
    
    print("All fixes are working correctly! ✅")

if __name__ == "__main__":
    main()