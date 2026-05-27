"""
Weather Utilities - Weather data processing and formatting
"""
from typing import Dict, Optional


def formatWindDirection(degrees: Optional[float]) -> str:
    """Convert wind direction degrees to compass direction"""
    if degrees is None:
        return 'N/A'
    
    degNorm = degrees % 360
    dirs = [
        'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
    ]
    idx = int((degNorm / 22.5) + 0.5) % len(dirs)
    return dirs[idx]


def formatWeatherData(weatherFrame: Dict) -> Dict:
    """Format weather data for display"""
    if not weatherFrame:
        return {}
    
    return {
        'trackTemp': round(weatherFrame.get('trackTemp', 0), 1),
        'airTemp': round(weatherFrame.get('airTemp', 0), 1),
        'humidity': round(weatherFrame.get('humidity', 0), 0),
        'windSpeed': round(weatherFrame.get('windSpeed', 0), 1),
        'windDirection': formatWindDirection(weatherFrame.get('windDirection')),
        'windDirectionDeg': weatherFrame.get('windDirection'),
        'rainState': weatherFrame.get('rainState', 'DRY')
    }
