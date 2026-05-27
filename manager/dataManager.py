"""
Data Manager - Complete F1 data processing with all features
Includes: Weather, DRS, Safety Car, Race Control, Track Status, Tyre Model
"""
import os
import pickle
import sys
import math
from datetime import datetime, timedelta
import fastf1
import numpy as np
import pandas as pd
from models.safetyCarModel import SafetyCarModel
from models.tyreModel import TyreDegradationModel
from utils.trackUtils import buildTrackFromLap
from utils.weatherUtils import formatWeatherData


class DataManager:
    def __init__(self, cacheDir='.fastf1-cache'):
        self.cacheDir = cacheDir
        self._ensureCacheDir()
        fastf1.Cache.enable_cache(self.cacheDir)
        self.FPS = 25
        self.DT = 1 / self.FPS
    
    def _ensureCacheDir(self):
        if not os.path.exists(self.cacheDir):
            os.makedirs(self.cacheDir)
    
    def getAvailableSeasons(self):
        current_year = datetime.now().year
        return list(range(2018, current_year + 1))
    
    def getRacesForSeason(self, year):
        try:
            schedule = fastf1.get_event_schedule(year)
            races = []
            
            for idx, event in schedule.iterrows():
                if event['EventFormat'] != 'testing':
                    races.append({
                        'round': int(event['RoundNumber']),
                        'name': str(event['EventName']),
                        'location': str(event['Location']),
                        'country': str(event['Country']),
                        'date': event['EventDate'].strftime('%Y-%m-%d') if pd.notna(event['EventDate']) else ''
                    })
            
            return races
        except Exception as e:
            print(f'Error loading races for {year}: {e}')
            return []
    
    def loadRaceData(self, year, roundNum, sessionType='R', socketio=None):
        print(f'Loading {year} Round {roundNum} Session {sessionType}...')
        
        def emit_progress(message, percent):
            if socketio:
                socketio.emit('loading_progress', {'message': message, 'percent': percent})
        
        # Check cache
        cacheFile = f'computed_data/{year}_R{roundNum}_{sessionType}_enhanced.pkl'
        print(f'Checking cache file: {cacheFile}')
        print(f'Cache exists: {os.path.exists(cacheFile)}')
        print(f'sys.argv: {sys.argv}')
        
        if os.path.exists(cacheFile):
            emit_progress('Loading from cache...', 10)
            print('✅ Loading from cache - this should be fast!')
            with open(cacheFile, 'rb') as f:
                data = pickle.load(f)
            emit_progress('Cache loaded!', 100)
            print(f'✅ Cache loaded successfully! {len(data["frames"])} frames')
            return data
        
        print('⚠️ Cache not found, processing from scratch...')
        
        # Load session
        emit_progress('Loading session data...', 10)
        session = fastf1.get_session(year, roundNum, sessionType)
        
        emit_progress('Loading telemetry data...', 20)
        session.load(telemetry=True, weather=True, messages=True)
        
        # Process all data
        emit_progress('Processing race data...', 30)
        raceData = self._processCompleteRaceData(session, socketio, emit_progress)
        
        # Cache
        emit_progress('Saving to cache...', 95)
        os.makedirs('computed_data', exist_ok=True)
        with open(cacheFile, 'wb') as f:
            pickle.dump(raceData, f)
        
        emit_progress('Complete!', 100)
        print('Race data loaded successfully!')
        return raceData
    
    def _processCompleteRaceData(self, session, socketio=None, emit_progress=None):
        """Process complete race data with all features"""
        print('Processing complete telemetry with all features...')
        
        if emit_progress:
            emit_progress('Processing telemetry...', 35)
        
        drivers = session.drivers
        driverCodes = {num: session.get_driver(num)['Abbreviation'] for num in drivers}
        driverColors = self._getDriverColors(session)
        
        # Get track layout with DRS zones
        if emit_progress:
            emit_progress('Building track layout...', 40)
        trackData = self._getEnhancedTrackLayout(session)
        
        # Process driver telemetry
        driverTelemetry = {}
        globalTMin = None
        globalTMax = None
        maxLapNumber = 0
        
        total_drivers = len(drivers)
        for idx, driverNum in enumerate(drivers):
            code = driverCodes[driverNum]
            print(f'Processing driver: {code}')
            
            if emit_progress:
                progress = 40 + int((idx / total_drivers) * 30)
                emit_progress(f'Processing driver {code}...', progress)
            
            laps = session.laps.pick_drivers(driverNum)
            if laps.empty:
                continue
            
            telData = self._processDriverLaps(laps)
            if telData is None:
                continue
            
            driverTelemetry[code] = telData
            
            tMin = telData['t'].min()
            tMax = telData['t'].max()
            maxLap = int(laps['LapNumber'].max())
            
            globalTMin = tMin if globalTMin is None else min(globalTMin, tMin)
            globalTMax = tMax if globalTMax is None else max(globalTMax, tMax)
            maxLapNumber = max(maxLapNumber, maxLap)
        
        # Create timeline
        if emit_progress:
            emit_progress('Creating timeline...', 70)
        timeline = np.arange(globalTMin, globalTMax, self.DT) - globalTMin
        
        # Resample all drivers
        if emit_progress:
            emit_progress('Resampling telemetry...', 75)
        resampledData = {}
        for code, data in driverTelemetry.items():
            t = data['t'] - globalTMin
            order = np.argsort(t)
            
            resampledData[code] = {
                'x': np.interp(timeline, t[order], data['x'][order]),
                'y': np.interp(timeline, t[order], data['y'][order]),
                'speed': np.interp(timeline, t[order], data['speed'][order]),
                'lap': np.interp(timeline, t[order], data['lap'][order]),
                'dist': np.interp(timeline, t[order], data['dist'][order]),
                'tyre': np.interp(timeline, t[order], data['tyre'][order]),
                'tyreLife': np.interp(timeline, t[order], data['tyreLife'][order]),
                'gear': np.interp(timeline, t[order], data['gear'][order]),
                'drs': np.interp(timeline, t[order], data['drs'][order]),
                'throttle': np.interp(timeline, t[order], data['throttle'][order]),
                'brake': np.interp(timeline, t[order], data['brake'][order])
            }
        
        # Process weather data
        if emit_progress:
            emit_progress('Processing weather...', 80)
        weatherData = self._processWeatherData(session, timeline, globalTMin)
        
        # Process track status
        if emit_progress:
            emit_progress('Processing track status...', 82)
        trackStatuses = self._processTrackStatus(session, globalTMin)
        
        # Process race control messages
        if emit_progress:
            emit_progress('Processing race control...', 84)
        raceControlMessages = self._processRaceControlMessages(session, globalTMin)
        
        # Build frames
        if emit_progress:
            emit_progress('Building frames...', 86)
        frames = []
        for i, t in enumerate(timeline):
            frame = {
                't': float(t),
                'drivers': {},
                'weather': weatherData[i] if weatherData else None
            }
            
            for code, data in resampledData.items():
                frame['drivers'][code] = {
                    'x': float(data['x'][i]),
                    'y': float(data['y'][i]),
                    'speed': float(data['speed'][i]),
                    'lap': int(data['lap'][i]),
                    'dist': float(data['dist'][i]),
                    'tyre': int(data['tyre'][i]),
                    'tyreLife': int(data['tyreLife'][i]),
                    'gear': int(data['gear'][i]),
                    'drs': int(data['drs'][i]),
                    'throttle': float(data['throttle'][i]),
                    'brake': float(data['brake'][i]),
                    'position': 1,
                    'inPit': False
                }
            
            frames.append(frame)
        
        # Add safety car positions
        if emit_progress:
            emit_progress('Computing safety car...', 90)
        if trackData and trackStatuses:
            try:
                scModel = SafetyCarModel(trackData)
                scModel.computeSafetyCarPositions(frames, trackStatuses)
                print('Safety car positions computed')
            except Exception as e:
                print(f'Could not compute safety car: {e}')
        
        # Initialize tyre model
        if emit_progress:
            emit_progress('Initializing tyre model...', 92)
        tyreModel = TyreDegradationModel()
        tyreModel.initializeFromSession(session)
        
        print(f'Generated {len(frames)} frames with all features')
        
        return {
            'eventName': session.event['EventName'],
            'circuitName': session.event['Location'],
            'country': session.event['Country'],
            'date': session.event['EventDate'].strftime('%Y-%m-%d'),
            'totalLaps': maxLapNumber,
            'frames': frames,
            'drivers': list(driverCodes.values()),
            'driverColors': driverColors,
            'trackData': trackData,
            'trackStatuses': trackStatuses,
            'raceControlMessages': raceControlMessages,
            'tyreModel': tyreModel,
            'hasWeather': weatherData is not None,
            'hasDrsZones': len(trackData.get('drsZones', [])) > 0
        }
    
    def _processDriverLaps(self, laps):
        """Process all laps for a driver"""
        tAll, xAll, yAll, distAll, lapNumbers = [], [], [], [], []
        tyreAll, tyreLifeAll, speedAll, gearAll, drsAll = [], [], [], [], []
        throttleAll, brakeAll = [], []
        
        totalDistSoFar = 0.0
        
        for _, lap in laps.iterlaps():
            tel = lap.get_telemetry()
            if tel.empty:
                continue
            
            lapNumber = lap['LapNumber']
            tyreCompound = self._getTyreCompoundInt(lap['Compound'])
            tyreLife = lap['TyreLife'] if pd.notna(lap['TyreLife']) else 0
            
            t = tel['SessionTime'].dt.total_seconds().to_numpy()
            x = tel['X'].to_numpy()
            y = tel['Y'].to_numpy()
            d = tel['Distance'].to_numpy()
            speed = tel['Speed'].to_numpy()
            gear = tel['nGear'].to_numpy()
            drs = tel['DRS'].to_numpy()
            throttle = tel['Throttle'].to_numpy()
            brake = tel['Brake'].to_numpy().astype(float)
            
            raceDist = totalDistSoFar + d
            
            tAll.append(t)
            xAll.append(x)
            yAll.append(y)
            distAll.append(raceDist)
            lapNumbers.append(np.full_like(t, lapNumber))
            tyreAll.append(np.full_like(t, tyreCompound))
            tyreLifeAll.append(np.full_like(t, tyreLife))
            speedAll.append(speed)
            gearAll.append(gear)
            drsAll.append(drs)
            throttleAll.append(throttle)
            brakeAll.append(brake)
        
        if not tAll:
            return None
        
        return {
            't': np.concatenate(tAll),
            'x': np.concatenate(xAll),
            'y': np.concatenate(yAll),
            'dist': np.concatenate(distAll),
            'lap': np.concatenate(lapNumbers),
            'tyre': np.concatenate(tyreAll),
            'tyreLife': np.concatenate(tyreLifeAll),
            'speed': np.concatenate(speedAll),
            'gear': np.concatenate(gearAll),
            'drs': np.concatenate(drsAll),
            'throttle': np.concatenate(throttleAll),
            'brake': np.concatenate(brakeAll)
        }
    
    def _processWeatherData(self, session, timeline, globalTMin):
        """Process weather data"""
        try:
            weatherDf = getattr(session, 'weather_data', None)
            if weatherDf is None or weatherDf.empty:
                return None
            
            weatherTimes = (weatherDf['Time'].dt.total_seconds().to_numpy() - globalTMin)
            order = np.argsort(weatherTimes)
            weatherTimes = weatherTimes[order]
            
            def resample(col):
                if col not in weatherDf:
                    return None
                data = weatherDf[col].to_numpy()[order]
                return np.interp(timeline, weatherTimes, data.astype(float))
            
            trackTemp = resample('TrackTemp')
            airTemp = resample('AirTemp')
            humidity = resample('Humidity')
            windSpeed = resample('WindSpeed')
            windDirection = resample('WindDirection')
            rainfall = resample('Rainfall')
            
            weatherFrames = []
            for i in range(len(timeline)):
                weatherFrames.append({
                    'trackTemp': float(trackTemp[i]) if trackTemp is not None else None,
                    'airTemp': float(airTemp[i]) if airTemp is not None else None,
                    'humidity': float(humidity[i]) if humidity is not None else None,
                    'windSpeed': float(windSpeed[i]) if windSpeed is not None else None,
                    'windDirection': float(windDirection[i]) if windDirection is not None else None,
                    'rainState': 'WET' if (rainfall is not None and rainfall[i] > 0) else 'DRY'
                })
            
            return weatherFrames
        except Exception as e:
            print(f'Could not process weather: {e}')
            return None
    
    def _processTrackStatus(self, session, globalTMin):
        """Process track status data"""
        try:
            trackStatus = session.track_status
            formattedStatuses = []
            
            for status in trackStatus.to_dict('records'):
                seconds = timedelta.total_seconds(status['Time'])
                startTime = seconds - globalTMin
                
                if formattedStatuses:
                    formattedStatuses[-1]['endTime'] = startTime
                
                formattedStatuses.append({
                    'status': str(status['Status']),
                    'startTime': startTime,
                    'endTime': None
                })
            
            return formattedStatuses
        except Exception as e:
            print(f'Could not process track status: {e}')
            return []
    
    def _processRaceControlMessages(self, session, globalTMin):
        """Process race control messages"""
        try:
            rcMessages = getattr(session, 'race_control_messages', None)
            if rcMessages is None or rcMessages.empty:
                return []
            
            formatted = []
            for msg in rcMessages.to_dict('records'):
                timeVal = msg['Time']
                if hasattr(timeVal, 'total_seconds'):
                    seconds = timeVal.total_seconds()
                else:
                    seconds = (timeVal - session.t0_date).total_seconds()
                
                msgTime = seconds - globalTMin
                
                if msgTime > 0.0:
                    formatted.append({
                        'time': round(msgTime, 3),
                        'category': str(msg.get('Category', '')),
                        'message': str(msg.get('Message', '')),
                        'flag': str(msg.get('Flag', '')),
                        'scope': str(msg.get('Scope', '')),
                        'sector': str(msg.get('Sector', '')),
                        'racingNumber': str(msg.get('RacingNumber', ''))
                    })
            
            formatted.sort(key=lambda m: m['time'])
            return formatted
        except Exception as e:
            print(f'Could not process race control: {e}')
            return []
    
    def _getTyreCompoundInt(self, compound):
        mapping = {
            'SOFT': 0,
            'MEDIUM': 1,
            'HARD': 2,
            'INTERMEDIATE': 3,
            'WET': 4
        }
        return mapping.get(str(compound).upper(), 0)
    
    def _getDriverColors(self, session):
        """Get driver colors from FastF1 or use defaults"""
        try:
            # Try to get colors from session results
            colors = {}
            for driver in session.drivers:
                driver_info = session.get_driver(driver)
                abbr = driver_info['Abbreviation']
                
                # Try to get team color
                team = driver_info.get('TeamName', '')
                
                # Map teams to colors (2024 season)
                team_colors = {
                    'Red Bull Racing': '#3671C6',
                    'Mercedes': '#27F4D2',
                    'Ferrari': '#E8002D',
                    'McLaren': '#FF8000',
                    'Aston Martin': '#229971',
                    'Alpine': '#0093CC',
                    'Haas F1 Team': '#B6BABD',
                    'RB': '#6692FF',
                    'Williams': '#64C4FF',
                    'Kick Sauber': '#52E252',
                    'Sauber': '#52E252',
                    'AlphaTauri': '#6692FF',
                    'Alfa Romeo': '#C92D4B'
                }
                
                # Find matching team color
                color = '#FFFFFF'
                for team_name, team_color in team_colors.items():
                    if team_name.lower() in team.lower():
                        color = team_color
                        break
                
                colors[abbr] = color
            
            print(f'✅ Got colors for {len(colors)} drivers')
            return colors
            
        except Exception as e:
            print(f'⚠️ Could not get driver colors: {e}')
            # Return default colors
            return {
                'VER': '#3671C6', 'PER': '#3671C6',
                'HAM': '#27F4D2', 'RUS': '#27F4D2',
                'LEC': '#E8002D', 'SAI': '#E8002D',
                'NOR': '#FF8000', 'PIA': '#FF8000',
                'ALO': '#229971', 'STR': '#229971',
                'OCO': '#0093CC', 'GAS': '#0093CC',
                'BOT': '#52E252', 'ZHO': '#52E252',
                'MAG': '#B6BABD', 'HUL': '#B6BABD',
                'TSU': '#6692FF', 'RIC': '#6692FF',
                'ALB': '#64C4FF', 'SAR': '#64C4FF'
            }
    
    def _getEnhancedTrackLayout(self, session):
        """Get track layout with DRS zones and bounds"""
        try:
            fastestLap = session.laps.pick_fastest()
            tel = fastestLap.get_telemetry()
            return buildTrackFromLap(tel)
        except Exception as e:
            print(f'Error getting track layout: {e}')
            return {'x': [], 'y': [], 'distance': []}
