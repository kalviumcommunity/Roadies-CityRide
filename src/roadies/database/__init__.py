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


# ---------------------------------------------------------------------------
# Business metrics queries
# ---------------------------------------------------------------------------

QUERIES_PATH = Path("sql/queries")


def execute_metric_query(
    query_name: str,
    db_path: Path | str = DEFAULT_DB_PATH,
    queries_path: Path | str = QUERIES_PATH,
) -> pd.DataFrame:
    """Execute a named metric query from the SQL queries directory.

    Parameters
    ----------
    query_name:
        Name of the query (e.g., 'core_metrics', 'city_metrics').
    db_path:
        Path to SQLite database.
    queries_path:
        Path to SQL queries directory.

    Returns
    -------
    pd.DataFrame
        Query results.
    """
    queries_path = Path(queries_path)

    # Map query names to SQL statements
    query_map = {
        "core_metrics": _core_metrics_sql(),
        "city_metrics": _city_metrics_sql(),
        "demand_comparison": _demand_comparison_sql(),
        "daily_metrics": _daily_metrics_sql(),
        "hourly_metrics": _hourly_metrics_sql(),
        "city_deterioration": _city_deterioration_sql(),
    }

    sql = query_map.get(query_name)
    if sql is None:
        raise ValueError(f"Unknown query: {query_name}")

    return query(sql, db_path)


def _core_metrics_sql() -> str:
    return """
    SELECT
        COUNT(*) AS total_rides,
        SUM(was_accepted) AS accepted_rides,
        SUM(ride_completed) AS completed_rides,
        SUM(rider_cancelled) AS rider_cancellations,
        SUM(driver_cancelled) AS driver_cancellations,
        ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
        ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
        ROUND(SUM(driver_cancelled) * 100.0 / COUNT(*), 2) AS driver_cancel_rate,
        ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
        ROUND(AVG(surge_multiplier), 2) AS avg_surge,
        ROUND(AVG(demand_supply_ratio), 2) AS avg_demand_supply_ratio,
        ROUND(SUM(CASE WHEN is_high_demand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS high_demand_share
    FROM rides
    """


def _city_metrics_sql() -> str:
    return """
    SELECT
        city,
        COUNT(*) AS ride_volume,
        ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
        ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
        ROUND(SUM(driver_cancelled) * 100.0 / COUNT(*), 2) AS driver_cancel_rate,
        ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
        ROUND(AVG(surge_multiplier), 2) AS avg_surge,
        ROUND(AVG(demand_supply_ratio), 2) AS avg_demand_supply_ratio,
        ROUND(SUM(CASE WHEN is_high_demand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS high_demand_share
    FROM rides
    GROUP BY city
    ORDER BY ride_volume DESC
    """


def _demand_comparison_sql() -> str:
    return """
    SELECT
        CASE WHEN is_high_demand = 1 THEN 'high' ELSE 'normal' END AS demand_period,
        COUNT(*) AS ride_count,
        ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
        ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
        ROUND(SUM(driver_cancelled) * 100.0 / COUNT(*), 2) AS driver_cancel_rate,
        ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
        ROUND(AVG(surge_multiplier), 2) AS avg_surge,
        ROUND(AVG(demand_supply_ratio), 2) AS avg_demand_supply_ratio
    FROM rides
    GROUP BY is_high_demand
    ORDER BY is_high_demand
    """


def _daily_metrics_sql() -> str:
    return """
    SELECT
        DATE(request_timestamp) AS ride_date,
        COUNT(*) AS ride_count,
        ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
        ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
        ROUND(AVG(surge_multiplier), 2) AS avg_surge
    FROM rides
    GROUP BY DATE(request_timestamp)
    ORDER BY ride_date
    """


def _hourly_metrics_sql() -> str:
    return """
    SELECT
        STRFTIME('%H', request_timestamp) AS ride_hour,
        COUNT(*) AS ride_count,
        ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
        ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time
    FROM rides
    GROUP BY STRFTIME('%H', request_timestamp)
    ORDER BY ride_hour
    """


def _city_deterioration_sql() -> str:
    return """
    WITH city_normal AS (
        SELECT
            city,
            COUNT(*) AS normal_rides,
            ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS normal_acceptance,
            ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS normal_completion,
            ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS normal_cancel,
            ROUND(AVG(wait_time_minutes), 2) AS normal_wait,
            ROUND(AVG(surge_multiplier), 2) AS normal_surge
        FROM rides
        WHERE is_high_demand = 0
        GROUP BY city
    ),
    city_high AS (
        SELECT
            city,
            COUNT(*) AS high_rides,
            ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS high_acceptance,
            ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS high_completion,
            ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS high_cancel,
            ROUND(AVG(wait_time_minutes), 2) AS high_wait,
            ROUND(AVG(surge_multiplier), 2) AS high_surge
        FROM rides
        WHERE is_high_demand = 1
        GROUP BY city
    )
    SELECT
        n.city,
        n.normal_rides,
        h.high_rides,
        n.normal_acceptance,
        h.high_acceptance,
        ROUND(h.high_acceptance - n.normal_acceptance, 2) AS acceptance_change,
        n.normal_completion,
        h.high_completion,
        ROUND(h.high_completion - n.normal_completion, 2) AS completion_change,
        n.normal_cancel,
        h.high_cancel,
        ROUND(h.high_cancel - n.normal_cancel, 2) AS cancel_change,
        n.normal_wait,
        h.high_wait,
        ROUND(h.high_wait - n.normal_wait, 2) AS wait_change,
        n.normal_surge,
        h.high_surge,
        ROUND(h.high_surge - n.normal_surge, 2) AS surge_change
    FROM city_normal n
    JOIN city_high h ON n.city = h.city
    ORDER BY cancel_change DESC
    """
