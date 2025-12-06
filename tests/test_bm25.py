def test_bm25_returns_results(queries, run_bm25):
    for q in queries:
        results = run_bm25(q)

        # basic sanity checks
        assert isinstance(results, list)
        assert len(results) > 0

        first = results[0]
        assert "destination" in first
        assert "score" in first
        assert "content_preview" in first

import json

def test_bm25_save_results(queries, run_bm25):
    all_results = {}

    for q in queries:
        results = run_bm25(q)
        all_results[q] = results

    with open("bm25_all_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("Saved BM25 results to bm25_all_results.json")

