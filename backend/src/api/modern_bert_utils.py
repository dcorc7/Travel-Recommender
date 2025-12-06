import torch
from transformers import AutoTokenizer, AutoModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.src.api.bm25_utils import Whole_Blogs
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "nomic-ai/modernbert-embed-base"

# Load model + tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()

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

# Connect to DB
database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

with Session(engine) as session:
    blog_posts = session.query(Whole_Blogs).all()

    for post in tqdm(blog_posts, desc="Embedding blogs"):
        text = f"{post.page_title} {post.page_description} {post.content}"
        emb = embed_texts([text])[0].numpy().tolist()  # convert to list for DB storage
        post.embedding = emb  # assign to the new column

    session.commit()
    print("All embeddings saved to database")
