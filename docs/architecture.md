# Architecture

## Overview

GeoRAG Assistant combines two capabilities that are usually built separately: spatial queries over real geographic data and retrieval-augmented generation (RAG) over a text document. The project covers London boroughs and The London Plan 2021 (the official urban planning document for Greater London).

The core idea: a user can ask a question in natural language, and if the question mentions a borough, the system retrieves that borough's data, enriches the RAG search with that context, and returns an answer grounded in the actual planning document, along with a map that highlights the relevant area.

## Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL 16 with PostGIS (spatial data) and pgvector (embeddings), in a single unified database
- **ORM**: SQLAlchemy with GeoAlchemy2 and pgvector's SQLAlchemy integration
- **Migrations**: Alembic
- **LLM provider**: OpenRouter (used for both embeddings and chat completion)
- **Frontend**: React (Vite), Leaflet for the map
- **Containerization**: Docker, with a single docker-compose.yml running the database, API, and frontend together

## Database schema

Three tables:

- `documents`: metadata for ingested text sources (title, source, source URL)
- `document_chunks`: chunked text per document, each row holding a 2048-dimension embedding vector. One-to-many with `documents`, with `ondelete=CASCADE` enforced at the database level so deleting a document always removes its chunks, regardless of whether the delete happens through the ORM or raw SQL
- `boroughs`: spatial data for London's 33 boroughs, with a PostGIS MULTIPOLYGON geometry column (SRID 4326, WGS84) and population figures

Putting spatial data, text, and embeddings in one PostgreSQL database (rather than a separate vector database like Qdrant) means a single query can combine a spatial filter with a semantic search, and it avoids running two separate database services.

## Key decisions

### Embedding model

Chunks are embedded with `nvidia/llama-nemotron-embed-vl-1b-v2:free` on OpenRouter (2048 dimensions, confirmed via a live API call rather than assumed). It was chosen over a smaller free alternative because of its much larger context window, which comfortably fits the chunk sizes used here.

### Chat model

The chat endpoint uses `openrouter/free`, an auto-router that resolves to whichever free model is currently available, instead of a specific model name. OpenRouter's free model roster changes frequently, so hardcoding one model risks the project breaking within weeks. The auto-router keeps the project working without maintenance.

### Chunking strategy

Text is split into paragraphs, then grouped into chunks of roughly 350 words with a 50-word overlap between consecutive chunks. This keeps related sentences from being split across chunk boundaries while keeping each chunk small enough for precise retrieval.

### Resumable ingestion

Both the free embedding model and the free chat model have daily rate limits on OpenRouter. The ingestion script checks which chunks already have embeddings before processing, so an interrupted run (from hitting a rate limit) can simply be re-run without reprocessing completed work.

### pgvector installation

The official PostGIS Docker image is built on a Debian base whose default package repository does not include a current Postgres version, and the Postgres-specific package repository (apt.postgresql.org) returned errors when queried during the build. Installing pgvector by compiling it from source inside the image ran into the same repository problem, and removing the broken repository then caused a dependency conflict with libpq.

The final approach avoids package managers entirely: it copies the compiled pgvector files directly from the official `pgvector/pgvector` Docker image into the PostGIS image, using a multi-stage Docker build. This has no dependency on any external package repository at build time.

### Frontend build and theming

The frontend is built with Vite and served by Nginx in production (a two-stage Docker build: Node.js builds the static files, then a lightweight Nginx image serves them). Light and dark themes are implemented with CSS custom properties switched by a `data-theme` attribute, and the dark map tiles use a pure CSS filter rather than JavaScript DOM manipulation, which avoided a timing bug present in an earlier version.

## Known limitations

- Borough name matching in the combined geo-chat endpoint is simple substring matching on the question text. It will not catch misspellings or alternate phrasings. A more robust version could use the LLM itself to extract the mentioned borough.
- A few pages of the source PDF fail text extraction due to complex embedded graphics and are skipped with a logged warning rather than causing the whole ingestion run to fail.
