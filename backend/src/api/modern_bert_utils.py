import os
import torch
import faiss
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv

load_dotenv()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "nomic-ai/modernbert-embed-base"
EMBEDDINGS_PATH = "../../../backend/bert/travel_blog_embeddings.pt"

# -----------------------------
# Load model + tokenizer
# -----------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()

# -----------------------------
# Database model
# -----------------------------
class Base(DeclarativeBase):
    pass

class Whole_Blogs(Base):
    __tablename__ = "travel_blogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    blog_url: Mapped[str]
    page_url: Mapped[str]
    page_title: Mapped[str]
    page_description: Mapped[str]
    page_author: Mapped[str]
    location_name: Mapped[str]
    latitude: Mapped[float]
    longitude: Mapped[float]
    content: Mapped[str]

# -----------------------------
# Cache
# -----------------------------
_cached_posts = None
_index = None
_embeddings = None

# -----------------------------
# Embed helper for queries only
# -----------------------------
def embed_texts(texts_batch):
    encoded = tokenizer(
        texts_batch,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    ).to(DEVICE)

    with torch.no_grad():
        outputs = model(**encoded)

    last_hidden = outputs.last_hidden_state
    attention_mask = encoded["attention_mask"].unsqueeze(-1)
    sum_embeddings = torch.sum(last_hidden * attention_mask, dim=1)
    sum_mask = torch.sum(attention_mask, dim=1)
    sum_mask = torch.clamp(sum_mask, min=1e-9)
    embedding = sum_embeddings / sum_mask
    embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
    return embedding.cpu()

# -----------------------------
# Load posts and embeddings
# -----------------------------
def _load_posts_and_index():
    global _cached_posts, _index, _embeddings

    if _cached_posts is not None and _index is not None and _embeddings is not None:
        return _cached_posts, _index, _embeddings

    # Load metadata from DB
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    engine = create_engine(database_url)
    with Session(engine) as session:
        _cached_posts = session.query(Whole_Blogs).all()

    # Load precomputed embeddings
    data = torch.load(EMBEDDINGS_PATH, weights_only=True)
    _embeddings = data["embeddings"]

    # Build FAISS index
    _index = faiss.IndexFlatL2(_embeddings.shape[1])
    _index.add(_embeddings.numpy())

    return _cached_posts, _index, _embeddings

# -----------------------------
# Search function
# -----------------------------
def search_modernbert(query: str, top_k: int = 5):
    posts, index, embeddings = _load_posts_and_index()
    if not query.strip():
        return []

    q_emb = embed_texts([query]).numpy()
    distances, idxs = index.search(q_emb, top_k)

    results = []
    for i, idx in enumerate(idxs[0]):
        post = posts[idx]
        content_preview = post.content[:300] + ("..." if len(post.content) > 300 else "")
        location_parts = post.location_name.split(",")
        country = location_parts[-1].strip() if len(location_parts) > 1 else ""
        results.append({
            "destination": post.location_name,
            "country": country,
            "lat": post.latitude,
            "lon": post.longitude,
            "distance": float(distances[0][i]),
            "page_title": post.page_title,
            "page_url": post.page_url,
            "blog_url": post.blog_url,
            "author": post.page_author,
            "description": post.page_description,
            "content_preview": content_preview,
            "full_content": post.content
        })

    return results
