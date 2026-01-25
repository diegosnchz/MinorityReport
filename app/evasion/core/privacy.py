import hashlib
from typing import Dict, Any

class PrivacyMiddleware:
    """
    Capa de ofuscación para proteger la identidad de los operativos
    y los escondites seguros.
    """
    
    @staticmethod
    def hash_id(real_id: str) -> str:
        """SHA-256 hashing for User IDs."""
        return hashlib.sha256(real_id.encode()).hexdigest()[:12]

    @staticmethod
    def aggregate_coordinates(lat: float, lon: float, precision: int = 2) -> Dict[str, float]:
        """
        Redondea coordenadas para analytics visuales (aprox. 1km).
        Evita revelar la ubicación exacta de pisos francos.
        """
        return {
            "lat": round(lat, precision),
            "lon": round(lon, precision)
        }

    @staticmethod
    def sanitize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia un payload completo antes de enviarlo al Dashboard."""
        sanitized = data.copy()
        if "user_id" in sanitized:
            sanitized["user_id"] = PrivacyMiddleware.hash_id(sanitized["user_id"])
        
        if "lat" in sanitized and "lon" in sanitized:
            coords = PrivacyMiddleware.aggregate_coordinates(sanitized["lat"], sanitized["lon"])
            sanitized["lat"] = coords["lat"]
            sanitized["lon"] = coords["lon"]
            
        return sanitized
