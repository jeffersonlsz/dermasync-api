# API dermasync

## Description - English

This repository contains the backend service for the DermaSync project ([www.dermasync.com.br](https://www.dermasync.com.br)) — a platform designed to extract and deliver insights from the collective experiences of people living with atopic dermatitis.

It implements a Retrieval-Augmented Generation (RAG) pipeline that processes user-generated content from online communities (such as Facebook, Telegram, and Reddit). Using semantic vector embeddings, the system retrieves relevant segments and generates actionable insights to support patients in making informed decisions about their treatment.

The backend API for the DermaSync project. It is modularly organized to handle:
- Image upload and processing
- Processing of user reports
- Enrichment using LLMs
- Integration with a vector database (ChromaDB)

## 🏗️ Project initial structure

/app
/routes
├── imagens.py
├── relatos.py
└── usuario.py
/services
├── imagens_service.py
├── chroma_service.py
└── enriquecimento_service.py
/main.py


## How to run it

Create the virtual environment

1. python -m venv venv
2. source venv/bin/activate  # Linux/macOS
3. .\venv\Scripts\activate   # Windows

Steps to install and set up the project:
1. Clone the repository: `git clone https://github.com/seu-usuario/dermasync-api.git`
2. Install dependencies: `pip install requirements.txt`
3. Run uvicorn server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

How to run the tests
```bash
python .\run_tests.py
pytest .\tests\test_pipeline_02_enriquecer_metadados.py
```


## Usage
Instructions on how to use the project:
```python
# Example command
localhost:8000/docs

...and have fun...
```
## 🧠 Arquitetura do Projeto DermaSync

<img src="docs/arquitetura-dermasync.png" alt="Arquitetura DermaSync" width="50%" />

## Contributing
Guidelines for contributing to the project:
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Submit a pull request.

## License
Specify the license under which the project is distributed.

## Contact
Provide contact information or links for further inquiries.