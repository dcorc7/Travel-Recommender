import requests
from bs4 import BeautifulSoup
import warnings
from serpapi import GoogleSearch
import numpy as np
import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from urllib.parse import urlparse
import pandas as pd
import math
from decimal import Decimal
import re
# DB Connection Things
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationships
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

# Load a pre-trained English language model
nlp = spacy.load("en_core_web_sm")
# Load the geolocator
geolocator = Nominatim(user_agent="off_the_path")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
api_key = os.getenv("API_KEY")

print(f"Database URL: {DATABASE_URL}")
print(f"API Key: {api_key}")


def clean_text(text):
    # normalize quotes and dashes
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('–', '-').replace('—', '-')

    # remove unwanted characters
    c_text = text.translate(str.maketrans('', '', '()/*\\*><+=~^|#_%\'"'))
    c_text = c_text.translate(str.maketrans('', '', ',.!?;:"'))

    # replace some symbols with words
    c_text = c_text.replace('&', 'and').replace('%', 'percent').replace('@', 'at').replace('-'," ")

    # lowercase and collapse whitespace
    c_text = c_text.lower()
    c_text = re.sub(r'\s+', ' ', c_text).strip()

    return ' '.join(c_text)

def serpapi_search(query, api_key):
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": query,
        "hl": "en"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get('organic_results', [])

query = "travel site:wordpress.com"

def get_wordpress_pages(base_url):
    # init list to store page links
    all_pages = []
    # List of sitemap URL suffixes to try
    sitemap_paths = ["post-sitemap.xml", "sitemap-1.xml", "sitemap.xml", "sitemap_index.xml",]
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    # Try each sitemap path until a valid one is found
    sitemap_url = None
    for path in sitemap_paths:
        try:
            test_url = base_url.rstrip('/') + '/' + path
            r = requests.get(test_url, headers=headers, timeout=10)
            if 200 <= r.status_code < 300:
                sitemap_url = test_url
                sitemap_response = r
                break
        except requests.RequestException:
            continue 

    if not sitemap_url:
        print("No valid sitemap found.")
        return []

    # xml parser didnt work so html is a must, but it throws a warning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        soup = BeautifulSoup(sitemap_response.text, 'html.parser')
    # find all links on page and store in a list
    links = soup.find_all('url')
    for l in links:
        loc = l.find('loc')
        if loc:
            all_pages.append(loc.text)
    return all_pages


def is_useful_url(url):

    parsed = urlparse(url)
    path = parsed.path.lower()

    # skip pagination
    if "/page/" in path:
        return False

    # skip categories, tags, authors
    skip_segments = ["category", "tag", "author"]
    if any(f"/{seg}/" in path for seg in skip_segments):
        return False

    # skip feeds
    if "/feed/" in path:
        return False

    # skip wp system URLs
    if "wp-json" in path or "wp-admin" in path:
        return False

    # skip attachments / misc
    bad_ext = (".jpg", ".png", ".gif", ".pdf", ".xml", ".zip")
    if path.endswith(bad_ext):
        return False

    # skip query-string pages entirely
    if parsed.query:
        return False

    # optional: only allow URLs that “look like” posts/pages
    # e.g., end in a slash and contain a slug
    if not path.endswith("/"):
        return False

    return True
