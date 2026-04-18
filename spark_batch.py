import argparse
from pathlib import Path

from pyspark.ml.feature import HashingTF, MinHashLSH, RegexTokenizer, StopWordsRemover
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, input_file_name, regexp_extract

from config import RAW_DATA_DIR, RESULTS_DIR


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("DocumentSimilarityBatch").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    raw_path = str(RAW_DATA_DIR / "*.txt")
    df = spark.read.text(raw_path).withColumn("path", input_file_name())
    df = df.withColumn("doc_id", regexp_extract(col("path"), r"([^/\\]+)\.txt$", 1))
    if args.limit is not None:
        df = df.limit(args.limit)

    tokenizer = RegexTokenizer(inputCol="value", outputCol="tokens", pattern="\\W+")
    tokenized = tokenizer.transform(df)
    remover = StopWordsRemover(inputCol="tokens", outputCol="words")
    cleaned = remover.transform(tokenized)

    hashing_tf = HashingTF(inputCol="words", outputCol="features", numFeatures=1 << 18)
    featurized = hashing_tf.transform(cleaned)

    lsh = MinHashLSH(inputCol="features", outputCol="hashes", numHashTables=5)
    model = lsh.fit(featurized)

    joined = model.approxSimilarityJoin(featurized, featurized, 0.8, distCol="distance")
    result = (
        joined.select(
            col("datasetA.doc_id").alias("doc1"),
            col("datasetB.doc_id").alias("doc2"),
            (1 - col("distance")).alias("similarity"),
        )
        .where(col("doc1") < col("doc2"))
        .orderBy(col("similarity").desc())
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result.toPandas().to_csv(RESULTS_DIR / "outputs_spark_batch.csv", index=False)
    print(f"✅ Spark batch results saved to {RESULTS_DIR / 'outputs_spark_batch.csv'}")

    spark.stop()


if __name__ == "__main__":
    main()
