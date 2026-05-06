import os
import firebase_admin
from firebase_admin import initialize_app

from app.config import (
    FIREBASE_MODE,
    FIREBASE_STORAGE_BUCKET,
    GOOGLE_CLOUD_PROJECT,
    FIREBASE_STORAGE_EMULATOR_HOST,
)

firebase_app = None

def init_firebase():
    global firebase_app

    if firebase_app:
        return firebase_app

    if FIREBASE_MODE == "local":
        os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = FIREBASE_STORAGE_EMULATOR_HOST

    firebase_app = initialize_app(options={
        "projectId": GOOGLE_CLOUD_PROJECT,
        "storageBucket": FIREBASE_STORAGE_BUCKET,
    })

    return firebase_app