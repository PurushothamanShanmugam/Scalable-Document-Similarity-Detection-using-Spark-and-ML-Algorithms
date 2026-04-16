from pathlib import Path

from config import RAW_DATA_DIR

files = sorted(RAW_DATA_DIR.glob("*.txt"))[:10]
for i, path in enumerate(files):
    print(f"\n--- Document {i}: {path.name} ---\n")
    print(path.read_text(encoding="utf-8", errors="ignore")[:500])
