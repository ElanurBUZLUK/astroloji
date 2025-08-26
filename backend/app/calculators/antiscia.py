"""
Antiscia and Contra-Antiscia calculator
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math

@dataclass
class AntisciaPoint:
    """Antiscia or Contra-antiscia point"""
    original_planet: str
    original_longitude: float
    antiscia_longitude: float
    antiscia_sign: str
    antiscia_degree: float
    type: str  # "antiscia" or "contra_antiscia"
    orb_used: float = 1.0

@dataclass
class AntisciaContact:
    """Contact between antiscia and another point"""
    antiscia_point: AntisciaPoint
    contacted_planet: str
    contacted_longitude: float
    orb: float
    contact_type: str  # "conjunction", "opposition"

@dataclass
class AntisciaResult:
    """Complete antiscia calculation result"""
    antiscia_points: List[AntisciaPoint]
    contra_antiscia_points: List[AntisciaPoint]
    contacts: List[AntisciaContact]
    diagnostics: Dict[str, any]

class AntisciaCalculator:
    """Antiscia and Contra-Antiscia calculator"""
    
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    def __init__(self, orb: float = 1.0):
        """
        Initialize antiscia calculator
        
        Args:
            orb: Maximum orb for antiscia contacts (default 1.0 degrees)
        """
        self.orb = orb
    
    def longitude_to_sign_degree(self, longitude: float) -> Tuple[str, float]:
        """Convert longitude to sign and degree within sign"""
        sign_index = int(longitude // 30)
        degree = longitude % 30
        return self.SIGNS[sign_index], degree
    
    def calculate_antiscia(self, longitude: float) -> float:
        """
        Calculate antiscia (solstitial mirror)
        Antiscia reflects around the Cancer-Capricorn axis (0° Cancer = 90°, 0° Capricorn = 270°)
        Formula: Antiscia = 180° - longitude (for 0-180°) or 540° - longitude (for 180-360°)
        """
        # Solstitial antiscia: mirror around 0° Cancer/Capricorn axis
        # 0° Aries -> 0° Cancer (90°)
        # 30° Aries -> 30° Gemini (60°)
        # 0° Taurus -> 0° Gemini (60°)
        # etc.
        
        if 0 <= longitude < 90:  # Aries to early Cancer
            antiscia = 90 - longitude
        elif 90 <= longitude < 180:  # Late Cancer to Virgo
            antiscia = 90 + (180 - longitude)
        elif 180 <= longitude < 270:  # Libra to early Capricorn
            antiscia = 270 - longitude
        else:  # Late Capricorn to Pisces (270-360)
            antiscia = 270 + (360 - longitude)
        
        return antiscia % 360
    
    def calculate_contra_antiscia(self, longitude: float) -> float:
        """
        Calculate contra-antiscia (equinoctial mirror)
        Contra-antiscia reflects around the Aries-Libra axis (0° Aries = 0°, 0° Libra = 180°)
        """
        # Equinoctial contra-antiscia: mirror around 0° Aries/Libra axis
        # 0° Aries -> 0° Libra (180°)
        # 30° Aries -> 30° Virgo (150°)
        # 0° Taurus -> 0° Virgo (150°)
        # etc.
        
        if 0 <= longitude < 90:  # Aries to early Cancer
            contra = 180 - longitude
        elif 90 <= longitude < 180:  # Late Cancer to Virgo
            contra = 180 - longitude
        elif 180 <= longitude < 270:  # Libra to early Capricorn
            contra = 180 + (270 - longitude)
        else:  # Late Capricorn to Pisces (270-360)
            contra = 180 - (360 - longitude)
        
        return contra % 360
    
    def calculate_all_antiscia(self, planet_positions: Dict[str, float]) -> AntisciaResult:
        """
        Calculate all antiscia and contra-antiscia points for given planets
        
        Args:
            planet_positions: Dictionary of planet names to longitudes
        """
        antiscia_points = []
        contra_antiscia_points = []
        
        # Calculate antiscia and contra-antiscia for each planet
        for planet, longitude in planet_positions.items():
            # Antiscia
            antiscia_lon = self.calculate_antiscia(longitude)
            antiscia_sign, antiscia_deg = self.longitude_to_sign_degree(antiscia_lon)
            
            antiscia_point = AntisciaPoint(
                original_planet=planet,
                original_longitude=longitude,
                antiscia_longitude=antiscia_lon,
                antiscia_sign=antiscia_sign,
                antiscia_degree=antiscia_deg,
                type="antiscia",
                orb_used=self.orb
            )
            antiscia_points.append(antiscia_point)
            
            # Contra-antiscia
            contra_lon = self.calculate_contra_antiscia(longitude)
            contra_sign, contra_deg = self.longitude_to_sign_degree(contra_lon)
            
            contra_point = AntisciaPoint(
                original_planet=planet,
                original_longitude=longitude,
                antiscia_longitude=contra_lon,
                antiscia_sign=contra_sign,
                antiscia_degree=contra_deg,
                type="contra_antiscia",
                orb_used=self.orb
            )
            contra_antiscia_points.append(contra_point)
        
        # Find contacts between antiscia/contra-antiscia and planets
        contacts = self._find_antiscia_contacts(
            antiscia_points + contra_antiscia_points, 
            planet_positions
        )
        
        return AntisciaResult(
            antiscia_points=antiscia_points,
            contra_antiscia_points=contra_antiscia_points,
            contacts=contacts,
            diagnostics={
                "orb_used": self.orb,
                "total_antiscia": len(antiscia_points),
                "total_contra_antiscia": len(contra_antiscia_points),
                "total_contacts": len(contacts)
            }
        )
    
    def _find_antiscia_contacts(self, antiscia_points: List[AntisciaPoint], 
                              planet_positions: Dict[str, float]) -> List[AntisciaContact]:
        """Find contacts between antiscia points and planets"""
        contacts = []
        
        for antiscia_point in antiscia_points:
            for planet, planet_lon in planet_positions.items():
                # Skip self-contact
                if planet == antiscia_point.original_planet:
                    continue
                
                # Calculate orb
                orb = self._calculate_orb(antiscia_point.antiscia_longitude, planet_lon)
                
                if orb <= self.orb:
                    # Determine contact type (conjunction is primary for antiscia)
                    contact_type = "conjunction"
                    
                    contact = AntisciaContact(
                        antiscia_point=antiscia_point,
                        contacted_planet=planet,
                        contacted_longitude=planet_lon,
                        orb=orb,
                        contact_type=contact_type
                    )
                    contacts.append(contact)
        
        return contacts
    
    def _calculate_orb(self, pos1: float, pos2: float) -> float:
        """Calculate the shortest orb between two positions"""
        diff = abs(pos1 - pos2)
        return min(diff, 360 - diff)
    
    def get_antiscia_summary(self, planet_positions: Dict[str, float]) -> Dict[str, any]:
        """Get a summary of antiscia calculations"""
        result = self.calculate_all_antiscia(planet_positions)
        
        # Group contacts by original planet
        contacts_by_planet = {}
        for contact in result.contacts:
            original = contact.antiscia_point.original_planet
            if original not in contacts_by_planet:
                contacts_by_planet[original] = []
            contacts_by_planet[original].append({
                "contacted_planet": contact.contacted_planet,
                "antiscia_type": contact.antiscia_point.type,
                "orb": round(contact.orb, 2),
                "antiscia_position": f"{contact.antiscia_point.antiscia_sign} {contact.antiscia_point.antiscia_degree:.1f}°"
            })
        
        return {
            "antiscia_positions": [
                {
                    "planet": ap.original_planet,
                    "original_position": f"{self.longitude_to_sign_degree(ap.original_longitude)[0]} {ap.original_longitude % 30:.1f}°",
                    "antiscia_position": f"{ap.antiscia_sign} {ap.antiscia_degree:.1f}°",
                    "type": ap.type
                }
                for ap in result.antiscia_points + result.contra_antiscia_points
            ],
            "contacts": contacts_by_planet,
            "summary": {
                "total_contacts": len(result.contacts),
                "planets_with_contacts": len(contacts_by_planet),
                "orb_used": self.orb
            },
            "diagnostics": result.diagnostics
        }
    
    def get_strongest_antiscia_contacts(self, planet_positions: Dict[str, float], 
                                      limit: int = 5) -> List[Dict[str, any]]:
        """Get the strongest antiscia contacts sorted by orb"""
        result = self.calculate_all_antiscia(planet_positions)
        
        # Sort contacts by orb (tightest first)
        sorted_contacts = sorted(result.contacts, key=lambda c: c.orb)
        
        strongest = []
        for contact in sorted_contacts[:limit]:
            strongest.append({
                "original_planet": contact.antiscia_point.original_planet,
                "contacted_planet": contact.contacted_planet,
                "antiscia_type": contact.antiscia_point.type,
                "orb": round(contact.orb, 2),
                "antiscia_position": f"{contact.antiscia_point.antiscia_sign} {contact.antiscia_point.antiscia_degree:.1f}°",
                "strength": "Very Strong" if contact.orb < 0.5 else "Strong" if contact.orb < 1.0 else "Moderate"
            })
        
        return strongest