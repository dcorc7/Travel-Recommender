from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
import os

DATABASE_URL = 'postgresql://off_the_beaten_path_corpus_user:WU80pq1zJeX7eeZvDRkODby3fCIxIrbx@dpg-d4g6udidbo4c73a0s3cg-a.virginia-postgres.render.com/off_the_beaten_path_corpus'
print(DATABASE_URL)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    print([row[0] for row in result])