def get_blog_page_content(page_url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    response = requests.get(page_url, headers=headers, timeout=15)

    # Parse the HTML with Beautiful Soup
    soup = BeautifulSoup(response.text, 'html.parser')

    paragraphs = soup.find_all('p')
    all_paras = " ".join(p.get_text(strip=True) for p in paragraphs)
    return all_paras

def get_blog_page_meta_data(page_url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    response = requests.get(page_url, headers=headers, timeout=15)

    # Parse the HTML with Beautiful Soup
    soup = BeautifulSoup(response.text, 'html.parser')

    title_list = soup.find_all('title')
    title = str(title_list[0])
    title = title.replace("<title>","").replace("</title>","")

    description_meta = soup.find('meta', attrs={'property': 'og:description'})
    if description_meta:
        description_content = description_meta.get('content')
    else:
        description_content = ""

    author_meta = soup.find('meta', attrs={'property': 'author'})
    if author_meta:
        author_content = author_meta.get('content')
    else:
        author_content = ""

    return title, description_content, author_content

def find_geo_name(title, description):

    doc = nlp(title)

    for ent in doc.ents:
        if ent.label_ == "GPE" or ent.label_ == "LOC": # GPE: Geopolitical Entity, LOC: Location
            return ent
        else:
            doc = nlp(description)
            for ent in doc.ents:
                if ent.label_ == "GPE" or ent.label_ == "LOC":
                    return ent
                
def get_lat_long(location_name):
    try:
        location = geolocator.geocode(location_name)
        if location:
            lat = location.latitude
            long = location.longitude
            return lat, long
        else:
            print(f"Could not find location for: {location_name}")
    except GeocoderTimedOut:
        print("Error: Geocoding service timed out.")
    except Exception as e:
        print(f"An error occurred: {e}")

# I got this from ChatGPT since I couldnt figure out why things weren't writing to a DB

def clean_value(v):
    # Convert spaCy objects (Span, Token, Doc) to plain text
    if hasattr(v, "text"):
        return v.text

    # Convert numpy types to Python types
    if isinstance(v, (np.float32, np.float64)):
        if math.isnan(float(v)):
            return None
        return float(v)

    if isinstance(v, (np.int32, np.int64)):
        return int(v)

    # Convert NaN (float) to None
    if isinstance(v, float) and math.isnan(v):
        return None

    # Convert to string if needed
    return v

# I got this from ChatGPT since I couldnt figure out why things weren't writing to a DB

def convert_to_decimal(v):
    # NumPy floats → float
    if isinstance(v, (np.float32, np.float64)):
        v = float(v)

    # Convert Python floats → Decimal
    if isinstance(v, float):
        if math.isnan(v):
            return None  # DynamoDB accepts None
        return Decimal(str(v))  # use str to avoid precision issues

    # NumPy ints → int
    if isinstance(v, (np.int32, np.int64)):
        return int(v)

    return v

def db_connect_whole_blog():
    engine = create_engine(DATABASE_URL)

    class Base(DeclarativeBase):
        pass

    class Whole_Blogs(Base):

        __tablename__ = "blog_posts"

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
            return f"Whole_Blogs(id={self.id!r}, , location_name={self.location_name!r}, page_title={self.page_title!r})"

    # This actually creates the table
    Base.metadata.create_all(engine)

    return engine, Whole_Blogs


def main():
    
    query_urls = ['https://dangerousbusiness.wordpress.com', 'https://ashleighbugg.wordpress.com']
    # Connect SERP API HERE

    # init DB engine
    engine, Whole_Blogs = db_connect_whole_blog()
    id = 1
    with Session(engine) as session:  
        for blog_url in query_urls:
            all_links = get_wordpress_pages(blog_url)
            for link in all_links:
                if not is_useful_url(link):
                    print("Skipping:", link)
                    continue
                try:
                    # get blog content
                    content = get_blog_page_content(link)
                    # clean text
                    clean_content = clean_text(content)
                    # get blog meta data
                    title, description, author =  get_blog_page_meta_data(link)
                    place_name = find_geo_name(title, description)
                    lat, lon = get_lat_long(place_name)
                    # only write the row if the place name is defined
                    if place_name:
                        new_blog = Whole_Blogs(
                                    blog_url = clean_value(blog_url),
                                    page_url = clean_value(link),
                                    page_title = clean_value(title),
                                    page_description = clean_value(description),
                                    page_author = clean_value(author),
                                    location_name = clean_value(place_name),
                                    latitude = convert_to_decimal(lat),
                                    longitude = convert_to_decimal(lon),
                                    content = clean_value(clean_content)
                        )
                        id +=1
                        try:
                            session.add(new_blog)
                            session.commit()
                            print("Added blog for",place_name)
                        except Exception as e:
                            session.rollback()
                            print("Error:", e)
                        if id <2:
                            break
                except:
                    print("Not enough info in",link)
                    continue

if __name__ == "__main__":
    main()
