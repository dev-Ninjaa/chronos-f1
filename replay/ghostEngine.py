"""
Ghost Comparison System - Compare live replay against fastest lap reference
"""
import numpy as np
from typing import Dict, List, Optional, Tuple


class GhostEngine:
    """
    Ghost driver system for comparing current replay against fastest lap.
    
    Features:
    - Ghost represents fastest lap reference
    - Live delta timing
    - Sector delta timing
    - Color-coded performance (green=gaining, red=losing, gold=fastest)
    - Smooth interpolation
    - Replay speed synchronized (0.25x - 8x)
    """
    
    def __init__(self, fastestLapData: Dict, trackData: Dict):
        """
        Initialize ghost engine with fastest lap reference.
        
        Args:
            fastestLapData: {
                'driver': str,
                'lap_time': float,
                'telemetry': {
                    't': np.array,
                    'x': np.array,
                    'y': np.array,
                    'speed': np.array,
                    'dist': np.array
                },
                'sectors': [
                    {'start_dist': float, 'end_dist': float, 'time': float},
                    ...
                ]
            }
            trackData: Track layout with sector information
        """
        self.fastestLapData = fastestLapData
        self.trackData = trackData
        self.ghostDriver = fastestLapData['driver']
        self.ghostLapTime = fastestLapData['lap_time']
        
        # Ghost telemetry
        self.ghostTelemetry = fastestLapData['telemetry']
        self.ghostSectors = fastestLapData.get('sectors', [])
        
        # Current comparison state
        self.currentDelta = 0.0
        self.sectorDeltas = [0.0, 0.0, 0.0]  # 3 sectors
        self.currentSector = 0
        
        # Performance tracking
        self.deltaHistory = []
        self.maxHistorySize = 100
        
        print(f"👻 Ghost Engine initialized - Reference: {self.ghostDriver} ({self.ghostLapTime:.3f}s)")
    
    def getGhostPosition(self, currentTime: float, currentDistance: float) -> Optional[Dict]:
        """
        Get ghost driver position at current time/distance.
        
        Args:
            currentTime: Current replay time
            currentDistance: Current driver distance
        
        Returns:
            {
                'x': float,
                'y': float,
                'speed': float,
                'distance': float,
                'visible': bool
            }
        """
        # Find ghost position at equivalent distance
        ghostDist = self.ghostTelemetry['dist']
        
        # Find closest distance point
        idx = np.searchsorted(ghostDist, currentDistance)
        
        if idx >= len(ghostDist):
            return None
        
        # Interpolate position
        if idx > 0 and idx < len(ghostDist):
            # Linear interpolation between points
            d0, d1 = ghostDist[idx-1], ghostDist[idx]
            t = (currentDistance - d0) / (d1 - d0) if d1 != d0 else 0
            
            x = self.ghostTelemetry['x'][idx-1] * (1-t) + self.ghostTelemetry['x'][idx] * t
            y = self.ghostTelemetry['y'][idx-1] * (1-t) + self.ghostTelemetry['y'][idx] * t
            speed = self.ghostTelemetry['speed'][idx-1] * (1-t) + self.ghostTelemetry['speed'][idx] * t
        else:
            x = self.ghostTelemetry['x'][idx]
            y = self.ghostTelemetry['y'][idx]
            speed = self.ghostTelemetry['speed'][idx]
        
        return {
            'x': float(x),
            'y': float(y),
            'speed': float(speed),
            'distance': float(currentDistance),
            'visible': True
        }
    
    def calculateDelta(self, currentTime: float, currentDistance: float, currentSpeed: float) -> Dict:
        """
        Calculate delta timing between current position and ghost.
        
        Returns:
            {
                'lap_delta': float,  # Overall lap delta in seconds
                'sector_deltas': [float, float, float],  # Delta per sector
                'current_sector': int,  # Current sector (0, 1, 2)
                'delta_color': str,  # 'green', 'red', 'gold'
                'is_gaining': bool,
                'speed_diff': float  # Speed difference
            }
        """
        # Find ghost time at current distance
        ghostDist = self.ghostTelemetry['dist']
        ghostTime = self.ghostTelemetry['t']
        
        idx = np.searchsorted(ghostDist, currentDistance)
        
        if idx >= len(ghostDist):
            return self._emptyDelta()
        
        # Interpolate ghost time
        if idx > 0 and idx < len(ghostDist):
            d0, d1 = ghostDist[idx-1], ghostDist[idx]
            t = (currentDistance - d0) / (d1 - d0) if d1 != d0 else 0
            ghostTimeAtDist = ghostTime[idx-1] * (1-t) + ghostTime[idx] * t
        else:
            ghostTimeAtDist = ghostTime[idx]
        
        # Calculate delta (positive = behind ghost, negative = ahead of ghost)
        lapDelta = currentTime - ghostTimeAtDist
        self.currentDelta = lapDelta
        
        # Track delta history
        self._addToHistory(lapDelta)
        
        # Determine if gaining or losing
        isGaining = self._isGainingTime()
        
        # Calculate speed difference
        ghostSpeed = self.ghostTelemetry['speed'][idx]
        speedDiff = currentSpeed - ghostSpeed
        
        # Determine sector
        currentSector = self._getCurrentSector(currentDistance)
        
        # Calculate sector deltas
        sectorDeltas = self._calculateSectorDeltas(currentDistance, currentTime)
        
        # Determine color
        deltaColor = self._getDeltaColor(lapDelta, isGaining)
        
        return {
            'lap_delta': float(lapDelta),
            'sector_deltas': sectorDeltas,
            'current_sector': currentSector,
            'delta_color': deltaColor,
            # Ensure JSON-serializable (numpy.bool_ can appear from comparisons)
            'is_gaining': bool(isGaining),
            'speed_diff': float(speedDiff),
            'ghost_driver': self.ghostDriver,
            'ghost_lap_time': self.ghostLapTime
        }
    
    def _getCurrentSector(self, distance: float) -> int:
        """Determine current sector based on distance"""
        if not self.ghostSectors:
            # Default 3 equal sectors
            trackLength = self.trackData.get('length', 5000)
            sectorLength = trackLength / 3
            return min(2, int(distance / sectorLength))
        
        for i, sector in enumerate(self.ghostSectors):
            if sector['start_dist'] <= distance < sector['end_dist']:
                return i
        
        return 2  # Default to sector 3
    
    def _calculateSectorDeltas(self, currentDistance: float, currentTime: float) -> List[float]:
        """Calculate delta for each sector"""
        if not self.ghostSectors:
            return [0.0, 0.0, 0.0]
        
        deltas = []
        
        for sector in self.ghostSectors:
            # Find ghost time at sector end
            ghostDist = self.ghostTelemetry['dist']
            ghostTime = self.ghostTelemetry['t']
            
            sectorEndIdx = np.searchsorted(ghostDist, sector['end_dist'])
            
            if sectorEndIdx < len(ghostTime):
                ghostSectorTime = ghostTime[sectorEndIdx]
                
                # If we've passed this sector, calculate delta
                if currentDistance >= sector['end_dist']:
                    # Find our time at sector end
                    # (Simplified - in real implementation, track actual sector times)
                    delta = 0.0  # Placeholder
                else:
                    delta = 0.0
                
                deltas.append(delta)
            else:
                deltas.append(0.0)
        
        # Pad to 3 sectors
        while len(deltas) < 3:
            deltas.append(0.0)
        
        return deltas[:3]
    
    def _isGainingTime(self) -> bool:
        """Determine if currently gaining time on ghost"""
        if len(self.deltaHistory) < 2:
            return False
        
        # Compare recent deltas
        recentDeltas = self.deltaHistory[-5:]
        
        if len(recentDeltas) < 2:
            return False
        
        # If delta is decreasing (becoming more negative), we're gaining
        trend = recentDeltas[-1] - recentDeltas[0]
        # `trend < 0` can be numpy.bool_, coerce to real bool for JSON safety.
        return bool(trend < 0)
    
    def _getDeltaColor(self, delta: float, isGaining: bool) -> str:
        """
        Determine delta color:
        - Green: Gaining time (ahead or catching up)
        - Red: Losing time (behind and falling back)
        - Gold: Fastest sector (within 0.05s of ghost)
        """
        if abs(delta) < 0.05:
            return 'gold'  # Matching ghost pace
        elif isGaining:
            return 'green'
        else:
            return 'red'
    
    def _addToHistory(self, delta: float):
        """Add delta to history"""
        self.deltaHistory.append(delta)
        if len(self.deltaHistory) > self.maxHistorySize:
            self.deltaHistory.pop(0)
    
    def _emptyDelta(self) -> Dict:
        """Return empty delta structure"""
        return {
            'lap_delta': 0.0,
            'sector_deltas': [0.0, 0.0, 0.0],
            'current_sector': 0,
            'delta_color': 'red',
            'is_gaining': False,
            'speed_diff': 0.0,
            'ghost_driver': self.ghostDriver,
            'ghost_lap_time': self.ghostLapTime
        }
    
    def reset(self):
        """Reset ghost comparison state"""
        self.currentDelta = 0.0
        self.sectorDeltas = [0.0, 0.0, 0.0]
        self.currentSector = 0
        self.deltaHistory = []
        print("👻 Ghost comparison reset")


