import json
import time

from kafka import KafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

DOCS = [
    {"doc_id": "stream_1", "text": "Machine learning is powerful"},
    {"doc_id": "stream_2", "text": "Deep learning is evolving"},
    {"doc_id": "stream_3", "text": "Football is fun"},
    {"doc_id": "stream_4", "text": "AI is the future"},
]

for payload in DOCS:
    producer.send(KAFKA_TOPIC, payload)
    print(f"Sent: {payload['doc_id']}")
    time.sleep(1)

producer.flush()
