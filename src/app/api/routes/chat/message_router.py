import logging

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse

from app.domain.entities import ChatMessageDTO
from app.infra.flow_iq_agent import FlowIQAgent
from app.services.misc_services import form_as_model, format_sse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat")
async def chat(
    message: ChatMessageDTO = Depends(form_as_model(ChatMessageDTO)),
    file: UploadFile = File(...),
):
    async def event_generator():
        flow_iq_agent = FlowIQAgent()
        await flow_iq_agent.add_system_prompt(system_prompt="Code: 1225")
        async for event in flow_iq_agent.run(message=message.message):
            yield format_sse(data=event["data"], event=event["type"])

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
