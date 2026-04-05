import logging
import os
import shutil
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption
from docling_core.types.doc.document import ImageRefMode

logger = logging.getLogger(__name__)


def _normalize_docling_asset_paths(out_dir: Path, source_name: str) -> None:
    nested_root = out_dir / "uploads" / "_docling_assets" / source_name
    if not nested_root.exists():
        return

    for child in nested_root.iterdir():
        destination = out_dir / child.name
        if destination.exists():
            if destination.is_dir() and child.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        shutil.move(str(child), str(destination))

    shutil.rmtree(out_dir / "uploads", ignore_errors=True)


def _make_pdf_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions(
        generate_picture_images=True,
        images_scale=2,
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def extract_content(file_path: str, asset_dir=None, asset_prefix=None):
    """
    Extract text from PDF or DOCX using Docling.
    Returns (markdown_text, image_refs) where markdown_text is a single string.
    Images are saved to asset_dir (or a sibling temp dir) and referenced inline.
    """
    ext = Path(file_path).suffix.lower()
    if ext not in (".pdf", ".docx"):
        return "", []

    try:
        if ext == ".pdf":
            converter = _make_pdf_converter()
        else:
            converter = DocumentConverter()
        result = converter.convert(file_path)
        doc = result.document
    except Exception as e:
        logger.error("Docling failed to parse %s: %s", file_path, e)
        return "", []

    if ext == ".pdf":
        # Use a persistent asset dir alongside the output so images survive the request.
        source_name = Path(file_path).stem
        out_dir = Path(asset_dir) if asset_dir else Path(file_path).parent / "_docling_assets" / source_name
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / (source_name + ".md")
        try:
            doc.save_as_markdown(
                md_path,
                image_mode=ImageRefMode.REFERENCED,
                include_annotations=True,
            )
            _normalize_docling_asset_paths(out_dir, source_name)
            return md_path.read_text(encoding="utf-8"), []
        except Exception as e:
            logger.warning("save_as_markdown failed (%s), falling back to export_to_markdown", e)
            return doc.export_to_markdown(), []

    else:  # .docx
        return doc.export_to_markdown(), []


def extract_pdf_layout_html(file_path, asset_dir, asset_prefix, extracted_text=None, extracted_pages=None):
    """
    Layout HTML for the /upload-layout/ endpoint.
    Docling doesn't produce coordinate-based HTML, so we fall back to the
    markdown-in-a-styled-page approach.
    """
    from converter import to_html_page
    content = extracted_text or ""
    if not content and extracted_pages:
        content = "\n\n".join(extracted_pages)
    return to_html_page(content)