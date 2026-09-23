# recount

recount is an MCP server that lets Claude and other compatible assistants
query local data with DuckDB. It returns query results with warnings about
possible data-quality problems.

It reads CSV and Parquet files from a folder, or opens an existing DuckDB
database in read-only mode.

## What it checks

- Duplicate or missing keys, using row and distinct-key counts.
- An unusually high or low row count in the latest month.
- Data older than the configured freshness threshold.
- Columns with many missing values.

These checks flag issues for investigation. A warning does not establish
the cause, and passing the checks does not guarantee a correct analysis.

## Install and run

Use Python 3.11 or newer. From the repository folder:

```bash
uv venv
uv pip install -e ".[test]"
source .venv/bin/activate
claude mcp add recount -- recount ./example ./example/metrics.yaml
```

The example folder contains order and customer data. Ask the assistant to
list the tables, inspect the orders, or calculate the revenue metric.

You can also start the server directly:

```bash
recount ./example ./example/metrics.yaml
```

## Available tools

| Tool | Purpose |
|---|---|
| `list_tables` | List tables and columns. |
| `profile_table` | Show row counts, types, missing values, and sample values. |
| `query` | Run SQL and return warnings for the referenced tables. |
| `check` | Check one table, with optional key and date columns. |
| `metric` | Calculate a named metric by month from a YAML definition. |

## Metric definitions

The example defines revenue once in `example/metrics.yaml`:

```yaml
revenue:
  table: orders
  expression: sum(amount)
  where: status in ('paid', 'fulfilled')
  date_column: ordered_at
```

The metric tool returns the definition, monthly values, and any table
warnings together. It does not silently remove duplicate rows or decide
how a business metric should be defined.

## Tests

```bash
pytest
```

The tests cover data-quality checks and table discovery.