def createGhostFromFastestLap(session, trackData: Dict) -> Optional[GhostEngine]:
    """
    Create ghost engine from session's fastest lap.
    
    Args:
        session: FastF1 session object
        trackData: Track layout data
    
    Returns:
        GhostEngine instance or None
    """
    try:
        # Find fastest lap
        fastestLap = session.laps.pick_fastest()
        
        if fastestLap is None or fastestLap.empty:
            print("⚠️ No fastest lap found")
            return None
        
        # Get telemetry
        telemetry = fastestLap.get_telemetry()
        
        if telemetry.empty:
            print("⚠️ No telemetry for fastest lap")
            return None
        
        # Extract data
        driver = fastestLap['Driver']
        lapTime = fastestLap['LapTime'].total_seconds()
        
        # Build telemetry arrays
        t = telemetry['SessionTime'].dt.total_seconds().to_numpy()
        t = t - t[0]  # Normalize to start at 0
        
        fastestLapData = {
            'driver': driver,
            'lap_time': lapTime,
            'telemetry': {
                't': t,
                'x': telemetry['X'].to_numpy(),
                'y': telemetry['Y'].to_numpy(),
                'speed': telemetry['Speed'].to_numpy(),
                'dist': telemetry['Distance'].to_numpy()
            },
            'sectors': _extractSectors(telemetry, trackData)
        }
        
        return GhostEngine(fastestLapData, trackData)
        
    except Exception as e:
        print(f"❌ Error creating ghost: {e}")
        return None


def _extractSectors(telemetry, trackData: Dict) -> List[Dict]:
    """Extract sector information from telemetry"""
    # Simplified sector extraction
    # In real implementation, use track sector markers
    
    distances = telemetry['Distance'].to_numpy()
    times = telemetry['SessionTime'].dt.total_seconds().to_numpy()
    times = times - times[0]
    
    trackLength = distances[-1] if len(distances) > 0 else 5000
    sectorLength = trackLength / 3
    
    sectors = []
    for i in range(3):
        startDist = i * sectorLength
        endDist = (i + 1) * sectorLength
        
        # Find time at sector boundaries
        startIdx = np.searchsorted(distances, startDist)
        endIdx = np.searchsorted(distances, endDist)
        
        if endIdx < len(times) and startIdx < len(times):
            sectorTime = times[endIdx] - times[startIdx]
        else:
            sectorTime = 0.0
        
        sectors.append({
            'start_dist': float(startDist),
            'end_dist': float(endDist),
            'time': float(sectorTime)
        })
    
    return sectors
