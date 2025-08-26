"""
Zodiacal Releasing (ZR) calculator
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import date, datetime, timedelta

@dataclass
class ZRPeriod:
    """ZR period information"""
    level: int  # L1, L2, L3, L4
    sign: str
    ruler: str
    start_date: date
    end_date: date
    is_peak: bool = False
    is_lb: bool = False  # Loosing of the Bond
    tone: str = ""

@dataclass
class ZRTimeline:
    """Complete ZR timeline"""
    l1_periods: List[ZRPeriod]
    l2_periods: List[ZRPeriod]
    lot_used: str  # Spirit, Fortune, Eros
    diagnostics: Dict[str, Any]

class ZRCalculator:
    """Zodiacal Releasing calculator"""
    
    # L1 period durations in years
    PERIOD_DURATIONS = {
        "Aries": 15, "Taurus": 8, "Gemini": 20, "Cancer": 25,
        "Leo": 19, "Virgo": 20, "Libra": 8, "Scorpio": 15,
        "Sagittarius": 12, "Capricorn": 27, "Aquarius": 30, "Pisces": 12
    }
    
    SIGN_ORDER = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    def __init__(self):
        self.sign_rulers = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
    
    def lot_of_spirit(self, sun_lon: float, moon_lon: float, asc_lon: float, is_day: bool) -> float:
        """Calculate Lot of Spirit longitude"""
        if is_day:
            # Day: ASC + Sun - Moon
            spirit_lon = (asc_lon + sun_lon - moon_lon) % 360
        else:
            # Night: ASC + Moon - Sun
            spirit_lon = (asc_lon + moon_lon - sun_lon) % 360
        return spirit_lon
    
    def lot_of_fortune(self, sun_lon: float, moon_lon: float, asc_lon: float, is_day: bool) -> float:
        """Calculate Lot of Fortune longitude"""
        if is_day:
            # Day: ASC + Moon - Sun
            fortune_lon = (asc_lon + moon_lon - sun_lon) % 360
        else:
            # Night: ASC + Sun - Moon
            fortune_lon = (asc_lon + sun_lon - moon_lon) % 360
        return fortune_lon
    
    def longitude_to_sign(self, longitude: float) -> str:
        """Convert longitude to zodiac sign"""
        return self.SIGN_ORDER[int(longitude // 30)]
    
    def is_lb_transition(self, from_sign: str, to_sign: str) -> bool:
        """Check if transition involves Loosing of the Bond"""
        # LB occurs when moving from Cancer to Leo or Capricorn to Aquarius
        return (from_sign == "Cancer" and to_sign == "Leo") or \
               (from_sign == "Capricorn" and to_sign == "Aquarius")
    
    def apply_lb_jump(self, current_sign: str) -> str:
        """Apply LB jump to opposite solstitial sign"""
        if current_sign == "Cancer":
            return "Capricorn"
        elif current_sign == "Capricorn":
            return "Cancer"
        return current_sign
    
    def is_peak_period(self, sign: str, fortune_sign: str) -> bool:
        """Check if period is a peak based on Fortune angles"""
        # Fortune angles: 1st (same), 10th, 7th, 4th houses
        fortune_index = self.SIGN_ORDER.index(fortune_sign)
        sign_index = self.SIGN_ORDER.index(sign)
        
        # Calculate angular relationships
        angles = [0, 3, 6, 9]  # 1st, 4th, 7th, 10th houses
        relative_position = (sign_index - fortune_index) % 12
        
        return relative_position in angles
    
    def calculate_tone(self, ruler: str, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate period tone based on dignity, sect, almuten link, receptions"""
        
        # Initialize tone components
        intensity = "medium"
        valence = "neutral"
        reasons = []
        score = 0.5  # Base neutral score
        
        # Get chart context if available
        is_day = chart_data.get('is_day', True)
        almuten = chart_data.get('almuten', None)
        profection_lord = chart_data.get('profection_lord', None)
        firdaria_major = chart_data.get('firdaria_major', None)
        firdaria_minor = chart_data.get('firdaria_minor', None)
        planet_positions = chart_data.get('planets', {})
        
        # 1. Sect evaluation
        diurnal_planets = ['Sun', 'Jupiter', 'Saturn']
        nocturnal_planets = ['Moon', 'Venus', 'Mars']
        
        if ruler in diurnal_planets and is_day:
            score += 0.15
            reasons.append(f"{ruler} in sect (diurnal)")
        elif ruler in nocturnal_planets and not is_day:
            score += 0.15
            reasons.append(f"{ruler} in sect (nocturnal)")
        elif ruler in diurnal_planets and not is_day:
            score -= 0.1
            reasons.append(f"{ruler} out of sect (diurnal at night)")
        elif ruler in nocturnal_planets and is_day:
            score -= 0.1
            reasons.append(f"{ruler} out of sect (nocturnal in day)")
        
        # 2. Almuten connection
        if almuten and ruler == almuten:
            score += 0.2
            intensity = "high"
            reasons.append(f"{ruler} is chart Almuten")
        
        # 3. Time-lord connections (reception/cooperation)
        active_lords = []
        if profection_lord:
            active_lords.append(profection_lord)
        if firdaria_major:
            active_lords.append(firdaria_major)
        if firdaria_minor:
            active_lords.append(firdaria_minor)
        
        # Check for mutual reception or cooperation
        for lord in active_lords:
            if lord == ruler:
                score += 0.15
                reasons.append(f"{ruler} is active time-lord")
            # TODO: Add mutual reception checks when dignity tables are available
        
        # 4. Essential dignity (simplified - would need full dignity tables)
        ruler_dignities = {
            'Sun': ['Leo'],
            'Moon': ['Cancer'],
            'Mercury': ['Gemini', 'Virgo'],
            'Venus': ['Taurus', 'Libra'],
            'Mars': ['Aries', 'Scorpio'],
            'Jupiter': ['Sagittarius', 'Pisces'],
            'Saturn': ['Capricorn', 'Aquarius']
        }
        
        # Check if ruler has dignity in current positions (simplified)
        if ruler in planet_positions:
            planet_sign = planet_positions[ruler].get('sign', '')
            if planet_sign in ruler_dignities.get(ruler, []):
                score += 0.1
                reasons.append(f"{ruler} in own sign ({planet_sign})")
        
        # 5. Determine final valence and intensity
        if score >= 0.7:
            valence = "supportive"
            intensity = "high"
        elif score >= 0.6:
            valence = "supportive"
        elif score <= 0.3:
            valence = "challenging"
            intensity = "high"
        elif score <= 0.4:
            valence = "challenging"
        
        if score >= 0.75 or score <= 0.25:
            intensity = "high"
        elif score >= 0.6 or score <= 0.4:
            intensity = "medium"
        else:
            intensity = "low"
        
        return {
            "intensity": intensity,
            "valence": valence,
            "score": round(score, 3),
            "reasons": reasons,
            "ruler": ruler
        }
    
    def build_l1_periods(self, start_sign: str, birth_date: date) -> List[ZRPeriod]:
        """Build L1 periods starting from given sign with proper LB jumps"""
        periods = []
        current_date = birth_date
        current_sign_index = self.SIGN_ORDER.index(start_sign)
        
        # Generate periods for reasonable timespan (e.g., 120 years)
        total_years = 0
        
        while total_years < 120:
            sign = self.SIGN_ORDER[current_sign_index % 12]
            
            # Check for LB transition BEFORE creating the period
            # LB occurs when we would naturally move from Cancer to Leo or Capricorn to Aquarius
            next_sign_index = (current_sign_index + 1) % 12
            next_sign = self.SIGN_ORDER[next_sign_index]
            
            duration = self.PERIOD_DURATIONS[sign]
            ruler = self.sign_rulers[sign]
            
            end_date = current_date + timedelta(days=duration * 365.25)
            
            # Check if this period ends with an LB transition
            is_lb_period = self.is_lb_transition(sign, next_sign)
            
            period = ZRPeriod(
                level=1,
                sign=sign,
                ruler=ruler,
                start_date=current_date,
                end_date=end_date,
                tone=self.calculate_tone(ruler, {}),
                is_lb=is_lb_period
            )
            
            periods.append(period)
            
            current_date = end_date
            total_years += duration
            
            # Apply LB jump AFTER creating the period
            if is_lb_period:
                # Jump to opposite solstitial sign instead of natural progression
                jumped_sign = self.apply_lb_jump(sign)
                current_sign_index = self.SIGN_ORDER.index(jumped_sign)
            else:
                # Natural progression
                current_sign_index = next_sign_index
        
        return periods
    
    def subdivide_l2(self, l1_period: ZRPeriod) -> List[ZRPeriod]:
        """Subdivide L1 period into L2 subperiods with LB jump support"""
        l2_periods = []
        duration_months = (l1_period.end_date - l1_period.start_date).days / 30.44  # avg month
        months_per_l2 = duration_months / 12
        
        current_sign_index = self.SIGN_ORDER.index(l1_period.sign)
        current_date = l1_period.start_date
        
        for i in range(12):
            sign = self.SIGN_ORDER[current_sign_index % 12]
            
            # Check for LB transition at L2 level
            next_sign_index = (current_sign_index + 1) % 12
            next_sign = self.SIGN_ORDER[next_sign_index]
            is_lb_period = self.is_lb_transition(sign, next_sign)
            
            ruler = self.sign_rulers[sign]
            
            end_date = current_date + timedelta(days=months_per_l2 * 30.44)
            if end_date > l1_period.end_date:
                end_date = l1_period.end_date
            
            period = ZRPeriod(
                level=2,
                sign=sign,
                ruler=ruler,
                start_date=current_date,
                end_date=end_date,
                tone=self.calculate_tone(ruler, {}),
                is_lb=is_lb_period
            )
            
            l2_periods.append(period)
            current_date = end_date
            
            # Apply LB jump for next iteration
            if is_lb_period:
                jumped_sign = self.apply_lb_jump(sign)
                current_sign_index = self.SIGN_ORDER.index(jumped_sign)
            else:
                current_sign_index = next_sign_index
            
            if current_date >= l1_period.end_date:
                break
        
        return l2_periods
    
    def compute_zr_timeline(self, sun_lon: float, moon_lon: float, asc_lon: float, 
                           is_day: bool, birth_date: date, lot_type: str = "Spirit") -> ZRTimeline:
        """Compute complete ZR timeline"""
        # Calculate lots
        spirit_lon = self.lot_of_spirit(sun_lon, moon_lon, asc_lon, is_day)
        fortune_lon = self.lot_of_fortune(sun_lon, moon_lon, asc_lon, is_day)
        
        # Choose lot for ZR
        if lot_type == "Spirit":
            lot_lon = spirit_lon
        elif lot_type == "Fortune":
            lot_lon = fortune_lon
        else:
            lot_lon = spirit_lon  # Default to Spirit
        
        lot_sign = self.longitude_to_sign(lot_lon)
        fortune_sign = self.longitude_to_sign(fortune_lon)
        
        # Build L1 periods
        l1_periods = self.build_l1_periods(lot_sign, birth_date)
        
        # Mark peaks based on Fortune angles
        for period in l1_periods:
            period.is_peak = self.is_peak_period(period.sign, fortune_sign)
        
        # Build L2 periods for first few L1 periods
        l2_periods = []
        for l1_period in l1_periods[:5]:  # First 5 L1 periods
            l2_periods.extend(self.subdivide_l2(l1_period))
        
        # Mark L2 peaks based on Fortune angles (10th from Fortune at L2)
        for period in l2_periods:
            period.is_peak = self.is_peak_period(period.sign, fortune_sign)
        
        # LB transitions are now handled during period building
        
        return ZRTimeline(
            l1_periods=l1_periods,
            l2_periods=l2_periods,
            lot_used=lot_type,
            diagnostics={
                "lot_longitude": lot_lon,
                "lot_sign": lot_sign,
                "fortune_sign": fortune_sign,
                "spirit_longitude": spirit_lon,
                "fortune_longitude": fortune_lon,
                "l1_count": len(l1_periods),
                "l2_count": len(l2_periods)
            }
        )