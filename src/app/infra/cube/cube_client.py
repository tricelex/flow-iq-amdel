"""Cube.js client for querying the semantic analytics layer.

This module provides an async HTTP client for interacting with Cube.js API.
It handles metadata fetching, query execution, and response formatting.
"""

from typing import Any, Optional
import httpx
from pydantic import BaseModel, Field

from app.core.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CubeQueryResult(BaseModel):
    """Result from a Cube.js query execution.

    Attributes:
        success: Whether the query executed successfully
        data: List of result rows (each row is a dict)
        total_rows: Number of rows returned
        query: The original query that was executed
        error: Error message if query failed
    """
    success: bool
    data: list[dict[str, Any]] = Field(default_factory=list)
    total_rows: int = 0
    query: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class CubeClient:
    """Async HTTP client for Cube.js API.

    Provides methods to:
    - Fetch cube metadata (available measures, dimensions)
    - Execute analytics queries
    - Format metadata for AI agent prompts

    Example:
        ```python
        cube = CubeClient("http://localhost:4000", "secret-key")

        # Get metadata
        meta = await cube.get_meta()

        # Execute query
        result = await cube.query({
            "measures": ["customers.count"],
            "dimensions": ["customers.full_name"]
        })
        ```
    """

    def __init__(self, api_url: str, api_secret: str) -> None:
        """Initialize Cube.js client.

        Args:
            api_url: Base URL of Cube.js API (e.g., http://localhost:4000)
            api_secret: API secret key for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.api_secret = api_secret
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"Authorization": api_secret},
            timeout=30.0
        )
        logger.info("cube_client_initialized", api_url=self.api_url)

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.debug("cube_client_closed")

    async def get_meta(self) -> dict[str, Any]:
        """Fetch Cube.js metadata.

        Returns metadata about available cubes, measures, and dimensions.
        This is used to build the AI agent's system prompt.

        Returns:
            Dictionary containing:
            - cubes: List of cube definitions
            - Each cube has: name, measures, dimensions, title, description

        Raises:
            httpx.HTTPStatusError: If API request fails

        Example:
            ```python
            meta = await cube.get_meta()
            print(f"Available cubes: {[c['name'] for c in meta['cubes']]}")
            ```
        """
        try:
            logger.debug("fetching_cube_metadata")
            response = await self.client.get("/cubejs-api/v1/meta")
            response.raise_for_status()
            meta = response.json()

            cube_count = len(meta.get("cubes", []))
            logger.info("cube_metadata_fetched", cube_count=cube_count)

            return meta

        except httpx.HTTPStatusError as e:
            logger.exception(
                "cube_metadata_fetch_failed",
                status_code=e.response.status_code,
                error=e.response.text
            )
            raise
        except Exception as e:
            logger.exception("cube_metadata_error", error=str(e))
            raise

    async def query(self, query: dict[str, Any]) -> CubeQueryResult:
        """Execute a Cube.js analytics query.

        Sends a query to Cube.js and returns the results.

        Args:
            query: Query object containing:
                - measures: List of measures to calculate (e.g., ["customers.count"])
                - dimensions: List of dimensions to group by (optional)
                - filters: List of filter conditions (optional)
                - timeDimensions: Time-based filtering (optional)
                - order: Sort order (optional)
                - limit: Max rows to return (optional)

        Returns:
            CubeQueryResult with success status, data, and metadata

        Example:
            ```python
            result = await cube.query({
                "measures": ["customers.count", "payments.total_revenue"],
                "dimensions": ["customers.full_name"],
                "order": {"payments.total_revenue": "desc"},
                "limit": 10
            })

            if result.success:
                for row in result.data:
                    print(f"{row['customers.full_name']}: ${row['payments.total_revenue']}")
            ```
        """
        try:
            logger.debug("executing_cube_query", query=query)

            response = await self.client.post(
                "/cubejs-api/v1/load",
                json={"query": query}
            )
            response.raise_for_status()
            result = response.json()

            data = result.get("data", [])
            total_rows = len(data)

            logger.info(
                "cube_query_executed",
                total_rows=total_rows,
                measures=query.get("measures", []),
                dimensions=query.get("dimensions", [])
            )

            return CubeQueryResult(
                success=True,
                data=data,
                total_rows=total_rows,
                query=query
            )

        except httpx.HTTPStatusError as e:
            error_msg = e.response.text
            logger.exception(
                "cube_query_failed",
                status_code=e.response.status_code,
                error=error_msg,
                query=query
            )

            return CubeQueryResult(
                success=False,
                data=[],
                total_rows=0,
                query=query,
                error=f"HTTP {e.response.status_code}: {error_msg}"
            )

        except Exception as e:
            error_msg = str(e)
            logger.exception("cube_query_error", error=error_msg, query=query)

            return CubeQueryResult(
                success=False,
                data=[],
                total_rows=0,
                query=query,
                error=error_msg
            )

    async def format_meta_for_prompt(self) -> str:
        """Format cube metadata as readable text for AI agent's system prompt.

        Fetches cube metadata and formats it as a human-readable string
        that describes available metrics and dimensions.

        Returns:
            Formatted string describing all cubes, their measures, and dimensions

        Example output:
            ```
            ### Customers
            **Measures:**
            - customers.count: Total number of customers
            - customers.active_count: Number of active customers

            **Dimensions:**
            - customers.full_name: Customer name
            - customers.email: Email address
            ```
        """
        try:
            meta = await self.get_meta()

            output = []
            for cube in meta.get("cubes", []):
                cube_name = cube.get("name", "unknown")
                title = cube.get("title", cube_name)
                description = cube.get("description", "")

                output.append(f"\n### {title}")
                if description:
                    output.append(f"{description}\n")

                # Add measures
                measures = cube.get("measures", [])
                if measures:
                    output.append("\n**Measures:**")
                    for m in measures[:15]:  # Limit to avoid token bloat
                        name = f"{cube_name}.{m['name']}"
                        title_text = m.get("title", m["name"])
                        desc = m.get("description", "")
                        if desc:
                            output.append(f"- `{name}`: {desc}")
                        else:
                            output.append(f"- `{name}`: {title_text}")

                # Add dimensions
                dimensions = cube.get("dimensions", [])
                visible_dims = [d for d in dimensions if d.get("shown", True)]
                if visible_dims:
                    output.append("\n**Dimensions:**")
                    for d in visible_dims[:15]:  # Limit to avoid token bloat
                        name = f"{cube_name}.{d['name']}"
                        title_text = d.get("title", d["name"])
                        desc = d.get("description", "")
                        if desc:
                            output.append(f"- `{name}`: {desc}")
                        else:
                            output.append(f"- `{name}`: {title_text}")

            formatted = "\n".join(output)
            logger.debug("cube_metadata_formatted", length=len(formatted))

            return formatted

        except Exception as e:
            logger.exception("format_meta_error", error=str(e))
            return f"Error formatting metadata: {str(e)}"


# ============================================================
# Singleton Pattern
# ============================================================

_cube_client: Optional[CubeClient] = None


def get_cube_client() -> CubeClient:
    """Get or create the singleton Cube.js client instance.

    Returns:
        Shared CubeClient instance

    Example:
        ```python
        cube = get_cube_client()
        result = await cube.query({...})
        ```
    """
    global _cube_client

    if _cube_client is None:
        settings = get_settings()
        _cube_client = CubeClient(
            api_url=settings.CUBE_API_URL,
            api_secret=settings.CUBE_API_SECRET
        )
        logger.info("cube_client_singleton_created")

    return _cube_client


async def close_cube_client():
    """Close the singleton Cube.js client.

    Call this during application shutdown.
    """
    global _cube_client

    if _cube_client is not None:
        await _cube_client.close()
        _cube_client = None
        logger.info("cube_client_singleton_closed")
