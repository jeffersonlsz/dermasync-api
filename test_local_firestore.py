from app.firestore.client import get_firestore_client

db = get_firestore_client()

db.collection("debug").document("1").set({
    "msg": "funcionando local"
})

print("OK")
