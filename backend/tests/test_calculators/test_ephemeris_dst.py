import math
from datetime import datetime, timezone

from app.calculators.ephemeris import EphemerisService

def test_julian_day_known_epoch():
    ephem = EphemerisService()
    # 2000-01-01 12:00 UTC -> JD 2451545.0
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    jd = ephem.julian_day(dt)
    assert abs(jd - 2451545.0) < 1e-6

def test_istanbul_dst_boundary_2016_mar_27():
    ephem = EphemerisService()
    # UTC tarafında süreklilik kontrolü
    dt1 = datetime(2016, 3, 26, 21, 30, 0, tzinfo=timezone.utc)
    dt2 = datetime(2016, 3, 27, 1, 30, 0, tzinfo=timezone.utc)
    jd1 = ephem.julian_day(dt1)
    jd2 = ephem.julian_day(dt2)
    assert jd2 > jd1
    assert (jd2 - jd1) < 0.25  # < ~6 saat

def test_house_system_mock_fallback():
    ephem = EphemerisService()
    dt = datetime(2020, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
    houses = ephem.calculate_houses(dt, 41.0082, 28.9784, system="W")
    assert len(houses.cusps) == 12
