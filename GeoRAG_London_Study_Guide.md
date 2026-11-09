# GeoRAG London: Full Project Study Guide

This document walks through everything built in this project, in order, with the commands, code, and concepts explained. It is meant as a reference you can go back to, not just a changelog.

---

## 1. Project Overview

GeoRAG London combines two things that are usually built separately:

1. **Spatial data**: the real geographic boundaries of London's 33 boroughs, stored in PostGIS.
2. **RAG (Retrieval Augmented Generation)**: a searchable, embedded version of The London Plan 2021, the official planning document for London.

The core feature is a combined endpoint that detects when a question mentions a borough, pulls that borough's data, and uses it to sharpen both the text retrieval and the final answer, while also highlighting the borough on a map.

**Stack**: FastAPI, PostgreSQL 16 + PostGIS + pgvector (one database), SQLAlchemy, Alembic, React (Vite), Leaflet, OpenRouter (for embeddings and chat), Docker.

---

## 2. Git and GitHub Workflow

### 2.1 Branching model used throughout the project

- `main`: always stable, deploy-ready.
- `dev`: integration branch where finished features land.
- `feat/<topic>`, `chore/<topic>`, `docs/<topic>`: one branch per unit of work.

Each feature branch merges into `dev` through a Pull Request, even on a solo project. This is deliberate: it creates a record of what changed and why, it mirrors how real teams work, and it gives the repository a professional commit history.

### 2.2 Core commands

```bash
# Start a new feature branch from the latest dev
git checkout dev
git pull origin dev
git checkout -b feat/my-feature

# Stage, commit, push
git add .
git commit -m "feat: short description of what changed"
git push -u origin feat/my-feature

# After merging the PR on GitHub (and deleting the branch there)
git checkout dev
git pull origin dev
```

### 2.3 Rebasing a branch that was created before a dependency was merged

If a branch is created from an older point in `dev` and then `dev` gets new commits it needs, `rebase` replays the branch's commits on top of the new `dev`, keeping history linear:

```bash
git checkout feat/my-feature
git rebase dev
```

This is different from `git merge dev`, which would create an extra merge commit. For a personal feature branch not yet merged, rebase keeps the history cleaner.

---

## 3. Docker Fundamentals

### 3.1 What a Dockerfile does

A Dockerfile is a recipe for building an image: a self-contained snapshot of an application and everything it needs to run (OS packages, language runtime, dependencies, code).

### 3.2 Backend Dockerfile (`Dockerfile.api`)

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key points:

- **Copy `requirements.txt` before the rest of the code.** Docker caches each instruction as a layer. If only the application code changes, the cached `pip install` layer is reused, so the build does not reinstall every dependency from scratch each time.
- **`--host 0.0.0.0`**, not `localhost`. The server must accept connections from outside the container, not just from within it.
- **`EXPOSE`** is documentation, not enforcement. It does not open a port by itself; the actual port mapping happens in `docker-compose.yml`.

### 3.3 Frontend Dockerfile: multi-stage build (`Dockerfile.frontend`)

```dockerfile
# Stage 1: build the React app
FROM node:20-slim AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend/ .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Stage 2: serve the built files with Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
```

A React app does not run as a live process in production; it compiles down to static HTML, CSS, and JS files. A **multi-stage build** uses one stage (with Node.js) to compile those files, then copies only the final output into a second, much lighter stage (Nginx, a static file server). Node.js, `node_modules`, and the source code are discarded, so the final image stays small.

- `ARG VITE_API_BASE_URL` declares a build-time argument.
- `ENV VITE_API_BASE_URL=$VITE_API_BASE_URL` turns it into an environment variable, because Vite reads environment variables (`import.meta.env.VITE_...`) at build time, not `ARG`s directly.

### 3.4 The pgvector installation problem (a real debugging story)

The official `postgis/postgis` image did not include pgvector. Several approaches were tried, in order:

1. **`apt-get install postgresql-16-pgvector`**: failed because the Postgres package repository (`apt.postgresql.org`) returned a 404.
2. **Compile pgvector from source** (`git clone` + `make` + `make install`): hit the same broken repository when trying to install build tools like `postgresql-server-dev-16`.
3. **Remove the broken repository file** (`rm /etc/apt/sources.list.d/pgdg.list`) before compiling: this time `apt-get update` succeeded, but installing `libpq-dev` then failed because the base image already had a newer `libpq5` installed from the (now removed) repository, creating a version conflict the package manager could not resolve.
4. **Final working solution: multi-stage copy, no package manager involved at all.**

