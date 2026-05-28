"""
AI Commentary Module using local Ollama.
Generates real-time F1 race commentary based on telemetry data.
"""
from typing import Dict, List, Optional

from dotenv import load_dotenv

from ai.ollamaClient import OllamaClient, clean_commentary

load_dotenv()


class AICommentary:
    def __init__(self, apiKey: str = None):
        self.client = OllamaClient()
        self.modelName = self.client.modelName
        self.contextWindow = []
        self.maxContext = 5
        self.regulationsKnowledge = {}

    def loadRegulationsKnowledge(self, regulations: Dict):
        """Load F1 regulations knowledge from Docling processor."""
        self.regulationsKnowledge = regulations
        sections_count = len(regulations.get("sections", []))
        print(f"Loaded regulations knowledge: {sections_count} sections")
        print(f"   Available rules: {list(regulations.keys())}")

    def generateCommentary(self, telemetryData: Dict, eventType: str = "general") -> str:
        prompt = self._buildPrompt(telemetryData, eventType)

        for attempt in range(2):
            try:
                temp = 0.6 if attempt == 0 else 0.8
                commentary = clean_commentary(
                    self.client.generate(prompt, temperature=temp, maxTokens=120),
                    max_lines=3,
                )
                if commentary:
                    self._updateContext(commentary)
                    return commentary
                if attempt == 0:
                    print(f"AICommentary attempt {attempt+1} rejected, retrying...")
            except Exception as e:
                print(f"AI Commentary error (attempt {attempt+1}): {e}")

        return self._fallbackCommentary(telemetryData, eventType)

    def _buildPrompt(self, telemetryData: Dict, eventType: str) -> str:
        frame = telemetryData.get("frame", telemetryData)
        drivers = frame.get("drivers", {})
        weather = telemetryData.get("weather") or {}
        currentTime = telemetryData.get("t", frame.get("t", 0))

        sortedDrivers = sorted(
            drivers.items(),
            key=lambda item: item[1].get("position", 999),
        )
        leader = sortedDrivers[0] if sortedDrivers else None

        tyreInfo = ""
        if leader:
            leaderData = leader[1]
            tyreCompound = self._getTyreCompoundName(leaderData.get("tyre", 0))
            tyreLife = leaderData.get("tyreLife", 0)
            tyreInfo = f"\n- Leader tyres: {tyreCompound}, {tyreLife} laps old"

        regulationsContext = ""
        if self.regulationsKnowledge and eventType in ["drs_active", "pit_stop"]:
            if eventType == "drs_active" and "drs_rules" in self.regulationsKnowledge:
                regulationsContext = f"\n- DRS Rule: {self.regulationsKnowledge['drs_rules']}"
            elif eventType == "pit_stop" and "pit_rules" in self.regulationsKnowledge:
                regulationsContext = f"\n- Pit Rule: {self.regulationsKnowledge['pit_rules']}"

        return f"""Write F1 race commentary in 1 to 3 complete English sentences.

RULES:
- Write full sentences, NOT a driver code or abbreviation.
- Do NOT return JSON, quotes, markdown, or bullet points.
- Do NOT start with a driver abbreviation alone.

Current Race Situation:
- Time: {currentTime:.1f}s
- Leader: {leader[0] if leader else 'Unknown'} at {leader[1].get('speed', 0):.0f} km/h
- Weather: {weather.get('rainState', 'DRY')}, Track Temp: {weather.get('trackTemp', 0):.1f}C{tyreInfo}{regulationsContext}

Event Type: {eventType}

Recent Context:
{chr(10).join(self.contextWindow[-3:]) if self.contextWindow else 'Race start'}

Example: "Verstappen holds a comfortable lead with his medium tyres showing good pace. Hamilton is pushing hard from second, closing the gap through the technical sectors."

Write the commentary now:"""

    def _getTyreCompoundName(self, compound: int) -> str:
        compounds = {0: "SOFT", 1: "MEDIUM", 2: "HARD", 3: "INTERMEDIATE", 4: "WET"}
        return compounds.get(compound, "UNKNOWN")

    def _updateContext(self, commentary: str):
        self.contextWindow.append(commentary)
        if len(self.contextWindow) > self.maxContext:
            self.contextWindow.pop(0)

    def _fallbackCommentary(self, telemetryData: Dict, eventType: str) -> str:
        frame = telemetryData.get("frame", telemetryData)
        drivers = frame.get("drivers", {})

        if not drivers:
            return "The race is underway as the field settles into the opening rhythm."

        if eventType == "overtake":
            return "A decisive move changes the order as the battle intensifies."
        if eventType == "pit_stop":
            return "Into the pits for fresh tyres as strategy starts to shape the race."
        if eventType == "crash":
            return "There is an incident on track, and race control will be watching closely."

        leader = min(drivers.items(), key=lambda item: item[1].get("position", 999))
        return f"{leader[0]} leads the way, managing pace and tyre life at the front."

    def detectEvents(self, currentFrame: Dict, previousFrame: Optional[Dict]) -> List[str]:
        if not currentFrame or not previousFrame:
            return []

        events = []
        currentFrameData = currentFrame.get("frame", currentFrame)
        previousFrameData = previousFrame.get("frame", previousFrame)
        currentDrivers = currentFrameData.get("drivers", {})
        previousDrivers = previousFrameData.get("drivers", {})

        if not currentDrivers or not previousDrivers:
            return []

        for driver, data in currentDrivers.items():
            if driver not in previousDrivers or not data or not previousDrivers[driver]:
                continue

            prevData = previousDrivers[driver]
            if data.get("inPit") and not prevData.get("inPit"):
                events.append(f"pit_stop:{driver}")

            if data.get("position") != prevData.get("position"):
                if data.get("position") < prevData.get("position"):
                    events.append(f"overtake:{driver}")

            if data.get("drs", 0) > 0 and prevData.get("drs", 0) == 0:
                events.append(f"drs_active:{driver}")

            if data.get("speed", 0) > 320:
                events.append(f"high_speed:{driver}")

        return events


