"""Compare B's BM25 and Cross-Encoder ranks on the reviewed complex E2E set.

This is a local, offline diagnostic.  It writes only case IDs, fixture split,
document IDs and ranks; raw customer text and model prompts are never written.
"""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from .bm25_retriever import BM25Retriever
from .cross_encoder_reranker import CrossEncoderReranker
from .real_retriever import (
    DEFAULT_FAQ,
    DEFAULT_MODEL,
    DEFAULT_REVISION,
    _expand_replacement_fee_query,
)
from .retriever import DEFAULT_CHUNKS


ROOT = Path(__file__).resolve().parents[4]
FIXTURES = (
    ("development", ROOT / "tests/fixtures/evaluation/a_only_complex/v1/development.json"),
    ("holdout", ROOT / "tests/fixtures/evaluation/a_only_complex/v1/holdout.json"),
)
OVERLAYS = {
    "development": ROOT / "tests/fixtures/evaluation/semantic/v1/complex_language_development.json",
    "holdout": ROOT / "tests/fixtures/evaluation/semantic/v1/complex_language_holdout.json",
}


def _load_cases() -> list[dict]:
    cases: list[dict] = []
    for split, fixture_path in FIXTURES:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        overlay = json.loads(OVERLAYS[split].read_text(encoding="utf-8"))
        gold = {item["case_id"]: item for item in overlay["cases"]}
        for case in fixture["cases"]:
            cases.append(
                {
                    "case_id": case["case_id"],
                    "split": split,
                    "family": case["family"],
                    "query": case["input"],
                    "required_document_ids": gold[case["case_id"]].get("retrieval", {}).get(
                        "required_document_ids", []
                    ),
                }
            )
    return cases


def _position(document_id: str, ranked_ids: list[str]) -> int | None:
    try:
        return ranked_ids.index(document_id) + 1
    except ValueError:
        return None


def diagnose() -> dict:
    """Run the identical B candidate and reranking stages used by real E2E."""
    bm25 = BM25Retriever(
        str(DEFAULT_CHUNKS),
        normalize=True,
        title_weight=1.0,
        faq_path=str(DEFAULT_FAQ),
        faq_weight=0.5,
    )
    reranker = CrossEncoderReranker(
        DEFAULT_MODEL, revision=DEFAULT_REVISION, local_files_only=True
    )
    rows: list[dict] = []
    for case in _load_cases():
        retrieval_query = _expand_replacement_fee_query(case["query"])
        try:
            candidates = bm25.retrieve(retrieval_query, 20)
        except (TypeError, ValueError, ArithmeticError):
            candidates = {"status": "error", "data": {"docs": []}}
        if candidates["status"] != "ok":
            candidate_docs: list[dict] = []
            ce_docs: list[dict] = []
        else:
            candidate_docs = candidates["data"]["docs"]
            ce_docs = reranker.rerank(retrieval_query, candidate_docs, 5)
        bm25_ids = [doc["document_id"] for doc in candidate_docs]
        ce_ids = [doc["document_id"] for doc in ce_docs]
        required = list(case["required_document_ids"])
        rows.append(
            {
                "case_id": case["case_id"],
                "split": case["split"],
                "family": case["family"],
                "retrieval_status": candidates["status"],
                "required_document_ids": required,
                "bm25_candidate_ids": bm25_ids,
                "bm25_top5_ids": bm25_ids[:5],
                "cross_encoder_top5_ids": ce_ids,
                "required_document_positions": {
                    document_id: {
                        "bm25_top20": _position(document_id, bm25_ids),
                        "bm25_top5": _position(document_id, bm25_ids[:5]),
                        "cross_encoder_top5": _position(document_id, ce_ids),
                    }
                    for document_id in required
                },
            }
        )

    gold_rows = [row for row in rows if row["required_document_ids"]]

    def all_required_in(row: dict, stage: str) -> bool:
        return all(
            row["required_document_positions"][document_id][stage] is not None
            for document_id in row["required_document_ids"]
        )

    return {
        "evaluation": "complex_e2e_b_ranking_diagnostic_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": {
            "candidate_retriever": "optimized_bm25",
            "candidate_k": 20,
            "reranker": DEFAULT_MODEL,
            "reranker_revision": DEFAULT_REVISION,
            "output_k": 5,
            "query_rewrite": "disabled; only B-owned narrow normalization is retained",
        },
        "summary": {
            "cases": len(rows),
            "cases_with_required_gold_documents": len(gold_rows),
            "all_required_in_bm25_top20": sum(all_required_in(row, "bm25_top20") for row in gold_rows),
            "all_required_in_bm25_top5": sum(all_required_in(row, "bm25_top5") for row in gold_rows),
            "all_required_in_cross_encoder_top5": sum(
                all_required_in(row, "cross_encoder_top5") for row in gold_rows
            ),
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/evaluation/complex_e2e_b_ranking_diagnostic_v1.json",
    )
    args = parser.parse_args()
    report = diagnose()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_json": str(args.output), "summary": report["summary"]}))


if __name__ == "__main__":
    main()
