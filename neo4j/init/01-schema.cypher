// Neo4j Graph Schema for Astro-AA
// This script creates the graph model for astrological relationships

// Create constraints and indexes
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT chart_id_unique IF NOT EXISTS FOR (c:Chart) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT planet_name_unique IF NOT EXISTS FOR (p:Planet) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT sign_name_unique IF NOT EXISTS FOR (s:Sign) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT house_number_unique IF NOT EXISTS FOR (h:House) REQUIRE h.number IS UNIQUE;
CREATE CONSTRAINT aspect_type_unique IF NOT EXISTS FOR (a:AspectType) REQUIRE a.name IS UNIQUE;

// Create indexes for performance
CREATE INDEX user_email_index IF NOT EXISTS FOR (u:User) ON (u.email);
CREATE INDEX chart_datetime_index IF NOT EXISTS FOR (c:Chart) ON (c.datetime);
CREATE INDEX planet_position_index IF NOT EXISTS FOR (p:PlanetPosition) ON (p.longitude);
CREATE INDEX aspect_orb_index IF NOT EXISTS FOR (a:Aspect) ON (a.orb);

// Create basic astrological entities
// Planets
CREATE (:Planet {name: 'Sun', symbol: '☉', type: 'luminary', speed: 'fast'});
CREATE (:Planet {name: 'Moon', symbol: '☽', type: 'luminary', speed: 'fast'});
CREATE (:Planet {name: 'Mercury', symbol: '☿', type: 'personal', speed: 'fast'});
CREATE (:Planet {name: 'Venus', symbol: '♀', type: 'personal', speed: 'fast'});
CREATE (:Planet {name: 'Mars', symbol: '♂', type: 'personal', speed: 'medium'});
CREATE (:Planet {name: 'Jupiter', symbol: '♃', type: 'social', speed: 'slow'});
CREATE (:Planet {name: 'Saturn', symbol: '♄', type: 'social', speed: 'slow'});
CREATE (:Planet {name: 'Uranus', symbol: '♅', type: 'generational', speed: 'very_slow'});
CREATE (:Planet {name: 'Neptune', symbol: '♆', type: 'generational', speed: 'very_slow'});
CREATE (:Planet {name: 'Pluto', symbol: '♇', type: 'generational', speed: 'very_slow'});

// Zodiac Signs
CREATE (:Sign {name: 'Aries', symbol: '♈', element: 'Fire', modality: 'Cardinal', ruler: 'Mars', number: 1});
CREATE (:Sign {name: 'Taurus', symbol: '♉', element: 'Earth', modality: 'Fixed', ruler: 'Venus', number: 2});
CREATE (:Sign {name: 'Gemini', symbol: '♊', element: 'Air', modality: 'Mutable', ruler: 'Mercury', number: 3});
CREATE (:Sign {name: 'Cancer', symbol: '♋', element: 'Water', modality: 'Cardinal', ruler: 'Moon', number: 4});
CREATE (:Sign {name: 'Leo', symbol: '♌', element: 'Fire', modality: 'Fixed', ruler: 'Sun', number: 5});
CREATE (:Sign {name: 'Virgo', symbol: '♍', element: 'Earth', modality: 'Mutable', ruler: 'Mercury', number: 6});
CREATE (:Sign {name: 'Libra', symbol: '♎', element: 'Air', modality: 'Cardinal', ruler: 'Venus', number: 7});
CREATE (:Sign {name: 'Scorpio', symbol: '♏', element: 'Water', modality: 'Fixed', ruler: 'Mars', number: 8});
CREATE (:Sign {name: 'Sagittarius', symbol: '♐', element: 'Fire', modality: 'Mutable', ruler: 'Jupiter', number: 9});
CREATE (:Sign {name: 'Capricorn', symbol: '♑', element: 'Earth', modality: 'Cardinal', ruler: 'Saturn', number: 10});
CREATE (:Sign {name: 'Aquarius', symbol: '♒', element: 'Air', modality: 'Fixed', ruler: 'Saturn', number: 11});
CREATE (:Sign {name: 'Pisces', symbol: '♓', element: 'Water', modality: 'Mutable', ruler: 'Jupiter', number: 12});

// Houses
CREATE (:House {number: 1, name: 'Ascendant', theme: 'Self, Identity, Appearance'});
CREATE (:House {number: 2, name: 'Resources', theme: 'Money, Values, Possessions'});
CREATE (:House {number: 3, name: 'Communication', theme: 'Siblings, Learning, Short Trips'});
CREATE (:House {number: 4, name: 'Home', theme: 'Family, Roots, Foundation'});
CREATE (:House {number: 5, name: 'Creativity', theme: 'Children, Romance, Self-Expression'});
CREATE (:House {number: 6, name: 'Service', theme: 'Health, Work, Daily Routine'});
CREATE (:House {number: 7, name: 'Partnership', theme: 'Marriage, Open Enemies, Contracts'});
CREATE (:House {number: 8, name: 'Transformation', theme: 'Death, Rebirth, Shared Resources'});
CREATE (:House {number: 9, name: 'Philosophy', theme: 'Higher Learning, Travel, Religion'});
CREATE (:House {number: 10, name: 'Career', theme: 'Reputation, Authority, Public Life'});
CREATE (:House {number: 11, name: 'Community', theme: 'Friends, Groups, Hopes'});
CREATE (:House {number: 12, name: 'Spirituality', theme: 'Subconscious, Hidden Enemies, Sacrifice'});

