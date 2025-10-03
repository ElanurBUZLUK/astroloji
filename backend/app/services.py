"""
Database services for charts and interpretations
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from .models import (
    Chart,
    Interpretation,
    ZRPeriod,
    ProfectionPeriod,
    FirdariaPeriod,
)
from .database import get_db_session
import json

class ChartService:
    """Service for chart database operations"""

    @staticmethod
    def save_chart(chart_id: str, birth_data: Dict[str, Any],
                   calculations: Dict[str, Any]) -> bool:
        """Save chart to database"""
        session = get_db_session()
        try:
            # Extract birth data
            birth_date = birth_data.get('birth_date', '')
            birth_time = birth_data.get('birth_time')
            latitude = birth_data.get('latitude', 0.0)
            longitude = birth_data.get('longitude', 0.0)
            timezone = birth_data.get('timezone', 'UTC')
            place_name = birth_data.get('place_name')

            # Extract calculations
            planets = calculations.get('planets', {})
            houses = calculations.get('houses', {})
            almuten = calculations.get('almuten', {})
            zodiacal_releasing = calculations.get('zodiacal_releasing', {})
            lots = calculations.get('lots', {})
            is_day_birth = 1 if calculations.get('is_day_birth', False) else 0

            # Additional data
            profection = calculations.get('profection')
            firdaria = calculations.get('firdaria')
            antiscia = calculations.get('antiscia')

            # Create chart record
            chart = Chart(
                id=chart_id,
                birth_date=str(birth_date),
                birth_time=birth_time,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                place_name=place_name,
                planets=json.dumps(planets),
                houses=json.dumps(houses),
                almuten=json.dumps(almuten),
                zodiacal_releasing=json.dumps(zodiacal_releasing),
                lots=json.dumps(lots),
                lots_data=json.dumps(lots),  # Duplicate for now
                is_day_birth=is_day_birth,
                profection=json.dumps(profection) if profection else None,
                firdaria=json.dumps(firdaria) if firdaria else None,
                antiscia=json.dumps(antiscia) if antiscia else None
            )

            session.add(chart)
            session.flush()

            ChartService._upsert_zr_periods(session, chart.id, zodiacal_releasing)
            ChartService._upsert_profection_period(session, chart.id, profection)
            ChartService._upsert_firdaria_periods(session, chart.id, firdaria)

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error saving chart: {e}")
            return False
        finally:
            session.close()

    @staticmethod
    def _upsert_zr_periods(session: Session, chart_id: str, zr_data: Dict[str, Any]) -> None:
        session.query(ZRPeriod).filter(ZRPeriod.chart_id == chart_id).delete()
        if not zr_data:
            return
        periods = zr_data.get("current_periods", {})
        for level_key, level in ("l1", 1), ("l2", 2):
            level_data = periods.get(level_key)
            if not level_data:
                continue
            session.add(
                ZRPeriod(
                    chart_id=chart_id,
                    level=level,
                    sign=level_data.get("sign", ""),
                    ruler=level_data.get("ruler", ""),
                    start_date=ChartService._parse_date(level_data.get("start_date")),
                    end_date=ChartService._parse_date(level_data.get("end_date")),
                    is_peak=1 if level_data.get("is_peak") else 0,
                    is_lb=1 if level_data.get("is_lb") else 0,
                    tone=level_data.get("tone"),
                )
            )

    @staticmethod
    def _upsert_profection_period(session: Session, chart_id: str, profection: Optional[Dict[str, Any]]) -> None:
        session.query(ProfectionPeriod).filter(ProfectionPeriod.chart_id == chart_id).delete()
        if not profection:
            return
        session.add(
            ProfectionPeriod(
                chart_id=chart_id,
                age=profection.get("age", 0),
                profected_house=profection.get("profected_house", 0),
                profected_sign=profection.get("profected_sign", ""),
                year_lord=profection.get("year_lord"),
                activated_topics=profection.get("activated_topics"),
            )
        )

    @staticmethod
    def _upsert_firdaria_periods(session: Session, chart_id: str, firdaria: Optional[Dict[str, Any]]) -> None:
        session.query(FirdariaPeriod).filter(FirdariaPeriod.chart_id == chart_id).delete()
        if not firdaria:
            return
        for period_type in ("current_major", "current_minor"):
            pdata = firdaria.get(period_type)
            if not pdata:
                continue
            session.add(
                FirdariaPeriod(
                    chart_id=chart_id,
                    period_type="major" if period_type == "current_major" else "minor",
                    lord=pdata.get("lord", ""),
                    start_date=ChartService._parse_date(pdata.get("start_date")),
                    end_date=ChartService._parse_date(pdata.get("end_date")),
                )
            )

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    @staticmethod
    def get_chart(chart_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve chart from database"""
        session = get_db_session()
        try:
            chart = session.query(Chart).filter(Chart.id == chart_id).first()
            if not chart:
                return None

            # Convert back to dictionary format
            zr_periods = [
                {
                    "level": period.level,
                    "sign": period.sign,
                    "ruler": period.ruler,
                    "start_date": period.start_date.isoformat() if period.start_date else None,
                    "end_date": period.end_date.isoformat() if period.end_date else None,
                    "is_peak": bool(period.is_peak),
                    "is_lb": bool(period.is_lb),
                    "tone": period.tone,
                }
                for period in chart.zr_periods
            ]
            profection_periods = [
                {
                    "age": period.age,
                    "profected_house": period.profected_house,
                    "profected_sign": period.profected_sign,
                    "year_lord": period.year_lord,
                    "activated_topics": period.activated_topics,
                }
                for period in chart.profection_periods
            ]
            firdaria_periods = [
                {
                    "period_type": period.period_type,
                    "lord": period.lord,
                    "start_date": period.start_date.isoformat() if period.start_date else None,
                    "end_date": period.end_date.isoformat() if period.end_date else None,
                }
                for period in chart.firdaria_periods
            ]

            return {
                "chart_id": chart.id,
                "birth_data": {
                    "birth_date": chart.birth_date,
                    "birth_time": chart.birth_time,
                    "latitude": chart.latitude,
                    "longitude": chart.longitude,
                    "timezone": chart.timezone,
                    "place_name": chart.place_name
                },
                "calculations": {
                    "planets": json.loads(chart.planets) if chart.planets else {},
                    "houses": json.loads(chart.houses) if chart.houses else {},
                    "almuten": json.loads(chart.almuten) if chart.almuten else {},
                    "zodiacal_releasing": json.loads(chart.zodiacal_releasing) if chart.zodiacal_releasing else {},
                    "lots": json.loads(chart.lots) if chart.lots else {},
                    "is_day_birth": bool(chart.is_day_birth),
                    "profection": json.loads(chart.profection) if chart.profection else None,
                    "firdaria": json.loads(chart.firdaria) if chart.firdaria else None,
                    "antiscia": json.loads(chart.antiscia) if chart.antiscia else None
                },
                "created_at": chart.created_at.isoformat() if chart.created_at else None,
                "status": "stored",
                "normalized": {
                    "zr_periods": zr_periods,
                    "profection_periods": profection_periods,
                    "firdaria_periods": firdaria_periods,
                },
            }

        except Exception as e:
            print(f"Error retrieving chart: {e}")
            return None
        finally:
            session.close()

