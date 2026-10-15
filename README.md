# Employee Attendance & Analytics API

A robust FastAPI application built for managing employee attendance, shifts, and advanced analytics using Python and MongoDB.

## Features
- **Timezone Management:** Fully configured for Indian Standard Time (IST, UTC+05:30) with microsecond truncation.
- **Shift & Attendance Tracking:** Handles punch-in, punch-out, 10-minute late grace periods, and 30-minute overtime evaluation.
- **Advanced Analytics:** Monthly employee summaries, department breakdowns, late leaderboards, and trend analysis powered by MongoDB aggregation pipelines.
- **Admin Utilities:** Diagnostic endpoint explanations for contract transparency.

## Setup & Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/nikithavemuri/hrone-employee-attendance-api.git](https://github.com/nikithavemuri/hrone-employee-attendance-api.git)
   cd hrone-employee-attendance-api
2.Install dependencies:
pip install -r requirements.txt
3.Set up your .env file with your MongoDB connection string:
MONGO_URI=mongodb://localhost:27017
MONGO_DB=attendance_db
4.Run the application:
uvicorn app.main:app --reload --port 8000
Access the interactive documentation at http://localhost:8000/docs.


