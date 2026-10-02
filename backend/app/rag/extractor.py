import re
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from app.core.logging import logger

class ExtractedSection:
    def __init__(self, title: str, content: str, page_number: int):
        self.title = title
        self.content = content
        self.page_number = page_number

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "page_number": self.page_number
        }

class PDFExtractor:
    """
    Intelligent PDF Extractor that cleans artifacts, detects sections & headers,
    preserves page numbers, and parses tabular/formatted text.
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Normalize carriage returns and tabs
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
        # Remove repeated non-alphanumeric artifacts like underscores/dashes/dots
        text = re.sub(r'([_\-\.=~])\1{3,}', ' ', text)
        # Fix multiple spaces
        text = re.sub(r'[ \t]{2,}', ' ', text)
        # Fix excessive newlines (max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def is_likely_heading(line: str) -> bool:
        line = line.strip()
        if not line or len(line) > 80:
            return False
        # Heading patterns:
        # 1. Section numbering like "1. Product Overview", "1.1 Specifications", "SECTION A:"
        if re.match(r'^(?:[0-9]+(?:\.[0-9]+)*|section\s+[a-z0-9]+|part\s+[a-z0-9]+)[:\s\.\-]', line, re.IGNORECASE):
            return True
        # 2. ALL CAPS headings (at least 3 characters)
        if line.isupper() and len(line) >= 4 and any(c.isalpha() for c in line):
            return True
        # 3. Lines ending with a colon (e.g., "Troubleshooting Guide:", "Warranty Policy:")
        if line.endswith(":") and len(line.split()) <= 7:
            return True
        # 4. Title Case short line without sentence-ending punctuation (.!?)
        words = line.split()
        if 1 <= len(words) <= 6 and not any(line.endswith(punct) for punct in ['.', '!', '?']):
            title_case_ratio = sum(1 for w in words if w and w[0].isupper()) / len(words)
            if title_case_ratio >= 0.7:
                return True
        return False

    @classmethod
    def extract_document(cls, pdf_path: str) -> Dict[str, Any]:
        """
        Extracts structured text from a PDF file preserving page numbers and detecting sections.
        """
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            pages_data: List[Dict[str, Any]] = []
            all_sections: List[ExtractedSection] = []

            current_section_title = "General Overview"

            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                raw_text = page.extract_text() or ""
                cleaned_text = cls.clean_text(raw_text)

                lines = cleaned_text.split("\n")
                current_section_lines: List[str] = []

                for line in lines:
                    line_stripped = line.strip()
                    if cls.is_likely_heading(line_stripped):
                        # Flush previous section if accumulated content
                        if current_section_lines:
                            section_content = "\n".join(current_section_lines).strip()
                            if section_content:
                                all_sections.append(ExtractedSection(
                                    title=current_section_title,
                                    content=section_content,
                                    page_number=page_num
                                ))
                            current_section_lines = []
                        current_section_title = line_stripped
                    else:
                        if line_stripped:
                            current_section_lines.append(line_stripped)

                # Flush remainder of page
                if current_section_lines:
                    section_content = "\n".join(current_section_lines).strip()
                    if section_content:
                        all_sections.append(ExtractedSection(
                            title=current_section_title,
                            content=section_content,
                            page_number=page_num
                        ))

                pages_data.append({
                    "page_number": page_num,
                    "text": cleaned_text,
                    "char_count": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                })

            logger.info(f"Extracted {total_pages} pages and {len(all_sections)} sections from {pdf_path}")
            return {
                "total_pages": total_pages,
                "pages": pages_data,
                "sections": [s.to_dict() for s in all_sections],
            }
        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {e}")
            raise e
