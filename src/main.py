from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from infrastructure.database.connection import engine, Base
from presentation.api.user_routes import router as user_router
from presentation.api.auth_routes import router as auth_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(
        title="DDD FastAPI Application",
        description="A FastAPI application following Domain Driven Design principles",
        version="1.0.0",
        redirect_slashes=False  # Desabilita redirecionamento automático de trailing slash
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Logar requisições suspeitas para endpoints de IA
        ai_endpoints = ["/v1/models", "/v1/chat", "/v1/completions", "/models", "/chat"]
        if any(request.url.path.startswith(endpoint) for endpoint in ai_endpoints):
            logger.warning(
                f"AI API request detected: {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'} "
                f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
            )
        
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Logar requisições problemáticas e redirecionamentos
        if response.status_code >= 400 or request.url.path.startswith("/v1/") or response.status_code == 307:
            status_msg = ""
            if response.status_code == 307:
                status_msg = " (REDIRECT - check trailing slash)"
            
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code}{status_msg} - "
                f"Time: {process_time:.4f}s - "
                f"Client: {request.client.host if request.client else 'unknown'}"
            )
        
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(user_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")

    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    create_tables()


@app.get("/")
async def root():
    return {"message": "Welcome to DDD FastAPI Application"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/v1/models")
async def models_endpoint():
    """
    Endpoint para esclarecer que esta não é uma API de modelos de IA.
    Algumas ferramentas podem tentar acessar este endpoint pensando que é uma API OpenAI-like.
    """
    return {
        "error": "Not an AI models API",
        "message": "This is a FastAPI DDD application, not an AI models server",
        "application": "FastAPI DDD Project",
        "available_endpoints": [
            "/docs - API Documentation",
            "/api/v1/users - User management endpoints",
            "/api/v1/auth - Authentication endpoints",
            "/health - Health check"
        ],
        "note": "If you're looking for AI models, try OpenAI API, Ollama, or similar services"
    }


@app.post("/v1/chat/completions")
@app.post("/v1/completions")
@app.get("/models")
async def ai_endpoints_handler():
    """
    Handler para outros endpoints comuns de APIs de IA
    """
    return {
        "error": "AI API not available",
        "message": "This is not an AI service. This is a FastAPI DDD application for user management.",
        "redirect": "Check /docs for available endpoints",
        "suggestion": "For AI services, try OpenAI, Anthropic, Ollama, or other AI providers"
    }