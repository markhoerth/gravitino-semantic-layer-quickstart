"""
MetricFlow MCP Server
Exposes governed metrics from a dbt/MetricFlow project as MCP tools.
"""

import os
import json
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Path to the dbt project root — set via environment variable
DBT_PROJECT_DIR = os.environ.get(
    "DBT_PROJECT_DIR",
    os.path.expanduser("~/gravitino-semantic-layer-quickstart/gravitino_semantic_layer")
)

_port = int(os.environ.get("METRICFLOW_MCP_PORT", 8003))
mcp = FastMCP("metricflow", host="0.0.0.0", port=_port)


def read_semantic_manifest() -> dict:
    """Read the compiled semantic manifest from the dbt target directory."""
    manifest_path = Path(DBT_PROJECT_DIR) / "target" / "semantic_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"semantic_manifest.json not found at {manifest_path}. "
            "Run 'dbt parse' in your dbt project first."
        )
    with open(manifest_path) as f:
        return json.load(f)


def run_mf_command(args: list[str]) -> str:
    """Run a MetricFlow CLI command from the dbt project directory."""
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = os.path.expanduser("~/.dbt")

    result = subprocess.run(
        ["mf"] + args,
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True,
        env=env
    )

    if result.returncode != 0:
        raise RuntimeError(f"MetricFlow error: {result.stderr}")

    return result.stdout


@mcp.tool()
def list_metrics() -> str:
    """
    List all available governed metrics in the semantic layer.
    Returns metric names, descriptions, and available dimensions for each metric.
    Use this tool first to discover what metrics are available before querying.
    """
    try:
        manifest = read_semantic_manifest()
        metrics = manifest.get("metrics", [])

        if not metrics:
            return "No metrics found in the semantic manifest."

        output = []
        for metric in metrics:
            name = metric.get("name", "unknown")
            description = metric.get("description", "No description")
            metric_type = metric.get("type", "unknown")
            output.append(f"- {name} ({metric_type}): {description}")

        return "Available metrics:\n" + "\n".join(output)

    except Exception as e:
        return f"Error listing metrics: {str(e)}"


@mcp.tool()
def query_metric(metric: str, group_by: str = None) -> str:
    """
    Compile a governed metric to SQL using MetricFlow.
    Returns the SQL that would be executed — use this to answer business questions
    with trusted, governed metric definitions rather than raw table access.

    Args:
        metric: The name of the metric to query (e.g. 'total_trips', 'average_fare')
        group_by: Optional dimension to group by (e.g. 'metric_time__day', 'trip__vendor_id')
                  Use list_metrics first to discover valid dimension names.
    """
    try:
        args = ["query", "--metrics", metric, "--explain"]
        if group_by:
            args += ["--group-by", group_by]

        sql = run_mf_command(args)

        lines = sql.splitlines()
        sql_lines = []
        in_sql = False
        for line in lines:
            if "SQL" in line and "explain" in line.lower():
                in_sql = True
                continue
            if in_sql:
                sql_lines.append(line)

        clean_sql = "\n".join(sql_lines).strip()
        if not clean_sql:
            clean_sql = sql.strip()

        return f"Governed SQL for metric '{metric}':\n\n{clean_sql}"

    except Exception as e:
        return f"Error querying metric '{metric}': {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", mount_path="/mcp")
