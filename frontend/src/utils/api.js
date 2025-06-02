import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.quantum-trader.com';

// Custom axios instance with security headers
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Client-ID': 'web-client',
        'Accept': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }
});

// Request interceptor for rate limiting
api.interceptors.request.use((config) => {
    // Add timestamp for request tracking
    config.headers['X-Request-Timestamp'] = Date.now();
    
    // Add request ID for better tracking
    config.headers['X-Request-ID'] = Math.random().toString(36).substring(2, 15);
    
    return config;
}, (error) => {
    return Promise.reject(error);
});

// Response interceptor for error handling
api.interceptors.response.use((response) => {
    // Handle success
    return response;
}, (error) => {
    // Handle rate limit errors
    if (error.response?.status === 429) {
        throw new Error('Rate limit exceeded. Please try again later.');
    }
    
    // Handle other errors
    return Promise.reject(error);
});

export default api;
