"""
Transits calculator
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class Transit:
    """Transit aspect information"""
    transiting_planet: str
    natal_point: str
    aspect_type: str
    orb: float
    exact_date: Optional[date] = None
    applying: bool = True
    separating: bool = False

@dataclass
class TransitPeriod:
    """Transit period information"""
    transiting_planet: str
    natal_house: int
    sign: str
    entry_date: date
    exit_date: Optional[date] = None
    duration_days: Optional[int] = None

@dataclass
class TransitsResult:
    """Complete transits calculation result"""
    current_transits: List[Transit]
    upcoming_transits: List[Transit]
    transit_periods: List[TransitPeriod]
    diagnostics: Dict[str, Any]

class TransitsCalculator:
    """Transits calculator"""
    
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # Standard orbs for transits
    ASPECT_ORBS = {
        "conjunction": 2.0,
        "opposition": 2.0,
        "square": 2.0,
        "trine": 2.0,
        "sextile": 1.5
    }
    
    # Aspect angles
    ASPECTS = {
        0: "conjunction",
        60: "sextile",
        90: "square",
        120: "trine",
        180: "opposition"
    }
    
    # Average daily motions (degrees per day)
    DAILY_MOTIONS = {
        "Sun": 0.9856,
        "Moon": 13.1764,
        "Mercury": 1.383,
        "Venus": 1.602,
        "Mars": 0.524,
        "Jupiter": 0.083,
        "Saturn": 0.033,
        "Uranus": 0.042,
        "Neptune": 0.006,
        "Pluto": 0.004
    }
    
    def __init__(self, orb_factor: float = 1.0):
        """
        Initialize transits calculator
        
        Args:
            orb_factor: Multiplier for standard orbs (default 1.0)
        """
        self.orb_factor = orb_factor
    
    def longitude_to_sign_degree(self, longitude: float) -> Tuple[str, float]:
        """Convert longitude to sign and degree within sign"""
        longitude = longitude % 360
        sign_index = int(longitude // 30)
        degree = longitude % 30
        return self.SIGNS[sign_index], degree
    
    def calculate_orb(self, pos1: float, pos2: float) -> float:
        """Calculate the shortest orb between two positions"""
        diff = abs(pos1 - pos2)
        return min(diff, 360 - diff)
    
    def find_current_transits(self, current_positions: Dict[str, float],
                            natal_positions: Dict[str, float]) -> List[Transit]:
        """Find current transit aspects"""
        transits = []
        
        for transiting_planet, transit_lon in current_positions.items():
            for natal_point, natal_lon in natal_positions.items():
                # Skip self-transits
                if transiting_planet == natal_point:
                    continue
                
                # Calculate angular separation
                separation = self.calculate_orb(transit_lon, natal_lon)
                
                # Check for aspects
                for aspect_angle, aspect_name in self.ASPECTS.items():
                    orb = self.ASPECT_ORBS[aspect_name] * self.orb_factor
                    aspect_diff = abs(separation - aspect_angle)
                    
                    if aspect_diff <= orb:
                        transit = Transit(
                            transiting_planet=transiting_planet,
                            natal_point=natal_point,
                            aspect_type=aspect_name,
                            orb=aspect_diff,
                            applying=True  # Simplified - would need motion calculation
                        )
                        transits.append(transit)
        
        return sorted(transits, key=lambda x: x.orb)
    
    def find_upcoming_transits(self, current_positions: Dict[str, float],
                             natal_positions: Dict[str, float],
                             days_ahead: int = 30) -> List[Transit]:
        """Find upcoming transit aspects within specified timeframe"""
        upcoming = []
        
        for day in range(1, days_ahead + 1):
            future_positions = {}
            
            # Calculate future positions
            for planet, current_lon in current_positions.items():
                if planet in self.DAILY_MOTIONS:
                    daily_motion = self.DAILY_MOTIONS[planet]
                    future_lon = (current_lon + daily_motion * day) % 360
                    future_positions[planet] = future_lon
            
            # Find transits for this day
            day_transits = self.find_current_transits(future_positions, natal_positions)
            
            # Add exact date and filter for tight orbs
            target_date = date.today() + timedelta(days=day)
            for transit in day_transits:
                if transit.orb <= 0.5:  # Only very tight upcoming transits
                    transit.exact_date = target_date
                    upcoming.append(transit)
        
        return sorted(upcoming, key=lambda x: (x.exact_date, x.orb))
    
    def calculate_house_from_longitude(self, longitude: float, asc_longitude: float) -> int:
        """Calculate house number from longitude (simplified whole sign houses)"""
        asc_sign_index = int(asc_longitude // 30)
        planet_sign_index = int(longitude // 30)
        
        # Calculate house using whole sign system
        house = ((planet_sign_index - asc_sign_index) % 12) + 1
        return house
    
    def find_transit_periods(self, current_positions: Dict[str, float],
                           natal_positions: Dict[str, float]) -> List[TransitPeriod]:
        """Find current transit periods (planets in houses)"""
        periods = []
        
        # Need ASC to calculate houses
        asc_longitude = natal_positions.get("ASC", 0.0)
        
        for planet, transit_lon in current_positions.items():
            if planet in ["ASC", "MC"]:  # Skip angles
                continue
            
            house = self.calculate_house_from_longitude(transit_lon, asc_longitude)
            sign, degree = self.longitude_to_sign_degree(transit_lon)
            
            period = TransitPeriod(
                transiting_planet=planet,
                natal_house=house,
                sign=sign,
                entry_date=date.today(),  # Simplified - would need precise calculation
                duration_days=None  # Would need to calculate based on planet speed
            )
            periods.append(period)
        
        return periods
    
    def calculate_transits(self, current_positions: Dict[str, float],
                         natal_positions: Dict[str, float],
                         days_ahead: int = 30) -> TransitsResult:
        """
        Calculate complete transits analysis
        
        Args:
            current_positions: Current planet positions
            natal_positions: Natal planet positions
            days_ahead: Days to look ahead for upcoming transits
        """
        # Find current transits
        current_transits = self.find_current_transits(current_positions, natal_positions)
        
        # Find upcoming transits
        upcoming_transits = self.find_upcoming_transits(current_positions, natal_positions, days_ahead)
        
        # Find transit periods
        transit_periods = self.find_transit_periods(current_positions, natal_positions)
        
        return TransitsResult(
            current_transits=current_transits,
            upcoming_transits=upcoming_transits,
            transit_periods=transit_periods,
            diagnostics={
                "calculation_date": date.today().isoformat(),
                "days_ahead": days_ahead,
                "current_transits_count": len(current_transits),
                "upcoming_transits_count": len(upcoming_transits),
                "orb_factor": self.orb_factor
            }
        )
    
    def get_major_transits(self, current_positions: Dict[str, float],
                         natal_positions: Dict[str, float]) -> Dict[str, Any]:
        """Get major transits with formatted output"""
        result = self.calculate_transits(current_positions, natal_positions)
        
        # Filter for major transits (outer planets and tight orbs)
        major_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        major_current = [
            t for t in result.current_transits 
            if t.transiting_planet in major_planets and t.orb <= 2.0
        ]
        
        major_upcoming = [
            t for t in result.upcoming_transits
            if t.transiting_planet in major_planets
        ]
        
        return {
            "major_current_transits": [
                {
                    "transiting_planet": t.transiting_planet,
                    "natal_point": t.natal_point,
                    "aspect": t.aspect_type,
                    "orb": f"{t.orb:.2f}°",
                    "strength": "very_strong" if t.orb <= 0.5 else "strong" if t.orb <= 1.0 else "moderate"
                }
                for t in major_current[:10]
            ],
            "major_upcoming_transits": [
                {
                    "transiting_planet": t.transiting_planet,
                    "natal_point": t.natal_point,
                    "aspect": t.aspect_type,
                    "exact_date": t.exact_date.isoformat() if t.exact_date else None,
                    "orb": f"{t.orb:.2f}°"
                }
                for t in major_upcoming[:5]
            ],
            "transit_periods": [
                {
                    "planet": p.transiting_planet,
                    "house": p.natal_house,
                    "sign": p.sign
                }
                for p in result.transit_periods
                if p.transiting_planet in major_planets
            ],
            "diagnostics": result.diagnostics
        }
    
    def compute(self, chart_data: Dict[str, Any], when: Optional[date] = None) -> Dict[str, Any]:
        """
        Standard compute interface for transits
        
        Args:
            chart_data: Chart data including natal and current positions
            when: Date for transit calculation (default: today)
        """
        natal_positions = chart_data.get("natal_planets", {})
        current_positions = chart_data.get("current_planets", {})
        
        # If no current positions provided, use simplified current positions
        if not current_positions:
            # This would normally come from ephemeris calculation
            current_positions = natal_positions  # Placeholder
        
        result = self.calculate_transits(current_positions, natal_positions)
        
        # Format for interpretation system
        features = []
        evidence = []
        
        # Add major transits as evidence
        major_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        for transit in result.current_transits:
            if transit.transiting_planet in major_planets and transit.orb <= 2.0:
                strength = "very_strong" if transit.orb <= 0.5 else "strong" if transit.orb <= 1.0 else "moderate"
                
                evidence.append({
                    "type": "TRANSIT",
                    "description": f"{transit.transiting_planet} {transit.aspect_type} natal {transit.natal_point}",
                    "orb": transit.orb,
                    "strength": strength,
                    "timing": "current",
                    "transiting_planet": transit.transiting_planet
                })
        
        # Add transit periods as features
        for period in result.transit_periods:
            if period.transiting_planet in major_planets:
                features.append({
                    "type": "transit_period",
                    "planet": period.transiting_planet,
                    "house": period.natal_house,
                    "sign": period.sign,
                    "significance": "major" if period.transiting_planet in ["Saturn", "Uranus", "Neptune", "Pluto"] else "moderate"
                })
        
        return {
            "features": features,
            "evidence": evidence,
            "diagnostics": result.diagnostics
        }