import logging
from typing import List, Optional, Any
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

class EmbeddingModelError(Exception):
    """Raised when the embedding model fails to initialize or generate embeddings."""
    pass

class EmbeddingService:
    """
    Singleton service manager for dense sentence embeddings.
    Loads and caches SentenceTransformer model once on CPU/GPU,
    avoiding repeated disk/model overhead across API requests.
    """
    _instance: Optional["EmbeddingService"] = None
    _model: Any = None
    _model_name: Optional[str] = None

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION

    @classmethod
    def get_instance(cls, model_name: Optional[str] = None) -> "EmbeddingService":
        target_name = model_name or settings.EMBEDDING_MODEL_NAME
        if cls._instance is None or cls._instance.model_name != target_name:
            cls._instance = cls(model_name=target_name)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resets singleton state for testing purposes."""
        cls._instance = None
        cls._model = None
        cls._model_name = None

    def get_model(self) -> Any:
        if self._model is None or self._model_name != self.model_name:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}")
                try:
                    # Attempt local cached load first to avoid network timeout in offline/sandbox environments
                    self._model = SentenceTransformer(
                        self.model_name,
                        device="cpu",
                        model_kwargs={"local_files_only": True},
                    )
                except Exception:
                    self._model = SentenceTransformer(self.model_name, device="cpu")
                self._model_name = self.model_name
                logger.info(f"SentenceTransformer '{self.model_name}' loaded successfully (dim: {self.dimension})")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model '{self.model_name}': {e}")
                raise EmbeddingModelError(
                    f"SentenceTransformer model '{self.model_name}' could not be loaded: {str(e)}"
                )
        return self._model

    def encode_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Generates normalized dense embeddings for a batch of strings.
        Output vectors have unit length (L2 norm = 1.0) so cosine similarity = dot product.
        """
        if not texts:
            raise EmbeddingModelError("Cannot generate embeddings for empty text input batch.")

        # Validate non-empty content
        cleaned_texts = [t.strip() if t and t.strip() else "" for t in texts]
        if all(not t for t in cleaned_texts):
            raise EmbeddingModelError("Cannot generate embeddings for completely empty text input.")

        model = self.get_model()
        bs = batch_size or settings.EMBEDDING_BATCH_SIZE

        try:
            embeddings = model.encode(
                cleaned_texts,
                batch_size=bs,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            if hasattr(embeddings, "tolist"):
                return embeddings.tolist()
            return [list(map(float, emb)) for emb in embeddings]
        except Exception as e:
            logger.error(f"Error encoding batch with model '{self.model_name}': {e}")
            raise EmbeddingModelError(f"Embedding batch generation failed: {str(e)}")

    def encode_text(self, text: str) -> List[float]:
        """Generates normalized embedding vector for a single string."""
        if not text or not text.strip():
            raise EmbeddingModelError("Cannot generate embedding for empty text input.")
        results = self.encode_texts([text])
        if not results:
            raise EmbeddingModelError("No embedding vector was produced.")
        return results[0]
