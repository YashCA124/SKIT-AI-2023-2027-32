# ML pipeline demo

The ML directory has two data paths:

- The booking ETL fetches records from `BACKEND_URL/api/ml/bookings`, then
  transforms and aggregates booking timestamps, duration, and revenue.
- The occupancy analytics consume hourly `lot_id`, `timestamp`,
  `occupancy_count`, and `capacity` rows. They calculate occupancy trends,
  detect anomalies, rank peak periods, and train/evaluate a next-hour
  Random Forest against a mean baseline.

The current backend does not expose `/api/ml/bookings`, and its booking
endpoint returns a different schema. Run the synthetic demo to exercise the
actual local ETL and occupancy analytics without a backend, credentials, or
database:

```powershell
python -m pip install -r .\ml\requirements.txt
python .\ml\demo.py
```

The demo deterministically creates `ml/data/demo/demo_bookings.csv` and
`ml/data/demo/demo_occupancy.csv`. It then writes transformed/aggregated
booking data, quality/EDA reports, occupancy forecasts, anomaly records,
and peak-hour summaries under `ml/outputs/demo/`. It injects a couple of
known occupancy spikes/drops so anomaly detection has visible examples.
Dates are UTC and span 28 synthetic days; the data is for demonstration,
not operational or real-user use.

The hourly forecast requires at least 25 observations per lot and the model
evaluation needs at least 50 training rows after feature construction. Rows
with missing or invalid timestamps/capacity/occupancy are excluded during
occupancy validation; conflicting records for the same lot and hour are
rejected.

Run the focused checks from the ML directory:

```powershell
Set-Location .\ml
python -m unittest discover -s tests -v
```
