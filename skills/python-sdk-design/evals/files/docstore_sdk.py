"""DocStore SDK - client library for the Acme DocStore service."""

import time
from enum import Enum

import requests


class ClientOptions:
    """Bundle of optional client settings."""

    def __init__(self, timeout=30, max_retries=3, verify_ssl=True, user_agent=None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.user_agent = user_agent


class DocumentState(Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Document:
    def __init__(self, doc_id, title, body, state=DocumentState.draft):
        self.doc_id = doc_id
        self.title = title
        self.body = body
        self.state = state


class DocStoreService:
    """Main entry point for the DocStore service."""

    def __init__(self, connection_string, options=None):
        parts = dict(p.split("=", 1) for p in connection_string.split(";"))
        self.endpoint = parts["Endpoint"]
        self.access_key = parts["AccessKey"]
        self.options = options or ClientOptions()

    def set_timeout(self, timeout):
        """Change the timeout used for subsequent requests."""
        self.options.timeout = timeout

    def getDocumentMetadata(self, doc_id):
        resp = requests.get(
            f"{self.endpoint}/documents/{doc_id}/meta",
            headers={"x-key": self.access_key},
            timeout=self.options.timeout,
        )
        return resp.json()

    def get_document(self, doc_id):
        """Fetch a document. Returns None if it does not exist."""
        resp = requests.get(
            f"{self.endpoint}/documents/{doc_id}",
            headers={"x-key": self.access_key},
            timeout=self.options.timeout,
        )
        if resp.status_code == 404:
            return None
        data = resp.json()
        return Document(data["id"], data["title"], data["body"])

    def document_exists(self, doc_id):
        """Raises DocumentNotFoundError if the document does not exist."""
        resp = requests.head(
            f"{self.endpoint}/documents/{doc_id}",
            headers={"x-key": self.access_key},
        )
        if resp.status_code == 404:
            raise DocumentNotFoundError(doc_id)
        return True

    def upload_document(self, doc_id, content, overwrite=False, content_type="text/plain", **kwargs):
        timeout = kwargs.pop("timeout", self.options.timeout)
        encoding = kwargs.pop("encoding", "utf-8")
        if not isinstance(content, Document):
            raise TypeError("content must be a Document instance")
        resp = requests.put(
            f"{self.endpoint}/documents/{doc_id}",
            json={"title": content.title, "body": content.body},
            headers={"x-key": self.access_key, "content-type": content_type,
                     "x-overwrite": str(overwrite), "x-encoding": encoding},
            timeout=timeout,
        )
        if resp.status_code >= 400:
            return False
        return True

    def list_documents(self, continuation_token=None):
        """Return (documents, next_token). Pass next_token back in to continue."""
        params = {}
        if continuation_token:
            params["page_token"] = continuation_token
        resp = requests.get(
            f"{self.endpoint}/documents",
            params=params,
            headers={"x-key": self.access_key},
        )
        data = resp.json()
        docs = [Document(d["id"], d["title"], d["body"]) for d in data["items"]]
        return docs, data.get("next_page_token")

    def export_documents(self, target_bucket):
        """Export all documents. Blocks until the export completes."""
        resp = requests.post(
            f"{self.endpoint}/exports",
            json={"bucket": target_bucket},
            headers={"x-key": self.access_key},
        )
        job_id = resp.json()["job_id"]
        while True:
            status = requests.get(
                f"{self.endpoint}/exports/{job_id}",
                headers={"x-key": self.access_key},
            ).json()
            if status["state"] == "done":
                return status
            time.sleep(5)

    async def delete_document_async(self, doc_id):
        import aiohttp

        async with aiohttp.ClientSession() as session:
            await session.delete(
                f"{self.endpoint}/documents/{doc_id}",
                headers={"x-key": self.access_key},
            )

    @staticmethod
    def build_document_url(endpoint, doc_id):
        return f"{endpoint}/documents/{doc_id}"


class DocumentNotFoundError(Exception):
    pass
