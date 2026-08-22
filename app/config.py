import os
try:
    from dotenv import load_dotenv
except ImportError:  # позволяет запускать базовые unit-тесты до установки зависимостей
    def load_dotenv():
        return False

load_dotenv()

def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
RETRIEVAL_LIMIT = int(os.getenv("RETRIEVAL_LIMIT", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.35"))
RELATIVE_SCORE_MARGIN = float(
    os.getenv("RELATIVE_SCORE_MARGIN", "0.15")
)

RETRIEVAL_INITIAL_LIMIT = int(
    os.getenv("RETRIEVAL_INITIAL_LIMIT", "50")
)

MAX_CHUNKS_PER_DOCUMENT = int(
    os.getenv("MAX_CHUNKS_PER_DOCUMENT", "2")
)
ENABLE_RERANKER = env_bool("ENABLE_RERANKER", False)
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
RERANK_SCORE_THRESHOLD = float(
    os.getenv("RERANK_SCORE_THRESHOLD", "-3.0")
)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))

ADMIN_API_KEY = os.getenv(
    "ADMIN_API_KEY",
    "",
)