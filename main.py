import os
import sys
import csv
import time
import argparse
import logging
import subprocess
import traceback
from itertools import combinations

from config import *
from src.preprocessing import preprocess
from src.shingling import create_shingles
from src.minhash import MinHash
from src.lsh import LSH
from src.jaccard import jaccard
from evaluation import run_evaluation


# -------------------------------------------------
# LOGGING
# -------------------------------------------------
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/project.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def log_step(step_name: str, start_time: float) -> None:
    elapsed = time.time() - start_time
    print(f"✅ {step_name} done in {elapsed:.2f}s")
    logging.info(f"{step_name} done in {elapsed:.2f}s")


def load_documents(limit=None):
    docs = []

    raw_dir = os.path.join("data", "raw")
    if not os.path.exists(raw_dir):
        return docs

    files = sorted([f for f in os.listdir(raw_dir) if f.endswith(".txt")])

    if limit is not None:
        files = files[:limit]

    print(f"📂 Loading {len(files)} file(s)...")

    for file in files:
        file_path = os.path.join(raw_dir, file)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                docs.append((file, f.read()))
        except Exception as e:
            logging.error(f"Error reading {file}: {e}")

    return docs


# -------------------------------------------------
# PYTHON PIPELINE
# -------------------------------------------------
def run_pipeline(limit=None, evaluate=True):
    print("\n🚀 Running Python pipeline...\n")
    logging.info("Python pipeline started")

    docs = load_documents(limit=limit)

    if not docs:
        print("⚠️ No data found in data/raw")
        logging.warning("No documents found")
        return

    try:
        step = time.time()
        print("🔹 Step 1: Preprocessing documents...")
        doc_names = [name for name, _ in docs]
        processed = [preprocess(text) for _, text in docs]
        log_step("Preprocessing", step)

        step = time.time()
        print("🔹 Step 2: Creating shingles...")
        shingles = [create_shingles(tokens, SHINGLE_SIZE) for tokens in processed]
        log_step("Shingling", step)

        step = time.time()
        print("🔹 Step 3: Generating MinHash signatures...")
        mh = MinHash(NUM_HASH)
        signatures = [mh.compute_signature(s) for s in shingles]
        log_step("MinHash", step)

        step = time.time()
        print("🔹 Step 4: Creating LSH buckets...")
        lsh = LSH(BANDS, ROWS)
        buckets = lsh.create_buckets(signatures)
        print(f"✅ LSH bucketing done ({len(buckets)} buckets)")
        logging.info(f"LSH bucketing done ({len(buckets)} buckets)")

        step = time.time()
        print("🔹 Step 5: Generating candidate pairs...")
        candidate_pairs = set()
        for bucket_docs in buckets.values():
            if len(bucket_docs) > 1:
                for i, j in combinations(bucket_docs, 2):
                    candidate_pairs.add((i, j))
        print(f"✅ Candidate pairs found: {len(candidate_pairs)}")
        logging.info(f"Candidate pairs found: {len(candidate_pairs)}")

        step = time.time()
        print("🔹 Step 6: Computing Jaccard similarity...")
        results = []
        for i, j in candidate_pairs:
            sim = jaccard(shingles[i], shingles[j])
            if sim >= SIMILARITY_THRESHOLD:
                results.append((doc_names[i], doc_names[j], sim))
        print(f"✅ Similarity computation done ({len(results)} matches >= {SIMILARITY_THRESHOLD})")
        logging.info(f"Similarity computation done ({len(results)} matches >= {SIMILARITY_THRESHOLD})")

        step = time.time()
        print("🔹 Step 7: Saving results...")
        os.makedirs("results", exist_ok=True)

        with open("results/outputs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["doc1", "doc2", "similarity"])
            writer.writerows(results)

        with open("results/metrics.txt", "w", encoding="utf-8") as f:
            f.write(f"Total documents: {len(docs)}\n")
            f.write(f"Total buckets: {len(buckets)}\n")
            f.write(f"Candidate pairs: {len(candidate_pairs)}\n")
            f.write(f"Matches above threshold ({SIMILARITY_THRESHOLD}): {len(results)}\n\n")
            for doc1, doc2, sim in results[:500]:
                f.write(f"{doc1} <-> {doc2} : {sim:.4f}\n")

        log_step("Saving results", step)

        print("✅ Python pipeline completed")
        logging.info("Python pipeline completed")

        if evaluate:
            try:
                run_evaluation()
                print("✅ Evaluation completed")
            except Exception as e:
                logging.warning(f"Evaluation failed: {e}")
                print(f"⚠️ Evaluation failed: {e}")

    except Exception as e:
        logging.error(f"Pipeline error: {e}")
        traceback.print_exc()
        print(f"❌ Pipeline failed: {repr(e)}")


# -------------------------------------------------
# SPARK BATCH
# -------------------------------------------------
def run_spark_batch(limit=None):
    print("\n🚀 Starting Spark Batch pipeline...\n")
    logging.info("Starting Spark batch pipeline")

    cmd = [sys.executable, "spark_batch.py"]

    if limit is not None:
        cmd.extend(["--limit", str(limit)])

    try:
        subprocess.run(cmd, check=True)
        print("✅ Spark Batch pipeline completed")

    except subprocess.CalledProcessError as e:
        logging.error(f"Spark Batch failed: {e}")
        print(f"❌ Spark Batch failed: {e}")

    except FileNotFoundError as e:
        logging.error(f"Spark Batch launch failed: {e}")
        print(f"❌ Spark Batch launch failed: {e}")


# -------------------------------------------------
# SPARK STREAMING
# -------------------------------------------------
def run_spark():
    print("\n🚀 Starting Spark Streaming...\n")
    logging.info("Starting Spark streaming pipeline")

    cmd = [sys.executable, "spark_streaming.py"]

    try:
        subprocess.run(cmd, check=True)
        print("✅ Spark Streaming completed")

    except subprocess.CalledProcessError as e:
        print("\n❌ Spark failed. Switching to Python Kafka fallback...\n")
        logging.error(f"Spark streaming failed: {e}")
        run_python_fallback()

    except FileNotFoundError as e:
        print("\n❌ Spark launch failed. Switching to Python Kafka fallback...\n")
        logging.error(f"Spark streaming launch failed: {e}")
        run_python_fallback()


# -------------------------------------------------
# PYTHON KAFKA FALLBACK
# -------------------------------------------------
def run_python_fallback():
    print("\n🟡 Running Kafka Consumer (Python fallback)...\n")
    logging.info("Switching to Python Kafka fallback")
    os.system(f'"{sys.executable}" kafka_consumer.py')


# -------------------------------------------------
# STREAM CONTROLLER
# -------------------------------------------------
def run_stream(mode="spark"):
    if mode == "spark":
        run_spark()
    elif mode == "python":
        run_python_fallback()
    else:
        print("❌ Invalid mode (use 'spark' or 'python')")


# -------------------------------------------------
# API
# -------------------------------------------------
def api():
    print("\n🚀 API -> http://127.0.0.1:5000/upload\n")
    os.system(f'"{sys.executable}" api.py')


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
def dashboard():
    print("\n🌐 Dashboard -> http://localhost:8501\n")
    os.system("streamlit run dashboard.py")


# -------------------------------------------------
# CLI
# -------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Document Similarity LSH Project")

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run Python pipeline")
    run_parser.add_argument("--limit", type=int, default=None, help="Limit number of files")

    spark_batch_parser = subparsers.add_parser("spark-batch", help="Run Spark batch pipeline")
    spark_batch_parser.add_argument("--limit", type=int, default=None, help="Limit number of files")

    stream_parser = subparsers.add_parser("stream", help="Run streaming pipeline")
    stream_parser.add_argument("mode", nargs="?", default="spark", choices=["spark", "python"])

    subparsers.add_parser("api", help="Start API")
    subparsers.add_parser("dashboard", help="Start dashboard")

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(limit=args.limit)

    elif args.command == "spark-batch":
        run_spark_batch(limit=args.limit)

    elif args.command == "stream":
        run_stream(mode=args.mode)

    elif args.command == "api":
        api()

    elif args.command == "dashboard":
        dashboard()

    else:
        parser.print_help()


# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    main()