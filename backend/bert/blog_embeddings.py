'''
Finds top travel destinations based on input query. Code loads blog embeddings and embeds input query.
Performs semantic search to find top travel locations
'''

import torch
from transformers import AutoTokenizer, AutoModel
import faiss
import argparse
import pandas as pd

MODEL_NAME = "nomic-ai/modernbert-embed-base" 
CSV_PATH = "../bm25/travel_blogs.csv"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# -------------------------------------------------------
# LOAD MODEL + TOKENIZER
# -------------------------------------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()

# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------
df = pd.read_csv(CSV_PATH)

# -------------------------------------------------------
# EMBEDDING FUNCTION (Batch optimized)
# -------------------------------------------------------
def embed_texts(texts_batch):
    # Tokenize (handles list of strings automatically)
    encoded = tokenizer(
        texts_batch,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    ).to(DEVICE)

    # Forward pass
    with torch.no_grad():
        outputs = model(**encoded)

    # ModernBERT uses last_hidden_state for embeddings
    last_hidden = outputs.last_hidden_state

    # Mean pooling
    attention_mask = encoded["attention_mask"].unsqueeze(-1)
    sum_embeddings = torch.sum(last_hidden * attention_mask, dim=1)
    sum_mask = torch.sum(attention_mask, dim=1)
    # Clamp sum_mask to avoid division by zero
    sum_mask = torch.clamp(sum_mask, min=1e-9)
    embedding = sum_embeddings / sum_mask
    
    # Normalize embeddings to unit length
    embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)

    return embedding.cpu()

data = torch.load("travel_blog_embeddings.pt", weights_only=True)
emb = data["embeddings"]  # shape (N, 768)

index = faiss.IndexFlatL2(emb.shape[1])
index.add(emb.numpy())

def search_blogs(query, k=5):
    # Pass as a list [query]
    q_emb = embed_texts([query]).numpy()
    distances, idxs = index.search(q_emb, k)
    rows = df.iloc[idxs[0]].copy()
    rows["distance"] = distances[0]
    return rows


# --------------------------
# ----- MAIN CLI ENTRY -----
# --------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "ModernBERT search over travel blog posts")

    parser.add_argument("query", 
                        type = str, 
                        help = "Search query")
    
    parser.add_argument("top", 
                        type = int,
                        help = "Number of top results to return")
    
    args = parser.parse_args()

    query = args.query
    top_n = args.top

    results = search_blogs(query, k=top_n)

    print(f"Search results for: '{query}'\n")
    for i in range(len(results)):
        row = results.iloc[i]
        print(f"Rank {i+1} (Distance: {row['distance']:.4f})")
        
        # Use correct column names from your dataframe
        if 'page_title' in row:
            print(f"Title: {row['page_title']}")
        if 'location_name' in row:
            print(f"Location: {row['location_name']}")
            
        # Print a longer snippet of the content
        content_snippet = str(row['content'])[:300].replace('\n', ' ')
        print(f"Content Snippet: {content_snippet}...\n")
        print("-" * 80)

"""
STEPS TO RUN:
python blog_embeddings.py "mountains in europe" 3 
"""