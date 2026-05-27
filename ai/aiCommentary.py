"""
AI Commentary Module using Google Gemini
Generates real-time F1 race commentary based on telemetry data
Integrated with Docling for regulations and Langflow for workflows
"""
import os
import requests
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AICommentary:
    def __init__(self, apiKey: str = None):
        self.apiKey = apiKey or os.getenv('GEMINI_API_KEY')
        if not self.apiKey:
            raise ValueError("GEMINI_API_KEY not found. Please set it in .env file")
        self.modelName = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.baseUrl = "https://generativelanguage.googleapis.com/v1beta"
        self.contextWindow = []
        self.maxContext = 5
        self.regulationsKnowledge = {}  # Loaded from Docling
        
    def loadRegulationsKnowledge(self, regulations: Dict):
        """Load F1 regulations knowledge from Docling processor"""
        self.regulationsKnowledge = regulations
        sections_count = len(regulations.get('sections', []))
        print(f"✅ Loaded regulations knowledge: {sections_count} sections")
        print(f"   Available rules: {list(regulations.keys())}")
        
    def generateCommentary(self, telemetryData: Dict, eventType: str = "general") -> str:
        prompt = self._buildPrompt(telemetryData, eventType)
        
        try:
            url = f"{self.baseUrl}/models/{self.modelName}:generateContent?key={self.apiKey}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 150,
                    "topP": 0.9
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    commentary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    self._updateContext(commentary)
                    return commentary
            
            return self._fallbackCommentary(telemetryData, eventType)
                
        except Exception as e:
            print(f"AI Commentary error: {e}")
            return self._fallbackCommentary(telemetryData, eventType)
    
    def _buildPrompt(self, telemetryData: Dict, eventType: str) -> str:
        # Handle nested frame structure from replayEngine
        frame = telemetryData.get('frame', telemetryData)
        drivers = frame.get('drivers', {})
        weather = telemetryData.get('weather') or {}
        currentTime = telemetryData.get('t', frame.get('t', 0))
        
        sortedDrivers = sorted(
            drivers.items(),
            key=lambda x: x[1].get('position', 999)
        )
        
        leader = sortedDrivers[0] if sortedDrivers else None
        
        # Add tyre information
        tyreInfo = ""
        if leader:
            leaderData = leader[1]
            tyreCompound = self._getTyreCompoundName(leaderData.get('tyre', 0))
            tyreLife = leaderData.get('tyreLife', 0)
            tyreInfo = f"\n- Leader tyres: {tyreCompound}, {tyreLife} laps old"
        
        # Add regulations context if available
        regulationsContext = ""
        if self.regulationsKnowledge and eventType in ['drs_active', 'pit_stop']:
            if eventType == 'drs_active' and 'drs_rules' in self.regulationsKnowledge:
                regulationsContext = f"\n- DRS Rule: {self.regulationsKnowledge['drs_rules']}"
            elif eventType == 'pit_stop' and 'pit_rules' in self.regulationsKnowledge:
                regulationsContext = f"\n- Pit Rule: {self.regulationsKnowledge['pit_rules']}"
        
        context = f"""You are an expert F1 race commentator. Provide exciting, insightful commentary.

Current Race Situation:
- Time: {currentTime:.1f}s
- Leader: {leader[0] if leader else 'Unknown'} at {leader[1].get('speed', 0):.0f} km/h
- Weather: {weather.get('rainState', 'DRY')}, Track Temp: {weather.get('trackTemp', 0):.1f}°C{tyreInfo}{regulationsContext}

Event Type: {eventType}

Recent Context:
{chr(10).join(self.contextWindow[-3:]) if self.contextWindow else 'Race start'}

Generate a brief, exciting commentary (1-2 sentences) about the current situation:"""
        
        return context
    
    def _getTyreCompoundName(self, compound: int) -> str:
        compounds = {0: 'SOFT', 1: 'MEDIUM', 2: 'HARD', 3: 'INTERMEDIATE', 4: 'WET'}
        return compounds.get(compound, 'UNKNOWN')
    
    def _updateContext(self, commentary: str):
        self.contextWindow.append(commentary)
        if len(self.contextWindow) > self.maxContext:
            self.contextWindow.pop(0)
    
    def _fallbackCommentary(self, telemetryData: Dict, eventType: str) -> str:
        # Handle nested frame structure
        frame = telemetryData.get('frame', telemetryData)
        drivers = frame.get('drivers', {})
        
        if not drivers:
            return "The race is underway!"
        
        if eventType == "overtake":
            return "What an incredible overtaking maneuver!"
        elif eventType == "pit_stop":
            return "Into the pits for fresh tyres!"
        elif eventType == "crash":
            return "Oh no! We have an incident on track!"
        else:
            leader = max(drivers.items(), key=lambda x: x[1].get('speed', 0))
            return f"{leader[0]} is pushing hard at {leader[1].get('speed', 0):.0f} km/h!"
    
    def detectEvents(self, currentFrame: Dict, previousFrame: Optional[Dict]) -> List[str]:
        if not currentFrame or not previousFrame:
            return []
        
        events = []
        
        # Handle nested frame structure
        currentFrameData = currentFrame.get('frame', currentFrame)
        previousFrameData = previousFrame.get('frame', previousFrame)
        
        currentDrivers = currentFrameData.get('drivers', {})
        previousDrivers = previousFrameData.get('drivers', {})
        
        if not currentDrivers or not previousDrivers:
            return []
        
        for driver, data in currentDrivers.items():
            if driver not in previousDrivers or not data or not previousDrivers[driver]:
                continue
            
            prevData = previousDrivers[driver]
            
            if data.get('inPit') and not prevData.get('inPit'):
                events.append(f"pit_stop:{driver}")
            
            if data.get('position') != prevData.get('position'):
                if data.get('position') < prevData.get('position'):
                    events.append(f"overtake:{driver}")
            
            if data.get('drs') > 0 and prevData.get('drs') == 0:
                events.append(f"drs_active:{driver}")
            
            if data.get('speed', 0) > 320:
                events.append(f"high_speed:{driver}")
        
        return events


