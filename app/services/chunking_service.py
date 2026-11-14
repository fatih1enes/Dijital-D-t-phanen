"""Document chunking service for semantic search and page-level retrieval."""

import os
import re
from typing import Any

from app.logger import log_event


def _split_text_into_chunks(text: str, max_chars: int = 600, overlap_chars: int = 100) -> list[str]:
    """Split text into coherent chunks respecting paragraph and sentence boundaries."""
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    # Split into paragraphs, then into sentences with fixed-width lookbehind
    raw_paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    sentence_blocks: list[str] = []
    for p in raw_paragraphs:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
        sentence_blocks.extend(sentences)

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    for s in sentence_blocks:
        s_len = len(s)
        if current_len + s_len > max_chars and current_chunk:
            joined = " ".join(current_chunk)
            chunks.append(joined)
            if overlap_chars > 0 and len(joined) > overlap_chars:
                overlap_text = joined[-overlap_chars:]
                current_chunk = [overlap_text, s]
                current_len = len(overlap_text) + s_len
            else:
                current_chunk = [s]
                current_len = s_len
        else:
            current_chunk.append(s)
            current_len += s_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


class DocumentChunker:
    """Extracts page-indexed chunks from PDF, EPUB, and TXT documents."""

    @staticmethod
    def chunk_pdf(doc_path: str, file_hash: str, max_chars: int = 600) -> list[dict[str, Any]]:
        """Extract chunks page-by-page from a PDF using pypdfium2."""
        import pypdfium2

        from app.pdf import PDFIUM_LOCK

        chunks: list[dict[str, Any]] = []
        if not os.path.exists(doc_path):
            return chunks

        try:
            with PDFIUM_LOCK:
                pdf = pypdfium2.PdfDocument(doc_path)
                try:
                    total_pages = len(pdf)
                    chunk_global_idx = 0

                    for page_idx in range(total_pages):
                        page_no = page_idx + 1
                        try:
                            page = pdf[page_idx]
                            textpage = page.get_textpage()
                            page_text = textpage.get_text_range() or ""
                            clean_text = page_text.strip()
                            if not clean_text:
                                continue

                            page_chunks = _split_text_into_chunks(clean_text, max_chars=max_chars)
                            for c_text in page_chunks:
                                chunks.append(
                                    {
                                        "dosya_hash": file_hash,
                                        "sayfa_no": page_no,
                                        "chunk_index": chunk_global_idx,
                                        "metin": c_text,
                                        "char_count": len(c_text),
                                    }
                                )
                                chunk_global_idx += 1
                        except Exception as p_err:
                            log_event(
                                "pdf",
                                "DEBUG",
                                f"PDF sayfa {page_no} metin ayrıştırma notu: {p_err}",
                            )
                finally:
                    pdf.close()
        except Exception as e:
            log_event("pdf", "ERROR", f"PDF pypdfium2 chunking hatası ({doc_path}): {e}")

        return chunks

    @staticmethod
    def chunk_epub_or_txt(
        doc_path: str, file_hash: str, max_chars: int = 600
    ) -> list[dict[str, Any]]:
        """Extract chunks from EPUB or TXT documents with estimated virtual pagination."""
        chunks: list[dict[str, Any]] = []
        if not os.path.exists(doc_path):
            return chunks

        lower_path = doc_path.lower()
        full_text = ""

        try:
            if lower_path.endswith(".epub"):
                from app.epub import extract_text_from_epub

                full_text = extract_text_from_epub(doc_path, max_chars=500000)
            else:
                with open(doc_path, encoding="utf-8", errors="replace") as f:
                    full_text = f.read()
        except Exception as e:
            log_event("document", "ERROR", f"EPUB/TXT okuma hatası ({doc_path}): {e}")
            return chunks

        if not full_text or not full_text.strip():
            return chunks

        # Estimate virtual page (~1800 characters per typical book page)
        chars_per_page = 1800
        total_len = len(full_text)
        chunk_global_idx = 0

        for start_pos in range(0, total_len, chars_per_page):
            page_no = (start_pos // chars_per_page) + 1
            segment = full_text[start_pos : start_pos + chars_per_page]
            seg_chunks = _split_text_into_chunks(segment, max_chars=max_chars)
            for c_text in seg_chunks:
                chunks.append(
                    {
                        "dosya_hash": file_hash,
                        "sayfa_no": page_no,
                        "chunk_index": chunk_global_idx,
                        "metin": c_text,
                        "char_count": len(c_text),
                    }
                )
                chunk_global_idx += 1

        return chunks

    @classmethod
    def chunk_document(
        cls, doc_path: str, file_hash: str, max_chars: int = 600
    ) -> list[dict[str, Any]]:
        """Dispatch document chunking based on extension."""
        if not doc_path or not os.path.exists(doc_path):
            return []

        lower = doc_path.lower()
        if lower.endswith(".pdf"):
            return cls.chunk_pdf(doc_path, file_hash, max_chars=max_chars)
        elif lower.endswith((".epub", ".txt")):
            return cls.chunk_epub_or_txt(doc_path, file_hash, max_chars=max_chars)
        return []


async def index_document_chunks(
    db: Any, chunks: list[dict[str, Any]], embeddings: list[bytes] | None = None
) -> int:
    """Store chunks into kitap_chunks and synchronize FTS5 virtual table."""
    if not chunks:
        return 0

    conn = getattr(db, "conn", db)
    file_hash = chunks[0]["dosya_hash"]

    # Clear existing chunks for this book to allow idempotent re-indexing
    await conn.execute("DELETE FROM kitap_chunks WHERE dosya_hash = ?", (file_hash,))
    await conn.execute("DELETE FROM kitap_chunks_fts WHERE dosya_hash = ?", (file_hash,))

    # Batch insert into kitap_chunks
    chunk_rows = []
    for i, c in enumerate(chunks):
        emb_blob = embeddings[i] if embeddings and i < len(embeddings) else None
        chunk_rows.append(
            (
                str(c["dosya_hash"]),
                int(c.get("sayfa_no", 1)),
                int(c.get("chunk_index", i)),
                str(c.get("metin", "")),
                int(c.get("char_count", len(c.get("metin", "")))),
                emb_blob,
            )
        )

    await conn.executemany(
        """
        INSERT INTO kitap_chunks (dosya_hash, sayfa_no, chunk_index, metin, char_count, embedding)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        chunk_rows,
    )

    # Populate FTS5 table
    fts_rows = [
        (
            str(c["dosya_hash"]),
            int(c.get("sayfa_no", 1)),
            int(c.get("chunk_index", i)),
            str(c.get("metin", "")),
        )
        for i, c in enumerate(chunks)
    ]
    await conn.executemany(
        """
        INSERT INTO kitap_chunks_fts (dosya_hash, sayfa_no, chunk_index, metin)
        VALUES (?, ?, ?, ?)
        """,
        fts_rows,
    )

    await conn.commit()
    log_event(
        "database",
        "INFO",
        f"{len(chunks)} adet sayfa pasajı başarıyla indekslendi.",
        file_hash=file_hash,
    )
    return len(chunks)
