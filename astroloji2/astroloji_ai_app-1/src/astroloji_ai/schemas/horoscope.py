from pydantic import BaseModel
from typing import List, Optional

class BirthInfo(BaseModel):
    lat: float
    lon: float
    tz: str

class HoroscopeRequest(BaseModel):
    user_id: str
    burc: str
    gun: str
    birth: BirthInfo
    goals: Optional[List[str]] = []

class HoroscopeResponse(BaseModel):
    burc: str
    gun: str
    yorum: str
    confidence: float
    natal: dict
    transit: dict
    dominant_enerjiler: List[str]
    pratik_tavsiyeler: List[str]
    kaynaklar: List[str]
    selected_model: str
    is_fallback: bool