class CommentaryManager:
    def __init__(self):
        self.aiCommentary = AICommentary()
        self.lastCommentaryTime = 0
        self.commentaryInterval = 90.0  # Generate every 1.5 minutes (90 seconds)
        self.commentaryHistory = []
        self.workflowOrchestrator = None  # Langflow integration
        self.analysisResults = []  # Store workflow analysis results
        self.lastCommentaryRealTime = 0  # Track real-world time for rate limiting
        
        # Accumulate data over the interval
        self.accumulatedEvents = []  # Store all events during the interval
        self.intervalStartTime = 0
        self.intervalFrames = []  # Store key frames during interval
        self.maxFramesToStore = 10  # Store up to 10 representative frames
    
    def setWorkflowOrchestrator(self, orchestrator):
        """Integrate Langflow workflow orchestrator"""
        self.workflowOrchestrator = orchestrator
        print("✅ Langflow orchestrator integrated with commentary manager")
    
    def loadRegulations(self, regulations: Dict):
        """Load F1 regulations from Docling"""
        self.aiCommentary.loadRegulationsKnowledge(regulations)
    
    def shouldGenerateCommentary(self, currentTime: float) -> bool:
        """
        Check if 1.5 minutes (90 seconds) have passed in real-world time.
        This allows accumulating events and data for comprehensive commentary.
        """
        import time
        currentRealTime = time.time()
        
        # Initialize on first call
        if self.lastCommentaryRealTime == 0:
            self.lastCommentaryRealTime = currentRealTime
            self.intervalStartTime = currentTime
            return False
        
        # Check if 90 seconds (1.5 minutes) have passed in real-world time
        timeSinceLastCommentary = currentRealTime - self.lastCommentaryRealTime
        if timeSinceLastCommentary >= self.commentaryInterval:
            print(f"✅ Commentary interval reached! {timeSinceLastCommentary:.1f}s elapsed (1.5 minutes)")
            print(f"📊 Accumulated {len(self.accumulatedEvents)} events over this period")
            self.lastCommentaryRealTime = currentRealTime
            return True
        return False
    
    def generateForFrame(self, currentFrame: Dict, previousFrame: Optional[Dict] = None) -> Optional[str]:
        if not currentFrame:
            print("⚠️ No current frame provided")
            return None
            
        currentTime = currentFrame.get('t', 0)
        
        # Detect events in this frame
        events = self.aiCommentary.detectEvents(currentFrame, previousFrame)
        
        # Accumulate events for the interval
        if events:
            print(f"🎯 Events detected: {events}")
            for event in events:
                self.accumulatedEvents.append({
                    'event': event,
                    'time': currentTime,
                    'frame': currentFrame
                })
        
        # Store representative frames (every Nth frame to avoid memory issues)
        if len(self.intervalFrames) < self.maxFramesToStore:
            self.intervalFrames.append({
                'time': currentTime,
                'frame': currentFrame
            })
        
        # Run Langflow analysis workflow for important events
        if events and self.workflowOrchestrator:
            try:
                analysisResult = self.workflowOrchestrator.executeWorkflow('commentary', {
                    'frame': currentFrame,
                    'events': events,
                    'time': currentTime
                })
                if analysisResult:
                    self.analysisResults.append(analysisResult)
                    print(f"📊 Workflow analysis completed")
            except Exception as e:
                print(f"Workflow analysis error: {e}")
        
        # Check if it's time to generate comprehensive commentary
        if self.shouldGenerateCommentary(currentTime):
            print(f"🎙️ Generating comprehensive commentary for the last 1.5 minutes")
            print(f"   Period: {self.intervalStartTime:.1f}s - {currentTime:.1f}s")
            
            # Generate commentary based on accumulated data
            commentary = self._generateIntervalCommentary(currentFrame, currentTime)
            
            # Reset accumulated data for next interval
            self.intervalStartTime = currentTime
            self.accumulatedEvents = []
            self.intervalFrames = []
            
            self.lastCommentaryTime = currentTime
            self.commentaryHistory.append({
                'time': currentTime,
                'text': commentary,
                'event': 'interval_summary',
                'events': []
            })
            return commentary
        
        return None
    
    def getCommentaryHistory(self) -> List[Dict]:
        return self.commentaryHistory
    
    def getAnalysisResults(self) -> List[Dict]:
        """Get Langflow workflow analysis results"""
        return self.analysisResults
    
    def _generateIntervalCommentary(self, currentFrame: Dict, currentTime: float) -> str:
        """
        Generate comprehensive commentary based on accumulated events and data
        over the last 1.5 minutes.
        """
        # Analyze accumulated events
        eventSummary = self._summarizeEvents()
        
        # Get current race state
        frame = currentFrame.get('frame', currentFrame)
        drivers = frame.get('drivers', {})
        weather = currentFrame.get('weather') or {}
        
        # Sort drivers by position
        sortedDrivers = sorted(
            drivers.items(),
            key=lambda x: x[1].get('position', 999)
        )
        
        # Get top 3 drivers
        top3 = sortedDrivers[:3] if len(sortedDrivers) >= 3 else sortedDrivers
        
        # Build comprehensive prompt
        prompt = f"""You are an expert F1 race commentator. Generate a comprehensive, exciting commentary summarizing the last 1.5 minutes of the race.

CURRENT RACE STATE (at {currentTime:.1f}s):
- Leader: {top3[0][0] if top3 else 'Unknown'} at {top3[0][1].get('speed', 0):.0f} km/h
- P2: {top3[1][0] if len(top3) > 1 else 'N/A'} (Gap: +{top3[1][1].get('gapToLeader', 0):.1f}s)
- P3: {top3[2][0] if len(top3) > 2 else 'N/A'} (Gap: +{top3[2][1].get('gapToLeader', 0):.1f}s)
- Weather: {weather.get('rainState', 'DRY')}, Track Temp: {weather.get('trackTemp', 0):.1f}°C

EVENTS IN LAST 1.5 MINUTES:
{eventSummary}

TYRE SITUATION:
{self._getTyreSummary(drivers)}

Generate a structured commentary (3-4 sentences) covering:
1. The most important event or battle
2. Current race leader situation
3. Any strategic developments (pit stops, tyre management)
4. What to watch for next

Keep it exciting and insightful like a real F1 commentator!"""
        
        try:
            url = f"{self.aiCommentary.baseUrl}/models/{self.aiCommentary.modelName}:generateContent?key={self.aiCommentary.apiKey}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 250,
                    "topP": 0.9
                }
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    commentary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    print(f"✅ Generated comprehensive commentary: {commentary[:100]}...")
                    return commentary
            
            # Fallback if API fails
            return self._generateFallbackIntervalCommentary(eventSummary, top3)
                
        except Exception as e:
            print(f"❌ Error generating interval commentary: {e}")
            return self._generateFallbackIntervalCommentary(eventSummary, top3)
    
    def _summarizeEvents(self) -> str:
        """Summarize accumulated events into readable text"""
        if not self.accumulatedEvents:
            return "- No major events during this period"
        
        # Count event types
        eventCounts = {}
        eventDetails = []
        
        for eventData in self.accumulatedEvents:
            event = eventData['event']
            eventType = event.split(':')[0]
            driver = event.split(':')[1] if ':' in event else 'Unknown'
            
            if eventType not in eventCounts:
                eventCounts[eventType] = []
            eventCounts[eventType].append(driver)
        
        # Format event summary
        summary = []
        if 'pit_stop' in eventCounts:
            drivers = ', '.join(set(eventCounts['pit_stop']))
            summary.append(f"- Pit stops: {drivers}")
        
        if 'overtake' in eventCounts:
            drivers = ', '.join(set(eventCounts['overtake']))
            summary.append(f"- Overtakes by: {drivers}")
        
        if 'drs_active' in eventCounts:
            summary.append(f"- DRS battles ongoing")
        
        if 'high_speed' in eventCounts:
            drivers = ', '.join(set(eventCounts['high_speed'][:3]))  # Top 3
            summary.append(f"- High speeds (>320 km/h): {drivers}")
        
        return '\n'.join(summary) if summary else "- Steady racing, no major incidents"
    
    def _getTyreSummary(self, drivers: Dict) -> str:
        """Generate tyre situation summary"""
        if not drivers:
            return "- No tyre data available"
        
        # Get tyre info for top 5 drivers
        sortedDrivers = sorted(
            drivers.items(),
            key=lambda x: x[1].get('position', 999)
        )[:5]
        
        tyreSummary = []
        for code, data in sortedDrivers:
            compound = self.aiCommentary._getTyreCompoundName(data.get('tyre', 0))
            age = data.get('tyreLife', 0)
            tyreSummary.append(f"  {code}: {compound} ({age} laps)")
        
        return '\n'.join(tyreSummary) if tyreSummary else "- No tyre data"
    
    def _generateFallbackIntervalCommentary(self, eventSummary: str, top3: List) -> str:
        """Generate fallback commentary if API fails"""
        leader = top3[0][0] if top3 else 'Unknown'
        
        if 'Pit stops' in eventSummary:
            return f"We've seen some pit stop action in the last 1.5 minutes! {leader} continues to lead the race. The strategy battle is heating up as teams make their moves."
        elif 'Overtakes' in eventSummary:
            return f"Exciting racing action! Multiple overtakes in the last 1.5 minutes. {leader} is currently leading, but the battle is far from over!"
        else:
            return f"Steady racing over the last 1.5 minutes. {leader} maintains the lead, managing the pace at the front. Teams are monitoring tyre wear and planning their strategies."
