import uuid
from enum import Enum

def generate_trace_id(prefix="rag"):
    return f"{prefix}-{str(uuid.uuid4())[:8]}"

class MCPMessageType(str, Enum):
    INGESTION_RESULT = "INGESTION_RESULT"
    RETRIEVAL_RESULT = "RETRIEVAL_RESULT"
    RESPONSE_RESULT = "RESPONSE_RESULT"

def MCPMessage(msg_type, sender, receiver, trace_id, payload):
    return {
        "type": msg_type,
        "sender": sender,
        "receiver": receiver,
        "trace_id": trace_id,
        "payload": payload
    }
