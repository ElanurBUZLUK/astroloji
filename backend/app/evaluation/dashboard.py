"""Generate simple dashboard snapshots from metrics/alerts."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from .observability import observability


def snapshot(time_window_minutes: int = 60) -> Dict[str, Any]:
    metrics_summary = {
        "response_time": observability.metrics.get_metric_summary("api_response_time", time_window_minutes),
        "rag_latency": observability.metrics.get_metric_summary("rag_latency", time_window_minutes),
        "coverage_score": observability.metrics.get_metric_summary("coverage_score", time_window_minutes),
    }
    alerts = [
        {
            "id": alert.id,
            "level": alert.level.value,
            "title": alert.title,
            "description": alert.description,
            "created_at": alert.timestamp.isoformat(),
            "resolved": alert.resolved,
        }
        for alert in observability.alerts.get_active_alerts()
    ]
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": metrics_summary,
        "active_alerts": alerts,
    }


def export_snapshot(path: str, time_window_minutes: int = 60) -> None:
    data = snapshot(time_window_minutes)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def latest_alert(level: Optional[str] = None) -> Optional[Dict[str, Any]]:
    alerts = observability.alerts.get_active_alerts()
    if level:
        alerts = [a for a in alerts if a.level.value == level]
    if not alerts:
        return None
    alert = sorted(alerts, key=lambda a: a.timestamp)[-1]
    return {
        "id": alert.id,
        "level": alert.level.value,
        "title": alert.title,
        "description": alert.description,
        "created_at": alert.timestamp.isoformat(),
    }
