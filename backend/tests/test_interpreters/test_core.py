"""
Tests for core interpretation engine
"""
import pytest
from app.interpreters.core import InterpretationEngine
from app.interpreters.output_composer import OutputMode, OutputStyle

def test_interpretation_engine_initialization():
    """Test interpretation engine initialization"""
    engine = InterpretationEngine()
    assert engine.scorer is not None
    assert engine.conflict_resolver is not None
    assert engine.output_composer is not None

def test_extract_evidence():
    """Test evidence extraction from chart data"""
    engine = InterpretationEngine()
    
    chart_data = {
        "almuten": {
            "winner": "Mercury",
            "scores": {"Sun": 8, "Moon": 6, "Mercury": 12, "Venus": 7}
        },
        "planets": {
            "Sun": {"sign": "Gemini"},
            "Moon": {"sign": "Scorpio"}
        },
        "zodiacal_releasing": {
            "current_periods": {
                "l1": {
                    "ruler": "Sun",
                    "is_peak": True,
                    "is_lb": False
                }
            }
        },
        "profection": {
            "year_lord": "Mars"
        },
        "is_day_birth": True
    }
    
    evidence_list = engine._extract_evidence(chart_data)
    
    assert len(evidence_list) > 0
    
    # Should have almuten evidence
    almuten_evidence = [e for e in evidence_list if e.type.value == "almuten"]
    assert len(almuten_evidence) > 0
    
    # Should have dignity evidence
    dignity_evidence = [e for e in evidence_list if e.type.value == "dignity"]
    assert len(dignity_evidence) > 0
    
    # Should have ZR evidence
    zr_evidence = [e for e in evidence_list if e.type.value == "zr_period"]
    assert len(zr_evidence) > 0

def test_group_evidence_by_element():
    """Test evidence grouping by element"""
    engine = InterpretationEngine()
    
    # Create mock evidence with different elements
    evidence_list = [
        engine.scorer.score_almuten("Sun", 15, True),
        engine.scorer.score_dignity("Sun", "Leo", "rulership", True),
        engine.scorer.score_almuten("Moon", 8, False),
        engine.scorer.score_time_lord("Mars", "profection", "annual")
    ]
    
    element_groups = engine._group_evidence_by_element(evidence_list)
    
    assert "Sun" in element_groups
    assert "Moon" in element_groups
    assert "Mars" in element_groups
    
    # Sun should have 2 pieces of evidence
    assert len(element_groups["Sun"]) == 2
    assert len(element_groups["Moon"]) == 1
    assert len(element_groups["Mars"]) == 1

def test_get_primary_element():
    """Test primary element extraction from evidence"""
    engine = InterpretationEngine()
    
    # Test planet evidence
    evidence = engine.scorer.score_dignity("Venus", "Taurus", "rulership", True)
    element = engine._get_primary_element(evidence)
    assert element == "Venus"
    
    # Test time-lord evidence
    evidence = engine.scorer.score_time_lord("Jupiter", "firdaria", "major")
    element = engine._get_primary_element(evidence)
    assert element == "Jupiter"
    
    # Test aspect evidence
    evidence = engine.scorer.score_aspect("Mars", "Saturn", "square", 2.0, True)
    element = engine._get_primary_element(evidence)
    assert element == "Mars"  # Should get first planet

