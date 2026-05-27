"""
Tyre Degradation Model - Bayesian statistical model for tyre health prediction
"""
import numpy as np
from typing import Dict, List, Optional


class TyreDegradationModel:
    """Bayesian tyre degradation model with compound-specific curves"""
    
    def __init__(self):
        self.compoundCurves = {
            0: {'name': 'SOFT', 'baseLife': 25, 'degradationRate': 0.045},
            1: {'name': 'MEDIUM', 'baseLife': 35, 'degradationRate': 0.032},
            2: {'name': 'HARD', 'baseLife': 45, 'degradationRate': 0.025},
            3: {'name': 'INTERMEDIATE', 'baseLife': 30, 'degradationRate': 0.035},
            4: {'name': 'WET', 'baseLife': 28, 'degradationRate': 0.040}
        }
        self.driverStints = {}
    
    def initializeFromSession(self, session):
        """Initialize model from session data"""
        try:
            for driverNum in session.drivers:
                code = session.get_driver(driverNum)['Abbreviation']
                laps = session.laps.pick_drivers(driverNum)
                
                if laps.empty:
                    continue
                
                stints = []
                currentStint = None
                
                for _, lap in laps.iterlaps():
                    compound = lap['Compound']
                    tyreLife = lap['TyreLife']
                    
                    if currentStint is None or currentStint['compound'] != compound:
                        if currentStint:
                            stints.append(currentStint)
                        currentStint = {
                            'compound': compound,
                            'startLap': lap['LapNumber'],
                            'laps': []
                        }
                    
                    currentStint['laps'].append({
                        'lapNumber': lap['LapNumber'],
                        'tyreLife': tyreLife,
                        'lapTime': lap['LapTime'].total_seconds() if lap['LapTime'] else None
                    })
                
                if currentStint:
                    stints.append(currentStint)
                
                self.driverStints[code] = stints
            
            return True
        except Exception as e:
            print(f'Error initializing tyre model: {e}')
            return False
    
    def getHealthForFrame(self, driverCode: str, frame: dict) -> Optional[Dict]:
        """Get tyre health prediction for a specific frame"""
        try:
            driverData = frame.get('drivers', {}).get(driverCode)
            if not driverData:
                return None
            
            compound = int(driverData.get('tyre', 0))
            tyreLife = int(driverData.get('tyreLife', 0))
            
            if compound not in self.compoundCurves:
                return None
            
            curve = self.compoundCurves[compound]
            baseLife = curve['baseLife']
            degradationRate = curve['degradationRate']
            
            # Calculate health (100% at start, decreases with laps)
            health = max(0, 100 - (tyreLife * degradationRate * 100))
            
            # Predict remaining laps
            remainingLaps = max(0, int((health / 100) * baseLife))
            
            return {
                'health': health,
                'tyreLife': tyreLife,
                'compound': curve['name'],
                'remainingLaps': remainingLaps,
                'baseLife': baseLife
            }
        except Exception as e:
            return None
    
    def getTyreCompoundName(self, compoundInt: int) -> str:
        """Get tyre compound name from integer"""
        return self.compoundCurves.get(compoundInt, {}).get('name', 'UNKNOWN')
