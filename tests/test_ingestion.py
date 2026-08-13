"""Tests for CSV and JSON ingestion loaders."""

from __future__ import annotations

import json
import pytest
import pandas as pd

from roadies.ingestion.loaders import (
    IngestionError,
    load_csv,
    load_json,
    load_dataset,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_csv(tmp_path):
    """Create a small CSV file for testing."""
    df = pd.DataFrame(
        {
            "ride_id": ["R-001", "R-002", "R-003"],
            "city": ["Mumbai", "Delhi", "Bangalore"],
            "surge_multiplier": [1.5, 1.2, 1.0],
        }
    )
    path = tmp_path / "test.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_json(tmp_path):
    """Create a small JSON Lines file for testing."""
    records = [
        {"ride_id": "R-001", "city": "Mumbai", "surge_multiplier": 1.5},
        {"ride_id": "R-002", "city": "Delhi", "surge_multiplier": 1.2},
        {"ride_id": "R-003", "city": "Bangalore", "surge_multiplier": 1.0},
    ]
    path = tmp_path / "test.json"
    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return path


@pytest.fixture
def empty_csv(tmp_path):
    """Create an empty CSV file."""
    path = tmp_path / "empty.csv"
    path.write_text("")
    return path


@pytest.fixture
def malformed_csv(tmp_path):
    """Create a malformed CSV file."""
    path = tmp_path / "malformed.csv"
    path.write_text("col_a,col_b\n1,2\n1,2,3,4,5")
    return path


@pytest.fixture
def malformed_json(tmp_path):
    """Create a malformed JSON file."""
    path = tmp_path / "malformed.json"
    path.write_text("{invalid json content")
    return path


# ---------------------------------------------------------------------------
# CSV Loading
# ---------------------------------------------------------------------------


class TestLoadCSV:
    def test_loads_successfully(self, sample_csv):
        df = load_csv(sample_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_preserves_columns(self, sample_csv):
        df = load_csv(sample_csv)
        assert list(df.columns) == ["ride_id", "city", "surge_multiplier"]

    def test_preserves_values(self, sample_csv):
        df = load_csv(sample_csv)
        assert df["ride_id"].tolist() == ["R-001", "R-002", "R-003"]
        assert df["city"].iloc[0] == "Mumbai"

    def test_row_count(self, sample_csv):
        df = load_csv(sample_csv)
        assert len(df) == 3


# ---------------------------------------------------------------------------
# JSON Loading
# ---------------------------------------------------------------------------


class TestLoadJSON:
    def test_loads_successfully(self, sample_json):
        df = load_json(sample_json)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_preserves_columns(self, sample_json):
        df = load_json(sample_json)
        assert set(df.columns) == {"ride_id", "city", "surge_multiplier"}

    def test_preserves_values(self, sample_json):
        df = load_json(sample_json)
        assert "R-001" in df["ride_id"].values

    def test_row_count(self, sample_json):
        df = load_json(sample_json)
        assert len(df) == 3


# ---------------------------------------------------------------------------
# Missing File Handling
# ---------------------------------------------------------------------------


class TestMissingFile:
    def test_csv_missing_file(self):
        with pytest.raises(IngestionError, match="File not found"):
            load_csv("/nonexistent/path/data.csv")

    def test_json_missing_file(self):
        with pytest.raises(IngestionError, match="File not found"):
            load_json("/nonexistent/path/data.json")

    def test_dataset_missing_file(self):
        with pytest.raises(IngestionError, match="File not found"):
            load_dataset("/nonexistent/path/data.csv")


# ---------------------------------------------------------------------------
# Unsupported Format
# ---------------------------------------------------------------------------


class TestUnsupportedFormat:
    def test_unsupported_extension(self, tmp_path):
        path = tmp_path / "data.parquet"
        path.write_text("fake data")
        with pytest.raises(IngestionError, match="Unsupported file format"):
            load_dataset(path)


# ---------------------------------------------------------------------------
# Malformed Input
# ---------------------------------------------------------------------------


class TestMalformedInput:
    def test_malformed_csv(self, malformed_csv):
        # Pandas may still parse this, but if it fails we get IngestionError
        try:
            df = load_csv(malformed_csv)
            # If it loads, it should still be a valid DataFrame
            assert isinstance(df, pd.DataFrame)
        except IngestionError:
            pass  # Expected if parsing fails

    def test_malformed_json(self, malformed_json):
        with pytest.raises(IngestionError, match="Failed to read JSON"):
            load_json(malformed_json)


# ---------------------------------------------------------------------------
# Empty Dataset
# ---------------------------------------------------------------------------


class TestEmptyDataset:
    def test_empty_csv(self, empty_csv):
        with pytest.raises(IngestionError):
            load_csv(empty_csv)

    def test_empty_json(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("")
        with pytest.raises(IngestionError):
            load_json(path)


# ---------------------------------------------------------------------------
# Format Detection
# ---------------------------------------------------------------------------


class TestFormatDetection:
    def test_csv_detected(self, sample_csv):
        df = load_dataset(sample_csv)
        assert len(df) == 3

    def test_json_detected(self, sample_json):
        df = load_dataset(sample_json)
        assert len(df) == 3


# ---------------------------------------------------------------------------
# Integration with Generated Dataset
# ---------------------------------------------------------------------------


class TestGeneratedDatasetIngestion:
    """Verify that the synthetic dataset from Issue #12 can be ingested."""

    def test_load_generated_csv(self, tmp_path):
        from roadies.ingestion.generator import generate_rides

        # Generate a small dataset
        df_generated = generate_rides(n_rows=100, seed=42)
        csv_path = tmp_path / "generated.csv"
        df_generated.to_csv(csv_path, index=False)

        # Load it back through the ingestion layer
        df_loaded = load_csv(csv_path)

        assert len(df_loaded) == 100
        assert list(df_loaded.columns) == list(df_generated.columns)
        assert df_loaded["ride_id"].is_unique
