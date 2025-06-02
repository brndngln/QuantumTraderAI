const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.quantum-trader.com';
const API_VERSION = 'v1';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Rate limiting configuration
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_REQUESTS = 100;

let requestCount = 0;
let lastRequestTime = 0;

const checkRateLimit = () => {
    const now = Date.now();
    if (now - lastRequestTime > RATE_LIMIT_WINDOW) {
        requestCount = 0;
    }
    if (requestCount >= MAX_REQUESTS) {
        throw new Error('Rate limit exceeded. Please try again later.');
    }
    requestCount++;
    lastRequestTime = now;
};

const getAuthHeaders = () => ({
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'X-Client-Version': '1.0.0',
    'X-Client-Platform': 'web',
    'X-Client-OS': 'web',
    'X-Client-Device': 'web',
    'X-Client-Id': localStorage.getItem('clientId') || Math.random().toString(36).substring(7)
});

const getErrorDetails = (response) => {
    try {
        return response.json();
    } catch {
        return { message: 'An error occurred' };
    }
};

export const fetchWithTimeout = async (url, options = {}, timeout = 30000) => {
    checkRateLimit();
    
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...getAuthHeaders(),
                ...options.headers
            }
        });

        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw new Error(`Network error: ${error.message}`);
    }
};

const handleResponse = async (response, endpoint) => {
    if (!response.ok) {
        const errorDetails = await getErrorDetails(response);
        throw new Error(`API error (${response.status}): ${errorDetails.message || 'Unknown error'}`);
    }
    return response.json();
};

const retryRequest = async (fn, endpoint, ...args) => {
    let lastError;
    for (let i = 0; i < MAX_RETRIES; i++) {
        try {
            return await fn(endpoint, ...args);
        } catch (error) {
            lastError = error;
            if (i < MAX_RETRIES - 1) {
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
            }
        }
    }
    throw lastError;
};

export const get = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}/${API_VERSION}${endpoint}`;
    return retryRequest(async () => {
        const response = await fetchWithTimeout(url, {
            method: 'GET',
            ...options
        });
        return handleResponse(response, endpoint);
    }, endpoint);
};

export const post = async (endpoint, data, options = {}) => {
    const url = `${API_BASE_URL}/${API_VERSION}${endpoint}`;
    return retryRequest(async () => {
        const response = await fetchWithTimeout(url, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
        return handleResponse(response, endpoint);
    }, endpoint, data);
};

export const put = async (endpoint, data, options = {}) => {
    const url = `${API_BASE_URL}/${API_VERSION}${endpoint}`;
    return retryRequest(async () => {
        const response = await fetchWithTimeout(url, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
        return handleResponse(response, endpoint);
    }, endpoint, data);
};

export const del = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}/${API_VERSION}${endpoint}`;
    return retryRequest(async () => {
        const response = await fetchWithTimeout(url, {
            method: 'DELETE',
            ...options
        });
        return handleResponse(response, endpoint);
    }, endpoint);
};

// Export all methods
export const api = {
    get,
    post,
    put,
    del
};

// Export utility functions
export const clearClientData = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('clientId');
};

export const setToken = (token) => {
    localStorage.setItem('token', token);
};

export const getToken = () => localStorage.getItem('token');
