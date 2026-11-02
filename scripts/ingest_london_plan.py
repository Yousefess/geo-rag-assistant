import re
import time

from pypdf import PdfReader

from app.db.session import SessionLocal
from app.db.models import Document, DocumentChunk
from app.services.embeddings import get_embedding
from app.core.config import settings

PDF_PATH = "data/raw/london_plan_2021.pdf"
CHUNK_TARGET_WORDS = 350
CHUNK_OVERLAP_WORDS = 50


def extract_full_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    total = len(reader.pages)

    page_limit = settings.max_pdf_pages if settings.max_pdf_pages > 0 else total
    page_limit = min(page_limit, total)

    if settings.max_pdf_pages > 0:
        print(
            f"LIMITED MODE: processing first {page_limit} of {total} pages "
            f"(set MAX_PDF_PAGES=0 in .env to process all)"
        )

    pages_text = []
    skipped_pages = []

    for i in range(page_limit):
        page = reader.pages[i]
        try:
            pages_text.append(page.extract_text())
        except Exception as e:
            print(f"  WARNING: failed to extract page {i}: {e}")
            skipped_pages.append(i)
            continue

        if (i + 1) % 25 == 0:
            print(f"  Extracted {i + 1}/{page_limit} pages...")

    if skipped_pages:
        print(f"Skipped {len(skipped_pages)} pages: {skipped_pages}")

    return "\n\n".join(pages_text)


def split_into_paragraphs(text: str) -> list[str]:
    # split on blank lines / numbered-paragraph markers like "0.0.24"
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if len(p.strip()) > 20]


def chunk_paragraphs(paragraphs: list[str]) -> list[str]:
    chunks = []
    current_words: list[str] = []

    for para in paragraphs:
        current_words.extend(para.split())
        if len(current_words) >= CHUNK_TARGET_WORDS:
            chunks.append(" ".join(current_words))
            # keep the last N words as overlap for the next chunk
            current_words = current_words[-CHUNK_OVERLAP_WORDS:]

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def main():
    print("Extracting text from PDF...")
    full_text = extract_full_text(PDF_PATH)

    print("Splitting into paragraphs...")
    paragraphs = split_into_paragraphs(full_text)
    print(f"Found {len(paragraphs)} paragraphs")

    print("Chunking...")
    chunks = chunk_paragraphs(paragraphs)
    print(f"Created {len(chunks)} chunks")

    db = SessionLocal()
    try:
        # Resume support: reuse an existing Document for this source,
        # or create one if it doesn't exist yet.
        document = (
            db.query(Document)
            .filter_by(
                source_url="https://www.london.gov.uk/sites/default/files/the_london_plan_2021.pdf"
            )
            .first()
        )
        if document is None:
            document = Document(
                title="The London Plan 2021",
                source="london_plan",
                source_url="https://www.london.gov.uk/sites/default/files/the_london_plan_2021.pdf",
            )
            db.add(document)
            db.flush()
            print(f"Created new document_id={document.id}")
        else:
            print(f"Resuming existing document_id={document.id}")

        already_done = {
            row.chunk_index
            for row in db.query(DocumentChunk.chunk_index).filter_by(
                document_id=document.id
            )
        }
        if already_done:
            print(f"{len(already_done)} chunks already embedded, skipping those.")

        for i, chunk_text in enumerate(chunks):
            if i in already_done:
                continue

            embedding = get_embedding(chunk_text)
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding,
                )
            )
            if (i + 1) % 10 == 0:
                print(f"  Embedded {i + 1}/{len(chunks)} chunks...")
                db.commit()

            time.sleep(1.5)  # more conservative pacing for the free tier

        db.commit()
        print(f"Done. Document {document.id} now has {len(chunks)} chunks total.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
