"""
Query expansion system for astrological queries
"""
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re

class ExpansionMethod(Enum):
    """Query expansion methods"""
    SYNONYMS = "synonyms"
    HYDE = "hyde"  # Hypothetical Document Embeddings
    CONTEXTUAL = "contextual"
    COMBINED = "combined"

@dataclass
class ExpandedQuery:
    """Expanded query with additional terms"""
    original_query: str
    expanded_terms: List[str]
    synonyms: List[str]
    contextual_terms: List[str]
    hyde_query: Optional[str] = None
    confidence: float = 1.0

class AstrologySynonymDict:
    """Astrological terminology synonym dictionary"""
    
    def __init__(self):
        self.synonyms = {
            # English-Turkish pairs
            "ascendant": ["asc", "rising", "yükselen", "asandan"],
            "midheaven": ["mc", "medium coeli", "gökyüzü ortası", "zenit"],
            "descendant": ["desc", "batı", "batan"],
            "imum coeli": ["ic", "gece yarısı", "nadir"],
            
            # Planets
            "sun": ["sol", "güneş", "solar"],
            "moon": ["luna", "ay", "lunar"],
            "mercury": ["merkür", "hermes"],
            "venus": ["venüs", "aphrodite", "zühre"],
            "mars": ["mars", "merih", "ares"],
            "jupiter": ["jüpiter", "müşteri", "zeus"],
            "saturn": ["satürn", "zuhal", "kronos"],
            "uranus": ["uranüs"],
            "neptune": ["neptün"],
            "pluto": ["plüton"],
            
            # Signs
            "aries": ["koç", "ram"],
            "taurus": ["boğa", "bull"],
            "gemini": ["ikizler", "twins"],
            "cancer": ["yengeç", "crab"],
            "leo": ["aslan", "lion"],
            "virgo": ["başak", "virgin"],
            "libra": ["terazi", "scales"],
            "scorpio": ["akrep", "scorpion"],
            "sagittarius": ["yay", "archer"],
            "capricorn": ["oğlak", "goat"],
            "aquarius": ["kova", "water bearer"],
            "pisces": ["balık", "fish"],
            
            # Aspects
            "conjunction": ["kavuşum", "birleşim", "0°"],
            "opposition": ["karşıt", "180°", "opposition"],
            "trine": ["üçgen", "120°", "trigon"],
            "square": ["kare", "90°", "tetragone"],
            "sextile": ["altıgen", "60°", "hexagon"],
            
            # Houses
            "first house": ["1. ev", "ascendant house", "identity"],
            "second house": ["2. ev", "money house", "values"],
            "third house": ["3. ev", "communication house", "siblings"],
            "fourth house": ["4. ev", "home house", "family"],
            "fifth house": ["5. ev", "creativity house", "children"],
            "sixth house": ["6. ev", "health house", "work"],
            "seventh house": ["7. ev", "partnership house", "marriage"],
            "eighth house": ["8. ev", "transformation house", "death"],
            "ninth house": ["9. ev", "philosophy house", "travel"],
            "tenth house": ["10. ev", "career house", "reputation"],
            "eleventh house": ["11. ev", "friendship house", "hopes"],
            "twelfth house": ["12. ev", "spirituality house", "hidden"],
            
            # Techniques
            "zodiacal releasing": ["zr", "zodiak salıverme", "zodyak releasing"],
            "profection": ["profeksiyon", "annual profection", "yıllık profeksiyon"],
            "firdaria": ["firdaria", "persian periods", "fars dönemleri"],
            "almuten": ["almuten figuris", "güçlü gezegen"],
            "antiscia": ["antisya", "gölge noktalar", "solstitial points"],
            "dignity": ["değerlik", "essential dignity", "temel değerlik"],
            "reception": ["kabul", "mutual reception", "karşılıklı kabul"],
            "sect": ["fırka", "day/night", "gündüz/gece"],
            
            # Timing
            "transit": ["geçiş", "current position", "şimdiki konum"],
            "progression": ["progresyon", "secondary progression"],
            "solar arc": ["güneş yayı", "solar arc direction"],
            "return": ["dönüş", "solar return", "güneş dönüşü"],
            
            # Lots
            "lot of fortune": ["talih noktası", "part of fortune"],
            "lot of spirit": ["ruh noktası", "part of spirit"],
            "arabic parts": ["arap noktaları", "lots"],
            
            # Qualities
            "cardinal": ["öncü", "moveable", "hareketli"],
            "fixed": ["sabit", "fixed", "durağan"],
            "mutable": ["değişken", "common", "ortak"],
            
            "fire": ["ateş", "fire element"],
            "earth": ["toprak", "earth element"],
            "air": ["hava", "air element"],
            "water": ["su", "water element"],
            
            # Conditions
            "retrograde": ["geri gidiş", "retrograd", "rx"],
            "direct": ["düz gidiş", "direkt"],
            "stationary": ["durağan", "station"],
            "cazimi": ["cazimi", "heart of sun"],
            "combust": ["yanık", "under beams"]
        }
        
        # Create reverse lookup
        self.reverse_synonyms = {}
        for key, synonyms in self.synonyms.items():
            for synonym in synonyms:
                if synonym not in self.reverse_synonyms:
                    self.reverse_synonyms[synonym] = []
                self.reverse_synonyms[synonym].append(key)
                
                # Add other synonyms
                for other_synonym in synonyms:
                    if other_synonym != synonym and other_synonym not in self.reverse_synonyms[synonym]:
                        self.reverse_synonyms[synonym].append(other_synonym)

