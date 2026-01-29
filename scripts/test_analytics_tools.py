#!/usr/bin/env python3
"""
Test script for analytics tools - tests the underlying functionality.

Since the tools use @function_tool decorator which is meant for AI agents,
we test the underlying Cube.js queries directly.

Usage:
    python scripts/test_analytics_tools.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.infra.cube.cube_client import get_cube_client


async def test_customer_queries():
    """Test customer-related queries"""
    print("=" * 70)
    print("TEST 1: Customer Queries")
    print("=" * 70)

    cube = get_cube_client()

    # Test 1.1: Customer count
    print("\n1.1 Customer count...")
    result = await cube.query({
        "measures": ["customers.count", "customers.active_count"]
    })

    if result.success and result.data:
        print(f"✅ Query successful")
        row = result.data[0]
        print(f"   Total customers: {row.get('customers.count')}")
        print(f"   Active customers: {row.get('customers.active_count')}")
    else:
        print(f"❌ Query failed: {result.error}")
        return False

    # Test 1.2: Top customers by rental count
    print("\n1.2 Top 5 customers by rental count...")
    result = await cube.query({
        "measures": ["rentals.count", "payments.total_revenue"],
        "dimensions": ["customers.full_name"],
        "order": {"rentals.count": "desc"},
        "limit": 5
    })

    if result.success:
        print(f"✅ Query successful: {result.total_rows} rows")
        for i, row in enumerate(result.data, 1):
            name = row.get("customers.full_name", "Unknown")
            rentals = row.get("rentals.count", 0)
            revenue = row.get("payments.total_revenue", 0)
            print(f"   {i}. {name}: {rentals} rentals, ${revenue}")
    else:
        print(f"❌ Query failed: {result.error}")
        return False

    return True


async def test_revenue_queries():
    """Test revenue-related queries"""
    print("\n" + "=" * 70)
    print("TEST 2: Revenue Queries")
    print("=" * 70)

    cube = get_cube_client()

    # Test 2.1: Total revenue
    print("\n2.1 Total revenue (all time)...")
    result = await cube.query({
        "measures": [
            "payments.total_revenue",
            "payments.count",
            "payments.average_payment",
            "payments.min_payment",
            "payments.max_payment"
        ]
    })

    if result.success and result.data:
        print(f"✅ Query successful")
        row = result.data[0]
        print(f"   Total revenue: ${row.get('payments.total_revenue')}")
        print(f"   Total payments: {row.get('payments.count')}")
        print(f"   Average payment: ${row.get('payments.average_payment')}")
        print(f"   Min payment: ${row.get('payments.min_payment')}")
        print(f"   Max payment: ${row.get('payments.max_payment')}")
    else:
        print(f"❌ Query failed: {result.error}")
        return False

    # Test 2.2: Revenue by customer (top 5)
    print("\n2.2 Revenue by customer (top 5)...")
    result = await cube.query({
        "measures": ["payments.total_revenue", "payments.count"],
        "dimensions": ["customers.full_name"],
        "order": {"payments.total_revenue": "desc"},
        "limit": 5
    })

    if result.success:
        print(f"✅ Query successful: {result.total_rows} customers")
        for i, row in enumerate(result.data, 1):
            name = row.get("customers.full_name", "Unknown")
            revenue = row.get("payments.total_revenue", 0)
            count = row.get("payments.count", 0)
            print(f"   {i}. {name}: ${revenue} ({count} payments)")
    else:
        print(f"❌ Query failed: {result.error}")
        return False

    return True


async def test_rental_queries():
    """Test rental-related queries"""
    print("\n" + "=" * 70)
    print("TEST 3: Rental Queries")
    print("=" * 70)

    cube = get_cube_client()

    # Test 3.1: Rental overview
    print("\n3.1 Rental overview...")
    result = await cube.query({
        "measures": [
            "rentals.count",
            "rentals.returned_count",
            "rentals.outstanding_count",
            "rentals.average_duration"
        ]
    })

    if result.success and result.data:
        print(f"✅ Query successful")
        row = result.data[0]
        total = int(row.get("rentals.count", 0))
        returned = int(row.get("rentals.returned_count", 0))
        outstanding = int(row.get("rentals.outstanding_count", 0))
        avg_duration = row.get("rentals.average_duration", 0)
        return_rate = round((returned / total * 100) if total > 0 else 0, 2)

        print(f"   Total rentals: {total}")
        print(f"   Returned rentals: {returned}")
        print(f"   Outstanding rentals: {outstanding}")
        print(f"   Return rate: {return_rate}%")
        print(f"   Average duration: {avg_duration} days")
    else:
        print(f"❌ Query failed: {result.error}")
        return False

    # Test 3.2: Rentals with customer details
    print("\n3.2 Top 5 customers by outstanding rentals...")
    result = await cube.query({
        "measures": ["rentals.outstanding_count"],
        "dimensions": ["customers.full_name", "customers.email"],
        "filters": [{
            "member": "rentals.outstanding_count",
            "operator": "gt",
            "values": ["0"]
        }],
        "order": {"rentals.outstanding_count": "desc"},
        "limit": 5
    })

    if result.success:
        print(f"✅ Query successful: {result.total_rows} customers with outstanding rentals")
        if result.data:
            for i, row in enumerate(result.data, 1):
                name = row.get("customers.full_name", "Unknown")
                outstanding = row.get("rentals.outstanding_count", 0)
                print(f"   {i}. {name}: {outstanding} outstanding")
    else:
        print(f"❌ Query failed: {result.error}")
        return False

    return True


async def test_metadata_query():
    """Test metadata fetching"""
    print("\n" + "=" * 70)
    print("TEST 4: Metadata Query")
    print("=" * 70)

    cube = get_cube_client()

    print("\n4.1 Fetching cube metadata...")
    try:
        meta = await cube.get_meta()
        cubes = meta.get("cubes", [])

        print(f"✅ Metadata fetched successfully")
        print(f"   Total cubes: {len(cubes)}")

        for cube_def in cubes:
            name = cube_def.get("name")
            measures = cube_def.get("measures", [])
            dimensions = cube_def.get("dimensions", [])

            print(f"\n   Cube: {name}")
            print(f"   - Measures: {len(measures)}")
            print(f"   - Dimensions: {len(dimensions)}")

            # Show first 3 measures
            if measures:
                print(f"   Sample measures:")
                for m in measures[:3]:
                    title = m.get("title", m.get("name"))
                    print(f"     - {m['name']}: {title}")

        return True

    except Exception as e:
        print(f"❌ Metadata fetch failed: {e}")
        return False


async def test_time_dimensions():
    """Test queries with time dimensions"""
    print("\n" + "=" * 70)
    print("TEST 5: Time Dimension Queries")
    print("=" * 70)

    cube = get_cube_client()

    # Test 5.1: Revenue by month
    print("\n5.1 Revenue by month...")
    result = await cube.query({
        "measures": ["payments.total_revenue", "payments.count"],
        "timeDimensions": [{
            "dimension": "payments.payment_date",
            "granularity": "month"
        }],
        "limit": 12
    })

    if result.success:
        print(f"✅ Query successful: {result.total_rows} months")
        print(f"   First 3 months:")
        for i, row in enumerate(result.data[:3], 1):
            month = row.get("payments.payment_date.month", "Unknown")
            revenue = row.get("payments.total_revenue", 0)
            count = row.get("payments.count", 0)
            print(f"   {i}. {month}: ${revenue} ({count} payments)")
    else:
        print(f"❌ Query failed: {result.error}")
        return False

    return True


async def main():
    """Run all tests"""
    print("\n" + "🧪 " * 30)
    print("ANALYTICS TOOLS TEST SUITE")
    print("Testing Cube.js queries that power the analytics tools")
    print("🧪 " * 30 + "\n")

    tests = [
        ("Customer Queries", test_customer_queries),
        ("Revenue Queries", test_revenue_queries),
        ("Rental Queries", test_rental_queries),
        ("Metadata Query", test_metadata_query),
        ("Time Dimension Queries", test_time_dimensions),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"\n❌ {test_name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All analytics queries working correctly!")
        print("\n✅ Phase 3.1: Analytics Tools - COMPLETE")
        print("\nNext steps:")
        print("1. Update INTEGRATION_CHECKLIST.md")
        print("2. Phase 4: Enhance FlowIQ agent with tools")
        print("3. Phase 5: Update chat API")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
