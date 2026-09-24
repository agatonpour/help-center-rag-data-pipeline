import json
import requests
from typing import Dict, List, Optional
from .http import get_with_retries

GRAPH = "https://graph.microsoft.com/v1.0"

class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, session: requests.Session):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session
        self._token: Optional[str] = None

    def token(self) -> str:
        if self._token:
            return self._token
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }
        r = self.session.post(url, data=data, timeout=30)
        r.raise_for_status()
        self._token = r.json()["access_token"]
        return self._token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token()}"}

    def ensure_folder(self, drive_id: str, parent_item_id: str, name: str) -> str:
        # Try find existing child folder
        url = f"{GRAPH}/drives/{drive_id}/items/{parent_item_id}/children?$select=id,name,folder"
        r = self.session.get(url, headers=self._headers(), timeout=30)
        r.raise_for_status()
        for item in r.json().get("value", []):
            if item.get("name") == name and item.get("folder") is not None:
                return item["id"]

        # Create folder
        url = f"{GRAPH}/drives/{drive_id}/items/{parent_item_id}/children"
        payload = {"name": name, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
        r = self.session.post(url, headers={**self._headers(), "Content-Type": "application/json"}, data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        return r.json()["id"]

    def ensure_path(self, drive_id: str, root_item_id: str, path_parts: List[str]) -> str:
        current = root_item_id
        for part in path_parts:
            if not part:
                continue
            current = self.ensure_folder(drive_id, current, part)
        return current

    def upload_small_file(self, drive_id: str, folder_item_id: str, filename: str, content_bytes: bytes) -> Dict:
        # PUT /content works well for small-ish files (HTML usually is)
        url = f"{GRAPH}/drives/{drive_id}/items/{folder_item_id}:/{filename}:/content"
        r = self.session.put(url, headers=self._headers(), data=content_bytes, timeout=60)
        r.raise_for_status()
        return r.json()

    def list_children(self, drive_id: str, folder_item_id: str) -> List[Dict]:
        items = []
        url = f"{GRAPH}/drives/{drive_id}/items/{folder_item_id}/children?$select=id,name,file,folder"
        while url:
            r = self.session.get(url, headers=self._headers(), timeout=30)
            r.raise_for_status()
            data = r.json()
            items.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
        return items

    def delete_item(self, drive_id: str, item_id: str) -> None:
        url = f"{GRAPH}/drives/{drive_id}/items/{item_id}"
        r = self.session.delete(url, headers=self._headers(), timeout=30)
        r.raise_for_status()

    def get_drive_root(self, drive_id: str) -> Dict:
        url = f"{GRAPH}/drives/{drive_id}/root"
        r = self.session.get(url, headers=self._headers(), timeout=30)
        r.raise_for_status()
        return r.json()

    def get_drive_id_by_name(self, host: str, site_path: str, drive_name: str) -> str:
        site_url = f"{GRAPH}/sites/{host}:{site_path}"
        r = self.session.get(site_url, headers=self._headers(), timeout=30)
        r.raise_for_status()
        site_id = r.json()["id"]

        drives_url = f"{GRAPH}/sites/{site_id}/drives"
        r = self.session.get(drives_url, headers=self._headers(), timeout=30)
        r.raise_for_status()

        for d in r.json()["value"]:
            if d["name"] == drive_name:
                return d["id"]

        raise RuntimeError(f"Drive '{drive_name}' not found")
