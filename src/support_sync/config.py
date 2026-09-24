import os
from urllib.parse import urlsplit
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    # Sitemap
    SITEMAP_URL: str = os.getenv(
        "SUPPORT_SITEMAP_URL",
        ""
    )
    ARTICLE_URL_CONTAINS: str = "/hc/en-us/articles/"

    # Azure / Graph
    TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")

    # SharePoint
    SHAREPOINT_HOST: str = os.getenv("SHAREPOINT_HOST", "")
    SHAREPOINT_SITE_PATH: str = os.getenv("SHAREPOINT_SITE_PATH", "")
    DRIVE_NAME: str = os.getenv("SHAREPOINT_DRIVE_NAME", "Documents")
    ROOT_FOLDER: str = os.getenv(
        "SHAREPOINT_ROOT_FOLDER",
        "knowledge-base/support"
    )

    # Local/state
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output/dry_run")
    STATE_PATH: str = os.getenv("STATE_PATH", "output/state_support.json")

    RATE_LIMIT_SECONDS: float = float(os.getenv("RATE_LIMIT_SECONDS", "0.5"))
    USER_AGENT: str = os.getenv("USER_AGENT", "support-sharepoint-sync/1.0")
    def __post_init__(self):
        sitemap = urlsplit(self.SITEMAP_URL)
        if sitemap.scheme not in {"http", "https"} or not sitemap.netloc:
            raise ValueError("Set SUPPORT_SITEMAP_URL to your Help Center sitemap URL")
