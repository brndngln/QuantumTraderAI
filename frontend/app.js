// Constants
const API_URL = 'http://localhost:8000/api';
const RETRY_DELAY = 1000; // 1 second
const MAX_RETRIES = 3;

// Error Handling
const handleError = (error, message = 'An error occurred') => {
    console.error(error);
let lastFailureTime = 0;
let circuitOpen = false;

// Cache for API responses
const apiCache = new Map();
const cacheTTL = 300000; // 5 minutes

async function apiCall(endpoint, options = {}) {
    // Circuit breaker check
    const now = Date.now();
    if (circuitOpen) {
        if (now - lastFailureTime < CIRCUIT_BREAKER_WINDOW) {
            throw new Error('Service temporarily unavailable due to high error rate');
        }
        circuitOpen = false;
    }

    // Check cache first
    const cacheKey = `${endpoint}-${JSON.stringify(options)}`;
    const cachedResponse = apiCache.get(cacheKey);
    if (cachedResponse && now - cachedResponse.timestamp < cacheTTL) {
        return cachedResponse.data;
    }

    // Add default headers
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Client-Version': '1.0.0',
        'X-Client-Platform': 'web',
        'X-Client-Timestamp': now
    };

    // Add authentication token if available
    if (localStorage.getItem('authToken')) {
        defaultHeaders['Authorization'] = `Bearer ${localStorage.getItem('authToken')}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...(options.headers || {})
        },
        credentials: 'include',
        timeout: REQUEST_TIMEOUT
    };

    // Retry logic with exponential backoff
    let retries = 0;
    let delay = RETRY_DELAY;
    while (retries < MAX_RETRIES) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

            const response = await fetch(`${API_URL}${endpoint}`, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'API request failed');
            }

            const data = await response.json();

            // Cache successful response
            apiCache.set(cacheKey, {
                data,
                timestamp: now
            });

            // Reset failure count on successful request
            failureCount = 0;
            circuitOpen = false;
            return data;
        } catch (error) {
            retries++;
            if (error.name === 'AbortError') {
                throw new Error('Request timed out');
            }

            if (retries === MAX_RETRIES) {
                // Update failure count for circuit breaker
                failureCount++;
                lastFailureTime = now;
                circuitOpen = true;
                throw error;
            }

            // Exponential backoff
            await new Promise(resolve => setTimeout(resolve, delay));
            delay *= 2;
        }
    }
}

// Enhanced error handling
function handleError(error) {
    console.error('API Error:', error);
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = error.message || 'An error occurred';
        errorDiv.style.display = 'block';

        // Log error to Sentry
        if (window.Sentry) {
            Sentry.captureException(error);
        }
    }
}

// Improved theme switching with persistence
function toggleTheme() {
    const body = document.body;
    const isDark = body.classList.contains('dark');
    body.classList.toggle('dark');

    // Update meta theme-color
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
        meta.content = isDark ? '#1a1a1a' : '#ffffff';
    }

    // Persist theme preference
    localStorage.setItem('theme', isDark ? 'light' : 'dark');

    // Send analytics event
    if (window.analytics) {
        analytics.track('theme_changed', {
            theme: isDark ? 'light' : 'dark'
        });
    }
}

// Initialize theme with fallback
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
        document.body.classList.toggle('dark', savedTheme === 'dark');
    } else {
        document.body.classList.toggle('dark', prefersDark);
    }

    // Update meta theme-color
    const meta = document.createElement('meta');
    meta.name = 'theme-color';
    meta.content = document.body.classList.contains('dark') ? '#1a1a1a' : '#ffffff';
    document.head.appendChild(meta);

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            document.body.classList.toggle('dark', e.matches);
            meta.content = e.matches ? '#1a1a1a' : '#ffffff';
        }
    });
}

// Enhanced trading form handling with validation
async function executeTrade() {
    const symbol = document.getElementById('symbol').value.trim().toUpperCase();
    const positionSize = parseFloat(document.getElementById('position-size').value);
    const strategy = document.getElementById('strategy').value;
    const leverage = parseFloat(document.getElementById('leverage').value || 1);
    const stopLoss = parseFloat(document.getElementById('stop-loss').value);
    const takeProfit = parseFloat(document.getElementById('take-profit').value);

    // Input validation
    if (!symbol || !positionSize || !strategy) {
        handleError(new Error('Please fill in all required fields'));
        return;
    }

    if (isNaN(positionSize) || positionSize <= 0) {
        handleError(new Error('Position size must be a positive number'));
        return;
    }

    if (leverage && (isNaN(leverage) || leverage <= 0 || leverage > 100)) {
        handleError(new Error('Leverage must be between 1 and 100'));
        return;
    }
// Generate unique client ID
function generateClientId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2);
    const clientId = `client_${timestamp}_${random}`;
    localStorage.setItem('clientId', clientId);
    return clientId;
}

// Enhanced performance chart with multiple metrics
async function updatePerformanceChart() {
    try {
        const data = await apiCall('/metrics/performance');
        const chartDiv = document.getElementById('performance-chart');
        if (!chartDiv) return;

        // Initialize Plotly chart with multiple metrics
        const layout = {
            title: 'Trading Performance Metrics',
            height: 600,
            showlegend: true,
            xaxis: {
                title: 'Time',
                type: 'date'
            },
            yaxis: {
                title: 'Value',
                domain: [0.3, 1]
            },
            yaxis2: {
                title: 'Drawdown',
                domain: [0, 0.25]
            }
        };

        const traces = [
            // Performance trace
            {
                x: data.timestamps,
                y: data.performance,
                type: 'scatter',
                mode: 'lines',
                name: 'Performance',
                yaxis: 'y1'
            },
            // Drawdown trace
            {
                x: data.timestamps,
                y: data.drawdown,
                type: 'scatter',
                mode: 'lines',
                name: 'Drawdown',
                yaxis: 'y2'
            },
            // Sharpe ratio trace
            {
                x: data.timestamps,
                y: data.sharpe,
                type: 'scatter',
                mode: 'lines',
                name: 'Sharpe Ratio',
                yaxis: 'y1'
            }
        ];

        // Add annotations for key metrics
        const annotations = [];
        if (data.metrics) {
            annotations.push(
                {
                    x: 0.5,
                    y: 0.95,
                    text: `Sharpe Ratio: ${data.metrics.sharpe_ratio.toFixed(2)}`,
                    showarrow: false,
                    font: { size: 12 }
                },
                {
                    x: 0.5,
                    y: 0.9,
                    text: `Max Drawdown: ${data.metrics.max_drawdown.toFixed(2)}%`,
                    showarrow: false,
                    font: { size: 12 }
                },
                {
                    x: 0.5,
                    y: 0.85,
                    text: `Annual Return: ${data.metrics.annual_return.toFixed(2)}%`,
                    showarrow: false,
                    font: { size: 12 }
                }
            );
        }

        layout.annotations = annotations;

        Plotly.newPlot('performance-chart', traces, layout);

        // Add hover event for detailed metrics
        const plotDiv = document.getElementById('performance-chart');
        plotDiv.on('plotly_hover', (eventData) => {
            const point = eventData.points[0];
            if (point) {
                const metrics = {
                    timestamp: point.x,
                    performance: point.y,
                    drawdown: data.drawdown[data.timestamps.indexOf(point.x)]
                };
                updateMetricsTooltip(metrics);
            }
        });
    } catch (error) {
        handleError(error);
    }
}

// Update metrics tooltip
function updateMetricsTooltip(metrics) {
    const tooltip = document.getElementById('metrics-tooltip');
    if (!tooltip) return;

    tooltip.innerHTML = `
        <div class="tooltip-content">
            <p><strong>Timestamp:</strong> ${new Date(metrics.timestamp).toLocaleString()}</p>
            <p><strong>Performance:</strong> ${metrics.performance.toFixed(2)}%</p>
            <p><strong>Drawdown:</strong> ${metrics.drawdown.toFixed(2)}%</p>
        </div>
    `;
    
    // Position tooltip
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.top = `${rect.top - 50}px`;
    tooltip.style.display = 'block';
}

// Initialize app with enhanced features
async function initApp() {
    try {
        // Initialize theme
        initTheme();
        
        // Initialize performance chart
        await updatePerformanceChart();
        
        // Set up event listeners
        document.getElementById('theme-toggle').onclick = toggleTheme;
        document.getElementById('execute-trade').onclick = executeTrade;
        
        // Initialize analytics
        if (window.analytics) {
            analytics.identify(localStorage.getItem('clientId') || generateClientId());
        }
        
        // Initialize Sentry
        if (window.Sentry) {
            Sentry.init({
                dsn: 'your_sentry_dsn_here',
                integrations: [
                    new Sentry.BrowserTracing(),
                    new Sentry.Replay()
                ],
                tracesSampleRate: 1.0,
                replaysSessionSampleRate: 0.1,
                replaysOnErrorSampleRate: 1.0
            });
        }
    } catch (error) {
        handleError(error);
    }
}

// Run initialization with error boundary
window.addEventListener('load', () => {
    try {
        initApp();
    } catch (error) {
        handleError(error);
    }
});

// Error Monitoring
async function sendErrorToBackend(error) {
    try {
        const clientId = localStorage.getItem('clientId') || generateClientId();
        await apiCall('/errors/report', {
            method: 'POST',
            body: JSON.stringify({
                error_message: error.message,
                stack_trace: error.stack,
                timestamp: Date.now(),
                client_id: clientId,
                user_agent: navigator.userAgent,
                page_url: window.location.href
            })
        });
    } catch (reportError) {
        console.error('Failed to report error to backend:', reportError);
    }
}

// Initialize UI
function initUI() {
    // Initialize chart
    updatePerformanceChart();
    
    // Initialize form handling
    document.querySelector('form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await executeTrade();
    });
    
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.dataset.theme = savedTheme;
    
    // Add theme toggle button
    const themeToggle = document.createElement('button');
    themeToggle.className = 'fixed bottom-4 right-4 p-4 bg-white rounded-full shadow-lg';
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggle.addEventListener('click', toggleTheme);
    document.body.appendChild(themeToggle);
}

// Run initialization
window.addEventListener('load', () => {
    try {
        initUI();
    } catch (error) {
        handleError(error);
    }
});
// Constants
const API_BASE_URL = 'https://api.quantumtrader.ai'
const MAX_RETRIES = 5
const RETRY_DELAY = 1000
const CIRCUIT_BREAKER_WINDOW = 60000
const CIRCUIT_BREAKER_THRESHOLD = 5
const REQUEST_TIMEOUT = 30000
const cacheTTL = 300000 // 5 minutes

// Global state
let failureCount = 0
let lastFailureTime = 0
let circuitOpen = false

// Cache for API responses
const apiCache = new Map()

// API client with enhanced retry and circuit breaker
async function apiCall(endpoint, options = {}) {
    // Circuit breaker check
    const now = Date.now()
    if (circuitOpen) {
        if (now - lastFailureTime < CIRCUIT_BREAKER_WINDOW) {
            throw new Error('Service temporarily unavailable due to high error rate')
        }
        circuitOpen = false
    }

    // Check cache first
    const cacheKey = `${endpoint}-${JSON.stringify(options)}`
    const cachedResponse = apiCache.get(cacheKey)
    if (cachedResponse && now - cachedResponse.timestamp < cacheTTL) {
        return cachedResponse.data
    }

    // Add default headers
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Client-Version': '1.0.0',
        'X-Client-Platform': 'web',
        'X-Client-Timestamp': now
    }

    // Add authentication token if available
    if (localStorage.getItem('authToken')) {
        defaultHeaders['Authorization'] = `Bearer ${localStorage.getItem('authToken')}`
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...(options.headers || {})
        },
        credentials: 'include',
        timeout: REQUEST_TIMEOUT
    }

    // Retry logic with exponential backoff
    let retries = 0
    let delay = RETRY_DELAY
    while (retries < MAX_RETRIES) {
        try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)
            
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...config,
                signal: controller.signal
            })
            
            clearTimeout(timeoutId)
            
            if (!response.ok) {
                const error = await response.json()
                throw new Error(error.detail || 'API request failed')
            }

            const data = await response.json()
            
            // Cache successful response
            apiCache.set(cacheKey, {
                data,
                timestamp: now
            })

            // Reset failure count on successful request
            failureCount = 0
            circuitOpen = false
            return data
        } catch (error) {
            retries++
            if (error.name === 'AbortError') {
                throw new Error('Request timed out')
            }
            
            if (retries === MAX_RETRIES) {
                // Update failure count for circuit breaker
                failureCount++
                lastFailureTime = now
                circuitOpen = true
                throw error
            }
            
            // Exponential backoff
            await new Promise(resolve => setTimeout(resolve, delay))
            delay *= 2
        }
    }
}

// Enhanced error handling
function handleError(error) {
    console.error('API Error:', error)
    const errorDiv = document.getElementById('error-message')
    if (errorDiv) {
        errorDiv.textContent = error.message || 'An error occurred'
        errorDiv.style.display = 'block'
        
        // Log error to Sentry
        if (window.Sentry) {
            Sentry.captureException(error)
        }
    }
}

// Improved theme switching with persistence
function toggleTheme() {
    const body = document.body
    const isDark = body.classList.contains('dark')
    body.classList.toggle('dark')
    
    // Update meta theme-color
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
        meta.content = isDark ? '#1a1a1a' : '#ffffff'
    }
    
    // Persist theme preference
    localStorage.setItem('theme', isDark ? 'light' : 'dark')
    
    // Send analytics event
    if (window.analytics) {
        analytics.track('theme_changed', {
            theme: isDark ? 'light' : 'dark'
        })
    }
}

// Initialize theme with fallback
function initTheme() {
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    if (savedTheme) {
        document.body.classList.toggle('dark', savedTheme === 'dark')
    } else {
        document.body.classList.toggle('dark', prefersDark)
    }
    
    // Update meta theme-color
    const meta = document.createElement('meta')
    meta.name = 'theme-color'
    meta.content = document.body.classList.contains('dark') ? '#1a1a1a' : '#ffffff'
    document.head.appendChild(meta)
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            document.body.classList.toggle('dark', e.matches)
            meta.content = e.matches ? '#1a1a1a' : '#ffffff'
        }
    })
}

// Enhanced trading form handling with validation
async function executeTrade() {
    const symbol = document.getElementById('symbol').value.trim().toUpperCase()
    const positionSize = parseFloat(document.getElementById('position-size').value)
    const strategy = document.getElementById('strategy').value
    const leverage = parseFloat(document.getElementById('leverage').value || 1)
    const stopLoss = parseFloat(document.getElementById('stop-loss').value)
    const takeProfit = parseFloat(document.getElementById('take-profit').value)

    // Input validation
    if (!symbol || !positionSize || !strategy) {
        handleError(new Error('Please fill in all required fields'))
        return
    }

    if (isNaN(positionSize) || positionSize <= 0) {
        handleError(new Error('Position size must be a positive number'))
        return
    }

    if (leverage && (isNaN(leverage) || leverage <= 0 || leverage > 100)) {
        handleError(new Error('Leverage must be between 1 and 100'))
        return
    }

    if ((stopLoss || takeProfit) && (isNaN(stopLoss) || isNaN(takeProfit))) {
        handleError(new Error('Stop loss and take profit must be valid numbers'))
        return
    }

    try {
        // Show loading state
        const button = document.getElementById('execute-trade')
        button.disabled = true
        button.textContent = 'Executing...'

        const response = await apiCall('/trading/execute', {
            method: 'POST',
            body: JSON.stringify({
                symbol,
                position_size: positionSize,
                strategy,
                leverage: leverage || 1,
                stop_loss: stopLoss || null,
                take_profit: takeProfit || null,
                client_id: localStorage.getItem('clientId') || generateClientId()
            })
        })

        // Update UI with results
        updateTradeResults(response)
        
        // Track trade execution
        if (window.analytics) {
            analytics.track('trade_executed', {
                strategy,
                symbol,
                position_size: positionSize,
                leverage,
                success: response.success
            })
        }
    } catch (error) {
        handleError(error)
    } finally {
        // Reset button state
        const button = document.getElementById('execute-trade')
        button.disabled = false
        button.textContent = 'Execute Trade'
    }
}

// Generate unique client ID
function generateClientId() {
    const timestamp = Date.now()
    const random = Math.random().toString(36).substring(2)
    const clientId = `client_${timestamp}_${random}`
    localStorage.setItem('clientId', clientId)
    return clientId
}

// Enhanced performance chart with multiple metrics
async function updatePerformanceChart() {
    try {
        const data = await apiCall('/metrics/performance')
        const chartDiv = document.getElementById('performance-chart')
        if (!chartDiv) return

        // Initialize Plotly chart with multiple metrics
        const layout = {
            title: 'Trading Performance Metrics',
            height: 600,
            showlegend: true,
            xaxis: {
                title: 'Time',
                type: 'date'
            },
            yaxis: {
                title: 'Value',
                domain: [0.3, 1]
            },
            yaxis2: {
                title: 'Drawdown',
                domain: [0, 0.25]
            }
        }

        const traces = [
            // Performance trace
            {
                x: data.timestamps,
                y: data.performance,
                type: 'scatter',
                mode: 'lines',
                name: 'Performance',
                yaxis: 'y1'
            },
            // Drawdown trace
            {
                x: data.timestamps,
                y: data.drawdown,
                type: 'scatter',
                mode: 'lines',
                name: 'Drawdown',
                yaxis: 'y2'
            },
            // Sharpe ratio trace
            {
                x: data.timestamps,
                y: data.sharpe,
                type: 'scatter',
                mode: 'lines',
                name: 'Sharpe Ratio',
                yaxis: 'y1'
            }
        ]

        // Add annotations for key metrics
        const annotations = []
        if (data.metrics) {
            annotations.push(
                {
                    x: 0.5,
                    y: 0.95,
                    text: `Sharpe Ratio: ${data.metrics.sharpe_ratio.toFixed(2)}`,
                    showarrow: false,
                    font: { size: 12 }
                },
                {
                    x: 0.5,
                    y: 0.9,
                    text: `Max Drawdown: ${data.metrics.max_drawdown.toFixed(2)}%`,
                    showarrow: false,
                    font: { size: 12 }
                },
                {
                    x: 0.5,
                    y: 0.85,
                    text: `Annual Return: ${data.metrics.annual_return.toFixed(2)}%`,
                    showarrow: false,
                    font: { size: 12 }
                }
            )
        }

        layout.annotations = annotations

        Plotly.newPlot('performance-chart', traces, layout)

        // Add hover event for detailed metrics
        const plotDiv = document.getElementById('performance-chart')
        plotDiv.on('plotly_hover', (eventData) => {
            const point = eventData.points[0]
            if (point) {
                const metrics = {
                    timestamp: point.x,
                    performance: point.y,
                    drawdown: data.drawdown[data.timestamps.indexOf(point.x)]
                }
                updateMetricsTooltip(metrics)
            }
        })
    } catch (error) {
        handleError(error)
    }
}

// Update metrics tooltip
function updateMetricsTooltip(metrics) {
    const tooltip = document.getElementById('metrics-tooltip')
    if (!tooltip) return

    tooltip.innerHTML = `
        <div class="tooltip-content">
            <p><strong>Timestamp:</strong> ${new Date(metrics.timestamp).toLocaleString()}</p>
            <p><strong>Performance:</strong> ${metrics.performance.toFixed(2)}%</p>
            <p><strong>Drawdown:</strong> ${metrics.drawdown.toFixed(2)}%</p>
        </div>
    `
    
    // Position tooltip
    const rect = event.target.getBoundingClientRect()
    tooltip.style.left = `${rect.left + rect.width / 2}px`
    tooltip.style.top = `${rect.top - 50}px`
    tooltip.style.display = 'block'
}

// Initialize app with enhanced features
async function initApp() {
    try {
        // Initialize theme
        initTheme()
        
        // Initialize performance chart
        await updatePerformanceChart()
        
        // Set up event listeners
        document.getElementById('theme-toggle').onclick = toggleTheme
        document.getElementById('execute-trade').onclick = executeTrade
        
        // Initialize analytics
        if (window.analytics) {
            analytics.identify(localStorage.getItem('clientId') || generateClientId())
        }
        
        // Initialize Sentry
        if (window.Sentry) {
            Sentry.init({
                dsn: 'your_sentry_dsn_here',
                integrations: [
                    new Sentry.BrowserTracing(),
                    new Sentry.Replay()
                ],
                tracesSampleRate: 1.0,
                replaysSessionSampleRate: 0.1,
                replaysOnErrorSampleRate: 1.0
            })
        }
    } catch (error) {
        handleError(error)
    }
}

// Run initialization with error boundary
window.addEventListener('load', () => {
    try {
        initApp()
    } catch (error) {
        handleError(error)
    }
})

// Error Monitoring
async function sendErrorToBackend(error) {
    try {
        const clientId = localStorage.getItem('clientId') || generateClientId()
        await apiCall('/errors/report', {
            method: 'POST',
            body: JSON.stringify({
                error_message: error.message,
                stack_trace: error.stack,
                timestamp: Date.now(),
                client_id: clientId,
                user_agent: navigator.userAgent,
                page_url: window.location.href
            })
        })
    } catch (reportError) {
        console.error('Failed to report error to backend:', reportError)
    }
}

// Performance Monitoring
const monitorPerformance = () => {
    if ('performance' in window) {
        const perf = window.performance;
        const timing = perf.timing;
        const navigation = perf.navigation;
        
        // Calculate key performance metrics
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        const domLoadTime = timing.domContentLoadedEventEnd - timing.navigationStart;
        const backendTime = timing.responseEnd - timing.requestStart;
        
        // Send metrics to analytics
        if (window.analytics) {
            analytics.track('performance_metrics', {
                load_time: loadTime,
                dom_load_time: domLoadTime,
                backend_time: backendTime,
                navigation_type: navigation.type,
                timestamp: Date.now()
            });
        }
    }
};

// Initialize performance monitoring
monitorPerformance();

// Export public functions for other modules
export {
    apiCall,
    handleError,
    toggleTheme,
    initTheme,
    executeTrade,
    updatePerformanceChart,
    sendErrorToBackend
};
    // Monitor page load time
    performance.mark('page-load');
    
    // Monitor API response times
    apiClient.request = async (...args) => {
        const start = performance.now();
        const result = await circuitBreaker(apiClient.request, ...args);
        const end = performance.now();
        
        // Log slow requests
        if (end - start > 500) {
            console.warn(`Slow API request: ${args[1]} took ${end - start}ms`);
        }
        
        return result;
    };
};

// Initialize everything
window.addEventListener('load', () => {
    try {
        initUI();
        monitorPerformance();
    } catch (error) {
        handleError(error, 'Failed to initialize application');
    }
});
