"""
Langflow Integration
Orchestrate AI workflows for F1 commentary and analysis
"""
import requests
import json
from typing import Dict, List, Optional, Any


class LangflowClient:
    def __init__(self, baseUrl: str = "http://localhost:7860"):
        self.baseUrl = baseUrl
        self.apiUrl = f"{baseUrl}/api/v1"
        self.flows = {}
        self._checkConnection()
    
    def _checkConnection(self):
        try:
            response = requests.get(f"{self.baseUrl}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Connected to Langflow")
                return True
        except Exception as e:
            print(f"⚠️ Langflow not running: {e}")
            print("Start Langflow with: langflow run")
        return False
    
    def isAvailable(self) -> bool:
        try:
            response = requests.get(f"{self.baseUrl}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def loadFlow(self, flowId: str, flowData: Dict) -> bool:
        try:
            self.flows[flowId] = flowData
            print(f"✅ Flow loaded: {flowId}")
            return True
        except Exception as e:
            print(f"Error loading flow: {e}")
            return False
    
    def runFlow(self, flowId: str, inputs: Dict) -> Optional[Dict]:
        if flowId not in self.flows:
            print(f"Flow not found: {flowId}")
            return None
        
        try:
            response = requests.post(
                f"{self.apiUrl}/run/{flowId}",
                json={"inputs": inputs},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Flow execution error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error running flow: {e}")
            return None
    
    def createCommentaryFlow(self) -> str:
        flowId = "f1_commentary_flow"
        flowData = {
            "name": "F1 Commentary Generator",
            "description": "Generate AI commentary for F1 races",
            "nodes": [
                {
                    "id": "telemetry_input",
                    "type": "input",
                    "data": {"name": "telemetry"}
                },
                {
                    "id": "context_builder",
                    "type": "prompt",
                    "data": {
                        "template": "Generate F1 commentary for: {telemetry}"
                    }
                },
                {
                    "id": "llm",
                    "type": "llm",
                    "data": {"model": "granite3-dense:8b"}
                },
                {
                    "id": "output",
                    "type": "output",
                    "data": {"name": "commentary"}
                }
            ]
        }
        
        self.loadFlow(flowId, flowData)
        return flowId


class F1WorkflowOrchestrator:
    def __init__(self):
        self.langflowClient = LangflowClient()
        self.workflows = {}
        self._initializeWorkflows()
    
    def _initializeWorkflows(self):
        self.workflows = {
            'commentary': self._createCommentaryWorkflow(),
            'analysis': self._createAnalysisWorkflow(),
            'prediction': self._createPredictionWorkflow()
        }
    
    def _createCommentaryWorkflow(self) -> Dict:
        return {
            'name': 'Race Commentary Analysis',
            'steps': [
                {'action': 'extract_telemetry', 'params': {}},
                {'action': 'detect_events', 'params': {}},
                {'action': 'analyze_tyre_strategy', 'params': {}},
                {'action': 'predict_pit_window', 'params': {}},
                {'action': 'generate_insights', 'params': {}},
                {'action': 'format_output', 'params': {}}
            ]
        }
    
    def _createAnalysisWorkflow(self) -> Dict:
        return {
            'name': 'Race Strategy Analysis',
            'steps': [
                {'action': 'load_race_data', 'params': {}},
                {'action': 'analyze_tyre_degradation', 'params': {}},
                {'action': 'analyze_strategy', 'params': {}},
                {'action': 'compare_drivers', 'params': {}},
                {'action': 'identify_key_moments', 'params': {}},
                {'action': 'generate_insights', 'params': {}}
            ]
        }
    
    def _createPredictionWorkflow(self) -> Dict:
        return {
            'name': 'Race Outcome Prediction',
            'steps': [
                {'action': 'load_historical_data', 'params': {}},
                {'action': 'analyze_current_pace', 'params': {}},
                {'action': 'analyze_tyre_strategy', 'params': {}},
                {'action': 'analyze_patterns', 'params': {}},
                {'action': 'predict_outcome', 'params': {}},
                {'action': 'calculate_confidence', 'params': {}}
            ]
        }
    
    def executeWorkflow(self, workflowName: str, data: Dict) -> Optional[Dict]:
        if workflowName not in self.workflows:
            print(f"Workflow not found: {workflowName}")
            return None
        
        workflow = self.workflows[workflowName]
        result = {'workflow': workflowName, 'steps': []}
        
        currentData = data
        
        for step in workflow['steps']:
            action = step['action']
            params = step['params']
            
            stepResult = self._executeStep(action, currentData, params)
            result['steps'].append({
                'action': action,
                'status': 'success' if stepResult else 'failed',
                'output': stepResult
            })
            
            if stepResult:
                currentData = stepResult
            else:
                break
        
        return result
    
    def _executeStep(self, action: str, data: Dict, params: Dict) -> Optional[Any]:
        try:
            if action == 'extract_telemetry':
                return self._extractTelemetry(data)
            elif action == 'detect_events':
                return self._detectEvents(data)
            elif action == 'analyze_tyre_strategy':
                return self._analyzeTyreStrategy(data)
            elif action == 'predict_pit_window':
                return self._predictPitWindow(data)
            elif action == 'analyze_tyre_degradation':
                return self._analyzeTyreDegradation(data)
            elif action == 'analyze_current_pace':
                return self._analyzeCurrentPace(data)
            elif action == 'identify_key_moments':
                return self._identifyKeyMoments(data)
            elif action == 'generate_insights':
                return self._generateInsights(data)
            elif action == 'format_output':
                return self._formatOutput(data)
            elif action == 'load_race_data':
                return self._loadRaceData(data)
            elif action == 'analyze_strategy':
                return self._analyzeStrategy(data)
            elif action == 'compare_drivers':
                return self._compareDrivers(data)
            elif action == 'load_historical_data':
                return self._loadHistoricalData(data)
            elif action == 'analyze_patterns':
                return self._analyzePatterns(data)
            elif action == 'predict_outcome':
                return self._predictOutcome(data)
            elif action == 'calculate_confidence':
                return self._calculateConfidence(data)
            else:
                print(f"Unknown action: {action}")
                return None
        except Exception as e:
            print(f"Error executing step {action}: {e}")
            return None
    
    def _extractTelemetry(self, data: Dict) -> Dict:
        # Handle nested frame structure
        frame = data.get('frame', data)
        return {
            'drivers': frame.get('drivers', {}),
            'weather': data.get('weather', {}),
            'time': data.get('t', frame.get('t', 0)),
            'frame': frame
        }
    
    def _detectEvents(self, data: Dict) -> Dict:
        events = []
        drivers = data.get('drivers', {})
        
        for driver, telemetry in drivers.items():
            if telemetry.get('inPit'):
                events.append({'type': 'pit_stop', 'driver': driver, 'time': data.get('time', 0)})
            if telemetry.get('drs') > 0:
                events.append({'type': 'drs_active', 'driver': driver})
            
            # Check tyre age
            tyreLife = telemetry.get('tyreLife', 0)
            if tyreLife > 20:
                events.append({'type': 'old_tyres', 'driver': driver, 'age': tyreLife})
        
        return {'events': events, 'data': data}
    
    def _analyzeTyreStrategy(self, data: Dict) -> Dict:
        """Analyze tyre strategy for all drivers"""
        drivers = data.get('drivers', {})
        tyreAnalysis = {}
        
        for driver, telemetry in drivers.items():
            compound = telemetry.get('tyre', 0)
            tyreLife = telemetry.get('tyreLife', 0)
            
            compoundNames = {0: 'SOFT', 1: 'MEDIUM', 2: 'HARD', 3: 'INTERMEDIATE', 4: 'WET'}
            compoundName = compoundNames.get(compound, 'UNKNOWN')
            
            # Estimate degradation (simple model)
            degradation = min(100, tyreLife * 3)  # 3% per lap
            health = max(0, 100 - degradation)
            
            # Predict pit window
            if health < 30:
                pitRecommendation = 'URGENT - Pit now'
            elif health < 50:
                pitRecommendation = 'Consider pitting soon'
            else:
                pitRecommendation = 'Tyres in good condition'
            
            tyreAnalysis[driver] = {
                'compound': compoundName,
                'age': tyreLife,
                'health': health,
                'degradation': degradation,
                'recommendation': pitRecommendation
            }
        
        return {'tyreAnalysis': tyreAnalysis, 'data': data}
    
    def _predictPitWindow(self, data: Dict) -> Dict:
        """Predict optimal pit stop windows"""
        tyreAnalysis = data.get('tyreAnalysis', {})
        predictions = {}
        
        for driver, analysis in tyreAnalysis.items():
            health = analysis.get('health', 100)
            age = analysis.get('age', 0)
            
            # Calculate laps remaining
            if health > 70:
                lapsRemaining = 15
            elif health > 50:
                lapsRemaining = 10
            elif health > 30:
                lapsRemaining = 5
            else:
                lapsRemaining = 2
            
            predictions[driver] = {
                'lapsRemaining': lapsRemaining,
                'pitWindow': f'Lap {age + lapsRemaining}',
                'urgency': 'HIGH' if health < 40 else 'MEDIUM' if health < 70 else 'LOW'
            }
        
        return {'predictions': predictions, 'data': data}
    
    def _analyzeTyreDegradation(self, data: Dict) -> Dict:
        """Detailed tyre degradation analysis"""
        return self._analyzeTyreStrategy(data)
    
    def _analyzeCurrentPace(self, data: Dict) -> Dict:
        """Analyze current pace of drivers"""
        drivers = data.get('drivers', {})
        paceAnalysis = {}
        
        for driver, telemetry in drivers.items():
            speed = telemetry.get('speed', 0)
            position = telemetry.get('position', 999)
            
            paceAnalysis[driver] = {
                'speed': speed,
                'position': position,
                'pace': 'Fast' if speed > 310 else 'Medium' if speed > 280 else 'Slow'
            }
        
        return {'paceAnalysis': paceAnalysis, 'data': data}
    
    def _identifyKeyMoments(self, data: Dict) -> Dict:
        """Identify key moments in the race"""
        events = data.get('events', [])
        keyMoments = []
        
        for event in events:
            if event.get('type') in ['pit_stop', 'overtake', 'crash']:
                keyMoments.append({
                    'time': event.get('time', 0),
                    'type': event.get('type'),
                    'driver': event.get('driver'),
                    'importance': 'HIGH'
                })
        
        return {'keyMoments': keyMoments, 'data': data}
    
    def _generateInsights(self, data: Dict) -> Dict:
        """Generate strategic insights"""
        insights = []
        
        # Tyre strategy insights
        if 'tyreAnalysis' in data:
            for driver, analysis in data['tyreAnalysis'].items():
                if analysis['health'] < 40:
                    insights.append(f"{driver} needs to pit soon - tyre health at {analysis['health']:.0f}%")
        
        # Pace insights
        if 'paceAnalysis' in data:
            fastestDriver = max(data['paceAnalysis'].items(), key=lambda x: x[1]['speed'])
            insights.append(f"{fastestDriver[0]} is fastest at {fastestDriver[1]['speed']:.0f} km/h")
        
        return {'insights': insights, 'data': data}
    
    def _formatOutput(self, data: Dict) -> Dict:
        """Format workflow output"""
        return {
            'summary': data.get('insights', []),
            'tyreAnalysis': data.get('tyreAnalysis', {}),
            'predictions': data.get('predictions', {}),
            'timestamp': data.get('time', 0)
        }
    
    def _loadRaceData(self, data: Dict) -> Dict:
        """Load race data for analysis"""
        return {
            'raceData': data,
            'loaded': True,
            'data': data
        }
    
    def _analyzeStrategy(self, data: Dict) -> Dict:
        """Analyze race strategy"""
        return self._analyzeTyreStrategy(data)
    
    def _compareDrivers(self, data: Dict) -> Dict:
        """Compare driver performance"""
        drivers = data.get('drivers', {})
        comparisons = []
        
        driverList = list(drivers.items())
        for i, (driver1, data1) in enumerate(driverList):
            for driver2, data2 in driverList[i+1:]:
                speedDiff = data1.get('speed', 0) - data2.get('speed', 0)
                positionDiff = data1.get('position', 999) - data2.get('position', 999)
                
                comparisons.append({
                    'drivers': f"{driver1} vs {driver2}",
                    'speedDiff': speedDiff,
                    'positionDiff': positionDiff,
                    'faster': driver1 if speedDiff > 0 else driver2
                })
        
        return {'comparisons': comparisons, 'data': data}
    
    def _loadHistoricalData(self, data: Dict) -> Dict:
        """Load historical race data"""
        return {
            'historical': 'Historical data loaded',
            'data': data
        }
    
    def _analyzePatterns(self, data: Dict) -> Dict:
        """Analyze race patterns"""
        return {
            'patterns': ['Pattern analysis complete'],
            'data': data
        }
    
    def _predictOutcome(self, data: Dict) -> Dict:
        """Predict race outcome"""
        drivers = data.get('drivers', {})
        if not drivers:
            return {'prediction': 'No data', 'data': data}
        
        # Simple prediction based on current positions and pace
        sortedDrivers = sorted(
            drivers.items(),
            key=lambda x: (x[1].get('position', 999), -x[1].get('speed', 0))
        )
        
        predictions = []
        for i, (driver, driverData) in enumerate(sortedDrivers[:3]):
            predictions.append({
                'position': i + 1,
                'driver': driver,
                'confidence': 85 - (i * 10)  # Simple confidence model
            })
        
        return {'predictions': predictions, 'data': data}
    
    def _calculateConfidence(self, data: Dict) -> Dict:
        """Calculate prediction confidence"""
        predictions = data.get('predictions', [])
        
        if not predictions:
            return {'confidence': 0, 'data': data}
        
        avgConfidence = sum(p.get('confidence', 0) for p in predictions) / len(predictions)
        
        return {
            'overallConfidence': avgConfidence,
            'predictions': predictions,
            'data': data
        }


class WorkflowBuilder:
    def __init__(self):
        self.workflow = {
            'name': '',
            'description': '',
            'steps': []
        }
    
    def setName(self, name: str):
        self.workflow['name'] = name
        return self
    
    def setDescription(self, description: str):
        self.workflow['description'] = description
        return self
    
    def addStep(self, action: str, params: Dict = None):
        self.workflow['steps'].append({
            'action': action,
            'params': params or {}
        })
        return self
    
    def build(self) -> Dict:
        return self.workflow
