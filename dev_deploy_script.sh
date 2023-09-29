#!/bin/bash

# Azure Databricks CLI setup
export DATABRICKS_HOST=https://adb-3943185736870612.12.azuredatabricks.net  
export DATABRICKS_TOKEN=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  
export DATABRICKS_ORG_ID=3943185736870612  

# Databricks workspace parameters
export WORKSPACE_PATH=/Shared/my_notebooks  

# GitHub token for authentication
export GITHUB_TOKEN=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

# Clone the repository to access notebooks in the dev branch
git clone -b dev https://github.com/RajuNaik/Project-K.git dev-repo

# Navigate to the directory with notebooks
cd dev-repo/notebooks

# Deploy all notebooks in the directory
for NOTEBOOK_FILE in *.dbc; do
  if [ -f "$NOTEBOOK_FILE" ]; then
    # Import the notebook into the Databricks workspace
    databricks workspace import -l PYTHON -f "$NOTEBOOK_FILE" "$WORKSPACE_PATH/$NOTEBOOK_FILE"

    # Check the import result
    if [ $? -eq 0 ]; then
      echo "Deployment of $NOTEBOOK_FILE to Dev environment succeeded."
    else
      echo "Deployment of $NOTEBOOK_FILE to Dev environment failed."
      exit 1
    fi
  fi
done