class CommentaryManager:
    def __init__(self):
        self.aiCommentary = AICommentary()
        self.lastCommentaryTime = 0
        self.commentaryInterval = 60.0
        self.commentaryHistory = []
        self.workflowOrchestrator = None
        self.analysisResults = []
        self.lastCommentaryRealTime = 0
        self.accumulatedEvents = []
        self.intervalStartTime = 0
        self.intervalFrames = []
        self.maxFramesToStore = 10

    def setWorkflowOrchestrator(self, orchestrator):
        """Integrate Langflow workflow orchestrator."""
        self.workflowOrchestrator = orchestrator
        print("Langflow orchestrator integrated with commentary manager")

    def loadRegulations(self, regulations: Dict):
        """Load F1 regulations from Docling."""
        self.aiCommentary.loadRegulationsKnowledge(regulations)

    def shouldGenerateCommentary(self, currentTime: float) -> bool:
        """Check if 1 minute has passed in real-world time."""
        import time

        currentRealTime = time.time()
        if self.lastCommentaryRealTime == 0:
            self.lastCommentaryRealTime = currentRealTime
            self.intervalStartTime = currentTime
            return False

        timeSinceLastCommentary = currentRealTime - self.lastCommentaryRealTime
        if timeSinceLastCommentary >= self.commentaryInterval:
            print(f"Commentary interval reached: {timeSinceLastCommentary:.1f}s elapsed")
            print(f"Accumulated {len(self.accumulatedEvents)} events over this period")
            self.lastCommentaryRealTime = currentRealTime
            return True
        return False

    def generateForFrame(self, currentFrame: Dict, previousFrame: Optional[Dict] = None) -> Optional[str]:
        if not currentFrame:
            print("No current frame provided")
            return None

        currentTime = currentFrame.get("t", 0)
        events = self.aiCommentary.detectEvents(currentFrame, previousFrame)

        if events:
            print(f"Events detected: {events}")
            for event in events:
                self.accumulatedEvents.append({
                    "event": event,
                    "time": currentTime,
                    "frame": currentFrame,
                })

        if len(self.intervalFrames) < self.maxFramesToStore:
            self.intervalFrames.append({
                "time": currentTime,
                "frame": currentFrame,
            })

        if events and self.workflowOrchestrator:
            try:
                analysisResult = self.workflowOrchestrator.executeWorkflow("commentary", {
                    "frame": currentFrame,
                    "events": events,
                    "time": currentTime,
                })
                if analysisResult:
                    self.analysisResults.append(analysisResult)
                    print("Workflow analysis completed")
            except Exception as e:
                print(f"Workflow analysis error: {e}")

        if self.shouldGenerateCommentary(currentTime):
            print("Generating commentary for the last 1 minute")
            print(f"   Period: {self.intervalStartTime:.1f}s - {currentTime:.1f}s")

            commentary = self._generateIntervalCommentary(currentFrame, currentTime)
            self.intervalStartTime = currentTime
            self.accumulatedEvents = []
            self.intervalFrames = []
            self.lastCommentaryTime = currentTime
            self.commentaryHistory.append({
                "time": currentTime,
                "text": commentary,
                "event": "interval_summary",
                "events": [],
            })
            return commentary

        return None

    def getCommentaryHistory(self) -> List[Dict]:
        return self.commentaryHistory

    def getAnalysisResults(self) -> List[Dict]:
        """Get Langflow workflow analysis results."""
        return self.analysisResults

    def _generateIntervalCommentary(self, currentFrame: Dict, currentTime: float) -> str:
        """Generate commentary based on accumulated events and data over 1 minute."""
        eventSummary = self._summarizeEvents()
        frame = currentFrame.get("frame", currentFrame)
        drivers = frame.get("drivers", {})
        weather = currentFrame.get("weather") or {}

        sortedDrivers = sorted(
            drivers.items(),
            key=lambda item: item[1].get("position", 999),
        )
        top3 = sortedDrivers[:3] if len(sortedDrivers) >= 3 else sortedDrivers

        prompt = f"""Write F1 race commentary summarizing the last 1 minute. Use 1 to 3 complete English sentences.

RULES:
- Write full sentences, NOT a driver code or abbreviation.
- Do NOT return JSON, quotes, markdown, or bullet points.
- Do NOT start with a driver abbreviation alone.

Current race state at {currentTime:.1f}s:
- Leader: {top3[0][0] if top3 else 'Unknown'} at {top3[0][1].get('speed', 0):.0f} km/h
- P2: {top3[1][0] if len(top3) > 1 else 'N/A'} (Gap: +{top3[1][1].get('gapToLeader', 0):.1f}s)
- P3: {top3[2][0] if len(top3) > 2 else 'N/A'} (Gap: +{top3[2][1].get('gapToLeader', 0):.1f}s)
- Weather: {weather.get('rainState', 'DRY')}, Track Temp: {weather.get('trackTemp', 0):.1f}C

Events in last 1 minute:
{eventSummary}

Tyre situation:
{self._getTyreSummary(drivers)}

Example: "Verstappen extends his lead at the front while Norris battles with Leclerc for second position. The pit window is opening as tyre degradation begins to bite across the field."

Write the commentary now:"""

        for attempt in range(2):
            try:
                temp = 0.6 if attempt == 0 else 0.8
                commentary = clean_commentary(
                    self.aiCommentary.client.generate(prompt, temperature=temp, maxTokens=160),
                    max_lines=3,
                )
                if commentary:
                    print(f"Generated commentary: {commentary[:100]}...")
                    return commentary
                if attempt == 0:
                    print(f"Interval commentary attempt {attempt+1} rejected, retrying...")
            except Exception as e:
                print(f"Error generating interval commentary (attempt {attempt+1}): {e}")

        return self._generateFallbackIntervalCommentary(eventSummary, top3)

    def _summarizeEvents(self) -> str:
        """Summarize accumulated events into readable text."""
        if not self.accumulatedEvents:
            return "- No major events during this period"

        eventCounts = {}
        for eventData in self.accumulatedEvents:
            event = eventData["event"]
            eventType = event.split(":")[0]
            driver = event.split(":")[1] if ":" in event else "Unknown"
            eventCounts.setdefault(eventType, []).append(driver)

        summary = []
        if "pit_stop" in eventCounts:
            summary.append(f"- Pit stops: {', '.join(set(eventCounts['pit_stop']))}")
        if "overtake" in eventCounts:
            summary.append(f"- Overtakes by: {', '.join(set(eventCounts['overtake']))}")
        if "drs_active" in eventCounts:
            summary.append("- DRS battles ongoing")
        if "high_speed" in eventCounts:
            summary.append(f"- High speeds over 320 km/h: {', '.join(set(eventCounts['high_speed'][:3]))}")

        return "\n".join(summary) if summary else "- Steady racing, no major incidents"

    def _getTyreSummary(self, drivers: Dict) -> str:
        """Generate tyre situation summary."""
        if not drivers:
            return "- No tyre data available"

        sortedDrivers = sorted(
            drivers.items(),
            key=lambda item: item[1].get("position", 999),
        )[:5]

        tyreSummary = []
        for code, data in sortedDrivers:
            compound = self.aiCommentary._getTyreCompoundName(data.get("tyre", 0))
            age = data.get("tyreLife", 0)
            tyreSummary.append(f"  {code}: {compound} ({age} laps)")

        return "\n".join(tyreSummary) if tyreSummary else "- No tyre data"

    def _generateFallbackIntervalCommentary(self, eventSummary: str, top3: List) -> str:
        """Generate fallback commentary if Ollama fails."""
        leader = top3[0][0] if top3 else "Unknown"

        if "Pit stops" in eventSummary:
            return f"We've seen pit stop action in the last minute. {leader} leads as the strategy battle heats up."
        if "Overtakes" in eventSummary:
            return f"Overtakes have shaken up the order in the last minute. {leader} leads, but the pressure is building."
        return f"Steady racing over the last minute. {leader} manages the pace while teams monitor tyre wear and strategy."
