import json
import pytest
from backend.src.api.bm25_utils import search_bm25
from backend.src.api.modern_bert_utils import search_modernbert

'''
@pytest.fixture
def queries():
    with open("backend/data/queries.json", "r") as f:
        return json.load(f)["queries"]
'''

@pytest.fixture
def run_bm25():
    return lambda q: search_bm25(q, top_n=5)
