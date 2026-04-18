import argparse
import json
import random
from pathlib import Path

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, RAW_DATA_DIR

TOPICS = [
    "machine learning improves pattern recognition and predictive analytics",
    "artificial intelligence is transforming healthcare and business workflows",
    "football tactics depend on passing movement and defensive structure",
    "data engineering pipelines support reliable analytics and reporting",
    "natural language processing helps compare text documents at scale",
]


def build_document(idx: int) -> str:
    base = random.choice(TOPICS)
    extra = random.choice(TOPICS)
    return f"Document {idx} discusses {base}. It also references {extra}."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    producer = None
    if args.stream:
        try:
            from kafka import KafkaProducer

            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except Exception:
            producer = None

    for i in range(args.count):
        text = build_document(i)
        path = RAW_DATA_DIR / f"doc_{i:06d}.txt"
        path.write_text(text, encoding="utf-8")
        if producer is not None:
            producer.send(KAFKA_TOPIC, {"doc_id": path.stem, "text": text})

    if producer is not None:
        producer.flush()

    print(f"✅ Generated {args.count} document(s) in {RAW_DATA_DIR}")
    if args.stream:
        print("✅ Documents were also streamed to Kafka")


if __name__ == "__main__":
    main()
