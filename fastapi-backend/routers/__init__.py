"""
Routers package initialization

Imports all router modules for easy access in main.py
"""

# Import all routers
from . import (
    auth,
    bots,
    crawl,
    documents,
    embeddings,
    chat,
    admin,
    analytics,
    widget,
    health
)

__all__ = [
    "auth",
    "bots", 
    "crawl",
    "documents",
    "embeddings",
    "chat",
    "admin",
    "analytics",
    "widget",
    "health"
]