"""
Interpretation request and result endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.interpreters.core import InterpretationEngine
from app.interpreters.output_composer import OutputMode, OutputStyle
from app.rag.core import RAGSystem, RAGQuery
from app.rag.citation import CitationStyle
from app.services import ChartService, InterpretationService

router = APIRouter()

class InterpretationRequest(BaseModel):
    """Interpretation request model"""
    chart_id: str = Field(..., description="Chart ID to interpret")
    mode: str = Field(..., description="Interpretation mode: natal, timing, today")
    focus_topic: Optional[str] = Field(None, description="Specific topic to focus on")
    language: str = Field("en", description="Response language (en, tr)")

class InterpretationResponse(BaseModel):
    """Interpretation response model"""
    request_id: str
    chart_id: str
    mode: str
    status: str
    summary: Optional[str] = None
    confidence: Optional[float] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

@router.post("/", response_model=Dict[str, Any])
async def create_interpretation_request(request_data: InterpretationRequest):
    """Create new interpretation request using the interpretation engine"""
    try:
        request_id = str(uuid.uuid4())
        
        # Initialize interpretation engine and RAG system
        style = OutputStyle.ACCESSIBLE if request_data.language == "en" else OutputStyle.ACCESSIBLE
        engine = InterpretationEngine(language=request_data.language, style=style)
        rag_system = RAGSystem()
        
        # Map mode string to OutputMode enum
        mode_mapping = {
            "natal": OutputMode.NATAL,
            "timing": OutputMode.TIMING,
            "today": OutputMode.TODAY
        }
        
        output_mode = mode_mapping.get(request_data.mode)
        if not output_mode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown interpretation mode: {request_data.mode}"
            )
        
        # Retrieve chart data from database
        chart = ChartService.get_chart(request_data.chart_id)
        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart with ID {request_data.chart_id} not found"
            )

        # Convert stored chart data to interpretation format
        chart_data = _convert_stored_chart_to_interpretation_format(chart)
        
        # Get interpretation summary to identify key elements
        interpretation_summary = engine.get_interpretation_summary(chart_data)
        main_elements = interpretation_summary.get("main_themes", [])
        
        # Query RAG system for additional context
        rag_context = {
            "user_level": "intermediate",
            "focus_areas": [request_data.focus_topic] if request_data.focus_topic else [],
            "chart_elements": main_elements
        }
        
        rag_response = await rag_system.query_for_interpretation(main_elements, rag_context)
        
        # Generate interpretation with RAG augmentation
        interpretation = engine.interpret_chart(
            chart_data=chart_data,
            mode=output_mode,
            focus_topic=request_data.focus_topic
        )
        
        # Augment interpretation with RAG content
        if rag_response.retrieved_content:
            # Add RAG insights to interpretation
            rag_insights = "\n\n**Traditional Sources:**\n"
            for i, content in enumerate(rag_response.retrieved_content[:3]):
                rag_insights += f"• {content[:200]}...\n"
            
            interpretation.summary += rag_insights
        
        # Save interpretation to database
        interpretation_text = interpretation.summary
        if rag_response.retrieved_content:
            rag_insights = "\n\n**Traditional Sources:**\n"
            for i, content in enumerate(rag_response.retrieved_content[:3]):
                rag_insights += f"• {content[:200]}...\n"
            interpretation_text += rag_insights

        saved = InterpretationService.save_interpretation(
            interpretation_id=request_id,
            chart_id=request_data.chart_id,
            query=f"Interpretation mode: {request_data.mode}" + (f", focus: {request_data.focus_topic}" if request_data.focus_topic else ""),
            mode=request_data.mode,
            interpretation=interpretation_text,
            confidence_score=interpretation.overall_confidence,
            sources={
                "rag_sources": len(rag_response.retrieved_content),
                "citations": [
                    {
                        "id": cite.id,
                        "title": cite.title,
                        "credibility": cite.credibility_score
                    }
                    for cite in (rag_response.citations or [])
                ]
            }
        )

        if not saved:
            print("Warning: Failed to save interpretation to database")

        # Format response
        response = {
            "request_id": request_id,
            "chart_id": request_data.chart_id,
            "mode": request_data.mode,
            "status": "completed",
            "summary": interpretation_text,
            "confidence": interpretation.overall_confidence,
            "sections": [
                {
                    "title": section.title,
                    "content": section.content,
                    "confidence": section.confidence,
                    "priority": section.priority
                }
                for section in interpretation.sections
            ],
            "evidence_summary": interpretation.evidence_summary,
            "warnings": interpretation.warnings,
            "metadata": interpretation.metadata,
            "rag_augmentation": {
                "sources_consulted": len(rag_response.retrieved_content),
                "rag_confidence": rag_response.confidence_score,
                "citations": [
                    {
                        "id": cite.id,
                        "title": cite.title,
                        "credibility": cite.credibility_score
                    }
                    for cite in (rag_response.citations or [])
                ],
                "processing_time": rag_response.processing_time
            },
            "stored_in_db": saved,
            "created_at": datetime.now()
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interpretation generation failed: {str(e)}"
        )

@router.get("/{request_id}")
async def get_interpretation_result(request_id: str):
    """Get interpretation result by request ID"""
    try:
        interpretation = InterpretationService.get_interpretation(request_id)
        if interpretation:
            return interpretation
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interpretation with ID {request_id} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interpretation: {str(e)}"
        )

def _convert_stored_chart_to_interpretation_format(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Convert stored chart data to interpretation engine format"""
    calculations = chart.get("calculations", {})

    return {
        "chart_id": chart.get("chart_id"),
        "planets": calculations.get("planets", {}),
        "houses": calculations.get("houses", {}),
        "almuten": calculations.get("almuten", {}),
        "zodiacal_releasing": calculations.get("zodiacal_releasing", {}),
        "profection": calculations.get("profection"),
        "firdaria": calculations.get("firdaria"),
        "antiscia": calculations.get("antiscia"),
        "lots": calculations.get("lots", {}),
        "is_day_birth": calculations.get("is_day_birth", False)
    }

