# Roadies-CityRide Data Quality — Missing Values

> Documents the missing-value policy, field-level rules, and imputation strategies for the ride-sharing dataset.

## Overview

The dataset contains **239,687 missing values** across 50,000 rows. All missing values are **structurally expected** — they arise from the business logic of ride requests, not from data quality failures.

## Missing Value Policy

### Principle

Not every missing value is an error. In ride-sharing data, nulls often encode meaningful information:

- A ride with no driver assigned has no driver metrics
- A ride that was not completed has no trip duration
- A ride that was not cancelled has no cancellation reason

The missing-value workflow distinguishes between:

1. **Expected nulls** — structurally valid, should remain null
2. **Conditional nulls** — depend on another field's value, should remain null
3. **Unexpected nulls** — not documented, flagged for review

## Field-Level Missingness Rules

| Field | Null Count (50k) | Null % | Missingness Type | Strategy | Reason |
|---|---|---|---|---|---|
| `driver_id` | ~25,592 | 51.2% | Conditional | Keep null | Null when no driver was assigned |
| `cancellation_reason` | ~48,485 | 97.0% | Conditional | Keep null | Null when neither party cancelled |
| `driver_acceptance_rate` | ~32,516 | 65.0% | Conditional | Keep null | Null when no driver assigned |
| `driver_rating` | ~32,516 | 65.0% | Conditional | Keep null | Null when no driver assigned |
| `wait_time_minutes` | ~32,516 | 65.0% | Conditional | Keep null | Null when ride not accepted |
| `trip_duration_minutes` | ~34,031 | 68.1% | Conditional | Keep null | Null when ride not completed |
| `trip_distance_km` | ~34,031 | 68.1% | Conditional | Keep null | Null when ride not completed |

## Imputation Strategies

### Current: No Imputation Required

All missing values in the generated dataset are **expected conditional nulls**. No imputation is performed. The default strategy for every nullable field is `keep_null`.

### When Imputation Would Be Needed

If future analysis requires complete values for fields like `wait_time_minutes` or `driver_acceptance_rate`, the following strategies would be appropriate:

| Field | Strategy | Rationale |
|---|---|---|
| `wait_time_minutes` | Group median by city + demand_level | Wait times vary by city and demand |
| `driver_acceptance_rate` | Median | Historical rate, stable within driver |
| `driver_rating` | Median | Historical rating, stable within driver |
| `trip_duration_minutes` | Group median by city | Trip times vary by city geography |
| `trip_distance_km` | Group median by city | Distances vary by city geography |

### Strategies NOT Recommended

- **Mean for wait_time_minutes**: Skewed distribution with long tail; median is more robust
- **Mode**: Numeric fields have too many unique values for mode to be meaningful
- **Global median for all fields**: Ignores city-level differences
- **Dropping rows**: Would remove ~65% of the dataset

## Workflow

```python
from roadies.quality.missing_values import profile_missing_values, impute_missing_values

# Step 1: Profile missing values
profile = profile_missing_values(df)
print(profile.summary())

# Step 2: Impute (all expected nulls retained by default)
result = impute_missing_values(df)
clean_df = result.df

# Step 3: Validate after imputation
from roadies.quality.validator import validate_dataset
validation = validate_dataset(clean_df)
assert validation.passed
```

## Complete Pipeline

```
load_dataset(...)
    ↓
validate_dataset(...)     # structural validation
    ↓
profile_missing_values(...)  # identify and classify nulls
    ↓
impute_missing_values(...)   # apply field-specific strategies
    ↓
validate_dataset(...)     # verify post-imputation validity
```

## Validation After Imputation

After imputation (or retention of expected nulls), the following checks pass:

- Required fields (`ride_id`, `rider_id`) remain populated
- Categorical values remain within documented categories
- Numeric values remain within documented ranges
- Logical constraints remain consistent
- Expected nulls remain null
- No invalid values introduced

## Key Findings from Generated Dataset

- **100% of rows** contain at least one missing value
- **All missing values** are expected conditional nulls
- **0 values imputed** — all nulls are structurally valid
- **7 fields** contain missing values, all documented in the data dictionary
