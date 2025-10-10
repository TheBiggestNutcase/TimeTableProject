import os
from typing import Any, Dict, Optional, Tuple, List
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(title="Timetable API", version="1.0.0")  

app.add_middleware(  
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    expose_headers=["*"],
)

@app.get("/")  
def root():
    return {"status": "ok", "service": "Timetable API", "version": "1.0.0"}  

@app.get("/healthz")  
def healthz():
    return {"status": "ok"}  

client = MongoClient(MONGO_URI)  
db = client[DB_NAME]  

def to_python_tuples(obj: Any) -> Any:  
    if isinstance(obj, list):
        if len(obj) == 2 and not isinstance(obj[0], (list, dict)) and not isinstance(obj[1], (list, dict)):
            return tuple(obj)
        return [to_python_tuples(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_python_tuples(v) for k, v in obj.items()}
    return obj  

def to_json_lists(obj: Any) -> Any:  
    if isinstance(obj, tuple):
        return [to_json_lists(x) for x in obj]
    if isinstance(obj, list):
        return [to_json_lists(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): to_json_lists(v) for k, v in obj.items()}
    return obj  

def get_payload(coll_name: str, doc_id: str, default: Any = None):  
    doc = db[coll_name].find_one({"_id": doc_id})
    if not doc:
        return default
    return doc.get("data", default)  

def upsert_payload(coll_name: str, doc_id: str, data: Any):  
    doc = {"_id": doc_id, "data": to_json_lists(data)}
    db[coll_name].update_one({"_id": doc_id}, {"$set": doc}, upsert=True)  

def get_constants():  
    c = db[COLL_META].find_one({"_id": DOC_ID_CONSTANTS}) or {}
    return {
        "DAYS": int(c.get("DAYS", 5)),
        "PERIODS": int(c.get("PERIODS", 6)),
        "MAX_THEORY_PASSES": int(c.get("MAX_THEORY_PASSES", 10)),
        "DEBUG_PLACEMENT": bool(c.get("DEBUG_PLACEMENT", True)),
    }  

def set_constants(days: int, periods: int, max_theory_passes: int, debug_placement: bool):  
    doc = {
        "_id": DOC_ID_CONSTANTS,
        "DAYS": int(days),
        "PERIODS": int(periods),
        "MAX_THEORY_PASSES": int(max_theory_passes),
        "DEBUG_PLACEMENT": bool(debug_placement),
    }
    db[COLL_META].update_one({"_id": DOC_ID_CONSTANTS}, {"$set": doc}, upsert=True)  

class ConfigWrapper(BaseModel):  
    data: dict  

class ConstantsModel(BaseModel):  
    DAYS: int = Field(5, ge=1)
    PERIODS: int = Field(6, ge=1)
    MAX_THEORY_PASSES: int = Field(10, ge=1)
    DEBUG_PLACEMENT: bool = True  

from collections import defaultdict  
import random  

def _prebook_matches(entries: List[dict] | List[tuple], day: int, period: int, section: str | None, subject: str | None) -> bool:
    """Return True if there exists an entry for (day,period) that matches section+subject if provided; if any entry exists but none matches, return False; if no entry exists for that slot, return None-equivalent by raising. """  
    matched_any = None
    for e in entries:
        if isinstance(e, (list, tuple)) and len(e) >= 2:
            d, p = int(e[0]), int(e[1])
            if d == day and p == period:
                # legacy generic block: blocks everything unless exact match is not representable
                return False
        elif isinstance(e, dict):
            d, p = int(e.get("day", -1)), int(e.get("period", -1))
            if d == day and p == period:
                matched_any = False
                esec = e.get("section_id")
                esub = e.get("subject")
                if section is not None and subject is not None and esec == section and esub == subject:
                    return True
    return matched_any is None  # True means no entry for that slot, so free; False means entries exist but none matched  

class LabTimetable:  
    def __init__(self, lab_subjects, teacher_busy, days, periods, prebooked=None):
        self.lab_subjects = lab_subjects
        self.teacher_busy = teacher_busy
        self.days = days
        self.periods_per_day = periods
        self.prebooked = prebooked if prebooked else {}
        self.lab_schedules: dict[str, dict[str, list[list[Optional[Tuple[str, str]]]]]] = {
            sec: {'B1': [[None]*self.periods_per_day for _ in range(self.days)],
                  'B2': [[None]*self.periods_per_day for _ in range(self.days)]}
            for sec in lab_subjects
        }  

    def can_schedule_pair(self, section, b1_sub, b1_teacher, b2_sub, b2_teacher, day, start):
        if start % 2 != 0 or start > self.periods_per_day - 2:
            return False
        for p in (start, start+1):
            if self.lab_schedules[section]['B1'][day][p] or self.lab_schedules[section]['B2'][day][p]:
                return False
            if self.teacher_busy[b1_teacher][day][p] or self.teacher_busy[b2_teacher][day][p]:
                return False
            # prebook exact-match enforcement
            if b1_teacher in self.prebooked:
                ok = _prebook_matches(self.prebooked[b1_teacher], day, p, section, b1_sub)
                if ok is False:
                    return False
            if b2_teacher in self.prebooked:
                ok = _prebook_matches(self.prebooked[b2_teacher], day, p, section, b2_sub)
                if ok is False:
                    return False
        return True  

    def place_lab_pair(self, section, b1_sub, b1_teacher, b2_sub, b2_teacher, day, start):
        for p in (start, start+1):
            self.lab_schedules[section]['B1'][day][p] = (b1_sub, b1_teacher)
            self.lab_schedules[section]['B2'][day][p] = (b2_sub, b2_teacher)
            self.teacher_busy[b1_teacher][day][p] = True
            self.teacher_busy[b2_teacher][day][p] = True  

    def generate_lab_pairs(self):
        from collections import defaultdict as _dd
        labs_per_day = _dd(lambda: _dd(int))
        for section, labs in self.lab_subjects.items():
            if len(labs) < 2:
                continue
            possible_slots = [(d, s) for d in range(self.days) for s in [4, 2, 0]]
            random.shuffle(possible_slots)
            for i in range(len(labs)):
                subj1, t1 = labs[i]
                subj2, t2 = labs[(i+1) % len(labs)]
                placed = False
                for day, start in possible_slots:
                    if labs_per_day[section][day] >= 2:
                        continue
                    if self.can_schedule_pair(section, subj1, t1, subj2, t2, day, start):
                        self.place_lab_pair(section, subj1, t1, subj2, t2, day, start)
                        labs_per_day[section][day] += 1
                        placed = True
                        break  

    def schedules(self):
        return self.lab_schedules  

class TheoryTimetable:  
    def __init__(self, semesters_sections, subjects_per_semester, teacher_assignments, teacher_busy, lab_schedules, days, periods):
        self.semesters_sections = semesters_sections
        self.subjects_per_semester = subjects_per_semester
        self.teacher_assignments = teacher_assignments
        self.teacher_busy = teacher_busy
        self.lab_schedules = lab_schedules
        self.days = days
        self.periods_per_day = periods

        self.section_subject_teacher: dict[Tuple[str, str], str] = {}
        for t, pairs in teacher_assignments.items():
            for sec, subj in pairs:
                self.section_subject_teacher[(sec, subj)] = t

        self.class_schedules: dict[str, list[list[Optional[Tuple[str, str]]]]] = {
            f"{y}{s}": [[None]*self.periods_per_day for _ in range(self.days)]
            for y, secs in semesters_sections.items() for s in secs
        }  

    def can_schedule(self, section, day, period, subject, relax_rules=False):
        teacher = self.section_subject_teacher.get((section, subject))
        if not teacher:
            return False

        if section in self.lab_schedules and (
            self.lab_schedules[section]['B1'][day][period] or
            self.lab_schedules[section]['B2'][day][period]
        ):
            return False

        if self.class_schedules[section][day][period]:
            return False

        if self.teacher_busy[teacher][day][period]:
            return False

        # prebook exact-match enforcement
        if teacher in getattr(self, "prebooked", {}):
            ok = _prebook_matches(self.prebooked[teacher], day, period, section, subject)
            if ok is False:
                return False

        if not relax_rules:
            if any(slot and slot[0] == subject for slot in self.class_schedules[section][day]):
                return False
            if period > 0 and self.class_schedules[section][day][period-1] and \
               self.class_schedules[section][day][period-1][0] == subject:
                return False
            if period < self.periods_per_day-1 and self.class_schedules[section][day][period+1] and \
               self.class_schedules[section][day][period+1][0] == subject:
                return False

        return True  

    def place_class(self, section, day, period, subject):
        teacher = self.section_subject_teacher[(section, subject)]
        self.class_schedules[section][day][period] = (subject, teacher)
        self.teacher_busy[teacher][day][period] = True  

    def generate(self, max_iterations: int):
        unplaced = {
            sec: [sub for sub, freq in self.subjects_per_semester[sec[:-1]].items() for _ in range(freq)]
            for sec in self.class_schedules
        }
        for iteration in range(1, max_iterations+1):
            relax = iteration > max_iterations // 2
            year4_sections = [s for s in unplaced if s.startswith("7")]
            other_sections = [s for s in unplaced if not s.startswith("7")]
            random.shuffle(year4_sections)
            random.shuffle(other_sections)
            sections = year4_sections + other_sections
            for sec in sections:
                random.shuffle(unplaced[sec])
                for subj in list(unplaced[sec]):
                    if sec.startswith("7"):
                        period_order = [0, 1, 2, 3, 4, 5]
                    else:
                        early = [0, 1, 2]; late = [3, 4, 5]
                        random.shuffle(early); random.shuffle(late)
                        period_order = early + late
                    day_load = [(d, sum(1 for slot in self.class_schedules[sec][d] if slot)) for d in range(self.days)]
                    day_load.sort(key=lambda x: x[1])
                    days_by_load = [d for d, _ in day_load]
                    day_periods = [(d, p) for d in days_by_load for p in period_order]
                    for d, p in day_periods:
                        if self.can_schedule(sec, d, p, subj, relax_rules=relax):
                            self.place_class(sec, d, p, subj)
                            unplaced[sec].remove(subj)
                            break  

    def schedules(self):
        return self.class_schedules  

LAST_LABS: Optional[dict] = None  
LAST_CLASSES: Optional[dict] = None  

def load_all_from_db():
    semesters_sections = to_python_tuples(get_payload(COLL_SEMESTERS, DOC_ID_SEMESTERS, default={}))
    subjects_per_semester = to_python_tuples(get_payload(COLL_SUBJECTS, DOC_ID_SUBJECTS, default={}))
    teacher_assignments = to_python_tuples(get_payload(COLL_TEACHERS, DOC_ID_TEACHERS, default={}))
    lab_subjects = to_python_tuples(get_payload(COLL_LABS, DOC_ID_LABS, default={}))
    prebooked = to_python_tuples(get_payload(COLL_PREBOOKED, DOC_ID_PREBOOKED, default={}) or {})
    constants = get_constants()
    return semesters_sections, subjects_per_semester, teacher_assignments, lab_subjects, prebooked, constants  

@app.get("/config/semesters_sections")
def get_semesters_sections():
    return {"_id": DOC_ID_SEMESTERS, "data": get_payload(COLL_SEMESTERS, DOC_ID_SEMESTERS, default={})}  

@app.put("/config/semesters_sections")
def put_semesters_sections(payload: ConfigWrapper):
    upsert_payload(COLL_SEMESTERS, DOC_ID_SEMESTERS, payload.data)
    return {"status": "ok", "_id": DOC_ID_SEMESTERS}  

@app.get("/config/subjects_per_semester")
def get_subjects_per_semester():
    return {"_id": DOC_ID_SUBJECTS, "data": get_payload(COLL_SUBJECTS, DOC_ID_SUBJECTS, default={})}  

@app.put("/config/subjects_per_semester")
def put_subjects_per_semester(payload: ConfigWrapper):
    upsert_payload(COLL_SUBJECTS, DOC_ID_SUBJECTS, payload.data)
    return {"status": "ok", "_id": DOC_ID_SUBJECTS}  

@app.get("/config/teacher_assignments")
def get_teacher_assignments():
    return {"_id": DOC_ID_TEACHERS, "data": get_payload(COLL_TEACHERS, DOC_ID_TEACHERS, default={})}  

@app.put("/config/teacher_assignments")
def put_teacher_assignments(payload: ConfigWrapper):
    upsert_payload(COLL_TEACHERS, DOC_ID_TEACHERS, payload.data)
    return {"status": "ok", "_id": DOC_ID_TEACHERS}  

@app.get("/config/lab_subjects")
def get_lab_subjects():
    return {"_id": DOC_ID_LABS, "data": get_payload(COLL_LABS, DOC_ID_LABS, default={})}  

@app.put("/config/lab_subjects")
def put_lab_subjects(payload: ConfigWrapper):
    upsert_payload(COLL_LABS, DOC_ID_LABS, payload.data)
    return {"status": "ok", "_id": DOC_ID_LABS}  

@app.get("/config/prebooked")
def get_prebooked():
    return {"_id": DOC_ID_PREBOOKED, "data": get_payload(COLL_PREBOOKED, DOC_ID_PREBOOKED, default={})}  

@app.put("/config/prebooked")
def put_prebooked(payload: ConfigWrapper):
    upsert_payload(COLL_PREBOOKED, DOC_ID_PREBOOKED, payload.data or {})
    return {"status": "ok", "_id": DOC_ID_PREBOOKED}  

@app.get("/config/constants")
def get_meta_constants():
    return get_constants()  

@app.put("/config/constants")
def put_meta_constants(model: ConstantsModel):
    set_constants(model.DAYS, model.PERIODS, model.MAX_THEORY_PASSES, model.DEBUG_PLACEMENT)
    return {"status": "ok"}  

class GenerateRequest(BaseModel):
    seed: Optional[int] = 42
    max_passes_override: Optional[int] = None  

@app.post("/timetable/generate")
def generate_timetable(req: GenerateRequest):
    global LAST_LABS, LAST_CLASSES
    try:
        semesters_sections, subjects_per_semester, teacher_assignments, lab_subjects, prebooked, c = load_all_from_db()
        DAYS = c["DAYS"]; PERIODS = c["PERIODS"]; MAX_THEORY_PASSES = req.max_passes_override or c["MAX_THEORY_PASSES"]
        random.seed(req.seed if req.seed is not None else 42)
        teacher_busy = defaultdict(lambda: [[False]*PERIODS for _ in range(DAYS)])
        lab_gen = LabTimetable(lab_subjects, teacher_busy, days=DAYS, periods=PERIODS, prebooked=prebooked)
        lab_gen.generate_lab_pairs()
        theory_gen = TheoryTimetable(semesters_sections, subjects_per_semester, teacher_assignments,
                                     teacher_busy, lab_gen.schedules(), days=DAYS, periods=PERIODS)
        # attach prebooked to theory timetable as well
        theory_gen.prebooked = prebooked
        theory_gen.generate(MAX_THEORY_PASSES)
        LAST_LABS = lab_gen.schedules(); LAST_CLASSES = theory_gen.schedules()
        return {"status": "ok", "days": DAYS, "periods": PERIODS,
                "labs_sections": list(LAST_LABS.keys()), "classes_sections": list(LAST_CLASSES.keys())}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {e}")  

@app.get("/timetable/labs")
def get_last_labs():
    if LAST_LABS is None:
        raise HTTPException(status_code=404, detail="No lab schedules generated yet")
    return to_json_lists(LAST_LABS)  

@app.get("/timetable/classes")
def get_last_classes():
    if LAST_CLASSES is None:
        raise HTTPException(status_code=404, detail="No class schedules generated yet")
    return to_json_lists(LAST_CLASSES)  

@app.get("/timetable/export")
def export_combined():
    if LAST_LABS is None or LAST_CLASSES is None:
        raise HTTPException(status_code=404, detail="No schedules generated yet")
    combined: Dict[str, List[List[str]]] = {}
    any_section = next(iter(LAST_CLASSES))
    DAYS = len(LAST_CLASSES[any_section]); PERIODS = len(LAST_CLASSES[any_section][0])
    for sec, grid in LAST_CLASSES.items():
        out = [["-" for _ in range(PERIODS)] for _ in range(DAYS)]
        for d in range(DAYS):
            for p in range(PERIODS):
                lab_here = False
                if sec in LAST_LABS and (LAST_LABS[sec]['B1'][d][p] or LAST_LABS[sec]['B2'][d][p]):
                    out[d][p] = "LAB"; lab_here = True
                if not lab_here and grid[d][p]:
                    out[d][p] = grid[d][p][0]
        combined[sec] = out
    return combined  