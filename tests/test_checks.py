from pathlib import Path

import pytest

from recount import checks, store

EXAMPLE = Path(__file__).parent.parent / "example"


@pytest.fixture
def con():
    return store.connect(str(EXAMPLE))


def test_finds_the_duplicated_file(con):
    found = checks.run_all(con, "orders")
    assert any("distinct order_id" in w for w in found)
    assert any("Loaded twice" in w for w in found)


def test_clean_table_is_quiet(con):
    found = checks.run_all(con, "customers")
    assert found == []


def test_guesses_key_and_date(con):
    assert store.guess_key(con, "orders") == "order_id"
    assert store.guess_date(con, "orders") == "ordered_at"


def test_text_table_is_aligned():
    text = store.as_text(["a", "bb"], [(1, "x"), (22, "yy")])
    assert text.splitlines()[0] == "a   bb"
    assert text.splitlines()[-1] == "22  yy"
