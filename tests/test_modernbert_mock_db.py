import pytest
import numpy as np
from types import SimpleNamespace

@pytest.fixture
def mock_modernbert_db(mocker):
    fake_posts = [
        SimpleNamespace(
            destination = "Kyoto",
            country = "Japan",
            lat = 35.0,
            lon = 135.0,
            page_title = "Kyoto Temples",
            page_url = "https://example.com/kyoto",
            blog_url = "https://example.com",
            author = "Test Author",
            description = "Kyoto travel",
            content = "Kyoto temples and shrines are beautiful.",
        )
    ]

    fake_embeddings = np.random.rand(1, 768).astype("float32")

    class FakeIndex:
        def search(self, x, k):
            return np.array([[0.1]]), np.array([[0]])

    mocker.patch(
        "backend.src.api.modern_bert_utils._load_posts_and_index",
        return_value = (fake_posts, FakeIndex(), fake_embeddings),
    )
       

def test_modernbert_basic(queries, mock_modernbert_db):
    from backend.src.api.modern_bert_utils import search_modernbert

    for q in queries:
        results = search_modernbert(q, top_k = 5)

        assert isinstance(results, list)
        assert len(results) > 0

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
            "full_content",
        ]
        for key in expected_keys:
            assert key in first

def test_modernbert_empty_query(mock_modernbert_db):
    from backend.src.api.modern_bert_utils import search_modernbert

    results = search_modernbert("", top_k = 5)
    assert results == []