```dockerfile
FROM pgvector/pgvector:pg16 AS pgvector_src

FROM postgis/postgis:16-3.4

COPY --from=pgvector_src /usr/lib/postgresql/16/lib/vector.so /usr/lib/postgresql/16/lib/vector.so
COPY --from=pgvector_src /usr/share/postgresql/16/extension/vector.control /usr/share/postgresql/16/extension/vector.control
COPY --from=pgvector_src /usr/share/postgresql/16/extension/ /usr/share/postgresql/16/extension/
```

This copies the already-compiled pgvector files directly from the official `pgvector/pgvector` image into the PostGIS image. Since both images are built on Postgres 16, the files are compatible. No apt, no compiler, no external repository dependency. This is the kind of debugging story worth explaining in an interview: multiple approaches tried, each failure diagnosed, and a final approach chosen because it removes the dependency that was causing the problem rather than working around it.

### 3.5 `docker-compose.yml`: running multiple containers together

```yaml
services:
  db:
    build:
      context: .
      dockerfile: Dockerfile.db
    container_name: georag_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-georag}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-georag}
      POSTGRES_DB: ${POSTGRES_DB:-georag}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-georag}"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: georag_api
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+psycopg2://${POSTGRES_USER:-georag}:${POSTGRES_PASSWORD:-georag}@db:5432/${POSTGRES_DB:-georag}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      MAX_PDF_PAGES: 0
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        VITE_API_BASE_URL: http://localhost:8000
    container_name: georag_frontend
    restart: unless-stopped
    depends_on:
      - api
    ports:
      - "5173:80"

volumes:
  pgdata:
```

Concepts to know:

- **`services`**: each top-level key is a separate container, built and run together.
- **Internal DNS**: inside the Docker network created by Compose, containers reach each other by service name, not `localhost`. The `api` service connects to the database at `db:5432`, not `localhost:5432`.
- **`volumes`** (the list form under a service, e.g. `- pgdata:/var/lib/postgresql/data`): mounts a named volume into the container at a path. Data written there survives container restarts and rebuilds.
- **`volumes`** (the top-level block at the end of the file): declares the named volume itself. This must be a mapping (`pgdata:`), not a list (`- pgdata`), which is a common YAML mistake.
- **`${VAR:-default}`**: reads `VAR` from the `.env` file; if it is not set, uses `default`.
- **`depends_on: db: condition: service_healthy`**: waits for the database's healthcheck to pass before starting `api`, preventing a race where the API tries to connect before Postgres is ready.
- **`ports: "5432:5432"`**: maps container port to host port. This must stay on the `db` service so you can still connect from `localhost` when running the backend directly (not through Docker) during local development, even though the `api` container itself uses the internal `db` hostname.

### 3.6 Essential Docker commands

```bash
# Build and start everything, rebuilding images
docker compose up -d --build

# Start a single service (useful when developing outside Docker)
docker compose up -d db

# Check status of all containers
docker compose ps

# View logs for one service
docker compose logs api

# Stop containers, KEEP volumes (data is preserved)
docker compose down

# Stop containers AND DELETE volumes (all data is lost)
docker compose down -v

# Run a command inside a running container
docker exec -it georag_db psql -U georag -d georag -c "\dt"

# Copy a file out of a container
docker cp georag_db:/tmp/file.dump ./local-file.dump
```

The difference between `down` and `down -v` matters a lot in practice: `-v` deletes named volumes, which means all database data is gone. Use it only when you deliberately want a clean slate.

### 3.7 `.dockerignore`

Same idea as `.gitignore`, but for what gets sent to the Docker build context:

```
.venv/
__pycache__/
*.pyc
.env
data/raw/*
!data/raw/.gitkeep
node_modules/
frontend/dist/
.git/
```

This keeps builds fast (less data to send) and keeps sensitive or irrelevant files (like `.env`) out of the image entirely.

---

## 4. Database: PostgreSQL + PostGIS + pgvector

