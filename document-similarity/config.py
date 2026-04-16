from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = BASE_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
LOGS_DIR = BASE_DIR / "logs"

NUM_HASH = 50
BANDS = 10
ROWS = 5
SHINGLE_SIZE = 2
SIMILARITY_THRESHOLD = 0.5
DEFAULT_FILE_LIMIT = 100
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "documents"
