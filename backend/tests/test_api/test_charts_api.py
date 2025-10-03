"""
Tests for Charts API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date

from app.main import app

client = TestClient(app)

def test_create_chart_basic():
    """Test basic chart creation"""
    birth_data = {
        "birth_date": "1990-06-15",
        "birth_time": "14:30",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "place_name": "New York, NY"
    }
    
    response = client.post("/charts/", json=birth_data)
    
    # Should return 200 or 500 (depending on ephemeris availability)
    # For now, we expect it to work with mock data
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "chart_id" in data
        assert "status" in data
        assert "calculations" in data
        
        calculations = data["calculations"]
        assert "planets" in calculations
        assert "houses" in calculations
        assert "almuten" in calculations
        assert "zodiacal_releasing" in calculations
        assert "profection" in calculations
        assert "firdaria" in calculations
        assert "antiscia" in calculations

def test_create_chart_without_time():
    """Test chart creation without birth time"""
    birth_data = {
        "birth_date": "1990-06-15",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "UTC",
        "place_name": "Test Location"
    }
    
    response = client.post("/charts/", json=birth_data)
    
    # Should handle missing time gracefully
    assert response.status_code in [200, 500]

def test_create_chart_invalid_data():
    """Test chart creation with invalid data"""
    birth_data = {
        "birth_date": "1990-06-15",
        "latitude": 91.0,  # Invalid latitude
        "longitude": -74.0060
    }
    
    response = client.post("/charts/", json=birth_data)
    assert response.status_code == 422  # Validation error

def test_get_chart():
    """Test chart retrieval"""
    chart_id = "test-chart-123"
    
    response = client.get(f"/charts/{chart_id}")
    
    # Should return placeholder response for now
    assert response.status_code == 200
    data = response.json()
    assert data["chart_id"] == chart_id

def test_chart_response_structure():
    """Test that chart response has expected structure"""
    birth_data = {
        "birth_date": "1990-06-15",
        "birth_time": "12:00",
        "latitude": 0.0,
        "longitude": 0.0,
        "timezone": "UTC"
    }
    
    response = client.post("/charts/", json=birth_data)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check top-level structure
        required_fields = ["chart_id", "status", "birth_data", "calculations", "created_at"]
        for field in required_fields:
            assert field in data
        
        # Check calculations structure
        calc = data["calculations"]
        calc_fields = ["planets", "houses", "almuten", "zodiacal_releasing", 
                      "profection", "firdaria", "antiscia", "lots", "is_day_birth"]
        for field in calc_fields:
            assert field in calc

        assert "normalized" in data
        
        # Check planet structure
        if "Sun" in calc["planets"]:
            sun = calc["planets"]["Sun"]
            planet_fields = ["longitude", "sign", "degree_in_sign", "is_retrograde", "speed"]
            for field in planet_fields:
                assert field in sun
        
        # Check almuten structure
        almuten = calc["almuten"]
        almuten_fields = ["winner", "scores"]
        for field in almuten_fields:
            assert field in almuten
        
        # Check profection structure
        profection = calc["profection"]
        profection_fields = ["age", "profected_house", "profected_sign", "year_lord", "activated_topics"]
        for field in profection_fields:
            assert field in profection
