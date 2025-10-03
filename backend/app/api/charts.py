"""
Chart creation and management endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, date
import uuid

from app.calculators.ephemeris import EphemerisService
from app.calculators.almuten import almuten_figuris, Point
from app.calculators.zodiac_releasing import ZRCalculator
from app.calculators.profection import ProfectionCalculator
from app.calculators.firdaria import FirdariaCalculator
from app.calculators.antiscia import AntisciaCalculator
from app.calculators.progressions import ProgressionsCalculator
from app.calculators.solar_arc import SolarArcCalculator
from app.calculators.transits import TransitsCalculator
from app.calculators.midpoints import MidpointsCalculator
from app.calculators.fixed_stars import FixedStarsCalculator
from app.services import ChartService

router = APIRouter()

class BirthData(BaseModel):
    """Birth data input model"""
    birth_date: date = Field(..., description="Birth date")
    birth_time: Optional[str] = Field(None, description="Birth time (HH:MM format)")
    latitude: float = Field(..., ge=-90, le=90, description="Birth latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Birth longitude")
    timezone: str = Field("UTC", description="Timezone identifier")
    place_name: Optional[str] = Field(None, description="Birth place name")

class ChartResponse(BaseModel):
    """Chart response model"""
    chart_id: str
    birth_data: BirthData
    planets: Dict[str, Any]
    houses: Dict[str, Any]
    almuten: Dict[str, Any]
    zodiacal_releasing: Dict[str, Any]
    lots: Dict[str, float]
    is_day_birth: bool
    created_at: datetime

@router.post("/", response_model=Dict[str, Any])
async def create_chart(birth_data: BirthData):
    """Create a new astrological chart with full calculations"""
    try:
        # Generate unique chart ID
        chart_id = str(uuid.uuid4())
        
        # Combine date and time
        if birth_data.birth_time:
            time_parts = birth_data.birth_time.split(":")
            birth_datetime = datetime.combine(
                birth_data.birth_date,
                datetime.min.time().replace(
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]) if len(time_parts) > 1 else 0
                )
            )
        else:
            # Default to noon if no time provided
            birth_datetime = datetime.combine(birth_data.birth_date, datetime.min.time().replace(hour=12))
        
        # Initialize services
        ephemeris = EphemerisService()
        zr_calc = ZRCalculator()
        profection_calc = ProfectionCalculator()
        firdaria_calc = FirdariaCalculator()
        antiscia_calc = AntisciaCalculator()
        progressions_calc = ProgressionsCalculator()
        solar_arc_calc = SolarArcCalculator()
        transits_calc = TransitsCalculator()
        midpoints_calc = MidpointsCalculator()
        fixed_stars_calc = FixedStarsCalculator()
        
        try:
            # Calculate Julian Day
            jd = ephemeris.julian_day(birth_datetime)
            
            # Get planet positions
            planets = ephemeris.get_all_planets(jd)
            
            # Calculate houses
            houses = ephemeris.get_houses(jd, birth_data.latitude, birth_data.longitude)
            
            # Determine day/night birth
            is_day = ephemeris.is_day_birth(planets, houses)
            
            # Calculate lots
            lots = ephemeris.calculate_lots(planets, houses, is_day)
            
            # Prepare points for Almuten calculation
            almuten_points = [
                Point("Sun", planets['Sun'].longitude, planets['Sun'].sign, planets['Sun'].degree_in_sign),
                Point("Moon", planets['Moon'].longitude, planets['Moon'].sign, planets['Moon'].degree_in_sign),
                Point("ASC", houses.asc, _longitude_to_sign(houses.asc), houses.asc % 30),
                Point("MC", houses.mc, _longitude_to_sign(houses.mc), houses.mc % 30),
                Point("Fortune", lots['Fortune'], _longitude_to_sign(lots['Fortune']), lots['Fortune'] % 30),
                Point("Spirit", lots['Spirit'], _longitude_to_sign(lots['Spirit']), lots['Spirit'] % 30)
            ]
            
            # Calculate Almuten Figuris
            chart_data = {"is_day": is_day}
            almuten_result = almuten_figuris(almuten_points, chart_data)
            
            # Calculate Zodiacal Releasing timeline
            zr_timeline = zr_calc.compute_zr_timeline(
                planets['Sun'].longitude,
                planets['Moon'].longitude,
                houses.asc,
                is_day,
                birth_data.birth_date
            )
            
            # Calculate Profection
            profection_result = profection_calc.calculate_profection(
                birth_data.birth_date,
                houses.asc
            )
            
            # Calculate Firdaria
            firdaria_result = firdaria_calc.get_current_firdaria(
                birth_data.birth_date,
                is_day
            )
            
            # Calculate Antiscia
            planet_longitudes = {name: pos.longitude for name, pos in planets.items()}
            antiscia_result = antiscia_calc.get_antiscia_summary(planet_longitudes)

            # Calculate Progressions (Secondary)
            progressions_result = progressions_calc.get_current_progressions(planet_longitudes, birth_data.birth_date)

            # Calculate Solar Arc Directions
            solar_arc_result = solar_arc_calc.get_current_solar_arc_directions(planet_longitudes, birth_data.birth_date)

            # Calculate Transits (current)
            # Note: For transits we need current positions, using simplified calculation
            transits_result = transits_calc.get_major_transits(planet_longitudes, planet_longitudes)

            # Calculate Midpoints
            midpoints_result = midpoints_calc.get_major_midpoints_summary(planet_longitudes)

            # Calculate Fixed Stars
            fixed_stars_result = fixed_stars_calc.get_star_contacts_summary(planet_longitudes)
            
            # Prepare calculations data for storage
            calculations_data = {
                "planets": {
                    name: {
                        "longitude": pos.longitude,
                        "sign": pos.sign,
                        "degree_in_sign": pos.degree_in_sign,
                        "is_retrograde": pos.is_retrograde,
                        "speed": pos.speed_longitude
                    }
                    for name, pos in planets.items()
                },
                "houses": {
                    "system": "placidus",
                    "cusps": houses.cusps,
                    "asc": houses.asc,
                    "mc": houses.mc,
                    "asc_sign": _longitude_to_sign(houses.asc),
                    "mc_sign": _longitude_to_sign(houses.mc)
                },
                "almuten": {
                    "winner": almuten_result.winner,
                    "scores": almuten_result.scores,
                    "tie_break_reason": almuten_result.tie_break_reason,
                    "diagnostics": almuten_result.diagnostics
                },
                "zodiacal_releasing": {
                    "lot_used": zr_timeline.lot_used,
                    "current_periods": _get_current_zr_periods(zr_timeline, datetime.now().date()),
                    "next_peaks": _get_next_peaks(zr_timeline, datetime.now().date()),
                    "diagnostics": zr_timeline.diagnostics
                },
                "profection": {
                    "age": profection_result.age,
                    "profected_house": profection_result.profected_house,
                    "profected_sign": profection_result.profected_sign,
                    "year_lord": profection_result.year_lord,
                    "activated_topics": profection_result.activated_topics
                },
                "firdaria": firdaria_result,
                                    "antiscia": {
                        "summary": antiscia_result["summary"],
                        "strongest_contacts": antiscia_calc.get_strongest_antiscia_contacts(planet_longitudes, limit=3)
                    },
                    "progressions": progressions_result,
                    "solar_arc": solar_arc_result,
                    "transits": transits_result,
                    "midpoints": midpoints_result,
                    "fixed_stars": fixed_stars_result,
                    "lots": lots,
                    "is_day_birth": is_day
                }

            # Save to database
            saved = ChartService.save_chart(
                chart_id=chart_id,
                birth_data=birth_data.dict(),
                calculations=calculations_data
            )

            if not saved:
                print("Warning: Failed to save chart to database")

            # Format response
            response = {
                "chart_id": chart_id,
                "status": "completed",
                "birth_data": birth_data.dict(),
                "calculations": calculations_data,
                "created_at": datetime.now(),
                "stored_in_db": saved
            }

            return response
            
        finally:
            ephemeris.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chart calculation failed: {str(e)}"
        )

@router.get("/{chart_id}")
async def get_chart(chart_id: str):
    """Get chart by ID"""
    try:
        chart = ChartService.get_chart(chart_id)
        if chart:
            return chart
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chart with ID {chart_id} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chart: {str(e)}"
        )

def _longitude_to_sign(longitude: float) -> str:
    """Convert longitude to zodiac sign"""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[int(longitude // 30)]

def _get_current_zr_periods(timeline, current_date: date) -> Dict[str, Any]:
    """Get current ZR periods for given date"""
    current_l1 = None
    current_l2 = None
    
    # Find current L1 period
    for period in timeline.l1_periods:
        if period.start_date <= current_date <= period.end_date:
            current_l1 = {
                "level": period.level,
                "sign": period.sign,
                "ruler": period.ruler,
                "start_date": period.start_date.isoformat(),
                "end_date": period.end_date.isoformat(),
                "is_peak": period.is_peak,
                "is_lb": period.is_lb,
                "tone": period.tone
            }
            break
    
    # Find current L2 period
    for period in timeline.l2_periods:
        if period.start_date <= current_date <= period.end_date:
            current_l2 = {
                "level": period.level,
                "sign": period.sign,
                "ruler": period.ruler,
                "start_date": period.start_date.isoformat(),
                "end_date": period.end_date.isoformat(),
                "is_peak": period.is_peak,
                "is_lb": period.is_lb,
                "tone": period.tone
            }
            break
    
    return {
        "l1": current_l1,
        "l2": current_l2
    }

def _get_next_peaks(timeline, current_date: date) -> list:
    """Get next peak periods"""
    next_peaks = []
    
    for period in timeline.l1_periods:
        if period.is_peak and period.start_date > current_date:
            next_peaks.append({
                "level": period.level,
                "sign": period.sign,
                "ruler": period.ruler,
                "start_date": period.start_date.isoformat(),
                "end_date": period.end_date.isoformat(),
                "years_from_now": (period.start_date - current_date).days / 365.25
            })
            if len(next_peaks) >= 3:  # Limit to next 3 peaks
                break
    
    return next_peaks