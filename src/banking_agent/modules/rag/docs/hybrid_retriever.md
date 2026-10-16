# Local hybrid retrieval experiment

Implementation: `src/banking_agent/modules/rag/hybrid_retriever.py`.
The public mock entry point is unchanged. No dev/test evaluation is run implicitly.

## Run (Python 3.11+)

```sh
python -m pip install -e '.[rag-dense]'
python -m banking_agent.modules.rag.hybrid_retriever --query 'How much does replacing a lost card cost?'
```

The first invocation can download the configured model to the normal Hugging Face
cache, outside the repository. Use `--local-files-only` once cached, or `--model`
with a local SentenceTransformer model directory. Use `--revision` with a model
commit to pin remote weights. Constructor also accepts device, candidate_k,
rrf_k, batch_size, query_prefix and document_prefix (for model-specific prompts).

```python
from banking_agent.modules.rag.hybrid_retriever import HybridRetriever

retriever = HybridRetriever(
    'src/banking_agent/modules/rag/chunks/NovaBank_knowledge_chunks_v1_1.jsonl',
    model_name='sentence-transformers/all-MiniLM-L6-v2',
    candidate_k=20, rrf_k=60,
)
for mode in ('bm25', 'dense', 'hybrid'):
    result = retriever.retrieve('lost card replacement fees', top_k=5, mode=mode)
    print(mode, result)
```

Both indexes are created during construction. Dense uses title + full excerpt,
normalizes vectors, and calculates cosine via matrix-vector multiplication.
Models may truncate their encoder input at max_seq_length: the full text is
passed in, but this implementation does not implement long-text window pooling.
The original returned excerpt is always complete. Inspect index_metadata before
experiments and consider a longer-context model if policy details are truncated.

BM25 mode is the original baseline, without the optional FAQ/title optimization.
Hybrid independently retrieves max(candidate_k, top_k) candidates from each
branch and sums 1/(rrf_k + one-based rank), deduplicating by document_id. A missing
branch contributes zero. Ties are resolved by document_id. No raw score addition,
threshold, LLM, external vector database, or query-time corpus read is involved.

Direct list methods raise ValueError for invalid input and propagate technical
failures. retrieve() returns error/docs=[] for invalid requests or recognized
runtime failures. Construction failures (corrupt corpus, missing model/dependency,
invalid vectors) raise explicitly. Empty corpora yield empty/docs=[].
Dense similarity and RRF score do not establish sufficient evidence; this module
does not solve no-evidence rejection. C still owns the final decision.

Save index_metadata with experiment results, including corpus hash, requested
model revision, dimension, candidate depth, prompts and maximum sequence length.
A missing revision is not a pinned model version. Injected encoders are for tests;
record their identity separately before treating results as model benchmarks.
There is no persistent vector cache: reconstruct the retriever after changing
corpus/model/configuration to rebuild both indexes. An existing instance remains
an in-memory snapshot and intentionally does not monitor files during retrieval.

Offline tests use deterministic fake embeddings to verify cosine/RRF mathematics,
error envelopes, filtering, 151-chunk loading, caching and complete evidence.
They do not measure actual sentence-transformer quality. Real-model execution
requires installing the optional dependency and obtaining weights.

API reference: https://www.sbert.net/docs/package_reference/sentence_transformer/model.html