### 4.1 Why one database for everything

Instead of a separate vector database (like Qdrant) plus a separate spatial database, this project keeps spatial data, text, and embeddings in a single PostgreSQL database with two extensions:

- **PostGIS**: adds geometry types and spatial functions.
- **pgvector**: adds a `vector` column type and nearest-neighbor search (cosine distance, etc.) for embeddings.

This allows a single SQL query to combine a spatial filter with a semantic search, and avoids running and maintaining two separate database services.

### 4.2 The three tables

```python
EMBEDDING_DIM = 2048  # confirmed via a live API call to the embedding model

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    document = relationship("Document", back_populates="chunks")


class Borough(Base):
    __tablename__ = "boroughs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    population = Column(Integer, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
```

Key concepts:

- **`ForeignKey(..., ondelete="CASCADE")`**: enforces, at the database level, that deleting a `Document` deletes its `DocumentChunk` rows. Without `ondelete="CASCADE"`, a raw SQL `DELETE` on `documents` fails with a foreign key violation, even though SQLAlchemy's own `cascade="all, delete-orphan"` (an ORM-level setting, not a database rule) handles the same case when deleting through the ORM. Both forms of cascade were needed because they operate at different layers.
- **`relationship(...)`**: a convenience layer in SQLAlchemy, not a database column. It lets you write `document.chunks` or `chunk.document` instead of writing a join manually. `back_populates` links both sides of the relationship so updating one side (e.g. appending to `document.chunks`) keeps the other side (`chunk.document`) in sync.
- **`Geometry(geometry_type="MULTIPOLYGON", srid=4326)`**: a PostGIS-aware column type from GeoAlchemy2. `MULTIPOLYGON` because a borough's boundary can consist of more than one polygon (e.g. disconnected pieces). SRID 4326 is WGS84, the standard latitude/longitude coordinate system used by GPS.
- **`Vector(EMBEDDING_DIM)`**: the pgvector column type. The dimension must exactly match the embedding model's actual output size; it was verified with a real API call rather than assumed from documentation.

### 4.3 Alembic migrations

Alembic tracks schema changes as versioned files, each with an `upgrade()` and a `downgrade()` function, so changes can be applied or rolled back.

```bash
# Create a new migration by comparing models to the current database state
alembic revision --autogenerate -m "description of the change"

# Apply all pending migrations
alembic upgrade head

# Check which migration is currently applied
alembic current
```

**Important habit: always read the generated migration file before running it.** Autogenerate is not always correct. Two real examples from this project:

1. It proposed `op.drop_table("spatial_ref_sys")`, a PostGIS system table that is not one of this project's models but is required for PostGIS to function. Running this would have broken the database. The fix was to delete that line from the migration before applying it.
2. It proposed a duplicate `CREATE INDEX` on a `Geometry` column, because GeoAlchemy2 already creates a GIST index automatically when the table is created, and autogenerate did not detect that. Running it caused a "relation already exists" error. The fix was to remove the redundant `op.create_index(...)` call.

### 4.4 Useful psql commands

```bash
# List tables
docker exec -it georag_db psql -U georag -d georag -c "\dt"

# Describe a table's columns and indexes
docker exec -it georag_db psql -U georag -d georag -c "\d document_chunks"

# List installed extensions
docker exec -it georag_db psql -U georag -d georag -c "\dx"

# Run an arbitrary query
docker exec -it georag_db psql -U georag -d georag -c "SELECT COUNT(*) FROM document_chunks;"
```

### 4.5 Database seed (backup and restore)

To avoid forcing anyone who clones the repository to re-run hours of embedding API calls, a snapshot of the finished database is exported and committed:

```bash
# Create a dump inside the container, then copy it out
docker exec georag_db pg_dump -U georag -d georag --format=custom --file=/tmp/georag_seed.dump
docker cp georag_db:/tmp/georag_seed.dump db-seed/georag_seed.dump

# Restore it into a fresh database
docker exec -i georag_db pg_restore -U georag -d georag --clean --if-exists < db-seed/georag_seed.dump
```

`--format=custom` produces a compact, binary dump restorable with `pg_restore`. `--clean --if-exists` drops existing objects before restoring, avoiding conflicts with old data.

