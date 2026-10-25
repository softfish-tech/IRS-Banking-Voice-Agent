# BANKING77 encoder classifier

Part A deliverable for the banking voice agent: a frozen
`sentence-transformers/all-MiniLM-L6-v2` sentence encoder followed by a multinomial logistic
regression probe.

## Results

| Metric | Value |
| --- | ---: |
| BANKING77 test Macro-F1 | **0.9307** |
| BANKING77 test accuracy | 0.9312 |
| Route Macro-F1 | 0.9604 |
| Route accuracy | 0.9838 |

The test split is scored once after refitting on all 10,003 train
examples. Model selection used a stratified 12% dev holdout of
train (seed 42).

## Files

| File | Purpose |
| --- | --- |
| `logreg_params.npz` | `coef` (77 x 384), `intercept` (77), and sklearn class order |
| `label_order.json` | 77 BANKING77 labels in published label-id order |
| `route_mapping.json` | Complete label-to-operational-route mapping |
| `preprocessing.json` | Raw-text, tokenizer, embedding, batch, and normalization config |
| `manifest.json` | Pinned encoder revision, per-file SHA-256, metrics, versions, entry point |
| `requirements-inference.txt` | Exact Python runtime used for inference |
| `requirements-export.txt` | Additional dependency for re-exporting the artifact |

## Frozen encoder

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- License: Apache-2.0
- Embedding dimension: 384
- Maximum sequence length: 256

The encoder weights are **not** stored in Git. The revision is immutable and
`manifest.json` records the byte size and SHA-256 of every file in the snapshot.
This avoids a ~90 MB binary in the repository while keeping the model pinned.

## Inference

```bash
python -m pip install -e .
python -m pip install -r src/banking_agent/modules/intent/model_artifacts/requirements-inference.txt
```

```python
from banking_agent.modules.intent import EncoderIntentClassifier

classifier = EncoderIntentClassifier.from_pretrained()
result = classifier.classify("Why was I charged this fee?")
print(result.intent, result.confidence, result.risk_level, result.entities)
```

`classify()` returns `UnderstandingResult`: operational intent, route-probability
confidence, risk level, and entities. It never returns an action, reason code, or
final response. To plug it into E's adapter:

```python
from banking_agent.modules.intent import IntentModuleAdapter

adapter = IntentModuleAdapter(classifier=classifier.classify)
```

## Verification and limits

- Loading verifies SHA-256 for all four parameter/config artifacts.
- The exported NumPy softmax path has zero prediction mismatches against
  `LogisticRegression.predict`; maximum probability difference is
  2.915e-06.
- Fine-grained mistakes should be interpreted through operational routes. Three
  routes (`fraud_suspicion`, `fee_complaint`, `product_recommendation`) are only
  partly or not represented in BANKING77 and still depend on the rule layer.
- The model always predicts one of 77 labels; abstention remains C's decision.

## Attribution

- BANKING77: Casanueva et al. (2020), `PolyAI/banking77`, CC-BY-4.0.
- `sentence-transformers/all-MiniLM-L6-v2`: Apache-2.0.

Reproduce with:

```bash
python scripts/export_encoder_classifier.py
```
