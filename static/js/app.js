// Main application JavaScript

// Configuration
const config = {
    apiBaseUrl: localStorage.getItem('apiBaseUrl') || 'http://localhost:5003',
    defaultChainId: localStorage.getItem('defaultChainId') || '1',
    defaultDexId: localStorage.getItem('defaultDexId') || 'uniswap_v2',
    defaultSlippage: localStorage.getItem('defaultSlippage') || '1.0',
    defaultGasSpeed: localStorage.getItem('defaultGasSpeed') || 'average',
    theme: localStorage.getItem('theme') || 'dark'
};

// DOM Elements
const elements = {
    // Tabs
    tabs: document.querySelectorAll('.tab-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    
    // Status
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    serverStatus: document.getElementById('server-status'),
    walletStatus: document.getElementById('wallet-status'),
    activeStrategiesCount: document.getElementById('active-strategies'),
    
    // Quick Actions
    connectWalletBtn: document.getElementById('connect-wallet-btn'),
    checkPriceBtn: document.getElementById('check-price-btn'),
    validateTokenBtn: document.getElementById('validate-token-btn'),
    
    // Gas Prices
    ethBaseFee: document.getElementById('eth-base-fee'),
    ethPriorityFee: document.getElementById('eth-priority-fee'),
    ethFast: document.getElementById('eth-fast'),
    ethAverage: document.getElementById('eth-average'),
    ethSlow: document.getElementById('eth-slow'),
    
    // Wallet Tab
    walletConnectionType: document.getElementById('wallet-connection-type'),
    walletInputLabel: document.getElementById('wallet-input-label'),
    walletInput: document.getElementById('wallet-input'),
    privateKeyWarning: document.getElementById('private-key-warning'),
    walletNetwork: document.getElementById('wallet-network'),
    connectWalletSubmit: document.getElementById('connect-wallet-submit'),
    disconnectWalletBtn: document.getElementById('disconnect-wallet-btn'),
    walletInfoCard: document.getElementById('wallet-info-card'),
    walletAddress: document.getElementById('wallet-address'),
    walletMode: document.getElementById('wallet-mode'),
    reloadBalances: document.getElementById('reload-balances'),
    nativeBalanceAmount: document.getElementById('native-balance-amount'),
    nativeTokenSymbol: document.getElementById('native-token-symbol'),
    tokenBalances: document.getElementById('token-balances'),
    
    // Trade Tab
    buyAction: document.getElementById('buy-action'),
    sellAction: document.getElementById('sell-action'),
    buyForm: document.getElementById('buy-form'),
    sellForm: document.getElementById('sell-form'),
    tradeNetwork: document.getElementById('trade-network'),
    tradeDex: document.getElementById('trade-dex'),
    tradeTokenAddress: document.getElementById('trade-token-address'),
    validateTradeToken: document.getElementById('validate-trade-token'),
    buyAmount: document.getElementById('buy-amount'),
    buyBaseToken: document.getElementById('buy-base-token'),
    sellAmount: document.getElementById('sell-amount'),
    sellPercent: document.getElementById('sell-percent'),
    sellBaseToken: document.getElementById('sell-base-token'),
    slippageBtns: document.querySelectorAll('.slippage-btn'),
    customSlippage: document.getElementById('custom-slippage'),
    gasSpeedBtns: document.querySelectorAll('.gas-speed-btn'),
    executeTradeBtn: document.getElementById('execute-trade-btn'),
    
    // Price Check
    priceCheckTokenAddress: document.getElementById('price-check-token-address'),
    priceCheckNetwork: document.getElementById('price-check-network'),
    priceCheckDex: document.getElementById('price-check-dex'),
    checkPriceSubmit: document.getElementById('check-price-submit'),
    priceResult: document.getElementById('price-result'),
    priceTokenSymbol: document.getElementById('price-token-symbol'),
    priceValue: document.getElementById('price-value'),
    
    // Strategies Tab
    strategyType: document.getElementById('strategy-type'),
    strategyDescription: document.getElementById('strategy-description'),
    strategyForm: document.getElementById('strategy-form'),
    strategyNetwork: document.getElementById('strategy-network'),
    strategyDex: document.getElementById('strategy-dex'),
    strategyTargetDexGroup: document.getElementById('strategy-target-dex-group'),
    strategyTargetDex: document.getElementById('strategy-target-dex'),
    strategyTokenAddress: document.getElementById('strategy-token-address'),
    strategyBaseToken: document.getElementById('strategy-base-token'),
    strategyAmount: document.getElementById('strategy-amount'),
    strategySlippage: document.getElementById('strategy-slippage'),
    strategyProfitTarget: document.getElementById('strategy-profit-target'),
    strategyStopLoss: document.getElementById('strategy-stop-loss'),
    strategyTrailingStop: document.getElementById('strategy-trailing-stop'),
    strategySpecificParams: document.getElementById('strategy-specific-params'),
    startStrategyBtn: document.getElementById('start-strategy-btn'),
    reloadStrategies: document.getElementById('reload-strategies'),
    activeStrategiesList: document.getElementById('active-strategies-list'),
    
    // Settings Tab
    defaultNetwork: document.getElementById('default-network'),
    defaultDex: document.getElementById('default-dex'),
    defaultSlippage: document.getElementById('default-slippage'),
    defaultGasSpeed: document.getElementById('default-gas-speed'),
    themeSelector: document.getElementById('theme-selector'),
    saveSettingsBtn: document.getElementById('save-settings-btn'),
    apiUrl: document.getElementById('api-url'),
    customApiUrl: document.getElementById('custom-api-url'),
    updateApiUrlBtn: document.getElementById('update-api-url-btn'),
    
    // Modal
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    modalCancel: document.getElementById('modal-cancel'),
    modalConfirm: document.getElementById('modal-confirm'),
    modalClose: document.querySelector('.close'),
    
    // Toast
    toastContainer: document.getElementById('toast-container')
};

// State
const state = {
    serverConnected: false,
    wallet: {
        connected: false,
        address: null,
        readOnly: true,
        chainId: 1
    },
    activeStrategies: [],
    slippage: 1.0,
    gasSpeed: 'average',
    tradeAction: 'buy',
    strategyData: null,
    customTokens: JSON.parse(localStorage.getItem('customTokens') || '{}')
};

// Initialize the application
function init() {
    // Apply saved theme
    applyTheme(config.theme);
    
    // Set initial values from config
    elements.tradeNetwork.value = config.defaultChainId;
    elements.tradeDex.value = config.defaultDexId;
    elements.priceCheckNetwork.value = config.defaultChainId;
    elements.priceCheckDex.value = config.defaultDexId;
    elements.strategyNetwork.value = config.defaultChainId;
    elements.strategyDex.value = config.defaultDexId;
    elements.strategyTargetDex.value = config.defaultDexId;
    elements.strategySlippage.value = config.defaultSlippage;
    elements.defaultNetwork.value = config.defaultChainId;
    elements.defaultDex.value = config.defaultDexId;
    elements.defaultSlippage.value = config.defaultSlippage;
    elements.defaultGasSpeed.value = config.defaultGasSpeed;
    elements.themeSelector.value = config.theme;
    elements.apiUrl.textContent = config.apiBaseUrl;
    elements.customApiUrl.value = config.apiBaseUrl;
    
    // Set active slippage and gas speed buttons
    document.querySelector(`.slippage-btn[data-value="${config.defaultSlippage}"]`)?.classList.add('active');
    document.querySelector(`.gas-speed-btn[data-value="${config.defaultGasSpeed}"]`)?.classList.add('active');
    
    // Setup event listeners
    setupEventListeners();
    
    // Check server status
    checkServerStatus();
    
    // Load gas prices
    loadGasPrices(1); // Ethereum by default
    
    // Load available strategies
    loadAvailableStrategies();
}

// Setup event listeners
function setupEventListeners() {
    // Tab switching
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab(tab.dataset.tab);
        });
    });
    
    // Quick actions
    elements.connectWalletBtn.addEventListener('click', () => {
        switchTab('wallet');
    });
    
    elements.checkPriceBtn.addEventListener('click', () => {
        switchTab('trade');
        document.querySelector('[data-tab="trade"]').scrollIntoView();
    });
    
    elements.validateTokenBtn.addEventListener('click', () => {
        showModal('Validate Token', `
            <div class="form-group">
                <label>Token Address</label>
                <input type="text" id="modal-token-address" placeholder="0x..." />
            </div>
            <div class="form-group">
                <label>Network</label>
                <select id="modal-network">
                    <option value="1">Ethereum</option>
                    <option value="56">BNB Smart Chain</option>
                    <option value="137">Polygon</option>
                    <option value="42161">Arbitrum</option>
                </select>
            </div>
        `, 'Validate', () => {
            const tokenAddress = document.getElementById('modal-token-address').value;
            const chainId = document.getElementById('modal-network').value;
            validateToken(tokenAddress, chainId);
        });
    });
    
    // Gas prices reload
    document.querySelectorAll('.reload-icon[data-chain-id]').forEach(icon => {
        icon.addEventListener('click', () => {
            const chainId = icon.dataset.chainId;
            loadGasPrices(chainId);
        });
    });
    
    // Wallet connection
    elements.walletConnectionType.addEventListener('change', () => {
        if (elements.walletConnectionType.value === 'private_key') {
            elements.walletInputLabel.textContent = 'Private Key';
            elements.walletInput.type = 'password';
            elements.privateKeyWarning.style.display = 'block';
        } else {
            elements.walletInputLabel.textContent = 'Wallet Address';
            elements.walletInput.type = 'text';
            elements.privateKeyWarning.style.display = 'none';
        }
    });
    
    elements.connectWalletSubmit.addEventListener('click', connectWallet);
    elements.disconnectWalletBtn.addEventListener('click', disconnectWallet);
    elements.reloadBalances.addEventListener('click', loadWalletBalances);
    
    // Trade actions
    elements.buyAction.addEventListener('click', () => {
        state.tradeAction = 'buy';
        elements.buyAction.classList.add('active');
        elements.sellAction.classList.remove('active');
        elements.buyForm.style.display = 'block';
        elements.sellForm.style.display = 'none';
    });
    
    elements.sellAction.addEventListener('click', () => {
        state.tradeAction = 'sell';
        elements.sellAction.classList.add('active');
        elements.buyAction.classList.remove('active');
        elements.sellForm.style.display = 'block';
        elements.buyForm.style.display = 'none';
    });
    
    elements.validateTradeToken.addEventListener('click', () => {
        validateToken(elements.tradeTokenAddress.value, elements.tradeNetwork.value);
    });
    
    elements.slippageBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.slippageBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.slippage = parseFloat(btn.dataset.value);
            elements.customSlippage.value = '';
        });
    });
    
    elements.customSlippage.addEventListener('input', () => {
        if (elements.customSlippage.value) {
            elements.slippageBtns.forEach(b => b.classList.remove('active'));
            state.slippage = parseFloat(elements.customSlippage.value);
        }
    });
    
    elements.gasSpeedBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.gasSpeedBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.gasSpeed = btn.dataset.value;
        });
    });
    
    elements.executeTradeBtn.addEventListener('click', executeTrade);
    
    // Price check
    elements.checkPriceSubmit.addEventListener('click', checkPrice);
    
    // Strategy tab
    elements.strategyType.addEventListener('change', () => {
        updateStrategyForm();
    });
    
    elements.startStrategyBtn.addEventListener('click', startStrategy);
    elements.reloadStrategies.addEventListener('click', loadActiveStrategies);
    
    // Settings
    elements.saveSettingsBtn.addEventListener('click', saveSettings);
    elements.updateApiUrlBtn.addEventListener('click', updateApiUrl);
    
    // Modal
    elements.modalClose.addEventListener('click', hideModal);
    elements.modalCancel.addEventListener('click', hideModal);
    window.addEventListener('click', (event) => {
        if (event.target === elements.modal) {
            hideModal();
        }
    });
    
    // Custom token select amounts
    elements.sellPercent.addEventListener('change', () => {
        if (elements.sellPercent.value) {
            elements.sellAmount.value = '';
            elements.sellAmount.disabled = true;
        } else {
            elements.sellAmount.disabled = false;
        }
    });
    
    elements.sellAmount.addEventListener('input', () => {
        if (elements.sellAmount.value) {
            elements.sellPercent.value = '';
        }
    });
}