// Aspect Types
CREATE (:AspectType {name: 'Conjunction', symbol: '☌', degrees: 0, orb: 8, nature: 'neutral'});
CREATE (:AspectType {name: 'Sextile', symbol: '⚹', degrees: 60, orb: 6, nature: 'harmonious'});
CREATE (:AspectType {name: 'Square', symbol: '□', degrees: 90, orb: 8, nature: 'challenging'});
CREATE (:AspectType {name: 'Trine', symbol: '△', degrees: 120, orb: 8, nature: 'harmonious'});
CREATE (:AspectType {name: 'Opposition', symbol: '☍', degrees: 180, orb: 8, nature: 'challenging'});
CREATE (:AspectType {name: 'Quincunx', symbol: '⚻', degrees: 150, orb: 3, nature: 'minor'});
CREATE (:AspectType {name: 'Semisextile', symbol: '⚺', degrees: 30, orb: 2, nature: 'minor'});
CREATE (:AspectType {name: 'Semisquare', symbol: '∠', degrees: 45, orb: 2, nature: 'minor'});
CREATE (:AspectType {name: 'Sesquiquadrate', symbol: '⚼', degrees: 135, orb: 2, nature: 'minor'});

// Create rulership relationships
MATCH (p:Planet {name: 'Mars'}), (s:Sign {name: 'Aries'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Venus'}), (s:Sign {name: 'Taurus'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Mercury'}), (s:Sign {name: 'Gemini'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Moon'}), (s:Sign {name: 'Cancer'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Sun'}), (s:Sign {name: 'Leo'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Mercury'}), (s:Sign {name: 'Virgo'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Venus'}), (s:Sign {name: 'Libra'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Mars'}), (s:Sign {name: 'Scorpio'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Jupiter'}), (s:Sign {name: 'Sagittarius'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Saturn'}), (s:Sign {name: 'Capricorn'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Saturn'}), (s:Sign {name: 'Aquarius'}) CREATE (p)-[:RULES]->(s);
MATCH (p:Planet {name: 'Jupiter'}), (s:Sign {name: 'Pisces'}) CREATE (p)-[:RULES]->(s);

// Create exaltation relationships
MATCH (p:Planet {name: 'Sun'}), (s:Sign {name: 'Aries'}) CREATE (p)-[:EXALTED_IN]->(s);
MATCH (p:Planet {name: 'Moon'}), (s:Sign {name: 'Taurus'}) CREATE (p)-[:EXALTED_IN]->(s);
MATCH (p:Planet {name: 'Mercury'}), (s:Sign {name: 'Virgo'}) CREATE (p)-[:EXALTED_IN]->(s);
MATCH (p:Planet {name: 'Venus'}), (s:Sign {name: 'Pisces'}) CREATE (p)-[:EXALTED_IN]->(s);
MATCH (p:Planet {name: 'Mars'}), (s:Sign {name: 'Capricorn'}) CREATE (p)-[:EXALTED_IN]->(s);
MATCH (p:Planet {name: 'Jupiter'}), (s:Sign {name: 'Cancer'}) CREATE (p)-[:EXALTED_IN]->(s);
MATCH (p:Planet {name: 'Saturn'}), (s:Sign {name: 'Libra'}) CREATE (p)-[:EXALTED_IN]->(s);

// Create detriment relationships (opposite of rulership)
MATCH (p:Planet {name: 'Mars'}), (s:Sign {name: 'Libra'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Venus'}), (s:Sign {name: 'Scorpio'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Mercury'}), (s:Sign {name: 'Sagittarius'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Moon'}), (s:Sign {name: 'Capricorn'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Sun'}), (s:Sign {name: 'Aquarius'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Mercury'}), (s:Sign {name: 'Pisces'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Venus'}), (s:Sign {name: 'Aries'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Mars'}), (s:Sign {name: 'Taurus'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Jupiter'}), (s:Sign {name: 'Gemini'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Saturn'}), (s:Sign {name: 'Cancer'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Saturn'}), (s:Sign {name: 'Leo'}) CREATE (p)-[:DETRIMENT_IN]->(s);
MATCH (p:Planet {name: 'Jupiter'}), (s:Sign {name: 'Virgo'}) CREATE (p)-[:DETRIMENT_IN]->(s);

// Create fall relationships (opposite of exaltation)
MATCH (p:Planet {name: 'Sun'}), (s:Sign {name: 'Libra'}) CREATE (p)-[:FALL_IN]->(s);
MATCH (p:Planet {name: 'Moon'}), (s:Sign {name: 'Scorpio'}) CREATE (p)-[:FALL_IN]->(s);
MATCH (p:Planet {name: 'Mercury'}), (s:Sign {name: 'Pisces'}) CREATE (p)-[:FALL_IN]->(s);
MATCH (p:Planet {name: 'Venus'}), (s:Sign {name: 'Virgo'}) CREATE (p)-[:FALL_IN]->(s);
MATCH (p:Planet {name: 'Mars'}), (s:Sign {name: 'Cancer'}) CREATE (p)-[:FALL_IN]->(s);
MATCH (p:Planet {name: 'Jupiter'}), (s:Sign {name: 'Capricorn'}) CREATE (p)-[:FALL_IN]->(s);
MATCH (p:Planet {name: 'Saturn'}), (s:Sign {name: 'Aries'}) CREATE (p)-[:FALL_IN]->(s);