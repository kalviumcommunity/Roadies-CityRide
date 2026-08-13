"""Tests for roadies.config."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from roadies.config import Settings, load_settings


class TestDefaultConfiguration:
    """Settings load correctly with no environment variables set."""

    def test_returns_settings_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ROADIES_ENVIRONMENT", raising=False)
        monkeypatch.delenv("ROADIES_PROJECT_DIR", raising=False)
        monkeypatch.delenv("ROADIES_RAW_DATA_DIR", raising=False)
        monkeypatch.delenv("ROADIES_PROCESSED_DATA_DIR", raising=False)
        monkeypatch.delenv("ROADIES_SYNTHETIC_DATA_DIR", raising=False)
        monkeypatch.delenv("ROADIES_DATABASE_URL", raising=False)
        monkeypatch.delenv("ROADIES_RANDOM_SEED", raising=False)

        settings = load_settings(env_file=None)
        assert isinstance(settings, Settings)

    def test_default_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ROADIES_ENVIRONMENT", raising=False)
        settings = load_settings(env_file=None)
        assert settings.environment == "local"

    def test_default_random_seed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ROADIES_RANDOM_SEED", raising=False)
        settings = load_settings(env_file=None)
        assert settings.random_seed == 42

    def test_default_paths_are_relative_to_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ROADIES_PROJECT_DIR", raising=False)
        monkeypatch.delenv("ROADIES_RAW_DATA_DIR", raising=False)
        monkeypatch.delenv("ROADIES_PROCESSED_DATA_DIR", raising=False)
        monkeypatch.delenv("ROADIES_SYNTHETIC_DATA_DIR", raising=False)

        settings = load_settings(env_file=None)
        # Paths should be under the project root
        project_root = Path(__file__).resolve().parent.parent
        assert settings.project_dir == project_root
        assert settings.raw_data_dir == project_root / "data" / "raw"
        assert settings.processed_data_dir == project_root / "data" / "processed"
        assert settings.synthetic_data_dir == project_root / "data" / "synthetic"

    def test_default_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ROADIES_DATABASE_URL", raising=False)
        monkeypatch.delenv("ROADIES_PROJECT_DIR", raising=False)
        settings = load_settings(env_file=None)
        assert "sqlite:///" in settings.database_url
        assert settings.database_url.endswith("roadies.db")


class TestEnvironmentOverrides:
    """Environment variables override defaults."""

    def test_environment_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_ENVIRONMENT", "production")
        settings = load_settings(env_file=None)
        assert settings.environment == "production"

    def test_random_seed_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_RANDOM_SEED", "123")
        settings = load_settings(env_file=None)
        assert settings.random_seed == 123

    def test_database_url_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_DATABASE_URL", "sqlite:///custom.db")
        settings = load_settings(env_file=None)
        assert settings.database_url == "sqlite:///custom.db"

    def test_raw_data_dir_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_RAW_DATA_DIR", "/tmp/test-raw")
        settings = load_settings(env_file=None)
        assert settings.raw_data_dir == Path("/tmp/test-raw")

    def test_project_dir_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_PROJECT_DIR", "/tmp/test-project")
        settings = load_settings(env_file=None)
        assert settings.project_dir == Path("/tmp/test-project")


class TestTypeConversion:
    """Configuration values are parsed into correct Python types."""

    def test_random_seed_is_int(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_RANDOM_SEED", "99")
        settings = load_settings(env_file=None)
        assert isinstance(settings.random_seed, int)
        assert settings.random_seed == 99

    def test_paths_are_path_objects(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = load_settings(env_file=None)
        assert isinstance(settings.project_dir, Path)
        assert isinstance(settings.raw_data_dir, Path)
        assert isinstance(settings.processed_data_dir, Path)
        assert isinstance(settings.synthetic_data_dir, Path)


class TestInvalidConfiguration:
    """Invalid values raise clear errors."""

    def test_invalid_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_ENVIRONMENT", "invalid")
        with pytest.raises(ValueError, match="Invalid ROADIES_ENVIRONMENT"):
            load_settings(env_file=None)

    def test_invalid_random_seed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_RANDOM_SEED", "not-a-number")
        with pytest.raises(ValueError, match="Invalid value for ROADIES_RANDOM_SEED"):
            load_settings(env_file=None)

    def test_negative_random_seed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_RANDOM_SEED", "-1")
        with pytest.raises(ValueError, match="Invalid ROADIES_RANDOM_SEED"):
            load_settings(env_file=None)


class TestPathHandling:
    """Paths are resolved correctly."""

    def test_absolute_path_preserved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROADIES_RAW_DATA_DIR", "/absolute/path")
        settings = load_settings(env_file=None)
        assert settings.raw_data_dir == Path("/absolute/path")

    def test_relative_path_resolved_from_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ROADIES_PROJECT_DIR", raising=False)
        monkeypatch.setenv("ROADIES_RAW_DATA_DIR", "custom/raw")
        settings = load_settings(env_file=None)
        assert settings.raw_data_dir == settings.project_dir / "custom" / "raw"

    def test_settings_are_frozen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ROADIES_ENVIRONMENT", raising=False)
        settings = load_settings(env_file=None)
        with pytest.raises(AttributeError):
            settings.environment = "modified"  # type: ignore[misc]
