"""
Evidence-based scoring system for astrological interpretations
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

class EvidenceType(Enum):
    """Types of astrological evidence"""
    ALMUTEN = "almuten"
    LIGHTS = "lights"  # Sun, Moon
    ANGLES = "angles"  # ASC, MC
    HOUSE_RULER = "house_ruler"
    DIGNITY = "dignity"
    RECEPTION = "reception"
    ASPECT = "aspect"
    ANTISCIA = "antiscia"
    MIDPOINT = "midpoint"
    FIXED_STAR = "fixed_star"
    ASTEROID = "asteroid"
    TNO = "tno"
    URANIAN = "uranian"
    ZR_PERIOD = "zr_period"
    PROFECTION = "profection"
    FIRDARIA = "firdaria"
    PROGRESSION = "progression"
    SOLAR_ARC = "solar_arc"
    TRANSIT = "transit"
    RETURN = "return"

@dataclass
class Evidence:
    """Single piece of astrological evidence"""
    type: EvidenceType
    description: str
    base_score: float
    multipliers: Dict[str, float]
    final_score: float
    orb: Optional[float] = None
    is_applying: Optional[bool] = None
    source_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.final_score == 0:
            self.final_score = self.calculate_final_score()
    
    def calculate_final_score(self) -> float:
        """Calculate final score with all multipliers applied"""
        score = self.base_score
        for multiplier in self.multipliers.values():
            score *= multiplier
        return score

@dataclass
class ScoringResult:
    """Complete scoring result for a chart element"""
    element: str  # Planet, house, aspect, etc.
    total_score: float
    evidence_list: List[Evidence]
    confidence: float
    interpretation_priority: str  # "main", "strong", "background", "drop"
    
class AstroScorer:
    """Astrological evidence scoring system"""
    
    # Base scores according to spec
    BASE_SCORES = {
        EvidenceType.ALMUTEN: 6.0,
        EvidenceType.LIGHTS: 5.0,  # Sun, Moon
        EvidenceType.ANGLES: 5.0,  # ASC, MC
        EvidenceType.HOUSE_RULER: 4.0,  # Angular house rulers
        EvidenceType.DIGNITY: 3.0,  # Standard planets
        EvidenceType.ASPECT: 3.0,
        EvidenceType.ANTISCIA: 3.0,
        EvidenceType.MIDPOINT: 3.0,
        EvidenceType.FIXED_STAR: 3.0,
        EvidenceType.ASTEROID: 2.5,
        EvidenceType.TNO: 2.5,
        EvidenceType.URANIAN: 2.5,
        EvidenceType.ZR_PERIOD: 4.0,
        EvidenceType.PROFECTION: 3.5,
        EvidenceType.FIRDARIA: 3.5,
        EvidenceType.PROGRESSION: 3.0,
        EvidenceType.SOLAR_ARC: 3.0,
        EvidenceType.TRANSIT: 2.5,
        EvidenceType.RETURN: 2.0
    }
    
    # Score thresholds
    THRESHOLDS = {
        "main": 7.5,      # ≥7.5 main interpretation
        "strong": 6.0,    # 6.0-7.49 strong
        "background": 4.5, # 4.5-5.99 background
        "drop": 4.5       # <4.5 drop
    }
    
    def __init__(self):
        pass
    
    def score_dignity(self, planet: str, sign: str, dignity_type: str, 
                     is_day_birth: bool = True) -> Evidence:
        """Score essential dignity"""
        base_score = self.BASE_SCORES[EvidenceType.DIGNITY]
        multipliers = {}
        
        # Dignity multipliers
        if dignity_type == "rulership":
            multipliers["dignity"] = 1.3
        elif dignity_type == "exaltation":
            multipliers["dignity"] = 1.15
        elif dignity_type == "detriment":
            multipliers["dignity"] = 0.85
        elif dignity_type == "fall":
            multipliers["dignity"] = 0.75
        else:
            multipliers["dignity"] = 1.0
        
        # Sect multiplier
        sect_planets = {
            "diurnal": ["Sun", "Jupiter", "Saturn"],
            "nocturnal": ["Moon", "Venus", "Mars"]
        }
        
        preferred_sect = "diurnal" if is_day_birth else "nocturnal"
        if planet in sect_planets[preferred_sect]:
            multipliers["sect"] = 1.2
        else:
            multipliers["sect"] = 1.0
        
        return Evidence(
            type=EvidenceType.DIGNITY,
            description=f"{planet} in {dignity_type} in {sign}",
            base_score=base_score,
            multipliers=multipliers,
            final_score=0,  # Will be calculated
            source_data={"planet": planet, "sign": sign, "dignity_type": dignity_type}
        )
    
    def score_aspect(self, planet1: str, planet2: str, aspect_type: str, 
                    orb: float, is_applying: bool = True) -> Evidence:
        """Score planetary aspect"""
        base_score = self.BASE_SCORES[EvidenceType.ASPECT]
        multipliers = {}
        
        # Orb multiplier
        if orb <= 2.0:
            multipliers["orb"] = 1.25
        elif orb <= 4.0:
            multipliers["orb"] = 1.1
        else:
            multipliers["orb"] = 1.0
        
        # Applying vs separating (for time-sensitive methods)
        if is_applying:
            multipliers["applying"] = 1.1
        else:
            multipliers["applying"] = 0.9
        
        # Aspect type strength (could be refined)
        aspect_strengths = {
            "conjunction": 1.0,
            "opposition": 1.0,
            "trine": 0.9,
            "square": 0.9,
            "sextile": 0.8
        }
        multipliers["aspect_type"] = aspect_strengths.get(aspect_type, 0.7)
        
        return Evidence(
            type=EvidenceType.ASPECT,
            description=f"{planet1} {aspect_type} {planet2}",
            base_score=base_score,
            multipliers=multipliers,
            final_score=0,
            orb=orb,
            is_applying=is_applying,
            source_data={"planet1": planet1, "planet2": planet2, "aspect_type": aspect_type}
        )
    
    def score_almuten(self, planet: str, almuten_score: int, is_winner: bool = False) -> Evidence:
        """Score Almuten Figuris evidence"""
        base_score = self.BASE_SCORES[EvidenceType.ALMUTEN]
        multipliers = {}
        
        # Winner gets full score, others proportional
        if is_winner:
            multipliers["almuten_status"] = 1.0
        else:
            # Proportional scoring based on almuten points
            multipliers["almuten_status"] = min(almuten_score / 20.0, 0.8)  # Max 80% for non-winners
        
        return Evidence(
            type=EvidenceType.ALMUTEN,
            description=f"{planet} Almuten Figuris {'winner' if is_winner else f'score: {almuten_score}'}",
            base_score=base_score,
            multipliers=multipliers,
            final_score=0,
            source_data={"planet": planet, "almuten_score": almuten_score, "is_winner": is_winner}
        )
    
    def score_time_lord(self, lord: str, method: str, level: str = "major", 
                       is_peak: bool = False, is_lb: bool = False) -> Evidence:
        """Score time-lord evidence"""
        method_types = {
            "zr": EvidenceType.ZR_PERIOD,
            "profection": EvidenceType.PROFECTION,
            "firdaria": EvidenceType.FIRDARIA
        }
        
        evidence_type = method_types.get(method, EvidenceType.ZR_PERIOD)
        base_score = self.BASE_SCORES[evidence_type]
        multipliers = {}
        
        # Method-specific multipliers
        if method == "zr":
            if level == "L1":
                multipliers["zr_level"] = 1.3
            elif level == "L2" and is_peak:
                multipliers["zr_level"] = 1.15
            elif level == "L2" and is_lb:
                multipliers["zr_level"] = 1.10
            else:
                multipliers["zr_level"] = 1.0
        elif method == "profection":
            multipliers["profection"] = 1.2
        elif method == "firdaria":
            if level == "major":
                multipliers["firdaria"] = 1.2
            else:  # minor
                multipliers["firdaria"] = 1.05
        
        # Peak/LB bonuses
        if is_peak:
            multipliers["peak"] = 1.1
        if is_lb:
            multipliers["lb"] = 1.05
        
        return Evidence(
            type=evidence_type,
            description=f"{lord} {method} {level} {'peak' if is_peak else ''} {'LB' if is_lb else ''}".strip(),
            base_score=base_score,
            multipliers=multipliers,
            final_score=0,
            source_data={"lord": lord, "method": method, "level": level, "is_peak": is_peak, "is_lb": is_lb}
        )
    
    def score_antiscia(self, planet1: str, planet2: str, antiscia_type: str, orb: float) -> Evidence:
        """Score antiscia contact"""
        base_score = self.BASE_SCORES[EvidenceType.ANTISCIA]
        multipliers = {}
        
        # Antiscia are considered equal to major aspects
        multipliers["antiscia_strength"] = 1.0
        
        # Tight orb bonus
        if orb <= 0.5:
            multipliers["orb"] = 1.25
        elif orb <= 1.0:
            multipliers["orb"] = 1.1
        else:
            multipliers["orb"] = 1.0
        
        return Evidence(
            type=EvidenceType.ANTISCIA,
            description=f"{planet1} {antiscia_type} {planet2}",
            base_score=base_score,
            multipliers=multipliers,
            final_score=0,
            orb=orb,
            source_data={"planet1": planet1, "planet2": planet2, "antiscia_type": antiscia_type}
        )
    
    def score_midpoint(self, midpoint_planets: List[str], contacted_planet: str, orb: float) -> Evidence:
        """Score midpoint contact"""
        base_score = self.BASE_SCORES[EvidenceType.MIDPOINT]
        multipliers = {}
        
        # Special bonus for Sun/Moon midpoint
        if set(midpoint_planets) == {"Sun", "Moon"}:
            multipliers["midpoint_type"] = 1.25
        else:
            multipliers["midpoint_type"] = 1.2
        
        # Tight orb requirement for midpoints
        if orb <= 1.0:
            multipliers["orb"] = 1.2
        elif orb <= 1.5:
            multipliers["orb"] = 1.0
        else:
            multipliers["orb"] = 0.8  # Penalty for wide orbs
        
        return Evidence(
            type=EvidenceType.MIDPOINT,
            description=f"{'/'.join(midpoint_planets)} midpoint contacted by {contacted_planet}",
            base_score=base_score,
            multipliers=multipliers,
            final_score=0,
            orb=orb,
            source_data={"midpoint_planets": midpoint_planets, "contacted_planet": contacted_planet}
        )
    
    def calculate_element_score(self, evidence_list: List[Evidence]) -> ScoringResult:
        """Calculate total score for a chart element from all evidence"""
        if not evidence_list:
            return ScoringResult("", 0.0, [], 0.0, "drop")
        
        # Calculate total score
        total_score = sum(evidence.final_score for evidence in evidence_list)
        
        # Multiple confirmations bonus
        if len(evidence_list) >= 3:
            total_score *= 1.2
        
        # Determine priority level
        if total_score >= self.THRESHOLDS["main"]:
            priority = "main"
        elif total_score >= self.THRESHOLDS["strong"]:
            priority = "strong"
        elif total_score >= self.THRESHOLDS["background"]:
            priority = "background"
        else:
            priority = "drop"
        
        # Calculate confidence (0-1 scale)
        confidence = min(total_score / 10.0, 1.0)  # Normalize to max 10
        
        # Get element name from first evidence
        element = evidence_list[0].source_data.get("planet", "Unknown") if evidence_list[0].source_data else "Unknown"
        
        return ScoringResult(
            element=element,
            total_score=total_score,
            evidence_list=evidence_list,
            confidence=confidence,
            interpretation_priority=priority
        )
    
    def flag_generational(self, planet: str) -> bool:
        """Flag generational planets"""
        generational_planets = ["Uranus", "Neptune", "Pluto"]
        return planet in generational_planets
    
    def get_scoring_summary(self, scoring_results: List[ScoringResult]) -> Dict[str, Any]:
        """Get summary of scoring results"""
        by_priority = {
            "main": [r for r in scoring_results if r.interpretation_priority == "main"],
            "strong": [r for r in scoring_results if r.interpretation_priority == "strong"],
            "background": [r for r in scoring_results if r.interpretation_priority == "background"],
            "dropped": [r for r in scoring_results if r.interpretation_priority == "drop"]
        }
        
        return {
            "total_elements": len(scoring_results),
            "by_priority": {k: len(v) for k, v in by_priority.items()},
            "highest_score": max((r.total_score for r in scoring_results), default=0),
            "average_confidence": sum(r.confidence for r in scoring_results) / len(scoring_results) if scoring_results else 0,
            "main_elements": [r.element for r in by_priority["main"]],
            "strong_elements": [r.element for r in by_priority["strong"]]
        }