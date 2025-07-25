import os

class Config:
    # File Upload Settings
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "csv", "txt", "md"}

    # Chunking for document ingestion
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # Retrieval Settings
    TOP_K_CHUNKS = 3

    # FAISS Vector Store Paths
    FAISS_INDEX_PATH = "vector_store/faiss_index.index"
    FAISS_META_PATH = "vector_store/faiss_index.pkl"

    # Embedding Model (used with SentenceTransformer)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # ✅ LLaMA Model Path
    LLAMA_MODEL_PATH = "models/llama-2-7b-chat.Q4_K_M.gguf"
