import json
import pytest

@pytest.fixture
def mock_bm25_db(mocker):
    mocker.patch(
        "backend.src.api.bm25_utils._load_blogs_from_db",
        return_value = [
            {
                "destination": "Kyoto",
                "country": "Japan",
                "content": "Kyoto is known for its temples and hidden shrines.",
                "page_title": "Hidden Kyoto",
                "page_url": "https://example.com/kyoto",
                "blog_url": "https://example.com",
                "author": "Test Author",
                "description": "Kyoto travel blog",
                "latitude": 35.0116,
                "longitude": 135.7681,
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
                "latitude": 46.4102,
                "longitude": 11.8440,
            },
        ],
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
