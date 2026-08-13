"""Centralised configuration for Roadies-CityRide.

Loads settings from environment variables with sensible defaults.
Supports .env files via python-dotenv.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_VALID_ENVIRONMENTS = frozenset({"local", "development", "staging", "production"})


@dataclass(frozen=True)
class Settings:
    """Immutable project configuration."""

    environment: str
    project_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    synthetic_data_dir: Path
    database_url: str
    random_seed: int


def _resolve_path(base: Path, value: str) -> Path:
    """Resolve a path relative to *base* unless it is already absolute."""
    p = Path(value)
    return p if p.is_absolute() else base / p


def _parse_int(value: str, name: str) -> int:
    """Parse an integer, raising a clear error on failure."""
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"Invalid value for {name}: {value!r}. Expected an integer."
        ) from None


def load_settings(
    env_file: str | Path | None = ".env",
    *,
    _environ: dict[str, str] | None = None,
) -> Settings:
    """Load settings from environment variables, optionally reading a .env file.

    Parameters
    ----------
    env_file:
        Path to a .env file to load.  Use ``None`` to skip file loading.
    _environ:
        Internal: override the environment dict (for testing).
    """
    load_dotenv(env_file)

    env = _environ if _environ is not None else os.environ

    # --- environment ---
    environment = env.get("ROADIES_ENVIRONMENT", "local")
    if environment not in _VALID_ENVIRONMENTS:
        raise ValueError(
            f"Invalid ROADIES_ENVIRONMENT: {environment!r}. "
            f"Must be one of: {', '.join(sorted(_VALID_ENVIRONMENTS))}"
        )

    # --- paths ---
    project_dir = _resolve_path(_PROJECT_ROOT, env.get("ROADIES_PROJECT_DIR", "."))
    raw_data_dir = _resolve_path(
        project_dir, env.get("ROADIES_RAW_DATA_DIR", "data/raw")
    )
    processed_data_dir = _resolve_path(
        project_dir, env.get("ROADIES_PROCESSED_DATA_DIR", "data/processed")
    )
    synthetic_data_dir = _resolve_path(
        project_dir, env.get("ROADIES_SYNTHETIC_DATA_DIR", "data/synthetic")
    )

    # --- database ---
    default_db = f"sqlite:///{project_dir / 'data' / 'roadies.db'}"
    database_url = env.get("ROADIES_DATABASE_URL", default_db)

    # --- random seed ---
    random_seed = _parse_int(env.get("ROADIES_RANDOM_SEED", "42"), "ROADIES_RANDOM_SEED")
    if random_seed < 0:
        raise ValueError(
            f"Invalid ROADIES_RANDOM_SEED: {random_seed}. Must be non-negative."
        )

    return Settings(
        environment=environment,
        project_dir=project_dir,
        raw_data_dir=raw_data_dir,
        processed_data_dir=processed_data_dir,
        synthetic_data_dir=synthetic_data_dir,
        database_url=database_url,
        random_seed=random_seed,
    )
