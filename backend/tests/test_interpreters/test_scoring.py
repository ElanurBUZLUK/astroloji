"""
Tests for scoring system
"""
import pytest
from app.interpreters.scoring import AstroScorer, Evidence, EvidenceType

def test_astro_scorer_initialization():
    """Test scorer initialization"""
    scorer = AstroScorer()
    assert scorer is not None
    assert len(scorer.BASE_SCORES) > 0
    assert len(scorer.THRESHOLDS) == 4

def test_score_dignity():
    """Test dignity scoring"""
    scorer = AstroScorer()
    
    # Test rulership
    evidence = scorer.score_dignity("Mars", "Aries", "rulership", is_day_birth=True)
    assert evidence.type == EvidenceType.DIGNITY
    assert evidence.multipliers["dignity"] == 1.3  # Rulership multiplier
    assert evidence.final_score > evidence.base_score
    
    # Test exaltation
    evidence = scorer.score_dignity("Sun", "Aries", "exaltation", is_day_birth=True)
    assert evidence.multipliers["dignity"] == 1.15  # Exaltation multiplier
    assert evidence.multipliers["sect"] == 1.2  # Day birth, Sun is diurnal
    
    # Test detriment
    evidence = scorer.score_dignity("Venus", "Aries", "detriment", is_day_birth=True)
    assert evidence.multipliers["dignity"] == 0.85  # Detriment penalty

def test_score_aspect():
    """Test aspect scoring"""
    scorer = AstroScorer()
    
    # Test tight orb, applying aspect
    evidence = scorer.score_aspect("Sun", "Moon", "conjunction", orb=1.5, is_applying=True)
    assert evidence.type == EvidenceType.ASPECT
    assert evidence.multipliers["orb"] == 1.25  # Tight orb bonus
    assert evidence.multipliers["applying"] == 1.1  # Applying bonus
    assert evidence.orb == 1.5
    assert evidence.is_applying == True

def test_score_almuten():
    """Test Almuten scoring"""
    scorer = AstroScorer()
    
    # Test winner
    evidence = scorer.score_almuten("Mercury", 15, is_winner=True)
    assert evidence.type == EvidenceType.ALMUTEN
    assert evidence.multipliers["almuten_status"] == 1.0  # Winner gets full score
    
    # Test non-winner
    evidence = scorer.score_almuten("Venus", 8, is_winner=False)
    assert evidence.multipliers["almuten_status"] < 1.0  # Proportional score

def test_score_time_lord():
    """Test time-lord scoring"""
    scorer = AstroScorer()
    
    # Test ZR L1 period
    evidence = scorer.score_time_lord("Sun", "zr", "L1", is_peak=True)
    assert evidence.type == EvidenceType.ZR_PERIOD
    assert evidence.multipliers["zr_level"] == 1.3  # L1 bonus
    assert evidence.multipliers["peak"] == 1.1  # Peak bonus
    
    # Test Profection
    evidence = scorer.score_time_lord("Mars", "profection", "annual")
    assert evidence.type == EvidenceType.PROFECTION
    assert evidence.multipliers["profection"] == 1.2

def test_score_antiscia():
    """Test antiscia scoring"""
    scorer = AstroScorer()
    
    evidence = scorer.score_antiscia("Sun", "Moon", "antiscia", orb=0.3)
    assert evidence.type == EvidenceType.ANTISCIA
    assert evidence.multipliers["orb"] == 1.25  # Very tight orb
    assert evidence.orb == 0.3

def test_score_midpoint():
    """Test midpoint scoring"""
    scorer = AstroScorer()
    
    # Test Sun/Moon midpoint
    evidence = scorer.score_midpoint(["Sun", "Moon"], "Mercury", orb=0.8)
    assert evidence.type == EvidenceType.MIDPOINT
    assert evidence.multipliers["midpoint_type"] == 1.25  # Sun/Moon special bonus
    assert evidence.multipliers["orb"] == 1.2  # Tight orb

def test_calculate_element_score():
    """Test element score calculation"""
    scorer = AstroScorer()
    
    # Create multiple evidence pieces
    evidence_list = [
        scorer.score_dignity("Mars", "Aries", "rulership", True),
        scorer.score_aspect("Mars", "Sun", "trine", 2.0, True),
        scorer.score_almuten("Mars", 10, False)
    ]
    
    result = scorer.calculate_element_score(evidence_list)
    
    assert result.element == "Mars"  # Should extract from first evidence
    assert result.total_score > 0
    assert len(result.evidence_list) == 3
    assert result.confidence > 0
    assert result.interpretation_priority in ["main", "strong", "background", "drop"]

def test_multiple_confirmations_bonus():
    """Test multiple confirmations bonus"""
    scorer = AstroScorer()
    
    # Create 3+ evidence pieces
    evidence_list = [
        scorer.score_dignity("Jupiter", "Sagittarius", "rulership", True),
        scorer.score_aspect("Jupiter", "Sun", "trine", 1.0, True),
        scorer.score_time_lord("Jupiter", "firdaria", "major"),
        scorer.score_antiscia("Jupiter", "Moon", "antiscia", 0.5)
    ]
    
    result = scorer.calculate_element_score(evidence_list)
    
    # Should get 20% bonus for 3+ confirmations
    base_total = sum(e.final_score for e in evidence_list)
    expected_total = base_total * 1.2
    
    assert abs(result.total_score - expected_total) < 0.01

def test_priority_thresholds():
    """Test priority threshold assignment"""
    scorer = AstroScorer()
    
    # Create high-scoring evidence
    high_evidence = [
        scorer.score_almuten("Sun", 20, True),  # High base score
        scorer.score_time_lord("Sun", "zr", "L1", True, False)  # More high scores
    ]
    
    result = scorer.calculate_element_score(high_evidence)
    
    # Should be "main" priority if score >= 7.5
    if result.total_score >= 7.5:
        assert result.interpretation_priority == "main"
    elif result.total_score >= 6.0:
        assert result.interpretation_priority == "strong"
    elif result.total_score >= 4.5:
        assert result.interpretation_priority == "background"
    else:
        assert result.interpretation_priority == "drop"

def test_generational_flag():
    """Test generational planet flagging"""
    scorer = AstroScorer()
    
    assert scorer.flag_generational("Uranus") == True
    assert scorer.flag_generational("Neptune") == True
    assert scorer.flag_generational("Pluto") == True
    assert scorer.flag_generational("Sun") == False
    assert scorer.flag_generational("Mars") == False

def test_scoring_summary():
    """Test scoring summary generation"""
    scorer = AstroScorer()
    
    # Create various scoring results
    results = [
        scorer.calculate_element_score([scorer.score_almuten("Sun", 15, True)]),
        scorer.calculate_element_score([scorer.score_dignity("Moon", "Cancer", "rulership", False)]),
        scorer.calculate_element_score([scorer.score_aspect("Mercury", "Venus", "sextile", 3.0, True)])
    ]
    
    # Set element names
    results[0].element = "Sun"
    results[1].element = "Moon"
    results[2].element = "Mercury"
    
    summary = scorer.get_scoring_summary(results)
    
    assert "total_elements" in summary
    assert "by_priority" in summary
    assert "highest_score" in summary
    assert "average_confidence" in summary
    assert summary["total_elements"] == 3