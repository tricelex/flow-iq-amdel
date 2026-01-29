"""Analytics tools for FlowIQ agent.

These tools allow the AI agent to query the DVD rental database through Cube.js.
Each tool is decorated with @function_tool to make it available to the OpenAI agent.
"""

from typing import Any, Optional, Literal
from agents import function_tool
from pydantic import BaseModel, Field

from app.infra.cube.cube_client import get_cube_client
from app.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================
# Pydantic Models for Query Parameters
# ============================================================

class CubeFilter(BaseModel):
    """Filter condition for Cube.js query."""
    member: str = Field(description="The field to filter (e.g., 'customers.active')")
    operator: Literal["equals", "notEquals", "contains", "gt", "gte", "lt", "lte"] = Field(
        description="Filter operator"
    )
    values: list[str] = Field(description="List of values to filter by")


class TimeDimension(BaseModel):
    """Time dimension for Cube.js query."""
    dimension: str = Field(description="Time field (e.g., 'rentals.rental_date')")
    dateRange: str | list[str] = Field(
        description="Date range like 'last 30 days', 'this month', or ['2024-01-01', '2024-12-31']"
    )
    granularity: Optional[Literal["day", "week", "month", "year"]] = Field(
        default=None,
        description="Optional grouping - 'day', 'week', 'month', 'year'"
    )


# ============================================================
# Core Analytics Tool
# ============================================================

@function_tool
async def query_analytics(
    measures: list[str],
    dimensions: Optional[list[str]] = None,
    filters: Optional[list[CubeFilter]] = None,
    time_dimensions: Optional[list[TimeDimension]] = None,
    order_by: Optional[str] = None,
    order_direction: Optional[Literal["asc", "desc"]] = None,
    limit: int = 100
) -> dict[str, Any]:
    """Query the DVD rental analytics database.

    This is the main flexible tool for querying customer, rental, and payment data.
    Use this when you need to analyze data with custom filters, groupings, or time ranges.

    Args:
        measures: List of metrics to calculate. Examples:
            - "customers.count" - Total customers
            - "customers.active_count" - Active customers
            - "rentals.count" - Total rentals
            - "rentals.returned_count" - Returned rentals
            - "rentals.outstanding_count" - Outstanding rentals
            - "payments.total_revenue" - Total revenue
            - "payments.average_payment" - Average payment amount

        dimensions: List of fields to group by. Examples:
            - "customers.full_name" - Customer name
            - "customers.email" - Customer email
            - "rentals.rental_date" - Rental date
            - "payments.payment_date" - Payment date

        filters: List of filter conditions. Each filter has:
            - member: The field to filter (e.g., "customers.active")
            - operator: equals, notEquals, contains, gt, gte, lt, lte
            - values: List of values to filter by
            Example: [{"member": "customers.active", "operator": "equals", "values": ["Active"]}]

        time_dimensions: Time-based filtering. Each has:
            - dimension: Time field (e.g., "rentals.rental_date")
            - dateRange: Date range like "last 30 days", "this month", or ["2024-01-01", "2024-12-31"]
            - granularity: Optional grouping - "day", "week", "month"

        order: Sort order. Example: {"rentals.count": "desc"}

        limit: Max rows to return (default 100)

    Returns:
        Query results with data array, row count, and success status

    Example queries:
        # Get all customers
        query_analytics(measures=["customers.count"])

        # Top customers by rental count
        query_analytics(
            measures=["rentals.count"],
            dimensions=["customers.full_name"],
            order={"rentals.count": "desc"},
            limit=10
        )
    """
    cube = get_cube_client()

    # Build query
    query = {
        "measures": measures,
        "limit": min(limit, 5000)
    }

    if dimensions:
        query["dimensions"] = dimensions
    if filters:
        query["filters"] = [f.model_dump() for f in filters]
    if time_dimensions:
        query["timeDimensions"] = [td.model_dump(exclude_none=True) for td in time_dimensions]
    if order_by and order_direction:
        query["order"] = {order_by: order_direction}

    logger.info(
        "executing_query_analytics",
        measures=measures,
        dimensions=dimensions,
        has_filters=bool(filters),
        limit=limit
    )

    # Execute query
    result = await cube.query(query)

    if result.success:
        logger.info("query_analytics_success", total_rows=result.total_rows)
        return {
            "success": True,
            "data": result.data,
            "total_rows": result.total_rows,
            "message": f"Query returned {result.total_rows} rows"
        }
    else:
        logger.error("query_analytics_failed", error=result.error)
        return {
            "success": False,
            "error": result.error,
            "message": f"Query failed: {result.error}"
        }


# ============================================================
# Specialized Tools
# ============================================================

@function_tool
async def get_customer_analysis(
    top_n: int = 10,
    include_details: bool = True
) -> dict[str, Any]:
    """Get customer analysis including rental counts and revenue contribution.

    Use this for questions like:
    - "Who are the top customers?"
    - "Which customers rent the most?"
    - "Show me customer activity"

    Args:
        top_n: Number of top customers to return (default 10)
        include_details: Include email addresses (default True)

    Returns:
        Customer analysis with rental counts and revenue for top customers
    """
    cube = get_cube_client()

    # Build dimensions
    dimensions = ["customers.full_name"]
    if include_details:
        dimensions.append("customers.email")

    query = {
        "measures": [
            "rentals.count",
            "rentals.returned_count",
            "rentals.outstanding_count",
            "payments.total_revenue"
        ],
        "dimensions": dimensions,
        "order": {"rentals.count": "desc"},
        "limit": top_n
    }

    logger.info("executing_customer_analysis", top_n=top_n)

    result = await cube.query(query)

    if result.success:
        # Calculate totals
        total_rentals = sum(int(row.get("rentals.count", 0)) for row in result.data)
        total_revenue = sum(float(row.get("payments.total_revenue", 0)) for row in result.data)

        return {
            "success": True,
            "total_customers_shown": result.total_rows,
            "total_rentals": total_rentals,
            "total_revenue": total_revenue,
            "customers": result.data,
            "message": f"Showing top {result.total_rows} customers"
        }
    else:
        return {
            "success": False,
            "error": result.error
        }


