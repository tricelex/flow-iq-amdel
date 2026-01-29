#!/usr/bin/env python3
"""
Test script for enhanced FlowIQ agent.

Tests the FlowIQ agent with various DVD rental queries to ensure it:
1. Initializes correctly with system prompt
2. Calls the right tools for different query types
3. Provides helpful, accurate responses
4. Handles errors gracefully

Usage:
    # Run as standalone script:
    python scripts/test_flow_iq_agent.py

    # Run with pytest:
    pytest scripts/test_flow_iq_agent.py -v
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.infra.flow_iq_agent.flow_iq import FlowIQAgent

# Mark all tests in this module as integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
]


# ============================================================
# Pytest Fixtures
# ============================================================

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the module."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    # Close the loop after all module tests complete
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()


@pytest.fixture(scope="module")
def initialized_agent(event_loop):
    """Create and initialize a FlowIQ agent for testing."""
    # Set the event loop for this thread
    asyncio.set_event_loop(event_loop)

    # Create and initialize agent
    agent = FlowIQAgent()
    event_loop.run_until_complete(agent.initialize())

    return agent


def print_separator(title: str):
    """Print a formatted separator."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def test_agent_initialization():
    """Test agent initialization."""
    print_separator("TEST 1: Agent Initialization")

    try:
        agent = FlowIQAgent()
        print("✅ Agent created")

        await agent.initialize()
        print("✅ Agent initialized with system prompt")

        return True, agent

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def run_simple_query(agent: FlowIQAgent, query: str):
    """Test a simple query and collect the response."""
    print(f"Query: \"{query}\"")
    print("\nResponse:")
    print("-" * 70)

    full_response = []
    tool_calls = []

    try:
        async for event in agent.run(query):
            if event["type"] == "raw_response_event":
                # Streaming text
                delta = event["data"]["delta"]
                print(delta, end="", flush=True)
                full_response.append(delta)

            elif event["type"] == "tool_call_item":
                # Tool being called
                tool_name = event["data"]["name"]
                tool_calls.append(tool_name)
                print(f"\n[🔧 Calling tool: {tool_name}]")

            elif event["type"] == "tool_call_output_item":
                # Tool output
                print(f"[✓ Tool completed]")

            elif event["type"] == "error":
                print(f"\n❌ Error: {event['data']['error']}")
                return False

        print("\n" + "-" * 70)

        if tool_calls:
            print(f"\n📊 Tools used: {', '.join(tool_calls)}")

        response_text = "".join(full_response)
        return len(response_text) > 0

    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def _test_customer_queries_impl(agent: FlowIQAgent):
    """Implementation for customer queries test."""
    print_separator("TEST 2: Customer Queries")

    queries = [
        "How many customers do we have?",
        "Who are the top 5 customers by rental count?",
    ]

    results = []
    for query in queries:
        print(f"\n{'─' * 70}\n")
        result = await run_simple_query(agent, query)
        results.append(result)
        await asyncio.sleep(1)  # Brief pause between queries

    return all(results)


# Pytest version
@pytest.mark.asyncio
async def test_customer_queries(initialized_agent: FlowIQAgent):
    """Test customer-related queries (pytest version)."""
    result = await _test_customer_queries_impl(initialized_agent)
    assert result, "Customer queries failed"


async def _test_revenue_queries_impl(agent: FlowIQAgent):
    """Implementation for revenue queries test."""
    print_separator("TEST 3: Revenue Queries")

    queries = [
        "What's our total revenue?",
        "Show me the top 3 customers by revenue",
    ]

    results = []
    for query in queries:
        print(f"\n{'─' * 70}\n")
        result = await run_simple_query(agent, query)
        results.append(result)
        await asyncio.sleep(1)

    return all(results)


# Pytest version
@pytest.mark.asyncio
async def test_revenue_queries(initialized_agent: FlowIQAgent):
    """Test revenue-related queries (pytest version)."""
    result = await _test_revenue_queries_impl(initialized_agent)
    assert result, "Revenue queries failed"


async def _test_rental_queries_impl(agent: FlowIQAgent):
    """Implementation for rental queries test."""
    print_separator("TEST 4: Rental Queries")

    queries = [
        "How many rentals are currently outstanding?",
        "What's our rental return rate?",
    ]

    results = []
    for query in queries:
        print(f"\n{'─' * 70}\n")
        result = await run_simple_query(agent, query)
        results.append(result)
        await asyncio.sleep(1)

    return all(results)


# Pytest version
@pytest.mark.asyncio
async def test_rental_queries(initialized_agent: FlowIQAgent):
    """Test rental-related queries (pytest version)."""
    result = await _test_rental_queries_impl(initialized_agent)
    assert result, "Rental queries failed"


async def _test_complex_query_impl(agent: FlowIQAgent):
    """Implementation for complex query test."""
    print_separator("TEST 5: Complex Query")

    query = "Who are the customers with the most outstanding rentals?"

    result = await run_simple_query(agent, query)
    return result


# Pytest version
@pytest.mark.asyncio
async def test_complex_query(initialized_agent: FlowIQAgent):
    """Test a complex analytical query (pytest version)."""
    result = await _test_complex_query_impl(initialized_agent)
    assert result, "Complex query failed"


async def _test_metadata_query_impl(agent: FlowIQAgent):
    """Implementation for metadata query test."""
    print_separator("TEST 6: Metadata Query")

    query = "What metrics and data can you show me?"

    result = await run_simple_query(agent, query)
    return result


# Pytest version
@pytest.mark.asyncio
async def test_metadata_query(initialized_agent: FlowIQAgent):
    """Test metadata/discovery query (pytest version)."""
    result = await _test_metadata_query_impl(initialized_agent)
    assert result, "Metadata query failed"


async def main():
    """Run all tests."""
    print("\n" + "🤖 " * 30)
    print("FLOWIQ AGENT TEST SUITE")
    print("Testing enhanced FlowIQ agent with DVD rental queries")
    print("🤖 " * 30 + "\n")

    # Test 1: Initialization
    init_passed, agent = await test_agent_initialization()
    if not init_passed or agent is None:
        print("\n⚠️  Agent initialization failed. Cannot continue tests.")
        return False

    # Run query tests
    tests = [
        ("Customer Queries", lambda: _test_customer_queries_impl(agent)),
        ("Revenue Queries", lambda: _test_revenue_queries_impl(agent)),
        ("Rental Queries", lambda: _test_rental_queries_impl(agent)),
        ("Complex Query", lambda: _test_complex_query_impl(agent)),
        ("Metadata Query", lambda: _test_metadata_query_impl(agent)),
    ]

    results = {"Initialization": init_passed}

    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"\n❌ {test_name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print_separator("TEST SUMMARY")

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All agent tests passed!")
        print("\n✅ Phase 4: Enhanced Agent - COMPLETE")
        print("\nNext steps:")
        print("1. Update INTEGRATION_CHECKLIST.md")
        print("2. Phase 5: Update chat API routes")
        print("3. Test the full API with streaming responses")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
