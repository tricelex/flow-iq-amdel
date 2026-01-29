from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.infra.flow_iq_agent import FlowIQAgent
from app.services.misc_services import format_sse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User's message/question", min_length=1)
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID for session persistence"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint (for documentation only - actual response is SSE)."""
    message: str = Field(description="AI response message")
    conversation_id: str = Field(description="Conversation ID for this session")


# ============================================================
# Chat Endpoint
# ============================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with FlowIQ Analytics Assistant",
    description="""
    Send a message to the FlowIQ AI analytics assistant and receive a streaming response.

    The assistant can help you analyze:
    - Customer data (counts, top customers, activity)
    - Revenue metrics (total, by customer, by period)
    - Rental statistics (outstanding, return rates, durations)

    Example queries:
    - "How many customers do we have?"
    - "What's our total revenue?"
    - "Who are the top 5 customers by rental count?"
    - "How many rentals are currently outstanding?"

    The response is streamed using Server-Sent Events (SSE).
    """,
    responses={
        200: {
            "description": "Streaming response with AI-generated insights",
            "content": {
                "text/event-stream": {
                    "example": "event: raw_response_event\ndata: {\"delta\":\"Hello\",\"type\":\"text_delta\"}\n\n"
                }
            }
        },
        500: {"description": "Internal server error during processing"}
    }
)
async def chat(request: ChatRequest):
    """Chat with FlowIQ analytics assistant.

    Receives a user message and streams back AI-generated analytics insights
    using Server-Sent Events (SSE).

    Args:
        request: Chat request with message and optional conversation ID

    Returns:
        StreamingResponse with SSE events containing AI responses and tool calls
    """
    logger.info(
        "chat_request_received",
        message_preview=request.message[:100],
        conversation_id=request.conversation_id
    )

    async def event_generator():
        """Generate SSE events from the FlowIQ agent."""
        agent = None

        try:
            # Initialize FlowIQ agent
            agent = FlowIQAgent(conversation_id=request.conversation_id)

            logger.info("initializing_agent")
            await agent.initialize()

            logger.info("agent_running", message=request.message[:100])

            # Stream events from agent
            async for event in agent.run(message=request.message):
                # Format as SSE and yield
                yield format_sse(data=event.get("data", {}), event=event.get("type", "unknown"))

            logger.info("chat_completed_successfully")

        except RuntimeError as e:
            # Agent not initialized or other runtime errors
            logger.exception("chat_runtime_error", error=str(e))
            error_event = {
                "type": "error",
                "data": {
                    "error": "Agent initialization failed",
                    "message": "The analytics assistant failed to initialize. Please try again.",
                    "details": str(e)
                }
            }
            yield format_sse(data=error_event["data"], event=error_event["type"])

        except Exception as e:
            # Unexpected errors
            logger.exception("chat_unexpected_error", error=str(e))
            error_event = {
                "type": "error",
                "data": {
                    "error": "Unexpected error",
                    "message": "An unexpected error occurred while processing your request.",
                    "details": str(e)
                }
            }
            yield format_sse(data=error_event["data"], event=error_event["type"])

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        },
    )
