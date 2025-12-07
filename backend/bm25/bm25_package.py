# backend/bm25/bm25_package.py

import csv
import re
import argparse
import os
from rank_bm25 import BM25Okapi

# Increase CSV field size (Windows-safe)
csv.field_size_limit(2**31 - 1)


# ---------------------
# ----- TOKENIZER -----
# ---------------------
TOKEN_RE = re.compile(r"\b\w+\b")
def tokenize(text):
    return TOKEN_RE.findall(text.lower())


# --------------------------
# ----- LOAD CSV DATA ------
# --------------------------
csv_file_path = os.path.join(os.path.dirname(__file__), "travel_blogs.csv")

posts = []
corpus = []

with open(csv_file_path, newline = "", encoding = "utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        posts.append(row)
        corpus.append(f"{row['page_title']} {row['content']}")

tokenized_corpus = [tokenize(doc) for doc in corpus]

# Build BM25 index
bm25 = BM25Okapi(tokenized_corpus)


# --------------------------
# ----- MAIN CLI ENTRY -----
# --------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "BM25 search over travel blog posts")

    parser.add_argument("query", 
                        type = str, 
                        help = "Search query")
    
    parser.add_argument("top", 
                        type = int,
                        help = "Number of top results to return")
    
    args = parser.parse_args()

    query = args.query
    top_n = args.top


    # --------------------
    # ----- RUN BM25 -----
    # --------------------

    # Tokenize the inputted query
    tokenized_query = tokenize(query)

    # Return bm25 scores for the query
    scores = bm25.get_scores(tokenized_query)

    # Get the top_n closely related blogs
    ranked_docs = bm25.get_top_n(tokenized_query, corpus, n = top_n)


    # ------------------------
    # ----- WRITE TO CSV -----
    # ------------------------
    output_file = "bm25_top_locations_package.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Score", "Location Name", "Page Title", "Longitude", "Latitude"])
        
        for doc in ranked_docs:
            idx = corpus.index(doc)
            writer.writerow([
                scores[idx],
                posts[idx]['location_name'],
                posts[idx]['page_title'],
                posts[idx]['longitude'],
                posts[idx]['latitude']
            ])

    print(f"Top {top_n} results written to {output_file}")


"""
STEPS TO RUN:
python bm25_package.py "Kyoto Japan temples" 10 

"""