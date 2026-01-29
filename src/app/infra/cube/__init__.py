"""Cube.js integration module.

This module provides integration with Cube.js semantic layer for analytics queries.
"""

from app.infra.cube.cube_client import CubeClient, CubeQueryResult, get_cube_client

__all__ = ["CubeClient", "CubeQueryResult", "get_cube_client"]
