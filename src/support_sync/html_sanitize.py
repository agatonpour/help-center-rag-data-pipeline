import re

# Very small + dependency-free sanitizer for "AI-friendly" HTML
# Keeps readable text structure, removes heavy/noisy content (images, base64, scripts, styles).
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
_NOSCRIPT_RE = re.compile(r"<noscript\b[^>]*>.*?</noscript>", re.IGNORECASE | re.DOTALL)
_IFRAME_RE = re.compile(r"<iframe\b[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL)
_SVG_RE = re.compile(r"<svg\b[^>]*>.*?</svg>", re.IGNORECASE | re.DOTALL)

# Remove data:* base64 blobs that sometimes appear inline
_DATA_URI_RE = re.compile(r"data:[^\"']{0,50};base64,[A-Za-z0-9+/=\s]{200,}", re.IGNORECASE)

def sanitize_html_for_ai(html: str) -> str:
    if not html:
        return ""

    # Remove heavy/noisy blocks
    html = _SCRIPT_RE.sub("", html)
    html = _STYLE_RE.sub("", html)
    html = _NOSCRIPT_RE.sub("", html)
    html = _IFRAME_RE.sub("", html)
    html = _SVG_RE.sub("", html)

    # Remove <img> tags entirely (prevents huge irrelevant chunks)
    html = _IMG_TAG_RE.sub("", html)

    # Remove any inline base64/data-uri blobs if present
    html = _DATA_URI_RE.sub("[removed inline data]", html)

    # Optional: collapse extremely long runs of whitespace
    html = re.sub(r"[ \t]{3,}", "  ", html)
    html = re.sub(r"\n{4,}", "\n\n", html)

    return html
