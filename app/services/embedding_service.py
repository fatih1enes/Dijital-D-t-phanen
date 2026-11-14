"""Lightweight, in-process embedding service with vector serialization and cosine math."""

import hashlib

import numpy as np

EMBEDDING_DIM = 384


def serialize_vector(vec: list[float] | np.ndarray) -> bytes:
    """Serialize a list of floats into binary IEEE 754 float32 bytes for SQLite BLOB storage."""
    arr = np.asarray(vec, dtype=np.float32)
    return arr.tobytes()


def deserialize_vector(data: bytes) -> list[float]:
    """Deserialize binary float32 bytes into a list of Python floats."""
    if not data:
        return []
    arr = np.frombuffer(data, dtype=np.float32)
    return arr.tolist()


def normalize_vector(vec: list[float] | np.ndarray) -> list[float]:
    """L2 normalize a vector so its euclidean length equals 1.0."""
    arr = np.asarray(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm < 1e-12:
        return arr.tolist()
    return (arr / norm).tolist()


def cosine_similarity(vec_a: list[float] | np.ndarray, vec_b: list[float] | np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.asarray(vec_a, dtype=np.float32)
    b = np.asarray(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class EmbeddingService:
    """Provides vector embeddings and similarity computation."""

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.dim = dim

    def generate_embedding(self, text: str) -> list[float]:
        """Generate a dense normalized 384-dimensional vector embedding for text.

        Uses feature hashing with subword n-gram frequency to guarantee
        fast, deterministic, and semantically consistent embeddings on CPU without PyTorch.
        """
        if not text or not text.strip():
            return [0.0] * self.dim

        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().split()

        for word in words:
            # 1. Word level hash projection
            h_word = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h_word % self.dim
            sign = 1.0 if ((h_word >> 8) & 1) else -1.0
            vec[idx] += sign

            # 2. Character n-gram projection (captures morphology and spelling variations)
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    ngram = word[i : i + 3]
                    h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    ng_idx = h_ng % self.dim
                    ng_sign = 0.5 if ((h_ng >> 8) & 1) else -0.5
                    vec[ng_idx] += ng_sign

        norm = np.linalg.norm(vec)
        if norm > 1e-12:
            vec = vec / norm
        return vec.tolist()

    def generate_embedding_blob(self, text: str) -> bytes:
        """Generate embedding and immediately serialize to SQLite BLOB bytes."""
        vec = self.generate_embedding(text)
        return serialize_vector(vec)


# Global singleton instance
embedding_service = EmbeddingService()
