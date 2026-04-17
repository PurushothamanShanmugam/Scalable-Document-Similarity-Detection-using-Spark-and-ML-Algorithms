import time
from itertools import combinations
from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt

from config import BANDS, NUM_HASH, PLOTS_DIR, RAW_DATA_DIR, ROWS, SHINGLE_SIZE
from src.jaccard import jaccard
from src.lsh import LSH
from src.minhash import MinHash
from src.preprocessing import preprocess
from src.shingling import create_shingles


def _load_local_documents(limit: int = 20) -> List[str]:
    if not RAW_DATA_DIR.exists():
        return []
    docs: List[str] = []
    for path in sorted(RAW_DATA_DIR.glob("*.txt"))[:limit]:
        docs.append(path.read_text(encoding="utf-8", errors="ignore"))
    return docs


def run_evaluation(documents: Optional[List[str]] = None) -> None:
    docs = documents if documents is not None else _load_local_documents(limit=20)
    if len(docs) < 2:
        print("⚠️ Evaluation skipped: need at least 2 local documents.")
        return

    processed_docs = [preprocess(doc) for doc in docs]
    shingles_list = [create_shingles(doc, k=SHINGLE_SIZE) for doc in processed_docs]

    # -----------------------------------------
    # 1. Brute force timing
    # -----------------------------------------
    start = time.time()
    brute_scores = []
    for i, j in combinations(range(len(shingles_list)), 2):
        sim = jaccard(shingles_list[i], shingles_list[j])
        brute_scores.append(sim)
    brute_time = time.time() - start

    # -----------------------------------------
    # 2. LSH timing
    # -----------------------------------------
    start = time.time()
    mh = MinHash(num_hash=NUM_HASH)
    signatures = [mh.compute_signature(sh) for sh in shingles_list]

    lsh = LSH(bands=BANDS, rows=ROWS)
    buckets = lsh.create_buckets(signatures)

    candidate_pairs = set()
    bucket_sizes = []

    for bucket in buckets.values():
        bucket_sizes.append(len(bucket))
        if len(bucket) > 1:
            for i, j in combinations(bucket, 2):
                candidate_pairs.add((i, j))

    lsh_scores = []
    for i, j in candidate_pairs:
        sim = jaccard(shingles_list[i], shingles_list[j])
        lsh_scores.append(sim)

    lsh_time = time.time() - start

    # -----------------------------------------
    # 3. Document sizes
    # -----------------------------------------
    doc_word_counts = [len(doc) for doc in processed_docs]

    # -----------------------------------------
    # 4. Create plots directory
    # -----------------------------------------
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------
    # Plot 1: Performance Comparison
    # -----------------------------------------
    methods = ["Brute Force", "LSH"]
    times = [brute_time, lsh_time]

    plt.figure(figsize=(6, 4))
    plt.bar(methods, times)
    plt.title("Performance Comparison")
    plt.xlabel("Method")
    plt.ylabel("Time (seconds)")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "performance.png")
    plt.close()

    # -----------------------------------------
    # Plot 2: Similarity Score Distribution
    # -----------------------------------------
    if brute_scores:
        plt.figure(figsize=(7, 4))
        plt.hist(brute_scores, bins=15)
        plt.title("Brute Force Similarity Distribution")
        plt.xlabel("Jaccard Similarity")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / "similarity_distribution.png")
        plt.close()

    # -----------------------------------------
    # Plot 3: Candidate Pair Count
    # -----------------------------------------
    plt.figure(figsize=(6, 4))
    plt.bar(["Candidate Pairs"], [len(candidate_pairs)])
    plt.title("LSH Candidate Pair Count")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "candidate_pairs.png")
    plt.close()

    # -----------------------------------------
    # Plot 4: Bucket Size Distribution
    # -----------------------------------------
    if bucket_sizes:
        plt.figure(figsize=(7, 4))
        plt.hist(bucket_sizes, bins=15)
        plt.title("LSH Bucket Size Distribution")
        plt.xlabel("Bucket Size")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / "bucket_size_distribution.png")
        plt.close()

    # -----------------------------------------
    # Plot 5: Document Length Distribution
    # -----------------------------------------
    if doc_word_counts:
        plt.figure(figsize=(7, 4))
        plt.hist(doc_word_counts, bins=15)
        plt.title("Document Length Distribution")
        plt.xlabel("Token Count After Preprocessing")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / "document_length_distribution.png")
        plt.close()

    # -----------------------------------------
    # Plot 6: Similarity Method Comparison Summary
    # -----------------------------------------
    summary_labels = ["Documents", "Brute Pairs", "LSH Candidates"]
    summary_values = [
        len(docs),
        len(brute_scores),
        len(candidate_pairs),
    ]

    plt.figure(figsize=(7, 4))
    plt.bar(summary_labels, summary_values)
    plt.title("Evaluation Summary")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "evaluation_summary.png")
    plt.close()

    print("✅ Evaluation completed. Generated plots:")
    print(f"   - {PLOTS_DIR / 'performance.png'}")
    print(f"   - {PLOTS_DIR / 'similarity_distribution.png'}")
    print(f"   - {PLOTS_DIR / 'candidate_pairs.png'}")
    print(f"   - {PLOTS_DIR / 'bucket_size_distribution.png'}")
    print(f"   - {PLOTS_DIR / 'document_length_distribution.png'}")
    print(f"   - {PLOTS_DIR / 'evaluation_summary.png'}")