// Chronos F1 Enhanced - Complete Implementation with All Features

class ChronosF1Enhanced {
    constructor() {
        this.socket = null;
        this.canvas = null;
        this.ctx = null;
        this.raceData = null;
        this.currentTelemetry = null;
        this.isPlaying = false;
        this.selectedDrivers = [];
        this.analysisInterval = null;  // For Langflow analysis updates
        this.comparisonInterval = null;  // For telemetry comparison updates

        // Ghost comparison overlay
        this.ghostEnabled = false;
        this.ghostPosition = null;
        this.ghostDelta = null;
        
        // Telemetry comparison
        this.showComparison = false;
        this.comparisonHistory = {
            speed: [],
            throttle: [],
            brake: [],
            gear: []
        };
        this.maxHistoryPoints = 100;  // Keep last 100 data points
        
        // Display toggles
        this.showDrs = true;
        this.showWeather = true;
        this.showCharts = false;
        this.gapMode = 'interval'; // 'interval' or 'leader'
        
        // Track rendering
        this.trackScale = 1;
        this.trackOffsetX = 0;
        this.trackOffsetY = 0;
        this.rotateTrack = false;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Chronos F1 Enhanced...');
        this.setupSocketIO();
        this.setupUI();
        this.loadSeasons();
        console.log('✅ Initialization complete');
    }
    
    setupSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('✅ Connected to server');
            this.updateConnectionStatus(true);
            // Request AI capabilities/status so UI can enable/disable sections.
            this.socket.emit('get_ai_status');
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from server');
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('telemetry_update', (data) => {
            console.log('📊 Telemetry update:', data.frameIndex, '/', data.totalFrames);
            this.handleTelemetryUpdate(data);
        });
        
        this.socket.on('ai_commentary', (data) => {
            console.log('🎙️ AI Commentary:', data.text);
            this.displayCommentary(data.text, data.time);
        });
        
        this.socket.on('ai_status', (data) => {
            console.log('🤖 AI Status:', data);
            this.updateAIStatus(data);
        });
        
        this.socket.on('analysis_results', (data) => {
            console.log('📊 Analysis Results:', data);
            this.displayAnalysisResults(data.results);
        });
        
        this.socket.on('driver_comparison_data', (data) => {
            console.log('📊 Driver Comparison Data:', data);
            this.updateTelemetryComparison(data);
        });
        
        this.socket.on('playback_status', (data) => {
            console.log('▶️ Playback status:', data);
            this.handlePlaybackStatus(data);
        });
        
        this.socket.on('loading_progress', (data) => {
            console.log('⏳ Loading progress:', data.percent + '%', '-', data.message);
            this.handleLoadingProgress(data);
        });
        
