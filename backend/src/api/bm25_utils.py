# backend/src/api/bm25_utils.py

import re
import os
from typing import List, Dict
from rank_bm25 import BM25Okapi
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv
# Import Logger
from .logging_utils import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("bm25_utils")

# Tokenizer
TOKEN_RE = re.compile(r"\b\w+\b")

def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words."""
    if not text:
        return []
    return TOKEN_RE.findall(text.lower())


# Database Model
class Base(DeclarativeBase):
    pass


class Whole_Blogs(Base):
    __tablename__ = "travel_blogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    blog_url: Mapped[str]
    page_url: Mapped[str] = mapped_column(unique=True, nullable=False)
    page_title: Mapped[str]
    page_description: Mapped[str]
    page_author: Mapped[str]
    location_name: Mapped[str]
    latitude: Mapped[float]
    longitude: Mapped[float]
    content: Mapped[str]

    def __repr__(self) -> str:
        return f"Whole_Blogs(id={self.id!r}, location_name={self.location_name!r}, page_title={self.page_title!r})"


# Cache for loaded data (so we don't reload from DB on every search)
_cached_posts = None
_cached_bm25 = None


def _load_blogs_from_db():
    """Load blog posts from database and build BM25 index."""
    global _cached_posts, _cached_bm25
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        raise ValueError("DATABASE_URL not found in environment variables")
    
    logger.info("Loading blog posts from database...")
    engine = create_engine(database_url)
    
    posts = []
    corpus = []
    
    with Session(engine) as session:
        blog_posts = session.query(Whole_Blogs).all()
        logger.info(f"Loaded {len(blog_posts)} blog posts from database")
        
        for post in blog_posts:
            posts.append({
                "id": post.id,
                "location_name": post.location_name,
                "page_title": post.page_title,
                "page_description": post.page_description,
                "page_author": post.page_author,
                "page_url": post.page_url,
                "blog_url": post.blog_url,
                "latitude": post.latitude,
                "longitude": post.longitude,
                "content": post.content,
            })
            
            # Combine title, description, and content for searching
            search_text = f"{post.page_title} {post.page_description} {post.content}"
            corpus.append(search_text)
    
    # Build BM25 index
    logger.info("Building BM25 index...")
    tokenized_corpus = [tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    logger.info(f"BM25 index built with {len(posts)} documents")
    
    # Cache the results
    _cached_posts = posts
    _cached_bm25 = bm25
    
    return posts, bm25


def search_bm25(query: str, top_n: int = 12) -> List[Dict]:
    """
    Search blog posts using BM25.
    
    Args:
        query: Search query string
        top_n: Number of top results to return
        
    Returns:
        List of dicts with search results
    """
    global _cached_posts, _cached_bm25
    
    # Load data if not already cached
    if _cached_posts is None or _cached_bm25 is None:
        _load_blogs_from_db()
    
    if not query.strip():
        return []
    
    # Tokenize query
    tokenized_query = tokenize(query)
    
    if not tokenized_query:
        return []
    
    # Get BM25 scores
    scores = _cached_bm25.get_scores(tokenized_query)
    
    # Get top N document indices
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
    
    # Build results
    results = []
    for idx in top_indices:
        post = _cached_posts[idx]
        
        # Create content preview (first 300 chars)
        content_preview = post.get("content", "")[:300]
        if len(post.get("content", "")) > 300:
            content_preview += "..."
        
        # Try to extract country from location_name (if formatted like "City, Country")
        location_parts = post.get("location_name", "").split(",")
        country = location_parts[-1].strip() if len(location_parts) > 1 else ""
        
        results.append({
            "destination": post.get("location_name", "Unknown"),
            "country": country,
            "lat": float(post.get("latitude", 0)) if post.get("latitude") else None,
            "lon": float(post.get("longitude", 0)) if post.get("longitude") else None,
            "score": float(scores[idx]),
            "page_title": post.get("page_title", ""),
            "page_url": post.get("page_url", ""),
            "blog_url": post.get("blog_url", ""),
            "author": post.get("page_author", ""),
            "description": post.get("page_description", ""),
            "content_preview": content_preview,
            "full_content": post.get('content', ""),
        })
    
    return results