def _get_mock_chart_data(chart_id: str) -> Dict[str, Any]:
    """Get mock chart data for testing - in production this would query database"""
    return {
        "chart_id": chart_id,
        "planets": {
            "Sun": {"longitude": 84.5, "sign": "Gemini", "degree_in_sign": 24.5, "is_retrograde": False},
            "Moon": {"longitude": 210.3, "sign": "Scorpio", "degree_in_sign": 20.3, "is_retrograde": False},
            "Mercury": {"longitude": 75.2, "sign": "Gemini", "degree_in_sign": 15.2, "is_retrograde": False},
            "Venus": {"longitude": 45.8, "sign": "Taurus", "degree_in_sign": 15.8, "is_retrograde": False},
            "Mars": {"longitude": 315.1, "sign": "Aquarius", "degree_in_sign": 15.1, "is_retrograde": False},
            "Jupiter": {"longitude": 120.7, "sign": "Leo", "degree_in_sign": 0.7, "is_retrograde": False},
            "Saturn": {"longitude": 285.4, "sign": "Capricorn", "degree_in_sign": 15.4, "is_retrograde": False}
        },
        "houses": {
            "asc": 0.0,
            "mc": 270.0,
            "asc_sign": "Aries",
            "mc_sign": "Capricorn"
        },
        "almuten": {
            "winner": "Mercury",
            "scores": {
                "Sun": 8, "Moon": 6, "Mercury": 12, "Venus": 7, 
                "Mars": 5, "Jupiter": 9, "Saturn": 10
            },
            "tie_break_reason": None
        },
        "zodiacal_releasing": {
            "lot_used": "Spirit",
            "current_periods": {
                "l1": {
                    "sign": "Leo",
                    "ruler": "Sun",
                    "start_date": "2020-01-01",
                    "end_date": "2039-01-01",
                    "is_peak": True,
                    "is_lb": False,
                    "tone": "positive"
                },
                "l2": {
                    "sign": "Virgo",
                    "ruler": "Mercury",
                    "start_date": "2023-01-01",
                    "end_date": "2024-07-01",
                    "is_peak": False,
                    "is_lb": False,
                    "tone": "neutral"
                }
            }
        },
        "profection": {
            "age": 33,
            "profected_house": 10,
            "profected_sign": "Capricorn",
            "year_lord": "Saturn",
            "activated_topics": ["career", "reputation", "authority", "public life"]
        },
        "firdaria": {
            "current_major": {
                "lord": "Jupiter",
                "start_date": "2020-01-01",
                "end_date": "2032-01-01"
            },
            "current_minor": {
                "lord": "Venus",
                "start_date": "2023-01-01",
                "end_date": "2024-05-01"
            }
        },
        "antiscia": {
            "summary": {"total_contacts": 3},
            "strongest_contacts": [
                {
                    "original_planet": "Sun",
                    "contacted_planet": "Moon",
                    "antiscia_type": "antiscia",
                    "orb": 0.8
                },
                {
                    "original_planet": "Venus",
                    "contacted_planet": "Mars",
                    "antiscia_type": "contra_antiscia",
                    "orb": 1.2
                }
            ]
        },
        "is_day_birth": True
    }

