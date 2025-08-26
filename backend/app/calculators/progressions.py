"""
Secondary Progressions (Day-for-a-Year) calculator
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import date, timedelta
import math

@dataclass
class ProgressedPosition:
    """Progressed planet position"""
    planet: str
    progressed_longitude: float
    progressed_sign: str
    progressed_degree: float
    natal_longitude: float
    arc_of_direction: float
    is_retrograde: bool = False

@dataclass
class ProgressedAspect:
    """Progressed aspect to natal point"""
    progressed_planet: str
    natal_point: str
    aspect_type: str  # conjunction, opposition, square, trine, sextile
    orb: float
    exact_date: Optional[date] = None
    applying: bool = True

@dataclass
class SignIngress:
    """Progressed planet sign change"""
    planet: str
    from_sign: str
    to_sign: str
    ingress_date: date
    progressed_degree: float

@dataclass
class ProgressionsResult:
    """Complete progressions calculation result"""
    progressed_positions: List[ProgressedPosition]
    progressed_aspects: List[ProgressedAspect]
    sign_ingresses: List[SignIngress]
    progressed_angles: Dict[str, ProgressedPosition]
    diagnostics: Dict[str, Any]

class ProgressionsCalculator:
    """Secondary Progressions calculator using day-for-a-year method"""
    
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # Standard orbs for progressed aspects
    ASPECT_ORBS = {
        "conjunction": 1.0,
        "opposition": 1.0,
        "square": 1.0,
        "trine": 1.0,
        "sextile": 0.5
    }
    
    # Aspect angles
    ASPECTS = {
        0: "conjunction",
        60: "sextile", 
        90: "square",
        120: "trine",
        180: "opposition"
    }
    
    def __init__(self, orb_factor: float = 1.0):
        """
        Initialize progressions calculator
        
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
    
    def calculate_progressed_position(self, natal_longitude: float, birth_date: date, 
                                    target_date: date, daily_motion: float = 1.0) -> ProgressedPosition:
        """
        Calculate progressed position for a planet
        
        Args:
            natal_longitude: Natal position in degrees
            birth_date: Birth date
            target_date: Date for progression
            daily_motion: Average daily motion (degrees per day)
        """
        # Calculate days since birth
        days_elapsed = (target_date - birth_date).days
        
        # Day-for-a-year: each day = one year
        arc_of_direction = days_elapsed * daily_motion
        
        # Calculate progressed longitude
        progressed_longitude = (natal_longitude + arc_of_direction) % 360
        
        # Convert to sign and degree
        progressed_sign, progressed_degree = self.longitude_to_sign_degree(progressed_longitude)
        
        return ProgressedPosition(
            planet="",  # Will be set by caller
            progressed_longitude=progressed_longitude,
            progressed_sign=progressed_sign,
            progressed_degree=progressed_degree,
            natal_longitude=natal_longitude,
            arc_of_direction=arc_of_direction
        )
    
    def find_progressed_aspects(self, progressed_positions: List[ProgressedPosition],
                              natal_positions: Dict[str, float]) -> List[ProgressedAspect]:
        """Find progressed aspects to natal positions"""
        aspects = []
        
        for prog_pos in progressed_positions:
            for natal_planet, natal_lon in natal_positions.items():
                # Skip self-aspects
                if prog_pos.planet == natal_planet:
                    continue
                
                # Calculate angular separation
                separation = abs(prog_pos.progressed_longitude - natal_lon)
                if separation > 180:
                    separation = 360 - separation
                
                # Check for aspects
                for aspect_angle, aspect_name in self.ASPECTS.items():
                    orb = self.ASPECT_ORBS[aspect_name] * self.orb_factor
                    aspect_diff = abs(separation - aspect_angle)
                    
                    if aspect_diff <= orb:
                        aspect = ProgressedAspect(
                            progressed_planet=prog_pos.planet,
                            natal_point=natal_planet,
                            aspect_type=aspect_name,
                            orb=aspect_diff,
                            applying=True  # Simplified - would need motion calculation
                        )
                        aspects.append(aspect)
        
        return aspects
    
    def find_sign_ingresses(self, natal_positions: Dict[str, float], birth_date: date,
                          years_ahead: int = 10) -> List[SignIngress]:
        """Find upcoming sign ingresses for progressed planets"""
        ingresses = []
        
        # Standard daily motions (approximate)
        daily_motions = {
            "Sun": 0.9856,      # ~1 degree per day
            "Moon": 13.1764,    # ~13 degrees per day  
            "Mercury": 1.383,   # Variable, average
            "Venus": 1.602,     # Variable, average
            "Mars": 0.524,      # ~0.5 degrees per day
            "Jupiter": 0.083,   # Very slow
            "Saturn": 0.033,    # Very slow
        }
        
        for planet, natal_lon in natal_positions.items():
            if planet not in daily_motions:
                continue
                
            daily_motion = daily_motions[planet]
            current_sign_index = int(natal_lon // 30)
            current_sign = self.SIGNS[current_sign_index]
            
            # Calculate degrees to next sign boundary
            degrees_to_boundary = 30 - (natal_lon % 30)
            
            # Calculate days to reach boundary (day-for-a-year)
            days_to_ingress = degrees_to_boundary / daily_motion
            
            # Check if ingress occurs within timeframe
            if days_to_ingress <= years_ahead * 365.25:
                ingress_date = birth_date + timedelta(days=int(days_to_ingress))
                next_sign_index = (current_sign_index + 1) % 12
                next_sign = self.SIGNS[next_sign_index]
                
                ingress = SignIngress(
                    planet=planet,
                    from_sign=current_sign,
                    to_sign=next_sign,
                    ingress_date=ingress_date,
                    progressed_degree=0.0  # Ingress at 0 degrees
                )
                ingresses.append(ingress)
        
        return sorted(ingresses, key=lambda x: x.ingress_date)
    
    def calculate_progressions(self, natal_positions: Dict[str, float], 
                             birth_date: date, target_date: date = None) -> ProgressionsResult:
        """
        Calculate complete progressions for given date
        
        Args:
            natal_positions: Dictionary of planet names to natal longitudes
            birth_date: Birth date
            target_date: Date for progressions (default: today)
        """
        if target_date is None:
            target_date = date.today()
        
        # Standard daily motions
        daily_motions = {
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
        
        progressed_positions = []
        
        # Calculate progressed positions
        for planet, natal_lon in natal_positions.items():
            if planet in daily_motions:
                daily_motion = daily_motions[planet]
                prog_pos = self.calculate_progressed_position(
                    natal_lon, birth_date, target_date, daily_motion
                )
                prog_pos.planet = planet
                progressed_positions.append(prog_pos)
        
        # Find progressed aspects
        progressed_aspects = self.find_progressed_aspects(progressed_positions, natal_positions)
        
        # Find sign ingresses
        sign_ingresses = self.find_sign_ingresses(natal_positions, birth_date)
        
        # Calculate progressed angles (simplified - would need birth time/location)
        progressed_angles = {}
        if "ASC" in natal_positions:
            asc_prog = self.calculate_progressed_position(
                natal_positions["ASC"], birth_date, target_date, 0.9856  # Use solar rate
            )
            asc_prog.planet = "ASC"
            progressed_angles["ASC"] = asc_prog
        
        if "MC" in natal_positions:
            mc_prog = self.calculate_progressed_position(
                natal_positions["MC"], birth_date, target_date, 0.9856
            )
            mc_prog.planet = "MC"
            progressed_angles["MC"] = mc_prog
        
        return ProgressionsResult(
            progressed_positions=progressed_positions,
            progressed_aspects=progressed_aspects,
            sign_ingresses=sign_ingresses,
            progressed_angles=progressed_angles,
            diagnostics={
                "birth_date": birth_date.isoformat(),
                "target_date": target_date.isoformat(),
                "years_progressed": (target_date - birth_date).days / 365.25,
                "total_aspects": len(progressed_aspects),
                "upcoming_ingresses": len(sign_ingresses),
                "orb_factor": self.orb_factor
            }
        )
    
    def get_current_progressions(self, natal_positions: Dict[str, float], 
                               birth_date: date) -> Dict[str, Any]:
        """Get current progressions with formatted output"""
        result = self.calculate_progressions(natal_positions, birth_date)
        
        return {
            "progressed_positions": [
                {
                    "planet": pos.planet,
                    "natal_position": f"{self.longitude_to_sign_degree(pos.natal_longitude)[0]} {pos.natal_longitude % 30:.1f}°",
                    "progressed_position": f"{pos.progressed_sign} {pos.progressed_degree:.1f}°",
                    "arc_of_direction": f"{pos.arc_of_direction:.1f}°"
                }
                for pos in result.progressed_positions
            ],
            "major_aspects": [
                {
                    "progressed_planet": asp.progressed_planet,
                    "natal_point": asp.natal_point,
                    "aspect": asp.aspect_type,
                    "orb": f"{asp.orb:.2f}°",
                    "applying": asp.applying
                }
                for asp in result.progressed_aspects
                if asp.orb <= 0.5  # Only tight aspects
            ],
            "upcoming_ingresses": [
                {
                    "planet": ing.planet,
                    "transition": f"{ing.from_sign} → {ing.to_sign}",
                    "date": ing.ingress_date.isoformat(),
                    "years_from_now": (ing.ingress_date - date.today()).days / 365.25
                }
                for ing in result.sign_ingresses[:5]  # Next 5 ingresses
            ],
            "diagnostics": result.diagnostics
        }
    
    def compute(self, chart_data: Dict[str, Any], when: Optional[date] = None) -> Dict[str, Any]:
        """
        Standard compute interface for progressions
        
        Args:
            chart_data: Chart data including natal positions and birth date
            when: Target date for progressions
        """
        natal_positions = chart_data.get("planets", {})
        birth_date = chart_data.get("birth_date")
        
        if isinstance(birth_date, str):
            birth_date = date.fromisoformat(birth_date)
        
        result = self.calculate_progressions(natal_positions, birth_date, when)
        
        # Format for interpretation system
        features = []
        evidence = []
        
        # Add major progressed aspects as evidence
        for aspect in result.progressed_aspects:
            if aspect.orb <= 0.5:  # Tight orbs only
                evidence.append({
                    "type": "PROGRESSION",
                    "description": f"Progressed {aspect.progressed_planet} {aspect.aspect_type} natal {aspect.natal_point}",
                    "orb": aspect.orb,
                    "strength": "strong" if aspect.orb <= 0.25 else "moderate",
                    "timing": "current"
                })
        
        # Add upcoming sign changes as features
        for ingress in result.sign_ingresses[:3]:
            features.append({
                "type": "sign_change",
                "planet": ingress.planet,
                "transition": f"{ingress.from_sign} to {ingress.to_sign}",
                "date": ingress.ingress_date.isoformat(),
                "significance": "major" if ingress.planet in ["Sun", "Moon"] else "moderate"
            })
        
        return {
            "features": features,
            "evidence": evidence,
            "diagnostics": result.diagnostics
        }