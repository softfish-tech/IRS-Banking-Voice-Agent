# Local BM25 retriever

`src/banking_agent/modules/rag/bm25_retriever.py` implements the existing evidence
result contract without changing shared schemas or C/E decision ownership.

Install the project in a Python 3.11+ environment:

```sh
python -m pip install -e .
python -m unittest banking_agent.modules.rag.tests.unit.test_bm25_retriever -v
```

```python
from banking_agent.modules.rag.bm25_retriever import BM25Retriever

retriever = BM25Retriever('/path/to/validated.jsonl')  # once at application startup
result = retriever.retrieve('lost card replacement fees', top_k=5)
```

Every nonblank input row must be an object with nonempty string `chunk_id`,
`title`, `source_type`, and `content` or `excerpt`. If both body fields exist they
must agree. IDs must be unique across all rows. Only exact source types
`Category Master Policy` and `FAQ` are indexed; these rows also require nonempty
`source_policy_id` and `source_policy_version`. Other source types are excluded.

The generated knowledge JSONL includes `source_type`, copied from each owning
policy's verified frontmatter. The builder rejects missing or unsupported policy
source types and records `source_type_matches_policy_metadata` in its report.
The corpus can be loaded directly by BM25Retriever; the public mock entry point
remains unchanged until E selects the backend.

File access errors propagate as OSError; invalid data raises
ChunkValidationError with location information; invalid query/top_k raises
ValueError. Empty/fully excluded corpora and queries without token overlap return
`empty`. Recognized score-computation failures return `error`, with `docs=[]`.
Excerpts are preserved exactly; normalization affects only indexed text.

Raw BM25 scores are not probabilities and may be zero or negative in small
corpora. Matching documents are ranked descending with deterministic ID ties;
documents without any query-token overlap are excluded. Lexical overlap is not
semantic evidence certification. Evidence thresholds and final answer permission
still require evaluation and C/E integration. No policy/date applicability can
be inferred from a query-only interface.

## Optional dev-selected ranking configuration

The original one-argument constructor preserves the baseline. To prioritize top-5
coverage, initialize once with `normalize=True, title_weight=1.0, faq_weight=0.5`
and `faq_path` pointing to `chunks/NovaBank_faq_chunk_mapping_v1_1.jsonl`.
All indexes, including FAQ expressions, are built at initialization. The score is
a weighted BM25 sum; evidence excerpts remain unchanged. FAQ associations are
candidate hints, not authoritative gold. Normalization is deliberately limited
to a small banking inflection map and stoplist retaining negation and numbers.
`coverage_weight` is an experimental lexical diversification option, disabled by
default because it reduced dev recall. See the evaluation experiment report for
all ablations and tradeoffs. These options do not implement a no-evidence gate.
