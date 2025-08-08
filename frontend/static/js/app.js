// Main JavaScript for CryptoEdge Pro
document.addEventListener('DOMContentLoaded', function() {
    // Application State
    const appState = {
        isConnected: false,
        isBotRunning: false,
        isDemo: false,
        activeStrategy: null,
        totalBudget: 0,
        availableBudget: 0,
        activeTradesCount: 0,
        maxTrades: 10,
        dailyPnL: 0,
        pnlPercent: 0,
        strategies: [],
        portfolio: {},
        tradeHistory: [],
        gpuStatus: {}
    };

    // DOM Elements
    const elements = {
        connectionStatus: document.getElementById('connection-status'),
        botStatus: document.getElementById('bot-status'),
        gpuStatus: document.getElementById('gpu-status'),
        loginSection: document.getElementById('login-section'),
        dashboardSection: document.getElementById('dashboard-section'),
        loginForm: document.getElementById('login-form'),
        demoLogin: document.getElementById('demo-login'),
        loginError: document.getElementById('login-error'),
        loginErrorMessage: document.getElementById('login-error-message'),
        startTrading: document.getElementById('start-trading'),
        stopTrading: document.getElementById('stop-trading'),
        benchmarkBtn: document.getElementById('benchmark-btn'),
        refreshData: document.getElementById('refresh-data'),
        totalBudget: document.getElementById('total-budget'),
        availableBudget: document.getElementById('available-budget'),
        availablePercent: document.getElementById('available-percent'),
        activeTrades: document.getElementById('active-trades'),
        dailyPnl: document.getElementById('daily-pnl'),
        pnlPercent: document.getElementById('pnl-percent'),
        gpuStatusContent: document.getElementById('gpu-status-content'),
        strategiesContent: document.getElementById('strategies-content'),
        portfolioContent: document.getElementById('portfolio-content'),
        tradeHistory: document.getElementById('trade-history'),
        recentActivities: document.getElementById('recent-activities'),
        topAssets: document.getElementById('top-assets'),
        logsContent: document.getElementById('logs-content'),
        mobileNavigation: document.getElementById('mobile-navigation'),
        manualTradeForm: document.getElementById('manual-trade-form'),
        loadingModal: new bootstrap.Modal(document.getElementById('loading-modal')),
        benchmarkModal: new bootstrap.Modal(document.getElementById('benchmark-modal')),
        alertContainer: document.getElementById('alert-container')
    };

    // Initialize charts lazily after login to reduce initial load
function initChartsWhenReady() {
    if (window.ApexCharts) {
        initializeCharts();
        return;
    }
    // Dynamically load ApexCharts only when needed
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/apexcharts@3.35.0/dist/apexcharts.min.js';
    script.defer = true;
    document.head.appendChild(script);

    const start = Date.now();
    const timerId = setInterval(() => {
        if (window.ApexCharts || Date.now() - start > 5000) {
            clearInterval(timerId);
            if (window.ApexCharts) {
                initializeCharts();
            }
        }
    }, 50);
}

// Event Listeners
    setupEventListeners();

    // Initialize WebSocket Connection (mock)
    initializeWebSocket();

    // Functions
    function setupEventListeners() {
        // Login Form
        elements.loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleLogin();
        });

        // Demo Login
        elements.demoLogin.addEventListener('click', function() {
            handleDemoLogin();
        });

        // Start Trading
        elements.startTrading.addEventListener('click', function() {
            startBot();
        });

        // Stop Trading
        elements.stopTrading.addEventListener('click', function() {
            stopBot();
        });

        // Benchmark Button
        elements.benchmarkBtn.addEventListener('click', function() {
            runBenchmark();
        });

        // Refresh Data
        elements.refreshData.addEventListener('click', function() {
            refreshData();
        });

        // Mobile Navigation
        if (elements.mobileNavigation) {
            elements.mobileNavigation.addEventListener('change', function() {
                const target = this.value;
                const tabElement = document.querySelector(`#${target}-pill`);
                if (tabElement) {
                    tabElement.click();
                }
            });
        }

        // Manual Trade Form
        if (elements.manualTradeForm) {
            elements.manualTradeForm.addEventListener('submit', function(e) {
                e.preventDefault();
                executeManualTrade();
            });
        }
    }

    function handleLogin() {
        const apiKey = document.getElementById('api-key').value;
        const apiSecret = document.getElementById('api-secret').value;
        const apiPassphrase = document.getElementById('api-passphrase').value;
        const sandbox = document.getElementById('sandbox').checked;

        if (!apiKey || !apiSecret || !apiPassphrase) {
            showLoginError('Please fill in all fields');
            return;
        }

        elements.loadingModal.show();

        // Simulate API call
        setTimeout(() => {
            elements.loadingModal.hide();
            connectToExchange({
                apiKey,
                apiSecret,
                apiPassphrase,
                sandbox
            });
        }, 1500);
    }

    function handleDemoLogin() {
        elements.loadingModal.show();
        
        // Simulate API call
        setTimeout(() => {
            elements.loadingModal.hide();
            connectToExchange({
                demo: true
            });
        }, 1000);
    }

    function showLoginError(message) {
        elements.loginErrorMessage.textContent = message;
        elements.loginError.style.display = 'block';
    }

    function connectToExchange(credentials) {
        // Update app state
        appState.isConnected = true;
        appState.isDemo = !!credentials.demo;

        // Update UI
        updateConnectionStatus(true);
        elements.loginSection.style.display = 'none';
        elements.dashboardSection.style.display = 'block';
        
        // Initialize charts once needed
        initChartsWhenReady();

        // Initialize data
        loadMockData();
        
        // Add connection activity
        addActivity({
            type: 'connection',
            title: appState.isDemo ? 'Demo Mode Activated' : 'Connected to Exchange',
            message: appState.isDemo ? 'Demo mode has been activated with simulated trading capabilities.' : 'Successfully established connection to exchange API',
            time: 'Just now'
        });

        // Show notification
        showAlert({
            type: 'success',
            title: appState.isDemo ? 'Demo Mode Active' : 'Connection Successful',
            message: appState.isDemo ? 'You are now in demo mode with simulated trading.' : 'Successfully connected to exchange'
        });
    }

    function updateConnectionStatus(isConnected) {
        if (isConnected) {
            elements.connectionStatus.className = 'status-badge status-success';
            elements.connectionStatus.innerHTML = '<i class="fas fa-wifi me-1"></i> Connected';
        } else {
            elements.connectionStatus.className = 'status-badge status-danger';
            elements.connectionStatus.innerHTML = '<i class="fas fa-wifi me-1"></i> Disconnected';
        }
    }

    function updateBotStatus(isRunning) {
        if (isRunning) {
            elements.botStatus.className = 'status-badge status-success';
            elements.botStatus.innerHTML = '<i class="fas fa-power-off me-1"></i> Running';
            elements.startTrading.style.display = 'none';
            elements.stopTrading.style.display = 'inline-block';
        } else {
            elements.botStatus.className = 'status-badge status-secondary';
            elements.botStatus.innerHTML = '<i class="fas fa-power-off me-1"></i> Stopped';
            elements.startTrading.style.display = 'inline-block';
            elements.stopTrading.style.display = 'none';
        }
    }

    function startBot() {
        elements.loadingModal.show();
        
        // Simulate API call
        setTimeout(() => {
            elements.loadingModal.hide();
            
            // Update app state
            appState.isBotRunning = true;
            
            // Update UI
            updateBotStatus(true);
            
            // Add activity
            addActivity({
                type: 'bot',
                title: 'Bot Started',
                message: `Trading bot started successfully with ${appState.strategies.filter(s => s.isActive).length} active strategies`,
                time: 'Just now'
            });
            
            // Show notification
            showAlert({
                type: 'success',
                title: 'Bot Started',
                message: 'Trading bot is now running and monitoring the market'
            });
        }, 1500);
    }

    function stopBot() {
        elements.loadingModal.show();
        
        // Simulate API call
        setTimeout(() => {
            elements.loadingModal.hide();
            
            // Update app state
            appState.isBotRunning = false;
            
            // Update UI
            updateBotStatus(false);
            
            // Add activity
            addActivity({
                type: 'bot',
                title: 'Bot Stopped',
                message: 'Trading bot has been stopped successfully',
                time: 'Just now'
            });
            
            // Show notification
            showAlert({
                type: 'warning',
                title: 'Bot Stopped',
                message: 'Trading bot has been stopped'
            });
        }, 1000);
    }

    function runBenchmark() {
        elements.loadingModal.show();
        
        // Simulate API call
        setTimeout(() => {
            elements.loadingModal.hide();
            
            // Generate mock benchmark results
            const benchmarkResults = {
                gpuModel: 'NVIDIA GeForce RTX 3080',
                cpuModel: 'AMD Ryzen 9 5900X',
                memoryUsage: '4.2 GB / 16 GB',
                results: [
                    { test: 'RSI Calculation (1000 assets)', cpu: 2450, gpu: 64, speedup: '38.2x' },
                    { test: 'Moving Average (5000 datapoints)', cpu: 1850, gpu: 78, speedup: '23.7x' },
                    { test: 'Volatility Analysis', cpu: 3200, gpu: 194, speedup: '16.5x' },
                    { test: 'Multi-Strategy Optimization', cpu: 5600, gpu: 248, speedup: '22.6x' }
                ]
            };
            
            // Display benchmark results
            displayBenchmarkResults(benchmarkResults);
            
            // Show benchmark modal
            elements.benchmarkModal.show();
        }, 3000);
    }

    function displayBenchmarkResults(results) {
        const container = document.getElementById('benchmark-results-container');
        
        if (!container) return;
        
        let html = `
            <div class="mb-4">
                <h6 class="text-muted mb-3">System Information</h6>
                <div class="row">
                    <div class="col-md-6">
                        <div class="d-flex align-items-center mb-3">
                            <div class="icon-circle primary-gradient me-3">
                                <i class="fas fa-microchip text-white"></i>
                            </div>
                            <div>
                                <h6 class="mb-0">${results.gpuModel}</h6>
                                <small class="text-muted">GPU</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex align-items-center mb-3">
                            <div class="icon-circle info-gradient me-3">
                                <i class="fas fa-memory text-white"></i>
                            </div>
                            <div>
                                <h6 class="mb-0">${results.cpuModel}</h6>
                                <small class="text-muted">CPU</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <div class="icon-circle success-gradient me-3">
                        <i class="fas fa-memory text-white"></i>
                    </div>
                    <div>
                        <h6 class="mb-0">${results.memoryUsage}</h6>
                        <small class="text-muted">Memory Usage</small>
                    </div>
                </div>
            </div>
            
            <h6 class="text-muted mb-3">Performance Comparison (milliseconds - lower is better)</h6>
            
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Test</th>
                            <th class="text-center">CPU Time</th>
                            <th class="text-center">GPU Time</th>
                            <th class="text-center">Speedup</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        results.results.forEach(result => {
            html += `
                <tr>
                    <td>${result.test}</td>
                    <td class="text-center">${result.cpu} ms</td>
                    <td class="text-center">${result.gpu} ms</td>
                    <td class="text-center"><span class="badge bg-success">${result.speedup}</span></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
            
            <div class="text-center mt-4">
                <div class="alert alert-success">
                    <i class="fas fa-bolt me-2"></i> GPU acceleration is working optimally on your system
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    function refreshData() {
        elements.loadingModal.show();
        
        // Simulate API call
        setTimeout(() => {
            elements.loadingModal.hide();
            loadMockData();
            
            // Show notification
            showAlert({
                type: 'info',
                title: 'Data Refreshed',
                message: 'All trading data has been refreshed'
            });
        }, 1000);
    }

    function loadMockData() {
        // Mock data for testing UI
        appState.totalBudget = 25000 + Math.random() * 5000;
        appState.availableBudget = appState.totalBudget * (0.3 + Math.random() * 0.4);
        appState.activeTradesCount = Math.floor(Math.random() * appState.maxTrades);
        appState.dailyPnL = Math.random() > 0.3 ? Math.random() * 800 : -Math.random() * 300;
        appState.pnlPercent = (appState.dailyPnL / appState.totalBudget) * 100;
        
        // Load GPU status
        loadGpuStatus();
        
        // Load strategies
        loadStrategies();
        
        // Load portfolio
        loadPortfolio();
        
        // Load trade history
        loadTradeHistory();
        
        // Load logs
        loadLogs();
        
        // Update UI
        updateDashboardData();
    }

    function loadGpuStatus() {
        appState.gpuStatus = {
            model: 'NVIDIA GeForce RTX 3080',
            memory: {
                total: 10240,
                used: 2048
            },
            temperature: 65,
            utilization: 75,
            cores: 8704,
            isActive: true
        };
        
        // Update GPU Status UI
        updateGpuStatusUI();
    }

    function updateGpuStatusUI() {
        if (!elements.gpuStatusContent) return;
        
        const memoryUsedPercent = (appState.gpuStatus.memory.used / appState.gpuStatus.memory.total) * 100;
        const memoryUsedGB = appState.gpuStatus.memory.used / 1024;
        const memoryTotalGB = appState.gpuStatus.memory.total / 1024;
        
        // Update GPU Status indicator
        if (appState.gpuStatus.isActive) {
            elements.gpuStatus.className = 'status-badge status-success';
            elements.gpuStatus.innerHTML = '<i class="fas fa-microchip me-1"></i> GPU Active';
        } else {
            elements.gpuStatus.className = 'status-badge status-warning';
            elements.gpuStatus.innerHTML = '<i class="fas fa-microchip me-1"></i> GPU Inactive';
        }
        
        // Update GPU Status content
        elements.gpuStatusContent.innerHTML = `
            <div class="col-lg-4 col-md-6">
                <div class="card bg-light mb-3">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between">
                            <h6 class="mb-1">GPU Model</h6>
                            <span class="badge bg-primary">NVIDIA</span>
                        </div>
                        <p class="mb-0 fs-sm">${appState.gpuStatus.model}</p>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-md-6">
                <div class="card bg-light mb-3">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between">
                            <h6 class="mb-1">Memory Usage</h6>
                            <span class="badge bg-${memoryUsedPercent > 80 ? 'warning' : 'success'}">${memoryUsedPercent.toFixed(0)}%</span>
                        </div>
                        <div class="progress mb-2" style="height: 6px;">
                            <div class="progress-bar bg-${memoryUsedPercent > 80 ? 'warning' : 'success'}" role="progressbar" style="width: ${memoryUsedPercent}%"></div>
                        </div>
                        <p class="mb-0 fs-sm">${memoryUsedGB.toFixed(1)} GB / ${memoryTotalGB.toFixed(1)} GB</p>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-md-6">
                <div class="card bg-light mb-3">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between">
                            <h6 class="mb-1">Temperature</h6>
                            <span class="badge bg-${appState.gpuStatus.temperature > 80 ? 'danger' : appState.gpuStatus.temperature > 70 ? 'warning' : 'success'}">${appState.gpuStatus.temperature}°C</span>
                        </div>
                        <div class="progress mb-2" style="height: 6px;">
                            <div class="progress-bar bg-${appState.gpuStatus.temperature > 80 ? 'danger' : appState.gpuStatus.temperature > 70 ? 'warning' : 'success'}" role="progressbar" style="width: ${(appState.gpuStatus.temperature / 100) * 100}%"></div>
                        </div>
                        <p class="mb-0 fs-sm">Optimal temperature range</p>
                    </div>
                </div>
            </div>
        `;
    }

    function loadStrategies() {
        appState.strategies = [
            {
                id: 'gpu_rsi_strategy',
                name: 'GPU RSI Strategy',
                description: 'RSI-based trading with GPU acceleration for faster processing of multiple assets simultaneously.',
                type: 'technical',
                isActive: true,
                allocation: 25,
                performance: {
                    daily: 1.2,
                    weekly: 5.8,
                    monthly: 12.3
                },
                pairs: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
                settings: {
                    rsiPeriod: 14,
                    oversold: 30,
                    overbought: 70,
                    timeframe: '15m'
                }
            },
            {
                id: 'gpu_volatility_strategy',
                name: 'GPU Volatility Breakout',
                description: 'Volatility-based breakout detection accelerated with GPU computation.',
                type: 'volatility',
                isActive: true,
                allocation: 20,
                performance: {
                    daily: 0.8,
                    weekly: 3.2,
                    monthly: 9.7
                },
                pairs: ['BTC/USDT', 'ETH/USDT', 'ADA/USDT'],
                settings: {
                    period: 20,
                    deviationMultiplier: 2.5,
                    timeframe: '1h'
                }
            },
            {
                id: 'gpu_ma_strategy',
                name: 'GPU Moving Average Cross',
                description: 'Moving average crossover strategy optimized for GPU calculations.',
                type: 'trend',
                isActive: false,
                allocation: 15,
                performance: {
                    daily: -0.3,
                    weekly: 2.1,
                    monthly: 7.5
                },
                pairs: ['BTC/USDT', 'ETH/USDT'],
                settings: {
                    fastPeriod: 10,
                    slowPeriod: 50,
                    timeframe: '30m'
                }
            },
            {
                id: 'pump_detection',
                name: 'Pump Detection',
                description: 'Identifies and capitalizes on sudden market pumps using GPU-accelerated pattern recognition.',
                type: 'momentum',
                isActive: true,
                allocation: 15,
                performance: {
                    daily: 2.1,
                    weekly: 7.3,
                    monthly: 22.5
                },
                pairs: ['BTC/USDT', 'SOL/USDT', 'DOGE/USDT'],
                settings: {
                    volumeThreshold: 2.5,
                    priceChangeThreshold: 3.0,
                    timeframe: '5m'
                }
            }
        ];
        
        // Update Strategies UI
        updateStrategiesUI();
    }

    function updateStrategiesUI() {
        if (!elements.strategiesContent) return;
        
        let html = '';
        
        appState.strategies.forEach(strategy => {
            const performanceClass = strategy.performance.daily >= 0 ? 'success' : 'danger';
            const performanceIcon = strategy.performance.daily >= 0 ? 'arrow-up' : 'arrow-down';
            
            html += `
                <div class="col-lg-6">
                    <div class="card glass-card strategy-card ${strategy.isActive ? 'active' : ''}">
                        <div class="card-body">
                            <span class="strategy-status-badge ${strategy.isActive ? 'bg-success-soft text-success' : 'bg-secondary text-white'}">
                                ${strategy.isActive ? 'Active' : 'Inactive'}
                            </span>
                            
                            <div class="d-flex align-items-center mb-3">
                                <div class="icon-circle primary-gradient me-3">
                                    <i class="fas fa-${strategy.type === 'technical' ? 'chart-line' : strategy.type === 'volatility' ? 'bolt' : strategy.type === 'trend' ? 'chart-area' : 'rocket'} text-white"></i>
                                </div>
                                <div>
                                    <h5 class="mb-0">${strategy.name}</h5>
                                    <span class="badge bg-primary-soft text-primary">${strategy.type.charAt(0).toUpperCase() + strategy.type.slice(1)}</span>
                                </div>
                            </div>
                            
                            <p class="text-muted mb-3">${strategy.description}</p>
                            
                            <div class="row g-3 mb-3">
                                <div class="col-4">
                                    <div class="text-center">
                                        <h6 class="text-${performanceClass} mb-0">
                                            <i class="fas fa-${performanceIcon} me-1"></i> ${strategy.performance.daily.toFixed(1)}%
                                        </h6>
                                        <small class="text-muted">24h</small>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="text-center">
                                        <h6 class="mb-0">${strategy.performance.weekly.toFixed(1)}%</h6>
                                        <small class="text-muted">7d</small>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="text-center">
                                        <h6 class="mb-0">${strategy.performance.monthly.toFixed(1)}%</h6>
                                        <small class="text-muted">30d</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="badge bg-light text-dark me-1">${strategy.pairs.length} pairs</span>
                                    <span class="badge bg-light text-dark">${strategy.allocation}% allocation</span>
                                </div>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="strategy-${strategy.id}" ${strategy.isActive ? 'checked' : ''}>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        elements.strategiesContent.innerHTML = html;
        
        // Add event listeners to strategy switches
        appState.strategies.forEach(strategy => {
            const checkbox = document.getElementById(`strategy-${strategy.id}`);
            if (checkbox) {
                checkbox.addEventListener('change', function() {
                    toggleStrategy(strategy.id, this.checked);
                });
            }
        });
    }

    function toggleStrategy(strategyId, isActive) {
        // Find strategy in app state
        const strategy = appState.strategies.find(s => s.id === strategyId);
        if (strategy) {
            strategy.isActive = isActive;
            
            // Show notification
            showAlert({
                type: isActive ? 'success' : 'warning',
                title: isActive ? 'Strategy Activated' : 'Strategy Deactivated',
                message: `${strategy.name} has been ${isActive ? 'activated' : 'deactivated'}`
            });
            
            // Add activity
            addActivity({
                type: 'strategy',
                title: isActive ? 'Strategy Activated' : 'Strategy Deactivated',
                message: `${strategy.name} has been ${isActive ? 'activated' : 'deactivated'}`,
                time: 'Just now'
            });
        }
    }

    function loadPortfolio() {
        appState.portfolio = {
            total: appState.totalBudget,
            available: appState.availableBudget,
            assets: [
                { symbol: 'USDT', name: 'Tether', amount: appState.availableBudget, value: appState.availableBudget, allocation: (appState.availableBudget / appState.totalBudget) * 100, change24h: 0 },
                { symbol: 'BTC', name: 'Bitcoin', amount: 0.12, value: 0.12 * 36782.14, allocation: (0.12 * 36782.14 / appState.totalBudget) * 100, change24h: 2.4 },
                { symbol: 'ETH', name: 'Ethereum', amount: 2.5, value: 2.5 * 2415.30, allocation: (2.5 * 2415.30 / appState.totalBudget) * 100, change24h: 3.8 },
                { symbol: 'SOL', name: 'Solana', amount: 15, value: 15 * 104.52, allocation: (15 * 104.52 / appState.totalBudget) * 100, change24h: 5.2 }
            ]
        };
        
        // Update Portfolio UI
        updatePortfolioUI();
    }

    function updatePortfolioUI() {
        if (!elements.portfolioContent) return;
        
        let html = `
            <div class="table-responsive">
                <table class="table align-middle">
                    <thead>
                        <tr>
                            <th>Asset</th>
                            <th>Amount</th>
                            <th>Value</th>
                            <th>Change (24h)</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        appState.portfolio.assets.forEach(asset => {
            const changeClass = asset.change24h > 0 ? 'success' : asset.change24h < 0 ? 'danger' : 'secondary';
            const changeIcon = asset.change24h > 0 ? 'arrow-up' : asset.change24h < 0 ? 'arrow-down' : 'minus';
            
            html += `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="coin-icon ${asset.symbol.toLowerCase()} me-2"></div>
                            <div>
                                <h6 class="mb-0">${asset.name}</h6>
                                <small class="text-muted">${asset.symbol}</small>
                            </div>
                        </div>
                    </td>
                    <td>${asset.amount.toFixed(asset.symbol === 'USDT' ? 2 : 6)} ${asset.symbol}</td>
                    <td>$${asset.value.toFixed(2)}</td>
                    <td>
                        <span class="text-${changeClass}">
                            <i class="fas fa-${changeIcon} me-1"></i> ${Math.abs(asset.change24h).toFixed(1)}%
                        </span>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        elements.portfolioContent.innerHTML = html;
    }

    function loadTradeHistory() {
        const trades = [
            { 
                id: 'T12345',
                pair: 'BTC/USDT',
                type: 'buy',
                amount: 0.005,
                price: 36782.14,
                value: 0.005 * 36782.14,
                time: '10:23:45',
                strategy: 'GPU RSI Strategy',
                status: 'completed'
            },
            { 
                id: 'T12346',
                pair: 'SOL/USDT',
                type: 'buy',
                amount: 5,
                price: 104.52,
                value: 5 * 104.52,
                time: '09:45:30',
                strategy: 'GPU Volatility Breakout',
                status: 'completed'
            },
            { 
                id: 'T12347',
                pair: 'ETH/USDT',
                type: 'sell',
                amount: 0.5,
                price: 2415.30,
                value: 0.5 * 2415.30,
                time: '08:15:12',
                strategy: 'GPU RSI Strategy',
                status: 'completed'
            },
            { 
                id: 'T12348',
                pair: 'ADA/USDT',
                type: 'buy',
                amount: 100,
                price: 0.52,
                value: 100 * 0.52,
                time: 'Yesterday',
                strategy: 'Manual Decision',
                status: 'completed'
            }
        ];
        
        appState.tradeHistory = trades;
        
        // Update Trade History UI
        updateTradeHistoryUI();
    }

    function updateTradeHistoryUI() {
        if (!elements.tradeHistory) return;
        
        let html = `
            <table class="table align-middle mb-0">
                <thead>
                    <tr>
                        <th>Pair</th>
                        <th>Type</th>
                        <th>Price</th>
                        <th>Amount</th>
                        <th>Value</th>
                        <th>Time</th>
                        <th>Strategy</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        appState.tradeHistory.forEach(trade => {
            const typeClass = trade.type === 'buy' ? 'success' : 'danger';
            const typeIcon = trade.type === 'buy' ? 'arrow-up' : 'arrow-down';
            
            html += `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="coin-icon ${trade.pair.split('/')[0].toLowerCase()} me-2"></div>
                            <span>${trade.pair}</span>
                        </div>
                    </td>
                    <td>
                        <span class="badge bg-${typeClass}-soft text-${typeClass}">
                            <i class="fas fa-${typeIcon} me-1"></i> ${trade.type.toUpperCase()}
                        </span>
                    </td>
                    <td>$${trade.price.toFixed(2)}</td>
                    <td>${trade.amount} ${trade.pair.split('/')[0]}</td>
                    <td>$${trade.value.toFixed(2)}</td>
                    <td>${trade.time}</td>
                    <td><span class="badge bg-primary-soft text-primary">${trade.strategy}</span></td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        elements.tradeHistory.innerHTML = html;
    }

    function loadLogs() {
        if (!elements.logsContent) return;
        
        const logs = [
            { type: 'info', message: 'Trading bot started successfully', timestamp: '2023-05-15 10:24:35' },
            { type: 'info', message: 'Connected to exchange API', timestamp: '2023-05-15 10:24:33' },
            { type: 'info', message: 'GPU acceleration enabled', timestamp: '2023-05-15 10:24:30' },
            { type: 'warning', message: 'Market volatility detected for BTC/USDT', timestamp: '2023-05-15 10:20:15' },
            { type: 'success', message: 'Order executed: Buy 0.005 BTC at $36,782.14', timestamp: '2023-05-15 10:15:22' },
            { type: 'info', message: 'RSI strategy triggered buy signal for BTC/USDT', timestamp: '2023-05-15 10:15:20' },
            { type: 'info', message: 'Fetched market data for 10 trading pairs', timestamp: '2023-05-15 10:10:00' },
            { type: 'error', message: 'Failed to process market data for XRP/USDT', timestamp: '2023-05-15 10:05:30' },
            { type: 'success', message: 'Order executed: Buy 5 SOL at $104.52', timestamp: '2023-05-15 09:45:30' },
            { type: 'warning', message: 'API rate limit at 80% usage', timestamp: '2023-05-15 09:30:00' },
            { type: 'info', message: 'System initialized with 4 active strategies', timestamp: '2023-05-15 09:00:00' }
        ];
        
        let html = '';
        
        logs.forEach(log => {
            html += `
                <div class="log-entry">
                    <span class="log-timestamp">[${log.timestamp}]</span>
                    <span class="log-${log.type}">[${log.type.toUpperCase()}]</span>
                    <span>${log.message}</span>
                </div>
            `;
        });
        
        elements.logsContent.innerHTML = html;
    }

    function updateDashboardData() {
        // Update budget and statistics
        elements.totalBudget.textContent = `$${formatNumber(appState.totalBudget.toFixed(2))}`;
        elements.availableBudget.textContent = `$${formatNumber(appState.availableBudget.toFixed(2))}`;
        elements.availablePercent.textContent = `${((appState.availableBudget / appState.totalBudget) * 100).toFixed(0)}% of total`;
        
        // Update active trades
        elements.activeTrades.textContent = `${appState.activeTradesCount}/${appState.maxTrades}`;
        const activeTradesProgress = document.querySelector('#active-trades').nextElementSibling.querySelector('.progress-bar');
        if (activeTradesProgress) {
            activeTradesProgress.style.width = `${(appState.activeTradesCount / appState.maxTrades) * 100}%`;
        }
        
        // Update PnL
        elements.dailyPnl.textContent = `$${Math.abs(appState.dailyPnL).toFixed(2)}`;
        elements.pnlPercent.textContent = `${appState.pnlPercent >= 0 ? '+' : '-'}${Math.abs(appState.pnlPercent).toFixed(2)}%`;
        elements.pnlPercent.className = appState.pnlPercent >= 0 ? 'text-success' : 'text-danger';
    }

    function executeManualTrade() {
        const symbol = document.getElementById('trade-symbol').value;
        const side = document.querySelector('input[name="trade-side"]:checked').value;
        const amount = parseFloat(document.getElementById('trade-amount').value);
        const strategy = document.getElementById('trade-strategy').value;
        
        if (!symbol || !side || isNaN(amount) || amount <= 0) {
            showAlert({
                type: 'danger',
                title: 'Error',
                message: 'Please fill in all fields correctly'
            });
            return;
        }
        
        elements.loadingModal.show();
        
        // Simulate API call
        setTimeout(() => {
            elements.loadingModal.hide();
            
            // Add new trade to history
            const trade = {
                id: 'T' + Math.floor(Math.random() * 100000),
                pair: symbol,
                type: side,
                amount: side === 'buy' ? amount / 36782.14 : 0.001,
                price: 36782.14,
                value: amount,
                time: 'Just now',
                strategy: strategy === 'manual' ? 'Manual Decision' : document.getElementById('trade-strategy').options[document.getElementById('trade-strategy').selectedIndex].text,
                status: 'completed'
            };
            
            appState.tradeHistory.unshift(trade);
            
            // Update trade history UI
            updateTradeHistoryUI();
            
            // Add activity
            addActivity({
                type: 'trade',
                title: 'Trade Executed',
                message: `${symbol} - ${side === 'buy' ? 'Bought' : 'Sold'} ${trade.amount.toFixed(6)} at $${trade.price.toFixed(2)}`,
                time: 'Just now'
            });
            
            // Show notification
            showAlert({
                type: 'success',
                title: 'Trade Executed',
                message: `${side === 'buy' ? 'Bought' : 'Sold'} ${trade.amount.toFixed(6)} ${symbol.split('/')[0]} at $${trade.price.toFixed(2)}`
            });
        }, 2000);
    }

    function addActivity(activity) {
        const dotClass = activity.type === 'connection' ? 'primary' : 
                         activity.type === 'bot' ? 'success' : 
                         activity.type === 'trade' ? 'warning' : 
                         activity.type === 'strategy' ? 'info' : 'secondary';
                         
        const html = `
            <div class="activity-item">
                <div class="activity-dot bg-${dotClass}"></div>
                <div class="activity-content">
                    <div class="d-flex justify-content-between">
                        <h6 class="mb-1">${activity.title}</h6>
                        <small class="text-muted">${activity.time}</small>
                    </div>
                    <p class="mb-0 text-muted fs-sm">${activity.message}</p>
                </div>
            </div>
        `;
        
        // Add at the beginning
        if (elements.recentActivities) {
            elements.recentActivities.innerHTML = html + elements.recentActivities.innerHTML;
        }
    }

    function showAlert(alert) {
        const id = 'alert-' + Date.now();
        const html = `
            <div id="${id}" class="alert alert-${alert.type} alert-dismissible fade show">
                <div class="d-flex align-items-center">
                    <i class="fas fa-${alert.type === 'success' ? 'check-circle' : 
                                     alert.type === 'danger' ? 'exclamation-circle' : 
                                     alert.type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                    <div>
                        <strong>${alert.title}</strong>
                        <div>${alert.message}</div>
                    </div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        elements.alertContainer.innerHTML += html;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alertElement = document.getElementById(id);
            if (alertElement) {
                alertElement.classList.remove('show');
                setTimeout(() => {
                    alertElement.remove();
                }, 500);
            }
        }, 5000);
    }

    function formatNumber(number) {
        return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    function initializeWebSocket() {
        // This is a mock websocket implementation
        console.log('WebSocket initialized');
        
        // Simulate connection after 2 seconds
        setTimeout(() => {
            // Sometimes we'll simulate a disconnection for testing
            if (Math.random() > 0.8) {
                updateConnectionStatus(false);
                
                showAlert({
                    type: 'danger',
                    title: 'Connection Lost',
                    message: 'Connection to the exchange has been lost. Attempting to reconnect...'
                });
                
                // Simulate reconnection after 3 seconds
                setTimeout(() => {
                    updateConnectionStatus(true);
                    
                    showAlert({
                        type: 'success',
                        title: 'Connection Restored',
                        message: 'Successfully reconnected to the exchange'
                    });
                }, 3000);
            }
        }, 2000);
    }

    function initializeCharts() {
        // Performance Chart
        if (document.getElementById('performance-chart')) {
            const performanceChart = new ApexCharts(document.getElementById('performance-chart'), {
                series: [{
                    name: 'Portfolio Value',
                    data: [22500, 23100, 23400, 23200, 23800, 24500, 25000, 24800, 25300, 25200, 25800, 26200]
                }],
                chart: {
                    type: 'area',
                    height: 300,
                    toolbar: {
                        show: false
                    },
                    zoom: {
                        enabled: false
                    }
                },
                dataLabels: {
                    enabled: false
                },
                stroke: {
                    curve: 'smooth',
                    width: 3
                },
                colors: ['#3a86ff'],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.7,
                        opacityTo: 0.2,
                        stops: [0, 90, 100]
                    }
                },
                xaxis: {
                    categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    labels: {
                        style: {
                            colors: '#999'
                        }
                    }
                },
                yaxis: {
                    labels: {
                        formatter: function(val) {
                            return '$' + val.toFixed(0);
                        },
                        style: {
                            colors: '#999'
                        }
                    }
                },
                tooltip: {
                    x: {
                        show: false
                    },
                    y: {
                        formatter: function(val) {
                            return '$' + val.toFixed(2);
                        }
                    },
                    theme: 'dark'
                }
            });
            
            performanceChart.render();
        }
        
        // Strategy Performance Chart
        if (document.getElementById('strategy-performance-chart')) {
            const strategyPerformanceChart = new ApexCharts(document.getElementById('strategy-performance-chart'), {
                series: [{
                    name: 'GPU RSI Strategy',
                    data: [3.2, 2.8, -1.2, 1.5, 2.2, 3.1, 1.8]
                }, {
                    name: 'GPU Volatility Breakout',
                    data: [2.1, 1.5, -0.8, 2.8, 1.2, -0.5, 0.9]
                }, {
                    name: 'Pump Detection',
                    data: [4.5, 3.2, -2.1, 3.9, 2.8, 1.5, 2.2]
                }],
                chart: {
                    type: 'bar',
                    height: 300,
                    stacked: false,
                    toolbar: {
                        show: false
                    }
                },
                plotOptions: {
                    bar: {
                        horizontal: false,
                        columnWidth: '65%',
                        borderRadius: 5
                    },
                },
                dataLabels: {
                    enabled: false
                },
                stroke: {
                    show: true,
                    width: 2,
                    colors: ['transparent']
                },
                colors: ['#3a86ff', '#ffbe0b', '#38b000'],
                xaxis: {
                    categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    labels: {
                        style: {
                            colors: '#999'
                        }
                    }
                },
                yaxis: {
                    title: {
                        text: 'Daily Return (%)'
                    },
                    labels: {
                        formatter: function(val) {
                            return val.toFixed(1) + '%';
                        },
                        style: {
                            colors: '#999'
                        }
                    }
                },
                fill: {
                    opacity: 1
                },
                tooltip: {
                    y: {
                        formatter: function(val) {
                            return val.toFixed(2) + '%';
                        }
                    },
                    theme: 'dark'
                }
            });
            
            strategyPerformanceChart.render();
        }
        
        // Strategy Comparison Chart
        if (document.getElementById('strategy-comparison-chart')) {
            const strategyComparisonChart = new ApexCharts(document.getElementById('strategy-comparison-chart'), {
                series: [{
                    name: 'Return (%)',
                    data: [12.3, 9.7, 7.5, 22.5]
                }],
                chart: {
                    type: 'bar',
                    height: 350,
                    toolbar: {
                        show: false
                    }
                },
                plotOptions: {
                    bar: {
                        borderRadius: 8,
                        columnWidth: '60%',
                        distributed: true,
                    }
                },
                dataLabels: {
                    enabled: false
                },
                legend: {
                    show: false
                },
                colors: ['#3a86ff', '#ffbe0b', '#38b000', '#ff5a5f'],
                xaxis: {
                    categories: [
                        'GPU RSI Strategy',
                        'GPU Volatility Breakout',
                        'GPU Moving Average Cross',
                        'Pump Detection'
                    ],
                    labels: {
                        style: {
                            colors: '#999',
                            fontSize: '12px'
                        }
                    }
                },
                yaxis: {
                    title: {
                        text: 'Monthly Return (%)'
                    },
                    labels: {
                        formatter: function(val) {
                            return val.toFixed(1) + '%';
                        },
                        style: {
                            colors: '#999'
                        }
                    }
                },
                tooltip: {
                    y: {
                        formatter: function(val) {
                            return val.toFixed(2) + '%';
                        }
                    },
                    theme: 'dark'
                }
            });
            
            strategyComparisonChart.render();
        }
        
        // GPU Gains Chart
        if (document.getElementById('gpu-gains-chart')) {
            const gpuGainsChart = new ApexCharts(document.getElementById('gpu-gains-chart'), {
                series: [{
                    name: 'Speedup Factor',
                    data: [38.2, 23.7, 16.5, 22.6]
                }],
                chart: {
                    type: 'radar',
                    height: 250,
                    toolbar: {
                        show: false
                    }
                },
                dataLabels: {
                    enabled: true,
                    background: {
                        enabled: true,
                        borderRadius: 2,
                    }
                },
                plotOptions: {
                    radar: {
                        size: 140,
                        polygons: {
                            strokeColors: '#e9e9e9',
                            fill: {
                                colors: ['#f8f8f8', '#fff']
                            }
                        }
                    }
                },
                colors: ['#3a86ff'],
                markers: {
                    size: 5,
                    colors: ['#fff'],
                    strokeColor: '#3a86ff',
                    strokeWidth: 2,
                },
                tooltip: {
                    y: {
                        formatter: function(val) {
                            return val.toFixed(1) + 'x faster';
                        }
                    },
                    theme: 'dark'
                },
                xaxis: {
                    categories: ['RSI Calculation', 'Moving Average', 'Volatility Analysis', 'Multi-Strategy']
                },
                yaxis: {
                    show: false
                }
            });
            
            gpuGainsChart.render();
        }
        
        // Portfolio Chart
        if (document.getElementById('portfolio-chart')) {
            const portfolioChart = new ApexCharts(document.getElementById('portfolio-chart'), {
                series: [40, 25, 15, 20],
                chart: {
                    type: 'donut',
                    height: 350
                },
                labels: ['USDT', 'BTC', 'ETH', 'SOL'],
                colors: ['#6c757d', '#f7931a', '#627eea', '#00aee9'],
                plotOptions: {
                    pie: {
                        donut: {
                            size: '55%',
                            labels: {
                                show: true,
                                total: {
                                    show: true,
                                    label: 'Total Value',
                                    formatter: function(w) {
                                        return '$' + formatNumber(appState.totalBudget.toFixed(2));
                                    }
                                }
                            }
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    formatter: function(val) {
                        return val.toFixed(1) + '%';
                    }
                },
                legend: {
                    position: 'bottom',
                    offsetY: 0
                },
                tooltip: {
                    y: {
                        formatter: function(val) {
                            return val.toFixed(1) + '%';
                        }
                    },
                    theme: 'dark'
                },
                responsive: [{
                    breakpoint: 480,
                    options: {
                        chart: {
                            height: 300
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }]
            });
            
            portfolioChart.render();
        }
        
        // Portfolio Performance Chart
        if (document.getElementById('portfolio-performance-chart')) {
            const portfolioPerformanceChart = new ApexCharts(document.getElementById('portfolio-performance-chart'), {
                series: [{
                    name: 'Portfolio Value',
                    data: [24800, 24900, 24850, 24700, 24900, 25100, 25000, 24950, 25200, 25400, 25300, 25500, 25450, 25600, 25650, 25800, 25900, 26100, 26000, 26200, 25800, 25900, 26200, 26500]
                }],
                chart: {
                    type: 'line',
                    height: 350,
                    toolbar: {
                        show: false
                    },
                    zoom: {
                        enabled: false
                    }
                },
                dataLabels: {
                    enabled: false
                },
                stroke: {
                    curve: 'smooth',
                    width: 3
                },
                colors: ['#38b000'],
                markers: {
                    size: 0,
                    hover: {
                        size: 5
                    }
                },
                grid: {
                    show: true,
                    borderColor: '#f1f1f1',
                    xaxis: {
                        lines: {
                            show: false
                        }
                    }
                },
                xaxis: {
                    categories: Array.from({ length: 24 }, (_, i) => (i).toString() + ':00'),
                    labels: {
                        style: {
                            colors: '#999'
                        }
                    }
                },
                yaxis: {
                    labels: {
                        formatter: function(val) {
                            return '$' + val.toFixed(0);
                        },
                        style: {
                            colors: '#999'
                        }
                    }
                },
                tooltip: {
                    x: {
                        show: false
                    },
                    y: {
                        formatter: function(val) {
                            return '$' + val.toFixed(2);
                        }
                    },
                    theme: 'dark'
                }
            });
            
            portfolioPerformanceChart.render();
        }
        
        // Market Analysis Chart
        if (document.getElementById('market-analysis-chart')) {
            const marketAnalysisChart = new ApexCharts(document.getElementById('market-analysis-chart'), {
                series: [{
                    name: 'BTC/USDT',
                    data: [36400, 36500, 36700, 36600, 36800, 36750, 36900, 37000, 36950, 36800, 36850, 36782]
                }],
                chart: {
                    type: 'candlestick',
                    height: 350,
                    toolbar: {
                        show: true,
                        tools: {
                            download: false,
                            selection: true,
                            zoom: true,
                            zoomin: true,
                            zoomout: true,
                            pan: true,
                            reset: true
                        }
                    }
                },
                xaxis: {
                    type: 'datetime',
                    categories: Array.from({ length: 12 }, (_, i) => new Date(new Date().setHours(new Date().getHours() - (11 - i))).toISOString()),
                    labels: {
                        style: {
                            colors: '#999'
                        }
                    }
                },
                yaxis: {
                    tooltip: {
                        enabled: true
                    },
                    labels: {
                        formatter: function(val) {
                            return '$' + val.toFixed(0);
                        },
                        style: {
                            colors: '#999'
                        }
                    }
                },
                tooltip: {
                    theme: 'dark'
                }
            });
            
            marketAnalysisChart.render();
        }
    }
});
