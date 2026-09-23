from pathlib import Path

import duckdb


def connect(path: str) -> duckdb.DuckDBPyConnection:
    """A folder of csv or parquet files becomes tables. A .duckdb file is opened as is."""
    p = Path(path)
    if p.suffix == ".duckdb":
        return duckdb.connect(str(p), read_only=True)

    con = duckdb.connect()
    for f in sorted(p.iterdir()):
        if f.suffix in (".csv", ".parquet"):
            con.execute(f'create view "{f.stem}" as select * from \'{f}\'')
    return con


def tables(con) -> list[str]:
    rows = con.execute("select table_name from information_schema.tables order by 1").fetchall()
    return [r[0] for r in rows]


def columns(con, table: str) -> list[tuple[str, str]]:
    rows = con.execute(
        "select column_name, data_type from information_schema.columns "
        "where table_name = ? order by ordinal_position",
        [table],
    ).fetchall()
    return [(name, kind) for name, kind in rows]


def guess_key(con, table: str) -> str | None:
    names = [c for c, _ in columns(con, table)]
    for name in names:
        if name == "id" or name.endswith("_id") and name.startswith(table.rstrip("s")):
            return name
    for name in names:
        if name.endswith("_id"):
            return name
    return None


def guess_date(con, table: str) -> str | None:
    for name, kind in columns(con, table):
        if "DATE" in kind or "TIMESTAMP" in kind:
            return name
    return None


def as_text(cols: list[str], rows: list[tuple], limit: int = 50) -> str:
    """Rows as an aligned text table."""
    shown = rows[:limit]
    cells = [[str(v) for v in r] for r in shown]
    widths = [max(len(c), *(len(r[i]) for r in cells)) if cells else len(c) for i, c in enumerate(cols)]

    def line(values):
        return "  ".join(v.ljust(w) for v, w in zip(values, widths))

    out = [line(cols), line(["-" * w for w in widths]), *[line(r) for r in cells]]
    if len(rows) > limit:
        out.append(f"... {len(rows) - limit} more rows")
    return "\n".join(out)
