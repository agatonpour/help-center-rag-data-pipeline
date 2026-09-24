import xml.etree.ElementTree as ET
from typing import List, Dict
from .http import get_with_retries

def parse_sitemap(xml_text: str) -> List[Dict[str, str]]:
    # Supports both sitemapindex and urlset
    root = ET.fromstring(xml_text)

    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    entries = []

    if root.tag.endswith("sitemapindex"):
        for sm in root.findall(f"{ns}sitemap"):
            loc = sm.findtext(f"{ns}loc") or ""
            lastmod = sm.findtext(f"{ns}lastmod") or ""
            entries.append({"type": "sitemap", "loc": loc.strip(), "lastmod": lastmod.strip()})
        return entries

    if root.tag.endswith("urlset"):
        for u in root.findall(f"{ns}url"):
            loc = (u.findtext(f"{ns}loc") or "").strip()
            lastmod = (u.findtext(f"{ns}lastmod") or "").strip()
            entries.append({"type": "url", "loc": loc, "lastmod": lastmod})
        return entries

    return []

def fetch_all_article_urls(session, sitemap_url: str, article_contains: str) -> List[Dict[str, str]]:
    r = get_with_retries(session, sitemap_url)
    first = parse_sitemap(r.text)

    urls: List[Dict[str, str]] = []

    # If it's an index, fetch each child sitemap and aggregate urls
    if any(e["type"] == "sitemap" for e in first):
        for e in first:
            if e["type"] != "sitemap":
                continue
            rr = get_with_retries(session, e["loc"])
            for u in parse_sitemap(rr.text):
                if u.get("type") == "url" and article_contains in u.get("loc", ""):
                    urls.append({"url": u["loc"], "lastmod": u.get("lastmod", "")})
        return urls

    # Otherwise it's already a urlset
    for u in first:
        if u.get("type") == "url" and article_contains in u.get("loc", ""):
            urls.append({"url": u["loc"], "lastmod": u.get("lastmod", "")})

    return urls