class QueryExpander:
    """Query expansion system for astrological queries"""
    
    def __init__(self):
        self.synonym_dict = AstrologySynonymDict()
        self.contextual_rules = self._load_contextual_rules()
    
    def _load_contextual_rules(self) -> Dict[str, List[str]]:
        """Load contextual expansion rules"""
        return {
            # When someone asks about planets, include related concepts
            "planet_context": {
                "triggers": ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"],
                "additions": ["dignity", "aspect", "house", "sign"]
            },
            
            # When asking about timing, include time-lord methods
            "timing_context": {
                "triggers": ["timing", "when", "period", "phase"],
                "additions": ["zodiacal releasing", "profection", "firdaria", "transit", "progression"]
            },
            
            # When asking about relationships, include 7th house themes
            "relationship_context": {
                "triggers": ["relationship", "marriage", "partner", "love"],
                "additions": ["seventh house", "venus", "mars", "descendant"]
            },
            
            # When asking about career, include 10th house themes
            "career_context": {
                "triggers": ["career", "job", "work", "profession"],
                "additions": ["tenth house", "midheaven", "saturn", "sun"]
            },
            
            # When asking about identity, include 1st house themes
            "identity_context": {
                "triggers": ["identity", "personality", "self", "character"],
                "additions": ["first house", "ascendant", "sun", "moon"]
            }
        }
    
    def expand_query(self, query: str, method: ExpansionMethod = ExpansionMethod.COMBINED,
                    max_expansions: int = 10) -> ExpandedQuery:
        """Expand query using specified method"""
        
        query_lower = query.lower()
        
        if method == ExpansionMethod.SYNONYMS:
            return self._expand_synonyms(query, query_lower, max_expansions)
        elif method == ExpansionMethod.HYDE:
            return self._expand_hyde(query, query_lower, max_expansions)
        elif method == ExpansionMethod.CONTEXTUAL:
            return self._expand_contextual(query, query_lower, max_expansions)
        else:  # COMBINED
            return self._expand_combined(query, query_lower, max_expansions)
    
    def _expand_synonyms(self, query: str, query_lower: str, max_expansions: int) -> ExpandedQuery:
        """Expand query using synonyms"""
        synonyms = []
        query_terms = query_lower.split()
        
        for term in query_terms:
            # Direct lookup
            if term in self.synonym_dict.synonyms:
                synonyms.extend(self.synonym_dict.synonyms[term][:3])  # Limit per term
            
            # Reverse lookup
            if term in self.synonym_dict.reverse_synonyms:
                synonyms.extend(self.synonym_dict.reverse_synonyms[term][:3])
        
        # Remove duplicates and limit
        unique_synonyms = list(set(synonyms))[:max_expansions]
        
        return ExpandedQuery(
            original_query=query,
            expanded_terms=unique_synonyms,
            synonyms=unique_synonyms,
            contextual_terms=[],
            confidence=0.8
        )
    
    def _expand_contextual(self, query: str, query_lower: str, max_expansions: int) -> ExpandedQuery:
        """Expand query using contextual rules"""
        contextual_terms = []
        
        for context_name, rules in self.contextual_rules.items():
            triggers = rules["triggers"]
            additions = rules["additions"]
            
            # Check if any trigger is in the query
            if any(trigger in query_lower for trigger in triggers):
                contextual_terms.extend(additions[:3])  # Limit per context
        
        # Remove duplicates and limit
        unique_contextual = list(set(contextual_terms))[:max_expansions]
        
        return ExpandedQuery(
            original_query=query,
            expanded_terms=unique_contextual,
            synonyms=[],
            contextual_terms=unique_contextual,
            confidence=0.7
        )
    
    def _expand_hyde(self, query: str, query_lower: str, max_expansions: int) -> ExpandedQuery:
        """Expand query using HyDE (Hypothetical Document Embeddings)"""
        # Generate a hypothetical document that would answer the query
        hyde_templates = {
            "what": "This astrological concept explains {query}. It involves {related_concepts} and is used for {purpose}.",
            "how": "To understand {query} in astrology, one must consider {factors}. The process involves {steps}.",
            "when": "The timing of {query} can be determined through {timing_methods}. Key indicators include {indicators}.",
            "why": "The astrological significance of {query} stems from {principles}. This is important because {reasons}."
        }
        
        # Determine query type
        query_type = "what"  # default
        if query_lower.startswith("how"):
            query_type = "how"
        elif query_lower.startswith("when"):
            query_type = "when"
        elif query_lower.startswith("why"):
            query_type = "why"
        
        # Generate hypothetical document
        template = hyde_templates[query_type]
        
        # Extract key terms for placeholders
        key_terms = self._extract_key_terms(query_lower)
        
        hyde_query = template.format(
            query=query,
            related_concepts="planetary dignities, house rulerships, aspects",
            purpose="interpretation and timing",
            factors="essential dignities, accidental conditions, time-lord periods",
            steps="calculation, analysis, synthesis",
            timing_methods="zodiacal releasing, profections, transits",
            indicators="peaks, loosing of bond, angular periods",
            principles="traditional astrological doctrine",
            reasons="it reveals core life themes and timing"
        )
        
        return ExpandedQuery(
            original_query=query,
            expanded_terms=key_terms,
            synonyms=[],
            contextual_terms=[],
            hyde_query=hyde_query,
            confidence=0.6
        )
    
    def _expand_combined(self, query: str, query_lower: str, max_expansions: int) -> ExpandedQuery:
        """Combine all expansion methods"""
        synonym_expansion = self._expand_synonyms(query, query_lower, max_expansions // 3)
        contextual_expansion = self._expand_contextual(query, query_lower, max_expansions // 3)
        hyde_expansion = self._expand_hyde(query, query_lower, max_expansions // 3)
        
        # Combine all terms
        all_terms = (synonym_expansion.synonyms + 
                    contextual_expansion.contextual_terms + 
                    hyde_expansion.expanded_terms)
        
        # Remove duplicates and limit
        unique_terms = list(set(all_terms))[:max_expansions]
        
        return ExpandedQuery(
            original_query=query,
            expanded_terms=unique_terms,
            synonyms=synonym_expansion.synonyms,
            contextual_terms=contextual_expansion.contextual_terms,
            hyde_query=hyde_expansion.hyde_query,
            confidence=0.9  # Higher confidence for combined approach
        )
    
    def _extract_key_terms(self, query_lower: str) -> List[str]:
        """Extract key astrological terms from query"""
        key_terms = []
        
        # Check for known astrological terms
        all_terms = set()
        all_terms.update(self.synonym_dict.synonyms.keys())
        all_terms.update(self.synonym_dict.reverse_synonyms.keys())
        
        for term in all_terms:
            if term in query_lower:
                key_terms.append(term)
        
        return key_terms[:5]  # Limit to 5 key terms
    
    def suggest_related_queries(self, query: str, max_suggestions: int = 5) -> List[str]:
        """Suggest related queries based on the input"""
        query_lower = query.lower()
        suggestions = []
        
        # Template-based suggestions
        if any(planet in query_lower for planet in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]):
            suggestions.extend([
                "What are the essential dignities?",
                "How do planetary aspects work?",
                "What is sect in astrology?"
            ])
        
        if any(timing in query_lower for timing in ["when", "timing", "period"]):
            suggestions.extend([
                "How does zodiacal releasing work?",
                "What are annual profections?",
                "How to interpret transits?"
            ])
        
        if any(house in query_lower for house in ["house", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"]):
            suggestions.extend([
                "What do the astrological houses mean?",
                "How are house rulers determined?",
                "What is whole sign houses?"
            ])
        
        return suggestions[:max_suggestions]
    
    def get_expansion_stats(self, expanded_query: ExpandedQuery) -> Dict[str, Any]:
        """Get statistics about query expansion"""
        return {
            "original_length": len(expanded_query.original_query.split()),
            "total_expansions": len(expanded_query.expanded_terms),
            "synonym_count": len(expanded_query.synonyms),
            "contextual_count": len(expanded_query.contextual_terms),
            "has_hyde": expanded_query.hyde_query is not None,
            "confidence": expanded_query.confidence,
            "expansion_ratio": len(expanded_query.expanded_terms) / max(len(expanded_query.original_query.split()), 1)
        }