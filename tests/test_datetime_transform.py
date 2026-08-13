"""Tests for date/time transformation pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.datetime_transform import (
    DatetimeTransformReport,
    transform_datetime,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts_df(timestamps: list[str | None]) -> pd.DataFrame:
    return pd.DataFrame({"request_timestamp": timestamps})


# ---------------------------------------------------------------------------
# Valid timestamp conversion
# ---------------------------------------------------------------------------

class TestValidTimestamps:
    def test_iso_format(self) -> None:
        df = _ts_df(["2025-06-15T10:30:00Z"])
        result, report = transform_datetime(df)
        assert report.valid_timestamps == 1
        assert result["year"].iloc[0] == 2025
        assert result["month"].iloc[0] == 6
        assert result["hour"].iloc[0] == 10

    def test_date_only(self) -> None:
        df = _ts_df(["2025-01-01"])
        result, _ = transform_datetime(df)
        assert result["date"].iloc[0] == "2025-01-01"

    def test_multiple_valid(self) -> None:
        df = _ts_df(["2025-03-10T08:00:00Z", "2025-07-20T18:30:00Z"])
        _, report = transform_datetime(df)
        assert report.valid_timestamps == 2
        assert report.invalid_timestamps == 0


# ---------------------------------------------------------------------------
# Invalid timestamp handling
# ---------------------------------------------------------------------------

class TestInvalidTimestamps:
    def test_garbage_string(self) -> None:
        df = _ts_df(["not-a-date", "2025-01-01T00:00:00Z"])
        _, report = transform_datetime(df)
        assert report.invalid_timestamps == 1
        assert report.valid_timestamps == 1


# ---------------------------------------------------------------------------
# Missing timestamp handling
# ---------------------------------------------------------------------------

class TestMissingTimestamps:
    def test_none_missing(self) -> None:
        df = _ts_df([None])
        _, report = transform_datetime(df)
        assert report.missing_timestamps == 1

    def test_empty_string_missing(self) -> None:
        df = _ts_df([""])
        _, report = transform_datetime(df)
        assert report.missing_timestamps == 1

    def test_whitespace_only_missing(self) -> None:
        df = _ts_df(["   "])
        _, report = transform_datetime(df)
        assert report.missing_timestamps == 1


# ---------------------------------------------------------------------------
# Timezone behaviour
# ---------------------------------------------------------------------------

class TestTimezone:
    def test_utc_timezone(self) -> None:
        df = _ts_df(["2025-06-15T10:30:00Z"])
        result, report = transform_datetime(df)
        assert report.timezone == "UTC"
        assert str(result["request_timestamp"].dt.tz) == "UTC"


# ---------------------------------------------------------------------------
# Derived fields
# ---------------------------------------------------------------------------

class TestDerivedFields:
    def test_weekend_detection(self) -> None:
        # Saturday
        df = _ts_df(["2025-06-14T12:00:00Z"])
        result, _ = transform_datetime(df)
        assert result["is_weekend"].iloc[0] == True

    def test_weekday_detection(self) -> None:
        # Monday
        df = _ts_df(["2025-06-16T12:00:00Z"])
        result, _ = transform_datetime(df)
        assert result["is_weekend"].iloc[0] == False

    def test_time_period(self) -> None:
        df = _ts_df(["2025-06-15T03:00:00Z"])
        result, _ = transform_datetime(df)
        assert result["time_period"].iloc[0] == "night"

    def test_day_name(self) -> None:
        df = _ts_df(["2025-06-15T12:00:00Z"])
        result, _ = transform_datetime(df)
        assert result["day_name"].iloc[0] == "Sunday"

    def test_hour(self) -> None:
        df = _ts_df(["2025-06-15T14:30:00Z"])
        result, _ = transform_datetime(df)
        assert result["hour"].iloc[0] == 14


# ---------------------------------------------------------------------------
# Missing column
# ---------------------------------------------------------------------------

class TestMissingColumn:
    def test_no_timestamp_column(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai"]})
        _, report = transform_datetime(df)
        assert report.total_rows == 1
        assert report.valid_timestamps == 0


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDatasetIntegration:
    def test_generated_dataset_transforms(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        result, report = transform_datetime(df)
        assert report.valid_timestamps > 0
        assert "date" in result.columns
        assert "hour" in result.columns
        assert "is_weekend" in result.columns
