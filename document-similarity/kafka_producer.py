import json
import time

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

DOCUMENTS = [
    {"doc_id": "sample_1", "text": "machine learning is powerful and practical"},
    {"doc_id": "sample_2", "text": "machine learning is useful in many applications"},
    {"doc_id": "sample_3", "text": "football is a great sport with tactics"},
    {"doc_id": "sample_4", "text": "deep learning improves accuracy for many tasks"},
]

for payload in DOCUMENTS:
    producer.send(KAFKA_TOPIC, payload)
    print(f"Sent: {payload['doc_id']}")
    time.sleep(0.5)

producer.flush()
print("✅ Done")
