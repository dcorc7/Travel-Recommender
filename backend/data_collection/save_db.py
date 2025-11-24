from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationships
from dotenv import load_dotenv
import sqlite3
import os
import json
import math

load_dotenv()

database_url = os.getenv("DATABASE_URL")

print(f"Database URL: {database_url}")

engine = create_engine(database_url)

Session = sessionmaker(bind=engine)
session = Session()

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

