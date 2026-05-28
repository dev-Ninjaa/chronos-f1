"""
Intelligence Engine - Central telemetry analysis and insight generation
Produces normalized structured insights consumed by all AI features
"""
from typing import Dict, List, Optional, Any
import numpy as np


class IntelligenceEngine:
    """
    Central intelligence layer that consumes raw telemetry and produces
    normalized structured insights for all AI features to consume.
    
    Avoids duplicated logic across Fan Mode, Engineer Mode, Race Debrief, and Ghost System.
    """
    
    def __init__(self):
        self.previousFrame = None
        self.eventHistory = []
        self.maxHistorySize = 1000
        
    def analyzeFrame(self, currentFrame: Dict, previousFrame: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a single frame and produce structured insights.
        
        Returns:
            {
                "timestamp": float,
                "lap": int,
                "events": [
                    {
                        "driver": str,
                        "event": str,  # "DRS Activation", "Pit Stop", "Overtake", etc.
                        "gap_change": float,
                        "tyre_health": int,
                        "weather": str,
                        "confidence": float,
                        "metadata": dict
                    }
                ],
                "driver_states": {
                    "VER": {
                        "position": int,
                        "speed": float,
                        "gap_to_leader": float,
                        "interval_gap": float,
                        "tyre_compound": str,
                        "tyre_age": int,
                        "tyre_health": int,
                        "drs_active": bool,
                        "in_pit": bool,
                        "sector_performance": dict
                    }
                },
                "race_state": {
                    "leader": str,
                    "safety_car": bool,
                    "track_status": str,
                    "weather_condition": str
                }
            }
        """
        if not currentFrame:
            return self._emptyInsight()
        
        frame = currentFrame.get('frame', currentFrame)
        timestamp = currentFrame.get('t', frame.get('t', 0))
        drivers = frame.get('drivers', {})
        weather = currentFrame.get('weather', {})
        trackStatus = currentFrame.get('trackStatus', '1')
        
        # Detect events
        events = self._detectEvents(currentFrame, previousFrame or self.previousFrame)
        
        # Analyze driver states
        driverStates = self._analyzeDriverStates(drivers, weather)
        
        # Analyze race state
        raceState = self._analyzeRaceState(currentFrame, driverStates)
        
        # Build insight object
        insight = {
            "timestamp": timestamp,
            "lap": self._getLeaderLap(drivers),
            "events": events,
            "driver_states": driverStates,
            "race_state": raceState
        }
        
        # Store in history
        self._addToHistory(insight)
        
        # Update previous frame
        self.previousFrame = currentFrame
        
        return insight

    def _coerceNumber(self, value: Any, default: float = 0.0) -> float:
        """Coerce telemetry values that may be nested/typed oddly into a number."""
        if value is None:
            return float(default)
        if isinstance(value, (int, float, np.integer, np.floating)):
            return float(value)
        if isinstance(value, dict):
            # Common pattern: tyre model returns {"health": <num>, ...}
            if 'health' in value:
                return self._coerceNumber(value.get('health'), default=default)
            if 'value' in value:
                return self._coerceNumber(value.get('value'), default=default)
        try:
            return float(value)
        except Exception:
            return float(default)

    def _getTyreHealth(self, driverData: Dict, default: float = 100.0) -> float:
        return self._coerceNumber(driverData.get('tyreHealth', default), default=default)
    
    def _detectEvents(self, currentFrame: Dict, previousFrame: Optional[Dict]) -> List[Dict]:
        """Detect racing events between frames"""
        if not previousFrame:
            return []
        
        events = []
        
        currentDrivers = currentFrame.get('frame', currentFrame).get('drivers', {})
        previousDrivers = previousFrame.get('frame', previousFrame).get('drivers', {})
        weather = currentFrame.get('weather', {})
        
        for driver, currentData in currentDrivers.items():
            if driver not in previousDrivers:
                continue
            
            prevData = previousDrivers[driver]
            
            # DRS Activation
            if currentData.get('drs', 0) > 0 and prevData.get('drs', 0) == 0:
                events.append({
                    "driver": driver,
                    "event": "DRS Activation",
                    "gap_change": self._calculateGapChange(currentData, prevData),
                    "tyre_health": self._getTyreHealth(currentData),
                    "weather": weather.get('rainState', 'DRY'),
                    "confidence": 0.95,
                    "metadata": {
                        "speed": currentData.get('speed', 0),
                        "position": currentData.get('position', 0)
                    }
                })
            
            # Pit Stop
            if currentData.get('inPit', False) and not prevData.get('inPit', False):
                events.append({
                    "driver": driver,
                    "event": "Pit Stop",
                    "gap_change": 0.0,
                    "tyre_health": 100,  # Fresh tyres
                    "weather": weather.get('rainState', 'DRY'),
                    "confidence": 0.98,
                    "metadata": {
                        "old_tyre": self._getTyreCompoundName(prevData.get('tyre', 0)),
                        "new_tyre": self._getTyreCompoundName(currentData.get('tyre', 0)),
                        "lap": currentData.get('lap', 0)
                    }
                })
            
            # Overtake
            currentPos = currentData.get('position', 999)
            prevPos = prevData.get('position', 999)
            if currentPos < prevPos and currentPos > 0:
                events.append({
                    "driver": driver,
                    "event": "Overtake",
                    "gap_change": -(prevPos - currentPos),
                    "tyre_health": self._getTyreHealth(currentData),
                    "weather": weather.get('rainState', 'DRY'),
                    "confidence": 0.90,
                    "metadata": {
                        "from_position": prevPos,
                        "to_position": currentPos,
                        "speed": currentData.get('speed', 0)
                    }
                })
            
            # High Speed Achievement
            speed = currentData.get('speed', 0)
            if speed > 320 and prevData.get('speed', 0) <= 320:
                events.append({
                    "driver": driver,
                    "event": "High Speed",
                    "gap_change": 0.0,
                    "tyre_health": self._getTyreHealth(currentData),
                    "weather": weather.get('rainState', 'DRY'),
                    "confidence": 0.85,
                    "metadata": {
                        "speed": speed,
                        "gear": currentData.get('gear', 0)
                    }
                })
            
            # Tyre Degradation Warning
            tyreHealth = self._getTyreHealth(currentData, default=100.0)
            prevTyreHealth = self._getTyreHealth(prevData, default=100.0)
            if tyreHealth < 40 and prevTyreHealth >= 40:
                events.append({
                    "driver": driver,
                    "event": "Tyre Degradation",
                    "gap_change": 0.0,
                    "tyre_health": tyreHealth,
                    "weather": weather.get('rainState', 'DRY'),
                    "confidence": 0.80,
                    "metadata": {
                        "tyre_compound": self._getTyreCompoundName(currentData.get('tyre', 0)),
                        "tyre_age": currentData.get('tyreLife', 0)
                    }
                })
            
            # Gap Closing (within DRS range)
            intervalGap = currentData.get('intervalGap', 999)
            prevIntervalGap = prevData.get('intervalGap', 999)
            if intervalGap < 1.0 and prevIntervalGap >= 1.0:
                events.append({
                    "driver": driver,
                    "event": "DRS Range",
                    "gap_change": intervalGap - prevIntervalGap,
                    "tyre_health": self._getTyreHealth(currentData),
                    "weather": weather.get('rainState', 'DRY'),
                    "confidence": 0.88,
                    "metadata": {
                        "gap": intervalGap,
                        "position": currentPos
                    }
                })
        
        return events
    
    def _analyzeDriverStates(self, drivers: Dict, weather: Dict) -> Dict[str, Dict]:
        """Analyze current state of all drivers"""
        states = {}
        
        for driver, data in drivers.items():
            states[driver] = {
                "position": data.get('position', 0),
                "speed": data.get('speed', 0),
                "gap_to_leader": data.get('gapToLeader', 0),
                "interval_gap": data.get('intervalGap', 0),
                "tyre_compound": self._getTyreCompoundName(data.get('tyre', 0)),
                "tyre_age": data.get('tyreLife', 0),
                "tyre_health": self._getTyreHealth(data),
                "drs_active": data.get('drs', 0) > 0,
                "in_pit": data.get('inPit', False),
                "throttle": data.get('throttle', 0),
                "brake": data.get('brake', 0),
                "gear": data.get('gear', 0),
                "lap": data.get('lap', 0),
                "sector_performance": self._calculateSectorPerformance(data)
            }
        
        return states
    
    def _analyzeRaceState(self, currentFrame: Dict, driverStates: Dict) -> Dict:
        """Analyze overall race state"""
        # Find leader
        leader = None
        minPos = 999
        for driver, state in driverStates.items():
            if state['position'] < minPos and state['position'] > 0:
                minPos = state['position']
                leader = driver
        
        trackStatus = currentFrame.get('trackStatus', '1')
        weather = currentFrame.get('weather', {})
        
        return {
            "leader": leader,
            "safety_car": trackStatus in ['4', '6'],  # SC or VSC
            "track_status": trackStatus,
            "weather_condition": weather.get('rainState', 'DRY'),
            "track_temp": weather.get('trackTemp', 0),
            "air_temp": weather.get('airTemp', 0)
        }
    
    def _calculateGapChange(self, currentData: Dict, prevData: Dict) -> float:
        """Calculate gap change between frames"""
        currentGap = currentData.get('intervalGap', 0)
        prevGap = prevData.get('intervalGap', 0)
        return currentGap - prevGap
    
    def _calculateSectorPerformance(self, data: Dict) -> Dict:
        """Calculate sector performance metrics"""
        # Simplified sector performance based on speed and throttle
        speed = data.get('speed', 0)
        throttle = data.get('throttle', 0)
        
        return {
            "speed_rating": min(100, (speed / 350) * 100),
            "throttle_usage": throttle,
            "efficiency": (throttle / 100) * (speed / 350) * 100 if speed > 0 else 0
        }
    
    def _getTyreCompoundName(self, compound: int) -> str:
        """Convert tyre compound int to name"""
        compounds = {
            0: 'SOFT',
            1: 'MEDIUM',
            2: 'HARD',
            3: 'INTERMEDIATE',
            4: 'WET'
        }
        return compounds.get(compound, 'UNKNOWN')
    
    def _getLeaderLap(self, drivers: Dict) -> int:
        """Get current lap of race leader"""
        maxLap = 0
        for driver, data in drivers.items():
            lap = data.get('lap', 0)
            if lap > maxLap:
                maxLap = lap
        return maxLap
    
    def _addToHistory(self, insight: Dict):
        """Add insight to history"""
        self.eventHistory.append(insight)
        if len(self.eventHistory) > self.maxHistorySize:
            self.eventHistory.pop(0)
    
    def _emptyInsight(self) -> Dict:
        """Return empty insight structure"""
        return {
            "timestamp": 0,
            "lap": 0,
            "events": [],
            "driver_states": {},
            "race_state": {
                "leader": None,
                "safety_car": False,
                "track_status": "1",
                "weather_condition": "DRY"
            }
        }
    
    def getRecentEvents(self, count: int = 10) -> List[Dict]:
        """Get recent events from history"""
        allEvents = []
        for insight in self.eventHistory[-count:]:
            for event in insight.get('events', []):
                event['timestamp'] = insight['timestamp']
                event['lap'] = insight['lap']
                allEvents.append(event)
        return allEvents
    
    def getDriverHistory(self, driver: str, count: int = 10) -> List[Dict]:
        """Get recent history for specific driver"""
        history = []
        for insight in self.eventHistory[-count:]:
            if driver in insight.get('driver_states', {}):
                history.append({
                    'timestamp': insight['timestamp'],
                    'lap': insight['lap'],
                    'state': insight['driver_states'][driver]
                })
        return history
