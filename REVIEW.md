# REVIEW.md

List every defect you found in the starter `app/main.py` (helpers and endpoints). For each one:

| # | Where (function / line) | What is wrong | How you'd notice it (test, input, or symptom) | How you fixed it |
|---|---|---|---|---|
| 1 |compute_work_hours|Uses standard floating-point division for hours calculation, leading to precision loss|Testing fractional punch intervals results in rounding discrepancies|Replaced with Python's decimal.Decimal and ROUND_HALF_UP rounding logic|
| 2 |list_attendance| Fetches all logs into memory and sorts them using Python instead of the database|Performance degradation and high memory usage as attendance records scale up|Offloaded sorting, skipping, and limiting directly to MongoDB native queries|



Also note anything you looked at and decided was **not** a defect, and why.
