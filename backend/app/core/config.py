import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    ENV: str = Field(default="development", description="Environment: development, staging, production")
    APP_NAME: str = "Dhoodh Plus WhatsApp AI Agent"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "dhoodh-plus-super-secret-key-change-in-production"
    ADMIN_PASSWORD: str = "admin123"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # Redis Cache & Broker (Render Redis / Upstash / Local)
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = True

    # WhatsApp Gateway ("meta" or "openwa" or "baileys")
    WHATSAPP_GATEWAY: str = "meta"  # "meta" or "openwa"
    WHATSAPP_GATEWAY_URL: str = "http://localhost:3001"
    
    # Meta WhatsApp Cloud API
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "dhood_plus_secure_verify_token_2026"
    WHATSAPP_API_VERSION: str = "v20.0"
    WHATSAPP_APP_SECRET: Optional[str] = None

    # OpenWA Gateway (self-hosted WhatsApp bridge https://github.com/rmyndharis/OpenWA)
    OPENWA_API_URL: str = "http://localhost:3000"
    OPENWA_API_KEY: Optional[str] = None
    OPENWA_SESSION: str = "default"

    # LLM Settings
    LLM_PROVIDER: str = "openai"  # openai, gemini, groq, mock
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    MAX_CONTEXT_TOKENS: int = 3000

    # Embedding Settings
    EMBEDDING_PROVIDER: str = "openai"  # openai, gemini, mock
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # RAG Settings
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.35
    MAX_HISTORY_MESSAGES: int = 6

    # Storage & Uploads
    UPLOAD_DIR: str = "./storage/documents"
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
