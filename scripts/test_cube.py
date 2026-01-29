#!/usr/bin/env python3
"""
Test script to verify Cube.js connectivity and basic queries.

Usage:
    python scripts/test_cube.py
"""
import asyncio
import httpx
import json


CUBE_API_URL = "http://localhost:4000"
CUBE_API_SECRET = "flowiq-dev-secret-key"


async def test_cube_metadata():
    """Test fetching Cube.js metadata"""
    print("=" * 70)
    print("TEST 1: Fetch Cube.js Metadata")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{CUBE_API_URL}/cubejs-api/v1/meta",
                headers={"Authorization": CUBE_API_SECRET}
            )
            response.raise_for_status()
            meta = response.json()

            print(f"✅ Successfully connected to Cube.js")
            print(f"✅ Found {len(meta.get('cubes', []))} cubes")

            for cube in meta.get('cubes', []):
                cube_name = cube.get('name', 'unknown')
                measures_count = len(cube.get('measures', []))
                dimensions_count = len(cube.get('dimensions', []))
                print(f"  - {cube_name}: {measures_count} measures, {dimensions_count} dimensions")

            return True

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_customer_count():
    """Test customer count query"""
    print("\n" + "=" * 70)
    print("TEST 2: Customer Count Query")
    print("=" * 70)

    query = {
        "measures": ["customers.count", "customers.active_count"]
    }

    print(f"Query: {json.dumps(query, indent=2)}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CUBE_API_URL}/cubejs-api/v1/load",
                headers={"Authorization": CUBE_API_SECRET},
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            data = result.get('data', [])
            print(f"✅ Query executed successfully")

            if data:
                row = data[0]
                total = row.get('customers.count', 0)
                active = row.get('customers.active_count', 0)
                print(f"✅ Total Customers: {total}")
                print(f"✅ Active Customers: {active}")
            else:
                print("⚠️  No data returned")

            return True

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_revenue_query():
    """Test revenue metrics query"""
    print("\n" + "=" * 70)
    print("TEST 3: Revenue Metrics Query")
    print("=" * 70)

    query = {
        "measures": [
            "payments.total_revenue",
            "payments.count",
            "payments.average_payment"
        ]
    }

    print(f"Query: {json.dumps(query, indent=2)}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CUBE_API_URL}/cubejs-api/v1/load",
                headers={"Authorization": CUBE_API_SECRET},
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            data = result.get('data', [])
            print(f"✅ Query executed successfully")

            if data:
                row = data[0]
                revenue = row.get('payments.total_revenue', 0)
                count = row.get('payments.count', 0)
                avg = row.get('payments.average_payment', 0)
                print(f"✅ Total Revenue: ${revenue}")
                print(f"✅ Total Payments: {count}")
                print(f"✅ Average Payment: ${avg}")
            else:
                print("⚠️  No data returned")

            return True

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_rental_analysis():
    """Test rental analysis with customer grouping"""
    print("\n" + "=" * 70)
    print("TEST 4: Rental Analysis by Customer")
    print("=" * 70)

    query = {
        "measures": [
            "rentals.count",
            "rentals.returned_count",
            "rentals.outstanding_count"
        ],
        "dimensions": ["customers.full_name"],
        "order": {"rentals.count": "desc"},
        "limit": 5
    }

    print(f"Query: {json.dumps(query, indent=2)}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CUBE_API_URL}/cubejs-api/v1/load",
                headers={"Authorization": CUBE_API_SECRET},
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            data = result.get('data', [])
            print(f"✅ Query executed successfully")
            print(f"✅ Returned {len(data)} rows")

            if data:
                print("\nTop 5 Customers by Rental Count:")
                for row in data:
                    name = row.get('customers.full_name', 'Unknown')
                    total = row.get('rentals.count', 0)
                    returned = row.get('rentals.returned_count', 0)
                    outstanding = row.get('rentals.outstanding_count', 0)
                    print(f"  {name}:")
                    print(f"    Total: {total}, Returned: {returned}, Outstanding: {outstanding}")
            else:
                print("⚠️  No data returned")

            return True

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def main():
    """Run all tests"""
    print("\n" + "🔧 " * 30)
    print("CUBE.JS CONNECTIVITY TEST - DVD RENTAL DATABASE")
    print("🔧 " * 30 + "\n")

    # Test 1: Metadata
    test1_passed = await test_cube_metadata()

    if not test1_passed:
        print("\n❌ FAILED: Cannot connect to Cube.js")
        print("\nTroubleshooting:")
        print("1. Make sure Cube.js is running: docker-compose ps")
        print("2. Check Cube.js logs: docker-compose logs cube")
        print("3. Verify CUBE_API_SECRET matches in .env and docker-compose.yml")
        print("4. Ensure cube models are in cube/model/cubes/ directory")
        return

    # Test 2: Customer count
    test2_passed = await test_customer_count()

    # Test 3: Revenue query
    test3_passed = await test_revenue_query()

    # Test 4: Rental analysis
    test4_passed = await test_rental_analysis()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Metadata: {'PASS' if test1_passed else 'FAIL'}")
    print(f"✅ Customer Count: {'PASS' if test2_passed else 'FAIL'}")
    print(f"✅ Revenue Metrics: {'PASS' if test3_passed else 'FAIL'}")
    print(f"✅ Rental Analysis: {'PASS' if test4_passed else 'FAIL'}")

    if test1_passed and test2_passed and test3_passed and test4_passed:
        print("\n🎉 All tests passed! Cube.js is ready to use.")
        print("\nNext steps:")
        print("1. Create Cube.js client in src/app/infra/cube/")
        print("2. Create analytics tools")
        print("3. Enhance FlowIQ agent with Cube.js context")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")


if __name__ == "__main__":
    asyncio.run(main())
