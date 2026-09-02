import os
import re
import sys
from pathlib import Path

import yaml
from mcp.server.mcpserver import MCPServer

from recount import checks, store

mcp = MCPServer("recount")
con = None
metrics: dict = {}


def warnings_for(sql: str) -> list[str]:
    """Check every table named in the sql."""
    found = []
    for table in store.tables(con):
        if re.search(rf"\b{re.escape(table)}\b", sql, re.IGNORECASE):
            found += checks.run_all(con, table)
    return found


def with_warnings(text: str, found: list[str]) -> str:
    if not found:
        return text + "\n\nChecks: nothing unusual."
    return text + "\n\nWarnings:\n" + "\n".join(f"- {w}" for w in found)


@mcp.tool()
def list_tables() -> str:
    """The tables you can query, with their columns."""
    out = []
    for t in store.tables(con):
        cols = ", ".join(f"{c} {k.lower()}" for c, k in store.columns(con, t))
        out.append(f"{t}: {cols}")
    return "\n".join(out) or "No tables found."


@mcp.tool()
def profile_table(table: str) -> str:
    """Row count. For each column: type, how many empty, how many distinct, some examples."""
    if table not in store.tables(con):
        return f"No table called {table}."
    total = con.execute(f'select count(*) from "{table}"').fetchone()[0]
    rows = []
    for name, kind in store.columns(con, table):
        empty, distinct = con.execute(
            f'select count(*) - count("{name}"), count(distinct "{name}") from "{table}"'
        ).fetchone()
        examples = con.execute(
            f'select "{name}" from "{table}" where "{name}" is not null limit 3'
        ).fetchall()
        rows.append((name, kind.lower(), empty, distinct, ", ".join(str(e[0]) for e in examples)))
    text = f"{table}: {total} rows\n\n" + store.as_text(
        ["column", "type", "empty", "distinct", "examples"], rows
    )
    return with_warnings(text, checks.run_all(con, table))


@mcp.tool()
def query(sql: str) -> str:
    """Run a select query. Returns the rows and the warnings for every table in the query."""
    if not sql.strip().lower().startswith(("select", "with")):
        return "Only select queries. recount does not change data."
    try:
        result = con.execute(sql)
        rows = result.fetchall()
        cols = [d[0] for d in result.description]
    except Exception as e:
        return f"Query failed: {e}"
    return with_warnings(store.as_text(cols, rows), warnings_for(sql))


@mcp.tool()
def check(table: str, key: str = "", date_column: str = "") -> str:
    """Run the checks on one table: duplicate keys, a month that jumped, stale data, empty columns."""
    if table not in store.tables(con):
        return f"No table called {table}."
    found = checks.run_all(con, table, key or None, date_column or None)
    return with_warnings(f"Checked {table}.", found)


@mcp.tool()
def metric(name: str) -> str:
    """A metric from metrics.yaml, by month."""
    if name not in metrics:
        known = ", ".join(metrics) or "none"
        return f"No metric called {name}. Known metrics: {known}."
    m = metrics[name]
    where = f"where {m['where']}" if m.get("where") else ""
    sql = (
        f"select date_trunc('month', \"{m['date_column']}\") as month, {m['expression']} as {name} "
        f"from \"{m['table']}\" {where} group by 1 order by 1"
    )
    result = con.execute(sql)
    rows = result.fetchall()
    text = f"{name} = {m['expression']} from {m['table']}" + (f" {where}" if where else "") + "\n\n"
    text += store.as_text(["month", name], [(f"{mo:%Y-%m}", v) for mo, v in rows])
    return with_warnings(text, checks.run_all(con, m["table"]))


def load_metrics(path: str | None) -> dict:
    if not path or not Path(path).exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def main():
    global con, metrics
    data = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RECOUNT_DATA", ".")
    con = store.connect(data)
    metrics = load_metrics(sys.argv[2] if len(sys.argv) > 2 else os.environ.get("RECOUNT_METRICS"))
    mcp.run()


if __name__ == "__main__":
    main()
