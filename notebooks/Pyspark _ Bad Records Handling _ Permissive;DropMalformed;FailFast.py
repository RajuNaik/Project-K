# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC ##Data avaiable at the end of this notebook

# COMMAND ----------

from pyspark.sql.types import StructType,StructField,IntegerType,StringType,DoubleType

df_sch=StructType([
StructField("Month",StringType(),nullable=False),
StructField("Product",StringType(),nullable=False),
StructField("Category",StringType(),nullable=False),
StructField("Quantity",IntegerType(),nullable=True),
StructField("SalesAmount",DoubleType(),nullable=True),
StructField("_corrupt_record",StringType(),nullable=False)
])

# COMMAND ----------

df=spark.read \
        .format("CSV") \
        .option("header",True) \
        .schema(df_sch) \
        .load("/FileStore/spark/test/sales_data.csv")
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##PERMISSIVE MODE While reading

# COMMAND ----------

df=spark.read \
        .format("csv") \
        .option("header",True) \
        .schema(df_sch) \
        .option("mode","PERMISSIVE") \
        .load("/FileStore/spark/test/sales_data.csv")
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##Drop bad records while reading

# COMMAND ----------

df=spark.read \
        .format("csv") \
        .option("header",True) \
        .schema(df_sch) \
        .option("mode","DROPMALFORMED") \
        .load("/FileStore/spark/test/sales_data.csv")
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##fail reading process while reading

# COMMAND ----------

df=spark.read \
        .format("csv") \
        .option("header",True) \
        .schema(df_sch) \
        .option("mode","FAILFAST") \
        .load("/FileStore/spark/test/sales_data.csv")
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC Month,Product,Category,Quantity,SalesAmount
# MAGIC January,Product A,Electronics,100,1000.00
# MAGIC February,Product B,Furniture,80,800.00,,
# MAGIC March,Product C,Appliances,75,750.00
# MAGIC April,Product A,Electronics,120,1200.00
# MAGIC May,Product B,Furniture,Hundred,900.00
# MAGIC June,Product C,Appliances,110,1100.00
# MAGIC July,Product A,Electronics,130,1300.00
# MAGIC August,Product B,Furniture,70,700.00
# MAGIC September,Product C,Appliances,80,800.00
# MAGIC October,Product A,Electronics,150,1500.00
# MAGIC November,Product B,Furniture,60,600.00
# MAGIC December,Product C,Appliances,95,950.00,hyderabad
