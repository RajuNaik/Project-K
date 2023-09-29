# Databricks notebook source
emp_data=[
(1,"raj",100,111),
(2,"ram",2000,222),
(3,"Jake",3000,333),
(4,"John",4000,444),
(10,"Binny",1000,000)
]

emp_sch=["id","name","salary","dept"]

# COMMAND ----------

emp_df=spark.createDataFrame(data=emp_data,schema=emp_sch)
display(emp_df)

# COMMAND ----------

dept_data=[
(111,"HR"),
(222,"TECH"),
(333,"Consulting"),
(444,"Tax"),
(999,"Assurance")
]

dept_sch=["dept_id","dept_name"]

# COMMAND ----------

dept_df=spark.createDataFrame(data=dept_data,schema=dept_sch)
display(dept_df)

# COMMAND ----------

display(emp_df)
display(dept_df)

# COMMAND ----------

from pyspark.sql.functions import broadcast as bc

df_inner=emp_df.join(bc(dept_df),emp_df.dept==dept_df.dept_id,"inner")
display(df_inner)

# COMMAND ----------

df_inner.explain(True)

# COMMAND ----------

df_left=emp_df.join(dept_df,emp_df.dept==dept_df.dept_id,"left_outer") #left,leftouter, left_outer anything is fine  
display(df_left)

# COMMAND ----------

df_right=emp_df.join(dept_df,emp_df.dept==dept_df.dept_id,"rightouter")  #rightout,right,right_outer also fine
display(df_right)

# COMMAND ----------

df_full=emp_df.join(dept_df,emp_df.dept==dept_df.dept_id,"full") #fullouter, full_outer also works
display(df_full)

# COMMAND ----------

#just like inner join, but fetches columns only from left table

df_semi=emp_df.join(dept_df,emp_df.dept==dept_df.dept_id,"semi")  #semileft,semi_left also works
display(df_semi)

# COMMAND ----------

df_anti=emp_df.join(dept_df,emp_df.dept==dept_df.dept_id,"anti")  #left_anti,leftanti also works
display(df_anti)
