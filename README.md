# Agentic RAG Chatbot for Multi-Format Document QA using Model Context Protocol (MCP)

## Project Description

This project implements an agent-based Retrieval-Augmented Generation (RAG) chatbot designed to answer user questions using uploaded documents of various formats. The architecture strictly adheres to an agentic structure and incorporates a custom Model Context Protocol (MCP) for seamless communication between agents and between agents and the Language Model (LLM). This solution addresses the core functional requirements of a coding round problem statement, focusing on robust document ingestion, an extensible agentic design, and efficient information retrieval.

## Core Functional Requirements

This RAG chatbot solution fulfills the following core functional requirements:

1.  **Support for Diverse Document Formats**:
    *   ✅ PDF
    *   ✅ PPTX
    *   ✅ CSV
    *   ✅ DOCX
    *   ✅ TXT / Markdown

2.  **Agentic Architecture**:
    The system is built with a clear separation of concerns, utilizing a minimum of three distinct agents:
    *   **IngestionAgent**: Responsible for parsing and preprocessing uploaded documents, converting them into a standardized format suitable for indexing.
    *   **RetrievalAgent**: Handles the embedding of document chunks and performs semantic retrieval of relevant information based on user queries.
    *   **LLMResponseAgent**: Formulates the final query to the Language Model, incorporating retrieved context, and generates the ultimate answer to the user.

3.  **Model Context Protocol (MCP)**:
    All inter-agent communication and agent-to-LLM interactions are facilitated through a structured, MCP-like context protocol. This ensures clear, standardized message passing throughout the system. An example message structure is:
    ```json
    {
        "sender": "RetrievalAgent",
        "receiver": "LLMResponseAgent",
        "type": "CONTEXT_RESPONSE",
        "trace_id": "abc-123",
        "payload": {
            "top_chunks": ["...", "..."],
            "query": "What are the KPIs?"
        }
    }
    ```
    The current implementation uses in-memory messaging for MCP.

