#!/bin/bash
cd ~/gravitino-semantic-layer-quickstart
source venv/bin/activate

DBT_PROJECT_DIR=~/gravitino-semantic-layer-quickstart/gravitino_semantic_layer \
DBT_PROFILES_DIR=~/.dbt \
METRICFLOW_MCP_PORT=8003 \
python gravitino_semantic_layer/metricflow_mcp_server.py
