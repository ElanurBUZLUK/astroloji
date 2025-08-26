"""
Admin and monitoring endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from ..evaluation.observability import observability
from ..evaluation.test_suite import TestSuite
from ..evaluation.metrics import EvaluationSuite

router = APIRouter()
test_suite = TestSuite()
evaluation_suite = EvaluationSuite()

@router.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    return observability.get_dashboard_data()

@router.get("/health")
async def get_system_health():
    """Get system health status"""
    health_data = observability.update_system_health()
    return {
        "status": "ok",
        "health": health_data,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/eval")
async def get_evaluation_metrics():
    """Get evaluation metrics summary"""
    summary = evaluation_suite.get_evaluation_summary(time_window_hours=24)
    return summary

@router.post("/eval/run-tests")
async def run_evaluation_tests(tags: Optional[List[str]] = Query(None)):
    """Run evaluation test suite"""
    try:
        # Mock systems for testing
        class MockRAG:
            async def query(self, q):
                return {
                    "answer": "Mock answer for: " + q,
                    "sources": [{"content": "Mock source", "score": 0.8}],
                    "citations": [{"title": "Mock Citation", "credibility": 0.9}]
                }
        
        class MockInterpreter:
            async def generate_interpretation(self, data):
                return {
                    "interpretation": "Mock interpretation",
                    "confidence": 0.75,
                    "coherence_score": 0.82
                }
        
        mock_systems = {
            "rag_system": MockRAG(),
            "interpretation_engine": MockInterpreter()
        }
        
        results = await test_suite.run_all_tests(mock_systems)
        summary = test_suite.get_test_summary(results)
        
        return {
            "summary": summary,
            "results": [
                {
                    "test_case_id": r.test_case_id,
                    "status": r.status.value,
                    "score": r.score,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "description": m.description
                        }
                        for m in r.metrics
                    ]
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

@router.get("/eval/test-cases")
async def list_test_cases(tags: Optional[List[str]] = Query(None)):
    """List available test cases"""
    test_cases = test_suite.test_cases
    if tags:
        test_cases = [tc for tc in test_cases if tc.tags and any(tag in tc.tags for tag in tags)]
    
    return {
        "test_cases": [
            {
                "id": tc.id,
                "name": tc.name,
                "description": tc.description,
                "category": tc.category,
                "tags": tc.tags or []
            }
            for tc in test_cases
        ]
    }

@router.post("/eval/test-case/{test_id}")
async def run_single_test(test_id: str):
    """Run a single test case"""
    test_case = next((tc for tc in test_suite.test_cases if tc.id == test_id), None)
    if not test_case:
        raise HTTPException(status_code=404, detail=f"Test case {test_id} not found")
    
    try:
        # Mock system based on test category
        class MockRAG:
            async def query(self, q):
                return {
                    "answer": "Mock answer for: " + q,
                    "sources": [{"content": "Mock source", "score": 0.8}],
                    "citations": [{"title": "Mock Citation", "credibility": 0.9}]
                }
        
        class MockInterpreter:
            async def generate_interpretation(self, data):
                return {
                    "interpretation": "Mock interpretation",
                    "confidence": 0.75,
                    "coherence_score": 0.82
                }
        
        if test_case.category == "rag":
            system = MockRAG()
        elif test_case.category == "interpretation":
            system = MockInterpreter()
        else:
            system = {}
        
        result = await test_suite.run_test_case(test_case, system)
        return {
            "test_case": {
                "id": test_case.id,
                "name": test_case.name,
                "description": test_case.description
            },
            "result": {
                "status": result.status.value,
                "score": result.score,
                "execution_time": result.execution_time,
                "error_message": result.error_message,
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "description": m.description
                    }
                    for m in result.metrics
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

@router.get("/alerts")
async def get_alerts():
    """Get system alerts"""
    active_alerts = observability.alerts.get_active_alerts()
    alert_history = observability.alerts.get_alert_history(hours=24)
    
    return {
        "active_alerts": [
            {
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "description": alert.description,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in active_alerts
        ],
        "recent_alerts": [
            {
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "resolved": alert.resolved,
                "timestamp": alert.timestamp.isoformat(),
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in alert_history
        ]
    }

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    observability.alerts.resolve_alert(alert_id)
    return {"message": f"Alert {alert_id} resolved"}

@router.get("/performance")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    dashboard_data = observability.get_dashboard_data()
    
    return {
        "response_times": {
            "average": dashboard_data["performance"]["avg_response_time"],
            "p95": dashboard_data["performance"]["p95_response_time"]
        },
        "error_rate": dashboard_data["performance"]["error_rate"],
        "cache_performance": {
            "hit_rate": dashboard_data["performance"]["cache_hit_rate"]
        },
        "activity": dashboard_data["activity"],
        "timestamp": dashboard_data["timestamp"]
    }

@router.get("/quality")
async def get_quality_metrics():
    """Get quality metrics"""
    dashboard_data = observability.get_dashboard_data()
    
    return {
        "interpretation_quality": {
            "coherence": dashboard_data["quality"]["interpretation_coherence"],
            "user_satisfaction": dashboard_data["quality"]["user_satisfaction"]
        },
        "rag_quality": {
            "faithfulness": dashboard_data["quality"]["rag_faithfulness"]
        },
        "timestamp": dashboard_data["timestamp"]
    }

@router.post("/simulate-load")
async def simulate_load(requests: int = 100, concurrent: int = 10):
    """Simulate load for testing observability"""
    import asyncio
    import random
    
    async def simulate_request():
        # Simulate API request
        response_time = random.uniform(0.1, 3.0)
        status_code = random.choices([200, 400, 500], weights=[0.9, 0.08, 0.02])[0]
        
        observability.track_api_request(
            endpoint="/test",
            method="GET",
            status_code=status_code,
            response_time=response_time
        )
        
        # Simulate some quality metrics
        if status_code == 200:
            observability.track_interpretation_quality(
                coherence=random.uniform(0.6, 1.0),
                accuracy=random.uniform(0.5, 0.9),
                confidence=random.uniform(0.4, 0.8),
                user_satisfaction=random.uniform(0.3, 1.0)
            )
            
            observability.track_rag_performance(
                recall=random.uniform(0.5, 0.9),
                precision=random.uniform(0.4, 0.8),
                faithfulness=random.uniform(0.6, 0.95),
                response_time=response_time * 0.3
            )
        
        await asyncio.sleep(random.uniform(0.01, 0.1))
    
    # Run concurrent requests
    tasks = []
    for _ in range(requests):
        tasks.append(simulate_request())
        if len(tasks) >= concurrent:
            await asyncio.gather(*tasks)
            tasks = []
    
    if tasks:
        await asyncio.gather(*tasks)
    
    # Update system health
    health_update = observability.update_system_health()
    
    return {
        "message": f"Simulated {requests} requests with {concurrent} concurrent",
        "health_update": health_update
    }