"""Limbo - MCP Aggregator

A self-aware MCP server that manages and aggregates other MCP tools and servers.
"""
from importlib import metadata

try:
    __version__ = metadata.version("limbo")
except metadata.PackageNotFoundError:
    __version__ = "unknown"

del metadata

# Export main components
from .client import LimboClient
from .messaging import LimboMessageHandler, MessageRouter, ServerMessageCoordinator

__all__ = [
    "LimboClient",
    "LimboMessageHandler",
    "MessageRouter",
    "ServerMessageCoordinator",
]
