import os
import torch
from transformers import AutoTokenizer, AutoModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from backend.src.api.bm25_utils import Whole_Blogs, Base
from tqdm import tqdm

load_dotenv()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "nomic-ai/modernbert-embed-base"

# Load ModernBERT
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()

# -----------------------------
# Embed helper
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
# Main embedding script
# -----------------------------
def embed_all_blogs():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with Session(engine) as session:
        blog_posts = session.query(Whole_Blogs).all()

        print(f"Embedding {len(blog_posts)} blog posts...")
        for post in tqdm(blog_posts):
            text = f"{post.page_title} {post.page_description} {post.content}"
            emb = embed_texts([text])[0].numpy().tolist()
            post.embedding = emb

        session.commit()
        print("All embeddings saved to database.")

if __name__ == "__main__":
    embed_all_blogs()
