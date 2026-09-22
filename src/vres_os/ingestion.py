from __future__ import annotations

import csv
import hashlib
import json
import io
import stat
from pathlib import PurePosixPath
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_CONTAINER_BYTES = 100 * 1024 * 1024
MAX_OOXML_UNCOMPRESSED = 64 * 1024 * 1024
MAX_OOXML_ENTRIES = 20_000
MAX_OOXML_RATIO = 250
MAX_EXTRACTED_CHARS = 8_000_000


class IngestionInputError(RuntimeError):
    """Expected bad/unsafe input. Onboarding may route this file to human review."""


class UnsafeContainer(IngestionInputError):
    pass


class ParserInputError(IngestionInputError):
    pass


class InputTooLarge(IngestionInputError):
    pass


@dataclass(slots=True)
class ExtractedDocument:
    title: str
    text: str
    metadata: dict[str, Any]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _bounded_plain(path: Path) -> ExtractedDocument:
    size = path.stat().st_size
    if size <= MAX_TEXT_BYTES:
        return ExtractedDocument(path.name, path.read_text(encoding="utf-8", errors="replace"), {"sampled": False})
    half = MAX_TEXT_BYTES // 2
    with path.open("rb") as handle:
        first = handle.read(half)
        handle.seek(max(0, size - half))
        last = handle.read(half)
    marker = f"\n\n[...middle omitted from {size} byte file...]\n\n"
    text = first.decode("utf-8", errors="replace") + marker + last.decode("utf-8", errors="replace")
    return ExtractedDocument(path.name, text, {"sampled": True, "size_bytes": size})


def _json(path: Path) -> ExtractedDocument:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise InputTooLarge(f"JSON exceeds {MAX_JSON_BYTES} bytes; catalogue/review instead of full parse")
    try:
        # utf-8-sig accepts ordinary UTF-8 unchanged while stripping one leading BOM.
        text = path.read_text(encoding="utf-8-sig")
        raw = json.loads(text)
    except (json.JSONDecodeError, UnicodeError, OSError, RecursionError) as exc:
        raise ParserInputError(str(exc)) from exc
    # Preserve the bounded source spelling after BOM-aware decoding instead of exponentially
    # expanding indentation on nested input. The source bytes on disk are never rewritten.
    return ExtractedDocument(path.name, text, {"structured": True})


def _csv(path: Path) -> ExtractedDocument:
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_TEXT_BYTES + 1)
        truncated = len(raw) > MAX_TEXT_BYTES
        raw = raw[:MAX_TEXT_BYTES]
        if truncated:
            raw = raw.rsplit(b"\n", 1)[0]
        text = raw.decode("utf-8-sig", errors="replace")
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        sample = []
        reader = csv.reader(io.StringIO(text), dialect)
        for index, row in enumerate(reader):
            if index >= 200:
                break
            sample.append(row[:200])
    except (csv.Error, OSError, UnicodeError) as exc:
        raise ParserInputError(str(exc)) from exc
    result, clipped = _trim("\n".join("\t".join(row) for row in sample))
    return ExtractedDocument(path.name, result, {"sample_rows": len(sample), "sampled": True,
        "input_truncated": truncated, "text_truncated": clipped, "delimiter": dialect.delimiter,
        "encoding": "utf-8 with replacement; verify non-UTF8 inputs separately"})


def _ooxml_preflight(path: Path) -> dict[str, int]:
    size = path.stat().st_size
    if size > MAX_CONTAINER_BYTES:
        raise InputTooLarge(f"OOXML container exceeds {MAX_CONTAINER_BYTES} bytes")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_OOXML_ENTRIES:
                raise UnsafeContainer(f"OOXML archive has {len(infos)} entries")
            names = set()
            for info in infos:
                name = info.filename.replace("\\", "/")
                pure = PurePosixPath(name)
                if pure.is_absolute() or ".." in pure.parts or ":" in name or name in names:
                    raise UnsafeContainer("OOXML contains duplicate or unsafe member names")
                if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                    raise UnsafeContainer("OOXML contains encrypted or linked members")
                names.add(name)
            total_uncompressed = sum(i.file_size for i in infos)
            total_compressed = max(1, sum(i.compress_size for i in infos))
            ratio = total_uncompressed / total_compressed
            if total_uncompressed > MAX_OOXML_UNCOMPRESSED:
                raise UnsafeContainer(f"OOXML expands to {total_uncompressed} bytes")
            if ratio > MAX_OOXML_RATIO and total_uncompressed > 32 * 1024 * 1024:
                raise UnsafeContainer(f"OOXML suspicious compression ratio {ratio:.1f}:1")
            return {"zip_entries": len(infos), "uncompressed_bytes": total_uncompressed}
    except zipfile.BadZipFile as exc:
        raise ParserInputError("Invalid OOXML ZIP container") from exc


