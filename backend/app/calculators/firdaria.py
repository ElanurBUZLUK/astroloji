"""
Firdaria (Persian Periods) calculator
"""
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class FirdarPeriod:
    """Firdaria period information"""
    level: str  # "major" or "minor"
    lord: str
    start_date: date
    end_date: date
    duration_years: float
    sequence_number: int

@dataclass
class FirdariaResult:
    """Complete Firdaria calculation result"""
    major_periods: List[FirdarPeriod]
    minor_periods: List[FirdarPeriod]
    current_major: FirdarPeriod = None
    current_minor: FirdarPeriod = None
    diagnostics: Dict[str, Any] = None

class FirdariaCalculator:
    """Firdaria (Persian Periods) calculator"""
    
    # Diurnal (Day) sequence and durations
    DIURNAL_SEQUENCE = [
        ("Sun", 10),
        ("Venus", 8),
        ("Mercury", 13),
        ("Moon", 9),
        ("Saturn", 11),
        ("Jupiter", 12),
        ("Mars", 7)
    ]
    
    # Nocturnal (Night) sequence and durations
    NOCTURNAL_SEQUENCE = [
        ("Moon", 9),
        ("Saturn", 11),
        ("Jupiter", 12),
        ("Mars", 7),
        ("Sun", 10),
        ("Venus", 8),
        ("Mercury", 13)
    ]
    
    def __init__(self):
        pass
    
    def calculate_firdaria(self, birth_date: date, is_day_birth: bool) -> FirdariaResult:
        """
        Calculate complete Firdaria timeline
        
        Args:
            birth_date: Birth date
            is_day_birth: True for day birth, False for night birth
        """
        # Choose sequence based on sect
        sequence = self.DIURNAL_SEQUENCE if is_day_birth else self.NOCTURNAL_SEQUENCE
        
        # Calculate major periods
        major_periods = self._calculate_major_periods(birth_date, sequence)
        
        # Calculate minor periods for each major period
        minor_periods = []
        for major_period in major_periods:
            minor_periods.extend(self._calculate_minor_periods(major_period, sequence))
        
        # Find current periods
        today = date.today()
        current_major = self._find_current_period(major_periods, today)
        current_minor = self._find_current_period(minor_periods, today)
        
        return FirdariaResult(
            major_periods=major_periods,
            minor_periods=minor_periods,
            current_major=current_major,
            current_minor=current_minor,
            diagnostics={
                "birth_date": birth_date.isoformat(),
                "is_day_birth": is_day_birth,
                "sequence_type": "diurnal" if is_day_birth else "nocturnal",
                "total_major_periods": len(major_periods),
                "total_minor_periods": len(minor_periods)
            }
        )
    
    def _calculate_major_periods(self, birth_date: date, sequence: List[Tuple[str, int]]) -> List[FirdarPeriod]:
        """Calculate major Firdaria periods"""
        periods = []
        current_date = birth_date
        
        for seq_num, (lord, duration) in enumerate(sequence, 1):
            end_date = current_date + timedelta(days=duration * 365.25)
            
            period = FirdarPeriod(
                level="major",
                lord=lord,
                start_date=current_date,
                end_date=end_date,
                duration_years=duration,
                sequence_number=seq_num
            )
            
            periods.append(period)
            current_date = end_date
        
        return periods
    
    def _calculate_minor_periods(self, major_period: FirdarPeriod, 
                               sequence: List[Tuple[str, int]]) -> List[FirdarPeriod]:
        """Calculate minor periods within a major period using weighted durations"""
        minor_periods = []
        
        # Find the major lord's position in sequence
        major_lord_index = next(i for i, (lord, _) in enumerate(sequence) if lord == major_period.lord)
        
        # Create minor period sequence starting from major lord
        minor_sequence = []
        for i in range(len(sequence)):
            index = (major_lord_index + i) % len(sequence)
            minor_sequence.append(sequence[index])
        
        # Calculate weighted durations based on each lord's major period duration
        total_weight = sum(duration for _, duration in minor_sequence)
        total_days = (major_period.end_date - major_period.start_date).days
        
        current_date = major_period.start_date
        
        for seq_num, (minor_lord, lord_duration) in enumerate(minor_sequence, 1):
            # Calculate proportional duration based on lord's major period weight
            weight_fraction = lord_duration / total_weight
            minor_duration_days = total_days * weight_fraction
            
            end_date = current_date + timedelta(days=minor_duration_days)
            
            # Ensure last minor period ends exactly with major period
            if seq_num == len(minor_sequence):
                end_date = major_period.end_date
            
            minor_period = FirdarPeriod(
                level="minor",
                lord=minor_lord,
                start_date=current_date,
                end_date=end_date,
                duration_years=minor_duration_days / 365.25,
                sequence_number=seq_num
            )
            
            minor_periods.append(minor_period)
            current_date = end_date
        
        return minor_periods
    
    def _find_current_period(self, periods: List[FirdarPeriod], target_date: date) -> FirdarPeriod:
        """Find the period that contains the target date"""
        for period in periods:
            if period.start_date <= target_date <= period.end_date:
                return period
        return None
    
    def get_current_firdaria(self, birth_date: date, is_day_birth: bool) -> Dict[str, Any]:
        """Get current Firdaria periods with context"""
        result = self.calculate_firdaria(birth_date, is_day_birth)
        
        return {
            "current_major": {
                "lord": result.current_major.lord if result.current_major else None,
                "start_date": result.current_major.start_date.isoformat() if result.current_major else None,
                "end_date": result.current_major.end_date.isoformat() if result.current_major else None,
                "duration_years": result.current_major.duration_years if result.current_major else None,
                "sequence_number": result.current_major.sequence_number if result.current_major else None
            },
            "current_minor": {
                "lord": result.current_minor.lord if result.current_minor else None,
                "start_date": result.current_minor.start_date.isoformat() if result.current_minor else None,
                "end_date": result.current_minor.end_date.isoformat() if result.current_minor else None,
                "duration_years": result.current_minor.duration_years if result.current_minor else None,
                "sequence_number": result.current_minor.sequence_number if result.current_minor else None
            },
            "diagnostics": result.diagnostics
        }
    
    def get_firdaria_timeline(self, birth_date: date, is_day_birth: bool, 
                            years_ahead: int = 20) -> Dict[str, Any]:
        """Get Firdaria timeline for specified years ahead"""
        result = self.calculate_firdaria(birth_date, is_day_birth)
        
        # Filter periods within the specified timeframe
        cutoff_date = date.today() + timedelta(days=years_ahead * 365.25)
        
        relevant_major = [p for p in result.major_periods if p.start_date <= cutoff_date]
        relevant_minor = [p for p in result.minor_periods if p.start_date <= cutoff_date]
        
        return {
            "major_periods": [
                {
                    "lord": p.lord,
                    "start_date": p.start_date.isoformat(),
                    "end_date": p.end_date.isoformat(),
                    "duration_years": p.duration_years,
                    "sequence_number": p.sequence_number
                }
                for p in relevant_major
            ],
            "minor_periods": [
                {
                    "lord": p.lord,
                    "start_date": p.start_date.isoformat(),
                    "end_date": p.end_date.isoformat(),
                    "duration_years": p.duration_years,
                    "sequence_number": p.sequence_number
                }
                for p in relevant_minor
            ],
            "current": self.get_current_firdaria(birth_date, is_day_birth),
            "diagnostics": result.diagnostics
        }
    
    def get_lord_themes(self, lord: str) -> List[str]:
        """Get thematic keywords for Firdaria lords"""
        themes = {
            "Sun": ["Authority", "Leadership", "Recognition", "Vitality", "Father"],
            "Moon": ["Emotions", "Public", "Changes", "Mother", "Intuition"],
            "Mercury": ["Communication", "Learning", "Travel", "Commerce", "Siblings"],
            "Venus": ["Relationships", "Beauty", "Arts", "Pleasure", "Women"],
            "Mars": ["Action", "Conflict", "Energy", "Competition", "Brothers"],
            "Jupiter": ["Expansion", "Wisdom", "Teaching", "Religion", "Fortune"],
            "Saturn": ["Structure", "Discipline", "Limitations", "Elders", "Karma"]
        }
        
        return themes.get(lord, ["Unknown themes"])