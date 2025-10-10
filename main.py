import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from pymongo import MongoClient
import uvicorn

load_dotenv() 
MONGO_CLIENT_URI = os.getenv("MONGO_CLIENT_URI")
DB_NAME = os.getenv("DB_NAME")
app = FastAPI(title="School Timetable API")

# MongoDB connection 
client = MongoClient(MONGO_CLIENT_URI)
db = client[DB_NAME]
timetable_col = db["timetables"]

# Pydantic models for timetable
class Slot(BaseModel):
    subject: str
    teacher: Optional[str]

class DailySchedule(BaseModel):
    day: str
    periods: List[Optional[Slot]]

class TimetableResponse(BaseModel):
    section: str
    schedule: List[DailySchedule]

# Helper to fetch timetable from MongoDB
def get_timetable(section: str) -> Optional[Dict]:
    doc = timetable_col.find_one({"section": section})
    if not doc:
        return None
    # Convert MongoDB doc to API response format
    schedule = []
    for day_sched in doc["schedule"]:
        schedule.append(DailySchedule(day=day_sched["day"], periods=day_sched["periods"]))
    return TimetableResponse(section=doc["section"], schedule=schedule)

# API endpoint to get timetable for a section
@app.get("/timetable/{section}", response_model=TimetableResponse)
async def fetch_timetable(section: str):
    result = get_timetable(section)
    if not result:
        raise HTTPException(status_code=404, detail="Timetable not found")
    return result

# Example API for health check
@app.get("/")
async def root():
    return {"message": "School Timetable API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)