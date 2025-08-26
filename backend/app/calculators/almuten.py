from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class Point:
    """Astrological point (planet, angle, lot)"""
    name: str
    longitude: float
    sign: str
    degree: float

@dataclass
class AlmutenResult:
    """Almuten calculation result"""
    winner: str
    scores: Dict[str, int]
    tie_break_reason: str = ""
    diagnostics: Dict[str, Any] = None

class DignityTables:
    """Essential dignity tables"""
    
    def __init__(self):
        # Rulerships (Domicile)
        self.rulerships = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        
        # Exaltations
        self.exaltations = {
            "Aries": "Sun", "Taurus": "Moon", "Cancer": "Jupiter",
            "Virgo": "Mercury", "Libra": "Saturn", "Capricorn": "Mars",
            "Pisces": "Venus"
        }
        
        # Detriments (opposite of rulership)
        self.detriments = {
            "Aries": "Venus", "Taurus": "Mars", "Gemini": "Jupiter",
            "Cancer": "Saturn", "Leo": "Saturn", "Virgo": "Jupiter",
            "Libra": "Mars", "Scorpio": "Venus", "Sagittarius": "Mercury",
            "Capricorn": "Moon", "Aquarius": "Sun", "Pisces": "Mercury"
        }
        
        # Falls (opposite of exaltation)
        self.falls = {
            "Aries": "Saturn", "Taurus": "Uranus", "Cancer": "Mars",
            "Virgo": "Venus", "Libra": "Sun", "Capricorn": "Moon",
            "Pisces": "Mercury"
        }
        
        # Triplicities (Fire, Earth, Air, Water)
        self.triplicities = {
            # Fire signs (Aries, Leo, Sagittarius)
            "Fire": {"day": "Sun", "night": "Jupiter", "participating": "Saturn"},
            # Earth signs (Taurus, Virgo, Capricorn)  
            "Earth": {"day": "Venus", "night": "Moon", "participating": "Mars"},
            # Air signs (Gemini, Libra, Aquarius)
            "Air": {"day": "Saturn", "night": "Mercury", "participating": "Jupiter"},
            # Water signs (Cancer, Scorpio, Pisces)
            "Water": {"day": "Venus", "night": "Mars", "participating": "Moon"}
        }
        
        # Sign to element mapping
        self.sign_elements = {
            "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
            "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
            "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
            "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
        }
        
        # Egyptian Terms (Bounds) - simplified version
        self.terms = {
            "Aries": [
                (0, 6, "Jupiter"), (6, 12, "Venus"), (12, 20, "Mercury"),
                (20, 25, "Mars"), (25, 30, "Saturn")
            ],
            "Taurus": [
                (0, 8, "Venus"), (8, 14, "Mercury"), (14, 22, "Jupiter"),
                (22, 27, "Saturn"), (27, 30, "Mars")
            ],
            "Gemini": [
                (0, 6, "Mercury"), (6, 12, "Jupiter"), (12, 17, "Venus"),
                (17, 24, "Mars"), (24, 30, "Saturn")
            ],
            "Cancer": [
                (0, 7, "Mars"), (7, 13, "Venus"), (13, 19, "Mercury"),
                (19, 26, "Jupiter"), (26, 30, "Saturn")
            ],
            "Leo": [
                (0, 6, "Jupiter"), (6, 11, "Venus"), (11, 18, "Saturn"),
                (18, 24, "Mercury"), (24, 30, "Mars")
            ],
            "Virgo": [
                (0, 7, "Mercury"), (7, 17, "Venus"), (17, 21, "Jupiter"),
                (21, 28, "Mars"), (28, 30, "Saturn")
            ],
            "Libra": [
                (0, 6, "Saturn"), (6, 14, "Mercury"), (14, 21, "Jupiter"),
                (21, 28, "Venus"), (28, 30, "Mars")
            ],
            "Scorpio": [
                (0, 7, "Mars"), (7, 11, "Venus"), (11, 19, "Mercury"),
                (19, 24, "Jupiter"), (24, 30, "Saturn")
            ],
            "Sagittarius": [
                (0, 12, "Jupiter"), (12, 17, "Venus"), (17, 21, "Mercury"),
                (21, 26, "Saturn"), (26, 30, "Mars")
            ],
            "Capricorn": [
                (0, 7, "Mercury"), (7, 14, "Jupiter"), (14, 22, "Venus"),
                (22, 26, "Saturn"), (26, 30, "Mars")
            ],
            "Aquarius": [
                (0, 6, "Mercury"), (6, 12, "Venus"), (12, 20, "Jupiter"),
                (20, 25, "Mars"), (25, 30, "Saturn")
            ],
            "Pisces": [
                (0, 12, "Venus"), (12, 16, "Jupiter"), (16, 19, "Mercury"),
                (19, 28, "Mars"), (28, 30, "Saturn")
            ]
        }
        
        # Faces (Decans) - 10-degree divisions
        self.faces = {
            "Aries": [(0, 10, "Mars"), (10, 20, "Sun"), (20, 30, "Venus")],
            "Taurus": [(0, 10, "Mercury"), (10, 20, "Moon"), (20, 30, "Saturn")],
            "Gemini": [(0, 10, "Jupiter"), (10, 20, "Mars"), (20, 30, "Sun")],
            "Cancer": [(0, 10, "Venus"), (10, 20, "Mercury"), (20, 30, "Moon")],
            "Leo": [(0, 10, "Saturn"), (10, 20, "Jupiter"), (20, 30, "Mars")],
            "Virgo": [(0, 10, "Sun"), (10, 20, "Venus"), (20, 30, "Mercury")],
            "Libra": [(0, 10, "Moon"), (10, 20, "Saturn"), (20, 30, "Jupiter")],
            "Scorpio": [(0, 10, "Mars"), (10, 20, "Sun"), (20, 30, "Venus")],
            "Sagittarius": [(0, 10, "Mercury"), (10, 20, "Moon"), (20, 30, "Saturn")],
            "Capricorn": [(0, 10, "Jupiter"), (10, 20, "Mars"), (20, 30, "Sun")],
            "Aquarius": [(0, 10, "Venus"), (10, 20, "Mercury"), (20, 30, "Moon")],
            "Pisces": [(0, 10, "Saturn"), (10, 20, "Jupiter"), (20, 30, "Mars")]
        }
    
    def is_ruler(self, planet: str, sign: str) -> bool:
        return self.rulerships.get(sign) == planet
    
    def is_exalted(self, planet: str, sign: str) -> bool:
        return self.exaltations.get(sign) == planet
    
    def is_detriment(self, planet: str, sign: str) -> bool:
        return self.detriments.get(sign) == planet
    
    def is_fall(self, planet: str, sign: str) -> bool:
        return self.falls.get(sign) == planet
    
    def in_triplicity(self, planet: str, sign: str, is_day: bool) -> bool:
        element = self.sign_elements.get(sign)
        if not element:
            return False
        
        triplicity = self.triplicities.get(element)
        if not triplicity:
            return False
        
        # Check day/night ruler or participating ruler
        return (planet == triplicity["day"] and is_day) or \
               (planet == triplicity["night"] and not is_day) or \
               (planet == triplicity["participating"])
    
    def in_term(self, planet: str, sign: str, degree: float) -> bool:
        terms = self.terms.get(sign, [])
        for start, end, term_ruler in terms:
            if start <= degree < end and term_ruler == planet:
                return True
        return False
    
    def in_face(self, planet: str, sign: str, degree: float) -> bool:
        faces = self.faces.get(sign, [])
        for start, end, face_ruler in faces:
            if start <= degree < end and face_ruler == planet:
                return True
        return False

