#!/usr/bin/env python3
"""
Collect travel blog posts to build a raw text corpus.

This script searches for travel blogs, extracts URLs, scrapes pages for title, 
description, content, and other meta data and saves it into a json.

Usage:
    python src/data/get_travel_blogs.py --api-key <SERPAPI_KEY> --num-sites n
"""

import os
import re
import json
import time
import random
import requests
import warnings
import argparse
import logging
from typing import List, Dict
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("travel-data")

RAW_PATH = os.path.join(os.path.dirname(__file__), "../../data/raw/travel_posts_raw.json")

def load_serpapi_key() -> str:
    """Load the SerpAPI key from ~/.serpAPI"""
    key_path = os.path.expanduser("~/.serpAPI") # NOTE: this is on my local machine
    if not os.path.exists(key_path):
        raise FileNotFoundError("API key file not found at ~/.serpAPI")
    with open(key_path, "r") as f:
        key = f.read().strip()
    return key

def serpapi_search(query: str, api_key: str, num_sites: int = 5) -> List[str]:
    """Return a list of top site URLs for the given search query."""
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": query,
        "hl": "en"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    links = [r["link"] for r in results.get("organic_results", []) if "link" in r]
    logger.info(f"Found {len(links)} candidate sites for '{query}'")
    return links

def get_wordpress_pages(base_url: str) -> List[str]:
    """Extract all post URLs from a WordPress sitemap."""
    # init list to store page links
    all_pages = []
    # List of sitemap URL suffixes to try
    sitemap_paths = ["sitemap-1.xml", "sitemap.xml"]
    
    # Try each sitemap path until a valid one is found
    sitemap_url = None
    for path in sitemap_paths:
        try:
            test_url = base_url.rstrip('/') + '/' + path
            response = requests.get(test_url)
            if response.status_code == 200:
                sitemap_url = test_url
                # stop if sucessful one is found
                break 
        except requests.RequestException:
            continue 

    if not sitemap_url:
        logger.warning(f"No valid sitemap found for {base_url}")
        return []

    # xml parser didnt work so html is a must, but it throws a warning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        soup = BeautifulSoup(response.text, 'html.parser')

    # find all links on page and store in a list
    links = soup.find_all('url')
    for l in links:
        loc = l.find('loc')
        if loc:
            all_pages.append(loc.text)
    return all_pages

def get_blog_post_data(page_url: str) -> Dict:
    """Scrape title, meta, and paragraph content from one blog page."""
    try:
        r = requests.get(page_url, timeout=10)
        if r.status_code != 200:
            return {}

        soup = BeautifulSoup(r.text, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Description
        description_meta = soup.find("meta", attrs={"property": "og:description"}) \
            or soup.find("meta", attrs={"name": "description"})
        description = description_meta.get("content").strip() if description_meta else None

        # Author
        author_meta = soup.find("meta", attrs={"property": "author"}) \
            or soup.find("meta", attrs={"name": "author"})
        author = author_meta.get("content").strip() if author_meta else None

        # Body text
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        content = "\n".join(p for p in paragraphs if len(p) > 30)

        if not content:
            return {}

        return {
            "url": page_url,
            "title": title,
            "description": description,
            "author": author,
            "content": content
        }

    except Exception as e:
        logger.debug(f"Error scraping {page_url}: {e}")
        return {}

def filter_links(links: List[str]) -> List[str]:
    """Remove non-article pages such as contact or privacy."""
    banned = ["privacy", "about", "contact", "terms", "policy", "wp-json"]
    return [l for l in links if not any(b in l.lower() for b in banned)]

def main():
    parser = argparse.ArgumentParser(description="Scrape travel blogs into a corpus")
    parser.add_argument("--api-key", type=str, required=False, help="SerpAPI key (optional if ~/.serpAPI exists)")
    parser.add_argument("--num-sites", type=int, default=3, help="Number of blogs to collect")
    parser.add_argument("--max-pages", type=int, default=40, help="Max pages per blog")
    parser.add_argument("--output", type=str, default=RAW_PATH, help="Output JSON path")
    args = parser.parse_args()

    if args.api_key:
        api_key = args.api_key
    else:
        api_key = load_serpapi_key()
    
    all_posts = []
    queries = [
        "travel blog site:wordpress.com",
        "off the beaten path travel blog",
        "hidden gems travel adventures"
    ]

    for query in queries:
        base_sites = serpapi_search(query, api_key, args.num_sites)
        for site in base_sites:
            match = re.match(r"https?://[^/]+", site)
            if not match:
                continue
            base_url = match.group(0)
            logger.info(f"Processing {base_url}")

            urls = filter_links(get_wordpress_pages(base_url))[: args.max_pages]
            for u in urls:
                post_data = get_blog_post_data(u)
                if post_data:
                    post_data["base_domain"] = base_url
                    all_posts.append(post_data)

                # Small delay for polite crawling 
                time.sleep(random.uniform(0.5, 1.5))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(all_posts)} posts to {args.output}")

if __name__ == "__main__":
    main()

