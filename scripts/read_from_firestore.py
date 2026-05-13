import argparse
import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
# para que os módulos da 'app' possam ser encontrados.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.firestore.client import get_firestore_client

def initialize_firestore():
    """
    Initializes the Firestore client using the centralized app configuration.
    """
    try:
        return get_firestore_client()
    except Exception as e:
        print(f"Error initializing Firestore: {e}")
        sys.exit(1)


def read_relato(doc_id):
    """
    Reads a document from the 'relatos' collection by ID.
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

def read_imagem(doc_id):
    """
    Reads a document from the 'imagens' collection by ID.
    """
    db = initialize_firestore()
    
    print(f"Attempting to fetch document '{doc_id}' from collection 'imagens'...")
    
    doc_ref = db.collection('imagens').document(doc_id)
    doc = doc_ref.get()

    if doc.exists:
        print(f"SUCCESS: Document found.")
        print("-" * 30)
        print(f"ID: {doc.id}")
        print(f"Data: {doc.to_dict()}")
        print("-" * 30)
        return doc.to_dict()
    else:
        print(f"FAILURE: No document found with ID: {doc_id} in collection 'imagens'")
        return None

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Read a document from a Firestore collection."
    )
    parser.add_argument(
        "collection",
        type=str,
        help="The collection to read from (e.g., 'relatos', 'imagens')"
    )
    parser.add_argument(
        "id", 
        type=str, 
        help="The unique ID of the document to retrieve"
    )

    args = parser.parse_args()
    
    if args.collection == "relatos":
        read_relato(args.id)
    elif args.collection == "imagens":
        read_imagem(args.id)
    else:
        print(f"Unknown collection: {args.collection}")
        sys.exit(1)