@function_tool
async def get_revenue_summary(
    period: Optional[str] = None,
    group_by: str = "total"
) -> dict[str, Any]:
    """Get revenue summary and payment statistics.

    Use this for questions like:
    - "What's our total revenue?"
    - "How much have we earned?"
    - "Show me revenue statistics"

    Args:
        period: Time period to analyze. Examples:
            - "last 30 days"
            - "this month"
            - "last month"
            - "this year"
            - None for all time (default)

        group_by: How to group results:
            - "total" - Overall totals (default)
            - "customer" - By customer
            - "month" - By month

    Returns:
        Revenue metrics including total revenue, payment count, and averages
    """
    cube = get_cube_client()

    query = {
        "measures": [
            "payments.total_revenue",
            "payments.count",
            "payments.average_payment",
            "payments.min_payment",
            "payments.max_payment"
        ]
    }

    # Add grouping
    if group_by == "customer":
        query["dimensions"] = ["customers.full_name"]
        query["order"] = {"payments.total_revenue": "desc"}
        query["limit"] = 20
    elif group_by == "month":
        query["timeDimensions"] = [{
            "dimension": "payments.payment_date",
            "granularity": "month"
        }]
        if period:
            query["timeDimensions"][0]["dateRange"] = period

    # Add time filter for total
    elif period:
        query["timeDimensions"] = [{
            "dimension": "payments.payment_date",
            "dateRange": period
        }]

    logger.info("executing_revenue_summary", period=period, group_by=group_by)

    result = await cube.query(query)

    if result.success:
        if group_by == "total" and result.data:
            # Single row with totals
            row = result.data[0]
            return {
                "success": True,
                "total_revenue": row.get("payments.total_revenue"),
                "total_payments": row.get("payments.count"),
                "average_payment": row.get("payments.average_payment"),
                "min_payment": row.get("payments.min_payment"),
                "max_payment": row.get("payments.max_payment"),
                "period": period or "all time",
                "message": f"Revenue for {period or 'all time'}"
            }
        else:
            # Multiple rows
            total_revenue = sum(
                float(row.get("payments.total_revenue", 0))
                for row in result.data
            )
            return {
                "success": True,
                "total_revenue": total_revenue,
                "breakdown": result.data,
                "group_by": group_by,
                "period": period or "all time",
                "message": f"Revenue breakdown by {group_by}"
            }
    else:
        return {
            "success": False,
            "error": result.error
        }


@function_tool
async def get_rental_overview() -> dict[str, Any]:
    """Get overview of rental statistics.

    Use this for questions like:
    - "How many rentals do we have?"
    - "How many outstanding rentals?"
    - "What's the rental summary?"

    Returns:
        Rental statistics including total, returned, and outstanding counts
    """
    cube = get_cube_client()

    query = {
        "measures": [
            "rentals.count",
            "rentals.returned_count",
            "rentals.outstanding_count",
            "rentals.average_duration"
        ]
    }

    logger.info("executing_rental_overview")

    result = await cube.query(query)

    if result.success and result.data:
        row = result.data[0]
        total = int(row.get("rentals.count", 0))
        returned = int(row.get("rentals.returned_count", 0))
        outstanding = int(row.get("rentals.outstanding_count", 0))
        avg_duration = row.get("rentals.average_duration", 0)

        return {
            "success": True,
            "total_rentals": total,
            "returned_rentals": returned,
            "outstanding_rentals": outstanding,
            "return_rate": round((returned / total * 100) if total > 0 else 0, 2),
            "average_rental_duration_days": avg_duration,
            "message": f"{outstanding} rentals currently outstanding out of {total} total"
        }
    else:
        return {
            "success": False,
            "error": result.error if not result.success else "No data"
        }


# ============================================================
# Utility Tools
# ============================================================

@function_tool
async def get_available_metrics() -> dict[str, Any]:
    """Get list of available metrics and dimensions you can query.

    Use this when you need to understand what data is available or what metrics exist.

    Returns:
        List of all cubes with their available measures and dimensions
    """
    cube = get_cube_client()

    logger.info("fetching_available_metrics")

    try:
        meta = await cube.get_meta()

        cubes_info = []
        for cube_def in meta.get("cubes", []):
            cube_info = {
                "cube": cube_def.get("name"),
                "title": cube_def.get("title"),
                "description": cube_def.get("description"),
                "measures": [],
                "dimensions": []
            }

            # Add measures
            for m in cube_def.get("measures", []):
                cube_info["measures"].append({
                    "name": f"{cube_def['name']}.{m['name']}",
                    "title": m.get("title", m["name"]),
                    "type": m.get("type", ""),
                    "description": m.get("description", "")
                })

            # Add dimensions
            for d in cube_def.get("dimensions", []):
                if d.get("shown", True):
                    cube_info["dimensions"].append({
                        "name": f"{cube_def['name']}.{d['name']}",
                        "title": d.get("title", d["name"]),
                        "type": d.get("type", "string"),
                        "description": d.get("description", "")
                    })

            cubes_info.append(cube_info)

        return {
            "success": True,
            "cubes": cubes_info,
            "total_cubes": len(cubes_info),
            "message": f"Found {len(cubes_info)} cubes with their metrics"
        }

    except Exception as e:
        logger.error("get_available_metrics_failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }
