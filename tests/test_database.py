"""Tests for SQL database integration."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.database import (
    create_database,
    create_schema,
    get_connection,
    get_row_count,
    get_table_info,
    list_tables,
    load_dataframe,
    load_dataset,
    query,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(n)],
        "rider_id": np.random.choice([f"rider-{i}" for i in range(10)], n),
        "driver_id": np.random.choice([f"driver-{i}" for i in range(15)], n),
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "ride_completed": np.random.choice([True, False], n, p=[0.7, 0.3]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "demand_supply_ratio": np.random.uniform(0.5, 2.0, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


# ---------------------------------------------------------------------------
# Database creation
# ---------------------------------------------------------------------------

class TestDatabaseCreation:
    def test_create_database(self, temp_db: Path) -> None:
        create_database(temp_db)
        assert temp_db.exists()

    def test_get_connection(self, temp_db: Path) -> None:
        create_database(temp_db)
        conn = get_connection(temp_db)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

class TestTableCreation:
    def test_tables_exist(self, temp_db: Path) -> None:
        create_database(temp_db)
        tables = list_tables(temp_db)
        assert "rides" in tables

    def test_schema_columns(self, temp_db: Path) -> None:
        create_database(temp_db)
        info = get_table_info(temp_db)
        column_names = info["name"].tolist()
        assert "ride_id" in column_names
        assert "city" in column_names


# ---------------------------------------------------------------------------
# Primary key behaviour
# ---------------------------------------------------------------------------

class TestPrimaryKey:
    def test_ride_id_is_pk(self, temp_db: Path) -> None:
        create_database(temp_db)
        info = get_table_info(temp_db)
        pk_row = info[info["pk"] == 1]
        assert len(pk_row) == 1
        assert pk_row["name"].iloc[0] == "ride_id"


# ---------------------------------------------------------------------------
# Row count after loading
# ---------------------------------------------------------------------------

class TestRowCount:
    def test_row_count(self, temp_db: Path) -> None:
        create_database(temp_db)
        df = _sample_df()
        load_dataframe(df, temp_db)
        count = get_row_count(temp_db)
        assert count == 100


# ---------------------------------------------------------------------------
# Loading empty dataset
# ---------------------------------------------------------------------------

class TestEmptyDataset:
    def test_empty_load(self, temp_db: Path) -> None:
        create_database(temp_db)
        df = pd.DataFrame()
        rows = load_dataframe(df, temp_db)
        assert rows == 0


# ---------------------------------------------------------------------------
# Repeated loading
# ---------------------------------------------------------------------------

class TestRepeatedLoading:
    def test_replace_behavior(self, temp_db: Path) -> None:
        create_database(temp_db)
        df = _sample_df()
        load_dataframe(df, temp_db)
        load_dataframe(df, temp_db, if_exists="replace")
        count = get_row_count(temp_db)
        assert count == 100


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------

class TestQuerying:
    def test_query(self, temp_db: Path) -> None:
        create_database(temp_db)
        df = _sample_df()
        load_dataframe(df, temp_db)
        result = query("SELECT COUNT(*) as count FROM rides", temp_db)
        assert result["count"].iloc[0] == 100

    def test_query_with_filter(self, temp_db: Path) -> None:
        create_database(temp_db)
        df = _sample_df()
        load_dataframe(df, temp_db)
        result = query("SELECT * FROM rides WHERE city = 'Mumbai'", temp_db)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_workflow(self, temp_db: Path) -> None:
        create_database(temp_db)
        df = _sample_df()
        rows = load_dataframe(df, temp_db)
        assert rows == 100

        count = get_row_count(temp_db)
        assert count == 100

        tables = list_tables(temp_db)
        assert "rides" in tables

        info = get_table_info(temp_db)
        assert "ride_id" in info["name"].values
