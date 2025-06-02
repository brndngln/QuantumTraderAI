from fastapi import FastAPI, APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import json
import os

app = FastAPI(
    title="Quantum AI Trader API",
    description="Advanced AI-powered trading system with quantum computing features",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom API router for documentation
api_router = APIRouter()

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI endpoint"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Quantum AI Trader API Documentation",
        swagger_favicon_url="/static/favicon.ico",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """Custom OpenAPI JSON endpoint"""
    return get_openapi(
        title="Quantum AI Trader API",
        version="1.0.0",
        description="Advanced AI-powered trading system with quantum computing features",
        routes=app.routes,
    )

# Custom API documentation
api_docs = {
    "info": {
        "title": "Quantum AI Trader API",
        "version": "1.0.0",
        "description": "Advanced AI-powered trading system with quantum computing features",
        "contact": {
            "name": "Support",
            "email": "support@quantumtrader.ai",
            "url": "https://quantumtrader.ai"
        },
        "license": {
            "name": "Proprietary",
            "url": "https://quantumtrader.ai/license"
        }
    },
    "servers": [
        {
            "url": "https://api.quantumtrader.ai",
            "description": "Production server"
        },
        {
            "url": "https://api-staging.quantumtrader.ai",
            "description": "Staging server"
        }
    ],
    "tags": [
        {
            "name": "trading",
            "description": "Trading operations"
        },
        {
            "name": "ai",
            "description": "AI and machine learning operations"
        },
        {
            "name": "quantum",
            "description": "Quantum computing operations"
        },
        {
            "name": "system",
            "description": "System operations"
        }
    ],
    "components": {
        "schemas": {
            "Trade": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique trade identifier"
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol"
                    },
                    "side": {
                        "type": "string",
                        "enum": ["buy", "sell"],
                        "description": "Trade side"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Trade quantity"
                    },
                    "price": {
                        "type": "number",
                        "description": "Trade price"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "executed", "cancelled"],
                        "description": "Trade status"
                    }
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "integer",
                        "description": "Error code"
                    },
                    "message": {
                        "type": "string",
                        "description": "Error message"
                    },
                    "details": {
                        "type": "object",
                        "description": "Additional error details"
                    }
                }
            }
        },
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}

# Save API documentation
api_docs_path = os.path.join(os.path.dirname(__file__), "api_docs.json")
with open(api_docs_path, "w") as f:
    json.dump(api_docs, f, indent=2)

# Include API router
app.include_router(api_router)
