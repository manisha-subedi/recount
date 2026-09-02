# recount

An MCP server that never hands the model a number without the checks.

Most database tools for AI run the SQL and trust the answer. If a file was
loaded twice, the model reports double the revenue with full confidence.
`recount` runs the same SQL, then checks every table the query touched, and
returns the number together with the warnings.

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

## Install

```bash
pip install git+https://github.com/manisha-subedi/recount
```

Point it at a folder of CSV or Parquet files. Each file becomes a table.
A `.duckdb` file works too.

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

The metrics file is optional. Try it on the example first:

```bash
claude mcp add recount -- recount ./example ./example/metrics.yaml
```

Then ask: "What was revenue in August?"

## Tools

| Tool | What it does |
|---|---|
| `list_tables` | Tables and their columns. |
| `profile_table` | Row count, and for each column the type, how many empty, how many distinct, a few examples. |
| `query` | Runs a select. The result comes back with the checks for every table it used. |
| `check` | Runs the checks on one table. |
| `metric` | A metric from `metrics.yaml`, by month. One definition, so "revenue" always means one thing. |

## The checks

Four checks. Each is one query. Each catches something a type test does not.

- **Duplicates.** Rows against distinct ids. Equal in a clean table.
- **A month that jumped.** The newest month against the usual month. Double means loaded twice, half means missing data.
- **Stale data.** The newest date is more than 40 days old.
- **Empty columns.** A column that is mostly null.

`recount` guesses the id column (`id`, or the first column that ends in `_id`)
and the date column (the first date or timestamp). You can pass both to
`check` if the guess is wrong.

## Metrics

```yaml
revenue:
  table: orders
  expression: sum(amount)
  where: status in ('paid', 'fulfilled')
  date_column: ordered_at
```

With this file, the model asks for `revenue` and gets one definition every
time, instead of writing its own.

## What it does not do

It never changes data. Only select queries run. When it finds a duplicate, it
tells you. Fixing the load is a job for a person.

## Development

```bash
uv venv && uv pip install -e ".[test]"
python example/make_data.py
pytest
```

The example is a small shop, June to August 2026, with the August file
loaded twice. That is the fault every check should catch.
