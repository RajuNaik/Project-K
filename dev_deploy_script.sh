#!/bin/bash

# Azure Databricks CLI setup
export DATABRICKS_HOST=https://adb-3943185736870612.12.azuredatabricks.net  # Replace with your Databricks workspace URL
export DATABRICKS_TOKEN=<Your_Databricks_Token>  # Replace with your Databricks API token
export DATABRICKS_ORG_ID=3943185736870612  # Replace with your organization ID

# Databricks workspace parameters
export WORKSPACE_PATH=/Shared/my_notebooks  # Replace with the desired workspace path
export NOTEBOOK_FILE=my_notebook.dbc  # Replace with the name of your DBC file

# GitHub token for authentication
export GITHUB_TOKEN=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

# Import the notebook into the Databricks workspace
databricks workspace import -l PYTHON -f $NOTEBOOK_FILE $WORKSPACE_PATH/$NOTEBOOK_FILE

# Check the import result
if [ $? -eq 0 ]; then
  echo "Deployment to Dev environment succeeded."
else
  echo "Deployment to Dev environment failed."
  exit 1
fi