def test_interpret_chart():
    """Test complete chart interpretation"""
    engine = InterpretationEngine()
    
    chart_data = {
        "almuten": {
            "winner": "Mercury",
            "scores": {"Sun": 8, "Moon": 6, "Mercury": 12, "Venus": 7, "Mars": 5, "Jupiter": 9, "Saturn": 10}
        },
        "planets": {
            "Sun": {"sign": "Gemini"},
            "Moon": {"sign": "Scorpio"},
            "Mercury": {"sign": "Gemini"}
        },
        "zodiacal_releasing": {
            "current_periods": {
                "l1": {
                    "ruler": "Sun",
                    "is_peak": True,
                    "is_lb": False
                },
                "l2": {
                    "ruler": "Mercury",
                    "is_peak": False,
                    "is_lb": False
                }
            }
        },
        "profection": {
            "year_lord": "Saturn"
        },
        "firdaria": {
            "current_major": {"lord": "Jupiter"},
            "current_minor": {"lord": "Venus"}
        },
        "antiscia": {
            "strongest_contacts": [
                {
                    "original_planet": "Sun",
                    "contacted_planet": "Moon",
                    "antiscia_type": "antiscia",
                    "orb": 0.8
                }
            ]
        },
        "is_day_birth": True
    }
    
    interpretation = engine.interpret_chart(chart_data, OutputMode.NATAL)
    
    assert interpretation is not None
    assert interpretation.summary is not None
    assert len(interpretation.sections) > 0
    assert 0 <= interpretation.overall_confidence <= 1
    assert interpretation.evidence_summary is not None
    assert isinstance(interpretation.warnings, list)
    assert interpretation.metadata is not None

def test_get_interpretation_summary():
    """Test interpretation summary generation"""
    engine = InterpretationEngine()
    
    chart_data = {
        "almuten": {
            "winner": "Mercury",
            "scores": {"Mercury": 12, "Sun": 8, "Jupiter": 9}
        },
        "planets": {
            "Mercury": {"sign": "Gemini"},
            "Sun": {"sign": "Gemini"}
        },
        "is_day_birth": True
    }
    
    summary = engine.get_interpretation_summary(chart_data)
    
    assert "main_themes" in summary
    assert "supporting_themes" in summary
    assert "overall_confidence" in summary
    assert "total_evidence" in summary
    assert "conflicts_found" in summary
    assert "scoring_summary" in summary
    
    assert isinstance(summary["main_themes"], list)
    assert isinstance(summary["supporting_themes"], list)
    assert 0 <= summary["overall_confidence"] <= 1

def test_interpret_specific_element():
    """Test specific element interpretation"""
    engine = InterpretationEngine()
    
    chart_data = {
        "almuten": {
            "winner": "Mercury",
            "scores": {"Mercury": 12, "Sun": 8}
        },
        "planets": {
            "Mercury": {"sign": "Gemini"}
        },
        "profection": {
            "year_lord": "Mercury"
        },
        "is_day_birth": True
    }
    
    # Test existing element
    result = engine.interpret_specific_element(chart_data, "Mercury")
    
    assert "element" in result
    assert result["element"] == "Mercury"
    assert "total_score" in result
    assert "confidence" in result
    assert "priority" in result
    assert "evidence_count" in result
    assert "evidence_details" in result
    assert "conflicts" in result
    
    # Test non-existing element
    result = engine.interpret_specific_element(chart_data, "NonExistent")
    assert "error" in result

def test_different_output_modes():
    """Test different output modes"""
    engine = InterpretationEngine()
    
    chart_data = {
        "almuten": {"winner": "Sun", "scores": {"Sun": 15}},
        "planets": {"Sun": {"sign": "Leo"}},
        "is_day_birth": True
    }
    
    # Test natal mode
    natal_interpretation = engine.interpret_chart(chart_data, OutputMode.NATAL)
    assert natal_interpretation.metadata["mode"] == "natal"
    
    # Test timing mode
    timing_interpretation = engine.interpret_chart(chart_data, OutputMode.TIMING)
    assert timing_interpretation.metadata["mode"] == "timing"
    
    # Test today mode
    today_interpretation = engine.interpret_chart(chart_data, OutputMode.TODAY)
    assert today_interpretation.metadata["mode"] == "today"

def test_language_and_style_options():
    """Test different language and style options"""
    # Test English
    engine_en = InterpretationEngine(language="en", style=OutputStyle.ACCESSIBLE)
    assert engine_en.output_composer.language == "en"
    assert engine_en.output_composer.style == OutputStyle.ACCESSIBLE
    
    # Test Turkish
    engine_tr = InterpretationEngine(language="tr", style=OutputStyle.TECHNICAL)
    assert engine_tr.output_composer.language == "tr"
    assert engine_tr.output_composer.style == OutputStyle.TECHNICAL