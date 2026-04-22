import base64
import mimetypes
import os
import re
import subprocess
import time
import logging
from pathlib import Path

from openai import OpenAI
from markdown import markdown as render_markdown


logger = logging.getLogger(__name__)
MAX_AI_INPUT_CHARS = 9000
CHUNK_SIZE = 7000
MAX_CHUNKS = 30
OPENAI_TIMEOUT_SECONDS = 45.0
DEFAULT_GROQ_MODEL = "qwen/qwen3-32b"
FALLBACK_GROQ_MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile"]
HIGHLIGHT_KEYWORDS = [kw.strip() for kw in os.getenv("HIGHLIGHT_KEYWORDS", "").split(",") if kw.strip()]


def _build_ai_client() -> tuple[OpenAI, str, str]:
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        client = OpenAI(api_key=groq_key, base_url=base_url, timeout=OPENAI_TIMEOUT_SECONDS)
        return client, model, "groq-qwen"

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        client = OpenAI(api_key=openai_key, timeout=OPENAI_TIMEOUT_SECONDS)
        return client, model, "openai"

    raise RuntimeError("Set GROQ_API_KEY (recommended for Qwen) or OPENAI_API_KEY")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug or "document"


def _escape_title(value: str) -> str:
    return value.replace('"', "\\\"")


def _frontmatter(title: str, slug: str) -> str:
    return (
        "---\n"
        f'title: "{_escape_title(title)}"\n'
        f"slug: /{slug}\n"
        "---\n\n"
    )


def _prepend_frontmatter_if_missing(markdown: str, title: str, slug: str) -> str:
    stripped = markdown.lstrip()
    if stripped.startswith("---\n"):
        return markdown
    return _frontmatter(title, slug) + markdown.strip() + "\n"


def _sanitize_model_markdown(markdown: str) -> str:
    # Drop reasoning traces that some models emit.
    cleaned = re.sub(r"<think>.*?</think>", "", markdown, flags=re.IGNORECASE | re.DOTALL)

    # Drop any markdown code fences around the whole response.
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", cleaned.strip())
    cleaned = re.sub(r"\n```$", "", cleaned.strip())

    # Remove any frontmatter blocks; we add one consistent block later.
    cleaned = re.sub(r"(?ms)^---\n.*?\n---\n?", "", cleaned).strip()
    return cleaned


def _is_token_limit_error(error: Exception) -> bool:
    message = str(error).lower()
    token_signals = [
        "rate_limit_exceeded",
        "request too large",
        "tokens per minute",
        "requested",
        "413",
    ]
    return any(signal in message for signal in token_signals)


def _is_markdown_table_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("|") and stripped.count("|") >= 2:
        return True
    if re.match(r"^\|?\s*:?[-]{3,}:?\s*(\|\s*:?[-]{3,}:?\s*)+\|?$", stripped):
        return True
    return False


def _chunk_text(text: str) -> list[str]:
    """Split text into chunks without cutting markdown/html tables in half."""
    lines = text.strip().splitlines()
    if not lines:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    in_html_table = False
    in_markdown_table = False

    for idx, line in enumerate(lines):
        lower = line.lower()
        if "<table" in lower:
            in_html_table = True

        is_md_table_line = _is_markdown_table_line(line)
        line_len = len(line) + 1
        would_overflow = bool(current and (current_len + line_len > CHUNK_SIZE))

        # Do not split while inside table context.
        if would_overflow and not (in_html_table or in_markdown_table or is_md_table_line):
            if len(chunks) >= MAX_CHUNKS - 1:
                remaining = current + lines[idx:]
                chunks.append("\n".join(remaining).strip())
                return [chunk for chunk in chunks if chunk][:MAX_CHUNKS]
            chunks.append("\n".join(current).strip())
            current = []
            current_len = 0

        current.append(line)
        current_len += line_len

        if is_md_table_line:
            in_markdown_table = True
        elif in_markdown_table and not line.strip():
            in_markdown_table = False
        elif in_markdown_table and line.strip() and not is_md_table_line:
            in_markdown_table = False

        if "</table>" in lower:
            in_html_table = False

    if current:
        chunks.append("\n".join(current).strip())

    return [chunk for chunk in chunks if chunk][:MAX_CHUNKS]


