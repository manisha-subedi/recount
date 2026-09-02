from datetime import date

from recount import store


def duplicates(con, table: str, key: str) -> str | None:
    total, distinct = con.execute(
        f'select count(*), count(distinct "{key}") from "{table}"'
    ).fetchone()
    if total != distinct:
        return f'{table}: {total} rows but only {distinct} distinct {key}. Some rows are in twice.'
    return None


def period_jump(con, table: str, date_col: str) -> str | None:
    """Newest month against the usual month."""
    rows = con.execute(
        f'select date_trunc(\'month\', "{date_col}") as m, count(*) from "{table}" '
        "group by 1 order by 1"
    ).fetchall()
    if len(rows) < 3:
        return None
    counts = [n for _, n in rows]
    usual = sorted(counts[:-1])[len(counts[:-1]) // 2]
    last_month, last = rows[-1]
    if last > 1.5 * usual:
        return f"{table}: {last} rows in {last_month:%Y-%m}, the usual month has about {usual}. Loaded twice?"
    if last < 0.5 * usual:
        return f"{table}: {last} rows in {last_month:%Y-%m}, the usual month has about {usual}. Missing data?"
    return None


def stale(con, table: str, date_col: str, max_age_days: int = 40) -> str | None:
    newest = con.execute(f'select max("{date_col}") from "{table}"').fetchone()[0]
    if newest is None:
        return f"{table}: {date_col} is empty."
    newest = newest.date() if hasattr(newest, "date") else newest
    age = (date.today() - newest).days
    if age > max_age_days:
        return f"{table}: newest {date_col} is {newest}, {age} days ago."
    return None


def empty_columns(con, table: str, threshold: float = 0.5) -> str | None:
    bad = []
    for name, _ in store.columns(con, table):
        rate = con.execute(f'select avg(case when "{name}" is null then 1 else 0 end) from "{table}"').fetchone()[0]
        if rate and rate >= threshold:
            bad.append(f"{name} ({rate:.0%} empty)")
    if bad:
        return f"{table}: mostly empty columns: {', '.join(bad)}."
    return None


def run_all(con, table: str, key: str | None = None, date_col: str | None = None) -> list[str]:
    key = key or store.guess_key(con, table)
    date_col = date_col or store.guess_date(con, table)
    found = []
    if key:
        found.append(duplicates(con, table, key))
    else:
        found.append(f"{table}: no id column found, so duplicates were not checked.")
    if date_col:
        found.append(period_jump(con, table, date_col))
        found.append(stale(con, table, date_col))
    found.append(empty_columns(con, table))
    return [f for f in found if f]
