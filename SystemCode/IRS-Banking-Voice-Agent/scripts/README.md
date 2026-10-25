# Scripts

Place repeatable development, data-preparation, and validation scripts here. Keep core application logic in `src/banking_agent/`.

- `export_encoder_classifier.py` reproduces and exports Part A's pinned
  `all-MiniLM-L6-v2` + logistic-regression BANKING77 artifact.
- `train_intent_baseline.py` runs the BANKING77 baseline ladder.
- `validate_intent_mapping.py` checks the 77-label and route mapping.
