import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.api.routes import (
    whatsapp,
    whatsapp_connect,
    documents,
    conversations,
    customers,
    settings as settings_route,
    analytics,
    health,
    auth
)

app = FastAPI(
    title="Dhoodh Plus WhatsApp AI Agent",
    description="Production-grade WhatsApp AI customer support chatbot with PDF RAG, Supabase pgvector, and Admin Dashboard",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api
app.include_router(auth.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(whatsapp_connect.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(settings_route.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(health.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"{settings.APP_NAME} started on environment: {settings.ENV}")
    logger.info(f"WhatsApp webhook ready at: /api/whatsapp/webhook")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "api": "/api",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
