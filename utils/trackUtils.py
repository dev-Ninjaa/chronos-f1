"""
Track Utilities - Track processing, DRS zones, finish line detection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional


def buildTrackFromLap(telemetry) -> Dict:
    """Build track geometry from telemetry data"""
    try:
        x = telemetry['X'].to_numpy()
        y = telemetry['Y'].to_numpy()
        distance = telemetry['Distance'].to_numpy()
        
        # Detect DRS zones
        drsZones = []
        if 'DRS' in telemetry.columns:
            drsZones = detectDrsZones(telemetry)
        
        # Calculate track bounds (inner/outer)
        innerX, innerY, outerX, outerY = calculateTrackBounds(x, y)
        
        # Find finish line
        finishLine = detectFinishLine(x, y, distance)
        
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'distance': distance.tolist(),
            'innerX': innerX,
            'innerY': innerY,
            'outerX': outerX,
            'outerY': outerY,
            'drsZones': drsZones,
            'finishLine': finishLine,
            'xMin': float(x.min()),
            'xMax': float(x.max()),
            'yMin': float(y.min()),
            'yMax': float(y.max())
        }
    except Exception as e:
        print(f'Error building track: {e}')
        return {'x': [], 'y': [], 'distance': []}


def detectDrsZones(telemetry) -> List[Dict]:
    """Detect DRS zones from telemetry"""
    try:
        drs = telemetry['DRS'].to_numpy()
        distance = telemetry['Distance'].to_numpy()
        
        zones = []
        inZone = False
        zoneStart = None
        
        for i in range(len(drs)):
            if drs[i] >= 10 and not inZone:
                # DRS zone starts
                inZone = True
                zoneStart = distance[i]
            elif drs[i] < 10 and inZone:
                # DRS zone ends
                inZone = False
                if zoneStart is not None:
                    zones.append({
                        'start': float(zoneStart),
                        'end': float(distance[i-1]),
                        'startIndex': i - (i - np.where(distance == zoneStart)[0][0]),
                        'endIndex': i - 1
                    })
                zoneStart = None
        
        # Close last zone if still open
        if inZone and zoneStart is not None:
            zones.append({
                'start': float(zoneStart),
                'end': float(distance[-1]),
                'startIndex': len(distance) - 1,
                'endIndex': len(distance) - 1
            })
        
        return zones
    except Exception as e:
        print(f'Error detecting DRS zones: {e}')
        return []


def calculateTrackBounds(x: np.ndarray, y: np.ndarray, width: float = 15.0) -> Tuple:
    """Calculate inner and outer track bounds"""
    try:
        # Calculate normals
        dx = np.gradient(x)
        dy = np.gradient(y)
        norm = np.sqrt(dx**2 + dy**2)
        norm[norm == 0] = 1.0
        
        nx = -dy / norm
        ny = dx / norm
        
        # Inner and outer bounds
        innerX = x + nx * width
        innerY = y + ny * width
        outerX = x - nx * width
        outerY = y - ny * width
        
        return innerX.tolist(), innerY.tolist(), outerX.tolist(), outerY.tolist()
    except Exception as e:
        print(f'Error calculating track bounds: {e}')
        return x.tolist(), y.tolist(), x.tolist(), y.tolist()


def detectFinishLine(x: np.ndarray, y: np.ndarray, distance: np.ndarray) -> Optional[Dict]:
    """Detect finish line position"""
    try:
        # Finish line is at distance ~0
        finishIdx = np.argmin(np.abs(distance))
        
        return {
            'x': float(x[finishIdx]),
            'y': float(y[finishIdx]),
            'index': int(finishIdx)
        }
    except Exception as e:
        return None


def interpolatePoints(xs: List, ys: List, numPoints: int = 2000) -> List[Tuple]:
    """Interpolate points for smooth rendering"""
    if len(xs) < 2:
        return list(zip(xs, ys))
    
    tOld = np.linspace(0, 1, len(xs))
    tNew = np.linspace(0, 1, numPoints)
    xsInterp = np.interp(tNew, tOld, xs)
    ysInterp = np.interp(tNew, tOld, ys)
    
    return list(zip(xsInterp, ysInterp))
