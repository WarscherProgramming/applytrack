import io
import logging
import re
import zipfile
from pathlib import PurePosixPath

from app.exceptions.http import ValidationError

logger = logging.getLogger(__name__)

# Hard cap on extracted characters fed into a prompt. Keeps token usage (and
# cost) bounded regardless of how large an uploaded document is; the tail of a
# resume is rarely decisive for a match analysis.
MAX_RESUME_CHARS = 20_000

_XML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"[ \t]*\n[ \t]*")


class ResumeTextExtractionError(ValidationError):
    """Raised (422) when readable text cannot be extracted from a document."""


def _normalise(text: str) -> str:
    """Collapse noisy whitespace and trim to the character cap."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE.sub("\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if len(text) > MAX_RESUME_CHARS:
        text = text[:MAX_RESUME_CHARS].rstrip() + "\n…[truncated]"
    return text


def _from_plain(content: bytes) -> str:
    # errors="replace" keeps extraction resilient to odd encodings.
    return content.decode("utf-8", errors="replace")


def _from_rtf(content: bytes) -> str:
    # Minimal RTF handling: drop control words and group braces. Good enough to
    # recover the visible text without pulling in an RTF parser dependency.
    raw = content.decode("latin-1", errors="replace")
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", "", raw)  # escaped hex chars
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)  # control words
    raw = raw.replace("{", " ").replace("}", " ")
    return raw


def _from_zip_xml(content: bytes, *, inner_path: str) -> str:
    """Extract visible text from an OOXML/ODF document (docx, odt).

    Both formats are ZIP archives whose main part is XML. Rather than depend on
    python-docx/odfpy, we read the relevant XML part and strip tags — adequate
    for feeding plain text to the model. Paragraph/run boundaries become spaces.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            xml = archive.read(inner_path).decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ResumeTextExtractionError(
            "The document appears to be corrupt or not in the expected format"
        ) from exc
    # Close tags that imply a break become spaces so words don't run together.
    xml = re.sub(r"</(w:p|text:p|text:line-break)>", " ", xml)
    return _XML_TAG.sub("", xml)


def _from_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ResumeTextExtractionError(
            "PDF text extraction is unavailable on this server"
        ) from exc
    try:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise ResumeTextExtractionError(
            "Could not read text from the PDF (it may be scanned or image-only)"
        ) from exc


def extract_text(file_name: str, content: bytes) -> str:
    """
    Extract plain text from an uploaded resume.

    Dispatches on file extension. Raises ResumeTextExtractionError (422) for
    unsupported formats or when no readable text is found — callers surface that
    to the user rather than sending an empty prompt to the model.
    """
    if not content:
        raise ResumeTextExtractionError("The resume file is empty")

    ext = PurePosixPath(file_name).suffix.lower()
    if ext in (".txt", ".md"):
        text = _from_plain(content)
    elif ext == ".rtf":
        text = _from_rtf(content)
    elif ext == ".docx":
        text = _from_zip_xml(content, inner_path="word/document.xml")
    elif ext == ".odt":
        text = _from_zip_xml(content, inner_path="content.xml")
    elif ext == ".pdf":
        text = _from_pdf(content)
    else:
        raise ResumeTextExtractionError(
            f"Cannot extract text from '{ext or file_name}'. "
            "Upload a PDF, DOCX, ODT, TXT, RTF, or Markdown resume."
        )

    normalised = _normalise(text)
    if not normalised:
        raise ResumeTextExtractionError(
            "No readable text was found in the resume. If it is a scanned PDF, "
            "upload a text-based version."
        )
    return normalised
