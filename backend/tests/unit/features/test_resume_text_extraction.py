import io
import zipfile

import pytest

from app.features.resume_match.text_extraction import (
    MAX_RESUME_CHARS,
    ResumeTextExtractionError,
    extract_text,
)


def _zip_bytes(inner_path: str, xml: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(inner_path, xml)
    return buffer.getvalue()


class TestPlainFormats:
    def test_extracts_txt(self) -> None:
        assert extract_text("resume.txt", b"Hello world") == "Hello world"

    def test_extracts_markdown(self) -> None:
        out = extract_text("resume.md", b"# Title\n\nSome body text")
        assert "Title" in out
        assert "Some body text" in out

    def test_decodes_non_utf8_gracefully(self) -> None:
        # Invalid byte should be replaced, not raise.
        out = extract_text("resume.txt", b"Caf\xe9")
        assert "Caf" in out


class TestRtf:
    def test_strips_control_words(self) -> None:
        rtf = rb"{\rtf1\ansi\deff0 {\fonttbl} Hello \b World\b0 }"
        out = extract_text("resume.rtf", rtf)
        assert "Hello" in out
        assert "World" in out
        assert "rtf1" not in out


class TestOoxmlAndOdf:
    def test_extracts_docx(self) -> None:
        xml = (
            "<w:document><w:body>"
            "<w:p><w:r><w:t>Python</w:t></w:r></w:p>"
            "<w:p><w:r><w:t>FastAPI</w:t></w:r></w:p>"
            "</w:body></w:document>"
        )
        out = extract_text("resume.docx", _zip_bytes("word/document.xml", xml))
        assert "Python" in out
        assert "FastAPI" in out
        assert "<w:t>" not in out

    def test_extracts_odt(self) -> None:
        xml = "<office><text:p>Senior Engineer</text:p></office>"
        out = extract_text("resume.odt", _zip_bytes("content.xml", xml))
        assert "Senior Engineer" in out

    def test_corrupt_docx_raises(self) -> None:
        with pytest.raises(ResumeTextExtractionError):
            extract_text("resume.docx", b"not a zip file")


class TestErrors:
    def test_empty_file_raises(self) -> None:
        with pytest.raises(ResumeTextExtractionError):
            extract_text("resume.txt", b"")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ResumeTextExtractionError):
            extract_text("resume.txt", b"   \n\t  ")

    def test_unsupported_extension_raises(self) -> None:
        with pytest.raises(ResumeTextExtractionError, match="Cannot extract"):
            extract_text("resume.doc", b"\xd0\xcf legacy binary")


class TestTruncation:
    def test_truncates_to_cap(self) -> None:
        big = ("word " * (MAX_RESUME_CHARS)).encode()
        out = extract_text("resume.txt", big)
        assert len(out) <= MAX_RESUME_CHARS + len("\n…[truncated]")
        assert out.endswith("[truncated]")
