DEFAULT_MODEL_NAME = "BAAI/bge-base-zh-v1.5"
_MODEL_CACHE = {}


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME):
    """
    Load a sentence-transformers embedding model.

    The first run may download the model to the local Hugging Face cache.
    """
    from sentence_transformers import SentenceTransformer

    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)

    return _MODEL_CACHE[model_name]


def embed_texts(
    texts: list[str],
    model_name: str = DEFAULT_MODEL_NAME,
):
    """
    Convert a list of text chunks into embedding vectors.

    Day 10 baseline:
    texts -> numpy embedding matrix
    """
    if not texts:
        raise ValueError("texts must not be empty")

    model = get_embedding_model(model_name)

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    return embeddings
