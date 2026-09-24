import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from support_sync.config import Config
from support_sync.sync_updates import fetch_article_body_html


class ConfiguredSourceTests(unittest.TestCase):
    def test_fetch_uses_configured_help_center(self):
        session = Mock()
        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = {"article": {"body": "<p>Example</p>"}}
        result = fetch_article_body_html(session, "123", "https://help.example.com/hc/sitemap.xml")
        session.get.assert_called_once_with(
            "https://help.example.com/api/v2/help_center/en-us/articles/123.json", timeout=30
        )
        self.assertEqual(result, ("<p>Example</p>", "ok"))

    def test_missing_source_fails_before_network_calls(self):
        with self.assertRaisesRegex(ValueError, "SUPPORT_SITEMAP_URL"):
            Config(SITEMAP_URL="")

    def test_unauthorized_article_is_skipped(self):
        session = Mock()
        session.get.return_value.status_code = 401
        self.assertEqual(
            fetch_article_body_html(session, "123", "https://help.example.com/hc/sitemap.xml"),
            (None, "unauthorized"),
        )