@router.get("/summary/{chart_id}")
async def get_interpretation_summary(chart_id: str):
    """Get quick interpretation summary without full composition"""
    try:
        engine = InterpretationEngine()
        mock_chart_data = _get_mock_chart_data(chart_id)
        
        summary = engine.get_interpretation_summary(mock_chart_data)
        
        return {
            "chart_id": chart_id,
            "summary": summary,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}"
        )

@router.get("/element/{chart_id}/{element}")
async def get_element_interpretation(chart_id: str, element: str):
    """Get detailed interpretation for specific chart element"""
    try:
        engine = InterpretationEngine()
        mock_chart_data = _get_mock_chart_data(chart_id)
        
        element_analysis = engine.interpret_specific_element(mock_chart_data, element)
        
        return {
            "chart_id": chart_id,
            "element_analysis": element_analysis,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Element interpretation failed: {str(e)}"
        )

@router.post("/rag-query")
async def rag_query(query_data: Dict[str, Any]):
    """Direct RAG system query for astrological knowledge"""
    try:
        rag_system = RAGSystem()
        
        query_text = query_data.get("query", "")
        if not query_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query text is required"
            )
        
        rag_query = RAGQuery(
            query=query_text,
            top_k=query_data.get("top_k", 5),
            expand_query=query_data.get("expand_query", True),
            rerank_results=query_data.get("rerank_results", True),
            include_citations=query_data.get("include_citations", True),
            citation_style=CitationStyle.INLINE,
            filters=query_data.get("filters")
        )
        
        response = await rag_system.query(rag_query)
        
        return {
            "query": response.query,
            "results": response.retrieved_content,
            "confidence": response.confidence_score,
            "citations": [
                {
                    "id": cite.id,
                    "title": cite.title,
                    "snippet": cite.content_snippet,
                    "credibility": cite.credibility_score,
                    "source_type": cite.source_type
                }
                for cite in (response.citations or [])
            ],
            "stats": {
                "retrieval": response.retrieval_stats,
                "expansion": response.expansion_stats,
                "reranking": response.reranking_stats,
                "processing_time": response.processing_time
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )

@router.get("/rag-topic/{topic}")
async def rag_topic_query(topic: str, top_k: int = 5):
    """Query RAG system by astrological topic"""
    try:
        rag_system = RAGSystem()
        response = await rag_system.query_by_topic(topic, top_k)
        
        return {
            "topic": topic,
            "results": response.retrieved_content,
            "confidence": response.confidence_score,
            "citations": [
                {
                    "title": cite.title,
                    "credibility": cite.credibility_score
                }
                for cite in (response.citations or [])
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Topic query failed: {str(e)}"
        )