"""
Annual Profection calculator
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import date, datetime

@dataclass
class ProfectionResult:
    """Annual Profection result"""
    age: int
    profected_house: int
    profected_sign: str
    year_lord: str
    activated_topics: List[str]
    diagnostics: Dict[str, Any]

class ProfectionCalculator:
    """Annual Profection calculator"""
    
    # House topics/themes
    HOUSE_TOPICS = {
        1: ["Identity", "Appearance", "Vitality", "New Beginnings"],
        2: ["Resources", "Values", "Possessions", "Self-Worth"],
        3: ["Communication", "Siblings", "Short Trips", "Learning"],
        4: ["Home", "Family", "Roots", "Private Life"],
        5: ["Creativity", "Children", "Romance", "Self-Expression"],
        6: ["Health", "Work", "Service", "Daily Routine"],
        7: ["Partnerships", "Marriage", "Open Enemies", "Others"],
        8: ["Transformation", "Shared Resources", "Death/Rebirth", "Occult"],
        9: ["Philosophy", "Higher Learning", "Travel", "Spirituality"],
        10: ["Career", "Reputation", "Authority", "Public Life"],
        11: ["Friends", "Groups", "Hopes", "Social Networks"],
        12: ["Spirituality", "Hidden Enemies", "Sacrifice", "Unconscious"]
    }
    
    # Sign rulers
    SIGN_RULERS = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
        "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
        "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
        "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
    }
    
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    def __init__(self):
        pass
    
    def calculate_age(self, birth_date: date, target_date: date = None) -> int:
        """Calculate age at target date (default: today)"""
        if target_date is None:
            target_date = date.today()
        
        age = target_date.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if target_date.month < birth_date.month or \
           (target_date.month == birth_date.month and target_date.day < birth_date.day):
            age -= 1
        
        return age
    
    def longitude_to_sign(self, longitude: float) -> str:
        """Convert longitude to zodiac sign"""
        return self.SIGNS[int(longitude // 30)]
    
    def calculate_profection(self, birth_date: date, asc_longitude: float, 
                           target_date: date = None) -> ProfectionResult:
        """
        Calculate Annual Profection for given date
        
        Args:
            birth_date: Birth date
            asc_longitude: Ascendant longitude in degrees
            target_date: Date to calculate for (default: today)
        """
        if target_date is None:
            target_date = date.today()
        
        # Calculate age
        age = self.calculate_age(birth_date, target_date)
        
        # Profected house = (age % 12) + 1
        # Age 0 = House 1, Age 1 = House 2, etc.
        profected_house = (age % 12) + 1
        
        # Get Ascendant sign
        asc_sign = self.longitude_to_sign(asc_longitude)
        asc_sign_index = self.SIGNS.index(asc_sign)
        
        # Calculate profected sign
        # House 1 = ASC sign, House 2 = next sign, etc.
        profected_sign_index = (asc_sign_index + profected_house - 1) % 12
        profected_sign = self.SIGNS[profected_sign_index]
        
        # Year lord = ruler of profected sign
        year_lord = self.SIGN_RULERS[profected_sign]
        
        # Activated topics from house themes
        activated_topics = self.HOUSE_TOPICS.get(profected_house, [])
        
        return ProfectionResult(
            age=age,
            profected_house=profected_house,
            profected_sign=profected_sign,
            year_lord=year_lord,
            activated_topics=activated_topics,
            diagnostics={
                "birth_date": birth_date.isoformat(),
                "target_date": target_date.isoformat(),
                "asc_sign": asc_sign,
                "calculation_method": "annual_profection"
            }
        )
    
    def get_profection_timeline(self, birth_date: date, asc_longitude: float, 
                              years_ahead: int = 10) -> List[ProfectionResult]:
        """Get profection timeline for multiple years"""
        timeline = []
        current_date = date.today()
        
        for i in range(years_ahead + 1):
            target_date = date(current_date.year + i, birth_date.month, birth_date.day)
            profection = self.calculate_profection(birth_date, asc_longitude, target_date)
            timeline.append(profection)
        
        return timeline
    
    def get_year_lord_periods(self, birth_date: date, asc_longitude: float,
                             target_year: int = None) -> Dict[str, Any]:
        """
        Get detailed year lord periods for a specific year
        This can be extended to include monthly profections within the year
        """
        if target_year is None:
            target_year = date.today().year
        
        target_date = date(target_year, birth_date.month, birth_date.day)
        annual_profection = self.calculate_profection(birth_date, asc_longitude, target_date)
        
        # Calculate monthly profections within the year
        monthly_profections = []
        for month in range(12):
            # Each month advances one house
            monthly_house = ((annual_profection.profected_house - 1 + month) % 12) + 1
            monthly_sign_index = (self.SIGNS.index(annual_profection.profected_sign) + month) % 12
            monthly_sign = self.SIGNS[monthly_sign_index]
            monthly_lord = self.SIGN_RULERS[monthly_sign]
            
            monthly_profections.append({
                "month": month + 1,
                "house": monthly_house,
                "sign": monthly_sign,
                "lord": monthly_lord,
                "topics": self.HOUSE_TOPICS.get(monthly_house, [])
            })
        
        return {
            "year": target_year,
            "annual": {
                "age": annual_profection.age,
                "house": annual_profection.profected_house,
                "sign": annual_profection.profected_sign,
                "year_lord": annual_profection.year_lord,
                "topics": annual_profection.activated_topics
            },
            "monthly": monthly_profections,
            "diagnostics": annual_profection.diagnostics
        }