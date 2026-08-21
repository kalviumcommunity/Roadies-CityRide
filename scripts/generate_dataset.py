#!/usr/bin/env python3
"""Generate the synthetic ride-sharing dataset.

Usage:
    uv run python scripts/generate_dataset.py
    uv run python scripts/generate_dataset.py --rows 10000 --seed 123
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path so we can import roadies
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from roadies.config import load_settings
from roadies.ingestion.generator import generate_rides


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic ride-sharing dataset"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=50_000,
        help="Number of ride requests to generate (default: 50000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed (default: from project config)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: data/synthetic/rides.csv)",
    )
    args = parser.parse_args()

    settings = load_settings(env_file=None)
    seed = args.seed if args.seed is not None else settings.random_seed

    output_path = Path(args.output) if args.output else settings.synthetic_data_dir / "rides.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.rows:,} rides with seed={seed}...")
    df = generate_rides(n_rows=args.rows, seed=seed)
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")
    print(f"Shape: {df.shape}")
    print(f"Cities: {df['city'].unique().tolist()}")
    print(f"Date range: {df['request_timestamp'].min()} to {df['request_timestamp'].max()}")

    # Also copy to data/raw for pipeline compatibility
    raw_path = settings.raw_data_dir / "rides.csv"
    if output_path != raw_path:
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw_path, index=False)
        print(f"Copied to {raw_path}")


if __name__ == "__main__":
    main()
