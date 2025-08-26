"""
Output composition system for astrological interpretations
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random

from .scoring import ScoringResult, Evidence, EvidenceType
from .conflict_resolver import Conflict

class OutputMode(Enum):
    """Output modes for different interpretation types"""
    NATAL = "natal"
    TIMING = "timing"
    TODAY = "today"
    TRANSIT = "transit"

class OutputStyle(Enum):
    """Output styles for different audiences"""
    TECHNICAL = "technical"
    ACCESSIBLE = "accessible"
    BRIEF = "brief"
    DETAILED = "detailed"

@dataclass
class InterpretationSection:
    """A section of the interpretation"""
    title: str
    content: str
    confidence: float
    evidence_count: int
    priority: str

@dataclass
class ComposedInterpretation:
    """Complete composed interpretation"""
    summary: str
    sections: List[InterpretationSection]
    overall_confidence: float
    evidence_summary: Dict[str, Any]
    warnings: List[str]
    metadata: Dict[str, Any]

class OutputComposer:
    """Composes astrological interpretations from scored evidence"""
    
    # Template phrases for different evidence types
    TEMPLATES = {
        EvidenceType.ALMUTEN: {
            "intro": [
                "Your chart's Almuten Figuris reveals that {planet} holds the strongest essential dignity",
                "The calculation of Almuten Figuris shows {planet} as the dominant planetary influence",
                "{planet} emerges as your Almuten, indicating core life themes"
            ],
            "meaning": [
                "This suggests your essential nature is strongly influenced by {planet_qualities}",
                "Your life direction and core identity are shaped by {planet_qualities}",
                "The fundamental expression of your being resonates with {planet_qualities}"
            ]
        },
        
        EvidenceType.ZR_PERIOD: {
            "intro": [
                "Your current Zodiacal Releasing period is ruled by {lord} in {sign}",
                "According to Zodiacal Releasing, you are in a {lord} period",
                "The ZR timeline shows {lord} as your current time-lord"
            ],
            "meaning": [
                "This period emphasizes {lord_themes} in your life experience",
                "The focus during this time is on {lord_themes}",
                "Current life circumstances are colored by {lord_themes}"
            ],
            "peak": [
                "This is a peak period, indicating heightened significance and opportunity",
                "You are in a peak phase, suggesting important developments",
                "This peak period brings increased activity and potential"
            ],
            "lb": [
                "This period involves a Loosing of the Bond, indicating a significant transition",
                "The LB marker suggests a major shift or release from previous patterns",
                "This transitional period marks a loosening of old bonds"
            ]
        },
        
        EvidenceType.PROFECTION: {
            "intro": [
                "Your {age}th year activates the {house}th house, ruled by {lord}",
                "Annual profection places emphasis on {house}th house themes this year",
                "The profected year highlights {house}th house matters under {lord}'s guidance"
            ],
            "meaning": [
                "This year's focus is on {house_themes}",
                "Expect developments in areas of {house_themes}",
                "The year's energy supports growth in {house_themes}"
            ]
        },
        
        EvidenceType.DIGNITY: {
            "strong": [
                "{planet} in {sign} shows strong essential dignity",
                "{planet} is well-placed in {sign}, indicating natural strength",
                "The placement of {planet} in {sign} provides solid foundation"
            ],
            "weak": [
                "{planet} in {sign} faces some essential dignity challenges",
                "{planet} in {sign} requires extra effort to express positively",
                "The placement of {planet} in {sign} suggests areas for growth"
            ]
        },
        
        EvidenceType.ASPECT: {
            "harmonious": [
                "{planet1} forms a harmonious {aspect} with {planet2}",
                "The {aspect} between {planet1} and {planet2} creates supportive energy",
                "{planet1} and {planet2} work together through their {aspect}"
            ],
            "challenging": [
                "{planet1} forms a dynamic {aspect} with {planet2}",
                "The {aspect} between {planet1} and {planet2} creates productive tension",
                "{planet1} and {planet2} generate growth through their {aspect}"
            ]
        }
    }
    
    # Planet qualities and themes
    PLANET_QUALITIES = {
        "Sun": ["leadership", "vitality", "self-expression", "authority", "creativity"],
        "Moon": ["emotions", "intuition", "nurturing", "cycles", "receptivity"],
        "Mercury": ["communication", "learning", "adaptability", "analysis", "connection"],
        "Venus": ["relationships", "beauty", "values", "harmony", "attraction"],
        "Mars": ["action", "courage", "initiative", "competition", "drive"],
        "Jupiter": ["expansion", "wisdom", "optimism", "growth", "meaning"],
        "Saturn": ["structure", "discipline", "responsibility", "mastery", "time"]
    }
    
    # House themes
    HOUSE_THEMES = {
        1: ["identity", "appearance", "new beginnings", "self-assertion"],
        2: ["resources", "values", "possessions", "self-worth"],
        3: ["communication", "learning", "siblings", "local environment"],
        4: ["home", "family", "roots", "emotional foundation"],
        5: ["creativity", "children", "romance", "self-expression"],
        6: ["health", "work", "service", "daily routines"],
        7: ["partnerships", "relationships", "cooperation", "others"],
        8: ["transformation", "shared resources", "depth", "regeneration"],
        9: ["philosophy", "higher learning", "travel", "meaning"],
        10: ["career", "reputation", "authority", "public life"],
        11: ["friends", "groups", "hopes", "social networks"],
        12: ["spirituality", "transcendence", "hidden matters", "release"]
    }
    
    def __init__(self, language: str = "en", style: OutputStyle = OutputStyle.ACCESSIBLE):
        self.language = language
        self.style = style
    
    def compose_interpretation(self, scoring_results: List[ScoringResult], 
                             conflicts: List[Conflict], mode: OutputMode,
                             chart_data: Dict[str, Any] = None) -> ComposedInterpretation:
        """Compose complete interpretation from scoring results"""
        
        # Filter and sort results by priority
        main_results = [r for r in scoring_results if r.interpretation_priority == "main"]
        strong_results = [r for r in scoring_results if r.interpretation_priority == "strong"]
        background_results = [r for r in scoring_results if r.interpretation_priority == "background"]
        
        # Sort by score within each priority
        main_results.sort(key=lambda x: x.total_score, reverse=True)
        strong_results.sort(key=lambda x: x.total_score, reverse=True)
        
        sections = []
        
        # Create sections based on mode
        if mode == OutputMode.NATAL:
            sections.extend(self._compose_natal_sections(main_results, strong_results, chart_data))
        elif mode == OutputMode.TIMING:
            sections.extend(self._compose_timing_sections(main_results, strong_results, chart_data))
        elif mode == OutputMode.TODAY:
            sections.extend(self._compose_today_sections(main_results, strong_results, chart_data))
        
        # Generate summary
        summary = self._generate_summary(sections, main_results)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(scoring_results, conflicts)
        
        # Generate warnings
        warnings = self._generate_warnings(conflicts, scoring_results)
        
        # Evidence summary
        evidence_summary = self._create_evidence_summary(scoring_results)
        
        return ComposedInterpretation(
            summary=summary,
            sections=sections,
            overall_confidence=overall_confidence,
            evidence_summary=evidence_summary,
            warnings=warnings,
            metadata={
                "mode": mode.value,
                "style": self.style.value,
                "language": self.language,
                "total_evidence": sum(len(r.evidence_list) for r in scoring_results),
                "conflicts_resolved": len(conflicts)
            }
        )
    
    def _compose_natal_sections(self, main_results: List[ScoringResult], 
                               strong_results: List[ScoringResult],
                               chart_data: Dict[str, Any]) -> List[InterpretationSection]:
        """Compose natal interpretation sections"""
        sections = []
        
        # Core Identity (Almuten + Lights + Angles)
        core_elements = []
        for result in main_results:
            almuten_evidence = [e for e in result.evidence_list if e.type == EvidenceType.ALMUTEN]
            lights_evidence = [e for e in result.evidence_list if e.type == EvidenceType.LIGHTS]
            angles_evidence = [e for e in result.evidence_list if e.type == EvidenceType.ANGLES]
            
            if almuten_evidence or lights_evidence or angles_evidence:
                core_elements.append(result)
        
        if core_elements:
            content = self._compose_core_identity_section(core_elements)
            sections.append(InterpretationSection(
                title="Core Identity",
                content=content,
                confidence=sum(r.confidence for r in core_elements) / len(core_elements),
                evidence_count=sum(len(r.evidence_list) for r in core_elements),
                priority="main"
            ))
        
        # Time-Lord Analysis
        time_lord_elements = []
        for result in main_results + strong_results:
            time_lord_evidence = [e for e in result.evidence_list 
                                if e.type in [EvidenceType.ZR_PERIOD, EvidenceType.PROFECTION, EvidenceType.FIRDARIA]]
            if time_lord_evidence:
                time_lord_elements.append(result)
        
        if time_lord_elements:
            content = self._compose_time_lord_section(time_lord_elements)
            sections.append(InterpretationSection(
                title="Current Life Phase",
                content=content,
                confidence=sum(r.confidence for r in time_lord_elements) / len(time_lord_elements),
                evidence_count=sum(len(r.evidence_list) for r in time_lord_elements),
                priority="main" if any(r.interpretation_priority == "main" for r in time_lord_elements) else "strong"
            ))
        
        # Essential Nature (Dignities + Aspects)
        dignity_elements = []
        for result in main_results + strong_results:
            dignity_evidence = [e for e in result.evidence_list 
                              if e.type in [EvidenceType.DIGNITY, EvidenceType.ASPECT]]
            if dignity_evidence:
                dignity_elements.append(result)
        
        if dignity_elements:
            content = self._compose_dignity_section(dignity_elements)
            sections.append(InterpretationSection(
                title="Essential Nature",
                content=content,
                confidence=sum(r.confidence for r in dignity_elements) / len(dignity_elements),
                evidence_count=sum(len(r.evidence_list) for r in dignity_elements),
                priority="strong"
            ))
        
        return sections
    
    def _compose_timing_sections(self, main_results: List[ScoringResult], 
                                strong_results: List[ScoringResult],
                                chart_data: Dict[str, Any]) -> List[InterpretationSection]:
        """Compose timing-focused sections"""
        sections = []
        
        # Current Periods
        current_periods_content = self._compose_current_periods(main_results + strong_results)
        if current_periods_content:
            sections.append(InterpretationSection(
                title="Current Time-Lord Periods",
                content=current_periods_content,
                confidence=0.8,  # High confidence for current periods
                evidence_count=len([r for r in main_results + strong_results 
                                  if any(e.type in [EvidenceType.ZR_PERIOD, EvidenceType.PROFECTION, EvidenceType.FIRDARIA] 
                                        for e in r.evidence_list)]),
                priority="main"
            ))
        
        return sections
    
    def _compose_today_sections(self, main_results: List[ScoringResult], 
                               strong_results: List[ScoringResult],
                               chart_data: Dict[str, Any]) -> List[InterpretationSection]:
        """Compose today-focused sections"""
        sections = []
        
        # Today's Influences
        today_content = self._compose_daily_influences(main_results + strong_results)
        if today_content:
            sections.append(InterpretationSection(
                title="Today's Astrological Weather",
                content=today_content,
                confidence=0.7,  # Moderate confidence for daily
                evidence_count=len(main_results + strong_results),
                priority="main"
            ))
        
        return sections
    
    def _compose_core_identity_section(self, core_elements: List[ScoringResult]) -> str:
        """Compose core identity section"""
        content_parts = []
        
        for result in core_elements:
            almuten_evidence = [e for e in result.evidence_list if e.type == EvidenceType.ALMUTEN]
            
            if almuten_evidence:
                evidence = almuten_evidence[0]
                planet = evidence.source_data.get("planet", "")
                
                if planet:
                    template = random.choice(self.TEMPLATES[EvidenceType.ALMUTEN]["intro"])
                    intro = template.format(planet=planet)
                    
                    qualities = self.PLANET_QUALITIES.get(planet, ["unique qualities"])
                    meaning_template = random.choice(self.TEMPLATES[EvidenceType.ALMUTEN]["meaning"])
                    meaning = meaning_template.format(planet_qualities=", ".join(qualities[:3]))
                    
                    content_parts.append(f"{intro}. {meaning}")
        
        return " ".join(content_parts) if content_parts else "Core identity analysis requires more data."
    
    def _compose_time_lord_section(self, time_lord_elements: List[ScoringResult]) -> str:
        """Compose time-lord section"""
        content_parts = []
        
        for result in time_lord_elements:
            for evidence in result.evidence_list:
                if evidence.type == EvidenceType.ZR_PERIOD:
                    lord = evidence.source_data.get("lord", "")
                    is_peak = evidence.source_data.get("is_peak", False)
                    is_lb = evidence.source_data.get("is_lb", False)
                    
                    template = random.choice(self.TEMPLATES[EvidenceType.ZR_PERIOD]["intro"])
                    intro = template.format(lord=lord, sign="")  # Sign would need to be passed
                    
                    meaning_template = random.choice(self.TEMPLATES[EvidenceType.ZR_PERIOD]["meaning"])
                    lord_themes = ", ".join(self.PLANET_QUALITIES.get(lord, ["unique themes"])[:2])
                    meaning = meaning_template.format(lord_themes=lord_themes)
                    
                    content_parts.append(f"{intro}. {meaning}")
                    
                    if is_peak:
                        peak_text = random.choice(self.TEMPLATES[EvidenceType.ZR_PERIOD]["peak"])
                        content_parts.append(peak_text)
                    
                    if is_lb:
                        lb_text = random.choice(self.TEMPLATES[EvidenceType.ZR_PERIOD]["lb"])
                        content_parts.append(lb_text)
                
                elif evidence.type == EvidenceType.PROFECTION:
                    age = evidence.source_data.get("age", 0)
                    house = evidence.source_data.get("house", 1)
                    lord = evidence.source_data.get("lord", "")
                    
                    template = random.choice(self.TEMPLATES[EvidenceType.PROFECTION]["intro"])
                    intro = template.format(age=age, house=house, lord=lord)
                    
                    house_themes = ", ".join(self.HOUSE_THEMES.get(house, ["life themes"])[:2])
                    meaning_template = random.choice(self.TEMPLATES[EvidenceType.PROFECTION]["meaning"])
                    meaning = meaning_template.format(house_themes=house_themes)
                    
                    content_parts.append(f"{intro}. {meaning}")
        
        return " ".join(content_parts) if content_parts else "Time-lord analysis requires more data."
    
    def _compose_dignity_section(self, dignity_elements: List[ScoringResult]) -> str:
        """Compose dignity and aspect section"""
        content_parts = []
        
        for result in dignity_elements:
            for evidence in result.evidence_list:
                if evidence.type == EvidenceType.DIGNITY:
                    planet = evidence.source_data.get("planet", "")
                    sign = evidence.source_data.get("sign", "")
                    dignity_type = evidence.source_data.get("dignity_type", "")
                    
                    if dignity_type in ["rulership", "exaltation"]:
                        template = random.choice(self.TEMPLATES[EvidenceType.DIGNITY]["strong"])
                    else:
                        template = random.choice(self.TEMPLATES[EvidenceType.DIGNITY]["weak"])
                    
                    content_parts.append(template.format(planet=planet, sign=sign))
                
                elif evidence.type == EvidenceType.ASPECT:
                    planet1 = evidence.source_data.get("planet1", "")
                    planet2 = evidence.source_data.get("planet2", "")
                    aspect_type = evidence.source_data.get("aspect_type", "")
                    
                    if aspect_type in ["trine", "sextile"]:
                        template = random.choice(self.TEMPLATES[EvidenceType.ASPECT]["harmonious"])
                    else:
                        template = random.choice(self.TEMPLATES[EvidenceType.ASPECT]["challenging"])
                    
                    content_parts.append(template.format(
                        planet1=planet1, planet2=planet2, aspect=aspect_type
                    ))
        
        return " ".join(content_parts) if content_parts else "Essential nature analysis requires more data."
    
    def _compose_current_periods(self, results: List[ScoringResult]) -> str:
        """Compose current periods content"""
        # This would be similar to time_lord_section but focused on current timing
        return self._compose_time_lord_section(results)
    
    def _compose_daily_influences(self, results: List[ScoringResult]) -> str:
        """Compose daily influences content"""
        content_parts = ["Today's astrological influences suggest:"]
        
        # This would analyze transit and progression evidence
        # For now, provide a template
        content_parts.append("Focus on current time-lord themes and be mindful of planetary dignities.")
        
        return " ".join(content_parts)
    
    def _generate_summary(self, sections: List[InterpretationSection], 
                         main_results: List[ScoringResult]) -> str:
        """Generate interpretation summary"""
        if not sections:
            return "Interpretation requires more astrological data."
        
        # Take key points from highest-confidence sections
        key_points = []
        for section in sorted(sections, key=lambda x: x.confidence, reverse=True)[:2]:
            # Extract first sentence as key point
            first_sentence = section.content.split('.')[0] + '.'
            key_points.append(first_sentence)
        
        summary = "**Astrological Summary:** " + " ".join(key_points)
        return summary
    
    def _calculate_overall_confidence(self, scoring_results: List[ScoringResult], 
                                    conflicts: List[Conflict]) -> float:
        """Calculate overall interpretation confidence"""
        if not scoring_results:
            return 0.0
        
        # Average confidence of all results
        base_confidence = sum(r.confidence for r in scoring_results) / len(scoring_results)
        
        # Penalty for conflicts
        conflict_penalty = len(conflicts) * 0.05
        
        # Bonus for multiple confirmations
        main_count = len([r for r in scoring_results if r.interpretation_priority == "main"])
        confirmation_bonus = min(main_count * 0.1, 0.3)
        
        final_confidence = max(0.0, min(1.0, base_confidence - conflict_penalty + confirmation_bonus))
        return final_confidence
    
    def _generate_warnings(self, conflicts: List[Conflict], 
                          scoring_results: List[ScoringResult]) -> List[str]:
        """Generate interpretation warnings"""
        warnings = []
        
        # Conflict warnings
        if len(conflicts) > 3:
            warnings.append("Multiple conflicting indications found - interpretation confidence reduced")
        
        # Generational planet warnings
        generational_main = [r for r in scoring_results 
                           if r.interpretation_priority == "main" and 
                           any(self._is_generational_planet(e.source_data.get("planet", "")) 
                               for e in r.evidence_list)]
        
        if generational_main:
            warnings.append("Some indications involve generational planets - consider collective rather than personal influence")
        
        # Low evidence warnings
        low_evidence = [r for r in scoring_results if len(r.evidence_list) < 2]
        if len(low_evidence) > len(scoring_results) * 0.5:
            warnings.append("Some interpretations based on limited evidence - consider additional factors")
        
        return warnings
    
    def _create_evidence_summary(self, scoring_results: List[ScoringResult]) -> Dict[str, Any]:
        """Create evidence summary"""
        evidence_types = {}
        total_evidence = 0
        
        for result in scoring_results:
            for evidence in result.evidence_list:
                evidence_type = evidence.type.value
                if evidence_type not in evidence_types:
                    evidence_types[evidence_type] = 0
                evidence_types[evidence_type] += 1
                total_evidence += 1
        
        return {
            "total_evidence": total_evidence,
            "by_type": evidence_types,
            "main_elements": len([r for r in scoring_results if r.interpretation_priority == "main"]),
            "strong_elements": len([r for r in scoring_results if r.interpretation_priority == "strong"]),
            "background_elements": len([r for r in scoring_results if r.interpretation_priority == "background"])
        }
    
    def _is_generational_planet(self, planet: str) -> bool:
        """Check if planet is generational"""
        return planet in ["Uranus", "Neptune", "Pluto"]