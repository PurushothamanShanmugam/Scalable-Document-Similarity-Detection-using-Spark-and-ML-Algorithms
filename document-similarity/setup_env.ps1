# Activate conda
conda activate docsim

# Set Java
$env:JAVA_HOME = "C:\Java\jdk1.8.0_481"

# Set PySpark
$env:PYSPARK_PYTHON = (Get-Command python).Source
$env:PYSPARK_DRIVER_PYTHON = (Get-Command python).Source

# Set Spark
$env:SPARK_HOME = "D:\conda_envs\docsim\Lib\site-packages\pyspark"

# Set Hadoop
$env:HADOOP_HOME = "C:\hadoop"

# Update PATH
$env:PATH = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;$env:PATH"

Write-Host "✅ Environment ready"