def _trim(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_EXTRACTED_CHARS:
        return text, False
    half = MAX_EXTRACTED_CHARS // 2
    return text[:half] + "\n\n[...extracted text truncated...]\n\n" + text[-half:], True


class _TextParts:
    def __init__(self):
        self.parts: list[str] = []
        self.remaining = MAX_EXTRACTED_CHARS
        self.truncated = False

    def append(self, text: str) -> None:
        if self.remaining <= 0:
            self.truncated = True
            return
        value = str(text)
        self.parts.append(value[:self.remaining])
        self.truncated |= len(value) > self.remaining
        self.remaining -= len(value) + 1

    def __iter__(self):
        return iter(self.parts)


def _xlsx(path: Path) -> ExtractedDocument:
    preflight = _ooxml_preflight(path)
    try:
        from openpyxl import load_workbook
        from openpyxl.utils.exceptions import InvalidFileException
    except ImportError:
        raise
    try:
        wb = load_workbook(path, read_only=True, data_only=True, keep_links=False)
    except (InvalidFileException, zipfile.BadZipFile, OSError, ValueError, KeyError) as exc:
        raise ParserInputError(str(exc)) from exc
    sections = _TextParts()
    sheet_meta = []
    try:
        for sheet_index, ws in enumerate(wb.worksheets):
            if sheet_index >= 100:
                sections.append("[...additional sheets omitted...]")
                break
            sections.append(f"# SHEET {ws.title}")
            count = 0
            for row in ws.iter_rows(min_row=1, max_row=500, min_col=1, max_col=min(ws.max_column or 1, 200), values_only=True):
                sections.append("\t".join("" if v is None else str(v) for v in row[:200]))
                count += 1
                if count >= 500:
                    sections.append("[...sheet sample truncated at 500 rows...]")
                    break
            sheet_meta.append({"name": ws.title, "sample_rows": count})
    finally:
        wb.close()
    text, truncated = _trim("\n".join(sections))
    return ExtractedDocument(path.name, text, {**preflight, "sheets": sheet_meta, "text_truncated": truncated or sections.truncated, "sampled": True, "formula_policy": "cached values only; formulas are not recalculated", "external_links_loaded": False})


def _docx(path: Path) -> ExtractedDocument:
    preflight = _ooxml_preflight(path)
    try:
        from docx import Document
        from docx.opc.exceptions import PackageNotFoundError
    except ImportError:
        raise
    try:
        doc = Document(path)
    except (PackageNotFoundError, zipfile.BadZipFile, OSError, ValueError, KeyError) as exc:
        raise ParserInputError(str(exc)) from exc
    parts = _TextParts()
    for paragraph in doc.paragraphs[:10_000]:
        if paragraph.text:
            parts.append(paragraph.text)
    # Tables often carry the process/rule content missing from paragraphs.
    cells = 0
    for table in doc.tables[:500]:
        for row in table.rows:
            parts.append("\t".join(cell.text for cell in row.cells[:100]))
            cells += len(row.cells)
            if cells >= 20_000:
                parts.append("[...table extraction truncated...]")
                break
        if cells >= 20_000:
            break
    text, truncated = _trim("\n".join(parts))
    return ExtractedDocument(path.name, text, {**preflight, "text_truncated": truncated or parts.truncated})


def _pptx(path: Path) -> ExtractedDocument:
    preflight = _ooxml_preflight(path)
    try:
        from pptx import Presentation
        from pptx.exc import PackageNotFoundError
    except ImportError:
        raise
    try:
        prs = Presentation(path)
    except (PackageNotFoundError, zipfile.BadZipFile, OSError, ValueError, KeyError) as exc:
        raise ParserInputError(str(exc)) from exc
    parts = _TextParts()
    slides = 0
    for i, slide in enumerate(prs.slides, 1):
        if i > 2000:
            parts.append("[...additional slides omitted...]")
            break
        slides += 1
        parts.append(f"# SLIDE {i}")
        for shape in slide.shapes:
            text = getattr(shape, "text", None)
            if text:
                parts.append(str(text))
    text, truncated = _trim("\n".join(parts))
    return ExtractedDocument(path.name, text, {**preflight, "slides": slides, "text_truncated": truncated or parts.truncated, "extraction": "slide text only; diagrams/tables need review"})


def _pdf(path: Path) -> ExtractedDocument:
    if path.stat().st_size > MAX_CONTAINER_BYTES:
        raise InputTooLarge(f"PDF exceeds {MAX_CONTAINER_BYTES} bytes")
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError, PdfStreamError
    try:
        with path.open("rb") as handle:
            doc = PdfReader(handle, strict=True)
            if doc.is_encrypted:
                raise ParserInputError("Encrypted PDF: no document passwords are requested during onboarding")
            parts, chars, pages, text_pages = [], 0, min(len(doc.pages), 500), 0
            for index in range(pages):
                text = doc.pages[index].extract_text() or ""
                if text.strip():
                    text_pages += 1
                part = f"# PAGE {index + 1}\n{text}"
                remaining = max(0, MAX_EXTRACTED_CHARS - chars)
                parts.append(part[:remaining])
                chars += len(part)
                if chars >= MAX_EXTRACTED_CHARS:
                    break
            if not text_pages:
                raise ParserInputError("PDF has no extractable text layer; scanned/image documents require separate review")
            text, clipped = _trim("\n".join(parts))
            return ExtractedDocument(path.name, text, {"pages_sampled": len(parts), "pages_total": len(doc.pages),
                "text_pages": text_pages, "text_truncated": clipped or chars >= MAX_EXTRACTED_CHARS,
                "sampled": len(parts) < len(doc.pages), "extraction": "text only; figures and tables require review"})
    except (PdfReadError, PdfStreamError, ValueError, RecursionError, OSError) as exc:
        raise ParserInputError(str(exc)) from exc


EXTRACTORS = {
    ".txt": _bounded_plain, ".md": _bounded_plain, ".py": _bounded_plain, ".sql": _bounded_plain,
    ".toml": _bounded_plain, ".yaml": _bounded_plain, ".yml": _bounded_plain, ".json": _json,
    ".csv": _csv, ".xlsx": _xlsx, ".xlsm": _xlsx, ".docx": _docx, ".pptx": _pptx, ".pdf": _pdf,
}


def extract(path: Path) -> ExtractedDocument | None:
    fn = EXTRACTORS.get(path.suffix.lower())
    return None if not fn else fn(path)



def extract_isolated(path: Path, timeout: float = 30) -> ExtractedDocument | None:
    """Expensive Office/PDF parsers run outside the persistent parent process."""
    if path.suffix.lower() not in {".pdf", ".xlsx", ".xlsm", ".docx", ".pptx"}:
        return extract(path)
    import sys
    from .processes import run_bounded, worker_command
    result = run_bounded(worker_command("vres_os.parse_worker", str(path.resolve())), timeout=timeout,
                         max_output_bytes=48 * 1024 * 1024, max_result_chars=40 * 1024 * 1024, redact_output=False)
    if result.returncode in {124, 125}:
        raise InputTooLarge("Document parser exceeded its time/output budget; source was not indexed")
    try:
        response = json.loads(result.output.splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise RuntimeError("Parser worker returned an invalid protocol response; ingestion must stop") from exc
    if not isinstance(response, dict):
        raise RuntimeError("Parser worker returned a non-object response")
    if response.get("ok") is not True:
        if response.get("error_kind") == "input":
            raise ParserInputError(response.get("error", "Document extraction rejected"))
        raise RuntimeError("Parser worker internal failure: " + response.get("error", "unknown"))
    if result.returncode != 0:
        raise RuntimeError("Parser reported success but exited unsuccessfully")
    data = response.get("document")
    if data is None:
        return None
    if (not isinstance(data, dict) or not isinstance(data.get("text"), str)
            or not isinstance(data.get("metadata"), dict) or len(data["text"]) > MAX_EXTRACTED_CHARS + 1000):
        raise RuntimeError("Parser document violates its bounded output contract")
    return ExtractedDocument(path.name, data["text"], data["metadata"])

def classify_mechanically(path: Path, extracted: ExtractedDocument | None) -> tuple[str, float]:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix in {".py", ".sql", ".js", ".ts", ".tsx", ".sh", ".ps1"}:
        return "code", 1.0
    text = extracted.text[:5000].lower() if extracted else ""
    signals = {
        "process": ["process", "procedure", "workflow", "runbook", "διαδικασία"],
        "decision": ["decision", "adr", "approved", "decided", "απόφαση"],
        "requirements": ["requirement", "acceptance criteria", "brief", "specification"],
        "analysis": ["analysis", "finding", "insight", "variance", "summary"],
        "code": [".py", ".js", ".ts", ".sql"],
    }
    best = ("unknown", 0.2)
    for kind, needles in signals.items():
        score = 0
        for n in needles:
            # Extension-like needles must match the actual filename suffix, not an
            # arbitrary substring, so ".js" cannot match inside ".json".
            name_hit = suffix == n if n.startswith(".") else n in name
            if name_hit or n in text:
                score += 1
        candidate = min(0.93, 0.45 + score * 0.12)
        if score and candidate > best[1]:
            best = (kind, candidate)
    if best[0] == "unknown" and extracted and extracted.text.strip() and suffix not in {".csv", ".xlsx", ".xlsm"}:
        return "document", 0.5
    return best
