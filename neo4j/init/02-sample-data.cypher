// Sample data for testing the Astro-AA graph model

// Create a sample user
CREATE (u:User {
    id: 'user-123',
    email: 'john.doe@example.com',
    username: 'johndoe',
    created_at: datetime('2025-01-01T00:00:00Z')
});

// Create a sample natal chart
CREATE (c:Chart {
    id: 'chart-456',
    user_id: 'user-123',
    name: 'John Doe - Natal Chart',
    chart_type: 'natal',
    datetime: datetime('1990-06-15T14:30:00Z'),
    location: 'New York, NY, USA',
    latitude: 40.7128,
    longitude: -74.0060,
    timezone: 'America/New_York',
    house_system: 'whole_sign',
    created_at: datetime('2025-01-01T00:00:00Z')
});

// Connect user to chart
MATCH (u:User {id: 'user-123'}), (c:Chart {id: 'chart-456'})
CREATE (u)-[:OWNS]->(c);

// Create planet positions for the sample chart
CREATE (pp1:PlanetPosition {
    chart_id: 'chart-456',
    planet: 'Sun',
    longitude: 84.5,
    latitude: 0.0,
    sign: 'Gemini',
    house: 5,
    degree: 24,
    minute: 30,
    retrograde: false
});

CREATE (pp2:PlanetPosition {
    chart_id: 'chart-456',
    planet: 'Moon',
    longitude: 156.2,
    latitude: 2.1,
    sign: 'Virgo',
    house: 8,
    degree: 6,
    minute: 12,
    retrograde: false
});

CREATE (pp3:PlanetPosition {
    chart_id: 'chart-456',
    planet: 'Mercury',
    longitude: 72.8,
    latitude: 1.5,
    sign: 'Gemini',
    house: 5,
    degree: 12,
    minute: 48,
    retrograde: false
});

CREATE (pp4:PlanetPosition {
    chart_id: 'chart-456',
    planet: 'Venus',
    longitude: 45.3,
    latitude: -1.2,
    sign: 'Taurus',
    house: 4,
    degree: 15,
    minute: 18,
    retrograde: false
});

CREATE (pp5:PlanetPosition {
    chart_id: 'chart-456',
    planet: 'Mars',
    longitude: 298.7,
    latitude: 0.8,
    sign: 'Aquarius',
    house: 1,
    degree: 28,
    minute: 42,
    retrograde: false
});

// Connect planet positions to chart
MATCH (c:Chart {id: 'chart-456'}), (pp:PlanetPosition {chart_id: 'chart-456'})
CREATE (c)-[:HAS_POSITION]->(pp);

// Connect planet positions to planets and signs
MATCH (pp:PlanetPosition {planet: 'Sun'}), (p:Planet {name: 'Sun'})
CREATE (pp)-[:REPRESENTS]->(p);

MATCH (pp:PlanetPosition {planet: 'Sun'}), (s:Sign {name: 'Gemini'})
CREATE (pp)-[:IN_SIGN]->(s);

MATCH (pp:PlanetPosition {planet: 'Moon'}), (p:Planet {name: 'Moon'})
CREATE (pp)-[:REPRESENTS]->(p);

MATCH (pp:PlanetPosition {planet: 'Moon'}), (s:Sign {name: 'Virgo'})
CREATE (pp)-[:IN_SIGN]->(s);

MATCH (pp:PlanetPosition {planet: 'Mercury'}), (p:Planet {name: 'Mercury'})
CREATE (pp)-[:REPRESENTS]->(p);

MATCH (pp:PlanetPosition {planet: 'Mercury'}), (s:Sign {name: 'Gemini'})
CREATE (pp)-[:IN_SIGN]->(s);

MATCH (pp:PlanetPosition {planet: 'Venus'}), (p:Planet {name: 'Venus'})
CREATE (pp)-[:REPRESENTS]->(p);

MATCH (pp:PlanetPosition {planet: 'Venus'}), (s:Sign {name: 'Taurus'})
CREATE (pp)-[:IN_SIGN]->(s);

MATCH (pp:PlanetPosition {planet: 'Mars'}), (p:Planet {name: 'Mars'})
CREATE (pp)-[:REPRESENTS]->(p);

MATCH (pp:PlanetPosition {planet: 'Mars'}), (s:Sign {name: 'Aquarius'})
CREATE (pp)-[:IN_SIGN]->(s);

// Connect planet positions to houses
MATCH (pp:PlanetPosition {house: 1}), (h:House {number: 1})
CREATE (pp)-[:IN_HOUSE]->(h);

MATCH (pp:PlanetPosition {house: 4}), (h:House {number: 4})
CREATE (pp)-[:IN_HOUSE]->(h);

