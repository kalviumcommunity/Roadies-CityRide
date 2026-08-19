# SQL Database Setup — Roadies-CityRide

## Overview

The Roadies-CityRide project uses SQLite as its analytical database for SQL-based queries and analysis.

## Database Location

```
data/roadies.db
```

## Schema

The database contains a single table `rides` with the following structure:

| Column | Type | Description |
|---|---|---|
| ride_id | TEXT (PK) | Unique ride identifier |
| rider_id | TEXT | Rider identifier |
| driver_id | TEXT | Driver identifier |
| city | TEXT | City name |
| vehicle_type | TEXT | Vehicle type |
| ride_distance_km | REAL | Ride distance |
| ride_duration_minutes | REAL | Ride duration |
| base_fare | REAL | Base fare |
| total_fare | REAL | Total fare |
| payment_method | TEXT | Payment method |
| rider_rating | REAL | Rider rating |
| driver_rating | REAL | Driver rating |
| request_timestamp | TEXT | Request timestamp |
| was_accepted | INTEGER | Whether ride was accepted |
| ride_completed | INTEGER | Whether ride was completed |
| rider_cancelled | INTEGER | Whether rider cancelled |
| driver_cancelled | INTEGER | Whether driver cancelled |
| wait_time_minutes | REAL | Wait time |
| surge_multiplier | REAL | Surge multiplier |
| demand_supply_ratio | REAL | Demand/supply ratio |
| is_high_demand | INTEGER | High demand flag |
| demand_period | TEXT | Demand period category |
| surge_category | TEXT | Surge category |
| time_period | TEXT | Time period |

## Usage

### Creating the Database

```python
from roadies.database import create_database
create_database()  # Creates data/roadies.db with schema
```

### Loading Data

```python
from roadies.database import load_dataframe
import pandas as pd

df = pd.read_csv("data/raw/rides.csv")
load_dataframe(df)  # Loads into rides table
```

### Querying Data

```python
from roadies.database import query, get_connection

# Using query helper
df = query("SELECT city, COUNT(*) FROM rides GROUP BY city")

# Using connection directly
with get_connection() as conn:
    df = pd.read_sql("SELECT * FROM rides WHERE city = 'Mumbai'", conn)
```

### Inspecting Schema

```python
from roadies.database import get_table_info, list_tables

tables = list_tables()
info = get_table_info()
```

## Loading Strategy

- **Default**: Replace existing table on each load
- **Append mode**: Use `if_exists="append"` for incremental loads
- **Deduplication**: Primary key constraint on `ride_id` prevents duplicate rides

## Indexes

The following indexes are created for query performance:

- `idx_rides_city` on `city`
- `idx_rides_timestamp` on `request_timestamp`
- `idx_rides_demand` on `is_high_demand`
- `idx_rides_rider` on `rider_id`
- `idx_rides_driver` on `driver_id`
