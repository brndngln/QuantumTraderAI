import { securityConfig } from '../security/securityConfig';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import cors from 'cors';

// Initialize rate limiter
const limiter = rateLimit(securityConfig.rateLimit);

// Initialize security headers
const securityHeaders = helmet({
    contentSecurityPolicy: {
        directives: securityConfig.csp.directives
    },
    crossOriginEmbedderPolicy: false,
    crossOriginResourcePolicy: false
});

// Initialize CORS
const corsMiddleware = cors(securityConfig.cors);

// Custom headers middleware
const customHeaders = (req, res, next) => {
    Object.entries(securityConfig.headers).forEach(([key, value]) => {
        res.setHeader(key, value);
    });
    next();
};

export { limiter, securityHeaders, corsMiddleware, customHeaders };
