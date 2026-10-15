# REVIEW.md

List every defect you found in the starter `app/main.py` (helpers and endpoints). For each one:

| # | Where (function / line) | What is wrong | How you'd notice it (test, input, or symptom) | How you fixed it |
|---|---|---|---|---|
| 1 |compute_work_hours|Uses standard floating-point division for hours calculation, leading to precision loss|Testing fractional punch intervals results in rounding discrepancies|Replaced with Python's decimal.Decimal and ROUND_HALF_UP rounding logic|
| 2 |list_attendance| Fetches all logs into memory and sorts them using Python instead of the database|Performance degradation and high memory usage as attendance records scale up|Offloaded sorting, skipping, and limiting directly to MongoDB native queries|
| 3 | compute_late_minutes/ Punch-in| Missing explicit IST timezone handling and microsecond clearing|Timezone misalignment errors or duplicate key conflicts during rapid punch-ins| Enforced explicit IST (`UTC+05:30`) timezone awareness and truncated microseconds|
| 4 |compute_overtime|Overtime was calculated without a strict threshold or rule enforcement|Employees receiving overtime credit for minor schedule overages|Implemented a mandatory 30-minute threshold requirement before overtime minutes accrue|

Also note anything you looked at and decided was **not** a defect, and why.
POST /employees validation: Checked the employee creation logic and decided it was correct because it correctly verifies duplicate `emp_code` entries and handles 409 status conflicts.
