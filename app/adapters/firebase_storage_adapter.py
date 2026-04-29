import asyncio
import json
import os

import firebase_admin
from firebase_admin import credentials, storage


def init_firebase() -> firebase_admin.App:
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    if not bucket_name:
        raise ValueError("FIREBASE_STORAGE_BUCKET is not set")

    options = {"storageBucket": bucket_name}
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_PATH")
    if service_account_path:
        credential = credentials.Certificate(service_account_path)
        return firebase_admin.initialize_app(credential, options)

    credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if credentials_json:
        credential_info = json.loads(credentials_json)
        credential = credentials.Certificate(credential_info)
        return firebase_admin.initialize_app(credential, options)

    return firebase_admin.initialize_app(options=options)


class FirebaseStorageAdapter:
    def __init__(self) -> None:
        self._app = init_firebase()

    async def upload_bytes(
        self,
        *,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self._upload_bytes_sync,
            path=path,
            content=content,
            content_type=content_type,
        )

    def _upload_bytes_sync(
        self,
        *,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        bucket = storage.bucket(app=self._app)
        blob = bucket.blob(path)
        blob.upload_from_string(content, content_type=content_type)
        blob.make_public()
        return blob.public_url
