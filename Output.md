# API Execution & Sample Outputs

## How to Test the API
1. Start the FastAPI server using Uvicorn:
   ```bash
   uvicorn app.main:app --reload --port 8000
  Sample Endpoint Outputs
  1. Punch In (POST /attendance/punch-in)
    Request Payload:
 {
  "emp_code": "EMP001",
  "status": "PRESENT"
 }
 Response Output (201 Created):
{
  "emp_code": "EMP001",
  "date": "2026-10-15",
  "status": "PRESENT",
  "punch_in": "2026-10-15T09:35:00+05:30",
  "punch_out": null,
  "work_hours": null,
  "late_minutes": 5,
  "overtime_minutes": 0,
  "half_day": false,
  "history": [],
  "id": "670f1234567890abcdef1234"
}
2.Punch Out
Request Payload:
{
  "emp_code": "EMP001"
}

Response Output (200 OK):
{
  "emp_code": "EMP001",
  "date": "2026-10-15",
  "status": "PRESENT",
  "punch_in": "2026-10-15T09:35:00+05:30",
  "punch_out": "2026-10-15T18:45:00+05:30",
  "work_hours": 9.17,
  "late_minutes": 5,
  "overtime_minutes": 15,
  "half_day": false,
  "history": [],
  "id": "670f1234567890abcdef1234"
}
3.Monthly Analytics 
(GET /analytics/employees/EMP001/monthly?year=2026&month=10)
Response Output (200 OK):
{
  "emp_code": "EMP001",
  "year": 2026,
  "month": 10,
  "total_days_present": 12,
  "total_work_hours": 108.5,
  "total_overtime_minutes": 120,
  "avg_late_minutes": 4.17
}

      

