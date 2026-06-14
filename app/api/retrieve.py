from fastapi import APIRouter

from app.api.schemas import RetrieveRequest, RetrieveResponse
from app.services.retrieve_service import retrieve_chunks


router = APIRouter()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    results = retrieve_chunks(query=request.query, top_k=request.top_k)

    return RetrieveResponse(
        query=request.query,
        top_k=request.top_k,
        results=results,
    )
