"""
AI Race Debrief - Comprehensive race analysis at replay completion
"""
from typing import Dict, List, Optional
from dotenv import load_dotenv
from ai.ollamaClient import OllamaClient, clean_commentary

load_dotenv()


class RaceDebriefGenerator:
    """
    Generates comprehensive race debrief at replay completion.
    Analyzes entire race using accumulated IntelligenceEngine insights.
    """
    
    def __init__(self, apiKey: str = None):
        self.client = OllamaClient()
        self.modelName = self.client.modelName
    
    def generateDebrief(self, intelligenceEngine, raceData: Dict) -> Dict:
        """
        Generate comprehensive race debrief.
        
        Args:
            intelligenceEngine: IntelligenceEngine instance with full race history
            raceData: Race metadata (event name, circuit, etc.)
        
        Returns:
            {
                "race_info": {...},
                "best_strategy": str,
                "critical_events": [str],
                "most_aggressive_driver": str,
                "tyre_efficiency": {...},
                "safety_car_impact": str,
                "predicted_vs_actual": str,
                "ai_recommendations": [str],
                "race_summary": str
            }
        """
        print("🏁 Generating AI Race Debrief...")
        
        # Gather insights from intelligence engine
        allInsights = intelligenceEngine.eventHistory
        
        if not allInsights:
            return self._emptyDebrief(raceData)
        
        # Analyze race
        analysis = self._analyzeRace(allInsights)
        
        # Generate AI commentary for each section
        debrief = {
            "race_info": {
                "event": raceData.get('eventName', 'Unknown'),
                "circuit": raceData.get('circuitName', 'Unknown'),
                "date": raceData.get('date', 'Unknown'),
                "total_laps": raceData.get('totalLaps', 0)
            },
            "best_strategy": self._analyzeBestStrategy(analysis),
            "critical_events": self._identifyCriticalEvents(analysis),
            "most_aggressive_driver": self._findMostAggressiveDriver(analysis),
            "tyre_efficiency": self._analyzeTyreEfficiency(analysis),
            "safety_car_impact": self._analyzeSafetyCarImpact(analysis),
            "predicted_vs_actual": self._comparePredictions(analysis),
            "ai_recommendations": self._generateRecommendations(analysis),
            "race_summary": self._generateRaceSummary(analysis, raceData)
        }
        
        print("✅ Race Debrief generated successfully")
        return debrief
    
    def _analyzeRace(self, insights: List[Dict]) -> Dict:
        """Analyze all race insights"""
        analysis = {
            "total_events": 0,
            "overtakes": [],
            "pit_stops": [],
            "drs_activations": [],
            "safety_car_periods": [],
            "tyre_data": {},
            "driver_performance": {},
            "lap_count": 0
        }
        
        for insight in insights:
            analysis['lap_count'] = max(analysis['lap_count'], insight.get('lap', 0))
            
            # Collect events
            for event in insight.get('events', []):
                analysis['total_events'] += 1
                
                driver = event['driver']
                eventType = event['event']
                
                if eventType == 'Overtake':
                    analysis['overtakes'].append(event)
                elif eventType == 'Pit Stop':
                    analysis['pit_stops'].append(event)
                elif eventType == 'DRS Activation':
                    analysis['drs_activations'].append(event)
                
                # Track driver performance
                if driver not in analysis['driver_performance']:
                    analysis['driver_performance'][driver] = {
                        'overtakes': 0,
                        'pit_stops': 0,
                        'drs_uses': 0,
                        'avg_tyre_health': []
                    }
                
                if eventType == 'Overtake':
                    analysis['driver_performance'][driver]['overtakes'] += 1
                elif eventType == 'Pit Stop':
                    analysis['driver_performance'][driver]['pit_stops'] += 1
                elif eventType == 'DRS Activation':
                    analysis['driver_performance'][driver]['drs_uses'] += 1
                
                # Track tyre health
                if event.get('tyre_health'):
                    analysis['driver_performance'][driver]['avg_tyre_health'].append(
                        event['tyre_health']
                    )
            
            # Track safety car
            raceState = insight.get('race_state', {})
            if raceState.get('safety_car'):
                analysis['safety_car_periods'].append(insight['timestamp'])
        
        # Calculate averages
        for driver, perf in analysis['driver_performance'].items():
            if perf['avg_tyre_health']:
                perf['avg_tyre_health'] = sum(perf['avg_tyre_health']) / len(perf['avg_tyre_health'])
            else:
                perf['avg_tyre_health'] = 100
        
        return analysis
    
    def _analyzeBestStrategy(self, analysis: Dict) -> str:
        """Determine best race strategy"""
        # Find driver with best tyre management and fewest stops
        bestDriver = None
        bestScore = 0
        
        for driver, perf in analysis['driver_performance'].items():
            # Score: high tyre health, fewer stops
            score = perf['avg_tyre_health'] - (perf['pit_stops'] * 10)
            if score > bestScore:
                bestScore = score
                bestDriver = driver
        
        if bestDriver:
            stops = analysis['driver_performance'][bestDriver]['pit_stops']
            tyreHealth = analysis['driver_performance'][bestDriver]['avg_tyre_health']
            return f"{bestDriver} executed optimal strategy with {stops} stop(s) and {tyreHealth:.0f}% average tyre health"
        
        return "One-stop strategy proved most effective"
    
    def _identifyCriticalEvents(self, analysis: Dict) -> List[str]:
        """Identify critical race moments"""
        events = []
        
        # Major overtakes
        if analysis['overtakes']:
            topOvertakes = sorted(
                analysis['overtakes'],
                key=lambda e: e['metadata'].get('from_position', 99)
            )[:3]
            for ot in topOvertakes:
                events.append(
                    f"Lap {ot.get('lap', 0)}: {ot['driver']} overtakes for P{ot['metadata'].get('to_position', '?')}"
                )
        
        # Safety car periods
        if analysis['safety_car_periods']:
            events.append(f"Safety car deployed ({len(analysis['safety_car_periods'])} periods)")
        
        # Strategic pit stops
        if analysis['pit_stops']:
            events.append(f"{len(analysis['pit_stops'])} pit stops executed")
        
        return events[:5]  # Top 5 events
    
    def _findMostAggressiveDriver(self, analysis: Dict) -> str:
        """Find most aggressive driver"""
        mostOvertakes = 0
        aggressiveDriver = None
        
        for driver, perf in analysis['driver_performance'].items():
            overtakes = perf['overtakes']
            if overtakes > mostOvertakes:
                mostOvertakes = overtakes
                aggressiveDriver = driver
        
        if aggressiveDriver:
            return f"{aggressiveDriver} with {mostOvertakes} overtake(s)"
        
        return "No significant overtaking activity"
    
    def _analyzeTyreEfficiency(self, analysis: Dict) -> Dict:
        """Analyze tyre efficiency across drivers"""
        efficiency = {}
        
        for driver, perf in analysis['driver_performance'].items():
            efficiency[driver] = {
                "avg_health": round(perf['avg_tyre_health'], 1),
                "pit_stops": perf['pit_stops']
            }
        
        # Find best tyre manager
        bestManager = max(
            efficiency.items(),
            key=lambda x: x[1]['avg_health'],
            default=(None, {})
        )
        
        if bestManager[0]:
            efficiency['best_manager'] = bestManager[0]
        
        return efficiency
    
    def _analyzeSafetyCarImpact(self, analysis: Dict) -> str:
        """Analyze safety car impact on race"""
        scPeriods = len(analysis['safety_car_periods'])
        
        if scPeriods == 0:
            return "No safety car deployment - clean race"
        elif scPeriods < 5:
            return f"Safety car deployed briefly ({scPeriods} periods), minimal impact on strategy"
        else:
            return f"Extended safety car periods ({scPeriods}) significantly affected race strategy"
    
    def _comparePredictions(self, analysis: Dict) -> str:
        """Compare predicted vs actual outcomes"""
        # Simplified prediction comparison
        totalOvertakes = len(analysis['overtakes'])
        
        if totalOvertakes > 10:
            return "High overtaking activity exceeded expectations"
        elif totalOvertakes > 5:
            return "Moderate overtaking as predicted"
        else:
            return "Lower overtaking activity than expected"
    
    def _generateRecommendations(self, analysis: Dict) -> List[str]:
        """Generate AI recommendations"""
        recommendations = []
        
        # Tyre strategy recommendations
        avgPitStops = sum(p['pit_stops'] for p in analysis['driver_performance'].values()) / max(len(analysis['driver_performance']), 1)
        
        if avgPitStops < 1.5:
            recommendations.append("One-stop strategy viable - consider extending first stint")
        else:
            recommendations.append("Two-stop strategy recommended for optimal pace")
        
        # Overtaking recommendations
        if len(analysis['overtakes']) > 10:
            recommendations.append("High overtaking opportunities - aggressive strategy beneficial")
        else:
            recommendations.append("Limited overtaking - track position critical, prioritize qualifying")
        
        # DRS recommendations
        if len(analysis['drs_activations']) > 20:
            recommendations.append("DRS highly effective - focus on maintaining gap within 1 second")
        
        return recommendations
    
    def _generateRaceSummary(self, analysis: Dict, raceData: Dict) -> str:
        """Generate comprehensive race summary using AI"""
        prompt = f"""Generate a comprehensive F1 race summary for the Chronos AI Race Debrief.

Race: {raceData.get('eventName', 'Unknown')}
Circuit: {raceData.get('circuitName', 'Unknown')}
Total Laps: {analysis['lap_count']}

Statistics:
- Total Events: {analysis['total_events']}
- Overtakes: {len(analysis['overtakes'])}
- Pit Stops: {len(analysis['pit_stops'])}
- DRS Activations: {len(analysis['drs_activations'])}
- Safety Car Periods: {len(analysis['safety_car_periods'])}

Top Performers:
{self._formatTopPerformers(analysis)}

Generate a professional race summary (3-4 sentences) covering:
1. Overall race narrative
2. Key strategic decisions
3. Standout performances
4. Race outcome significance

Style: Professional F1 analysis, insightful and comprehensive."""
        
        summary = self._callOllama(prompt, maxTokens=300)
        
        if not summary:
            # Fallback summary
            return f"The {raceData.get('eventName', 'race')} at {raceData.get('circuitName', 'the circuit')} featured {len(analysis['overtakes'])} overtakes and {len(analysis['pit_stops'])} pit stops across {analysis['lap_count']} laps. Strategic tyre management proved crucial in determining the final outcome."
        
        return summary
    
    def _formatTopPerformers(self, analysis: Dict) -> str:
        """Format top performers for prompt"""
        performers = []
        
        # Sort by overtakes
        sorted_drivers = sorted(
            analysis['driver_performance'].items(),
            key=lambda x: x[1]['overtakes'],
            reverse=True
        )[:3]
        
        for driver, perf in sorted_drivers:
            performers.append(
                f"- {driver}: {perf['overtakes']} overtakes, {perf['pit_stops']} stops, {perf['avg_tyre_health']:.0f}% tyre health"
            )
        
        return '\n'.join(performers) if performers else "- No significant performances"
    
    def _callOllama(self, prompt: str, maxTokens: int = 300) -> Optional[str]:
        """Call local Ollama."""
        try:
            return clean_commentary(
                self.client.generate(prompt, temperature=0.6, maxTokens=maxTokens),
                max_lines=4,
            )
        except Exception as e:
            print(f"Ollama API error: {e}")
            return None
    
    def _emptyDebrief(self, raceData: Dict) -> Dict:
        """Return empty debrief structure"""
        return {
            "race_info": {
                "event": raceData.get('eventName', 'Unknown'),
                "circuit": raceData.get('circuitName', 'Unknown'),
                "date": raceData.get('date', 'Unknown'),
                "total_laps": raceData.get('totalLaps', 0)
            },
            "best_strategy": "Insufficient data",
            "critical_events": [],
            "most_aggressive_driver": "N/A",
            "tyre_efficiency": {},
            "safety_car_impact": "N/A",
            "predicted_vs_actual": "N/A",
            "ai_recommendations": [],
            "race_summary": "Race analysis unavailable"
        }
