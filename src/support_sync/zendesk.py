import re
from typing import Tuple

ARTICLE_RE = re.compile(r"/articles/(\d+)-(.+)$")

def article_id_and_slug(url: str) -> Tuple[str, str]:
    m = ARTICLE_RE.search(url)
    if not m:
        # fallback: safe filename from full url
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", url).strip("-")
        return safe[:64], "article"
    return m.group(1), m.group(2)

def filename_for(url: str) -> str:
    aid, slug = article_id_and_slug(url)
    safe_slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-")
    return f"{aid}-{safe_slug}.html"
