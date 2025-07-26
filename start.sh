#!/bin/bash

echo "📦 Checking model directory..."

MODEL_FILE="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_PATH=$(find "$HOME/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots" -name "$MODEL_FILE" | head -n 1)

if [ -z "$MODEL_PATH" ]; then
    echo "❌ Model file not found!"
    echo "⬇️ Downloading TinyLLaMA model from Hugging Face..."

    mkdir -p "$HOME/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots"

    wget -O "$HOME/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/$MODEL_FILE" \
        "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/$MODEL_FILE"
else
    echo "✅ Model found at: $MODEL_PATH"
fi

echo "🚀 Starting the RAG chatbot server..."
python src/app.py
