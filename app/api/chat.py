from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db
from app.db.models import DocumentChunk
from app.services.embeddings import get_embedding
from app.services.llm import generate_answer

router = APIRouter(prefix="/chat", tags=["chat"])

TOP_K = 4  # how many chunks to retrieve as context


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    query_embedding = get_embedding(request.question)

    results = (
        db.query(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(TOP_K)
        .all()
    )

    context_chunks = [r.content for r in results]
    answer = generate_answer(request.question, context_chunks)

    return ChatResponse(
        answer=answer,
        sources=[f"chunk {r.chunk_index}" for r in results],
    )
