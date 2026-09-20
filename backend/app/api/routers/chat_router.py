from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.domain.session.value_objects import ChatSessionId
from app.api.schemas.requests import ChatRequest
from app.api.schemas.responses import ChatResponseChunk
from app.api.dependencies import get_chat_service
from app.application.chat.services import ChatService

import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)

@router.post(path='')
def chat(
    req: ChatRequest,
    service: ChatService = Depends(get_chat_service)
) -> StreamingResponse:
    """ 聊天 """
    
    def generate_sse():
        for chunk in service.chat(
            session_id=ChatSessionId(req.session_id),
            query=req.query,
            thinking=req.thinking,
            web=req.web,
            regenerate=req.regenerate
        ):
            yield f'data: {
                ChatResponseChunk(
                    session_id=req.session_id,
                    type=chunk.type.value,
                    content=chunk.content,
                    reasoning_content=chunk.reasoning_content,
                    reasoning_time=chunk.reasoning_time,
                    done=chunk.done
                ).model_dump_json(by_alias=True)
            }\n\n'

    return StreamingResponse(
        generate_sse(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )
