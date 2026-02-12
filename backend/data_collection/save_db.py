from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import json
import math

load_dotenv()

database_url = os.getenv("DATABASE_URL")

print(f"Database URL: {database_url}")

engine = create_engine(database_url)

# Session = sessionmaker(bind=engine)
session = Session(engine)

# Create the table if it doesn't exist
create_table_sql = """
CREATE TABLE IF NOT EXISTS travel_blogs (
    id SERIAL PRIMARY KEY,
    blog_url TEXT,
    page_url TEXT UNIQUE NOT NULL,
    page_title TEXT,
    page_description TEXT,
    page_author TEXT,
    location_name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    content TEXT
);
"""

with engine.connect() as conn:
    conn.execute(text(create_table_sql))
    conn.commit()

# Fetch all rows from a table 
result = session.execute(text("SELECT * FROM travel_blogs")).mappings().all()
data_to_save = [dict(row) for row in result]

# Example: Saving to a JSON file
chunk_size = 300
total_chunks = math.ceil(len(data_to_save) / chunk_size)

for i in range(total_chunks):
    start_index = i * chunk_size
    end_index = start_index + chunk_size
    chunk = data_to_save[start_index:end_index]
    
    filename = f"data/raw/travel_blogs_part_{i+1}.json"
    with open(filename, "w") as jsonfile:
        json.dump(chunk, jsonfile, indent=4)
    print(f"Saved {len(chunk)} records to {filename}")

session.close()

