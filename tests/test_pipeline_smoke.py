import main


def test_run_pipeline_creates_output_files_for_small_local_dataset(tmp_path, monkeypatch):
    data_raw = tmp_path / "data" / "raw"
    results_dir = tmp_path / "results"
    logs_dir = tmp_path / "logs"
    data_raw.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)

    (data_raw / "doc1.txt").write_text(
        "Document similarity with minhash and lsh for duplicate detection.",
        encoding="utf-8",
    )
    (data_raw / "doc2.txt").write_text(
        "Document similarity with minhash and lsh for near duplicate detection.",
        encoding="utf-8",
    )
    (data_raw / "doc3.txt").write_text(
        "Completely different cooking recipe with tomato and onion.",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    main.run_pipeline(limit=3, evaluate=False)

    output_file = results_dir / "outputs.csv"
    metrics_file = results_dir / "metrics.txt"

    assert output_file.exists()
    assert metrics_file.exists()

    output_text = output_file.read_text(encoding="utf-8")
    metrics_text = metrics_file.read_text(encoding="utf-8")

    assert "doc1" in output_text
    assert "doc2" in output_text
    assert "Total documents: 3" in metrics_text