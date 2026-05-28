"""
Commentary Modes - Fan Mode and Engineer Mode.
Uses local Ollama generation with the same IntelligenceEngine insights.
"""
from typing import Dict, Optional

from ai.ollamaClient import OllamaClient, clean_commentary


class CommentaryModes:
    """
    Generates commentary in two modes:
    - Fan Mode: simple broadcast-style commentary
    - Engineer Mode: technical, data-driven commentary
    """

    def __init__(self, apiKey: str = None):
        self.client = OllamaClient()
        self.modelName = self.client.modelName
        self.currentMode = "fan"

    def setMode(self, mode: str):
        """Set commentary mode: 'fan' or 'engineer'."""
        if mode not in ["fan", "engineer"]:
            raise ValueError("Mode must be 'fan' or 'engineer'")
        self.currentMode = mode
        print(f"Commentary mode set to: {mode.upper()}")

    def generateCommentary(self, insight: Dict) -> Optional[str]:
        """Generate commentary based on the current mode and insight data."""
        if not insight:
            return None

        if self.currentMode == "fan":
            return self._generateFanCommentary(insight)
        return self._generateEngineerCommentary(insight)

    def _generateFanCommentary(self, insight: Dict) -> Optional[str]:
        event = self._selectMostExcitingEvent(insight.get("events", []))
        driverStates = insight.get("driver_states", {})
        raceState = insight.get("race_state", {})
        leader = self._leaderFromStates(driverStates)

        if event:
            metadata = event.get("metadata", {})
            driver = event.get('driver', leader)
            driverPos = driverStates.get(driver, {}).get('position', '?')
            eventText = f"""Event: {event.get('event', 'Race update')}
Driver: {driver} (P{driverPos})
Speed: {metadata.get('speed', 0):.0f} km/h
Weather: {event.get('weather', raceState.get('weather', 'DRY'))}"""
        else:
            eventText = f"""Event: Race rhythm update
Leader: {leader}
Weather: {raceState.get('weather', raceState.get('rain_state', 'DRY'))}
Track Temp: {raceState.get('track_temp', 0):.1f}C"""

        prompt = f"""Write exciting F1 broadcast commentary for fans. Use 1 to 3 complete English sentences.

RULES:
- Write full sentences, NOT a driver code or abbreviation.
- Do NOT return JSON, quotes, markdown, or bullet points.
- Do NOT start with a driver abbreviation alone.

{eventText}

Example output: "Verstappen storms past Hamilton on the straight! The crowd is on their feet as the gap closes to under a second."

Write the commentary now:"""

        return self._callOllama(prompt, maxTokens=100)

    def _generateEngineerCommentary(self, insight: Dict) -> Optional[str]:
        event = self._selectMostExcitingEvent(insight.get("events", []))
        driverStates = insight.get("driver_states", {})
        raceState = insight.get("race_state", {})
        leader = self._leaderFromStates(driverStates)
        driver = event.get("driver") if event else leader
        driverState = driverStates.get(driver, {})
        metadata = event.get("metadata", {}) if event else {}

        prompt = f"""Write technical F1 race-engineer commentary. Use 1 to 3 complete English sentences with data.

RULES:
- Write full sentences, NOT a driver code or abbreviation.
- Do NOT return JSON, quotes, markdown, or bullet points.
- Do NOT start with a driver abbreviation alone.
- Include specific numbers (speed, gap, tyre age) in your sentences.

Event: {event.get('event', 'Race rhythm update') if event else 'Race rhythm update'}
Driver: {driver} (P{driverState.get('position', '?')})
Speed: {metadata.get('speed', driverState.get('speed', 0)):.0f} km/h
Gap Change: {(event.get('gap_change', 0) if event else 0):.3f}s
Tyre: {driverState.get('tyre_compound', 'Unknown')} compound, {driverState.get('tyre_age', 0)} laps old
Tyre Health: {event.get('tyre_health', driverState.get('tyre_health', 'N/A')) if event else driverState.get('tyre_health', 'N/A')}%
Throttle: {driverState.get('throttle', 0):.0f}%
Track Temp: {raceState.get('track_temp', 0):.1f}C

Example output: "Verstappen's medium compound tyres are 18 laps old with health at 62%. Gap to Norris has closed by 0.3 seconds over the last sector, suggesting a potential undercut window."

Write the engineering commentary now:"""

        return self._callOllama(prompt, maxTokens=140)

    def _selectMostExcitingEvent(self, events: list) -> Optional[Dict]:
        """Select the most important event from the window."""
        if not events:
            return None

        priority = {
            "Overtake": 10,
            "Pit Stop": 9,
            "DRS Range": 8,
            "DRS Activation": 7,
            "Tyre Degradation": 6,
            "High Speed": 5,
        }

        sortedEvents = sorted(
            events,
            key=lambda event: priority.get(event.get("event"), 0),
            reverse=True,
        )
        return sortedEvents[0] if sortedEvents else None

    def _leaderFromStates(self, driverStates: Dict) -> str:
        if not driverStates:
            return "the leader"

        leader = min(
            driverStates.items(),
            key=lambda item: item[1].get("position", 999) if isinstance(item[1], dict) else 999,
            default=("the leader", {}),
        )
        return leader[0]

    def _callOllama(self, prompt: str, maxTokens: int = 150) -> Optional[str]:
        """Call local Ollama with retry. Returns cleaned text or None."""
        for attempt in range(2):
            try:
                temp = 0.6 if attempt == 0 else 0.8
                text = self.client.generate(prompt, temperature=temp, maxTokens=maxTokens)
                result = clean_commentary(text, max_lines=3)
                if result:
                    return result
                if attempt == 0:
                    print(f"Commentary attempt {attempt+1} rejected, retrying...")
            except Exception as e:
                print(f"Ollama call error (attempt {attempt+1}): {e}")
        return None

    def generateFallbackCommentary(self, insight: Dict) -> str:
        """Generate fallback commentary if Ollama fails or returns a fragment."""
        events = insight.get("events", []) if insight else []
        if not events:
            if self.currentMode == "engineer":
                return "The field is settling into rhythm while teams monitor tyre wear, pace delta, and track evolution."
            return "The race settles into a tense rhythm as the leaders keep the pressure on."

        event = self._selectMostExcitingEvent(events)
        driver = event.get("driver", "The driver")
        eventType = event.get("event", "Race update")
        metadata = event.get("metadata", {})

        if self.currentMode == "fan":
            templates = {
                "Overtake": f"{driver} makes the move!",
                "Pit Stop": f"{driver} dives into the pits!",
                "DRS Activation": f"{driver} opens DRS and starts the chase!",
                "DRS Range": f"{driver} is closing in and the pressure is rising!",
                "High Speed": f"{driver} is flying down the straight!",
                "Tyre Degradation": f"{driver}'s tyres are starting to fade!",
            }
        else:
            templates = {
                "Overtake": f"{driver} gained position with stronger traction and exit speed.",
                "Pit Stop": f"{driver} is pitting for fresh {metadata.get('new_tyre', 'tyres')}.",
                "DRS Activation": f"{driver} has DRS active, reducing drag for the next attack.",
                "DRS Range": f"{driver} is inside the 1.0s DRS detection window.",
                "High Speed": f"{driver} reached {metadata.get('speed', 0):.0f} km/h on the straight.",
                "Tyre Degradation": f"{driver} tyre health is at {event.get('tyre_health', 'unknown')}%.",
            }

        return templates.get(eventType, f"{driver} is the focus after a {eventType.lower()} update.")
