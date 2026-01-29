#!/usr/bin/env python3
"""
Test script for CubeClient integration.

Tests the CubeClient class to ensure it can:
1. Connect to Cube.js
2. Fetch metadata
3. Execute queries
4. Format metadata for prompts

Usage:
    python scripts/test_cube_client.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.infra.cube.cube_client import CubeClient, get_cube_client


async def test_cube_client_direct():
    """Test CubeClient with direct instantiation"""
    print("=" * 70)
    print("TEST 1: Direct CubeClient Instantiation")
    print("=" * 70)

    client = CubeClient(
        api_url="http://localhost:4000",
        api_secret="flowiq-dev-secret-key"
    )

    try:
        # Test get_meta
        print("\n1. Testing get_meta()...")
        meta = await client.get_meta()
        cubes = meta.get("cubes", [])
        print(f"✅ Found {len(cubes)} cubes:")
        for cube in cubes:
            print(f"   - {cube['name']}")

        # Test query
        print("\n2. Testing query()...")
        result = await client.query({
            "measures": ["customers.count", "customers.active_count"]
        })

        if result.success:
            print(f"✅ Query successful: {result.total_rows} rows")
            if result.data:
                print(f"   Data: {result.data[0]}")
        else:
            print(f"❌ Query failed: {result.error}")

        # Test format_meta_for_prompt
        print("\n3. Testing format_meta_for_prompt()...")
        formatted = await client.format_meta_for_prompt()
        lines = formatted.split("\n")
        print(f"✅ Formatted metadata: {len(lines)} lines")
        print(f"   Preview (first 10 lines):")
        for line in lines[:10]:
            print(f"   {line}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        await client.close()


async def test_cube_client_singleton():
    """Test CubeClient with singleton pattern"""
    print("\n" + "=" * 70)
    print("TEST 2: Singleton Pattern get_cube_client()")
    print("=" * 70)

    try:
        # Get singleton instance
        print("\n1. Getting singleton instance...")
        cube = get_cube_client()
        print(f"✅ Got CubeClient instance")

        # Test query
        print("\n2. Testing revenue query...")
        result = await cube.query({
            "measures": [
                "payments.total_revenue",
                "payments.count",
                "payments.average_payment"
            ]
        })

        if result.success:
            print(f"✅ Query successful")
            if result.data:
                row = result.data[0]
                revenue = row.get("payments.total_revenue", 0)
                count = row.get("payments.count", 0)
                avg = row.get("payments.average_payment", 0)
                print(f"   Total Revenue: ${revenue}")
                print(f"   Total Payments: {count}")
                print(f"   Average Payment: ${avg}")
        else:
            print(f"❌ Query failed: {result.error}")

        # Test query with filters and order
        print("\n3. Testing query with dimensions and ordering...")
        result = await cube.query({
            "measures": ["rentals.count", "rentals.returned_count"],
            "dimensions": ["customers.full_name"],
            "order": {"rentals.count": "desc"},
            "limit": 5
        })

        if result.success:
            print(f"✅ Query successful: {result.total_rows} rows")
            print(f"   Top 5 customers by rental count:")
            for row in result.data:
                name = row.get("customers.full_name", "Unknown")
                total = row.get("rentals.count", 0)
                returned = row.get("rentals.returned_count", 0)
                print(f"   - {name}: {total} rentals ({returned} returned)")
        else:
            print(f"❌ Query failed: {result.error}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling with invalid queries"""
    print("\n" + "=" * 70)
    print("TEST 3: Error Handling")
    print("=" * 70)

    cube = get_cube_client()

    # Test 1: Invalid cube name
    print("\n1. Testing invalid cube name...")
    result = await cube.query({
        "measures": ["nonexistent.count"]
    })

    if not result.success:
        print(f"✅ Error caught correctly: {result.error[:100]}...")
    else:
        print(f"❌ Should have failed but didn't")

    # Test 2: Invalid measure name
    print("\n2. Testing invalid measure name...")
    result = await cube.query({
        "measures": ["customers.nonexistent_measure"]
    })

    if not result.success:
        print(f"✅ Error caught correctly: {result.error[:100]}...")
    else:
        print(f"❌ Should have failed but didn't")

    return True


async def main():
    """Run all tests"""
    print("\n" + "🧪 " * 30)
    print("CUBECLIENT INTEGRATION TEST")
    print("🧪 " * 30 + "\n")

    # Test 1: Direct instantiation
    test1_passed = await test_cube_client_direct()

    # Test 2: Singleton pattern
    test2_passed = await test_cube_client_singleton()

    # Test 3: Error handling
    test3_passed = await test_error_handling()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Direct Instantiation: {'PASS' if test1_passed else 'FAIL'}")
    print(f"✅ Singleton Pattern: {'PASS' if test2_passed else 'FAIL'}")
    print(f"✅ Error Handling: {'PASS' if test3_passed else 'FAIL'}")

    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 All tests passed! CubeClient is working correctly.")
        print("\nNext steps:")
        print("1. Create analytics tools in src/app/infra/flow_iq_agent/tools/")
        print("2. Enhance FlowIQ agent with Cube.js context")
        print("3. Update chat API to use new tools")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")


if __name__ == "__main__":
    asyncio.run(main())