        this.socket.on('race_loaded', (data) => {
            console.log('🏁 Race loaded event received:', data);
            this.handleRaceLoaded(data);
        });
    }
    
    setupUI() {
        // Season select
        document.getElementById('seasonSelect').addEventListener('change', (e) => {
            this.loadRaces(e.target.value);
        });
        
        // Race select
        document.getElementById('raceSelect').addEventListener('change', (e) => {
            document.getElementById('loadRaceBtn').disabled = !e.target.value;
        });
        
        // Load race
        document.getElementById('loadRaceBtn').addEventListener('click', () => {
            this.loadRace();
        });
        
        // Playback controls
        document.getElementById('playPauseBtn').addEventListener('click', () => {
            this.togglePlayPause();
        });
        
        document.getElementById('restartBtn').addEventListener('click', () => {
            this.restart();
        });
        
        document.getElementById('speedSelect').addEventListener('change', (e) => {
            this.setSpeed(parseFloat(e.target.value));
        });
        
        document.getElementById('progressSlider').addEventListener('input', (e) => {
            this.seek(parseInt(e.target.value, 10));
        });
        
        // Feature toggles
        document.getElementById('toggleDrs').addEventListener('click', () => {
            this.showDrs = !this.showDrs;
            document.getElementById('toggleDrs').classList.toggle('active');
        });
        
        document.getElementById('toggleWeather').addEventListener('click', () => {
            this.showWeather = !this.showWeather;
            document.getElementById('toggleWeather').classList.toggle('active');
            document.getElementById('weatherSection').style.display = 
                this.showWeather ? 'block' : 'none';
        });
        
        // Gap mode toggles
        document.getElementById('gapLeaderBtn').addEventListener('click', () => {
            console.log('🔄 Switching to Leader gap mode');
            this.gapMode = 'leader';
            document.getElementById('gapLeaderBtn').classList.add('active');
            document.getElementById('gapIntervalBtn').classList.remove('active');
            // Refresh leaderboard to show new gap mode
            if (this.currentTelemetry && this.currentTelemetry.frame) {
                console.log('Refreshing leaderboard with leader gaps');
                this.updateLeaderboard(this.currentTelemetry.frame.drivers);
            }
        });
        
        document.getElementById('gapIntervalBtn').addEventListener('click', () => {
            console.log('🔄 Switching to Interval gap mode');
            this.gapMode = 'interval';
            document.getElementById('gapIntervalBtn').classList.add('active');
            document.getElementById('gapLeaderBtn').classList.remove('active');
            // Refresh leaderboard to show new gap mode
            if (this.currentTelemetry && this.currentTelemetry.frame) {
                console.log('Refreshing leaderboard with interval gaps');
                this.updateLeaderboard(this.currentTelemetry.frame.drivers);
            }
        });
        
        // Canvas setup
        this.canvas = document.getElementById('trackCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('contextmenu', (e) => this.handleCanvasClick(e));
        window.addEventListener('resize', () => this.resizeCanvas());

        const rotateBtn = document.getElementById('toggleRotate');
        if (rotateBtn) {
            rotateBtn.addEventListener('click', () => {
                this.rotateTrack = !this.rotateTrack;
                rotateBtn.classList.toggle('active');
                this.drawFrame();
            });
        }
    }

    getTransformedPoint(px, py) {
        if (!this.rotateTrack) return { x: px, y: py };
        return { x: py, y: -px };
    }

    handleCanvasClick(e) {
        if (!this.currentTelemetry || !this.currentTelemetry.frame || !this.currentTelemetry.frame.drivers) return;
        const isRightClick = e.type === 'contextmenu' || e.button === 2;
        if (isRightClick) {
            e.preventDefault();
        }
        const rect = this.canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;

        let best = null;
        let bestDist = Infinity;
        for (const [code, data] of Object.entries(this.currentTelemetry.frame.drivers)) {
            if (data.x === undefined || data.y === undefined) continue;
            const pt = this.getTransformedPoint(data.x, data.y);
            const x = pt.x * this.trackScale + this.trackOffsetX;
            const y = pt.y * this.trackScale + this.trackOffsetY;
            const d = Math.hypot(x - clickX, y - clickY);
            if (d < bestDist) {
                bestDist = d;
                best = code;
            }
        }

        // Select only if click is near a car
        if (best && bestDist <= 16) {
            this.selectDriver(best, isRightClick, this.currentTelemetry.frame.drivers);
        }
    }

    selectDriver(code, isMultiSelect = false, drivers = null) {
        if (!code) return;

        if (isMultiSelect) {
            const idx = this.selectedDrivers.indexOf(code);
            if (idx > -1) {
                this.selectedDrivers.splice(idx, 1);
            } else {
                this.selectedDrivers.push(code);
            }
        } else {
            this.selectedDrivers = [code];
        }

        const driverMap = drivers || (this.currentTelemetry && this.currentTelemetry.frame
            ? this.currentTelemetry.frame.drivers
            : null);
        if (driverMap) {
            this.updateLeaderboard(driverMap);
        }

        this.syncComparisonPanelState();
        this.drawFrame();
    }

    syncComparisonPanelState() {
        // Request comparison if 2+ drivers selected
        if (this.selectedDrivers.length >= 2) {
            this.requestDriverComparison();

            // Start continuous comparison updates
            if (this.comparisonInterval) {
                clearInterval(this.comparisonInterval);
            }
            this.comparisonInterval = setInterval(() => {
                if (this.selectedDrivers.length >= 2) {
                    this.requestDriverComparison();
                }
            }, 500);  // Update every 500ms
            return;
        }

        // Close comparison if less than 2 drivers
        if (this.comparisonInterval) {
            clearInterval(this.comparisonInterval);
            this.comparisonInterval = null;
        }
        const panel = document.getElementById('telemetryComparison');
        if (panel) {
            panel.style.display = 'none';
        }
        this.showComparison = false;
        this.comparisonHistory = {
            speed: [],
            throttle: [],
            brake: [],
            gear: []
        };
    }
    
    updateConnectionStatus(connected) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
            
            // Check AI status
            this.socket.emit('get_ai_status');
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    }
    
    displayCommentary(text, time) {
        const commentaryBox = document.getElementById('aiCommentary');
        if (!commentaryBox) return;
        
        const commentaryItem = document.createElement('div');
        commentaryItem.className = 'commentary-item';
        commentaryItem.innerHTML = `
            <span class="commentary-time">${this.formatTime(time)}</span>
            <span class="commentary-text">${text}</span>
        `;
        
        commentaryBox.insertBefore(commentaryItem, commentaryBox.firstChild);
        
        // Keep only last 10 items
        while (commentaryBox.children.length > 10) {
            commentaryBox.removeChild(commentaryBox.lastChild);
        }
    }
    
    updateAIStatus(data) {
        const aiIndicator = document.getElementById('aiIndicator');
        if (!aiIndicator) return;
        
        let statusText = '🤖 AI: ';
        if (data.enabled) {
            statusText += 'ON';
            if (data.docling) statusText += ' | 📚 Regs';
            if (data.langflow) statusText += ' | 🔄 Workflows';
            aiIndicator.style.color = '#4ade80';
        } else {
            statusText += 'OFF';
            aiIndicator.style.color = '#94a3b8';
        }
        aiIndicator.textContent = statusText;
        
        // Show strategy insights section if Langflow is enabled
        if (data.langflow) {
            document.getElementById('strategyInsightsSection').style.display = 'block';
        }
        
        // Show regulations section if Docling is enabled
        if (data.docling) {
            document.getElementById('regulationsSection').style.display = 'block';
            const regCount = document.getElementById('regulationsCount');
            if (regCount && data.regulations_count) {
                regCount.textContent = `${data.regulations_count} sections loaded`;
            }
            console.log(`📚 Docling enabled: ${data.regulations_count} regulation sections loaded`);
        }

        // Enable optional panels when supported
        const debriefSection = document.getElementById('debriefSection');
        if (debriefSection) debriefSection.style.display = data.race_debrief ? 'block' : 'none';
        const ghostSection = document.getElementById('ghostSection');
        if (ghostSection) ghostSection.style.display = data.ghost_engine ? 'block' : 'none';

        // Sync current commentary mode if provided
        if (data.current_mode) {
            currentCommentaryMode = data.current_mode;
            const fanBtn = document.getElementById('fanModeBtn');
            const engBtn = document.getElementById('engineerModeBtn');
            if (fanBtn && engBtn) {
                fanBtn.classList.toggle('active', currentCommentaryMode === 'fan');
                engBtn.classList.toggle('active', currentCommentaryMode === 'engineer');
            }
        }
    }
    
    displayAnalysisResults(results) {
        const insightsBox = document.getElementById('strategyInsights');
        console.log('📊 Displaying analysis results:', results);
        
        if (!insightsBox) {
            console.warn('⚠️ Strategy insights box not found in DOM');
            return;
        }
        
        if (!results || results.length === 0) {
            console.log('⚠️ No analysis results to display');
            insightsBox.innerHTML = '<div class="insight-item">Waiting for analysis data...</div>';
            return;
        }
        
        const latestResult = results[results.length - 1];
        console.log('Latest result:', latestResult);
        
        const summary = latestResult.steps?.find(s => s.action === 'format_output')?.output;
        
        if (summary) {
            insightsBox.innerHTML = '';
            
            // Display insights
            if (summary.summary && summary.summary.length > 0) {
                summary.summary.forEach(insight => {
                    const insightItem = document.createElement('div');
                    insightItem.className = 'insight-item';
                    insightItem.textContent = insight;
                    insightsBox.appendChild(insightItem);
                });
            }
            
            // Display tyre analysis
            if (summary.tyreAnalysis) {
                const tyreSection = document.createElement('div');
                tyreSection.className = 'tyre-analysis-section';
                tyreSection.innerHTML = '<h4>Tyre Status</h4>';
                
                Object.entries(summary.tyreAnalysis).forEach(([driver, analysis]) => {
                    const tyreItem = document.createElement('div');
                    tyreItem.className = 'tyre-item';
                    tyreItem.innerHTML = `
                        <strong>${driver}</strong>: ${analysis.compound} 
                        (${analysis.age} laps, ${analysis.health.toFixed(0)}% health)
                    `;
                    tyreSection.appendChild(tyreItem);
                });
                
                insightsBox.appendChild(tyreSection);
            }
            
            // Display predictions if available
            if (summary.predictions) {
                const predSection = document.createElement('div');
                predSection.className = 'tyre-analysis-section';
                predSection.innerHTML = '<h4>Pit Window Predictions</h4>';
                
                Object.entries(summary.predictions).forEach(([driver, pred]) => {
                    const predItem = document.createElement('div');
                    predItem.className = 'tyre-item';
                    predItem.innerHTML = `
                        <strong>${driver}</strong>: ${pred.lapsRemaining} laps remaining 
                        (${pred.urgency} urgency)
                    `;
                    predSection.appendChild(predItem);
                });
                
                insightsBox.appendChild(predSection);
            }
        } else {
            console.warn('⚠️ No summary found in analysis results');
            insightsBox.innerHTML = '<div class="insight-item">Processing analysis...</div>';
        }
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    async loadSeasons() {
        console.log('🔄 Loading seasons...');
        try {
            const response = await fetch('/api/seasons');
            console.log('📡 Seasons response:', response);
            const data = await response.json();
            console.log('📊 Seasons data:', data);
            
            if (data.success) {
                const select = document.getElementById('seasonSelect');
                data.seasons.forEach(year => {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    select.appendChild(option);
                });
                console.log(`✅ Loaded ${data.seasons.length} seasons`);
            } else {
                console.error('❌ Failed to load seasons:', data);
            }
        } catch (error) {
            console.error('❌ Error loading seasons:', error);
        }
    }
    
    async loadRaces(year) {
        const raceSelect = document.getElementById('raceSelect');
        raceSelect.innerHTML = '<option value="">Loading...</option>';
        raceSelect.disabled = true;
        
        try {
            const response = await fetch(`/api/races/${year}`);
            const data = await response.json();
            
            if (data.success) {
                raceSelect.innerHTML = '<option value="">Select Race...</option>';
                data.races.forEach(race => {
                    const option = document.createElement('option');
                    option.value = race.round;
                    option.textContent = `R${race.round}: ${race.name}`;
                    raceSelect.appendChild(option);
                });
                raceSelect.disabled = false;
            }
        } catch (error) {
            console.error('Error loading races:', error);
            raceSelect.innerHTML = '<option value="">Error loading races</option>';
        }
    }
    
    async loadRace() {
        const year = document.getElementById('seasonSelect').value;
        const round = document.getElementById('raceSelect').value;
        
        if (!year || !round) return;
        
        const loadBtn = document.getElementById('loadRaceBtn');
        const originalText = loadBtn.textContent;
        loadBtn.textContent = 'Loading...';
        loadBtn.disabled = true;
        
        // Show loading screen with progress
        const loadingScreen = document.getElementById('loadingScreen');
        const loadingContent = loadingScreen.querySelector('.loading-content');
        loadingContent.innerHTML = `
            <h2>Loading Race Data</h2>
            <div class="progress-bar-container">
                <div class="progress-bar-fill" id="loadingProgressBar"></div>
            </div>
            <p id="loadingMessage">Initializing...</p>
        `;
        loadingScreen.style.display = 'flex';
        
        try {
            const response = await fetch('/api/load-race', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ year: parseInt(year), round: parseInt(round) })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                alert('Error loading race: ' + data.error);
                loadBtn.textContent = originalText;
                loadBtn.disabled = false;
                loadingScreen.style.display = 'none';
            }
            // Success will be handled by 'race_loaded' socket event
        } catch (error) {
            console.error('Error loading race:', error);
            alert('Error loading race');
            loadBtn.textContent = originalText;
            loadBtn.disabled = false;
            loadingScreen.style.display = 'none';
        }
    }
    
    handleLoadingProgress(data) {
        const progressBar = document.getElementById('loadingProgressBar');
        const message = document.getElementById('loadingMessage');
        
        if (progressBar) {
            progressBar.style.width = data.percent + '%';
        }
        if (message) {
            message.textContent = data.message;
        }
    }
    
    handleRaceLoaded(data) {
        const loadBtn = document.getElementById('loadRaceBtn');
        
        if (data.success) {
            console.log('Race loaded successfully:', data.raceInfo);
            this.raceData = data.raceInfo;
            this.showRaceInfo();
            this.initializeViewer();
            loadBtn.textContent = 'Load Race';
            loadBtn.disabled = false;
        } else {
            console.error('Race loading failed:', data.error);
            alert('Error loading race: ' + data.error);
            loadBtn.textContent = 'Load Race';
            loadBtn.disabled = false;
            const loadingScreen = document.getElementById('loadingScreen');
            loadingScreen.style.display = 'flex';
            loadingScreen.querySelector('.loading-content').innerHTML = `
                <h2>Error loading race</h2>
                <p>${data.error}</p>
                <p>Please try again or select a different race</p>
            `;
        }
    }
    
    showRaceInfo() {
        console.log('Showing race info:', this.raceData);
        
        document.getElementById('eventName').textContent = this.raceData.eventName;
        document.getElementById('circuitName').textContent = this.raceData.circuitName;
        document.getElementById('raceDate').textContent = this.raceData.date;
        document.getElementById('totalLaps').textContent = this.raceData.totalLaps;
        document.getElementById('sessionTotalLaps').textContent = this.raceData.totalLaps;

        // Frame-accurate progress slider
        const slider = document.getElementById('progressSlider');
        if (slider) {
            slider.max = String(Math.max(0, (this.raceData.totalFrames || 0) - 1));
            slider.value = '0';
        }
        
        // Show all sections
        document.getElementById('raceInfoSection').style.display = 'block';
        document.getElementById('leaderboardSection').style.display = 'block';
        document.getElementById('tyreStrategySection').style.display = 'block';
        document.getElementById('raceControlSection').style.display = 'block';
        document.getElementById('aiCommentarySection').style.display = 'block';

        // Optional feature panels (availability depends on server-side features)
        const debriefSection = document.getElementById('debriefSection');
        if (debriefSection) debriefSection.style.display = 'block';
        const ghostSection = document.getElementById('ghostSection');
        if (ghostSection) ghostSection.style.display = 'block';
        
        if (this.raceData.hasWeather) {
            document.getElementById('weatherSection').style.display = 'block';
        }
        
        // Start requesting analysis results periodically
        if (this.analysisInterval) {
            clearInterval(this.analysisInterval);
        }
        // Prime the UI immediately so it doesn't look stuck.
        const insightsBox = document.getElementById('strategyInsights');
        if (insightsBox && !insightsBox.innerHTML.trim()) {
            insightsBox.innerHTML = '<div class="insight-item">Waiting for analysis data...</div>';
        }
        this.socket.emit('get_analysis_results');
        this.analysisInterval = setInterval(() => {
            this.socket.emit('get_analysis_results');
        }, 15000); // Every 15 seconds
        
        console.log('Race info sections displayed');
    }
    
    initializeViewer() {
        console.log('Initializing viewer...');
        
        document.getElementById('loadingScreen').style.display = 'none';
        this.canvas.style.display = 'block';
        document.getElementById('sessionInfo').style.display = 'block';
        document.getElementById('controls').style.display = 'flex';
        
        this.resizeCanvas();
        
        console.log('Viewer initialized successfully');
    }
    
    resizeCanvas() {
        if (!this.canvas) return;
        
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
        
        if (this.currentTelemetry) {
            this.drawFrame();
        }
    }
    
    handleTelemetryUpdate(data) {
        console.log('📊 Telemetry received:', {
            frame: data.frameIndex,
            hasTrackData: !!data.trackData,
            trackPoints: data.trackData?.x?.length || 0,
            drivers: Object.keys(data.frame?.drivers || {}).length,
            colors: Object.keys(data.driverColors || {}).length,
            hasTyreHealth: !!data.tyreHealthData
        });
        
        this.currentTelemetry = data;
        this.updateUI(data);
        this.updateTyreStrategy(data);
        this.drawFrame();
    }
    
    updateUI(data) {
        // Session info
        document.getElementById('sessionTime').textContent = data.sessionData.time;
        document.getElementById('sessionLap').textContent = data.sessionData.lap;
        document.getElementById('sessionLeader').textContent = data.sessionData.leader;
        
        // Track status
        const trackStatus = this.getTrackStatusName(data.trackStatus);
        const statusEl = document.getElementById('trackStatus');
        statusEl.textContent = trackStatus;
        statusEl.className = `track-status ${trackStatus}`;
        
        // Weather
        if (data.weather && this.showWeather) {
            document.getElementById('trackTemp').textContent = `${data.weather.trackTemp}°C`;
            document.getElementById('airTemp').textContent = `${data.weather.airTemp}°C`;
            document.getElementById('humidity').textContent = `${data.weather.humidity}%`;
            document.getElementById('wind').textContent = 
                `${data.weather.windSpeed} km/h ${data.weather.windDirection}`;
        }
        
        // Progress (frame-accurate)
        const slider = document.getElementById('progressSlider');
        if (slider) {
            const max = Math.max(0, (data.totalFrames || 0) - 1);
            if (parseInt(slider.max, 10) !== max) slider.max = String(max);
            slider.value = String(data.frameIndex || 0);
        }
        document.getElementById('currentFrame').textContent = data.frameIndex;
        document.getElementById('totalFrames').textContent = data.totalFrames;
        
        // Leaderboard
        this.updateLeaderboard(data.frame.drivers);
        
        // Race control
        if (data.raceControlMessages) {
            this.updateRaceControl(data.raceControlMessages);
        }
    }
    
    getTrackStatusName(status) {
        const statusMap = {
            '1': 'GREEN',
            '2': 'YELLOW',
            '4': 'SC',
            '5': 'RED',
            '6': 'VSC',
            '7': 'VSC'
        };
        return statusMap[status] || 'GREEN';
    }
    
    
    updateTelemetryComparison(data) {
        if (!data || !data.drivers || data.drivers.length < 2) {
            return;
        }
        
        // Show comparison panel
        const panel = document.getElementById('telemetryComparison');
        if (panel) {
            panel.style.display = 'block';
            this.showComparison = true;
        }
        
        // Update driver badges
        const driversDiv = document.getElementById('comparisonDrivers');
        if (driversDiv) {
            driversDiv.innerHTML = '';
            data.drivers.forEach(driver => {
                const badge = document.createElement('div');
                badge.className = 'comparison-driver-badge';
                badge.style.borderColor = driver.color;
                badge.style.color = driver.color;
                badge.innerHTML = `
                    <div class="driver-color-dot" style="background: ${driver.color}"></div>
                    <span>${driver.code}</span>
                    <span style="opacity: 0.7; font-size: 0.8rem;">P${driver.position}</span>
                `;
                driversDiv.appendChild(badge);
            });
        }
        
        // Add data to history
        const dataPoint = {
            timestamp: data.timestamp,
            drivers: {}
        };
        
        data.drivers.forEach(driver => {
            dataPoint.drivers[driver.code] = {
                speed: driver.speed,
                throttle: driver.throttle,
                brake: driver.brake,
                gear: driver.gear,
                color: driver.color
            };
        });
        
        // Add to history and limit size
        this.comparisonHistory.speed.push(dataPoint);
        this.comparisonHistory.throttle.push(dataPoint);
        this.comparisonHistory.brake.push(dataPoint);
        this.comparisonHistory.gear.push(dataPoint);
        
        if (this.comparisonHistory.speed.length > this.maxHistoryPoints) {
            this.comparisonHistory.speed.shift();
            this.comparisonHistory.throttle.shift();
            this.comparisonHistory.brake.shift();
            this.comparisonHistory.gear.shift();
        }
        
        // Draw charts
        this.drawComparisonChart('speedChart', this.comparisonHistory.speed, 'speed', 0, 350);
        this.drawComparisonChart('throttleChart', this.comparisonHistory.throttle, 'throttle', 0, 100);
        this.drawComparisonChart('brakeChart', this.comparisonHistory.brake, 'brake', 0, 1);
        this.drawComparisonChart('gearChart', this.comparisonHistory.gear, 'gear', 0, 8);
        
        // Update stats
        this.updateComparisonStats(data);
    }
    
    drawComparisonChart(canvasId, history, metric, minY, maxY) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        if (history.length < 2) return;
        
        // Draw grid
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Get all driver codes from first data point
        const firstPoint = history[0];
        const driverCodes = Object.keys(firstPoint.drivers);
        
        // Draw line for each driver
        driverCodes.forEach(code => {
            const color = firstPoint.drivers[code].color;
            
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            let started = false;
            history.forEach((point, index) => {
                if (!point.drivers[code]) return;
                
                const value = point.drivers[code][metric];
                const x = (index / (history.length - 1)) * width;
                const y = height - ((value - minY) / (maxY - minY)) * height;
                
                if (!started) {
                    ctx.moveTo(x, y);
                    started = true;
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
            
            // Draw current value label
            const lastPoint = history[history.length - 1];
            if (lastPoint.drivers[code]) {
                const value = lastPoint.drivers[code][metric];
                const y = height - ((value - minY) / (maxY - minY)) * height;
                
                ctx.fillStyle = color;
                ctx.font = 'bold 10px Arial';
                ctx.textAlign = 'right';
                ctx.fillText(Math.round(value), width - 5, y);
            }
        });
    }
    
    updateComparisonStats(data) {
        const statsDiv = document.getElementById('telemetryStats');
        if (!statsDiv || !data.drivers || data.drivers.length < 2) return;
        
        const driver1 = data.drivers[0];
        const driver2 = data.drivers[1];
        
        const speedDiff = (driver1.speed - driver2.speed).toFixed(1);
        const throttleDiff = (driver1.throttle - driver2.throttle).toFixed(1);
        const gearDiff = driver1.gear - driver2.gear;
        
        statsDiv.innerHTML = `
            <div class="stat-row">
                <span class="stat-label">Speed Difference</span>
                <span class="stat-value" style="color: ${speedDiff > 0 ? driver1.color : driver2.color}">
                    ${Math.abs(speedDiff)} km/h
                </span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Throttle Difference</span>
                <span class="stat-value" style="color: ${throttleDiff > 0 ? driver1.color : driver2.color}">
                    ${Math.abs(throttleDiff)}%
                </span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Position Gap</span>
                <span class="stat-value">
                    ${Math.abs(driver1.position - driver2.position)} positions
                </span>
            </div>
            ${driver1.tyreHealth && driver2.tyreHealth ? `
            <div class="stat-row">
                <span class="stat-label">Tyre Health</span>
                <div class="stat-values">
                    <span style="color: ${driver1.color}">${driver1.tyreHealth.health.toFixed(0)}%</span>
                    <span style="color: ${driver2.color}">${driver2.tyreHealth.health.toFixed(0)}%</span>
                </div>
            </div>
            ` : ''}
        `;
    }
    
    requestDriverComparison() {
        if (this.selectedDrivers.length >= 2) {
            this.socket.emit('get_driver_comparison', {
                drivers: this.selectedDrivers
            });
        }
    }
    
    updateLeaderboard(drivers) {
        const leaderboard = document.getElementById('leaderboard');
        
        const sortedDrivers = Object.entries(drivers).sort((a, b) => {
            return a[1].position - b[1].position;
        });
        
        // Log gap data for debugging
        console.log(`📊 Gap Mode: ${this.gapMode}`);
        if (sortedDrivers.length > 0) {
            const firstDriver = sortedDrivers[0];
            console.log(`Sample driver data (${firstDriver[0]}):`, {
                position: firstDriver[1].position,
                gapToLeader: firstDriver[1].gapToLeader,
                intervalGap: firstDriver[1].intervalGap
            });
        }
        
        leaderboard.innerHTML = '';
        sortedDrivers.forEach(([code, data]) => {
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            if (this.selectedDrivers.includes(code)) {
                item.classList.add('selected');
            }
            item.style.borderLeftColor = this.getDriverColor(code);
            
            // Gap display
            let gapText = '';
            if (this.gapMode === 'leader' && data.gapToLeader !== undefined) {
                gapText = data.position === 1 ? '-' : `+${data.gapToLeader.toFixed(1)}s`;
            } else if (this.gapMode === 'interval' && data.intervalGap !== undefined) {
                gapText = data.position === 1 ? '-' : `+${data.intervalGap.toFixed(1)}s`;
            }
            
            // Tyre indicator with compound names
            const tyreCompounds = ['SOFT', 'MEDIUM', 'HARD', 'INTER', 'WET'];
            const tyreColors = ['#ff0000', '#ffff00', '#ffffff', '#00ff00', '#0000ff'];
            const tyreColor = tyreColors[data.tyre] || '#888';
            const tyreName = tyreCompounds[data.tyre] || '?';
            
            // Tyre health indicator
            let tyreHealthBar = '';
            if (data.tyreHealth !== undefined && typeof data.tyreHealth === 'number') {
                const health = data.tyreHealth;
                let healthColor;
                if (health > 70) healthColor = '#00ff00';
                else if (health > 40) healthColor = '#ffff00';
                else if (health > 20) healthColor = '#ff8800';
                else healthColor = '#ff0000';
                
                tyreHealthBar = `
                    <div class="tyre-health-container" title="Tyre Health: ${health.toFixed(0)}%">
                        <div class="tyre-health-bar" style="width: ${health}%; background: ${healthColor}"></div>
                    </div>
                `;
            }
            
            // DRS indicator
            const drsActive = data.drs >= 10;
            
            // Status badges
            let statusBadge = '';
            if (data.inPit) {
                statusBadge = '<span class="status-badge pit">PIT</span>';
            }
            
            // Tyre life display
            const tyreLife = data.tyreLife || 0;
            
            item.innerHTML = `
                <span class="position">${data.position}</span>
                <span class="code">${code}</span>
                ${gapText ? `<span class="gap">${gapText}</span>` : ''}
                <span class="speed">${Math.round(data.speed)} km/h</span>
                <div class="tyre-info">
                    <span class="tyre-indicator" style="background: ${tyreColor}" title="${tyreName} - ${tyreLife} laps"></span>
                    <span class="tyre-laps">${tyreLife}</span>
                </div>
                ${tyreHealthBar}
                <span class="drs-indicator ${drsActive ? 'active' : ''}" title="${drsActive ? 'DRS Active' : 'DRS Inactive'}"></span>
                ${statusBadge}
            `;
            
            item.title = 'Left click: select only this driver. Right click: add/remove for comparison.';

            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectDriver(code, false, drivers);
            });

            item.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.selectDriver(code, true, drivers);
            });
            
            leaderboard.appendChild(item);
        });
    }
    
    
    updateTyreStrategy(data) {
        if (!data.tyreHealthData) {
            return;
        }
        
        const panel = document.getElementById('tyreStrategyPanel');
        if (!panel) return;
        
        const drivers = data.frame.drivers;
        const tyreHealthData = data.tyreHealthData;
        
        // Sort by position
        const sortedDrivers = Object.entries(drivers).sort((a, b) => {
            return a[1].position - b[1].position;
        });
        
        panel.innerHTML = '';
        
        sortedDrivers.forEach(([code, driverData]) => {
            const healthData = tyreHealthData[code];
            if (!healthData) return;
            
            const health = healthData.health;
            const compound = healthData.compound;
            const tyreLife = healthData.tyreLife;
            const remainingLaps = healthData.remainingLaps;
            const baseLife = healthData.baseLife;
            
            // Determine health class
            let healthClass = 'excellent';
            if (health <= 20) healthClass = 'critical';
            else if (health <= 40) healthClass = 'warning';
            else if (health <= 70) healthClass = 'good';
            
            // Determine if pit stop recommended
            const shouldPit = health < 30 || remainingLaps < 5;
            
            // Get driver color
            const driverColor = this.getDriverColor(code);
            
            const item = document.createElement('div');
            item.className = 'tyre-strategy-item';
            item.style.borderLeftColor = driverColor;
            
            item.innerHTML = `
                <div class="tyre-strategy-header">
                    <div class="tyre-driver-info">
                        <span class="tyre-driver-code" style="color: ${driverColor}">${code}</span>
                        <span class="tyre-compound-badge ${compound}">${compound}</span>
                        <span class="tyre-age">${tyreLife} laps</span>
                    </div>
                    <span class="tyre-health-value ${healthClass}">${health.toFixed(0)}%</span>
                </div>
                <div class="tyre-health-display">
                    <div class="tyre-health-bar-container">
                        <div class="tyre-health-bar-fill ${healthClass}" style="width: ${health}%"></div>
                    </div>
                    <div class="tyre-health-stats">
                        <span class="tyre-remaining-laps">
                            ${remainingLaps} / ${baseLife} laps remaining
                        </span>
                    </div>
                </div>
                ${shouldPit ? '<div class="tyre-pit-recommendation">⚠️ PIT WINDOW RECOMMENDED</div>' : ''}
            `;
            
            panel.appendChild(item);
        });
    }
    
    updateRaceControl(messages) {
        const feed = document.getElementById('raceControlFeed');
        if (!feed) return;
        
        // Only show last 5 messages
        const recentMessages = messages.slice(-5);
        
        // Prevent flickering by only updating if messages changed
        const msgHash = JSON.stringify(recentMessages);
        if (feed.dataset.lastHash === msgHash) return;
        feed.dataset.lastHash = msgHash;
        
        feed.innerHTML = '';
        recentMessages.forEach(msg => {
            const item = document.createElement('div');
            item.className = 'race-control-message';
            
            if (msg.flag) item.classList.add('flag');
            if (msg.category.includes('SAFETY')) item.classList.add('safety-car');
            if (msg.category.includes('PENALTY')) item.classList.add('penalty');
            
            const time = Math.floor(msg.time);
            const minutes = Math.floor(time / 60);
            const seconds = time % 60;
            
            item.innerHTML = `
                <div class="time">${minutes}:${seconds.toString().padStart(2, '0')}</div>
                <div>
                    <span class="category">${msg.category}</span>
                    ${msg.message}
                </div>
            `;
            
            feed.appendChild(item);
        });
    }
    
    drawFrame() {
        if (!this.currentTelemetry || !this.ctx) {
            console.log('⚠️ Cannot draw frame: missing telemetry or context');
            return;
        }
        
        console.log('🎨 Drawing frame:', this.currentTelemetry.frameIndex);
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw track
        this.drawTrack();
        
        // Draw DRS zones
        if (this.showDrs && this.currentTelemetry.trackData && this.currentTelemetry.trackData.drsZones) {
            this.drawDrsZones();
        }
        
        // Draw finish line
        if (this.currentTelemetry.trackData && this.currentTelemetry.trackData.finishLine) {
            this.drawFinishLine();
        }
        
        // Draw safety car
        if (this.currentTelemetry.frame.safetyCar) {
            this.drawSafetyCar(this.currentTelemetry.frame.safetyCar);
        }

        // Draw ghost overlay (fastest-lap reference) if enabled
        if (this.ghostEnabled && this.ghostPosition && this.ghostPosition.visible) {
            this.drawGhost(this.ghostPosition);
        }
        
        // Draw cars
        const drivers = this.currentTelemetry.frame.drivers;
        if (drivers) {
            Object.entries(drivers).forEach(([code, data]) => {
                this.drawCar(data.x, data.y, code, data);
            });
        }
    }

    drawGhost(pos) {
        const pt = this.getTransformedPoint(pos.x, pos.y);
        const x = pt.x * this.trackScale + this.trackOffsetX;
        const y = pt.y * this.trackScale + this.trackOffsetY;

        this.ctx.fillStyle = 'rgba(0, 255, 255, 0.25)';
        this.ctx.beginPath();
        this.ctx.arc(x, y, 10, 0, Math.PI * 2);
        this.ctx.fill();

        this.ctx.strokeStyle = 'rgba(0, 255, 255, 0.8)';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.9)';
        this.ctx.lineWidth = 3;
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'bottom';
        this.ctx.strokeText('GHOST', x, y - 14);
        this.ctx.fillText('GHOST', x, y - 14);
    }

    setGhostEnabled(enabled) {
        this.ghostEnabled = !!enabled;
        this.drawFrame();
    }

    setGhostData(data) {
        if (!data) return;
        if (data.ghost_position) this.ghostPosition = data.ghost_position;
        if (data.delta) this.ghostDelta = data.delta;
        if (this.ghostEnabled) this.drawFrame();
    }
    
    drawTrack() {
        if (!this.currentTelemetry || !this.currentTelemetry.trackData) {
            console.log('⚠️ No track data available');
            return;
        }
        
        const track = this.currentTelemetry.trackData;
        if (!track.x || track.x.length === 0) {
            console.log('⚠️ Track data is empty');
            return;
        }
        
        console.log(`✅ Drawing track with ${track.x.length} points`);
        
        // Calculate scale
        const padding = 50;
        let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
        
        for (let i = 0; i < track.x.length; i++) {
            const pt = this.getTransformedPoint(track.x[i], track.y[i]);
            if (pt.x < xMin) xMin = pt.x;
            if (pt.x > xMax) xMax = pt.x;
            if (pt.y < yMin) yMin = pt.y;
            if (pt.y > yMax) yMax = pt.y;
        }
        
        const trackWidth = xMax - xMin;
        const trackHeight = yMax - yMin;
        
        const scaleX = (this.canvas.width - padding * 2) / trackWidth;
        const scaleY = (this.canvas.height - padding * 2) / trackHeight;
        this.trackScale = Math.min(scaleX, scaleY);
        
        this.trackOffsetX = padding - xMin * this.trackScale + (this.canvas.width - trackWidth * this.trackScale) / 2;
        this.trackOffsetY = padding - yMin * this.trackScale + (this.canvas.height - trackHeight * this.trackScale) / 2;
        // this.trackOffsetY -= 5;
        
        // Draw track outline
        this.ctx.strokeStyle = '#444';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        
        for (let i = 0; i < track.x.length; i++) {
            const pt = this.getTransformedPoint(track.x[i], track.y[i]);
            const x = pt.x * this.trackScale + this.trackOffsetX;
            const y = pt.y * this.trackScale + this.trackOffsetY;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.closePath();
        this.ctx.stroke();
        
        // Draw inner/outer bounds if available
        if (track.innerX && track.outerX) {
            this.ctx.strokeStyle = '#333';
            this.ctx.lineWidth = 1;
            
            // Inner bound
            this.ctx.beginPath();
            for (let i = 0; i < track.innerX.length; i++) {
                const pt = this.getTransformedPoint(track.innerX[i], track.innerY[i]);
                const x = pt.x * this.trackScale + this.trackOffsetX;
                const y = pt.y * this.trackScale + this.trackOffsetY;
                if (i === 0) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            this.ctx.stroke();
            
            // Outer bound
            this.ctx.beginPath();
            for (let i = 0; i < track.outerX.length; i++) {
                const pt = this.getTransformedPoint(track.outerX[i], track.outerY[i]);
                const x = pt.x * this.trackScale + this.trackOffsetX;
                const y = pt.y * this.trackScale + this.trackOffsetY;
                if (i === 0) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            this.ctx.stroke();
        }
    }
    
    drawDrsZones() {
        const zones = this.currentTelemetry.trackData.drsZones;
        if (!zones || zones.length === 0) return;
        
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.lineWidth = 6;
        
        zones.forEach(zone => {
            const startIdx = zone.startIndex;
            const endIdx = zone.endIndex;
            const track = this.currentTelemetry.trackData;
            
            this.ctx.beginPath();
            for (let i = startIdx; i <= endIdx && i < track.x.length; i++) {
                const pt = this.getTransformedPoint(track.x[i], track.y[i]);
                const x = pt.x * this.trackScale + this.trackOffsetX;
                const y = pt.y * this.trackScale + this.trackOffsetY;
                if (i === startIdx) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            this.ctx.stroke();
        });
    }
    
    drawFinishLine() {
        const finish = this.currentTelemetry.trackData.finishLine;
        const pt = this.getTransformedPoint(finish.x, finish.y);
        const x = pt.x * this.trackScale + this.trackOffsetX;
        const y = pt.y * this.trackScale + this.trackOffsetY;
        
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 4;
        this.ctx.setLineDash([10, 5]);
        this.ctx.beginPath();
        this.ctx.moveTo(x - 15, y - 15);
        this.ctx.lineTo(x + 15, y + 15);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }
    
    drawSafetyCar(scData) {
        const pt = this.getTransformedPoint(scData.x, scData.y);
        const x = pt.x * this.trackScale + this.trackOffsetX;
        const y = pt.y * this.trackScale + this.trackOffsetY;
        const alpha = scData.alpha;
        
        // Glow effect
        if (scData.phase === 'deploying' || scData.phase === 'returning') {
            const pulse = 0.5 + 0.5 * Math.sin(Date.now() / 100);
            this.ctx.fillStyle = `rgba(255, 165, 0, ${alpha * pulse * 0.3})`;
            this.ctx.beginPath();
            this.ctx.arc(x, y, 20, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // SC body
        this.ctx.fillStyle = `rgba(255, 165, 0, ${alpha})`;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 8, 0, Math.PI * 2);
        this.ctx.fill();
        
        // SC label
        this.ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('SC', x, y - 12);
    }
    
    drawCar(worldX, worldY, code, data) {
        const pt = this.getTransformedPoint(worldX, worldY);
        const x = pt.x * this.trackScale + this.trackOffsetX;
        const y = pt.y * this.trackScale + this.trackOffsetY;
        
        const color = this.getDriverColor(code);
        const isSelected = this.selectedDrivers.includes(code);
        
        // Draw car with larger size
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 8, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Add border for better visibility
        this.ctx.strokeStyle = isSelected ? '#ffffff' : '#000000';
        this.ctx.lineWidth = isSelected ? 3 : 1;
        this.ctx.stroke();
        
        // Always draw driver code above car
        this.ctx.fillStyle = '#ffffff';
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 3;
        this.ctx.font = 'bold 11px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'bottom';
        
        // Draw text with outline for better visibility
        this.ctx.strokeText(code, x, y - 12);
        this.ctx.fillText(code, x, y - 12);
        
        // Draw position number below car
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textBaseline = 'top';
        this.ctx.strokeText(data.position.toString(), x, y + 12);
        this.ctx.fillText(data.position.toString(), x, y + 12);
        
        // Draw pit indicator if in pit
        if (data.inPit) {
            this.ctx.fillStyle = '#ff8800';
            this.ctx.beginPath();
            this.ctx.arc(x + 10, y - 10, 4, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = 'bold 8px Arial';
            this.ctx.fillText('P', x + 10, y - 8);
        }
        
        // Draw tyre health indicator
        if (data.tyreHealth !== undefined && typeof data.tyreHealth === 'number') {
            const health = data.tyreHealth;
            let healthColor;
            if (health > 70) healthColor = '#00ff00';
            else if (health > 40) healthColor = '#ffff00';
            else if (health > 20) healthColor = '#ff8800';
            else healthColor = '#ff0000';
            
            this.ctx.fillStyle = healthColor;
            this.ctx.fillRect(x - 8, y + 18, 16, 3);
        }
    }
    
    getDriverColor(code) {
        // First try to get from current telemetry
        if (this.currentTelemetry && this.currentTelemetry.driverColors && this.currentTelemetry.driverColors[code]) {
            console.log(`Color for ${code}:`, this.currentTelemetry.driverColors[code]);
            return this.currentTelemetry.driverColors[code];
        }
        
        // Fallback to default team colors (2024 season)
        const colors = {
            'VER': '#3671C6', 'PER': '#3671C6',  // Red Bull
            'HAM': '#27F4D2', 'RUS': '#27F4D2',  // Mercedes
            'LEC': '#E8002D', 'SAI': '#E8002D',  // Ferrari
            'NOR': '#FF8000', 'PIA': '#FF8000',  // McLaren
            'ALO': '#229971', 'STR': '#229971',  // Aston Martin
            'OCO': '#0093CC', 'GAS': '#0093CC',  // Alpine
            'BOT': '#52E252', 'ZHO': '#52E252',  // Kick Sauber
            'MAG': '#B6BABD', 'HUL': '#B6BABD',  // Haas
            'TSU': '#6692FF', 'RIC': '#6692FF',  // RB
            'ALB': '#64C4FF', 'SAR': '#64C4FF',  // Williams
            'BEA': '#E8002D', 'LAW': '#3671C6',  // Reserve drivers
            'DEV': '#FF8000', 'COL': '#229971'
        };
        
        return colors[code] || '#FFFFFF';
    }
    
    togglePlayPause() {
        if (this.isPlaying) {
            this.socket.emit('pause');
            document.getElementById('playPauseBtn').textContent = '▶';
        } else {
            this.socket.emit('play');
            document.getElementById('playPauseBtn').textContent = '⏸';
        }
        this.isPlaying = !this.isPlaying;
    }
    
    restart() {
        this.socket.emit('restart');
        this.isPlaying = false;
        document.getElementById('playPauseBtn').textContent = '▶';
    }
    
    setSpeed(speed) {
        this.socket.emit('set_speed', { speed });
    }
    
    seek(progress) {
        if (!this.raceData) return;
        const frameIndex = Math.max(0, Math.min(progress, (this.raceData.totalFrames || 1) - 1));
        this.socket.emit('seek', { frameIndex });
    }
    
    handlePlaybackStatus(data) {
        console.log('Playback status:', data);
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.chronos = new ChronosF1Enhanced();
});


// ===== TTS COMMENTARY INTEGRATION =====
class TTSCommentary {
    constructor() {
        this.synth = window.speechSynthesis;
        this.enabled = true;
        this.voice = null;
        this.rate = 1.0;
        this.volume = 0.8;
        this.initVoices();
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = () => this.initVoices();
        }
    }
    
    initVoices() {
        const voices = this.synth.getVoices();
        const preferredVoices = ['Google UK English Male', 'Google US English', 'Microsoft David - English (United States)', 'Alex', 'Daniel'];
        for (const preferred of preferredVoices) {
            const found = voices.find(v => v.name === preferred);
            if (found) {
                this.voice = found;
                console.log(`✅ TTS Voice: ${found.name}`);
                return;
            }
        }
        const englishVoice = voices.find(v => v.lang.startsWith('en'));
        if (englishVoice) this.voice = englishVoice;
    }
    
    speak(text, mode = 'fan') {
        if (!this.enabled || !this.synth) return;
        this.synth.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        if (this.voice) utterance.voice = this.voice;
        utterance.rate = mode === 'engineer' ? 0.95 : 1.0;
        utterance.volume = this.volume;
        utterance.onstart = () => console.log('🔊 Speaking:', text.substring(0, 50) + '...');
        this.synth.speak(utterance);
    }
    
    toggle() {
        this.enabled = !this.enabled;
        if (!this.enabled) this.synth.cancel();
        return this.enabled;
    }
}

// Global TTS instance
window.ttsCommentary = new TTSCommentary();

// ===== NEW FEATURES INTEGRATION =====
let currentCommentaryMode = 'fan';
let ghostEnabled = false;

// Initialize new features
function initializeNewFeatures() {
    console.log('🚀 Initializing new features...');
    
    // Listen for AI commentary with TTS
    if (window.chronos && window.chronos.socket) {
        window.chronos.socket.on('ai_commentary', (data) => {
            console.log('🎙️ AI Commentary:', data.text);
            // Speak the commentary
            if (window.ttsCommentary && data.text) {
                window.ttsCommentary.speak(data.text, data.mode || currentCommentaryMode);
            }
        });
        
        // Listen for commentary mode changes
        window.chronos.socket.on('commentary_mode_changed', (data) => {
            currentCommentaryMode = data.mode;
            console.log('Mode changed to:', data.mode);
        });
        
        // Listen for race debrief
        window.chronos.socket.on('race_debrief', (debrief) => {
            console.log('📊 Race Debrief received');
            displayRaceDebrief(debrief);
        });
        
        // Listen for ghost updates
        window.chronos.socket.on('ghost_update', (data) => {
            console.log('👻 Ghost update received:', data);
            if (window.chronos && typeof window.chronos.setGhostData === 'function') {
                window.chronos.setGhostData(data);
            }
            // Always update display if data is received (backend only sends when enabled)
            updateGhostDisplay(data);
        });

        // Listen for ghost status (enabled + reference driver)
        window.chronos.socket.on('ghost_status', (data) => {
            const ref = document.getElementById('ghostRef');
            if (ref && data && data.driver) ref.textContent = data.driver;
        });
        
        // Listen for regulation context updates
        window.chronos.socket.on('regulation_context', (data) => {
            console.log('📚 Regulation context received:', data);
            displayRegulationContext(data);
        });
        
        // Listen for replay completion
        window.chronos.socket.on('replay_completed', () => {
            console.log('🏁 Replay completed');
            setTimeout(() => requestRaceDebrief(), 1000);
        });
    }
    
    console.log('✅ New features initialized');
}

// Set commentary mode
function setCommentaryMode(mode) {
    if (window.chronos && window.chronos.socket) {
        window.chronos.socket.emit('set_commentary_mode', { mode: mode });
        currentCommentaryMode = mode;
    }

    const fanBtn = document.getElementById('fanModeBtn');
    const engBtn = document.getElementById('engineerModeBtn');
    if (fanBtn && engBtn) {
        fanBtn.classList.toggle('active', mode === 'fan');
        engBtn.classList.toggle('active', mode === 'engineer');
    }
}

// Request race debrief
function requestRaceDebrief() {
    if (window.chronos && window.chronos.socket) {
        window.chronos.socket.emit('request_race_debrief');
    }
}

// Display race debrief
function displayRaceDebrief(debrief) {
    const modalHTML = `
        <div id="debriefModal" class="modal active">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>🏁 Race Debrief</h2>
                    <button class="close-btn" onclick="closeDebriefModal()">×</button>
                </div>
                <div class="modal-body">
                    <h3>${debrief.race_info.event}</h3>
                    <p><strong>Best Strategy:</strong> ${debrief.best_strategy}</p>
                    <p><strong>Most Aggressive:</strong> ${debrief.most_aggressive_driver}</p>
                    <p><strong>Summary:</strong> ${debrief.race_summary}</p>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeDebriefModal() {
    const modal = document.getElementById('debriefModal');
    if (modal) modal.remove();
}

// Toggle ghost
function toggleGhost(enabled) {
    ghostEnabled = enabled;
    if (window.chronos && window.chronos.socket) {
        window.chronos.socket.emit('toggle_ghost', { enabled: enabled });
    }
    if (window.chronos && typeof window.chronos.setGhostEnabled === 'function') {
        window.chronos.setGhostEnabled(enabled);
    }

    const text = document.getElementById('ghostToggleText');
    if (text) text.textContent = enabled ? 'Disable Ghost' : 'Enable Ghost';
    
    const panel = document.getElementById('ghostPanel');
    if (panel) panel.style.display = enabled ? 'block' : 'none';
}

// Update ghost display
function updateGhostDisplay(data) {
    console.log('🎯 updateGhostDisplay called with data:', data);
    
    if (!data || !data.delta) {
        console.warn('⚠️ No delta data in ghost update');
        return;
    }
    
    const delta = data.delta;
    console.log('📊 Delta data:', delta);
    
    // Update lap delta
    const lapDelta = document.getElementById('lapDelta');
    if (lapDelta) {
        const sign = delta.lap_delta >= 0 ? '+' : '';
        lapDelta.textContent = `${sign}${delta.lap_delta.toFixed(3)}`;
        lapDelta.className = `delta-value ${delta.delta_color}`;
        console.log('✅ Updated lap delta:', lapDelta.textContent);
    } else {
        console.warn('⚠️ lapDelta element not found');
    }
    
    // Update speed differential
    const speedDelta = document.getElementById('speedDelta');
    if (speedDelta) {
        const sign = delta.speed_diff >= 0 ? '+' : '';
        speedDelta.textContent = `${sign}${Math.round(delta.speed_diff)} km/h`;
        
        // Color based on speed difference
        if (Math.abs(delta.speed_diff) < 5) {
            speedDelta.style.color = '#fbbf24'; // Gold - similar speed
        } else if (delta.speed_diff > 0) {
            speedDelta.style.color = '#4ade80'; // Green - faster
        } else {
            speedDelta.style.color = '#ef4444'; // Red - slower
        }
        console.log('✅ Updated speed delta:', speedDelta.textContent);
    } else {
        console.warn('⚠️ speedDelta element not found');
    }
    
    // Update sector deltas
    if (delta.sector_deltas && delta.sector_deltas.length >= 3) {
        console.log('📍 Updating sector deltas:', delta.sector_deltas);
        for (let i = 0; i < 3; i++) {
            const sectorDelta = delta.sector_deltas[i];
            const sectorEl = document.getElementById(`sector${i + 1}Delta`);
            
            if (sectorEl) {
                if (Math.abs(sectorDelta) < 0.001) {
                    sectorEl.textContent = '-';
                    sectorEl.className = 'delta-value';
                } else {
                    const sign = sectorDelta >= 0 ? '+' : '';
                    sectorEl.textContent = `${sign}${sectorDelta.toFixed(3)}`;
                    
                    // Color based on sector performance
                    if (Math.abs(sectorDelta) < 0.05) {
                        sectorEl.className = 'delta-value gold';
                    } else if (sectorDelta < 0) {
                        sectorEl.className = 'delta-value green';
                    } else {
                        sectorEl.className = 'delta-value red';
                    }
                }
                console.log(`✅ Updated sector ${i + 1}:`, sectorEl.textContent);
            } else {
                console.warn(`⚠️ sector${i + 1}Delta element not found`);
            }
        }
    }
    
    // Update current sector highlight
    if (delta.current_sector !== undefined) {
        console.log('🎯 Current sector:', delta.current_sector + 1);
        for (let i = 0; i < 3; i++) {
            const sectorEl = document.getElementById(`sector${i + 1}Delta`);
            if (sectorEl) {
                const parent = sectorEl.parentElement;
                if (parent) {
                    if (i === delta.current_sector) {
                        parent.style.background = 'rgba(255,255,255,0.15)';
                        parent.style.borderLeft = '2px solid #4ade80';
                    } else {
                        parent.style.background = 'rgba(255,255,255,0.05)';
                        parent.style.borderLeft = 'none';
                    }
                }
            }
        }
    }
    
    console.log('✅ Ghost display update complete');
}

// Toggle TTS
function toggleTTS() {
    if (window.ttsCommentary) {
        const enabled = window.ttsCommentary.toggle();

        const btn = document.getElementById('ttsToggle');
        const text = document.getElementById('ttsToggleText');
        if (btn) btn.classList.toggle('active', enabled);
        if (text) text.textContent = enabled ? 'Voice On' : 'Voice Off';
        console.log(`🔊 TTS ${enabled ? 'enabled' : 'disabled'}`);
    }
}

// Close telemetry comparison
function closeTelemetryComparison() {
    const panel = document.getElementById('telemetryComparison');
    if (panel) {
        panel.style.display = 'none';
    }
    
    if (window.chronos) {
        window.chronos.showComparison = false;
        window.chronos.selectedDrivers = [];
        window.chronos.comparisonHistory = {
            speed: [],
            throttle: [],
            brake: [],
            gear: []
        };
        
        if (window.chronos.comparisonInterval) {
            clearInterval(window.chronos.comparisonInterval);
            window.chronos.comparisonInterval = null;
        }
        
        // Refresh leaderboard to clear selection
        if (window.chronos.currentTelemetry && window.chronos.currentTelemetry.frame) {
            window.chronos.updateLeaderboard(window.chronos.currentTelemetry.frame.drivers);
        }
        
        // Redraw track to clear selection highlights
        window.chronos.drawFrame();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNewFeatures);
} else {
    initializeNewFeatures();
}


// Display regulation context in UI
function displayRegulationContext(data) {
    const regulationsDisplay = document.getElementById('regulationsDisplay');
    if (!regulationsDisplay) {
        console.warn('⚠️ regulationsDisplay element not found');
        return;
    }
    
    if (!data || !data.regulations || data.regulations.length === 0) {
        console.log('📚 No regulations to display');
        return;
    }
    
    console.log(`📚 Displaying ${data.regulations.length} regulation(s)`);
    
    // Clear existing content
    regulationsDisplay.innerHTML = '';
    
    // Helper for basic markdown
    const parseMD = (text) => {
        if (!text) return '';
        return text
            .replace(/###\s*(.*?)(?=\n|$)/g, '<strong>$1</strong><br/>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br/>');
    };

    // Add each regulation
    data.regulations.forEach(reg => {
        const regItem = document.createElement('div');
        regItem.className = 'regulation-item' + (reg.active ? ' active' : '');
        
        regItem.innerHTML = `
            <div class="regulation-title">${reg.title}</div>
            <div class="regulation-content">${parseMD(reg.content)}</div>
            <div class="regulation-timestamp">${formatTime(data.timestamp)}</div>
        `;
        
        regulationsDisplay.appendChild(regItem);
        
        console.log(`✅ Displayed regulation: ${reg.title}`);
    });
    
    // Auto-remove after 30 seconds
    setTimeout(() => {
        const items = regulationsDisplay.querySelectorAll('.regulation-item.active');
        items.forEach(item => {
            item.classList.remove('active');
            item.style.opacity = '0.5';
        });
    }, 30000);
}

// Helper function to format time
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
