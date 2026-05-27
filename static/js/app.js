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
        
        // Display toggles
        this.showDrs = true;
        this.showWeather = true;
        this.showCharts = false;
        this.gapMode = 'interval'; // 'interval' or 'leader'
        
        // Track rendering
        this.trackScale = 1;
        this.trackOffsetX = 0;
        this.trackOffsetY = 0;
        
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
            this.seek(parseInt(e.target.value));
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
        window.addEventListener('resize', () => this.resizeCanvas());
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
        
        // Show all sections
        document.getElementById('raceInfoSection').style.display = 'block';
        document.getElementById('leaderboardSection').style.display = 'block';
        document.getElementById('raceControlSection').style.display = 'block';
        document.getElementById('aiCommentarySection').style.display = 'block';
        
        if (this.raceData.hasWeather) {
            document.getElementById('weatherSection').style.display = 'block';
        }
        
        // Start requesting analysis results periodically
        if (this.analysisInterval) {
            clearInterval(this.analysisInterval);
        }
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
    
    showRaceInfo() {
        document.getElementById('eventName').textContent = this.raceData.eventName;
        document.getElementById('circuitName').textContent = this.raceData.circuitName;
        document.getElementById('raceDate').textContent = this.raceData.date;
        document.getElementById('totalLaps').textContent = this.raceData.totalLaps;
        document.getElementById('sessionTotalLaps').textContent = this.raceData.totalLaps;
        
        document.getElementById('raceInfoSection').style.display = 'block';
        document.getElementById('leaderboardSection').style.display = 'block';
        document.getElementById('raceControlSection').style.display = 'block';
        document.getElementById('aiCommentarySection').style.display = 'block';
        
        if (this.raceData.hasWeather) {
            document.getElementById('weatherSection').style.display = 'block';
        }
    }
    
    initializeViewer() {
        document.getElementById('loadingScreen').style.display = 'none';
        this.canvas.style.display = 'block';
        document.getElementById('sessionInfo').style.display = 'block';
        document.getElementById('controls').style.display = 'flex';
        
        this.resizeCanvas();
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
            colors: Object.keys(data.driverColors || {}).length
        });
        
        this.currentTelemetry = data;
        this.updateUI(data);
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
        
        // Progress
        const progress = (data.frameIndex / data.totalFrames) * 100;
        document.getElementById('progressSlider').value = progress;
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
            
            item.addEventListener('click', (e) => {
                if (e.shiftKey) {
                    // Multi-select
                    const idx = this.selectedDrivers.indexOf(code);
                    if (idx > -1) {
                        this.selectedDrivers.splice(idx, 1);
                    } else {
                        this.selectedDrivers.push(code);
                    }
                } else {
                    // Single select
                    this.selectedDrivers = [code];
                }
                this.updateLeaderboard(drivers);
            });
            
            leaderboard.appendChild(item);
        });
    }
    
    updateRaceControl(messages) {
        const feed = document.getElementById('raceControlFeed');
        
        // Only show last 5 messages
        const recentMessages = messages.slice(-5);
        
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
        
        // Draw cars
        const drivers = this.currentTelemetry.frame.drivers;
        if (drivers) {
            Object.entries(drivers).forEach(([code, data]) => {
                this.drawCar(data.x, data.y, code, data);
            });
        }
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
        const xMin = Math.min(...track.x);
        const xMax = Math.max(...track.x);
        const yMin = Math.min(...track.y);
        const yMax = Math.max(...track.y);
        
        const trackWidth = xMax - xMin;
        const trackHeight = yMax - yMin;
        
        const scaleX = (this.canvas.width - padding * 2) / trackWidth;
        const scaleY = (this.canvas.height - padding * 2) / trackHeight;
        this.trackScale = Math.min(scaleX, scaleY);
        
        this.trackOffsetX = padding - xMin * this.trackScale + (this.canvas.width - trackWidth * this.trackScale) / 2;
        this.trackOffsetY = padding - yMin * this.trackScale + (this.canvas.height - trackHeight * this.trackScale) / 2;
        
        // Draw track outline
        this.ctx.strokeStyle = '#444';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        
        for (let i = 0; i < track.x.length; i++) {
            const x = track.x[i] * this.trackScale + this.trackOffsetX;
            const y = track.y[i] * this.trackScale + this.trackOffsetY;
            
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
                const x = track.innerX[i] * this.trackScale + this.trackOffsetX;
                const y = track.innerY[i] * this.trackScale + this.trackOffsetY;
                if (i === 0) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            this.ctx.stroke();
            
            // Outer bound
            this.ctx.beginPath();
            for (let i = 0; i < track.outerX.length; i++) {
                const x = track.outerX[i] * this.trackScale + this.trackOffsetX;
                const y = track.outerY[i] * this.trackScale + this.trackOffsetY;
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
                const x = track.x[i] * this.trackScale + this.trackOffsetX;
                const y = track.y[i] * this.trackScale + this.trackOffsetY;
                if (i === startIdx) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            this.ctx.stroke();
        });
    }
    
    drawFinishLine() {
        const finish = this.currentTelemetry.trackData.finishLine;
        const x = finish.x * this.trackScale + this.trackOffsetX;
        const y = finish.y * this.trackScale + this.trackOffsetY;
        
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
        const x = scData.x * this.trackScale + this.trackOffsetX;
        const y = scData.y * this.trackScale + this.trackOffsetY;
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
        const x = worldX * this.trackScale + this.trackOffsetX;
        const y = worldY * this.trackScale + this.trackOffsetY;
        
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
        const frameIndex = Math.floor((progress / 100) * this.raceData.totalFrames);
        this.socket.emit('seek', { frameIndex });
    }
    
    handlePlaybackStatus(data) {
        console.log('Playback status:', data);
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    new ChronosF1Enhanced();
});
