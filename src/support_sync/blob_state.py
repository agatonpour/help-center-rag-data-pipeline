import json
import os
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError


def _get_blob_client():
    connection_string = os.getenv("AzureWebJobsStorage", "")
    container_name = os.getenv("STATE_CONTAINER", "sync-state")
    blob_name = os.getenv("STATE_BLOB_NAME", "support/state_support.json")

    if not connection_string:
        raise RuntimeError("AzureWebJobsStorage is not set")

    service = BlobServiceClient.from_connection_string(connection_string)
    container = service.get_container_client(container_name)
    blob = container.get_blob_client(blob_name)
    return container, blob


def load_state_from_blob() -> dict:
    container, blob = _get_blob_client()

    try:
        data = blob.download_blob().readall()
        return json.loads(data.decode("utf-8"))
    except ResourceNotFoundError:
        try:
            container.create_container()
        except Exception:
            pass
        return {"articles": {}, "unauthorized": {}, "empty": {}}


def save_state_to_blob(state: dict) -> None:
    _, blob = _get_blob_client()
    blob.upload_blob(
        json.dumps(state, ensure_ascii=False, indent=2),
        overwrite=True
    )
