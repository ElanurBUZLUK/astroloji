"""
Solar Arc Directions calculator
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import date, timedelta
import math

@dataclass
class ArcDirectedPosition:
    """Solar arc directed planet position"""
    planet: str
    natal_longitude: float
    directed_longitude: float
    directed_sign: str
    directed_degree: float
    arc_of_direction: float
    is_retrograde: bool = False

@dataclass
class SolarArcAspect:
    """Solar arc aspect to natal point"""
    directed_planet: str
    natal_point: str
    aspect_type: str  # conjunction, opposition, square, trine, sextile
    orb: float
    exact_date: Optional[date] = None
    applying: bool = True

@dataclass
class SolarArcResult:
    """Complete solar arc calculation result"""
    directed_positions: List[ArcDirectedPosition]
    solar_arc_aspects: List[SolarArcAspect]
    major_directions: List[SolarArcAspect]
    diagnostics: Dict[str, Any]

class SolarArcCalculator:
    """Solar Arc Directions calculator"""

    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    # Standard orbs for solar arc aspects
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
        Initialize solar arc calculator

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

    def calculate_solar_arc_position(self, natal_longitude: float,
                                   natal_sun_longitude: float,
                                   target_sun_longitude: float) -> ArcDirectedPosition:
        """
        Calculate solar arc directed position

        Args:
            natal_longitude: Natal planet longitude
            natal_sun_longitude: Natal Sun longitude
            target_sun_longitude: Target Sun longitude (current or future)
        """
        # Calculate arc of direction (Sun's movement)
        arc_of_direction = abs(target_sun_longitude - natal_sun_longitude)

        # Apply the arc to the planet (in the same direction as Sun)
        directed_longitude = (natal_longitude + arc_of_direction) % 360

        # Convert to sign and degree
        directed_sign, directed_degree = self.longitude_to_sign_degree(directed_longitude)

        return ArcDirectedPosition(
            planet="",  # Will be set by caller
            natal_longitude=natal_longitude,
            directed_longitude=directed_longitude,
            directed_sign=directed_sign,
            directed_degree=directed_degree,
            arc_of_direction=arc_of_direction
        )

    def find_solar_arc_aspects(self, directed_positions: List[ArcDirectedPosition],
                             natal_positions: Dict[str, float]) -> List[SolarArcAspect]:
        """Find solar arc aspects to natal positions"""
        aspects = []

        for directed_pos in directed_positions:
            for natal_point, natal_lon in natal_positions.items():
                # Skip self-aspects
                if directed_pos.planet == natal_point:
                    continue

                # Calculate angular separation
                separation = abs(directed_pos.directed_longitude - natal_lon)
                if separation > 180:
                    separation = 360 - separation

                # Check for aspects
                for aspect_angle, aspect_name in self.ASPECTS.items():
                    orb = self.ASPECT_ORBS[aspect_name] * self.orb_factor
                    aspect_diff = abs(separation - aspect_angle)

                    if aspect_diff <= orb:
                        aspect = SolarArcAspect(
                            directed_planet=directed_pos.planet,
                            natal_point=natal_point,
                            aspect_type=aspect_name,
                            orb=aspect_diff,
                            applying=True  # Simplified - would need motion calculation
                        )
                        aspects.append(aspect)

        return aspects

    def calculate_solar_arc_directions(self, natal_positions: Dict[str, float],
                                     birth_date: date, target_date: date = None) -> SolarArcResult:
        """
        Calculate complete solar arc directions

        Args:
            natal_positions: Dictionary of planet names to natal longitudes
            birth_date: Birth date
            target_date: Date for solar arc directions (default: today)
        """
        if target_date is None:
            target_date = date.today()

        # Get natal Sun position
        if "Sun" not in natal_positions:
            raise ValueError("Natal Sun position required for solar arc calculations")

        natal_sun_longitude = natal_positions["Sun"]

        # Calculate current Sun position (simplified - would use ephemeris)
        # For demonstration, we'll calculate approximate position
        days_since_birth = (target_date - birth_date).days
        # Sun moves approximately 0.9856 degrees per day
        target_sun_longitude = (natal_sun_longitude + days_since_birth * 0.9856) % 360

        directed_positions = []

        # Calculate solar arc directed positions for all planets
        for planet, natal_lon in natal_positions.items():
            if planet != "Sun":  # Sun is the directing planet
                directed_pos = self.calculate_solar_arc_position(
                    natal_lon, natal_sun_longitude, target_sun_longitude
                )
                directed_pos.planet = planet
                directed_positions.append(directed_pos)

        # Find solar arc aspects
        solar_arc_aspects = self.find_solar_arc_aspects(directed_positions, natal_positions)

        # Filter for major aspects (tight orbs and important planets)
        major_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        major_directions = [
            aspect for aspect in solar_arc_aspects
            if aspect.directed_planet in major_planets and aspect.orb <= 1.0
        ]

        return SolarArcResult(
            directed_positions=directed_positions,
            solar_arc_aspects=solar_arc_aspects,
            major_directions=major_directions,
            diagnostics={
                "birth_date": birth_date.isoformat(),
                "target_date": target_date.isoformat(),
                "natal_sun_longitude": natal_sun_longitude,
                "target_sun_longitude": target_sun_longitude,
                "arc_of_direction": (target_sun_longitude - natal_sun_longitude) % 360,
                "years_progressed": days_since_birth / 365.25,
                "total_aspects": len(solar_arc_aspects),
                "major_directions": len(major_directions),
                "orb_factor": self.orb_factor
            }
        )

    def get_current_solar_arc_directions(self, natal_positions: Dict[str, float],
                                       birth_date: date) -> Dict[str, Any]:
        """Get current solar arc directions with formatted output"""
        result = self.calculate_solar_arc_directions(natal_positions, birth_date)

        return {
            "directed_positions": [
                {
                    "planet": pos.planet,
                    "natal_position": f"{self.longitude_to_sign_degree(pos.natal_longitude)[0]} {pos.natal_longitude % 30:.1f}°",
                    "directed_position": f"{pos.directed_sign} {pos.directed_degree:.1f}°",
                    "arc_of_direction": f"{pos.arc_of_direction:.1f}°"
                }
                for pos in result.directed_positions
            ],
            "major_directions": [
                {
                    "directed_planet": asp.directed_planet,
                    "natal_point": asp.natal_point,
                    "aspect": asp.aspect_type,
                    "orb": f"{asp.orb:.2f}°",
                    "strength": "very_strong" if asp.orb <= 0.3 else "strong" if asp.orb <= 0.6 else "moderate"
                }
                for asp in result.major_directions
            ],
            "all_aspects": [
                {
                    "directed_planet": asp.directed_planet,
                    "natal_point": asp.natal_point,
                    "aspect": asp.aspect_type,
                    "orb": f"{asp.orb:.2f}°"
                }
                for asp in result.solar_arc_aspects
                if asp.orb <= 2.0  # Within reasonable orb
            ],
            "diagnostics": result.diagnostics
        }

    def calculate_exact_date(self, natal_positions: Dict[str, float], birth_date: date,
                           directed_planet: str, natal_point: str, aspect_type: str) -> Optional[date]:
        """
        Calculate exact date when solar arc aspect becomes exact

        Args:
            natal_positions: Natal planet positions
            birth_date: Birth date
            directed_planet: Planet being directed
            natal_point: Natal point being aspected
            aspect_type: Type of aspect
        """
        if aspect_type not in self.ASPECTS.values():
            return None

        # Get aspect angle
        aspect_angle = None
        for angle, name in self.ASPECTS.items():
            if name == aspect_type:
                aspect_angle = angle
                break

        if aspect_angle is None:
            return None

        # Get positions
        directed_natal = natal_positions.get(directed_planet)
        natal_target = natal_positions.get(natal_point)

        if directed_natal is None or natal_target is None:
            return None

        # Calculate required arc
        current_separation = abs(directed_natal - natal_target)
        if current_separation > 180:
            current_separation = 360 - current_separation

        required_arc = (aspect_angle - current_separation) % 360

        # Calculate days needed (Sun moves ~0.9856 degrees per day)
        days_needed = required_arc / 0.9856

        # Return future date
        return birth_date + timedelta(days=int(days_needed))

    def compute(self, chart_data: Dict[str, Any], when: Optional[date] = None) -> Dict[str, Any]:
        """
        Standard compute interface for solar arc directions

        Args:
            chart_data: Chart data including natal positions and birth date
            when: Target date for solar arc directions
        """
        natal_positions = chart_data.get("planets", {})
        birth_date = chart_data.get("birth_date")

        if isinstance(birth_date, str):
            birth_date = date.fromisoformat(birth_date)

        if when is None:
            when = date.today()

        result = self.calculate_solar_arc_directions(natal_positions, birth_date, when)

        # Format for interpretation system
        features = []
        evidence = []

        # Add major solar arc directions as evidence
        for aspect in result.major_directions:
            if aspect.orb <= 1.0:  # Tight aspects only
                strength = "very_strong" if aspect.orb <= 0.3 else "strong" if aspect.orb <= 0.6 else "moderate"

                evidence.append({
                    "type": "SOLAR_ARC",
                    "description": f"Solar arc {aspect.directed_planet} {aspect.aspect_type} natal {aspect.natal_point}",
                    "orb": aspect.orb,
                    "strength": strength,
                    "timing": "current",
                    "directed_planet": aspect.directed_planet,
                    "aspect_type": aspect.aspect_type
                })

        # Add significant solar arc configurations as features
        sun_directions = [asp for asp in result.major_directions if asp.directed_planet == "Sun"]
        if sun_directions:
            features.append({
                "type": "solar_arc_sun_directions",
                "count": len(sun_directions),
                "directions": [f"{asp.aspect_type} {asp.natal_point}" for asp in sun_directions[:3]],
                "significance": "major"
            })

        return {
            "features": features,
            "evidence": evidence,
            "diagnostics": result.diagnostics
        }


