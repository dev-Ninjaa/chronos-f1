"""
Replay Engine - Manages race replay with all features
Includes: Weather, DRS, Safety Car, Race Control, Track Status, Tyre Health
"""
import time
import threading
from utils.weatherUtils import formatWeatherData


class ReplayEngine:
    def __init__(self, raceData, socketio):
        self.raceData = raceData
        self.socketio = socketio
        self.frames = raceData['frames']
        self.totalFrames = len(self.frames)
        self.currentFrame = 0
        self.playing = False
        self.playbackSpeed = 1.0
        self.lastUpdateTime = None
        self.lock = threading.Lock()
        
        # Enhanced data
        self.trackStatuses = raceData.get('trackStatuses', [])
        self.raceControlMessages = raceData.get('raceControlMessages', [])
        self.tyreModel = raceData.get('tyreModel')
        self.trackData = raceData.get('trackData', {})
        self.driverColors = raceData.get('driverColors', {})
    
    def play(self):
        with self.lock:
            self.playing = True
            self.lastUpdateTime = time.time()
    
    def pause(self):
        with self.lock:
            self.playing = False
    
    def isPlaying(self):
        with self.lock:
            return self.playing
    
    def restart(self):
        with self.lock:
            self.currentFrame = 0
            self.lastUpdateTime = time.time()
    
    def seekToFrame(self, frameIndex):
        with self.lock:
            self.currentFrame = max(0, min(frameIndex, self.totalFrames - 1))
            self.lastUpdateTime = time.time()
    
    def setPlaybackSpeed(self, speed):
        with self.lock:
            self.playbackSpeed = max(0.1, min(speed, 10.0))
    
    def getCurrentTelemetry(self):
        with self.lock:
            if not self.playing:
                return None
            
            # Update frame
            currentTime = time.time()
            if self.lastUpdateTime:
                deltaTime = currentTime - self.lastUpdateTime
                framesToAdvance = int(deltaTime * 25 * self.playbackSpeed)
                
                if framesToAdvance > 0:
                    self.currentFrame += framesToAdvance
                    self.lastUpdateTime = currentTime
                    
                    if self.currentFrame >= self.totalFrames:
                        self.currentFrame = 0
            
            if self.currentFrame >= self.totalFrames:
                return None
            
            frame = self.frames[self.currentFrame]
            
            # Calculate positions
            driverProgress = {}
            for code, data in frame['drivers'].items():
                lap = data.get('lap', 1)
                dist = data.get('dist', 0)
                progress = (lap - 1) * 5000 + dist
                driverProgress[code] = progress
            
            sortedDrivers = sorted(driverProgress.items(), key=lambda x: x[1], reverse=True)
            
            # Update positions and calculate gaps
            leaderProgress = sortedDrivers[0][1] if sortedDrivers else 0
            for pos, (code, driverProg) in enumerate(sortedDrivers, 1):
                frame['drivers'][code]['position'] = pos
                
                # Calculate gap to leader (in seconds, approximate)
                gapMeters = leaderProgress - driverProg
                gapSeconds = gapMeters / 55.56  # Assume ~200 km/h average
                frame['drivers'][code]['gapToLeader'] = gapSeconds
                
                # Calculate interval gap (to car ahead)
                if pos > 1:
                    aheadProgress = sortedDrivers[pos-2][1]
                    intervalMeters = aheadProgress - driverProg
                    intervalSeconds = intervalMeters / 55.56
                    frame['drivers'][code]['intervalGap'] = intervalSeconds
                else:
                    frame['drivers'][code]['intervalGap'] = 0
                
                # Add tyre health if model available
                if self.tyreModel:
                    tyreHealth = self.tyreModel.getHealthForFrame(code, frame)
                    if tyreHealth:
                        frame['drivers'][code]['tyreHealth'] = tyreHealth
            
            # Get current track status
            currentTrackStatus = self._getCurrentTrackStatus(frame['t'])
            
            # Get race control messages up to current time
            currentRcMessages = [
                msg for msg in self.raceControlMessages
                if msg['time'] <= frame['t']
            ]
            
            # Format time
            t = frame['t']
            hours = int(t // 3600)
            minutes = int((t % 3600) // 60)
            seconds = int(t % 60)
            
            leaderCode = sortedDrivers[0][0] if sortedDrivers else ''
            leaderLap = frame['drivers'][leaderCode]['lap'] if leaderCode else 1
            
            # Format weather data
            weatherData = None
            if frame.get('weather'):
                weatherData = formatWeatherData(frame['weather'])
            
            return {
                'frameIndex': self.currentFrame,
                'totalFrames': self.totalFrames,
                'frame': frame,
                'playbackSpeed': self.playbackSpeed,
                'trackStatus': currentTrackStatus,
                'weather': weatherData,
                'raceControlMessages': currentRcMessages[-10:],  # Last 10 messages
                'sessionData': {
                    'time': f'{hours:02d}:{minutes:02d}:{seconds:02d}',
                    'lap': leaderLap,
                    'leader': leaderCode,
                    'totalLaps': self.raceData['totalLaps']
                },
                'trackData': self.trackData,
                'driverColors': self.driverColors
            }
    
    def _getCurrentTrackStatus(self, currentTime):
        """Get current track status"""
        for status in self.trackStatuses:
            if (currentTime >= status['startTime'] and 
                (status['endTime'] is None or currentTime < status['endTime'])):
                return status['status']
        return '1'  # Green flag default
