import React, { Component } from 'react';
import { Alert } from '@mui/material';

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            // Handle rate limit errors
            if (this.state.error.message.includes('Rate limit exceeded')) {
                return (
                    <Alert severity="error" sx={{ mt: 2 }}>
                        Rate limit exceeded. Please try again later.
                    </Alert>
                );
            }
            
            // Handle other errors
            return (
                <Alert severity="error" sx={{ mt: 2 }}>
                    An unexpected error occurred. Please try again later.
                </Alert>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
