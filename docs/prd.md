# Product Requirements Document (PRD): Roadies-CityRide Analytics

## Problem Statement
Roadies-CityRide is experiencing challenges with rider satisfaction during peak hours. The goal of this data product is to identify, analyze, and visualize the specific factors contributing to rider experience degradation so the operations team can take targeted corrective actions.

## Success Criteria
- Deliver a fully functional Streamlit dashboard that visualizes the metrics of rider experience degradation.
- Ensure the data pipeline can successfully process and aggregate the 90-day synthetic dataset across all 6 target cities.

## Scope
- **Tech Stack:** Python, SQL, Streamlit.
- **Coverage:** 6 operating cities.
- **Data Volume:** 90-day synthetic dataset.

## Stakeholders
1. **City Operations Managers:** Need actionable insights to adjust driver incentives and routing during peak hours.
2. **Pricing Strategy Team:** Requires visibility into surge multipliers and their impact on acceptance rates.
3. **Rider Support Team:** Needs context on wait times and cancellation rates to handle customer complaints effectively.

## Key Definitions
- **High-Demand Period:** Any operational hour falling within the top 20% of total ride requests for that specific day, OR any period where the `surge_multiplier` exceeds 1.5x.
- **Rider Experience Degradation:** A quantifiable drop in service quality, measured by the following indicators:
  1. Average wait time exceeding 10 minutes.
  2. Rider cancellation rate increasing by more than 15% above the city's daily baseline.
  3. Driver acceptance rate falling below 75%.
  4. Prolonged surge levels (multiplier > 1.5x) lasting longer than 45 consecutive minutes.

## Assumptions
1. The synthetic data accurately represents the real-world distribution of ride requests and driver behavior.
2. The 6 selected cities share standard operational protocols, allowing for uniform metric comparison.
3. The necessary Python and SQL environments will be standardized across the development team.

## Risks
- **Data Quality:** The synthetic dataset may contain anomalies or missing values that skew the baseline metrics.
- **Scope Creep:** Stakeholders may request additional predictive analytics that fall outside the current retrospective analytics scope.

## Timeline
- **Phase 1:** Product Definition & Repository Setup (Current)
- **Phase 2:** SQL Data Pipeline & Metrics Design
- **Phase 3:** Python Data Processing
- **Phase 4:** Streamlit Dashboard Development
