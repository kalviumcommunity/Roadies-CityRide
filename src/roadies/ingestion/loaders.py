"""File ingestion loaders for CSV and JSON datasets.

Provides functions to load ride-sharing data from files into Pandas DataFrames.
The ingestion layer performs only structural checks — no cleaning or transformation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".json"})


class IngestionError(Exception):
    """Raised when a dataset cannot be loaded."""


def _verify_file(path: Path) -> None:
    """Check that the file exists and has a supported extension."""
    if not path.exists():
        raise IngestionError(f"File not found: {path}")
    if not path.is_file():
        raise IngestionError(f"Path is not a file: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise IngestionError(
            f"Unsupported file format: {path.suffix!r}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )


def _verify_not_empty(df: pd.DataFrame, path: Path) -> None:
    """Check that the loaded DataFrame is not empty."""
    if df.empty:
        raise IngestionError(f"Dataset is empty: {path}")


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a Pandas DataFrame.

    Parameters
    ----------
    path:
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.

    Raises
    ------
    IngestionError
        If the file is missing, unsupported, empty, or cannot be parsed.
    """
    path = Path(path)
    _verify_file(path)

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise IngestionError(f"Failed to read CSV: {path}") from exc

    _verify_not_empty(df, path)
    return df


def load_json(path: str | Path) -> pd.DataFrame:
    """Load a JSON file into a Pandas DataFrame.

    Expects JSON Lines format (one JSON object per line) or a JSON array.

    Parameters
    ----------
    path:
        Path to the JSON file.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.

    Raises
    ------
    IngestionError
        If the file is missing, unsupported, empty, or cannot be parsed.
    """
    path = Path(path)
    _verify_file(path)

    try:
        df = pd.read_json(path, lines=True)
    except ValueError:
        # Try standard JSON array format if lines format fails
        try:
            df = pd.read_json(path)
        except Exception as exc:
            raise IngestionError(f"Failed to read JSON: {path}") from exc
    except Exception as exc:
        raise IngestionError(f"Failed to read JSON: {path}") from exc

    _verify_not_empty(df, path)
    return df


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a dataset by detecting format from file extension.

    Parameters
    ----------
    path:
        Path to the dataset file.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.

    Raises
    ------
    IngestionError
        If the format is unsupported or the file cannot be loaded.
    """
    path = Path(path)
    _verify_file(path)

    ext = path.suffix.lower()
    if ext == ".csv":
        return load_csv(path)
    elif ext == ".json":
        return load_json(path)
    else:
        # Should not reach here due to _verify_file, but handle defensively
        raise IngestionError(
            f"Unsupported file format: {ext!r}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
