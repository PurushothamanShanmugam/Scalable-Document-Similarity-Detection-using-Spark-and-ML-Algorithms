import json
import logging
import time
from datetime import datetime

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, LOGS_DIR, RAW_DATA_DIR

LOGS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOGS_DIR / "consumer.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Import run_pipeline after logging is set up
try:
    from main import run_pipeline
except Exception as exc:
    raise SystemExit(f"Could not import run_pipeline from main.py: {exc}")

try:
    from kafka import KafkaConsumer
except Exception as exc:
    raise SystemExit(
        f"kafka-python not installed. Run: pip install kafka-python\nError: {exc}"
    )

# ---------------------------------------------------------------------------
# Retry connecting to Kafka — it may take a few seconds to be ready
# ---------------------------------------------------------------------------
MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds

consumer = None
for attempt in range(1, MAX_RETRIES + 1):
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
            consumer_timeout_ms=-1,          # block forever waiting for messages
            request_timeout_ms=30000,
            session_timeout_ms=10000,
        )
        # Force a metadata fetch to confirm the connection is alive
        consumer.topics()
        print(f"✅ Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS} (attempt {attempt})")
        logging.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        break
    except Exception as exc:
        print(f"⏳ Kafka not ready yet (attempt {attempt}/{MAX_RETRIES}): {exc}")
        logging.warning(f"Kafka connection attempt {attempt} failed: {exc}")
        if attempt == MAX_RETRIES:
            raise SystemExit(
                f"\n❌ Could not connect to Kafka after {MAX_RETRIES} attempts.\n"
                f"   Make sure Kafka is running:  docker-compose up zookeeper kafka\n"
                f"   Expected address: {KAFKA_BOOTSTRAP_SERVERS}"
            )
        time.sleep(RETRY_DELAY)

print(f"🚀 Kafka Consumer listening on topic '{KAFKA_TOPIC}'...\n")
logging.info(f"Kafka Consumer started, listening on '{KAFKA_TOPIC}'")

# ---------------------------------------------------------------------------
# Batch-aware pipeline triggering
# ---------------------------------------------------------------------------
# If many files arrive quickly, we don't want to re-run the full pipeline
# after every single message. We collect incoming docs for up to
# BATCH_WINDOW seconds, then run the pipeline once for the whole batch.

BATCH_WINDOW = 2.0   # seconds to wait for more messages before running pipeline
pending_docs = []    # docs received but pipeline not yet run

def flush_pipeline():
    """Save all pending docs and run the similarity pipeline."""
    global pending_docs
    if not pending_docs:
        return

    saved = []
    for doc_id, text, filename in pending_docs:
        try:
            filename.write_text(text, encoding="utf-8")
            saved.append(filename.name)
            logging.info(f"Saved: {filename.name}")
        except Exception as e:
            print(f"❌ Could not save {filename.name}: {e}")
            logging.error(f"Save error for {filename.name}: {e}")

    if saved:
        print(f"📄 Saved {len(saved)} doc(s): {saved}")
        print(f"⚡ Running pipeline on latest 100 files...")
        try:
            run_pipeline(limit=100, evaluate=False)
            print("✅ Pipeline complete — results updated in results/outputs.csv\n")
            logging.info(f"Pipeline complete after batch of {len(saved)}")
        except Exception as exc:
            print(f"❌ Pipeline error: {exc}")
            logging.error(f"Pipeline error: {exc}")

    pending_docs = []


last_message_time = None

for message in consumer:
    try:
        data = message.value
        text = (data.get("text") or "").strip()

        if not text:
            logging.warning("Empty message skipped")
            continue

        doc_id = (
            data.get("doc_id")
            or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        )
        filename = RAW_DATA_DIR / f"{doc_id}.txt"
        pending_docs.append((doc_id, text, filename))

        print(f"📥 Received: {doc_id}  ({len(text)} chars)")
        logging.info(f"Received message: {doc_id}")

        last_message_time = time.time()

    except Exception as exc:
        print(f"❌ Error reading message: {exc}")
        logging.error(f"Message read error: {exc}")
        continue

    # Check if the batch window has elapsed since the last message
    # by trying to poll briefly — if no new message arrives within
    # BATCH_WINDOW seconds, flush and run the pipeline.
    consumer.poll(timeout_ms=int(BATCH_WINDOW * 1000))

    if last_message_time and (time.time() - last_message_time) >= BATCH_WINDOW:
        flush_pipeline()
        last_message_time = None