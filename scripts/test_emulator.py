import os
from firebase_admin import initialize_app, storage

os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "localhost:9199"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"

initialize_app()

bucket = storage.bucket("dermasync-3d14a.firebasestorage.app")
blob = bucket.blob("debug.txt")

blob.upload_from_string("teste local")

print("UPLOAD OK")