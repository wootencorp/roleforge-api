"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, characters, campaigns, sessions, ai

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(characters.router, prefix="/characters", tags=["Characters"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Game Sessions"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Services"])

