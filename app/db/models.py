from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector

from app.db.session import Base

EMBEDDING_DIM = 1536  # based on the embedding model we'll choose later


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)  # e.g. "london_plan", "wikipedia"
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(
        Integer, nullable=False
    )  # position of this chunk within the document
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    document = relationship("Document", back_populates="chunks")


class Borough(Base):
    __tablename__ = "boroughs"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    population = Column(Integer, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
