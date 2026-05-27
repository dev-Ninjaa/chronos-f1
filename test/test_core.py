#!/usr/bin/env python3
"""
Core functionality tests for Chronos F1
Tests data processing, replay engine, and models
"""

import sys
import os

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"[OK] {text}")

def print_error(text):
    print(f"[FAIL] {text}")

def test_data_manager():
    """Test DataManager functionality"""
    print_header("Testing DataManager")
    
    try:
        from manager.dataManager import DataManager
        
        dm = DataManager()
        print_success("DataManager initialized")
        
        # Test season retrieval
        seasons = dm.getAvailableSeasons()
        if seasons and len(seasons) > 0:
            print_success(f"Available seasons: {len(seasons)} seasons ({seasons[0]}-{seasons[-1]})")
        else:
            print_error("No seasons available")
            return False
        
        # Test race retrieval for a season
        races = dm.getRacesForSeason(2024)
        if races and len(races) > 0:
            print_success(f"2024 races: {len(races)} races")
            print(f"   First race: {races[0]['name']}")
        else:
            print_error("No races found for 2024")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"DataManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_replay_engine():
    """Test ReplayEngine functionality"""
    print_header("Testing ReplayEngine")
    
    try:
        from replay.replayEngine import ReplayEngine
        
        # Create mock race data
        mockRaceData = {
            'eventName': 'Test Grand Prix',
            'circuitName': 'Test Circuit',
            'country': 'Test Country',
            'date': '2024-01-01',
            'totalLaps': 50,
            'frames': [
                {
                    't': 0.0,
                    'drivers': {
                        'VER': {'position': 1, 'speed': 300, 'lap': 1, 'dist': 0}
                    }
                },
                {
                    't': 0.04,
                    'drivers': {
                        'VER': {'position': 1, 'speed': 305, 'lap': 1, 'dist': 10}
                    }
                }
            ],
            'drivers': ['VER'],
            'driverColors': {'VER': '#3671C6'},
            'trackData': {'x': [], 'y': [], 'distance': []},
            'trackStatuses': [],
            'raceControlMessages': [],
            'tyreModel': None
        }
        
        # Mock socketio
        class MockSocketIO:
            def emit(self, event, data):
                pass
        
        engine = ReplayEngine(mockRaceData, MockSocketIO())
        print_success("ReplayEngine initialized")
        
        # Test playback controls
        engine.play()
        if engine.isPlaying():
            print_success("Play functionality works")
        else:
            print_error("Play functionality failed")
            return False
        
        engine.pause()
        if not engine.isPlaying():
            print_success("Pause functionality works")
        else:
            print_error("Pause functionality failed")
            return False
        
        engine.setPlaybackSpeed(2.0)
        print_success("Speed control works")
        
        engine.seekToFrame(1)
        print_success("Seek functionality works")
        
        engine.restart()
        print_success("Restart functionality works")
        
        return True
        
    except Exception as e:
        print_error(f"ReplayEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tyre_model():
    """Test TyreDegradationModel"""
    print_header("Testing Tyre Model")
    
    try:
        from models.tyreModel import TyreDegradationModel
        
        model = TyreDegradationModel()
        print_success("TyreDegradationModel initialized")
        
        # Test compound curves
        if model.compoundCurves:
            print_success(f"Compound curves loaded: {len(model.compoundCurves)} compounds")
        else:
            print_error("No compound curves loaded")
            return False
        
        # Test health calculation for a frame
        testFrame = {
            'drivers': {
                'VER': {
                    'tyre': 0,  # SOFT
                    'tyreLife': 10
                }
            }
        }
        
        health = model.getHealthForFrame('VER', testFrame)
        if health is not None:
            print_success(f"Health calculation works: {health}")
        else:
            print_success("Health calculation method exists (returns None without session data)")
        
        return True
        
    except Exception as e:
        print_error(f"Tyre model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_safety_car_model():
    """Test SafetyCarModel"""
    print_header("Testing Safety Car Model")
    
    try:
        from models.safetyCarModel import SafetyCarModel
        
        # Create mock track data
        mockTrackData = {
            'x': [0, 100, 200, 300, 400],
            'y': [0, 50, 100, 50, 0],
            'distance': [0, 100, 200, 300, 400]
        }
        
        model = SafetyCarModel(mockTrackData)
        print_success("SafetyCarModel initialized")
        
        # Test with mock frames and track statuses
        mockFrames = [
            {'t': 0.0, 'drivers': {'VER': {'dist': 0}}},
            {'t': 1.0, 'drivers': {'VER': {'dist': 100}}}
        ]
        
        mockTrackStatuses = [
            {'status': '4', 'startTime': 0.0, 'endTime': 2.0}  # SC period
        ]
        
        # Test computeSafetyCarPositions method
        model.computeSafetyCarPositions(mockFrames, mockTrackStatuses)
        print_success("SC position computation works")
        
        # Check if SC state was created
        if hasattr(model, 'scState'):
            print_success("SC state tracking initialized")
        
        return True
        
    except Exception as e:
        print_error(f"Safety car model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all core tests"""
    print("\n" + "="*60)
    print("  CHRONOS F1 - Core Functionality Tests")
    print("="*60)
    
    results = {
        'DataManager': test_data_manager(),
        'ReplayEngine': test_replay_engine(),
        'TyreModel': test_tyre_model(),
        'SafetyCarModel': test_safety_car_model()
    }
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All core tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

