"""SQL database integration for Roadies-CityRide.

Provides reusable functionality for creating, populating, and querying
the SQLite analytical database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH = Path("data/roadies.db")
SCHEMA_PATH = Path("sql/schemas/rides.sql")


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get a database connection.

    Parameters
    ----------
    db_path:
        Path to SQLite database.

    Returns
    -------
    sqlite3.Connection
        Database connection.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))


# ---------------------------------------------------------------------------
# Schema management
# ---------------------------------------------------------------------------

def create_schema(
    db_path: Path | str = DEFAULT_DB_PATH,
    schema_path: Path | str = SCHEMA_PATH,
) -> None:
    """Create database schema from SQL file.

    Parameters
    ----------
    db_path:
        Path to SQLite database.
    schema_path:
        Path to SQL schema file.
    """
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema_sql = schema_path.read_text()

    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)


def create_database(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create database with schema.

    Parameters
    ----------
    db_path:
        Path to SQLite database.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    create_schema(db_path)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_dataframe(
    df: pd.DataFrame,
    db_path: Path | str = DEFAULT_DB_PATH,
    table_name: str = "rides",
    if_exists: str = "replace",
) -> int:
    """Load a DataFrame into the database.

    Parameters
    ----------
    df:
        Dataset to load.
    db_path:
        Path to SQLite database.
    table_name:
        Target table name.
    if_exists:
        How to handle existing table: 'fail', 'replace', or 'append'.

    Returns
    -------
    int
        Number of rows loaded.
    """
    if df.empty:
        return 0

    with get_connection(db_path) as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)

    return len(df)


def load_dataset(
    data_path: Path | str,
    db_path: Path | str = DEFAULT_DB_PATH,
    table_name: str = "rides",
) -> int:
    """Load a CSV dataset into the database.

    Parameters
    ----------
    data_path:
        Path to CSV dataset.
    db_path:
        Path to SQLite database.
    table_name:
        Target table name.

    Returns
    -------
    int
        Number of rows loaded.
    """
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    return load_dataframe(df, db_path, table_name)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def query(sql: str, db_path: Path | str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame.

    Parameters
    ----------
    sql:
        SQL query to execute.
    db_path:
        Path to SQLite database.

    Returns
    -------
    pd.DataFrame
        Query results.
    """
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn)


def get_table_info(
    db_path: Path | str = DEFAULT_DB_PATH,
    table_name: str = "rides",
) -> pd.DataFrame:
    """Get table schema information.

    Parameters
    ----------
    db_path:
        Path to SQLite database.
    table_name:
        Table to inspect.

    Returns
    -------
    pd.DataFrame
        Table column information.
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return pd.DataFrame(columns, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"])


def get_row_count(
    db_path: Path | str = DEFAULT_DB_PATH,
    table_name: str = "rides",
) -> int:
    """Get row count for a table.

    Parameters
    ----------
    db_path:
        Path to SQLite database.
    table_name:
        Table to count.

    Returns
    -------
    int
        Row count.
    """
    result = query(f"SELECT COUNT(*) as count FROM {table_name}", db_path)
    return int(result["count"].iloc[0])


def list_tables(db_path: Path | str = DEFAULT_DB_PATH) -> list[str]:
    """List all tables in the database.

    Parameters
    ----------
    db_path:
        Path to SQLite database.

    Returns
    -------
    list[str]
        Table names.
    """
    result = query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        db_path,
    )
    return result["name"].tolist()
