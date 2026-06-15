from fastapi import APIRouter

from app.api.schemas import ChatRequest, ChatResponse
from app.services.rag_service import generate_chat_response


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    response = generate_chat_response(query=request.query, top_k=request.top_k)

    return ChatResponse(**response)
