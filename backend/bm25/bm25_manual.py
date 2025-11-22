# backend/bm25/bm25_manual.py

from collections import Counter
import math
import re
import csv
import argparse
import os
import sys

# Increase CSV field size (Windows-safe)
csv.field_size_limit(2**31 - 1)

# ----------------------------
# Tokenizer
# ----------------------------
TOKEN_RE = re.compile(r"\b\w+\b")
def tokenize(text):
    return TOKEN_RE.findall(text.lower())

# ----------------------------
# BM25 class
# ----------------------------
class BM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.N = len(corpus)
        self.doc_lens = [len(tokenize(doc)) for doc in corpus]
        self.avgdl = sum(self.doc_lens) / self.N
        self.df = self._doc_freqs()

    def _doc_freqs(self):
        df = {}
        for doc in self.corpus:
            tokens = set(tokenize(doc))
            for t in tokens:
                df[t] = df.get(t, 0) + 1
        return df

    def score(self, query, doc):
        score = 0.0
        doc_tokens = tokenize(doc)
        doc_len = len(doc_tokens)
        frequencies = Counter(doc_tokens)

        for word in tokenize(query):
            if word not in self.df:
                continue

            df = self.df[word]
            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))

            tf = frequencies[word]
            denom = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)

            score += idf * ((tf * (self.k1 + 1)) / denom)

        return score


# -------------------------
# ----- LOAD CSV DATA -----
# -------------------------

csv_file_path = os.path.join(os.path.dirname(__file__), "travel_blogs.csv")

posts = []
corpus = []

with open(csv_file_path, newline = "", encoding = "utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        posts.append(row)
        corpus.append(f"{row['page_title']} {row['content']}")


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


    # Create BM25 object
    bm25 = BM25(corpus)

    # Return bm25 scores for the query
    scores = [(doc, bm25.score(args.query, doc)) for doc in corpus]

    # Get the top_n closely related blogs
    ranked = sorted(scores, key = lambda x: x[1], reverse = True)[:args.top]


    # ------------------------
    # ----- WRITE TO CSV -----
    # ------------------------
    output_file = "bm25_top_locations_manual.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Score", "Location Name", "Page Title", "Longitude", "Latitude"])
        
        for doc, score in ranked:
            idx = corpus.index(doc)
            writer.writerow([
                score,
                posts[idx]['location_name'],
                posts[idx]['page_title'],
                posts[idx]['longitude'],
                posts[idx]['latitude']
            ])

    print(f"Top {args.top} results written to {output_file}")


"""
STEPS TO RUN:
python bm25_package.py "Kyoto Japan temples" 10 

"""