4.  **Vector Store + Embeddings**:
    *   **Embeddings**: The project utilizes `sentence-transformers` (specifically `all-MiniLM-L6-v2`) for generating document and query embeddings.
    *   **Vector Database**: [FAISS](https://github.com/facebookresearch/faiss) is employed as the vector store for efficient storage and retrieval of document embeddings.

5.  **Chatbot Interface (UI)**:
    A user-friendly web interface is provided, built with Flask, allowing users to:
    *   Upload documents.
    *   Ask multi-turn questions.
    *   View responses along with the source context from which the information was retrieved.

## Features

*   **Document Ingestion**: Upload and process PDF, DOCX, PPTX, CSV, TXT, and MD files.
*   **FAISS Vector Store**: Efficiently store and retrieve document embeddings for RAG.
*   **Local LLM Integration**: Utilizes a local Llama model for natural language understanding and generation.
*   **Retrieval Augmented Generation (RAG)**: Enhances LLM responses with relevant information extracted from uploaded documents.
*   **Chat Interface**: Provides a web-based interface for interacting with the chatbot.
*   **Conversation History**: Maintains a history of chat interactions.
*   **System Statistics**: Provides insights into the vector store and conversation count.

## Technologies Used

*   **Backend**: Flask
*   **Vector Store**: FAISS
*   **LLM**: Llama (via `llama-cpp-python`)
*   **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`)
*   **Document Parsing**: PyPDF2, python-docx, python-pptx, pandas
*   **Other Libraries**: Flask-CORS, Werkzeug

## Installation

To set up the project locally, follow these steps:

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/Bhanuprakashgu/Agentic-RAG-Chatbot
    cd rag_chatbot_project
    ```

2.  **Create a virtual environment** (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Download the Llama model**:

    The `LLMResponseAgent` expects a Llama GGUF model file. By default, it looks for `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` in `~/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/`. You can download this model or any other compatible Llama GGUF model and place it in the specified path or update `src/config.py` and `src/agents/llm_response_agent.py` to point to your model's location.

    Example download (using `wget` for TinyLlama):

    ```bash
    mkdir -p ~/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/
    wget -O ~/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
    ```

## Usage

1.  **Run the Flask application**:

    ```bash
    python3 src/app.py
    ```

    The application will start on `http://localhost:5000`.

2.  **Access the Chatbot**: Open your web browser and navigate to `http://localhost:5000`.

3.  **Upload Documents**: Use the provided interface to upload documents (PDF, DOCX, PPTX, CSV, TXT, MD). These documents will be processed and indexed for RAG.

4.  **Chat with the Bot**: Type your queries into the chat interface. The bot will respond using the local LLM, potentially leveraging the uploaded documents for context.

## API Endpoints

The Flask application exposes the following API endpoints:

*   `POST /api/chatbot/upload`: Upload a document for processing.
    *   **Request Body**: `multipart/form-data` with a `file` field.
    *   **Response**: JSON object indicating success/failure, filename, metadata, and trace ID.

*   `POST /api/chatbot/chat`: Send a message to the chatbot.
    *   **Request Body**: JSON object with `message` (string) and optional `use_rag` (boolean, default `true`).
    *   **Response**: JSON object with `response` (string), `sources` (array of objects), `query` (string), and `trace_id`.

*   `GET /api/chatbot/history`: Retrieve the conversation history.
    *   **Response**: JSON object with `history` (array of conversation records).

*   `GET /api/chatbot/stats`: Get system statistics (vector store info, conversation count).
    *   **Response**: JSON object with `vector_store` and `conversation_count`.

*   `POST /api/chatbot/clear`: Clear the conversation history.
    *   **Response**: JSON object indicating success.

## Project Structure

```
rag_chatbot_project/
├── requirements.txt
└── src/
    ├── __init__.py
    ├── app.py
    ├── config.py
    ├── agents/
    │   ├── __init__.py
    │   ├── llm_response_agent.py
    │   └── mcp.py
    ├── document_processors/
    │   ├── __init__.py
    │   ├── all_parsers.py
    │   ├── csv_parser.py
    │   ├── docx_parser.py
    │   ├── md_parser.py
    │   ├── pdf_parser.py
    │   ├── pptx_parser.py
    │   └── txt_parser.py
    ├── routes/
    │   ├── __init__.py
    │   └── chatbot.py
    ├── static/
    │   └── (frontend files like index.html, CSS, JS)
    ├── test_documents/
    │   └── (sample documents for testing)
    ├── uploads/
    │   └── (uploaded documents will be stored here)
    └── vector_store/
        ├── __init__.py
        └── faiss_store.py
```

## Sample Workflow (Message Passing with MCP)

This section illustrates a typical interaction flow within the RAG chatbot, highlighting the message passing between agents using the Model Context Protocol (MCP).

**Scenario**: User uploads `sales_review.pdf` and `metrics.csv`, then asks: "What KPIs were tracked in Q1?"

1.  **User Interaction**: The user uploads documents and submits a query via the UI.

2.  **UI to CoordinatorAgent**: The UI forwards the user's query to an internal `CoordinatorAgent` (represented by `LocalCoordinator` in `src/routes/chatbot.py`).

3.  **CoordinatorAgent Orchestration**:
    *   **Ingestion**: The `CoordinatorAgent` triggers the `IngestionAgent` (implicitly handled by `process_document` and `document_processors` in the current structure) to parse and preprocess the uploaded documents. These documents are then chunked and indexed into the FAISS vector store.
    *   **Retrieval**: For the user's query, the `CoordinatorAgent` initiates the `RetrievalAgent` (represented by `FAISSVectorStore` in `src/routes/chatbot.py`) to find relevant chunks from the indexed documents. This involves embedding the query and performing a semantic search against the vector store.

4.  **RetrievalAgent to LLMResponseAgent (MCP Message)**:
    The `RetrievalAgent` constructs an MCP message containing the retrieved context and the original query, then sends it to the `LLMResponseAgent`. An example of such a message:
    ```json
    {
        "type": "RETRIEVAL_RESULT",
        "sender": "RetrievalAgent",
        "receiver": "LLMResponseAgent",
        "trace_id": "rag-457",
        "payload": {
            "retrieved_context": ["slide 3: revenue up", "doc: Q1 summary..."],
            "query": "What KPIs were tracked in Q1?"
        }
    }
    ```

5.  **LLMResponseAgent Processing**:
    The `LLMResponseAgent` receives the MCP message. It then formulates a comprehensive prompt for the local Llama LLM, incorporating the user's query and the `retrieved_context`. The LLM generates an answer based on this augmented prompt.

6.  **Chatbot Response**: The `LLMResponseAgent` returns the generated answer and the source information to the `CoordinatorAgent`, which then sends it back to the UI. The chatbot displays the answer to the user, along with details about the source chunks used.

## Configuration

The `src/config.py` file contains important configuration settings:

*   `UPLOAD_FOLDER`: Directory for uploaded files.
*   `MAX_CONTENT_LENGTH`: Maximum allowed file size for uploads.
*   `ALLOWED_EXTENSIONS`: Supported file types for ingestion.
*   `CHUNK_SIZE`, `CHUNK_OVERLAP`: Parameters for document chunking.
*   `TOP_K_CHUNKS`: Number of top relevant chunks to retrieve for RAG.
*   `FAISS_INDEX_PATH`, `FAISS_META_PATH`: Paths for saving and loading the FAISS index.
*   `EMBEDDING_MODEL`: Name of the Sentence Transformer model used for embeddings.
*   `LLAMA_MODEL_PATH`: Path to the local Llama GGUF model.

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details (assuming an MIT license, if not, this should be updated).

## Acknowledgements

*   [Flask](https://flask.palletsprojects.com/)
*   [FAISS](https://github.com/facebookresearch/faiss)
*   [Llama.cpp](https://github.com/ggerganov/llama.cpp)
*   [Hugging Face Transformers](https://huggingface.co/docs/transformers/index)

---

*README generated by Manus AI.*

