"""
Safety Car Model - Simulates safety car deployment and positioning
"""
import numpy as np
from typing import Dict, List, Optional
from scipy.spatial import cKDTree


class SafetyCarModel:
    """Simulates safety car position based on track status"""
    
    def __init__(self, trackData: Dict):
        self.trackData = trackData
        self.refXs = np.array(trackData['x'])
        self.refYs = np.array(trackData['y'])
        
        # Build KD-Tree for fast position lookups
        self.trackTree = cKDTree(np.column_stack((self.refXs, self.refYs)))
        
        # Calculate cumulative distances
        diffs = np.sqrt(np.diff(self.refXs)**2 + np.diff(self.refYs)**2)
        self.refCumdist = np.concatenate(([0.0], np.cumsum(diffs)))
        self.refTotalLength = float(self.refCumdist[-1])
        
        # Calculate normals
        dx = np.gradient(self.refXs)
        dy = np.gradient(self.refYs)
        norm = np.sqrt(dx**2 + dy**2)
        norm[norm == 0] = 1.0
        self.refNx = -dy / norm
        self.refNy = dx / norm
        
        # Constants
        self.SC_OFFSET_METERS = 150
        self.DEPLOY_DURATION = 4.0
        self.RETURN_DURATION = 8.0
        
        self.scState = {}
    
    def computeSafetyCarPositions(self, frames: List[Dict], trackStatuses: List[Dict]) -> None:
        """Compute safety car positions for all frames"""
        # Find SC periods
        scPeriods = []
        for status in trackStatuses:
            if str(status.get('status', '')) == '4':
                scPeriods.append({
                    'startTime': status['startTime'],
                    'endTime': status.get('endTime')
                })
        
        if not scPeriods:
            return
        
        print(f'Safety Car: Found {len(scPeriods)} SC period(s)')
        
        # Process each frame
        for frameIdx, frame in enumerate(frames):
            t = frame['t']
            
            # Check if in SC period
            activeSc = None
            activeScIdx = None
            
            for scIdx, sc in enumerate(scPeriods):
                scStart = sc['startTime']
                scEnd = sc.get('endTime')
                effectiveEnd = (scEnd + self.RETURN_DURATION) if scEnd else None
                
                if t >= scStart and (effectiveEnd is None or t < effectiveEnd):
                    activeSc = sc
                    activeScIdx = scIdx
                    break
            
            if activeSc is None:
                frame['safetyCar'] = None
                continue
            
            scStart = activeSc['startTime']
            scEnd = activeSc.get('endTime')
            elapsed = t - scStart
            
            # Initialize state
            if activeScIdx not in self.scState:
                self.scState[activeScIdx] = {
                    'trackDist': self.refTotalLength * 0.05,
                    'lastT': t
                }
            
            state = self.scState[activeScIdx]
            dtFrame = max(0.0, t - state['lastT'])
            state['lastT'] = t
            
            # Get leader position
            leaderCode, leaderDist = self._getLeaderInfo(frame)
            
            # Determine phase
            if scEnd is None or t < scEnd:
                # Deploying or on track
                if elapsed < self.DEPLOY_DURATION:
                    phase = 'deploying'
                    alpha = elapsed / self.DEPLOY_DURATION
                else:
                    phase = 'onTrack'
                    alpha = 1.0
                    
                    # Follow leader
                    if leaderDist is not None:
                        targetDist = (leaderDist + self.SC_OFFSET_METERS) % self.refTotalLength
                        state['trackDist'] = targetDist
            else:
                # Returning
                returnElapsed = t - scEnd
                if returnElapsed < self.RETURN_DURATION:
                    phase = 'returning'
                    alpha = max(0.0, 1.0 - (returnElapsed / self.RETURN_DURATION))
                    
                    # Accelerate away
                    state['trackDist'] += 400.0 * dtFrame
                    state['trackDist'] = state['trackDist'] % self.refTotalLength
                else:
                    frame['safetyCar'] = None
                    continue
            
            # Get position
            scX, scY = self._posAtDist(state['trackDist'])
            
            frame['safetyCar'] = {
                'x': round(scX, 2),
                'y': round(scY, 2),
                'phase': phase,
                'alpha': round(alpha, 3)
            }
    
    def _getLeaderInfo(self, frame: Dict) -> tuple:
        """Get leader code and distance"""
        drivers = frame.get('drivers', {})
        if not drivers:
            return None, None
        
        bestProgress = -1
        bestCode = None
        bestDist = None
        
        for code, data in drivers.items():
            lap = data.get('lap', 1)
            dist = data.get('dist', 0)
            progress = (lap - 1) * self.refTotalLength + dist
            
            if progress > bestProgress:
                bestProgress = progress
                bestCode = code
                bestDist = dist
        
        return bestCode, bestDist
    
    def _posAtDist(self, distM: float) -> tuple:
        """Get (x, y) at distance along track"""
        d = distM % self.refTotalLength
        idx = int(np.searchsorted(self.refCumdist, d))
        idx = min(idx, len(self.refXs) - 1)
        return float(self.refXs[idx]), float(self.refYs[idx])
