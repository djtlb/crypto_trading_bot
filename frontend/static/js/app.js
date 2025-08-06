/**
 * GPU-Accelerated Crypto Trading Bot - Frontend JavaScript
 * Handles all UI interactions and API communications
 */

class TradingBotUI {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.isConnected = false;
        this.isTrading = false;
        this.refreshInterval = null;
        this.updateInterval = 30000; // 30 seconds
        
        // WebSocket properties
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkConnectionStatus();
        this.initWebSocket();
        this.showAlert('Welcome to GPU-Accelerated Trading Bot!', 'info');
    }

    // WebSocket initialization and management
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.showConnectionStatus(true);
            
            // Send ping to keep connection alive
            this.pingInterval = setInterval(() => {
                if (this.websocket.readyState === WebSocket.OPEN) {
                    this.websocket.send(JSON.stringify({type: 'ping'}));
                }
            }, 30000); // Send ping every 30 seconds
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.websocket.onclose = (event) => {
            console.log('WebSocket disconnected');
            this.showConnectionStatus(false);
            
            if (this.pingInterval) {
                clearInterval(this.pingInterval);
            }
            
            // Attempt to reconnect
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                setTimeout(() => this.initWebSocket(), 3000 * this.reconnectAttempts); // Exponential backoff
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'pong':
                // Connection is alive
                break;
                
            case 'portfolio_update':
                this.updatePortfolioDisplay(data.data);
                break;
                
            case 'market_update':
                this.updateMarketData(data.data);
                break;
                
            case 'trade_notification':
                this.showTradeNotification(data.data);
                break;
                
            case 'strategy_update':
                this.updateStrategyDisplay(data.data);
                break;
                
            case 'immediate_update':
                this.updateDashboard(data.data);
                break;
                
            case 'alert':
                this.showAlert(data.data.message, data.data.type || 'info');
                break;
                
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    showConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Real-time Connected' : 'Real-time Disconnected';
            statusElement.className = `badge ${connected ? 'bg-success' : 'bg-danger'}`;
        }
    }

    requestUpdate() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({type: 'request_update'}));
        }
    }

    updateDashboard(data) {
        if (data.portfolio) {
            this.updatePortfolioDisplay(data.portfolio);
        }
        if (data.strategies) {
            this.updateStrategyDisplay(data.strategies);
        }
        if (data.bot_status) {
            this.updateBotStatus(data.bot_status);
        }
        if (data.gpu_status) {
            this.updateGpuStatus(data.gpu_status);
        }
    }

    updateBotStatus(status) {
        const statusElement = document.getElementById('bot-status');
        if (statusElement) {
            statusElement.textContent = status.running ? 'Running' : 'Stopped';
            statusElement.className = `badge ${status.running ? 'bg-success' : 'bg-secondary'}`;
        }
        this.isTrading = status.running;
    }

    updateGpuStatus(gpuStatus) {
        const gpuElement = document.getElementById('gpu-status');
        if (gpuElement) {
            gpuElement.textContent = gpuStatus.gpu_available ? 'GPU Available' : 'CPU Only';
            gpuElement.className = `badge ${gpuStatus.gpu_available ? 'bg-success' : 'bg-warning'}`;
        }
    }

    showTradeNotification(tradeData) {
        const message = `${tradeData.action} ${tradeData.amount} ${tradeData.symbol} at $${tradeData.price}`;
        this.showAlert(message, tradeData.action === 'BUY' ? 'success' : 'warning');
    }

    updateMarketData(marketData) {
        // Update market data displays
        if (marketData && Array.isArray(marketData)) {
            const marketContainer = document.getElementById('market-data');
            if (marketContainer) {
                marketContainer.innerHTML = '';
                
                marketData.forEach(ticker => {
                    const tickerElement = document.createElement('div');
                    tickerElement.className = 'col-md-4 mb-3';
                    tickerElement.innerHTML = `
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-title">${ticker.symbol}</h6>
                                <p class="card-text">
                                    <strong>$${ticker.price?.toFixed(4) || 'N/A'}</strong>
                                    <br>
                                    <small class="text-${ticker.change >= 0 ? 'success' : 'danger'}">
                                        ${ticker.change >= 0 ? '+' : ''}${ticker.change?.toFixed(2) || '0.00'}%
                                    </small>
                                </p>
                            </div>
                        </div>
                    `;
                    marketContainer.appendChild(tickerElement);
                });
            }
        }
    }

    updatePortfolioDisplay(portfolioData) {
        if (portfolioData) {
            // Update total budget
            const totalBudgetElement = document.getElementById('total-budget');
            if (totalBudgetElement && portfolioData.total_value !== undefined) {
                totalBudgetElement.textContent = `$${portfolioData.total_value.toFixed(2)}`;
            }
            
            // Update available budget
            const availableBudgetElement = document.getElementById('available-budget');
            if (availableBudgetElement && portfolioData.available_budget !== undefined) {
                availableBudgetElement.textContent = `$${portfolioData.available_budget.toFixed(2)}`;
            }
            
            // Update active trades
            const activeTradesElement = document.getElementById('active-trades');
            if (activeTradesElement && portfolioData.active_trades !== undefined) {
                activeTradesElement.textContent = `${portfolioData.active_trades}/${portfolioData.max_trades || 10}`;
            }
            
            // Update daily PnL
            const dailyPnlElement = document.getElementById('daily-pnl');
            if (dailyPnlElement && portfolioData.daily_pnl !== undefined) {
                const pnl = portfolioData.daily_pnl;
                dailyPnlElement.textContent = `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`;
                dailyPnlElement.className = pnl >= 0 ? 'text-success' : 'text-danger';
            }
        }
    }

    updateStrategyDisplay(strategiesData) {
        const strategiesContainer = document.getElementById('strategies-content');
        if (strategiesContainer && strategiesData) {
            strategiesContainer.innerHTML = '';
            
            Object.entries(strategiesData).forEach(([name, data]) => {
                const strategyElement = document.createElement('div');
                strategyElement.className = 'col-md-6 mb-3';
                strategyElement.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">${name}</h6>
                            <p class="card-text">
                                <strong>Total Trades:</strong> ${data.total_trades || 0}<br>
                                <strong>Success Rate:</strong> ${data.successful_trades || 0}/${data.total_trades || 0}<br>
                                <strong>Symbols:</strong> ${(data.symbols || []).join(', ') || 'None'}
                            </p>
                            <div class="progress mb-2">
                                <div class="progress-bar bg-success" style="width: ${((data.successful_trades || 0) / Math.max(data.total_trades || 1, 1)) * 100}%"></div>
                            </div>
                        </div>
                    </div>
                `;
                strategiesContainer.appendChild(strategyElement);
            });
        }
    }

    bindEvents() {
        // Login form
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Trading controls
        document.getElementById('start-trading').addEventListener('click', () => {
            this.startTrading();
        });

        document.getElementById('stop-trading').addEventListener('click', () => {
            this.stopTrading();
        });

        // Benchmark button
        document.getElementById('benchmark-btn').addEventListener('click', () => {
            this.runBenchmark();
        });

        // Refresh button
        document.getElementById('refresh-data').addEventListener('click', () => {
            this.refreshData();
        });

        // Manual trade form
        document.getElementById('manual-trade-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.executeManualTrade();
        });

        // Tab changes
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                this.handleTabChange(e.target.getAttribute('data-bs-target'));
            });
        });
    }

    async handleLogin() {
        const apiKey = document.getElementById('api-key').value;
        const apiSecret = document.getElementById('api-secret').value;
        const apiPassphrase = document.getElementById('api-passphrase').value;
        const sandbox = document.getElementById('sandbox').checked;

        if (!apiKey || !apiSecret || !apiPassphrase) {
            this.showAlert('Please fill in all API credentials', 'danger');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    api_key: apiKey,
                    api_secret: apiSecret,
                    api_passphrase: apiPassphrase,
                    sandbox: sandbox
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.isConnected = true;
                this.showDashboard();
                this.updateConnectionStatus('Connected', 'success');
                this.showAlert('Successfully connected to Coinbase Pro!', 'success');
                this.startDataRefresh();
                
                // Display GPU status
                if (data.gpu_status) {
                    this.updateGPUStatus(data.gpu_status);
                }
            } else {
                throw new Error(data.detail || 'Login failed');
            }
        } catch (error) {
            this.showAlert(`Login failed: ${error.message}`, 'danger');
            this.showLoginError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async startTrading() {
        if (!this.isConnected) {
            this.showAlert('Please connect to Coinbase Pro first', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/trading/start`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                this.isTrading = true;
                this.updateTradingControls();
                this.showAlert('Automated trading started!', 'success');
            } else {
                throw new Error(data.detail || 'Failed to start trading');
            }
        } catch (error) {
            this.showAlert(`Failed to start trading: ${error.message}`, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    async stopTrading() {
        this.showLoading(true);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/trading/stop`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                this.isTrading = false;
                this.updateTradingControls();
                this.showAlert('Automated trading stopped!', 'info');
            } else {
                throw new Error(data.detail || 'Failed to stop trading');
            }
        } catch (error) {
            this.showAlert(`Failed to stop trading: ${error.message}`, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    async runBenchmark() {
        if (!this.isConnected) {
            this.showAlert('Please connect to Coinbase Pro first', 'warning');
            return;
        }

        this.showLoading(true);
        this.showAlert('Running GPU vs CPU benchmark...', 'info');

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/strategies/benchmark`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                this.displayBenchmarkResults(data.benchmark_results);
                this.showAlert('Benchmark completed successfully!', 'success');
            } else {
                throw new Error(data.detail || 'Benchmark failed');
            }
        } catch (error) {
            this.showAlert(`Benchmark failed: ${error.message}`, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    async executeManualTrade() {
        if (!this.isConnected) {
            this.showAlert('Please connect to Coinbase Pro first', 'warning');
            return;
        }

        const symbol = document.getElementById('trade-symbol').value;
        const side = document.getElementById('trade-side').value;
        const amount = parseFloat(document.getElementById('trade-amount').value);
        const strategy = document.getElementById('trade-strategy').value;

        if (!symbol || !side || !amount || amount <= 0) {
            this.showAlert('Please fill in all trade details', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/trade/manual`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    side: side,
                    amount: amount,
                    strategy: strategy
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showAlert(`Trade executed successfully! Order ID: ${data.order_id}`, 'success');
                this.refreshTradeHistory();
                document.getElementById('manual-trade-form').reset();
            } else {
                throw new Error(data.detail || 'Trade execution failed');
            }
        } catch (error) {
            this.showAlert(`Trade failed: ${error.message}`, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    async refreshData() {
        if (!this.isConnected) return;

        try {
            // Request immediate update via WebSocket
            this.requestUpdate();
            
            // Refresh status
            const statusResponse = await fetch(`${this.apiBaseUrl}/api/status`);
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                this.updateDashboardData(statusData);
            }

            // Refresh current tab content
            const activeTab = document.querySelector('.nav-link.active').getAttribute('data-bs-target');
            this.loadTabContent(activeTab);

        } catch (error) {
            console.error('Failed to refresh data:', error);
        }
    }

    async loadTabContent(tabId) {
        switch (tabId) {
            case '#strategies':
                await this.loadStrategies();
                break;
            case '#portfolio':
                await this.loadPortfolio();
                break;
            case '#trading':
                await this.refreshTradeHistory();
                break;
            case '#market':
                await this.loadMarketData();
                break;
            case '#logs':
                await this.loadLogs();
                break;
        }
    }

    async loadStrategies() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/strategies`);
            if (response.ok) {
                const data = await response.json();
                this.displayStrategies(data);
            }
        } catch (error) {
            console.error('Failed to load strategies:', error);
        }
    }

    async loadPortfolio() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/portfolio`);
            if (response.ok) {
                const data = await response.json();
                this.displayPortfolio(data);
            }
        } catch (error) {
            console.error('Failed to load portfolio:', error);
        }
    }

    async loadMarketData() {
        const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'];
        const marketContainer = document.getElementById('market-data');
        marketContainer.innerHTML = '';

        for (const symbol of symbols) {
            try {
                const response = await fetch(`${this.apiBaseUrl}/api/market/${encodeURIComponent(symbol)}`);
                if (response.ok) {
                    const data = await response.json();
                    this.addMarketCard(marketContainer, data);
                }
            } catch (error) {
                console.error(`Failed to load ${symbol} data:`, error);
            }
        }
    }

    async refreshTradeHistory() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/trades/history`);
            if (response.ok) {
                const data = await response.json();
                this.displayTradeHistory(data.trades);
            }
        } catch (error) {
            console.error('Failed to load trade history:', error);
        }
    }

    async loadLogs() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/logs`);
            if (response.ok) {
                const data = await response.json();
                this.displayLogs(data.logs);
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    }

    // UI Update Methods

    showDashboard() {
        document.getElementById('login-section').style.display = 'none';
        document.getElementById('dashboard-section').style.display = 'block';
    }

    showLoginError(message) {
        const errorDiv = document.getElementById('login-error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    updateConnectionStatus(status, type) {
        const statusBadge = document.getElementById('connection-status');
        statusBadge.textContent = status;
        statusBadge.className = `badge bg-${type}`;
    }

    updateTradingControls() {
        const startBtn = document.getElementById('start-trading');
        const stopBtn = document.getElementById('stop-trading');

        if (this.isTrading) {
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
        } else {
            startBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
        }
    }

    updateDashboardData(data) {
        if (data.portfolio) {
            document.getElementById('total-budget').textContent = `$${data.portfolio.total_budget?.toFixed(2) || '0.00'}`;
            document.getElementById('available-budget').textContent = `$${data.portfolio.available_budget?.toFixed(2) || '0.00'}`;
            document.getElementById('active-trades').textContent = `${data.portfolio.active_trades || 0}/${data.portfolio.max_trades || 10}`;
            document.getElementById('daily-pnl').textContent = `$${data.portfolio.daily_pnl?.toFixed(2) || '0.00'}`;
        }

        this.isTrading = data.running || false;
        this.updateTradingControls();

        if (data.gpu_status) {
            this.updateGPUStatus(data.gpu_status);
        }
    }

    updateGPUStatus(gpuStatus) {
        const container = document.getElementById('gpu-status-content');
        container.innerHTML = `
            <div class="col-md-3">
                <div class="gpu-status-item ${gpuStatus.gpu_available ? 'enabled' : 'disabled'}">
                    <i class="fas fa-microchip me-2"></i>
                    <span>GPU Available: ${gpuStatus.gpu_available ? 'Yes' : 'No'}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="gpu-status-item ${gpuStatus.use_numba ? 'enabled' : 'disabled'}">
                    <i class="fas fa-rocket me-2"></i>
                    <span>Numba JIT: ${gpuStatus.use_numba ? 'Active' : 'Inactive'}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="gpu-status-item ${gpuStatus.use_polars ? 'enabled' : 'disabled'}">
                    <i class="fas fa-database me-2"></i>
                    <span>Polars: ${gpuStatus.use_polars ? 'Active' : 'Inactive'}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="gpu-status-item ${gpuStatus.use_opencl ? 'enabled' : 'disabled'}">
                    <i class="fas fa-bolt me-2"></i>
                    <span>OpenCL: ${gpuStatus.use_opencl ? 'Active' : 'Inactive'}</span>
                </div>
            </div>
        `;
    }

    displayStrategies(strategies) {
        const container = document.getElementById('strategies-content');
        container.innerHTML = '';

        Object.entries(strategies).forEach(([name, info]) => {
            const successRate = info.trade_count > 0 ? 
                ((info.successful_trades / info.trade_count) * 100).toFixed(1) : '0.0';
            
            const strategyClass = name.includes('rsi') ? 'rsi' : 
                                name.includes('volatility') ? 'volatility' : 'moving-average';

            const card = document.createElement('div');
            card.className = `card strategy-card ${strategyClass}`;
            card.innerHTML = `
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="card-title">${this.formatStrategyName(name)}</h6>
                            <p class="card-text">Symbols: ${info.symbols.join(', ')}</p>
                        </div>
                        <div class="col-md-6">
                            <div class="row text-center">
                                <div class="col-4">
                                    <strong>${info.trade_count}</strong><br>
                                    <small>Total Trades</small>
                                </div>
                                <div class="col-4">
                                    <strong class="text-success">${info.successful_trades}</strong><br>
                                    <small>Successful</small>
                                </div>
                                <div class="col-4">
                                    <strong>${successRate}%</strong><br>
                                    <small>Success Rate</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    }

    displayPortfolio(data) {
        const container = document.getElementById('portfolio-content');
        const portfolio = data.portfolio;
        const balance = data.balance;

        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Portfolio Summary</h6>
                    <div class="allocation-item">
                        <span>Total Budget:</span>
                        <strong>$${portfolio.total_budget?.toFixed(2) || '0.00'}</strong>
                    </div>
                    <div class="allocation-item">
                        <span>Available Budget:</span>
                        <strong class="text-success">$${portfolio.available_budget?.toFixed(2) || '0.00'}</strong>
                    </div>
                    <div class="allocation-item">
                        <span>Allocated Budget:</span>
                        <strong class="text-warning">$${(portfolio.total_budget - portfolio.available_budget)?.toFixed(2) || '0.00'}</strong>
                    </div>
                    <div class="allocation-item">
                        <span>Daily P&L:</span>
                        <strong class="${portfolio.daily_pnl >= 0 ? 'text-success' : 'text-danger'}">$${portfolio.daily_pnl?.toFixed(2) || '0.00'}</strong>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Exchange Balance</h6>
                    ${Object.entries(balance || {}).map(([asset, amount]) => `
                        <div class="allocation-item">
                            <span>${asset}:</span>
                            <strong>${parseFloat(amount).toFixed(8)}</strong>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    displayTradeHistory(trades) {
        const container = document.getElementById('trade-history');
        
        if (!trades || trades.length === 0) {
            container.innerHTML = '<p class="text-muted">No trades found</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'table table-sm trade-history-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Amount</th>
                    <th>Price</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${trades.map(trade => `
                    <tr class="trade-${trade.side}">
                        <td>${new Date(trade.timestamp || trade.datetime).toLocaleString()}</td>
                        <td>${trade.symbol}</td>
                        <td>
                            <span class="badge bg-${trade.side === 'buy' ? 'success' : 'danger'}">
                                ${trade.side.toUpperCase()}
                            </span>
                        </td>
                        <td>${trade.amount}</td>
                        <td>$${trade.price?.toFixed(2) || 'N/A'}</td>
                        <td>
                            <span class="badge bg-${trade.status === 'closed' ? 'success' : 'warning'}">
                                ${trade.status || 'Unknown'}
                            </span>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        
        container.innerHTML = '';
        container.appendChild(table);
    }

    addMarketCard(container, data) {
        const changeClass = data.change >= 0 ? 'text-success' : 'text-danger';
        const changeIcon = data.change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';

        const card = document.createElement('div');
        card.className = 'col-md-4 col-lg-2 mb-3';
        card.innerHTML = `
            <div class="card market-card">
                <div class="card-body text-center">
                    <h6 class="card-title">${data.symbol}</h6>
                    <h5 class="card-text">$${data.price?.toFixed(2) || 'N/A'}</h5>
                    <p class="card-text ${changeClass}">
                        <i class="fas ${changeIcon}"></i>
                        ${data.change?.toFixed(2) || '0.00'}%
                    </p>
                    <small class="text-muted">Vol: ${data.volume?.toFixed(0) || 'N/A'}</small>
                </div>
            </div>
        `;
        container.appendChild(card);
    }

    displayLogs(logs) {
        const container = document.getElementById('logs-content');
        
        if (!logs || logs.length === 0) {
            container.innerHTML = '<p class="text-muted">No logs available</p>';
            return;
        }

        container.innerHTML = logs.map(log => {
            const logType = this.getLogType(log);
            return `<div class="log-entry log-${logType}">${log.trim()}</div>`;
        }).join('');
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    displayBenchmarkResults(results) {
        const message = `
            GPU Benchmark Results:
            • GPU Available: ${results.gpu_available ? 'Yes' : 'No'}
            • Numba JIT: ${results.numba_available ? 'Active' : 'Inactive'}
            • Performance: ${results.performance_improvement || 'N/A'}
            • Test Status: ${results.test_passed ? 'PASSED' : 'FAILED'}
        `;
        this.showAlert(message, 'info', 10000);
    }

    // Utility Methods

    formatStrategyName(name) {
        return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    getLogType(log) {
        if (log.includes('ERROR') || log.includes('error')) return 'error';
        if (log.includes('WARNING') || log.includes('warning')) return 'warning';
        if (log.includes('SUCCESS') || log.includes('success')) return 'success';
        return 'info';
    }

    showAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.getElementById('alert-container');
        const alertId = `alert-${Date.now()}`;
        
        const alert = document.createElement('div');
        alert.id = alertId;
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto dismiss
        setTimeout(() => {
            const alertElement = document.getElementById(alertId);
            if (alertElement) {
                alertElement.remove();
            }
        }, duration);
    }

    showLoading(show) {
        const modal = new bootstrap.Modal(document.getElementById('loading-modal'));
        if (show) {
            modal.show();
        } else {
            modal.hide();
        }
    }

    async checkConnectionStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/status`);
            if (response.ok) {
                const data = await response.json();
                if (data.connected) {
                    this.isConnected = true;
                    this.showDashboard();
                    this.updateConnectionStatus('Connected', 'success');
                    this.startDataRefresh();
                    this.updateDashboardData(data);
                }
            }
        } catch (error) {
            console.log('Not connected yet');
        }
    }

    startDataRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, this.updateInterval);
    }

    handleTabChange(tabId) {
        this.loadTabContent(tabId);
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.tradingBot = new TradingBotUI();
});
