import os
import sys
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv

from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ---------- Config ----------

load_dotenv() 
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')

COLL_SEMESTERS = os.getenv('COLL_SEMESTERS')
COLL_SUBJECTS = os.getenv('COLL_SUBJECTS')
COLL_TEACHERS = os.getenv('COLL_TEACHERS')
COLL_PREBOOKED = os.getenv('COLL_PREBOOKED')
COLL_LABS = os.getenv('COLL_LABS')
COLL_META = os.getenv('COLL_META')

DOC_ID_SEMESTERS = os.getenv('DOC_ID_SEMESTERS')
DOC_ID_SUBJECTS = os.getenv('DOC_ID_SUBJECTS')
DOC_ID_TEACHERS = os.getenv('DOC_ID_TEACHERS')
DOC_ID_PREBOOKED = os.getenv('DOC_ID_PREBOOKED')
DOC_ID_LABS = os.getenv('DOC_ID_LABS')
DOC_ID_CONSTANTS = os.getenv('DOC_ID_CONSTANTS')

# # ---- Import variables.py ----
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

try:
    import variables
except Exception as e:
    print(f"Failed to import variables.py: {e}")
    sys.exit(1)

def to_json_compatible(obj: Any) -> Any:
    if isinstance(obj, tuple):
        return [to_json_compatible(x) for x in obj]
    if isinstance(obj, list):
        return [to_json_compatible(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_json_compatible(v) for k, v in obj.items()}
    return obj

def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    try:
        # Accept either new or legacy names during testing
        # Legacy Names - Initially, all 'semesters' names were saved as 'years'
        semesters_sections = getattr(variables, "YEARS_SECTIONS", None)
        if semesters_sections is None:
            semesters_sections = getattr(variables, "YEARS_SECTIONS", {})
        subjects_per_semester = getattr(variables, "SUBJECTS_PER_YEAR", None)
        if subjects_per_semester is None:
            subjects_per_semester = getattr(variables, "SUBJECTS_PER_YEAR", {})

        teacher_assignments = getattr(variables, "TEACHER_ASSIGNMENTS", {})
        prebooked = getattr(variables, "PREBOOKED", {})
        lab_subjects = getattr(variables, "LAB_SUBJECTS", {})
        constants = getattr(variables, "TIMETABLE_CONSTANTS", {})

        db[COLL_SEMESTERS].update_one(
            {"_id": DOC_ID_SEMESTERS},
            {"$set": {"_id": DOC_ID_SEMESTERS, "data": to_json_compatible(semesters_sections)}},
            upsert=True,
        )
        db[COLL_SUBJECTS].update_one(
            {"_id": DOC_ID_SUBJECTS},
            {"$set": {"_id": DOC_ID_SUBJECTS, "data": to_json_compatible(subjects_per_semester)}},
            upsert=True,
        )
        db[COLL_TEACHERS].update_one(
            {"_id": DOC_ID_TEACHERS},
            {"$set": {"_id": DOC_ID_TEACHERS, "data": to_json_compatible(teacher_assignments)}},
            upsert=True,
        )
        db[COLL_PREBOOKED].update_one(
            {"_id": DOC_ID_PREBOOKED},
            {"$set": {"_id": DOC_ID_PREBOOKED, "data": to_json_compatible(prebooked)}},
            upsert=True,
        )
        db[COLL_LABS].update_one(
            {"_id": DOC_ID_LABS},
            {"$set": {"_id": DOC_ID_LABS, "data": to_json_compatible(lab_subjects)}},
            upsert=True,
        )
        db[COLL_META].update_one(
            {"_id": DOC_ID_CONSTANTS},
            {"$set": {"_id": DOC_ID_CONSTANTS, "data": to_json_compatible(constants)}},
            upsert=True,
        )
        print("Seeded semester-based documents.")
    except PyMongoError as e:
        print(f"Mongo error: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()