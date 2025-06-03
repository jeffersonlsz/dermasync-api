# API dermasync

## Description - English

This repository contains the backend service for the DermaSync project ([www.dermasync.com.br](https://www.dermasync.com.br)) — a platform designed to extract and deliver insights from the collective experiences of people living with atopic dermatitis.

It implements a Retrieval-Augmented Generation (RAG) pipeline that processes user-generated content from online communities (such as Facebook, Telegram, and Reddit). Using semantic vector embeddings, the system retrieves relevant segments and generates actionable insights to support patients in making informed decisions about their treatment.


## How to run it
Steps to install and set up the project:
1. Clone the repository: `git clone <repository-url>`
2. Install dependencies: `pip install requirements.txt`
3. Run uvicorn server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Usage
Instructions on how to use the project:
```python
# Example command
npm start
```

## Contributing
Guidelines for contributing to the project:
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Submit a pull request.

## License
Specify the license under which the project is distributed.

## Contact
Provide contact information or links for further inquiries.