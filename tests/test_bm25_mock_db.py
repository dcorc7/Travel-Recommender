import json
import pytest
from rank_bm25 import BM25Okapi

@pytest.fixture
def mock_bm25_db(mocker):
    fake_posts = [
        {
            "destination": "Kyoto",
            "country": "Japan",
            "content": "Kyoto is known for temples and shrines.",
            "page_title": "Hidden Kyoto",
            "page_url": "https://example.com/kyoto",
            "blog_url": "https://example.com",
            "author": "Test Author",
            "description": "Kyoto travel blog",
            "latitude": 35.0,
            "longitude": 135.0,
        },
        {
            "destination": "Dolomites",
            "country": "Italy",
            "content": "The Dolomites offer dramatic mountain landscapes.",
            "page_title": "Dolomites Guide",
            "page_url": "https://example.com/dolomites",
            "blog_url": "https://example.com",
            "author": "Test Author",
            "description": "Mountain travel blog",
            "latitude": 46.0,
            "longitude": 11.8,
        },
    ]

    tokenized_docs = [p["content"].lower().split() for p in fake_posts]
    fake_bm25 = BM25Okapi(tokenized_docs)

    mocker.patch("backend.src.api.bm25_utils._cached_posts", fake_posts)
    mocker.patch("backend.src.api.bm25_utils._cached_bm25", fake_bm25)

    # prevent real DB load
    mocker.patch(
        "backend.src.api.bm25_utils._load_blogs_from_db",
        return_value = fake_posts,
    )


def test_bm25_returns_results(queries, run_bm25, mock_bm25_db):
    for q in queries:
        results = run_bm25(q)

        assert isinstance(results, list)
        assert len(results) > 0

        first = results[0]
        assert "destination" in first
        assert "score" in first
        assert "content_preview" in first

def test_bm25_save_results(queries, run_bm25, mock_bm25_db):
    all_results = {}

    for q in queries:
        results = run_bm25(q)
        all_results[q] = results

    with open("bm25_all_results.json", "w", encoding = "utf-8") as f:
        json.dump(all_results, f, indent = 2, ensure_ascii = False)

    assert len(all_results) > 0
