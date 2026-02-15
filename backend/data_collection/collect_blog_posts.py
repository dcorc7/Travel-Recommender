import requests
from bs4 import BeautifulSoup
import warnings
from serpapi import GoogleSearch
import numpy as np
import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import ArcGIS
from urllib.parse import urlparse
import math
from decimal import Decimal
import re
import time
import random
# DB Connection Things
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import os
import unicodedata

# Load a pre-trained English language model
nlp = spacy.load("en_core_web_sm")

# Load the geolocator
#geolocator = Nominatim(user_agent="off_the_path")
geolocator = ArcGIS(timeout=10)


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
api_key = os.getenv("API_KEY")

#print(f"Database URL: {DATABASE_URL}")
#print(f"API Key: {api_key}")


def clean_text(text):
    # normalize quotes and dashes
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('–', '-').replace('—', '-')
    text = unicodedata.normalize('NFKC', text)
    # Replace multiple spaces with single space
    text = " ".join(text.split())

    # remove unwanted characters
    c_text = text.translate(str.maketrans('', '', '()/*\\*><+=~^|#_%\'"'))
    c_text = c_text.translate(str.maketrans('', '', ',.!?;:"'))

    # replace some symbols with words
    c_text = c_text.replace('&', 'and').replace('%', 'percent').replace('@', 'at').replace('-'," ")

    # lowercase and collapse whitespace
    c_text = c_text.lower()
    c_text = re.sub(r'\s+', ' ', c_text).strip()

    return c_text

def serpapi_search(api_key, start_page = "0"):
    query = "travel site:wordpress.com"
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": query,
        "hl": "en",
        "start": start_page
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get('organic_results', [])

def get_all_blog_urls():
    #page_list = ['0', '10', '20', '30', '40', '50', '60', '70', '80', '90', '150', '160', '170', '180', '190', '200']
    page_list = ['0', '10', '20', '30', '40', '50', '60', '70', '80', '90']

    url_list = []

    for page in page_list:
        results = serpapi_search(api_key, page)
        for result in results:
            url = result['link']
            url_list.append(url)

    return url_list

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
    for link in links:
        loc = link.find('loc')
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
    all_paras = " ".join(clean_text(p.get_text(strip=True)) for p in paragraphs)
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

    author_content = ""
    
    # Try different author meta tag patterns
    author_meta = soup.find('meta', attrs={'name': 'author'})
    if not author_meta:
        author_meta = soup.find('meta', attrs={'property': 'article:author'})
    if not author_meta:
        author_meta = soup.find('meta', attrs={'name': 'article:author'})
    
    if author_meta:
        author_content = author_meta.get('content', '')
    
    # Fallback: look for author in HTML structure
    if not author_content:
        author_elem = soup.find('span', class_='author')
        if not author_elem:
            author_elem = soup.find('a', rel='author')
        if author_elem:
            author_content = author_elem.get_text(strip=True)

    return title, description_content, author_content

def find_geo_name(title, description):
    def extract_geo(doc):
        for i, ent in enumerate(doc.ents):
            if ent.label_ in ["GPE", "LOC"]:
                # If the entity is already multi-word, return it
                if len(ent.text.split()) > 1:
                    return ent.text
                # Try to combine with next consecutive GPE/LOC
                if i + 1 < len(doc.ents):
                    next_ent = doc.ents[i + 1]
                    if next_ent.start == ent.end and next_ent.label_ in ["GPE", "LOC"]:
                        return f"{ent.text}, {next_ent.text}"
                # fallback: single entity
                return ent.text
        return None

    # Check title first
    doc_title = nlp(title)
    result = extract_geo(doc_title)
    if result:
        return result

    # If nothing found, check description
    doc_desc = nlp(description)
    return extract_geo(doc_desc)
                
def get_lat_long(location_name):
    if not location_name:
        return None, None
        
    try:
        print(f"Geocoding '{location_name}'...")
        time.sleep(0.5)  # Small delay, ArcGIS is more lenient
        
        location = geolocator.geocode(location_name, timeout=10)

        if location:
            lat = location.latitude
            long = location.longitude
            print(f"✓ Found coordinates: {lat}, {long}")
            return lat, long
        else:
            print(f"Could not find location for: {location_name}")
            return None, None
            
    except Exception as e:
        print(f"Geocoding error for {location_name}: {e}")
        return None, None

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
            return f"Whole_Blogs(id={self.id!r}, , location_name={self.location_name!r}, page_title={self.page_title!r}"

    # This actually creates the table
    Base.metadata.create_all(engine)

    return engine, Whole_Blogs


def main():
    # Connect SERP API HERE
    query_urls = get_all_blog_urls()
    # query_urls = ['https://ashleighbugg.wordpress.com']
    print("Number of Travel Blogs:",len(query_urls))
    with open("backend/data_collection/query_urls.txt", 'w') as file_object:
        for item in query_urls:
            file_object.write(f"{item}\n")
    
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
                    # slow down requests to avoid 509
                    time.sleep(1)

                    # get blog content
                    content = get_blog_page_content(link)

                    # clean text
                    clean_content = clean_text(content)

                    # get blog meta data
                    title, description, author =  get_blog_page_meta_data(link)
                    place_name = find_geo_name(title, description)
 
                    lat, lon = get_lat_long(place_name)

                    print(f"\nURL: {link}")
                    print(f"Title: {title}")
                    print(f"Description: {description}")
                    print(f"Author: {author}")
                    print(f"Location: {place_name}")
                    print(f"Lat/Lon: {lat}, {lon}")
                    print(f"Content preview: {clean_content[:200]}")
                    print("")

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
                        except IntegrityError:
                            # Duplicate detected, skip this item
                            session.rollback()
                            print(f"Skipping duplicate URL: {'page_url'}")
                            continue
                        except Exception as e:
                            session.rollback()
                            print("Error:", e)

                except Exception as e:
                    print("Error while processing", link)
                    print(e)
                    continue

if __name__ == "__main__":
    main()


"""
HOW TO RUN:

python ./backend/data_collection/collect_travel_blogs.py
"""