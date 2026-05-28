"""
Chronos F1 - Web-based F1 Race Replay Application
Complete implementation with all features: Weather, DRS, Safety Car, Race Control, etc.
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import os
from manager.dataManager import DataManager
from replay.replayEngine import ReplayEngine
from ai.aiCommentary import CommentaryManager
from ai.graniteClient import GraniteClient
from ai.intelligenceEngine import IntelligenceEngine
from ai.commentaryModes import CommentaryModes
from ai.raceDebrief import RaceDebriefGenerator
from replay.ghostEngine import GhostEngine, createGhostFromFastestLap
from documents.documentProcessor import DocumentProcessor
from workflows.langflowIntegration import F1WorkflowOrchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chronos-f1-enhanced-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60, ping_interval=25)

# Global instances
data_manager = DataManager()
replay_engine = None
replay_thread = None
replay_lock = threading.Lock()

# AI Commentary (optional)
commentary_manager = None
granite_client = None
ai_enabled = False

# New AI features
intelligence_engine = None
commentary_modes = None
race_debrief_generator = None
ghost_engine = None
ghost_enabled = False  # Track if ghost comparison is enabled
commentary_mode = "fan"  # Default: fan mode

# Docling integration
document_processor = None
regulations_loaded = False

# Langflow integration
workflow_orchestrator = None
workflows_enabled = False

try:
    # Initialize local Ollama client
    granite_client = GraniteClient()
    if granite_client.isAvailable():
        commentary_manager = CommentaryManager()
        ai_enabled = True
        print('✅ AI Commentary enabled (Ollama)')
        
        # Initialize new AI features (optional)
        try:
            intelligence_engine = IntelligenceEngine()
            commentary_modes = CommentaryModes()
            race_debrief_generator = RaceDebriefGenerator()
            print('✅ Intelligence Engine initialized')
            print('✅ Commentary Modes initialized (Fan/Engineer)')
            print('✅ Race Debrief Generator initialized')
        except Exception as e:
            print(f'⚠️ Advanced AI features not available: {e}')
    else:
        # Ollama not available, but still initialize commentary manager for regulations
        print('⚠️ AI Commentary disabled (Ollama not available)')
        print('📚 Initializing CommentaryManager for regulations only...')
        try:
            commentary_manager = CommentaryManager()
            print('✅ CommentaryManager initialized (regulations only)')
        except Exception as e:
            print(f'❌ Could not initialize CommentaryManager: {e}')
except Exception as e:
    print(f'⚠️ AI Features initialization error: {e}')
    # Still try to initialize commentary manager for regulations
    try:
        commentary_manager = CommentaryManager()
        print('✅ CommentaryManager initialized (regulations only)')
    except Exception as e2:
        print(f'❌ Could not initialize CommentaryManager: {e2}')

# Initialize Docling for regulations (INDEPENDENT of Ollama/AI)
if commentary_manager:
    try:
        document_processor = DocumentProcessor()
        
        # Load F1 regulations from markdown file
        regulationsPath = 'documents/f1_regulations_sample.md'
        if os.path.exists(regulationsPath):
            print(f'📄 Loading F1 regulations from: {regulationsPath}')
            regulationsDoc = document_processor.processDocument(regulationsPath)
            
            # Extract structured rules
            extractedRules = document_processor.extractRegulationRules(regulationsDoc)
            
            # Build regulations knowledge base
            basicRegulations = {
                'drs_rules': 'DRS can only be used when within 1 second of car ahead in designated zones',
                'pit_rules': 'Pit lane speed limit is 80 km/h, minimum 2 tyre compounds must be used',
                'tyre_rules': 'Each driver must use at least two different compounds during dry race',
                'safety_car_rules': 'No overtaking allowed under safety car, maintain position',
                'sections': regulationsDoc.get('sections', [])
            }
            
            # Add extracted rules
            for ruleType, rulesList in extractedRules.items():
                if rulesList:
                    # Use first rule as summary
                    basicRegulations[ruleType] = rulesList[0].get('content', '')[:200]
            
            commentary_manager.loadRegulations(basicRegulations)
            regulations_loaded = True
            print(f'✅ Docling integrated - {len(regulationsDoc.get("sections", []))} regulation sections loaded')
        else:
            print(f'⚠️ Regulations file not found: {regulationsPath}')
            # Use basic fallback
            basicRegulations = {
                'drs_rules': 'DRS can only be used when within 1 second of car ahead in designated zones',
                'pit_rules': 'Pit lane speed limit is 80 km/h, minimum 2 tyre compounds must be used',
                'tyre_rules': 'Each driver must use at least two different compounds during dry race',
                'safety_car_rules': 'No overtaking allowed under safety car, maintain position',
                'flag_rules': 'Yellow Flag: Reduce speed, no overtaking. Red Flag: Session suspended.',
                'sections': []
            }
            commentary_manager.loadRegulations(basicRegulations)
            regulations_loaded = True
            print('✅ Docling integrated - Basic regulations loaded')
    except Exception as e:
        print(f'⚠️ Docling error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ CommentaryManager not available - regulations cannot be loaded')

# Initialize Langflow orchestrator (only if AI is enabled)
if ai_enabled and commentary_manager:
    try:
        workflow_orchestrator = F1WorkflowOrchestrator()
        commentary_manager.setWorkflowOrchestrator(workflow_orchestrator)
        workflows_enabled = True
        print('✅ Langflow integrated - Workflows enabled')
    except Exception as e:
        print(f'⚠️ Langflow not available: {e}')


@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')


@app.route('/api/seasons')
def get_seasons():
    """Get available F1 seasons"""
    try:
        seasons = data_manager.getAvailableSeasons()
        return jsonify({'success': True, 'seasons': seasons})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/races/<int:year>')
def get_races(year):
    """Get races for a specific season"""
    try:
        races = data_manager.getRacesForSeason(year)
        return jsonify({'success': True, 'races': races})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/load-race', methods=['POST'])
def load_race():
    """Load race data for replay"""
    global replay_engine, ghost_engine, intelligence_engine
    
    try:
        data = request.json
        year = data.get('year')
        round_num = data.get('round')
        session_type = data.get('sessionType', 'R')
        
        if not year or not round_num:
            return jsonify({'success': False, 'error': 'Missing year or round'}), 400
        
        # Start loading in background thread
        def load_in_background():
            global replay_engine, ghost_engine, intelligence_engine
            try:
                with replay_lock:
                    race_data = data_manager.loadRaceData(year, round_num, session_type, socketio)
                    replay_engine = ReplayEngine(race_data, socketio)
                    
                    # Reset intelligence engine per race
                    if intelligence_engine:
                        intelligence_engine = IntelligenceEngine()
                    
                    # Try to create ghost engine (fastest-lap reference)
                    ghost_engine = None
                    try:
                        import fastf1
                        session = fastf1.get_session(year, round_num, session_type)
                        session.load(telemetry=True)
                        ghost_engine = createGhostFromFastestLap(session, race_data['trackData'])
                        if ghost_engine:
                            print(f"✅ Ghost engine created for {ghost_engine.ghostDriver}")
                    except Exception as e:
                        print(f"⚠️ Could not create ghost engine: {e}")
                
                socketio.emit('race_loaded', {
                    'success': True,
                    'raceInfo': {
                        'eventName': race_data['eventName'],
                        'circuitName': race_data['circuitName'],
                        'country': race_data['country'],
                        'date': race_data['date'],
                        'totalLaps': race_data['totalLaps'],
                        'totalFrames': len(race_data['frames']),
                        'drivers': race_data['drivers'],
                        'hasWeather': race_data.get('hasWeather', False),
                        'hasDrsZones': race_data.get('hasDrsZones', False),
                        'trackData': race_data['trackData'],
                        'hasGhost': ghost_engine is not None
                    }
                })
            except Exception as e:
                socketio.emit('race_loaded', {
                    'success': False,
                    'error': str(e)
                })
        
        loading_thread = threading.Thread(target=load_in_background, daemon=True)
        loading_thread.start()
        
        return jsonify({'success': True, 'message': 'Loading started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connection_status', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')


@socketio.on('play')
def handle_play():
    """Start replay playback"""
    global replay_thread
    
    with replay_lock:
        if replay_engine and not replay_engine.isPlaying():
            replay_engine.play()
            
            # Start broadcast thread if not running
            if replay_thread is None or not replay_thread.is_alive():
                replay_thread = threading.Thread(target=broadcast_telemetry, daemon=True)
                replay_thread.start()
            
            emit('playback_status', {'status': 'playing'}, broadcast=True)


@socketio.on('pause')
def handle_pause():
    """Pause replay playback"""
    with replay_lock:
        if replay_engine:
            replay_engine.pause()
            emit('playback_status', {'status': 'paused'}, broadcast=True)


@socketio.on('seek')
def handle_seek(data):
    """Seek to specific frame"""
    frame_index = data.get('frameIndex', 0)
    
    with replay_lock:
        if replay_engine:
            replay_engine.seekToFrame(frame_index)
            emit('playback_status', {
                'status': 'seeked',
                'frameIndex': frame_index
            }, broadcast=True)


@socketio.on('set_speed')
def handle_set_speed(data):
    """Set playback speed"""
    speed = data.get('speed', 1.0)
    
    with replay_lock:
        if replay_engine:
            replay_engine.setPlaybackSpeed(speed)
            emit('playback_status', {
                'status': 'speed_changed',
                'speed': speed
            }, broadcast=True)


@socketio.on('restart')
def handle_restart():
    """Restart replay from beginning"""
    with replay_lock:
        if replay_engine:
            replay_engine.restart()
            emit('playback_status', {'status': 'restarted'}, broadcast=True)


@socketio.on('get_ai_status')
def handle_get_ai_status():
    """Get AI commentary status"""
    emit('ai_status', {
        'enabled': ai_enabled,
        'models': granite_client.listModels() if granite_client else [],
        'docling': regulations_loaded,
        'langflow': workflows_enabled,
        'intelligence_engine': intelligence_engine is not None,
        'commentary_modes': commentary_modes is not None,
        'race_debrief': race_debrief_generator is not None,
        'ghost_engine': ghost_engine is not None,
        'ghost_enabled': ghost_enabled,
        'current_mode': commentary_mode,
        'regulations_count': len(commentary_manager.aiCommentary.regulationsKnowledge.get('sections', [])) if commentary_manager and regulations_loaded else 0
    })
    
    # Also log to console for debugging
    print(f"📊 AI Status Check: ghost_engine={ghost_engine is not None}, ghost_enabled={ghost_enabled}, regulations_loaded={regulations_loaded}")


@socketio.on('set_commentary_mode')
def handle_set_commentary_mode(data):
    """Set commentary mode: fan or engineer"""
    global commentary_mode
    
    mode = data.get('mode', 'fan')
    if mode not in ['fan', 'engineer']:
        emit('error', {'message': 'Invalid mode. Use \"fan\" or \"engineer\"'})
        return
    
    commentary_mode = mode
    if commentary_modes:
        commentary_modes.setMode(mode)
    
    emit('commentary_mode_changed', {'mode': mode}, broadcast=True)
    print(f"✅ Commentary mode changed to: {mode.upper()}")


@socketio.on('request_race_debrief')
def handle_request_race_debrief():
    """Generate and send race debrief"""
    global intelligence_engine, race_debrief_generator, replay_engine
    
    if not intelligence_engine or not race_debrief_generator:
        emit('error', {'message': 'Race debrief not available'})
        return
    
    if not replay_engine:
        emit('error', {'message': 'No race loaded'})
        return
    
    try:
        print("🏁 Generating race debrief...")
        raceData = replay_engine.raceData
        debrief = race_debrief_generator.generateDebrief(intelligence_engine, raceData)
        emit('race_debrief', debrief)
        print("✅ Race debrief sent to client")
    except Exception as e:
        print(f"❌ Error generating race debrief: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Error generating debrief: {str(e)}'})


@socketio.on('toggle_ghost')
def handle_toggle_ghost(data):
    """Toggle ghost comparison on/off"""
    global ghost_engine, ghost_enabled
    
    enabled = data.get('enabled', False)
    ghost_enabled = enabled
    
    print(f"🔄 Ghost toggle request: enabled={enabled}, ghost_engine exists={ghost_engine is not None}")
    
    if enabled and ghost_engine:
        print(f"✅ Ghost comparison enabled - Reference: {ghost_engine.ghostDriver}")
        emit('ghost_status', {'enabled': True, 'driver': ghost_engine.ghostDriver})
    elif not enabled:
        print("⏸️ Ghost comparison disabled")
        emit('ghost_status', {'enabled': False})
    else:
        print("⚠️ Ghost engine not available")
        emit('error', {'message': 'Ghost engine not available'})


@socketio.on('get_analysis_results')
def handle_get_analysis_results():
    """Get Langflow workflow analysis results"""
    if commentary_manager and workflows_enabled:
        results = commentary_manager.getAnalysisResults()
        print(f"📊 Sending {len(results)} analysis results to client")
        emit('analysis_results', {'results': results})
    else:
        print(f"⚠️ Analysis results requested but workflows not enabled")
        emit('analysis_results', {'results': []})


@socketio.on('get_driver_comparison')
def handle_get_driver_comparison(data):
    """Get telemetry comparison data for selected drivers"""
    if not replay_engine:
        emit('error', {'message': 'No race loaded'})
        return
    
    try:
        driver_codes = data.get('drivers', [])
        if not driver_codes or len(driver_codes) < 2:
            emit('error', {'message': 'Select at least 2 drivers for comparison'})
            return
        
        # Get current telemetry
        current_telemetry = replay_engine.getCurrentTelemetry()
        if not current_telemetry:
            return
        
        frame = current_telemetry.get('frame', {})
        drivers_data = frame.get('drivers', {})
        
        # Build comparison data
        comparison = {
            'drivers': [],
            'timestamp': current_telemetry.get('t', 0),
            'frameIndex': current_telemetry.get('frameIndex', 0)
        }
        
        for code in driver_codes:
            if code not in drivers_data:
                continue
            
            driver_data = drivers_data[code]
            
            # Get tyre health if available
            tyre_health = None
            if replay_engine.raceData.get('tyreModel'):
                health = replay_engine.raceData['tyreModel'].getHealthForFrame(code, frame)
                if health:
                    tyre_health = health
            
            comparison['drivers'].append({
                'code': code,
                'position': driver_data.get('position', 0),
                'speed': driver_data.get('speed', 0),
                'throttle': driver_data.get('throttle', 0),
                'brake': driver_data.get('brake', 0),
                'gear': driver_data.get('gear', 0),
                'drs': driver_data.get('drs', 0),
                'lap': driver_data.get('lap', 0),
                'tyreLife': driver_data.get('tyreLife', 0),
                'tyre': driver_data.get('tyre', 0),
                'tyreHealth': tyre_health,
                'color': current_telemetry.get('driverColors', {}).get(code, '#FFFFFF')
            })
        
        emit('driver_comparison_data', comparison)
        
    except Exception as e:
        print(f"❌ Error getting driver comparison: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Error getting comparison: {str(e)}'})


@app.route('/api/process-document', methods=['POST'])
def process_document():
    """Process F1 document with Docling"""
    if not document_processor:
        return jsonify({'success': False, 'error': 'Docling not available'}), 400
    
    try:
        data = request.json
        filePath = data.get('filePath')
        
        if not filePath:
            return jsonify({'success': False, 'error': 'No file path provided'}), 400
        
        print(f"📄 Processing document via API: {filePath}")
        docData = document_processor.processDocument(filePath)
        
        return jsonify({
            'success': True,
            'document': {
                'title': docData.get('metadata', {}).get('title', 'Unknown'),
                'sections': len(docData.get('sections', [])),
                'text': docData.get('text', '')[:500] + '...'
            }
        })
    except Exception as e:
        print(f"❌ Document processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/regulations/status')
def get_regulations_status():
    """Get current regulations status and content"""
    if not commentary_manager or not regulations_loaded:
        return jsonify({
            'success': False,
            'loaded': False,
            'message': 'Regulations not loaded'
        })
    
    regulations = commentary_manager.aiCommentary.regulationsKnowledge
    
    return jsonify({
        'success': True,
        'loaded': True,
        'sections_count': len(regulations.get('sections', [])),
        'rule_types': [k for k in regulations.keys() if k.endswith('_rules')],
        'sample_rules': {
            'drs': regulations.get('drs_rules', '')[:150],
            'pit': regulations.get('pit_rules', '')[:150],
            'safety_car': regulations.get('safety_car_rules', '')[:150]
        }
    })


@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """Execute Langflow workflow"""
    if not workflow_orchestrator:
        return jsonify({'success': False, 'error': 'Langflow not available'}), 400
    
    try:
        data = request.json
        workflowName = data.get('workflow', 'commentary')
        workflowData = data.get('data', {})
        
        result = workflow_orchestrator.executeWorkflow(workflowName, workflowData)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def broadcast_telemetry():
    """Background thread to broadcast telemetry data"""
    previous_frame = None
    analysis_counter = 0  # Counter for periodic analysis
    replay_completed = False
    
    # Commentary batching: collect events for 60s, then emit 1 commentary message.
    commentary_window_start = None
    buffered_events = []
    latest_insight_for_window = None
    
    def _extractRegulationContext(events, telemetry_data):
        """Extract relevant regulation context based on events"""
        if not commentary_manager or not regulations_loaded:
            return None
        
        regulations = commentary_manager.aiCommentary.regulationsKnowledge
        if not regulations:
            return None
        
        context = {
            'timestamp': telemetry_data.get('t', 0),
            'regulations': []
        }
        
        for event in events:
            event_type = event.get('type', '') if isinstance(event, dict) else event
            event_lower = event_type.lower()
            
            if 'drs' in event_lower and 'drs_rules' in regulations:
                context['regulations'].append({
                    'type': 'DRS',
                    'title': 'DRS Activation Rules',
                    'content': regulations['drs_rules'][:200],
                    'active': True
                })
                print(f"📚 Sending DRS regulation context to UI")
            
            elif 'pit' in event_lower and 'pit_rules' in regulations:
                context['regulations'].append({
                    'type': 'PIT',
                    'title': 'Pit Stop Regulations',
                    'content': regulations['pit_rules'][:200],
                    'active': True
                })
                print(f"📚 Sending Pit Stop regulation context to UI")
            
            elif 'safety' in event_lower and 'safety_car_rules' in regulations:
                context['regulations'].append({
                    'type': 'SAFETY_CAR',
                    'title': 'Safety Car Procedure',
                    'content': regulations['safety_car_rules'][:200],
                    'active': True
                })
                print(f"📚 Sending Safety Car regulation context to UI")
            
            elif 'yellow_flag' in event_lower and 'flag_rules' in regulations:
                context['regulations'].append({
                    'type': 'YELLOW_FLAG',
                    'title': 'Yellow Flag Rules',
                    'content': regulations.get('flag_rules', 'Yellow Flag: Reduce speed, no overtaking')[:200],
                    'active': True
                })
                print(f"📚 Sending Yellow Flag regulation context to UI")
        
        # Check track status for additional context
        track_status = telemetry_data.get('trackStatus', '1')
        if track_status in ['4', '6', '7'] and 'safety_car_rules' in regulations:
            if not any(r['type'] == 'SAFETY_CAR' for r in context['regulations']):
                context['regulations'].append({
                    'type': 'SAFETY_CAR',
                    'title': 'Safety Car Deployed',
                    'content': regulations['safety_car_rules'][:200],
                    'active': True
                })
                print(f"📚 Sending Safety Car regulation (track status) to UI")
        
        elif track_status == '2' and 'flag_rules' in regulations:
            if not any(r['type'] == 'YELLOW_FLAG' for r in context['regulations']):
                context['regulations'].append({
                    'type': 'YELLOW_FLAG',
                    'title': 'Yellow Flag - Caution',
                    'content': regulations.get('flag_rules', 'Yellow Flag: Reduce speed, no overtaking')[:200],
                    'active': True
                })
                print(f"📚 Sending Yellow Flag regulation (track status) to UI")
        
        return context if context['regulations'] else None
    
    while True:
        try:
            with replay_lock:
                if replay_engine and replay_engine.isPlaying():
                    telemetry_data = replay_engine.getCurrentTelemetry()
                    
                    # Add tyre health data to telemetry
                    if telemetry_data and replay_engine.raceData.get('tyreModel'):
                        tyreModel = replay_engine.raceData['tyreModel']
                        frame = telemetry_data.get('frame', {})
                        drivers = frame.get('drivers', {})
                        
                        tyreHealthData = {}
                        for driverCode in drivers.keys():
                            health = tyreModel.getHealthForFrame(driverCode, frame)
                            if health:
                                tyreHealthData[driverCode] = health
                        
                        telemetry_data['tyreHealthData'] = tyreHealthData
                    
                    telemetry_data = telemetry_data
                    if telemetry_data:
                        socketio.emit('telemetry_update', telemetry_data)
                        
                        # Broadcast regulation context (independent of AI)
                        if regulations_loaded and commentary_manager:
                            try:
                                # Detect events for regulation context
                                if previous_frame:
                                    events = commentary_manager.aiCommentary.detectEvents(telemetry_data, previous_frame)
                                    if events:
                                        regulation_context = _extractRegulationContext(events, telemetry_data)
                                        if regulation_context:
                                            socketio.emit('regulation_context', regulation_context)
                            except Exception as e:
                                print(f"❌ Regulation context error: {e}")
                        
                        # Broadcast ghost comparison if enabled (independent of AI features)
                        if ghost_enabled and ghost_engine:
                            try:
                                frame = telemetry_data.get('frame', telemetry_data)
                                drivers = frame.get('drivers', {})
                                
                                if not drivers:
                                    if telemetry_data.get('frameIndex', 0) % 100 == 0:
                                        print("⚠️ No drivers data in frame")
                                else:
                                    leader = min(drivers.items(), key=lambda x: x[1].get('position', 999), default=(None, {}))
                                    if leader[0]:
                                        leaderData = leader[1]
                                        currentDist = leaderData.get('dist', 0)
                                        currentTime = telemetry_data.get('t', 0)
                                        currentSpeed = leaderData.get('speed', 0)
                                        
                                        # Debug log every 100 frames
                                        if telemetry_data.get('frameIndex', 0) % 100 == 0:
                                            print(f"👻 Ghost calc: dist={currentDist:.1f}, time={currentTime:.1f}, speed={currentSpeed:.1f}")
                                        
                                        ghostPos = ghost_engine.getGhostPosition(currentTime, currentDist)
                                        delta = ghost_engine.calculateDelta(currentTime, currentDist, currentSpeed)
                                        
                                        if ghostPos and delta:
                                            socketio.emit('ghost_update', {
                                                'ghost_position': ghostPos,
                                                'delta': delta
                                            })
                                        else:
                                            if telemetry_data.get('frameIndex', 0) % 100 == 0:
                                                print(f"⚠️ Ghost calc returned None: pos={ghostPos is not None}, delta={delta is not None}")
                            except Exception as e:
                                print(f"❌ Ghost comparison error: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Use Intelligence Engine to analyze frame (for AI commentary only)
                        if intelligence_engine:
                            try:
                                insight = intelligence_engine.analyzeFrame(telemetry_data, previous_frame)
                                latest_insight_for_window = insight
                                
                                now = time.time()
                                if commentary_window_start is None:
                                    commentary_window_start = now
                                
                                if insight.get('events'):
                                    buffered_events.extend(insight.get('events', []))
                                
                                # Generate ONE commentary message per 60 seconds (wall-clock time)
                                if commentary_modes and commentary_window_start is not None:
                                    if (now - commentary_window_start) >= 60:
                                        batchInsight = dict(latest_insight_for_window or insight or {})
                                        batchInsight['events'] = buffered_events
                                        
                                        commentary = commentary_modes.generateCommentary(batchInsight)
                                        if not commentary:
                                            commentary = commentary_modes.generateFallbackCommentary(batchInsight)
                                        
                                        if commentary:
                                            print(f"✅ {commentary_mode.upper()} Commentary: {commentary}")
                                            socketio.emit('ai_commentary', {
                                                'text': commentary,
                                                'time': telemetry_data.get('t', 0),
                                                'mode': commentary_mode
                                            })
                                        
                                        commentary_window_start = now
                                        buffered_events = []
                            
                            except Exception as e:
                                print(f"❌ Intelligence Engine error: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Fallback to old commentary system
                        elif ai_enabled and commentary_manager:
                            try:
                                commentary = commentary_manager.generateForFrame(
                                    telemetry_data,
                                    previous_frame
                                )
                                if commentary:
                                    print(f"✅ Commentary generated: {commentary}")
                                    socketio.emit('ai_commentary', {
                                        'text': commentary,
                                        'time': telemetry_data.get('t', 0)
                                    })
                            except Exception as e:
                                print(f"❌ Commentary generation error: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Run workflow analysis every 15 seconds (375 frames at 25 FPS)
                        if workflows_enabled and workflow_orchestrator and commentary_manager:
                            analysis_counter += 1
                            if analysis_counter >= 375:  # 15 seconds
                                analysis_counter = 0
                                try:
                                    print(f"🔄 Running periodic workflow analysis...")
                                    analysisResult = workflow_orchestrator.executeWorkflow('analysis', {
                                        'frame': telemetry_data,
                                        'time': telemetry_data.get('t', 0)
                                    })
                                    if analysisResult:
                                        commentary_manager.analysisResults.append(analysisResult)
                                        print(f"✅ Analysis complete, broadcasting to clients")
                                        socketio.emit('analysis_results', {
                                            'results': commentary_manager.getAnalysisResults()
                                        })
                                except Exception as e:
                                    print(f"❌ Workflow analysis error: {e}")
                        
                        # Check if replay completed
                        if replay_engine.currentFrame >= replay_engine.totalFrames - 1:
                            if not replay_completed:
                                replay_completed = True
                                print("🏁 Replay completed - triggering race debrief")
                                socketio.emit('replay_completed', {'completed': True})
                        else:
                            replay_completed = False
                        
                        previous_frame = telemetry_data
            
            time.sleep(0.04)  # 25 FPS
        except Exception as e:
            print(f'Broadcast error: {e}')
            time.sleep(0.1)


if __name__ == '__main__':
    print('=' * 60)
    print('CHRONOS F1 - Web-based Race Replay')
    print('=' * 60)
    print('Starting server on http://localhost:5000')
    print('Press Ctrl+C to stop')
    print('=' * 60)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
