"""
Conflict resolution system for astrological interpretations
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .scoring import Evidence, ScoringResult, EvidenceType

class ConflictType(Enum):
    """Types of conflicts in astrological interpretation"""
    CONTRADICTORY_DIGNITIES = "contradictory_dignities"
    OPPOSING_ASPECTS = "opposing_aspects"
    TIME_LORD_MISMATCH = "time_lord_mismatch"
    SECT_CONFLICT = "sect_conflict"
    GENERATIONAL_OVERRIDE = "generational_override"
    ORBING_CONFLICT = "orbing_conflict"

@dataclass
class Conflict:
    """Represents a conflict between pieces of evidence"""
    type: ConflictType
    description: str
    evidence_a: Evidence
    evidence_b: Evidence
    resolution: str
    winner: Evidence
    confidence_impact: float  # How much this affects overall confidence

class ConflictResolver:
    """Resolves conflicts in astrological interpretation according to traditional hierarchy"""
    
    # Hierarchy rules from spec
    HIERARCHY_RULES = {
        # Primary hierarchy: Almuten+Lights+Angles > rulers > others
        "primary": [
            EvidenceType.ALMUTEN,
            EvidenceType.LIGHTS,
            EvidenceType.ANGLES,
            EvidenceType.HOUSE_RULER,
            EvidenceType.DIGNITY,
            EvidenceType.ASPECT
        ],
        
        # Time-lord hierarchy: ZR/Profection/Firdaria alignment > single transit
        "time_lords": [
            EvidenceType.ZR_PERIOD,
            EvidenceType.PROFECTION,
            EvidenceType.FIRDARIA,
            EvidenceType.PROGRESSION,
            EvidenceType.SOLAR_ARC,
            EvidenceType.TRANSIT,
            EvidenceType.RETURN
        ],
        
        # Aspect hierarchy: dignity+reception > raw aspect
        "aspect_quality": [
            "dignity_with_reception",
            "dignity_only",
            "reception_only",
            "raw_aspect"
        ]
    }
    
    def __init__(self):
        self.conflicts_found = []
        self.resolutions_applied = []
    
    def resolve_conflicts(self, scoring_results: List[ScoringResult]) -> Tuple[List[ScoringResult], List[Conflict]]:
        """
        Resolve conflicts between scoring results according to traditional hierarchy
        
        Returns:
            Tuple of (resolved_results, conflicts_found)
        """
        self.conflicts_found = []
        resolved_results = []
        
        for result in scoring_results:
            # Check for internal conflicts within each result
            internal_conflicts = self._find_internal_conflicts(result)
            self.conflicts_found.extend(internal_conflicts)
            
            # Apply conflict resolution
            resolved_result = self._apply_conflict_resolution(result, internal_conflicts)
            resolved_results.append(resolved_result)
        
        # Check for conflicts between results
        cross_conflicts = self._find_cross_conflicts(resolved_results)
        self.conflicts_found.extend(cross_conflicts)
        
        # Apply cross-result conflict resolution
        final_results = self._apply_cross_resolution(resolved_results, cross_conflicts)
        
        return final_results, self.conflicts_found
    
    def _find_internal_conflicts(self, result: ScoringResult) -> List[Conflict]:
        """Find conflicts within a single scoring result"""
        conflicts = []
        evidence_list = result.evidence_list
        
        for i, evidence_a in enumerate(evidence_list):
            for evidence_b in evidence_list[i+1:]:
                conflict = self._check_evidence_conflict(evidence_a, evidence_b)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_evidence_conflict(self, evidence_a: Evidence, evidence_b: Evidence) -> Optional[Conflict]:
        """Check if two pieces of evidence conflict"""
        
        # Contradictory dignities (e.g., exaltation vs fall)
        if (evidence_a.type == EvidenceType.DIGNITY and evidence_b.type == EvidenceType.DIGNITY):
            dignity_a = evidence_a.source_data.get("dignity_type", "")
            dignity_b = evidence_b.source_data.get("dignity_type", "")
            
            contradictory_pairs = [
                ("rulership", "detriment"),
                ("exaltation", "fall")
            ]
            
            for positive, negative in contradictory_pairs:
                if (dignity_a == positive and dignity_b == negative) or \
                   (dignity_a == negative and dignity_b == positive):
                    
                    winner = evidence_a if dignity_a in ["rulership", "exaltation"] else evidence_b
                    
                    return Conflict(
                        type=ConflictType.CONTRADICTORY_DIGNITIES,
                        description=f"Contradictory dignities: {dignity_a} vs {dignity_b}",
                        evidence_a=evidence_a,
                        evidence_b=evidence_b,
                        resolution="Positive dignity takes precedence",
                        winner=winner,
                        confidence_impact=-0.1
                    )
        
        # Opposing aspects (e.g., trine vs square to same planet)
        if (evidence_a.type == EvidenceType.ASPECT and evidence_b.type == EvidenceType.ASPECT):
            # Check if same planets involved but different aspect types
            planets_a = {evidence_a.source_data.get("planet1"), evidence_a.source_data.get("planet2")}
            planets_b = {evidence_b.source_data.get("planet1"), evidence_b.source_data.get("planet2")}
            
            if planets_a == planets_b:
                aspect_a = evidence_a.source_data.get("aspect_type", "")
                aspect_b = evidence_b.source_data.get("aspect_type", "")
                
                # Harmonious vs challenging aspects
                harmonious = ["trine", "sextile"]
                challenging = ["square", "opposition"]
                
                if (aspect_a in harmonious and aspect_b in challenging) or \
                   (aspect_a in challenging and aspect_b in harmonious):
                    
                    # Tighter orb wins, or challenging aspect if equal
                    if evidence_a.orb and evidence_b.orb:
                        if abs(evidence_a.orb - evidence_b.orb) < 0.5:
                            winner = evidence_a if aspect_a in challenging else evidence_b
                        else:
                            winner = evidence_a if evidence_a.orb < evidence_b.orb else evidence_b
                    else:
                        winner = evidence_a if aspect_a in challenging else evidence_b
                    
                    return Conflict(
                        type=ConflictType.OPPOSING_ASPECTS,
                        description=f"Opposing aspects: {aspect_a} vs {aspect_b}",
                        evidence_a=evidence_a,
                        evidence_b=evidence_b,
                        resolution="Tighter orb or challenging aspect takes precedence",
                        winner=winner,
                        confidence_impact=-0.15
                    )
        
        # Time-lord alignment conflicts
        time_lord_types = [EvidenceType.ZR_PERIOD, EvidenceType.PROFECTION, EvidenceType.FIRDARIA]
        if evidence_a.type in time_lord_types and evidence_b.type in time_lord_types:
            lord_a = evidence_a.source_data.get("lord", "")
            lord_b = evidence_b.source_data.get("lord", "")
            
            if lord_a != lord_b and lord_a and lord_b:
                # ZR takes precedence over others
                if evidence_a.type == EvidenceType.ZR_PERIOD:
                    winner = evidence_a
                elif evidence_b.type == EvidenceType.ZR_PERIOD:
                    winner = evidence_b
                else:
                    # Profection over Firdaria
                    winner = evidence_a if evidence_a.type == EvidenceType.PROFECTION else evidence_b
                
                return Conflict(
                    type=ConflictType.TIME_LORD_MISMATCH,
                    description=f"Time-lord mismatch: {lord_a} vs {lord_b}",
                    evidence_a=evidence_a,
                    evidence_b=evidence_b,
                    resolution="ZR > Profection > Firdaria hierarchy applied",
                    winner=winner,
                    confidence_impact=-0.05
                )
        
        return None
    
    def _find_cross_conflicts(self, results: List[ScoringResult]) -> List[Conflict]:
        """Find conflicts between different scoring results"""
        conflicts = []
        
        # Check for generational planet over-emphasis
        for result in results:
            if any(self._is_generational_planet(evidence.source_data.get("planet", "")) 
                   for evidence in result.evidence_list):
                if result.interpretation_priority == "main":
                    # Create a conflict to flag this
                    generational_evidence = next(
                        evidence for evidence in result.evidence_list 
                        if self._is_generational_planet(evidence.source_data.get("planet", ""))
                    )
                    
                    conflicts.append(Conflict(
                        type=ConflictType.GENERATIONAL_OVERRIDE,
                        description=f"Generational planet {generational_evidence.source_data.get('planet')} in main interpretation",
                        evidence_a=generational_evidence,
                        evidence_b=generational_evidence,  # Self-reference
                        resolution="Flag as generational background influence",
                        winner=generational_evidence,
                        confidence_impact=-0.2
                    ))
        
        return conflicts
    
    def _apply_conflict_resolution(self, result: ScoringResult, conflicts: List[Conflict]) -> ScoringResult:
        """Apply conflict resolution to a scoring result"""
        if not conflicts:
            return result
        
        # Adjust confidence based on conflicts
        confidence_penalty = sum(conflict.confidence_impact for conflict in conflicts)
        adjusted_confidence = max(0.0, result.confidence + confidence_penalty)
        
        # Filter evidence based on conflict resolutions
        winning_evidence = []
        losing_evidence_ids = set()
        
        for conflict in conflicts:
            if conflict.winner == conflict.evidence_a:
                losing_evidence_ids.add(id(conflict.evidence_b))
            else:
                losing_evidence_ids.add(id(conflict.evidence_a))
        
        # Keep winning evidence and non-conflicted evidence
        for evidence in result.evidence_list:
            if id(evidence) not in losing_evidence_ids:
                winning_evidence.append(evidence)
        
        # Recalculate total score
        new_total_score = sum(evidence.final_score for evidence in winning_evidence)
        
        # Determine new priority
        if new_total_score >= 7.5:
            new_priority = "main"
        elif new_total_score >= 6.0:
            new_priority = "strong"
        elif new_total_score >= 4.5:
            new_priority = "background"
        else:
            new_priority = "drop"
        
        return ScoringResult(
            element=result.element,
            total_score=new_total_score,
            evidence_list=winning_evidence,
            confidence=adjusted_confidence,
            interpretation_priority=new_priority
        )
    
    def _apply_cross_resolution(self, results: List[ScoringResult], conflicts: List[Conflict]) -> List[ScoringResult]:
        """Apply cross-result conflict resolution"""
        adjusted_results = []
        
        for result in results:
            # Check if this result is affected by cross-conflicts
            affected_conflicts = [c for c in conflicts if 
                                any(evidence.source_data.get("planet") == result.element 
                                    for evidence in [c.evidence_a, c.evidence_b])]
            
            if affected_conflicts:
                # Apply generational flagging
                generational_conflicts = [c for c in affected_conflicts 
                                        if c.type == ConflictType.GENERATIONAL_OVERRIDE]
                
                if generational_conflicts:
                    # Downgrade generational planets from main to strong
                    if result.interpretation_priority == "main":
                        new_priority = "strong"
                        confidence_penalty = -0.2
                    else:
                        new_priority = result.interpretation_priority
                        confidence_penalty = -0.1
                    
                    adjusted_result = ScoringResult(
                        element=result.element,
                        total_score=result.total_score,
                        evidence_list=result.evidence_list,
                        confidence=max(0.0, result.confidence + confidence_penalty),
                        interpretation_priority=new_priority
                    )
                    adjusted_results.append(adjusted_result)
                else:
                    adjusted_results.append(result)
            else:
                adjusted_results.append(result)
        
        return adjusted_results
    
    def _is_generational_planet(self, planet: str) -> bool:
        """Check if planet is generational"""
        return planet in ["Uranus", "Neptune", "Pluto"]
    
    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get summary of conflicts found and resolved"""
        conflict_types = {}
        for conflict in self.conflicts_found:
            conflict_type = conflict.type.value
            if conflict_type not in conflict_types:
                conflict_types[conflict_type] = 0
            conflict_types[conflict_type] += 1
        
        return {
            "total_conflicts": len(self.conflicts_found),
            "by_type": conflict_types,
            "average_confidence_impact": sum(c.confidence_impact for c in self.conflicts_found) / len(self.conflicts_found) if self.conflicts_found else 0,
            "resolutions_applied": len(self.resolutions_applied)
        }