import json
import pytest
from rank_bm25 import BM25Okapi

@pytest.fixture
def mock_bm25_db(mocker):
    fake_docs = [
        "Kyoto is known for temples and shrines",
        "The Dolomites are stunning mountain landscapes",
    ]
    tokenized_docs = [doc.lower().split() for doc in fake_docs]
    fake_bm25 = BM25Okapi(tokenized_docs)

    mocker.patch(
        "backend.src.api.bm25_utils._load_blogs_from_db",
        return_value = [
            {
                "destination": "Kyoto",
                "country": "Japan",
                "content": fake_docs[0],
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
                "content": fake_docs[1],
                "page_title": "Dolomites Guide",
                "page_url": "https://example.com/dolomites",
                "blog_url": "https://example.com",
                "author": "Test Author",
                "description": "Mountain travel blog",
                "latitude": 46.0,
                "longitude": 11.8,
            },
        ],
    )

    mocker.patch(
        "backend.src.api.bm25_utils._cached_bm25",
        fake_bm25,
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
