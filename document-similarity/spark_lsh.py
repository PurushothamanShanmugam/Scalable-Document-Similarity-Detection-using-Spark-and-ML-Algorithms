from pyspark.sql import SparkSession
from pyspark.ml.feature import Tokenizer, HashingTF, MinHashLSH

spark = SparkSession.builder.appName("LSH").getOrCreate()

data = [
    (0, "machine learning is powerful"),
    (1, "machine learning is useful"),
    (2, "football is popular sport")
]

df = spark.createDataFrame(data, ["id", "text"])

# Tokenize
tokenizer = Tokenizer(inputCol="text", outputCol="words")
wordsData = tokenizer.transform(df)

# Hashing
hashingTF = HashingTF(inputCol="words", outputCol="features")
featurizedData = hashingTF.transform(wordsData)

# MinHash LSH
mh = MinHashLSH(inputCol="features", outputCol="hashes", numHashTables=3)
model = mh.fit(featurizedData)

# Similarity
result = model.approxSimilarityJoin(featurizedData, featurizedData, 0.6)

result.select("datasetA.id", "datasetB.id", "distCol").show()