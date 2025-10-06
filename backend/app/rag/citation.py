"""
Citation management system for RAG responses
"""
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import re

from .retriever import RetrievalResult

class CitationStyle(Enum):
    """Citation formatting styles"""
    ACADEMIC = "academic"
    INLINE = "inline"
    FOOTNOTE = "footnote"
    MINIMAL = "minimal"

@dataclass
class Citation:
    """Single citation with source information"""
    id: str
    source_id: str
    title: str
    content_snippet: str
    source_type: str  # "traditional", "modern", "calculation", etc.
    credibility_score: float
    url: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    page: Optional[str] = None

@dataclass
class CitedResponse:
    """Response with embedded citations"""
    content: str
    citations: List[Citation]
    citation_count: int
    credibility_score: float
    source_diversity: float

class CitationManager:
    """Manages citations for RAG responses"""
    
    def __init__(self):
        self.citation_cache = {}
        self.source_metadata = self._load_source_metadata()
    
    def _load_source_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load metadata for known sources"""
        return {
            "traditional_astrology": {
                "title": "Traditional Astrological Principles",
                "author": "Classical Sources",
                "credibility": 0.9,
                "type": "traditional"
            },
            "hellenistic_timing": {
                "title": "Hellenistic Time-Lord Techniques",
                "author": "Ancient Practitioners",
                "credibility": 0.95,
                "type": "traditional"
            },
            "persian_periods": {
                "title": "Persian Firdaria System",
                "author": "Medieval Persian Astrologers",
                "credibility": 0.85,
                "type": "traditional"
            },
            "essential_dignities": {
                "title": "Essential Dignity Tables",
                "author": "Traditional Compilation",
                "credibility": 0.9,
                "type": "calculation"
            },
            "hellenistic_foundations": {
                "title": "Hellenistic Astrological Foundations",
                "author": "Hellenistic Astrologers",
                "credibility": 0.95,
                "type": "traditional"
            },
            "traditional_techniques": {
                "title": "Traditional Astrological Techniques",
                "author": "Classical Methods",
                "credibility": 0.85,
                "type": "traditional"
            }
        }
    
    def create_citations(self, retrieval_results: List[RetrievalResult]) -> List[Citation]:
        """Create citations from retrieval results"""
        citations = []
        
        for i, result in enumerate(retrieval_results):
            citation_id = self._generate_citation_id(result)
            
            # Get source metadata
            source_key = result.metadata.get("source", "unknown") if result.metadata else "unknown"
            source_meta = self.source_metadata.get(source_key, {})
            
            # Create citation
            citation = Citation(
                id=citation_id,
                source_id=result.source_id,
                title=source_meta.get("title", f"Source {i+1}"),
                content_snippet=self._create_snippet(result.content),
                source_type=source_meta.get("type", "unknown"),
                credibility_score=source_meta.get("credibility", 0.5),
                author=source_meta.get("author"),
                date=source_meta.get("date"),
                url=source_meta.get("url")
            )
            
            citations.append(citation)
            
            # Cache citation
            self.citation_cache[citation_id] = citation
        
        return citations
    
    def embed_citations(self, content: str, citations: List[Citation],
                       style: CitationStyle = CitationStyle.INLINE) -> CitedResponse:
        """Embed citations into content"""
        
        if style == CitationStyle.INLINE:
            cited_content = self._embed_inline_citations(content, citations)
        elif style == CitationStyle.FOOTNOTE:
            cited_content = self._embed_footnote_citations(content, citations)
        elif style == CitationStyle.ACADEMIC:
            cited_content = self._embed_academic_citations(content, citations)
        else:  # MINIMAL
            cited_content = self._embed_minimal_citations(content, citations)
        
        # Calculate metrics
        credibility_score = self._calculate_credibility_score(citations)
        source_diversity = self._calculate_source_diversity(citations)
        
        return CitedResponse(
            content=cited_content,
            citations=citations,
            citation_count=len(citations),
            credibility_score=credibility_score,
            source_diversity=source_diversity
        )
    
    def _generate_citation_id(self, result: RetrievalResult) -> str:
        """Generate unique citation ID"""
        content_hash = hashlib.md5(result.content.encode()).hexdigest()[:8]
        return f"cite_{result.source_id}_{content_hash}"
    
    def _create_snippet(self, content: str, max_length: int = 100) -> str:
        """Create content snippet for citation"""
        if len(content) <= max_length:
            return content
        
        # Try to break at sentence boundary
        sentences = content.split('. ')
        snippet = sentences[0]
        
        if len(snippet) > max_length:
            # Break at word boundary
            words = snippet.split()
            snippet = ""
            for word in words:
                if len(snippet + word) > max_length - 3:
                    break
                snippet += word + " "
            snippet = snippet.strip() + "..."
        else:
            snippet += "."
        
        return snippet
    
    def _embed_inline_citations(self, content: str, citations: List[Citation]) -> str:
        """Embed inline citations [1], [2], etc."""
        cited_content = content
        
        # Add citation markers
        for i, citation in enumerate(citations):
            citation_marker = f"[{i+1}]"
            # Insert citation marker at relevant points
            # For now, add at the end of sentences that might reference this source
            cited_content = self._insert_citation_markers(cited_content, citation, citation_marker)
        
        # Add citation list at the end
        citation_list = "\n\n**References:**\n"
        for i, citation in enumerate(citations):
            citation_list += f"[{i+1}] {citation.title}"
            if citation.author:
                citation_list += f" - {citation.author}"
            citation_list += f" (Credibility: {citation.credibility_score:.1f})\n"
        
        return cited_content + citation_list
    
    def _embed_footnote_citations(self, content: str, citations: List[Citation]) -> str:
        """Embed footnote-style citations"""
        cited_content = content
        footnotes = "\n\n**Footnotes:**\n"
        
        for i, citation in enumerate(citations):
            footnote_marker = f"^{i+1}"
            cited_content = self._insert_citation_markers(cited_content, citation, footnote_marker)
            
            footnotes += f"{i+1}. {citation.content_snippet} - {citation.title}\n"
        
        return cited_content + footnotes
    
    def _embed_academic_citations(self, content: str, citations: List[Citation]) -> str:
        """Embed academic-style citations (Author, Date)"""
        cited_content = content
        
        for citation in citations:
            if citation.author and citation.date:
                citation_marker = f"({citation.author}, {citation.date})"
            elif citation.author:
                citation_marker = f"({citation.author})"
            else:
                citation_marker = f"({citation.title})"
            
            cited_content = self._insert_citation_markers(cited_content, citation, citation_marker)
        
        # Add bibliography
        bibliography = "\n\n**Bibliography:**\n"
        for citation in citations:
            bibliography += f"• {citation.title}"
            if citation.author:
                bibliography += f" by {citation.author}"
            if citation.date:
                bibliography += f" ({citation.date})"
            bibliography += f" - Credibility: {citation.credibility_score:.1f}\n"
        
        return cited_content + bibliography
    
    def _embed_minimal_citations(self, content: str, citations: List[Citation]) -> str:
        """Embed minimal citations (just source count)"""
        if not citations:
            return content
        
        source_count = len(citations)
        avg_credibility = sum(c.credibility_score for c in citations) / len(citations)
        
        citation_note = f"\n\n*Based on {source_count} traditional astrological sources (avg. credibility: {avg_credibility:.1f})*"
        
        return content + citation_note
    
    def _insert_citation_markers(self, content: str, citation: Citation, marker: str) -> str:
        """Insert citation markers at relevant points in content"""
        # Simple approach: look for key terms from citation in content
        citation_terms = self._extract_key_terms(citation.content_snippet)
        
        # Find sentences that contain citation terms
        sentences = content.split('. ')
        modified_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains terms from this citation
            if any(term.lower() in sentence_lower for term in citation_terms):
                # Add citation marker at end of sentence
                if not sentence.endswith('.'):
                    sentence += '.'
                sentence = sentence[:-1] + f" {marker}."
            
            modified_sentences.append(sentence)
        
        return '. '.join(modified_sentences)
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for citation matching"""
        # Remove common words and extract meaningful terms
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        key_terms = [word for word in words if word not in common_words and len(word) > 3]
        
        return key_terms[:5]  # Return top 5 key terms
    
    def _calculate_credibility_score(self, citations: List[Citation]) -> float:
        """Calculate overall credibility score for citations"""
        if not citations:
            return 0.0
        
        # Weighted average based on citation relevance
        total_credibility = sum(citation.credibility_score for citation in citations)
        return total_credibility / len(citations)
    
    def _calculate_source_diversity(self, citations: List[Citation]) -> float:
        """Calculate source diversity (0-1, higher = more diverse)"""
        if not citations:
            return 0.0
        
        # Count unique source types
        source_types = set(citation.source_type for citation in citations)
        
        # Diversity score based on type variety
        max_types = 4  # traditional, modern, calculation, experimental
        diversity = len(source_types) / max_types
        
        return min(diversity, 1.0)
    
    def validate_citations(self, citations: List[Citation]) -> Dict[str, Any]:
        """Validate citation quality and completeness"""
        validation_results = {
            "total_citations": len(citations),
            "valid_citations": 0,
            "missing_titles": 0,
            "missing_authors": 0,
            "low_credibility": 0,
            "average_credibility": 0.0,
            "source_types": {},
            "issues": []
        }
        
        if not citations:
            validation_results["issues"].append("No citations provided")
            return validation_results
        
        credibility_scores = []
        
        for citation in citations:
            is_valid = True
            
            # Check required fields
            if not citation.title or citation.title.strip() == "":
                validation_results["missing_titles"] += 1
                validation_results["issues"].append(f"Citation {citation.id} missing title")
                is_valid = False
            
            if not citation.author:
                validation_results["missing_authors"] += 1
            
            # Check credibility
            if citation.credibility_score < 0.5:
                validation_results["low_credibility"] += 1
                validation_results["issues"].append(f"Citation {citation.id} has low credibility ({citation.credibility_score})")
            
            credibility_scores.append(citation.credibility_score)
            
            # Count source types
            source_type = citation.source_type
            if source_type not in validation_results["source_types"]:
                validation_results["source_types"][source_type] = 0
            validation_results["source_types"][source_type] += 1
            
            if is_valid:
                validation_results["valid_citations"] += 1
        
        # Calculate average credibility
        if credibility_scores:
            validation_results["average_credibility"] = sum(credibility_scores) / len(credibility_scores)
        
        return validation_results
    
    def get_citation_by_id(self, citation_id: str) -> Optional[Citation]:
        """Retrieve citation by ID"""
        return self.citation_cache.get(citation_id)
    
    def format_citation_list(self, citations: List[Citation], 
                           style: CitationStyle = CitationStyle.ACADEMIC) -> str:
        """Format citation list in specified style"""
        if not citations:
            return ""
        
        formatted_list = "**Sources:**\n"
        
        for i, citation in enumerate(citations):
            if style == CitationStyle.ACADEMIC:
                formatted_list += f"{i+1}. {citation.title}"
                if citation.author:
                    formatted_list += f" by {citation.author}"
                if citation.date:
                    formatted_list += f" ({citation.date})"
            elif style == CitationStyle.INLINE:
                formatted_list += f"[{i+1}] {citation.title} - {citation.author or 'Unknown Author'}"
            else:  # MINIMAL or FOOTNOTE
                formatted_list += f"• {citation.title} (Credibility: {citation.credibility_score:.1f})"
            
            formatted_list += "\n"
        
        return formatted_list


def ensure_paragraph_coverage(answer_text: str, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure each non-empty paragraph has at least one citation reference."""

    paragraphs = [segment for segment in (answer_text or "").split("\n\n") if segment.strip()]
    if not paragraphs or not citations:
        return citations

    normalized: List[Dict[str, Any]] = []
    assigned = set()
    for entry in citations:
        data = dict(entry)
        paragraph = data.get("paragraph")
        if isinstance(paragraph, int) and 0 <= paragraph < len(paragraphs):
            assigned.add(paragraph)
        else:
            data["paragraph"] = None
        normalized.append(data)

    fallback_idx = 0
    for paragraph_idx in range(len(paragraphs)):
        if paragraph_idx in assigned:
            continue
        target = normalized[fallback_idx % len(normalized)]
        target["paragraph"] = paragraph_idx
        assigned.add(paragraph_idx)
        fallback_idx += 1

    return normalized
