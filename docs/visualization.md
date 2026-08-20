# Business Visualisation — Roadies-CityRide

## Overview

Reusable Plotly chart functions for communicating key operational findings.

## Charts Implemented

### 1. City Performance Comparison (`plot_city_metric`)
- **Business Question**: How do cities compare on key metrics?
- **Chart Type**: Bar chart
- **Dimensions**: City (x), Metric (y)
- **Use**: Compare acceptance, cancellation, wait time, surge across cities

### 2. High-Demand Impact (`plot_demand_impact`)
- **Business Question**: How does high demand affect operations?
- **Chart Type**: Grouped bar chart
- **Dimensions**: Metric (x), Value (y), Demand Period (color)
- **Use**: Show normal vs high-demand differences

### 3. Demand/Supply Relationship (`plot_demand_supply_relationship`)
- **Business Question**: How does demand pressure relate to surge/wait?
- **Chart Type**: Scatter plot
- **Dimensions**: Demand/supply ratio (x), Surge (y), City (color)
- **Use**: Visualize correlation between demand pressure and outcomes

### 4. City Deterioration (`plot_city_deterioration`)
- **Business Question**: Which cities degrade most during high demand?
- **Chart Type**: Bar chart with color scale
- **Dimensions**: City (x), Deterioration (y)
- **Use**: Rank cities by high-demand degradation

### 5. Temporal Pattern (`plot_temporal_pattern`)
- **Business Question**: How do operations change by time of day?
- **Chart Type**: Line chart
- **Dimensions**: Hour (x), Metrics (y, multiple lines)
- **Use**: Show hourly patterns in acceptance, cancellation

### 6. City Heatmap (`plot_city_heatmap`)
- **Business Question**: How do cities perform across multiple metrics?
- **Chart Type**: Heatmap
- **Dimensions**: City (y), Metric (x), Value (color)
- **Use**: Compare cities across all metrics at once

## Usage

```python
from roadies.visualization import plot_city_metric, plot_demand_impact

# City comparison
fig = plot_city_metric(city_df, "rider_cancel_rate")
fig.show()

# Demand impact
fig = plot_demand_impact(demand_df)
fig.show()
```

## Design Principles

- Clear titles and axis labels
- Meaningful units and legends
- Consistent color schemes
- Appropriate chart types for data
- Minimal decoration
- Business-focused messaging
