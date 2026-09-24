import os
import json
import re
import requests
from pathlib import Path
from urllib.parse import urlsplit

from .config import Config
from .http import make_session, get_with_retries, rate_limit
from .html_sanitize import sanitize_html_for_ai
from .sitemap import fetch_all_article_urls
from .zendesk import filename_for
from .sharepoint_graph import GraphClient
from .blob_state import load_state_from_blob, save_state_to_blob


ARTICLE_ID_RE = re.compile(r"/articles/(\d+)-")


def extract_article_id(url: str) -> str | None:
    m = ARTICLE_ID_RE.search(url)
    return m.group(1) if m else None

def strip_prefix_before_dash(filename: str) -> str:
    if "-" in filename:
        return filename.split("-", 1)[1]
    return filename


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {"articles": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)




def fetch_article_body_html(session, article_id: str, sitemap_url: str):
    source = urlsplit(sitemap_url)
    api_url = f"{source.scheme}://{source.netloc}/api/v2/help_center/en-us/articles/{article_id}.json"
    r = session.get(api_url, timeout=30)

    if r.status_code == 401:
        return None, "unauthorized"

    r.raise_for_status()
    data = r.json()
    return data["article"].get("body"), "ok"


def main():
    print("Starting support → SharePoint sync...")
    cfg = Config()
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    session = make_session(cfg.USER_AGENT)
    state = load_state_from_blob()
    state.setdefault("unauthorized", {})
    state.setdefault("empty", {})

    urls = fetch_all_article_urls(session, cfg.SITEMAP_URL, cfg.ARTICLE_URL_CONTAINS)

    # SharePoint setup
    graph = GraphClient(cfg.TENANT_ID, cfg.CLIENT_ID, cfg.CLIENT_SECRET, session)
    drive_id = graph.get_drive_id_by_name(cfg.SHAREPOINT_HOST, cfg.SHAREPOINT_SITE_PATH, cfg.DRIVE_NAME)
    root_id = graph.get_drive_root(drive_id)["id"]
    target_folder_id = graph.ensure_path(drive_id, root_id, cfg.ROOT_FOLDER.split("/"))

    updated = 0
    skipped = 0
    failed = 0

    for entry in urls:
        url = entry["url"]
        lastmod = entry.get("lastmod", "")

        fname = strip_prefix_before_dash(filename_for(url))
        prev = state["articles"].get(url)

        if prev and prev.get("lastmod") == lastmod:
            skipped += 1
            continue

        article_id = extract_article_id(url)
        if not article_id:
            failed += 1
            print(f"[ERROR] Could not parse article id: {url}")
            continue

        empty = state["empty"].get(url)
        if empty and empty.get("lastmod") == lastmod:
            skipped += 1
            continue

        try:
            raw_html, status = fetch_article_body_html(session, article_id, cfg.SITEMAP_URL)

            # 1. Unauthorized → skip
            if status == "unauthorized":
                state["unauthorized"][url] = {"lastmod": lastmod}
                skipped += 1
                continue

            # 2. Empty from API → skip
            if not raw_html:
                state["empty"][url] = {"lastmod": lastmod, "reason": "empty_raw"}
                skipped += 1
                continue

            html = sanitize_html_for_ai(raw_html)

            # 3. Empty after sanitize → skip
            if not html.strip():
                state["empty"][url] = {"lastmod": lastmod, "reason": "empty_after_sanitize"}
                skipped += 1
                continue

            # 4. Normal happy path
            out_path = Path(cfg.OUTPUT_DIR) / fname
            out_path.write_text(html, encoding="utf-8")

            graph.upload_small_file(
                drive_id,
                target_folder_id,
                fname,
                html.encode("utf-8")
            )

            state["articles"][url] = {"lastmod": lastmod, "filename": fname}
            updated += 1
            rate_limit(cfg.RATE_LIMIT_SECONDS)


        except Exception as e:
            failed += 1
            print(f"[ERROR] Unexpected failure for {url}: {e}")

    save_state_to_blob(state)
    print(f"Done. updated={updated} skipped={skipped} failed={failed} total={len(urls)}")


if __name__ == "__main__":
    main()
