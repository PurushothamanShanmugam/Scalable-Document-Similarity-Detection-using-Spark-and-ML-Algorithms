import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, RAW_DATA_DIR

app = Flask(__name__)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

producer = None


def build_kafka_producer():
    try:
        from kafka import KafkaProducer

        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    except Exception:
        return None


def get_kafka_producer():
    global producer
    if producer is None:
        producer = build_kafka_producer()
    return producer


def safe_filename(name: str) -> str:
    clean = Path(name).name.strip()
    if not clean:
        clean = f"api_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.txt"
    if not clean.lower().endswith(".txt"):
        clean = f"{clean}.txt"
    return clean


def save_document(text: str, filename: Optional[str] = None) -> Path:
    if filename:
        final_name = safe_filename(filename)
    else:
        final_name = f"api_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.txt"

    file_path = RAW_DATA_DIR / final_name
    file_path.write_text(text, encoding="utf-8")
    return file_path


def stream_document_to_kafka(file_path: Path, text: str):
    kafka_producer = get_kafka_producer()
    if kafka_producer is None:
        return False, "Kafka producer unavailable"

    try:
        kafka_producer.send(
            KAFKA_TOPIC,
            {
                "doc_id": file_path.stem,
                "filename": file_path.name,
                "text": text,
                "timestamp": datetime.now().isoformat(),
            },
        )
        kafka_producer.flush()
        return True, None
    except Exception as e:
        return False, str(e)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "message": "Document Similarity API is running",
            "upload_endpoint": "/upload",
            "health_endpoint": "/health",
            "mode": "local_save_plus_optional_kafka",
        }
    ), 200


@app.route("/health", methods=["GET"])
def health():
    kafka_producer = get_kafka_producer()
    kafka_available = kafka_producer is not None

    return jsonify(
        {
            "status": "ok",
            "kafka_configured": bool(KAFKA_BOOTSTRAP_SERVERS),
            "kafka_producer_available": kafka_available,
            "kafka_topic": KAFKA_TOPIC,
            "raw_data_dir": str(RAW_DATA_DIR),
            "api_url": "http://127.0.0.1:5000",
        }
    ), 200


@app.route("/upload", methods=["POST", "OPTIONS"])
def upload():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}

    # -------------------------------------------------
    # MODE 1: MULTIPLE DOCUMENTS
    # Expected:
    # {
    #   "documents": [
    #       {"text": "...", "filename": "a.txt"},
    #       {"text": "...", "filename": "b.txt"}
    #   ]
    # }
    # -------------------------------------------------
    if "documents" in payload:
        documents = payload.get("documents") or []
        if not isinstance(documents, list) or len(documents) == 0:
            return jsonify({"error": "'documents' must be a non-empty list."}), 400

        results = []

        for item in documents:
            text = (item.get("text") or "").strip() if isinstance(item, dict) else ""
            filename = item.get("filename") if isinstance(item, dict) else None

            if not text:
                results.append(
                    {
                        "file": filename or "",
                        "message": "Skipped empty document",
                        "streamed_to_kafka": False,
                    }
                )
                continue

            file_path = save_document(text, filename)
            streamed, kafka_error = stream_document_to_kafka(file_path, text)

            row = {
                "message": "Saved document",
                "file": file_path.name,
                "saved_to": str(file_path),
                "streamed_to_kafka": streamed,
                "kafka_topic": KAFKA_TOPIC,
            }
            if kafka_error:
                row["kafka_error"] = kafka_error

            results.append(row)

        return jsonify(
            {
                "message": "Batch upload processed",
                "count": len(results),
                "results": results,
            }
        ), 200

    # -------------------------------------------------
    # MODE 2: SINGLE DOCUMENT
    # Expected:
    # {
    #   "text": "...",
    #   "filename": "a.txt"
    # }
    # -------------------------------------------------
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify(
            {"error": "Request JSON must include a non-empty 'text' field."}
        ), 400

    provided_filename = (payload.get("filename") or "").strip()
    file_path = save_document(text, provided_filename if provided_filename else None)

    streamed, kafka_error = stream_document_to_kafka(file_path, text)

    response = {
        "message": "Saved document",
        "file": file_path.name,
        "saved_to": str(file_path),
        "streamed_to_kafka": streamed,
        "kafka_topic": KAFKA_TOPIC,
        "api_host_hint": "Use http://127.0.0.1:5000 when dashboard runs on the same machine",
    }

    if kafka_error:
        response["kafka_error"] = kafka_error

    return jsonify(response), 200


if __name__ == "__main__":
    producer = build_kafka_producer()

    print("API running at:")
    print("  http://127.0.0.1:5000")
    print("  Endpoints: /upload, /health")
    print(f"  Raw data directory: {RAW_DATA_DIR}")
    print(f"  Kafka topic: {KAFKA_TOPIC}")

    app.run(host="0.0.0.0", port=5000, debug=False)