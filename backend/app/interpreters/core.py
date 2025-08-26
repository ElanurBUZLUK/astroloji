"""
Core interpretation engine that orchestrates all interpretation components
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date

from .scoring import AstroScorer, Evidence, ScoringResult, EvidenceType
from .conflict_resolver import ConflictResolver
from .output_composer import OutputComposer, OutputMode, OutputStyle, ComposedInterpretation

class InterpretationEngine:
    """Main interpretation engine that coordinates scoring, conflict resolution, and output composition"""
    
    def __init__(self, language: str = "en", style: OutputStyle = OutputStyle.ACCESSIBLE):
        self.scorer = AstroScorer()
        self.conflict_resolver = ConflictResolver()
        self.output_composer = OutputComposer(language=language, style=style)
    
    def interpret_chart(self, chart_data: Dict[str, Any], mode: OutputMode = OutputMode.NATAL,
                       focus_topic: Optional[str] = None) -> ComposedInterpretation:
        """
        Generate complete interpretation from chart data
        
        Args:
            chart_data: Complete chart calculation results
            mode: Interpretation mode (natal, timing, today)
            focus_topic: Optional specific topic to focus on
        
        Returns:
            ComposedInterpretation with full analysis
        """
        
        # Extract evidence from chart data
        evidence_list = self._extract_evidence(chart_data)
        
        # Group evidence by chart elements (planets, houses, etc.)
        element_groups = self._group_evidence_by_element(evidence_list)
        
        # Score each element group
        scoring_results = []
        for element, evidence_group in element_groups.items():
            scoring_result = self.scorer.calculate_element_score(evidence_group)
            scoring_result.element = element  # Ensure element name is set
            scoring_results.append(scoring_result)
        
        # Resolve conflicts
        resolved_results, conflicts = self.conflict_resolver.resolve_conflicts(scoring_results)
        
        # Compose final interpretation
        interpretation = self.output_composer.compose_interpretation(
            resolved_results, conflicts, mode, chart_data
        )
        
        return interpretation
    
    def _extract_evidence(self, chart_data: Dict[str, Any]) -> List[Evidence]:
        """Extract all evidence from chart calculation results"""
        evidence_list = []
        
        # Extract Almuten evidence
        if "almuten" in chart_data:
            almuten_data = chart_data["almuten"]
            winner = almuten_data.get("winner")
            scores = almuten_data.get("scores", {})
            
            for planet, score in scores.items():
                is_winner = (planet == winner)
                evidence = self.scorer.score_almuten(planet, score, is_winner)
                evidence_list.append(evidence)
        
        # Extract planet dignity evidence
        if "planets" in chart_data:
            planets_data = chart_data["planets"]
            is_day = chart_data.get("is_day_birth", True)
            
            for planet_name, planet_info in planets_data.items():
                sign = planet_info.get("sign", "")
                
                # For now, assume basic dignity - would need dignity calculation
                # This is a simplified version
                evidence = self.scorer.score_dignity(planet_name, sign, "placement", is_day)
                evidence_list.append(evidence)
        
        # Extract ZR evidence
        if "zodiacal_releasing" in chart_data:
            zr_data = chart_data["zodiacal_releasing"]
            current_periods = zr_data.get("current_periods", {})
            
            # L1 period
            l1_period = current_periods.get("l1")
            if l1_period:
                evidence = self.scorer.score_time_lord(
                    lord=l1_period.get("ruler", ""),
                    method="zr",
                    level="L1",
                    is_peak=l1_period.get("is_peak", False),
                    is_lb=l1_period.get("is_lb", False)
                )
                evidence_list.append(evidence)
            
            # L2 period
            l2_period = current_periods.get("l2")
            if l2_period:
                evidence = self.scorer.score_time_lord(
                    lord=l2_period.get("ruler", ""),
                    method="zr",
                    level="L2",
                    is_peak=l2_period.get("is_peak", False),
                    is_lb=l2_period.get("is_lb", False)
                )
                evidence_list.append(evidence)
        
        # Extract Profection evidence
        if "profection" in chart_data:
            profection_data = chart_data["profection"]
            year_lord = profection_data.get("year_lord", "")
            
            if year_lord:
                evidence = self.scorer.score_time_lord(
                    lord=year_lord,
                    method="profection",
                    level="annual"
                )
                evidence_list.append(evidence)
        
        # Extract Firdaria evidence
        if "firdaria" in chart_data:
            firdaria_data = chart_data["firdaria"]
            current_major = firdaria_data.get("current_major", {})
            current_minor = firdaria_data.get("current_minor", {})
            
            if current_major.get("lord"):
                evidence = self.scorer.score_time_lord(
                    lord=current_major["lord"],
                    method="firdaria",
                    level="major"
                )
                evidence_list.append(evidence)
            
            if current_minor.get("lord"):
                evidence = self.scorer.score_time_lord(
                    lord=current_minor["lord"],
                    method="firdaria",
                    level="minor"
                )
                evidence_list.append(evidence)
        
        # Extract Antiscia evidence
        if "antiscia" in chart_data:
            antiscia_data = chart_data["antiscia"]
            strongest_contacts = antiscia_data.get("strongest_contacts", [])
            
            for contact in strongest_contacts:
                evidence = self.scorer.score_antiscia(
                    planet1=contact.get("original_planet", ""),
                    planet2=contact.get("contacted_planet", ""),
                    antiscia_type=contact.get("antiscia_type", ""),
                    orb=contact.get("orb", 1.0)
                )
                evidence_list.append(evidence)
        
        return evidence_list
    
    def _group_evidence_by_element(self, evidence_list: List[Evidence]) -> Dict[str, List[Evidence]]:
        """Group evidence by chart elements (planets, houses, etc.)"""
        element_groups = {}
        
        for evidence in evidence_list:
            # Determine primary element from evidence
            element = self._get_primary_element(evidence)
            
            if element not in element_groups:
                element_groups[element] = []
            element_groups[element].append(evidence)
        
        return element_groups
    
    def _get_primary_element(self, evidence: Evidence) -> str:
        """Get primary element name from evidence"""
        source_data = evidence.source_data or {}
        
        # Try to get planet name
        if "planet" in source_data:
            return source_data["planet"]
        
        # Try to get lord name (for time-lords)
        if "lord" in source_data:
            return source_data["lord"]
        
        # Try to get first planet from aspect/antiscia
        if "planet1" in source_data:
            return source_data["planet1"]
        
        # Try to get original planet from antiscia
        if "original_planet" in source_data:
            return source_data["original_planet"]
        
        # Default fallback
        return f"Element_{evidence.type.value}"
    
    def get_interpretation_summary(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a quick summary of interpretation without full composition"""
        evidence_list = self._extract_evidence(chart_data)
        element_groups = self._group_evidence_by_element(evidence_list)
        
        scoring_results = []
        for element, evidence_group in element_groups.items():
            scoring_result = self.scorer.calculate_element_score(evidence_group)
            scoring_result.element = element
            scoring_results.append(scoring_result)
        
        resolved_results, conflicts = self.conflict_resolver.resolve_conflicts(scoring_results)
        
        # Get top elements by priority
        main_elements = [r for r in resolved_results if r.interpretation_priority == "main"]
        strong_elements = [r for r in resolved_results if r.interpretation_priority == "strong"]
        
        return {
            "main_themes": [r.element for r in sorted(main_elements, key=lambda x: x.total_score, reverse=True)[:3]],
            "supporting_themes": [r.element for r in sorted(strong_elements, key=lambda x: x.total_score, reverse=True)[:3]],
            "overall_confidence": sum(r.confidence for r in resolved_results) / len(resolved_results) if resolved_results else 0,
            "total_evidence": len(evidence_list),
            "conflicts_found": len(conflicts),
            "scoring_summary": self.scorer.get_scoring_summary(resolved_results)
        }
    
    def interpret_specific_element(self, chart_data: Dict[str, Any], element: str) -> Dict[str, Any]:
        """Get detailed interpretation for a specific chart element"""
        evidence_list = self._extract_evidence(chart_data)
        element_groups = self._group_evidence_by_element(evidence_list)
        
        if element not in element_groups:
            return {"error": f"No evidence found for element: {element}"}
        
        evidence_group = element_groups[element]
        scoring_result = self.scorer.calculate_element_score(evidence_group)
        scoring_result.element = element
        
        # Check for conflicts within this element
        conflicts = self.conflict_resolver._find_internal_conflicts(scoring_result)
        resolved_result = self.conflict_resolver._apply_conflict_resolution(scoring_result, conflicts)
        
        return {
            "element": element,
            "total_score": resolved_result.total_score,
            "confidence": resolved_result.confidence,
            "priority": resolved_result.interpretation_priority,
            "evidence_count": len(resolved_result.evidence_list),
            "evidence_details": [
                {
                    "type": e.type.value,
                    "description": e.description,
                    "score": e.final_score,
                    "multipliers": e.multipliers
                }
                for e in resolved_result.evidence_list
            ],
            "conflicts": [
                {
                    "type": c.type.value,
                    "description": c.description,
                    "resolution": c.resolution
                }
                for c in conflicts
            ]
        }