MATCH (pp:PlanetPosition {house: 5}), (h:House {number: 5})
CREATE (pp)-[:IN_HOUSE]->(h);

MATCH (pp:PlanetPosition {house: 8}), (h:House {number: 8})
CREATE (pp)-[:IN_HOUSE]->(h);

// Create sample aspects
CREATE (a1:Aspect {
    chart_id: 'chart-456',
    planet1: 'Sun',
    planet2: 'Mercury',
    aspect_type: 'Conjunction',
    orb: 2.3,
    applying: true,
    exact_degrees: 0.0,
    strength: 0.85
});

CREATE (a2:Aspect {
    chart_id: 'chart-456',
    planet1: 'Venus',
    planet2: 'Mars',
    aspect_type: 'Square',
    orb: 6.4,
    applying: false,
    exact_degrees: 90.0,
    strength: 0.65
});

// Connect aspects to chart
MATCH (c:Chart {id: 'chart-456'}), (a:Aspect {chart_id: 'chart-456'})
CREATE (c)-[:HAS_ASPECT]->(a);

// Connect aspects to aspect types
MATCH (a:Aspect {aspect_type: 'Conjunction'}), (at:AspectType {name: 'Conjunction'})
CREATE (a)-[:OF_TYPE]->(at);

MATCH (a:Aspect {aspect_type: 'Square'}), (at:AspectType {name: 'Square'})
CREATE (a)-[:OF_TYPE]->(at);

// Connect aspects to planet positions
MATCH (a:Aspect {planet1: 'Sun', planet2: 'Mercury'}), 
      (pp1:PlanetPosition {planet: 'Sun'}), 
      (pp2:PlanetPosition {planet: 'Mercury'})
CREATE (a)-[:BETWEEN]->(pp1), (a)-[:BETWEEN]->(pp2);

MATCH (a:Aspect {planet1: 'Venus', planet2: 'Mars'}), 
      (pp1:PlanetPosition {planet: 'Venus'}), 
      (pp2:PlanetPosition {planet: 'Mars'})
CREATE (a)-[:BETWEEN]->(pp1), (a)-[:BETWEEN]->(pp2);

// Create house cusps
CREATE (hc1:HouseCusp {chart_id: 'chart-456', house: 1, longitude: 270.0, sign: 'Capricorn'});
CREATE (hc2:HouseCusp {chart_id: 'chart-456', house: 2, longitude: 300.0, sign: 'Aquarius'});
CREATE (hc3:HouseCusp {chart_id: 'chart-456', house: 3, longitude: 330.0, sign: 'Pisces'});
CREATE (hc4:HouseCusp {chart_id: 'chart-456', house: 4, longitude: 0.0, sign: 'Aries'});
CREATE (hc5:HouseCusp {chart_id: 'chart-456', house: 5, longitude: 30.0, sign: 'Taurus'});
CREATE (hc6:HouseCusp {chart_id: 'chart-456', house: 6, longitude: 60.0, sign: 'Gemini'});
CREATE (hc7:HouseCusp {chart_id: 'chart-456', house: 7, longitude: 90.0, sign: 'Cancer'});
CREATE (hc8:HouseCusp {chart_id: 'chart-456', house: 8, longitude: 120.0, sign: 'Leo'});
CREATE (hc9:HouseCusp {chart_id: 'chart-456', house: 9, longitude: 150.0, sign: 'Virgo'});
CREATE (hc10:HouseCusp {chart_id: 'chart-456', house: 10, longitude: 180.0, sign: 'Libra'});
CREATE (hc11:HouseCusp {chart_id: 'chart-456', house: 11, longitude: 210.0, sign: 'Scorpio'});
CREATE (hc12:HouseCusp {chart_id: 'chart-456', house: 12, longitude: 240.0, sign: 'Sagittarius'});

// Connect house cusps to chart and houses
MATCH (c:Chart {id: 'chart-456'}), (hc:HouseCusp {chart_id: 'chart-456'})
CREATE (c)-[:HAS_CUSP]->(hc);

MATCH (hc:HouseCusp {house: 1}), (h:House {number: 1})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 2}), (h:House {number: 2})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 3}), (h:House {number: 3})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 4}), (h:House {number: 4})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 5}), (h:House {number: 5})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 6}), (h:House {number: 6})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 7}), (h:House {number: 7})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 8}), (h:House {number: 8})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 9}), (h:House {number: 9})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 10}), (h:House {number: 10})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 11}), (h:House {number: 11})
CREATE (hc)-[:CUSP_OF]->(h);

MATCH (hc:HouseCusp {house: 12}), (h:House {number: 12})
CREATE (hc)-[:CUSP_OF]->(h);