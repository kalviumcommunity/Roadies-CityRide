# Roadies-CityRide Data Quality

> Documents the data quality policies, missing-value handling, and type standardisation for the ride-sharing dataset.

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

---

## Data-Type Standardisation

### Overview

The standardisation layer enforces the types defined by the data dictionary so downstream workflows receive predictable data.

### Target Types

| Field | Target Type | Nullable | Notes |
|---|---|---|---|
| `ride_id` | string | No | Primary key |
| `rider_id` | string | No | Foreign key |
| `driver_id` | string | Yes | Null when no driver assigned |
| `request_timestamp` | datetime | No | ISO 8601 format |
| `city` | string | No | Categorical (6 cities) |
| `accepted` | boolean | No | True/False |
| `completed` | boolean | No | True/False |
| `cancelled_by_rider` | boolean | No | True/False |
| `cancelled_by_driver` | boolean | No | True/False |
| `cancellation_reason` | string | Yes | Null when not cancelled |
| `driver_acceptance_rate` | float | Yes | 0.0–1.0 or null |
| `driver_rating` | float | Yes | 1.0–5.0 or null |
| `city_hour_requested_rides` | integer | No | 1–500 |
| `city_hour_available_drivers` | integer | No | 0–300 |
| `demand_level` | string | No | Categorical (4 levels) |
| `surge_multiplier` | float | No | 1.0–5.0 |
| `base_fare` | float | No | 50.0–500.0 INR |
| `wait_time_minutes` | float | Yes | 0.0–60.0 or null |
| `trip_duration_minutes` | float | Yes | 0.0–120.0 or null |
| `trip_distance_km` | float | Yes | 0.0–50.0 or null |

### Conversion Rules

| Input | Output | Rule |
|---|---|---|
| `"true"` / `"True"` / `"1"` | `True` | Boolean string mapping |
| `"false"` / `"False"` / `"0"` | `False` | Boolean string mapping |
| Numeric string (`"100"`) | `100` | `pd.to_numeric` with coerce |
| ISO datetime string | `datetime64[ns]` | `pd.to_datetime` with coerce |
| Already correct type | No change | Skipped |

### Invalid-Value Behaviour

- Conversion failures are reported in `StandardizationResult.conversions`
- Failed values are accessible via `ColumnConversion.failure_values`
- The workflow does **not** drop rows with conversion failures
- Invalid values remain as `NaN` in the output

### Nullable-Field Handling

Nullable fields (`driver_id`, `cancellation_reason`, `driver_acceptance_rate`, `driver_rating`, `wait_time_minutes`, `trip_duration_minutes`, `trip_distance_km`) remain nullable after standardisation. Null values are never imputed during type conversion.

### Workflow

```python
from roadies.quality.standardize import standardize_dtypes
from roadies.quality.validator import validate_dataset

# Standardise types
result = standardize_dtypes(df)
clean_df = result.df

# Verify
print(result.summary())

# Validate
validation = validate_dataset(clean_df)
assert validation.passed
```

### Complete Pipeline

```
load_dataset(...)
    ↓
validate_dataset(...)        # structural validation
    ↓
standardize_dtypes(...)      # enforce data types
    ↓
profile_missing_values(...)  # classify nulls
    ↓
impute_missing_values(...)   # apply strategies (keep null by default)
    ↓
validate_dataset(...)        # verify post-imputation validity
```

---

## Duplicate Detection and Deduplication

### What Counts as a Duplicate

| Type | Definition | Handling |
|---|---|---|
| **Exact duplicate row** | All fields identical to another row | Remove redundant copy, keep first |
| **Duplicate ride ID** | Same `ride_id` appears more than once | Investigate; remove if identical |
| **Conflicting duplicate** | Same `ride_id` but different field values | Report conflict; keep first occurrence |

### Deduplication Policy

1. **Exact duplicates**: Remove redundant copies. Retain the first occurrence deterministically.
2. **Duplicate ride IDs (identical)**: Remove redundant copies. Retain the first occurrence.
3. **Conflicting records**: Do NOT silently discard. Report as conflicts. Retain first occurrence for downstream processing.

### Workflow

```python
from roadies.quality.deduplication import detect_duplicates, deduplicate_dataset

# Detect only (no changes)
report = detect_duplicates(df)
print(report.summary())

# Detect and deduplicate
result = deduplicate_dataset(df)
clean_df = result.df
conflicts = result.conflicts_df  # None if no conflicts
```

### Complete Pipeline

```
load_dataset(...)
    ↓
validate_dataset(...)        # structural validation
    ↓
standardize_dtypes(...)      # enforce data types
    ↓
detect_duplicates(...)       # detect without removing
    ↓
deduplicate_dataset(...)     # remove exact dups, report conflicts
    ↓
profile_missing_values(...)  # classify nulls
    ↓
impute_missing_values(...)   # apply strategies
    ↓
validate_dataset(...)        # final validation
```

---

## String Cleaning and Text Normalisation

### Fields Affected

| Field | Normalisation | Canonical Form |
|---|---|---|
| `city` | Case + whitespace + canonical map | Title case (`Mumbai`, `Delhi`, etc.) |
| `demand_level` | Case + whitespace + canonical map | Lowercase (`low`, `medium`, `high`, `critical`) |
| `cancellation_reason` | Case + whitespace + canonical map | Title case (`Long wait time`, etc.) |
| `ride_id` | Whitespace only | As-is (already clean) |
| `rider_id` | Whitespace only | As-is (already clean) |
| `driver_id` | Whitespace only | As-is (already clean) |

### Normalisation Rules

1. **Whitespace**: Strip leading/trailing; collapse repeated internal whitespace
2. **Case**: Map to canonical form via lookup dictionary
3. **Textual nulls**: Convert `""`, `" "`, `"NA"`, `"N/A"`, `"null"`, etc. to actual `None`

### Canonical Representations

**Cities**: Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Pune (title case)

**Demand levels**: low, medium, high, critical (lowercase)

**Cancellation reasons**: Long wait time, Driver rude, Changed mind, Vehicle quality, Other (title case)

### Textual Null Handling

The following strings are treated as missing values and converted to `None`:

```
""  " "  "NA"  "N/A"  "null"  "None"  "NULL"  "nan"  "NaN"  "-"  "n/a"  "na"
```

### Workflow

```python
from roadies.quality.string_clean import clean_strings

cleaned_df, report = clean_strings(df)
print(report.summary())
```

### Complete Pipeline

```
load_dataset(...)
    ↓
validate_dataset(...)
    ↓
clean_strings(...)           # normalise text
    ↓
standardize_dtypes(...)
    ↓
detect_duplicates(...)
    ↓
deduplicate_dataset(...)
    ↓
profile_missing_values(...)
    ↓
impute_missing_values(...)
    ↓
validate_dataset(...)
```
