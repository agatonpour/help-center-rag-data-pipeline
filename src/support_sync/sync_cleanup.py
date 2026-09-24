import os
import json

from .config import Config
from .http import make_session
from .sitemap import fetch_all_article_urls
from .sharepoint_graph import GraphClient
from .blob_state import load_state_from_blob


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {"articles": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = Config()
    session = make_session(cfg.USER_AGENT)
    state = load_state_from_blob()

    # Current truth from sitemap
    urls = fetch_all_article_urls(session, cfg.SITEMAP_URL, cfg.ARTICLE_URL_CONTAINS)
    live_urls = set(u["url"] for u in urls)

    # SharePoint setup (same as updates job)
    graph = GraphClient(cfg.TENANT_ID, cfg.CLIENT_ID, cfg.CLIENT_SECRET, session)
    drive_id = graph.get_drive_id_by_name(cfg.SHAREPOINT_HOST, cfg.SHAREPOINT_SITE_PATH, cfg.DRIVE_NAME)

    root_id = graph.get_drive_root(drive_id)["id"]
    target_folder_id = graph.ensure_path(drive_id, root_id, cfg.ROOT_FOLDER.split("/"))

    # Allowed filenames based on live sitemap URLs
    allowed_filenames = set()
    for url in live_urls:
        meta = state.get("articles", {}).get(url)
        if meta and meta.get("filename"):
            allowed_filenames.add(meta["filename"])

    # Delete files not present in sitemap
    children = graph.list_children(drive_id, target_folder_id)
    deleted = 0

    for item in children:
        if item.get("file") is None:
            continue
        name = item.get("name", "")
        if name not in allowed_filenames:
            graph.delete_item(drive_id, item["id"])
            deleted += 1

    print(f"Cleanup done. deleted={deleted}")


if __name__ == "__main__":
    main()
