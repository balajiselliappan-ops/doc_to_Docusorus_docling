from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil, os
from parser import extract_content, extract_pdf_layout_html
from cleaner import clean_content, clean_content_pages
from converter import to_docusaurus_markdown, to_html_page

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


def _slugify_name(value):
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-") or "document"


@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    file_path = f"{UPLOAD_DIR}/{file.filename}"
    file_stem = os.path.splitext(file.filename)[0]

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    raw, _ = extract_content(file_path)
    cleaned = clean_content(raw)
    markdown, engine = to_docusaurus_markdown(cleaned, file_path)
    html_page = to_html_page(markdown, output_dir=".")

    output_name = f"{file_stem}.md"
    output_file = f"{OUTPUT_DIR}/{output_name}"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    html_name = f"{file_stem}.html"
    html_output_file = f"{OUTPUT_DIR}/{html_name}"
    with open(html_output_file, "w", encoding="utf-8") as f:
        f.write(html_page)

    return {
        "mdx": markdown,
        "markdown": markdown,
        "html": html_page,
        "engine": engine,
        "output_file": output_name,
        "html_output_file": html_name,
    }


@app.post("/upload-layout/")
async def upload_layout(file: UploadFile = File(...)):
    file_path = f"{UPLOAD_DIR}/{file.filename}"
    file_stem = os.path.splitext(file.filename)[0]

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Layout-preserved HTML is currently supported for PDF only")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    raw, _ = extract_content(file_path)
    extracted_text = clean_content(raw)
    extracted_pages = clean_content_pages(raw)

    doc_slug = _slugify_name(file_stem)
    layout_asset_dir = os.path.join(OUTPUT_DIR, "layout-assets", doc_slug)
    layout_asset_prefix = f"./layout-assets/{doc_slug}"
    layout_html = extract_pdf_layout_html(
        file_path,
        layout_asset_dir,
        layout_asset_prefix,
        extracted_text=extracted_text,
        extracted_pages=extracted_pages,
    )

    html_name = f"{file_stem}.layout.html"
    html_output_file = f"{OUTPUT_DIR}/{html_name}"
    with open(html_output_file, "w", encoding="utf-8") as f:
        f.write(layout_html)

    return {
        "html": layout_html,
        "engine": "layout-preserved-pdf",
        "extracted_text": extracted_text,
        "extracted_pages": extracted_pages,
        "html_output_file": html_name,
    }