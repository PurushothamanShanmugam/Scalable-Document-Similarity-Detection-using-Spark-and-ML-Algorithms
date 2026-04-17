## Document Similarity Intelligence Hub

A scalable document similarity system built using MinHash + LSH, with support for:
Local Python processing
Apache Spark batch processing
Optional Kafka streaming
Flask API for ingestion
Streamlit dashboard for visualization

## Overview

This project provides:

## Document Ingestion
Local file upload (data/raw/)
API-based ingestion
Batch processing
## Similarity Detection
Shingling
MinHash
Locality Sensitive Hashing (LSH)
## Scalable Processing
Python pipeline (small datasets)
Apache Spark (large datasets)
## Interactive Dashboard
2D & 3D visualizations
Document similarity exploration
Performance analytics

## System Architecture
                ┌──────────────┐
                │   Documents  │
                └──────┬───────┘
                       │
               Preprocessing
                       │
                 Tokenization
                       │
                  Shingling
                       │
                MinHash Signatures
                       │
                      LSH
                       │
        ┌──────────────┴──────────────┐
        │                             │
   Similar Pairs                Real-time Stream
        │                             │
   Output Files                 Kafka → Spark
        │                             │
     Dashboard                    API Layer

## Optional Streaming Architecture
API → Kafka Producer → Kafka Consumer → Processing → Results

## Project Structure
docsim_proj/
│
├── api.py                  # Flask API
├── dashboard.py            # Streamlit UI
├── main.py                 # Core pipeline
├── spark_batch.py          # Spark batch processing
├── setup_env.ps1           # Windows setup script
│
├── config.py
│
├── data/
│   ├── raw/                # Input documents
│   └── processed/
│
├── results/
│   ├── outputs.csv
│   ├── metrics.txt
│   └── plots/
│
├── src/
│   ├── preprocessing.py
│   ├── shingling.py
│   ├── minhash.py
│   ├── lsh.py
│   └── jaccard.py
│
├── tests/                  # Pytest test cases
├── requirements.txt
└── .github/workflows/ci.yml

## ⚙️ Installation
     1️⃣ Create Environment
     conda create -n docsim python=3.10 -y
     conda activate docsim
     ▶️set the environment variables: .\setup_env.ps1

     2️⃣ Install Dependencies
     pip install -r requirements.txt
     ▶️ Execution Guide

##  1. Python-Based Execution (Recommended)
Step 1: Add documents

Place .txt files in:
data/raw/
Step 2: Run pipeline
python main.py
Step 3: Run evaluation
python -c "from src.evaluation import run_evaluation; run_evaluation()"
Step 4: Launch dashboard
streamlit run dashboard.py

 Open in browser:

http://localhost:8501

## 2. Spark Batch Execution (Scalable)

Run Spark pipeline:

python spark_batch.py --limit 10000

For large scale:

python spark_batch.py --limit 100000

Output:results/outputs_spark_batch.csv


##  3. API Execution
Start API
python api.py

API URL:http://127.0.0.1:5000
Test API
python -c "import requests; print(requests.get('http://127.0.0.1:5000/health').json())"
Upload Document via API

import requests
requests.post(
    "http://127.0.0.1:5000/upload",
    json={"text": "sample document text"}
)

## Important Fix (Common Issue)

If you see:
     Upload failed: Connection refused
     ✅ Reason:
     API is NOT running
     OR wrong URL used 
     ✅ Fix:Use:http://127.0.0.1:5000

##  Dashboard Features
Similarity distribution graphs
Top matching document pairs
2D & 3D visualizations
Document browser
Pagination for large datasets
Image gallery navigation

## Docker Setup
Build Image
docker build -t docsim-app .
Run Container
docker run -p 8501:8501 -p 5000:5000 docsim-app
Services
Streamlit → http://localhost:8501
API → http://localhost:5000

## Testing (CI Ready)
Run tests:
pytest -q
Covers:
     Preprocessing
     Shingling
     MinHash
     LSH
     Pipeline
     API endpoints

##  ⚙️ Running Without Kafka (Recommended)
If Kafka is not used:
API still works
Documents saved locally
Processing via Python/Spark
"streamed_to_kafka": false
✅ This is expected behavior

## Troubleshooting
1. API Connection Refused
python api.py
2. Dashboard Empty
streamlit run dashboard.py
3. Spark Errors (Java)
echo $env:JAVA_HOME
4. Kafka Issues

👉 Ignore if not using Kafka

5. winutils.exe Error (Windows)

Place file in:C:\hadoop\bin\winutils.exe

## Scalability
Mode	Scale
Python	≤ 10K documents
Spark Batch	100K+ documents
Kafka + Spark	Real-time scale

## Authors
Purushothaman S
Pranav Sri Vasthav Tenali Gnana
Aakanksha Nalamati
M.Tech Data Engineering
Indian Institute of Technology Jodhpur
