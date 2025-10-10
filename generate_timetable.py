import os
from dotenv import load_dotenv

import random
from collections import defaultdict
from typing import Optional, Tuple, Any, Dict
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ------------ MONGODB CONFIG -------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

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

# ------------ HELPERS -------------

def to_python_tuples(obj: Any) -> Any:
    """
    Recursively convert list-pairs back to tuples for in-memory use,
    because MongoDB stores tuples as arrays.
    - For TEACHER_ASSIGNMENTS: {teacher: [[section_id, subject], ...]}
    - For LAB_SUBJECTS: {section_id: [[lab, teacher], ...]}
    - For PREBOOKED: {teacher: [[day, period], ...]}
    """
    if isinstance(obj, list):
        # If it's a 2-length list of scalars, prefer tuple
        if len(obj) == 2 and not isinstance(obj[0], (list, dict)) and not isinstance(obj[1], (list, dict)):
            return tuple(obj)
        return [to_python_tuples(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_python_tuples(v) for k, v in obj.items()}
    return obj

def load_config_from_mongo() -> Dict[str, Any]:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    def get_doc(coll_name: str, doc_id: str, default: Any = None, wrap_data: bool = True):
        coll = db[coll_name]
        doc = coll.find_one({"_id": doc_id})
        if not doc:
            return default
        # populate_mongodb.py stores payload under "data" to mirror variables.py shape
        return doc["data"] if wrap_data else doc

    try:
        semesters_sections = get_doc(COLL_SEMESTERS, DOC_ID_SEMESTERS, default={}, wrap_data=True)
        subjects_per_semester = get_doc(COLL_SUBJECTS, DOC_ID_SUBJECTS, default={}, wrap_data=True)
        teacher_assignments = get_doc(COLL_TEACHERS, DOC_ID_TEACHERS, default={}, wrap_data=True)
        lab_subjects = get_doc(COLL_LABS, DOC_ID_LABS, default={}, wrap_data=True)
        prebooked = get_doc(COLL_PREBOOKED, DOC_ID_PREBOOKED, default={}, wrap_data=True) or {}

        constants = db[COLL_META].find_one({"_id": DOC_ID_CONSTANTS}) or {}
        # Fallbacks if constants not present
        days = int(constants.get("DAYS", 5))
        periods = int(constants.get("PERIODS", 6))
        max_theory_passes = int(constants.get("MAX_THEORY_PASSES", 10))
        debug_placement = bool(constants.get("DEBUG_PLACEMENT", True))

        # Convert arrays back to tuples where appropriate
        teacher_assignments = to_python_tuples(teacher_assignments)
        lab_subjects = to_python_tuples(lab_subjects)
        prebooked = to_python_tuples(prebooked)

        return {
            "SEMESTERS_SECTIONS": semesters_sections,
            "SUBJECTS_PER_SEMESTER": subjects_per_semester,
            "TEACHER_ASSIGNMENTS": teacher_assignments,
            "LAB_SUBJECTS": lab_subjects,
            "PREBOOKED": prebooked,
            "DAYS": days,
            "PERIODS": periods,
            "MAX_THEORY_PASSES": max_theory_passes,
            "DEBUG_PLACEMENT": debug_placement,
            "_client": client,  # retain for lifecycle management
        }
    except PyMongoError as e:
        try:
            client.close()
        except Exception:
            pass
        raise
    # leave client open to reuse; main() will close after run

# ------------ LAB SCHEDULER -------------

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
            if b1_teacher in self.prebooked and (day, p) in self.prebooked[b1_teacher]:
                return False
            if b2_teacher in self.prebooked and (day, p) in self.prebooked[b2_teacher]:
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
                if not placed:
                    print(f"WARNING: Could not place labs {subj1}/{subj2} for {section}")

    def print_lab_timetables(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        for section in sorted(self.lab_schedules):
            for batch in ('B1', 'B2'):
                print(f"\nSection {section}-{batch} Labs:")
                print("Day " + "".join(f"P{i+1:^12}" for i in range(self.periods_per_day)))
                for d in range(self.days):
                    row = f"{days[d]:<4}"
                    for p in range(self.periods_per_day):
                        slot = self.lab_schedules[section][batch][d][p]
                        display = slot[0] if slot else "-"
                        row += f"{display:^12}"
                    print(row)

# ------------ THEORY SCHEDULER -------------

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

    def can_schedule(self, section, day, period, subject, relax_rules=False, debug=False):
        teacher = self.section_subject_teacher.get((section, subject))
        if not teacher:
            if debug: print(f"[NO TEACHER] {section} {subject}")
            return False

        if section in self.lab_schedules and (
            self.lab_schedules[section]['B1'][day][period] or
            self.lab_schedules[section]['B2'][day][period]
        ):
            if debug: print(f"[LAB CONFLICT] {section} {subject} at {day},{period}")
            return False

        if self.class_schedules[section][day][period]:
            if debug: print(f"[CLASS OCCUPIED] {section} {subject} at {day},{period}")
            return False

        if self.teacher_busy[teacher][day][period]:
            if debug: print(f"[TEACHER BUSY] {teacher} at {day},{period}")
            return False

        if not relax_rules:
            if any(slot and slot == subject for slot in self.class_schedules[section][day]):
                if debug: print(f"[ONCE/DAY FAIL] {section} {subject} on day {day}")
                return False

            if period > 0 and self.class_schedules[section][day][period-1] and \
               self.class_schedules[section][day][period-1] == subject:
                if debug: print(f"[CONSEC BEFORE] {section} {subject} at p{period}")
                return False

            if period < self.periods_per_day-1 and self.class_schedules[section][day][period+1] and \
               self.class_schedules[section][day][period+1] == subject:
                if debug: print(f"[CONSEC AFTER] {section} {subject} at p{period}")
                return False

        return True

    def place_class(self, section, day, period, subject):
        teacher = self.section_subject_teacher[(section, subject)]
        self.class_schedules[section][day][period] = (subject, teacher)
        self.teacher_busy[teacher][day][period] = True

    def generate_timetable(self, max_iterations: int):
        unplaced = {
            sec: [sub for sub, freq in self.subjects_per_semester[sec[:-1]].items() for _ in range(freq)]
            for sec in self.class_schedules
        }

        for iteration in range(1, max_iterations+1):
            relax = iteration > max_iterations // 2
            print(f"\n--- Pass {iteration} (relax={relax}) ---")

            # Priority: Year 4 first (year "7")
            year4_sections = [s for s in unplaced if s.startswith("7")]
            other_sections = [s for s in unplaced if not s.startswith("7")]
            random.shuffle(year4_sections)
            random.shuffle(other_sections)
            sections = year4_sections + other_sections

            placed_any = False
            for sec in sections:
                random.shuffle(unplaced[sec])
                for subj in list(unplaced[sec]):
                    # Early period preference
                    if sec.startswith("7"):
                        period_order = [0, 1, 2, 3, 4, 5]
                    else:
                        early = [0, 1, 2]
                        late = [3, 4, 5]
                        random.shuffle(early)
                        random.shuffle(late)
                        period_order = early + late

                    # Balance days: fewest scheduled first
                    day_load = [(d, sum(1 for slot in self.class_schedules[sec][d] if slot)) for d in range(self.days)]
                    day_load.sort(key=lambda x: x[1])
                    days_by_load = [d for d, _ in day_load]
                    day_periods = [(d, p) for d in days_by_load for p in period_order]

                    for d, p in day_periods:
                        if self.can_schedule(sec, d, p, subj, relax_rules=relax):
                            self.place_class(sec, d, p, subj)
                            unplaced[sec].remove(subj)
                            placed_any = True
                            break
                if not placed_any:
                    break

            self.post_repair(unplaced)

            for sec, subs in unplaced.items():
                for subj in subs:
                    print(f"[UNPLACED] {subj} in {sec}")

    def post_repair(self, unplaced):
        for sec in list(unplaced.keys()):
            for subj in list(unplaced[sec]):
                teacher = self.section_subject_teacher.get((sec, subj))
                if not teacher:
                    continue
                placed = False
                for d in range(self.days):
                    for p in range(self.periods_per_day):
                        if self.can_schedule(sec, d, p, subj, relax_rules=True):
                            self.place_class(sec, d, p, subj)
                            if subj in unplaced[sec]:
                                unplaced[sec].remove(subj)
                            placed = True
                            break
                        else:
                            for other_sec in self.class_schedules:
                                other_slot = self.class_schedules[other_sec][d][p]
                                if other_slot is not None:
                                    o_subj, _ = other_slot
                                    if self.can_schedule(sec, d, p, subj, relax_rules=True) and \
                                       self.can_schedule(other_sec, d, p, o_subj, relax_rules=True):
                                        self.class_schedules[sec][d][p] = (subj, teacher)
                                        if subj in unplaced[sec]:
                                            unplaced[sec].remove(subj)
                                        placed = True
                                        break
                    if placed:
                        break
                if placed:
                    break

# ------------ MAIN -------------

def main():
    cfg = load_config_from_mongo()
    SEMESTERS_SECTIONS = cfg["SEMESTERS_SECTIONS"]
    SUBJECTS_PER_SEMESTER = cfg["SUBJECTS_PER_SEMESTER"]
    TEACHER_ASSIGNMENTS = cfg["TEACHER_ASSIGNMENTS"]
    LAB_SUBJECTS = cfg["LAB_SUBJECTS"]
    PREBOOKED = cfg["PREBOOKED"]
    DAYS = cfg["DAYS"]
    PERIODS = cfg["PERIODS"]
    MAX_THEORY_PASSES = cfg["MAX_THEORY_PASSES"]
    DEBUG_PLACEMENT = cfg["DEBUG_PLACEMENT"]
    client = cfg["_client"]

    try:
        random.seed(42)
        teacher_busy = defaultdict(lambda: [[False]*PERIODS for _ in range(DAYS)])

        lab_gen = LabTimetable(LAB_SUBJECTS, teacher_busy, days=DAYS, periods=PERIODS, prebooked=PREBOOKED)
        lab_gen.generate_lab_pairs()

        theory_gen = TheoryTimetable(SEMESTERS_SECTIONS, SUBJECTS_PER_SEMESTER, TEACHER_ASSIGNMENTS,
                                     teacher_busy, lab_gen.lab_schedules, days=DAYS, periods=PERIODS)
        theory_gen.generate_timetable(max_iterations=MAX_THEORY_PASSES)

        lab_gen.print_lab_timetables()

        print("\n=== FINAL COMBINED TIMETABLE ===")
        days_lbl = ["Mon","Tue","Wed","Thu","Fri"]
        for sec in sorted(theory_gen.class_schedules):
            print(f"\nSection {sec}:")
            print("Day " + "".join(f"P{i+1:^15}" for i in range(PERIODS)))
            for d in range(DAYS):
                row = f"{days_lbl[d]:<4}"
                for p in range(PERIODS):
                    if sec in lab_gen.lab_schedules and (
                        lab_gen.lab_schedules[sec]['B1'][d][p] or lab_gen.lab_schedules[sec]['B2'][d][p]
                    ):
                        row += f"{'LAB':^15}"
                    else:
                        slot = theory_gen.class_schedules[sec][d][p]
                        row += f"{slot[0][:12] if slot else '-':^15}"
                print(row)
    finally:
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()