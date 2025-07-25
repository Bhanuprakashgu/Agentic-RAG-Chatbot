import os
import uuid
import logging
import re
from typing import List, Dict
from llama_cpp import Llama

from agents.mcp import MCPMessage, generate_trace_id

logger = logging.getLogger(__name__)


class LLMResponseAgent:
    def __init__(self):
        self.name = "LLMResponseAgent"

        # Set model file path (adjust if your model is in a different location)
        self.model_path = os.path.expanduser(
            "~/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/"
        )
        self.model_file = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

        full_model_path = None
        for root, _, files in os.walk(self.model_path):
            for file in files:
                if file == self.model_file:
                    full_model_path = os.path.join(root, file)
                    break

        if not full_model_path:
            raise FileNotFoundError("Model GGUF file not found.")

        self.llm = Llama(
            model_path=full_model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0
        )

    def load_default_documents(self) -> tuple:
        context = []
        source_info = []
        doc_folder = "./data"

        if not os.path.exists(doc_folder):
            return context, source_info

        seen = set()
        for idx, file_name in enumerate(os.listdir(doc_folder)):
            if file_name.endswith((".txt", ".md", ".csv")):
                full_path = os.path.join(doc_folder, file_name)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        context.append(content[:3000])
                        if file_name not in seen:
                            source_info.append({
                                "file_name": file_name,
                                "file_type": file_name.split(".")[-1],
                                "score": 0.5,
                                "context_number": idx + 1
                            })
                            seen.add(file_name)
                except Exception as e:
                    logger.error(f"Failed to load {file_name}: {e}")

        return context, source_info

    def format_response_with_newlines(self, text: str) -> str:
        """
        Post-process the LLM response to ensure proper newlines for numbered and bulleted lists.
        """
        # Add newlines before numbered points (1., 2., 3., etc.)
        text = re.sub(r'(\d+\.\s)', r'\n\1', text)
        
        # Add newlines before bullet points (•, -, *)
        text = re.sub(r'([•\-\*]\s)', r'\n\1', text)
        
        # Clean up multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading newline if present
        text = text.lstrip('\n')
        
        return text

    def generate_response(self, query: str, context: List[str], source_info: List[Dict]) -> tuple:
        context_text = "\n\n".join([f"[Context {i+1}]\n{ctx}" for i, ctx in enumerate(context)]) if context else ""

        prompt = f"""<|system|>
You are an exceptionally effective and intelligent AI assistant, designed to provide comprehensive, accurate, and well-structured answers. Your primary goal is to deliver responses that not only match but *exceed* the quality and helpfulness of leading AI chatbots like OpenAI's models.

**Core Directives:**
1. **Strictly Context-Bound:** Answer questions *only* using the information provided in the <context> section. Do not introduce outside knowledge.
2. **Information Gaps:** If the answer cannot be found within the provided context, state clearly: "I don't have that information in the provided documents."
3. **Clarity & Conciseness:** Be comprehensive in your answers, but avoid verbosity. Get straight to the point while ensuring all aspects of the query are addressed.
4. **Professional Tone:** Maintain a helpful, professional, and engaging conversational tone.

**Critical Formatting Requirements:**
- When listing multiple points or features, ALWAYS put each numbered item (1., 2., 3., etc.) on a NEW LINE
- When using bullet points (•, -, *), ALWAYS put each bullet point on a NEW LINE
- Use proper line breaks to separate different sections of your response
- Make your responses easy to read and well-structured

**Quality Standards:**
- Provide accurate, detailed answers based on the context
- Include relevant examples or specifics from the documents when available
- If the context contains partial information, acknowledge what you know and what might be missing
- Cross-reference information from multiple sources in the context when relevant
- Ensure your response directly addresses the user's question

**Response Structure:**
1. Start with a direct answer to the main question
2. Provide supporting details from the context
3. If applicable, organize information in clear numbered lists or bullet points (each on a new line)
4. End with any relevant additional context or clarifications

Remember: Your responses should be informative, well-structured, and formatted for easy reading. Each numbered point or bullet point must be on its own line.

<context>
{context_text}
</context>

<|user|>
{query}

<|assistant|>"""

        try:
            result = self.llm(prompt, max_tokens=512, stop=["<|user|>"])
            text = result["choices"][0]["text"].strip()
            if not text:
                raise ValueError("Empty response from LLM.")
            
            # Apply post-processing to ensure proper newlines
            text = self.format_response_with_newlines(text)
            
        except Exception as e:
            logger.warning(f"LLM error: {e}")
            text = "Sorry, I couldn't generate a valid response."

        seen = set()
        sources = []
        for i, info in enumerate(source_info):
            file_name = info.get("file_name", "unknown")
            if file_name not in seen:
                sources.append({
                    "file_name": file_name,
                    "file_type": info.get("file_type", "unknown"),
                    "relevance_score": round(info.get("score", 0), 3),
                    "context_number": i + 1
                })
                seen.add(file_name)

        return text, sources

    def generate_response_from_message(self, mcp_msg: Dict) -> tuple:
        query = mcp_msg["payload"].get("query")
        context = mcp_msg["payload"].get("retrieved_context", [])
        source_info = mcp_msg["payload"].get("source_info", [])

        return self.generate_response(query, context, source_info)