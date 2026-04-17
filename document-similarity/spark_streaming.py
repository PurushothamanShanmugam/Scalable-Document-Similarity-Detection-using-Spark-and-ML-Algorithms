import os

from pyspark.ml.feature import HashingTF, MinHashLSH, RegexTokenizer, StopWordsRemover
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, from_json
from pyspark.sql.types import StringType, StructField, StructType

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

spark = SparkSession.builder.appName("DocumentSimilarityStreaming").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

schema = StructType(
    [
        StructField("doc_id", StringType(), True),
        StructField("text", StringType(), True),
    ]
)

stream_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", KAFKA_TOPIC)
    .load()
)

parsed = (
    stream_df.selectExpr("CAST(value AS STRING) as json_str")
    .select(from_json(col("json_str"), schema).alias("data"))
    .select("data.*")
    .na.drop(subset=["text"])
)

# Tokenize + remove stopwords for each micro-batch before similarity join.
tokenizer = RegexTokenizer(inputCol="text", outputCol="tokens", pattern="\\W+")
remover = StopWordsRemover(inputCol="tokens", outputCol="words")
hashing_tf = HashingTF(inputCol="words", outputCol="features", numFeatures=1 << 16)



def save_batch(batch_df, epoch_id: int):
    os.makedirs("results", exist_ok=True)
    if batch_df.count() < 2:
        return

    tokenized = tokenizer.transform(batch_df)
    cleaned = remover.transform(tokenized)
    featurized = hashing_tf.transform(cleaned)

    lsh = MinHashLSH(inputCol="features", outputCol="hashes", numHashTables=3)
    model = lsh.fit(featurized)
    similar = model.approxSimilarityJoin(featurized, featurized, 0.8, distCol="distance")

    result = (
        similar.select(
            col("datasetA.doc_id").alias("doc1"),
            col("datasetB.doc_id").alias("doc2"),
            (1 - col("distance")).alias("similarity"),
        )
        .where(col("doc1") < col("doc2"))
        .orderBy(col("similarity").desc())
    )

    pdf = result.toPandas()
    if pdf.empty:
        return

    pdf.to_csv("results/outputs.csv", index=False)
    with open("results/metrics.txt", "w", encoding="utf-8") as f:
        for _, row in pdf.iterrows():
            f.write(f"{row['doc1']} <-> {row['doc2']}: {row['similarity']:.4f}\n")

    print(f"✅ Spark processed batch {epoch_id}")


query = (
    parsed.writeStream.foreachBatch(save_batch)
    .outputMode("append")
    .option("checkpointLocation", "checkpoints/spark_streaming")
    .start()
)

query.awaitTermination()