def almuten_figuris(points: List[Point], chart_data: Dict[str, Any]) -> AlmutenResult:
    """
    Calculate Almuten Figuris from given points
    
    Points: Sun, Moon, ASC, MC, Fortuna, Spirit
    Scoring: rulership=5, exalt=4, triplicity=3, term=2, face=1
    """
    tables = DignityTables()
    totals: Dict[str, int] = {}
    planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    
    # Initialize scores
    for planet in planets:
        totals[planet] = 0
    
    is_day = chart_data.get("is_day", True)
    
    # Calculate scores for each point
    for point in points:
        sign = point.sign
        degree = point.degree
        
        for planet in planets:
            score = 0
            if tables.is_ruler(planet, sign):
                score += 5
            if tables.is_exalted(planet, sign):
                score += 4
            if tables.in_triplicity(planet, sign, is_day):
                score += 3
            if tables.in_term(planet, sign, degree):
                score += 2
            if tables.in_face(planet, sign, degree):
                score += 1
            
            totals[planet] += score
    
    # Find winner(s)
    max_score = max(totals.values()) if totals.values() else 0
    winners = [planet for planet, score in totals.items() if score == max_score]
    
    if len(winners) == 1:
        return AlmutenResult(
            winner=winners[0],
            scores=totals,
            diagnostics={"points_analyzed": len(points), "max_score": max_score}
        )
    
    # Tie-breaking logic
    if len(winners) > 1:
        tie_break_winner = tie_break_almuten(winners, points, chart_data, totals)
        return AlmutenResult(
            winner=tie_break_winner,
            scores=totals,
            tie_break_reason=f"Tie-break applied among: {', '.join(winners)}",
            diagnostics={
                "points_analyzed": len(points), 
                "tied_planets": winners,
                "max_score": max_score
            }
        )
    
    # No winner found
    return AlmutenResult(
        winner="None",
        scores=totals,
        tie_break_reason="No dignities found",
        diagnostics={"points_analyzed": len(points), "max_score": 0}
    )

