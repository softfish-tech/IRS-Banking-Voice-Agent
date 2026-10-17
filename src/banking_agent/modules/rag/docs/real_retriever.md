# B-RAG integration entry

See [delivery guide](../README.md) for the current
keep/archive inventory, initialization, contract, test commands and limitations.

```python
from banking_agent.modules.rag import create_retriever
backend = create_retriever('real')  # once at startup, cached model required
result = backend.retrieve('lost card replacement fees', top_k=5)
```

The package-level retrieve and real backend now convert invalid requests and
runtime Exceptions into error/docs=[]. Startup errors still propagate explicitly;
no silent mock fallback. Low-level BM25 methods retain ValueError for experiments.
No rejection threshold has been enabled. C owns sufficiency decisions, E owns State.