// Switch between tabs
function switchTab(tabId) {
    elements.tabs.forEach(tab => {
        if (tab.dataset.tab === tabId) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    elements.tabPanes.forEach(pane => {
        if (pane.id === tabId) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });
    
    // Load tab-specific data
    if (tabId === 'dashboard') {
        checkServerStatus();
        loadGasPrices(1);
        if (state.wallet.connected) {
            loadActiveStrategies();
        }
    } else if (tabId === 'wallet' && state.wallet.connected) {
        loadWalletBalances();
    } else if (tabId === 'strategies' && state.wallet.connected) {
        loadActiveStrategies();
    }
}

// Apply theme
function applyTheme(theme) {
    if (theme === 'light') {
        document.body.classList.add('light-theme');
    } else {
        document.body.classList.remove('light-theme');
    }
}

// Check server status
async function checkServerStatus() {
    try {
        elements.serverStatus.textContent = 'Checking...';
        const response = await fetch(`${config.apiBaseUrl}/api/status`);
        const data = await response.json();
        
        if (data.status === 'running') {
            elements.serverStatus.textContent = 'Connected';
            elements.statusDot.classList.remove('disconnected');
            elements.statusDot.classList.add('connected');
            elements.statusText.textContent = 'Connected';
            state.serverConnected = true;
            
            // Update wallet status if connected
            if (data.wallet_connected) {
                updateWalletStatus(data.wallet_address);
            }
            
            // Update active strategies count
            elements.activeStrategiesCount.textContent = data.active_strategies;
        } else {
            throw new Error('Server not running');
        }
    } catch (error) {
        console.error('Server status error:', error);
        elements.serverStatus.textContent = 'Disconnected';
        elements.statusDot.classList.remove('connected');
        elements.statusDot.classList.add('disconnected');
        elements.statusText.textContent = 'Disconnected';
        state.serverConnected = false;
        
        showToast('Server connection failed', 'error');
    }
}

// Load gas prices
async function loadGasPrices(chainId) {
    try {
        const icon = document.querySelector(`.reload-icon[data-chain-id="${chainId}"]`);
        icon.classList.add('rotating');
        
        const response = await fetch(`${config.apiBaseUrl}/api/get_gas_price?chain_id=${chainId}`);
        const data = await response.json();
        
        if (data.success) {
            if (chainId == 1) { // Ethereum
                elements.ethBaseFee.textContent = data.base_fee_gwei.toFixed(2);
                elements.ethPriorityFee.textContent = data.priority_fee_gwei.toFixed(2);
                elements.ethFast.textContent = data.estimated_fast_gwei.toFixed(2);
                elements.ethAverage.textContent = (data.base_fee_gwei + data.priority_fee_gwei).toFixed(2);
                elements.ethSlow.textContent = data.estimated_slow_gwei.toFixed(2);
            }
        } else {
            throw new Error(data.error || 'Failed to load gas prices');
        }
    } catch (error) {
        console.error(`Gas price error for chain ${chainId}:`, error);
        showToast(`Failed to load gas prices: ${error.message}`, 'error');
    } finally {
        const icon = document.querySelector(`.reload-icon[data-chain-id="${chainId}"]`);
        icon.classList.remove('rotating');
    }
}

// Connect wallet
async function connectWallet() {
    try {
        if (!state.serverConnected) {
            showToast('Server not connected', 'error');
            return;
        }
        
        const connectionType = elements.walletConnectionType.value;
        const input = elements.walletInput.value.trim();
        const chainId = parseInt(elements.walletNetwork.value);
        
        if (!input) {
            showToast(`${connectionType === 'private_key' ? 'Private key' : 'Wallet address'} is required`, 'error');
            return;
        }
        
        const payload = {
            type: connectionType
        };
        
        if (connectionType === 'private_key') {
            payload.private_key = input;
        } else {
            payload.address = input;
        }
        
        const response = await fetch(`${config.apiBaseUrl}/api/connect_wallet`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateWalletStatus(data.address, data.read_only !== undefined ? data.read_only : connectionType === 'address');
            showToast(data.message, 'success');
            
            // Load wallet balances
            loadWalletBalances();
            
            // Reset input
            elements.walletInput.value = '';
            
            // Switch to dashboard
            switchTab('dashboard');
        } else {
            throw new Error(data.error || 'Failed to connect wallet');
        }
    } catch (error) {
        console.error('Wallet connection error:', error);
        showToast(`Wallet connection failed: ${error.message}`, 'error');
    }
}

// Disconnect wallet
async function disconnectWallet() {
    try {
        if (!state.serverConnected) {
            showToast('Server not connected', 'error');
            return;
        }
        
        const response = await fetch(`${config.apiBaseUrl}/api/disconnect_wallet`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update UI
            elements.walletStatus.textContent = 'Not Connected';
            elements.connectWalletBtn.style.display = 'inline-flex';
            elements.walletInfoCard.style.display = 'none';
            elements.disconnectWalletBtn.style.display = 'none';
            elements.connectWalletSubmit.style.display = 'inline-flex';
            
            // Update state
            state.wallet.connected = false;
            state.wallet.address = null;
            state.wallet.readOnly = true;
            
            showToast(data.message, 'success');
        } else {
            throw new Error(data.error || 'Failed to disconnect wallet');
        }
    } catch (error) {
        console.error('Wallet disconnection error:', error);
        showToast(`Wallet disconnection failed: ${error.message}`, 'error');
    }
}

// Update wallet status
function updateWalletStatus(address, readOnly = true) {
    state.wallet.connected = true;
    state.wallet.address = address;
    state.wallet.readOnly = readOnly;
    
    elements.walletStatus.textContent = `Connected: ${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    elements.connectWalletBtn.style.display = 'none';
    elements.walletInfoCard.style.display = 'block';
    elements.disconnectWalletBtn.style.display = 'inline-flex';
    elements.connectWalletSubmit.style.display = 'none';
    
    elements.walletAddress.textContent = `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    elements.walletMode.textContent = readOnly ? 'Read-Only' : 'Trading';
}

// Load wallet balances
async function loadWalletBalances() {
    try {
        if (!state.wallet.connected) {
            return;
        }
        
        elements.reloadBalances.classList.add('rotating');
        
        const chainId = parseInt(elements.walletNetwork.value);
        state.wallet.chainId = chainId;
        
        const response = await fetch(`${config.apiBaseUrl}/api/wallet_balances?chain_id=${chainId}`);
        const data = await response.json();
        
        if (data.success) {
            // Update native token balance
            elements.nativeBalanceAmount.textContent = data.native_balance.toFixed(6);
            elements.nativeTokenSymbol.textContent = data.native_token;
            
            // Update token balances
            if (Object.keys(data.token_balances).length > 0) {
                let balancesHtml = '';
                
                for (const [address, balanceData] of Object.entries(data.token_balances)) {
                    balancesHtml += `
                        <div class="token-balance">
                            <p>${balanceData.token.symbol}: ${balanceData.balance_formatted}</p>
                        </div>
                    `;
                    
                    // Add custom token to local storage if not exists
                    if (!state.customTokens[address]) {
                        state.customTokens[address] = {
                            symbol: balanceData.token.symbol,
                            decimals: balanceData.token.decimals,
                            chainId: chainId
                        };
                        
                        localStorage.setItem('customTokens', JSON.stringify(state.customTokens));
                    }
                }
                
                elements.tokenBalances.innerHTML = balancesHtml;
            } else {
                elements.tokenBalances.innerHTML = '<p class="empty-message">No token balances</p>';
            }
        } else {
            throw new Error(data.error || 'Failed to load wallet balances');
        }
    } catch (error) {
        console.error('Wallet balances error:', error);
        showToast(`Failed to load wallet balances: ${error.message}`, 'error');
    } finally {
        elements.reloadBalances.classList.remove('rotating');
    }
}

// Validate token
async function validateToken(tokenAddress, chainId) {
    try {
        if (!tokenAddress) {
            showToast('Token address is required', 'error');
            return;
        }
        
        showModal('Validating Token', `
            <p>Validating token at address: ${tokenAddress}</p>
            <p>This may take a moment...</p>
            <div class="loading" style="text-align: center; margin: 20px 0;">
                <i class="fas fa-spinner fa-spin" style="font-size: 24px;"></i>
            </div>
        `);
        
        elements.modalCancel.style.display = 'none';
        elements.modalConfirm.style.display = 'none';
        
        const response = await fetch(`${config.apiBaseUrl}/api/validate_token?token_address=${tokenAddress}&chain_id=${chainId}`);
        const data = await response.json();
        
        if (data.success) {
            let statusColor = data.is_honeypot ? 'color: var(--error)' : 'color: var(--success)';
            let buyColor = data.can_buy ? 'color: var(--success)' : 'color: var(--error)';
            let sellColor = data.can_sell ? 'color: var(--success)' : 'color: var(--error)';
            
            let details = '';
            if (data.details) {
                details = '<h3>Details:</h3><ul>';
                for (const [key, value] of Object.entries(data.details)) {
                    details += `<li>${key}: ${value}</li>`;
                }
                details += '</ul>';
            }
            
            showModal('Token Validation Results', `
                <p>Token Address: ${data.token_address}</p>
                <p>Network: ${getNetworkName(data.chain_id)}</p>
                <p>Honeypot Status: <span style="${statusColor}">${data.is_honeypot ? 'HONEYPOT DETECTED' : 'SAFE'}</span></p>
                <p>Can Buy: <span style="${buyColor}">${data.can_buy ? 'YES' : 'NO'}</span></p>
                <p>Can Sell: <span style="${sellColor}">${data.can_sell ? 'YES' : 'NO'}</span></p>
                ${details}
            `, 'Close');
            
            elements.modalCancel.style.display = 'none';
            elements.modalConfirm.style.display = 'inline-flex';
        } else {
            throw new Error(data.error || 'Token validation failed');
        }
    } catch (error) {
        console.error('Token validation error:', error);
        showToast(`Token validation failed: ${error.message}`, 'error');
        hideModal();
    }
}

// Execute trade
async function executeTrade() {
    try {
        if (!state.wallet.connected) {
            showToast('Wallet not connected', 'error');
            return;
        }
        
        if (state.wallet.readOnly) {
            showToast('Wallet is in read-only mode', 'error');
            return;
        }
        
        const tokenAddress = elements.tradeTokenAddress.value.trim();
        if (!tokenAddress) {
            showToast('Token address is required', 'error');
            return;
        }
        
        const chainId = parseInt(elements.tradeNetwork.value);
        const dexId = elements.tradeDex.value;
        
        let amount, baseTokenAddress, percent;
        
        if (state.tradeAction === 'buy') {
            amount = elements.buyAmount.value;
            if (!amount || parseFloat(amount) <= 0) {
                showToast('Amount must be greater than 0', 'error');
                return;
            }
            baseTokenAddress = elements.buyBaseToken.value;
        } else { // sell
            amount = elements.sellAmount.value;
            percent = elements.sellPercent.value;
            if (!amount && !percent) {
                showToast('Amount or percent is required', 'error');
                return;
            }
            baseTokenAddress = elements.sellBaseToken.value;
        }
        
        // Prepare payload
        const payload = {
            token_address: tokenAddress,
            chain_id: chainId,
            dex_id: dexId,
            slippage: state.slippage,
            auto_gas: true,
            gas_speed: state.gasSpeed,
            base_token_address: baseTokenAddress
        };
        
        if (state.tradeAction === 'buy') {
            payload.amount = amount;
        } else { // sell
            if (amount) {
                payload.amount = amount;
            } else if (percent) {
                payload.percent = percent;
            }
        }
        
        // Confirm trade
        const actionText = state.tradeAction === 'buy' ? 'Buy' : 'Sell';
        const amountText = state.tradeAction === 'buy' ? 
            `${amount} ${getTokenSymbol(baseTokenAddress)}` : 
            (amount ? `${amount} tokens` : `${percent}% of holdings`);
        
        showModal(`Confirm ${actionText}`, `
            <p>You are about to ${state.tradeAction} ${amountText} on ${getDexName(dexId)} (${getNetworkName(chainId)}).</p>
            <p>Token Address: ${tokenAddress}</p>
            <p>Slippage: ${state.slippage}%</p>
            <p>Gas Speed: ${state.gasSpeed}</p>
            <p>Are you sure you want to proceed?</p>
        `, 'Confirm', async () => {
            try {
                hideModal();
                showToast(`Preparing ${state.tradeAction} transaction...`, 'info');
                
                const endpoint = state.tradeAction === 'buy' ? 'quick_buy' : 'quick_sell';
                const response = await fetch(`${config.apiBaseUrl}/api/${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast(data.message, 'success');
                    
                    // Show transaction details
                    const txUrl = `${getExplorerUrl(chainId)}/tx/${data.transaction_hash}`;
                    
                    showModal('Transaction Successful', `
                        <p>${data.message}</p>
                        <p>Transaction Hash: <a href="${txUrl}" target="_blank">${data.transaction_hash.substring(0, 10)}...${data.transaction_hash.substring(data.transaction_hash.length - 8)}</a></p>
                        <p>Gas Used: ${data.gas_used}</p>
                    `, 'Close');
                    
                    elements.modalCancel.style.display = 'none';
                    
                    // Reset form
                    if (state.tradeAction === 'buy') {
                        elements.buyAmount.value = '';
                    } else {
                        elements.sellAmount.value = '';
                        elements.sellPercent.value = '';
                    }
                    
                    // Load wallet balances
                    loadWalletBalances();
                } else {
                    throw new Error(data.error || `${actionText} transaction failed`);
                }
            } catch (error) {
                console.error(`${actionText} error:`, error);
                showToast(`${actionText} failed: ${error.message}`, 'error');
            }
        });
    } catch (error) {
        console.error('Execute trade error:', error);
        showToast(`Trade execution failed: ${error.message}`, 'error');
    }
}

// Check token price
async function checkPrice() {
    try {
        const tokenAddress = elements.priceCheckTokenAddress.value.trim();
        if (!tokenAddress) {
            showToast('Token address is required', 'error');
            return;
        }
        
        const chainId = parseInt(elements.priceCheckNetwork.value);
        const dexId = elements.priceCheckDex.value;
        
        showToast('Checking price...', 'info');
        
        const response = await fetch(`${config.apiBaseUrl}/api/price_feed?token_address=${tokenAddress}&chain_id=${chainId}&dex_id=${dexId}`);
        const data = await response.json();
        
        if (data.success) {
            elements.priceResult.style.display = 'block';
            elements.priceTokenSymbol.textContent = data.token_symbol;
            elements.priceValue.textContent = data.price_formatted;
            
            // Add custom token to local storage if not exists
            if (!state.customTokens[tokenAddress]) {
                state.customTokens[tokenAddress] = {
                    symbol: data.token_symbol,
                    chainId: chainId
                };
                
                localStorage.setItem('customTokens', JSON.stringify(state.customTokens));
            }
        } else {
            throw new Error(data.error || 'Failed to check price');
        }
    } catch (error) {
        console.error('Price check error:', error);
        showToast(`Price check failed: ${error.message}`, 'error');
    }
}

// Load available strategies
async function loadAvailableStrategies() {
    try {
        const response = await fetch(`${config.apiBaseUrl}/api/select_strategy`);
        const data = await response.json();
        
        if (data.success) {
            state.strategyData = data.strategies;
        } else {
            throw new Error(data.error || 'Failed to load strategies');
        }
    } catch (error) {
        console.error('Load strategies error:', error);
        showToast(`Failed to load strategies: ${error.message}`, 'error');
    }
}

// Update strategy form based on selected strategy
function updateStrategyForm() {
    const strategyType = elements.strategyType.value;
    
    if (!strategyType || !state.strategyData) {
        elements.strategyDescription.innerHTML = '<p>Select a strategy to see description</p>';
        elements.strategyForm.style.display = 'none';
        elements.startStrategyBtn.disabled = true;
        return;
    }
    
    const strategy = state.strategyData[strategyType];
    
    elements.strategyDescription.innerHTML = `<p>${strategy.description}</p>`;
    elements.strategyForm.style.display = 'block';
    elements.startStrategyBtn.disabled = false;
    
    // Show/hide target DEX for arbitrage
    if (strategyType === 'arbitrage') {
        elements.strategyTargetDexGroup.style.display = 'block';
    } else {
        elements.strategyTargetDexGroup.style.display = 'none';
    }
    
    // Set default profit target and stop loss based on strategy
    if (strategyType === 'sniper') {
        elements.strategyProfitTarget.value = '50.0';
        elements.strategyStopLoss.value = '20.0';
        elements.strategySlippage.value = '3.0';
    } else if (strategyType === 'scalping') {
        elements.strategyProfitTarget.value = '2.0';
        elements.strategyStopLoss.value = '1.0';
        elements.strategySlippage.value = '1.0';
    } else if (strategyType === 'swing') {
        elements.strategyProfitTarget.value = '20.0';
        elements.strategyStopLoss.value = '10.0';
        elements.strategySlippage.value = '1.0';
    } else if (strategyType === 'arbitrage') {
        elements.strategyProfitTarget.value = '1.0';
        elements.strategyStopLoss.value = '0.5';
        elements.strategySlippage.value = '0.5';
    }
    
    // Add strategy-specific parameters
    let specificParamsHtml = '';
    
    if (strategyType === 'sniper') {
        specificParamsHtml = `
            <div class="form-group">
                <label>Auto-sell Time (seconds, 0 = disabled)</label>
                <input type="number" id="strategy-auto-sell-time" value="0" min="0" step="1" />
            </div>
            <div class="form-group">
                <label>Gas Multiplier</label>
                <input type="number" id="strategy-gas-multiplier" value="1.5" min="1.0" step="0.1" />
            </div>
        `;
    } else if (strategyType === 'scalping') {
        specificParamsHtml = `
            <div class="form-group">
                <label>Price Check Interval (seconds)</label>
                <input type="number" id="strategy-price-check-interval" value="5" min="1" step="1" />
            </div>
            <div class="form-group">
                <label>Max Trades Per Day</label>
                <input type="number" id="strategy-max-trades" value="10" min="1" step="1" />
            </div>
            <div class="form-group">
                <label>Max Gas Cost (%)</label>
                <input type="number" id="strategy-max-gas-cost" value="5.0" min="0.1" step="0.1" />
            </div>
        `;
    } else if (strategyType === 'swing') {
        specificParamsHtml = `
            <div class="form-group">
                <label>Price Check Interval (seconds)</label>
                <input type="number" id="strategy-price-check-interval" value="300" min="1" step="1" />
            </div>
            <div class="form-group">
                <label>Trend Strength Threshold</label>
                <input type="number" id="strategy-trend-strength" value="5.0" min="0.1" step="0.1" />
            </div>
            <div class="form-group">
                <label>Max Hold Time (days)</label>
                <input type="number" id="strategy-max-hold-time" value="7" min="1" step="1" />
            </div>
        `;
    } else if (strategyType === 'arbitrage') {
        specificParamsHtml = `
            <div class="form-group">
                <label>Min Profit Threshold (%)</label>
                <input type="number" id="strategy-min-profit" value="1.0" min="0.1" step="0.1" />
            </div>
            <div class="form-group">
                <label>Check Interval (seconds)</label>
                <input type="number" id="strategy-check-interval" value="30" min="1" step="1" />
            </div>
            <div class="form-group">
                <label>Max Concurrent Arbitrages</label>
                <input type="number" id="strategy-max-arbs" value="1" min="1" step="1" />
            </div>
        `;
    }
    
    elements.strategySpecificParams.innerHTML = specificParamsHtml;
}

// Start a trading strategy
async function startStrategy() {
    try {
        if (!state.wallet.connected) {
            showToast('Wallet not connected', 'error');
            return;
        }
        
        if (state.wallet.readOnly) {
            showToast('Wallet is in read-only mode', 'error');
            return;
        }
        
        const strategyType = elements.strategyType.value;
        if (!strategyType) {
            showToast('Strategy type is required', 'error');
            return;
        }
        
        const tokenAddress = elements.strategyTokenAddress.value.trim();
        if (!tokenAddress) {
            showToast('Token address is required', 'error');
            return;
        }
        
        const amount = elements.strategyAmount.value;
        if (!amount || parseFloat(amount) <= 0) {
            showToast('Amount must be greater than 0', 'error');
            return;
        }
        
        const chainId = parseInt(elements.strategyNetwork.value);
        const dexId = elements.strategyDex.value;
        const baseTokenAddress = elements.strategyBaseToken.value;
        const slippage = parseFloat(elements.strategySlippage.value);
        const profitTarget = parseFloat(elements.strategyProfitTarget.value);
        const stopLoss = parseFloat(elements.strategyStopLoss.value);
        const trailingStop = elements.strategyTrailingStop.value === 'true';
        
        // Prepare payload
        const payload = {
            strategy_type: strategyType,
            token_address: tokenAddress,
            chain_id: chainId,
            dex_id: dexId,
            base_token_address: baseTokenAddress,
            amount: amount,
            slippage: slippage,
            profit_target: profitTarget,
            stop_loss: stopLoss,
            trailing_stop: trailingStop,
            custom_params: {}
        };
        
        // Add strategy-specific parameters
        if (strategyType === 'sniper') {
            payload.custom_params.auto_sell_time = parseInt(document.getElementById('strategy-auto-sell-time').value);
            payload.custom_params.gas_multiplier = parseFloat(document.getElementById('strategy-gas-multiplier').value);
        } else if (strategyType === 'scalping') {
            payload.custom_params.price_check_interval = parseInt(document.getElementById('strategy-price-check-interval').value);
            payload.custom_params.max_trades_per_day = parseInt(document.getElementById('strategy-max-trades').value);
            payload.custom_params.max_gas_cost_percent = parseFloat(document.getElementById('strategy-max-gas-cost').value);
        } else if (strategyType === 'swing') {
            payload.custom_params.price_check_interval = parseInt(document.getElementById('strategy-price-check-interval').value);
            payload.custom_params.trend_strength_threshold = parseFloat(document.getElementById('strategy-trend-strength').value);
            payload.custom_params.max_hold_time = parseInt(document.getElementById('strategy-max-hold-time').value) * 86400; // days to seconds
        } else if (strategyType === 'arbitrage') {
            payload.custom_params.target_dex_id = elements.strategyTargetDex.value;
            payload.custom_params.min_profit_threshold = parseFloat(document.getElementById('strategy-min-profit').value);
            payload.custom_params.check_interval = parseInt(document.getElementById('strategy-check-interval').value);
            payload.custom_params.max_concurrent_arbs = parseInt(document.getElementById('strategy-max-arbs').value);
        }
        
        // Confirm strategy
        showModal(`Confirm ${strategyType.charAt(0).toUpperCase() + strategyType.slice(1)} Strategy`, `
            <p>You are about to start a ${strategyType} strategy with the following parameters:</p>
            <p>Token: ${tokenAddress}</p>
            <p>Amount: ${amount} ${getTokenSymbol(baseTokenAddress)}</p>
            <p>Network: ${getNetworkName(chainId)}</p>
            <p>DEX: ${getDexName(dexId)}</p>
            <p>Profit Target: ${profitTarget}%</p>
            <p>Stop Loss: ${stopLoss}%</p>
            <p>Are you sure you want to proceed?</p>
        `, 'Start Strategy', async () => {
            try {
                hideModal();
                showToast('Starting strategy...', 'info');
                
                const response = await fetch(`${config.apiBaseUrl}/api/start_trade`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast(data.message, 'success');
                    
                    // Reset form
                    elements.strategyType.value = '';
                    elements.strategyTokenAddress.value = '';
                    elements.strategyAmount.value = '';
                    updateStrategyForm();
                    
                    // Load active strategies
                    loadActiveStrategies();
                    
                    // Show strategy details
                    showModal('Strategy Started', `
                        <p>${data.message}</p>
                        <p>Strategy ID: ${data.strategy_id}</p>
                        <p>Status: ${data.status}</p>
                    `, 'Close');
                    
                    elements.modalCancel.style.display = 'none';
                } else {
                    throw new Error(data.error || 'Failed to start strategy');
                }
            } catch (error) {
                console.error('Start strategy error:', error);
                showToast(`Failed to start strategy: ${error.message}`, 'error');
            }
        });
    } catch (error) {
        console.error('Start strategy error:', error);
        showToast(`Failed to start strategy: ${error.message}`, 'error');
    }
}

// Load active strategies
async function loadActiveStrategies() {
    try {
        if (!state.wallet.connected) {
            return;
        }
        
        elements.reloadStrategies.classList.add('rotating');
        
        const response = await fetch(`${config.apiBaseUrl}/api/strategy_status`);
        const data = await response.json();
        
        if (data.success) {
            const strategies = data.strategies;
            state.activeStrategies = strategies;
            
            if (strategies.length > 0) {
                let strategiesHtml = '<div class="strategies-list">';
                
                for (const strategy of strategies) {
                    const statusClass = strategy.status === 'running' ? 'success' : (strategy.status === 'error' ? 'error' : 'warning');
                    
                    strategiesHtml += `
                        <div class="strategy-item">
                            <div class="strategy-header">
                                <h3>${strategy.id}</h3>
                                <span class="status-badge ${statusClass}">${strategy.status}</span>
                            </div>
                            <div class="strategy-details">
                                <p>Type: ${strategy.type || 'N/A'}</p>
                                <p>Token: ${strategy.token_address ? `${strategy.token_address.substring(0, 6)}...${strategy.token_address.substring(strategy.token_address.length - 4)}` : 'N/A'}</p>
                                <p>Started: ${strategy.start_time ? new Date(strategy.start_time * 1000).toLocaleString() : 'N/A'}</p>
                                ${strategy.stop_time ? `<p>Stopped: ${new Date(strategy.stop_time * 1000).toLocaleString()}</p>` : ''}
                            </div>
                            <div class="strategy-actions">
                                <button class="btn secondary stop-strategy-btn" data-id="${strategy.id}" ${strategy.status !== 'running' ? 'disabled' : ''}>Stop</button>
                                <button class="btn secondary force-sell-btn" data-id="${strategy.id}" ${strategy.status !== 'running' ? 'disabled' : ''}>Force Sell</button>
                            </div>
                        </div>
                    `;
                }
                
                strategiesHtml += '</div>';
                elements.activeStrategiesList.innerHTML = strategiesHtml;
                
                // Add event listeners for stop and force sell buttons
                document.querySelectorAll('.stop-strategy-btn').forEach(btn => {
                    btn.addEventListener('click', () => stopStrategy(btn.dataset.id, false));
                });
                
                document.querySelectorAll('.force-sell-btn').forEach(btn => {
                    btn.addEventListener('click', () => stopStrategy(btn.dataset.id, true));
                });
            } else {
                elements.activeStrategiesList.innerHTML = '<p class="empty-message">No active strategies</p>';
            }
            
            // Update dashboard count
            elements.activeStrategiesCount.textContent = strategies.length;
            
            // Update active trades list in dashboard
            const activeTradesList = document.getElementById('active-trades-list');
            if (strategies.filter(s => s.status === 'running').length > 0) {
                let tradesHtml = '<div class="active-trades">';
                
                for (const strategy of strategies.filter(s => s.status === 'running')) {
                    tradesHtml += `
                        <div class="active-trade">
                            <p>${strategy.type || 'Unknown'}: ${strategy.token_address ? `${strategy.token_address.substring(0, 6)}...${strategy.token_address.substring(strategy.token_address.length - 4)}` : 'N/A'}</p>
                        </div>
                    `;
                }
                
                tradesHtml += '</div>';
                activeTradesList.innerHTML = tradesHtml;
            } else {
                activeTradesList.innerHTML = '<p class="empty-message">No active trades</p>';
            }
        } else {
            throw new Error(data.error || 'Failed to load active strategies');
        }
    } catch (error) {
        console.error('Load active strategies error:', error);
        showToast(`Failed to load active strategies: ${error.message}`, 'error');
    } finally {
        elements.reloadStrategies.classList.remove('rotating');
    }
}

// Stop a strategy
async function stopStrategy(strategyId, forceSell = false) {
    try {
        if (!state.wallet.connected) {
            showToast('Wallet not connected', 'error');
            return;
        }
        
        if (state.wallet.readOnly) {
            showToast('Wallet is in read-only mode', 'error');
            return;
        }
        
        const action = forceSell ? 'force sell' : 'stop';
        
        showModal(`Confirm ${action}`, `
            <p>Are you sure you want to ${action} strategy ${strategyId}?</p>
            ${forceSell ? '<p>This will immediately sell all tokens held by this strategy.</p>' : ''}
        `, 'Confirm', async () => {
            try {
                hideModal();
                showToast(`${action.charAt(0).toUpperCase() + action.slice(1)}ping strategy...`, 'info');
                
                const response = await fetch(`${config.apiBaseUrl}/api/stop_trade`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        strategy_id: strategyId,
                        force_sell: forceSell
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast(data.message, 'success');
                    loadActiveStrategies();
                } else {
                    throw new Error(data.error || `Failed to ${action} strategy`);
                }
            } catch (error) {
                console.error(`${action} strategy error:`, error);
                showToast(`Failed to ${action} strategy: ${error.message}`, 'error');
            }
        });
    } catch (error) {
        console.error('Stop strategy error:', error);
        showToast(`Failed to stop strategy: ${error.message}`, 'error');
    }
}

// Save settings
function saveSettings() {
    try {
        const defaultChainId = elements.defaultNetwork.value;
        const defaultDexId = elements.defaultDex.value;
        const defaultSlippage = elements.defaultSlippage.value;
        const defaultGasSpeed = elements.defaultGasSpeed.value;
        const theme = elements.themeSelector.value;
        
        localStorage.setItem('defaultChainId', defaultChainId);
        localStorage.setItem('defaultDexId', defaultDexId);
        localStorage.setItem('defaultSlippage', defaultSlippage);
        localStorage.setItem('defaultGasSpeed', defaultGasSpeed);
        localStorage.setItem('theme', theme);
        
        config.defaultChainId = defaultChainId;
        config.defaultDexId = defaultDexId;
        config.defaultSlippage = defaultSlippage;
        config.defaultGasSpeed = defaultGasSpeed;
        config.theme = theme;
        
        applyTheme(theme);
        
        showToast('Settings saved successfully', 'success');
    } catch (error) {
        console.error('Save settings error:', error);
        showToast('Failed to save settings', 'error');
    }
}

// Update API URL
function updateApiUrl() {
    try {
        const apiUrl = elements.customApiUrl.value.trim();
        
        if (!apiUrl) {
            showToast('API URL is required', 'error');
            return;
        }
        
        localStorage.setItem('apiBaseUrl', apiUrl);
        config.apiBaseUrl = apiUrl;
        elements.apiUrl.textContent = apiUrl;
        
        showToast('API URL updated successfully', 'success');
        
        // Check server status with new URL
        checkServerStatus();
    } catch (error) {
        console.error('Update API URL error:', error);
        showToast('Failed to update API URL', 'error');
    }
}

// Modal functions
function showModal(title, content, confirmText = 'Confirm', confirmCallback = null) {
    elements.modalTitle.textContent = title;
    elements.modalBody.innerHTML = content;
    
    if (confirmText) {
        elements.modalConfirm.textContent = confirmText;
        elements.modalConfirm.style.display = 'inline-flex';
    } else {
        elements.modalConfirm.style.display = 'none';
    }
    
    if (confirmCallback) {
        elements.modalConfirm.onclick = confirmCallback;
    }
    
    elements.modal.classList.add('show');
    elements.modalCancel.style.display = 'inline-flex';
}

function hideModal() {
    elements.modal.classList.remove('show');
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '';
    switch (type) {
        case 'success':
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case 'error':
            icon = '<i class="fas fa-exclamation-circle"></i>';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        default:
            icon = '<i class="fas fa-info-circle"></i>';
    }
    
    toast.innerHTML = `
        ${icon}
        <div class="toast-content">${message}</div>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Remove after animation completes
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Helper functions
function getNetworkName(chainId) {
    switch (parseInt(chainId)) {
        case 1:
            return 'Ethereum Mainnet';
        case 56:
            return 'BNB Smart Chain';
        case 137:
            return 'Polygon';
        case 42161:
            return 'Arbitrum One';
        default:
            return `Chain ID ${chainId}`;
    }
}

function getDexName(dexId) {
    switch (dexId) {
        case 'uniswap_v2':
            return 'Uniswap V2';
        case 'uniswap_v3':
            return 'Uniswap V3';
        case 'pancakeswap_v2':
            return 'PancakeSwap V2';
        case 'sushiswap':
            return 'SushiSwap';
        default:
            return dexId;
    }
}

function getTokenSymbol(address) {
    if (address === '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE') {
        switch (parseInt(state.wallet.chainId)) {
            case 1:
            case 42161:
                return 'ETH';
            case 56:
                return 'BNB';
            case 137:
                return 'MATIC';
            default:
                return 'ETH';
        }
    }
    
    return state.customTokens[address]?.symbol || 'Unknown';
}

function getExplorerUrl(chainId) {
    switch (parseInt(chainId)) {
        case 1:
            return 'https://etherscan.io';
        case 56:
            return 'https://bscscan.com';
        case 137:
            return 'https://polygonscan.com';
        case 42161:
            return 'https://arbiscan.io';
        default:
            return '';
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', init);
