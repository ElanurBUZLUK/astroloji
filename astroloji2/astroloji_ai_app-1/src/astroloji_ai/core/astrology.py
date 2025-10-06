from typing import Dict, Any
import math

def zodiac_sign(degree: float) -> str:
    signs = [
        (0, "Koç"), (30, "Boğa"), (60, "İkizler"), (90, "Yengeç"),
        (120, "Aslan"), (150, "Başak"), (180, "Terazi"), (210, "Akrep"),
        (240, "Yay"), (270, "Oğlak"), (300, "Kova"), (330, "Balık")
    ]
    for boundary, sign in signs:
        if degree < boundary:
            return sign
    return "Balık"

def calculate_aspects(positions: Dict[str, Any], ephemeris: Any) -> list[Dict[str, Any]]:
    aspects = []
    planets = list(positions.keys())
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            angle = abs(positions[planets[i]]["lon_deg"] - positions[planets[j]]["lon_deg"])
            angle = angle if angle <= 360 else angle - 360
            if angle in [0, 60, 90, 120, 180]:
                aspects.append({
                    "from": planets[i],
                    "to": planets[j],
                    "angle": angle,
                    "type": "conjunction" if angle == 0 else "trine" if angle == 120 else "square" if angle == 90 else "opposition" if angle == 180 else "sextile"
                })
    return aspects

def dominant_energies(positions: Dict[str, Any]) -> list[str]:
    energy_count = {}
    for planet, data in positions.items():
        sign = zodiac_sign(data["lon_deg"])
        energy_count[sign] = energy_count.get(sign, 0) + 1
    dominant = sorted(energy_count.items(), key=lambda item: item[1], reverse=True)
    return [sign for sign, count in dominant[:3]]

def house_label(house_number: int) -> str:
    house_labels = {
        1: "Kendilik", 2: "Mali", 3: "İletişim", 4: "Aile",
        5: "Aşk", 6: "Sağlık", 7: "Evlilik", 8: "Ortaklık",
        9: "Felsefe", 10: "Kariyer", 11: "Arkadaşlık", 12: "Bilinçaltı"
    }
    return house_labels.get(house_number, "Bilinmeyen")