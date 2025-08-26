"""
Fixed Stars calculator
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import date

@dataclass
class FixedStar:
    """Fixed star information"""
    name: str
    longitude: float  # Current longitude (with precession)
    magnitude: float
    nature: str  # Planetary nature (e.g., "Mars-Jupiter")
    keywords: List[str]
    is_royal: bool = False

@dataclass
class StarContact:
    """Contact between planet and fixed star"""
    star: FixedStar
    planet: str
    planet_longitude: float
    orb: float
    contact_type: str  # "conjunction", "opposition"

@dataclass
class FixedStarsResult:
    """Complete fixed stars calculation result"""
    star_contacts: List[StarContact]
    royal_star_contacts: List[StarContact]
    diagnostics: Dict[str, Any]

class FixedStarsCalculator:
    """Fixed Stars calculator"""
    
    # Major fixed stars with their approximate 2000.0 positions
    # Note: These positions need regular updates due to precession
    FIXED_STARS = {
        # Royal Stars (Watchers of Heaven)
        "Aldebaran": {
            "longitude": 69.47,  # ~9° Gemini
            "magnitude": 0.85,
            "nature": "Mars",
            "keywords": ["Honor", "Intelligence", "Courage", "Leadership", "Military success"],
            "is_royal": True
        },
        "Regulus": {
            "longitude": 149.59,  # ~29° Leo
            "magnitude": 1.35,
            "nature": "Mars-Jupiter",
            "keywords": ["Royalty", "Leadership", "Success", "Honor", "Magnanimity"],
            "is_royal": True
        },
        "Antares": {
            "longitude": 249.47,  # ~9° Sagittarius
            "magnitude": 1.09,
            "nature": "Mars-Jupiter",
            "keywords": ["Courage", "Destructiveness", "War", "Honors", "Danger"],
            "is_royal": True
        },
        "Fomalhaut": {
            "longitude": 333.52,  # ~3° Pisces
            "magnitude": 1.16,
            "nature": "Venus-Mercury",
            "keywords": ["Idealism", "Psychic ability", "Magic", "Inspiration", "Fame"],
            "is_royal": True
        },
        
        # Other major stars
        "Sirius": {
            "longitude": 104.0,  # ~14° Cancer
            "magnitude": -1.46,
            "nature": "Jupiter-Mars",
            "keywords": ["Fame", "Honor", "Wealth", "Passion", "Devotion"],
            "is_royal": False
        },
        "Capella": {
            "longitude": 71.53,  # ~21° Gemini
            "magnitude": 0.08,
            "nature": "Mars-Mercury",
            "keywords": ["Learning", "Research", "Inquisitiveness", "Wisdom"],
            "is_royal": False
        },
        "Vega": {
            "longitude": 285.17,  # ~15° Capricorn
            "magnitude": 0.03,
            "nature": "Venus-Mercury",
            "keywords": ["Artistic ability", "Music", "Refinement", "Charisma"],
            "is_royal": False
        },
        "Spica": {
            "longitude": 203.50,  # ~23° Libra
            "magnitude": 1.04,
            "nature": "Venus-Mars",
            "keywords": ["Success", "Renown", "Wealth", "Artistic gifts", "Science"],
            "is_royal": False
        },
        "Arcturus": {
            "longitude": 204.22,  # ~24° Libra
            "magnitude": -0.05,
            "nature": "Mars-Jupiter",
            "keywords": ["Prosperity", "Honors", "Riches", "Fame", "Leadership"],
            "is_royal": False
        },
        "Algol": {
            "longitude": 56.13,  # ~26° Taurus
            "magnitude": 2.12,
            "nature": "Saturn-Jupiter",
            "keywords": ["Violence", "Decapitation", "Losing head", "Transformation"],
            "is_royal": False
        },
        "Procyon": {
            "longitude": 95.47,  # ~25° Cancer
            "magnitude": 0.34,
            "nature": "Mercury-Mars",
            "keywords": ["Activity", "Violence", "Sudden fame", "Hasty judgments"],
            "is_royal": False
        },
        "Canopus": {
            "longitude": 74.22,  # ~14° Cancer (Southern hemisphere)
            "magnitude": -0.74,
            "nature": "Saturn-Jupiter",
            "keywords": ["Voyages", "Educational work", "Stability", "Conservatism"],
            "is_royal": False
        }
    }
    
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    def __init__(self, orb: float = 1.0):
        """
        Initialize fixed stars calculator
        
        Args:
            orb: Maximum orb for star contacts (default 1.0 degrees)
        """
        self.orb = orb
    
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
    
    def create_fixed_star_objects(self) -> List[FixedStar]:
        """Create FixedStar objects from star data"""
        stars = []
        
        for name, data in self.FIXED_STARS.items():
            star = FixedStar(
                name=name,
                longitude=data["longitude"],
                magnitude=data["magnitude"],
                nature=data["nature"],
                keywords=data["keywords"],
                is_royal=data["is_royal"]
            )
            stars.append(star)
        
        return stars
    
    def find_star_contacts(self, planet_positions: Dict[str, float]) -> List[StarContact]:
        """Find contacts between planets and fixed stars"""
        contacts = []
        stars = self.create_fixed_star_objects()
        
        for star in stars:
            for planet, planet_lon in planet_positions.items():
                # Calculate orb for conjunction
                orb_conj = self.calculate_orb(star.longitude, planet_lon)
                
                if orb_conj <= self.orb:
                    contact = StarContact(
                        star=star,
                        planet=planet,
                        planet_longitude=planet_lon,
                        orb=orb_conj,
                        contact_type="conjunction"
                    )
                    contacts.append(contact)
                
                # Calculate orb for opposition
                opposite_point = (star.longitude + 180) % 360
                orb_opp = self.calculate_orb(opposite_point, planet_lon)
                
                if orb_opp <= self.orb:
                    contact = StarContact(
                        star=star,
                        planet=planet,
                        planet_longitude=planet_lon,
                        orb=orb_opp,
                        contact_type="opposition"
                    )
                    contacts.append(contact)
        
        return sorted(contacts, key=lambda x: x.orb)
    
    def calculate_fixed_stars(self, planet_positions: Dict[str, float]) -> FixedStarsResult:
        """
        Calculate complete fixed stars analysis
        
        Args:
            planet_positions: Dictionary of planet names to longitudes
        """
        # Find all star contacts
        star_contacts = self.find_star_contacts(planet_positions)
        
        # Filter for royal star contacts
        royal_star_contacts = [
            contact for contact in star_contacts 
            if contact.star.is_royal
        ]
        
        return FixedStarsResult(
            star_contacts=star_contacts,
            royal_star_contacts=royal_star_contacts,
            diagnostics={
                "total_contacts": len(star_contacts),
                "royal_contacts": len(royal_star_contacts),
                "orb_used": self.orb,
                "calculation_date": date.today().isoformat(),
                "stars_checked": len(self.FIXED_STARS)
            }
        )
    
    def get_star_contacts_summary(self, planet_positions: Dict[str, float]) -> Dict[str, Any]:
        """Get summary of fixed star contacts with formatted output"""
        result = self.calculate_fixed_stars(planet_positions)
        
        return {
            "royal_star_contacts": [
                {
                    "star_name": contact.star.name,
                    "planet": contact.planet,
                    "star_position": f"{self.longitude_to_sign_degree(contact.star.longitude)[0]} {contact.star.longitude % 30:.1f}°",
                    "planet_position": f"{self.longitude_to_sign_degree(contact.planet_longitude)[0]} {contact.planet_longitude % 30:.1f}°",
                    "contact_type": contact.contact_type,
                    "orb": f"{contact.orb:.2f}°",
                    "star_nature": contact.star.nature,
                    "keywords": contact.star.keywords[:3],  # First 3 keywords
                    "magnitude": contact.star.magnitude
                }
                for contact in result.royal_star_contacts
            ],
            "major_star_contacts": [
                {
                    "star_name": contact.star.name,
                    "planet": contact.planet,
                    "contact_type": contact.contact_type,
                    "orb": f"{contact.orb:.2f}°",
                    "star_nature": contact.star.nature,
                    "keywords": contact.star.keywords[:2],
                    "strength": "very_strong" if contact.orb <= 0.3 else "strong" if contact.orb <= 0.6 else "moderate"
                }
                for contact in result.star_contacts
                if contact.star.magnitude <= 1.5  # Bright stars only
            ],
            "all_contacts": [
                {
                    "star_name": contact.star.name,
                    "planet": contact.planet,
                    "contact_type": contact.contact_type,
                    "orb": f"{contact.orb:.2f}°"
                }
                for contact in result.star_contacts
            ],
            "diagnostics": result.diagnostics
        }
    
    def get_star_by_longitude(self, longitude: float, orb: float = 1.0) -> Optional[FixedStar]:
        """Find fixed star near given longitude"""
        stars = self.create_fixed_star_objects()
        
        for star in stars:
            if self.calculate_orb(star.longitude, longitude) <= orb:
                return star
        
        return None
    
    def compute(self, chart_data: Dict[str, Any], when: Optional[date] = None) -> Dict[str, Any]:
        """
        Standard compute interface for fixed stars
        
        Args:
            chart_data: Chart data including planet positions
            when: Date for calculation (not used for fixed stars)
        """
        positions = chart_data.get("planets", {})
        result = self.calculate_fixed_stars(positions)
        
        # Format for interpretation system
        features = []
        evidence = []
        
        # Add royal star contacts as high-priority evidence
        for contact in result.royal_star_contacts:
            strength = "very_strong" if contact.orb <= 0.3 else "strong" if contact.orb <= 0.6 else "moderate"
            
            evidence.append({
                "type": "FIXED_STAR",
                "description": f"{contact.planet} {contact.contact_type} {contact.star.name}",
                "orb": contact.orb,
                "strength": strength,
                "timing": "natal",
                "star_name": contact.star.name,
                "star_nature": contact.star.nature,
                "keywords": contact.star.keywords,
                "is_royal": True
            })
        
        # Add other bright star contacts
        for contact in result.star_contacts:
            if not contact.star.is_royal and contact.star.magnitude <= 1.0 and contact.orb <= 0.5:
                evidence.append({
                    "type": "FIXED_STAR",
                    "description": f"{contact.planet} {contact.contact_type} {contact.star.name}",
                    "orb": contact.orb,
                    "strength": "strong",
                    "timing": "natal",
                    "star_name": contact.star.name,
                    "star_nature": contact.star.nature,
                    "keywords": contact.star.keywords,
                    "is_royal": False
                })
        
        # Add royal star emphasis as feature
        if result.royal_star_contacts:
            features.append({
                "type": "royal_star_emphasis",
                "count": len(result.royal_star_contacts),
                "stars": [contact.star.name for contact in result.royal_star_contacts],
                "significance": "major"
            })
        
        return {
            "features": features,
            "evidence": evidence,
            "diagnostics": result.diagnostics
        }