---

## 5. FastAPI Backend

### 5.1 Configuration with Pydantic Settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    openrouter_api_key: str = ""
    max_pdf_pages: int = 0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

`BaseSettings` reads values from environment variables or a `.env` file and validates them automatically. If a required value (like `database_url`) is missing, the application fails immediately at startup with a clear error, instead of failing unpredictably later.

### 5.2 Database session setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`get_db` is written as a generator (`yield`) so it can be used as a FastAPI dependency: FastAPI calls it, hands the yielded session to the endpoint function, and runs the code after `yield` (closing the session) once the request finishes, regardless of whether it succeeded or raised an error.

### 5.3 Routers and dependency injection

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import Borough

router = APIRouter(prefix="/boroughs", tags=["boroughs"])

@router.get("/{name}")
def get_borough(name: str, db: Session = Depends(get_db)):
    borough = db.query(Borough).filter(Borough.name.ilike(name)).first()
    if borough is None:
        raise HTTPException(status_code=404, detail=f"Borough '{name}' not found")
    return {"id": borough.id, "name": borough.name}
```

- `APIRouter(prefix=...)` groups related endpoints under a shared URL prefix, instead of defining every route directly on the main app.
- `Depends(get_db)` is FastAPI's dependency injection mechanism. FastAPI calls `get_db()` automatically for each request, passes the resulting session into the endpoint, and manages its lifecycle.
- **Route ordering matters.** A route like `/boroughs/geojson/all` must be defined before `/boroughs/{name}`, or FastAPI will try to match `geojson` as a borough name.

### 5.4 Pydantic request and response models

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    ...
```

`ChatRequest` validates the incoming JSON body automatically; a malformed request gets a clear 422 error without any manual checking. `response_model` documents and validates the shape of the response, and also powers the automatic interactive documentation at `/docs`.

### 5.5 CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Browsers block requests between different origins (different ports count as different origins) by default. This middleware explicitly allows the frontend's origin to call the backend.

---

## 6. RAG Pipeline

### 6.1 The full chain

```
PDF -> extract text -> split into chunks -> embed each chunk -> store in pgvector
question -> embed question -> find nearest chunks (cosine distance) -> pass as context to an LLM -> generated answer
```

### 6.2 Extracting text robustly

```python
def extract_full_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages_text = []
    skipped_pages = []
    for i, page in enumerate(reader.pages):
        try:
            pages_text.append(page.extract_text())
        except Exception as e:
            skipped_pages.append(i)
            continue
    return "\n\n".join(pages_text)
```

A few pages in the real PDF (complex embedded graphics) throw errors during extraction. Wrapping each page's extraction in `try/except` and skipping the failed ones, rather than letting one bad page crash the whole run, is a common and important pattern when processing real-world data.

### 6.3 Chunking with overlap

```python
def chunk_paragraphs(paragraphs, target_words=350, overlap_words=50):
    chunks = []
    current_words = []
    for para in paragraphs:
        current_words.extend(para.split())
        if len(current_words) >= target_words:
            chunks.append(" ".join(current_words))
            current_words = current_words[-overlap_words:]
    if current_words:
        chunks.append(" ".join(current_words))
    return chunks
```

Chunks that are too large hurt retrieval precision; chunks that are too small lose context. The overlap (keeping the last 50 words of one chunk as the start of the next) prevents an important sentence from being split exactly at a chunk boundary and losing its surrounding context.

### 6.4 Calling the embedding API with retries

```python
def get_embedding(text: str, max_retries: int = 6) -> list[float]:
    for attempt in range(max_retries):
        response = requests.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            json={"model": "nvidia/llama-nemotron-embed-vl-1b-v2:free", "input": text},
        )
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        if response.status_code == 429:
            wait = min(2 ** attempt, 60)
            time.sleep(wait)
            continue
        response.raise_for_status()
    raise RuntimeError(f"Failed to get embedding after {max_retries} retries")
```

This is **exponential backoff**: each retry waits twice as long as the previous one (1s, 2s, 4s, 8s...), capped at 60 seconds, instead of retrying immediately and making rate limiting worse.

### 6.5 Resumable ingestion

Free-tier API rate limits (OpenRouter enforces a daily request cap on free models) mean a long ingestion run can be interrupted partway through. The script checks which chunks are already embedded before processing:

