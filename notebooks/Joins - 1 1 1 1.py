# Databricks notebook source
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

df1_data=[
  (1,),
  (1,),
  (1,),
  (1,),
  (1,)
]

df1_sch=StructType([
StructField("id1",IntegerType(),nullable=True)
])

df1=spark.createDataFrame(df1_data,schema=df1_sch)
display(df1)

# COMMAND ----------

spark_version = spark.version
print(spark_version)

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

df2_data=[
  (1,),
  (1,)
]

df2_sch=StructType([
StructField("id2", IntegerType(), nullable=True)  
])

df2=spark.createDataFrame(df2_data,schema=df2_sch)
display(df2)

# COMMAND ----------

df_inner=df1.join(df2,df1.id1==df2.id2,"full")
display(df_inner)
