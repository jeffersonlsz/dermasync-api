# firestore/client.py
from google.cloud import firestore
from ..config import GOOGLE_CLOUD_PROJECT

db = firestore.Client()
increment_function = firestore.Increment
#expoe firestore 

