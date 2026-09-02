# recount

An MCP server for your data. When Claude asks for a number, recount runs
the SQL and also checks the tables. The answer comes back with warnings, if
there are any.

Example. Ask "what was revenue in August?" on the example data:

```
revenue = sum(amount) from orders where status in ('paid', 'fulfilled')

month    revenue
-------  -------
2026-06  46665
2026-07  47665
2026-08  90050

Warnings:
- orders: 4811 rows but only 3615 distinct order_id. Some rows are in twice.
- orders: 2392 rows in 2026-08, the usual month has about 1219. Loaded twice?
```

The August file was loaded twice. Without the checks, the model says 90,050
and moves on.

## Install

```bash
pip install git+https://github.com/manisha-subedi/recount
```

Point it at a folder with CSV or Parquet files. Each file becomes a table.
A `.duckdb` file also works.

Claude Code:

```bash
claude mcp add recount -- recount /path/to/data /path/to/metrics.yaml
```

Claude Desktop, in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "recount": {
      "command": "recount",
      "args": ["/path/to/data", "/path/to/metrics.yaml"]
    }
  }
}
```

The metrics file is optional. To try the example:

```bash
claude mcp add recount -- recount ./example ./example/metrics.yaml
```

Then ask Claude: "What was revenue in August?"

## Tools

| Tool | What it does |
|---|---|
| `list_tables` | Tables and their columns. |
| `profile_table` | Row count. For each column: type, how many empty, how many distinct, some examples. |
| `query` | Runs a select query. Returns the rows and the warnings for every table in the query. |
| `check` | Runs the checks on one table. |
| `metric` | A metric from `metrics.yaml`, by month. |

## Checks

- Duplicates. Number of rows against number of distinct ids.
- Month jump. Newest month against the usual month. Double means loaded twice, half means data is missing.
- Old data. Newest date is more than 40 days ago.
- Empty columns. More than half of the values are empty.

recount guesses the id column (`id`, or the first column that ends with
`_id`) and the date column (the first date or timestamp column). If the
guess is wrong, pass them to `check`.

## Metrics

```yaml
revenue:
  table: orders
  expression: sum(amount)
  where: status in ('paid', 'fulfilled')
  date_column: ordered_at
```

With this file, "revenue" always means the same thing. The model does not
write its own definition.

## Notes

Only select queries run. recount never changes data. When it finds a
problem, it tells you. Fixing the data is your job.

## Development

```bash
uv venv && uv pip install -e ".[test]"
python example/make_data.py
pytest
```

The example data is a small shop, June to August 2026. The August file is
loaded twice on purpose.