def tie_break_almuten(winners: List[str], points: List[Point], 
                     chart_data: Dict[str, Any], scores: Dict[str, int]) -> str:
    """
    Tie-breaking logic for Almuten Figuris
    Priority: total essential > proximity to Lights > angularity > sect
    """
    # 1. Already tied on total essential dignities
    
    # 2. Proximity to Lights (Sun and Moon)
    sun_point = next((p for p in points if p.name == "Sun"), None)
    moon_point = next((p for p in points if p.name == "Moon"), None)
    
    if sun_point and moon_point:
        light_proximity = {}
        for planet in winners:
            # Find planet position in points or use 0 as default
            planet_point = next((p for p in points if p.name == planet), None)
            if planet_point:
                # Calculate proximity to both lights
                sun_distance = min(abs(planet_point.longitude - sun_point.longitude),
                                 360 - abs(planet_point.longitude - sun_point.longitude))
                moon_distance = min(abs(planet_point.longitude - moon_point.longitude),
                                  360 - abs(planet_point.longitude - moon_point.longitude))
                light_proximity[planet] = min(sun_distance, moon_distance)
            else:
                light_proximity[planet] = 180  # Maximum distance
        
        closest_to_lights = min(light_proximity, key=light_proximity.get)
        min_distance = light_proximity[closest_to_lights]
        
        # Check if one planet is significantly closer
        close_planets = [p for p, d in light_proximity.items() if d <= min_distance + 5]
        if len(close_planets) == 1:
            return close_planets[0]
        winners = close_planets
    
    # 3. Angularity (ASC, MC priority)
    angular_points = ["ASC", "MC"]
    angular_scores = {planet: 0 for planet in winners}
    
    for point in points:
        if point.name in angular_points:
            # Check which planet has strongest connection to this angle
            tables = DignityTables()
            for planet in winners:
                if tables.is_ruler(planet, point.sign):
                    angular_scores[planet] += 2
                elif tables.is_exalted(planet, point.sign):
                    angular_scores[planet] += 1
    
    max_angular = max(angular_scores.values()) if angular_scores.values() else 0
    if max_angular > 0:
        angular_winners = [p for p, s in angular_scores.items() if s == max_angular]
        if len(angular_winners) == 1:
            return angular_winners[0]
        winners = angular_winners
    
    # 4. Sect preference
    is_day = chart_data.get("is_day", True)
    sect_planets = {
        "diurnal": ["Sun", "Jupiter", "Saturn"],
        "nocturnal": ["Moon", "Venus", "Mars"]
    }
    
    preferred_sect = "diurnal" if is_day else "nocturnal"
    sect_winners = [p for p in winners if p in sect_planets[preferred_sect]]
    
    if sect_winners:
        return sect_winners[0]
    
    # 5. Default: return first winner
    return winners[0]