def _convert_with_ai(text: str, title: str, slug: str, is_continuation: bool = False) -> tuple[str, str]:
    client, model, provider = _build_ai_client()

    candidate_models = [model]
    if provider == "groq-qwen":
        for fallback_model in FALLBACK_GROQ_MODELS:
            if fallback_model not in candidate_models:
                candidate_models.append(fallback_model)

    candidate_sizes = [MAX_AI_INPUT_CHARS, 7000, 5000, 3500]
    candidate_sizes = [size for size in candidate_sizes if size > 0]
    candidate_sizes = list(dict.fromkeys(candidate_sizes))

    started_at = time.perf_counter()
    last_error: Exception | None = None
    response = None
    used_model = model
    for candidate_size in candidate_sizes:
        if is_continuation:
            prompt = (
                "Convert the following document section to clean Markdown.\n"
                "Requirements:\n"
                "- Keep heading structure coherent.\n"
                "- Remove repeated headers/footers and OCR noise.\n"
                "- Use valid Markdown only; no code fences around whole output.\n"
                "- Preserve all detected tables.\n"
                "- For simple tables, use markdown pipe tables.\n"
                "- For merged cells (rowspan/colspan) or multi-line cells, output raw HTML <table>...</table> with proper rowspan/colspan.\n"
                "- Never flatten tables into prose.\n"
                "- Never split a table; output complete table blocks only.\n"
                "- If input already contains HTML <table> blocks, keep them as-is.\n"
                "- Do NOT include frontmatter (no --- blocks).\n"
                "- Return only final markdown (no thinking/explanations).\n\n"
                "Document section:\n"
                f"{text[:candidate_size]}"
            )
        else:
            prompt = (
                "Convert extracted document text into clean Docusaurus-compatible Markdown.\n"
                "Requirements:\n"
                "- Keep heading structure coherent.\n"
                "- Remove repeated headers/footers and OCR noise.\n"
                "- Use valid Markdown only; no code fences around whole output.\n"
                "- Preserve all detected tables.\n"
                "- For simple tables, use markdown pipe tables.\n"
                "- For merged cells (rowspan/colspan) or multi-line cells, output raw HTML <table>...</table> with proper rowspan/colspan.\n"
                "- Never flatten tables into prose.\n"
                "- Never split a table; output complete table blocks only.\n"
                "- If input already contains HTML <table> blocks, keep them as-is.\n"
                f"- title must be: {title}\n"
                f"- slug must be: /{slug}\n"
                "- Return only final markdown (no thinking/explanations).\n\n"
                "Document text:\n"
                f"{text[:candidate_size]}"
            )

        for candidate_model in candidate_models:
            try:
                response = client.chat.completions.create(
                    model=candidate_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert technical writer producing Docusaurus-compatible Markdown. "
                                "DEBUG_DOCILING_PROMPT_V2. "
                                "Never output chain-of-thought, think tags, or meta commentary. "
                                "Return only final markdown."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                used_model = candidate_model
                break
            except Exception as error:
                last_error = error
                logger.warning(
                    "AI model failed (model=%s, chars=%s): %s",
                    candidate_model,
                    candidate_size,
                    error,
                )
                continue

        if response is not None:
            break

        if last_error and not _is_token_limit_error(last_error):
            break

    if response is None:
        raise RuntimeError(f"All AI models failed: {last_error}")

    output = (response.choices[0].message.content or "").strip()
    output = _sanitize_model_markdown(output)
    if not output:
        raise RuntimeError("AI model returned empty output")
    logger.info(
        "AI conversion finished in %.2fs using provider=%s model=%s",
        time.perf_counter() - started_at,
        provider,
        used_model,
    )
    engine_name = f"{provider}/{used_model}"
    return _prepend_frontmatter_if_missing(output, title, slug), engine_name


def _convert_with_pandoc(text: str, title: str, slug: str) -> str:
    started_at = time.perf_counter()
    temp_txt = "temp.txt"
    with open(temp_txt, "w", encoding="utf-8") as file:
        file.write(text)

    output = "temp.md"
    subprocess.run(
        ["pandoc", temp_txt, "-f", "markdown", "-t", "gfm", "-o", output],
        check=True,
    )

    with open(output, "r", encoding="utf-8") as file:
        markdown = file.read()

    logger.info("Pandoc conversion finished in %.2fs", time.perf_counter() - started_at)
    return _prepend_frontmatter_if_missing(markdown, title, slug)


def to_docusaurus_markdown(text: str, file_path: str) -> tuple[str, str]:
    source_name = Path(file_path).stem
    title = source_name.replace("_", " ").replace("-", " ").strip().title() or "Document"
    slug = _slugify(source_name)

    chunks = _chunk_text(text)
    logger.info("Document split into %d chunk(s) for conversion", len(chunks))

    try:
        first_md, engine_name = _convert_with_ai(chunks[0], title, slug, is_continuation=False)

        if len(chunks) == 1:
            return _normalize_table_boundaries(first_md), engine_name

        parts = [first_md]
        for i, chunk in enumerate(chunks[1:], start=2):
            try:
                chunk_md, _ = _convert_with_ai(chunk, title, slug, is_continuation=True)
                # Strip any frontmatter the model added despite instructions
                chunk_md = re.sub(r"(?ms)^---\n.*?\n---\n?", "", chunk_md).strip()
                parts.append(chunk_md)
                logger.info("Converted chunk %d/%d", i, len(chunks))
            except Exception as chunk_err:
                # Never drop content: keep original chunk text if AI fails.
                logger.warning("Chunk %d failed, using raw fallback chunk: %s", i, chunk_err)
                parts.append(chunk.strip())

        joined = "\n\n".join(parts) + "\n"
        return _normalize_table_boundaries(joined), engine_name

    except Exception as error:
        logger.warning("AI conversion failed, falling back to pandoc: %s", error)
        markdown = _convert_with_pandoc(text, title, slug)
        return _normalize_table_boundaries(markdown), "pandoc"


def _normalize_table_boundaries(markdown_text: str) -> str:
    # Keep table blocks separated from surrounding text.
    text = re.sub(r"([^\n])\n(\|[^\n]+\|)", r"\1\n\n\2", markdown_text)
    text = re.sub(r"(\|[^\n]+\|)\n([^\n|<])", r"\1\n\n\2", text)

    # Collapse blank lines that appear inside markdown pipe tables.
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\|.*\|$", line.strip()):
            out.append(line)
            i += 1
            # Inside a table block, drop empty lines between table rows.
            while i < len(lines):
                cur = lines[i].strip()
                if cur == "":
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1
                    if j < len(lines) and re.match(r"^\|.*\|$", lines[j].strip()):
                        i = j
                        continue
                    out.append("")
                    i += 1
                    break
                if re.match(r"^\|.*\|$", cur):
                    out.append(lines[i])
                    i += 1
                    continue
                break
            continue

        out.append(line)
        i += 1

    return "\n".join(out)
#def _normalize_table_boundaries(markdown_text: str) -> str:
 ##  text = re.sub(r"([^\n])\n(\|[^\n]+\|)", r"\1\n\n\2", markdown_text)
   # text = re.sub(r"(\|[^\n]+\|)\n([^\n|<])", r"\1\n\n\2", text)
    #return text


def to_mdx(text: str, file_path: str) -> str:
    markdown, _ = to_docusaurus_markdown(text, file_path)
    return markdown


def _split_frontmatter(markdown_text: str) -> tuple[str, str]:
    match = re.match(r"(?ms)^---\n(.*?)\n---\n?", markdown_text.strip())
    if not match:
        return "", markdown_text.strip()
    return match.group(1), markdown_text[match.end():].strip()


def _extract_title_slug(frontmatter: str, fallback_slug: str, fallback_title: str) -> tuple[str, str]:
    title_match = re.search(r'(?m)^title:\s*"?(.+?)"?\s*$', frontmatter or "")
    slug_match = re.search(r'(?m)^slug:\s*(.+?)\s*$', frontmatter or "")
    title = (title_match.group(1).strip() if title_match else fallback_title).strip('"')
    slug = (slug_match.group(1).strip() if slug_match else f"/{fallback_slug}").strip()
    if not slug.startswith("/"):
        slug = f"/{slug}"
    return title, slug


def rewrite_docling_image_paths(markdown_text: str, source_name: str, doc_slug: str) -> str:
    """
    Convert backend-local image refs into Docusaurus static paths.
    uploads/_docling_assets/<source>/<source>_artifacts/file.png -> /img/docs/<doc_slug>/file.png
    """
    pattern = (
        rf"uploads/_docling_assets/{re.escape(source_name)}/"
        rf"{re.escape(source_name)}_artifacts/([^)\s]+)"
    )
    return re.sub(pattern, rf"/img/docs/{doc_slug}/\1", markdown_text)


def split_markdown_by_chapters(markdown_text: str, source_slug: str) -> list[tuple[str, str]]:
    """Split markdown into chapter files using level-2 headings (## ...)."""
    frontmatter, body = _split_frontmatter(markdown_text)
    base_title, base_slug = _extract_title_slug(
        frontmatter,
        fallback_slug=source_slug,
        fallback_title=source_slug.replace("-", " ").title(),
    )

    lines = body.splitlines()
    chapter_indices = [i for i, line in enumerate(lines) if re.match(r"^##\s+\S", line)]

    if not chapter_indices:
        filename = f"01-{source_slug}.md"
        chapter_frontmatter = (
            "---\n"
            f'title: "{_escape_title(base_title)}"\n'
            f"slug: {base_slug}\n"
            "sidebar_position: 1\n"
            "---\n\n"
        )
        return [(filename, chapter_frontmatter + body.strip() + "\n")]

    chapter_files: list[tuple[str, str]] = []
    for idx, start in enumerate(chapter_indices, start=1):
        end = chapter_indices[idx] if idx < len(chapter_indices) else len(lines)
        chunk = "\n".join(lines[start:end]).strip()

        heading = re.sub(r"^##\s+", "", lines[start]).strip()
        chapter_slug = _slugify(heading) or f"chapter-{idx}"

        chapter_frontmatter = (
            "---\n"
            f'title: "{_escape_title(heading)}"\n'
            f"slug: {base_slug}/{chapter_slug}\n"
            f"sidebar_position: {idx}\n"
            "---\n\n"
        )
        filename = f"{idx:02d}-{chapter_slug}.md"
        chapter_files.append((filename, chapter_frontmatter + chunk + "\n"))

    return chapter_files


def _highlight_keywords(html: str, keywords: list[str]) -> str:
    """Wrap configured keywords in <mark> for visual emphasis."""
    if not keywords:
        return html
    updated = html
    for kw in keywords:
        if not kw:
            continue
        pattern = re.compile(rf"\b({re.escape(kw)})\b", re.IGNORECASE)
        updated = pattern.sub(r'<mark class="keyword-mark">\1</mark>', updated)
    return updated


def _inline_images(html: str, output_dir: str, img_docs_dir: str | None = None) -> str:
    """Replace relative <img src="..."> paths with base64 data URLs."""
    def replace_src(m):
        src = m.group(1)
        # Skip already-inlined or remote URLs
        if src.startswith("data:") or src.startswith("http"):
            return m.group(0)

        img_path = None
        if src.startswith("/img/docs/") and img_docs_dir:
            # Map /img/docs/<doc-slug>/<file> to output/docusaurus-assets/<doc-slug>/<file>
            rel = src[len("/img/docs/") :]
            img_path = os.path.normpath(os.path.join(img_docs_dir, rel))
        elif not os.path.isabs(src):
            # Resolve path: relative src paths are resolved from output_dir
            img_path = os.path.normpath(os.path.join(output_dir, src))

        if not img_path:
            return m.group(0)
        if not os.path.isfile(img_path):
            return m.group(0)
        mime, _ = mimetypes.guess_type(img_path)
        mime = mime or "image/png"
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'src="data:{mime};base64,{b64}"'

    return re.sub(r'src="([^"]+)"', replace_src, html)


def to_html_page(markdown_text: str, output_dir: str | None = None, img_docs_dir: str | None = None) -> str:
    body_markdown = re.sub(r"(?ms)^---\n.*?\n---\n?", "", markdown_text).strip()
    # Strip [TOC] markers the AI sometimes emits — we don't want a generated TOC
    body_markdown = re.sub(r"^\[TOC\]\s*", "", body_markdown, flags=re.IGNORECASE | re.MULTILINE)
    html_body = render_markdown(
        body_markdown,
        extensions=["tables", "fenced_code"],
        output_format="html5",
    )
    if output_dir:
        html_body = _inline_images(
            html_body,
            os.path.abspath(output_dir),
            img_docs_dir=os.path.abspath(img_docs_dir) if img_docs_dir else None,
        )

    if HIGHLIGHT_KEYWORDS:
        html_body = _highlight_keywords(html_body, HIGHLIGHT_KEYWORDS)

    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "  <title>Docusaurus Preview</title>\n"
        "  <style>\n"
        "    :root { color-scheme: light; }\n"
        "    body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: #f8fafc; color: #0f172a; }\n"
        "    main { max-width: 900px; margin: 0 auto; padding: 2rem 1rem 3rem; line-height: 1.65; }\n"
        "    h1, h2, h3, h4 { line-height: 1.3; }\n"
        "    pre { background: #0b1220; color: #e2e8f0; padding: 1rem; border-radius: 10px; overflow-x: auto; }\n"
        "    code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }\n"
        "    table { border-collapse: collapse; width: 100%; }\n"
        "    th, td { border: 1px solid #cbd5e1; padding: 0.5rem; text-align: left; }\n"
        "    th { background: #e2e8f0; }\n"
        "    mark.keyword-mark { background: #fff7cc; border: 1px solid #f59f00; padding: 0 2px; border-radius: 4px; }\n"
        "    img { display: block; max-width: 100%; height: auto; margin: 1rem auto; border-radius: 8px; }\n"
        "    p > img { margin-top: 1rem; margin-bottom: 1rem; }\n"
        "    main { overflow-wrap: anywhere; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        f"{html_body}\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )