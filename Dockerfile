FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p data/raw data/processed results/plots logs

EXPOSE 8501
EXPOSE 5000

CMD ["python", "main.py", "run"]