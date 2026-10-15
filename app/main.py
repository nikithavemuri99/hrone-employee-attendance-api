"""
Employee Attendance & Analytics API - STARTER

Run:  uvicorn app.main:app --port 8000
Env:  MONGO_URI, MONGO_DB (a local .env is loaded for convenience)

This file was written quickly by a colleague who has left the company. The happy path
works, but nobody has reviewed it. Read PROBLEM_STATEMENT.docx for what is expected of you,
openapi.yaml for the contract and DATA_MODEL.md for what is stored in MongoDB.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from decimal import Decimal, ROUND_HALF_UP

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client[os.getenv("MONGO_DB", "attendance_db")]

IST = timezone(timedelta(hours=5, minutes=30))

app = FastAPI(title="Employee Attendance & Analytics API", version="2.0.0")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def compute_late_minutes(punch_in: datetime, shift_start: str) -> int:
    h, m = map(int, shift_start.split(":"))
    if punch_in.tzinfo is None:
        punch_in = punch_in.replace(tzinfo=IST)
    start = punch_in.replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=IST)
    minutes = int((punch_in - start).total_seconds() // 60)
    return minutes if minutes > 10 else 0


def compute_work_hours(punch_in: datetime, punch_out: datetime) -> float:
    seconds = (punch_out - punch_in).total_seconds()
    hours = Decimal(str(seconds)) / Decimal("3600")
    rounded = hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(rounded)
    

def compute_overtime(punch_out: datetime, shift_end: str, date_str: str) -> int:
    h, m = map(int, shift_end.split(":"))
    end = datetime.fromisoformat(date_str).replace(hour=h, minute=m, tzinfo=IST)
    if punch_out.tzinfo is None:
        punch_out = punch_out.replace(tzinfo=IST)

    minutes = int((punch_out - end).total_seconds() // 60)
    if minutes >= 30:
        return minutes
    return 0
    


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class EmployeeIn(BaseModel):
    emp_code: str
    name: str
    email: str
    department: str
    shift_start: str = "09:30"
    shift_end: str = "18:30"
    joined_on: str


class PunchInIn(BaseModel):
    emp_code: str
    punched_at: Optional[int] = None
    status: str = "PRESENT"


# --------------------------------------------------------------------------- #
# Endpoints provided
# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/employees", status_code=201)
def create_employee(body: EmployeeIn):
    if db.employees.find_one({"emp_code": body.emp_code}):
        raise HTTPException(409, "emp_code already exists")
    doc = body.model_dump()
    doc["created_at"] = datetime.now()
    db.employees.insert_one(doc)
    doc.pop("_id", None)
    return doc


@app.get("/employees")
def list_employees(department: Optional[str] = None, page: int = 1, page_size: int = 20):
    q = {}
    if department:
        q["department"] = department
    skip = (page - 1) * page_size
    total = db.employees.count_documents({})
    items = list(db.employees.find(q, {"_id": 0}).skip(skip).limit(page_size))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@app.post("/attendance/punch-in", status_code=201)
def punch_in(body: PunchInIn):
    emp = db.employees.find_one({"emp_code": body.emp_code})
    ts = datetime.fromtimestamp(body.punched_at / 1000, tz=IST) if body.punched_at else datetime.now(IST)
    ts = ts.replace(microsecond=0)

    d = ts.date().isoformat()
    if db.attendance_logs.find_one({"emp_code": body.emp_code, "date": d}):
        raise HTTPException(409, "already punched in for this date")
    doc = {
        "emp_code": body.emp_code,
        "date": d,
        "status": body.status,
        "punch_in": ts,
        "punch_out": None,
        "work_hours": None,
        "late_minutes": compute_late_minutes(ts, emp["shift_start"]),
        "overtime_minutes": 0,
        "half_day": False,
        "history": [],
    }
    res = db.attendance_logs.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc.pop("_id", None)
    return doc

@app.get("/attendance")
def list_attendance(
    emp_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    q = {}
    if emp_code:
        q["emp_code"] = emp_code
    if date_from or date_to:
        q["date"] = {}
        if date_from:
            q["date"]["$gte"] = date_from
        if date_to:
            q["date"]["$lte"] = date_to
    if status:
        q["status"] = status

    skip = (page - 1) * page_size
    total = db.attendance_logs.count_documents(q)

    # Use MongoDB cursor methods for pagination and sorting instead of in-memory Python sorting
    cursor = db.attendance_logs.find(q).sort("date", -1).skip(skip).limit(page_size)
    page_docs = []
    for d in cursor:
        d["id"] = str(d.pop("_id"))
        page_docs.append(d)

    return {"items": page_docs, "total": total, "page": page, "page_size": page_size}
    

        
# --------------------------------------------------------------------------- #
# TODO - the rest of the contract (see openapi.yaml):
#   POST  /attendance/punch-out
#   PATCH /attendance/{emp_code}/{date}
#   GET   /analytics/employees/{emp_code}/monthly
#   GET   /analytics/departments/summary
#   GET   /analytics/leaderboard/late
#   GET   /analytics/departments/{department}/trend
#   GET   /admin/explain/{endpoint}
# --------------------------------------------------------------------------- #
@app.post("/attendance/punch-out", status_code=200)
def punch_out(body: PunchIn):  # You can also use a dedicated PunchOut model if defined, or reuse PunchIn
    # 1. Determine punch-out timestamp in IST, truncated to whole seconds
    out_ts = datetime.fromtimestamp(body.punched_at / 1000, tz=IST) if body.punched_at else datetime.now(IST)
    out_ts = out_ts.replace(microsecond=0)
    d = out_ts.date().isoformat()

    # 2. Find the active attendance log for today without a punch_out
    log = db.attendance_logs.find_one({"emp_code": body.emp_code, "date": d, "punch_out": None})
    if not log:
        raise HTTPException(404, "No active punch-in found for today")

    # 3. Fetch employee details for shift end time lookup
    emp = db.employees.find_one({"emp_code": body.emp_code})
    shift_end = emp.get("shift_end", "18:30") if emp else "18:30"

    # 4. Calculate work hours and overtime using our helpers
    punch_in_dt = log["punch_in"]
    if punch_in_dt.tzinfo is None:
        punch_in_dt = punch_in_dt.replace(tzinfo=IST)

    work_hours = compute_work_hours(punch_in_dt, out_ts)
    overtime_mins = compute_overtime(out_ts, shift_end, d)

    # 5. Determine if it's a half-day (e.g., work hours less than 4 hours as a standard rule)
    half_day = work_hours < 4.0

    # 6. Update the document in MongoDB
    db.attendance_logs.update_one(
        {"_id": log["_id"]},
        {
            "$set": {
                "punch_out": out_ts,
                "work_hours": work_hours,
                "overtime_minutes": overtime_mins,
                "half_day": half_day,
                "status": "PRESENT"
            }
        }
    )

    # Fetch updated document to return
    updated_log = db.attendance_logs.find_one({"_id": log["_id"]})
    updated_log["id"] = str(updated_log.pop("_id"))
    return updated_log
    
@app.get("/analytics/employees/{emp_code}/monthly")
def employee_monthly_analytics(emp_code: str, year: int, month: int):
    # Construct date prefix for matching (e.g., "2026-10")
    month_str = f"{year:04d}-{month:02d}"
    
    pipeline = [
        {
            "$match": {
                "emp_code": emp_code,
                "date": {"$regex": f"^{month_str}"}
            }
        },
        {
            "$group": {
                "_id": "$emp_code",
                "total_days_present": {"$sum": 1},
                "total_work_hours": {"$sum": {"$ifNull": ["$work_hours", 0]}},
                "total_overtime_minutes": {"$sum": {"$ifNull": ["$overtime_minutes", 0]}},
                "avg_late_minutes": {"$avg": {"$ifNull": ["$late_minutes", 0]}}
            }
        }
    ]
    
    result = list(db.attendance_logs.aggregate(pipeline))
    if not result:
        return {
            "emp_code": emp_code,
            "year": year,
            "month": month,
            "total_days_present": 0,
            "total_work_hours": 0.0,
            "total_overtime_minutes": 0,
            "avg_late_minutes": 0.0
        }
        
    data = result[0]
    return {
        "emp_code": emp_code,
        "year": year,
        "month": month,
        "total_days_present": data["total_days_present"],
        "total_work_hours": round(data["total_work_hours"], 2),
        "total_overtime_minutes": int(data["total_overtime_minutes"]),
        "avg_late_minutes": round(data["avg_late_minutes"], 2)
    }
@app.get("/analytics/departments/summary")
def department_summary(date: str):
    # Lookup employees, match attendance by date, and group by department
    pipeline = [
        {
            "$lookup": {
                "from": "employees",
                "localField": "emp_code",
                "foreignField": "emp_code",
                "as": "employee_info"
            }
        },
        {"$unwind": "$employee_info"},
        {
            "$match": {"date": date}
        },
        {
            "$group": {
                "_id": "$employee_info.department",
                "total_present": {"$sum": 1},
                "total_late": {
                    "$sum": {"$cond": [{"$gt": ["$late_minutes", 0]}, 1, 0]}
                },
                "total_overtime": {
                    "$sum": {"$cond": [{"$gt": ["$overtime_minutes", 0]}, 1, 0]}
                }
            }
        }
    ]
    
    results = list(db.attendance_logs.aggregate(pipeline))
    summary = []
    for r in results:
        summary.append({
            "department": r["_id"],
            "total_present": r["total_present"],
            "total_late": r["total_late"],
            "total_overtime": r["total_overtime"]
        })
    return {"date": date, "departments": summary}
@app.get("/analytics/leaderboard/late")
def late_leaderboard(date_from: str, date_to: str, limit: int = 10):
    pipeline = [
        {
            "$match": {
                "date": {"$gte": date_from, "$lte": date_to},
                "late_minutes": {"$gt": 0}
            }
        },
        {
            "$group": {
                "_id": "$emp_code",
                "total_late_minutes": {"$sum": "$late_minutes"},
                "late_count": {"$sum": 1}
            }
        },
        {"$sort": {"total_late_minutes": -1}},
        {"$limit": limit}
    ]
    
    results = list(db.attendance_logs.aggregate(pipeline))
    leaderboard = []
    for r in results:
        emp = db.employees.find_one({"emp_code": r["_id"]})
        leaderboard.append({
            "emp_code": r["_id"],
            "name": emp["name"] if emp else "Unknown",
            "total_late_minutes": r["total_late_minutes"],
            "late_count": r["late_count"]
        })
    return {"items": leaderboard}
@app.get("/analytics/departments/{department}/trend")
def department_trend(department: str, date_from: str, date_to: str):
    pipeline = [
        {
            "$lookup": {
                "from": "employees",
                "localField": "emp_code",
                "foreignField": "emp_code",
                "as": "employee_info"
            }
        },
        {"$unwind": "$employee_info"},
        {
            "$match": {
                "employee_info.department": department,
                "date": {"$gte": date_from, "$lte": date_to}
            }
        },
        {
            "$group": {
                "_id": "$date",
                "present_count": {"$sum": 1},
                "total_work_hours": {"$sum": {"$ifNull": ["$work_hours", 0]}},
                "late_count": {
                    "$sum": {"$cond": [{"$gt": ["$late_minutes", 0]}, 1, 0]}
                }
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    results = list(db.attendance_logs.aggregate(pipeline))
    trend = []
    for r in results:
        trend.append({
            "date": r["_id"],
            "present_count": r["present_count"],
            "total_work_hours": round(r["total_work_hours"], 2),
            "late_count": r["late_count"]
        })
    return {"department": department, "trend": trend}


@app.get("/admin/explain/{endpoint}")
def admin_explain(endpoint: str):
    explanations = {
        "punch-in": "Records employee entry, enforces IST timezone, truncates microseconds, and evaluates late arrival grace periods.",
        "punch-out": "Records employee exit, validates active shifts, computes quantized half-up work hours, and checks 30-minute overtime thresholds.",
        "attendance": "Performs paginated and server-side sorted queries on attendance logs for high scalability.",
        "monthly": "Aggregates monthly attendance metrics including total present days, work hours, and average late minutes using MongoDB pipelines.",
        "summary": "Groups daily attendance statistics by department using MongoDB lookups and conditional aggregation."
    }
    
    clean_key = endpoint.strip("/")
    explanation = explanations.get(clean_key, "No explanation available for this endpoint.")
    return {"endpoint": endpoint, "explanation": explanation}


