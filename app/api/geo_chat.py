import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db
from app.db.models import Borough, DocumentChunk
from app.services.embeddings import get_embedding
from app.services.llm import generate_answer

router = APIRouter(prefix="/geo-chat", tags=["geo-chat"])

TOP_K = 4


class GeoChatRequest(BaseModel):
    question: str


class GeoChatResponse(BaseModel):
    answer: str
    sources: list[str]
    matched_borough: dict | None


def find_mentioned_borough(db: Session, question: str) -> Borough | None:
    """Naive borough-name matching: check if any borough name appears
    in the question text (case-insensitive)."""
    boroughs = db.query(Borough).all()
    question_lower = question.lower()
    for borough in boroughs:
        if borough.name.lower() in question_lower:
            return borough
    return None


@router.post("", response_model=GeoChatResponse)
def geo_chat(request: GeoChatRequest, db: Session = Depends(get_db)):
    borough = find_mentioned_borough(db, request.question)

    # Enrich the query with borough context if we found one, so the
    # embedding search is more likely to retrieve relevant policy chunks
    search_query = request.question
    if borough is not None:
        search_query = f"{request.question} (relating to {borough.name} borough)"

    query_embedding = get_embedding(search_query)

    results = (
        db.query(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(TOP_K)
        .all()
    )

    context_chunks = [r.content for r in results]

    # If we matched a borough, add its stats as extra context for the LLM
    if borough is not None:
        borough_context = (
            f"Note: the question relates to the borough of {borough.name} "
            f"(population: {borough.population})."
        )
        context_chunks = [borough_context] + context_chunks

    answer = generate_answer(request.question, context_chunks)

    return GeoChatResponse(
        answer=answer,
        sources=[f"chunk {r.chunk_index}" for r in results],
        matched_borough=(
            {"name": borough.name, "population": borough.population}
            if borough is not None
            else None
        ),
    )