class InterpretationService:
    """Service for interpretation database operations"""

    @staticmethod
    def save_interpretation(interpretation_id: str, chart_id: str,
                           query: str, mode: str, interpretation: str,
                           confidence_score: float, sources: Optional[Dict] = None) -> bool:
        """Save interpretation to database"""
        session = get_db_session()
        try:
            interp = Interpretation(
                id=interpretation_id,
                chart_id=chart_id,
                query=query,
                mode=mode,
                interpretation=interpretation,
                confidence_score=confidence_score,
                sources=json.dumps(sources) if sources else None
            )

            session.add(interp)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error saving interpretation: {e}")
            return False
        finally:
            session.close()

    @staticmethod
    def get_interpretation(interpretation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve interpretation from database"""
        session = get_db_session()
        try:
            interp = session.query(Interpretation).filter(Interpretation.id == interpretation_id).first()
            if not interp:
                return None

            return {
                "id": interp.id,
                "chart_id": interp.chart_id,
                "query": interp.query,
                "mode": interp.mode,
                "interpretation": interp.interpretation,
                "confidence_score": interp.confidence_score,
                "sources": json.loads(interp.sources) if interp.sources else None,
                "created_at": interp.created_at.isoformat() if interp.created_at else None
            }

        except Exception as e:
            print(f"Error retrieving interpretation: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_chart_interpretations(chart_id: str) -> list:
        """Get all interpretations for a chart"""
        session = get_db_session()
        try:
            interpretations = session.query(Interpretation).filter(Interpretation.chart_id == chart_id).all()
            return [{
                "id": interp.id,
                "query": interp.query,
                "mode": interp.mode,
                "confidence_score": interp.confidence_score,
                "created_at": interp.created_at.isoformat() if interp.created_at else None
            } for interp in interpretations]

        except Exception as e:
            print(f"Error retrieving chart interpretations: {e}")
            return []
        finally:
            session.close()

class AlertService:
    """Service for alert database operations"""

    @staticmethod
    def create_alert(alert_type: str, severity: str, title: str,
                    message: str, metadata: Optional[Dict] = None, user_id: Optional[str] = None) -> Optional[str]:
        """Create a new alert"""
        from app.models import Alert
        import uuid

        session = get_db_session()
        try:
            alert_id = str(uuid.uuid4())
            alert = Alert(
                id=alert_id,
                user_id=user_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                metadata_info=json.dumps(metadata) if metadata else None
            )

            session.add(alert)
            session.commit()
            return alert_id

        except Exception as e:
            session.rollback()
            print(f"Error creating alert: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_alerts(user_id: Optional[str] = None, include_resolved: bool = False) -> list:
        """Get alerts for a user or all alerts if no user specified"""
        from app.models import Alert

        session = get_db_session()
        try:
            query = session.query(Alert)
            if user_id:
                query = query.filter(Alert.user_id == user_id)
            if not include_resolved:
                query = query.filter(Alert.is_resolved == 0)

            alerts = query.order_by(Alert.created_at.desc()).all()

            return [{
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "metadata": json.loads(alert.metadata_info) if alert.metadata_info else None,
                "is_read": bool(alert.is_read),
                "is_resolved": bool(alert.is_resolved),
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            } for alert in alerts]

        except Exception as e:
            print(f"Error retrieving alerts: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def mark_as_read(alert_id: str) -> bool:
        """Mark alert as read"""
        from app.models import Alert

        session = get_db_session()
        try:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.is_read = 1
                session.commit()
                return True
            return False

        except Exception as e:
            session.rollback()
            print(f"Error marking alert as read: {e}")
            return False
        finally:
            session.close()

    @staticmethod
    def resolve_alert(alert_id: str) -> bool:
        """Resolve an alert"""
        from app.models import Alert
        from datetime import datetime

        session = get_db_session()
        try:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.is_resolved = 1
                alert.resolved_at = datetime.utcnow()
                session.commit()
                return True
            return False

        except Exception as e:
            session.rollback()
            print(f"Error resolving alert: {e}")
            return False
        finally:
            session.close()
