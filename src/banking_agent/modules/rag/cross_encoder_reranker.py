"""Rank existing candidates only; no evidence rejection or query rewriting."""
from __future__ import annotations
from typing import Any
import numpy as np


class CrossEncoderReranker:
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L6-v2', *,
                 revision: str | None = None, model: Any = None,
                 local_files_only: bool = False) -> None:
        if model is None:
            from sentence_transformers import CrossEncoder
            import torch
            model = CrossEncoder(model_name, revision=revision, device='cpu',
                                 max_length=512, activation_fn=torch.nn.Identity(),
                                 trust_remote_code=False, local_files_only=local_files_only,
                                 # The immutable upstream revision includes both formats.
                                 # Its safetensors artifact produces NaN activations under
                                 # the pinned macOS ARM reference stack, while the matching
                                 # PyTorch artifact yields finite logits.  Pin the verified
                                 # artifact rather than silently accepting invalid scores.
                                 model_kwargs={'use_safetensors': False})
        self.model = model

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        if not isinstance(query, str) or not query.strip() or type(top_k) is not int or top_k <= 0:
            raise ValueError('Nonempty query and positive integer top_k required')
        if len({d['document_id'] for d in candidates}) != len(candidates):
            raise ValueError('Duplicate candidate IDs')
        if not candidates:
            return []
        pairs = [(query, d['title'] + '\n' + d['excerpt']) for d in candidates]
        scores = np.asarray(self.model.predict(pairs, batch_size=16,
                                               show_progress_bar=False, convert_to_numpy=True))
        if scores.shape != (len(candidates),) or not np.isfinite(scores).all():
            raise ValueError('Invalid cross-encoder scores')
        order = sorted(range(len(candidates)), key=lambda i: (-float(scores[i]), candidates[i]['document_id']))
        # Scores are raw relevance logits, not calibrated answer confidence.
        return [dict(candidates[i], score=float(scores[i])) for i in order[:top_k]]
