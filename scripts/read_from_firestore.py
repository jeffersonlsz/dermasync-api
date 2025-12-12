import argparse
import os
import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def initialize_firestore():
    """
    Initializes the Firestore client.
    
    This function assumes you are using Application Default Credentials (ADC)
    by setting the GOOGLE_APPLICATION_CREDENTIALS environment variable.
    
    If you are using a local service account file, uncomment the lines below.
    """
    try:
        # Check if the app is already initialized
        if not firebase_admin._apps:
            # Option 1: Use Application Default Credentials (Recommended for production/cloud)
            firebase_admin.initialize_app()
            
            # Option 2: Use a service account JSON file (Common for local development)
            # cred = credentials.Certificate('path/to/serviceAccountKey.json')
            # firebase_admin.initialize_app(cred)
            
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firestore: {e}")
        sys.exit(1)

def read_relato(doc_id):
    """
    Reads a document from the 'relator' collection by ID.
    """
    db = initialize_firestore()
    
    print(f"Attempting to fetch document '{doc_id}' from collection 'relatos'...")
    
    doc_ref = db.collection('relatos').document(doc_id)
    doc = doc_ref.get()

    if doc.exists:
        print(f"SUCCESS: Document found.")
        print("-" * 30)
        print(f"ID: {doc.id}")
        print(f"Data: {doc.to_dict()}")
        print("-" * 30)
        return doc.to_dict()
    else:
        print(f"FAILURE: No document found with ID: {doc_id}")
        return None

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Read a document from the 'jornadas' Firestore collection."
    )
    parser.add_argument(
        "id", 
        type=str, 
        help="The unique ID of the document to retrieve"
    )

    args = parser.parse_args()
    
    # Run the function
    read_relato(args.id)
