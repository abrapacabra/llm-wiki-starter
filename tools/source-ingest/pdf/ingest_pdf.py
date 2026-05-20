#!/usr/bin/env python3
"""Create reusable wiki source artifacts from a local PDF."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml


SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
SOURCE_TIERS = ("primary", "secondary", "reference", "background", "restricted")
OUTPUT_DIRS = ("pages", "tables", "figures", "source-maps")


@dataclass(frozen=True)
class DoclingRuntime:
    DocumentConverter: type
    PdfFormatOption: type
    PdfPipelineOptions: type
    InputFormat: type
    HybridChunker: type
    PictureItem: type
    TableItem: type


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decompose a PDF into wiki navigation and search artifacts."
    )
    parser.add_argument("--pdf", required=True, help="Path to the local PDF.")
    parser.add_argument("--source-id", required=True, help="Stable source id, using lowercase words and dashes.")
    parser.add_argument("--source-tier", required=True, choices=SOURCE_TIERS, help="Generic source tier.")
    parser.add_argument("--title", required=True, help="Human-readable source title.")
    parser.add_argument("--output-root", default="raw/derived", help="Folder where derived source folders are written.")
    parser.add_argument("--page-range", default="", help="Optional 1-based ranges such as 1-5,9,12-14.")
    parser.add_argument(
        "--parser-profile",
        default="docling",
        choices=("docling", "pymupdf"),
        help="PDF parser profile. 'pymupdf' is accepted as a deprecated compatibility alias.",
    )
    parser.add_argument("--max-chars", type=int, default=1800, help="Target maximum characters per chunk.")
    parser.add_argument("--large-source", action="store_true", help="Record that this source is large.")
    parser.add_argument(
        "--extract-figures",
        dest="extract_figures",
        action="store_true",
        help="Compatibility flag; figure extraction is enabled by default.",
    )
    parser.add_argument(
        "--no-extract-figures",
        dest="extract_figures",
        action="store_false",
        help="Disable Docling picture and table image export.",
    )
    parser.add_argument(
        "--render-pages",
        dest="render_pages",
        action="store_true",
        help="Compatibility flag; page rendering is enabled by default.",
    )
    parser.add_argument(
        "--no-render-pages",
        dest="render_pages",
        action="store_false",
        help="Disable rendered page preview PNG files.",
    )
    parser.add_argument("--no-ocr", dest="do_ocr", action="store_false", help="Disable Docling OCR.")
    parser.add_argument("--image-scale", type=float, default=2.0, help="Scale for rendered page and figure images.")
    parser.add_argument(
        "--document-timeout",
        type=float,
        default=120.0,
        help="Docling document timeout in seconds.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing derived source folder.")
    parser.add_argument("--vault-id", default="", help="Stable external vault id, if one exists.")
    parser.add_argument("--vault-provider", default="local", help="Vault or storage provider label.")
    parser.add_argument("--original-repo-pointer", default="", help="Repository-relative pointer to a source note or vault README.")
    parser.add_argument("--no-local-path-hint", action="store_true", help="Omit the machine-specific local path hint.")
    parser.set_defaults(extract_figures=True, render_pages=True, do_ocr=True)
    return parser.parse_args(argv)


def require_source_id(source_id: str) -> None:
    if not SOURCE_ID_RE.match(source_id):
        raise SystemExit("source-id must use lowercase letters, digits, and dashes.")


def import_docling() -> DoclingRuntime:
    try:
        from docling.chunking import HybridChunker  # type: ignore
        from docling.datamodel.base_models import InputFormat  # type: ignore
        from docling.datamodel.pipeline_options import PdfPipelineOptions  # type: ignore
        from docling.document_converter import DocumentConverter, PdfFormatOption  # type: ignore
        from docling_core.types.doc import PictureItem, TableItem  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Docling is required for PDF ingest. Run with "
            "`uv run --group pdf python tools/source-ingest/pdf/ingest_pdf.py ...`."
        ) from exc
    return DoclingRuntime(
        DocumentConverter=DocumentConverter,
        PdfFormatOption=PdfFormatOption,
        PdfPipelineOptions=PdfPipelineOptions,
        InputFormat=InputFormat,
        HybridChunker=HybridChunker,
        PictureItem=PictureItem,
        TableItem=TableItem,
    )


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_page_count(path: Path) -> int:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise SystemExit("pypdf is required for PDF page counting. Run with `uv run --group pdf ...`.") from exc
    return len(PdfReader(str(path)).pages)


def parse_page_range_spec(page_range: str) -> list[int] | None:
    if not page_range:
        return None
    pages: set[int] = set()
    for part in page_range.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            try:
                start = int(start_text)
                end = int(end_text)
            except ValueError as exc:
                raise SystemExit(f"page-range contains invalid range: {part!r}") from exc
            if start > end:
                start, end = end, start
            pages.update(range(start, end + 1))
        else:
            try:
                pages.add(int(part))
            except ValueError as exc:
                raise SystemExit(f"page-range contains invalid page: {part!r}") from exc
    return sorted(pages)


def selected_pages(total_pages: int, page_range: str) -> list[int]:
    pages = parse_page_range_spec(page_range)
    if pages is None:
        return list(range(1, total_pages + 1))
    invalid = [page for page in pages if page < 1 or page > total_pages]
    if invalid:
        raise SystemExit(f"page-range contains invalid page(s): {invalid}")
    return pages


def conversion_page_range(page_numbers: list[int]) -> tuple[int, int]:
    return min(page_numbers), max(page_numbers)


def ensure_output(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise SystemExit(f"Output folder already exists: {path}. Use --overwrite to replace it.")
    if path.exists():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
    path.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_DIRS:
        (path / name).mkdir(parents=True, exist_ok=True)


def build_converter(args: argparse.Namespace, runtime: DoclingRuntime):
    pipeline_options = runtime.PdfPipelineOptions()
    pipeline_options.do_ocr = bool(args.do_ocr)
    pipeline_options.do_table_structure = True
    pipeline_options.generate_page_images = bool(args.render_pages)
    pipeline_options.generate_picture_images = bool(args.extract_figures)
    pipeline_options.images_scale = float(args.image_scale)
    pipeline_options.document_timeout = float(args.document_timeout)
    return runtime.DocumentConverter(
        format_options={
            runtime.InputFormat.PDF: runtime.PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def convert_pdf(pdf_path: Path, args: argparse.Namespace, page_numbers: list[int], runtime: DoclingRuntime):
    converter = build_converter(args, runtime)
    return converter.convert(
        pdf_path,
        raises_on_error=False,
        page_range=conversion_page_range(page_numbers),
    )


def filtered_document(document: Any, page_numbers: list[int]) -> Any:
    filter_method = getattr(document, "filter", None)
    if callable(filter_method):
        return filter_method(page_nrs=set(page_numbers))
    return document


def markdown_for_page(document: Any, page_number: int) -> str:
    try:
        return str(document.export_to_markdown(page_no=page_number)).strip()
    except TypeError:
        page_doc = filtered_document(document, [page_number])
        return str(page_doc.export_to_markdown()).strip()


def dict_for_page(document: Any, page_number: int) -> dict[str, Any]:
    page_doc = filtered_document(document, [page_number])
    return ensure_dict(page_doc.export_to_dict())


def ensure_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {"value": jsonable(value)}


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(child) for child in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return model_dump(mode="json")
        except TypeError:
            return model_dump()
    return str(value)


def yaml_text(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def frontmatter_text(data: dict[str, Any]) -> str:
    return "---\n" + yaml_text(data) + "---\n\n"


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(jsonable(row), ensure_ascii=True) + "\n")


def write_page_files(
    output_dir: Path,
    document: Any,
    page_numbers: list[int],
    source_id: str,
    source_tier: str,
    title: str,
) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for page_number in page_numbers:
        stem = f"page-{page_number:04d}"
        text = markdown_for_page(document, page_number)
        page_dict = dict_for_page(document, page_number)
        image_count = count_page_images(page_dict)
        md_path = output_dir / "pages" / f"{stem}.md"
        json_path = output_dir / "pages" / f"{stem}.json"
        md_path.write_text(
            frontmatter_text(
                {
                    "artifact_type": "source-map",
                    "status": "needs-review",
                    "source_id": source_id,
                    "source_tier": source_tier,
                    "title": title,
                    "pdf_page": page_number,
                    "updated": date.today().isoformat(),
                }
            )
            + f"# Page {page_number}\n\n"
            + text
            + "\n",
            encoding="utf-8",
        )
        json_path.write_text(
            json.dumps(
                {
                    "source_id": source_id,
                    "page_number": page_number,
                    "char_count": len(text),
                    "image_count": image_count,
                    "text": text,
                    "docling": page_dict,
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        pages.append(
            {
                "page_number": page_number,
                "text": text,
                "image_count": image_count,
            }
        )
    return pages


def count_page_images(page_dict: dict[str, Any]) -> int:
    count = 0
    stack: list[Any] = [page_dict]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            label = str(value.get("label", "")).lower()
            if "picture" in label or "image" in label:
                count += 1
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    return count


def page_image_for(document: Any, page_number: int) -> Any:
    pages = getattr(document, "pages", {})
    page = None
    if isinstance(pages, dict):
        page = pages.get(page_number) or pages.get(str(page_number))
    elif isinstance(pages, list):
        for candidate in pages:
            if int(getattr(candidate, "page_no", -1)) == page_number:
                page = candidate
                break
    image = getattr(page, "image", None)
    return getattr(image, "pil_image", None)


def write_page_previews(output_dir: Path, document: Any, page_numbers: list[int]) -> int:
    preview_dir = output_dir / "pages" / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for page_number in page_numbers:
        image = page_image_for(document, page_number)
        if image is None:
            continue
        image.save(preview_dir / f"page-{page_number:04d}.png", format="PNG")
        written += 1
    return written


def item_page_number(item: Any) -> int | None:
    prov = getattr(item, "prov", None)
    if isinstance(prov, list) and prov:
        page_no = getattr(prov[0], "page_no", None)
        if page_no is not None:
            return int(page_no)
        if isinstance(prov[0], dict) and prov[0].get("page_no") is not None:
            return int(prov[0]["page_no"])
    page_no = getattr(item, "page_no", None)
    return int(page_no) if page_no is not None else None


def item_text(item: Any) -> str:
    for name in ("text", "caption", "name"):
        value = getattr(item, name, None)
        if value:
            return str(value).strip()
    return ""


def section_rows(document: Any, page_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    iterate_items = getattr(document, "iterate_items", None)
    if callable(iterate_items):
        for item, _level in iterate_items():
            class_name = item.__class__.__name__.lower()
            label = str(getattr(item, "label", "")).lower()
            if "section" not in class_name and "section" not in label and "heading" not in class_name:
                continue
            title = item_text(item)
            if not title:
                continue
            page_number = item_page_number(item) or 1
            rows.append(
                {
                    "section_id": f"section-{len(rows) + 1:04d}",
                    "level": int(getattr(item, "level", 1) or 1),
                    "title": title,
                    "page_number": page_number,
                    "anchor": f"pdf-page-{page_number}",
                }
            )
    if rows:
        return rows
    markdown = str(document.export_to_markdown())
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not match:
            continue
        rows.append(
            {
                "section_id": f"section-{len(rows) + 1:04d}",
                "level": len(match.group(1)),
                "title": match.group(2).strip(),
                "page_number": 1,
                "anchor": "pdf-page-1",
            }
        )
    if not rows:
        rows.append(
            {
                "section_id": "section-0001",
                "level": 1,
                "title": "Full source",
                "page_number": 1,
                "anchor": f"pdf-page-1-{page_count}",
            }
        )
    return rows


def collect_page_numbers(value: Any) -> set[int]:
    pages: set[int] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"page_no", "page_number", "page"} and isinstance(child, int):
                pages.add(child)
            pages.update(collect_page_numbers(child))
    elif isinstance(value, list):
        for child in value:
            pages.update(collect_page_numbers(child))
    return pages


def split_text(text: str, max_chars: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []
    parts: list[str] = []
    current: list[str] = []
    current_size = 0
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        next_size = current_size + len(paragraph) + (2 if current else 0)
        if current and next_size > max_chars:
            parts.append("\n\n".join(current))
            current = []
            current_size = 0
        current.append(paragraph)
        current_size += len(paragraph) + (2 if current_size else 0)
    if current:
        parts.append("\n\n".join(current))
    return parts


def chunk_rows(document: Any, max_chars: int, fallback_pages: list[int], runtime: DoclingRuntime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        chunker = runtime.HybridChunker()
        raw_chunks = list(chunker.chunk(dl_doc=document))
        for raw_chunk in raw_chunks:
            text = str(chunker.contextualize(raw_chunk)).strip()
            metadata = jsonable(getattr(raw_chunk, "meta", {}))
            pages = collect_page_numbers(metadata) or {fallback_pages[0], fallback_pages[-1]}
            for part in split_text(text, max_chars):
                rows.append(
                    {
                        "chunk_id": f"chunk-{len(rows) + 1:05d}",
                        "page_start": min(pages),
                        "page_end": max(pages),
                        "char_count": len(part),
                        "text": part,
                        "docling_meta": metadata,
                    }
                )
    except Exception as exc:
        text = str(document.export_to_markdown()).strip()
        for part in split_text(text, max_chars):
            rows.append(
                {
                    "chunk_id": f"chunk-{len(rows) + 1:05d}",
                    "page_start": fallback_pages[0],
                    "page_end": fallback_pages[-1],
                    "char_count": len(part),
                    "text": part,
                    "chunker_warning": f"Docling HybridChunker fallback: {exc}",
                }
            )
    return rows


def save_item_image(item: Any, document: Any, path: Path) -> bool:
    get_image = getattr(item, "get_image", None)
    if not callable(get_image):
        return False
    image = get_image(document)
    if image is None:
        return False
    image.save(path, "PNG")
    return True


def figure_rows(output_dir: Path, document: Any, runtime: DoclingRuntime, extract_images: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    iterate_items = getattr(document, "iterate_items", None)
    if not callable(iterate_items):
        return rows
    for item, _level in iterate_items(traverse_pictures=True):
        if not isinstance(item, runtime.PictureItem):
            continue
        page_number = item_page_number(item)
        figure_id = f"figure-{len(rows) + 1:04d}"
        row: dict[str, Any] = {
            "figure_id": figure_id,
            "page_number": page_number,
            "label": str(getattr(item, "label", "")),
            "caption": item_text(item),
            "extracted": False,
        }
        if extract_images:
            filename = f"{figure_id}.png"
            if save_item_image(item, document, output_dir / "figures" / filename):
                row["extracted"] = True
                row["path"] = f"figures/{filename}"
        rows.append(row)
    return rows


def table_rows(output_dir: Path, document: Any, runtime: DoclingRuntime, extract_images: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for table_index, table in enumerate(getattr(document, "tables", []), start=1):
        table_id = f"table-{table_index:04d}"
        csv_path = output_dir / "tables" / f"{table_id}.csv"
        html_path = output_dir / "tables" / f"{table_id}.html"
        row: dict[str, Any] = {
            "table_id": table_id,
            "page_number": item_page_number(table),
            "csv_path": f"tables/{csv_path.name}",
            "html_path": f"tables/{html_path.name}",
            "image_path": "",
        }
        dataframe = table.export_to_dataframe(doc=document)
        dataframe.to_csv(csv_path, index=False)
        html_path.write_text(table.export_to_html(doc=document), encoding="utf-8")
        if extract_images:
            image_path = output_dir / "tables" / f"{table_id}.png"
            if save_item_image(table, document, image_path):
                row["image_path"] = f"tables/{image_path.name}"
        rows.append(row)
    return rows


def write_manifest(
    output_dir: Path,
    args: argparse.Namespace,
    pdf_path: Path,
    page_count: int,
    selected_count: int,
    source_hash: str,
    conversion_result: Any,
) -> None:
    stat = pdf_path.stat()
    metadata = {
        "source_id": args.source_id,
        "title": args.title,
        "source_tier": args.source_tier,
        "status": "needs-review",
        "parser_profile": "docling",
        "requested_parser_profile": args.parser_profile,
        "docling_version": package_version("docling"),
        "large_source": bool(args.large_source),
        "created": date.today().isoformat(),
        "pdf": {
            "page_count": page_count,
            "selected_page_count": selected_count,
            "size_bytes": stat.st_size,
            "sha256": source_hash,
        },
        "conversion": {
            "status": str(getattr(conversion_result, "status", "")),
            "errors": jsonable(getattr(conversion_result, "errors", [])),
            "settings": {
                "ocr": bool(args.do_ocr),
                "table_structure": True,
                "render_pages": bool(args.render_pages),
                "extract_figures": bool(args.extract_figures),
                "image_scale": float(args.image_scale),
                "document_timeout": float(args.document_timeout),
            },
        },
        "source_location": {
            "vault_id": args.vault_id,
            "vault_provider": args.vault_provider,
            "original_repo_pointer": args.original_repo_pointer,
            "local_path_hint": "" if args.no_local_path_hint else str(pdf_path),
        },
        "outputs": [
            "manifest.yaml",
            "quality-report.md",
            "source-summary.md",
            "source-maps/outline.md",
            "sections.jsonl",
            "chunks.jsonl",
            "pages/",
            "tables/",
            "figures/",
        ],
    }
    (output_dir / "manifest.yaml").write_text(yaml_text(metadata), encoding="utf-8")


def write_quality_report(
    output_dir: Path,
    pages: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    figures: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    preview_count: int,
    conversion_result: Any,
) -> None:
    empty_pages = [page["page_number"] for page in pages if not str(page["text"]).strip()]
    status = "needs-review" if empty_pages or str(getattr(conversion_result, "status", "")).lower().endswith("failure") else "verified"
    lines = [
        "# Quality Report",
        "",
        f"- Pages processed: {len(pages)}",
        f"- Empty text pages: {len(empty_pages)}",
        f"- Chunks written: {len(chunks)}",
        f"- Figure metadata rows: {len(figures)}",
        f"- Table metadata rows: {len(tables)}",
        f"- Page previews written: {preview_count}",
        f"- Conversion status: {getattr(conversion_result, 'status', '')}",
        f"- Status: {status}",
        "",
        "## Empty Pages",
        "",
    ]
    if empty_pages:
        lines.extend(f"- {page_number}" for page_number in empty_pages)
    else:
        lines.append("- None")
    lines.append("")
    (output_dir / "quality-report.md").write_text("\n".join(lines), encoding="utf-8")


def write_source_summary(output_dir: Path, args: argparse.Namespace, page_count: int, selected_count: int) -> None:
    body = [
        f"# {args.title}",
        "",
        "## Scope",
        "",
        "This source has been decomposed with Docling for navigation and search.",
        "",
        "## Counts",
        "",
        f"- Total PDF pages: {page_count}",
        f"- Processed pages: {selected_count}",
        "",
        "## Review Notes",
        "",
        "- Derived text is `needs-review` until checked in a scoped workstream.",
        "- Source maps are navigation artifacts and do not create durable claims by themselves.",
        "",
    ]
    (output_dir / "source-summary.md").write_text(
        frontmatter_text(
            {
                "artifact_type": "source-summary",
                "status": "needs-review",
                "source_id": args.source_id,
                "source_tier": args.source_tier,
                "title": args.title,
                "updated": date.today().isoformat(),
            }
        )
        + "\n".join(body),
        encoding="utf-8",
    )


def write_outline(output_dir: Path, args: argparse.Namespace, sections: list[dict[str, Any]], page_count: int) -> None:
    lines = [
        f"# {args.title} Outline",
        "",
        "| Section | PDF Page | Anchor |",
        "| --- | ---: | --- |",
    ]
    if sections:
        for section in sections:
            title = str(section["title"]).replace("|", "\\|")
            lines.append(f"| {title} | {section['page_number']} | `{section['anchor']}` |")
    else:
        lines.append(f"| Full source | 1-{page_count} | `pdf-page-1` |")
    lines.append("")
    (output_dir / "source-maps" / "outline.md").write_text(
        frontmatter_text(
            {
                "artifact_type": "source-map",
                "status": "needs-review",
                "source_id": args.source_id,
                "source_tier": args.source_tier,
                "title": args.title,
                "updated": date.today().isoformat(),
            }
        )
        + "\n".join(lines),
        encoding="utf-8",
    )


def ingest_pdf(
    args: argparse.Namespace,
    *,
    runtime: DoclingRuntime | None = None,
    page_count_reader=pdf_page_count,
) -> Path:
    require_source_id(args.source_id)
    if args.parser_profile == "pymupdf":
        print("WARNING: parser profile 'pymupdf' is deprecated; using Docling.", file=sys.stderr)
    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if not pdf_path.is_file():
        raise SystemExit(f"PDF path is not a file: {pdf_path}")

    page_count = page_count_reader(pdf_path)
    page_numbers = selected_pages(page_count, args.page_range)
    runtime = runtime or import_docling()
    output_root = Path(args.output_root).resolve()
    output_dir = output_root / args.source_id
    ensure_output(output_dir, args.overwrite)

    conversion_result = convert_pdf(pdf_path, args, page_numbers, runtime)
    document = filtered_document(conversion_result.document, page_numbers)

    chunks = chunk_rows(document, max(200, args.max_chars), page_numbers, runtime)
    sections = section_rows(document, page_count)
    figures = figure_rows(output_dir, document, runtime, bool(args.extract_figures))
    tables = table_rows(output_dir, document, runtime, bool(args.extract_figures))
    preview_count = write_page_previews(output_dir, document, page_numbers) if args.render_pages else 0
    pages = write_page_files(output_dir, document, page_numbers, args.source_id, args.source_tier, args.title)
    source_hash = sha256_file(pdf_path)

    write_manifest(output_dir, args, pdf_path, page_count, len(page_numbers), source_hash, conversion_result)
    write_jsonl(output_dir / "sections.jsonl", sections)
    write_jsonl(output_dir / "chunks.jsonl", (dict(chunk, source_id=args.source_id) for chunk in chunks))
    write_jsonl(output_dir / "figures" / "figures.jsonl", figures)
    write_jsonl(output_dir / "tables" / "tables.jsonl", tables)
    write_quality_report(output_dir, pages, chunks, figures, tables, preview_count, conversion_result)
    write_source_summary(output_dir, args, page_count, len(page_numbers))
    write_outline(output_dir, args, sections, page_count)
    return output_dir


def main(argv: list[str] | None = None) -> int:
    output_dir = ingest_pdf(parse_args(argv))
    print(f"Wrote derived source artifacts to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
