# Databricks notebook source
import json
import pyspark.sql.functions as F

data = [
    ("A", "X", 100, "Hyd"),
    ("B", "A", 200, "Hyd"),
    ("C", "X", 300, "Pune"),
    ("D", "C", 400, "Bglr"),
    ("E", "D", 500, "KOL"),
    ("F", "E", 600, "Mumbai"),
    ("G", "F", 700, "Chennai"),
    ("H", "X", 800, "Chennai")
]
df = spark.createDataFrame(data, ["employee", "manager", "salary", "location"])

# Function to check if a record is a leaf node
def is_leaf_node(employee):
    return df.filter(F.col("manager") == employee).count() == 0

# Recursive function to build the employee hierarchy
def build_hierarchy(manager):
    # Get the direct reports for the given manager
    direct_reports = df.filter(F.col("manager") == manager)

    # Base case: If no direct reports, return an empty list
    if direct_reports.count() == 0:
        return []

    # Recursive case: Build hierarchy for each direct report
    hierarchy = []
    for row in direct_reports.collect():
        report = {
            "employee": row["employee"],
            "salary": row["salary"],
            "location": row["location"],
            "subordinates": [] if is_leaf_node(row["employee"]) else build_hierarchy(row["employee"]),
            "manager": row["manager"]
        }
        hierarchy.append(report)

    return hierarchy if hierarchy else []

# Build hierarchy starting from the root manager
root_manager = "X"
hierarchy_data = build_hierarchy(root_manager)

# Construct the JSON data
json_data = {
    "manager": root_manager,
    "subordinates": hierarchy_data
}

# Convert JSON data to a string
json_string = json.dumps(json_data, indent=4)

# Print the JSON string
print(json_string)


# COMMAND ----------


