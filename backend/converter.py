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


def _chunk_text(text: str) -> list[str]:
    """Split text at paragraph boundaries into CHUNK_SIZE chunks, capped at MAX_CHUNKS."""
    chunks = []
    remaining = text.strip()
    while len(remaining) > CHUNK_SIZE:
        split_at = remaining.rfind("\n\n", 0, CHUNK_SIZE)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, CHUNK_SIZE)
        if split_at == -1:
            split_at = CHUNK_SIZE
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks[:MAX_CHUNKS]


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
                "- Preserve any detected tables and tabular columns as markdown tables; do not flatten them into prose.\n"
                "- If input already contains HTML <table> blocks, preserve them as-is (including merged cells / colspan).\n"
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
                "- Preserve any detected tables and tabular columns as markdown tables; do not flatten them into prose.\n"
                "- If input already contains HTML <table> blocks, preserve them as-is (including merged cells / colspan).\n"
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
            return first_md, engine_name

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

        return "\n\n".join(parts) + "\n", engine_name

    except Exception as error:
        logger.warning("AI conversion failed, falling back to pandoc: %s", error)
        markdown = _convert_with_pandoc(text, title, slug)
        return markdown, "pandoc"


def to_mdx(text: str, file_path: str) -> str:
    markdown, _ = to_docusaurus_markdown(text, file_path)
    return markdown


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


def _inline_images(html: str, output_dir: str) -> str:
    """Replace relative <img src="..."> paths with base64 data URLs."""
    def replace_src(m):
        src = m.group(1)
        # Skip already-inlined or remote URLs
        if src.startswith("data:") or src.startswith("http"):
            return m.group(0)
        # Resolve path: src is relative to output_dir
        img_path = os.path.normpath(os.path.join(output_dir, src))
        if not os.path.isfile(img_path):
            return m.group(0)
        mime, _ = mimetypes.guess_type(img_path)
        mime = mime or "image/png"
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'src="data:{mime};base64,{b64}"'

    return re.sub(r'src="([^"]+)"', replace_src, html)


def to_html_page(markdown_text: str, output_dir: str | None = None) -> str:
    body_markdown = re.sub(r"(?ms)^---\n.*?\n---\n?", "", markdown_text).strip()
    # Strip [TOC] markers the AI sometimes emits — we don't want a generated TOC
    body_markdown = re.sub(r"^\[TOC\]\s*", "", body_markdown, flags=re.IGNORECASE | re.MULTILINE)
    html_body = render_markdown(
        body_markdown,
        extensions=["tables", "fenced_code"],
        output_format="html5",
    )
    if output_dir:
        html_body = _inline_images(html_body, os.path.abspath(output_dir))

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