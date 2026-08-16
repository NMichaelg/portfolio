#!/usr/bin/env python3
"""
One-time download of the sentence-transformers embedding model to local disk,
so get_embedding_model() never has to hit the Hugging Face Hub at runtime.

Usage:
    uv run scripts/download_embedding_model.py

Run this once, with network access. After this, point EMBEDDING_MODEL_PATH
at the saved folder and set HF_HUB_OFFLINE=1 wherever the app actually runs.
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# backend/models/all-MiniLM-L6-v2
LOCAL_DIR = Path(__file__).parent.parent / "models" / "all-MiniLM-L6-v2"


def main():
    print(f"Downloading {MODEL_NAME} (needs network this one time)...")
    model = SentenceTransformer(MODEL_NAME)

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(LOCAL_DIR))

    # Sanity check so a bad save fails loudly here, not later at request time.
    config_path = LOCAL_DIR / "config.json"
    if not config_path.exists() or '"model_type"' not in config_path.read_text():
        raise RuntimeError(f"Save looks incomplete: {config_path} missing or malformed.")

    print(f"Saved complete model to {LOCAL_DIR}")
    print("Verified config.json. Safe to load offline now.")


if __name__ == "__main__":
    main()