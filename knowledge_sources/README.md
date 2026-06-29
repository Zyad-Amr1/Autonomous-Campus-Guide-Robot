# External Knowledge Sources

Place optional chatbot knowledge files in `knowledge_sources/documents/`.

Supported document types:
- `.txt`
- `.md`
- `.csv`
- `.pdf` when `pypdf` is installed

Website pages are configured in `knowledge_sources/web_sources.json`.
Run the external sync command to ingest website and document chunks into the local RAG knowledge base.

