import os

ENV = os.getenv("ENV", "local")

if ENV == "local":
    os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "localhost:9199"
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"

    PROJECT_ID = "demo-dermasync"
    STORAGE_BUCKET = "demo-dermasync.appspot.com"

else:
    PROJECT_ID = "dermasync-3d14a"
    STORAGE_BUCKET = "dermasync-3d14a.appspot.com"