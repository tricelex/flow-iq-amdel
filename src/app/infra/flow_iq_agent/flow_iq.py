from agents import Agent, Runner, OpenAIConversationsSession, ItemHelpers

from openai.types.responses import ResponseTextDeltaEvent, ResponseFunctionToolCall

# from app.domain.entities import AgentContextDTO
from app.infra.flow_iq_agent.tools import get_occupancy
from typing import AsyncGenerator, Dict, Any
import logging
import dotenv
dotenv.load_dotenv(override=True)

logger = logging.getLogger(__name__)

class FlowIQAgent:
    def __init__(self, conversation_id: str | None = None):
        self.agent = Agent(
            name="flow-iq",
            model="gpt-5",
            instructions="You are a helpful assistant.",
            tools=[get_occupancy]
        )
        self.runner = Runner()
        self.session = OpenAIConversationsSession(conversation_id=conversation_id)
    
    async def add_system_prompt(self, system_prompt: str):
        await self.session.add_items([{
            "role": "system", 
            "content": system_prompt
        }])
    
    async def run(self, message: str) -> AsyncGenerator[Dict[str, Any]]:
        result = self.runner.run_streamed(self.agent, message, session=self.session)

        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield {"type": "raw_response_event", "data": {
                    "delta": event.data.delta,
                    "type": "text_delta"
                }}

            # elif event.type == "agent_updated_stream_event":
            #     yield {"type": "agent_updated_stream_event", "data": event.new_agent.name}

            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    function_tool_call = event.item.raw_item
                    if isinstance(function_tool_call, ResponseFunctionToolCall):
                        yield {"type": "tool_call_item", "data": {
                            "name": function_tool_call.name,
                            "arguments": function_tool_call.arguments,
                            "type": "function_tool_call"
                        }}


                elif event.item.type == "tool_call_output_item":
                    yield {"type": "tool_call_output_item", "data": {
                        "output": event.item.output,
                        "type": "tool_call_output"
                    }}

                elif event.item.type == "message_output_item":
                    yield {"type": "message_output_item", "data": {
                        "output": ItemHelpers.text_message_output(event.item),
                        "type": "message_output"
                    }}

                else:
                    pass

