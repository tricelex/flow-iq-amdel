from collections.abc import AsyncGenerator
from typing import Any

import dotenv
from agents import Agent, ItemHelpers, OpenAIConversationsSession, Runner
from openai.types.responses import ResponseFunctionToolCall, ResponseTextDeltaEvent

from app.infra.flow_iq_agent.context_builder import build_system_prompt
from app.infra.flow_iq_agent.tools import (
    get_occupancy,
    query_analytics,
    get_customer_analysis,
    get_revenue_summary,
    get_rental_overview,
    get_available_metrics,
)
from app.core.logging import get_logger

dotenv.load_dotenv(override=True)

logger = get_logger(__name__)


class FlowIQAgent:
    """FlowIQ AI Analytics Agent.

    An AI agent specialized in DVD rental analytics, powered by Cube.js
    semantic layer and OpenAI's function calling.

    Usage:
        ```python
        agent = FlowIQAgent()
        await agent.initialize()

        async for event in agent.run("Who are our top customers?"):
            print(event)
        ```
    """

    def __init__(self, conversation_id: str | None = None):
        """Initialize FlowIQ agent.

        Args:
            conversation_id: Optional conversation ID for session persistence
        """
        self.conversation_id = conversation_id
        self.session = OpenAIConversationsSession(conversation_id=conversation_id)
        self.runner = Runner()

        # Initialize agent with all analytics tools
        self.agent = Agent(
            name="flow-iq",
            model="gpt-4o",
            instructions="You are FlowIQ, an AI analytics assistant. You will receive detailed instructions.",
            tools=[
                # Analytics tools
                query_analytics,
                get_customer_analysis,
                get_revenue_summary,
                get_rental_overview,
                get_available_metrics,
                # Legacy tool (can be removed later)
                get_occupancy,
            ]
        )

        self._initialized = False
        logger.info("flow_iq_agent_created", conversation_id=conversation_id)

    async def initialize(self) -> None:
        """Initialize agent with system prompt.

        This must be called after construction to set up the agent's
        context and instructions. It fetches Cube.js metadata and builds
        the complete system prompt.
        """
        if self._initialized:
            logger.debug("agent_already_initialized")
            return

        logger.info("initializing_flow_iq_agent")

        try:
            # Build system prompt with Cube.js context
            system_prompt = await build_system_prompt()

            # Add system prompt to session
            await self.session.add_items([{"role": "system", "content": system_prompt}])

            self._initialized = True
            logger.info("flow_iq_agent_initialized", prompt_length=len(system_prompt))

        except Exception as e:
            logger.exception("agent_initialization_failed", error=str(e))
            raise RuntimeError(f"Failed to initialize FlowIQ agent: {e}") from e

    async def add_system_prompt(self, system_prompt: str) -> None:
        """Add a custom system prompt to the session.

        Args:
            system_prompt: Custom system prompt text
        """
        await self.session.add_items([{"role": "system", "content": system_prompt}])
        logger.debug("custom_system_prompt_added", length=len(system_prompt))

    async def run(self, message: str) -> AsyncGenerator[dict[str, Any]]:
        """Run the agent with a user message and stream responses.

        Args:
            message: User's message/question

        Yields:
            Stream events including text deltas, tool calls, and outputs

        Raises:
            RuntimeError: If agent is not initialized
        """
        # Ensure agent is initialized
        if not self._initialized:
            logger.error("agent_not_initialized")
            raise RuntimeError(
                "Agent not initialized. Call await agent.initialize() before running."
            )

        logger.info("agent_run_started", message_preview=message[:100])

        try:
            result = self.runner.run_streamed(self.agent, message, session=self.session)

            async for event in result.stream_events():
                # Text delta events (streaming response)
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    yield {
                        "type": "raw_response_event",
                        "data": {"delta": event.data.delta, "type": "text_delta"}
                    }

                # Run item events (tool calls, outputs, messages)
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        # Tool being called
                        function_tool_call = event.item.raw_item
                        if isinstance(function_tool_call, ResponseFunctionToolCall):
                            logger.info(
                                "tool_called",
                                tool_name=function_tool_call.name,
                                arguments_preview=str(function_tool_call.arguments)[:200]
                            )
                            yield {
                                "type": "tool_call_item",
                                "data": {
                                    "name": function_tool_call.name,
                                    "arguments": function_tool_call.arguments,
                                    "type": "function_tool_call",
                                },
                            }

                    elif event.item.type == "tool_call_output_item":
                        # Tool output/result
                        logger.debug("tool_output_received", output_preview=str(event.item.output)[:200])
                        yield {
                            "type": "tool_call_output_item",
                            "data": {"output": event.item.output, "type": "tool_call_output"},
                        }

                    elif event.item.type == "message_output_item":
                        # Final message output
                        output = ItemHelpers.text_message_output(event.item)
                        logger.info("message_output", output_preview=output[:200])
                        yield {
                            "type": "message_output_item",
                            "data": {"output": output, "type": "message_output"},
                        }

            logger.info("agent_run_completed")

        except Exception as e:
            logger.exception("agent_run_failed", error=str(e))
            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "message": "An error occurred while processing your request."
                }
            }
