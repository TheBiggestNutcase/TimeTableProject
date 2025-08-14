import pandas as pd
from timetable_with_labs_and_theory import (
    LabTimetable,
    TheoryTimetable,
    LAB_SUBJECTS,
    PREBOOKED,
    DAYS,
    PERIODS
)
from variables import YEARS_SECTIONS, SUBJECTS_PER_YEAR, TEACHER_ASSIGNMENTS
from collections import defaultdict
import random

def export_excel(filename="timetable_export.xlsx"):
    random.seed(42)

    # Keep track of teacher usage
    teacher_busy = defaultdict(lambda: [[False]*PERIODS for _ in range(DAYS)])

    # 1. Generate labs
    lab_gen = LabTimetable(LAB_SUBJECTS, teacher_busy, prebooked=PREBOOKED)
    lab_gen.generate_lab_pairs()

    # 2. Generate theory
    theory_gen = TheoryTimetable(YEARS_SECTIONS, SUBJECTS_PER_YEAR,
                                 TEACHER_ASSIGNMENTS, teacher_busy, lab_gen.lab_schedules)
    theory_gen.generate_timetable()

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # --- CLASS TIMETABLES ---
        for sec in sorted(theory_gen.class_schedules):
            data = []
            for d in range(DAYS):
                row = []
                for p in range(PERIODS):
                    if (sec in lab_gen.lab_schedules and
                        (lab_gen.lab_schedules[sec]['B1'][d][p] or
                         lab_gen.lab_schedules[sec]['B2'][d][p])):
                        cell_val = "LAB"
                    else:
                        slot = theory_gen.class_schedules[sec][d][p]
                        cell_val = slot[0] if slot else "-"
                    row.append(cell_val)
                data.append(row)
            df = pd.DataFrame(data, columns=[f"Period {i+1}" for i in range(PERIODS)])
            df.insert(0, "Day", day_names[:DAYS])
            df.to_excel(writer, sheet_name=f"Class_{sec}", index=False)

        # --- TEACHER TIMETABLES ---
        for teacher in sorted(TEACHER_ASSIGNMENTS.keys()):
            data = []
            for d in range(DAYS):
                row = []
                for p in range(PERIODS):
                    # Check labs first
                    found = "-"
                    for sec, batches in lab_gen.lab_schedules.items():
                        for batch, sched in batches.items():
                            slot = sched[d][p]
                            if slot and slot[1] == teacher:
                                found = f"{sec}-{batch}:{slot[0]}"
                                break
                        if found != "-":
                            break
                    # Check theory if not lab
                    if found == "-":
                        for sec, sched in theory_gen.class_schedules.items():
                            slot = sched[d][p]
                            if slot and slot[1] == teacher:
                                found = f"{sec}:{slot[0]}"
                                break
                    row.append(found)
                data.append(row)
            df = pd.DataFrame(data, columns=[f"Period {i+1}" for i in range(PERIODS)])
            df.insert(0, "Day", day_names[:DAYS])
            # Excel sheet name limit is 31 chars
            sheet_name = f"T_{teacher[:25]}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"✅ Timetable exported to {filename}")


if __name__ == "__main__":
    export_excel()
