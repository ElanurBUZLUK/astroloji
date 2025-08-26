"""
Midpoints calculator
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import date

@dataclass
class Midpoint:
    """Midpoint information"""
    planet1: str
    planet2: str
    midpoint_longitude: float
    midpoint_sign: str
    midpoint_degree: float

@dataclass
class MidpointContact:
    """Contact to a midpoint"""
    midpoint: Midpoint
    contacted_planet: str
    contact_type: str  # "conjunction", "opposition", "square"
    orb: float

@dataclass
class MidpointsResult:
    """Complete midpoints calculation result"""
    midpoints: List[Midpoint]
    contacts: List[MidpointContact]
    major_contacts: List[MidpointContact]
    diagnostics: Dict[str, Any]

class MidpointsCalculator:
    """Midpoints calculator"""
    
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # Standard orbs for midpoint contacts
    CONTACT_ORBS = {
        "conjunction": 2.0,
        "opposition": 2.0,
        "square": 1.5
    }
    
    # Major midpoint combinations (most significant)
    MAJOR_MIDPOINTS = [
        ("Sun", "Moon"),      # SO/MO - Core identity
        ("Sun", "ASC"),       # SO/ASC - Self-expression
        ("Sun", "MC"),        # SO/MC - Life direction
        ("Moon", "ASC"),      # MO/ASC - Emotional expression
        ("Moon", "MC"),       # MO/MC - Public image
        ("ASC", "MC"),        # ASC/MC - Life axis
        ("Venus", "Mars"),    # VE/MA - Relationships/sexuality
        ("Sun", "Venus"),     # SO/VE - Love nature
        ("Sun", "Mars"),      # SO/MA - Drive/energy
        ("Moon", "Venus"),    # MO/VE - Emotional needs
        ("Moon", "Mars"),     # MO/MA - Emotional reactions
        ("Mercury", "Venus"), # ME/VE - Communication in love
        ("Mercury", "Mars"),  # ME/MA - Mental energy
    ]
    
    def __init__(self, orb_factor: float = 1.0):
        """
        Initialize midpoints calculator
        
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
    
    def calculate_midpoint(self, lon1: float, lon2: float) -> float:
        """
        Calculate midpoint between two longitudes
        
        Args:
            lon1: First longitude
            lon2: Second longitude
            
        Returns:
            Midpoint longitude (0-360 degrees)
        """
        # Calculate both possible midpoints
        midpoint1 = (lon1 + lon2) / 2
        midpoint2 = (midpoint1 + 180) % 360
        
        # Choose the midpoint that's closer to both planets
        diff1 = min(abs(midpoint1 - lon1), 360 - abs(midpoint1 - lon1)) + \
                min(abs(midpoint1 - lon2), 360 - abs(midpoint1 - lon2))
        diff2 = min(abs(midpoint2 - lon1), 360 - abs(midpoint2 - lon1)) + \
                min(abs(midpoint2 - lon2), 360 - abs(midpoint2 - lon2))
        
        return midpoint1 if diff1 <= diff2 else midpoint2
    
    def calculate_orb(self, pos1: float, pos2: float) -> float:
        """Calculate the shortest orb between two positions"""
        diff = abs(pos1 - pos2)
        return min(diff, 360 - diff)
    
    def calculate_all_midpoints(self, positions: Dict[str, float]) -> List[Midpoint]:
        """Calculate all midpoints for given positions"""
        midpoints = []
        planet_list = list(positions.keys())
        
        # Calculate midpoints for all planet pairs
        for i, planet1 in enumerate(planet_list):
            for planet2 in planet_list[i+1:]:
                lon1 = positions[planet1]
                lon2 = positions[planet2]
                
                midpoint_lon = self.calculate_midpoint(lon1, lon2)
                midpoint_sign, midpoint_degree = self.longitude_to_sign_degree(midpoint_lon)
                
                midpoint = Midpoint(
                    planet1=planet1,
                    planet2=planet2,
                    midpoint_longitude=midpoint_lon,
                    midpoint_sign=midpoint_sign,
                    midpoint_degree=midpoint_degree
                )
                midpoints.append(midpoint)
        
        return midpoints
    
    def find_midpoint_contacts(self, midpoints: List[Midpoint], 
                             positions: Dict[str, float]) -> List[MidpointContact]:
        """Find contacts between midpoints and planets"""
        contacts = []
        
        for midpoint in midpoints:
            for planet, planet_lon in positions.items():
                # Skip if planet is part of the midpoint
                if planet in [midpoint.planet1, midpoint.planet2]:
                    continue
                
                # Calculate orb to midpoint
                orb_conj = self.calculate_orb(midpoint.midpoint_longitude, planet_lon)
                
                # Check for conjunction
                if orb_conj <= self.CONTACT_ORBS["conjunction"] * self.orb_factor:
                    contact = MidpointContact(
                        midpoint=midpoint,
                        contacted_planet=planet,
                        contact_type="conjunction",
                        orb=orb_conj
                    )
                    contacts.append(contact)
                
                # Check for opposition (planet opposite to midpoint)
                opposite_point = (midpoint.midpoint_longitude + 180) % 360
                orb_opp = self.calculate_orb(opposite_point, planet_lon)
                
                if orb_opp <= self.CONTACT_ORBS["opposition"] * self.orb_factor:
                    contact = MidpointContact(
                        midpoint=midpoint,
                        contacted_planet=planet,
                        contact_type="opposition",
                        orb=orb_opp
                    )
                    contacts.append(contact)
                
                # Check for squares (90 degrees from midpoint)
                square_points = [
                    (midpoint.midpoint_longitude + 90) % 360,
                    (midpoint.midpoint_longitude - 90) % 360
                ]
                
                for square_point in square_points:
                    orb_sq = self.calculate_orb(square_point, planet_lon)
                    
                    if orb_sq <= self.CONTACT_ORBS["square"] * self.orb_factor:
                        contact = MidpointContact(
                            midpoint=midpoint,
                            contacted_planet=planet,
                            contact_type="square",
                            orb=orb_sq
                        )
                        contacts.append(contact)
        
        return sorted(contacts, key=lambda x: x.orb)
    
    def calculate_midpoints(self, positions: Dict[str, float]) -> MidpointsResult:
        """
        Calculate complete midpoints analysis
        
        Args:
            positions: Dictionary of planet names to longitudes
        """
        # Calculate all midpoints
        midpoints = self.calculate_all_midpoints(positions)
        
        # Find contacts
        contacts = self.find_midpoint_contacts(midpoints, positions)
        
        # Filter for major midpoints
        major_contacts = []
        for contact in contacts:
            midpoint_pair = (contact.midpoint.planet1, contact.midpoint.planet2)
            reverse_pair = (contact.midpoint.planet2, contact.midpoint.planet1)
            
            if midpoint_pair in self.MAJOR_MIDPOINTS or reverse_pair in self.MAJOR_MIDPOINTS:
                major_contacts.append(contact)
        
        return MidpointsResult(
            midpoints=midpoints,
            contacts=contacts,
            major_contacts=major_contacts,
            diagnostics={
                "total_midpoints": len(midpoints),
                "total_contacts": len(contacts),
                "major_contacts": len(major_contacts),
                "orb_factor": self.orb_factor,
                "calculation_date": date.today().isoformat()
            }
        )
    
    def get_major_midpoints_summary(self, positions: Dict[str, float]) -> Dict[str, Any]:
        """Get summary of major midpoints with formatted output"""
        result = self.calculate_midpoints(positions)
        
        return {
            "major_midpoints": [
                {
                    "planets": f"{mp.planet1}/{mp.planet2}",
                    "position": f"{mp.midpoint_sign} {mp.midpoint_degree:.1f}°",
                    "significance": "high" if (mp.planet1, mp.planet2) in self.MAJOR_MIDPOINTS[:6] else "moderate"
                }
                for mp in result.midpoints
                if (mp.planet1, mp.planet2) in self.MAJOR_MIDPOINTS or 
                   (mp.planet2, mp.planet1) in self.MAJOR_MIDPOINTS
            ],
            "major_contacts": [
                {
                    "midpoint": f"{contact.midpoint.planet1}/{contact.midpoint.planet2}",
                    "contacted_planet": contact.contacted_planet,
                    "contact_type": contact.contact_type,
                    "orb": f"{contact.orb:.2f}°",
                    "strength": "very_strong" if contact.orb <= 0.5 else "strong" if contact.orb <= 1.0 else "moderate"
                }
                for contact in result.major_contacts[:10]  # Top 10 contacts
            ],
            "tight_contacts": [
                {
                    "midpoint": f"{contact.midpoint.planet1}/{contact.midpoint.planet2}",
                    "contacted_planet": contact.contacted_planet,
                    "contact_type": contact.contact_type,
                    "orb": f"{contact.orb:.2f}°"
                }
                for contact in result.contacts
                if contact.orb <= 1.0  # Very tight contacts only
            ],
            "diagnostics": result.diagnostics
        }
    
    def compute(self, chart_data: Dict[str, Any], when: Optional[date] = None) -> Dict[str, Any]:
        """
        Standard compute interface for midpoints
        
        Args:
            chart_data: Chart data including planet positions
            when: Date for calculation (not used for natal midpoints)
        """
        positions = chart_data.get("planets", {})
        result = self.calculate_midpoints(positions)
        
        # Format for interpretation system
        features = []
        evidence = []
        
        # Add major midpoint contacts as evidence
        for contact in result.major_contacts:
            if contact.orb <= 2.0:  # Within reasonable orb
                strength = "very_strong" if contact.orb <= 0.5 else "strong" if contact.orb <= 1.0 else "moderate"
                
                evidence.append({
                    "type": "MIDPOINT",
                    "description": f"{contact.contacted_planet} {contact.contact_type} {contact.midpoint.planet1}/{contact.midpoint.planet2} midpoint",
                    "orb": contact.orb,
                    "strength": strength,
                    "timing": "natal",
                    "midpoint_planets": [contact.midpoint.planet1, contact.midpoint.planet2]
                })
        
        # Add significant midpoint structures as features
        sun_moon_midpoint = next(
            (mp for mp in result.midpoints 
             if (mp.planet1 == "Sun" and mp.planet2 == "Moon") or 
                (mp.planet1 == "Moon" and mp.planet2 == "Sun")), 
            None
        )
        
        if sun_moon_midpoint:
            features.append({
                "type": "sun_moon_midpoint",
                "position": f"{sun_moon_midpoint.midpoint_sign} {sun_moon_midpoint.midpoint_degree:.1f}°",
                "significance": "major"
            })
        
        return {
            "features": features,
            "evidence": evidence,
            "diagnostics": result.diagnostics
        }