import api


def test_health_endpoint_returns_ok_status():
    client = api.app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert "raw_data_dir" in body


def test_upload_single_document_saves_file(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr(api, "get_kafka_producer", lambda: None)

    client = api.app.test_client()
    response = client.post(
        "/upload",
        json={
            "filename": "sample_doc.txt",
            "text": "Document similarity test through API upload",
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["file"] == "sample_doc.txt"
    assert body["streamed_to_kafka"] is False
    assert (tmp_path / "sample_doc.txt").exists()


def test_upload_batch_documents_skips_empty_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr(api, "get_kafka_producer", lambda: None)

    client = api.app.test_client()
    response = client.post(
        "/upload",
        json={
            "documents": [
                {"filename": "doc1.txt", "text": "minhash similarity document"},
                {"filename": "doc2.txt", "text": "   "},
            ]
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 2
    assert body["results"][0]["file"] == "doc1.txt"
    assert body["results"][1]["message"] == "Skipped empty document"