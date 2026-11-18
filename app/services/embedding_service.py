"""Multi-tier semantic vector embedding service (Gemini Cloud / Ollama / Local CPU ONNX / Deterministic Hash)."""

from __future__ import annotations

import hashlib
import logging
import os
import pathlib
import re
import tarfile
import threading
from typing import Any

import numpy as np

from app.constants import DATA_DIR
from app.utils import tr_lower

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384

MODEL_GEMINI = "gemini-embedding-001"
MODEL_OLLAMA = "ollama-embed-384"
MODEL_ONNX = "onnx-minilm-l6-v2"
MODEL_HASH = "hash-v1"


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
    norm = float(np.linalg.norm(arr))
    if norm < 1e-12:
        return arr.tolist()
    return (arr / norm).tolist()


def cosine_similarity(vec_a: list[float] | np.ndarray, vec_b: list[float] | np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.asarray(vec_a, dtype=np.float32)
    b = np.asarray(vec_b, dtype=np.float32)
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _project_to_dim(vec: np.ndarray, target_dim: int = EMBEDDING_DIM) -> np.ndarray:
    """Deterministically adapt any embedding vector dimension to ``target_dim`` and L2-normalize."""
    arr = np.asarray(vec, dtype=np.float32).reshape(-1)
    cur_dim = arr.shape[0]
    if cur_dim == 0:
        return np.zeros(target_dim, dtype=np.float32)
    if cur_dim == target_dim:
        out = arr
    elif cur_dim > target_dim:
        # Matryoshka-compatible prefix slice + folded residual energy
        out = arr[:target_dim].copy()
        rem = arr[target_dim:]
        for i in range(rem.shape[0]):
            out[i % target_dim] += 0.25 * rem[i]
    else:
        out = np.zeros(target_dim, dtype=np.float32)
        out[:cur_dim] = arr

    norm = float(np.linalg.norm(out))
    if norm > 1e-12:
        out = out / norm
    return out


class EmbeddingService:
    """Provides 3-tier neural vector embeddings and deterministic fallback similarity math."""

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.dim = dim
        self._onnx_lock = threading.Lock()
        self._onnx_checked = False
        self._onnx_session: Any = None
        self._onnx_tokenizer: Any = None

    def _locate_onnx_dir(self) -> pathlib.Path | None:
        """Locate local 384-dim ONNX transformer weights on disk without requiring network access."""
        candidates = [
            pathlib.Path(DATA_DIR) / "models" / "onnx",
            pathlib.Path.home() / ".cache" / "chroma" / "onnx_models" / "all-MiniLM-L6-v2" / "onnx",
        ]
        for folder in candidates:
            if (folder / "model.onnx").is_file() and (folder / "tokenizer.json").is_file():
                return folder

        # Auto-extract Chroma's cached onnx.tar.gz if present but not yet unpacked
        tar_path = (
            pathlib.Path.home()
            / ".cache"
            / "chroma"
            / "onnx_models"
            / "all-MiniLM-L6-v2"
            / "onnx.tar.gz"
        )
        if tar_path.is_file():
            target_parent = tar_path.parent
            try:
                with tarfile.open(tar_path, "r:gz") as tf:
                    for member in tf.getmembers():
                        member_path = (target_parent / member.name).resolve()
                        if not str(member_path).startswith(str(target_parent.resolve())):
                            raise ValueError("Unsafe tar member path")
                    tf.extractall(path=target_parent)
                extracted = target_parent / "onnx"
                if (extracted / "model.onnx").is_file() and (extracted / "tokenizer.json").is_file():
                    return extracted
            except Exception as tar_err:
                logger.debug("ONNX tar extraction skipped: %s", tar_err)
        return None

    def _ensure_onnx_model(self) -> bool:
        """Lazily initialize CPU ONNX Runtime session and Rust tokenizer."""
        if self._onnx_checked:
            return self._onnx_session is not None and self._onnx_tokenizer is not None

        with self._onnx_lock:
            if self._onnx_checked:
                return self._onnx_session is not None and self._onnx_tokenizer is not None
            self._onnx_checked = True
            if os.environ.get("DISABLE_ONNX_EMBEDDINGS") == "1":
                return False

            model_dir = self._locate_onnx_dir()
            if model_dir is None:
                return False

            try:
                import onnxruntime as ort  # type: ignore
                from tokenizers import Tokenizer  # type: ignore

                sess_opts = ort.SessionOptions()
                sess_opts.intra_op_num_threads = min(4, max(1, (os.cpu_count() or 2) // 2))
                sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

                tok = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
                tok.enable_truncation(max_length=256)
                tok.enable_padding(pad_id=0, pad_token="[PAD]")

                sess = ort.InferenceSession(
                    str(model_dir / "model.onnx"),
                    sess_options=sess_opts,
                    providers=["CPUExecutionProvider"],
                )
                self._onnx_tokenizer = tok
                self._onnx_session = sess
                return True
            except Exception as onnx_err:
                logger.debug("Local ONNX embedding initialization unavailable: %s", onnx_err)
                self._onnx_tokenizer = None
                self._onnx_session = None
                return False

    def active_local_model_id(self) -> str:
        """Return the identifier of the active local offline embedding engine."""
        return MODEL_ONNX if self._ensure_onnx_model() else MODEL_HASH

    def generate_hash_embedding(self, text: str) -> list[float]:
        """Generate a deterministic 384-dim subword + word-bigram feature hash vector."""
        if not text or not text.strip():
            return [0.0] * self.dim

        vec = np.zeros(self.dim, dtype=np.float32)
        words = re.findall(r"\w+", tr_lower(text), flags=re.UNICODE)
        if not words:
            return [0.0] * self.dim

        for idx_w, word in enumerate(words):
            h_word = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h_word % self.dim
            sign = 1.0 if ((h_word >> 8) & 1) else -1.0
            vec[idx] += sign

            if len(word) >= 3:
                for i in range(len(word) - 2):
                    ngram = word[i : i + 3]
                    h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    ng_idx = h_ng % self.dim
                    ng_sign = 0.5 if ((h_ng >> 8) & 1) else -0.5
                    vec[ng_idx] += ng_sign

            if idx_w + 1 < len(words):
                bigram = f"{word}_{words[idx_w + 1]}"
                h_bg = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
                bg_idx = h_bg % self.dim
                bg_sign = 0.35 if ((h_bg >> 8) & 1) else -0.35
                vec[bg_idx] += bg_sign

        norm = float(np.linalg.norm(vec))
        if norm > 1e-12:
            vec = vec / norm
        return vec.tolist()

    def generate_onnx_embeddings_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]] | None:
        """Encode a batch of texts into 384-dim L2-normalized vectors using local CPU ONNX."""
        if not self._ensure_onnx_model():
            return None
        if not texts:
            return []

        results: list[list[float]] = []
        try:
            input_names = {inp.name for inp in self._onnx_session.get_inputs()}
            for start in range(0, len(texts), max(1, batch_size)):
                sub = [t.strip() if t and t.strip() else " " for t in texts[start : start + batch_size]]
                encodings = self._onnx_tokenizer.encode_batch(sub)
                ids = np.array([e.ids for e in encodings], dtype=np.int64)
                mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
                feeds: dict[str, Any] = {"input_ids": ids, "attention_mask": mask}
                if "token_type_ids" in input_names:
                    feeds["token_type_ids"] = np.zeros_like(ids)

                token_embeddings = self._onnx_session.run(None, feeds)[0]
                mask_exp = np.expand_dims(mask, -1).astype(np.float32)
                summed = np.sum(token_embeddings * mask_exp, axis=1)
                counts = np.clip(mask_exp.sum(axis=1), 1e-9, None)
                pooled = summed / counts

                for row_idx, raw_t in enumerate(texts[start : start + batch_size]):
                    if not raw_t or not raw_t.strip():
                        results.append([0.0] * self.dim)
                    else:
                        proj = _project_to_dim(pooled[row_idx], self.dim)
                        results.append(proj.tolist())
            return results
        except Exception as run_err:
            logger.debug("Local ONNX batch embedding failed: %s", run_err)
            return None

    def generate_onnx_embedding(self, text: str) -> list[float] | None:
        """Encode a single text string using local CPU ONNX."""
        if not text or not text.strip():
            return [0.0] * self.dim
        batch = self.generate_onnx_embeddings_batch([text], batch_size=1)
        if batch and len(batch) == 1:
            return batch[0]
        return None

    def generate_gemini_embeddings_batch(
        self,
        texts: list[str],
        api_key: str,
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 64,
    ) -> list[list[float]] | None:
        """Generate 384-dim Matryoshka multilingual embeddings via Google Gemini Embedding API."""
        from app.config import is_real_api_key

        if not is_real_api_key(api_key) or not texts:
            return None

        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore

            client = genai.Client(api_key=api_key)
            all_vecs: list[list[float]] = []

            for start in range(0, len(texts), max(1, batch_size)):
                batch = [
                    (t.strip()[:6000] if t and t.strip() else " ")
                    for t in texts[start : start + batch_size]
                ]
                cfg = types.EmbedContentConfig(
                    output_dimensionality=self.dim,
                    task_type=task_type,
                )
                resp = client.models.embed_content(
                    model=MODEL_GEMINI,
                    contents=batch,
                    config=cfg,
                )
                emb_items = getattr(resp, "embeddings", None) or []
                if len(emb_items) != len(batch):
                    return None
                for raw_t, emb_obj in zip(texts[start : start + batch_size], emb_items, strict=False):
                    vals = getattr(emb_obj, "values", None)
                    if not raw_t or not raw_t.strip() or not vals:
                        all_vecs.append([0.0] * self.dim)
                    else:
                        all_vecs.append(_project_to_dim(np.asarray(vals, dtype=np.float32), self.dim).tolist())
            return all_vecs
        except Exception as gem_err:
            logger.debug("Gemini embedding batch fallback triggered: %s", gem_err)
            return None

    def generate_ollama_embeddings_batch(
        self,
        texts: list[str],
        base_url: str,
        embed_model: str = "nomic-embed-text",
    ) -> list[list[float]] | None:
        """Generate embeddings via local Ollama / OpenAI-compatible embedding endpoint."""
        if not texts:
            return None
        clean_url = (base_url or "http://localhost:11434/v1").strip().rstrip("/")
        if not clean_url.startswith(("http://", "https://")) or "169.254.169.254" in clean_url:
            return None

        try:
            import httpx

            openai_url = (
                f"{clean_url}/embeddings"
                if clean_url.endswith("/v1")
                else f"{clean_url}/v1/embeddings"
            )
            payload_inputs = [t.strip()[:4000] if t and t.strip() else " " for t in texts]
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(
                    openai_url,
                    json={"model": embed_model, "input": payload_inputs},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data") or []
                    if len(data) == len(texts):
                        out: list[list[float]] = []
                        for raw_t, item in zip(texts, data, strict=False):
                            vec = item.get("embedding") or []
                            if not raw_t or not raw_t.strip() or not vec:
                                out.append([0.0] * self.dim)
                            else:
                                out.append(_project_to_dim(np.asarray(vec, dtype=np.float32), self.dim).tolist())
                        return out
        except Exception as ol_err:
            logger.debug("Local HTTP embedding endpoint unavailable: %s", ol_err)
        return None

    def generate_embedding(self, text: str) -> list[float]:
        """Generate a dense normalized 384-dimensional vector embedding on CPU (ONNX or hash fallback)."""
        if not text or not text.strip():
            return [0.0] * self.dim

        onnx_vec = self.generate_onnx_embedding(text)
        if onnx_vec is not None:
            return onnx_vec
        return self.generate_hash_embedding(text)

    def generate_embedding_blob(self, text: str) -> bytes:
        """Generate embedding and immediately serialize to SQLite BLOB bytes."""
        vec = self.generate_embedding(text)
        return serialize_vector(vec)

    def generate_embeddings_batch(self, texts: list[str]) -> list[bytes]:
        """Generate serialized float32 BLOB embeddings for a batch of chunk texts on local CPU."""
        if not texts:
            return []
        onnx_vecs = self.generate_onnx_embeddings_batch(texts)
        if onnx_vecs is not None:
            return [serialize_vector(v) for v in onnx_vecs]
        return [serialize_vector(self.generate_hash_embedding(t)) for t in texts]

    def generate_semantic_embeddings_batch(
        self,
        texts: list[str],
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> tuple[list[bytes], str]:
        """Generate best-tier semantic embeddings (Gemini -> Ollama -> Local ONNX -> Hash) and return ``(blobs, model_id)``."""
        if not texts:
            return [], self.active_local_model_id()

        from app.config import is_real_api_key, load_config, resolve_ai_credentials

        cfg = load_config()
        eff_provider, eff_key, _, eff_url = resolve_ai_credentials(
            provider=provider,
            api_key=api_key,
            model=None,
            base_url=base_url,
            cfg=cfg,
            is_key_fn=is_real_api_key,
        )

        if eff_provider == "gemini" and is_real_api_key(eff_key):
            gem_vecs = self.generate_gemini_embeddings_batch(
                texts, eff_key, task_type="RETRIEVAL_DOCUMENT"
            )
            if gem_vecs is not None and len(gem_vecs) == len(texts):
                return [serialize_vector(v) for v in gem_vecs], MODEL_GEMINI

        if eff_provider in ("ollama", "lmstudio"):
            ol_vecs = self.generate_ollama_embeddings_batch(texts, eff_url or "")
            if ol_vecs is not None and len(ol_vecs) == len(texts):
                return [serialize_vector(v) for v in ol_vecs], MODEL_OLLAMA

        onnx_vecs = self.generate_onnx_embeddings_batch(texts)
        if onnx_vecs is not None and len(onnx_vecs) == len(texts):
            return [serialize_vector(v) for v in onnx_vecs], MODEL_ONNX

        return [serialize_vector(self.generate_hash_embedding(t)) for t in texts], MODEL_HASH

    def embed_query_for_model(
        self,
        query: str,
        model_id: str | None = None,
        api_key: str = "",
        base_url: str = "",
    ) -> list[float]:
        """Embed a search query in the exact vector space matching ``model_id``."""
        if not query or not query.strip():
            return [0.0] * self.dim

        target = (model_id or "").strip() or self.active_local_model_id()
        if target == MODEL_GEMINI:
            from app.config import is_real_api_key, load_config

            eff_key = api_key
            if not is_real_api_key(eff_key):
                cfg = load_config()
                eff_key = str(cfg.get("ai_api_key") or os.environ.get("GEMINI_API_KEY") or "").strip()
            if is_real_api_key(eff_key):
                gem = self.generate_gemini_embeddings_batch(
                    [query], eff_key, task_type="RETRIEVAL_QUERY", batch_size=1
                )
                if gem and len(gem) == 1:
                    return gem[0]
            return self.generate_embedding(query)

        if target == MODEL_OLLAMA:
            from app.config import load_config

            eff_url = base_url or str(load_config().get("ai_base_url") or "")
            ol = self.generate_ollama_embeddings_batch([query], eff_url)
            if ol and len(ol) == 1:
                return ol[0]
            return self.generate_embedding(query)

        if target == MODEL_ONNX:
            onnx_v = self.generate_onnx_embedding(query)
            if onnx_v is not None:
                return onnx_v
            return self.generate_hash_embedding(query)

        return self.generate_hash_embedding(query)


# Global singleton instance
embedding_service = EmbeddingService()
