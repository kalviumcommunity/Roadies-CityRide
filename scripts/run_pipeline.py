"""Run the Roadies-CityRide analytical pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from roadies.monitoring import run_pipeline


def main() -> None:
    """Execute the pipeline and report results."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Roadies-CityRide Analytical Pipeline")
    logger.info("=" * 60)

    results = run_pipeline()

    if "error" in results:
        logger.error("Pipeline failed: %s", results["error"])
        sys.exit(1)

    # Report
    logger.info("-" * 60)
    logger.info("Pipeline Results")
    logger.info("-" * 60)
    logger.info("Rows loaded: %s", results.get("rows_loaded", "N/A"))

    alert_result = results.get("alerts")
    if alert_result:
        logger.info("Alerts evaluated: %d", alert_result.total_evaluated)
        logger.info("Alerts triggered: %d", alert_result.total_triggered)

        triggered = alert_result.triggered_alerts()
        if triggered:
            logger.info("")
            logger.info("TRIGGERED ALERTS:")
            for alert in triggered:
                logger.info("  [%s] %s: %s", alert.severity.value.upper(), alert.name, alert.message)
        else:
            logger.info("No alerts triggered.")

    logger.info("=" * 60)
    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
