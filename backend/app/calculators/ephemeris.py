"""Swiss Ephemeris wrapper for astrological calculations."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytz
from dateutil import tz
from loguru import logger

try:  # pragma: no cover - import-time capability check
    import swisseph as swe  # type: ignore
    SWISSEPH_AVAILABLE = True
except Exception as exc:  # pragma: no cover - fallback path
    swe = None  # type: ignore
    SWISSEPH_AVAILABLE = False
    logger.warning(
        "Swiss Ephemeris unavailable; falling back to mock calculations",
        extra={"error": str(exc)},
    )

from backend.app.config import settings

if SWISSEPH_AVAILABLE:
    ephe_path = settings.SWISSEPH_DATA_PATH
    if ephe_path:
        try:
            swe.set_ephe_path(str(Path(ephe_path).expanduser()))
        except Exception as exc:  # pragma: no cover - environment specific
            logger.warning(
                "Failed to set Swiss Ephemeris data path",
                extra={"path": ephe_path, "error": str(exc)},
            )

@dataclass
class PlanetPosition:
    """Planet position data"""
    name: str
    longitude: float
    latitude: float
    distance: float
    speed_longitude: float
    speed_latitude: float
    speed_distance: float
    
    @property
    def sign(self) -> str:
        """Get zodiac sign"""
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        return signs[int(self.longitude // 30)]
    
    @property
    def degree_in_sign(self) -> float:
        """Get degree within sign (0-29.999...)"""
        return self.longitude % 30
    
    @property
    def is_retrograde(self) -> bool:
        """Check if planet is retrograde"""
        return self.speed_longitude < 0

@dataclass
class HouseSystem:
    """House system data"""
    cusps: List[float]  # 12 house cusps
    asc: float  # Ascendant
    mc: float   # Midheaven
    armc: float # ARMC
    vertex: float
    equatorial_asc: float
    co_asc_koch: float
    co_asc_munkasey: float
    polar_asc: float

class EphemerisService:
    """Swiss Ephemeris service for astrological calculations"""
    
    # Planet constants from Swiss Ephemeris (PySwisseph uses numeric values)
    if SWISSEPH_AVAILABLE:
        PLANETS = {
            'Sun': 0,        # SE_SUN
            'Moon': 1,       # SE_MOON
            'Mercury': 2,    # SE_MERCURY
            'Venus': 3,      # SE_VENUS
            'Mars': 4,       # SE_MARS
            'Jupiter': 5,    # SE_JUPITER
            'Saturn': 6,     # SE_SATURN
            'Uranus': 7,     # SE_URANUS
            'Neptune': 8,    # SE_NEPTUNE
            'Pluto': 9,      # SE_PLUTO
            'North Node': 10, # SE_MEAN_NODE
            'South Node': 10, # Will calculate opposite of North Node
            'Chiron': 15,    # SE_CHIRON
        }
        
        # House systems (PySwisseph uses strings)
        HOUSE_SYSTEMS = {
            'placidus': 'P',
            'koch': 'K',
            'porphyrius': 'O',
            'regiomontanus': 'R',
            'campanus': 'C',
            'equal': 'E',
            'whole_sign': 'W',
            'alcabitius': 'B',
            'morinus': 'M',
        }
    else:
        # Mock constants when Swiss Ephemeris is not available
        PLANETS = {
            'Sun': 0, 'Moon': 1, 'Mercury': 2, 'Venus': 3, 'Mars': 4,
            'Jupiter': 5, 'Saturn': 6, 'Uranus': 7, 'Neptune': 8, 
            'Pluto': 9, 'North Node': 10, 'South Node': 11, 'Chiron': 12
        }
        HOUSE_SYSTEMS = {
            'placidus': 'P', 'koch': 'K', 'whole_sign': 'W', 'equal': 'E'
        }
    
    def __init__(self, ephemeris_path: Optional[str] = None):
        """Initialize ephemeris service."""
        self._ephemeris_path = ephemeris_path or settings.SWISSEPH_DATA_PATH
        self._mock_used = not SWISSEPH_AVAILABLE
        if SWISSEPH_AVAILABLE:
            if self._ephemeris_path:
                try:
                    swe.set_ephe_path(str(Path(self._ephemeris_path).expanduser()))
                except Exception as exc:  # pragma: no cover - environment specific
                    logger.warning(
                        "Failed to configure Swiss Ephemeris path",
                        extra={"path": self._ephemeris_path, "error": str(exc)},
                    )
            self.flags = getattr(swe, "FLG_SWIEPH", 0) | getattr(swe, "FLG_SPEED", 0)
        else:
            self.flags = 0

    @property
    def status(self) -> str:
        """Return execution mode information for observability."""
        return "mock" if self._mock_used else "swisseph"

    def julian_day(self, dt: datetime) -> float:
        """Convert datetime to Julian Day"""
        # Convert to UTC if timezone aware
        if dt.tzinfo:
            dt = dt.astimezone(pytz.UTC).replace(tzinfo=None)

        if SWISSEPH_AVAILABLE:
            return swe.julday(dt.year, dt.month, dt.day,
                             dt.hour + dt.minute/60.0 + dt.second/3600.0)
        else:
            # Simple Julian Day calculation for mock mode
            import math
            a = math.floor(dt.year / 100.0)
            b = 2 - a + math.floor(a / 4.0)
            jd = math.floor(365.25 * (dt.year + 4716)) + math.floor(30.6001 * (dt.month + 1)) + dt.day + b - 1524.5
            return jd + (dt.hour + dt.minute/60.0 + dt.second/3600.0) / 24.0
    
    def get_planet_position(self, planet: str, jd: float) -> PlanetPosition:
        """Get planet position for given Julian Day"""
        if planet not in self.PLANETS:
            raise ValueError(f"Unknown planet: {planet}")
        
        planet_id = self.PLANETS[planet]
        
        if not SWISSEPH_AVAILABLE:
            # Use mock data when Swiss Ephemeris is not available
            self._mock_used = True
            return self._get_mock_planet_position(planet, jd)

        try:
            # Special handling for South Node
            if planet == 'South Node':
                result = swe.calc_ut(jd, swe.MEAN_NODE, self.flags)
                # South Node is opposite to North Node
                longitude = (result[0][0] + 180) % 360
                position_data = [longitude] + list(result[0][1:])
            else:
                result = swe.calc_ut(jd, planet_id, self.flags)
                position_data = result[0]
        except Exception as exc:
            # If Swiss Ephemeris fails, use mock calculation
            logger.warning(
                "Swiss Ephemeris planet calculation failed",
                extra={"planet": planet, "error": str(exc)},
            )
            self._mock_used = True
            return self._get_mock_planet_position(planet, jd)

        return PlanetPosition(
            name=planet,
            longitude=position_data[0],
            latitude=position_data[1],
            distance=position_data[2],
            speed_longitude=position_data[3],
            speed_latitude=position_data[4],
            speed_distance=position_data[5]
        )
    
    def get_all_planets(self, jd: float) -> Dict[str, PlanetPosition]:
        """Get all planet positions"""
        positions = {}
        for planet_name in self.PLANETS.keys():
            positions[planet_name] = self.get_planet_position(planet_name, jd)
        return positions
    
    def get_houses(self, jd: float, lat: float, lon: float, 
                   house_system: str = 'placidus') -> HouseSystem:
        """Calculate house cusps and angles"""
        if house_system not in self.HOUSE_SYSTEMS:
            raise ValueError(f"Unknown house system: {house_system}")
        
        if not SWISSEPH_AVAILABLE:
            self._mock_used = True
            return self._get_mock_houses(jd, lat, lon, house_system)
        
        hsys = self.HOUSE_SYSTEMS[house_system]
        
        try:
            # Calculate houses
            houses_result = swe.houses(jd, lat, lon, hsys)
            cusps = houses_result[0]  # 12 house cusps
            ascmc = houses_result[1]  # ASC, MC, ARMC, Vertex, etc.
            
            return HouseSystem(
                cusps=list(cusps[1:]),  # Skip index 0, use 1-12
                asc=ascmc[0],
                mc=ascmc[1],
                armc=ascmc[2],
                vertex=ascmc[3],
                equatorial_asc=ascmc[4],
                co_asc_koch=ascmc[5],
                co_asc_munkasey=ascmc[6],
                polar_asc=ascmc[7]
            )
        except Exception as exc:
            logger.warning(
                "Swiss Ephemeris house computation failed",
                extra={"error": str(exc)},
            )
            self._mock_used = True
            return self._get_mock_houses(jd, lat, lon, house_system)
    
    def get_whole_sign_houses(self, asc_longitude: float) -> List[float]:
        """Calculate Whole Sign house cusps from Ascendant"""
        # In Whole Sign, each house is exactly 30 degrees
        # House 1 starts at the beginning of the Ascendant's sign
        asc_sign_start = (int(asc_longitude // 30)) * 30
        
        cusps = []
        for i in range(12):
            cusp = (asc_sign_start + (i * 30)) % 360
            cusps.append(cusp)
        
        return cusps
    
    def calculate_lots(self, planets: Dict[str, PlanetPosition], 
                      houses: HouseSystem, is_day_birth: bool) -> Dict[str, float]:
        """Calculate Arabic Lots/Parts"""
        sun_lon = planets['Sun'].longitude
        moon_lon = planets['Moon'].longitude
        asc_lon = houses.asc
        
        lots = {}
        
        # Lot of Fortune
        if is_day_birth:
            # Day: ASC + Moon - Sun
            fortune = (asc_lon + moon_lon - sun_lon) % 360
        else:
            # Night: ASC + Sun - Moon
            fortune = (asc_lon + sun_lon - moon_lon) % 360
        lots['Fortune'] = fortune
        
        # Lot of Spirit
        if is_day_birth:
            # Day: ASC + Sun - Moon
            spirit = (asc_lon + sun_lon - moon_lon) % 360
        else:
            # Night: ASC + Moon - Sun
            spirit = (asc_lon + moon_lon - sun_lon) % 360
        lots['Spirit'] = spirit
        
        # Lot of Love/Eros (Venus + Mars - Spirit)
        if 'Venus' in planets and 'Mars' in planets:
            venus_lon = planets['Venus'].longitude
            mars_lon = planets['Mars'].longitude
            eros = (venus_lon + mars_lon - spirit) % 360
            lots['Eros'] = eros
        
        return lots
    
    def is_day_birth(self, planets: Dict[str, PlanetPosition], 
                     houses: HouseSystem) -> bool:
        """Determine if birth is during day or night"""
        sun_lon = planets['Sun'].longitude
        asc_lon = houses.asc
        desc_lon = (asc_lon + 180) % 360
        
        # Check if Sun is above horizon (between ASC and DESC)
        if asc_lon < desc_lon:
            return asc_lon <= sun_lon <= desc_lon
        else:
            return sun_lon >= asc_lon or sun_lon <= desc_lon
    
    def calculate_aspects(self, pos1: float, pos2: float, 
                         orb: float = 8.0) -> Optional[Dict[str, any]]:
        """Calculate aspect between two positions"""
        # Calculate the shortest arc between positions
        diff = abs(pos1 - pos2)
        if diff > 180:
            diff = 360 - diff
        
        # Major aspects and their exact degrees
        aspects = {
            'conjunction': 0,
            'sextile': 60,
            'square': 90,
            'trine': 120,
            'opposition': 180
        }
        
        for aspect_name, exact_degree in aspects.items():
            if abs(diff - exact_degree) <= orb:
                return {
                    'aspect': aspect_name,
                    'orb': abs(diff - exact_degree),
                    'exact_degree': exact_degree,
                    'applying': self._is_applying(pos1, pos2, exact_degree)
                }
        
        return None
    
    def _is_applying(self, pos1: float, pos2: float, exact_degree: float) -> bool:
        """Determine if aspect is applying or separating (simplified)"""
        # This is a simplified version - in reality, we need planet speeds
        # For now, return True (applying) as default
        return True
    
    def _get_mock_planet_position(self, planet: str, jd: float) -> PlanetPosition:
        """Get mock planet position when Swiss Ephemeris is not available"""
        # Mock positions based on planet ID and Julian Day
        planet_id = self.PLANETS[planet]
        
        # Simple mock calculation - in reality, you'd use astronomical formulas
        base_longitude = planet_id * 30  # Spread planets across zodiac
        daily_motion = {
            'Sun': 1.0, 'Moon': 13.2, 'Mercury': 1.4, 'Venus': 1.2, 'Mars': 0.5,
            'Jupiter': 0.08, 'Saturn': 0.03, 'Uranus': 0.01, 'Neptune': 0.006,
            'Pluto': 0.004, 'North Node': -0.05, 'South Node': -0.05, 'Chiron': 0.02
        }.get(planet, 1.0)
        
        # Calculate longitude based on time
        days_since_epoch = jd - 2451545.0  # J2000.0 epoch
        longitude = (base_longitude + daily_motion * days_since_epoch) % 360
        
        # Special handling for South Node
        if planet == 'South Node':
            north_node_lon = (self.PLANETS['North Node'] * 30 - 0.05 * days_since_epoch) % 360
            longitude = (north_node_lon + 180) % 360
        
        return PlanetPosition(
            name=planet,
            longitude=longitude,
            latitude=0.0,  # Simplified
            distance=1.0,  # AU
            speed_longitude=daily_motion,
            speed_latitude=0.0,
            speed_distance=0.0
        )
    
    def _get_mock_houses(self, jd: float, latitude: float, longitude: float, 
                        house_system: str = 'placidus') -> HouseSystem:
        """Get mock house system when Swiss Ephemeris is not available"""
        # Simple mock calculation - equal houses based on time
        days_since_epoch = jd - 2451545.0
        base_asc = (longitude + days_since_epoch) % 360  # Very simplified ASC calculation
        
        # Calculate house cusps (equal house system for simplicity)
        cusps = []
        for i in range(12):
            cusp = (base_asc + i * 30) % 360
            cusps.append(cusp)
        
        mc = (base_asc + 90) % 360  # Simplified MC
        
        return HouseSystem(
            cusps=cusps,
            asc=base_asc,
            mc=mc,
            armc=mc,
            vertex=(base_asc + 180) % 360,
            equatorial_asc=base_asc,
            co_asc_koch=base_asc,
            co_asc_munkasey=base_asc,
            polar_asc=base_asc
        )

    def _longitude_to_sign(self, longitude: float) -> str:
        """Convert longitude to zodiac sign"""
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        return signs[int(longitude // 30)]

    def close(self):
        """Close Swiss Ephemeris"""
        if SWISSEPH_AVAILABLE:
            swe.close()

# Global ephemeris service instance
ephemeris = EphemerisService()
