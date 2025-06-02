import { useState, useEffect } from 'react';

const RATE_LIMIT_WINDOW = 15 * 60 * 1000; // 15 minutes
const MAX_REQUESTS = 100;

export const useRateLimiter = () => {
    const [requests, setRequests] = useState(0);
    const [isLimited, setIsLimited] = useState(false);
    const [lastRequestTime, setLastRequestTime] = useState(0);

    const incrementRequest = () => {
        const now = Date.now();
        
        // Reset counter if window has passed
        if (now - lastRequestTime > RATE_LIMIT_WINDOW) {
            setRequests(1);
            setLastRequestTime(now);
            setIsLimited(false);
            return true;
        }

        // Check if we've hit the limit
        if (requests >= MAX_REQUESTS) {
            setIsLimited(true);
            return false;
        }

        setRequests(prev => prev + 1);
        setLastRequestTime(now);
        return true;
    };

    // Reset counter when window passes
    useEffect(() => {
        const timer = setInterval(() => {
            const now = Date.now();
            if (now - lastRequestTime > RATE_LIMIT_WINDOW) {
                setRequests(0);
                setIsLimited(false);
            }
        }, 1000);

        return () => clearInterval(timer);
    }, [lastRequestTime]);

    return {
        incrementRequest,
        isLimited,
        remainingRequests: MAX_REQUESTS - requests,
        resetTime: Math.ceil((RATE_LIMIT_WINDOW - (Date.now() - lastRequestTime)) / 1000)
    };
};
