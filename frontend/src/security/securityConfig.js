export const securityConfig = {
    // Rate limiting configuration
    rateLimit: {
        windowMs: 15 * 60 * 1000, // 15 minutes
        max: 100, // limit each IP to 100 requests per windowMs
        message: 'Too many requests from this IP, please try again later.',
        standardHeaders: true,
        legacyHeaders: false
    },

    // CORS configuration
    cors: {
        origin: process.env.REACT_APP_API_URL || 'https://api.quantum-trader.com',
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization'],
        credentials: true
    },

    // Content Security Policy
    csp: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://*.google-analytics.com"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            imgSrc: ["'self'", "data:", "https:", "http:"],
            fontSrc: ["'self'", "https://fonts.gstatic.com"],
            connectSrc: ["'self'", "https://api.quantum-trader.com"],
            frameSrc: [],
            objectSrc: [],
            mediaSrc: [],
            childSrc: [],
            formAction: ["'self'"]
        }
    },

    // Security headers
    headers: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
};