```python
already_done = {
    row.chunk_index
    for row in db.query(DocumentChunk.chunk_index).filter_by(document_id=document.id)
}

for i, chunk_text in enumerate(chunks):
    if i in already_done:
        continue
    embedding = get_embedding(chunk_text)
    # ... save it
    if (i + 1) % 10 == 0:
        db.commit()  # periodic commit so progress is not lost
```

Periodic commits (not just one commit at the end) mean that if the script crashes or hits a rate limit, the already-processed chunks are saved, and a simple re-run picks up where it left off, rather than starting over.

### 6.6 Semantic search with pgvector

```python
results = (
    db.query(DocumentChunk)
    .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
    .limit(TOP_K)
    .all()
)
```

`cosine_distance` is provided by pgvector's SQLAlchemy integration. Ordering by it returns the chunks whose embeddings are closest in meaning to the query's embedding, lowest distance (most similar) first.

### 6.7 Generating a grounded answer

```python
def generate_answer(question: str, context_chunks: list[str]) -> str:
    context_text = "\n\n---\n\n".join(context_chunks)
    system_prompt = (
        "You are an assistant answering questions about London urban planning "
        "and geography, based on the London Plan 2021. Use ONLY the provided "
        "context to answer. If the context doesn't contain the answer, say so "
        "clearly instead of guessing."
    )
    user_prompt = f"Context:\n{context_text}\n\nQuestion: {question}"
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
        json={
            "model": "openrouter/free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
```

The explicit instruction to use only the provided context is a **grounding instruction**: without it, a language model tends to blend its own general knowledge with the retrieved text, which can contradict the actual source document. This is the core defense against hallucination in a RAG system.

**Model choice**: `openrouter/free` is an auto-router that resolves to whichever free model is currently available, rather than a specific hardcoded model name. OpenRouter's free model lineup changes often, so pinning a specific model risks the project breaking within weeks for reasons unrelated to the code.

### 6.8 Combining spatial and text retrieval (the project's core feature)

```python
def find_mentioned_borough(db, question: str):
    boroughs = db.query(Borough).all()
    question_lower = question.lower()
    for borough in boroughs:
        if borough.name.lower() in question_lower:
            return borough
    return None

@router.post("")
def geo_chat(request: GeoChatRequest, db: Session = Depends(get_db)):
    borough = find_mentioned_borough(db, request.question)

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
    if borough is not None:
        context_chunks = [f"Note: relates to {borough.name} (population: {borough.population})."] + context_chunks

    answer = generate_answer(request.question, context_chunks)
    return GeoChatResponse(
        answer=answer,
        sources=[f"chunk {r.chunk_index}" for r in results],
        matched_borough={"name": borough.name, "population": borough.population} if borough else None,
    )
```

If a borough name appears in the question, it enriches both the search query (for better retrieval) and the LLM's context (so the answer can reference borough-specific facts), and the response includes the matched borough so the frontend can highlight it on the map. This is a simple substring match, not fuzzy matching or named entity recognition; a known limitation, but good enough for an MVP.

---

## 7. React Frontend

### 7.1 Core concepts

- **Component**: a reusable, self-contained piece of UI, written as a function that returns markup (JSX).
- **State** (`useState`): data that belongs to a component; changing it causes React to re-render the parts of the UI that depend on it.
- **Props**: data passed from a parent component to a child component.
- **Hooks**: special functions (always starting with `use`) that let a function component manage state, side effects, or other React features.

### 7.2 `useState` and `useEffect`

```jsx
const [geoData, setGeoData] = useState(null);

useEffect(() => {
  axios.get(`${API_BASE_URL}/boroughs/geojson/all`).then((response) => {
    setGeoData(response.data);
  });
}, []);
```

`useState(null)` creates a piece of state starting at `null`, with `setGeoData` as the function to update it. `useEffect(fn, [])` runs `fn` once, right after the component first renders; the empty dependency array means "run only on mount." This is the standard pattern for fetching data when a component first appears.

### 7.3 Lifting state up

When two sibling components (a map and a chat panel) need to share and react to the same piece of data (which borough is selected), that state lives in their common parent, and is passed down as props, with a callback passed down so a child can request a change:

