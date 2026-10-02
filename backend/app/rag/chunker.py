import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.core.config import settings

class SemanticChunk:
    def __init__(
        self,
        document_id: UUID,
        page_number: int,
        chunk_index: int,
        content: str,
        section_title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.document_id = document_id
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.content = content
        self.section_title = section_title or "General Information"
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": str(self.document_id),
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "section_title": self.section_title,
            "metadata": self.metadata,
        }

class IntelligentChunker:
    """
    Splits document sections semantically into coherent chunks.
    Ensures headers, product specifications, policies, and tables remain grouped together.
    """

    def __init__(self, target_chunk_size: int = None, chunk_overlap: int = None):
        self.target_chunk_size = target_chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def split_into_paragraphs_or_sentences(self, text: str) -> List[str]:
        # First try double newline (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        units: List[str] = []
        for p in paragraphs:
            # If paragraph is within reasonable size, keep as single unit
            if len(p) <= self.target_chunk_size:
                units.append(p)
            else:
                # Split large paragraph by sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', p)
                current_sentence_group = []
                current_len = 0
                for s in sentences:
                    s_clean = s.strip()
                    if not s_clean:
                        continue
                    if current_len + len(s_clean) > self.target_chunk_size and current_sentence_group:
                        units.append(" ".join(current_sentence_group))
                        current_sentence_group = [s_clean]
                        current_len = len(s_clean)
                    else:
                        current_sentence_group.append(s_clean)
                        current_len += len(s_clean)
                if current_sentence_group:
                    units.append(" ".join(current_sentence_group))
        return units

    def chunk_extracted_data(
        self,
        document_id: UUID,
        extracted_data: Dict[str, Any],
        doc_name: str = ""
    ) -> List[SemanticChunk]:
        chunks: List[SemanticChunk] = []
        sections = extracted_data.get("sections", [])
        chunk_idx = 0

        if not sections:
            # Fallback to page-by-page chunking if no structured sections
            pages = extracted_data.get("pages", [])
            for page in pages:
                page_num = page["page_number"]
                page_text = page["text"]
                units = self.split_into_paragraphs_or_sentences(page_text)
                current_accum = ""
                for unit in units:
                    if len(current_accum) + len(unit) > self.target_chunk_size and current_accum:
                        chunks.append(SemanticChunk(
                            document_id=document_id,
                            page_number=page_num,
                            chunk_index=chunk_idx,
                            content=current_accum.strip(),
                            section_title="General",
                            metadata={"doc_name": doc_name, "char_count": len(current_accum)}
                        ))
                        chunk_idx += 1
                        # Overlap: keep last sentence or tail
                        current_accum = unit
                    else:
                        current_accum = f"{current_accum}\n{unit}".strip()
                if current_accum:
                    chunks.append(SemanticChunk(
                        document_id=document_id,
                        page_number=page_num,
                        chunk_index=chunk_idx,
                        content=current_accum.strip(),
                        section_title="General",
                        metadata={"doc_name": doc_name, "char_count": len(current_accum)}
                    ))
                    chunk_idx += 1
            return chunks

        # Process structured sections
        for sec in sections:
            sec_title = sec["title"]
            sec_content = sec["content"]
            page_num = sec["page_number"]

            # If section content fits inside chunk size + header, keep it intact!
            # Prefixing chunk with section header guarantees semantic context is preserved
            prefixed_header = f"[{sec_title}]" if not sec_content.startswith("[") else ""
            
            if len(sec_content) + len(prefixed_header) + 2 <= self.target_chunk_size:
                full_content = f"{prefixed_header}\n{sec_content}".strip() if prefixed_header else sec_content
                chunks.append(SemanticChunk(
                    document_id=document_id,
                    page_number=page_num,
                    chunk_index=chunk_idx,
                    content=full_content,
                    section_title=sec_title,
                    metadata={"doc_name": doc_name, "char_count": len(full_content)}
                ))
                chunk_idx += 1
            else:
                # Split large section into coherent logical units
                units = self.split_into_paragraphs_or_sentences(sec_content)
                current_chunk_text = prefixed_header
                
                for unit in units:
                    if len(current_chunk_text) + len(unit) + 2 > self.target_chunk_size and current_chunk_text != prefixed_header:
                        chunks.append(SemanticChunk(
                            document_id=document_id,
                            page_number=page_num,
                            chunk_index=chunk_idx,
                            content=current_chunk_text.strip(),
                            section_title=sec_title,
                            metadata={"doc_name": doc_name, "char_count": len(current_chunk_text)}
                        ))
                        chunk_idx += 1
                        # Re-prefix section header for continuity across chunk boundaries
                        current_chunk_text = f"{prefixed_header}\n(Continued) {unit}".strip()
                    else:
                        current_chunk_text = f"{current_chunk_text}\n{unit}".strip()

                if current_chunk_text and current_chunk_text != prefixed_header:
                    chunks.append(SemanticChunk(
                        document_id=document_id,
                        page_number=page_num,
                        chunk_index=chunk_idx,
                        content=current_chunk_text.strip(),
                        section_title=sec_title,
                        metadata={"doc_name": doc_name, "char_count": len(current_chunk_text)}
                    ))
                    chunk_idx += 1

        return chunks
