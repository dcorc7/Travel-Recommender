import pytest
from backend.src.api.modern_bert_utils import search_modernbert

pytestmark = pytest.mark.integration


@pytest.fixture
def queries():
    # Replace with a few sample queries for testing
    return [
        "Kyoto Japan temples",
        "mountains in Europe",
        "beaches in Thailand"
    ]

def test_modernbert_basic(queries):
    for q in queries:
        results = search_modernbert(q, top_k=5)

        # Ensure results are a list
        assert isinstance(results, list)
        assert len(results) > 0

        # Check the first result has expected keys
        first = results[0]
        expected_keys = [
            "destination",
            "country",
            "lat",
            "lon",
            "distance",
            "page_title",
            "page_url",
            "blog_url",
            "author",
            "description",
            "content_preview",
            "full_content"
        ]
        for key in expected_keys:
            assert key in first

def test_modernbert_empty_query():
    results = search_modernbert("", top_k=5)
    assert results == []  # Should return empty list for empty query