```jsx
function App() {
  const [selectedBorough, setSelectedBorough] = useState(null);
  return (
    <>
      <MapView selectedBorough={selectedBorough} />
      <ChatPanel onBoroughMatch={setSelectedBorough} />
    </>
  );
}
```

`ChatPanel` never touches `MapView` directly. It calls `onBoroughMatch(name)`, which is really `setSelectedBorough(name)` passed down from `App`. `App` re-renders with the new state, and that new value flows back down into `MapView` as a prop. This is the standard way for sibling components to communicate in React.

### 7.4 Calling the backend from React

```jsx
const handleSubmit = async (e) => {
  e.preventDefault();
  try {
    const response = await axios.post(`${API_BASE_URL}/geo-chat`, {
      question: userMessage.content,
    });
    const { answer, matched_borough, sources } = response.data;
    setMessages((prev) => [...prev, { role: "assistant", content: answer, sources }]);
  } catch (error) {
    // handle error
  }
};
```

`async`/`await` works the same way conceptually as in Python. `setMessages((prev) => [...prev, newMessage])` updates state based on its previous value using a functional update, which avoids subtle bugs when several updates happen close together. `[...prev, newMessage]` is the spread operator, producing a new array containing everything in `prev` plus the new item.

### 7.5 Leaflet integration (`react-leaflet`)

```jsx
<MapContainer center={LONDON_CENTER} zoom={10} style={{ height: "100%", width: "100%" }}>
  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
  <GeoJSON data={geoData} style={styleFn} onEachFeature={onEachFeatureFn} />
</MapContainer>
```

`GeoJSON` renders a standard GeoJSON FeatureCollection directly, which is exactly the format the backend's `/boroughs/geojson/all` endpoint returns. `onEachFeature` runs for every feature (every borough) and is used here to attach a popup showing the borough's name and population.

A custom component using the `useMap()` hook can reach into the underlying Leaflet map instance to do things like fly to a borough's bounding box when it gets selected, something that cannot be done purely declaratively:

```jsx
function FlyToBorough({ geoData, selectedBorough }) {
  const map = useMap();
  useEffect(() => {
    // compute bounds from the selected feature's geometry, then:
    map.flyToBounds(bounds, { padding: [40, 40], duration: 1 });
  }, [selectedBorough, geoData, map]);
  return null;
}
```

### 7.6 Theming with CSS custom properties

```css
:root {
  --bg: #0f1419;
  --text: #e5e7eb;
  --accent: #60a5fa;
}
[data-theme="light"] {
  --bg: #ffffff;
  --text: #1a1d23;
  --accent: #2563eb;
}
```

```jsx
useEffect(() => {
  document.documentElement.setAttribute("data-theme", theme);
}, [theme]);
```

Every component references colors through `var(--bg)`, `var(--text)`, etc., instead of hardcoding values. Flipping the `data-theme` attribute on `<html>` switches every variable at once, so the entire UI re-themes without touching individual components.

A dark map was implemented as a pure CSS rule tied to the same attribute:

```css
[data-theme="dark"] .leaflet-tile-pane {
  filter: invert(1) hue-rotate(180deg) brightness(0.95) contrast(0.9);
}
```

An earlier version tried to apply this filter by finding the DOM element in JavaScript (`useEffect` + `querySelectorAll`) and toggling a class manually, which had a timing bug on first load. Expressing it as a plain CSS rule tied directly to the attribute removed the timing dependency entirely.

---

## 8. Command Reference (Quick Lookup)

```bash
# Git
git checkout -b feat/name          # new branch
git add . && git commit -m "..."   # stage and commit
git push -u origin feat/name       # first push of a branch
git rebase dev                     # replay a branch on top of updated dev

# Python environment (uv)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Running the backend directly
uvicorn app.main:app --reload

# Alembic
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic current

# Running scripts as modules (so `app` imports resolve)
python3 -m scripts.ingest_boroughs

# Docker
docker compose up -d --build
docker compose ps
docker compose logs api
docker compose down          # keeps data
docker compose down -v       # deletes data, use carefully
docker exec -it <container> psql -U georag -d georag -c "\dt"

# Frontend
npm install
npm run dev
npm run build
```
