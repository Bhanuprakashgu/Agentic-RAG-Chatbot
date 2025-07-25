import os
import uuid
import logging
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from config import Config
from vector_store.faiss_store import FAISSVectorStore
from agents.llm_response_agent import LLMResponseAgent
from agents.mcp import MCPMessage, generate_trace_id

logger = logging.getLogger(__name__)
chatbot_bp = Blueprint('chatbot', __name__)


class LocalCoordinator:
    def __init__(self):
        self.llm = LLMResponseAgent()
        self.vector_store = FAISSVectorStore()
        self.conversation_history = []

        vector_store_path = Config.FAISS_INDEX_PATH
        if os.path.exists(f"{vector_store_path}.pkl"):
            self.vector_store.load(vector_store_path)
            logger.info("✅ Vector store loaded successfully.")

    def process_document(self, file_path, file_name):
        try:
            trace_id = generate_trace_id("ingest")

            from document_processors.all_parsers import get_parser
            parser = get_parser(file_name.split('.')[-1].lower())
            if not parser:
                raise ValueError("Unsupported file type")

            parsed_data = parser.parse(file_path)
            chunks = parsed_data["chunks"]
            metadata = parsed_data["metadata"]

            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                meta = metadata.copy()
                meta.update({
                    "file_name": file_name,
                    "chunk_id": i,
                    "file_type": file_name.split('.')[-1],
                    "chunk_text": chunk[:100] + "..." if len(chunk) > 100 else chunk
                })
                chunk_metadata.append(meta)

            self.vector_store.add_documents(chunks, chunk_metadata)
            self.vector_store.save(Config.FAISS_INDEX_PATH)

            return {
                "status": "success",
                "message": f"Document {file_name} processed and indexed.",
                "trace_id": trace_id,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ Document processing error: {e}")
            return {"status": "error", "message": str(e), "trace_id": None}

    def process_query(self, query, use_rag=True):
        try:
            trace_id = generate_trace_id("chat")

            if use_rag:
                results = self.vector_store.search(query, top_k=Config.TOP_K_CHUNKS)
                results = [r for r in results if r["score"] > 0.4]

                chunks = [r["text"] for r in results]

                source_info = [
                    {
                        "file_name": r["metadata"].get("file_name", "unknown"),
                        "file_type": r["metadata"].get("file_type", "txt"),
                        "score": round(r["score"], 3),
                        "context_number": i + 1
                    }
                    for i, r in enumerate(results)
                ]

                mcp_msg = MCPMessage(
                    msg_type="RETRIEVAL_RESULT",
                    sender="RetrievalAgent",
                    receiver="LLMResponseAgent",
                    trace_id=trace_id,
                    payload={
                        "retrieved_context": chunks,
                        "query": query,
                        "source_info": source_info
                    }
                )
                response_text, sources_used = self.llm.generate_response_from_message(mcp_msg)
            else:
                chunks, source_info = self.llm.load_default_documents()
                response_text, sources_used = self.llm.generate_response(query, chunks, source_info)

            record = {
                "trace_id": trace_id,
                "query": query,
                "response": response_text,
                "sources": sources_used
            }
            self.conversation_history.append(record)
            return {"status": "success", **record}

        except Exception as e:
            logger.error(f"❌ Error in query processing: {e}")
            return {"status": "error", "message": str(e), "trace_id": None}

    def get_conversation_history(self):
        return self.conversation_history

    def get_system_stats(self):
        try:
            return {
                "vector_store": self.vector_store.get_stats(),
                "conversation_count": len(self.conversation_history)
            }
        except Exception as e:
            return {"error": str(e)}


coordinator = LocalCoordinator()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@chatbot_bp.route('/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not supported. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'}), 400

        filename = secure_filename(file.filename)
        upload_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(upload_path)

        result = coordinator.process_document(upload_path, filename)
        if result['status'] == 'success':
            return jsonify({
                'message': result['message'],
                'filename': filename,
                'metadata': result.get('metadata', {}),
                'trace_id': result['trace_id']
            }), 200
        else:
            return jsonify({'error': result['message']}), 500

    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        query = data['message']
        use_rag = data.get('use_rag', True)

        result = coordinator.process_query(query, use_rag)
        if result['status'] == 'success':
            return jsonify({
                'response': result['response'],
                'sources': result.get('sources', []),
                'query': result['query'],
                'trace_id': result['trace_id']
            }), 200
        else:
            return jsonify({'error': result['message']}), 500

    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/history', methods=['GET'])
def get_history():
    try:
        return jsonify({'history': coordinator.get_conversation_history()}), 200
    except Exception as e:
        logger.error(f"❌ History error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        return jsonify(coordinator.get_system_stats()), 200
    except Exception as e:
        logger.error(f"❌ Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/clear', methods=['POST'])
def clear_history():
    try:
        coordinator.conversation_history.clear()
        return jsonify({'message': 'Conversation history cleared.'}), 200
    except Exception as e:
        logger.error(f"❌ Clear history error: {str(e)}")
        return jsonify({'error': str(e)}), 500