"""
Tests for Fixed Stars calculator
"""
import pytest
from app.calculators.fixed_stars import FixedStarsCalculator

def test_fixed_stars_calculator_initialization():
    """Test fixed stars calculator initialization"""
    calc = FixedStarsCalculator()
    assert calc is not None
    assert calc.orb == 1.0
    
    calc_custom = FixedStarsCalculator(orb=0.5)
    assert calc_custom.orb == 0.5

def test_fixed_star_data():
    """Test fixed star data integrity"""
    calc = FixedStarsCalculator()
    
    # Check that we have the royal stars
    royal_stars = ["Aldebaran", "Regulus", "Antares", "Fomalhaut"]
    for star_name in royal_stars:
        assert star_name in calc.FIXED_STARS
        assert calc.FIXED_STARS[star_name]["is_royal"] == True
    
    # Check that all stars have required fields
    for star_name, star_data in calc.FIXED_STARS.items():
        assert "longitude" in star_data
        assert "magnitude" in star_data
        assert "nature" in star_data
        assert "keywords" in star_data
        assert "is_royal" in star_data
        assert isinstance(star_data["keywords"], list)
        assert len(star_data["keywords"]) > 0

def test_star_objects_creation():
    """Test creation of FixedStar objects"""
    calc = FixedStarsCalculator()
    
    stars = calc.create_fixed_star_objects()
    
    assert len(stars) == len(calc.FIXED_STARS)
    
    # Check that royal stars are properly marked
    royal_stars = [star for star in stars if star.is_royal]
    assert len(royal_stars) == 4  # Four royal stars
    
    # Check Regulus specifically
    regulus = next((star for star in stars if star.name == "Regulus"), None)
    assert regulus is not None
    assert regulus.is_royal == True
    assert "Leadership" in regulus.keywords

def test_star_contacts_detection():
    """Test detection of star contacts"""
    calc = FixedStarsCalculator(orb=1.0)
    
    # Position a planet near Regulus (~29° Leo)
    planet_positions = {
        "Sun": 149.0,  # Close to Regulus at 149.59°
        "Moon": 69.0   # Close to Aldebaran at 69.47°
    }
    
    result = calc.calculate_fixed_stars(planet_positions)
    
    # Should find contacts
    assert len(result.star_contacts) > 0
    
    # Should find royal star contacts
    assert len(result.royal_star_contacts) > 0
    
    # Check that contacts are sorted by orb
    for i in range(1, len(result.star_contacts)):
        assert result.star_contacts[i-1].orb <= result.star_contacts[i].orb

def test_regulus_contact():
    """Test specific contact with Regulus"""
    calc = FixedStarsCalculator(orb=1.0)
    
    # Place Sun exactly on Regulus
    planet_positions = {
        "Sun": 149.59  # Regulus longitude
    }
    
    result = calc.calculate_fixed_stars(planet_positions)
    
    # Should find Sun conjunct Regulus
    regulus_contacts = [
        contact for contact in result.star_contacts 
        if contact.star.name == "Regulus" and contact.planet == "Sun"
    ]
    
    assert len(regulus_contacts) > 0
    regulus_contact = regulus_contacts[0]
    assert regulus_contact.contact_type == "conjunction"
    assert regulus_contact.orb < 0.1  # Very tight orb

def test_opposition_contacts():
    """Test opposition contacts to fixed stars"""
    calc = FixedStarsCalculator(orb=1.0)
    
    # Place planet opposite to Regulus
    regulus_longitude = 149.59
    opposite_longitude = (regulus_longitude + 180) % 360  # ~329.59° (Aquarius)
    
    planet_positions = {
        "Mars": opposite_longitude
    }
    
    result = calc.calculate_fixed_stars(planet_positions)
    
    # Should find Mars opposite Regulus
    regulus_oppositions = [
        contact for contact in result.star_contacts 
        if contact.star.name == "Regulus" and contact.contact_type == "opposition"
    ]
    
    assert len(regulus_oppositions) > 0

def test_star_contacts_summary():
    """Test star contacts summary generation"""
    calc = FixedStarsCalculator()
    
    planet_positions = {
        "Sun": 149.5,  # Near Regulus
        "Moon": 69.5,  # Near Aldebaran
        "Mars": 249.5  # Near Antares
    }
    
    summary = calc.get_star_contacts_summary(planet_positions)
    
    assert "royal_star_contacts" in summary
    assert "major_star_contacts" in summary
    assert "all_contacts" in summary
    assert "diagnostics" in summary
    
    # Should have royal star contacts
    assert len(summary["royal_star_contacts"]) > 0
    
    # Check structure of royal star contacts
    for contact in summary["royal_star_contacts"]:
        assert "star_name" in contact
        assert "planet" in contact
        assert "contact_type" in contact
        assert "orb" in contact
        assert "star_nature" in contact
        assert "keywords" in contact

def test_star_lookup_by_longitude():
    """Test finding star by longitude"""
    calc = FixedStarsCalculator()
    
    # Look for star near Regulus position
    star = calc.get_star_by_longitude(149.5, orb=1.0)
    
    assert star is not None
    assert star.name == "Regulus"
    assert star.is_royal == True

def test_compute_interface():
    """Test standard compute interface"""
    calc = FixedStarsCalculator()
    
    chart_data = {
        "planets": {
            "Sun": 149.5,  # Near Regulus
            "Moon": 69.5   # Near Aldebaran
        }
    }
    
    result = calc.compute(chart_data)
    
    assert "features" in result
    assert "evidence" in result
    assert "diagnostics" in result
    
    # Should have evidence for royal star contacts
    royal_evidence = [
        ev for ev in result["evidence"] 
        if ev["type"] == "FIXED_STAR" and ev.get("is_royal", False)
    ]
    assert len(royal_evidence) > 0

def test_bright_stars_filtering():
    """Test filtering for bright stars"""
    calc = FixedStarsCalculator()
    
    # Get all stars and check magnitude filtering
    stars = calc.create_fixed_star_objects()
    bright_stars = [star for star in stars if star.magnitude <= 1.5]
    
    # Should have several bright stars
    assert len(bright_stars) > 5
    
    # Sirius should be the brightest
    sirius = next((star for star in stars if star.name == "Sirius"), None)
    assert sirius is not None
    assert sirius.magnitude < 0  # Negative magnitude = very bright

def test_orb_calculation():
    """Test orb calculation between positions"""
    calc = FixedStarsCalculator()
    
    # Test cases for orb calculation
    test_cases = [
        (0.0, 1.0, 1.0),      # Simple case
        (0.0, 359.0, 1.0),    # Across 0° boundary
        (180.0, 181.0, 1.0),  # Simple case
        (10.0, 350.0, 20.0),  # Across boundary
        (0.0, 180.0, 180.0),  # Opposition
    ]
    
    for pos1, pos2, expected_orb in test_cases:
        orb = calc.calculate_orb(pos1, pos2)
        assert abs(orb - expected_orb) < 0.1, f"Failed for {pos1}° and {pos2}°: expected {expected_orb}°, got {orb}°"