from collections import Counter
import re


HEADER_FOOTER_SCAN_LINES = 3
HEADER_FOOTER_REPEAT_THRESHOLD = 3
# Body dedup limit — high enough to keep legitimate repeated terms in tables/lists.
MAX_BODY_REPEAT = 5

PLACEHOLDER_PATTERNS = [
    re.compile(r"^\(to be updated.*\)$", re.IGNORECASE),
    re.compile(r"^\(to be confirmed.*\)$", re.IGNORECASE),
    re.compile(r"^\(to be completed.*\)$", re.IGNORECASE),
    re.compile(r"^tbd$", re.IGNORECASE),
]


def _normalize_line(line):
    """Normalize for header/footer detection only (digits → token)."""
    normalized = re.sub(r"\d+", "<num>", line.lower().strip())
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _normalize_for_dedup(line):
    """Normalize for body dedup — keep digits so numeric IDs don't collide."""
    normalized = line.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _is_table_line(line):
    """Table rows must never be dropped by the dedup filter."""
    stripped = line.strip()
    if stripped.startswith("|") or stripped.endswith("|"):
        return True
    if re.match(r"<t[rdh][\s>]", stripped, re.IGNORECASE):
        return True
    return False


def _is_placeholder_line(line):
    compact = " ".join(line.split()).strip()
    if not compact:
        return False
    return any(pattern.match(compact) for pattern in PLACEHOLDER_PATTERNS)


def _is_noise_line(line):
    if not line:
        return True
    if re.match(r"^\d+$", line):
        return True
    if "table of contents" in line.lower():
        return True
    if re.search(r"\.{5,}", line):
        return True
    if _is_placeholder_line(line):
        return True
    return False


def _clean_flat_text(text):
    lines = text.split("\n")
    cleaned = []
    seen = {}

    for raw_line in lines:
        line = raw_line.strip()
        if _is_noise_line(line):
            continue

        if _is_table_line(line):
            cleaned.append(line)
            continue

        normalized = _normalize_for_dedup(line)
        seen[normalized] = seen.get(normalized, 0) + 1
        if seen[normalized] > MAX_BODY_REPEAT:
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def _clean_paged_text(pages):
    return "\n\n".join(_clean_paged_lines(pages))


def _clean_paged_lines(pages):
    page_lines = []
    repeated_edges = Counter()

    for page in pages:
        lines = [line.strip() for line in page.splitlines() if line.strip()]
        page_lines.append(lines)

        for line in lines[:HEADER_FOOTER_SCAN_LINES]:
            if not _is_noise_line(line):
                repeated_edges[("head", _normalize_line(line))] += 1

        for line in lines[-HEADER_FOOTER_SCAN_LINES:]:
            if not _is_noise_line(line):
                repeated_edges[("foot", _normalize_line(line))] += 1

    removable = {
        key
        for key, count in repeated_edges.items()
        if count >= HEADER_FOOTER_REPEAT_THRESHOLD
    }

    cleaned_pages = []
    for lines in page_lines:
        total_lines = len(lines)
        kept_lines = []
        # Reset per-page so valid content on later pages isn't dropped by earlier pages.
        seen = {}

        for index, line in enumerate(lines):
            if _is_noise_line(line):
                continue

            normalized = _normalize_line(line)
            in_header_zone = index < HEADER_FOOTER_SCAN_LINES
            in_footer_zone = index >= max(0, total_lines - HEADER_FOOTER_SCAN_LINES)

            if in_header_zone and ("head", normalized) in removable:
                continue
            if in_footer_zone and ("foot", normalized) in removable:
                continue

            if not _is_table_line(line):
                dedup_key = _normalize_for_dedup(line)
                seen[dedup_key] = seen.get(dedup_key, 0) + 1
                if seen[dedup_key] > MAX_BODY_REPEAT:
                    continue

            kept_lines.append(line)

        if kept_lines:
            cleaned_pages.append("\n".join(kept_lines))

    return cleaned_pages


def clean_content_pages(text):
    if isinstance(text, list):
        return _clean_paged_lines(text)
    cleaned = _clean_flat_text(text)
    return [cleaned] if cleaned else []


def clean_content(text):
    if isinstance(text, list):
        return _clean_paged_text(text)
    return _clean_flat_text(text)